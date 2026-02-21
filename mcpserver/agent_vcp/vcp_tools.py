#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VCP MCP工具集 - 弥娅的VCP记忆工具
"""

import logging
from typing import Dict, Any
from .vcp_agent import get_vcp_agent

logger = logging.getLogger(__name__)

async def vcp_rag_query(query: str, top_k: int = 5, use_tags: str = "") -> Dict[str, Any]:
    """
    使用VCP TagMemo浪潮算法检索相关记忆
    
    这个工具利用VCP的高级RAG系统,包括:
    - EPA模块:逻辑深度和世界观门控
    - 残差金字塔:多级语义剥离
    - 知识库管理器:智能标签召回
    - 偏振语义舵:语义对冲机制
    
    Args:
        query: 查询内容
        top_k: 返回结果数量(1-20)
        use_tags: 指定标签进行检索(可选,逗号分隔)
    
    Returns:
        {
            "success": bool,
            "results": [
                {
                    "content": str,
                    "similarity": float,
                    "tags": List[str],
                    "diary_name": str,
                    "timestamp": str
                },
                ...
            ],
            "message": str
        }
    """
    try:
        vcp_agent = get_vcp_agent()
        result = await vcp_agent.rag_query(query, top_k, use_tags)
        
        if "error" in result:
            return {
                "success": False,
                "results": [],
                "message": f"VCP查询失败: {result['error']}"
            }
        
        return {
            "success": True,
            "results": result.get("results", []),
            "message": f"成功检索到 {len(result.get('results', []))} 条相关记忆"
        }
        
    except Exception as e:
        logger.error(f"[VCP] RAG查询异常: {e}")
        return {
            "success": False,
            "results": [],
            "message": f"查询异常: {str(e)}"
        }


async def vcp_store_memory(
    content: str, 
    tags: list = None,
    diary_name: str = None
) -> Dict[str, Any]:
    """
    存储记忆到VCP向量数据库
    
    VCP会自动进行:
    - 向量化(embedding)
    - 标签提取和关联
    - 索引构建和更新
    - 实时文件监控
    
    Args:
        content: 记忆内容(支持多行文本)
        tags: 标签列表(可选,系统也会自动提取)
        diary_name: 日记本名称(默认"弥娅记忆")
    
    Returns:
        {
            "success": bool,
            "memory_id": str,
            "message": str
        }
    """
    try:
        if tags is None:
            tags = []
        
        if diary_name is None:
            diary_name = "弥娅记忆"
        
        vcp_agent = get_vcp_agent()
        result = await vcp_agent.store_memory(content, tags, diary_name)
        
        if "error" in result:
            return {
                "success": False,
                "memory_id": "",
                "message": f"存储失败: {result['error']}"
            }
        
        return {
            "success": True,
            "memory_id": result.get("id", ""),
            "message": "记忆已成功存储到VCP向量数据库"
        }
        
    except Exception as e:
        logger.error(f"[VCP] 存储记忆异常: {e}")
        return {
            "success": False,
            "memory_id": "",
            "message": f"存储异常: {str(e)}"
        }


async def vcp_meta_thinking(theme: str, enable_group: bool = True) -> Dict[str, Any]:
    """
    使用VCP元思考系统进行深度推理
    
    VCP元思考系统提供:
    - 超动态递归思维链
    - 词元组捕网系统
    - 元逻辑模块库
    - 多阶段递归融合
    
    支持的思维主题:
    - creative_writing: 创意写作
    - logical_reasoning: 逻辑推理
    - problem_solving: 问题解决
    - debate: 辩证思考
    
    Args:
        theme: 思维主题名称
        enable_group: 是否启用词元组网(默认True)
    
    Returns:
        {
            "success": bool,
            "thinking_process": str,
            "conclusion": str,
            "message": str
        }
    """
    try:
        vcp_agent = get_vcp_agent()
        result = await vcp_agent.meta_thinking(theme, enable_group)
        
        if "error" in result:
            return {
                "success": False,
                "thinking_process": "",
                "conclusion": "",
                "message": f"元思考失败: {result['error']}"
            }
        
        # 提取思考过程和结论
        choices = result.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")
        else:
            content = ""
        
        return {
            "success": True,
            "thinking_process": content,
            "conclusion": content.split("\n")[-1] if content else "",
            "message": f"成功完成{theme}主题的元思考"
        }
        
    except Exception as e:
        logger.error(f"[VCP] 元思考异常: {e}")
        return {
            "success": False,
            "thinking_process": "",
            "conclusion": "",
            "message": f"元思考异常: {str(e)}"
        }


async def vcp_get_stats() -> Dict[str, Any]:
    """
    获取VCP向量数据库统计信息
    
    Returns:
        {
            "success": bool,
            "total_memories": int,
            "total_tags": int,
            "vector_dimension": int,
            "index_size_mb": float,
            "message": str
        }
    """
    try:
        vcp_agent = get_vcp_agent()
        result = await vcp_agent.get_vector_stats()
        
        if "error" in result:
            return {
                "success": False,
                "total_memories": 0,
                "total_tags": 0,
                "vector_dimension": 0,
                "index_size_mb": 0.0,
                "message": f"获取统计失败: {result['error']}"
            }
        
        return {
            "success": True,
            "total_memories": result.get("total_memories", 0),
            "total_tags": result.get("total_tags", 0),
            "vector_dimension": result.get("vector_dimension", 0),
            "index_size_mb": result.get("index_size_mb", 0.0),
            "message": "成功获取VCP统计信息"
        }
        
    except Exception as e:
        logger.error(f"[VCP] 获取统计异常: {e}")
        return {
            "success": False,
            "total_memories": 0,
            "total_tags": 0,
            "vector_dimension": 0,
            "index_size_mb": 0.0,
            "message": f"获取统计异常: {str(e)}"
        }


# 工具注册表
VCP_TOOLS = {
    "vcp_rag_query": vcp_rag_query,
    "vcp_store_memory": vcp_store_memory,
    "vcp_meta_thinking": vcp_meta_thinking,
    "vcp_get_stats": vcp_get_stats,
}

def get_vcp_tools_info() -> Dict[str, Dict]:
    """获取VCP工具信息,用于MCP注册"""
    return {
        "vcp_rag_query": {
            "description": "使用VCP TagMemo浪潮算法检索相关记忆,支持EPA、残差金字塔等高级特性",
            "parameters": {
                "query": {"type": "string", "required": True, "description": "查询内容"},
                "top_k": {"type": "integer", "required": False, "default": 5, "description": "返回结果数量"},
                "use_tags": {"type": "string", "required": False, "description": "指定标签(可选)"}
            }
        },
        "vcp_store_memory": {
            "description": "存储记忆到VCP向量数据库,自动向量化和索引",
            "parameters": {
                "content": {"type": "string", "required": True, "description": "记忆内容"},
                "tags": {"type": "array", "required": False, "items": {"type": "string"}, "description": "标签列表"},
                "diary_name": {"type": "string", "required": False, "description": "日记本名称"}
            }
        },
        "vcp_meta_thinking": {
            "description": "使用VCP元思考系统进行深度推理,支持递归思维链",
            "parameters": {
                "theme": {"type": "string", "required": True, "description": "思维主题(如creative_writing)"},
                "enable_group": {"type": "boolean", "required": False, "default": True, "description": "是否启用词元组网"}
            }
        },
        "vcp_get_stats": {
            "description": "获取VCP向量数据库统计信息",
            "parameters": {}
        }
    }
