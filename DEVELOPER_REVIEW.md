# Developer Review: Lenovo LOQ Keyboard Backlight Customizer

**Review date:** 2026-10-08  
**Scope:** Static review of the Python source, checked-in configuration, launcher, README, and tests. No tests were run and no commands were sent to the physical keyboard. The packaged executable was not inspected.

## Executive summary

The project has a useful separation of responsibilities: `BacklightApplication` coordinates the app, `EffectEngine` generates lighting patterns, `LenovoDriver` wraps the Lenovo device interface, `IdleMonitor` handles inactivity, and separate GUI/tray modules provide controls. The main risks are in the boundaries between these components:

1. Driver reconnection can self-deadlock because a non-reentrant lock is acquired recursively.
2. Two idle-monitor methods call app callbacks while holding the monitor lock; the wake callback asks the monitor for its state and can deadlock.
3. Several Tk operations are reached from background and hotkey/tray threads instead of being marshalled onto the Tk main loop.
4. Windows API signatures are not declared, so 64-bit handle correctness and argument conversion are not reliable.

These are worth addressing before relying on unattended use. In addition, configuration/save failures are hidden from the user, and the checked-in runtime configuration differs materially from the defaults and README.

## Findings and recommended fixes

### 1. Driver reconnect deadlocks while holding its lock — Critical

**Location:** [driver.py](D:/Coding/keyboard_backlit_customizer/driver.py:85), especially lines 91–94 and 131–134; `_connect()` acquires the same lock at lines 60–61.

**Context:** `get_raw_status()` and `set_level()` enter `with self._lock`. When `is_connected()` returns false, both call `_connect()`, which also enters `with self._lock`. The lock is a standard `threading.Lock`, not an `RLock`, so the same thread blocks waiting for a lock it already owns. This path is reachable after a failed initial open or after `set_level()` clears `self.handle` for an invalid/disconnected device.

**Impact:** Hardware reads or writes can hang permanently during device loss/recovery. Because the effect engine and the hardware sync watcher both use the driver, one stuck call can also stall lighting and synchronization.

**Recommended fix:** Make lock ownership explicit. Prefer a private `_connect_locked()` helper that assumes the lock is already held, and a public/internal `_connect()` wrapper that acquires it, or restructure callers to decide/connect without nesting. Do not just switch to `RLock` without reviewing all handle lifecycle paths; a helper makes the locking contract clearer. Treat `INVALID_HANDLE_VALUE` consistently and avoid leaving stale handles open.

**Acceptance criteria:** With a simulated disconnected/invalid handle, concurrent `get_raw_status()` and `set_level()` calls return or fail within a bounded time; neither deadlocks. Reconnect attempts do not leak handles.

### 2. Idle callbacks can deadlock on re-entrant state reads — Critical

**Location:** [idle_tracker.py](D:/Coding/keyboard_backlit_customizer/idle_tracker.py:51) (`set_enabled`) and lines 63–69 (`wake`); callback path in [Lenovo_LOQ_Backlight_Customizer.py](D:/Coding/keyboard_backlit_customizer/Lenovo_LOQ_Backlight_Customizer.py:233).

**Context:** `set_enabled()` and `wake()` call `on_wake` while holding `IdleMonitor._lock`. The app’s `_on_system_wake()` calls `tray.update_status(..., is_sleeping=False)`, and application paths that query state use `idle_monitor.is_sleeping()`, which attempts to take the same non-reentrant lock. Calling callbacks under a component’s internal lock also makes lock ordering depend on tray/engine implementation details.

**Impact:** Turning off power saving while the app is sleeping, or forcing a wake after a hardware key action, can freeze the calling thread. In the tray callback path, that can also make the tray appear unresponsive.

**Recommended fix:** Under the lock, update state and record whether a transition occurred. Release the lock, then invoke the callback. Apply the same pattern consistently in all transition paths. Add a small helper to centralize state transitions if that makes duplicate callbacks less likely.

**Acceptance criteria:** Calling `wake()` or disabling monitoring while sleeping completes promptly; `on_wake` runs once per transition and can safely call `is_sleeping()`.

### 3. Tk widgets are modified outside the Tk event loop — High

**Location:** [gui.py](D:/Coding/keyboard_backlit_customizer/gui.py:440) (`sync_external_mode_change`), lines 397–400 (`show_from_tray`), and [Lenovo_LOQ_Backlight_Customizer.py](D:/Coding/keyboard_backlit_customizer/Lenovo_LOQ_Backlight_Customizer.py:93), lines 170–188, and 203–224.

**Context:** Tray callbacks run on the tray library’s thread, global hotkey callbacks run through the `keyboard` package, and external hardware updates may run on either the effect thread or `_hardware_sync_loop`. These paths call `set_mode()` and/or `show_ui()`, which directly call `mode_var.set()`, `deiconify()`, `lift()`, and `focus_force()`. `update_hardware_level()` and `update_idle_status()` already schedule rendering with `after()`, but `sync_external_mode_change()` does not. `toggle_power_saving()` also directly sets `power_saving_var`.

**Impact:** Tkinter is not generally safe for arbitrary cross-thread widget access. Symptoms can include intermittent `RuntimeError`/Tcl errors, missed updates, hangs during shutdown, or UI instability that is hard to reproduce.

**Recommended fix:** Establish one UI-thread dispatch method, such as a queue drained by a recurring `after()` callback or a guarded `call_on_ui_thread()` wrapper. Route every widget operation and window show/hide action through it. Keep controller/model updates thread-safe and separate from widget updates. Ensure queued work is discarded safely once the root window is closing.

**Acceptance criteria:** Tray mode changes, hotkeys, Fn+Space synchronization, idle/wake transitions, and reopening the dashboard update the UI without calling widget methods from worker threads. Repeated close/reopen/shutdown does not produce Tcl exceptions.

### 4. Windows API function signatures are implicit — High

**Location:** [driver.py](D:/Coding/keyboard_backlit_customizer/driver.py:50), `_connect()` at lines 60–78, and DeviceIoControl calls at lines 100–107 and 140–146.

**Context:** The code calls `ctypes.windll.kernel32` functions without setting `argtypes` or `restype`. In ctypes, undeclared functions default to a C `int` return type. `CreateFileW` returns a pointer-sized `HANDLE`; on 64-bit Python, treating it as a 32-bit integer can truncate it. Explicit signatures are also needed to ensure pointer and buffer arguments are passed with the expected widths. The code checks `handle != -1`, while the native API sentinel is `INVALID_HANDLE_VALUE` (all bits set for the pointer width).

**Impact:** Driver open and IOCTL operations may fail unpredictably or treat an invalid/truncated handle as valid, particularly on 64-bit Windows.

**Recommended fix:** Declare exact ctypes signatures for every Win32 function used (`CreateFileW`, `CloseHandle`, `DeviceIoControl`, and any error retrieval function). Use `wintypes.HANDLE`, `DWORD`, `BOOL`, and pointer types as appropriate; compare against `INVALID_HANDLE_VALUE` in pointer width. Capture `GetLastError()` immediately after a failed API call and report the numeric error in diagnostics.

**Acceptance criteria:** On supported 64-bit Windows, opened handles survive round-trip use by `DeviceIoControl`, failed opens are recognized reliably, and close/reconnect paths use the same typed handle representation.

### 5. Save and startup-registration failures are silently reported as success — Medium

**Location:** [config.py](D:/Coding/keyboard_backlit_customizer/config.py:29) and `set_startup_enabled()` at lines 62–89; callers at [Lenovo_LOQ_Backlight_Customizer.py](D:/Coding/keyboard_backlit_customizer/Lenovo_LOQ_Backlight_Customizer.py:127) and 139–143; UI success status in [gui.py](D:/Coding/keyboard_backlit_customizer/gui.py:367).

**Context:** `save_config()` and `set_startup_enabled()` return success/failure values, but the controller ignores them. The UI displays “Saved & Applied!” after the callback returns even if writing the JSON file or updating the Run registry value failed. Hotkey registration failures are printed but do not surface in the UI.

**Impact:** Users can believe settings persisted or startup was enabled when the next launch will not reflect that state. Troubleshooting is difficult, especially when launched with `pythonw.exe` or the packaged GUI executable, where console output is not visible.

**Recommended fix:** Have the save/apply operation collect per-operation results and return a structured outcome to the GUI. Show success only when required writes succeed; otherwise show which setting failed and retain or restore the displayed value as appropriate. Add a user-accessible log file or diagnostic view instead of relying only on `print()`.

**Acceptance criteria:** Simulated config-write, registry-write, and hotkey-registration failures are visible to the user and are not presented as a complete save success.

### 6. Checked-in active configuration conflicts with documented defaults — Medium

**Location:** [backlight_config.json](D:/Coding/keyboard_backlit_customizer/backlight_config.json) versus [config.py](D:/Coding/keyboard_backlit_customizer/config.py:13) and [README.md](D:/Coding/keyboard_backlit_customizer/README.md).

**Context:** The checked-in JSON selects `Off`, sets a 5-second timeout, enables startup, and starts minimized. `DEFAULT_CONFIG` uses `Breathing`, a 30-second timeout, and disables startup/minimized launch. The README also describes 30 seconds as the default and presents a dashboard-first first launch. Because the config file sits beside the source/executable and is loaded at startup, it is the effective configuration for this checkout/distribution when present.

**Impact:** First launch can appear broken or surprising (starts hidden with lighting off), may activate at Windows login, and does not match the advertised default behavior.

**Recommended fix:** Decide which behavior is intended for a clean install. If the JSON is user/runtime state, do not ship a personalized state file; generate it from defaults on first run and keep local user config out of release packaging. If the checked-in values are intentional, update the README and document the startup/minimized behavior. Avoid silently changing existing users’ preferences during this cleanup.

**Acceptance criteria:** A clean install has a predictable, documented first-run state; existing user settings remain preserved across upgrades.

### 7. Hardware claims and support boundaries need verification — Medium

**Location:** [README.md](D:/Coding/keyboard_backlit_customizer/README.md), especially the “two-way synchronization” and “100% Hardware Safe” claims; protocol constants and status map in [driver.py](D:/Coding/keyboard_backlit_customizer/driver.py:12).

**Context:** The source contains a fixed IOCTL value, command values, accepted status values, and comments identifying an EnergyDrv interface. This review did not validate those values against official Lenovo documentation, the target laptop, or driver versions. The README makes broad compatibility and safety statements that are stronger than the evidence available from source inspection alone.

**Impact:** Unsupported Lenovo models, driver versions, or status encodings could fail without a useful explanation. A failed `DeviceIoControl` currently generally becomes `None`/`False`, while the UI does not clearly distinguish unsupported hardware from transient I/O errors.

**Recommended fix:** Document the tested model/OS/driver combinations and the exact supported assumptions. Validate each IOCTL and status encoding on the intended models, and handle unknown status codes explicitly (report unsupported/unknown rather than silently mapping or falling back). Replace absolute safety/compatibility claims with scoped, evidence-based wording. Keep the original brightness restoration behavior and verify it on normal shutdown and failure paths.

**Acceptance criteria:** Release notes identify verified hardware/software combinations; unknown status and driver failures are diagnosable; the README’s claims match tested behavior.

## Suggested implementation order

1. Fix driver lock ownership and Win32 ctypes signatures together; the driver path is the hardware boundary.
2. Move idle callbacks outside locks and add transition-level coverage.
3. Add a single UI-thread dispatch mechanism and route all cross-thread UI actions through it.
4. Make persistence/startup/hotkey errors visible and reconcile the checked-in config with first-run documentation.
5. Validate IOCTL/status behavior and revise compatibility claims based on actual supported hardware.

## Verification plan for the developer

The following are proposed checks; they were not run as part of this static review.

- Add deterministic mock tests for disconnected-driver reconnection, asserting operations complete under a short timeout.
- Add idle-monitor tests where `on_wake` calls `is_sleeping()`, including `wake()` and `set_enabled(False)` while sleeping.
- Add a UI-dispatch test or manual stress pass that issues mode changes from simulated tray, hotkey, idle, and sync worker threads.
- Run driver integration checks only on explicitly supported Lenovo hardware, first capturing the current hardware level and confirming restoration after shutdown.
- Test settings persistence and registry failure paths with mocked failures; verify the UI reports partial failure.
- Validate a clean-install run separately from an upgrade with an existing user config.

## Review limitations

This is a static source review. The exact EnergyDrv protocol, target-model compatibility, actual Windows API behavior on the intended systems, and correspondence between the Python source and the 32 MB packaged executable remain unverified. Tests were not run, and the physical keyboard was not modified.
