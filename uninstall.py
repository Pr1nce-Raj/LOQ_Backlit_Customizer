import os
import sys
import time
import shutil
import winreg
import argparse
import subprocess
from typing import Optional

APP_NAME = "Lenovo LOQ Backlight Customizer"
APP_REG_NAME = "LenovoLOQBacklightCustomizer"
EXE_NAME = "Lenovo_LOQ_Backlight_Customizer.exe"

COLOR_BG = "#121317"
COLOR_CARD = "#1a1c23"
COLOR_CARD_BORDER = "#2b2e3b"
COLOR_ACCENT = "#00b4d8"
COLOR_ACCENT_HOVER = "#0096c7"
COLOR_DANGER = "#e71d36"
COLOR_DANGER_HOVER = "#c1121f"
COLOR_TEXT_MUTED = "#8d99ae"


def kill_running_processes() -> bool:
    """Terminate any running instances of Lenovo_LOQ_Backlight_Customizer.exe."""
    try:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        subprocess.run(
            ["taskkill", "/f", "/im", EXE_NAME],
            capture_output=True,
            creationflags=flags
        )
        time.sleep(0.5)
        return True
    except Exception as e:
        print(f"[Uninstall] Note: Process kill error: {e}")
        return False


def remove_run_registry_entry() -> bool:
    """Remove application from Windows Startup Run registry."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(key, APP_REG_NAME)
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"[Uninstall] Note: Run registry removal error: {e}")
        return False


def remove_uninstall_registry_entry() -> bool:
    """Remove application entry from Windows Installed Apps / Control Panel registry."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteKey(key, APP_REG_NAME)
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"[Uninstall] Note: Uninstall registry removal error: {e}")
        return False


def remove_shortcuts() -> bool:
    """Remove Desktop and Start Menu shortcuts (under Tools and legacy folder)."""
    success = True
    appdata = os.environ.get("APPDATA")
    if appdata:
        # 1. Clean shortcuts under Programs\Tools
        tools_dir = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Tools")
        for lnk_name in [f"{APP_NAME}.lnk", f"Uninstall {APP_NAME}.lnk"]:
            lnk_path = os.path.join(tools_dir, lnk_name)
            if os.path.exists(lnk_path):
                try:
                    os.remove(lnk_path)
                except Exception as e:
                    print(f"[Uninstall] Error removing Start Menu link {lnk_name}: {e}")
                    success = False
        # If Tools folder is empty, cleanly remove it
        if os.path.exists(tools_dir):
            try:
                if not os.listdir(tools_dir):
                    os.rmdir(tools_dir)
            except Exception:
                pass

        # 2. Also remove legacy folder Programs\Lenovo LOQ Backlight Customizer if present
        legacy_folder = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Lenovo LOQ Backlight Customizer")
        if os.path.exists(legacy_folder):
            try:
                shutil.rmtree(legacy_folder, ignore_errors=True)
            except Exception as e:
                print(f"[Uninstall] Error removing legacy Start Menu folder: {e}")
                success = False

    # Desktop shortcut
    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        desktop_shortcut = os.path.join(userprofile, "Desktop", f"{APP_NAME}.lnk")
        if os.path.exists(desktop_shortcut):
            try:
                os.remove(desktop_shortcut)
            except Exception as e:
                print(f"[Uninstall] Error removing Desktop shortcut: {e}")
                success = False

    return success


def remove_user_data() -> bool:
    """Remove %APPDATA%/LenovoLOQBacklightCustomizer configuration and logs."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        data_dir = os.path.join(appdata, "LenovoLOQBacklightCustomizer")
        if os.path.exists(data_dir):
            try:
                shutil.rmtree(data_dir, ignore_errors=True)
                return True
            except Exception as e:
                print(f"[Uninstall] Error removing user data: {e}")
                return False
    return True


def remove_install_directory(install_dir: str) -> bool:
    """Delete all files inside install_dir and the directory itself."""
    if not os.path.exists(install_dir):
        return True
    try:
        # Retry with slight delays in case Windows takes a moment to release file handles
        for _ in range(5):
            try:
                shutil.rmtree(install_dir, ignore_errors=False)
                break
            except Exception:
                time.sleep(0.4)
        if os.path.exists(install_dir):
            shutil.rmtree(install_dir, ignore_errors=True)
        return not os.path.exists(install_dir)
    except Exception as e:
        print(f"[Uninstall] Error deleting install dir: {e}")
        return False


def perform_uninstall(install_dir: str, purge_data: bool = False) -> bool:
    """Execute complete uninstallation pipeline."""
    kill_running_processes()
    remove_run_registry_entry()
    remove_uninstall_registry_entry()
    remove_shortcuts()
    if purge_data:
        remove_user_data()
    if install_dir and os.path.exists(install_dir):
        remove_install_directory(install_dir)
    return True


def run_gui(install_dir: str):
    """Launch modern CustomTkinter uninstallation dialog."""
    import customtkinter as ctk

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Uninstall Lenovo LOQ Backlight Customizer")
    root.geometry("520x360")
    root.resizable(False, False)
    root.configure(fg_color=COLOR_BG)

    # Set window icon if available
    icon_path = os.path.join(install_dir, "app_icon.ico")
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        temp_icon = os.path.join(sys._MEIPASS, "app_icon.ico")
        if os.path.exists(temp_icon):
            icon_path = temp_icon
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass

    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() - 520) // 2
    y = (root.winfo_screenheight() - 360) // 2
    root.geometry(f"+{x}+{y}")

    # Main Card
    card = ctk.CTkFrame(
        root,
        fg_color=COLOR_CARD,
        border_color=COLOR_CARD_BORDER,
        border_width=1,
        corner_radius=12
    )
    card.pack(fill="both", expand=True, padx=20, pady=20)

    title_label = ctk.CTkLabel(
        card,
        text="Uninstall Lenovo LOQ Backlight Customizer",
        font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
        text_color="#ffffff"
    )
    title_label.pack(pady=(24, 8), padx=20, anchor="w")

    desc_label = ctk.CTkLabel(
        card,
        text="This will remove Lenovo LOQ Backlight Customizer from your system,\nincluding application files, Start Menu entries, and shortcuts.",
        font=ctk.CTkFont(family="Segoe UI", size=13),
        text_color=COLOR_TEXT_MUTED,
        justify="left"
    )
    desc_label.pack(pady=(0, 16), padx=20, anchor="w")

    loc_label = ctk.CTkLabel(
        card,
        text=f"Location: {install_dir}",
        font=ctk.CTkFont(family="Consolas", size=11),
        text_color="#64748b",
        anchor="w"
    )
    loc_label.pack(pady=(0, 16), padx=20, anchor="w")

    purge_var = ctk.BooleanVar(value=False)
    purge_cb = ctk.CTkCheckBox(
        card,
        text="Also remove saved configuration, presets, and preferences",
        variable=purge_var,
        font=ctk.CTkFont(family="Segoe UI", size=12),
        text_color="#e2e8f0",
        fg_color=COLOR_DANGER,
        hover_color=COLOR_DANGER_HOVER
    )
    purge_cb.pack(pady=(0, 24), padx=20, anchor="w")

    status_label = ctk.CTkLabel(
        card,
        text="",
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        text_color="#38bdf8"
    )
    status_label.pack(pady=(0, 10), padx=20, anchor="w")

    btn_frame = ctk.CTkFrame(card, fg_color="transparent")
    btn_frame.pack(fill="x", padx=20, pady=(0, 16), side="bottom")

    def on_cancel():
        root.destroy()
        sys.exit(0)

    def on_confirm_uninstall():
        cancel_btn.configure(state="disabled")
        uninstall_btn.configure(state="disabled")
        status_label.configure(text="Uninstalling... Please wait.")
        root.update()

        purge = purge_var.get()
        perform_uninstall(install_dir, purge_data=purge)

        status_label.configure(
            text="Uninstallation completed successfully!",
            text_color="#2ec4b6"
        )
        uninstall_btn.pack_forget()
        cancel_btn.configure(
            text="Close",
            state="normal",
            command=root.destroy,
            fg_color="#334155",
            hover_color="#475569"
        )

    cancel_btn = ctk.CTkButton(
        btn_frame,
        text="Cancel",
        width=100,
        height=36,
        fg_color="#262a36",
        hover_color="#323846",
        command=on_cancel
    )
    cancel_btn.pack(side="right", padx=(8, 0))

    uninstall_btn = ctk.CTkButton(
        btn_frame,
        text="Uninstall",
        width=110,
        height=36,
        fg_color=COLOR_DANGER,
        hover_color=COLOR_DANGER_HOVER,
        font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        command=on_confirm_uninstall
    )
    uninstall_btn.pack(side="right")

    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="Lenovo LOQ Backlight Customizer Uninstaller")
    parser.add_argument("--quiet", "--silent", action="store_true", help="Quiet uninstallation without UI")
    parser.add_argument("--purge-data", action="store_true", help="Purge user config and preferences")
    parser.add_argument("--install-dir", type=str, default="", help="Target installation directory")
    parser.add_argument("--subtask", action="store_true", help="Internal flag indicating execution from temp folder")
    args = parser.parse_args()

    # Determine installation directory
    if args.install_dir:
        install_dir = os.path.abspath(args.install_dir)
    else:
        # Default to directory containing this script or executable
        if getattr(sys, "frozen", False):
            install_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            install_dir = os.path.dirname(os.path.abspath(__file__))

    # If running from inside the install directory itself, Windows file locks will prevent
    # uninstall.exe from deleting its own folder. Delegate to %TEMP% copy:
    if not args.subtask and getattr(sys, "frozen", False):
        temp_dir = os.environ.get("TEMP", os.environ.get("TMP", os.path.expanduser("~")))
        temp_exe = os.path.join(temp_dir, "LenovoLOQ_Uninstaller.exe")
        try:
            shutil.copy2(sys.executable, temp_exe)
            delegated_args = [temp_exe, "--subtask", "--install-dir", install_dir]
            if args.quiet:
                delegated_args.append("--quiet")
            if args.purge_data:
                delegated_args.append("--purge-data")
            subprocess.Popen(delegated_args, close_fds=True)
            sys.exit(0)
        except Exception as e:
            print(f"[Uninstall] Delegation to temp failed ({e}), proceeding directly.")

    # We are running as subtask or in development script mode:
    if args.quiet:
        perform_uninstall(install_dir, purge_data=args.purge_data)
    else:
        run_gui(install_dir)

    # If running from temp as subtask, schedule self-deletion
    if args.subtask:
        try:
            self_exe = sys.executable
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            subprocess.Popen(
                f'cmd.exe /c timeout /t 2 /nobreak >nul & del /f /q "{self_exe}"',
                shell=True,
                creationflags=flags
            )
        except Exception:
            pass


if __name__ == "__main__":
    main()
