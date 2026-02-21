@echo off
chcp 65001 >nul
echo ====================================
echo NagaAgent 一键启动脚本
echo ====================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.11+
    pause
    exit /b 1
)

echo ✅ Python已安装
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
    echo ❌ 未找到config.json
    pause
    exit /b 1
)

echo ✅ config.json存在
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

REM 检查uv是否可用
where uv >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 未找到uv，使用虚拟环境启动
    echo.
    if exist ".venv\Scripts\python.exe" (
        call .venv\Scripts\activate.bat
        python main.py
    ) else (
        echo ❌ 未检测到虚拟环境，请先运行 setup.bat 进行初始化
        pause > nul
        exit /b 1
    )
) else (
    echo 正在启动...
    echo.
    echo 提示:
    echo 1. QQ自动回复会随程序自动启动
    echo 2. 微信登录二维码会在控制台显示（如果启用微信）
    echo 3. 给机器人QQ (3681817929) 发送消息测试
    echo.
    echo ====================================
    uv run python main.py
)

if %errorlevel% neq 0 (
    echo.
    echo ====================================
    echo 程序异常退出，返回码: %errorlevel%
    echo ====================================
)

pause
