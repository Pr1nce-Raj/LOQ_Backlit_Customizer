import os
import sys
import time
import shutil
import winreg
import argparse
import subprocess
import threading
from datetime import datetime
from typing import Optional

import customtkinter as ctk
from tkinter import filedialog

APP_NAME = "Lenovo LOQ Backlight Customizer"
APP_REG_NAME = "LenovoLOQBacklightCustomizer"
APP_VERSION = "1.0.1"
APP_PUBLISHER = "Prince Raj"
EXE_NAME = "Lenovo_LOQ_Backlight_Customizer.exe"
UNINSTALL_EXE_NAME = "uninstall.exe"
ICON_NAME = "app_icon.ico"
GITHUB_URL = "https://github.com/Pr1nce-Raj/LOQ_Backlit_Customizer"

# UI Theme Palette
COLOR_BG = "#121317"
COLOR_CARD = "#1a1c23"
COLOR_CARD_BORDER = "#2b2e3b"
COLOR_ACCENT = "#00b4d8"
COLOR_ACCENT_HOVER = "#0096c7"
COLOR_SUCCESS = "#2ec4b6"
COLOR_WARNING = "#ff9f1c"
COLOR_DANGER = "#e71d36"
COLOR_TEXT_MUTED = "#8d99ae"


def get_default_install_dir() -> str:
    """Return default per-user installation directory in %LOCALAPPDATA%/Programs."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return os.path.join(local_app_data, "Programs", "LenovoLOQBacklightCustomizer")
    userprofile = os.environ.get("USERPROFILE", "C:\\")
    return os.path.join(userprofile, "AppData", "Local", "Programs", "LenovoLOQBacklightCustomizer")


def get_bundle_dir() -> str:
    """Get the source directory where packaged files reside (PyInstaller MEIPASS or local dir)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def create_windows_shortcut(target_path: str, shortcut_path: str, working_dir: str = "", icon_path: str = "", description: str = "") -> bool:
    """Create Windows .lnk shortcut via PowerShell WScript.Shell COM object."""
    try:
        dir_name = os.path.dirname(shortcut_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        target_path = os.path.abspath(target_path)
        working_dir = os.path.abspath(working_dir or os.path.dirname(target_path))
        icon_path = os.path.abspath(icon_path or target_path)

        target_clean = target_path.replace("'", "''")
        lnk_clean = shortcut_path.replace("'", "''")
        work_clean = working_dir.replace("'", "''")
        icon_clean = icon_path.replace("'", "''")
        desc_clean = description.replace("'", "''")

        ps_script = f"""
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut('{lnk_clean}')
$s.TargetPath = '{target_clean}'
$s.WorkingDirectory = '{work_clean}'
$s.IconLocation = '{icon_clean}'
$s.Description = '{desc_clean}'
$s.Save()
"""
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        res = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "-"],
            input=ps_script,
            text=True,
            capture_output=True,
            creationflags=flags
        )
        return res.returncode == 0 and os.path.exists(shortcut_path)
    except Exception as e:
        print(f"[Installer] Shortcut creation error: {e}")
        return False


def register_in_windows_uninstall(install_dir: str, main_exe: str, uninstall_exe: str, icon_path: str) -> bool:
    """Register application in HKCU Uninstall key for Windows Settings and Control Panel."""
    key_path = rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_REG_NAME}"
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)

        # Calculate estimated size in KB
        size_kb = 35000
        if os.path.exists(install_dir):
            total_bytes = sum(
                os.path.getsize(os.path.join(root, file))
                for root, _, files in os.walk(install_dir)
                for file in files
            )
            size_kb = max(1, total_bytes // 1024)

        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, APP_PUBLISHER)
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, install_dir)
        winreg.SetValueEx(key, "InstallDate", 0, winreg.REG_SZ, datetime.now().strftime("%Y%m%d"))
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, f'"{main_exe}",0')
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{uninstall_exe}"')
        winreg.SetValueEx(key, "QuietUninstallString", 0, winreg.REG_SZ, f'"{uninstall_exe}" --quiet')
        winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, size_kb)
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "URLInfoAbout", 0, winreg.REG_SZ, GITHUB_URL)
        winreg.SetValueEx(key, "HelpLink", 0, winreg.REG_SZ, GITHUB_URL)
        winreg.SetValueEx(key, "Comments", 0, winreg.REG_SZ, "100% Offline keyboard backlight customizer for Lenovo LOQ laptops")

        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"[Installer] Registry registration error: {e}")
        return False


def set_startup_registry(main_exe: str, enable: bool) -> bool:
    """Configure Windows Run key for automatic startup."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enable:
            cmd = f'"{main_exe}" --minimized'
            winreg.SetValueEx(key, APP_REG_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_REG_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"[Installer] Startup registry error: {e}")
        return False


def kill_running_app() -> None:
    """Terminate any existing instance before overwriting files."""
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    try:
        subprocess.run(["taskkill", "/f", "/im", EXE_NAME], capture_output=True, creationflags=flags)
        time.sleep(0.4)
    except Exception:
        pass


def execute_install_pipeline(
    install_dir: str,
    create_start_menu: bool,
    create_desktop: bool,
    start_with_windows: bool,
    on_progress: callable
) -> bool:
    """Run file copy, shortcut generation, and system registration."""
    bundle = get_bundle_dir()

    # Step 1: Kill running instances
    on_progress(10, "Closing running application instances...")
    kill_running_app()

    # Step 2: Ensure directories exist
    on_progress(25, "Preparing target installation directory...")
    os.makedirs(install_dir, exist_ok=True)

    # Step 3: Copy binaries and assets
    on_progress(45, "Installing application files...")
    target_main_exe = os.path.join(install_dir, EXE_NAME)
    target_uninstall_exe = os.path.join(install_dir, UNINSTALL_EXE_NAME)
    target_icon = os.path.join(install_dir, ICON_NAME)

    # File sources
    files_to_copy = [
        (os.path.join(bundle, EXE_NAME), target_main_exe),
        (os.path.join(bundle, UNINSTALL_EXE_NAME), target_uninstall_exe),
        (os.path.join(bundle, ICON_NAME), target_icon),
        (os.path.join(bundle, "LICENSE"), os.path.join(install_dir, "LICENSE")),
        (os.path.join(bundle, "README.md"), os.path.join(install_dir, "README.md")),
    ]

    for src, dst in files_to_copy:
        if os.path.exists(src):
            try:
                shutil.copy2(src, dst)
            except Exception as e:
                print(f"[Installer] Warning copying {src} -> {dst}: {e}")

    # Step 4: Register in Windows Installed Apps & Control Panel
    on_progress(65, "Registering application with Windows Settings...")
    register_in_windows_uninstall(install_dir, target_main_exe, target_uninstall_exe, target_icon)

    # Step 5: Create Start Menu shortcuts under Tools
    if create_start_menu:
        on_progress(80, "Creating Start Menu shortcuts under Tools...")
        appdata = os.environ.get("APPDATA")
        if appdata:
            tools_dir = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Tools")
            os.makedirs(tools_dir, exist_ok=True)
            create_windows_shortcut(
                target_path=target_main_exe,
                shortcut_path=os.path.join(tools_dir, f"{APP_NAME}.lnk"),
                working_dir=install_dir,
                icon_path=target_icon if os.path.exists(target_icon) else target_main_exe,
                description="Lenovo LOQ Backlight Customizer"
            )
            create_windows_shortcut(
                target_path=target_uninstall_exe,
                shortcut_path=os.path.join(tools_dir, f"Uninstall {APP_NAME}.lnk"),
                working_dir=install_dir,
                icon_path=target_icon if os.path.exists(target_icon) else target_uninstall_exe,
                description="Uninstall Lenovo LOQ Backlight Customizer"
            )

    # Step 6: Create Desktop shortcut
    if create_desktop:
        on_progress(90, "Creating Desktop shortcut...")
        userprofile = os.environ.get("USERPROFILE")
        if userprofile:
            desktop_dir = os.path.join(userprofile, "Desktop")
            create_windows_shortcut(
                target_path=target_main_exe,
                shortcut_path=os.path.join(desktop_dir, f"{APP_NAME}.lnk"),
                working_dir=install_dir,
                icon_path=target_icon if os.path.exists(target_icon) else target_main_exe,
                description="Lenovo LOQ Backlight Customizer"
            )

    # Step 7: Configure Startup
    if start_with_windows:
        on_progress(95, "Configuring startup registry...")
        set_startup_registry(target_main_exe, enable=True)

    on_progress(100, "Installation complete!")
    time.sleep(0.3)
    return True


class SetupWizard(ctk.CTk):
    """Modern dark GUI installation wizard for Lenovo LOQ Backlight Customizer."""

    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Lenovo LOQ Backlight Customizer Setup")
        self.geometry("640x560")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)

        # Set window icon if available
        bundle = get_bundle_dir()
        icon_path = os.path.join(bundle, ICON_NAME)
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 640) // 2
        y = (self.winfo_screenheight() - 560) // 2
        self.geometry(f"+{x}+{y}")

        self.install_dir_var = ctk.StringVar(value=get_default_install_dir())
        self.start_menu_var = ctk.BooleanVar(value=True)
        self.desktop_var = ctk.BooleanVar(value=True)
        self.startup_var = ctk.BooleanVar(value=False)
        self.launch_after_var = ctk.BooleanVar(value=True)

        self.current_step = 0
        self.steps = [
            self._show_welcome_step,
            self._show_security_step,
            self._show_options_step,
            self._show_progress_step,
            self._show_finish_step,
        ]

        # Container frame
        self.container = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self.container.pack(fill="both", expand=True)

        self._render_current_step()

    def _render_current_step(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        self.steps[self.current_step]()

    # ----------------------------------------------------
    # STEP 0: Welcome
    # ----------------------------------------------------
    def _show_welcome_step(self):
        card = ctk.CTkFrame(self.container, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        # Header Badge
        badge = ctk.CTkLabel(
            card,
            text="✨ Setup Wizard",
            text_color=COLOR_ACCENT,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        badge.pack(anchor="w", padx=24, pady=(24, 4))

        title = ctk.CTkLabel(
            card,
            text="Lenovo LOQ Backlight Customizer",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#ffffff"
        )
        title.pack(anchor="w", padx=24, pady=(0, 4))

        ver_label = ctk.CTkLabel(
            card,
            text=f"Version {APP_VERSION}  •  Open-Source Edition",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MUTED
        )
        ver_label.pack(anchor="w", padx=24, pady=(0, 16))

        info_box = ctk.CTkFrame(card, fg_color="#14161d", corner_radius=8, border_color=COLOR_CARD_BORDER, border_width=1)
        info_box.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        welcome_text = (
            "Welcome to the official setup wizard for Lenovo LOQ Backlight Customizer.\n\n"
            "This installer will configure everything needed to run and manage the software "
            "seamlessly on your Windows laptop:\n\n"
            "  • Installs clean per-user binaries into your Local Programs folder\n"
            "  • Creates standard Start Menu and Desktop shortcuts\n"
            "  • Registers with Windows Settings ('Installed Apps') & Control Panel\n"
            "  • Provides a clean, dedicated uninstaller\n"
            "  • Saves all profiles to %APPDATA%, keeping your Downloads folder clean\n\n"
            "Click Next to review the transparent security and hardware access disclosures."
        )
        txt = ctk.CTkLabel(
            info_box,
            text=welcome_text,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#cbd5e1",
            justify="left",
            wraplength=520
        )
        txt.pack(padx=16, pady=16, anchor="nw")

        # Bottom Bar
        nav = ctk.CTkFrame(card, fg_color="transparent")
        nav.pack(fill="x", padx=24, pady=(0, 20), side="bottom")

        cancel_btn = ctk.CTkButton(
            nav, text="Cancel", width=90, height=36,
            fg_color="#262a36", hover_color="#323846",
            command=self.destroy
        )
        cancel_btn.pack(side="left")

        next_btn = ctk.CTkButton(
            nav, text="Next >", width=110, height=36,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self._next_step
        )
        next_btn.pack(side="right")

    # ----------------------------------------------------
    # STEP 1: Security & Hardware Access Disclosure
    # ----------------------------------------------------
    def _show_security_step(self):
        card = ctk.CTkFrame(self.container, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        badge = ctk.CTkLabel(
            card,
            text="🛡️ Transparency & Architecture",
            text_color=COLOR_SUCCESS,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        badge.pack(anchor="w", padx=24, pady=(20, 2))

        title = ctk.CTkLabel(
            card,
            text="What is Used, Why, & 100% Offline Notice",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#ffffff"
        )
        title.pack(anchor="w", padx=24, pady=(0, 12))

        scroll = ctk.CTkScrollableFrame(card, fg_color="#14161d", corner_radius=8, border_color=COLOR_CARD_BORDER, border_width=1)
        scroll.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        items = [
            ("🔒 100% Offline — Zero Telemetry",
             "This software contains NO network sockets, analytics, or background internet connections. "
             "It operates completely locally on your hardware. Your lighting profiles remain strictly on your PC."),
            ("💻 Lenovo ACPI Driver (\\\\.\\EnergyDrv)",
             "Controls keyboard LED brightness states (Off, Half, Full) via the Lenovo Energy Management "
             "ACPI driver interface using IOCTL code 0x831020C8. This is the exact native mechanism Lenovo Vantage uses."),
            ("⌨️ Global Shortcut Hook",
             "Uses low-level Windows keyboard hooks to listen for your configured toggle shortcut "
             "(default Ctrl+Shift+L). Keystrokes are not logged, recorded, or stored anywhere."),
            ("⏱️ Inactivity Guard (Idle Monitor)",
             "Calls Windows API GetLastInputInfo to measure idle time for automatic backlight sleep. "
             "It only reads elapsed milliseconds since the last user action without recording keystroke content."),
            ("⚠️ Note on 'Unknown Publisher' / Windows SmartScreen",
             "Microsoft Defender SmartScreen flags newly downloaded open-source programs because they lack a "
             "commercial $400/yr corporate code-signing certificate. Because this project is free and fully inspectable on GitHub, "
             "you can safely click 'More info' -> 'Run anyway'.")
        ]

        for head, body in items:
            h_lbl = ctk.CTkLabel(
                scroll,
                text=head,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color="#38bdf8",
                anchor="w"
            )
            h_lbl.pack(fill="x", padx=12, pady=(10, 2))

            b_lbl = ctk.CTkLabel(
                scroll,
                text=body,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#cbd5e1",
                justify="left",
                wraplength=500
            )
            b_lbl.pack(fill="x", padx=12, pady=(0, 8))

        # Bottom Bar
        nav = ctk.CTkFrame(card, fg_color="transparent")
        nav.pack(fill="x", padx=24, pady=(0, 20), side="bottom")

        back_btn = ctk.CTkButton(
            nav, text="< Back", width=90, height=36,
            fg_color="#262a36", hover_color="#323846",
            command=self._prev_step
        )
        back_btn.pack(side="left")

        next_btn = ctk.CTkButton(
            nav, text="Next >", width=110, height=36,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self._next_step
        )
        next_btn.pack(side="right")

    # ----------------------------------------------------
    # STEP 2: Options & Destination
    # ----------------------------------------------------
    def _show_options_step(self):
        card = ctk.CTkFrame(self.container, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        badge = ctk.CTkLabel(
            card,
            text="📁 Destination & Preferences",
            text_color=COLOR_ACCENT,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        badge.pack(anchor="w", padx=24, pady=(20, 2))

        title = ctk.CTkLabel(
            card,
            text="Select Installation Options",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#ffffff"
        )
        title.pack(anchor="w", padx=24, pady=(0, 16))

        # Destination Section
        dest_card = ctk.CTkFrame(card, fg_color="#14161d", corner_radius=8, border_color=COLOR_CARD_BORDER, border_width=1)
        dest_card.pack(fill="x", padx=24, pady=(0, 16))

        dest_title = ctk.CTkLabel(
            dest_card,
            text="Installation Folder:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#ffffff"
        )
        dest_title.pack(anchor="w", padx=16, pady=(12, 4))

        path_row = ctk.CTkFrame(dest_card, fg_color="transparent")
        path_row.pack(fill="x", padx=16, pady=(0, 6))

        path_entry = ctk.CTkEntry(
            path_row,
            textvariable=self.install_dir_var,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            height=34
        )
        path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        def browse_folder():
            current = self.install_dir_var.get()
            initial = current if os.path.exists(current) else os.path.dirname(current)
            if not initial or not os.path.exists(initial):
                initial = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
            selected = filedialog.askdirectory(
                parent=self,
                title="Select Installation Folder",
                initialdir=initial
            )
            if selected:
                norm = os.path.normpath(selected)
                if not norm.lower().endswith("lenovoloqbacklightcustomizer"):
                    norm = os.path.join(norm, "LenovoLOQBacklightCustomizer")
                self.install_dir_var.set(norm)

        browse_btn = ctk.CTkButton(
            path_row,
            text="📁 Browse...",
            width=100,
            height=34,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=browse_folder
        )
        browse_btn.pack(side="right")

        dest_note = ctk.CTkLabel(
            dest_card,
            text="Use the Browse button to pick any custom folder on your system.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_MUTED
        )
        dest_note.pack(anchor="w", padx=16, pady=(0, 12))

        # Checkbox Options
        opts_card = ctk.CTkFrame(card, fg_color="#14161d", corner_radius=8, border_color=COLOR_CARD_BORDER, border_width=1)
        opts_card.pack(fill="x", padx=24, pady=(0, 20))

        opts_title = ctk.CTkLabel(
            opts_card,
            text="Shortcuts & Integration:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#ffffff"
        )
        opts_title.pack(anchor="w", padx=16, pady=(12, 8))

        ctk.CTkCheckBox(
            opts_card,
            text="Add to Start Menu under 'Tools'",
            variable=self.start_menu_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#e2e8f0"
        ).pack(anchor="w", padx=16, pady=(0, 8))

        ctk.CTkCheckBox(
            opts_card,
            text="Automatically create Desktop shortcut",
            variable=self.desktop_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#e2e8f0"
        ).pack(anchor="w", padx=16, pady=(0, 8))

        ctk.CTkCheckBox(
            opts_card,
            text="Start with Windows (minimized to system tray)",
            variable=self.startup_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#e2e8f0"
        ).pack(anchor="w", padx=16, pady=(0, 14))

        # Bottom Bar
        nav = ctk.CTkFrame(card, fg_color="transparent")
        nav.pack(fill="x", padx=24, pady=(0, 20), side="bottom")

        back_btn = ctk.CTkButton(
            nav, text="< Back", width=90, height=36,
            fg_color="#262a36", hover_color="#323846",
            command=self._prev_step
        )
        back_btn.pack(side="left")

        install_btn = ctk.CTkButton(
            nav, text="Install Now", width=120, height=36,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self._start_installation
        )
        install_btn.pack(side="right")

    # ----------------------------------------------------
    # STEP 3: Progress
    # ----------------------------------------------------
    def _show_progress_step(self):
        card = ctk.CTkFrame(self.container, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        badge = ctk.CTkLabel(
            card,
            text="⚙️ Installing",
            text_color=COLOR_ACCENT,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        badge.pack(anchor="w", padx=24, pady=(24, 4))

        title = ctk.CTkLabel(
            card,
            text="Installing Application Files...",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#ffffff"
        )
        title.pack(anchor="w", padx=24, pady=(0, 20))

        self.progress_bar = ctk.CTkProgressBar(card, height=14, corner_radius=7, fg_color="#14161d", progress_color=COLOR_ACCENT)
        self.progress_bar.pack(fill="x", padx=24, pady=(30, 12))
        self.progress_bar.set(0.0)

        self.status_label = ctk.CTkLabel(
            card,
            text="Initializing setup...",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MUTED
        )
        self.status_label.pack(anchor="w", padx=24, pady=(0, 20))

    def _start_installation(self):
        self.current_step = 3
        self._render_current_step()

        def worker():
            install_dir = os.path.normpath(self.install_dir_var.get())
            create_start_menu = self.start_menu_var.get()
            create_desktop = self.desktop_var.get()
            startup = self.startup_var.get()

            def update_progress(pct: int, msg: str):
                self.after(0, lambda: self._apply_progress(pct, msg))

            success = execute_install_pipeline(
                install_dir=install_dir,
                create_start_menu=create_start_menu,
                create_desktop=create_desktop,
                start_with_windows=startup,
                on_progress=update_progress
            )

            if success:
                self.after(400, self._show_completion)

        threading.Thread(target=worker, daemon=True).start()

    def _apply_progress(self, pct: int, msg: str):
        if hasattr(self, "progress_bar"):
            self.progress_bar.set(pct / 100.0)
        if hasattr(self, "status_label"):
            self.status_label.configure(text=msg)

    def _show_completion(self):
        self.current_step = 4
        self._render_current_step()

    # ----------------------------------------------------
    # STEP 4: Complete
    # ----------------------------------------------------
    def _show_finish_step(self):
        card = ctk.CTkFrame(self.container, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        badge = ctk.CTkLabel(
            card,
            text="🎉 Completed",
            text_color=COLOR_SUCCESS,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        badge.pack(anchor="w", padx=24, pady=(24, 4))

        title = ctk.CTkLabel(
            card,
            text="Installation Completed Successfully!",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#ffffff"
        )
        title.pack(anchor="w", padx=24, pady=(0, 16))

        box = ctk.CTkFrame(card, fg_color="#14161d", corner_radius=8, border_color=COLOR_CARD_BORDER, border_width=1)
        box.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        summary_text = (
            "Lenovo LOQ Backlight Customizer is ready for use.\n\n"
            f"Installed Location:\n{os.path.normpath(self.install_dir_var.get())}\n\n"
            "System Integration Summary:\n"
            "  ✔ Registered in Windows Settings ('Installed Apps')\n"
            "  ✔ Registered in Control Panel ('Programs and Features')\n"
            "  ✔ Desktop shortcut automatically created\n"
            "  ✔ Added to Windows Start Menu under 'Tools'\n"
            "  ✔ Configuration cleanly mapped to %APPDATA%\n\n"
            "You can launch the application now or from your Start Menu at any time."
        )
        ctk.CTkLabel(
            box,
            text=summary_text,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#cbd5e1",
            justify="left",
            wraplength=520
        ).pack(padx=16, pady=16, anchor="nw")

        launch_cb = ctk.CTkCheckBox(
            card,
            text="Launch Lenovo LOQ Backlight Customizer now",
            variable=self.launch_after_var,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#ffffff",
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER
        )
        launch_cb.pack(anchor="w", padx=24, pady=(0, 20))

        # Finish button
        nav = ctk.CTkFrame(card, fg_color="transparent")
        nav.pack(fill="x", padx=24, pady=(0, 20), side="bottom")

        finish_btn = ctk.CTkButton(
            nav, text="Finish", width=120, height=36,
            fg_color=COLOR_SUCCESS, hover_color="#25a195",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self._on_finish
        )
        finish_btn.pack(side="right")

    def _on_finish(self):
        if self.launch_after_var.get():
            install_dir = os.path.normpath(self.install_dir_var.get())
            exe_path = os.path.join(install_dir, EXE_NAME)
            if os.path.exists(exe_path):
                try:
                    subprocess.Popen([exe_path], cwd=install_dir)
                except Exception as e:
                    print(f"[Installer] Launch failed: {e}")
        self.destroy()

    def _next_step(self):
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self._render_current_step()

    def _prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self._render_current_step()


def main():
    parser = argparse.ArgumentParser(description="Lenovo LOQ Backlight Customizer Setup Wizard")
    parser.add_argument("--silent", "--quiet", action="store_true", help="Silent installation with defaults")
    parser.add_argument("--dir", type=str, default="", help="Target installation directory")
    args = parser.parse_args()

    if args.silent:
        target_dir = args.dir or get_default_install_dir()
        execute_install_pipeline(
            install_dir=target_dir,
            create_start_menu=True,
            create_desktop=True,
            start_with_windows=False,
            on_progress=lambda p, m: print(f"[{p}%] {m}")
        )
    else:
        app = SetupWizard()
        app.mainloop()


if __name__ == "__main__":
    main()
