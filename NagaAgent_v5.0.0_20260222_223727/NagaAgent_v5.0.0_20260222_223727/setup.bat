@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo Checking Python version...
python --version 2>&1 | findstr /R "3\.[1][1-9]" >nul
if errorlevel 1 (
    echo [ERROR] Python 3.11 or higher required
    pause > nul
    exit /b 1
)
echo [OK] Python version check passed
echo.
python setup.py
pause > nul