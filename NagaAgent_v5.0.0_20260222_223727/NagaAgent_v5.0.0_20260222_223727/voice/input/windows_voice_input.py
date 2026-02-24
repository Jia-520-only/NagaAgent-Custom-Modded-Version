#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 语音输入模块 - 简化版
在聊天窗口中使用 Windows 自带的语音识别
"""
import logging
import threading
from typing import Optional, Callable

logger = logging.getLogger("WindowsVoiceInput")

class WindowsVoiceInput:
    """Windows语音输入管理器"""

    def __init__(self):
        self.recognizer = None
        self.is_active = False
        self.on_text: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_status: Optional[Callable[[str], None]] = None
        self._thread = None

    def start(self, on_text: Callable[[str], None], on_error: Optional[Callable[[str], None]] = None, on_status: Optional[Callable[[str], None]] = None):
        """启动语音识别"""
        if self.is_active:
            logger.warning("语音识别已在运行")
            return False

        self.on_text = on_text
        self.on_error = on_error
        self.on_status = on_status

        try:
            from voice.input.windows_speech import WindowsSpeechRecognizer
            self.recognizer = WindowsSpeechRecognizer()

            # 检查是否可用
            if not self.recognizer.is_available():
                error_msg = "Windows语音识别不可用，请安装 SpeechRecognition 和 pyaudio 库"
                logger.error(error_msg)
                if self.on_error:
                    self.on_error(error_msg)
                return False

            # 启动识别
            success = self.recognizer.start_listening(
                on_result=self._on_text,
                on_error=self._on_error,
                on_status=self._on_status
            )

            if success:
                self.is_active = True
                logger.info("Windows语音输入已启动")
                return True
            else:
                return False

        except Exception as e:
            import traceback
            error_msg = f"启动Windows语音输入失败: {e}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            if self.on_error:
                self.on_error(error_msg)
            return False

    def stop(self):
        """停止语音识别"""
        if not self.is_active:
            return

        if self.recognizer:
            self.recognizer.stop_listening()
            self.recognizer = None

        self.is_active = False
        logger.info("Windows语音输入已停止")

    def _on_text(self, text: str):
        """处理识别结果"""
        if self.on_text:
            self.on_text(text)

    def _on_error(self, error: str):
        """处理错误"""
        if self.on_error:
            self.on_error(error)

    def _on_status(self, status: str):
        """处理状态"""
        if self.on_status:
            self.on_status(status)

    def is_available(self) -> bool:
        """检查Windows语音输入是否可用"""
        try:
            from voice.input.windows_speech import WindowsSpeechRecognizer
            recognizer = WindowsSpeechRecognizer()
            return recognizer.is_available()
        except Exception as e:
            logger.error(f"检查Windows语音输入可用性失败: {e}")
            return False


# 单例实例
_windows_voice_input = None

def get_windows_voice_input():
    """获取Windows语音输入单例"""
    global _windows_voice_input
    if _windows_voice_input is None:
        _windows_voice_input = WindowsVoiceInput()
    return _windows_voice_input
