import ctypes
from ctypes import wintypes
import struct
import threading
import atexit
import time
import logging
from typing import Optional

logger = logging.getLogger("LenovoDriver")

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 3
FILE_SHARE_READ = 1
FILE_SHARE_WRITE = 2

IOCTL_LENOVO_BACKLIGHT = 0x83102144
CMD_GET_STATUS = 0x32

VAL_OFF = 0x00000033
VAL_LOW = 0x00010033
VAL_HIGH = 0x00020033

STATUS_MAP = {
    0x00000001: 0,
    0x00010001: 0,
    0x00000003: 1,
    0x00010003: 1,
    0x00000005: 2,
    0x00010005: 2,
}

LEVEL_TO_VAL = {
    0: VAL_OFF,
    1: VAL_LOW,
    2: VAL_HIGH
}

# Explicit Win32 API function signatures
kernel32 = ctypes.windll.kernel32

INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

kernel32.CreateFileW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE
]
kernel32.CreateFileW.restype = wintypes.HANDLE

kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

kernel32.DeviceIoControl.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPVOID
]
kernel32.DeviceIoControl.restype = wintypes.BOOL

kernel32.GetLastError.argtypes = []
kernel32.GetLastError.restype = wintypes.DWORD

def _is_valid_handle(handle) -> bool:
    """Check if handle is non-null and not INVALID_HANDLE_VALUE."""
    if handle is None or handle == 0:
        return False
    if handle == -1 or handle == INVALID_HANDLE_VALUE:
        return False
    return True


class LenovoDriver:
    """Safe, thread-safe interface to the Lenovo EnergyDrv ACPI backlight driver."""

    def __init__(self, driver_path="\\\\.\\EnergyDrv", mock: bool = False):
        self.driver_path = driver_path
        self.mock = mock
        self.handle = None
        self._lock = threading.Lock()
        self.initial_level = None
        self.current_level = 0
        self.mock_hardware_level = 0
        self.last_set_level = None
        self.last_set_timestamp = 0.0

        if not self.mock:
            self._connect()
            self.initial_level = self.get_level()
            self.current_level = self.initial_level
            self.last_set_level = self.initial_level
            self.last_set_timestamp = time.time()
            atexit.register(self.restore_initial)

    def _is_connected_locked(self) -> bool:
        if self.mock:
            return True
        return _is_valid_handle(self.handle)

    def is_connected(self) -> bool:
        if self.mock:
            return True
        with self._lock:
            return self._is_connected_locked()

    def _connect_locked(self) -> bool:
        """Internal helper to connect to driver. Assumes self._lock is already held."""
        if _is_valid_handle(self.handle):
            try:
                kernel32.CloseHandle(self.handle)
            except Exception:
                pass
            self.handle = None

        h = kernel32.CreateFileW(
            self.driver_path,
            GENERIC_READ | GENERIC_WRITE,
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            None,
            OPEN_EXISTING,
            0,
            None
        )
        if not _is_valid_handle(h):
            err = kernel32.GetLastError()
            logger.debug("CreateFileW failed for %s (error code: %d)", self.driver_path, err)
            self.handle = None
            return False

        self.handle = h
        return True

    def _connect(self) -> bool:
        """Public connect wrapper that acquires self._lock."""
        with self._lock:
            return self._connect_locked()

    def get_raw_status(self) -> Optional[int]:
        """Query raw uint32 status code from driver."""
        if self.mock:
            lvl = getattr(self, "mock_hardware_level", self.current_level)
            return 0x00010001 if lvl == 0 else (0x00010003 if lvl == 1 else 0x00010005)

        with self._lock:
            if not self._is_connected_locked():
                if not self._connect_locked():
                    return None

            in_buf = struct.pack("<I", CMD_GET_STATUS)
            out_buf = ctypes.create_string_buffer(16)
            bytes_ret = wintypes.DWORD()

            res = kernel32.DeviceIoControl(
                self.handle,
                IOCTL_LENOVO_BACKLIGHT,
                in_buf, len(in_buf),
                out_buf, len(out_buf),
                ctypes.byref(bytes_ret),
                None
            )
            if not res or bytes_ret.value < 4:
                err = kernel32.GetLastError()
                logger.debug("DeviceIoControl get_raw_status failed (error code: %d)", err)
                if err in (6, 1167):  # ERROR_INVALID_HANDLE, ERROR_DEVICE_NOT_CONNECTED
                    if _is_valid_handle(self.handle):
                        try:
                            kernel32.CloseHandle(self.handle)
                        except Exception:
                            pass
                    self.handle = None
                return None

            raw_val = struct.unpack("<I", out_buf.raw[:4])[0]
            if raw_val not in STATUS_MAP:
                logger.warning("Unrecognized raw status code from EnergyDrv: 0x%08X", raw_val)
            return raw_val

    def get_level(self) -> int:
        """Returns backlight level: 0 (Off), 1 (Low), 2 (High)."""
        raw = self.get_raw_status()
        if raw is not None and raw in STATUS_MAP:
            return STATUS_MAP[raw]
        return self.current_level

    def set_level(self, level: int) -> bool:
        """Set backlight level safely (0 = Off, 1 = Low, 2 = High)."""
        level = max(0, min(2, int(level)))
        val = LEVEL_TO_VAL[level]

        if self.mock:
            self.current_level = level
            self.mock_hardware_level = level
            self.last_set_level = level
            self.last_set_timestamp = time.time()
            return True

        with self._lock:
            if not self._is_connected_locked():
                if not self._connect_locked():
                    return False

            in_buf = struct.pack("<I", val)
            out_buf = ctypes.create_string_buffer(16)
            bytes_ret = wintypes.DWORD()

            res = kernel32.DeviceIoControl(
                self.handle,
                IOCTL_LENOVO_BACKLIGHT,
                in_buf, len(in_buf),
                out_buf, len(out_buf),
                ctypes.byref(bytes_ret),
                None
            )
            if res:
                self.current_level = level
                self.last_set_level = level
                self.last_set_timestamp = time.time()
                return True
            else:
                err = kernel32.GetLastError()
                logger.debug("DeviceIoControl set_level failed (error code: %d)", err)
                if err in (6, 1167):  # ERROR_INVALID_HANDLE, ERROR_DEVICE_NOT_CONNECTED
                    if _is_valid_handle(self.handle):
                        try:
                            kernel32.CloseHandle(self.handle)
                        except Exception:
                            pass
                    self.handle = None
                return False

    def check_external_hardware_change(self) -> Optional[int]:
        """Poll the actual hardware to check if an external control (e.g. Fn+Space or Lenovo Vantage) changed the backlight."""
        raw = self.get_raw_status()
        if raw is None or raw not in STATUS_MAP:
            return None

        actual_level = STATUS_MAP[raw]
        with self._lock:
            if actual_level != self.current_level:
                # If actual differs from what we think it is, and we didn't just command it
                if time.time() - self.last_set_timestamp > 0.05:
                    self.current_level = actual_level
                    self.last_set_level = actual_level
                    return actual_level
        return None

    def restore_initial(self):
        """Restore initial brightness on application shutdown."""
        lvl = self.initial_level
        self.initial_level = None
        if lvl is not None:
            try:
                self.set_level(lvl)
            except Exception:
                pass

    def close(self):
        """Close driver handle."""
        self.restore_initial()
        with self._lock:
            if _is_valid_handle(self.handle):
                try:
                    kernel32.CloseHandle(self.handle)
                except Exception:
                    pass
            self.handle = None
