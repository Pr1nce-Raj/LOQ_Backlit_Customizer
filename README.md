# Lenovo LOQ Backlight Customizer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Windows 11 / 10](https://img.shields.io/badge/Platform-Windows%2011%20%7C%2010-0078d4.svg)](#compatibility)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](requirements.txt)
[![Download EXE](https://img.shields.io/badge/Download-Release%20Binaries-orange.svg)](https://github.com/Pr1nce-Raj/LOQ_Backlit_Customizer/releases)

A lightweight Windows tray app that adds breathing/wave effects, custom hotkeys, and an auto-sleep timer to your Lenovo LOQ keyboard backlight — completely offline, with zero bloat.

---

### Why this exists

If you own a Lenovo LOQ laptop, you already know the frustration:
- The keyboard backlight only has Off, Low, and High via `Fn + Space`.
- There is no idle sleep timer, so the backlight stays on even when you step away or watch a movie.
- Lenovo Vantage is heavy, runs multiple background services, and still doesn't give you custom lighting effects.

This tool talks directly to Lenovo's onboard ACPI driver (`\\.\EnergyDrv`) to give you smooth lighting animations and automatic idle sleep, running quietly in your system tray at virtually 0% CPU and ~30 MB RAM.

---

## Compatibility

This app controls the standard **monochrome (white) backlight** used on Lenovo LOQ laptops:

| Laptop | Supported? | Notes |
| :--- | :---: | :--- |
| **Lenovo LOQ (White Backlight)** | Yes | Tested on LOQ 15IRX9 (83GS003NIN); works on 15IAX9, 15ARP9, 16IRH8, etc. |
| **IdeaPad Gaming 3 (White)** | Yes | Any model using the Lenovo Energy Management driver (`\\.\EnergyDrv`). |
| **Legion (White 2-stage)** | Yes | Standard 2-level white keyboard models. |
| **4-Zone / Per-Key RGB Models** | No | RGB models use a proprietary USB HID controller, not ACPI brightness. |
| **Other Brands (ASUS, HP, Dell)** | No | Other vendors use proprietary motherboard drivers (ASUS WMI, OMEN, AlienFX). |

---

## How to Install

### Terminal (Fastest)

**WinGet** (built into Windows 10 & 11):
```powershell
winget install PrinceRaj.LenovoLOQBacklightCustomizer
```

**Scoop**:
```powershell
scoop install https://raw.githubusercontent.com/Pr1nce-Raj/LOQ_Backlit_Customizer/main/scoop/lenovo-loq-backlight-customizer.json
```

**Chocolatey**:
```powershell
choco install lenovo-loq-backlight-customizer
```

---

### Download the .exe

Grab the latest release from the [Releases page](https://github.com/Pr1nce-Raj/LOQ_Backlit_Customizer/releases):

- **Setup Wizard (`Lenovo_LOQ_Backlight_Customizer_Setup.exe`)**:
  Recommended. Installs to your user folder (no admin prompt needed), lets you pick a custom directory with the Browse button, adds a Desktop shortcut, registers a clean uninstaller in Windows Settings / Control Panel, and groups shortcuts in your Start Menu under `Tools`.
- **Portable (`Lenovo_LOQ_Backlight_Customizer.exe`)**:
  No installation needed. Just drop it wherever you like and run it. Settings are saved to `%APPDATA%`, so it will never clutter your Downloads folder.

#### Note on Windows SmartScreen ("Unknown Publisher")
Because this is a free personal project and doesn't have an expensive corporate code-signing certificate ($400/year), Windows SmartScreen will show a blue *"Windows protected your PC"* prompt the first time you run it:
1. Click **More info**.
2. Click **Run anyway**.

The app is 100% open-source, operates completely offline with zero telemetry, and you can inspect every line of Python in this repository. Over time, as more people download and run it, Windows SmartScreen will automatically build reputation for the file hash.

---

## Features & Usage

- **Auto-Sleep / Inactivity Guard**: Set an idle timeout between 5s and 120s (default is 30s). When you stop typing or moving the mouse, the backlight turns off to save battery. The second you press any key or touch the trackpad, it instantly wakes up.
- **Lighting Effects**:
  - **Breathing**: Smooth fade between Off, Low, and High.
  - **Wave**: Continuous light wave.
  - **Pulse**: Double-pulse heartbeat flash.
  - **Police & Blink**: Rapid flashing patterns.
  - **SOS**: Morse code emergency sequence.
  - **Solid High / Low**: Steady brightness without opening Vantage.
- **Custom Hotkey**: Click **Record Keys** in the app to set any shortcut (default is `Ctrl + Shift + L`) to toggle or cycle modes from anywhere.
- **Plays Nice with `Fn + Space`**: You can still use your physical `Fn + Space` key anytime. The app detects hardware changes and yields immediately without fighting the controller.
- **System Tray**: Closing the window (`X`) minimizes to the system tray next to your clock. Right-click the tray icon to switch modes or exit.

---

## Running from Source

If you want to run or modify the Python source directly:

```powershell
git clone https://github.com/Pr1nce-Raj/LOQ_Backlit_Customizer.git
cd LOQ_Backlit_Customizer
pip install -r requirements.txt
python Lenovo_LOQ_Backlight_Customizer.py
```

To run the unit test suite:
```powershell
python -m unittest discover -s tests
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.  
*Disclaimer: Independent project made for Lenovo LOQ laptop users. Not affiliated with or endorsed by Lenovo.*
