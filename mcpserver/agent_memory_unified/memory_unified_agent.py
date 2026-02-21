"""
统一记忆服务

整合了以下三个服务的功能：
- agent_memory (知识图谱五元组)
- agent_lifebook (日记记忆)
- agent_vcp (向量数据库+RAG)

提供统一的记忆存储和检索接口，支持：
1. 自动选择最优存储方式
2. 多后端融合检索
3. 智能总结生成
4. 知识节点管理

作者: NagaAgent Team
版本: 1.0.0
创建日期: 2026-01-28
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio

# 配置日志
logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """记忆类型"""
    AUTO = "auto"        # 自动选择
    KNOWLEDGE = "knowledge"  # 知识图谱（Neo4j）
    DIARY = "diary"      # 日记（LifeBook）
    VECTOR = "vector"    # 向量数据库（VCP）


class QueryMode(Enum):
    """查询模式"""
    SEMANTIC = "semantic"  # 语义检索
    KEYWORD = "keyword"    # 关键词检索
    GRAPH = "graph"        # 图谱检索
    HYBRID = "hybrid"      # 混合检索


@dataclass
class MemoryItem:
    """记忆项"""
    id: str
    content: str
    type: str
    timestamp: str
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NodeData:
    """知识节点"""
    id: str
    name: str
    type: str
    properties: Dict[str, Any] = None


class MemoryUnifiedAgent:
    """统一记忆服务Agent"""

    def __init__(self, config: Dict[str, Any]):
        """初始化

        Args:
            config: 配置字典
        """
        self.config = config

        # 记忆后端配置
        self.memory_config = config.get('memory', {})
        self.vcp_config = config.get('vcp', {})
        self.lifebook_config = config.get('lifebook', {})

        # 后端启用状态
        self.backends = {
            'neo4j': self.memory_config.get('enabled', False),
            'vcp': self.vcp_config.get('enabled', False),
            'lifebook': self.lifebook_config.get('enabled', True)  # 默认启用
        }

        # 延迟加载组件
        self._neo4j_driver = None
        self._vcp_client = None
        self._lifebook_service = None

        logger.info("[统一记忆] 初始化完成")
        logger.info(f"[统一记忆] 后端状态: {self.backends}")

    # ==================== 记忆存储 ====================

    async def store_memory(
        self,
        content: str,
        memory_type: str = MemoryType.AUTO.value,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """统一记忆存储，自动选择最优存储方式

        Args:
            content: 记忆内容
            memory_type: 记忆类型 (auto/knowledge/diary/vector)
            metadata: 元数据

        Returns:
            存储结果
        """
        metadata = metadata or {}
        memory_type = memory_type or MemoryType.AUTO.value

        logger.info(f"[统一记忆] 存储记忆: type={memory_type}, length={len(content)}")

        try:
            # 自动选择类型
            if memory_type == MemoryType.AUTO.value:
                memory_type = await self._select_best_type(content, metadata)

            # 根据类型存储
            if memory_type == MemoryType.KNOWLEDGE.value:
                return await self._store_knowledge(content, metadata)
            elif memory_type == MemoryType.DIARY.value:
                return await self._store_diary(content, metadata)
            elif memory_type == MemoryType.VECTOR.value:
                return await self._store_vector(content, metadata)
            else:
                # 默认存储为日记
                return await self._store_diary(content, metadata)

        except Exception as e:
            logger.error(f"[统一记忆] 存储失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'type': memory_type
            }

    async def _select_best_type(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> str:
        """智能选择最佳存储类型

        规则：
        - 包含结构化关系 → knowledge
        - 时间相关/生活记录 → diary
        - 需要语义检索 → vector
        """
        # 检查是否包含关系结构
        if any(keyword in content for keyword in ['是', '属于', '包含', '关联', '位于']):
            return MemoryType.KNOWLEDGE.value

        # 检查是否是时间相关的
        if any(keyword in content for keyword in ['今天', '明天', '昨天', '记得', '记录']):
            return MemoryType.DIARY.value

        # 检查是否需要语义检索
        if any(keyword in content for keyword in ['记得', '找', '搜索', '回忆']):
            return MemoryType.VECTOR.value

        # 默认：如果VCP可用使用向量，否则使用日记
        if self.backends['vcp']:
            return MemoryType.VECTOR.value
        return MemoryType.DIARY.value

    async def _store_knowledge(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """存储到知识图谱（Neo4j）"""
        if not self.backends['neo4j']:
            logger.warning("[统一记忆] Neo4j未启用，降级为日记存储")
            return await self._store_diary(content, metadata)

        try:
            # 提取五元组（简化版）
            quintuples = await self._extract_quintuples(content)

            # 存储到Neo4j
            # TODO: 实现Neo4j存储逻辑
            # 这里使用文件存储作为备用
            return await self._store_knowledge_file(content, quintuples, metadata)

        except Exception as e:
            logger.error(f"[统一记忆] 知识存储失败: {e}")
            # 降级为日记存储
            return await self._store_diary(content, metadata)

    async def _extract_quintuples(self, content: str) -> List[Dict[str, str]]:
        """提取五元组（简化版）"""
        # TODO: 实现智能五元组提取
        # 这里返回一个示例
        return [{
            'subject': '弥娅',
            'predicate': '记住',
            'object': content[:50],
            'time': datetime.now().isoformat(),
            'location': 'unknown'
        }]

    async def _store_knowledge_file(
        self,
        content: str,
        quintuples: List[Dict],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """存储到文件（Neo4j备用方案）"""
        try:
            import os
            from pathlib import Path

            # 创建存储目录
            storage_dir = Path("summer_memory/knowledge_graph")
            storage_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = storage_dir / filename

            # 存储数据
            data = {
                'quintuples': quintuples,
                'content': content,
                'metadata': metadata,
                'timestamp': datetime.now().isoformat()
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"[统一记忆] 知识存储到文件: {filepath}")

            return {
                'success': True,
                'type': MemoryType.KNOWLEDGE.value,
                'backend': 'file',
                'path': str(filepath),
                'quintuples_count': len(quintuples)
            }

        except Exception as e:
            logger.error(f"[统一记忆] 文件存储失败: {e}")
            raise

    async def _store_diary(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """存储到日记（LifeBook）"""
        try:
            from pathlib import Path

            # 创建存储目录
            storage_dir = Path("summer_memory/diary")
            storage_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            filename = f"{datetime.now().strftime('%Y%m%d')}.md"
            filepath = storage_dir / filename

            # 追加内容
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(f"\n\n## {datetime.now().strftime('%H:%M:%S')}\n\n")
                f.write(content)
                f.write(f"\n\n---\n")

            logger.info(f"[统一记忆] 日记存储: {filepath}")

            return {
                'success': True,
                'type': MemoryType.DIARY.value,
                'backend': 'file',
                'path': str(filepath)
            }

        except Exception as e:
            logger.error(f"[统一记忆] 日记存储失败: {e}")
            raise

    async def _store_vector(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """存储到向量数据库（VCP）"""
        if not self.backends['vcp']:
            logger.warning("[统一记忆] VCP未启用，降级为日记存储")
            return await self._store_diary(content, metadata)

        try:
            # 调用VCP API
            # TODO: 实现VCP存储逻辑
            # 这里降级为日记存储
            logger.warning("[统一记忆] VCP存储暂未实现，降级为日记存储")
            return await self._store_diary(content, metadata)

        except Exception as e:
            logger.error(f"[统一记忆] 向量存储失败: {e}")
            # 降级为日记存储
            return await self._store_diary(content, metadata)

    # ==================== 记忆检索 ====================

    async def recall_memory(
        self,
        query: str,
        mode: str = QueryMode.HYBRID.value,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """智能回忆，支持多种查询方式

        Args:
            query: 查询内容
            mode: 查询模式 (semantic/keyword/graph/hybrid)
            limit: 返回结果数量

        Returns:
            记忆列表
        """
        logger.info(f"[统一记忆] 检索记忆: query={query[:50]}, mode={mode}, limit={limit}")

        try:
            results = []

            # 根据模式检索
            if mode in [QueryMode.SEMANTIC.value, QueryMode.HYBRID.value]:
                results.extend(await self._recall_vector(query, limit))

            if mode in [QueryMode.KEYWORD.value, QueryMode.HYBRID.value]:
                results.extend(await self._recall_keyword(query, limit))

            if mode in [QueryMode.GRAPH.value, QueryMode.HYBRID.value]:
                results.extend(await self._recall_graph(query, limit))

            # 去重和排序
            results = self._deduplicate_and_rank(results, limit)

            return results

        except Exception as e:
            logger.error(f"[统一记忆] 检索失败: {e}")
            return []

    async def _recall_vector(
        self,
        query: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """向量检索（VCP）"""
        # TODO: 实现VCP向量检索
        return []

    async def _recall_keyword(
        self,
        query: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """关键词检索（LifeBook）"""
        try:
            from pathlib import Path

            storage_dir = Path("summer_memory/diary")
            results = []

            # 遍历日记文件
            if storage_dir.exists():
                for filepath in storage_dir.glob("*.md"):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 关键词匹配
                    if query.lower() in content.lower():
                        results.append({
                            'content': content[:500],  # 返回摘要
                            'source': str(filepath),
                            'type': MemoryType.DIARY.value,
                            'relevance': 0.8
                        })

            return results[:limit]

        except Exception as e:
            logger.error(f"[统一记忆] 关键词检索失败: {e}")
            return []

    async def _recall_graph(
        self,
        query: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """图谱检索（Neo4j）"""
        try:
            from pathlib import Path

            storage_dir = Path("summer_memory/knowledge_graph")
            results = []

            # 遍历知识文件
            if storage_dir.exists():
                for filepath in storage_dir.glob("*.json"):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 关键词匹配
                    for quintuple in data.get('quintuples', []):
                        if query.lower() in str(quintuple).lower():
                            results.append({
                                'content': str(quintuple),
                                'source': str(filepath),
                                'type': MemoryType.KNOWLEDGE.value,
                                'relevance': 0.9
                            })

            return results[:limit]

        except Exception as e:
            logger.error(f"[统一记忆] 图谱检索失败: {e}")
            return []

    def _deduplicate_and_rank(
        self,
        results: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """去重和排序"""
        # 简单去重（基于内容）
        seen = set()
        unique_results = []
        for r in results:
            content_key = r.get('content', '')[:100]
            if content_key not in seen:
                seen.add(content_key)
                unique_results.append(r)

        # 按相关性排序
        unique_results.sort(key=lambda x: x.get('relevance', 0), reverse=True)

        return unique_results[:limit]

    # ==================== 总结生成 ====================

    async def generate_summary(
        self,
        period: str = "week",
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成时间总结（日/周/月/季）

        Args:
            period: 时间周期 (day/week/month/quarter)
            topic: 主题过滤（可选）

        Returns:
            总结结果
        """
        logger.info(f"[统一记忆] 生成总结: period={period}, topic={topic}")

        try:
            # TODO: 实现智能总结生成
            # 这里返回一个示例
            return {
                'success': True,
                'period': period,
                'topic': topic,
                'summary': f"这是{period}的总结...",
                'key_points': [],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"[统一记忆] 总结生成失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== 节点管理 ====================

    async def manage_nodes(
        self,
        action: str,
        node_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """知识节点管理

        Args:
            action: 操作类型 (create/update/delete/list)
            node_data: 节点数据

        Returns:
            操作结果
        """
        logger.info(f"[统一记忆] 节点管理: action={action}")

        try:
            if action == 'create':
                return await self._create_node(node_data)
            elif action == 'update':
                return await self._update_node(node_data)
            elif action == 'delete':
                return await self._delete_node(node_data)
            elif action == 'list':
                return await self._list_nodes()
            else:
                return {
                    'success': False,
                    'error': f'未知操作: {action}'
                }

        except Exception as e:
            logger.error(f"[统一记忆] 节点管理失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _create_node(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建节点"""
        try:
            from pathlib import Path

            storage_dir = Path("summer_memory/nodes")
            storage_dir.mkdir(parents=True, exist_ok=True)

            node_id = node_data.get('id', str(datetime.now().timestamp()))
            filepath = storage_dir / f"{node_id}.json"

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(node_data, f, ensure_ascii=False, indent=2)

            return {
                'success': True,
                'action': 'create',
                'node_id': node_id,
                'path': str(filepath)
            }

        except Exception as e:
            logger.error(f"[统一记忆] 创建节点失败: {e}")
            raise

    async def _update_node(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新节点"""
        # TODO: 实现节点更新
        return {
            'success': False,
            'error': '暂未实现'
        }

    async def _delete_node(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """删除节点"""
        # TODO: 实现节点删除
        return {
            'success': False,
            'error': '暂未实现'
        }

    async def _list_nodes(self) -> Dict[str, Any]:
        """列出所有节点"""
        try:
            from pathlib import Path

            storage_dir = Path("summer_memory/nodes")
            nodes = []

            if storage_dir.exists():
                for filepath in storage_dir.glob("*.json"):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        node = json.load(f)
                        nodes.append(node)

            return {
                'success': True,
                'action': 'list',
                'count': len(nodes),
                'nodes': nodes
            }

        except Exception as e:
            logger.error(f"[统一记忆] 列出节点失败: {e}")
            raise

    # ==================== 工具方法 ====================

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'service': 'MemoryUnifiedAgent',
            'version': '1.0.0',
            'backends': self.backends,
            'status': 'running'
        }


# ==================== MCP工具注册 ====================

def get_tools():
    """获取工具列表（用于MCP注册）"""
    return {
        'store_memory': {
            'description': '统一记忆存储，自动选择最优存储方式',
            'parameters': {
                'content': {'type': 'string', 'description': '记忆内容'},
                'type': {'type': 'string', 'description': '记忆类型 (auto/knowledge/diary/vector)', 'default': 'auto'},
                'metadata': {'type': 'object', 'description': '元数据'}
            }
        },
        'recall_memory': {
            'description': '智能回忆，支持多种查询方式',
            'parameters': {
                'query': {'type': 'string', 'description': '查询内容'},
                'mode': {'type': 'string', 'description': '查询模式 (semantic/keyword/graph/hybrid)', 'default': 'hybrid'},
                'limit': {'type': 'integer', 'description': '返回结果数量', 'default': 10}
            }
        },
        'generate_summary': {
            'description': '生成时间总结（日/周/月/季）',
            'parameters': {
                'period': {'type': 'string', 'description': '时间周期 (day/week/month/quarter)', 'default': 'week'},
                'topic': {'type': 'string', 'description': '主题过滤（可选）'}
            }
        },
        'manage_nodes': {
            'description': '知识节点管理',
            'parameters': {
                'action': {'type': 'string', 'description': '操作类型 (create/update/delete/list)'},
                'node_data': {'type': 'object', 'description': '节点数据'}
            }
        }
    }


if __name__ == '__main__':
    # 测试代码
    import asyncio

    async def test():
        config = {
            'memory': {'enabled': False},
            'vcp': {'enabled': False},
            'lifebook': {'enabled': True}
        }

        agent = MemoryUnifiedAgent(config)

        # 测试存储
        print("\n=== 测试存储 ===")
        result = await agent.store_memory(
            "今天学习了Python编程",
            metadata={'type': 'learning', 'date': '2026-01-28'}
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # 测试检索
        print("\n=== 测试检索 ===")
        results = await agent.recall_memory("Python", mode="keyword", limit=5)
        for r in results:
            print(f"- {r['source']}: {r['content'][:50]}")

        # 测试节点管理
        print("\n=== 测试节点管理 ===")
        result = await agent.manage_nodes('create', {
            'id': 'test_node',
            'name': '测试节点',
            'type': 'person'
        })
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # 测试状态
        print("\n=== 服务状态 ===")
        status = agent.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))

    asyncio.run(test())
