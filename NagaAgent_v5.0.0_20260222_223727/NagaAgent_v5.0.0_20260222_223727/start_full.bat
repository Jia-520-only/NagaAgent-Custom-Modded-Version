@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ======================================================
echo   MIYA AI - Full Feature Startup Script
echo   Version: 4.0 Modified
echo ======================================================
echo.

:: Check Python environment
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not detected, please install Python 3.11+
    pause
    exit /b 1
)

echo [OK] Python version:
python --version
echo.

:: Check virtual environment
if not exist ".venv\Scripts\python.exe" (
    echo [TIP] Virtual environment not detected, creating...
    call setup.bat
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

:: Check VCPToolBox
echo ======================================================
echo   Checking VCPToolBox Advanced Memory System
echo ======================================================
echo.

node --version >nul 2>&1
if errorlevel 1 (
    echo [TIP] Node.js not detected, VCPToolBox will not start
    echo    Download: https://nodejs.org/
) else (
    if exist "VCPToolBox\config.env" (
        echo [OK] VCPToolBox config file exists
        echo    TIP: You can run start_vcptoolbox.bat to start VCPToolBox separately
    ) else (
        echo [TIP] VCPToolBox config file not found
    )
)

echo.
echo ======================================================
echo   Feature Status
echo ======================================================
echo.

python -c "import json; config = json.load(open('config.json', 'r', encoding='utf-8')); print(f'Consciousness System: {\"[OK] Enabled\" if config.get(\"consciousness\", {}).get(\"enabled\") else \"[ ] Disabled\"}'); print(f'API Server: {\"[OK] Enabled\" if config.get(\"api_server\", {}).get(\"enabled\") else \"[ ] Disabled\"} (Port {config.get(\"api_server\", {}).get(\"port\", \"N/A\")})'); print(f'Agent Server: {\"[OK] Enabled\" if config.get(\"agentserver\", {}).get(\"enabled\") else \"[ ] Disabled\"} (Port {config.get(\"agentserver\", {}).get(\"port\", \"N/A\")})'); print(f'MCP Server: {\"[OK] Enabled\" if config.get(\"mcpserver\", {}).get(\"enabled\") else \"[ ] Disabled\"} (Port {config.get(\"mcpserver\", {}).get(\"port\", \"N/A\")})'); print(f'GRAG Memory: {\"[OK] Enabled\" if config.get(\"grag\", {}).get(\"enabled\") else \"[ ] Disabled\"}'); print(f'QQ Bot: {\"[OK] Enabled\" if config.get(\"qq_wechat\", {}).get(\"qq\", {}).get(\"enabled\") else \"[ ] Disabled\"}'); print(f'Voice: {\"[OK] Enabled\" if config.get(\"system\", {}).get(\"voice_enabled\") else \"[ ] Disabled\"}')"

echo.
echo ======================================================
echo   系统即将启动
echo ======================================================
echo.

pause

:: 启动主程序
call .venv\Scripts\activate.bat
python main.py
