#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自我优化系统Agent
为MCP提供自我优化工具
"""

import asyncio
import logging
from typing import Dict, Any

from .tools import SelfOptimizationTools, TOOLS_REGISTRY, call_tool

logger = logging.getLogger(__name__)


class AgentSelfOptimization:
    """自我优化系统Agent"""

    def __init__(self):
        """初始化Agent"""
        self.tools = None
        self.initialized = False

    def initialize(self, config: Dict[str, Any] = None):
        """初始化Agent"""
        try:
            logger.info("[SelfOptimization] 开始初始化...")

            # 初始化工具实例
            self.tools = SelfOptimizationTools()

            self.initialized = True
            logger.info("[SelfOptimization] ✅ 初始化完成")

        except Exception as e:
            logger.error(f"[SelfOptimization] 初始化失败: {e}", exc_info=True)
            self.initialized = False

    async def handle_handoff(self, data: Dict[str, Any]) -> str:
        """
        处理handoff调用

        Args:
            data: 包含tool_name和其他参数的数据

        Returns:
            工具执行结果
        """
        if not self.initialized:
            return "自我优化系统未初始化"

        try:
            tool_name = data.get("tool_name", "")
            # 提取tool_name之外的所有参数
            parameters = {k: v for k, v in data.items() if k != "tool_name"}

            logger.info(f"[SelfOptimization] 调用工具: {tool_name}, 参数: {parameters}")

            # 调用工具
            result = await call_tool(tool_name, parameters)

            return result

        except Exception as e:
            logger.error(f"[SelfOptimization] 工具调用失败: {e}", exc_info=True)
            return f"工具执行失败: {str(e)}"

    def get_tools_schema(self) -> list:
        """获取工具schema"""
        return list(TOOLS_REGISTRY.values())

    async def shutdown(self):
        """关闭Agent"""
        try:
            self.initialized = False
            logger.info("[SelfOptimization] 已关闭")
        except Exception as e:
            logger.error(f"[SelfOptimization] 关闭失败: {e}")
