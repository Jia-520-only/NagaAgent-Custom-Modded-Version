@echo off
chcp 65001 > nul
echo 检查Python版本...
python --version 2>&1 | findstr /R "3\.[1][1-9]" >nul
if errorlevel 1 (
    echo ❌ 需要Python 3.11或更高版本
    pause > nul
    exit /b 1
)
echo ✅ Python版本检查通过
echo.
python setup.py
pause > nul