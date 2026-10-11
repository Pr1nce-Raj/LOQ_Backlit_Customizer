"""Automated build script for Lenovo LOQ Backlight Customizer.

Compiles:
1. uninstall.exe (Standalone Uninstaller with embedded PE version info)
2. Lenovo_LOQ_Backlight_Customizer.exe (Main Application with embedded PE version info)
3. Lenovo_LOQ_Backlight_Customizer_Setup.exe (Setup Wizard bundling app and uninstaller)
"""

import os
import sys
import shutil
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")


def run_cmd(cmd_list, description):
    print(f"\n[BUILD] >>> {description}...")
    res = subprocess.run(cmd_list, cwd=BASE_DIR)
    if res.returncode != 0:
        print(f"[BUILD ERROR] {description} failed with exit code {res.returncode}")
        sys.exit(res.returncode)
    print(f"[BUILD SUCCESS] {description} finished.")


def main():
    pyinstaller = os.path.join(os.path.dirname(sys.executable), "Scripts", "pyinstaller.exe")
    if not os.path.exists(pyinstaller):
        pyinstaller = "pyinstaller"

    # 1. Build Uninstaller
    run_cmd([
        pyinstaller,
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--icon", "app_icon.ico",
        "--version-file", "uninstall_version_info.txt",
        "--name", "uninstall",
        "uninstall.py"
    ], "Compiling standalone uninstaller (uninstall.exe)")

    dist_uninstall = os.path.join(DIST_DIR, "uninstall.exe")
    root_uninstall = os.path.join(BASE_DIR, "uninstall.exe")
    shutil.copy2(dist_uninstall, root_uninstall)

    # 2. Build Main Application
    run_cmd([
        pyinstaller,
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--icon", "app_icon.ico",
        "--version-file", "version_info.txt",
        "--add-data", "app_icon.ico;.",
        "--name", "Lenovo_LOQ_Backlight_Customizer",
        "Lenovo_LOQ_Backlight_Customizer.py"
    ], "Compiling main application (Lenovo_LOQ_Backlight_Customizer.exe)")

    dist_main = os.path.join(DIST_DIR, "Lenovo_LOQ_Backlight_Customizer.exe")
    root_main = os.path.join(BASE_DIR, "Lenovo_LOQ_Backlight_Customizer.exe")
    shutil.copy2(dist_main, root_main)

    # 3. Build Setup Wizard Installer
    run_cmd([
        pyinstaller,
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--icon", "app_icon.ico",
        "--version-file", "installer_version_info.txt",
        "--add-data", f"{root_main};.",
        "--add-data", f"{root_uninstall};.",
        "--add-data", "app_icon.ico;.",
        "--add-data", "LICENSE;.",
        "--add-data", "README.md;.",
        "--name", "Lenovo_LOQ_Backlight_Customizer_Setup",
        "installer.py"
    ], "Compiling setup wizard installer (Lenovo_LOQ_Backlight_Customizer_Setup.exe)")

    dist_setup = os.path.join(DIST_DIR, "Lenovo_LOQ_Backlight_Customizer_Setup.exe")
    root_setup = os.path.join(BASE_DIR, "Lenovo_LOQ_Backlight_Customizer_Setup.exe")
    shutil.copy2(dist_setup, root_setup)

    print("\n" + "=" * 60)
    print("ALL BINARIES BUILT AND PACKAGED SUCCESSFULLY!")
    print(f"1. Setup Wizard: {root_setup}")
    print(f"2. Main App:     {root_main}")
    print(f"3. Uninstaller:  {root_uninstall}")
    print("=" * 60)


if __name__ == "__main__":
    main()
