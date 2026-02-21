"""
包豆AI MCP Agent - 视觉自动化控制系统
"""
from .baodou_controller import BaodouAIController, get_controller, initialize_controller
from .baodou_tools import (
    baodou_capture_screen,
    baodou_analyze_task,
    baodou_get_status,
    baodou_mark_coordinates,
    baodou_mouse_move,
    baodou_mouse_click,
    baodou_keyboard_type,
    baodou_keyboard_press,
    baodou_launch_gui
)


class BaodouAIAgent:
    """包豆AI Agent类 - 用于MCP注册和初始化"""

    def __init__(self):
        """初始化Agent"""
        self.controller = None
        self.is_initialized = False

    def initialize(self, config: dict = None):
        """初始化控制器（可选）"""
        try:
            # 使用系统配置中的启用状态和配置路径
            if config:
                system_enabled = config.get("baodou_ai", {}).get("enabled", False)
                config_path = config.get("baodou_ai", {}).get("config_path", "baodou_AI/config.json")
                self.controller = initialize_controller(config_path, system_enabled)
            else:
                # 使用默认配置
                self.controller = initialize_controller()

            self.is_initialized = True
            return True
        except Exception as e:
            import sys
            sys.stderr.write(f"BaodouAIAgent初始化失败: {e}\n")
            return False

    async def call_tool(
        self,
        tool_name: str,
        parameters: dict,
        context: dict = None
    ) -> str:
        """调用包豆AI工具

        Args:
            tool_name: 工具名称
            parameters: 工具参数
            context: 执行上下文（可选）

        Returns:
            工具执行结果
        """
        # 导入工具函数
        from .baodou_tools import (
            baodou_capture_screen,
            baodou_analyze_task,
            baodou_get_status,
            baodou_mark_coordinates,
            baodou_mouse_move,
            baodou_mouse_click,
            baodou_keyboard_type,
            baodou_keyboard_press,
            baodou_launch_gui
        )

        # 工具函数映射
        tool_map = {
            'baodou_capture_screen': baodou_capture_screen,
            'baodou_analyze_task': baodou_analyze_task,
            'baodou_get_status': baodou_get_status,
            'baodou_mark_coordinates': baodou_mark_coordinates,
            'baodou_mouse_move': baodou_mouse_move,
            'baodou_mouse_click': baodou_mouse_click,
            'baodou_keyboard_type': baodou_keyboard_type,
            'baodou_keyboard_press': baodou_keyboard_press,
            'baodou_launch_gui': baodou_launch_gui
        }

        # 获取工具函数
        tool_func = tool_map.get(tool_name)
        if not tool_func:
            return f"错误: 未找到工具 '{tool_name}'"

        try:
            # 调用工具函数
            import inspect
            sig = inspect.signature(tool_func)
            param_names = set(sig.parameters.keys())

            # 只传递工具函数需要的参数
            filtered_params = {k: v for k, v in parameters.items() if k in param_names}

            # 执行工具（同步或异步）
            result = tool_func(**filtered_params)

            # 如果是协程，等待执行完成
            if inspect.iscoroutine(result):
                result = await result

            # 格式化返回结果
            if isinstance(result, dict):
                return str(result)
            return str(result)

        except Exception as e:
            import traceback
            error_msg = f"工具 '{tool_name}' 执行失败: {str(e)}\n{traceback.format_exc()}"
            return error_msg



__all__ = [
    "BaodouAIAgent",
    "BaodouAIController",
    "get_controller",
    "initialize_controller",
    "baodou_capture_screen",
    "baodou_analyze_task",
    "baodou_get_status",
    "baodou_mark_coordinates",
    "baodou_mouse_move",
    "baodou_mouse_click",
    "baodou_keyboard_type",
    "baodou_keyboard_press",
    "baodou_launch_gui"
]

