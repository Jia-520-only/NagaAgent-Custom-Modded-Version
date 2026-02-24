"""
工具基类

提供标准化的工具实现模板

作者: NagaAgent Team
版本: 1.0.0
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
import json

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """工具基类"""

    def __init__(self, name: str, config: Dict[str, Any] = None):
        """初始化

        Args:
            name: 工具名称
            config: 配置字典
        """
        self.name = name
        self.config = config or {}
        self.description = ""
        self.parameters = {}

        logger.info(f"[{self.name}] 工具初始化")

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            执行结果字典，必须包含 'success' 字段
        """
        pass

    async def validate(self, params: Dict[str, Any]) -> bool:
        """验证参数

        Args:
            params: 参数字典

        Returns:
            验证结果
        """
        # 检查必需参数
        for param_name, param_config in self.parameters.items():
            if param_config.get('required', False) and param_name not in params:
                logger.error(f"[{self.name}] 缺少必需参数: {param_name}")
                return False

            # 类型检查
            expected_type = param_config.get('type')
            if expected_type and param_name in params:
                value = params[param_name]
                if expected_type == 'string' and not isinstance(value, str):
                    logger.error(f"[{self.name}] 参数类型错误: {param_name} 应为 string")
                    return False
                elif expected_type == 'integer' and not isinstance(value, int):
                    logger.error(f"[{self.name}] 参数类型错误: {param_name} 应为 integer")
                    return False
                elif expected_type == 'boolean' and not isinstance(value, bool):
                    logger.error(f"[{self.name}] 参数类型错误: {param_name} 应为 boolean")
                    return False
                elif expected_type == 'object' and not isinstance(value, dict):
                    logger.error(f"[{self.name}] 参数类型错误: {param_name} 应为 object")
                    return False
                elif expected_type == 'array' and not isinstance(value, list):
                    logger.error(f"[{self.name}] 参数类型错误: {param_name} 应为 array")
                    return False

        return True

    def get_schema(self) -> Dict[str, Any]:
        """获取工具模式

        Returns:
            工具模式字典
        """
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters
        }

    def get_default_params(self) -> Dict[str, Any]:
        """获取默认参数

        Returns:
            默认参数字典
        """
        defaults = {}
        for param_name, param_config in self.parameters.items():
            if 'default' in param_config:
                defaults[param_name] = param_config['default']
        return defaults

    async def safe_execute(self, **kwargs) -> Dict[str, Any]:
        """安全执行工具（带验证和错误处理）

        Args:
            **kwargs: 工具参数

        Returns:
            执行结果
        """
        # 合并默认参数
        params = {**self.get_default_params(), **kwargs}

        # 验证参数
        if not await self.validate(params):
            return {
                'success': False,
                'error': '参数验证失败',
                'tool': self.name
            }

        # 执行工具
        try:
            logger.info(f"[{self.name}] 开始执行: {params}")
            result = await self.execute(**params)
            logger.info(f"[{self.name}] 执行完成: {result.get('success', False)}")
            return result
        except Exception as e:
            logger.error(f"[{self.name}] 执行失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'tool': self.name
            }


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """注册工具

        Args:
            tool: 工具实例
        """
        if tool.name in self._tools:
            logger.warning(f"工具已存在，将覆盖: {tool.name}")

        self._tools[tool.name] = tool
        logger.info(f"工具已注册: {tool.name}")

    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具

        Args:
            name: 工具名称

        Returns:
            工具实例，不存在返回None
        """
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具

        Returns:
            工具模式列表
        """
        return [tool.get_schema() for tool in self._tools.values()]

    def get_tool_names(self) -> List[str]:
        """获取所有工具名称

        Returns:
            工具名称列表
        """
        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """检查工具是否存在

        Args:
            name: 工具名称

        Returns:
            是否存在
        """
        return name in self._tools

    async def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """执行工具

        Args:
            name: 工具名称
            **kwargs: 工具参数

        Returns:
            执行结果
        """
        tool = self.get(name)
        if tool is None:
            return {
                'success': False,
                'error': f'工具未找到: {name}'
            }

        return await tool.safe_execute(**kwargs)


# 全局工具注册表
_global_registry: Optional[ToolRegistry] = None


def get_global_registry() -> ToolRegistry:
    """获取全局工具注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry
