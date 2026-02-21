#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自我优化系统 - Undefined工具集成
为Undefined工具集提供自我优化相关功能
"""

__version__ = "1.0.0"
__all__ = ["AgentSelfOptimization", "SelfOptimizationTools", "TOOLS_REGISTRY", "call_tool"]

from .agent_self_optimization import AgentSelfOptimization
from .tools import SelfOptimizationTools, TOOLS_REGISTRY, call_tool
