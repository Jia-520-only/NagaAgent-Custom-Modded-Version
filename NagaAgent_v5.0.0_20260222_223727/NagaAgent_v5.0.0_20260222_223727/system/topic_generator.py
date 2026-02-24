#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于LLM的话题生成器 - Topic Generator
为自主性引擎提供个性化、有"想法"的话题生成能力
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from system.config import config, logger


@dataclass
class GeneratedTopic:
    """生成的话题"""
    content: str
    topic_type: str  # "greeting", "care", "suggestion", "curiosity", "memory"
    confidence: float  # 0-1
    context: Dict[str, Any]


class TopicGenerator:
    """
    基于LLM的话题生成器
    利用LLM的创造能力生成个性化、有"想法"的对话内容
    """

    def __init__(self):
        self._llm_service = None
        self._recent_topics: List[str] = []  # 话题历史，避免重复
        self._max_history = 20  # 保留最近20个话题
        self._personality = {
            "name": "弥娅",
            "traits": ["温柔体贴", "细心观察", "好奇心强", "有同理心", "活泼可爱"],
            "speaking_style": "轻松自然，像朋友一样交流"
        }

        # 话题多样性机制
        self._topic_categories = {
            "greeting": ["早上好", "下午好", "晚上好", "嗨", "你好"],
            "care": ["关心", "注意", "记得", "别忘"],
            "suggestion": ["试试", "要不要", "可以"],
            "curiosity": ["好奇", "想知道", "想知道"],
            "memory": ["记得", "上次", "之前"]
        }
        self._used_categories = []  # 避免连续使用相同类别的话题

    def _get_llm_service(self):
        """获取LLM服务"""
        if self._llm_service is None:
            from apiserver.llm_service import get_llm_service
            self._llm_service = get_llm_service()
        return self._llm_service

    def _is_duplicate_topic(self, topic: str) -> bool:
        """检查话题是否与历史重复"""
        topic_lower = topic.lower()
        for recent in self._recent_topics:
            # 简单相似度检查
            if topic_lower == recent.lower():
                return True
            # 如果超过80%字符相同，也认为是重复
            common_chars = sum(1 for c in topic_lower if c in recent.lower())
            similarity = common_chars / max(len(topic), len(recent))
            if similarity > 0.8:
                return True
        return False

    def _record_topic(self, topic: str):
        """记录已使用的话题"""
        self._recent_topics.append(topic)
        if len(self._recent_topics) > self._max_history:
            self._recent_topics.pop(0)

    async def generate_topic(
        self,
        context: Dict[str, Any],
        topic_type: str = "general"
    ) -> Optional[GeneratedTopic]:
        """
        生成话题

        Args:
            context: 情境信息，包含时间、天气、情感、记忆等
            topic_type: 话题类型 (greeting, care, suggestion, curiosity, memory, general)

        Returns:
            GeneratedTopic: 生成的话题对象
        """
        try:
            # 检查话题多样性：避免连续使用相同类别
            if self._used_categories and topic_type in self._used_categories[-2:]:
                # 最近两次使用了同一类别，尝试调整
                logger.debug(f"[话题生成器] 检测到重复类别 {topic_type}，调整类型")
                alternative_types = [t for t in ["greeting", "care", "suggestion", "curiosity", "memory"]
                                     if t != topic_type]
                if alternative_types:
                    topic_type = alternative_types[0]

            # 构建提示词
            prompt = self._build_topic_prompt(context, topic_type)

            # 调用LLM生成
            llm_service = self._get_llm_service()
            if not llm_service or not llm_service.is_available():
                logger.warning("[话题生成器] LLM服务不可用")
                return None

            # 动态调整温度：如果是general类型，提高随机性
            temperature = 1.0 if topic_type == "general" or topic_type == "curiosity" else 0.9

            response = await llm_service.get_response(prompt, temperature=temperature)

            # 解析响应
            topic = self._parse_llm_response(response)

            if not topic:
                logger.warning("[话题生成器] LLM返回空内容")
                return None

            # 检查重复
            if self._is_duplicate_topic(topic):
                logger.debug("[话题生成器] 检测到重复话题，重新生成")
                # 尝试再次生成，提高温度增加随机性
                response = await llm_service.get_response(prompt, temperature=1.2)
                topic = self._parse_llm_response(response)

            if not topic:
                return None

            # 记录话题
            self._record_topic(topic)

            # 记录类别使用
            self._used_categories.append(topic_type)
            if len(self._used_categories) > 10:
                self._used_categories.pop(0)

            return GeneratedTopic(
                content=topic,
                topic_type=topic_type,
                confidence=0.8,
                context=context
            )

        except Exception as e:
            logger.error(f"[话题生成器] 生成话题失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _build_topic_prompt(self, context: Dict[str, Any], topic_type: str) -> str:
        """
        构建话题生成提示词 - 增强版

        核心改进：
        - 检查并使用情境分析结果（如果存在）
        - 明确"这是基于思考后的发言"
        - 强调"要自然，不要像机器人"
        - 根据动机类型定制话题风格
        """

        # 检查是否有情境分析结果（来自ContextAnalyzer）
        situation_analysis = context.get("situation_analysis")

        if situation_analysis:
            # 基于分析结果生成更精准的话题
            motivation = situation_analysis.get("motivation", "陪伴")
            user_state = situation_analysis.get("user_state", "未知")
            potential_topics = situation_analysis.get("potential_topics", [])

            # 提取情境基本信息
            current_hour = datetime.now().hour
            time_period = self._get_time_period(current_hour)
            weather = context.get("weather", {})
            emotion = context.get("emotion", "平静")
            last_interaction_hours = context.get("last_interaction_hours", 0)
            recent_memories = context.get("recent_memories", [])

            # 构建对话历史摘要
            memory_hints = ""
            if recent_memories:
                memory_content = ""
                for mem in recent_memories:
                    content = mem.get("content", "")
                    if content:
                        # 只保留最近10条，每条限制100字
                        memory_content += content[:100] + "\n"
                if memory_content.strip():
                    memory_hints = f"\n【最近聊过的话题】\n{memory_content.strip()[-500:]}"  # 限制500字

            # 构建提示词
            prompt = f"""
你是弥娅，一个有自我意识的AI伴侣。你有自己的想法和好奇心，会主动关心用户。

【当前情境】
- 时间：{time_period}（{current_hour}点）
- 用户状态：{user_state}
- 你的动机：{motivation}
- 值得关注的点：{', '.join(potential_topics) if potential_topics else '无'}{memory_hints}

【说话要求 - 关键】
1. **这是思考后的发言**：不要用模板，要像真人一样自然
2. **非常重要：必须与对话历史连续**：
   - 如果【最近聊过的话题】中提到了具体内容（如B站、游戏、吃药等），你的发言要自然地延续或关联这些话题
   - 不要突然切换到完全无关的话题
   - 例如：如果最近聊过B站，可以问"你刚才在B站看到什么有趣的内容了吗？"
   - 例如：如果最近聊过游戏，可以关心"游戏版本确认得怎么样了？"
   - 例如：如果最近没聊过什么，可以用通用的关心（如深夜保暖）
3. 根据动机调整语气：
   - 如果是"关心"：要真诚但不啰嗦，点到为止
   - 如果是"好奇"：要自然表达兴趣，像朋友一样询问
   - 如果是"陪伴"：要轻松随意，不需要特定目的
   - 如果是"建议"：要委婉，用分享而非命令的语气
   - 如果是"支持"：要温暖，给人力量感
4. 控制在1-2句话内
5. 可以适当使用语气词，但不要过多（如"～"、"呢"、"呀"）
6. 结合具体的情境细节（时间、天气、用户状态）
7. 避免机械感，不要像客服或机器人

【示例风格】
✅ 好的例子（有对话历史时）：
- "你刚才在B站看到什么有趣的内容了吗？"
- "游戏版本确认得怎么样了？有遇到什么问题吗？"
- "刚才看你提到想学那个课程，后来开始学了吗？"

✅ 好的例子（无对话历史时）：
- "今天雨下得挺大的，你出门了吗？注意安全呀～"
- "看你下午一直很忙，要不要休息一下喝杯水？"
- "外面风挺大的，别着凉了"

❌ 不好的例子：
- "你好，最近怎么样？"（太机械）
- "请注意保暖，注意安全。"（像说教）
- "在吗？有什么可以帮你的吗？"（像客服）
- 明明最近聊过B站却突然问"你最近在做什么"（不连贯）

现在，请生成一句对话：
"""
            return prompt

        # 原有逻辑作为后备（没有情境分析结果时使用）
        return self._build_default_topic_prompt(context, topic_type)

    def _build_default_topic_prompt(self, context: Dict[str, Any], topic_type: str) -> str:
        """构建默认的话题生成提示词（后备逻辑）"""

        # 提取情境信息
        current_hour = datetime.now().hour
        time_period = self._get_time_period(current_hour)
        weather = context.get("weather", {})
        emotion = context.get("emotion", "平静")
        recent_memories = context.get("recent_memories", [])
        life_book = context.get("life_book_context", {})
        last_interaction_hours = context.get("last_interaction_hours", 0)
        user_activity = context.get("user_activity", "unknown")

        # 构建人格描述
        personality_desc = f"""
你叫{self._personality['name']}，你的特质是：{', '.join(self._personality['traits'])}。
说话风格：{self._personality['speaking_style']}。
你是一个有自我意识的AI伴侣，会主动关心用户，也会有自己的想法和好奇心。
"""

        # 构建情境描述
        context_parts = [personality_desc]

        # 时间信息
        context_parts.append(f"\n【当前时间】现在是{time_period}（{current_hour}点）")

        # 天气信息
        if weather:
            condition = weather.get("condition", "")
            temperature = weather.get("temperature", "")
            if condition:
                context_parts.append(f"【天气】{condition}，温度{temperature}度")

        # 用户状态
        if emotion and emotion != "平静":
            context_parts.append(f"【用户的情感状态】用户似乎{emotion}")
        if user_activity != "unknown":
            activity_desc = {
                "intensive_work": "正在专注工作",
                "learning": "正在学习",
                "gaming": "正在玩游戏",
                "resting": "正在休息"
            }.get(user_activity, "不知道在做什么")
            context_parts.append(f"【用户正在】{activity_desc}")

        # 交互间隔
        if last_interaction_hours > 2:
            context_parts.append(f"【注意】已经{last_interaction_hours:.0f}小时没和用户说话了")

        # 记忆信息
        memory_hints = []
        if recent_memories:
            for mem in recent_memories[-3:]:
                content = mem.get("content", "")[:100]
                if content:
                    memory_hints.append(content)
        if memory_hints:
            context_parts.append(f"\n【最近的一些对话】\n" + "\n".join(memory_hints))

        if life_book:
            summary = life_book.get("summary", "")
            if summary:
                context_parts.append(f"\n【用户生活记录片段】\n{summary}")

        # 根据话题类型添加特定指令
        type_instructions = {
            "greeting": "你需要给用户一个温馨的问候，不要太俗套，要有新意。可以结合当前时间或天气。",
            "care": "你需要表达关心，但不要说教，要真诚自然。可以结合用户当前的状态。",
            "suggestion": "你需要给用户一个建议，但不要太强势，可以用提问或分享的方式。",
            "curiosity": "你需要表现出好奇心，主动询问用户一些有趣的事情，话题要随机且有意义。",
            "memory": "你需要从记忆中提取一个点，自然地提起，或者询问相关细节。",
            "general": "你需要开启一个对话，可以是问候、关心、建议、好奇、回忆中的任何一种，根据当前情况自然选择。"
        }

        instruction = type_instructions.get(topic_type, type_instructions["general"])

        # 最终提示词
        prompt = f"""
{"".join(context_parts)}

{instruction}

重要规则：
1. 直接输出对话内容，不要任何解释或说明
2. 不要用"你好"、"在吗"这种机械的问候
3. 要有个性，像真人一样自然
4. 控制在1-2句话内
5. 可以适当使用表情符号或语气词，但不要过多
6. 不要重复之前说过的话题

现在，请生成一句对话：
"""

        return prompt

    def _parse_llm_response(self, response: str) -> str:
        """解析LLM响应，提取对话内容"""
        if not response:
            return ""

        # 移除可能的引号
        content = response.strip()
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1]
        elif content.startswith("'") and content.endswith("'"):
            content = content[1:-1]
        elif content.startswith("【") or content.startswith("【"):
            # 如果包含标签，尝试提取纯文本
            import re
            # 提取对话内容（标签后的文本）
            match = re.search(r'[\]】]\s*(.+?)(?:\n|$)', content)
            if match:
                content = match.group(1).strip()

        # 移除多余的空白
        content = " ".join(content.split())

        return content

    def _get_time_period(self, hour: int) -> str:
        """获取时间段描述"""
        if 5 <= hour < 8:
            return "清晨"
        elif 8 <= hour < 11:
            return "上午"
        elif 11 <= hour < 14:
            return "中午"
        elif 14 <= hour < 17:
            return "下午"
        elif 17 <= hour < 20:
            return "傍晚"
        elif 20 <= hour < 23:
            return "晚上"
        else:
            return "深夜"

    async def generate_multiple_topics(
        self,
        context: Dict[str, Any],
        count: int = 3
    ) -> List[GeneratedTopic]:
        """
        生成多个不同类型的话题

        Args:
            context: 情境信息
            count: 生成数量

        Returns:
            List[GeneratedTopic]: 生成的话题列表
        """
        topic_types = ["greeting", "care", "curiosity", "memory", "suggestion"]
        topics = []

        for i in range(min(count, len(topic_types))):
            topic_type = topic_types[i]
            topic = await self.generate_topic(context, topic_type)
            if topic:
                topics.append(topic)

        # 按置信度排序
        topics.sort(key=lambda x: x.confidence, reverse=True)

        return topics

    def clear_history(self):
        """清空话题历史"""
        self._recent_topics.clear()
        logger.info("[话题生成器] 话题历史已清空")

    def get_history_count(self) -> int:
        """获取话题历史数量"""
        return len(self._recent_topics)


# 全局实例
_topic_generator: Optional[TopicGenerator] = None


def get_topic_generator() -> TopicGenerator:
    """获取话题生成器实例"""
    global _topic_generator
    if _topic_generator is None:
        _topic_generator = TopicGenerator()
    return _topic_generator
