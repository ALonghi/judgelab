@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3.13 -m venv .venv
  if errorlevel 1 (
    echo Python 3.13 could not create the environment. See the README for manual setup with Python 3.13 or newer.
    pause
    exit /b 1
  )
)
.venv\Scripts\python.exe run.py --check >nul 2>&1
if errorlevel 1 (
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Dependency installation failed. Check your connection and read README.md.
    pause
    exit /b 1
  )
)
.venv\Scripts\python.exe run.py %*
pause
