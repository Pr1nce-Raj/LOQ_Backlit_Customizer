import sys
import os
import threading
import time
from typing import Optional, Tuple, Dict, Any
import keyboard

from config import load_config, save_config, set_startup_enabled, is_startup_enabled
from driver import LenovoDriver
from idle_tracker import IdleMonitor
from effects import EffectEngine, ALL_MODES
from tray import SystemTrayManager
from gui import ModernBacklightGUI

class BacklightApplication:
    """Master application controller with two-way laptop backlight synchronization and conflict-free control."""

    def __init__(self, start_minimized=False):
        self.config = load_config()
        self.start_minimized = start_minimized or self.config.get("start_minimized", False)

        # 1. Hardware Driver
        self.driver = LenovoDriver()

        # 2. Effects Engine (defaults to 0.5x speed)
        self.engine = EffectEngine(
            driver=self.driver,
            mode=self.config.get("effect", "Breathing"),
            speed=float(self.config.get("speed", 0.5)),
            on_level_changed=self._on_hardware_level_changed,
            on_external_override=self._on_external_hardware_override
        )

        # 3. Idle Monitor (Power saving via GetLastInputInfo across keyboard, mouse, and trackpad)
        self.idle_monitor = IdleMonitor(
            timeout_seconds=float(self.config.get("idle_timeout_seconds", 30)),
            enabled=self.config.get("power_saving_enabled", True),
            on_idle=self._on_system_idle,
            on_wake=self._on_system_wake,
            on_tick=self._on_idle_tick,
            poll_interval=0.1
        )

        # 4. System Tray Manager
        self.tray = SystemTrayManager(
            on_show_ui=self.show_ui,
            on_set_mode=self.set_mode,
            on_toggle_power_saving=self.toggle_power_saving,
            on_exit=self.exit_app,
            get_current_mode=self.engine.get_mode,
            is_power_saving_enabled=lambda: self.idle_monitor.enabled
        )

        # 5. Modern GUI
        self.gui = ModernBacklightGUI(
            config=self.config,
            on_save_config=self.save_all_settings,
            on_change_mode=self.set_mode,
            on_change_speed=self.set_speed,
            on_change_power_saving=self.update_power_saving,
            on_exit_app=self.exit_app
        )

        # 6. Two-Way Hardware Sync Watcher (Monitors Fn+Space and Lenovo Vantage)
        self._sync_watcher_running = False
        self._sync_thread = None

        # 7. Global Hotkey Registration
        self.current_registered_hotkey = None
        self._register_hotkey(self.config.get("shortcut", "ctrl+shift+l"))

        initial_mode = self.engine.get_mode()
        self._last_active_mode = initial_mode if initial_mode != "Off" else "Breathing"

    def start(self):
        """Start all services and run the GUI main loop."""
        self.engine.start()
        self.idle_monitor.start()
        self.tray.start()

        # Start hardware sync thread to track Fn+Space & Vantage
        self._sync_watcher_running = True
        self._sync_thread = threading.Thread(target=self._hardware_sync_loop, name="HardwareSyncWatcherThread", daemon=True)
        self._sync_thread.start()

        if self.start_minimized:
            self.gui.hide_to_tray()

        try:
            self.gui.mainloop()
        except KeyboardInterrupt:
            self.exit_app()

    def show_ui(self):
        self.gui.show_from_tray()

    def set_mode(self, mode: str):
        if mode in ALL_MODES and mode != "Off":
            self._last_active_mode = mode
        self.engine.set_mode(mode)
        self.config["effect"] = mode
        save_config(self.config)

        self.gui.sync_external_mode_change(mode)
        self.tray.update_status(mode, self.idle_monitor.is_sleeping())

    def set_speed(self, speed: float):
        self.engine.set_speed(speed)
        self.config["speed"] = speed
        save_config(self.config)

    def toggle_power_saving(self):
        new_state = not self.idle_monitor.enabled
        self.idle_monitor.set_enabled(new_state)
        self.config["power_saving_enabled"] = new_state
        save_config(self.config)
        self.gui.sync_power_saving_state(new_state)
        self.tray.update_status(self.engine.get_mode(), self.idle_monitor.is_sleeping())

    def update_power_saving(self, enabled: bool, timeout: float):
        self.idle_monitor.set_enabled(enabled)
        self.idle_monitor.set_timeout(timeout)
        self.config["power_saving_enabled"] = enabled
        self.config["idle_timeout_seconds"] = int(timeout)
        save_config(self.config)
        self.tray.update_status(self.engine.get_mode(), self.idle_monitor.is_sleeping())

    def save_all_settings(self, new_config: dict) -> dict:
        errors = []
        self.config.update(new_config)

        if not save_config(self.config):
            errors.append("Failed to write backlight_config.json")

        # Apply settings
        self.set_mode(self.config.get("effect", "Breathing"))
        self.set_speed(float(self.config.get("speed", 0.5)))
        self.update_power_saving(
            self.config.get("power_saving_enabled", True),
            float(self.config.get("idle_timeout_seconds", 30))
        )

        # Windows Startup toggle
        if not set_startup_enabled(self.config.get("start_with_windows", False)):
            errors.append("Failed to configure Windows startup registry")

        # Re-register hotkey if changed
        hk_ok, hk_err = self._register_hotkey(self.config.get("shortcut", "ctrl+shift+l"))
        if not hk_ok and hk_err:
            errors.append(f"Invalid hotkey: {hk_err}")

        return {
            "success": len(errors) == 0,
            "errors": errors
        }

    def _register_hotkey(self, shortcut: str) -> tuple[bool, Optional[str]]:
        shortcut = shortcut.strip().lower()
        if ' ' in shortcut and '+' not in shortcut:
            shortcut = shortcut.replace(' ', '+')

        if self.current_registered_hotkey:
            try:
                keyboard.remove_hotkey(self.current_registered_hotkey)
            except Exception:
                pass
            self.current_registered_hotkey = None

        if not shortcut:
            return True, None

        try:
            self.current_registered_hotkey = keyboard.add_hotkey(
                shortcut,
                self._handle_hotkey_triggered,
                suppress=False
            )
            print(f"[Hotkey] Successfully registered global shortcut: {shortcut}")
            return True, None
        except Exception as e:
            err_msg = str(e)
            print(f"[Hotkey] Failed to register shortcut '{shortcut}': {err_msg}")
            return False, err_msg

    def _handle_hotkey_triggered(self):
        action = self.config.get("shortcut_action", "toggle")
        current_mode = self.engine.get_mode()

        if action == "toggle":
            # If backlight is currently active (any trick or solid mode), turn it off
            if current_mode != "Off":
                self.set_mode("Off")
            else:
                # Restore previous active mode (or Breathing)
                target = self._last_active_mode if self._last_active_mode in ALL_MODES and self._last_active_mode != "Off" else "Breathing"
                self.set_mode(target)
        elif action == "cycle":
            try:
                idx = ALL_MODES.index(current_mode)
                next_mode = ALL_MODES[(idx + 1) % len(ALL_MODES)]
            except ValueError:
                next_mode = "Breathing"
            self.set_mode(next_mode)

    # ---------------- Two-Way Hardware Synchronization ----------------

    def _hardware_sync_loop(self):
        """Background loop that polls hardware to sync external Fn+Space or Lenovo Vantage changes into app."""
        while self._sync_watcher_running:
            try:
                ext_level = self.driver.check_external_hardware_change()
                if ext_level is not None:
                    self._on_external_hardware_override(ext_level)
            except Exception:
                pass
            time.sleep(0.08)

    def _on_external_hardware_override(self, new_level: int):
        """Called when user presses Fn+Space on the laptop keyboard or toggles in Lenovo Vantage."""
        level_to_mode = {0: "Off", 1: "Solid Low", 2: "Solid High"}
        new_mode = level_to_mode.get(new_level, "Off")
        print(f"[Hardware Sync] Laptop backlight change detected: Level {new_level} -> Mode {new_mode}")

        # If user pressed Fn+Space to turn ON the backlight while system was idle/sleeping, wake up!
        if self.idle_monitor.is_sleeping() and new_level > 0:
            self.idle_monitor.wake()
        elif not self.idle_monitor.is_sleeping():
            self.engine.set_paused(False)

        if new_mode != "Off":
            self._last_active_mode = new_mode

        self.engine.set_mode(new_mode)
        self.config["effect"] = new_mode
        save_config(self.config)

        self.gui.sync_external_mode_change(new_mode)
        self.gui.update_hardware_level(new_level)
        self.tray.update_status(new_mode, self.idle_monitor.is_sleeping())

    # ---------------- Idle Callbacks ----------------

    def _on_system_idle(self):
        """Called by IdleMonitor when no key/mouse/trackpad event occurred for 30s."""
        self.engine.set_paused(True)
        self.tray.update_status(self.engine.get_mode(), is_sleeping=True)

    def _on_system_wake(self):
        """Called by IdleMonitor immediately when any keyboard, mouse, or trackpad input occurs."""
        self.engine.set_paused(False)
        self.tray.update_status(self.engine.get_mode(), is_sleeping=False)

    def _on_idle_tick(self, idle_sec: float):
        """Called on each timer tick to update UI countdown."""
        self.gui.update_idle_status(idle_sec, self.idle_monitor.is_sleeping())

    def _on_hardware_level_changed(self, level: int):
        """Called whenever the hardware backlight level changes."""
        self.gui.update_hardware_level(level)

    def exit_app(self):
        """Gracefully terminate background threads, restore hardware backlight, and exit."""
        print("[App] Shutting down...")
        self._sync_watcher_running = False

        if self.current_registered_hotkey:
            try:
                keyboard.remove_hotkey(self.current_registered_hotkey)
            except Exception:
                pass

        self.idle_monitor.stop()
        self.engine.stop()
        self.tray.stop()
        self.driver.close()

        try:
            self.gui.destroy()
        except Exception:
            pass
        sys.exit(0)

if __name__ == "__main__":
    minimized = "--minimized" in sys.argv or "--background" in sys.argv
    app = BacklightApplication(start_minimized=minimized)
    app.start()
