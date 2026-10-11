@echo off
cd /d "%~dp0"

:: Verify and auto-install any missing dependencies quietly
python -c "import customtkinter, pystray, PIL, keyboard" 2>nul
if errorlevel 1 (
    echo Installing required libraries (CustomTkinter, Pystray, Pillow, Keyboard)...
    python -m pip install customtkinter pystray pillow keyboard
)

echo Starting Lenovo LOQ Backlight Customizer in background...
start "" pythonw.exe Lenovo_LOQ_Backlight_Customizer.py %*
