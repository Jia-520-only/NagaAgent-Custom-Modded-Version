"""
统一记忆服务

整合了以下三个服务的功能：
- agent_memory (知识图谱五元组)
- agent_lifebook (日记记忆)
- agent_vcp (向量数据库+RAG)

提供统一的记忆存储和检索接口

作者: NagaAgent Team
版本: 1.0.0
创建日期: 2026-01-28
"""

from .memory_unified_agent import MemoryUnifiedAgent, get_tools

__all__ = ['MemoryUnifiedAgent', 'get_tools']
