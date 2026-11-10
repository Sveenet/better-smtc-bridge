@echo off
setlocal
cd /d "%~dp0"
if exist "Better SMTC Bridge.exe" (
  start "" "Better SMTC Bridge.exe"
  exit /b
)
if not exist ".venv\Scripts\pythonw.exe" (
  echo Setting up Better SMTC Bridge in this folder for the first time...
  py -3.14 -m venv .venv
  if errorlevel 1 goto failed
  .venv\Scripts\python.exe install_deps.py requirements.txt
  if errorlevel 1 goto failed
)
start "" ".venv\Scripts\pythonw.exe" bridge.py
exit /b
:failed
echo.
echo Setup could not finish. Install Python 3.14 from python.org, then try again.
echo The standalone Windows release does not need Python installed.
pause
exit /b 1
