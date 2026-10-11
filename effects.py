import threading
import time
from typing import Callable, Optional, Dict, List
from driver import LenovoDriver

ALL_MODES = [
    "Breathing",
    "Pulse",
    "Wave",
    "Police",
    "SOS",
    "Blink x3",
    "Solid High",
    "Solid Low",
    "Off"
]

class EffectEngine:
    """Continuous lighting animation engine with pause/resume and sub-millisecond responsiveness."""

    def __init__(
        self,
        driver: LenovoDriver,
        mode: str = "Breathing",
        speed: float = 0.5,
        on_level_changed: Optional[Callable[[int], None]] = None,
        on_external_override: Optional[Callable[[int], None]] = None
    ):
        self.driver = driver
        self.mode = mode if mode in ALL_MODES else "Breathing"
        self.speed = max(0.2, min(3.0, float(speed)))
        self.on_level_changed = on_level_changed
        self.on_external_override = on_external_override

        self._running = False
        self._paused = False
        self._stop_event = threading.Event()
        self._wake_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def set_mode(self, mode: str):
        if mode not in ALL_MODES:
            return
        with self._lock:
            self.mode = mode
        # Wake up any waiting sleeps so mode takes effect instantly
        self._wake_event.set()

    def get_mode(self) -> str:
        with self._lock:
            return self.mode

    def set_speed(self, speed: float):
        with self._lock:
            self.speed = max(0.2, min(3.0, float(speed)))

    def get_speed(self) -> float:
        with self._lock:
            return self.speed

    def set_paused(self, paused: bool):
        with self._lock:
            if self._paused == paused:
                return
            self._paused = paused

        if paused:
            # Turn backlight off once for power saving
            self._set_hardware_level(0, force=True)
        else:
            self._wake_event.set()

    def is_paused(self) -> bool:
        with self._lock:
            return self._paused

    def start(self):
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._wake_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="EffectEngineThread", daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self._stop_event.set()
        self._wake_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

    def _sleep_interruptible(self, seconds: float) -> bool:
        """Sleep that can be interrupted immediately when mode changes, engine stops, or user presses Fn+Space."""
        with self._lock:
            spd = self.speed
        actual_sleep = seconds / spd
        end_time = time.time() + actual_sleep

        while time.time() < end_time:
            if self._stop_event.is_set():
                return False
            if self._wake_event.is_set():
                self._wake_event.clear()
                return False

            # Check if user manually changed backlight on laptop (Fn+Space or Vantage)
            ext_level = self.driver.check_external_hardware_change()
            if ext_level is not None:
                if self.on_external_override:
                    try:
                        self.on_external_override(ext_level)
                    except Exception:
                        pass
                return False

            time.sleep(min(0.02, end_time - time.time()))
        return True

    def _set_hardware_level(self, level: int, force: bool = False):
        if not force and self.driver.current_level == level:
            return
        self.driver.set_level(level)
        if self.on_level_changed:
            try:
                self.on_level_changed(level)
            except Exception:
                pass

    def _wait_for_change(self):
        """Wait while idle in static modes, checking for external hardware changes or mode switches."""
        if self._wake_event.wait(timeout=0.10):
            self._wake_event.clear()
            return

        ext_level = self.driver.check_external_hardware_change()
        if ext_level is not None:
            if self.on_external_override:
                try:
                    self.on_external_override(ext_level)
                except Exception:
                    pass

    def _run_loop(self):
        while not self._stop_event.is_set():
            if self._paused:
                self._wake_event.wait(timeout=0.20)
                self._wake_event.clear()
                continue

            with self._lock:
                current_mode = self.mode

            if current_mode == "Solid High":
                self._set_hardware_level(2)
                self._wait_for_change()
            elif current_mode == "Solid Low":
                self._set_hardware_level(1)
                self._wait_for_change()
            elif current_mode == "Off":
                self._set_hardware_level(0)
                self._wait_for_change()
            elif current_mode == "Breathing":
                self._step_sequence([
                    (0, 0.40),
                    (1, 0.35),
                    (2, 0.85),
                    (1, 0.35),
                    (0, 0.50)
                ])
            elif current_mode == "Pulse":
                self._step_sequence([
                    (1, 0.12),
                    (2, 0.20),
                    (0, 0.12),
                    (1, 0.12),
                    (2, 0.25),
                    (0, 0.60)
                ])
            elif current_mode == "Wave":
                self._step_sequence([
                    (0, 0.18),
                    (1, 0.22),
                    (2, 0.30),
                    (1, 0.22),
                    (0, 0.30)
                ])
            elif current_mode == "Police":
                self._step_sequence([
                    (2, 0.06), (0, 0.06),
                    (2, 0.06), (0, 0.06),
                    (2, 0.06), (0, 0.20),
                    (1, 0.06), (0, 0.06),
                    (1, 0.06), (0, 0.06),
                    (1, 0.06), (0, 0.30)
                ])
            elif current_mode == "SOS":
                # . . .  - - -  . . .
                seq = []
                # 3 short
                for _ in range(3):
                    seq.extend([(2, 0.14), (0, 0.12)])
                seq.append((0, 0.18))
                # 3 long
                for _ in range(3):
                    seq.extend([(2, 0.40), (0, 0.15)])
                seq.append((0, 0.18))
                # 3 short
                for _ in range(3):
                    seq.extend([(2, 0.14), (0, 0.12)])
                seq.append((0, 0.9))
                self._step_sequence(seq)
            elif current_mode == "Blink x3":
                self._step_sequence([
                    (2, 0.20), (0, 0.18),
                    (2, 0.20), (0, 0.18),
                    (2, 0.20), (0, 0.7)
                ])
            else:
                time.sleep(0.05)

    def _step_sequence(self, steps: List[tuple]):
        """Execute a list of (level, duration_seconds) steps, aborting immediately if interrupted or overridden."""
        for level, duration in steps:
            if self._stop_event.is_set() or self._paused:
                break

            # Check if user touched Fn+Space before next step
            ext_level = self.driver.check_external_hardware_change()
            if ext_level is not None:
                if self.on_external_override:
                    try:
                        self.on_external_override(ext_level)
                    except Exception:
                        pass
                break

            self._set_hardware_level(level, force=True)
            if not self._sleep_interruptible(duration):
                break
