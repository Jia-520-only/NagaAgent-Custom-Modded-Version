@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ======================================================
echo   弥娅 AI - 完整功能启动脚本
echo   版本: 4.0 Modified
echo ======================================================
echo.

:: 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到 Python，请先安装 Python 3.11+
    pause
    exit /b 1
)

echo ✅ Python 版本:
python --version
echo.

:: 检查虚拟环境
if not exist ".venv\Scripts\python.exe" (
    echo ⚠️ 未检测到虚拟环境，正在创建...
    call setup.bat
    if errorlevel 1 (
        echo ❌ 虚拟环境创建失败
        pause
        exit /b 1
    )
)

:: 检查 VCPToolBox
echo ======================================================
echo   检查 VCPToolBox 高级记忆系统
echo ======================================================
echo.

node --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  未检测到 Node.js，VCPToolBox 将无法启动
    echo    下载地址: https://nodejs.org/
) else (
    if exist "VCPToolBox\config.env" (
        echo ✅ VCPToolBox 配置文件存在
        echo    提示: 可以运行 start_vcptoolbox.bat 单独启动 VCPToolBox
    ) else (
        echo ⚠️  VCPToolBox 配置文件不存在
    )
)

echo.
echo ======================================================
echo   功能启用状态
echo ======================================================
echo.

python -c "import json; config = json.load(open('config.json', 'r', encoding='utf-8')); print(f'初意识系统: {\"✅ 启用\" if config.get(\"consciousness\", {}).get(\"enabled\") else \"❌ 未启用\"}'); print(f'API服务器: {\"✅ 启用\" if config.get(\"api_server\", {}).get(\"enabled\") else \"❌ 未启用\"} (端口 {config.get(\"api_server\", {}).get(\"port\", \"N/A\")})'); print(f'Agent服务器: {\"✅ 启用\" if config.get(\"agentserver\", {}).get(\"enabled\") else \"❌ 未启用\"} (端口 {config.get(\"agentserver\", {}).get(\"port\", \"N/A\")})'); print(f'MCP服务器: {\"✅ 启用\" if config.get(\"mcpserver\", {}).get(\"enabled\") else \"❌ 未启用\"} (端口 {config.get(\"mcpserver\", {}).get(\"port\", \"N/A\")})'); print(f'GRAG记忆系统: {\"✅ 启用\" if config.get(\"grag\", {}).get(\"enabled\") else \"❌ 未启用\"}'); print(f'QQ机器人: {\"✅ 启用\" if config.get(\"qq_wechat\", {}).get(\"qq\", {}).get(\"enabled\") else \"❌ 未启用\"}'); print(f'语音功能: {\"✅ 启用\" if config.get(\"system\", {}).get(\"voice_enabled\") else \"❌ 未启用\"}')"

echo.
echo ======================================================
echo   系统即将启动
echo ======================================================
echo.

pause

:: 启动主程序
call .venv\Scripts\activate.bat
python main.py
