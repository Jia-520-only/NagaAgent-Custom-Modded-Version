@echo off
chcp 65001 > nul
cd /d "%~dp0"
title GPT-SoVITS 语音合成服务

echo ======================================================
echo   GPT-SoVITS 语音合成服务
echo   端口: 9880
echo   说明: 本地定制化语音合成引擎
echo ======================================================
echo.

:: 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python 版本:
python --version
echo.

:: 检查虚拟环境
if not exist ".venv\Scripts\python.exe" (
    echo ⚠️ 未检测到虚拟环境，正在使用系统 Python
) else (
    echo ✅ 使用虚拟环境
    call .venv\Scripts\activate.bat
)

echo.
echo ======================================================
echo   GPT-SoVITS 配置检查
echo ======================================================
echo.

:: 检查配置文件
if exist "config.json" (
    echo ✅ 找到 config.json

    python -c "import json; config = json.load(open('config.json', 'r', encoding='utf-8')); print(f'  GPT-SoVITS启用: {config.get(\"tts\", {}).get(\"gpt_sovits_enabled\", False)}'); print(f'  服务地址: {config.get(\"tts\", {}).get(\"gpt_sovits_url\", \"未配置\")}'); print(f'  语速: {config.get(\"tts\", {}).get(\"gpt_sovits_speed\", 1.0)}'); print(f'  Top-K: {config.get(\"tts\", {}).get(\"gpt_sovits_top_k\", 15)}'); print(f'  Top-P: {config.get(\"tts\", {}).get(\"gpt_sovits_top_p\", 1.0)}'); print(f'  Temperature: {config.get(\"tts\", {}).get(\"gpt_sovits_temperature\", 1.0)}'); print(f'  免参考模式: {config.get(\"tts\", {}).get(\"gpt_sovits_ref_free\", False)}')"

    echo.
) else (
    echo ❌ 未找到 config.json
    pause
    exit /b 1
)

:: 检查是否启用
python -c "import json; enabled = json.load(open('config.json', 'r', encoding='utf-8')).get('tts', {}).get('gpt_sovits_enabled', False); exit(0 if enabled else 1)"
if errorlevel 1 (
    echo.
    echo ⚠️ GPT-SoVITS 未在 config.json 中启用
    echo    如需启用，请设置 tts.gpt_sovits_enabled 为 true
    echo.
    echo 是否继续启动? (Y/N)
    choice /c YN /n /m "请选择: "
    if errorlevel 2 exit /b 0
)

echo.
echo ======================================================
echo   GPT-SoVITS 状态说明
echo ======================================================
echo.
echo GPT-SoVITS 是一个本地语音合成引擎，需要单独安装和启动。
echo.
echo 前置步骤:
echo   1. 下载 GPT-SoVITS 项目
echo      GitHub: https://github.com/RVC-Boss/GPT-SoVITS
echo   2. 安装依赖（参考项目文档）
echo   3. 准备声学模型和参考音频
echo   4. 启动 GPT-SoVITS 推理服务（端口 9880）
echo.
echo 在本项目中的配置:
echo   - 默认URL: http://127.0.0.1:9880
echo   - 配置位置: config.json -> tts -> gpt_sovits_*
echo   - 默认引擎: edge_tts (可在 config.json 中修改)
echo.
echo 当前集成状态:
echo   ✅ GPT-SoVITS 集成代码已就绪
echo   ✅ 配置项已添加到 config.json
echo   ⚠️  GPT-SoVITS 服务需要单独启动
echo.
echo ======================================================
echo   集成测试
echo ======================================================
echo.

echo 正在测试 GPT-SoVITS 集成...
python voice/start_gptsovits.py

if errorlevel 1 (
    echo.
    echo ⚠️ GPT-SoVITS 服务未运行或不可用
    echo    这是正常的，如需使用请先启动 GPT-SoVITS 服务
) else (
    echo.
    echo ✅ GPT-SoVITS 集成测试通过
)

echo.
echo ======================================================
echo   使用说明
echo ======================================================
echo.
echo 1. 启动 GPT-SoVITS 服务（在 GPT-SoVITS 项目目录）
echo    2. 在 config.json 中设置 tts.gpt_sovits_enabled = true
echo    3. 在 config.json 中设置 tts.default_engine = "gpt_sovits"
echo    4. 重启主程序: start.bat
echo.
echo 配置参数说明:
echo   - gpt_sovits_url: GPT-SoVITS 服务地址
echo   - gpt_sovits_speed: 语速 (0.1-3.0, 默认 1.0)
echo   - gpt_sovits_top_k: Top-K 参数 (1-50, 默认 15)
echo   - gpt_sovits_top_p: Top-P 参数 (0.0-1.0, 默认 1.0)
echo   - gpt_sovits_temperature: 温度参数 (0.1-2.0, 默认 1.0)
echo   - gpt_sovits_ref_free: 是否免参考模式 (默认 false)
echo   - gpt_sovits_ref_text: 参考文本
echo   - gpt_sovits_ref_audio_path: 参考音频路径
echo.
echo 按任意键退出...
pause >nul
