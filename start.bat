@echo off
chcp 65001 > nul
cd /d "%~dp0"
title Naga Agent
if exist ".venv\Scripts\python.exe" (
    call .venv\Scripts\activate.bat
    python main.py
) else (
    echo ❌ 未检测到虚拟环境，请先运行 setup.bat 进行初始化，或手动配置。
    pause > nul
)  