@echo off
chcp 65001 > nul
echo ========================================
echo     Undefined 依赖安装脚本
echo ========================================
echo.

cd /d "%~dp0"
cd Undefined

REM 检查 pip 是否可用
where pip >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] 未找到 pip，请先安装 Python
    pause
    exit /b 1
)

echo [1/5] 检查 Python 版本...
python --version
if %ERRORLEVEL% neq 0 (
    echo [错误] 未找到 Python
    pause
    exit /b 1
)

echo.
echo [2/5] 升级 pip 到最新版本...
python -m pip install --upgrade pip

echo.
echo [3/5] 安装核心依赖...
pip install -r requirements.txt --upgrade
if %ERRORLEVEL% neq 0 (
    echo [警告] 核心依赖安装可能存在问题
)

echo.
echo [4/5] 安装可选依赖 (如果有)...
if exist requirements-optional.txt (
    pip install -r requirements-optional.txt --upgrade
    if %ERRORLEVEL% neq 0 (
        echo [警告] 可选依赖安装可能存在问题
    )
)

echo.
echo [5/5] 验证安装...
python -c "import httpx; import aiofiles; import tomllib; print('[OK] 核心依赖验证成功')"
if %ERRORLEVEL% neq 0 (
    echo [错误] 依赖安装验证失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo     安装完成！
echo ========================================
echo.
echo 提示：
echo   - 核心依赖已安装在当前 Python 环境
echo   - 如果需要虚拟环境，请先激活 venv
echo   - 查看 requirements.txt 了解依赖列表
echo.
pause
