# Lenovo LOQ Keyboard Backlight Customizer & Inactivity Guard

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Windows 11 / 10](https://img.shields.io/badge/Platform-Windows%2011%20%7C%2010-0078d4.svg)](#-hardware-support--compatibility-boundaries)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](requirements.txt)
[![Release: Standalone EXE](https://img.shields.io/badge/Download-Standalone%20.EXE-orange.svg)](https://github.com/Pr1nce-Raj/LOQ_Backlit_Customizer/releases)

A modern native Windows background application designed specifically for **Lenovo LOQ** laptops (tested on **LOQ 15IRX9 / 83GS003NIN** on Windows 11 64-bit) equipped with white single-color backlit keyboards.

---

## ⚡ Quick Download & Run

You have two simple ways to use the customizer:

### Option 1: Standalone Executable (No Python Required)
- **Direct Download**: Download [`Lenovo_LOQ_Backlight_Customizer.exe`](Lenovo_LOQ_Backlight_Customizer.exe) directly from the repository or from [**GitHub Releases**](https://github.com/Pr1nce-Raj/LOQ_Backlit_Customizer/releases).
- Double-click to run! Zero terminal window will flash or appear.

### Option 2: Run from Source
1. Clone the repository:
   ```powershell
   git clone https://github.com/Pr1nce-Raj/LOQ_Backlit_Customizer.git
   cd LOQ_Backlit_Customizer
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Run the application:
   ```powershell
   python Lenovo_LOQ_Backlight_Customizer.py
   # Or double-click Start_Backlight_Customizer.bat
   ```

---

## 🌟 Features

- **Two-Way Hardware Synchronization (Zero Conflict)**:
  - **Laptop -> App**: If you change the backlight using laptop controls (such as **`Fn + Space`** or inside **Lenovo Vantage**), the app detects the hardware state change, updates the dashboard status in real time, and synchronizes to your chosen level (`Solid Low`, `Solid High`, or `Off`).
  - **App -> Laptop**: When the app commands a brightness change, the laptop hardware and Embedded Controller register the change immediately.
  - **Conflict-Free Override**: Pressing `Fn + Space` at any time always takes priority—if an animated trick was active, it yields smoothly to your manual hardware choice!
- **Continuous Lighting Tricks & Modes (Default 0.5x Relaxed Speed)**:
  - **Breathing**: Smooth, rhythmic breathing cycle (`Off -> Low -> High -> Low -> Off`).
  - **Pulse**: Dual-beat heartbeat pulse.
  - **Wave**: Gentle cascading swell of illumination.
  - **Police**: Rapid emergency dual-burst pattern.
  - **SOS**: Morse code emergency distress pattern (`... --- ...`).
  - **Blink x3**: Triple-flash cadence.
  - **Solid High**: Steady 100% brightness.
  - **Solid Low**: Steady 50% brightness.
  - **Off**: Backlight turned off.
- **30-Second Inactivity Guard (Automated Power Saving)**:
  - Continuously monitors system-wide idle time via Windows `GetLastInputInfo`.
  - Automatically turns off the backlight after 30 seconds of inactivity (customizable from 5s to 120s).
  - **Instantaneous Wake**: As soon as you press **any key** on the keyboard or move/click the **mouse / trackpad**, the backlight immediately wakes up and resumes your active mode!
- **Global Custom Shortcuts**:
  - Set any custom key combination (e.g. `ctrl+shift+l` or `ctrl+alt+k`).
  - Includes a **Record Keys** button in the UI (just click and press your keys).
  - Shortcut action can be set to **Toggle On/Off** or **Cycle Next Mode**.
- **Modern Native UI (CustomTkinter)**:
  - Sleek, dark-themed dashboard inspired by Lenovo Legion / LOQ gaming aesthetics.
  - Real-time hardware status indicators (Off / Low / High).
  - Live system inactivity progress bar and countdown.
  - Animation speed slider (0.3x to 2.5x, default 0.5x).
  - Real-time status reporting for settings persistence, hotkey binding, and startup registry changes.
- **Silent Background & System Tray Integration**:
  - Sits quietly in the Windows Notification Area (System Tray) with a custom status icon.
  - Right-click tray menu allows quick switching between modes, toggling power saving, or reopening the dashboard.
  - Closing the window (X) minimizes to the system tray rather than killing the background service.
- **Windows Auto-Start**:
  - Toggle "Start with Windows" in the dashboard to launch automatically in the background on boot.
- **User-Space Device Communication**:
  - Communicates directly with Lenovo's official `\\.\EnergyDrv` user-space device interface via standard ACPI IOCTL commands.
  - Does **not** install third-party kernel drivers, patch system binaries, or flash BIOS/firmware.
  - Automatically records and restores the initial backlight level upon application exit.

---

## 💻 Hardware Support & Compatibility Boundaries

- **Supported Hardware**: Lenovo LOQ and Legion laptops with **single-color (white) backlit keyboards** controlled via the Lenovo Energy Management ACPI driver (`\\.\EnergyDrv`).
- **Verified Environment**: Tested and confirmed on **Lenovo LOQ 15IRX9 (Type 83GS, Model 83GS003NIN)** running 64-bit Windows 11 with official Lenovo Energy Management driver installed.
- **Unsupported Hardware**: Laptops with **4-Zone RGB** or **Per-Key RGB** keyboards use a proprietary USB HID lighting interface rather than the ACPI EnergyDrv interface, and are **not** supported by this utility.

---

## 🔨 Building the Standalone Executable

To compile the application into a standalone `.exe`:
```powershell
pip install -r requirements.txt
pyinstaller --noconfirm --onefile --windowed --icon "app_icon.ico" --collect-all customtkinter --distpath . Lenovo_LOQ_Backlight_Customizer.py
```

---

## 🧪 Automated Testing

To run the full suite of automated unit tests:
```powershell
python -m unittest discover -s tests
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.
