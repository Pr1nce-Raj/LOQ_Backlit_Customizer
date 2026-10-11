import threading
import time
import customtkinter as ctk
from typing import Callable, Dict, Any, Optional
import keyboard
from effects import ALL_MODES

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLOR_BG = "#121317"
COLOR_CARD = "#1a1c23"
COLOR_CARD_BORDER = "#2b2e3b"
COLOR_ACCENT = "#00b4d8"
COLOR_ACCENT_HOVER = "#0096c7"
COLOR_SUCCESS = "#2ec4b6"
COLOR_WARNING = "#ff9f1c"
COLOR_DANGER = "#e71d36"
COLOR_TEXT_MUTED = "#8d99ae"

class ModernBacklightGUI(ctk.CTk):
    """Ultra-modern Lenovo LOQ Backlight Customizer dashboard built with CustomTkinter."""

    def __init__(
        self,
        config: Dict[str, Any],
        on_save_config: Callable[[Dict[str, Any]], None],
        on_change_mode: Callable[[str], None],
        on_change_speed: Callable[[float], None],
        on_change_power_saving: Callable[[bool, float], None],
        on_exit_app: Callable[[], None],
    ):
        super().__init__()

        self.config = config
        self.on_save_config = on_save_config
        self.on_change_mode = on_change_mode
        self.on_change_speed = on_change_speed
        self.on_change_power_saving = on_change_power_saving
        self.on_exit_app = on_exit_app

        self.title("Lenovo LOQ - Keyboard Backlight Customizer")
        self.geometry("640x780")
        self.minsize(580, 680)
        self.configure(fg_color=COLOR_BG)

        self._recording_hotkey = False
        self._current_hw_level = 0
        self._is_sleeping = False
        self._idle_sec = 0.0

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._handle_window_close)

    def _build_ui(self):
        # Scrollable container for flawless layout across all laptop display scalings
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=COLOR_BG, corner_radius=0)
        self.scroll.pack(fill="both", expand=True, padx=16, pady=16)

        # Header Section
        header_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 14))

        title_subframe = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_subframe.pack(side="left")

        brand_label = ctk.CTkLabel(
            title_subframe,
            text="LENOVO LOQ",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=COLOR_ACCENT
        )
        brand_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            title_subframe,
            text="Hardware Backlight Customizer & Inactivity Guard",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MUTED
        )
        subtitle_label.pack(anchor="w")

        self.status_badge = ctk.CTkLabel(
            header_frame,
            text="● ACTIVE",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_SUCCESS,
            fg_color="#172b26",
            corner_radius=8,
            padx=12,
            pady=4
        )
        self.status_badge.pack(side="right", pady=4)

        # ---------------- Card 1: Live Status & Power Saving Monitor ----------------
        status_card = ctk.CTkFrame(self.scroll, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=COLOR_CARD_BORDER)
        status_card.pack(fill="x", pady=8, padx=4)

        card1_title = ctk.CTkLabel(status_card, text="LIVE HARDWARE STATUS", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=COLOR_TEXT_MUTED)
        card1_title.pack(anchor="w", padx=16, pady=(12, 4))

        # Hardware Brightness visualizer
        hw_row = ctk.CTkFrame(status_card, fg_color="transparent")
        hw_row.pack(fill="x", padx=16, pady=6)

        self.lbl_hw_status = ctk.CTkLabel(hw_row, text="Current Output: Level 0 (Off)", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"))
        self.lbl_hw_status.pack(side="left")

        # Visual indicator dots (Off, Low, High)
        dots_frame = ctk.CTkFrame(hw_row, fg_color="transparent")
        dots_frame.pack(side="right")

        self.dot_off = ctk.CTkLabel(dots_frame, text="● OFF", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_ACCENT)
        self.dot_off.pack(side="left", padx=4)
        self.dot_low = ctk.CTkLabel(dots_frame, text="● LOW", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_MUTED)
        self.dot_low.pack(side="left", padx=4)
        self.dot_high = ctk.CTkLabel(dots_frame, text="● HIGH", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_MUTED)
        self.dot_high.pack(side="left", padx=4)

        # Idle progress bar
        idle_info_row = ctk.CTkFrame(status_card, fg_color="transparent")
        idle_info_row.pack(fill="x", padx=16, pady=(10, 2))

        self.lbl_idle_timer = ctk.CTkLabel(idle_info_row, text="System Idle: 0.0s / 30.0s", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_MUTED)
        self.lbl_idle_timer.pack(side="left")

        self.lbl_idle_wake_hint = ctk.CTkLabel(idle_info_row, text="Wakes on any key or mouse/trackpad movement", font=ctk.CTkFont(size=11, slant="italic"), text_color=COLOR_TEXT_MUTED)
        self.lbl_idle_wake_hint.pack(side="right")

        self.idle_progress = ctk.CTkProgressBar(status_card, fg_color="#2b2e3b", progress_color=COLOR_ACCENT, height=8, corner_radius=4)
        self.idle_progress.pack(fill="x", padx=16, pady=(4, 14))
        self.idle_progress.set(0.0)

        # ---------------- Card 2: Lighting Mode & Animation ----------------
        mode_card = ctk.CTkFrame(self.scroll, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=COLOR_CARD_BORDER)
        mode_card.pack(fill="x", pady=8, padx=4)

        card2_title = ctk.CTkLabel(mode_card, text="LIGHTING TRICKS & MODES", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=COLOR_TEXT_MUTED)
        card2_title.pack(anchor="w", padx=16, pady=(12, 8))

        mode_select_row = ctk.CTkFrame(mode_card, fg_color="transparent")
        mode_select_row.pack(fill="x", padx=16, pady=4)

        ctk.CTkLabel(mode_select_row, text="Active Effect Mode:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        self.mode_var = ctk.StringVar(value=self.config.get("effect", "Breathing"))
        self.mode_menu = ctk.CTkOptionMenu(
            mode_select_row,
            variable=self.mode_var,
            values=ALL_MODES,
            command=self._on_mode_dropdown_changed,
            fg_color="#2b2e3b",
            button_color=COLOR_ACCENT,
            button_hover_color=COLOR_ACCENT_HOVER,
            width=180
        )
        self.mode_menu.pack(side="right")

        # Speed Slider
        speed_row = ctk.CTkFrame(mode_card, fg_color="transparent")
        speed_row.pack(fill="x", padx=16, pady=(12, 4))

        self.speed_var = ctk.DoubleVar(value=float(self.config.get("speed", 0.5)))
        self.lbl_speed = ctk.CTkLabel(speed_row, text=f"Animation Speed: {self.speed_var.get():.1f}x", font=ctk.CTkFont(size=12))
        self.lbl_speed.pack(side="left")

        self.speed_slider = ctk.CTkSlider(
            mode_card,
            from_=0.3,
            to=2.5,
            number_of_steps=22,
            variable=self.speed_var,
            command=self._on_speed_slider_changed,
            progress_color=COLOR_ACCENT,
            button_color=COLOR_ACCENT,
            button_hover_color=COLOR_ACCENT_HOVER
        )
        self.speed_slider.pack(fill="x", padx=16, pady=(4, 14))

        # ---------------- Card 3: Inactivity & Power Saving ----------------
        power_card = ctk.CTkFrame(self.scroll, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=COLOR_CARD_BORDER)
        power_card.pack(fill="x", pady=8, padx=4)

        card3_title = ctk.CTkLabel(power_card, text="AUTOMATED POWER SAVING (IDLE SLEEP)", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=COLOR_TEXT_MUTED)
        card3_title.pack(anchor="w", padx=16, pady=(12, 8))

        self.power_saving_var = ctk.BooleanVar(value=self.config.get("power_saving_enabled", True))
        self.switch_power = ctk.CTkSwitch(
            power_card,
            text="Enable 30-Second Inactivity Guard",
            variable=self.power_saving_var,
            command=self._on_power_saving_toggle,
            progress_color=COLOR_ACCENT,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.switch_power.pack(anchor="w", padx=16, pady=4)

        # Timeout Slider
        timeout_row = ctk.CTkFrame(power_card, fg_color="transparent")
        timeout_row.pack(fill="x", padx=16, pady=(10, 2))

        self.timeout_var = ctk.IntVar(value=int(self.config.get("idle_timeout_seconds", 30)))
        self.lbl_timeout = ctk.CTkLabel(timeout_row, text=f"Inactivity Timeout: {self.timeout_var.get()} seconds", font=ctk.CTkFont(size=12))
        self.lbl_timeout.pack(side="left")

        self.timeout_slider = ctk.CTkSlider(
            power_card,
            from_=5,
            to=120,
            number_of_steps=23,
            variable=self.timeout_var,
            command=self._on_timeout_slider_changed,
            progress_color=COLOR_ACCENT,
            button_color=COLOR_ACCENT,
            button_hover_color=COLOR_ACCENT_HOVER
        )
        self.timeout_slider.pack(fill="x", padx=16, pady=(4, 14))

        # ---------------- Card 4: Shortcuts & Hotkeys ----------------
        shortcut_card = ctk.CTkFrame(self.scroll, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=COLOR_CARD_BORDER)
        shortcut_card.pack(fill="x", pady=8, padx=4)

        card4_title = ctk.CTkLabel(shortcut_card, text="GLOBAL SYSTEM SHORTCUT", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=COLOR_TEXT_MUTED)
        card4_title.pack(anchor="w", padx=16, pady=(12, 8))

        sc_row = ctk.CTkFrame(shortcut_card, fg_color="transparent")
        sc_row.pack(fill="x", padx=16, pady=4)

        self.shortcut_var = ctk.StringVar(value=self.config.get("shortcut", "ctrl+shift+l"))
        self.entry_shortcut = ctk.CTkEntry(sc_row, textvariable=self.shortcut_var, width=180, fg_color="#2b2e3b", border_color=COLOR_CARD_BORDER)
        self.entry_shortcut.pack(side="left", padx=(0, 10))

        self.btn_record = ctk.CTkButton(
            sc_row,
            text="● Record Keys",
            command=self._start_recording_hotkey,
            fg_color="#2b2e3b",
            hover_color="#3a3e50",
            width=120
        )
        self.btn_record.pack(side="left")

        # Shortcut Action
        action_row = ctk.CTkFrame(shortcut_card, fg_color="transparent")
        action_row.pack(fill="x", padx=16, pady=(10, 14))

        ctk.CTkLabel(action_row, text="Shortcut Action:", font=ctk.CTkFont(size=12)).pack(side="left")
        self.action_var = ctk.StringVar(value=self.config.get("shortcut_action", "toggle"))
        self.action_menu = ctk.CTkOptionMenu(
            action_row,
            variable=self.action_var,
            values=["toggle", "cycle"],
            fg_color="#2b2e3b",
            button_color=COLOR_ACCENT,
            button_hover_color=COLOR_ACCENT_HOVER,
            width=140
        )
        self.action_menu.pack(side="right")

        # ---------------- Card 5: Windows & Background Startup ----------------
        system_card = ctk.CTkFrame(self.scroll, fg_color=COLOR_CARD, corner_radius=12, border_width=1, border_color=COLOR_CARD_BORDER)
        system_card.pack(fill="x", pady=8, padx=4)

        card5_title = ctk.CTkLabel(system_card, text="SYSTEM & BACKGROUND STARTUP", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=COLOR_TEXT_MUTED)
        card5_title.pack(anchor="w", padx=16, pady=(12, 8))

        self.startup_var = ctk.BooleanVar(value=self.config.get("start_with_windows", False))
        self.switch_startup = ctk.CTkSwitch(
            system_card,
            text="Start with Windows (Auto-start in background)",
            variable=self.startup_var,
            progress_color=COLOR_ACCENT
        )
        self.switch_startup.pack(anchor="w", padx=16, pady=4)

        self.min_close_var = ctk.BooleanVar(value=self.config.get("minimize_to_tray", True))
        self.switch_min_close = ctk.CTkSwitch(
            system_card,
            text="Minimize to System Tray on close (X)",
            variable=self.min_close_var,
            progress_color=COLOR_ACCENT
        )
        self.switch_min_close.pack(anchor="w", padx=16, pady=4)

        self.min_start_var = ctk.BooleanVar(value=self.config.get("start_minimized", False))
        self.switch_min_start = ctk.CTkSwitch(
            system_card,
            text="Launch silently in background (No window on boot)",
            variable=self.min_start_var,
            progress_color=COLOR_ACCENT
        )
        self.switch_min_start.pack(anchor="w", padx=16, pady=(4, 14))

        # Bottom Action Buttons
        btn_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(12, 6), padx=4)

        self.btn_save = ctk.CTkButton(
            btn_frame,
            text="✔ Save & Apply All Settings",
            command=self._handle_save_clicked,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.btn_save.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_tray = ctk.CTkButton(
            btn_frame,
            text="Minimize to Tray",
            command=self.hide_to_tray,
            fg_color="#2b2e3b",
            hover_color="#3a3e50",
            height=40,
            width=130
        )
        self.btn_tray.pack(side="left", padx=4)

        self.btn_quit = ctk.CTkButton(
            btn_frame,
            text="Quit App",
            command=self.on_exit_app,
            fg_color="#36171a",
            hover_color=COLOR_DANGER,
            height=40,
            width=90
        )
        self.btn_quit.pack(side="left", padx=(6, 0))

        # Status label reporting save/hotkey/registry feedback
        self.lbl_save_status = ctk.CTkLabel(
            self.scroll,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MUTED
        )
        self.lbl_save_status.pack(fill="x", pady=(0, 14), padx=4)

    # ---------------- Thread-Safe UI Dispatching ----------------

    def run_on_ui_thread(self, func: Callable, *args, **kwargs):
        """Safely marshal callable execution to the Tk main thread."""
        try:
            if not self.winfo_exists():
                return
            self.after(0, lambda: self._safe_invoke(func, *args, **kwargs))
        except (Exception, ctk.TclError):
            pass

    def _safe_invoke(self, func: Callable, *args, **kwargs):
        try:
            if self.winfo_exists():
                func(*args, **kwargs)
        except (Exception, ctk.TclError):
            pass

    # ---------------- UI Event Handlers ----------------

    def _on_mode_dropdown_changed(self, choice):
        self.on_change_mode(choice)

    def _on_speed_slider_changed(self, val):
        self.lbl_speed.configure(text=f"Animation Speed: {val:.1f}x")
        self.on_change_speed(val)

    def _on_power_saving_toggle(self):
        self.on_change_power_saving(self.power_saving_var.get(), float(self.timeout_var.get()))

    def _on_timeout_slider_changed(self, val):
        val_int = int(val)
        self.lbl_timeout.configure(text=f"Inactivity Timeout: {val_int} seconds")
        self.on_change_power_saving(self.power_saving_var.get(), float(val_int))

    def _start_recording_hotkey(self):
        if self._recording_hotkey:
            return
        self._recording_hotkey = True
        self.btn_record.configure(text="Press Keys Now...", fg_color=COLOR_WARNING, hover_color=COLOR_WARNING)

        def record_thread():
            try:
                hk = keyboard.read_hotkey(suppress=False)
                if hk:
                    self.run_on_ui_thread(self.shortcut_var.set, hk)
            except Exception:
                pass
            finally:
                self._recording_hotkey = False
                self.run_on_ui_thread(
                    lambda: self.btn_record.configure(text="● Record Keys", fg_color="#2b2e3b", hover_color="#3a3e50")
                )

        threading.Thread(target=record_thread, daemon=True).start()

    def _handle_save_clicked(self):
        sc = self.shortcut_var.get().strip().lower()
        if ' ' in sc and '+' not in sc:
            sc = sc.replace(' ', '+')
            self.shortcut_var.set(sc)

        updated_config = {
            "shortcut": sc,
            "shortcut_action": self.action_var.get(),
            "effect": self.mode_var.get(),
            "speed": float(self.speed_var.get()),
            "power_saving_enabled": self.power_saving_var.get(),
            "idle_timeout_seconds": int(self.timeout_var.get()),
            "start_with_windows": self.startup_var.get(),
            "minimize_to_tray": self.min_close_var.get(),
            "start_minimized": self.min_start_var.get(),
        }
        outcome = self.on_save_config(updated_config)

        if isinstance(outcome, dict) and not outcome.get("success", True):
            errors = outcome.get("errors", ["Failed to save settings"])
            err_msg = "; ".join(errors)
            self.btn_save.configure(text="⚠ Save Issues Encountered", fg_color=COLOR_DANGER)
            self.lbl_save_status.configure(text=f"Issues: {err_msg}", text_color=COLOR_DANGER)
            self.after(5000, self._reset_save_status_ui)
        else:
            self.btn_save.configure(text="✔ Saved & Applied!", fg_color=COLOR_SUCCESS)
            self.lbl_save_status.configure(text="All settings saved to disk and applied successfully.", text_color=COLOR_SUCCESS)
            self.after(2000, self._reset_save_status_ui)

    def _reset_save_status_ui(self):
        try:
            if self.winfo_exists():
                self.btn_save.configure(text="✔ Save & Apply All Settings", fg_color=COLOR_ACCENT)
                self.lbl_save_status.configure(text="")
        except Exception:
            pass

    def _handle_window_close(self):
        if self.min_close_var.get():
            self.hide_to_tray()
        else:
            self.on_exit_app()

    def hide_to_tray(self):
        self.run_on_ui_thread(self.withdraw)

    def show_from_tray(self):
        def _show():
            self.deiconify()
            self.lift()
            self.focus_force()
        self.run_on_ui_thread(_show)

    # ---------------- Live Status Updates ----------------

    def update_hardware_level(self, level: int):
        self._current_hw_level = level
        self.run_on_ui_thread(self._render_hardware_level, level)

    def _render_hardware_level(self, level: int):
        names = {0: "Level 0 (Off)", 1: "Level 1 (Low)", 2: "Level 2 (High)"}
        self.lbl_hw_status.configure(text=f"Current Output: {names.get(level, str(level))}")

        self.dot_off.configure(text_color=COLOR_ACCENT if level == 0 else COLOR_TEXT_MUTED)
        self.dot_low.configure(text_color=COLOR_ACCENT if level == 1 else COLOR_TEXT_MUTED)
        self.dot_high.configure(text_color=COLOR_ACCENT if level == 2 else COLOR_TEXT_MUTED)

    def update_idle_status(self, idle_sec: float, is_sleeping: bool):
        self._idle_sec = idle_sec
        self._is_sleeping = is_sleeping
        self.run_on_ui_thread(self._render_idle_status, idle_sec, is_sleeping)

    def _render_idle_status(self, idle_sec: float, is_sleeping: bool):
        timeout = float(self.timeout_var.get())
        if self.power_saving_var.get():
            fraction = min(1.0, idle_sec / timeout)
            self.idle_progress.set(fraction)
            if is_sleeping:
                self.lbl_idle_timer.configure(text=f"Power Saving Active: Idle for {idle_sec:.1f}s", text_color=COLOR_WARNING)
                self.status_badge.configure(text="🌙 POWER SAVING", text_color=COLOR_WARNING, fg_color="#332410")
            else:
                remaining = max(0.0, timeout - idle_sec)
                self.lbl_idle_timer.configure(text=f"System Idle: {idle_sec:.1f}s (Sleeping in {remaining:.1f}s)", text_color=COLOR_TEXT_MUTED)
                current_mode = self.mode_var.get()
                self.status_badge.configure(text=f"● ACTIVE: {current_mode.upper()}", text_color=COLOR_SUCCESS, fg_color="#172b26")
        else:
            self.idle_progress.set(0.0)
            self.lbl_idle_timer.configure(text="Power Saving Disabled", text_color=COLOR_TEXT_MUTED)
            current_mode = self.mode_var.get()
            self.status_badge.configure(text=f"● ACTIVE: {current_mode.upper()}", text_color=COLOR_SUCCESS, fg_color="#172b26")

    def sync_external_mode_change(self, mode: str):
        """Called when mode is changed via shortcut, Fn+Space, or system tray."""
        self.run_on_ui_thread(self.mode_var.set, mode)

    def sync_power_saving_state(self, enabled: bool):
        """Called when power saving is toggled via system tray."""
        self.run_on_ui_thread(self.power_saving_var.set, enabled)
