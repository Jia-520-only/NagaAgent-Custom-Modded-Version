#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Undefined工具集成Agent
将Undefined的工具系统注册为MCP服务，供其他Agent调用
"""

import sys
import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 添加Undefined到Python路径
undefined_path = Path(__file__).parent.parent.parent / "Undefined" / "src"
if undefined_path.exists():
    sys.path.insert(0, str(undefined_path))
    logger.info(f"添加Undefined到路径: {undefined_path}")
else:
    logger.warning(f"Undefined路径不存在: {undefined_path}")


@dataclass
class SimpleChatModelConfig:
    """简化的对话模型配置"""
    api_url: str
    api_key: str
    model_name: str
    max_tokens: int


@dataclass
class SimpleVisionModelConfig:
    """简化的视觉模型配置"""
    api_url: str
    api_key: str
    model_name: str


class MultiToolRegistry:
    """支持从多个目录加载工具的工具注册表"""

    def __init__(self, tools_dirs: List[Path]):
        """
        初始化工具注册表

        Args:
            tools_dirs: 工具目录列表
        """
        from Undefined.tools import ToolRegistry

        self.tool_registries: List[ToolRegistry] = []
        self._tools_schema: List[Dict[str, Any]] = []
        self._registry_map: Dict[str, ToolRegistry] = {}

        # 为每个目录创建独立的ToolRegistry
        for tools_dir in tools_dirs:
            if tools_dir.exists():
                logger.info(f"加载工具目录: {tools_dir}")
                registry = ToolRegistry(tools_dir)
                self.tool_registries.append(registry)

                # 合并工具schema
                for schema in registry.get_tools_schema():
                    tool_name = schema.get("function", {}).get("name", "")
                    if tool_name and tool_name not in self._registry_map:
                        self._tools_schema.append(schema)
                        self._registry_map[tool_name] = registry
                    else:
                        logger.warning(f"工具 {tool_name} 已存在，跳过重复加载")
            else:
                logger.warning(f"工具目录不存在: {tools_dir}")

        tool_names = list(self._registry_map.keys())
        logger.info(f"成功加载 {len(self._tools_schema)} 个工具: {', '.join(tool_names)}")

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """获取所有工具定义"""
        return self._tools_schema

    async def execute_tool(self, tool_name: str, args: Dict[str, Any], context: Dict[str, Any]) -> str:
        """执行指定工具"""
        registry = self._registry_map.get(tool_name)
        if not registry:
            return f"工具未找到: {tool_name}"

        try:
            # 使用ToolRegistry的execute方法
            result = await registry.execute(tool_name, args, context)
            return str(result)
        except Exception as e:
            logger.exception(f"执行工具 {tool_name} 时出错")
            return f"执行工具 {tool_name} 时出错: {str(e)}"


class AgentUndefined:
    """Undefined工具集成Agent"""

    def __init__(self):
        """初始化Agent"""
        self.tool_registry = None
        self.ai_client = None
        self.search_wrapper = None
        self.initialized = False

    def initialize(self, config: Dict[str, Any] = None):
        """初始化Agent

        Args:
            config: 配置字典（可选）
        """
        try:
            logger.info("开始初始化Undefined工具系统...")

            # 定义多个工具目录
            base_path = Path(__file__).parent.parent.parent
            tools_dirs = [
                base_path / "Undefined" / "src" / "Undefined" / "skills" / "tools",
                base_path / "Undefined" / "src" / "Undefined" / "skills" / "agents" / "info_agent" / "tools",
                # 可以添加更多agent的工具目录
                # base_path / "Undefined" / "src" / "Undefined" / "skills" / "agents" / "web_agent" / "tools",
            ]

            # 初始化工具注册表（支持多目录）
            self.tool_registry = MultiToolRegistry(tools_dirs)
            logger.info(f"工具注册表初始化完成，共加载 {len(self.tool_registry.get_tools_schema())} 个工具")

            # 初始化搜索包装器（如果可用）
            self.search_wrapper = self._init_search_wrapper()

            # 尝试初始化AI客户端（从Undefined的.env读取）
            self.ai_client = self._init_ai_client()

            self.initialized = True
            logger.info("✅ Undefined工具Agent初始化完成")

        except Exception as e:
            logger.error(f"❌ Undefined工具Agent初始化失败: {e}", exc_info=True)
            raise

    def _init_search_wrapper(self):
        """初始化搜索包装器"""
        try:
            # 导入系统配置
            from system.config import config

            # 检查是否配置了搜索服务
            # 使用 getattr 安全获取配置
            online_search = getattr(config, 'online_search', {})
            if isinstance(online_search, dict):
                searxng_url = online_search.get('searxng_url', '')
            else:
                searxng_url = getattr(online_search, 'searxng_url', '') if hasattr(online_search, 'searxng_url') else ''

            if searxng_url:
                try:
                    from langchain_community.utilities import SearxSearchWrapper
                    self.search_wrapper = SearxSearchWrapper(
                        searx_host=searxng_url, k=10
                    )
                    logger.info(f"搜索包装器初始化完成: {searxng_url}")
                    return self.search_wrapper
                except Exception as e:
                    logger.warning(f"搜索包装器初始化失败（langchain_community未安装或配置错误）: {e}")
            else:
                logger.debug("未配置searxng_url，搜索功能不可用")
        except Exception as e:
            logger.warning(f"初始化搜索包装器失败: {e}", exc_info=True)

        return None

    def _init_ai_client(self):
        """初始化AI客户端（从Undefined的.env读取）"""
        try:
            from dotenv import load_dotenv

            # 加载.env文件
            undefined_env = Path(__file__).parent.parent / "Undefined" / ".env"
            if undefined_env.exists():
                load_dotenv(undefined_env)
                logger.info(f"已加载Undefined配置文件: {undefined_env}")

                # 导入Undefined的AI Client
                from Undefined.ai import AIClient

                # 读取环境变量
                api_url = os.getenv("CHAT_MODEL_API_URL", "")
                api_key = os.getenv("CHAT_MODEL_API_KEY", "")
                model_name = os.getenv("CHAT_MODEL_NAME", "")

                if api_url and api_key and model_name:
                    chat_config = SimpleChatModelConfig(
                        api_url=api_url,
                        api_key=api_key,
                        model_name=model_name,
                        max_tokens=int(os.getenv("CHAT_MODEL_MAX_TOKENS", "8192"))
                    )
                    vision_config = SimpleVisionModelConfig(
                        api_url=os.getenv("VISION_MODEL_API_URL", api_url),
                        api_key=os.getenv("VISION_MODEL_API_KEY", api_key),
                        model_name=os.getenv("VISION_MODEL_NAME", model_name)
                    )

                    ai_client = AIClient(chat_config, vision_config)
                    logger.info(f"✅ AI客户端初始化成功 (模型: {model_name})")
                    return ai_client
                else:
                    logger.warning("Undefined配置不完整，AI客户端未初始化")
                    return None
            else:
                logger.info("未找到Undefined的.env文件，AI客户端将使用系统配置")
                return None
        except ImportError:
            logger.warning("未安装dotenv，无法加载Undefined配置")
            return None
        except Exception as e:
            logger.warning(f"初始化AI客户端失败: {e}")
            return None

    async def call_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """调用Undefined工具

        Args:
            tool_name: 工具名称
            parameters: 工具参数
            context: 执行上下文

        Returns:
            工具执行结果
        """
        if not self.initialized:
            return "Undefined工具系统未初始化"

        if not self.tool_registry:
            return "工具注册表未初始化"

        try:
            # 构建执行上下文
            tool_context = context or {}

            logger.info(f"[agent_undefined] 调用工具 {tool_name}, context keys: {list(tool_context.keys())}")

            # 添加搜索包装器到上下文
            if self.search_wrapper:
                tool_context["search_wrapper"] = self.search_wrapper

            # 添加AI客户端到上下文（如果已初始化）
            if self.ai_client:
                tool_context["ai_client"] = self.ai_client
                logger.info("[agent_undefined] AI客户端已添加到工具上下文")

            # 执行工具
            result = await self.tool_registry.execute_tool(tool_name, parameters, tool_context)
            logger.info(f"工具 {tool_name} 执行完成: {result[:100]}...")

            return result

        except Exception as e:
            logger.error(f"工具 {tool_name} 执行失败: {e}", exc_info=True)
            return f"工具执行失败: {str(e)}"

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取所有可用的工具

        Returns:
            工具定义列表
        """
        if not self.tool_registry:
            return []

        return self.tool_registry.get_tools_schema()

    def get_tool_list(self) -> List[str]:
        """获取工具名称列表

        Returns:
            工具名称列表
        """
        tools = self.get_available_tools()
        return [tool.get("function", {}).get("name", "") for tool in tools]

    async def shutdown(self):
        """关闭Agent"""
        try:
            if self.ai_client:
                await self.ai_client.close()
            logger.info("Undefined工具Agent已关闭")
        except Exception as e:
            logger.error(f"关闭Undefined工具Agent失败: {e}")
