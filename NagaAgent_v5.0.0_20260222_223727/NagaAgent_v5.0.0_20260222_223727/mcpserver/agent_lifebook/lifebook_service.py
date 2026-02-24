"""
LifeBook Service - LifeBook MCP服务实现
为弥娅提供长期记忆能力
"""

import os
import logging
from typing import Dict, Any
from .tools import LifeBookTools

logger = logging.getLogger(__name__)

class LifeBookService:
    """LifeBook MCP 服务"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化 LifeBook 服务

        Args:
            config: 配置字典
        """
        if config is None:
            config = {}

        # 从配置获取 LifeBook 路径
        lifebook_path = config.get("lifebook_path", "LifeBook")

        # 确保路径是绝对路径
        if not os.path.isabs(lifebook_path):
            # 相对于项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            lifebook_path = os.path.join(project_root, lifebook_path)

        service_config = {
            "lifebook_path": lifebook_path,
            **config
        }

        self.tools = LifeBookTools(service_config)
        logger.info(f"LifeBook 服务初始化完成，路径: {lifebook_path}")

    async def read_lifebook(self, args: Dict[str, Any]) -> str:
        """
        读取 LifeBook 历史上下文

        Args:
            args: 参数字典
                - months: 回溯月数，默认为 3
                - max_tokens: 最大 token 数限制，默认为 8000

        Returns:
            包含历史上下文的文本
        """
        return await self.tools.read_lifebook_context(args)

    async def write_diary(self, args: Dict[str, Any]) -> str:
        """
        写入日记

        Args:
            args: 参数字典
                - content: 日记内容（必填）
                - date: 日期，格式 YYYY-MM-DD，默认为今天
                - tags: 标签列表，如 ["#重要", "#和弥娅聊天"]

        Returns:
            写入结果
        """
        return await self.tools.write_diary(args)

    async def generate_summary(self, args: Dict[str, Any]) -> str:
        """
        生成总结（周度/月度/季度）

        Args:
            args: 参数字典
                - type: 总结类型，可选 "week", "month", "quarter", "year"
                - period: 时期
                - preview: 预览模式，默认为 true

        Returns:
            生成的总结内容
        """
        return await self.tools.generate_summary(args)

    async def create_node(self, args: Dict[str, Any]) -> str:
        """
        创建节点（人物节点或阶段性节点）

        Args:
            args: 参数字典
                - name: 节点名称
                - type: 节点类型，"character" 或 "stage"
                - description: 节点描述
                - create_date: 创建日期，默认为今天

        Returns:
            创建结果
        """
        return await self.tools.create_node(args)

    async def list_nodes(self, args: Dict[str, Any]) -> str:
        """
        列出所有节点

        Args:
            args: 参数字典
                - node_type: 节点类型过滤，可选 "character", "stage"

        Returns:
            节点列表
        """
        return await self.tools.list_nodes(args)

    async def handle_handoff(self, args: Dict[str, Any]) -> str:
        """
        处理 handoff 请求（兼容 MCP 调度器）

        Args:
            args: 参数字典，格式: {"tool_name": "xxx", "param_name": "...", ...}

        Returns:
            执行结果
        """
        # 获取工具名称
        tool_name = args.get("tool_name", "")
        
        # 获取工具参数：除了 tool_name 之外的所有键值对
        tool_args = {k: v for k, v in args.items() if k != "tool_name"}
        
        logger.info(f"[LifeBook handle_handoff] tool_name={tool_name}, tool_args={tool_args}")

        # 工具名称映射：中文工具名 -> 英文方法名
        # 支持 manifest.json 中定义的中文命令
        tool_name_map = {
            "读取记忆": "read_lifebook",
            "read_lifebook": "read_lifebook",
            "记录日记": "write_diary",
            "write_diary": "write_diary",
            "生成总结": "generate_summary",
            "generate_summary": "generate_summary",
            "创建节点": "create_node",
            "create_node": "create_node",
            "列出节点": "list_nodes",
            "list_nodes": "list_nodes",
        }

        # 方法映射
        method_map = {
            "read_lifebook": self.read_lifebook,
            "write_diary": self.write_diary,
            "generate_summary": self.generate_summary,
            "create_node": self.create_node,
            "list_nodes": self.list_nodes,
        }

        # 转换工具名称为标准方法名
        mapped_name = tool_name_map.get(tool_name, tool_name)

        if mapped_name in method_map:
            return await method_map[mapped_name](tool_args)
        else:
            logger.warning(f"未知的工具: {tool_name} (映射后: {mapped_name})")
            return f"未知的工具: {tool_name}"
