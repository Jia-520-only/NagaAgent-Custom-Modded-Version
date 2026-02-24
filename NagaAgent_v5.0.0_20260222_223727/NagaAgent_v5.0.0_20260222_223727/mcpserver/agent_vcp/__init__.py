#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VCP记忆工具 - 弥娅与VCPToolBox的桥接层

通过MCP协议,将VCPToolBox的高级记忆功能集成到弥娅中:
- TagMemo浪潮算法: 高级RAG检索
- 元思考系统: 递归思维链推理
- 向量数据库: 智能记忆存储

使用方法:
1. 启动VCPToolBox服务器(默认端口6005)
2. 配置弥娅的VCP连接参数
3. 弥娅即可使用VCP的记忆和思考能力
"""

from .vcp_agent import VCPAgent, get_vcp_agent
from .vcp_tools import VCP_TOOLS, get_vcp_tools_info, vcp_rag_query, vcp_store_memory, vcp_meta_thinking, vcp_get_stats

__all__ = [
    'VCPAgent',
    'get_vcp_agent',
    'VCP_TOOLS',
    'get_vcp_tools_info',
    'vcp_rag_query',
    'vcp_store_memory',
    'vcp_meta_thinking',
    'vcp_get_stats',
]
