#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
声纹识别系统
AI只与声纹主人交互
"""
import numpy as np
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Tuple
import json

logger = logging.getLogger("VoiceprintAuth")

class VoiceprintAuthenticator:
    """声纹认证系统"""

    def __init__(self, config_dir: str = "voice/auth"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.voiceprint_db_file = self.config_dir / "voiceprint_db.json"
        self.voiceprint_db: Dict[str, np.ndarray] = {}
        self.current_speaker: Optional[str] = None
        self.is_recording = False

        # 加载已有声纹数据库
        self._load_voiceprint_db()

    def _load_voiceprint_db(self):
        """加载声纹数据库"""
        try:
            if self.voiceprint_db_file.exists():
                with open(self.voiceprint_db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 将保存的numpy数组转换回来
                    for name, features in data.items():
                        self.voiceprint_db[name] = np.array(features)
                logger.info(f"已加载 {len(self.voiceprint_db)} 个声纹模板")
        except Exception as e:
            logger.error(f"加载声纹数据库失败: {e}")

    def _save_voiceprint_db(self):
        """保存声纹数据库"""
        try:
            data = {}
            for name, features in self.voiceprint_db.items():
                # 将numpy数组转换为列表保存
                data[name] = features.tolist()

            with open(self.voiceprint_db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("声纹数据库已保存")
        except Exception as e:
            logger.error(f"保存声纹数据库失败: {e}")

    def register_voiceprint(self, name: str, audio_features: np.ndarray, duration: float = 5.0) -> bool:
        """
        注册声纹

        Args:
            name: 用户名称
            audio_features: 音频特征（MFCC或其他特征）
            duration: 录制时长（秒）

        Returns:
            是否注册成功
        """
        try:
            # 检查是否已有该用户
            if name in self.voiceprint_db:
                logger.warning(f"用户 {name} 已存在，将更新声纹")

            # 简单处理：直接保存特征（实际应用中需要更复杂的处理）
            self.voiceprint_db[name] = audio_features
            self._save_voiceprint_db()

            logger.info(f"声纹注册成功: {name}, 时长: {duration:.1f}秒")
            return True

        except Exception as e:
            logger.error(f"声纹注册失败: {e}")
            return False

    def verify_voiceprint(self, audio_features: np.ndarray, threshold: float = 0.7) -> Tuple[bool, Optional[str], float]:
        """
        验证声纹

        Args:
            audio_features: 音频特征
            threshold: 相似度阈值

        Returns:
            (是否匹配, 匹配的用户名, 相似度)
        """
        try:
            if not self.voiceprint_db:
                return False, None, 0.0

            best_match = None
            best_score = 0.0

            # 简单相似度计算（实际应用中需要更复杂的算法）
            for name, template in self.voiceprint_db.items():
                # 使用余弦相似度
                score = self._cosine_similarity(audio_features, template)
                if score > best_score:
                    best_score = score
                    best_match = name

            is_matched = best_score >= threshold
            logger.debug(f"声纹验证: 最佳匹配={best_match}, 相似度={best_score:.3f}, 阈值={threshold}")

            return is_matched, best_match, best_score

        except Exception as e:
            logger.error(f"声纹验证失败: {e}")
            return False, None, 0.0

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        try:
            # 确保向量形状一致
            min_len = min(len(vec1), len(vec2))
            vec1 = vec1[:min_len]
            vec2 = vec2[:min_len]

            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)

        except Exception:
            return 0.0

    def extract_audio_features(self, audio_data: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """
        提取音频特征（简化版MFCC）

        Args:
            audio_data: 音频数据
            sample_rate: 采样率

        Returns:
            特征向量
        """
        try:
            # 简化的特征提取：使用幅度谱
            # 实际应用中应使用librosa等专业库提取MFCC
            import scipy.signal as signal

            # 计算功率谱
            freqs, times, Sxx = signal.spectrogram(
                audio_data,
                fs=sample_rate,
                nperseg=512,
                noverlap=256
            )

            # 取平均谱作为特征
            features = np.mean(Sxx, axis=1)

            return features

        except Exception as e:
            logger.error(f"音频特征提取失败: {e}")
            return np.zeros(256)

    def delete_voiceprint(self, name: str) -> bool:
        """删除声纹"""
        try:
            if name in self.voiceprint_db:
                del self.voiceprint_db[name]
                self._save_voiceprint_db()
                logger.info(f"已删除声纹: {name}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除声纹失败: {e}")
            return False

    def list_voiceprints(self) -> list:
        """列出所有已注册的声纹"""
        return list(self.voiceprint_db.keys())

    def is_owner_registered(self) -> bool:
        """检查是否已注册主人声纹"""
        from system.config import config
        owner_name = getattr(config.system, 'voiceprint_owner_name', '')
        return owner_name in self.voiceprint_db if owner_name else False

# 全局实例
_voiceprint_auth: Optional[VoiceprintAuthenticator] = None

def get_voiceprint_auth() -> VoiceprintAuthenticator:
    """获取声纹认证实例"""
    global _voiceprint_auth
    if _voiceprint_auth is None:
        _voiceprint_auth = VoiceprintAuthenticator()
    return _voiceprint_auth
