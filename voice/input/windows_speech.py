#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 11 本地语音识别模块
使用 speechrecognition 库和 Windows Speech API 进行语音识别
"""
import sys
import logging
import time
import threading
import queue
from typing import Optional, Callable

logger = logging.getLogger("WindowsSpeech")

class WindowsSpeechRecognizer:
    """Windows语音识别器"""

    def __init__(self):
        self.is_listening = False
        self.on_result: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_status: Optional[Callable[[str], None]] = None
        self.recognition_thread: Optional[threading.Thread] = None
        self.result_queue = queue.Queue()
        self.recognizer = None

    def start_listening(self, on_result: Callable[[str], None], on_error: Optional[Callable[[str], None]] = None, on_status: Optional[Callable[[str], None]] = None):
        """
        开始监听语音输入

        Args:
            on_result: 识别结果回调函数
            on_error: 错误回调函数
            on_status: 状态回调函数
        """
        if self.is_listening:
            logger.warning("已经在监听中")
            return False

        self.on_result = on_result
        self.on_error = on_error
        self.on_status = on_status
        self.is_listening = True

        # 启动识别线程
        self.recognition_thread = threading.Thread(target=self._recognition_loop, daemon=True)
        self.recognition_thread.start()

        if self.on_status:
            self.on_status("listening")
        logger.info("Windows语音识别已启动")
        return True

    def stop_listening(self):
        """停止监听"""
        if not self.is_listening:
            return

        self.is_listening = False

        if self.recognition_thread and self.recognition_thread.is_alive():
            self.recognition_thread.join(timeout=3)

        logger.info("Windows语音识别已停止")

    def _recognition_loop(self):
        """识别循环"""
        try:
            # 尝试导入 speechrecognition 库
            try:
                import speech_recognition as sr
            except ImportError:
                error_msg = "需要安装 speechrecognition 库：pip install SpeechRecognition pyaudio"
                logger.error(error_msg)
                if self.on_error:
                    self.on_error(error_msg)
                self.is_listening = False
                return

            # 检查是否在Windows上运行
            if sys.platform != 'win32':
                error_msg = "Windows语音识别仅在Windows上可用"
                logger.error(error_msg)
                if self.on_error:
                    self.on_error(error_msg)
                self.is_listening = False
                return

            # 创建识别器
            self.recognizer = sr.Recognizer()

            # 调整识别器参数
            self.recognizer.energy_threshold = 300  # 能量阈值
            self.recognizer.dynamic_energy_threshold = True  # 动态能量阈值
            self.recognizer.pause_threshold = 0.8  # 停顿阈值
            self.recognizer.phrase_threshold = 0.3  # 短语阈值
            self.recognizer.non_speaking_duration = 0.5  # 非说话时长

            # 使用麦克风
            with sr.Microphone() as source:
                # 在嘈杂环境中校准麦克风
                logger.info("正在校准麦克风环境噪声...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("麦克风校准完成，开始语音识别...")

                while self.is_listening:
                    try:
                        # 监听音频
                        if self.on_status:
                            self.on_status("listening")

                        audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=None)

                        # 尝试识别（使用 Google 语音识别作为备选）
                        try:
                            # 优先尝试使用 Google 语音识别（免费且准确）
                            text = self.recognizer.recognize_google(audio, language='zh-CN')
                            logger.info(f"识别结果: {text}")

                            if self.on_result:
                                self.on_result(text)

                        except sr.UnknownValueError:
                            # 无法理解音频
                            logger.debug("无法识别语音内容")
                            continue

                        except sr.RequestError as e:
                            # API 请求错误
                            error_msg = f"语音识别API请求失败: {e}"
                            logger.error(error_msg)
                            if self.on_error:
                                self.on_error(error_msg)

                    except sr.WaitTimeoutError:
                        # 等待超时
                        continue

                    except Exception as e:
                        # 其他错误
                        error_msg = f"语音识别错误: {e}"
                        logger.error(error_msg)
                        if self.on_error:
                            self.on_error(error_msg)
                        # 继续尝试
                        time.sleep(0.5)

        except Exception as e:
            import traceback
            error_msg = f"语音识别初始化失败: {e}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            if self.on_error:
                self.on_error(error_msg)
            self.is_listening = False

    def is_available(self) -> bool:
        """检查Windows语音识别是否可用"""
        if sys.platform != 'win32':
            return False

        try:
            import speech_recognition as sr
            import pyaudio
            # 尝试创建识别器和麦克风实例
            recognizer = sr.Recognizer()
            sr.Microphone()
            return True
        except ImportError as e:
            logger.warning(f"Windows语音识别依赖缺失: {e}")
            return False
        except Exception as e:
            logger.error(f"检查Windows语音识别可用性失败: {e}")
            return False


def test_windows_speech():
    """测试Windows语音识别"""
    recognizer = WindowsSpeechRecognizer()

    def on_result(text):
        print(f"识别结果: {text}")

    def on_error(error):
        print(f"错误: {error}")

    def on_status(status):
        print(f"状态: {status}")

    if recognizer.is_available():
        print("Windows语音识别可用")
        recognizer.start_listening(on_result, on_error, on_status)
        print("正在监听...（按 Ctrl+C 停止）")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n停止监听...")
            recognizer.stop_listening()
    else:
        print("Windows语音识别不可用")
        print("请安装依赖：pip install SpeechRecognition pyaudio")


if __name__ == "__main__":
    test_windows_speech()
