@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ====================================
echo NagaAgent 一键启动脚本
echo ====================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found, please install Python 3.11+
    pause
    exit /b 1
)

echo [OK] Python installed
echo.

echo ====================================
echo [1/4] 启动GPT-SoVITS...
echo ====================================
echo.
echo 请确保GPT-SoVITS已安装
echo 请在 config.json 中配置 gpt_sovits_url
echo 示例: "gpt_sovits_url": "http://127.0.0.1:9880"
echo.
pause

echo.
echo ====================================
echo [2/4] 检查NapCat-Go...
echo ====================================
echo.
echo 请确保NapCat-Go正在运行
echo 默认端口: 3000 (HTTP), 3001 (WebSocket)
echo.
echo 如果未启动，请运行NapCat.exe
echo.
pause

echo.
echo ====================================
echo [3/4] 检查配置...
echo ====================================
echo.

if not exist config.json (
    echo ERROR: config.json not found
    pause
    exit /b 1
)

echo [OK] config.json exists
echo.
echo 请在 config.json 中查看完整配置
echo 包括 QQ、微信、语音等设置
echo.
pause

echo.
echo ====================================
echo [4/4] 启动NagaAgent主程序...
echo ====================================
echo.

REM Check if uv is available
where uv >nul 2>&1
if errorlevel 1 (
    echo [TIP] uv not found, using virtual environment
    echo.
    if exist ".venv\Scripts\python.exe" (
        call .venv\Scripts\activate.bat
        python main.py
    ) else (
        echo [ERROR] Virtual environment not found, please run install.bat first
        pause > nul
        exit /b 1
    )
) else (
    echo Starting...
    echo.
    echo TIP:
    echo 1. QQ auto-reply will start automatically
    echo 2. WeChat QR code will be displayed (if WeChat enabled)
    echo 3. Send message to bot QQ to test
    echo.
    echo ====================================
    uv run python main.py
)

if %errorlevel% neq 0 (
    echo.
    echo ====================================
    echo Program exited with error code: %errorlevel%
    echo ====================================
)

pause
