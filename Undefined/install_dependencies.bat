@echo off
setlocal enabledelayedexpansion
REM 尝试设置UTF-8编码，如果失败则忽略
chcp 65001 > nul 2>&1
echo ========================================
echo     Undefined Dependency Installer
echo ========================================
echo.

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [Error] Python not found, please install Python 3.11+
    echo.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] Checking Python version...
python --version
echo.

echo [2/5] Upgrading pip...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
if %ERRORLEVEL% neq 0 (
    echo [Warning] pip upgrade may have issues, continuing...
)
echo.

echo [3/5] Checking uv package manager...
where uv >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Detected uv, using uv to install dependencies...
    uv sync
    if %ERRORLEVEL% neq 0 (
        echo [Warning] uv installation may have issues, trying pip...
    ) else (
        echo [OK] uv dependency installation completed
        goto install_complete
    )
) else (
    echo [Info] uv not detected, using pip...
    echo [Info] For faster installation, install uv: pip install uv
)

echo.
echo [4/5] Installing dependencies from pyproject.toml...

REM Check if pyproject.toml exists
if exist "pyproject.toml" (
    pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
    if %ERRORLEVEL% neq 0 (
        echo [Warning] Installation from pyproject.toml may have issues
    )
) else (
    echo [Warning] pyproject.toml not found
)

echo.
echo [5/5] Verifying core dependencies...
python -c "import httpx; import aiofiles; print('[OK] Core dependencies verified')" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [Error] Dependency verification failed
    echo.
    echo Try manual installation:
    echo   pip install httpx aiofiles aiohttp anthropic openai
    pause
    exit /b 1
)

:install_complete
echo.
echo ========================================
echo     Installation Complete!
echo ========================================
echo.
echo Tips:
echo   - Dependencies installed in current Python environment
echo   - For virtual environment: python -m venv venv
echo   - To activate virtual: venv\Scripts\activate
echo   - Config file: config.toml
echo.
pause
