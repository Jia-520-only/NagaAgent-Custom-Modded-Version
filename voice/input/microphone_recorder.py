#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 麦克风录音模块
使用 pyaudio 录制音频数据
"""
import sys
import logging
import threading
import time
from typing import Optional, Callable
import numpy as np

logger = logging.getLogger("MicrophoneRecorder")

class MicrophoneRecorder:
    """麦克风录音器"""

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        """
        初始化录音器

        Args:
            sample_rate: 采样率
            channels: 声道数
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.audio_data = []
        self.stream = None
        self.recording_thread = None
        self._audio = None  # pyaudio instance

    def start_recording(self, duration: Optional[float] = None) -> bool:
        """
        开始录音

        Args:
            duration: 录制时长（秒），None 表示无限录制直到调用 stop_recording

        Returns:
            是否成功启动
        """
        try:
            import pyaudio
        except ImportError:
            logger.error("pyaudio 未安装，请安装：pip install pyaudio")
            return False

        if self.is_recording:
            logger.warning("已经在录音中")
            return False

        try:
            self._audio = pyaudio.PyAudio()
            self.is_recording = True
            self.audio_data = []

            # 配置音频流
            self.stream = self._audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024,
                stream_callback=self._audio_callback if duration is None else None
            )

            logger.info(f"开始录音 (采样率: {self.sample_rate}Hz, 声道: {self.channels})")

            if duration is not None:
                # 指定时长录音
                self.stream.start_stream()
                frames = []
                for i in range(0, int(self.sample_rate / 1024 * duration)):
                    data = self.stream.read(1024)
                    frames.append(data)

                self.audio_data = b''.join(frames)
                self.stop_recording()
            else:
                # 无限录音模式
                self.stream.start_stream()

            return True

        except Exception as e:
            logger.error(f"启动录音失败: {e}")
            self.is_recording = False
            return False

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """音频回调函数"""
        if self.is_recording:
            self.audio_data.append(in_data)
        return (in_data, pyaudio.paContinue)

    def stop_recording(self):
        """停止录音"""
        if not self.is_recording:
            return

        self.is_recording = False

        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None

            if self._audio:
                self._audio.terminate()
                self._audio = None

            # 合并音频数据
            if self.audio_data and isinstance(self.audio_data, list):
                self.audio_data = b''.join(self.audio_data)

            logger.info(f"录音已停止，总时长: {len(self.audio_data) / (self.sample_rate * 2):.2f}秒")

        except Exception as e:
            logger.error(f"停止录音失败: {e}")

    def get_audio_data(self) -> Optional[bytes]:
        """获取录制的音频数据"""
        return self.audio_data if self.audio_data else None

    def get_audio_array(self) -> Optional[np.ndarray]:
        """获取录制的音频数据（numpy数组）"""
        if not self.audio_data:
            return None

        try:
            # 将字节数据转换为 numpy 数组
            audio_array = np.frombuffer(self.audio_data, dtype=np.int16)
            # 归一化到 [-1, 1]
            audio_array = audio_array.astype(np.float32) / 32768.0
            return audio_array
        except Exception as e:
            logger.error(f"转换音频数据失败: {e}")
            return None

    def is_available(self) -> bool:
        """检查麦克风是否可用"""
        if sys.platform != 'win32':
            logger.warning(f"当前平台 {sys.platform} 不支持此录音器")
            return False

        try:
            import pyaudio
            p = pyaudio.PyAudio()
            device_count = p.get_device_count()
            p.terminate()

            if device_count == 0:
                logger.warning("未检测到音频设备")
                return False

            logger.info(f"检测到 {device_count} 个音频设备")
            return True
        except ImportError:
            logger.warning("pyaudio 未安装，请安装：pip install pyaudio")
            return False
        except Exception as e:
            logger.error(f"检查麦克风可用性失败: {e}")
            return False

    def get_audio_devices(self):
        """获取所有音频输入设备列表"""
        if sys.platform != 'win32':
            return []

        try:
            import pyaudio
            p = pyaudio.PyAudio()
            devices = []
            for i in range(p.get_device_count()):
                device_info = p.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'sample_rate': int(device_info['defaultSampleRate']),
                        'channels': device_info['maxInputChannels']
                    })
            p.terminate()
            return devices
        except Exception as e:
            logger.error(f"获取音频设备列表失败: {e}")
            return []


# 测试代码
def test_microphone():
    """测试麦克风录音"""
    recorder = MicrophoneRecorder()

    if not recorder.is_available():
        print("麦克风不可用")
        return

    print("开始录音 3 秒...")
    success = recorder.start_recording(duration=3.0)

    if success:
        time.sleep(3.1)  # 等待录音完成
        audio_data = recorder.get_audio_data()

        if audio_data:
            print(f"录音完成！数据大小: {len(audio_data)} 字节")

            # 保存到 WAV 文件（可选）
            try:
                import wave
                with wave.open("test_recording.wav", 'wb') as wf:
                    wf.setnchannels(recorder.channels)
                    wf.setsampwidth(2)  # 16-bit = 2 bytes
                    wf.setframerate(recorder.sample_rate)
                    wf.writeframes(audio_data)
                print("已保存到 test_recording.wav")
            except Exception as e:
                print(f"保存录音文件失败: {e}")
        else:
            print("录音数据为空")
    else:
        print("录音失败")


if __name__ == "__main__":
    test_microphone()
