#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具优先级管理器 - 智能工具选择与降级系统
实现同类工具的优先级调用和失败降级机制
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from system.config import config, logger


class FallbackStrategy(Enum):
    """降级策略枚举"""
    AUTO = "auto"  # 自动降级：根据优先级自动选择下一个可用工具
    SEQUENTIAL = "sequential"  # 顺序降级：按工具列表顺序依次尝试
    NONE = "none"  # 不降级：只尝试首选工具


@dataclass
class ToolInfo:
    """工具信息"""
    name: str  # 工具名称
    display_name: str  # 显示名称
    description: str  # 描述
    capability: str  # 能力类别
    priority: int  # 优先级（数值越高越优先）
    enabled: bool  # 是否启用
    service_name: str  # 服务名称


@dataclass
class ToolCallResult:
    """工具调用结果"""
    success: bool
    tool_name: str
    result: Any
    error: Optional[str] = None
    fallback_used: bool = False
    attempt_count: int = 1


class ToolPriorityManager:
    """工具优先级管理器"""

    # 能力类别到服务名称的映射
    CAPABILITY_MAPPING = {
        "screen_control": ["包豆AI视觉自动化", "统一网页服务"],  # 屏幕控制优先包豆
        "browser_automation": ["统一网页服务", "Playwright浏览器控制"],
        "web_search": ["统一网页服务", "在线搜索服务"],
        "app_launcher": ["应用启动服务"],
        "system_control": ["System Control"],
        "file_operations": ["System Control"],
        "data_retrieval": ["VCPToolBox记忆系统", "GRAG知识图谱"],
        "messaging": ["QQ微信消息监听"],
    }

    # 工具到能力类别的映射
    TOOL_CAPABILITY_MAP = {
        # 包豆AI工具
        "baodou_capture_screen": "screen_control",
        "baodou_analyze_task": "screen_control",
        "baodou_mouse_move": "screen_control",
        "baodou_mouse_click": "screen_control",
        "baodou_keyboard_type": "screen_control",
        "baodou_keyboard_press": "screen_control",

        # 网页服务工具
        "web_search": "web_search",
        "web_crawl": "web_search",
        "web_browse": "browser_automation",
        "web_open": "browser_automation",

        # B站搜索工具
        "bilibili_search": "web_search",
        "bilibili_user_info": "web_search",
        "video_random_recommend": "web_search",

        # 应用启动（需要更长超时时间）
        "获取应用列表": "app_launcher",
        "启动应用": "app_launcher",

        # 消息工具
        "发送QQ消息": "messaging",
        "发送微信消息": "messaging",
    }

    # 工具特定的超时时间（毫秒），会覆盖默认的tool_timeout
    TOOL_SPECIFIC_TIMEOUT = {
        "启动应用": 60000,  # 应用启动需要更长时间（60秒）
        "获取应用列表": 60000,  # 获取应用列表也需要较长时间
    }

    # 参数名映射（用于修复参数名不匹配的问题）
    PARAM_NAME_MAP = {
        "bilibili_search": {"keyword": "msg"},  # 将 keyword 映射到 msg
        "music_global_search": {"keyword": "msg"},  # 将 keyword 映射到 msg
        "music_info_get": {"keyword": "msg"},  # 将 keyword 映射到 msg
        "music_lyrics": {"keyword": "msg"},  # 将 keyword 映射到 msg
        "qq_like": {"user_id": "target_user_id"},  # 将 user_id 映射到 target_user_id
    }

    def __init__(self):
        self.fallback_strategy = FallbackStrategy(config.tool_priority.fallback_strategy)
        self.tool_timeout = config.tool_priority.tool_timeout
        self.max_retries = config.tool_priority.max_retries
        self.log_fallback = config.tool_priority.log_fallback
        self.capability_priority = config.tool_priority.capability_priority
        self.preferred_tools = config.tool_priority.preferred_tools
        self.blocked_tools = config.tool_priority.blocked_tools

        # 工具信息缓存
        self._tools_info_cache: Dict[str, ToolInfo] = {}

        # 降级历史记录
        self._fallback_history: List[Dict[str, Any]] = []

        logger.info("[ToolPriority] 工具优先级管理器初始化完成")

    def get_capability(self, tool_name: str) -> str:
        """获取工具的能力类别"""
        # 优先从预定义映射中查找
        if tool_name in self.TOOL_CAPABILITY_MAP:
            return self.TOOL_CAPABILITY_MAP[tool_name]

        # 尝试从服务信息中推断
        try:
            from nagaagent_core.stable.mcp import get_service_info
            service_name = self._find_service_by_tool(tool_name)
            if service_name:
                service_info = get_service_info(service_name)
                if service_info:
                    description = service_info.get('description', '').lower()
                    if '屏幕' in description or '视觉' in description:
                        return 'screen_control'
                    elif '浏览器' in description or '网页' in description:
                        return 'browser_automation'
                    elif '搜索' in description:
                        return 'web_search'
                    elif '应用' in description or '启动' in description:
                        return 'app_launcher'
        except Exception as e:
            logger.debug(f"[ToolPriority] 推断工具能力类别失败: {e}")

        return "other"

    def _find_service_by_tool(self, tool_name: str) -> Optional[str]:
        """通过工具名称查找服务名称"""
        try:
            from nagaagent_core.stable.mcp import get_registered_services, get_service_info

            for service_name in get_registered_services():
                service_info = get_service_info(service_name)
                if service_info:
                    # 首先检查 invocationCommands 中的 command 字段
                    # invocationCommands 在 manifest 的根级别,不在 capabilities 下面
                    manifest = service_info.get('manifest', {})
                    invocation_commands = manifest.get('invocationCommands', [])
                    for cmd in invocation_commands:
                        if cmd.get('command') == tool_name:
                            return service_name

                    # 然后检查 displayName,支持通过 displayName 查找工具
                    display_name = service_info.get('displayName', '')
                    if display_name == tool_name:
                        return service_name

                    # 最后检查 name 字段本身
                    if manifest.get('name') == tool_name:
                        return service_name
        except Exception as e:
            logger.debug(f"[ToolPriority] 查找服务失败: {e}")

        return None

    def get_tool_priority(self, tool_name: str) -> int:
        """获取工具的优先级"""
        capability = self.get_capability(tool_name)
        base_priority = self.capability_priority.get(capability, 10)

        # 检查是否在白名单中（白名单工具优先级+20）
        for preferred_tool in self.preferred_tools:
            if preferred_tool in tool_name or tool_name in preferred_tool:
                base_priority += 20
                break

        # 检查是否在黑名单中（黑名单工具优先级设为0）
        for blocked_tool in self.blocked_tools:
            if blocked_tool in tool_name or tool_name in blocked_tool:
                return 0

        return base_priority

    def get_tool_info(self, tool_name: str) -> ToolInfo:
        """获取工具详细信息"""
        if tool_name in self._tools_info_cache:
            return self._tools_info_cache[tool_name]

        try:
            from nagaagent_core.stable.mcp import get_service_info

            service_name = self._find_service_by_tool(tool_name)
            if service_name:
                service_info = get_service_info(service_name)
                if service_info:
                    tool_info = ToolInfo(
                        name=tool_name,
                        display_name=service_info.get('displayName', tool_name),
                        description=service_info.get('description', ''),
                        capability=self.get_capability(tool_name),
                        priority=self.get_tool_priority(tool_name),
                        enabled=True,
                        service_name=service_name
                    )
                    self._tools_info_cache[tool_name] = tool_info
                    return tool_info
        except Exception as e:
            logger.debug(f"[ToolPriority] 获取工具信息失败: {e}")

        # 返回默认工具信息
        tool_info = ToolInfo(
            name=tool_name,
            display_name=tool_name,
            description='',
            capability=self.get_capability(tool_name),
            priority=self.get_tool_priority(tool_name),
            enabled=True,
            service_name='unknown'
        )
        self._tools_info_cache[tool_name] = tool_info
        return tool_info

    def get_fallback_tools(self, primary_tool: str) -> List[str]:
        """获取指定工具的降级工具列表"""
        capability = self.get_capability(primary_tool)

        # 获取该能力类别下的所有服务
        service_names = self.CAPABILITY_MAPPING.get(capability, [])

        # 收集所有工具
        all_tools = []
        for service_name in service_names:
            try:
                from nagaagent_core.stable.mcp import get_service_info
                service_info = get_service_info(service_name)
                if service_info:
                    # invocationCommands 在 manifest 的根级别,不在 capabilities 下面
                    manifest = service_info.get('manifest', {})
                    invocation_commands = manifest.get('invocationCommands', [])
                    for cmd in invocation_commands:
                        tool_name = cmd.get('command')
                        if tool_name and tool_name != primary_tool:
                            # 排除黑名单工具
                            if not any(bt in tool_name for bt in self.blocked_tools):
                                all_tools.append(tool_name)
            except Exception as e:
                logger.debug(f"[ToolPriority] 获取服务工具失败: {e}")

        # 按优先级排序
        all_tools.sort(key=lambda t: self.get_tool_priority(t), reverse=True)

        return all_tools

    async def call_tool_with_fallback(
        self,
        tool_call: Dict[str, Any],
        mcp_manager,
        primary_tool: str
    ) -> ToolCallResult:
        """带降级的工具调用"""
        tool_name = tool_call.get('tool_name', '')
        service_name = tool_call.get('service_name', None)
        params = {k: v for k, v in tool_call.items() if k not in ['service_name', 'tool_name', 'agentType']}

        # 如果指定了主工具，使用主工具；否则使用tool_call中的工具
        primary = primary_tool if primary_tool else tool_name

        if config.tool_priority.log_fallback:
            logger.info(f"[ToolPriority] 开始调用工具: {primary} (服务: {service_name})")

        # 尝试调用主工具，传入service_name
        result = await self._call_tool(primary, params, mcp_manager, attempt=1, service_name=service_name)

        if result.success:
            return result

        # 如果主工具失败，尝试降级
        if self.fallback_strategy == FallbackStrategy.NONE:
            logger.warning(f"[ToolPriority] 工具 {primary} 调用失败，降级已禁用")
            return result

        # 获取降级工具列表
        fallback_tools = self.get_fallback_tools(primary)

        if not fallback_tools:
            logger.warning(f"[ToolPriority] 工具 {primary} 没有可用的降级工具")
            return result

        # 尝试降级工具
        for i, fallback_tool in enumerate(fallback_tools):
            logger.info(f"[ToolPriority] 工具 {primary} 失败，尝试降级工具 {fallback_tool} ({i+1}/{len(fallback_tools)})")

            result = await self._call_tool(fallback_tool, params, mcp_manager, attempt=i+2)

            if result.success:
                result.fallback_used = True
                result.attempt_count = i + 2

                # 记录降级历史
                self._record_fallback(primary, fallback_tool, result)

                return result

        logger.error(f"[ToolPriority] 所有工具调用失败，主工具: {primary}, 尝试了 {len(fallback_tools)+1} 个工具")

        return result

    async def _call_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        mcp_manager,
        attempt: int = 1,
        service_name: Optional[str] = None
    ) -> ToolCallResult:
        """调用单个工具（带超时和重试）"""
        # 如果没有提供service_name，则通过tool_name查找
        if not service_name:
            service_name = self._find_service_by_tool(tool_name)

        # 特殊映射：如果找不到服务，检查是否是已知的工具
        if not service_name:
            # Undefined工具集的特殊映射
            undefined_tools = [
                "info_agent", "code_delivery_agent", "entertainment_agent",
                "file_analysis_agent", "naga_code_analysis_agent",
                "scheduler_agent", "web_agent",
                "ai_draw_one", "local_ai_draw", "minecraft_skin"
            ]

            if tool_name in undefined_tools or tool_name in entertainment_subtools:
                service_name = "Undefined工具集"
                logger.info(f"[ToolPriority] 使用映射服务: {tool_name} -> {service_name}")

        if not service_name:
            return ToolCallResult(
                success=False,
                tool_name=tool_name,
                result=None,
                error=f"找不到服务: {tool_name}"
            )

        # 应用参数名映射
        mapped_params = params.copy()
        if tool_name in self.PARAM_NAME_MAP:
            param_map = self.PARAM_NAME_MAP[tool_name]
            for old_key, new_key in param_map.items():
                if old_key in mapped_params:
                    mapped_params[new_key] = mapped_params.pop(old_key)
                    logger.debug(f"[ToolPriority] 参数名映射: {tool_name}.{old_key} -> {new_key}")

        # 获取工具特定的超时时间，如果没有则使用默认超时
        tool_timeout = self.TOOL_SPECIFIC_TIMEOUT.get(tool_name, self.tool_timeout)
        logger.debug(f"[ToolPriority] 工具 {tool_name} 使用超时: {tool_timeout}ms")

        for retry in range(self.max_retries + 1):
            try:
                # 使用超时机制（根据工具类型使用不同的超时时间）
                result = await asyncio.wait_for(
                    mcp_manager.unified_call(service_name, tool_name, mapped_params),
                    timeout=tool_timeout / 1000
                )

                logger.debug(f"[ToolPriority] 工具 {tool_name} 原始返回类型: {type(result)}, 内容: {str(result)[:200]}")

                # 检查结果是否成功
                # 成功的格式可能是:
                # 1. {"success": True, ...}
                # 2. {"status": "ok", ...}
                # 3. 直接返回字符串结果
                is_success = False
                
                # 如果result是字符串，尝试解析为JSON
                if isinstance(result, str):
                    try:
                        import json
                        result = json.loads(result)
                        logger.debug(f"[ToolPriority] 工具 {tool_name} 结果从字符串解析为JSON")
                    except:
                        logger.debug(f"[ToolPriority] 工具 {tool_name} 结果无法解析为JSON，保持为字符串")
                
                if isinstance(result, dict):
                    if result.get('success') is True:
                        is_success = True
                    elif result.get('status') == 'ok':
                        is_success = True
                    elif 'success' not in result and 'status' not in result:
                        # 直接返回的结果（无success/status字段），也视为成功
                        is_success = True
                    logger.debug(f"[ToolPriority] 工具 {tool_name} 结果解析: 字典, success={is_success}")
                elif isinstance(result, str):
                    logger.debug(f"[ToolPriority] 工具 {tool_name} 结果解析: 字符串: {result[:100]}")
                else:
                    logger.debug(f"[ToolPriority] 工具 {tool_name} 结果解析: 未知类型: {type(result)}")
                
                if is_success:
                    if config.tool_priority.log_fallback:
                        logger.info(f"[ToolPriority] 工具 {tool_name} 调用成功 (尝试 {attempt}, 重试 {retry})")
                    return ToolCallResult(
                        success=True,
                        tool_name=tool_name,
                        result=result,
                        attempt_count=attempt
                    )
                elif retry < self.max_retries:
                    logger.warning(f"[ToolPriority] 工具 {tool_name} 返回失败结果，重试 {retry+1}/{self.max_retries}")
                    await asyncio.sleep(1)  # 等待1秒后重试
                else:
                    return ToolCallResult(
                        success=False,
                        tool_name=tool_name,
                        result=result,
                        error="工具返回失败结果",
                        attempt_count=attempt
                    )

            except asyncio.TimeoutError:
                logger.warning(f"[ToolPriority] 工具 {tool_name} 调用超时，重试 {retry+1}/{self.max_retries}")
                if retry < self.max_retries:
                    await asyncio.sleep(1)
                else:
                    return ToolCallResult(
                        success=False,
                        tool_name=tool_name,
                        result=None,
                        error=f"工具调用超时 ({self.tool_timeout}ms)",
                        attempt_count=attempt
                    )
            except Exception as e:
                logger.error(f"[ToolPriority] 工具 {tool_name} 调用异常: {e}")
                if retry < self.max_retries:
                    await asyncio.sleep(1)
                else:
                    return ToolCallResult(
                        success=False,
                        tool_name=tool_name,
                        result=None,
                        error=str(e),
                        attempt_count=attempt
                    )

        return ToolCallResult(
            success=False,
            tool_name=tool_name,
            result=None,
            error=f"工具调用失败，已重试 {self.max_retries} 次",
            attempt_count=attempt
        )

    def _record_fallback(self, primary_tool: str, fallback_tool: str, result: ToolCallResult):
        """记录降级历史"""
        if not self.log_fallback:
            return

        record = {
            "primary_tool": primary_tool,
            "fallback_tool": fallback_tool,
            "timestamp": logger,
            "success": result.success,
            "error": result.error
        }

        self._fallback_history.append(record)

        # 保持历史记录不超过100条
        if len(self._fallback_history) > 100:
            self._fallback_history = self._fallback_history[-100:]

        logger.info(f"[ToolPriority] 记录降级历史: {primary_tool} -> {fallback_tool}")

    def get_fallback_history(self) -> List[Dict[str, Any]]:
        """获取降级历史"""
        return self._fallback_history

    def get_priority_summary(self) -> str:
        """获取优先级配置摘要"""
        summary = []
        summary.append("=== 工具优先级系统配置 ===")
        summary.append(f"降级策略: {self.fallback_strategy.value}")
        summary.append(f"工具超时: {self.tool_timeout}ms")
        summary.append(f"最大重试: {self.max_retries}")
        summary.append(f"记录降级: {self.log_fallback}")
        summary.append("\n能力类别优先级:")
        for capability, priority in sorted(self.capability_priority.items(), key=lambda x: -x[1]):
            summary.append(f"  {capability}: {priority}")
        summary.append(f"\n优先工具: {self.preferred_tools}")
        summary.append(f"禁用工具: {self.blocked_tools}")

        return "\n".join(summary)


# 全局单例
_tool_priority_manager = None


def get_tool_priority_manager() -> ToolPriorityManager:
    """获取全局工具优先级管理器实例"""
    global _tool_priority_manager
    if _tool_priority_manager is None:
        _tool_priority_manager = ToolPriorityManager()
    return _tool_priority_manager
