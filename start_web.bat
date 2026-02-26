@echo off
setlocal
cd /d %~dp0

echo Starting professional flood simulation web UI: http://127.0.0.1:8000
python web_app.py --host 0.0.0.0 --port 8000
if errorlevel 1 (
  echo Failed to start web UI. Please ensure Python is installed and added to PATH.
  exit /b 1
)
endlocal
