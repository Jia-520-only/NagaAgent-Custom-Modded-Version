@echo off
chcp 65001 >nul
echo ========================================
echo   停止 NagaAgent + OpenClaw 所有服务
echo ========================================
echo.

echo [1/3] 停止 OpenClaw Gateway...
call "%~dp0stop_openclaw.bat"

echo.
echo [2/3] 检查 NagaAgent 进程...
tasklist | findstr /i "python.exe" >nul
if errorlevel 0 (
    echo 发现 python 进程
    tasklist | findstr /i "python.exe"
    echo.
    echo 手动终止 NagaAgent:
    echo   方法1: 在 NagaAgent 窗口按 Ctrl+C
    echo   方法2: 关闭 NagaAgent 窗口
    echo   方法3: 使用任务管理器
    echo.
    set /p kill_python="是否强制终止所有 python 进程？(y/n): "
    if /i "%kill_python%"=="y" (
        echo 正在终止 python 进程...
        taskkill /F /IM python.exe >nul 2>&1
        if errorlevel 0 (
            echo ✅ Python 进程已终止
        ) else (
            echo ❌ 终止失败，可能需要管理员权限
        )
    )
) else (
    echo ✅ 未发现 NagaAgent 进程
)

echo.
echo [3/3] 最终检查...
timeout /t 1 /nobreak >nul
netstat -ano | findstr :18789 >nul
if errorlevel 1 (
    echo ✅ 端口 18789 已释放
) else (
    echo ⚠️  端口 18789 仍被占用
)

tasklist | findstr /i "python.exe" >nul
if errorlevel 1 (
    echo ✅ Python 进程已清理
)

echo.
echo ========================================
echo   清理完成
echo ========================================
echo.
pause
