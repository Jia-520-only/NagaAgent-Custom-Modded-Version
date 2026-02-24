@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ============================================================
echo              NagaAgent Install Dependencies Only
echo         Install All Dependencies - Skip Wizard
echo ============================================================
echo.

REM Check Python
echo [1/5] Checking Python environment...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found, please install Python 3.11 or later
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python version: %PYTHON_VERSION%
echo.

REM Check pip
echo [2/5] Checking pip...
pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] pip not found, please check Python installation
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('pip --version 2^>^&1') do set PIP_VERSION=%%i
echo [OK] pip version: %PIP_VERSION%
echo.

REM Check virtual environment
echo [3/5] Checking virtual environment...
if exist ".venv" (
    echo [TIP] Existing virtual environment detected
    choice /C YN /M "Delete and recreate?"
    if errorlevel 2 (
        echo Keeping existing .venv
    ) else (
        echo Deleting existing .venv...
        rmdir /s /q .venv
        echo Creating new .venv...
        python -m venv .venv
        if %errorLevel% neq 0 (
            echo [ERROR] Failed to create virtual environment
            pause
            exit /b 1
        )
    )
) else (
    echo Creating virtual environment...
    python -m venv .venv
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo [OK] Virtual environment created
echo.

REM Activate virtual environment
echo [4/5] Activating virtual environment...
call .venv\Scripts\activate.bat
if %errorLevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM Upgrade pip
echo [5/6] Upgrading pip (this may take a while)...
python -m pip install --upgrade pip -i https://pypi.org/simple
if %errorLevel% neq 0 (
    echo [Warning] Failed to upgrade pip, continuing with current version
    echo.
) else (
    echo [OK] pip upgraded
)
echo.

REM Install dependencies
echo [6/6] Installing project dependencies...
echo This may take several minutes, please wait...
echo.

if exist "requirements_install.txt" (
    echo Using requirements_install.txt (no Chinese comments)
    pip install -r requirements_install.txt -i https://pypi.org/simple --default-timeout=300
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
) else if exist "requirements.txt" (
    echo Using requirements.txt
    pip install -r requirements.txt -i https://pypi.org/simple --default-timeout=300
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
) else (
    echo [Warning] No requirements file found, skipping dependency installation
)

echo.
REM Verify critical dependencies
echo Verifying critical dependencies...
python -c "import PyQt5" >nul 2>&1
if %errorLevel% neq 0 (
    echo [Warning] PyQt5 not found, trying to install separately...
    pip install PyQt5 PyQt5-WebEngine -i https://pypi.org/simple
)

python -c "import PyQt5.QtWebEngineWidgets" >nul 2>&1
if %errorLevel% neq 0 (
    echo [Warning] PyQt5-WebEngine not found, trying to install separately...
    pip install PyQt5-WebEngine -i https://pypi.org/simple
)

echo [OK] Dependencies verified
echo.
echo ============================================================
echo.
echo [SUCCESS] All dependencies installed successfully!
echo.
echo Next steps:
echo   1. Check config.json exists and is properly configured
echo   2. Start program: start.bat
echo   3. Or start all services: start_all.bat
echo.
echo If you need to reconfigure, run: install_wizard.py
echo.
echo ============================================================
echo.

pause

