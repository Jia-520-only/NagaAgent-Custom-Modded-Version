#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPT-SoVITS 语音合成集成模块
支持本地部署的GPT-SoVITS推理服务
"""

import asyncio
import logging
import tempfile
import os
import threading
import time
import hashlib
import re
import io
import base64
import requests
from typing import Optional, List, Dict, Any
import sys
from pathlib import Path
from queue import Queue, Empty

# --- 配置部分 ---
# 你可以在这里修改一些默认设置
GPT_SOVITS_TTS_URL = "http://127.0.0.1:9880/tts"
GPT_SOVITS_SET_REF_URL = "http://127.0.0.1:9880/set_ref_text"
GPT_SOVITS_SET_GPT_URL = "http://127.0.0.1:9880/set_gpt_weights"

# GPT-SoVITS 参数
DEFAULT_SPEED = 1.0
DEFAULT_TOP_K = 15
DEFAULT_TOP_P = 1.0
DEFAULT_TEMPERATURE = 1.0
DEFAULT_REF_FREE = False

logger = logging.getLogger("GPTSoVITSIntegration")


class GPTSoVITSIntegration:
    """GPT-SoVITS语音集成模块"""

    def __init__(self):
        self.tts_url = GPT_SOVITS_TTS_URL
        self.ref_url = GPT_SOVITS_SET_REF_URL
        self.checkpoint_url = GPT_SOVITS_SET_GPT_URL
        self.speed = DEFAULT_SPEED
        self.top_k = DEFAULT_TOP_K
        self.top_p = DEFAULT_TOP_P
        self.temperature = DEFAULT_TEMPERATURE
        self.ref_free = DEFAULT_REF_FREE

        # 音频播放配置
        self.min_sentence_length = 5

        # 并发控制
        self.tts_semaphore = threading.Semaphore(2)  # 限制TTS请求并发数

        # 音频文件存储目录
        self.audio_temp_dir = Path("logs/audio_temp")
        self.audio_temp_dir.mkdir(parents=True, exist_ok=True)

        # 流式处理状态
        self.text_buffer = ""  # 文本缓冲区
        self.is_processing = False  # 是否正在处理
        self.sentence_queue = Queue()  # 句子队列
        self.audio_queue = Queue()  # 音频队列

        # 播放状态控制
        self.is_playing = False
        self.current_playback = None  # 存储当前音频播放对象

        # 音频系统状态
        self.audio_available = False
        self._pygame = None  # pygame引用

        # 初始化音频系统
        self._init_audio_system()

        # 启动音频播放工作线程
        self.audio_thread = threading.Thread(target=self._audio_player_worker, daemon=True)
        self.audio_thread.start()

        # 启动音频处理工作线程（持续运行）
        self.processing_thread = threading.Thread(target=self._audio_processing_worker, daemon=True)
        self.processing_thread.start()

        # 启动音频文件清理线程
        self.cleanup_thread = threading.Thread(target=self._audio_cleanup_worker, daemon=True)
        self.cleanup_thread.start()

        logger.info("GPT-SoVITS语音集成模块初始化完成")

    def _init_audio_system(self):
        """初始化音频系统 - 使用pygame.mixer播放音频"""
        try:
            import pygame

            # 初始化pygame mixer
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

            self._pygame = pygame
            self.audio_available = True
            logger.info("音频系统初始化成功 (pygame.mixer)")

        except ImportError as e:
            logger.error(f"pygame未安装: {e}，请安装: pip install pygame")
            self.audio_available = False
        except Exception as e:
            logger.error(f"音频系统初始化失败: {e}")
            self.audio_available = False

    def set_reference_text(self, ref_text: str, ref_audio_path: str = ""):
        """设置参考文本和音频 (可选)"""
        try:
            payload = {"ref_text": ref_text, "ref_audio_path": ref_audio_path}
            response = requests.post(self.ref_url, json=payload, timeout=30)
            if response.status_code == 200:
                logger.info("参考文本设置成功")
                return True
            else:
                logger.error(f"参考文本设置失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"设置参考文本异常: {e}")
            return False

    def set_gpt_weights(self, gpt_weights_path: str):
        """设置GPT权重"""
        try:
            payload = {"gpt_weights_path": gpt_weights_path}
            response = requests.post(self.checkpoint_url, json=payload, timeout=30)
            if response.status_code == 200:
                logger.info("GPT权重设置成功")
                return True
            else:
                logger.error(f"GPT权重设置失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"设置GPT权重异常: {e}")
            return False

    def receive_final_text(self, final_text: str):
        """接收最终完整文本 - 流式处理"""
        if not self.audio_available:  # 简化，假设总是启用
            return

        if final_text and final_text.strip():
            logger.info(f"接收最终文本: {final_text[:100]}")
            # 重置状态，为新的对话做准备
            self.reset_processing_state()
            # 流式处理最终文本
            self._process_text_stream(final_text)

    def receive_text_chunk(self, text: str):
        """接收文本片段 - 流式处理"""
        if not self.audio_available:  # 简化，假设总是启用
            return

        if text and text.strip():
            # 流式文本直接处理，不累积
            logger.debug(f"接收文本片段: {text[:50]}...")
            self._process_text_stream(text.strip())

    def _process_text_stream(self, text: str):
        """处理文本流 - 直接接收处理好的普通文本"""
        if not text:
            return

        # 将文本添加到缓冲区
        self.text_buffer += text

        # 检查是否形成完整句子（简单的标点检测）
        self._check_and_queue_sentences()

    def _check_and_queue_sentences(self):
        """检查并加入句子队列 - 简化版本"""
        if not self.text_buffer:
            return

        # 简单的句子结束检测
        sentence_endings = [".", "。", "!", "！", "?", "？", ";", "；"]

        for ending in sentence_endings:
            if ending in self.text_buffer:
                # 找到句子结束位置
                end_pos = self.text_buffer.find(ending) + 1
                sentence = self.text_buffer[:end_pos]

                # 检查句子是否有效
                if sentence.strip():
                    # 加入句子队列
                    self.sentence_queue.put(sentence)
                    logger.info(f"加入句子队列: {sentence[:50]}...")

                    # 音频处理线程始终在运行，无需检查启动状态

                # 更新缓冲区
                self.text_buffer = self.text_buffer[end_pos:]
                break

    def reset_processing_state(self):
        """重置处理状态，为新的对话做准备"""
        # 清空队列
        while not self.sentence_queue.empty():
            try:
                self.sentence_queue.get_nowait()
            except Empty:
                break

        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except Empty:
                break

        # 重置状态（不重置is_processing，因为线程是持续运行的）
        self.text_buffer = ""

        logger.debug("语音处理状态已重置")

    def _audio_processing_worker(self):
        """音频处理工作线程 - 持续运行"""
        logger.info("音频处理工作线程启动")

        try:
            while True:
                try:
                    # 从句子队列获取句子，增加超时时间
                    sentence = self.sentence_queue.get(timeout=10)

                    # 设置处理状态
                    self.is_processing = True

                    # 生成音频
                    audio_data = self._generate_audio_sync(sentence)
                    if audio_data:
                        self.audio_queue.put(audio_data)
                        logger.debug(f"音频生成完成: {sentence[:30]}...")
                    else:
                        logger.warning(f"音频生成失败: {sentence[:30]}...")

                except Empty:
                    # 队列为空，检查是否还有待处理的文本
                    if self.text_buffer.strip():
                        # 还有未处理的文本，继续等待
                        continue
                    else:
                        # 没有更多文本，继续等待新的句子
                        logger.debug("音频处理线程等待新的句子...")
                        self.is_processing = False
                        continue

        except Exception as e:
            logger.error(f"音频处理工作线程错误: {e}")
            self.is_processing = False
        finally:
            self.is_processing = False
            logger.info("音频处理工作线程结束")

    def _generate_audio_sync(self, text: str) -> Optional[bytes]:
        """同步生成音频数据 - 使用GPT-SoVITS"""
        # 使用信号量控制并发
        if not self.tts_semaphore.acquire(timeout=10):  # 10秒超时
            logger.warning("TTS请求超时，跳过音频生成")
            return None

        try:
            # 简单的文本清理
            text = text.strip()
            if not text:
                logger.warning(f"音频生成失败：文本为空")
                return None

            logger.debug(f"开始生成GPT-SoVITS音频，文本长度: {len(text)}, 内容: {text[:50]}...")

            # 构造GPT-SoVITS TTS请求参数
            payload = {
                "text": text,
                "speed": self.speed,
                "top_k": self.top_k,
                "top_p": self.top_p,
                "temperature": self.temperature,
                "ref_free": self.ref_free,
                "streaming": False,  # 非流式输出
            }

            # 发送请求到GPT-SoVITS服务
            response = requests.post(
                self.tts_url,
                json=payload,
                timeout=60,  # GPT-SoVITS可能需要较长时间
            )

            if response.status_code == 200:
                # 返回音频数据
                audio_data = response.content
                if len(audio_data) > 0:
                    logger.info(f"音频生成成功: {len(audio_data)} bytes")
                    return audio_data
                else:
                    logger.error(f"GPT-SoVITS返回空音频数据")
                    return None
            else:
                logger.error(f"GPT-SoVITS API调用失败: {response.status_code} - {response.text[:200]}")
                return None

        except requests.Timeout:
            logger.error(f"GPT-SoVITS API请求超时（60秒），文本: {text[:50]}...")
            return None
        except Exception as e:
            logger.error(f"生成音频数据异常: {e}, 文本: {text[:50]}...", exc_info=True)
            return None
        finally:
            # 释放信号量
            self.tts_semaphore.release()

    def _audio_player_worker(self):
        """音频播放工作线程"""
        logger.info("音频播放工作线程启动")

        # 检查音频系统是否可用
        if not self.audio_available:
            logger.error("音频系统不可用，播放线程无法启动")
            return

        try:
            while True:
                try:
                    # 从队列获取音频数据，保持30秒超时
                    audio_data = self.audio_queue.get(timeout=30)

                    if audio_data:
                        # 播放音频数据
                        self._play_audio_data_sync(audio_data)

                except Empty:
                    # 队列为空，继续等待
                    logger.debug("音频队列为空，继续等待...")
                    continue
                except Exception as e:
                    logger.error(f"音频播放工作线程错误: {e}")
                    time.sleep(0.1)

        except Exception as e:
            logger.error(f"音频播放工作线程异常: {e}")
        finally:
            logger.info("音频播放工作线程结束")

    def _play_audio_data_sync(self, audio_data: bytes):
        """同步播放音频数据 - 使用pygame.mixer"""
        if not self.audio_available:
            logger.warning("音频系统不可用，无法播放音频")
            return

        try:
            # 停止当前正在播放的音频
            if self._pygame.mixer.music.get_busy():
                self._pygame.mixer.music.stop()
                time.sleep(0.1)

            # 创建临时文件用于播放（pygame.mixer需要文件路径）
            temp_file = tempfile.mktemp(suffix=".wav")

            # 写入音频数据
            with open(temp_file, "wb") as f:
                f.write(audio_data)

            # 加载并播放音频
            self._pygame.mixer.music.load(temp_file)
            self._pygame.mixer.music.play()
            self.is_playing = True

            # 等待播放完成
            start_time = time.time()
            while self._pygame.mixer.music.get_busy():
                time.sleep(0.1)

                # 防止无限等待（5分钟超时）
                if time.time() - start_time > 300:
                    logger.warning("音频播放超时，强制停止")
                    self._pygame.mixer.music.stop()
                    break

            self.is_playing = False
            logger.debug("音频播放完成")

            # 🔧 关键：先卸载音频以释放文件句柄
            try:
                self._pygame.mixer.music.unload()
                logger.debug("已卸载pygame音频")
            except Exception as e:
                logger.debug(f"卸载pygame音频失败: {e}")

            # 清理临时文件（带重试机制）
            try:
                import os
                import time

                # 等待pygame完全释放文件
                for attempt in range(20):  # 最多尝试20次（增加到20次）
                    try:
                        if os.path.exists(temp_file):
                            os.unlink(temp_file)
                            logger.debug(f"成功删除临时文件: {temp_file}")
                            break
                    except PermissionError as e:
                        if attempt < 19:
                            time.sleep(1.0)  # 等待1秒后重试（增加到1秒）
                        else:
                            logger.debug(f"清理临时文件失败: {e}")
            except Exception as e:
                logger.debug(f"清理临时文件失败: {e}")

        except Exception as e:
            logger.error(f"播放音频数据失败: {e}")
            import traceback

            traceback.print_exc()
            self.is_playing = False

    def _audio_cleanup_worker(self):
        """音频文件清理工作线程"""
        logger.info("音频文件清理工作线程启动")

        while True:
            try:
                time.sleep(60)  # 每60秒清理一次

                # 获取所有音频文件
                audio_files = list(self.audio_temp_dir.glob(f"*.wav"))

                # 清理文件
                files_to_clean = []
                for file_path in audio_files:
                    # 检查文件是否过旧（超过5分钟）
                    if time.time() - file_path.stat().st_mtime > 300:
                        files_to_clean.append(file_path)

                if files_to_clean:
                    logger.info(f"开始清理 {len(files_to_clean)} 个音频文件")
                    for file_path in files_to_clean:
                        try:
                            file_path.unlink()
                            logger.debug(f"已删除音频文件: {file_path}")
                        except Exception as e:
                            logger.warning(f"删除音频文件失败: {file_path} - {e}")

                    logger.info(f"音频文件清理完成，共清理 {len(files_to_clean)} 个文件")
                else:
                    logger.debug("本次清理检查完成，无需要清理的文件")

            except Exception as e:
                logger.error(f"音频文件清理异常: {e}")
                time.sleep(5)

    def finish_processing(self):
        """完成处理，清理剩余内容"""
        # 处理剩余的文本
        if self.text_buffer.strip():
            # 将剩余文本作为最后一个句子处理
            remaining_text = self.text_buffer.strip()
            if remaining_text:
                self.sentence_queue.put(remaining_text)
                logger.debug(f"处理剩余文本: {remaining_text[:50]}...")

        # 不再发送完成信号，因为线程是持续运行的
        # 只需要清空文本缓冲区
        self.text_buffer = ""

    def get_debug_info(self) -> Dict[str, Any]:
        """获取调试信息"""
        return {
            "text_buffer_length": len(self.text_buffer),
            "sentence_queue_size": self.sentence_queue.qsize(),
            "audio_queue_size": self.audio_queue.qsize(),
            "is_processing": self.is_processing,
            "is_playing": self.is_playing,
            "audio_available": self.audio_available,
            "temp_files": len(list(self.audio_temp_dir.glob("*.wav"))),
        }


def get_gptsovits_integration() -> GPTSoVITSIntegration:
    """获取GPT-SoVITS集成实例"""
    if not hasattr(get_gptsovits_integration, "_instance"):
        get_gptsovits_integration._instance = GPTSoVITSIntegration()
    return get_gptsovits_integration._instance


# --- 示例用法 ---
if __name__ == "__main__":
    # 测试集成
    integration = get_gptsovits_integration()
    integration.receive_final_text("你好，世界！这是一个测试。")
    # 让程序运行一会儿以便播放音频
    time.sleep(10)
    print("测试完成")
