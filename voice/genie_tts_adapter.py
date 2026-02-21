#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genie-TTS 适配器
Genie-TTS 是 GPT-SoVITS 的 ONNX 推理引擎,提供更快的推理速度和更低的资源占用
API 兼容 GPT-SoVITS,可以作为 GPT-SoVITS 的替代品使用
"""
import logging
import requests
from typing import Optional, Dict, Any
from pathlib import Path
import sys

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent))
from system.config import config

logger = logging.getLogger("GenieTTS")


class GenieTTSAdapter:
    """Genie-TTS 适配器 - 兼容 GPT-SoVITS API 格式"""

    def __init__(
        self,
        api_url: str = "http://127.0.0.1:9880",
        timeout: int = 60
    ):
        """初始化 Genie-TTS 适配器

        Args:
            api_url: Genie-TTS API 地址
            timeout: 请求超时时间(秒)
        """
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self.tts_endpoint = f"{self.api_url}/tts"

        # 默认参数 (与 GPT-SoVITS 保持兼容)
        self.default_params = {
            "text_lang": "zh",           # 文本语言: zh/en/ja/ko
            "prompt_lang": "zh",         # 提示语言: zh/en/ja/ko
            "top_k": 15,
            "top_p": 1.0,
            "temperature": 1.0,
            "speed_factor": 1.0,
            "text_split_method": "cut5",  # 文本分割方法: cut0/cut1/cut2/cut3/cut4/cut5
            "batch_size": 1,
            "media_type": "wav",
            "streaming_mode": False,
        }

        logger.info(f"Genie-TTS 适配器初始化完成 (API: {self.api_url})")

    def synthesize(
        self,
        text: str,
        ref_audio_path: str,
        prompt_text: str = "",
        text_lang: str = "zh",
        prompt_lang: str = "zh",
        speed: float = 1.0,
        top_k: int = 15,
        top_p: float = 1.0,
        temperature: float = 1.0,
        **kwargs
    ) -> Optional[bytes]:
        """合成语音

        Args:
            text: 要合成的文本
            ref_audio_path: 参考音频路径 (必需)
            prompt_text: 提示文本 (参考文本)
            text_lang: 文本语言
            prompt_lang: 提示语言
            speed: 语速因子
            top_k: top-k 采样
            top_p: top-p 采样
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            音频数据 (bytes) 或 None
        """
        try:
            if not text or not text.strip():
                logger.warning("输入文本为空")
                return None

            if not ref_audio_path:
                logger.error("参考音频路径为空 (Genie-TTS 必需)")
                return None

            # 构造请求参数 (兼容 GPT-SoVITS API 格式)
            payload = {
                "text": text.strip(),
                "text_lang": text_lang,
                "prompt_text": prompt_text if prompt_text else "默认文本",
                "prompt_lang": prompt_lang,
                "ref_audio_path": ref_audio_path,
                "top_k": top_k,
                "top_p": top_p,
                "temperature": temperature,
                "speed_factor": speed,
                "text_split_method": self.default_params["text_split_method"],
                "batch_size": self.default_params["batch_size"],
                "media_type": self.default_params["media_type"],
                "streaming_mode": self.default_params["streaming_mode"],
            }

            # 添加额外参数
            payload.update(kwargs)

            logger.info(f"Genie-TTS 请求: text={text[:50]}..., ref_audio={ref_audio_path}")

            # 发送请求
            response = requests.post(
                self.tts_endpoint,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                audio_data = response.content
                logger.info(f"Genie-TTS 合成成功: {len(audio_data)} bytes")
                return audio_data
            else:
                logger.error(f"Genie-TTS API 调用失败: {response.status_code} - {response.text}")

                # 尝试解析错误信息
                try:
                    error_json = response.json()
                    error_msg = error_json.get("message", response.text)
                    logger.error(f"错误详情: {error_msg}")
                except:
                    pass

                return None

        except requests.exceptions.Timeout:
            logger.error(f"Genie-TTS 请求超时 (>{self.timeout}s)")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Genie-TTS 连接失败: {self.api_url}")
            logger.error("请确保 Genie-TTS 服务正在运行")
            return None
        except Exception as e:
            logger.error(f"Genie-TTS 合成异常: {e}")
            import traceback
            traceback.print_exc()
            return None

    def check_service(self) -> bool:
        """检查 Genie-TTS 服务是否可用

        Returns:
            True if service is available, False otherwise
        """
        try:
            # 尝试访问健康检查端点 (如果有的话)
            health_url = f"{self.api_url}/health"
            response = requests.get(health_url, timeout=5)

            if response.status_code == 200:
                logger.info("Genie-TTS 服务健康检查通过")
                return True
        except:
            pass

        # 如果没有健康检查端点,尝试一个简单的 TTS 请求
        try:
            test_response = requests.get(self.api_url, timeout=5)
            if test_response.status_code < 500:
                logger.info("Genie-TTS 服务响应正常")
                return True
        except:
            pass

        logger.warning("Genie-TTS 服务不可用")
        return False

    def get_info(self) -> Dict[str, Any]:
        """获取 Genie-TTS 服务信息

        Returns:
            服务信息字典
        """
        try:
            info_url = f"{self.api_url}/info"
            response = requests.get(info_url, timeout=5)

            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "message": response.text}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def set_reference(
        self,
        ref_text: str,
        ref_audio_path: str
    ) -> bool:
        """设置参考文本和音频

        Args:
            ref_text: 参考文本
            ref_audio_path: 参考音频路径

        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "ref_text": ref_text,
                "ref_audio_path": ref_audio_path
            }

            response = requests.post(
                f"{self.api_url}/set_ref_text",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                logger.info("Genie-TTS 参考设置成功")
                return True
            else:
                logger.error(f"Genie-TTS 参考设置失败: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Genie-TTS 设置参考异常: {e}")
            return False

    @staticmethod
    def get_supported_languages() -> Dict[str, str]:
        """获取支持的语言列表

        Returns:
            语言代码到语言名称的映射
        """
        return {
            "zh": "中文",
            "en": "英语",
            "ja": "日语",
            "ko": "韩语"
        }

    @staticmethod
    def get_supported_text_split_methods() -> Dict[str, str]:
        """获取支持的文本分割方法

        Returns:
            方法代码到方法名称的映射
        """
        return {
            "cut0": "不切分",
            "cut1": "按标点符号切分",
            "cut2": "按句子切分",
            "cut3": "按段落切分",
            "cut4": "智能切分 (小模型)",
            "cut5": "智能切分 (大模型)"
        }


# 全局实例管理
_global_genie_tts_adapter = None


def get_genie_tts_adapter(
    api_url: str = None,
    timeout: int = None
) -> GenieTTSAdapter:
    """获取 Genie-TTS 适配器实例 (单例模式)

    Args:
        api_url: Genie-TTS API 地址 (如果为 None,从配置读取)
        timeout: 请求超时时间 (如果为 None,从配置读取)

    Returns:
        GenieTTSAdapter 实例
    """
    global _global_genie_tts_adapter

    if _global_genie_tts_adapter is None:
        # 从配置读取参数
        if api_url is None:
            api_url = getattr(config.tts, 'genie_url', 'http://127.0.0.1:9880')

        if timeout is None:
            timeout = getattr(config.tts, 'genie_timeout', 60)

        _global_genie_tts_adapter = GenieTTSAdapter(
            api_url=api_url,
            timeout=timeout
        )

    return _global_genie_tts_adapter


def initialize_genie_tts() -> bool:
    """初始化 Genie-TTS 适配器

    Returns:
        True if initialization successful, False otherwise
    """
    try:
        adapter = get_genie_tts_adapter()

        # 检查服务是否可用
        if adapter.check_service():
            logger.info("✅ Genie-TTS 初始化成功")
            return True
        else:
            logger.warning("⚠️ Genie-TTS 服务不可用,但适配器已初始化")
            return False

    except Exception as e:
        logger.error(f"❌ Genie-TTS 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# 示例用法
if __name__ == "__main__":
    # 初始化适配器
    success = initialize_genie_tts()
    print(f"Genie-TTS 初始化: {'成功' if success else '失败'}")

    if success:
        adapter = get_genie_tts_adapter()

        # 打印服务信息
        info = adapter.get_info()
        print(f"服务信息: {info}")

        # 合成示例
        audio = adapter.synthesize(
            text="你好,这是 Genie-TTS 的测试。",
            ref_audio_path="path/to/reference.wav",
            prompt_text="你好",
            text_lang="zh",
            prompt_lang="zh"
        )

        if audio:
            print(f"合成成功: {len(audio)} bytes")
        else:
            print("合成失败")
