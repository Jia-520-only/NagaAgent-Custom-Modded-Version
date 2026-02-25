#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音集成模块 - 重构版本：依赖apiserver的流式TTS实现
支持接收处理好的普通文本、并发音频合成和音频播放（使用simpleaudio替换pygame）
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
from typing import Optional, List, Dict, Any
from nagaagent_core.core import aiohttp
import sys
from pathlib import Path
from queue import Queue, Empty

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from system.config import config, AI_NAME

logger = logging.getLogger("VoiceIntegration")

# 简化的句子结束标点（依赖apiserver的预处理）
SENTENCE_ENDINGS = ["。", "！", "？", "；", ".", "!", "?", ";"]


class VoiceIntegration:
    """语音集成模块 - 重构版本：依赖apiserver的流式TTS实现"""

    def __init__(self):
        # 从配置读取默认引擎
        self.default_engine = getattr(config.tts, "default_engine", "edge_tts")
        self.provider = self.default_engine

        # 根据引擎设置URL
        if self.default_engine == "gpt_sovits":
            self.tts_url = getattr(config.tts, "gpt_sovits_url", "http://127.0.0.1:9880")
        elif self.default_engine == "genie_tts":
            self.tts_url = getattr(config.tts, "genie_tts_url", "http://127.0.0.1:8000")
        elif self.default_engine == "vits":
            self.tts_url = getattr(config.tts, "vits_url", "http://127.0.0.1:7860")
        else:  # edge_tts
            self.tts_url = f"http://127.0.0.1:{config.tts.port}/v1/audio/speech"

        # 音频播放配置
        self.min_sentence_length = 5  # 最小句子长度（硬编码默认值）
        self.max_concurrent_tasks = 3  # 最大并发任务数（硬编码默认值）

        # 并发控制
        self.tts_semaphore = threading.Semaphore(2)  # 限制TTS请求并发数为2

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
        self._sa = None  # simpleaudio引用
        self._AudioSegment = None  # pydub的AudioSegment引用

        # 🔧 首次播放优化：暂时不启用延迟
        self.first_playback = True  # 是否是第一次播放
        self.first_playback_delay_ms = 0  # 首次播放延迟（毫秒），暂时不启用
        self.enable_timing_debug = False  # 是否启用计时debug日志（默认关闭）

        # 初始化音频系统（替换pygame）
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

        # 记录当前使用的引擎
        engine_name = {"edge_tts": "Edge-TTS", "gpt_sovits": "GPT-SoVITS", "genie_tts": "Genie-TTS", "vits": "VITS"}.get(
            self.default_engine, self.default_engine
        )
        logger.info(f"语音集成模块初始化完成 - 当前引擎: {engine_name}")

    def _init_audio_system(self):
        """初始化音频系统 - 使用pygame.mixer播放MP3（无需ffmpeg）"""
        try:
            import pygame

            # 检查是否已经初始化
            if hasattr(self, '_pygame') and self._pygame:
                # 已经初始化过，避免重复初始化
                logger.debug("音频系统已初始化，跳过重复初始化")
                return

            # 初始化pygame mixer（可以直接播放MP3，无需ffmpeg）
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

            self._pygame = pygame
            self.audio_available = True
            logger.info("音频系统初始化成功 (pygame.mixer - 可直接播放MP3)")

        except ImportError as e:
            logger.error(f"pygame未安装: {e}，请安装: pip install pygame")
            self.audio_available = False
        except Exception as e:
            logger.error(f"音频系统初始化失败: {e}")
            self.audio_available = False

    def receive_final_text(self, final_text: str):
        """接收最终完整文本 - 流式处理（保持原始逻辑）"""
        if not config.system.voice_enabled:
            return

        if final_text and final_text.strip():
            logger.info(f"接收最终文本: {final_text[:100]}")
            # 重置状态，为新的对话做准备
            self.reset_processing_state()

            # 非流式模式：直接将完整文本加入队列，不依赖标点符号分割
            if not config.system.stream_mode:
                # 将完整文本作为一个整体加入队列
                self.sentence_queue.put(final_text)
                logger.info(f"非流式模式：完整文本已加入队列")
            else:
                # 流式模式：按句子分割处理
                self._process_text_stream(final_text)

    def receive_text_chunk(self, text: str):
        """接收文本片段 - 流式处理（保持原始逻辑）"""
        if not config.system.voice_enabled:
            return

        if text and text.strip():
            # 流式文本直接处理，不累积
            logger.debug(f"接收文本片段: {text[:50]}...")
            self._process_text_stream(text.strip())

    def receive_audio_url(self, audio_url: str):
        """接收音频URL - 直接播放apiserver生成的音频（保持原始逻辑）"""
        if not config.system.voice_enabled:
            return

        if audio_url and audio_url.strip():
            logger.info(f"接收音频URL: {audio_url}")
            # 直接播放音频
            self._play_audio_from_url(audio_url)

    def _process_text_stream(self, text: str):
        """处理文本流 - 直接接收apiserver处理好的普通文本（保持原始逻辑）"""
        if not text:
            return

        # 将文本添加到缓冲区
        self.text_buffer += text

        # 检查是否形成完整句子（简单的标点检测）
        self._check_and_queue_sentences()

    def _check_and_queue_sentences(self):
        """检查并加入句子队列 - 简化版本，依赖apiserver的预处理（保持原始逻辑）"""
        if not self.text_buffer:
            return

        # 简单的句子结束检测（apiserver已经处理过复杂的标点分割）
        sentence_endings = SENTENCE_ENDINGS

        for ending in sentence_endings:
            if ending in self.text_buffer:
                # 找到句子结束位置
                end_pos = self.text_buffer.find(ending) + 1
                sentence = self.text_buffer[:end_pos]

                # 检查句子是否有效 - 排除纯标点和空白
                sentence_stripped = sentence.strip()
                if sentence_stripped:
                    # 跳过仅由标点符号组成的句子（包括语气停顿符号）
                    # 使用原始字符串避免转义警告
                    if re.match(r'^[~…….,;:!?，。！？、；：""''"（）【】《】\\s]+$', sentence_stripped):
                        logger.debug(f"跳过纯标点句子: {sentence_stripped}")
                    else:
                        # 加入句子队列
                        self.sentence_queue.put(sentence)
                        logger.info(f"加入句子队列: {sentence[:50]}...")

                # 更新缓冲区
                self.text_buffer = self.text_buffer[end_pos:]
                break

    def _start_audio_processing(self):
        """启动音频处理线程（保持原始逻辑）"""
        # 线程已经在初始化时启动，这里只需要设置状态
        if not self.is_processing:
            logger.debug("音频处理线程已启动，准备处理新的句子...")
        # 线程会自动从队列中获取句子进行处理

    def reset_processing_state(self):
        """重置处理状态，为新的对话做准备（保持原始逻辑）"""
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
        """音频处理工作线程 - 持续运行（保持原始逻辑）"""
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
        """同步生成音频数据 - 支持多引擎TTS"""
        # 使用信号量控制并发
        if not self.tts_semaphore.acquire(timeout=10):  # 10秒超时
            logger.warning("TTS请求超时，跳过音频生成")
            return None

        try:
            # 文本预处理
            if not getattr(config.tts, "remove_filter", False):
                from voice.output.handle_text import prepare_tts_input_with_context

                text = prepare_tts_input_with_context(text)

            if not text.strip():
                return None

            # 根据配置选择TTS引擎
            engine = getattr(config.tts, "default_engine", "edge_tts")

            if engine == "gpt_sovits":
                return self._generate_gpt_sovits(text)
            elif engine == "genie_tts":
                return self._generate_genie_tts(text)
            elif engine == "vits":
                return self._generate_vits(text)
            else:  # edge_tts 或其他默认
                return self._generate_edge_tts(text)

        except Exception as e:
            logger.error(f"生成音频数据异常: {e}")
            import traceback

            traceback.print_exc()
            return None
        finally:
            # 释放信号量
            self.tts_semaphore.release()

    def _convert_time_to_chinese(self, text: str) -> str:
        """将时间格式转换为中文语音格式

        例如：
        - "02:51:46" -> "两点五十一分四十六秒"
        - "14:30" -> "十四点三十分"

        Args:
            text: 原始文本

        Returns:
            转换后的文本
        """
        # 匹配时间格式 HH:MM:SS 或 HH:MM
        time_pattern = r'\b(\d{1,2}):(\d{2})(?::(\d{2}))?\b'

        def convert_match(match):
            hour = int(match.group(1))
            minute = int(match.group(2))
            second = int(match.group(3)) if match.group(3) else None

            # 转换小时
            hour_str = f"{hour}点" if hour >= 10 else f"{hour}点"

            # 转换分钟
            minute_str = f"{minute}分" if minute >= 10 else f"{minute}分"

            # 转换秒（如果有）
            if second is not None:
                second_str = f"{second}秒" if second >= 10 else f"{second}秒"
                return f"{hour_str}{minute_str}{second_str}"
            else:
                return f"{hour_str}{minute_str}"

        # 替换所有时间格式
        text = re.sub(time_pattern, convert_match, text)

        return text

    def _filter_text_for_gpt_sovits(self, text: str) -> str:
        """为GPT-SoVITS过滤文本内容

        注意：保留 ~、……、... 作为语气停顿符号，这些不会影响语音朗读
        移除 *内容* 和 （内容） 形式的动作描写，只保留语言文本

        Args:
            text: 原始文本

        Returns:
            过滤后的文本，如果文本无效则返回None
        """
        # 0. 先转换时间格式为中文语音格式
        text = self._convert_time_to_chinese(text)

        # 1. 移除描述性句子（如"数据流泛起..."、"光晕浮现"等）
        # 匹配包含"数据流"、"光晕"、"涟漪"、"波动"等描述性词汇的句子
        descriptive_patterns = [
            r'(?:^|[。！？\n])数据流[^。！？\n]*[。！？]?',  # "数据流..."句子
            r'(?:^|[。！？\n])光晕[^。！？\n]*[。！？]?',  # "光晕..."句子
            r'(?:^|[。！？\n])涟漪[^。！？\n]*[。！？]?',  # "涟漪..."句子
            r'(?:^|[。！？\n])波动[^。！？\n]*[。！？]?',  # "波动..."句子
            r'(?:^|[。！？\n])扫描到[^。！？\n]*[。！？]?',  # "扫描到..."句子
            r'(?:^|[。！？\n])渲染[^。！？\n]*[。！？]?',  # "渲染..."句子
        ]
        for pattern in descriptive_patterns:
            text = re.sub(pattern, '', text)
            # 清理可能残留的空白
            text = re.sub(r'\s+', ' ', text)

        # 2. 移除 *内容* 格式的动作描写（斜体动作）
        text = re.sub(r"\*[^*]+\*", "", text)

        # 3. 移除 （内容）格式（中文括号）的动作描写
        text = re.sub(r"[（\(][^）\)]*[）\)]", "", text)

        # 4. 移除 【内容】格式的动作描写（注意：保留《书名号》）
        text = re.sub(r"[【\[].*?[】\]]", "", text)

        # 5. 移除其他括号类型的动作描写（注意：保留《书名号》的内容）
        # 只移除【】、【】等，保留《》（书名号）
        text = re.sub(r"[「『].*?[」』]", "", text)

        # 6. 清理多余空白
        text = re.sub(r"\s+", " ", text).strip()

        # 7. 清理无效字符，只保留：中文、英文、数字、基本标点、空格、以及语气停顿符号 ~……...
        text = re.sub(
            r'[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffefa-zA-Z0-9\s，。！？、；：""''"（）【】《》~……...]', "", text
        )
        text = text.strip()

        # 8. 如果清理后文本为空或太短（少于2个字符），返回None
        # 注意：只由 ~、……、... 组成的文本也应该被跳过
        if len(text) < 2 or re.match(r"^[~…….]+$", text):
            logger.debug(f"文本过滤后为空或太短（{len(text)}字符），跳过语音生成")
            return None

        # 9. 限制文本长度（避免过长）
        if len(text) > 200:
            text = text[:200]
            logger.debug(f"文本过长，截断至200字符")

        return text

    def _generate_gpt_sovits(self, text: str) -> Optional[bytes]:
        """使用GPT-SoVITS生成音频"""
        try:
            import requests

            # 应用文本过滤
            text = self._filter_text_for_gpt_sovits(text)
            if text is None:
                logger.debug("文本过滤后返回None，跳过语音生成")
                return None

            # 从配置中获取参考文本和音频路径
            ref_text = getattr(config.tts, "gpt_sovits_ref_text", "")
            ref_audio_path = getattr(config.tts, "gpt_sovits_ref_audio_path", "")
            ref_free = getattr(config.tts, "gpt_sovits_ref_free", False)

            logger.info(
                f"使用GPT-SoVITS生成语音，参考文本: {ref_text[:30] if ref_text and not ref_free else '免参考模式'}..."
            )

            # GPT-SoVITS v2pro API 格式（根据官方文档）
            # 注意：ref_audio_path 和 prompt_lang 是必需参数！

            # 如果启用了免参考模式但没有配置默认参考音频，无法使用
            if ref_free and not ref_audio_path:
                logger.error("免参考模式但仍需要参考音频路径！GPT-SoVITS v2pro 要求 ref_audio_path 为必需参数")
                logger.info(
                    "提示：请在 config.json 中配置有效的 gpt_sovits_ref_audio_path，或设置 gpt_sovits_ref_free 为 false"
                )
                return None

            # 构造请求参数
            payload = {
                "text": text,
                "text_lang": "zh",
                "ref_audio_path": ref_audio_path,  # 必需参数
                "prompt_text": ref_text if ref_text else "默认文本",  # 可选
                "prompt_lang": "zh",  # 必需参数
                "top_k": getattr(config.tts, "gpt_sovits_top_k", 5),
                "top_p": getattr(config.tts, "gpt_sovits_top_p", 1.0),
                "temperature": getattr(config.tts, "gpt_sovits_temperature", 1.0),
                "speed_factor": getattr(config.tts, "gpt_sovits_speed", 1.0),
                "text_split_method": "cut5",
                "batch_size": 1,
                "media_type": "wav",
                "streaming_mode": False,
            }

            logger.debug(f"GPT-SoVITS请求参数: {payload}")

            # 发送请求到GPT-SoVITS服务
            gpt_sovits_url = getattr(config.tts, "gpt_sovits_url", "http://127.0.0.1:9880")
            response = requests.post(f"{gpt_sovits_url}/tts", json=payload, timeout=60)

            if response.status_code == 200:
                audio_data = response.content
                logger.info(f"GPT-SoVITS音频生成成功: {len(audio_data)} bytes")
                return audio_data
            else:
                logger.error(f"GPT-SoVITS API调用失败: {response.status_code} - {response.text}")

                # 分析错误原因
                try:
                    error_json = response.json()
                    error_msg = error_json.get("message", response.text)
                    logger.error(f"错误详情: {error_msg}")

                    if "ref_audio_path is required" in error_msg:
                        logger.error("参考音频路径缺失或无效！")
                        logger.error(f"当前配置的路径: {ref_audio_path}")
                    elif "text_lang is not supported" in error_msg:
                        logger.error("不支持的语言代码")
                    elif "prompt_lang is required" in error_msg:
                        logger.error("提示语言缺失")
                except:
                    pass

                return None

        except Exception as e:
            logger.error(f"GPT-SoVITS生成音频失败: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _generate_genie_tts(self, text: str) -> Optional[bytes]:
        """使用Genie-TTS生成音频 - 已禁用"""
        try:
            logger.warning("Genie-TTS has been disabled. Falling back to Edge-TTS.")
            return None
        except Exception as e:
            logger.error(f"Genie-TTS生成音频失败: {e}")
            return None

            # 从配置中获取参数
            ref_text = getattr(config.tts, "genie_tts_ref_text", "")
            ref_audio_path = getattr(config.tts, "genie_tts_ref_audio_path", "")
            ref_free = getattr(config.tts, "genie_tts_ref_free", False)

            logger.info(
                f"使用Genie-TTS API生成语音，参考文本: {ref_text[:30] if ref_text and not ref_free else '免参考模式'}..."
            )

            # Genie-TTS API 格式 (兼容 GPT-SoVITS v2pro)
            payload = {
                "text": text,
                "text_lang": "zh",
                "ref_audio_path": ref_audio_path if ref_audio_path else "",
                "prompt_text": ref_text if ref_text else "默认文本",
                "prompt_lang": "zh",
                "top_k": getattr(config.tts, "genie_tts_top_k", 15),
                "top_p": getattr(config.tts, "genie_tts_top_p", 1.0),
                "temperature": getattr(config.tts, "genie_tts_temperature", 1.0),
                "speed_factor": getattr(config.tts, "genie_tts_speed", 1.0),
                "text_split_method": "cut5",
                "batch_size": 1,
                "media_type": "wav",
                "streaming_mode": False,
            }

            logger.debug(f"Genie-TTS请求参数: {payload}")

            # 发送请求到Genie-TTS服务
            genie_tts_url = getattr(config.tts, "genie_tts_url", "http://127.0.0.1:8000")
            response = requests.post(f"{genie_tts_url}/tts", json=payload, timeout=getattr(config.tts, "genie_tts_timeout", 60))

            if response.status_code == 200:
                audio_data = response.content
                logger.info(f"Genie-TTS音频生成成功: {len(audio_data)} bytes")
                return audio_data
            else:
                logger.error(f"Genie-TTS API调用失败: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Genie-TTS生成音频失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _generate_vits(self, text: str) -> Optional[bytes]:
        """使用VITS生成音频"""
        try:
            import requests

            # 构造VITS TTS请求参数
            payload = {
                "text": text,
                "voice_id": getattr(config.tts, "vits_voice_id", 0),
                "noise_scale": getattr(config.tts, "vits_noise_scale", 0.667),
                "noise_scale_w": getattr(config.tts, "vits_noise_scale_w", 0.8),
                "length_scale": getattr(config.tts, "vits_length_scale", 1.0),
            }

            # 发送请求到VITS服务
            vits_url = getattr(config.tts, "vits_url", "http://127.0.0.1:7860")
            response = requests.post(f"{vits_url}/api/tts", json=payload, timeout=60)

            if response.status_code == 200:
                audio_data = response.content
                logger.info(f"VITS音频生成成功: {len(audio_data)} bytes")
                return audio_data
            else:
                logger.error(f"VITS API调用失败: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"VITS生成音频失败: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _generate_edge_tts(self, text: str) -> Optional[bytes]:
        """使用Edge-TTS生成音频"""
        try:
            import requests

            headers = {}
            if config.tts.require_api_key:
                headers["Authorization"] = f"Bearer {config.tts.api_key}"

            payload = {
                "input": text,
                "voice": config.tts.default_voice,
                "response_format": config.tts.default_format,
                "speed": config.tts.default_speed,
            }

            # 使用requests进行同步调用
            response = requests.post(self.tts_url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                audio_data = response.content
                logger.debug(f"Edge-TTS音频生成成功: {len(audio_data)} bytes")
                return audio_data
            else:
                logger.error(f"Edge-TTS API调用失败: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Edge-TTS生成音频失败: {e}")
            return None

    def _audio_player_worker(self):
        """音频播放工作线程（保持原始线程逻辑，仅替换播放实现）"""
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
        """同步播放音频数据 - 使用pygame.mixer（无需ffmpeg）"""
        if not self.audio_available:
            logger.warning("音频系统不可用，无法播放音频")
            return

        try:
            # 🔧 首次播放计时开始
            playback_start_time = time.time()
            is_first_play = self.first_playback

            # 停止当前正在播放的音频
            if self._pygame.mixer.music.get_busy():
                self._pygame.mixer.music.stop()
                time.sleep(0.1)

            # 创建临时文件用于播放（pygame.mixer需要文件路径）
            import tempfile

            # 根据当前TTS引擎确定音频格式
            engine = getattr(config.tts, "default_engine", "edge_tts")
            if engine == "gpt_sovits":
                audio_format = "wav"  # GPT-SoVITS返回WAV格式
            elif engine == "vits":
                audio_format = "wav"  # VITS通常返回WAV格式
            else:
                audio_format = config.tts.default_format or "mp3"  # Edge-TTS使用配置的格式
            temp_file = tempfile.mktemp(suffix=f".{audio_format}")

            # 写入音频数据
            with open(temp_file, "wb") as f:
                f.write(audio_data)

            # ====== 商业级Live2D口型同步引擎 V2.0 ======
            # 🔧 关键修改：先启动口型同步，让引擎立即开始初始化
            self._start_live2d_lip_sync()

            # 如果需要口型同步，先加载音频数据进行分析（让引擎准备就绪）
            audio_array = None
            sample_rate = 44100

            # 尝试加载音频用于口型同步（可选功能）
            if hasattr(self, "_advanced_lip_sync_v2") or True:  # 尝试初始化
                try:
                    # 使用soundfile或wave读取音频数据用于分析
                    try:
                        import soundfile as sf

                        audio_array, sample_rate = sf.read(temp_file)
                        # 转换为单声道
                        if len(audio_array.shape) > 1:
                            audio_array = audio_array.mean(axis=1)
                        # 转换为int16格式
                        import numpy as np

                        audio_array = (audio_array * 32767).astype(np.int16)
                        logger.debug(f"使用soundfile加载音频: {len(audio_array)} 样本, {sample_rate}Hz")
                    except ImportError:
                        # soundfile不可用，尝试使用wave（仅支持WAV格式）
                        if audio_format == "wav":
                            import wave
                            import numpy as np

                            with wave.open(temp_file, "rb") as wf:
                                sample_rate = wf.getframerate()
                                frames = wf.readframes(wf.getnframes())
                                audio_array = np.frombuffer(frames, dtype=np.int16)
                            logger.debug(f"使用wave加载音频: {len(audio_array)} 样本, {sample_rate}Hz")

                    # 初始化口型同步引擎
                    if not hasattr(self, "_advanced_lip_sync_v2") and audio_array is not None:
                        try:
                            from voice.input.voice_realtime.core.advanced_lip_sync_v2 import AdvancedLipSyncEngineV2

                            self._advanced_lip_sync_v2 = AdvancedLipSyncEngineV2(sample_rate=sample_rate, target_fps=60)
                            logger.info("✅ TTS播放已启用商业级口型同步引擎V2.0")
                        except ImportError as e:
                            logger.error(f"商业级引擎导入失败: {e} - 口型同步功能将不可用")
                            self._advanced_lip_sync_v2 = None
                        except Exception as e:
                            logger.error(f"商业级引擎初始化失败: {e}")
                            self._advanced_lip_sync_v2 = None

                except Exception as e:
                    logger.debug(f"加载音频数据用于口型同步失败: {e}")
                    audio_array = None

            # 🔧 首次播放延迟：在口型引擎准备好后，延迟音频播放
            if self.first_playback and self.first_playback_delay_ms > 0:
                delay_seconds = self.first_playback_delay_ms / 1000.0
                if self.enable_timing_debug:
                    logger.info(
                        f"🎯 [EdgeTTS首次播放] 口型引擎已准备，延迟 {self.first_playback_delay_ms}ms 后再播放音频"
                    )
                time.sleep(delay_seconds)
                if self.enable_timing_debug:
                    logger.info(f"🎯 [EdgeTTS首次播放] 延迟结束，开始播放音频")
                self.first_playback = False

            # 加载并播放音频
            load_start_time = time.time()

            # 尝试使用pygame的sound.music.load()加载MP3
            try:
                self._pygame.mixer.music.load(temp_file)
                self._pygame.mixer.music.play()
            except Exception as load_error:
                logger.error(f"pygame.mixer.music.load()失败: {load_error}")
                logger.info("尝试使用pygame.mixer.Sound()替代...")
                try:
                    sound = self._pygame.mixer.Sound(temp_file)
                    sound.play()
                except Exception as sound_error:
                    logger.error(f"pygame.mixer.Sound()也失败: {sound_error}")
                    raise

            self.is_playing = True

            # 🔧 计时debug：记录加载和播放启动时间
            if is_first_play and self.enable_timing_debug:
                load_duration = (time.time() - load_start_time) * 1000
                total_startup = (time.time() - playback_start_time) * 1000
                logger.info(f"⏱️ [EdgeTTS播放计时] 音频加载耗时={load_duration:.2f}ms, 总启动时间={total_startup:.2f}ms")

            # 等待播放完成，同时更新口型
            start_time = time.time()
            lip_sync_count = 0  # 口型同步更新次数

            if audio_array is not None and self._advanced_lip_sync_v2:
                # 有音频数据，执行口型同步
                chunk_size = int(sample_rate / 60)  # 60FPS
                audio_pos = 0

                while self._pygame.mixer.music.get_busy():
                    current_time = time.time()
                    elapsed_time = current_time - start_time

                    # 根据播放时间计算当前音频位置
                    target_pos = int(elapsed_time * sample_rate)

                    # 获取当前音频块
                    if target_pos < len(audio_array):
                        chunk_start = max(0, target_pos - chunk_size // 2)
                        chunk_end = min(len(audio_array), target_pos + chunk_size // 2)
                        audio_chunk = audio_array[chunk_start:chunk_end].tobytes()

                        # 使用商业级引擎处理音频
                        if audio_chunk:
                            try:
                                # 🔧 首次播放计时：记录前5次口型同步耗时
                                if is_first_play and self.enable_timing_debug and lip_sync_count < 5:
                                    lip_sync_start = time.time()

                                self._update_live2d_with_advanced_engine(audio_chunk)

                                if is_first_play and self.enable_timing_debug and lip_sync_count < 5:
                                    lip_sync_duration = (time.time() - lip_sync_start) * 1000
                                    logger.info(
                                        f"⏱️ [EdgeTTS口型同步计时] 第{lip_sync_count + 1}次更新: 耗时={lip_sync_duration:.2f}ms"
                                    )
                                    lip_sync_count += 1
                            except Exception as e:
                                logger.debug(f"商业级引擎处理错误: {e}")

                    # 60FPS更新频率
                    time.sleep(1.0 / 60)

                    # 防止无限等待（5分钟超时）
                    if current_time - start_time > 300:
                        logger.warning("音频播放超时，强制停止")
                        self._pygame.mixer.music.stop()
                        break
            else:
                # 没有音频数据，仅等待播放完成
                while self._pygame.mixer.music.get_busy():
                    time.sleep(0.1)

                    # 防止无限等待
                    if time.time() - start_time > 300:
                        logger.warning("音频播放超时，强制停止")
                        self._pygame.mixer.music.stop()
                        break

            self.is_playing = False
            self._stop_live2d_lip_sync()
            logger.debug("音频播放完成")

            # 🔧 关键：先卸载音频以释放文件句柄
            try:
                self._pygame.mixer.music.unload()
                logger.debug("已卸载pygame音频")
            except Exception as e:
                logger.debug(f"卸载pygame音频失败: {e}")

            # 清理临时文件（带重试机制）
            try:
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
            self._stop_live2d_lip_sync()

            # 🔧 即使出错也标记已尝试首次播放
            if self.first_playback:
                self.first_playback = False

    def _audio_cleanup_worker(self):
        """音频文件清理工作线程（保持原始逻辑）"""
        logger.info("音频文件清理工作线程启动")

        while True:
            try:
                time.sleep(60)  # 每60秒清理一次（硬编码清理间隔）

                # 获取所有音频文件
                audio_files = list(self.audio_temp_dir.glob(f"*.{config.tts.default_format}"))

                # 清理文件
                files_to_clean = []
                for file_path in audio_files:
                    # 检查文件是否过旧（超过5分钟，硬编码超时时间）
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
        """完成处理，清理剩余内容（保持原始逻辑）"""
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
        """获取调试信息（保持原始逻辑，更新音频状态标识）"""
        return {
            "text_buffer_length": len(self.text_buffer),
            "sentence_queue_size": self.sentence_queue.qsize(),
            "audio_queue_size": self.audio_queue.qsize(),
            "is_processing": self.is_processing,
            "is_playing": self.is_playing,
            "audio_available": self.audio_available,  # 替换原pygame_available
            "temp_files": len(list(self.audio_temp_dir.glob(f"*.{config.tts.default_format}"))),
        }

    def _play_audio_from_url(self, audio_url: str):
        """从URL播放音频 - 使用pygame.mixer（异步执行，不阻塞）"""
        if not self.audio_available:
            logger.warning("音频系统不可用，无法播放音频URL")
            return

        # 异步执行音频播放，不阻塞调用线程
        logger.info(f"音频播放已加入后台队列: {audio_url}")
        threading.Thread(target=self._play_audio_from_url_async, args=(audio_url,), daemon=True).start()

    def _play_audio_from_url_async(self, audio_url: str):
        """异步执行音频播放逻辑"""
        try:
            import requests
            import tempfile
            import os

            # 判断是URL还是本地文件
            if audio_url.startswith("http://") or audio_url.startswith("https://"):
                # 下载音频文件
                logger.info(f"下载音频文件: {audio_url}")
                resp = requests.get(audio_url)
                temp_file = tempfile.mktemp(suffix=f".{config.tts.default_format or 'mp3'}")
                with open(temp_file, "wb") as f:
                    f.write(resp.content)
                audio_file = temp_file
            else:
                # 本地文件路径
                audio_file = audio_url

            # 检查文件是否存在
            if not os.path.exists(audio_file):
                logger.error(f"音频文件不存在: {audio_file}")
                return

            # 读取音频文件并播放
            with open(audio_file, "rb") as f:
                audio_data = f.read()
            self._play_audio_data_sync(audio_data)

            # 清理临时文件（带重试机制）
            if audio_file != audio_url:
                try:
                    for attempt in range(20):  # 最多尝试20次（增加到20次）
                        try:
                            if os.path.exists(audio_file):
                                os.unlink(audio_file)
                                logger.debug(f"成功删除临时文件: {audio_file}")
                                break
                        except PermissionError as e:
                            if attempt < 19:
                                time.sleep(1.0)  # 等待1秒后重试（增加到1秒）
                            else:
                                logger.debug(f"清理临时文件失败: {e}")
                except Exception as e:
                    logger.debug(f"清理临时文件失败: {e}")

        except Exception as e:
            logger.error(f"播放音频URL失败: {e}")

    # ====== Live2D嘴部同步辅助方法 ======
    def _get_live2d_widget(self):
        """获取Live2D widget引用"""
        try:
            # 通过config获取window，然后获取side widget和live2d_widget
            if hasattr(config, "window") and config.window:
                window = config.window
                if hasattr(window, "side") and hasattr(window.side, "live2d_widget"):
                    live2d_widget = window.side.live2d_widget
                    # 检查是否在Live2D模式且模型已加载
                    if (
                        hasattr(window.side, "display_mode")
                        and window.side.display_mode == "live2d"
                        and live2d_widget
                        and hasattr(live2d_widget, "is_model_loaded")
                        and live2d_widget.is_model_loaded()
                    ):
                        return live2d_widget
        except Exception as e:
            logger.debug(f"获取Live2D widget失败: {e}")
        return None

    def _start_live2d_lip_sync(self):
        """启动Live2D嘴部同步"""
        try:
            live2d_widget = self._get_live2d_widget()
            if live2d_widget:
                live2d_widget.start_speaking()
                logger.debug("Live2D嘴部同步已启动（音频播放）")
        except Exception as e:
            logger.debug(f"启动Live2D嘴部同步失败: {e}")

    def _update_live2d_with_advanced_engine(self, audio_chunk: bytes):
        """使用商业级引擎更新Live2D（完整5参数控制）"""
        try:
            live2d_widget = self._get_live2d_widget()
            if not live2d_widget:
                return

            # 使用商业级引擎处理音频
            lip_sync_params = self._advanced_lip_sync_v2.process_audio_chunk(audio_chunk)

            # 应用全部5个参数
            if "mouth_open" in lip_sync_params:
                live2d_widget.set_audio_volume(lip_sync_params["mouth_open"])

            if "mouth_form" in lip_sync_params:
                live2d_widget.set_mouth_form(lip_sync_params["mouth_form"])

            if hasattr(live2d_widget, "set_mouth_smile") and "mouth_smile" in lip_sync_params:
                live2d_widget.set_mouth_smile(lip_sync_params["mouth_smile"])

            if hasattr(live2d_widget, "set_eye_brow") and "eye_brow_up" in lip_sync_params:
                live2d_widget.set_eye_brow(lip_sync_params["eye_brow_up"])

            if hasattr(live2d_widget, "set_eye_wide") and "eye_wide" in lip_sync_params:
                live2d_widget.set_eye_wide(lip_sync_params["eye_wide"])

        except Exception as e:
            logger.debug(f"商业级引擎更新Live2D失败: {e}")

    def _stop_live2d_lip_sync(self):
        """停止Live2D嘴部同步"""
        try:
            live2d_widget = self._get_live2d_widget()
            if live2d_widget:
                live2d_widget.stop_speaking()
                logger.debug("Live2D嘴部同步已停止（音频播放完成）")
        except Exception as e:
            logger.debug(f"停止Live2D嘴部同步失败: {e}")


def get_voice_integration() -> VoiceIntegration:
    """获取语音集成实例（保持原始逻辑）"""
    if not hasattr(get_voice_integration, "_instance"):
        get_voice_integration._instance = VoiceIntegration()
    return get_voice_integration._instance
