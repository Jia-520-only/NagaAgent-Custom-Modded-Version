#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主动交流模式
AI会主动发起对话
基于LLM生成个性化话题，而非预设模板
"""
import asyncio
import logging
import random
import time
from datetime import datetime
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger("ActiveCommunication")

class ActiveCommunicationManager:
    """主动交流管理器 - 使用LLM生成话题"""

    def __init__(self):
        self.enabled = False
        self.running = False
        self.check_interval = 300  # 默认5分钟检查一次
        self.last_interaction_time = time.time()
        self.topics_file = Path("voice/auth/active_topics.json")
        self.topics: List[str] = []
        self.used_topics: List[str] = []

        # LLM话题生成器
        self._topic_generator = None
        self._use_llm = True  # 优先使用LLM生成

        # 加载话题库（作为回退方案）
        self._load_topics()

    def _load_topics(self):
        """加载话题库（作为回退方案）"""
        try:
            if self.topics_file.exists():
                import json
                with open(self.topics_file, 'r', encoding='utf-8') as f:
                    self.topics = json.load(f)
                logger.info(f"已加载 {len(self.topics)} 个备选话题（仅作为回退方案）")
            else:
                # 默认话题库（很少使用）
                self.topics = [
                    "今天过得怎么样？",
                    "有什么新鲜事吗？"
                ]
                self._save_topics()
        except Exception as e:
            logger.error(f"加载话题库失败: {e}")
            self.topics = ["今天过得怎么样？"]

    def _save_topics(self):
        """保存话题库"""
        try:
            self.topics_file.parent.mkdir(parents=True, exist_ok=True)
            import json
            with open(self.topics_file, 'w', encoding='utf-8') as f:
                json.dump(self.topics, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存话题库失败: {e}")

    def _get_topic_generator(self):
        """获取话题生成器"""
        if self._topic_generator is None:
            try:
                from system.topic_generator import get_topic_generator
                self._topic_generator = get_topic_generator()
                logger.info("[主动交流] LLM话题生成器已加载")
            except Exception as e:
                logger.warning(f"[主动交流] 话题生成器加载失败: {e}")
                self._use_llm = False
        return self._topic_generator

    async def _build_context(self) -> dict:
        """构建话题生成的上下文"""
        context = {
            "time": datetime.now(),
            "last_interaction_hours": (time.time() - self.last_interaction_time) / 3600,
            "emotion": "平静",
            "weather": None,
            "recent_memories": [],
            "life_book_context": {}
        }

        # 尝试从各系统获取上下文
        try:
            # 从后端意识获取
            from system.consciousness_engine import get_backend_awareness
            backend = get_backend_awareness()
            if backend:
                backend.update_all()
                state = backend.backend_state

                # 情感状态
                emotional = state.get("emotional_state", {})
                context["emotion"] = emotional.get("current_emotion", "平静")

                # 交互感知
                interaction = state.get("interaction_awareness", {})
                last_interaction = interaction.get("last_interaction_time")
                if last_interaction:
                    try:
                        last_time = datetime.fromisoformat(last_interaction) if isinstance(last_interaction, str) else last_interaction
                        hours = (datetime.now() - last_time).total_seconds() / 3600
                        context["last_interaction_hours"] = hours
                    except Exception:
                        pass

                # 天气
                spatial_temporal = state.get("spatial_temporal", {})
                if spatial_temporal:
                    weather_data = spatial_temporal.get("weather", {})
                    if weather_data:
                        context["weather"] = weather_data

        except Exception as e:
            logger.debug(f"[主动交流] 获取上下文失败: {e}")

        return context

    def add_topic(self, topic: str):
        """添加新话题（不建议使用，LLM会自动生成）"""
        if topic and topic not in self.topics:
            self.topics.append(topic)
            self._save_topics()
            logger.info(f"已添加话题: {topic}")

    def remove_topic(self, topic: str):
        """删除话题"""
        if topic in self.topics:
            self.topics.remove(topic)
            self._save_topics()
            logger.info(f"已删除话题: {topic}")

    def get_random_topic(self) -> Optional[str]:
        """获取随机话题（仅作为回退方案）"""
        available_topics = [t for t in self.topics if t not in self.used_topics]

        if not available_topics:
            self.used_topics = []
            available_topics = self.topics

        if available_topics:
            topic = random.choice(available_topics)
            self.used_topics.append(topic)
            if len(self.used_topics) > 10:
                self.used_topics.pop(0)
            return topic

        return None

    def record_interaction(self):
        """记录用户交互"""
        self.last_interaction_time = time.time()
        logger.debug("已记录用户交互时间")

    def should_initiate_conversation(self) -> bool:
        """判断是否应该主动发起对话"""
        if not self.enabled:
            return False

        idle_time = time.time() - self.last_interaction_time
        min_idle_time = self.check_interval * 2

        if idle_time >= min_idle_time:
            logger.info(f"用户空闲 {idle_time/60:.1f} 分钟，考虑主动交流")
            return True

        return False

    async def get_initiated_message(self) -> Optional[str]:
        """获取主动交流的消息（使用LLM生成）"""
        if not self.should_initiate_conversation():
            return None

        # 优先使用LLM生成
        if self._use_llm:
            try:
                generator = self._get_topic_generator()
                if generator:
                    context = await self._build_context()
                    topic = await generator.generate_topic(context, "general")

                    if topic and topic.content:
                        logger.info(f"[主动交流] LLM生成话题: {topic.content[:50]}...")
                        return topic.content
                    else:
                        logger.debug("[主动交流] LLM生成失败，使用回退话题")
            except Exception as e:
                logger.error(f"[主动交流] LLM生成异常: {e}")

        # 回退到预设话题
        topic = self.get_random_topic()
        if topic:
            logger.info(f"[主动交流] 预设话题: {topic}")
            return topic

        return None

    async def send_topic_suggestion(self, topic: str, context: dict = None):
        """发送话题建议（由自主引擎调用）"""
        logger.info(f"[主动交流] 接收话题建议: {topic[:50]}...")
        # 这里可以集成实际的发送逻辑
        # 目前由UI层处理

    def start(self):
        """启动主动交流（实际逻辑由调用方控制）"""
        from system.config import config
        self.enabled = getattr(config.system, 'active_communication', False)
        self.check_interval = 300  # 5分钟
        logger.info(f"主动交流模式: {'启用' if self.enabled else '禁用'} (使用{'LLM' if self._use_llm else '预设'}话题)")

    def stop(self):
        """停止主动交流"""
        self.enabled = False
        logger.info("主动交流模式已停止")


# 全局实例
_active_comm_manager: Optional[ActiveCommunicationManager] = None

def get_active_comm_manager() -> ActiveCommunicationManager:
    """获取主动交流管理器实例"""
    global _active_comm_manager
    if _active_comm_manager is None:
        _active_comm_manager = ActiveCommunicationManager()
    return _active_comm_manager
