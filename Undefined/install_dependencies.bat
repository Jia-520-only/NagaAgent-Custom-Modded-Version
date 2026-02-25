@echo off
REM chcp 65001 > nul
echo ========================================
echo     Undefined 依赖安装脚本
echo ========================================
echo.

cd /d "%~dp0"

REM 检查 Python 是否可用
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.11+
    echo.
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] 检查 Python 版本...
python --version
echo.

echo [2/5] 升级 pip 到最新版本...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
if %ERRORLEVEL% neq 0 (
    echo [警告] pip 升级可能存在问题，继续安装...
)
echo.

echo [3/5] 检查是否使用 uv 包管理器...
where uv >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] 检测到 uv，使用 uv 安装依赖...
    uv sync
    if %ERRORLEVEL% neq 0 (
        echo [警告] uv 安装可能存在问题，尝试使用 pip...
    ) else (
        echo [OK] uv 依赖安装完成
        goto install_complete
    )
) else (
    echo [提示] 未检测到 uv，使用 pip 安装依赖...
    echo [提示] 如需更快速度，可安装 uv: pip install uv
)

echo.
echo [4/5] 使用 pip 安装依赖 (从 pyproject.toml)...

REM 检查是否存在 pyproject.toml
if exist "pyproject.toml" (
    pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
    if %ERRORLEVEL% neq 0 (
        echo [警告] 从 pyproject.toml 安装可能存在问题
    )
) else (
    echo [警告] 未找到 pyproject.toml
)

echo.
echo [5/5] 验证核心依赖...
python -c "import httpx; import aiofiles; print('[OK] 核心依赖验证成功')" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [错误] 依赖安装验证失败
    echo.
    echo 请尝试手动安装依赖:
    echo   pip install httpx aiofiles aiohttp anthropic openai
    pause
    exit /b 1
)

:install_complete
echo.
echo ========================================
echo     安装完成！
echo ========================================
echo.
echo 提示：
echo   - 依赖已安装在当前 Python 环境
echo   - 如需虚拟环境，请运行: python -m venv venv
echo   - 如需激活虚拟环境: venv\Scripts\activate
echo   - 配置文件: config.toml
echo.
pause
