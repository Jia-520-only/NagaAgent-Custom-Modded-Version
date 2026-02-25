"""
Undefined MCP Agent
将Undefined的52个工具和7个Agent集成到NagaAgent的MCP框架中
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加父目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from .undefined_mcp import UndefinedMCPServer, get_server


class UndefinedMCPAgent:
    """Undefined MCP Agent
    
    将Undefined的工具和Agent暴露给NagaAgent的MCP框架
    """
    
    def __init__(self):
        """初始化Undefined MCP Agent"""
        self._server: Optional[UndefinedMCPServer] = None
        self._initialized = False
        
    async def initialize(self, config: Optional[Dict[str, Any]] = None):
        """初始化Agent
        
        Args:
            config: 配置字典（可选）
        """
        if self._initialized:
            return
            
        try:
            # 获取Undefined MCP Server单例
            self._server = await get_server()
            
            if not self._server or not self._server._initialized:
                sys.stderr.write("❌ Undefined MCP Server初始化失败\n")
                return False
            
            self._initialized = True
            sys.stderr.write("✅ Undefined MCP Agent初始化成功\n")
            return True
            
        except Exception as e:
            sys.stderr.write(f"❌ Undefined MCP Agent初始化失败: {e}\n")
            import traceback
            traceback.print_exc(file=sys.stderr)
            return False
    
    def initialize_sync(self, config: Optional[Dict[str, Any]] = None):
        """同步初始化方法（用于兼容旧版调用）

        Args:
            config: 配置字典（可选）
        """
        import threading

        # 在独立线程中运行异步初始化，避免事件循环冲突
        result_container = [None]
        exception_container = [None]
        ready_event = threading.Event()

        def run_in_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                result_container[0] = new_loop.run_until_complete(self.initialize(config))
                ready_event.set()
            except Exception as e:
                exception_container[0] = e
                ready_event.set()
            finally:
                new_loop.close()

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()

        # 等待线程完成（最多30秒）
        if ready_event.wait(timeout=30):
            thread.join(timeout=5)
            if exception_container[0]:
                raise exception_container[0]
            return result_container[0]
        else:
            raise TimeoutError("Undefined MCP Agent 初始化超时")
    
    async def handle_handoff(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """处理handoff调用

        Args:
            task: 任务字典，包含工具名称和参数
            context: 执行上下文

        Returns:
            str: 执行结果JSON字符串
        """
        # 自动初始化（如果未初始化）
        if not self._initialized:
            await self.initialize()
            if not self._initialized:
                return json.dumps({
                    "success": False,
                    "result": "Undefined MCP Agent未初始化"
                }, ensure_ascii=False)

        try:
            # 解析任务参数
            tool_name = task.get("tool_name", "")
            if not tool_name:
                return json.dumps({
                    "success": False,
                    "result": "缺少tool_name参数"
                }, ensure_ascii=False)

            # 构建参数字典（移除tool_name）
            arguments = {k: v for k, v in task.items() if k != "tool_name"}

            # 调用Undefined MCP Server的工具，传递context
            result = await self._server.call_tool(tool_name, arguments, context=context)

            # 返回标准格式结果
            if "error" in result:
                return json.dumps({
                    "success": False,
                    "result": result["error"]
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    "success": True,
                    "result": result.get("result", ""),
                    "details": result
                }, ensure_ascii=False)

        except Exception as e:
            sys.stderr.write(f"❌ Undefined MCP Agent执行失败: {e}\n")
            import traceback
            traceback.print_exc(file=sys.stderr)
            return json.dumps({
                "success": False,
                "result": f"执行失败: {str(e)}"
            }, ensure_ascii=False)

    async def call_tool(self, tool_name: str, args: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """异步工具调用接口

        Args:
            tool_name: 工具名称
            args: 工具参数
            context: 执行上下文

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 构建任务字典
        task = {"tool_name": tool_name, **args}

        # 调用异步方法，传递context
        result_str = await self.handle_handoff(task, context)

        # 解析结果
        try:
            return json.loads(result_str)
        except Exception as e:
            return {
                "success": False,
                "result": f"解析结果失败: {str(e)}"
            }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用的工具列表

        Returns:
            List[Dict[str, Any]]: 工具列表
        """
        # 自动初始化（如果未初始化）
        if not self._initialized:
            try:
                sys.stderr.write(f"[DEBUG] get_available_tools: 未初始化，开始自动初始化...\n")
                self.initialize_sync()
                sys.stderr.write(f"[DEBUG] get_available_tools: 初始化完成，_initialized={self._initialized}\n")
            except Exception as e:
                sys.stderr.write(f"❌ 自动初始化失败: {e}\n")
                import traceback
                traceback.print_exc(file=sys.stderr)
                return []

        if not self._initialized or not self._server:
            sys.stderr.write(f"[DEBUG] get_available_tools: 初始化后状态错误 - _initialized={self._initialized}, _server={bool(self._server)}\n")
            return []

        import threading

        # 在独立线程中运行，避免事件循环冲突
        result_container = [None]
        exception_container = [None]
        ready_event = threading.Event()

        def run_in_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                result_container[0] = new_loop.run_until_complete(self._server.get_available_tools())
                ready_event.set()
            except Exception as e:
                exception_container[0] = e
                ready_event.set()
            finally:
                new_loop.close()

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()

        # 等待线程完成（最多10秒）
        if ready_event.wait(timeout=10):
            thread.join(timeout=5)
            if exception_container[0]:
                sys.stderr.write(f"❌ 获取工具列表失败: {exception_container[0]}\n")
                return []
            return result_container[0] if result_container[0] else []
        else:
            sys.stderr.write("❌ 获取工具列表超时\n")
            return []
    
    async def shutdown(self):
        """关闭Agent"""
        if self._server:
            await self._server.shutdown()
        self._initialized = False
    
    def __del__(self):
        """析构函数，确保资源清理"""
        if self._server:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._server.shutdown())
                else:
                    loop.run_until_complete(self._server.shutdown())
            except Exception:
                pass
