@echo off
chcp 65001 > nul
cd /d "%~dp0"
title NagaAgent

if exist ".venv\Scripts\python.exe" (
    call .venv\Scripts\activate.bat
    python main.py
    if errorlevel 1 (
        echo.
        echo [Error] Program exited with error code: %errorlevel%
        echo Check logs for details.
        pause
    )
) else (
    echo ============================================================
    echo [ERROR] Virtual environment not found!
    echo.
    echo Please run one of the following:
    echo   1. install.bat     - Full installation with setup wizard
    echo   2. install.sh      - Full installation (Linux/Mac)
    echo.
    echo Or create manually:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements_install.txt
    echo ============================================================
    pause
)  