@echo off
setlocal
cd /d "%~dp0"
set "MPLCONFIGDIR=%CD%\.cache\matplotlib"
if not exist ".venv\Scripts\python.exe" (
    echo Preparing your Python environment...
    python -m venv .venv
    if errorlevel 1 exit /b 1
)
".venv\Scripts\python.exe" -c "import pandas, scipy, matplotlib, requests" >nul 2>&1
if errorlevel 1 (
    echo Installing project dependencies...
    ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements-lock.txt
    if errorlevel 1 exit /b 1
)
".venv\Scripts\python.exe" project.py run
exit /b %errorlevel%
