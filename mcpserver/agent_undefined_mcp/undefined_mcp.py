"""
Undefined MCP Server
将Undefined的所有工具和Agent通过MCP协议暴露给NagaAgent
"""
import asyncio
import sys
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 添加Undefined到Python路径
UNDEFINED_PATH = Path(__file__).parent.parent.parent / "Undefined"
# Undefined的源码在src/Undefined下
UNDEFINED_SRC_PATH = UNDEFINED_PATH / "src"

# 临时切换工作目录到 Undefined，确保 Python 优先使用 ai/ 目录而不是 ai.py 文件
import os
_original_cwd = os.getcwd()
os.chdir(str(UNDEFINED_PATH))

try:
    # 添加 src 到 sys.path（使用当前工作目录）
    sys.path.insert(0, str(Path.cwd() / "src"))

    # 关键修复: 清除可能存在的错误缓存
    # 如果之前 agent_undefined 加载了 ai.py 文件，需要清除缓存
    for module_name in list(sys.modules.keys()):
        if module_name.startswith('Undefined.ai'):
            del sys.modules[module_name]
            sys.stderr.write(f"[DEBUG] 清除模块缓存: {module_name}\n")

    # 导入Undefined的核心模块
    # 使用从 ai/ 目录导入的方式
    from Undefined.ai import AIClient

    from Undefined.config import get_config
    # 导入新版本ToolRegistry（用于skills/tools）
    from Undefined.skills.tools import ToolRegistry as NewToolRegistry
    # 导入旧版本ToolRegistry（用于tools/ai_draw_one等旧工具）
    from Undefined.tools import ToolRegistry as OldToolRegistry
    from Undefined.skills.agents import AgentRegistry
    from Undefined.memory import MemoryStorage
    from Undefined.end_summary_storage import EndSummaryStorage
    from Undefined.skills.agents.runner import run_agent_with_tools
    from Undefined import __version__

    print(f"Undefined版本: {__version__}")
    print(f"AIClient来自: {AIClient.__module__}")
except ImportError as e:
    print(f"警告: 无法导入Undefined模块 - {e}")
    import traceback
    traceback.print_exc()
    print(f"Undefined源码路径: {UNDEFINED_SRC_PATH}")
    AIClient = None
    get_config = None
    NewToolRegistry = None
    OldToolRegistry = None
    AgentRegistry = None
    MemoryStorage = None
    EndSummaryStorage = None
    run_agent_with_tools = None
finally:
    # 恢复原始工作目录
    os.chdir(_original_cwd)


class UndefinedMCPServer:
    """Undefined MCP服务器

    将Undefined的工具和Agent转换为MCP工具格式
    """

    def __init__(self, undefined_path: Path = UNDEFINED_PATH):
        self.undefined_path = undefined_path
        self.new_tool_registry: Optional[NewToolRegistry] = None  # 新版本（skills/tools）
        self.old_tool_registry: Optional[OldToolRegistry] = None  # 旧版本（tools/ai_draw_one）
        self.agent_registry: Optional[AgentRegistry] = None
        self.ai_client: Optional[AIClient] = None
        self.config = None
        self._initialized = False

    async def initialize(self) -> bool:
        """初始化Undefined环境"""
        if self._initialized:
            return True

        if not all([NewToolRegistry, OldToolRegistry, AgentRegistry, AIClient, get_config, MemoryStorage, EndSummaryStorage]):
            print("错误: Undefined模块未正确加载")
            print(f"Undefined源码路径: {UNDEFINED_SRC_PATH}")
            print(f"sys.path包含: {sys.path[:3]}")
            return False

        try:
            # 切换到Undefined目录加载配置
            import os
            original_dir = os.getcwd()
            target_dir = str(self.undefined_path)
            sys.stderr.write(f"[DEBUG] 切换工作目录: {original_dir} -> {target_dir}\n")
            os.chdir(target_dir)

            # 加载Undefined配置（使用非严格模式，允许配置字段为空）
            sys.stderr.write(f"[DEBUG] 开始加载Undefined配置...\n")
            try:
                self.config = get_config(strict=False)
                sys.stderr.write(f"[DEBUG] Undefined配置加载成功\n")
            except Exception as config_error:
                sys.stderr.write(f"[DEBUG] Undefined配置加载失败: {config_error}\n")
                import traceback
                traceback.print_exc(file=sys.stderr)
                os.chdir(original_dir)
                return False

            # 恢复原目录
            os.chdir(original_dir)

            # 初始化存储
            sys.stderr.write(f"[DEBUG] 初始化MemoryStorage...\n")
            memory_storage = MemoryStorage()
            sys.stderr.write(f"[DEBUG] 初始化EndSummaryStorage...\n")
            end_summary_storage = EndSummaryStorage()

            # 初始化AI客户端（传入必要的配置项）
            sys.stderr.write(f"[DEBUG] 初始化AIClient...\n")
            try:
                self.ai_client = AIClient(
                    chat_config=self.config.chat_model,
                    vision_config=self.config.vision_model,
                    agent_config=self.config.agent_model,
                    memory_storage=memory_storage,
                    end_summary_storage=end_summary_storage,
                    bot_qq=self.config.bot_qq,
                    runtime_config=self.config
                )
                sys.stderr.write(f"[DEBUG] AIClient初始化成功\n")
            except Exception as ai_error:
                sys.stderr.write(f"[DEBUG] AIClient初始化失败: {ai_error}\n")
                import traceback
                traceback.print_exc(file=sys.stderr)
                return False

            # 获取工具和Agent注册表
            # 新版本ToolRegistry（skills/tools和agents/*/tools目录）
            sys.stderr.write(f"[DEBUG] 初始化ToolRegistry...\n")
            new_tools_dir = UNDEFINED_SRC_PATH / "Undefined" / "skills" / "tools"
            info_agent_tools_dir = UNDEFINED_SRC_PATH / "Undefined" / "skills" / "agents" / "info_agent" / "tools"
            self.new_tool_registry = NewToolRegistry(new_tools_dir)
            # 加载额外的工具目录（info_agent/tools）
            if info_agent_tools_dir.exists():
                self.new_tool_registry._discover_items_in_dir(info_agent_tools_dir, prefix="")
            # 旧版本ToolRegistry（tools目录，包含ai_draw_one和local_ai_draw）
            self.old_tool_registry = OldToolRegistry()
            self.agent_registry = AgentRegistry()
            sys.stderr.write(f"[DEBUG] ToolRegistry初始化成功\n")

            # 扫描并加载Agent（同步方法）
            # 注意：这些是同步方法，不需要await
            sys.stderr.write(f"[DEBUG] 开始加载Agents...\n")
            try:
                self.agent_registry.load_agents()
                sys.stderr.write(f"[DEBUG] Agent加载成功，共 {len(self.agent_registry._items)} 个\n")
            except Exception as agent_error:
                sys.stderr.write(f"[DEBUG] Agent加载失败: {agent_error}\n")
                import traceback
                traceback.print_exc(file=sys.stderr)
                # Agent加载失败不影响整体初始化

            self._initialized = True
            print(f"Undefined MCP Server 初始化成功")
            print(f"  - 新版本工具数量 (skills/tools): {len(self.new_tool_registry._items)}")
            print(f"  - 旧版本工具数量 (tools/ai_draw_one等): {len(self.old_tool_registry._tools_handlers)}")
            print(f"  - Agent数量: {len(self.agent_registry._items)}")
            return True

        except Exception as e:
            print(f"Undefined MCP Server 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取所有可用的Undefined工具列表（OpenAI函数调用格式）"""
        if not self._initialized:
            await self.initialize()

        tools = []

        # 添加新版本工具（skills/tools）
        if self.new_tool_registry:
            for tool_name in self.new_tool_registry._items.keys():
                tool_info = {
                    "function": {
                        "name": f"tool.{tool_name}",
                        "description": f"工具: {tool_name}",
                    },
                    "type": "tool"
                }
                tools.append(tool_info)

        # 添加旧版本工具（tools/ai_draw_one等）
        if self.old_tool_registry:
            for tool_name in self.old_tool_registry._tools_handlers.keys():
                tool_info = {
                    "function": {
                        "name": f"tool.{tool_name}",
                        "description": f"旧版工具: {tool_name}",
                    },
                    "type": "tool"
                }
                tools.append(tool_info)

        # 添加Agent
        if self.agent_registry:
            for agent_name in self.agent_registry._items.keys():
                agent_info = {
                    "function": {
                        "name": f"agent.{agent_name}",
                        "description": f"Agent: {agent_name}",
                    },
                    "type": "agent"
                }
                tools.append(agent_info)

        return tools
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """调用指定的Undefined工具或Agent"""
        if not self._initialized:
            return {"error": "Undefined MCP Server 未初始化"}

        try:
            logger.info(f"[UndefinedMCP] call_tool: tool_name={tool_name}, arguments keys={list(arguments.keys())}")
            if context:
                logger.info(f"[UndefinedMCP] context keys={list(context.keys())}")

            # 检查是否是直接的 agent 名称(如 info_agent)
            if self.agent_registry and tool_name in self.agent_registry._items:
                logger.info(f"[UndefinedMCP] 找到Agent: {tool_name}")
                return await self._call_agent(tool_name, arguments, context)

            # 检查是否是直接的 tool 名称（优先旧版本，如 ai_draw_one, local_ai_draw）
            if self.old_tool_registry and tool_name in self.old_tool_registry._tools_handlers:
                logger.info(f"[UndefinedMCP] 找到旧版工具: {tool_name}")
                return await self._call_old_tool_internal(tool_name, arguments, context)

            # 检查是否是新版本的 tool 名称(如 get_current_time)
            if self.new_tool_registry and tool_name in self.new_tool_registry._items:
                logger.info(f"[UndefinedMCP] 找到新版工具: {tool_name}")
                return await self._call_new_tool_internal(tool_name, arguments, context)

            # 打印调试信息：工具列表
            if self.old_tool_registry:
                old_tool_names = list(self.old_tool_registry._tools_handlers.keys())
                logger.debug(f"[UndefinedMCP] 可用旧版工具列表: {old_tool_names[:20]}...")
            if self.new_tool_registry:
                new_tool_names = list(self.new_tool_registry._items.keys())
                logger.debug(f"[UndefinedMCP] 可用新版工具列表: {new_tool_names[:20]}...")

            # 解析工具名称(支持 tool.tool_name 或 agent.agent_name 格式)
            # 兼容不带前缀的工具名称（如 ai_draw_one）
            parts = tool_name.split(".", 1)

            # 定义 entertainment_agent 的子工具列表（仅限娱乐助手的工具）
            entertainment_subtools = {
                "minecraft_skin": "Minecraft皮肤"
            }

            if len(parts) == 2:
                # 有前缀: tool.tool_name 或 agent.agent_name
                tool_type, tool_id = parts
                logger.info(f"[UndefinedMCP] 解析前缀工具: type={tool_type}, id={tool_id}")
                if tool_type == "tool":
                    # 检查是否是 entertainment_agent 的子工具
                    if tool_id in entertainment_subtools:
                        logger.info(f"[UndefinedMCP] 识别到 {tool_id} 为 entertainment_agent 子工具")
                        # 构建prompt来调用entertainment_agent
                        prompt = f"请执行{entertainment_subtools[tool_id]}功能: {arguments.get('prompt', '')}"
                        return await self._call_agent("entertainment_agent", {"prompt": prompt}, context)
                    else:
                        # 优先检查旧版工具（ai_draw_one 和 local_ai_draw）
                        if self.old_tool_registry and tool_id in self.old_tool_registry._tools_handlers:
                            return await self._call_old_tool_internal(tool_id, arguments, context)
                        # 然后检查新版工具
                        elif self.new_tool_registry and tool_id in self.new_tool_registry._items:
                            return await self._call_new_tool_internal(tool_id, arguments, context)
                elif tool_type == "agent":
                    return await self._call_agent(tool_id, arguments, context)
                else:
                    return {"error": f"未知的工具类型: {tool_type}"}
            else:
                # 无前缀，尝试直接匹配工具和Agent
                logger.info(f"[UndefinedMCP] 无前缀工具，尝试直接匹配: {tool_name}")
                # 首先检查是否是 entertainment_agent 的子工具
                if tool_name in entertainment_subtools:
                    logger.info(f"[UndefinedMCP] 识别到 {tool_name} 为 entertainment_agent 子工具")
                    prompt = f"请执行{entertainment_subtools[tool_name]}功能: {arguments.get('prompt', '')}"
                    return await self._call_agent("entertainment_agent", {"prompt": prompt}, context)
                # 然后尝试旧版工具（ai_draw_one 和 local_ai_draw）
                elif self.old_tool_registry and tool_name in self.old_tool_registry._tools_handlers:
                    return await self._call_old_tool_internal(tool_name, arguments, context)
                # 然后尝试新版工具
                elif self.new_tool_registry and tool_name in self.new_tool_registry._items:
                    return await self._call_new_tool_internal(tool_name, arguments, context)
                # 最后尝试Agent
                elif self.agent_registry and tool_name in self.agent_registry._items:
                    return await self._call_agent(tool_name, arguments, context)
                else:
                    return {"error": f"工具不存在: {tool_name}"}

        except Exception as e:
            import traceback
            error_msg = f"调用工具失败: {e}"
            logger.error(f"错误详情: {traceback.format_exc()}")
            return {"error": error_msg}
    
    async def _call_old_tool_internal(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """调用旧版本工具（ai_draw_one, local_ai_draw等）"""
        if not self.old_tool_registry:
            return {"error": "旧版工具注册表未初始化"}

        # 构建工具上下文，注入QQ回调函数
        tool_context = context.copy() if context else {}

        # 尝试从MCP注册中心获取QQ适配器实例
        try:
            from mcpserver.mcp_registry import get_service_info

            qq_service = get_service_info("QQ/微信集成")
            if qq_service:
                qq_agent = qq_service.get("instance")
                if qq_agent and hasattr(qq_agent, 'qq_adapter'):
                    qq_adapter = qq_agent.qq_adapter

                    # 构建QQ回调函数
                    async def send_like_callback(target_user_id: int, times: int = 1) -> None:
                        """给用户点赞回调"""
                        if qq_adapter:
                            await qq_adapter.send_like(target_user_id, times)

                    async def send_image_callback(target_id: int, msg_type: str, file_path: str) -> None:
                        """发送图片回调"""
                        try:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.info(f"[send_image_callback] target_id={target_id}, msg_type={msg_type}, file_path={file_path}")

                            # 构建图片消息段
                            image_message = {
                                "type": "image",
                                "data": {
                                    "file": file_path
                                }
                            }

                            # 确定发送目标
                            if msg_type == "group":
                                await qq_adapter.send_group_message(target_id, image_message)
                            else:
                                await qq_adapter.send_message(str(target_id), image_message)

                            logger.info(f"[send_image_callback] 发送完成")
                        except Exception as e:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.error(f"发送图片回调失败: {e}")

                    async def send_message_callback(target_id: int, msg_type: str, message: str) -> None:
                        """发送消息回调"""
                        try:
                            import logging
                            logger = logging.getLogger(__name__)

                            if msg_type == "group":
                                await qq_adapter.send_group_message(target_id, message)
                            else:
                                await qq_adapter.send_message(str(target_id), message)

                            logger.info(f"[send_message_callback] 发送完成")
                        except Exception as e:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.error(f"发送消息回调失败: {e}")

                    # 将回调函数注入到上下文
                    tool_context["send_like_callback"] = send_like_callback
                    tool_context["send_image_callback"] = send_image_callback
                    tool_context["send_message_callback"] = send_message_callback
                    tool_context["sender"] = qq_adapter

                    print(f"[UndefinedMCP] 已注入QQ回调函数到工具上下文（旧版工具）")

        except Exception as e:
            import traceback
            print(f"[UndefinedMCP] 注入QQ回调函数失败: {e}")
            traceback.print_exc()

        # 使用旧版 ToolRegistry 的 execute_tool 方法调用工具
        try:
            result = await self.old_tool_registry.execute_tool(tool_name, arguments, tool_context)
            return {
                "result": result,
                "tool": tool_name,
                "success": True
            }
        except Exception as e:
            import traceback
            error_msg = f"旧版工具调用失败: {e}"
            print(f"错误详情: {traceback.format_exc()}")
            return {"error": error_msg, "tool": tool_name, "success": False}

    async def _call_new_tool_internal(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """调用新版本工具（skills/tools目录下的工具）"""
        if not self.new_tool_registry:
            return {"error": "新版工具注册表未初始化"}

        # 构建工具上下文，注入QQ回调函数
        tool_context = context.copy() if context else {}

        # 尝试从MCP注册中心获取QQ适配器实例
        try:
            from mcpserver.mcp_registry import get_service_info

            qq_service = get_service_info("QQ/微信集成")
            if qq_service:
                qq_agent = qq_service.get("instance")
                if qq_agent and hasattr(qq_agent, 'qq_adapter'):
                    qq_adapter = qq_agent.qq_adapter

                    # 构建QQ回调函数
                    async def send_like_callback(target_user_id: int, times: int = 1) -> None:
                        """给用户点赞回调"""
                        if qq_adapter:
                            await qq_adapter.send_like(target_user_id, times)

                    async def send_image_callback(target_id: int, msg_type: str, file_path: str) -> None:
                        """发送图片回调"""
                        try:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.info(f"[send_image_callback] target_id={target_id}, msg_type={msg_type}, file_path={file_path}")

                            # 构建图片消息段
                            image_message = {
                                "type": "image",
                                "data": {
                                    "file": file_path
                                }
                            }

                            # 确定发送目标
                            if msg_type == "group":
                                await qq_adapter.send_group_message(target_id, image_message)
                            else:
                                await qq_adapter.send_message(str(target_id), image_message)

                            logger.info(f"[send_image_callback] 发送完成")
                        except Exception as e:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.error(f"发送图片回调失败: {e}")

                    async def send_message_callback(target_id: int, msg_type: str, message: str) -> None:
                        """发送消息回调"""
                        try:
                            import logging
                            logger = logging.getLogger(__name__)

                            if msg_type == "group":
                                await qq_adapter.send_group_message(target_id, message)
                            else:
                                await qq_adapter.send_message(str(target_id), message)

                            logger.info(f"[send_message_callback] 发送完成")
                        except Exception as e:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.error(f"发送消息回调失败: {e}")

                    # 将回调函数注入到上下文
                    tool_context["send_like_callback"] = send_like_callback
                    tool_context["send_image_callback"] = send_image_callback
                    tool_context["send_message_callback"] = send_message_callback
                    tool_context["sender"] = qq_adapter

                    print(f"[UndefinedMCP] 已注入QQ回调函数到工具上下文（新版工具）")

        except Exception as e:
            import traceback
            print(f"[UndefinedMCP] 注入QQ回调函数失败: {e}")
            traceback.print_exc()

        # 使用新版本 ToolRegistry 的 execute 方法调用工具
        try:
            result = await self.new_tool_registry.execute(tool_name, arguments, tool_context)
            return {
                "result": result,
                "tool": tool_name,
                "success": True
            }
        except Exception as e:
            import traceback
            error_msg = f"新版工具调用失败: {e}"
            print(f"错误详情: {traceback.format_exc()}")
            return {"error": error_msg, "tool": tool_name, "success": False}

    async def _call_agent(
        self,
        agent_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """调用Agent"""
        if not self.agent_registry:
            return {"error": "Agent注册表未初始化"}

        if not run_agent_with_tools:
            return {"error": "Agent运行器未加载"}

        # 获取agent handler (SkillItem对象)
        agent_item = self.agent_registry._items.get(agent_name)
        if not agent_item:
            return {"error": f"Agent不存在: {agent_name}"}

        try:
            # 构建调用上下文
            if context is None:
                context = {}

            # 记录接收到的context
            logger.info(f"[UndefinedMCP] _call_agent({agent_name}): context keys={list(context.keys())}")

            # 尝试从MCP注册中心获取QQ适配器实例并注入到context
            try:
                from mcpserver.mcp_registry import get_service_info

                qq_service = get_service_info("QQ/微信集成")
                if qq_service:
                    qq_agent = qq_service.get("instance")
                    if qq_agent and hasattr(qq_agent, 'qq_adapter'):
                        qq_adapter = qq_agent.qq_adapter
                        context["sender"] = qq_adapter
                        context["onebot_client"] = qq_adapter
                        logger.info(f"[UndefinedMCP] 已注入 onebot_client 到 context")
            except Exception as e:
                logger.warning(f"[UndefinedMCP] 注入 onebot_client 失败: {e}")

            # 注入ai_client到context（保留原始context中的其他参数）
            context["ai_client"] = self.ai_client

            # 调用agent的execute方法 (使用SkillItem对象的handler属性)
            result = await self.agent_registry.execute(agent_name, arguments, context)

            return {
                "result": result,
                "agent": agent_name,
                "success": True
            }
        except Exception as e:
            import traceback
            error_msg = f"Agent {agent_name} 调用失败: {e}"
            logger.error(f"错误详情: {traceback.format_exc()}")
            return {"error": error_msg, "agent": agent_name, "success": False}
    
    async def shutdown(self):
        """关闭服务器"""
        # AIClient没有shutdown方法，只需要关闭HTTP客户端
        if self.ai_client and hasattr(self.ai_client, '_http_client'):
            await self.ai_client._http_client.aclose()
        self._initialized = False


# 全局单例
_server_instance: Optional[UndefinedMCPServer] = None


async def get_server() -> UndefinedMCPServer:
    """获取Undefined MCP Server单例"""
    global _server_instance
    if _server_instance is None:
        _server_instance = UndefinedMCPServer()
        await _server_instance.initialize()
    return _server_instance


# 测试代码
async def main():
    """测试Undefined MCP Server"""
    server = UndefinedMCPServer()
    success = await server.initialize()
    
    if success:
        print("\n=== 可用工具列表 ===")
        tools = await server.get_available_tools()
        for tool in tools:
            print(f"  [{tool['type']}] {tool['name']}: {tool['description'][:50]}")
        
        print("\n=== 测试调用 ===")
        # 测试调用一个工具
        result = await server.call_tool("tool.get_current_time", {})
        print(f"结果: {result}")
    
    await server.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
