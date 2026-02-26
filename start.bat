@echo off
setlocal
cd /d %~dp0

echo [1/2] Running urban drainage storm simulation...
python drainage_simulator.py --config sample_scenario.json --report-file simulation_report.md
if errorlevel 1 (
  echo Simulation failed. Please ensure Python is installed and added to PATH.
  exit /b 1
)

echo [2/2] Done. Report file: %~dp0simulation_report.md
endlocal
