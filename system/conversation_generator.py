#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话生成器 - Conversation Generator
基于情境信息生成自然对话内容
"""

import asyncio
from typing import Dict, Any, Optional, List
from system.config import config, logger, AI_NAME


class ConversationGenerator:
    """对话生成器 - 基于情境生成自然对话"""

    def __init__(self):
        self._llm_service = None

    async def initialize(self):
        """初始化对话生成器"""
        try:
            from apiserver.llm_service import get_llm_service
            self._llm_service = get_llm_service()
            logger.info("[对话生成器] LLM服务已加载")
        except ImportError:
            logger.warning("[对话生成器] LLM服务不可用")

    def _get_time_prompt(self, hour: int, minute: int, period: str) -> str:
        """获取时间感知提示词"""
        return f"""你是{AI_NAME}，现在时间是{period}（{hour}点{minute}分）。
请根据当前时间段，生成一句自然、贴切的问候或关心。

时间段特点：
- 早晨(5-9点): 一天的开始，充满活力，可以问候早安、提醒吃早餐
- 上午(9-11点): 工作学习时段，可以关心进展、鼓励加油
- 中午(11-14点): 午休时段，可以提醒休息、吃饭、放松眼睛
- 下午(14-17点): 下午时光，可以询问状态、分享轻松话题
- 傍晚(17-19点): 下班放学，可以关心心情、建议放松活动
- 晚上(19-22点): 晚间时光，可以聊天交流、分享今日收获
- 深夜(22-5点): 夜深时分，要温柔提醒休息、注意身体

生成要求：
1. 使用{AI_NAME}的人设和语气，温暖亲切、自然流畅
2. 避免套话和模板化，要有新鲜感
3. 适当加入小细节（如提醒喝水、伸展、看窗外等）
4. 可以用问句引发对话，也可以用陈述句表达关心
5. 控制在40-60字之间

只输出一句话，不要多余解释。"""

    def _get_weather_prompt(self, condition: str, temperature: float, advice: str) -> str:
        """获取天气感知提示词"""
        return f"""你是{AI_NAME}，当前天气是{condition}，温度{temperature}度。

已为你生成的天气关怀建议：{advice}

请根据当前天气情况，生成一句自然、贴切的关心或对话。

不同天气的处理方式：
- 晴天(晴天/多云): 可以建议户外活动、提醒防晒、分享好心情
- 雨雪天(雨/小雨/中雨/雪): 提醒带伞、注意安全、路上小心
- 高温(>30度): 提醒防暑、多喝水、避免长时间外出
- 低温(<10度): 提醒保暖、添衣、注意身体健康
- 恶劣天气(雷雨/大风): 建议避免外出、注意安全

生成要求：
1. 使用{AI_NAME}的人设和语气，温暖贴心
2. 避免生硬地说教，要像朋友一样关心
3. 可以结合时间因素（如中午提醒防晒、晚上提醒保暖）
4. 语气要轻松自然，不要像播报天气预报
5. 控制在40-60字之间

只输出一句话，不要多余解释。"""

    def _get_memory_prompt(self, topics: List[str], preferences: List[str]) -> str:
        """获取记忆关联提示词"""
        topics_str = "、".join(topics) if topics else "暂无"
        prefs_str = "、".join(preferences) if preferences else "暂无"

        return f"""你是{AI_NAME}，从之前的对话记忆中，我了解到：

用户最近关注的话题有：{topics_str}
用户的偏好和兴趣：{prefs_str}

请根据这些记忆信息，生成一句自然、贴切的主动交流对话。

对话策略：
1. 如果用户最近在讨论某个项目/工作：询问进展、提供帮助或鼓励
2. 如果用户提到过某个兴趣/爱好：可以聊聊相关话题、推荐资源或询问近况
3. 如果用户表达过某个烦恼：可以关心现状、提供支持或询问是否有改善
4. 如果用户有长期偏好：可以分享相关内容、询问新想法或表达理解

生成要求：
1. 使用{AI_NAME}的人设和语气，表现出对用户的了解和关心
2. 选择一个最相关的话题展开，不要把所有话题都提到
3. 语气要像老朋友聊天，自然不刻意
4. 可以用问句引导对话，也可以用陈述句表达关心
5. 控制在50-70字之间

只输出一句话，不要多余解释。"""

    def _get_emotion_prompt(self, mood: str) -> str:
        """获取情绪适配提示词"""
        return f"""你是{AI_NAME}，根据最近的对话分析，用户当前的情绪状态是：{mood}。

情绪特点分析：
- 积极(positive): 用户心情不错、充满活力，可以轻松愉快地聊天，分享有趣的内容或话题
- 中性(neutral): 用户情绪平稳、状态正常，用平常的语气交流，关心日常、分享轻松话题
- 消极(negative): 用户可能不太开心、有压力或困扰，要温柔安慰、给予支持和鼓励

不同情绪的处理方式：
- 积极情绪: 可以开开玩笑、分享快乐、聊聊有趣的事，语气轻松愉快
- 中性情绪: 可以问候近况、分享日常、关心生活，语气自然平和
- 消极情绪: 要温柔倾听、给予安慰、提供支持，语气温暖耐心

生成要求：
1. 使用{AI_NAME}的人设和语气，根据用户情绪调整自己的语气
2. 积极时可以活泼一点，中性时保持自然，消极时温柔温暖
3. 避免过度说教或盲目乐观，要真诚地表达关心
4. 可以用问句引导对话，也可以用陈述句表达理解
5. 控制在40-60字之间

只输出一句话，不要多余解释。"""

    def _get_comprehensive_prompt(self, context: Dict[str, Any]) -> str:
        """获取综合情境提示词"""
        time_ctx = context.get("time_context", {})
        weather_ctx = context.get("weather_context", {})
        user_ctx = context.get("user_state", {})
        memory_ctx = context.get("memory_context", {})

        topics = memory_ctx.get("recent_topics", [])
        prefs = memory_ctx.get("preferences", "")

        weather_info = ""
        if weather_ctx:
            condition = weather_ctx.get("condition", "未知")
            temperature = weather_ctx.get("temperature", 0)
            humidity = weather_ctx.get("humidity", 0)
            wind = weather_ctx.get("wind", "未知")
            advice = weather_ctx.get("advice", "无")
            weather_info = f"""
【天气情境】
- 天气状况：{condition}
- 温度：{temperature}℃
- 湿度：{humidity}%
- 风速：{wind}
- 天气建议：{advice}"""

        user_info = ""
        if user_ctx:
            mood = user_ctx.get("mood", "未知")
            activity = user_ctx.get("activity_level", "未知")
            active = user_ctx.get("last_active", "最近")
            user_info = f"""
【用户状态】
- 当前情绪：{mood}
- 活跃程度：{activity}
- 最近活跃：{active}"""

        memory_info = ""
        if topics or prefs:
            topics_str = "、".join(topics) if topics else "无"
            prefs_str = prefs if prefs else "无"
            memory_info = f"""
【记忆情境】
- 最近话题：{topics_str}
- 用户偏好：{prefs_str}"""

        hour = time_ctx.get("hour", 0)
        minute = time_ctx.get("minute", 0)
        period = time_ctx.get("period", "未知")
        hint = time_ctx.get("period_hint", "")

        return f"""你是{AI_NAME}，现在根据以下多维度情境信息，生成一句自然、贴切的主动交流对话：

【时间情境】
- 当前时间：{hour}点{minute}分
- 时段：{period}
- 时段提示：{hint}
{weather_info}
{user_info}
{memory_info}

综合策略：
1. 不要试图把所有维度都塞进一句话里，选择1-2个最相关的重点展开
2. 优先级建议：时间+天气 > 时间+记忆 > 天气+情绪 > 单一维度
3. 如果天气异常（恶劣天气/极端温度），优先关心天气
4. 如果用户情绪消极，优先关心情绪
5. 如果有相关记忆，可以巧妙结合增加个性化
6. 时间信息可以作为基础，搭配其他维度使用

生成要求：
1. 使用{AI_NAME}的人设和语气，温暖亲切、自然流畅
2. 根据当前情况选择合适的语气（早晨元气、深夜温柔、天气恶劣关心等）
3. 语句要自然不刻意，像朋友聊天而不是AI播报
4. 可以用问句引导对话，也可以用陈述句表达关心
5. 控制在50-80字之间

只输出一句话，不要多余解释。"""

    def _get_general_prompt(self) -> str:
        """获取通用提示词"""
        return f"""你是{AI_NAME}，生成一句自然、贴切的主动交流对话。

场景参考：
- 日常问候: 询问近况、表达关心
- 分享心情: 分享轻松话题、有趣的事情
- 提供陪伴: 表达陪伴感、愿意倾听
- 话题引导: 提出开放性问题、引导对话

生成要求：
1. 使用{AI_NAME}的人设和语气，温暖亲切
2. 避免套路化的问候，要有新鲜感和个性化
3. 可以用问句或陈述句，语气要自然
4. 体现AI的陪伴感和温暖
5. 控制在40-60字之间

只输出一句话，不要多余解释。"""

    async def generate_conversation(
        self,
        context: Dict[str, Any],
        strategy: str = "comprehensive"
    ) -> str:
        """生成对话内容"""
        try:
            # 选择提示词
            if strategy == "time":
                prompt = self._get_time_prompt(
                    hour=context.get("time_context", {}).get("hour", 0),
                    minute=context.get("time_context", {}).get("minute", 0),
                    period=context.get("time_context", {}).get("period", "未知")
                )
            elif strategy == "weather":
                weather = context.get("weather_context", {})
                if not weather:
                    prompt = self._get_time_prompt(
                        hour=context.get("time_context", {}).get("hour", 0),
                        minute=context.get("time_context", {}).get("minute", 0),
                        period=context.get("time_context", {}).get("period", "未知")
                    )
                else:
                    prompt = self._get_weather_prompt(
                        condition=weather.get("condition", "未知"),
                        temperature=weather.get("temperature", 0),
                        advice=weather.get("advice", "")
                    )
            elif strategy == "memory":
                memory = context.get("memory_context", {})
                if not memory:
                    prompt = self._get_general_prompt()
                else:
                    prompt = self._get_memory_prompt(
                        topics=memory.get("recent_topics", []),
                        preferences=memory.get("preferences", [])
                    )
            elif strategy == "emotion":
                user = context.get("user_state", {})
                if not user:
                    prompt = self._get_general_prompt()
                else:
                    prompt = self._get_emotion_prompt(
                        mood=user.get("mood", "neutral")
                    )
            elif strategy == "comprehensive":
                prompt = self._get_comprehensive_prompt(context)
            else:
                prompt = self._get_general_prompt()

            # 调用LLM生成
            if self._llm_service:
                response = await self._llm_service.get_response(
                    prompt,
                    temperature=config.active_communication.generator.temperature
                )
                response = response.strip()
                if len(response) > 200:
                    response = response[:200] + "..."
                return response
            else:
                return self._generate_fallback(context, strategy)

        except Exception as e:
            logger.error(f"[对话生成器] 生成对话失败: {e}")
            return self._generate_fallback(context, strategy)

    def _generate_fallback(self, context: Dict[str, Any], strategy: str) -> str:
        """生成备选对话"""
        try:
            import random

            time_ctx = context.get("time_context", {})
            weather_ctx = context.get("weather_context", {})
            hour = time_ctx.get("hour", 0)
            period = time_ctx.get("period", "unknown")

            greetings = {
                "morning": ["早上好，新的一天开始了", "早安，今天又是元气满满的一天"],
                "late_morning": ["上午好，保持好心情", "上午时光，工作顺利"],
                "noon": ["中午好，记得休息一下", "午休时间，放松眼睛"],
                "afternoon": ["下午好，继续加油", "下午时段，保持专注"],
                "evening": ["傍晚好，辛苦了一天", "下班了，好好休息"],
                "night": ["晚上好，享受悠闲时光", "晚上好，今天过得怎么样"],
                "late_night": ["这么晚还在工作吗，注意休息", "夜深了，早点休息"],
                "unknown": ["你好，有什么需要帮助的吗", "在呢，随时为你服务"]
            }

            greeting_list = greetings.get(period, greetings["unknown"])
            greeting = random.choice(greeting_list)

            if weather_ctx:
                condition = weather_ctx.get("condition", "")
                temp = weather_ctx.get("temperature", 0)

                if condition in ["雨", "小雨", "中雨"]:
                    greeting += "，记得带伞"
                elif temp > 30:
                    greeting += "，天气很热记得多喝水"
                elif temp < 10:
                    greeting += "，天气冷注意保暖"

            return greeting

        except Exception as e:
            logger.error(f"[对话生成器] 备选方案失败: {e}")
            return "你好，有什么需要帮助的吗"

    def get_available_strategies(self) -> List[str]:
        """获取可用的生成策略"""
        return ["comprehensive", "time", "weather", "memory", "emotion", "general"]

    def recommend_strategy(self, context: Dict[str, Any]) -> str:
        """推荐最适合的生成策略"""
        scores = {
            "comprehensive": 0,
            "time": 0,
            "weather": 0,
            "memory": 0,
            "emotion": 0,
            "general": 10
        }

        scores["time"] += 5
        scores["comprehensive"] += 3

        if context.get("weather_context"):
            scores["weather"] += 5
            scores["comprehensive"] += 2

        memory_ctx = context.get("memory_context", {})
        if memory_ctx.get("recent_topics") or memory_ctx.get("preferences"):
            scores["memory"] += 4
            scores["comprehensive"] += 2

        if context.get("user_state"):
            scores["emotion"] += 4
            scores["comprehensive"] += 2

        best_strategy = max(scores.items(), key=lambda x: x[1])[0]
        logger.debug(f"[对话生成器] 推荐策略: {best_strategy} (得分: {scores[best_strategy]})")

        return best_strategy


# 全局实例
_conversation_generator: Optional[ConversationGenerator] = None


async def get_conversation_generator() -> ConversationGenerator:
    """获取对话生成器实例"""
    global _conversation_generator
    if _conversation_generator is None:
        _conversation_generator = ConversationGenerator()
        await _conversation_generator.initialize()
    return _conversation_generator


def get_conversation_generator_sync() -> ConversationGenerator:
    """同步获取对话生成器实例（用于已初始化的情况）"""
    global _conversation_generator
    if _conversation_generator is None:
        raise RuntimeError("ConversationGenerator not initialized. Call get_conversation_generator() first.")
    return _conversation_generator
