#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能语意分析器 - 根据对话上下文智能判断：
1. 是否需要调用MCP工具
2. 输出应该用长文本还是短文本
3. 使用什么回复风格（简洁/详细/情感）
"""

import re
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class SemanticAnalysis:
    """语意分析结果"""
    # 是否需要调用工具
    need_tool_call: bool = False
    # 建议的输出模式: "short" (简洁), "long" (详细), "normal" (正常)
    output_mode: str = "normal"
    # 建议的回复风格: "concise" (简洁), "detailed" (详细), "emotional" (情感), "helpful" (帮助)
    reply_style: str = "helpful"
    # 检测到的意图关键词
    intent_keywords: List[str] = None
    # 置信度 0-1
    confidence: float = 0.0

    def __post_init__(self):
        if self.intent_keywords is None:
            self.intent_keywords = []


class SemanticAnalyzer:
    """智能语意分析器"""

    # 工具调用关键词映射
    TOOL_KEYWORDS = {
        "天气": ["天气", "气温", "温度", "降雨", "晴朗", "阴天", "forecast"],
        "时间": ["几点", "现在", "日期", "星期", "周几", "时间"],
        "搜索": ["搜索", "查询", "找一下", "看看有没有", "是什么", "百度"],
        "启动应用": ["打开", "启动", "运行", "开启", "exec", "launch"],
        "绘图": ["画", "生成图片", "画图", "图像", "绘画", "生成一张"],
        "网页解析": ["解析", "爬取", "提取", "分析网页", "get"],
        "视频": ["视频", "播放", "b站", "bilibili", "youtube"],
        "音乐": ["音乐", "歌曲", "听歌", "播放音乐", "singer"],
        "系统控制": ["清理", "优化", "重启", "关机", "命令", "cmd"],
        "记忆": ["记住", "存储", "备忘", "提醒", "note"],
    }

    # 短文本关键词（需要简洁回复）
    SHORT_RESPONSE_KEYWORDS = [
        "是", "否", "好", "行", "ok", "是的", "对的", "没问题",
        "多谢", "谢谢", "晚安", "早安", "再见", "拜拜",
        "几", "多少", "什么时候", "在哪", "哪里",
        "为什么", "什么", "怎么", "如何"
    ]

    # 长文本关键词（需要详细回复）
    LONG_RESPONSE_KEYWORDS = [
        "解释", "说明", "介绍", "分析", "详细", "详细点",
        "原理", "步骤", "教程", "指南", "方法", "方法",
        "为什么", "怎么办", "怎么解决", "如何处理",
        "故事", "经历", "感受", "想法", "建议"
    ]

    # 情感交流关键词（需要情感化回复）
    EMOTIONAL_KEYWORDS = [
        "喜欢", "爱", "讨厌", "讨厌", "开心", "难过",
        "生气", "担心", "害怕", "紧张", "放松",
        "孤独", "寂寞", "幸福", "痛苦", "累",
        "安慰", "拥抱", "鼓励", "支持", "陪伴"
    ]

    def __init__(self):
        """初始化分析器"""
        pass

    def analyze(self, message: str, conversation_history: List[Dict[str, str]] = None) -> SemanticAnalysis:
        """
        分析消息的语意

        Args:
            message: 用户消息
            conversation_history: 对话历史（可选）

        Returns:
            SemanticAnalysis: 分析结果
        """
        analysis = SemanticAnalysis()

        # 1. 检测是否需要工具调用
        analysis.need_tool_call, analysis.intent_keywords = self._detect_tool_intent(message)
        if analysis.need_tool_call:
            analysis.confidence = 0.8
            return analysis

        # 2. 检测输出模式（短文本/长文本/正常）
        analysis.output_mode = self._detect_output_mode(message)

        # 3. 检测回复风格
        analysis.reply_style = self._detect_reply_style(message, analysis.output_mode)

        # 4. 计算置信度
        analysis.confidence = self._calculate_confidence(message, analysis)

        return analysis

    def _detect_tool_intent(self, message: str) -> tuple:
        """
        检测是否需要调用工具

        Returns:
            (是否需要工具, 匹配的关键词列表)
        """
        message_lower = message.lower()
        matched_keywords = []

        for tool_name, keywords in self.TOOL_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    matched_keywords.append(f"{tool_name}:{keyword}")

        if matched_keywords:
            return True, matched_keywords

        return False, []

    def _detect_output_mode(self, message: str) -> str:
        """
        检测输出模式

        Returns:
            "short", "long", or "normal"
        """
        message_lower = message.lower()

        # 检查是否为简单问题（短文本）
        for keyword in self.SHORT_RESPONSE_KEYWORDS:
            if keyword in message_lower:
                # 排除"为什么"这种需要详细解释的词
                if "为什么" not in message:
                    return "short"

        # 检查是否需要详细解释（长文本）
        for keyword in self.LONG_RESPONSE_KEYWORDS:
            if keyword in message_lower:
                return "long"

        return "normal"

    def _detect_reply_style(self, message: str, output_mode: str) -> str:
        """
        检测回复风格

        Returns:
            "concise", "detailed", "emotional", or "helpful"
        """
        message_lower = message.lower()

        # 检查情感交流
        for keyword in self.EMOTIONAL_KEYWORDS:
            if keyword in message_lower:
                return "emotional"

        # 根据输出模式返回风格
        if output_mode == "short":
            return "concise"
        elif output_mode == "long":
            return "detailed"

        return "helpful"

    def _calculate_confidence(self, message: str, analysis: SemanticAnalysis) -> float:
        """计算置信度"""
        confidence = 0.5  # 默认置信度

        # 如果检测到工具调用意图，置信度较高
        if analysis.need_tool_call:
            confidence = 0.8
        # 如果检测到情感关键词，置信度中等
        elif analysis.reply_style == "emotional":
            confidence = 0.7
        # 如果输出模式明确，置信度中等
        elif analysis.output_mode in ["short", "long"]:
            confidence = 0.6

        return confidence

    def format_analysis_as_text(self, analysis: SemanticAnalysis) -> str:
        """
        将分析结果格式化为文本（用于调试）

        Args:
            analysis: 分析结果

        Returns:
            格式化文本
        """
        lines = [
            f"🔍 语意分析结果:",
            f"   - 工具调用: {'是' if analysis.need_tool_call else '否'}",
            f"   - 输出模式: {analysis.output_mode}",
            f"   - 回复风格: {analysis.reply_style}",
            f"   - 意图关键词: {', '.join(analysis.intent_keywords) if analysis.intent_keywords else '无'}",
            f"   - 置信度: {analysis.confidence:.2f}"
        ]
        return "\n".join(lines)


# 单例模式
_analyzer_instance: Optional[SemanticAnalyzer] = None


def get_semantic_analyzer() -> SemanticAnalyzer:
    """获取语义分析器单例"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = SemanticAnalyzer()
    return _analyzer_instance
