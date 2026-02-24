"""
弥娅与包豆GUI通信桥梁模块
实现弥娅向包豆传达任务的功能
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
from .baodou_gui_launcher import get_launcher

# 项目根目录 (从 mcpserver/agent_baodou/ 向上两级到达项目根目录)
PROJECT_ROOT = Path(__file__).parent.parent.parent
BAODOU_PATH = PROJECT_ROOT / "baodou_AI"


class BaodouTaskCommunicator:
    """包豆任务通信器 - 弥娅与包豆GUI之间的桥梁"""

    def __init__(self):
        self.task_queue_file = BAODOU_PATH / "task_queue.json"
        self.response_queue_file = BAODOU_PATH / "task_response.json"
        self.launcher = get_launcher()

    def send_task_to_baodou(self, task_description: str, wait_for_completion: bool = False,
                            timeout: int = 60) -> Dict[str, Any]:
        """向包豆GUI发送任务

        Args:
            task_description: 任务描述
            wait_for_completion: 是否等待任务完成
            timeout: 超时时间（秒）

        Returns:
            Dict: 任务执行结果
                - success: bool - 是否成功
                - message: str - 消息
                - result: Any - 执行结果
                - task_id: str - 任务ID
                - error: str - 错误信息（如果失败）
        """
        try:
            # 检查包豆GUI是否运行
            if not self.launcher.is_running():
                return {
                    "success": False,
                    "error": "包豆GUI未运行，无法执行任务"
                }

            # 创建任务ID（使用数字格式与包豆GUI保持一致）
            task_id = int(time.time() * 1000)

            # 准备任务数据（与包豆GUI TaskQueue格式一致）
            task_data = {
                "id": task_id,
                "task": task_description,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "pending"
            }

            # 写入任务队列文件（包豆GUI期望的任务数组格式）
            try:
                # 确保目录存在
                self.task_queue_file.parent.mkdir(parents=True, exist_ok=True)

                # 先读取现有任务列表
                existing_tasks = []
                if self.task_queue_file.exists():
                    try:
                        with open(self.task_queue_file, 'r', encoding='utf-8') as f:
                            existing_tasks = json.load(f)
                    except:
                        existing_tasks = []

                # 添加新任务
                existing_tasks.append(task_data)

                # 写入文件
                with open(self.task_queue_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_tasks, f, ensure_ascii=False, indent=2)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"写入任务队列失败: {str(e)}"
                }

            print(f"[弥娅->包豆] 发送任务: {task_description}")
            print(f"[弥娅->包豆] 任务ID: {task_id}")

            if not wait_for_completion:
                return {
                    "success": True,
                    "message": "任务已发送到包豆GUI",
                    "task_id": str(task_id)
                }

            # 等待任务完成
            return self._wait_for_task_completion(task_id, timeout)

        except Exception as e:
            return {
                "success": False,
                "error": f"发送任务失败: {str(e)}"
            }

    def _wait_for_task_completion(self, task_id: int, timeout: int) -> Dict[str, Any]:
        """等待任务完成

        Args:
            task_id: 任务ID（数字格式）
            timeout: 超时时间（秒）

        Returns:
            Dict: 任务执行结果
        """
        start_time = time.time()
        check_interval = 0.5  # 每0.5秒检查一次

        while time.time() - start_time < timeout:
            try:
                # 检查任务队列文件中的任务状态
                if self.task_queue_file.exists():
                    with open(self.task_queue_file, 'r', encoding='utf-8') as f:
                        tasks = json.load(f)

                    # 查找目标任务
                    for task in tasks:
                        if task.get("id") == task_id:
                            status = task.get("status")

                            if status == "completed":
                                return {
                                    "success": True,
                                    "message": task.get("result", "任务完成"),
                                    "result": task
                                }
                            elif status == "failed":
                                return {
                                    "success": False,
                                    "error": task.get("error", "任务执行失败")
                                }

                time.sleep(check_interval)

            except Exception as e:
                print(f"[弥娅->包豆] 检查任务状态时出错: {e}")
                time.sleep(check_interval)

        # 超时
        return {
            "success": False,
            "error": f"任务执行超时（等待{timeout}秒）"
        }

    def check_baodou_status(self) -> Dict[str, Any]:
        """检查包豆状态

        Returns:
            Dict: 状态信息
                - gui_running: bool - GUI是否运行
                - launcher_available: bool - 启动器是否可用
                - task_queue_exists: bool - 任务队列是否存在
                - response_queue_exists: bool - 响应队列是否存在
        """
        return {
            "gui_running": self.launcher.is_running(),
            "launcher_available": self.launcher is not None,
            "task_queue_exists": self.task_queue_file.exists(),
            "response_queue_exists": self.response_queue_file.exists()
        }


# 全局通信器实例
_communicator: Optional[BaodouTaskCommunicator] = None


def get_communicator() -> BaodouTaskCommunicator:
    """获取通信器单例"""
    global _communicator
    if _communicator is None:
        _communicator = BaodouTaskCommunicator()
    return _communicator


def initialize_communicator():
    """初始化通信器"""
    global _communicator
    _communicator = BaodouTaskCommunicator()
    return _communicator


def send_task_to_baodou(task_description: str, wait_for_completion: bool = False,
                        timeout: int = 60) -> Dict[str, Any]:
    """便捷函数：向包豆发送任务

    Args:
        task_description: 任务描述
        wait_for_completion: 是否等待任务完成
        timeout: 超时时间（秒）

    Returns:
        Dict: 任务执行结果
    """
    communicator = get_communicator()
    return communicator.send_task_to_baodou(task_description, wait_for_completion, timeout)


def check_baodou_status() -> Dict[str, Any]:
    """便捷函数：检查包豆状态"""
    communicator = get_communicator()
    return communicator.check_baodou_status()
