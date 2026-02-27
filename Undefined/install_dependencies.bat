@echo off
chcp 65001 >nul
title Undefined 一键安装依赖脚本
color 0B

echo ========================================
echo      Undefined 一键安装依赖脚本
echo ========================================
echo.

REM 检查 Python 版本
echo [1/4] 检查 Python 版本...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.11 或更高版本
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [成功] 检测到 Python %PYTHON_VERSION%
echo.

REM 检查是否在 Undefined 目录下
if not exist "pyproject.toml" (
    echo [错误] 未找到 pyproject.toml，请确保在 Undefined 根目录下运行此脚本
    pause
    exit /b 1
)

REM 检查并安装 uv
echo [2/4] 检查 uv 包管理器...
uv --version >nul 2>&1
if errorlevel 1 (
    echo [提示] 未检测到 uv，正在安装 uv...
    python -m pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo [错误] uv 安装失败
        pause
        exit /b 1
    )
) else (
    echo [成功] uv 已安装
)
echo.

REM 使用 uv 同步依赖
echo [3/4] 正在安装 Undefined 依赖...
echo 这可能需要几分钟时间，请耐心等待...
echo.

uv sync
if errorlevel 1 (
    echo [错误] 依赖安装失败
    echo.
    echo [提示] 如果遇到网络问题，可以尝试：
    echo 1. 使用国内镜像源
    echo 2. 手动运行: uv pip install -e .
    pause
    exit /b 1
)
echo.

REM 安装 Playwright 浏览器
echo [4/4] 安装 Playwright 浏览器...
uv run playwright install chromium
if errorlevel 1 (
    echo [警告] Playwright 浏览器安装失败，部分功能可能无法使用
    echo [提示] 可以稍后手动运行: uv run playwright install chromium
) else (
    echo [成功] Playwright 浏览器安装完成
)
echo.

REM 创建配置文件
echo [配置] 检查配置文件...
if not exist "config.toml" (
    if exist "config.toml.example" (
        echo [提示] 复制 config.toml.example 为 config.toml
        copy config.toml.example config.toml >nul
        echo [成功] 配置文件已创建，请根据需要修改 config.toml
    )
)

echo ========================================
echo           安装完成！
echo ========================================
echo.
echo 下一步：
echo 1. 编辑 config.toml 配置文件，填入你的 API Key 和 QQ 号
echo 2. 启动 Undefined: uv run Undefined
echo 3. 或使用 WebUI: uv run Undefined-webui
echo.
pause
