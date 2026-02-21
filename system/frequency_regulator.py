#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
频率调节器 - Frequency Regulator
根据用户反馈和活跃度智能调节主动交流频率
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from system.config import config, logger


@dataclass
class InteractionRecord:
    """交互记录"""
    timestamp: datetime
    user_response: str
    message_type: str
    response_score: float  # 0-1
    response_length: int


class FrequencyRegulator:
    """频率调节器 - 智能调节主动交流频率"""

    def __init__(self):
        # 从配置加载参数
        self._base_interval = config.active_communication.regulator.base_interval
        self._min_interval = config.active_communication.regulator.min_interval
        self._max_interval = config.active_communication.regulator.max_interval
        self._adjustment_factor = config.active_communication.regulator.adjustment_factor
        self._response_window = config.active_communication.regulator.response_window

        # 运行时状态
        self._current_interval = self._base_interval
        self._user_response_score = 0.5  # 0-1, 用户响应积极性
        self._interaction_history: List[InteractionRecord] = []
        self._last_trigger_time: Optional[datetime] = None
        self._total_interactions = 0
        self._positive_responses = 0

        # 情绪词汇库
        self._positive_words = [
            "好", "不错", "喜欢", "开心", "高兴", "哈哈", "嗯", "对",
            "谢谢", "可以", "行", "ok", "OK", "good", "yes", "是",
            "明白", "知道了", "懂了", "了解", "确实", "确实如此"
        ]

        self._negative_words = [
            "不", "别", "不想", "烦", "烦死了", "不要", "不需要",
            "忙", "很忙", "忙着", "在忙", "没空", "没时间", "安静",
            "闭嘴", "滚", "别说了", "不要说话", "no", "NO"
        ]

        logger.info(f"[频率调节器] 初始化完成 - 基础间隔: {self._base_interval}分钟, "
                   f"范围: {self._min_interval}-{self._max_interval}分钟")

    def record_interaction(
        self,
        user_response: str,
        message_type: str,
        timestamp: Optional[datetime] = None
    ) -> float:
        """
        记录用户交互并调整频率

        参数:
            user_response: 用户回复内容
            message_type: 消息类型
            timestamp: 交互时间戳（可选，默认为当前时间）

        返回:
            响应评分 (0-1)
        """
        if timestamp is None:
            timestamp = datetime.now()

        # 分析用户响应
        score = self._analyze_response(user_response)
        length = len(user_response.strip())

        # 创建交互记录
        record = InteractionRecord(
            timestamp=timestamp,
            user_response=user_response,
            message_type=message_type,
            response_score=score,
            response_length=length
        )

        # 添加到历史记录
        self._interaction_history.append(record)
        self._total_interactions += 1

        if score > 0.5:
            self._positive_responses += 1

        # 清理过期记录（只保留最近N条）
        self._cleanup_old_records()

        # 更新评分（使用指数平滑）
        self._update_response_score(score)

        # 调整频率
        self._adjust_frequency()

        logger.info(f"[频率调节器] 记录交互 - 评分: {score:.2f}, "
                   f"当前间隔: {self._current_interval:.1f}分钟")

        return score

    def _analyze_response(self, response: str) -> float:
        """
        分析用户响应积极性

        参数:
            response: 用户回复内容

        返回:
            0-1的评分（越接近1越积极）
        """
        if not response or not response.strip():
            # 无响应
            return 0.0

        response = response.strip().lower()

        # 基础评分：响应长度
        length_score = min(len(response) / 20, 1.0)  # 20字以上得满分

        # 情绪词分析
        positive_count = sum(1 for word in self._positive_words if word in response)
        negative_count = sum(1 for word in self._negative_words if word in response)

        # 情绪评分
        if negative_count > positive_count:
            emotion_score = 0.0  # 消极情绪
        elif positive_count > 0:
            emotion_score = min(positive_count / 2, 1.0)  # 积极情绪
        else:
            emotion_score = 0.5  # 中性情绪

        # 综合评分（长度权重0.3，情绪权重0.7）
        final_score = length_score * 0.3 + emotion_score * 0.7

        # 特殊情况处理
        if "忙" in response or "没空" in response:
            final_score = min(final_score, 0.2)  # 用户在忙，降低评分

        return max(0.0, min(1.0, final_score))

    def _update_response_score(self, new_score: float):
        """
        更新响应评分（使用指数平滑）

        公式: new_score = old_score * alpha + current_score * (1 - alpha)
        """
        alpha = 0.7  # 平滑系数，越接近1越保留历史信息
        self._user_response_score = self._user_response_score * alpha + new_score * (1 - alpha)

    def _adjust_frequency(self):
        """根据当前评分调整频率"""
        if self._user_response_score > 0.7:
            # 用户积极响应，增加频率
            self._current_interval = max(
                self._min_interval,
                self._current_interval * (1 - self._adjustment_factor)
            )
            logger.debug(f"[频率调节器] 用户积极，增加频率 -> {self._current_interval:.1f}分钟")

        elif self._user_response_score < 0.3:
            # 用户不积极，减少频率
            self._current_interval = min(
                self._max_interval,
                self._current_interval * (1 + self._adjustment_factor)
            )
            logger.debug(f"[频率调节器] 用户不积极，减少频率 -> {self._current_interval:.1f}分钟")

        else:
            # 回归基础间隔
            diff = self._current_interval - self._base_interval
            if abs(diff) > 5:  # 偏差大于5分钟时才调整
                adjustment = diff * 0.2  # 缓慢回归
                self._current_interval = self._base_interval + adjustment
            logger.debug(f"[频率调节器] 回归基础间隔 -> {self._current_interval:.1f}分钟")

    def _cleanup_old_records(self):
        """清理过期的交互记录"""
        if not self._interaction_history:
            return

        # 只保留最近的100条记录
        if len(self._interaction_history) > 100:
            self._interaction_history = self._interaction_history[-100:]

        # 清理超过30天的记录
        cutoff_time = datetime.now() - timedelta(days=30)
        self._interaction_history = [
            record for record in self._interaction_history
            if record.timestamp > cutoff_time
        ]

    def get_next_trigger_time(self) -> datetime:
        """
        获取下次触发时间

        返回:
            下次触发的时间点
        """
        return datetime.now() + timedelta(minutes=self._current_interval)

    def should_trigger_now(self) -> bool:
        """
        检查是否应该现在触发

        返回:
            True if should trigger now
        """
        if self._last_trigger_time is None:
            return True

        elapsed = (datetime.now() - self._last_trigger_time).total_seconds() / 60
        return elapsed >= self._current_interval

    def record_trigger(self):
        """记录触发时间"""
        self._last_trigger_time = datetime.now()
        logger.debug(f"[频率调节器] 记录触发时间: {self._last_trigger_time}")

    def get_current_interval(self) -> float:
        """获取当前间隔（分钟）"""
        return self._current_interval

    def get_user_response_score(self) -> float:
        """获取用户响应评分"""
        return self._user_response_score

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        返回:
            {
                "current_interval": 30.0,
                "base_interval": 30,
                "min_interval": 10,
                "max_interval": 120,
                "user_response_score": 0.5,
                "total_interactions": 10,
                "positive_responses": 5,
                "positive_rate": 0.5,
                "recent_history": [...]
            }
        """
        recent_history = [
            {
                "timestamp": record.timestamp.isoformat(),
                "response_length": record.response_length,
                "response_score": record.response_score,
                "message_type": record.message_type
            }
            for record in self._interaction_history[-10:]  # 最近10条
        ]

        return {
            "current_interval": round(self._current_interval, 1),
            "base_interval": self._base_interval,
            "min_interval": self._min_interval,
            "max_interval": self._max_interval,
            "user_response_score": round(self._user_response_score, 3),
            "total_interactions": self._total_interactions,
            "positive_responses": self._positive_responses,
            "positive_rate": round(self._positive_responses / max(self._total_interactions, 1), 3),
            "adjustment_factor": self._adjustment_factor,
            "recent_history": recent_history,
            "last_trigger": self._last_trigger_time.isoformat() if self._last_trigger_time else None
        }

    def reset(self):
        """重置调节器状态"""
        self._current_interval = self._base_interval
        self._user_response_score = 0.5
        self._interaction_history.clear()
        self._last_trigger_time = None
        self._total_interactions = 0
        self._positive_responses = 0
        logger.info("[频率调节器] 已重置")

    def adjust_interval_manually(self, interval: int):
        """
        手动调整间隔

        参数:
            interval: 新的间隔（分钟）
        """
        interval = max(self._min_interval, min(self._max_interval, interval))
        self._current_interval = float(interval)
        logger.info(f"[频率调节器] 手动调整间隔: {interval}分钟")

    def get_recent_interactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的交互记录

        参数:
            limit: 返回数量

        返回:
            交互记录列表
        """
        recent_records = self._interaction_history[-limit:]

        return [
            {
                "timestamp": record.timestamp.isoformat(),
                "user_response": record.user_response[:50] + "..." if len(record.user_response) > 50 else record.user_response,
                "response_score": record.response_score,
                "response_length": record.response_length,
                "message_type": record.message_type
            }
            for record in reversed(recent_records)
        ]

    def is_user_busy(self) -> bool:
        """
        判断用户是否忙碌

        基于最近的交互记录判断

        返回:
            True if user is busy
        """
        if not self._interaction_history:
            return False

        # 检查最近的交互中是否频繁出现"忙"字
        recent_minutes = 10
        cutoff_time = datetime.now() - timedelta(minutes=recent_minutes)

        recent_records = [
            record for record in self._interaction_history
            if record.timestamp > cutoff_time
        ]

        if not recent_records:
            return False

        # 统计"忙"字出现的频率
        busy_count = sum(
            1 for record in recent_records
            if "忙" in record.user_response or "没空" in record.user_response
        )

        return busy_count > 0 and busy_count >= len(recent_records) * 0.5

    def should_pause_during_busy(self) -> bool:
        """
        判断是否应该在用户忙碌时暂停主动交流

        返回:
            True if should pause
        """
        # 如果用户忙碌且当前评分较低，建议暂停
        if self.is_user_busy() and self._user_response_score < 0.3:
            logger.info("[频率调节器] 检测到用户忙碌，建议暂停主动交流")
            return True
        return False

    def export_stats(self) -> str:
        """
        导出统计信息为可读字符串

        返回:
            统计信息字符串
        """
        stats = self.get_stats()

        lines = [
            "=== 频率调节器统计 ===",
            f"当前间隔: {stats['current_interval']} 分钟",
            f"基础间隔: {stats['base_interval']} 分钟",
            f"范围: {stats['min_interval']}-{stats['max_interval']} 分钟",
            f"用户响应评分: {stats['user_response_score']}",
            f"总交互次数: {stats['total_interactions']}",
            f"积极响应: {stats['positive_responses']} ({stats['positive_rate']*100:.1f}%)",
            ""
        ]

        if stats['recent_history']:
            lines.append("=== 最近交互 ===")
            for i, record in enumerate(stats['recent_history'][:5], 1):
                lines.append(
                    f"{i}. 评分: {record['response_score']:.2f}, "
                    f"长度: {record['response_length']}, "
                    f"类型: {record['message_type']}"
                )

        return "\n".join(lines)


# 全局实例
_frequency_regulator: Optional[FrequencyRegulator] = None


def get_frequency_regulator() -> FrequencyRegulator:
    """获取频率调节器实例"""
    global _frequency_regulator
    if _frequency_regulator is None:
        _frequency_regulator = FrequencyRegulator()
    return _frequency_regulator
