#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VCP MCP Agent - 通过HTTP协议调用VCPToolBox的高级记忆功能
"""

import logging
import httpx
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class VCPAgent:
    """VCP工具箱代理类 - 通过HTTP调用VCP服务"""
    
    def __init__(self, vcp_base_url: str = "http://127.0.0.1:6005", vcp_key: str = ""):
        """
        初始化VCP代理
        
        Args:
            vcp_base_url: VCP服务器地址
            vcp_key: VCP访问密钥
        """
        self.base_url = vcp_base_url.rstrip('/')
        self.vcp_key = vcp_key
        self.client = httpx.AsyncClient(timeout=60.0)
        
        logger.info(f"[VCPAgent] 初始化完成: {self.base_url}")
    
    async def check_connection(self) -> bool:
        """检查VCP服务是否可用"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"[VCPAgent] 连接检查失败: {e}")
            return False
    
    async def rag_query(self, query: str, top_k: int = 5, use_tags: str = "") -> Dict[str, Any]:
        """
        使用VCP TagMemo浪潮算法检索相关记忆
        
        Args:
            query: 查询内容
            top_k: 返回结果数量
            use_tags: 指定标签(可选)
            
        Returns:
            检索结果
        """
        try:
            # 调用VCP的RAG插件
            payload = {
                "query": query,
                "top_k": top_k,
                "use_tags": use_tags if use_tags else None
            }
            
            response = await self.client.post(
                f"{self.base_url}/plugin/RAGDiaryPlugin/query",
                json=payload,
                headers={"X-VCP-Key": self.vcp_key} if self.vcp_key else {}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"[VCPAgent] RAG查询成功: 找到 {len(result.get('results', []))} 条相关记忆")
                return result
            else:
                logger.error(f"[VCPAgent] RAG查询失败: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"[VCPAgent] RAG查询异常: {e}")
            return {"error": str(e)}
    
    async def store_memory(
        self, 
        content: str, 
        tags: Optional[List[str]] = None,
        diary_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        存储记忆到VCP向量数据库
        
        Args:
            content: 记忆内容
            tags: 标签列表
            diary_name: 日记本名称(可选)
            
        Returns:
            存储结果
        """
        try:
            # 调用VCP的日记插件
            payload = {
                "content": content,
                "tags": tags or [],
                "diary_name": diary_name or "默认"
            }
            
            response = await self.client.post(
                f"{self.base_url}/plugin/VCPDailynote/save",
                json=payload,
                headers={"X-VCP-Key": self.vcp_key} if self.vcp_key else {}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"[VCPAgent] 记忆存储成功: {content[:50]}...")
                return result
            else:
                logger.error(f"[VCPAgent] 记忆存储失败: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"[VCPAgent] 记忆存储异常: {e}")
            return {"error": str(e)}
    
    async def meta_thinking(self, theme: str, enable_group: bool = True) -> Dict[str, Any]:
        """
        使用VCP元思考系统进行深度推理
        
        Args:
            theme: 思维主题(如creative_writing)
            enable_group: 是否启用词元组网
            
        Returns:
            思考结果
        """
        try:
            # 构建VCP元思考调用
            vcp_command = f"[[VCP元思考:{theme}::{'Group' if enable_group else 'Auto'}]]"
            
            payload = {
                "messages": [
                    {"role": "user", "content": vcp_command}
                ]
            }
            
            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.vcp_key}" if self.vcp_key else {},
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"[VCPAgent] 元思考调用成功: {theme}")
                return result
            else:
                logger.error(f"[VCPAgent] 元思考失败: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"[VCPAgent] 元思考异常: {e}")
            return {"error": str(e)}
    
    async def get_vector_stats(self) -> Dict[str, Any]:
        """获取向量数据库统计信息"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/vectordb/stats",
                headers={"X-VCP-Key": self.vcp_key} if self.vcp_key else {}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"[VCPAgent] 获取统计信息失败: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


# 全局VCP代理实例
_vcp_agent: Optional[VCPAgent] = None

def get_vcp_agent() -> VCPAgent:
    """获取全局VCP代理实例"""
    global _vcp_agent
    if _vcp_agent is None:
        from system.config import config
        
        # 从配置中读取VCP设置(如果存在)
        vcp_base_url = getattr(config, 'vcp_base_url', 'http://127.0.0.1:6005')
        vcp_key = getattr(config, 'vcp_key', '')
        
        _vcp_agent = VCPAgent(vcp_base_url, vcp_key)
    return _vcp_agent
