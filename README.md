# Lenovo LOQ Keyboard Backlight Customizer & Inactivity Guard

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Windows 11 / 10](https://img.shields.io/badge/Platform-Windows%2011%20%7C%2010-0078d4.svg)](#-hardware-compatibility-check-before-downloading)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](requirements.txt)
[![Download EXE](https://img.shields.io/badge/Download-Standalone%20.EXE-orange.svg)](https://github.com/Pr1nce-Raj/LOQ_Backlit_Customizer/releases)

An ultra-modern, lightweight background utility designed specifically for **Lenovo LOQ** laptops to add dynamic lighting tricks (Breathing, Wave, Pulse, SOS), automatic battery-saving inactivity sleep, and conflict-free two-way synchronization with your laptop's physical keyboard controls.

---

## ⚠️ Hardware Compatibility Check (Before Downloading)

Please verify your laptop model before running this utility:

| Laptop Category | Status | Details |
| :--- | :---: | :--- |
| **Lenovo LOQ (White Backlight)** | ✅ **Supported** | Tested on **LOQ 15IRX9 (83GS003NIN)**, compatible with 15IAX9, 15ARP9, 16IRH8, etc. |
| **Lenovo IdeaPad Gaming (White)** | ✅ **Supported** | Models using the official Lenovo Energy Management driver (`\\.\EnergyDrv`). |
| **Lenovo Legion (White 2-Stage)** | ✅ **Supported** | Models with standard 2-level white backlights. |
| **Lenovo 4-Zone / Per-Key RGB** | ❌ **Unsupported** | RGB models use proprietary USB HID lighting controllers, not ACPI brightness IOCTL. |
| **Other Brands (ASUS, HP, Dell, Acer)** | ❌ **Unsupported** | Other manufacturers use different motherboard controllers (ASUS WMI, AlienFX, OMEN). |

---

## 🎯 What to Expect When You Run It

- **100% Portable**: No installation wizard or administrator installer required. Just double-click the `.exe`.
- **Zero Console Popups**: Built with native Windows GUI flags (`--noconsole`). No black terminal window flashes on your screen.
- **Default Out-of-the-Box Setup**:
  - Starts in smooth **Breathing mode** (relaxed 0.5x animation speed).
  - **Inactivity Guard** is enabled by default with a **30-second timeout** (fully customizable from 5s to 120s).
- **Runs in the Background**:
  - Closing the dashboard with the **`X`** button minimizes the app to your **System Tray (Notification Area)** next to the clock.
  - To completely exit the application, right-click the system tray icon and select **Exit**, or click **Quit App** in the dashboard.
- **Smart Inactivity Guard & Instant Wake**:
  - When you step away from your laptop, the backlight automatically turns off after your chosen inactivity timeout (customizable from 5s to 120s via the slider; default 30s) to conserve power and prolong LED lifespan.
  - The instant you press **any key** or touch your **mouse / trackpad**, the backlight immediately wakes up and resumes your active mode!
- **Conflict-Free with `Fn + Space`**:
  - Pressing your laptop's physical `Fn + Space` or changing modes in **Lenovo Vantage** works seamlessly. If an animation is playing, the app yields instantly to your manual choice.
- **Hardware Safe**:
  - Operates purely in Windows user-space via Lenovo's official `\\.\EnergyDrv` driver interface. It does **not** flash firmware, touch UEFI/BIOS, or install kernel drivers.

---

## ⚡ Quick Download & Getting Started

### Option 1: Standalone Executable (Recommended - No Python Required)
1. Download **[`Lenovo_LOQ_Backlight_Customizer.exe`](Lenovo_LOQ_Backlight_Customizer.exe)** (available in the repo root or from [**GitHub Releases**](https://github.com/Pr1nce-Raj/LOQ_Backlit_Customizer/releases)).
2. Double-click **`Lenovo_LOQ_Backlight_Customizer.exe`**.
3. Select your favorite lighting mode, adjust the speed slider, or set a custom shortcut.
4. Click **✔ Save & Apply All Settings**, then close or minimize the window!

### Option 2: Run from Source Code (For Developers)
1. Clone the repository:
   ```powershell
   git clone https://github.com/Pr1nce-Raj/LOQ_Backlit_Customizer.git
   cd LOQ_Backlit_Customizer
   ```
2. Install Python dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Launch the app:
   ```powershell
   python Lenovo_LOQ_Backlight_Customizer.py
   # Or run: Start_Backlight_Customizer.bat
   ```

---

## 🌟 Available Lighting Modes

You can select any of these modes from the dashboard or directly by right-clicking the system tray icon:

- 🌊 **Breathing**: Rhythmic, smooth illumination wave (`Off -> Low -> High -> Low -> Off`).
- 💓 **Pulse**: Heartbeat double-pulse cadence.
- 〰️ **Wave**: Continuous cascading illumination swell.
- 🚨 **Police**: Rapid dual-burst emergency pattern.
- 🆘 **SOS**: International Morse Code emergency pattern (`... --- ...`).
- ⚡ **Blink x3**: Triple-flash cadence.
- 💡 **Solid High**: 100% steady brightness.
- 🔅 **Solid Low**: 50% steady brightness.
- 🌑 **Off**: Backlight disabled.

---

## ⌨️ Custom Global Shortcuts

- Set any global keyboard shortcut (default: `Ctrl + Shift + L`).
- Use the **● Record Keys** button in the dashboard to simply press your desired keys on the keyboard to bind them.
- Choose shortcut behavior:
  - **Toggle**: Turn active backlight/tricks On and Off.
  - **Cycle**: Cycle through all lighting modes sequentially.

---

## 🔨 Building the Executable from Source

To compile the standalone binary yourself using PyInstaller:
```powershell
pip install -r requirements.txt
pyinstaller --noconfirm --onefile --windowed --icon "app_icon.ico" --collect-all customtkinter --distpath . Lenovo_LOQ_Backlight_Customizer.py
```

---

## 🧪 Automated Testing

The project includes an automated test suite covering IOCTL commands, thread safety, idle tracking, and mock drivers:
```powershell
python -m unittest discover -s tests
```

---

## 📄 License & Disclaimer

- **License**: Released under the [MIT License](LICENSE).
- **Disclaimer**: This is an independent open-source utility developed for Lenovo LOQ laptop users and is not officially affiliated with or endorsed by Lenovo Group Limited.
