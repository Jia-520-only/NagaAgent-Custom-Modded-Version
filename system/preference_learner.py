#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户反馈学习系统
根据用户反馈动态调整自主性引擎的决策策略
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """反馈类型"""
    POSITIVE = "positive"    # 正面反馈（感谢、称赞、采纳建议）
    NEGATIVE = "negative"    # 负面反馈（拒绝、批评、打扰）
    NEUTRAL = "neutral"      # 中性反馈（忽略、无反应）
    IGNORED = "ignored"      # 被忽略（用户无回应）


class FeedbackAnalyzer:
    """反馈分析器 - 分析用户对主动行为的反馈"""

    # 正面反馈关键词
    POSITIVE_KEYWORDS = [
        "谢谢", "感谢", "好的", "不错", "很好", "棒", "太好了",
        "有帮助", "有用", "确实", "你说得对", "采纳", "接受",
        "😊", "👍", "❤️", "👏"
    ]

    # 负面反馈关键词
    NEGATIVE_KEYWORDS = [
        "不要", "不需要", "不用", "别", "闭嘴", "安静",
        "打扰", "烦", "吵", "讨厌", "滚", "走开",
        "🙄", "😒", "😤", "🙅", "🚫"
    ]

    # 忽略关键词（表示对建议无兴趣）
    IGNORE_KEYWORDS = [
        "嗯", "哦", "啊", "好吧", "随便", "不管",
        "...", "...", "没兴趣"
    ]

    def __init__(self):
        self.feedback_history: List[Dict[str, Any]] = []
        self.max_history = 200

    def analyze_user_message(self, message: str, context: Optional[Dict] = None) -> FeedbackType:
        """
        分析用户消息，判断反馈类型

        Args:
            message: 用户消息
            context: 上下文信息（包含最近的主动行为等）

        Returns:
            反馈类型
        """
        message_lower = message.lower()

        # 检查正面反馈
        for keyword in self.POSITIVE_KEYWORDS:
            if keyword in message:
                return FeedbackType.POSITIVE

        # 检查负面反馈
        for keyword in self.NEGATIVE_KEYWORDS:
            if keyword in message:
                return FeedbackType.NEGATIVE

        # 检查忽略
        for keyword in self.IGNORE_KEYWORDS:
            if keyword in message:
                return FeedbackType.IGNORED

        return FeedbackType.NEUTRAL

    def record_feedback(self, feedback: FeedbackType, action_id: str,
                      context: Dict[str, Any]):
        """
        记录反馈

        Args:
            feedback: 反馈类型
            action_id: 对应的行动ID
            context: 上下文信息
        """
        record = {
            "feedback": feedback.value,
            "action_id": action_id,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }

        self.feedback_history.append(record)
        if len(self.feedback_history) > self.max_history:
            self.feedback_history.pop(0)

        logger.debug(f"[反馈学习] 记录反馈: {feedback.value} for {action_id}")

    def get_feedback_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取反馈统计

        Args:
            hours: 统计最近几小时的反馈

        Returns:
            统计信息
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_feedback = [
            f for f in self.feedback_history
            if datetime.fromisoformat(f["timestamp"]) > cutoff_time
        ]

        if not recent_feedback:
            return {"total": 0, "positive": 0, "negative": 0, "ratio": 0.5}

        total = len(recent_feedback)
        positive = sum(1 for f in recent_feedback if f["feedback"] == "positive")
        negative = sum(1 for f in recent_feedback if f["feedback"] == "negative")
        ignored = sum(1 for f in recent_feedback if f["feedback"] == "ignored")

        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "ignored": ignored,
            "neutral": total - positive - negative - ignored,
            "positive_ratio": positive / total if total > 0 else 0,
            "negative_ratio": negative / total if total > 0 else 0
        }


class PreferenceLearner:
    """偏好学习器 - 根据反馈动态调整决策策略"""

    def __init__(self):
        self.feedback_analyzer = FeedbackAnalyzer()
        self.adjustment_history: List[Dict[str, Any]] = []

        # 当前调整值
        self.adjustments = {
            "intervention_threshold": 0.5,  # 干预阈值（0-1）
            "value_weights": {
                "user_efficiency": 0.35,
                "user_wellbeing": 0.30,
                "helpful": 0.25,
                "non_intrusive": 0.10,
            },
            "learning_rate": 0.1  # 学习率
        }

        # 加载历史调整
        self._load_adjustments()

    def _load_adjustments(self):
        """从文件加载历史调整"""
        try:
            file_path = Path(__file__).parent / "preference_adjustments.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.adjustments.update(data.get("adjustments", {}))
                    logger.info(f"[反馈学习] 加载调整: {self.adjustments}")
        except Exception as e:
            logger.warning(f"[反馈学习] 加载调整失败: {e}")

    def _save_adjustments(self):
        """保存调整到文件"""
        try:
            file_path = Path(__file__).parent / "preference_adjustments.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "adjustments": self.adjustments,
                    "last_updated": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"[反馈学习] 保存调整失败: {e}")

    def learn_from_feedback(self, action_id: str, context: Dict[str, Any]):
        """
        从反馈中学习

        Args:
            action_id: 行动ID
            context: 上下文（包含用户消息等）
        """
        user_message = context.get("user_message", "")
        feedback_type = self.feedback_analyzer.analyze_user_message(user_message, context)

        # 记录反馈
        self.feedback_analyzer.record_feedback(feedback_type, action_id, context)

        # 根据反馈调整策略
        if feedback_type == FeedbackType.POSITIVE:
            self._reinforce_positive(context)
        elif feedback_type == FeedbackType.NEGATIVE:
            self._reinforce_negative(context)
        elif feedback_type == FeedbackType.IGNORED:
            self._reinforce_ignored(context)

        # 保存调整
        self._save_adjustments()

    def _reinforce_positive(self, context: Dict[str, Any]):
        """正面反馈强化"""
        logger.info("[反馈学习] 正面反馈 - 增强当前策略")

        # 稍微提高干预阈值（用户接受，可以更主动）
        self.adjustments["intervention_threshold"] = min(
            self.adjustments["intervention_threshold"] + 0.05,
            0.8
        )

        # 增强"有帮助性"权重
        self.adjustments["value_weights"]["helpful"] = min(
            self.adjustments["value_weights"]["helpful"] + 0.02,
            0.4
        )
        self._normalize_weights()

    def _reinforce_negative(self, context: Dict[str, Any]):
        """负面反馈惩罚"""
        logger.warning("[反馈学习] 负面反馈 - 减弱主动性")

        # 降低干预阈值（用户觉得打扰，需要更谨慎）
        self.adjustments["intervention_threshold"] = max(
            self.adjustments["intervention_threshold"] - 0.1,
            0.3
        )

        # 增强"非打扰性"权重
        self.adjustments["value_weights"]["non_intrusive"] = min(
            self.adjustments["value_weights"]["non_intrusive"] + 0.05,
            0.3
        )
        self._normalize_weights()

    def _reinforce_ignored(self, context: Dict[str, Any]):
        """被忽略时调整"""
        logger.debug("[反馈学习] 被忽略 - 调整时机")

        # 不改变阈值，但记录忽略的情境
        # 可以用于后续的时序学习

    def _normalize_weights(self):
        """归一化权重"""
        weights = self.adjustments["value_weights"]
        total = sum(weights.values())

        for key in weights:
            weights[key] = weights[key] / total

    def get_adjusted_agency_level(self, original_level: str) -> str:
        """
        根据学习结果调整自主性等级

        Args:
            original_level: 原始等级

        Returns:
            调整后的等级
        """
        stats = self.feedback_analyzer.get_feedback_stats(hours=24)

        # 如果负面反馈超过60%，降低自主性
        if stats["negative_ratio"] > 0.6 and stats["total"] >= 5:
            if original_level == "HIGH":
                return "MEDIUM"
            elif original_level == "MEDIUM":
                return "LOW"

        # 如果正面反馈超过70%，提高自主性
        if stats["positive_ratio"] > 0.7 and stats["total"] >= 5:
            if original_level == "LOW":
                return "MEDIUM"
            elif original_level == "MEDIUM":
                return "HIGH"

        return original_level

    def get_adjusted_threshold(self, original_threshold: float) -> float:
        """
        获取调整后的决策阈值

        Args:
            original_threshold: 原始阈值

        Returns:
            调整后的阈值
        """
        # 返回学习后的阈值
        return self.adjustments["intervention_threshold"]

    def get_adjusted_weights(self) -> Dict[str, float]:
        """获取调整后的价值权重"""
        return self.adjustments["value_weights"].copy()

    def get_learning_status(self) -> Dict[str, Any]:
        """获取学习状态"""
        stats = self.feedback_analyzer.get_feedback_stats(hours=24)

        return {
            "feedback_stats": stats,
            "current_threshold": self.adjustments["intervention_threshold"],
            "current_weights": self.adjustments["value_weights"],
            "adjustment_count": len(self.adjustment_history),
            "learning_rate": self.adjustments["learning_rate"]
        }


# 全局实例
_preference_learner: Optional[PreferenceLearner] = None


def get_preference_learner() -> PreferenceLearner:
    """获取偏好学习器实例"""
    global _preference_learner
    if _preference_learner is None:
        _preference_learner = PreferenceLearner()
    return _preference_learner
