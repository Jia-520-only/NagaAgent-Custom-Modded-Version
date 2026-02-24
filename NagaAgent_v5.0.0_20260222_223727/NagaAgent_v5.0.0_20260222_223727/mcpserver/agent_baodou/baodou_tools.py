"""
包豆AI MCP工具 - 提供视觉自动化能力给弥娅
"""

from typing import Optional, Dict, Any, List
import subprocess
import sys
from pathlib import Path
from .baodou_controller import get_controller

# 不在导入时立即初始化控制器，改为按需获取
controller = None


def _get_controller():
    """获取控制器单例（延迟加载）"""
    global controller
    if controller is None:
        controller = get_controller()
    return controller


def baodou_capture_screen() -> Dict[str, Any]:
    """
    截取当前屏幕

    返回:
        Dict: 包含截图结果
            - success: bool - 是否成功
            - path: str - 截图保存路径
            - error: str - 错误信息(如果失败)
    """
    try:
        ctrl = _get_controller()
        result = ctrl.capture_screen()
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"截图失败: {str(e)}"
        }


def baodou_analyze_task(task_description: str,
                        max_iterations: Optional[int] = None) -> Dict[str, Any]:
    """
    分析任务并发送到包豆GUI执行 (统一交互界面)

    如果包豆GUI正在运行，自动将任务发送到GUI执行；
    如果GUI未运行，返回分析结果和启动建议。

    参数:
        task_description: str - 任务描述
        max_iterations: int - 最大迭代次数

    返回:
        Dict: 执行结果
            - success: bool - 是否成功
            - analysis: str - 任务分析
            - sent_to_gui: bool - 是否发送到GUI
            - suggested_steps: List[str] - 建议的执行步骤
            - estimated_time: str - 预计时间
            - task_id: str - 任务ID（如果已发送）
            - note: str - 提示信息
            - error: str - 错误信息(如果失败)
    """
    try:
        ctrl = _get_controller()

        # 检查是否启用
        status = ctrl.get_status()
        if not status["enabled"]:
            return {
                "success": False,
                "error": "包豆AI未启用,请先配置API密钥或在config.json中启用baodou_ai.enabled"
            }

        # 尝试检查并连接包豆GUI
        try:
            from .baodou_communicator import get_communicator

            communicator = get_communicator()
            gui_status = communicator.check_baodou_status()

            # 如果GUI正在运行，发送任务执行
            if gui_status.get("gui_running", False):
                print(f"[包豆工具] 检测到GUI运行，发送任务: {task_description}")
                result = communicator.send_task_to_baodou(
                    task_description=task_description,
                    wait_for_completion=False,
                    timeout=60
                )

                if result.get("success"):
                    return {
                        "success": True,
                        "analysis": f"任务已发送到包豆GUI: {task_description}",
                        "sent_to_gui": True,
                        "task_id": result.get("task_id"),
                        "message": result.get("message"),
                        "suggested_steps": ["任务正在包豆GUI中执行中..."],
                        "estimated_time": "视任务复杂度而定",
                        "note": "任务正在包豆GUI中执行，请查看GUI窗口"
                    }
                else:
                    # 发送失败，降级为返回分析
                    print(f"[包豆工具] 发送任务失败: {result.get('error')}")
                    pass

        except ImportError:
            print("[包豆工具] 通信模块不可用")
        except Exception as e:
            print(f"[包豆工具] 检查GUI状态异常: {e}")

        # GUI未运行或发送失败，返回分析结果
        analysis = f"任务分析: {task_description}"
        suggested_steps = [
            "1. 理解任务目标",
            "2. 截取当前屏幕",
            "3. 分析屏幕内容",
            "4. 确定操作序列",
            "5. 执行操作",
            "6. 验证结果"
        ]

        return {
            "success": True,
            "analysis": analysis,
            "sent_to_gui": False,
            "suggested_steps": suggested_steps,
            "estimated_time": "视任务复杂度而定",
            "note": "包豆GUI未运行，任务未自动执行。请启动包豆GUI或手动执行"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"任务分析失败: {str(e)}"
        }


def baodou_get_status() -> Dict[str, Any]:
    """
    获取包豆AI状态

    返回:
        Dict: 状态信息
            - enabled: bool - 是否启用
            - has_visual_module: bool - 是否有视觉模块
            - api_configured: bool - API是否配置
            - current_task: str - 当前任务
            - config: Dict - 当前配置
    """
    try:
        ctrl = _get_controller()
        status = ctrl.get_status()
        return {
            "success": True,
            **status,
            "config": ctrl.config
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"获取状态失败: {str(e)}"
        }


def baodou_mark_coordinates(coordinates: List[Dict[str, float]],
                           image_path: Optional[str] = None) -> Dict[str, Any]:
    """
    在屏幕截图上标记坐标点

    参数:
        coordinates: List[Dict] - 坐标点列表,每个点包含 x, y
            [{"x": 100.5, "y": 200.3}, ...]
        image_path: str - 源图像路径(可选)

    返回:
        Dict: 标记结果
            - success: bool - 是否成功
            - output_path: str - 标记后的图像路径
            - error: str - 错误信息(如果失败)
    """
    try:
        ctrl = _get_controller()
        result = ctrl.mark_coordinates(coordinates, image_path)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"标记坐标失败: {str(e)}"
        }


def baodou_mouse_move(x: float, y: float, duration: Optional[float] = None) -> Dict[str, Any]:
    """
    移动鼠标到指定位置 (基础功能)

    参数:
        x: float - 目标X坐标
        y: float - 目标Y坐标
        duration: float - 移动持续时间(秒)

    返回:
        Dict: 操作结果
            - success: bool - 是否成功
            - error: str - 错误信息(如果失败)
    """
    try:
        ctrl = _get_controller()
        import pyautogui

        # 设置移动持续时间
        if duration is None:
            duration = ctrl.config["mouse_config"]["move_duration"]

        # 移动鼠标
        pyautogui.moveTo(x, y, duration=duration)

        return {
            "success": True,
            "action": f"移动鼠标到 ({x}, {y})",
            "duration": duration
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"鼠标移动失败: {str(e)}"
        }


def baodou_mouse_click(x: Optional[float] = None,
                       y: Optional[float] = None,
                       button: str = "left",
                       clicks: int = 1) -> Dict[str, Any]:
    """
    鼠标点击操作

    参数:
        x: float - X坐标(可选,不指定则点击当前位置)
        y: float - Y坐标(可选,不指定则点击当前位置)
        button: str - 按键类型(left/right/middle)
        clicks: int - 点击次数

    返回:
        Dict: 操作结果
            - success: bool - 是否成功
            - error: str - 错误信息(如果失败)
    """
    try:
        import pyautogui

        # 执行点击
        if x is not None and y is not None:
            pyautogui.click(x, y, button=button, clicks=clicks)
            action = f"点击位置 ({x}, {y})"
        else:
            pyautogui.click(button=button, clicks=clicks)
            action = f"点击当前位置({button})"

        return {
            "success": True,
            "action": action,
            "button": button,
            "clicks": clicks
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"鼠标点击失败: {str(e)}"
        }


def baodou_keyboard_type(text: str,
                         interval: float = 0.01) -> Dict[str, Any]:
    """
    键盘输入文本

    参数:
        text: str - 要输入的文本
        interval: float - 每个字符之间的间隔(秒)

    返回:
        Dict: 操作结果
            - success: bool - 是否成功
            - text: str - 输入的文本
            - error: str - 错误信息(如果失败)
    """
    try:
        import pyautogui

        pyautogui.typewrite(text, interval=interval)

        return {
            "success": True,
            "action": f"输入文本: {text}",
            "interval": interval
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"键盘输入失败: {str(e)}"
        }


def baodou_keyboard_press(key: str,
                          presses: int = 1) -> Dict[str, Any]:
    """
    按下键盘按键

    参数:
        key: str - 按键名称(如 'enter', 'ctrl+c', 'alt+f4' 等)
        presses: int - 按压次数

    返回:
        Dict: 操作结果
            - success: bool - 是否成功
            - key: str - 按键
            - error: str - 错误信息(如果失败)
    """
    try:
        import pyautogui

        pyautogui.press(key, presses=presses)

        return {
            "success": True,
            "action": f"按键: {key}",
            "presses": presses
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"键盘操作失败: {str(e)}"
        }


def baodou_launch_gui() -> Dict[str, Any]:
    """
    启动包豆AI独立GUI程序

    返回:
        Dict: 操作结果
            - success: bool - 是否成功
            - message: str - 操作消息
            - error: str - 错误信息(如果失败)
    """
    try:
        # 获取包豆AI GUI路径
        baodou_path = Path(__file__).parent.parent.parent / "baodou_AI"
        gui_script = baodou_path / "pyqt_main.py"

        if not gui_script.exists():
            return {
                "success": False,
                "error": f"包豆AI GUI脚本不存在: {gui_script}"
            }

        # 检查是否已经在运行
        try:
            import psutil
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if isinstance(cmdline, list) and 'pyqt_main.py' in ' '.join(cmdline):
                        return {
                            "success": True,
                            "message": "包豆AI GUI已经在运行中",
                            "note": "如果未显示窗口，请检查任务栏或进程管理器"
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except ImportError:
            pass  # psutil未安装，跳过检查

        # 启动GUI程序（新进程，不阻塞）
        subprocess.Popen(
            [sys.executable, str(gui_script)],
            cwd=str(baodou_path),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )

        return {
            "success": True,
            "message": "包豆AI GUI已启动",
            "note": "请在GUI窗口中输入任务并执行",
            "path": str(gui_script)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"启动包豆AI GUI失败: {str(e)}"
        }


def baodou_send_task(task_description: str, wait_for_completion: bool = False,
                     timeout: int = 60) -> Dict[str, Any]:
    """
    弥娅向包豆GUI发送任务并执行（统一交互界面）

    这个工具实现了弥娅与包豆之间的通信，弥娅可以：
    1. 自动发送任务给包豆GUI
    2. 可选择等待任务完成
    3. 获取任务执行结果

    参数:
        task_description: str - 任务描述，例如"打开浏览器并搜索人工智能"
        wait_for_completion: bool - 是否等待任务完成
            - True: 等待任务执行完成并返回结果
            - False: 立即返回，任务在后台执行
        timeout: int - 等待超时时间（秒），仅在wait_for_completion=True时生效

    返回:
        Dict: 任务执行结果
            - success: bool - 是否成功
            - message: str - 消息
            - result: Any - 执行结果（如果等待完成）
            - task_id: str - 任务ID
            - error: str - 错误信息（如果失败）

    使用示例:
        # 不等待完成
        result = baodou_send_task("打开浏览器", wait_for_completion=False)

        # 等待完成
        result = baodou_send_task("搜索人工智能", wait_for_completion=True, timeout=30)
    """
    try:
        from .baodou_communicator import get_communicator

        communicator = get_communicator()

        # 发送任务到包豆GUI
        result = communicator.send_task_to_baodou(
            task_description=task_description,
            wait_for_completion=wait_for_completion,
            timeout=timeout
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"发送任务到包豆GUI失败: {str(e)}",
            "hint": "请确保包豆GUI已启动且配置正确"
        }


def baodou_check_status() -> Dict[str, Any]:
    """
    检查包豆GUI运行状态

    返回:
        Dict: 状态信息
            - success: bool - 是否成功获取状态
            - gui_running: bool - GUI是否运行
            - launcher_available: bool - 启动器是否可用
            - task_queue_exists: bool - 任务队列是否存在
            - message: str - 状态描述
    """
    try:
        from .baodou_communicator import get_communicator

        communicator = get_communicator()
        status = communicator.check_baodou_status()

        # 生成状态描述
        if status["gui_running"]:
            message = "✅ 包豆GUI正在运行，可以接收任务"
        else:
            message = "⚠️ 包豆GUI未运行，需要先启动GUI"

        return {
            "success": True,
            "message": message,
            **status
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"检查包豆状态失败: {str(e)}"
        }


