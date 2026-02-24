@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

REM Switch to script directory
cd /d "%~dp0"
echo Current directory: %CD%
echo.

echo ============================================================
echo              NagaAgent Install Script v1.0
echo         Auto Install - Env Check - Dependencies
echo ============================================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [Tip] Run as Administrator recommended
    echo.
)

REM 检查 Python 是否安装
echo [1/6] Checking Python environment...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [Error] Python not found, please install Python 3.11 or later
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python version: %PYTHON_VERSION%
echo.

REM 检查 pip
echo [2/6] Checking pip...
pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [Error] pip not found, please check Python installation
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('pip --version 2^>^&1') do set PIP_VERSION=%%i
echo [OK] pip version: %PIP_VERSION%
echo.

REM 检查虚拟环境
echo [3/6] Checking virtual environment...
if exist ".venv" (
    echo [Warning] Existing virtual environment detected
    choice /C YN /M "Delete and recreate?"
    if errorlevel 2 (
        echo Keeping existing .venv
    ) else (
        echo Deleting existing .venv...
        rmdir /s /q .venv
        echo Creating new .venv...
        python -m venv .venv
        if %errorLevel% neq 0 (
            echo [Error] Failed to create virtual environment
            pause
            exit /b 1
        )
    )
) else (
    echo Creating virtual environment...
    python -m venv .venv
    if %errorLevel% neq 0 (
        echo [Error] Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo [OK] Virtual environment created
echo.

REM 激活虚拟环境
echo [4/6] Activating virtual environment...
call .venv\Scripts\activate.bat
if %errorLevel% neq 0 (
    echo [Error] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip (this may take a while)...
python -m pip install --upgrade pip -i https://pypi.org/simple
if %errorLevel% neq 0 (
    echo [Warning] Failed to upgrade pip, continuing with current version
    echo.
) else (
    echo [OK] pip upgraded
)
echo.

REM 安装依赖
echo [5/6] Installing project dependencies...
if exist "requirements_install.txt" (
    pip install -r requirements_install.txt -i https://pypi.org/simple --default-timeout=300
    if %errorLevel% neq 0 (
        echo [Warning] Some dependencies failed to install, but continuing...
    )
    echo [OK] Dependencies installed (some may have failed)
) else (
    echo [Warning] requirements_install.txt not found, skipping dependency installation
)
echo.

REM Run configuration wizard
echo [6/6] Configuration...
echo.

if exist "config.json" (
    echo [TIP] config.json already exists
    choice /C YN /M "Run configuration wizard to overwrite?"
    if errorlevel 2 (
        echo Skipping configuration wizard
        echo.
        goto :install_complete
    )
)

echo Starting configuration wizard...
echo.
python install_wizard.py

:install_complete

echo.
echo ============================================================
echo.
echo [SUCCESS] Installation completed!
echo.
echo Next steps:
echo   1. Complete configuration following the wizard
echo   2. Install and start Neo4j if needed
echo   3. Install and start GPT-SoVITS if needed
echo   4. Start program:
echo      - start.bat      (Start main program)
echo      - start_all.bat  (Start all services)
echo.
echo ============================================================
echo.

pause
