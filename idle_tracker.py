import ctypes
import threading
import time
from typing import Callable, Optional

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]

def get_system_idle_seconds() -> float:
    """Returns elapsed seconds since any keyboard, mouse, or trackpad interaction."""
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
        tick = ctypes.windll.kernel32.GetTickCount()
        # Handle uint32 wrap-around safely
        elapsed_ms = (tick - lii.dwTime) & 0xFFFFFFFF
        return elapsed_ms / 1000.0
    return 0.0

class IdleMonitor:
    """Background monitor for system-wide keyboard, mouse, and trackpad inactivity."""

    def __init__(
        self,
        timeout_seconds: float = 30.0,
        enabled: bool = True,
        on_idle: Optional[Callable[[], None]] = None,
        on_wake: Optional[Callable[[], None]] = None,
        on_tick: Optional[Callable[[float], None]] = None,
        poll_interval: float = 0.1
    ):
        self.timeout_seconds = max(1.0, float(timeout_seconds))
        self.enabled = enabled
        self.on_idle = on_idle
        self.on_wake = on_wake
        self.on_tick = on_tick
        self.poll_interval = poll_interval

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._is_sleeping = False
        self._lock = threading.Lock()

    def set_timeout(self, seconds: float):
        with self._lock:
            self.timeout_seconds = max(1.0, float(seconds))

    def set_enabled(self, enabled: bool):
        should_wake = False
        with self._lock:
            self.enabled = enabled
            if not enabled and self._is_sleeping:
                self._is_sleeping = False
                should_wake = True
        if should_wake and self.on_wake:
            try:
                self.on_wake()
            except Exception:
                pass

    def is_sleeping(self) -> bool:
        with self._lock:
            return self._is_sleeping

    def wake(self):
        """Force wake from sleep (e.g. when user triggers hardware shortcut like Fn+Space)."""
        should_wake = False
        with self._lock:
            if self._is_sleeping:
                self._is_sleeping = False
                should_wake = True
        if should_wake and self.on_wake:
            try:
                self.on_wake()
            except Exception:
                pass

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, name="IdleMonitorThread", daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

    def _run_loop(self):
        while self._running:
            try:
                idle_sec = get_system_idle_seconds()

                if self.on_tick:
                    try:
                        self.on_tick(idle_sec)
                    except Exception:
                        pass

                with self._lock:
                    enabled = self.enabled
                    timeout = self.timeout_seconds
                    was_sleeping = self._is_sleeping

                action = None
                if enabled:
                    if not was_sleeping and idle_sec >= timeout:
                        with self._lock:
                            if not self._is_sleeping:
                                self._is_sleeping = True
                                action = "idle"
                    elif was_sleeping and idle_sec < 0.5:
                        with self._lock:
                            if self._is_sleeping:
                                self._is_sleeping = False
                                action = "wake"
                else:
                    if was_sleeping:
                        with self._lock:
                            if self._is_sleeping:
                                self._is_sleeping = False
                                action = "wake"

                # Invoke callbacks outside the monitor lock
                if action == "idle" and self.on_idle:
                    try:
                        self.on_idle()
                    except Exception:
                        pass
                elif action == "wake" and self.on_wake:
                    try:
                        self.on_wake()
                    except Exception:
                        pass

            except Exception:
                pass

            time.sleep(self.poll_interval)
