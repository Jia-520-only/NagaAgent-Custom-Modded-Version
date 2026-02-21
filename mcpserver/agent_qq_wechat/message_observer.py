#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息旁观系统 - Message Observer
让弥娅能够旁观群聊/私聊,主动记录有趣信息
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from collections import deque
import json

logger = logging.getLogger(__name__)


class MessageObserver:
    """消息旁观器 - 主动观察和记录有价值的信息"""

    def __init__(self, message_listener):
        """
        初始化消息旁观器

        Args:
            message_listener: QQ消息监听器实例
        """
        self.message_listener = message_listener
        self.qq_config = message_listener.qq_config if hasattr(message_listener, 'qq_config') else {}

        # 配置
        self.enabled = self.qq_config.get("enable_observer", True)
        self.observation_groups = self.qq_config.get("observation_groups", [])
        self.interest_keywords = self.qq_config.get("interest_keywords", [
            "喜欢", "讨厌", "爱", "恨", "开心", "难过", "生气",
            "重要", "记得", "记住", "秘密", "悄悄话",
            "建议", "推荐", "分享", "告诉", "提醒"
        ])

        # 观察
        self.observed_messages: deque = deque(maxlen=1000)
        self.interesting_messages: deque = deque(maxlen=200)
        self.last_observation_time = {}

        logger.info(f"[消息旁观] 初始化完成: enabled={self.enabled}, groups={self.observation_groups}")

    async def observe_message(
        self,
        message_type: str,
        sender_id: str,
        group_id: Optional[str],
        message: str,
        raw_data: Dict[str, Any]
    ) -> bool:
        """
        观察消息并判断是否需要记录

        Args:
            message_type: 消息类型 (private/group)
            sender_id: 发送者ID
            group_id: 群ID
            message: 消息内容
            raw_data: 原始消息数据

        Returns:
            是否已记录
        """
        if not self.enabled:
            return False

        try:
            # 检查是否在观察列表中
            should_observe = self._should_observe(message_type, group_id, sender_id)
            if not should_observe:
                return False

            # 记录观察到的消息
            observation = {
                "timestamp": datetime.now().isoformat(),
                "message_type": message_type,
                "sender_id": sender_id,
                "group_id": group_id,
                "message": message,
                "raw_data": raw_data
            }

            self.observed_messages.append(observation)

            # 判断是否为有趣消息
            if self._is_interesting(message):
                logger.info(f"[消息旁观] 发现有趣消息: {message[:50]}...")
                self.interesting_messages.append(observation)

                # 自动记录到记忆
                await self._record_interesting_message(observation)
                return True

            return False

        except Exception as e:
            logger.error(f"[消息旁观] 观察消息失败: {e}")
            return False

    def _should_observe(self, message_type: str, group_id: Optional[str], sender_id: str) -> bool:
        """判断是否应该观察此消息"""
        # 如果配置了特定群组,只在群组列表中观察
        if self.observation_groups:
            if message_type == "group":
                return str(group_id) in self.observation_groups
            elif message_type == "private":
                # 私聊如果配置了群组,不观察
                return len(self.observation_groups) == 0

        # 默认观察所有消息
        return True

    def _is_interesting(self, message: str) -> bool:
        """判断消息是否有趣"""
        # 检查是否包含兴趣关键词
        for keyword in self.interest_keywords:
            if keyword in message:
                return True

        # 检查消息长度(长消息通常更有价值)
        if len(message) > 100:
            return True

        # 检查是否包含感叹号或问号(表达强烈情感)
        if "!" in message or "!" in message or "?" in message or "？" in message:
            return True

        return False

    async def _record_interesting_message(self, observation: Dict[str, Any]) -> bool:
        """将有趣消息记录到记忆系统"""
        try:
            from summer_memory.memory_manager import get_memory_manager

            memory_manager = get_memory_manager()
            if not memory_manager or not memory_manager.enabled:
                return False

            # 构造记忆文本
            sender_name = observation["sender_id"]
            if observation["message_type"] == "group":
                memory_text = f"在群聊中,{sender_name}说: {observation['message']}"
            else:
                memory_text = f"{sender_name}私聊说: {observation['message']}"

            logger.info(f"[消息旁观] 记录有趣消息到记忆: {memory_text[:50]}...")

            # 异步记录(不等待完成)
            asyncio.create_task(memory_manager.add_conversation_memory(
                user_input=observation["message"],
                ai_response="[旁观记录]"
            ))

            return True

        except Exception as e:
            logger.error(f"[消息旁观] 记录有趣消息失败: {e}")
            return False

    def get_observation_summary(self) -> Dict[str, Any]:
        """获取观察摘要"""
        return {
            "total_observed": len(self.observed_messages),
            "interesting_count": len(self.interesting_messages),
            "recent_interesting": [
                {
                    "time": msg["timestamp"],
                    "sender": msg["sender_id"],
                    "message": msg["message"][:100]
                }
                for msg in list(self.interesting_messages)[-5:]
            ]
        }

    def get_recent_interesting_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的有趣消息"""
        return list(self.interesting_messages)[-limit:]

    def clear_old_observations(self, days: int = 7):
        """清理旧观察记录"""
        cutoff_time = datetime.now().timestamp() - (days * 86400)

        # 清理普通观察
        while self.observed_messages:
            obs_time = datetime.fromisoformat(self.observed_messages[0]["timestamp"]).timestamp()
            if obs_time < cutoff_time:
                self.observed_messages.popleft()
            else:
                break

        # 清理有趣消息
        while self.interesting_messages:
            obs_time = datetime.fromisoformat(self.interesting_messages[0]["timestamp"]).timestamp()
            if obs_time < cutoff_time:
                self.interesting_messages.popleft()
            else:
                break

        logger.info(f"[消息旁观] 清理了{days}天前的观察记录")


# 全局实例
_observer_instance: Optional[MessageObserver] = None


def get_message_observer() -> Optional[MessageObserver]:
    """获取消息旁观器实例"""
    return _observer_instance


def set_message_observer(observer: MessageObserver):
    """设置消息旁观器实例"""
    global _observer_instance
    _observer_instance = observer
