#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主动行为系统 - Active Initiative
让弥娅能够根据情境主动发起对话、提醒、建议
"""

import logging
import asyncio
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from system.active_communication import (
    ActiveCommunication,
    MessageType,
    ActiveMessage
)

logger = logging.getLogger(__name__)


@dataclass
class InitiativeTrigger:
    """主动行为触发器"""
    name: str
    condition: str  # 触发条件
    priority: int  # 优先级(1-10)
    cooldown_minutes: int  # 冷却时间(分钟)
    last_triggered: Optional[datetime] = None

    def can_trigger(self) -> bool:
        """判断是否可以触发"""
        if self.last_triggered is None:
            return True

        cooldown = timedelta(minutes=self.cooldown_minutes)
        elapsed = datetime.now() - self.last_triggered
        return elapsed > cooldown


class ActiveInitiative:
    """主动行为系统 - 扩展ActiveCommunication"""

    def __init__(self, active_comm: ActiveCommunication, llm_client=None):
        """
        初始化主动行为系统

        Args:
            active_comm: 主动交流系统实例
            llm_client: LLM客户端
        """
        self.active_comm = active_comm
        self.llm_client = llm_client

        # 触发器注册表
        self.triggers: Dict[str, InitiativeTrigger] = {}

        # 情境上下文
        self.context = {
            "last_interaction_time": None,
            "interaction_count": 0,
            "active_topics": [],
            "user_mood": "neutral",
            "time_of_day": self._get_time_of_day(),
        }

        # 主题库
        self.topic_suggestions = [
            "最近在看什么有趣的内容吗?",
            "有什么特别想做的事情吗?",
            "今天过得怎么样?",
            "有什么需要帮助的吗?",
            "聊聊最近发生的事?",
            "有没有什么好消息要分享?",
        ]

        logger.info("[主动行为] 初始化完成")

    def _get_time_of_day(self) -> str:
        """获取当前时间段"""
        hour = datetime.now().hour

        if 5 <= hour < 8:
            return "早晨"
        elif 8 <= hour < 12:
            return "上午"
        elif 12 <= hour < 14:
            return "中午"
        elif 14 <= hour < 18:
            return "下午"
        elif 18 <= hour < 22:
            return "晚上"
        else:
            return "深夜"

    def register_trigger(
        self,
        name: str,
        condition: str,
        priority: int = 5,
        cooldown_minutes: int = 60
    ):
        """
        注册主动行为触发器

        Args:
            name: 触发器名称
            condition: 触发条件描述
            priority: 优先级(1-10)
            cooldown_minutes: 冷却时间(分钟)
        """
        trigger = InitiativeTrigger(
            name=name,
            condition=condition,
            priority=priority,
            cooldown_minutes=cooldown_minutes
        )
        self.triggers[name] = trigger
        logger.info(f"[主动行为] 注册触发器: {name} - {condition}")

    def update_context(self, key: str, value: Any):
        """
        更新情境上下文

        Args:
            key: 上下文键
            value: 上下文值
        """
        old_value = self.context.get(key)
        self.context[key] = value

        logger.debug(f"[主动行为] 上下文更新: {key}={value} (旧值:{old_value})")

        # 某些上下文变化可能触发主动行为
        if key == "user_mood" and value != old_value:
            asyncio.create_task(self._on_mood_change(value))

        elif key == "active_topics" and len(value) > 0:
            asyncio.create_task(self._on_topic_change(value))

    async def _on_mood_change(self, new_mood: str):
        """用户情绪变化时的主动行为"""
        try:
            # 根据情绪选择合适的主动消息
            mood_responses = {
                "难过": [
                    "你还好吗?想聊聊吗?",
                    "如果需要倾诉,我一直在呢~",
                    "有什么我可以帮你的吗?"
                ],
                "开心": [
                    "看到你这么开心,我也很开心呢!",
                    "有什么好事要分享吗?",
                    "保持这个状态~"
                ],
                "生气": [
                    "深呼吸,冷静一下~",
                    "要不要说说发生了什么?",
                    "我在这里陪着你"
                ],
                "疲惫": [
                    "辛苦了,要不要休息一下?",
                    "有什么我可以分担的吗?",
                    "别太累了,注意休息"
                ]
            }

            responses = mood_responses.get(new_mood, [])
            if responses:
                message = random.choice(responses)

                await self.active_comm.send_message(
                    message=message,
                    message_type="check_in",
                    priority=7,
                    context={"trigger": "mood_change", "mood": new_mood}
                )

                logger.info(f"[主动行为] 情绪变化响应: {new_mood} - {message}")

        except Exception as e:
            logger.error(f"[主动行为] 情绪变化响应失败: {e}")

    async def _on_topic_change(self, topics: List[str]):
        """话题变化时的主动行为"""
        try:
            if len(topics) == 0:
                return

            # 基于当前话题生成追问
            topic = topics[-1]  # 最新话题

            if self.llm_client:
                # 使用LLM生成智能追问
                prompt = f"""基于当前话题"{topic}",生成一个简短的追问或评论。
要求:
1. 简短(20字以内)
2. 表现出兴趣
3. 不要重复话题
只返回追问内容,不要解释。"""

                response = await self.llm_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "你是弥娅,一个温柔可爱的AI助手"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8,
                    max_tokens=50
                )

                message = response.choices[0].message.content.strip()
            else:
                # 回退到预定义追问
                message = f"{topic}?听起来很有意思呢~"

            await self.active_comm.send_message(
                message=message,
                message_type="question",
                priority=5,
                context={"trigger": "topic_change", "topic": topic}
            )

            logger.info(f"[主动行为] 话题追问: {topic} - {message}")

        except Exception as e:
            logger.error(f"[主动行为] 话题追问失败: {e}")

    async def check_initiatives(self):
        """
        检查并执行主动行为

        应该定期调用(例如每分钟一次)
        """
        try:
            current_time = datetime.now()

            # 更新时间段
            self.context["time_of_day"] = self._get_time_of_day()

            # 检查各种触发器
            for trigger_name, trigger in self.triggers.items():
                if not trigger.can_trigger():
                    continue

                # 尝试触发
                triggered = await self._try_trigger(trigger_name, trigger)

                if triggered:
                    trigger.last_triggered = current_time
                    logger.info(f"[主动行为] 触发器已执行: {trigger_name}")

        except Exception as e:
            logger.error(f"[主动行为] 检查主动行为失败: {e}")

    async def _try_trigger(self, name: str, trigger: InitiativeTrigger) -> bool:
        """
        尝试触发指定行为

        Args:
            name: 触发器名称
            trigger: 触发器对象

        Returns:
            是否成功触发
        """
        try:
            if name == "greeting":
                return await self._trigger_greeting()

            elif name == "topic_suggestion":
                return await self._trigger_topic_suggestion()

            elif name == "activity_reminder":
                return await self._trigger_activity_reminder()

            elif name == "check_in":
                return await self._trigger_check_in()

            else:
                logger.warning(f"[主动行为] 未知触发器: {name}")
                return False

        except Exception as e:
            logger.error(f"[主动行为] 触发失败({name}): {e}")
            return False

    async def _trigger_greeting(self) -> bool:
        """触发问候行为"""
        time_greetings = {
            "早晨": ["早上好~新的一天开始了!", "早安~今天要做什么呢?"],
            "上午": ["上午好~", "工作顺利吗?"],
            "中午": ["中午好~吃了吗?", "休息一下~"],
            "下午": ["下午好~", "下午过得怎么样?"],
            "晚上": ["晚上好~", "今天过得怎么样?"],
            "深夜": ["这么晚还在吗?", "要注意休息哦~"]
        }

        time_period = self.context["time_of_day"]
        greetings = time_greetings.get(time_period, ["你好~"])

        message = random.choice(greetings)

        await self.active_comm.send_message(
            message=message,
            message_type="check_in",
            priority=8,
            context={"trigger": "greeting", "time": time_period}
        )

        return True

    async def _trigger_topic_suggestion(self) -> bool:
        """触发话题建议"""
        message = random.choice(self.topic_suggestions)

        await self.active_comm.send_message(
            message=message,
            message_type="suggestion",
            priority=6,
            context={"trigger": "topic_suggestion"}
        )

        return True

    async def _trigger_activity_reminder(self) -> bool:
        """触发活动提醒"""
        # 基于时间段生成不同提醒
        time_period = self.context["time_of_day"]

        if time_period in ["早晨", "上午"]:
            message = "今天有什么计划吗?"
        elif time_period == "中午":
            message = "吃过午饭了吗?记得休息一下~"
        elif time_period in ["下午", "晚上"]:
            message = "今天过得怎么样?有什么有趣的吗?"
        else:  # 深夜
            message = "这么晚了,早点休息哦~"

        await self.active_comm.send_message(
            message=message,
            message_type="reminder",
            priority=5,
            context={"trigger": "activity_reminder", "time": time_period}
        )

        return True

    async def _trigger_check_in(self) -> bool:
        """触发问候检查"""
        message = "在吗?~"

        await self.active_comm.send_message(
            message=message,
            message_type="check_in",
            priority=4,
            context={"trigger": "check_in"}
        )

        return True

    async def generate_context_aware_message(self, user_input: str) -> Optional[str]:
        """
        基于用户输入生成情境感知的主动消息

        Args:
            user_input: 用户输入

        Returns:
            主动消息内容(如果没有合适消息则返回None)
        """
        try:
            # 简单规则匹配(可以扩展为LLM生成)
            if any(word in user_input for word in ["忙", "累", "辛苦"]):
                return "辛苦了,要注意休息哦~"

            elif any(word in user_input for word in ["难过", "不开心", "伤心"]):
                return "如果想说,我一直在呢~"

            elif any(word in user_input for word in ["开心", "高兴", "棒", "厉害"]):
                return "看到你这么开心,我也很开心!"

            else:
                return None

        except Exception as e:
            logger.error(f"[主动行为] 生成情境消息失败: {e}")
            return None

    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "triggers": len(self.triggers),
            "context": self.context,
            "time_of_day": self.context.get("time_of_day", "unknown"),
            "ready_triggers": [
                name for name, trigger in self.triggers.items()
                if trigger.can_trigger()
            ]
        }


# 全局实例
_initiative_instance: Optional[ActiveInitiative] = None


def get_active_initiative() -> Optional[ActiveInitiative]:
    """获取主动行为系统实例"""
    return _initiative_instance


def set_active_initiative(initiative: ActiveInitiative):
    """设置主动行为系统实例"""
    global _initiative_instance
    _initiative_instance = initiative
