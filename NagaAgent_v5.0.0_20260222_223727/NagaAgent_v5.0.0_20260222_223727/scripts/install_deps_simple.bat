@echo off
REM 简化版依赖安装脚本
REM 适用于 Python 3.11.6

echo ============================================================
echo 弥娅依赖安装 (简化版)
echo ============================================================
echo.

echo [1/5] 安装核心依赖...
pip install PyQt5 PyQt5-Qt5 PyQt5-sip -i https://pypi.org/simple --no-deps
if errorlevel 1 echo PyQt5 安装失败 & pause

echo.
echo [2/5] 安装AI和通信库...
pip install openai dashscope httpx requests -i https://pypi.org/simple
if errorlevel 1 echo AI库安装失败 & pause

echo.
echo [3/5] 安装包豆AI依赖...
pip install opencv-python pyautogui pyperclip pillow -i https://pypi.org/simple
if errorlevel 1 echo 包豆AI依赖安装失败 & pause

echo.
echo [4/5] 安装其他依赖...
pip install aiohttp markdown pydantic sounddevice pystray -i https://pypi.org/simple
if errorlevel 1 echo 其他依赖安装失败 & pause

echo.
echo [5/5] 验证安装...
python -c "import PyQt5; print('PyQt5 OK')"
python -c "import openai; print('OpenAI OK')"
python -c "import cv2; print('OpenCV OK')"
python -c "import pyautogui; print('PyAutoGUI OK')"
python -c "import httpx; print('httpx OK')"

echo.
echo ============================================================
echo 安装完成!
echo 注意: 以下包在Python 3.14上可能无法编译:
echo   - pygame (音频播放)
echo   - onnxruntime (AI模型)
echo   - librosa (音频处理)
echo   - simpleaudio (音频)
echo 建议使用Python 3.11.6获得完整支持
echo ============================================================
pause
