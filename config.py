import json
import os
import sys
import winreg

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_config_dir():
    """Return user configuration directory in %APPDATA%/LenovoLOQBacklightCustomizer."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        cfg_dir = os.path.join(appdata, "LenovoLOQBacklightCustomizer")
    else:
        cfg_dir = BASE_DIR
    return cfg_dir

def get_default_config_path():
    """Return default configuration path in user AppData folder."""
    return os.path.join(get_config_dir(), "backlight_config.json")

CONFIG_PATH = get_default_config_path()
APP_REG_NAME = "LenovoLOQBacklightCustomizer"

DEFAULT_CONFIG = {
    "shortcut": "ctrl+shift+l",
    "shortcut_action": "toggle", # "toggle" or "cycle"
    "effect": "Breathing",
    "speed": 0.5,
    "power_saving_enabled": True,
    "idle_timeout_seconds": 30,
    "start_with_windows": False,
    "start_minimized": False,
    "minimize_to_tray": True
}

def migrate_legacy_config():
    """Migrate legacy config from BASE_DIR to AppData CONFIG_PATH if present and not already migrated."""
    if not os.path.exists(CONFIG_PATH):
        local_candidate = os.path.join(BASE_DIR, "backlight_config.json")
        if os.path.exists(local_candidate) and os.path.abspath(local_candidate) != os.path.abspath(CONFIG_PATH):
            try:
                with open(local_candidate, "r", encoding="utf-8") as f:
                    data = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(data)
                save_config(config)
                return True
            except Exception as e:
                print(f"[Config] Migration error from local file: {e}")
    return False

def load_config():
    """Load configuration from disk with fallback to defaults; auto-creates if missing."""
    if not os.path.exists(CONFIG_PATH):
        if CONFIG_PATH == get_default_config_path():
            if migrate_legacy_config() and os.path.exists(CONFIG_PATH):
                return load_config()
        cfg = DEFAULT_CONFIG.copy()
        save_config(cfg)
        return cfg
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge with defaults for any missing keys
        config = DEFAULT_CONFIG.copy()
        config.update(data)
        return config
    except Exception as e:
        print(f"[Config] Error loading config: {e}. Using defaults.")
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to disk."""
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"[Config] Error saving config: {e}")
        return False

def is_startup_enabled():
    """Check if app is configured in Windows Run registry key."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        try:
            val, _ = winreg.QueryValueEx(key, APP_REG_NAME)
            winreg.CloseKey(key)
            return bool(val)
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False

def set_startup_enabled(enable: bool):
    """Register or unregister app in Windows Run registry key."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enable:
            if getattr(sys, "frozen", False):
                cmd = f'"{sys.executable}" --minimized'
            else:
                pythonw_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
                if not os.path.exists(pythonw_path):
                    pythonw_path = sys.executable
                main_script = os.path.join(BASE_DIR, "Lenovo_LOQ_Backlight_Customizer.py")
                cmd = f'"{pythonw_path}" "{main_script}" --minimized'
            winreg.SetValueEx(key, APP_REG_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_REG_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"[Config] Error setting startup registry: {e}")
        return False
