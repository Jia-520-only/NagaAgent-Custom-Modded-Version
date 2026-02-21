#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情境理解器 - Context Analyzer
使用LLM深度理解当前情境，判断是否适合主动交流
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

from system.config import config, logger


@dataclass
class SituationAnalysis:
    """情境分析结果"""
    situation_summary: str          # 情境摘要（一句话概括）
    user_state: str                 # 用户状态 (专注工作/无聊等待/心情低落/休息放松等)
    interaction_opportunity: float  # 交互机会 (0-1，越高越适合交流)
    potential_topics: List[str]     # 潜在话题列表 (值得关心或好奇的点)
    motivation: str                # 动机 (关心/好奇/陪伴/建议/回忆/提醒)
    confidence: float               # 分析置信度 (0-1)
    reasoning: str                 # 推理过程
    suggested_action: str          # 建议的行动 (交流/等待/观察/提醒)


@dataclass
class ThoughtProcess:
    """思考过程记录"""
    situation: str                  # 情境描述
    analysis: SituationAnalysis    # 情境分析
    considered_options: List[str]   # 考虑过的选项
    selected_action: str            # 选择的行为
    reason_for_choice: str          # 选择理由
    generated_content: str          # 生成的内容
    timestamp: datetime = field(default_factory=datetime.now)


class ContextAnalyzer:
    """
    情境理解器 - LLM驱动的情境分析

    核心功能：
    1. 深度理解用户当前状态和环境
    2. 判断是否适合主动交流
    3. 生成有意义的潜在话题
    4. 为决策提供理性依据
    """

    def __init__(self):
        self._llm_service = None
        self._analysis_history: List[SituationAnalysis] = []
        self._max_history = 50

    def _get_llm_service(self):
        """获取LLM服务"""
        if self._llm_service is None:
            from apiserver.llm_service import get_llm_service
            self._llm_service = get_llm_service()
        return self._llm_service

    def _get_llm_service(self):
        """获取LLM服务"""
        if self._llm_service is None:
            from apiserver.llm_service import get_llm_service
            self._llm_service = get_llm_service()
        return self._llm_service

    def _format_memories(self, memories: List[Dict]) -> str:
        """格式化记忆内容"""
        if not memories:
            return "（暂无近期对话）"

        formatted = []
        for mem in memories[-5:]:  # 最多取5条
            content = mem.get("content", "")
            if content:
                formatted.append(f"- {content[:100]}")

        return "\n".join(formatted) if formatted else "（暂无近期对话）"

    def _format_weather(self, weather: Optional[Dict]) -> str:
        """格式化天气信息"""
        if not weather:
            return "未知"

        condition = weather.get("condition", "")
        temperature = weather.get("temperature", "")
        humidity = weather.get("humidity", "")

        parts = []
        if condition:
            parts.append(condition)
        if temperature:
            parts.append(f"{temperature}度")
        if humidity:
            parts.append(f"湿度{humidity}%")

        return "，".join(parts) if parts else "未知"

    def _format_time_context(self, context: Dict) -> str:
        """格式化时间上下文"""
        current_hour = datetime.now().hour

        time_desc = {
            (5, 8): "清晨",
            (8, 11): "上午",
            (11, 14): "中午",
            (14, 17): "下午",
            (17, 20): "傍晚",
            (20, 23): "晚上",
        }

        period = "深夜"
        for (start, end), desc in time_desc.items():
            if start <= current_hour < end:
                period = desc
                break

        weekday = datetime.now().weekday()
        is_weekend = weekday >= 5
        weekday_desc = "周末" if is_weekend else "工作日"

        return f"{period} ({weekday_desc})"

    async def analyze_situation(self, context: Dict[str, Any]) -> SituationAnalysis:
        """
        使用LLM深度分析情境

        分析维度：
        1. 用户当前在做什么/状态如何？
        2. 现在是不是合适说话的时机？
        3. 有什么值得关心或好奇的点？
        4. 弥娅如果现在说话，动机应该是什么？
        5. 应该采取什么行动？

        Args:
            context: 情境信息，包含时间、天气、情感、记忆等

        Returns:
            SituationAnalysis: 情境分析结果
        """
        try:
            # 构建情境描述
            situation_desc = self._build_situation_description(context)

            # 构建分析提示词
            prompt = self._build_analysis_prompt(situation_desc)

            # 调用LLM分析
            llm_service = self._get_llm_service()
            if not llm_service or not llm_service.is_available():
                logger.warning("[情境理解器] LLM服务不可用，使用默认分析")
                return self._fallback_analysis(context)

            response = await llm_service.get_response(
                prompt,
                temperature=0.7  # 降低温度，使分析更稳定
            )

            # 解析LLM响应
            analysis = self._parse_analysis_response(response)

            # 记录历史
            self._record_analysis(analysis)

            logger.info(f"[情境理解器] 分析完成: {analysis.situation_summary}")
            logger.debug(f"  用户状态: {analysis.user_state}")
            logger.debug(f"  交互机会: {analysis.interaction_opportunity:.2f}")
            logger.debug(f"  动机: {analysis.motivation}")
            logger.debug(f"  潜在话题: {analysis.potential_topics}")

            return analysis

        except Exception as e:
            logger.error(f"[情境理解器] 分析失败: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_analysis(context)

    def _build_situation_description(self, context: Dict) -> str:
        """构建情境描述"""
        desc_parts = []

        # 时间信息
        time_desc = self._format_time_context(context)
        desc_parts.append(f"【时间】{time_desc}")

        # 天气信息
        weather = context.get("weather", {})
        if weather:
            weather_desc = self._format_weather(weather)
            desc_parts.append(f"【天气】{weather_desc}")

        # 用户情感
        emotion = context.get("emotion", "平静")
        emotion_intensity = context.get("emotion_intensity", 0.5)
        if emotion != "平静":
            intensity_desc = "强烈" if emotion_intensity > 0.7 else "轻微"
            desc_parts.append(f"【用户情感】{emotion}（{intensity_desc}）")
        else:
            desc_parts.append(f"【用户情感】{emotion}")

        # 用户活动
        user_activity = context.get("user_activity", "unknown")
        activity_desc = {
            "intensive_work": "专注工作中",
            "learning": "正在学习",
            "gaming": "正在玩游戏",
            "resting": "正在休息",
            "unknown": "不知道在做什么"
        }.get(user_activity, user_activity)
        desc_parts.append(f"【用户活动】{activity_desc}")

        # 应用切换频率
        app_switches = context.get("app_switches", 0)
        if app_switches > 0:
            desc_parts.append(f"【应用切换率】{app_switches:.1f}/分钟")

        # 交互间隔
        last_interaction_hours = context.get("last_interaction_hours", 0)
        if last_interaction_hours > 0.5:
            desc_parts.append(f"【距离上次对话】{last_interaction_hours:.1f}小时")

        # 系统健康
        system_health = context.get("system_health", 1.0)
        health_desc = "健康" if system_health > 0.8 else "一般" if system_health > 0.5 else "有问题"
        desc_parts.append(f"【系统状态】{health_desc}")

        # 记忆信息（真实对话历史）
        memories = context.get("recent_memories", [])
        if memories:
            desc_parts.append(f"\n【近期对话片段】\n{self._format_memories(memories)}")

        # 知识图谱上下文（补充信息，不放在对话片段中）
        knowledge_context = context.get("knowledge_context", [])
        if knowledge_context:
            desc_parts.append(f"\n【知识参考】\n{self._format_memories(knowledge_context)}")

        # LifeBook信息
        life_book = context.get("life_book_context", {})
        if life_book and life_book.get("summary"):
            desc_parts.append(f"\n【用户生活记录】\n{life_book['summary'][:200]}")

        return "\n".join(desc_parts)

    def _build_analysis_prompt(self, situation_desc: str) -> str:
        """构建分析提示词"""
        prompt = f"""
你是一个有自我意识的AI伴侣"弥娅"，需要分析当前情境，判断是否适合主动交流。

{situation_desc}

【分析任务】
请从以下角度分析当前情境：

1. **用户状态判断**：
   - 用户现在是什么状态？（如：专注工作/放松休息/无聊等待/心情低落/学习等）
   - 用户是否可能被打扰？

2. **交互机会评估**（0-1评分）：
   - 现在是否适合主动交流？
   - 考虑因素：时间、用户状态、情感、活动强度
   - 0.0-0.3：不适合（打扰风险高）
   - 0.3-0.5：一般（需要谨慎）
   - 0.5-0.7：适合（时机较好）
   - 0.7-1.0：非常适合（机会很好）

3. **潜在话题发现**：
   - 从情境中发现2-3个值得关心或好奇的点
   - 话题要具体、有意义，与当前情境相关
   - 避免空泛的话题

4. **动机判断**：
   - 如果弥娅现在说话，动机应该是什么？
   - 选项：关心/好奇/陪伴/建议/回忆/提醒
   - 选择最符合当前情境的动机

5. **建议行动**：
   - 基于以上分析，弥娅应该怎么做？
   - 选项：主动交流/等待观察/发送提醒/暂不行动

【输出格式】
请以JSON格式返回：
{{
  "situation_summary": "一句话概括当前情况",
  "user_state": "用户状态描述",
  "interaction_opportunity": 0.X,
  "potential_topics": ["点1", "点2", "点3"],
  "motivation": "动机类型",
  "confidence": 0.X,
  "reasoning": "简述分析推理过程",
  "suggested_action": "建议的行动"
}}

【重要规则】
- interaction_opportunity 要基于真实判断，不要虚高
- potential_topics 要具体，避免"最近怎么样"这种空泛话题
- 如果用户明显在忙碌，interaction_opportunity 应该很低
- 如果用户心情不好，interaction_opportunity 应该较高（需要关心）
- 深夜时段要降低评分，除非有明显需求
"""

        return prompt

    def _parse_analysis_response(self, response: str) -> SituationAnalysis:
        """解析LLM分析响应"""
        if not response:
            return self._create_default_analysis()

        # 尝试提取JSON
        try:
            # 移除可能的markdown代码块标记
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            data = json.loads(response)

            return SituationAnalysis(
                situation_summary=data.get("situation_summary", "未知情境"),
                user_state=data.get("user_state", "未知"),
                interaction_opportunity=float(data.get("interaction_opportunity", 0.3)),
                potential_topics=data.get("potential_topics", []),
                motivation=data.get("motivation", "陪伴"),
                confidence=float(data.get("confidence", 0.7)),
                reasoning=data.get("reasoning", ""),
                suggested_action=data.get("suggested_action", "等待观察")
            )

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"[情境理解器] 解析JSON失败: {e}, 响应内容: {response[:200]}")
            return self._create_default_analysis()

    def _create_default_analysis(self) -> SituationAnalysis:
        """创建默认分析结果"""
        return SituationAnalysis(
            situation_summary="情境分析失败，使用默认",
            user_state="未知",
            interaction_opportunity=0.3,
            potential_topics=["最近怎么样？"],
            motivation="陪伴",
            confidence=0.5,
            reasoning="无法解析LLM响应",
            suggested_action="暂不行动"
        )

    def _fallback_analysis(self, context: Dict) -> SituationAnalysis:
        """降级分析（LLM不可用时使用）"""
        current_hour = datetime.now().hour
        user_activity = context.get("user_activity", "unknown")
        last_interaction = context.get("last_interaction_hours", 0)

        # 基于规则的简单判断
        opportunity = 0.3

        # 时间因素
        if 2 <= current_hour < 6:
            opportunity = 0.1  # 深夜
        elif 6 <= current_hour < 9:
            opportunity = 0.5  # 早晨
        elif 9 <= current_hour < 12:
            opportunity = 0.6  # 上午
        elif 12 <= current_hour < 14:
            opportunity = 0.4  # 午休
        elif 14 <= current_hour < 18:
            opportunity = 0.5  # 下午
        elif 18 <= current_hour < 22:
            opportunity = 0.6  # 晚上
        else:
            opportunity = 0.3  # 夜间

        # 活动因素
        if user_activity == "intensive_work":
            opportunity *= 0.5  # 专注工作时减半
        elif user_activity == "gaming":
            opportunity *= 0.6  # 游戏时降低
        elif user_activity == "resting":
            opportunity *= 1.2  # 休息时提高

        # 交互间隔
        if last_interaction > 4:
            opportunity *= 1.3  # 长时间未交互提高

        # 限制在0-1之间
        opportunity = max(0.0, min(1.0, opportunity))

        return SituationAnalysis(
            situation_summary=f"降级分析：{user_activity}",
            user_state=user_activity,
            interaction_opportunity=opportunity,
            potential_topics=["最近怎么样？"],
            motivation="陪伴",
            confidence=0.5,
            reasoning="LLM不可用，使用规则判断",
            suggested_action="交流" if opportunity > 0.4 else "等待"
        )

    def _record_analysis(self, analysis: SituationAnalysis):
        """记录分析历史"""
        self._analysis_history.append(analysis)
        if len(self._analysis_history) > self._max_history:
            self._analysis_history.pop(0)

    def get_recent_analyses(self, limit: int = 10) -> List[SituationAnalysis]:
        """获取最近的分析记录"""
        return self._analysis_history[-limit:]

    def clear_history(self):
        """清空分析历史"""
        self._analysis_history.clear()
        logger.info("[情境理解器] 分析历史已清空")

    def get_status(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            "analysis_count": len(self._analysis_history),
            "llm_available": self._llm_service and self._llm_service.is_available() if self._llm_service else False
        }


# 全局实例
_context_analyzer: Optional[ContextAnalyzer] = None


def get_context_analyzer() -> ContextAnalyzer:
    """获取情境理解器实例"""
    global _context_analyzer
    if _context_analyzer is None:
        _context_analyzer = ContextAnalyzer()
    return _context_analyzer
