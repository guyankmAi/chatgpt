@echo off
setlocal

REM Build Windows executable for desktop_reminder.py
python -m pip install --upgrade pip
python -m pip install pyinstaller

REM --noconsole keeps no terminal window for Tkinter GUI apps
pyinstaller --noconfirm --clean --onefile --windowed --name 桌面提醒助手 desktop_reminder.py

echo.
echo Build complete. EXE path:
echo   dist\桌面提醒助手.exe
pause
