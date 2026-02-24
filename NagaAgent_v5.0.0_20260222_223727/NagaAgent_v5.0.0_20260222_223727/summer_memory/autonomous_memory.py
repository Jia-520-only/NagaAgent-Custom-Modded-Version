#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自主记忆系统 - Autonomous Memory
让弥娅能够主动评估信息价值并选择性记录
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import re

logger = logging.getLogger(__name__)


@dataclass
class MemoryEvaluation:
    """记忆评估结果"""
    text: str
    value_score: float  # 0-1, 价值评分
    categories: List[str]  # 归类
    should_store: bool  # 是否应该存储
    priority: int  # 存储优先级
    reason: str  # 评估理由


class AutonomousMemory:
    """自主记忆评估器"""

    def __init__(self, llm_client=None):
        """
        初始化自主记忆系统

        Args:
            llm_client: LLM客户端(用于高级评估)
        """
        self.llm_client = llm_client
        self.enabled = True

        # 记忆评估规则
        self.value_rules = {
            "emotional": {
                "keywords": ["喜欢", "爱", "讨厌", "恨", "生气", "开心", "难过", "担心", "害怕"],
                "weight": 0.8,
                "description": "情感表达"
            },
            "preference": {
                "keywords": ["喜欢", "不喜欢", "偏好", "讨厌", "爱", "恨", "习惯", "通常"],
                "weight": 0.9,
                "description": "偏好设置"
            },
            "information": {
                "keywords": ["告诉", "说", "提到", "是", "有", "是"],
                "weight": 0.5,
                "description": "信息分享"
            },
            "request": {
                "keywords": ["想要", "希望", "需要", "请", "帮忙", "帮我"],
                "weight": 0.7,
                "description": "请求/需求"
            },
            "commitment": {
                "keywords": ["会", "要", "打算", "计划", "准备"],
                "weight": 0.8,
                "description": "承诺/计划"
            }
        }

        logger.info("[自主记忆] 初始化完成")

    async def evaluate_memory(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> MemoryEvaluation:
        """
        评估文本的记忆价值

        Args:
            text: 待评估文本
            context: 上下文信息

        Returns:
            记忆评估结果
        """
        try:
            # 基础规则评估
            base_score = self._evaluate_by_rules(text)
            categories = self._classify_text(text)

            # 如果有LLM,进行深度评估
            if self.llm_client:
                llm_score, llm_reason = await self._evaluate_with_llm(text, context)
                # 结合规则和LLM评分
                final_score = (base_score * 0.4 + llm_score * 0.6)
                reason = f"规则评分:{base_score:.2f}, LLM评分:{llm_score:.2f} - {llm_reason}"
            else:
                final_score = base_score
                reason = "规则评分: {:.2f} - 基于{}规则".format(
                    base_score, ", ".join(categories)
                )

            # 判断是否应该存储
            should_store = final_score > 0.5

            # 确定优先级
            priority = self._determine_priority(final_score, categories)

            return MemoryEvaluation(
                text=text,
                value_score=final_score,
                categories=categories,
                should_store=should_store,
                priority=priority,
                reason=reason
            )

        except Exception as e:
            logger.error(f"[自主记忆] 评估失败: {e}")
            return MemoryEvaluation(
                text=text,
                value_score=0.0,
                categories=[],
                should_store=False,
                priority=1,
                reason="评估失败"
            )

    def _evaluate_by_rules(self, text: str) -> float:
        """基于规则评估"""
        total_score = 0.0
        total_weight = 0.0

        for category, rule in self.value_rules.items():
            keywords = rule["keywords"]
            weight = rule["weight"]

            # 检查关键词匹配
            match_count = sum(1 for kw in keywords if kw in text)
            if match_count > 0:
                # 基于匹配数量和关键词权重计算分数
                score = min(match_count * 0.3, 1.0) * weight
                total_score += score
                total_weight += weight

        # 归一化
        if total_weight > 0:
            return total_score / total_weight
        return 0.0

    def _classify_text(self, text: str) -> List[str]:
        """文本分类"""
        categories = []

        # 情感类
        emotional_keywords = ["喜欢", "爱", "讨厌", "恨", "生气", "开心", "难过", "担心", "害怕", "激动"]
        if any(kw in text for kw in emotional_keywords):
            categories.append("情感")

        # 偏好类
        preference_keywords = ["喜欢", "不喜欢", "偏好", "讨厌", "爱", "恨", "习惯", "通常"]
        if any(kw in text for kw in preference_keywords):
            categories.append("偏好")

        # 信息类
        if re.search(r"[是|有|在|叫做|叫]", text):
            categories.append("信息")

        # 请求类
        request_keywords = ["想要", "希望", "需要", "请", "帮忙", "帮我", "能否", "可以"]
        if any(kw in text for kw in request_keywords):
            categories.append("请求")

        # 承诺/计划
        commitment_keywords = ["会", "要", "打算", "计划", "准备", "一定"]
        if any(kw in text for kw in commitment_keywords):
            categories.append("计划")

        if not categories:
            categories.append("普通")

        return categories

    async def _evaluate_with_llm(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, str]:
        """使用LLM进行深度评估"""
        try:
            # 构造评估提示
            prompt = f"""请评估以下对话记录的记忆价值,返回JSON格式:

对话内容: {text}

评估维度(0-1分):
1. 个性化信息: 是否包含个人偏好、习惯、特征
2. 重要信息: 是否包含重要事项、承诺、计划
3. 情感价值: 是否包含情感表达、关系信息
4. 知识价值: 是否包含有用信息、知识

请只返回JSON:
{{
    "score": 0.85,
    "reason": "包含用户偏好信息,有价值"
}}"""

            response = await self.llm_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是记忆价值评估专家,只返回JSON格式"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )

            # 解析响应
            result_text = response.choices[0].message.content.strip()
            # 提取JSON
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                import json
                result = json.loads(json_match.group())
                return result.get("score", 0.5), result.get("reason", "")
            else:
                return 0.5, "无法解析LLM响应"

        except Exception as e:
            logger.error(f"[自主记忆] LLM评估失败: {e}")
            return 0.5, "LLM评估失败,回退到规则"

    def _determine_priority(self, score: float, categories: List[str]) -> int:
        """确定存储优先级(1-10)"""
        if score >= 0.8:
            return 10  # 高价值
        elif score >= 0.6:
            return 7   # 中高价值
        elif score >= 0.4:
            return 5   # 中等价值
        else:
            return 3   # 低价值

    async def autonomous_store(
        self,
        user_input: str,
        ai_response: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        自主决策是否存储对话

        Args:
            user_input: 用户输入
            ai_response: AI回复
            context: 上下文

        Returns:
            是否已存储
        """
        try:
            # 评估用户输入
            user_eval = await self.evaluate_memory(user_input, context)

            # 评估AI回复
            ai_eval = await self.evaluate_memory(ai_response, context)

            # 综合评分
            combined_score = (user_eval.value_score + ai_eval.value_score) / 2
            should_store = user_eval.should_store or ai_eval.should_store or combined_score > 0.4

            if should_store:
                logger.info(
                    f"[自主记忆] 决定存储: score={combined_score:.2f}, "
                    f"reason={user_eval.reason[:50]}..."
                )
                return True
            else:
                logger.debug(f"[自主记忆] 跳过存储: score={combined_score:.2f}")
                return False

        except Exception as e:
            logger.error(f"[自主记忆] 自主存储决策失败: {e}")
            # 出错时保守存储
            return True


# 全局实例
_autonomous_memory_instance: Optional[AutonomousMemory] = None


def get_autonomous_memory() -> Optional[AutonomousMemory]:
    """获取自主记忆实例"""
    return _autonomous_memory_instance


def set_autonomous_memory(memory: AutonomousMemory):
    """设置自主记忆实例"""
    global _autonomous_memory_instance
    _autonomous_memory_instance = memory
