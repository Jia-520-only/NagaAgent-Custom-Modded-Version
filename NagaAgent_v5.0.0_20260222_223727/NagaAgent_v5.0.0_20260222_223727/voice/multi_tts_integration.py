#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多引擎TTS集成模块 - 统一GPT-SoVITS、VITS和Edge-TTS
支持本地部署的多种TTS推理服务
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
from enum import Enum

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent))
from system.config import config

logger = logging.getLogger("MultiTTSEngine")

class TTSEngine(str, Enum):
    """TTS引擎类型"""
    EDGE_TTS = "edge_tts"
    GPT_SOVITS = "gpt_sovits"
    GENIE_TTS = "genie_tts"  # Genie-TTS: GPT-SoVITS ONNX 推理引擎
    VITS = "vits"
    # 可扩展其他引擎


class TTSProviderConfig:
    """TTS提供者配置"""

    # GPT-SoVITS 配置
    GPT_SOVITS_TTS_URL = "http://127.0.0.1:9880/tts"
    GPT_SOVITS_SET_REF_URL = "http://127.0.0.1:9880/set_ref_text"
    GPT_SOVITS_SET_GPT_URL = "http://127.0.0.1:9880/set_gpt_weights"

    # Genie-TTS 配置 (独立的 ONNX 推理引擎)
    GENIE_TTS_URL = "http://127.0.0.1:8000"  # Genie-TTS 默认端口 (与 GPT-SoVITS 不同)
    GENIE_TTS_TIMEOUT = 60

    # VITS 配置
    VITS_TTS_URL = "http://127.0.0.1:7860/api/tts"
    VITS_VOICE_ID = 0  # 默认说话人ID

    # 默认参数
    DEFAULT_SPEED = 1.0
    DEFAULT_TOP_K = 15
    DEFAULT_TOP_P = 1.0
    DEFAULT_TEMPERATURE = 1.0
    DEFAULT_REF_FREE = False


class MultiTTSEngine:
    """多引擎TTS集成 - 统一GPT-SoVITS、VITS和Edge-TTS"""

    def __init__(self, default_engine: TTSEngine = TTSEngine.EDGE_TTS):
        """初始化多引擎TTS系统

        Args:
            default_engine: 默认使用的TTS引擎
        """
        self.default_engine = default_engine
        self.current_engine = default_engine

        # GPT-SoVITS 参数
        self.gpt_sovits_config = {
            "speed": TTSProviderConfig.DEFAULT_SPEED,
            "top_k": TTSProviderConfig.DEFAULT_TOP_K,
            "top_p": TTSProviderConfig.DEFAULT_TOP_P,
            "temperature": TTSProviderConfig.DEFAULT_TEMPERATURE,
            "ref_free": TTSProviderConfig.DEFAULT_REF_FREE,
        }

        # Genie-TTS 参数 (与 GPT-SoVITS 保持兼容)
        self.genie_tts_config = {
            "speed": TTSProviderConfig.DEFAULT_SPEED,
            "top_k": TTSProviderConfig.DEFAULT_TOP_K,
            "top_p": TTSProviderConfig.DEFAULT_TOP_P,
            "temperature": TTSProviderConfig.DEFAULT_TEMPERATURE,
            "ref_free": TTSProviderConfig.DEFAULT_REF_FREE,
        }

        # VITS 参数
        self.vits_config = {
            "voice_id": TTSProviderConfig.VITS_VOICE_ID,
            "noise_scale": 0.667,
            "noise_scale_w": 0.8,
            "length_scale": 1.0,
        }

        # 音频播放配置
        self.min_sentence_length = 5

        # 并发控制
        self.tts_semaphore = threading.Semaphore(2)

        # 音频文件存储目录
        self.audio_temp_dir = Path("logs/audio_temp")
        self.audio_temp_dir.mkdir(parents=True, exist_ok=True)

        # 流式处理状态
        self.text_buffer = ""
        self.is_processing = False
        self.sentence_queue = Queue()
        self.audio_queue = Queue()

        # 播放状态控制
        self.is_playing = False
        self.current_playback = None

        # 音频系统状态
        self.audio_available = False
        self._pygame = None

        # 初始化音频系统
        self._init_audio_system()

        # 启动工作线程
        self.audio_thread = threading.Thread(target=self._audio_player_worker, daemon=True)
        self.audio_thread.start()

        self.processing_thread = threading.Thread(target=self._audio_processing_worker, daemon=True)
        self.processing_thread.start()

        self.cleanup_thread = threading.Thread(target=self._audio_cleanup_worker, daemon=True)
        self.cleanup_thread.start()

        logger.info(f"多引擎TTS集成模块初始化完成 (默认引擎: {default_engine})")

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

    def set_engine(self, engine: TTSEngine):
        """切换TTS引擎

        Args:
            engine: 目标引擎类型
        """
        self.current_engine = engine
        logger.info(f"TTS引擎已切换为: {engine}")

    def set_gpt_sovits_reference(self, ref_text: str, ref_audio_path: str = ""):
        """设置GPT-SoVITS参考文本和音频"""
        try:
            payload = {
                "ref_text": ref_text,
                "ref_audio_path": ref_audio_path
            }
            response = requests.post(
                TTSProviderConfig.GPT_SOVITS_SET_REF_URL,
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                logger.info("GPT-SoVITS参考文本设置成功")
                return True
            else:
                logger.error(f"GPT-SoVITS参考文本设置失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"设置GPT-SoVITS参考文本异常: {e}")
            return False

    def set_gpt_sovits_weights(self, gpt_weights_path: str):
        """设置GPT-SoVITS的GPT权重"""
        try:
            payload = {
                "gpt_weights_path": gpt_weights_path
            }
            response = requests.post(
                TTSProviderConfig.GPT_SOVITS_SET_GPT_URL,
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                logger.info("GPT-SoVITS权重设置成功")
                return True
            else:
                logger.error(f"GPT-SoVITS权重设置失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"设置GPT-SoVITS权重异常: {e}")
            return False

    def set_vits_voice(self, voice_id: int):
        """设置VITS说话人ID

        Args:
            voice_id: 说话人ID
        """
        self.vits_config["voice_id"] = voice_id
        logger.info(f"VITS说话人已设置为: {voice_id}")

    def receive_final_text(self, final_text: str):
        """接收最终完整文本 - 流式处理"""
        if not self.audio_available:
            return

        if final_text and final_text.strip():
            logger.info(f"接收最终文本: {final_text[:100]}")
            self.reset_processing_state()
            self._process_text_stream(final_text)

    def receive_text_chunk(self, text: str):
        """接收文本片段 - 流式处理"""
        if not self.audio_available:
            return

        if text and text.strip():
            logger.debug(f"接收文本片段: {text[:50]}...")
            self._process_text_stream(text.strip())

    def _process_text_stream(self, text: str):
        """处理文本流"""
        if not text:
            return

        # 将文本添加到缓冲区
        self.text_buffer += text

        # 检查是否形成完整句子
        self._check_and_queue_sentences()

    def _check_and_queue_sentences(self):
        """检查并加入句子队列"""
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
                    self.sentence_queue.put(sentence)
                    logger.info(f"加入句子队列: {sentence[:50]}...")

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

        # 重置状态
        self.text_buffer = ""
        logger.debug("语音处理状态已重置")

    def _audio_processing_worker(self):
        """音频处理工作线程 - 持续运行"""
        logger.info("音频处理工作线程启动")

        try:
            while True:
                try:
                    # 从句子队列获取句子
                    sentence = self.sentence_queue.get(timeout=10)

                    # 设置处理状态
                    self.is_processing = True

                    # 根据当前引擎生成音频
                    audio_data = self._generate_audio_sync(sentence, self.current_engine)
                    if audio_data:
                        self.audio_queue.put(audio_data)
                        logger.debug(f"音频生成完成: {sentence[:30]}...")
                    else:
                        logger.warning(f"音频生成失败: {sentence[:30]}...")

                except Empty:
                    # 队列为空，检查是否还有待处理的文本
                    if self.text_buffer.strip():
                        continue
                    else:
                        logger.debug("音频处理线程等待新的句子...")
                        self.is_processing = False
                        continue

        except Exception as e:
            logger.error(f"音频处理工作线程错误: {e}")
            self.is_processing = False
        finally:
            self.is_processing = False
            logger.info("音频处理工作线程结束")

    def _generate_audio_sync(self, text: str, engine: TTSEngine) -> Optional[bytes]:
        """同步生成音频数据 - 根据引擎类型选择生成方法"""
        # 使用信号量控制并发
        if not self.tts_semaphore.acquire(timeout=10):
            logger.warning("TTS请求超时，跳过音频生成")
            return None

        try:
            # 简单的文本清理
            text = text.strip()
            if not text:
                return None

            # 根据引擎类型调用不同的生成方法
            if engine == TTSEngine.GPT_SOVITS:
                return self._generate_gpt_sovits(text)
            elif engine == TTSEngine.GENIE_TTS:
                return self._generate_genie_tts(text)
            elif engine == TTSEngine.VITS:
                return self._generate_vits(text)
            elif engine == TTSEngine.EDGE_TTS:
                return self._generate_edge_tts(text)
            else:
                logger.error(f"不支持的TTS引擎: {engine}")
                return None

        except Exception as e:
            logger.error(f"生成音频数据异常: {e}")
            return None
        finally:
            # 释放信号量
            self.tts_semaphore.release()

    def _generate_gpt_sovits(self, text: str) -> Optional[bytes]:
        """使用GPT-SoVITS生成音频"""
        try:
            # 从配置中获取参考文本和音频路径
            ref_text = getattr(config.tts, 'gpt_sovits_ref_text', '')
            ref_audio_path = getattr(config.tts, 'gpt_sovits_ref_audio_path', '')
            ref_free = getattr(config.tts, 'gpt_sovits_ref_free', False)

            logger.info(f"使用GPT-SoVITS生成语音，参考文本: {ref_text[:30] if ref_text and not ref_free else '免参考模式'}...")

            # GPT-SoVITS v2pro API 格式（根据官方文档）
            # 注意：ref_audio_path 和 prompt_lang 是必需参数！

            # 如果启用了免参考模式但没有配置默认参考音频，无法使用
            if ref_free and not ref_audio_path:
                logger.error("免参考模式但仍需要参考音频路径！GPT-SoVITS v2pro 要求 ref_audio_path 为必需参数")
                logger.info("提示：请在 config.json 中配置有效的 gpt_sovits_ref_audio_path，或设置 gpt_sovits_ref_free 为 false")
                return None

            # 构造请求参数
            payload = {
                "text": text,
                "text_lang": "zh",
                "ref_audio_path": ref_audio_path,  # 必需参数
                "prompt_text": ref_text if ref_text else "默认文本",  # 可选
                "prompt_lang": "zh",  # 必需参数
                "top_k": self.gpt_sovits_config["top_k"],
                "top_p": self.gpt_sovits_config["top_p"],
                "temperature": self.gpt_sovits_config["temperature"],
                "speed_factor": self.gpt_sovits_config["speed"],
                "text_split_method": "cut5",
                "batch_size": 1,
                "media_type": "wav",
                "streaming_mode": False,
            }

            logger.debug(f"GPT-SoVITS请求参数: {payload}")

            # 发送请求到GPT-SoVITS服务
            gpt_sovits_url = getattr(config.tts, 'gpt_sovits_url', TTSProviderConfig.GPT_SOVITS_TTS_URL)
            response = requests.post(
                f"{gpt_sovits_url}/tts",
                json=payload,
                timeout=60
            )

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
            return None

    def _generate_genie_tts(self, text: str) -> Optional[bytes]:
        """使用Genie-TTS生成音频 (GPT-SoVITS ONNX 推理引擎)"""
        try:
            from voice.genie_tts_adapter import get_genie_tts_adapter

            # 从配置中获取参考文本和音频路径
            ref_text = getattr(config.tts, 'genie_ref_text', '')
            ref_audio_path = getattr(config.tts, 'genie_ref_audio_path', '')
            ref_free = getattr(config.tts, 'genie_ref_free', False)

            logger.info(f"使用Genie-TTS生成语音，参考文本: {ref_text[:30] if ref_text and not ref_free else '免参考模式'}...")

            # 如果启用了免参考模式但没有配置默认参考音频，无法使用
            if ref_free and not ref_audio_path:
                logger.error("免参考模式但仍需要参考音频路径！Genie-TTS 要求 ref_audio_path 为必需参数")
                logger.info("提示：请在 config.json 中配置有效的 genie_ref_audio_path，或设置 genie_ref_free 为 false")
                return None

            # 如果没有配置 ref_audio_path，尝试使用 GPT-SoVITS 的配置
            if not ref_audio_path:
                ref_audio_path = getattr(config.tts, 'gpt_sovits_ref_audio_path', '')
                logger.info(f"使用 GPT-SoVITS 的参考音频配置: {ref_audio_path}")

            if not ref_text:
                ref_text = getattr(config.tts, 'gpt_sovits_ref_text', '')
                logger.info(f"使用 GPT-SoVITS 的参考文本配置: {ref_text}")

            # 获取 Genie-TTS 适配器
            genie_tts = get_genie_tts_adapter()

            # 合成语音
            audio_data = genie_tts.synthesize(
                text=text,
                ref_audio_path=ref_audio_path,
                prompt_text=ref_text,
                text_lang="zh",
                prompt_lang="zh",
                speed=self.genie_tts_config["speed"],
                top_k=self.genie_tts_config["top_k"],
                top_p=self.genie_tts_config["top_p"],
                temperature=self.genie_tts_config["temperature"]
            )

            if audio_data:
                logger.info(f"Genie-TTS音频生成成功: {len(audio_data)} bytes")
                return audio_data
            else:
                logger.error("Genie-TTS音频生成失败")
                return None

        except ImportError:
            logger.error("Genie-TTS 适配器未找到，请检查 voice/genie_tts_adapter.py 是否存在")
            return None
        except Exception as e:
            logger.error(f"Genie-TTS生成音频失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _generate_vits(self, text: str) -> Optional[bytes]:
        """使用VITS生成音频"""
        try:
            # 构造VITS TTS请求参数
            payload = {
                "text": text,
                "voice_id": self.vits_config["voice_id"],
                "noise_scale": self.vits_config["noise_scale"],
                "noise_scale_w": self.vits_config["noise_scale_w"],
                "length_scale": self.vits_config["length_scale"]
            }

            # 发送请求到VITS服务
            response = requests.post(
                TTSProviderConfig.VITS_TTS_URL,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                audio_data = response.content
                logger.debug(f"VITS音频生成成功: {len(audio_data)} bytes")
                return audio_data
            else:
                logger.error(f"VITS API调用失败: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"VITS生成音频失败: {e}")
            return None

    def _generate_edge_tts(self, text: str) -> Optional[bytes]:
        """使用Edge-TTS生成音频（回退方案）"""
        try:
            from voice.output.tts_handler import generate_speech

            # 转换为edge_tts需要的参数
            voice = config.tts.default_voice
            response_format = config.tts.default_format
            speed = config.tts.default_speed

            # 调用edge_tts生成音频
            temp_file = generate_speech(text, voice, response_format, speed)

            if temp_file and os.path.exists(temp_file):
                # 读取音频数据
                with open(temp_file, 'rb') as f:
                    audio_data = f.read()

                # 删除临时文件（带重试机制）
                import time
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

                logger.debug(f"Edge-TTS音频生成成功: {len(audio_data)} bytes")
                return audio_data
            else:
                logger.error("Edge-TTS音频生成失败")
                return None

        except Exception as e:
            logger.error(f"Edge-TTS生成音频失败: {e}")
            return None

    def _audio_player_worker(self):
        """音频播放工作线程"""
        logger.info("音频播放工作线程启动")

        if not self.audio_available:
            logger.error("音频系统不可用，播放线程无法启动")
            return

        try:
            while True:
                try:
                    # 从队列获取音频数据
                    audio_data = self.audio_queue.get(timeout=30)

                    if audio_data:
                        self._play_audio_data_sync(audio_data)

                except Empty:
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

            # 创建临时文件用于播放
            temp_file = tempfile.mktemp(suffix=".wav")

            # 写入音频数据
            with open(temp_file, 'wb') as f:
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
                time.sleep(60)

                # 获取所有音频文件
                audio_files = list(self.audio_temp_dir.glob("*.wav"))

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

            except Exception as e:
                logger.error(f"音频文件清理异常: {e}")
                time.sleep(5)

    def finish_processing(self):
        """完成处理，清理剩余内容"""
        # 处理剩余的文本
        if self.text_buffer.strip():
            remaining_text = self.text_buffer.strip()
            if remaining_text:
                self.sentence_queue.put(remaining_text)
                logger.debug(f"处理剩余文本: {remaining_text[:50]}...")

        self.text_buffer = ""

    def get_debug_info(self) -> Dict[str, Any]:
        """获取调试信息"""
        return {
            "current_engine": self.current_engine,
            "text_buffer_length": len(self.text_buffer),
            "sentence_queue_size": self.sentence_queue.qsize(),
            "audio_queue_size": self.audio_queue.qsize(),
            "is_processing": self.is_processing,
            "is_playing": self.is_playing,
            "audio_available": self.audio_available,
            "temp_files": len(list(self.audio_temp_dir.glob("*.wav")))
        }


# 全局实例管理
_global_multi_tts_engine = None


def get_multi_tts_engine() -> MultiTTSEngine:
    """获取多引擎TTS集成实例（单例模式）"""
    global _global_multi_tts_engine
    if _global_multi_tts_engine is None:
        # 从配置读取默认引擎
        default_engine_str = getattr(config.tts, 'default_engine', 'edge_tts')
        try:
            default_engine = TTSEngine(default_engine_str)
        except ValueError:
            logger.warning(f"无效的默认引擎: {default_engine_str}，使用默认值: edge_tts")
            default_engine = TTSEngine.EDGE_TTS

        _global_multi_tts_engine = MultiTTSEngine(default_engine=default_engine)
    return _global_multi_tts_engine


def auto_initialize():
    """自动初始化多引擎TTS（用于main.py调用）"""
    try:
        engine = get_multi_tts_engine()
        logger.info(f"✅ 多引擎TTS自动初始化完成 (当前引擎: {engine.current_engine})")
        return engine
    except Exception as e:
        logger.error(f"❌ 多引擎TTS自动初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return None


# 示例用法
if __name__ == "__main__":
    # 测试集成
    engine = get_multi_tts_engine()

    # 切换到GPT-SoVITS
    engine.set_engine(TTSEngine.GPT_SOVITS)
    engine.receive_final_text("你好，这是GPT-SoVITS测试。")
    time.sleep(5)

    # 切换到VITS
    engine.set_engine(TTSEngine.VITS)
    engine.receive_final_text("你好，这是VITS测试。")
    time.sleep(5)

    # 切换到Edge-TTS
    engine.set_engine(TTSEngine.EDGE_TTS)
    engine.receive_final_text("你好，这是Edge-TTS测试。")
    time.sleep(5)

    print("测试完成")
