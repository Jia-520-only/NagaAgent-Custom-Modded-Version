@echo off
chcp 65001 > nul
cd /d "%~dp0"
title VCPToolBox 高级记忆系统

echo ======================================================
echo   VCPToolBox 高级记忆系统
echo   端口: 6005
echo   AI Provider: DeepSeek
echo ======================================================
echo.

:: 检查 Node.js 是否安装
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到 Node.js，请先安装 Node.js
    echo    下载地址: https://nodejs.org/
    pause
    exit /b 1
)

echo ✅ Node.js 版本:
node --version
echo.

:: 检查是否已安装依赖
if not exist "node_modules\" (
    echo 📦 首次运行，正在安装依赖...
    echo    这可能需要几分钟，请耐心等待...
    call npm install
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
    echo.
    echo ✅ 依赖安装完成
    echo.
)

:: 检查配置文件
if not exist "config.env" (
    echo ❌ 未找到配置文件 config.env
    echo    请确保配置文件存在
    pause
    exit /b 1
)

echo 🚀 正在启动 VCPToolBox...
echo.
echo 服务地址: http://127.0.0.1:6005
echo 按 Ctrl+C 停止服务
echo.
echo ======================================================
echo.

npm start

if errorlevel 1 (
    echo.
    echo ❌ 服务启动失败
    pause
)
