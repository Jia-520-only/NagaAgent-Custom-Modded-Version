"""
任务队列系统 - 连接弥娅和包豆GUI的任务桥梁
"""
import json
import os
import time
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from queue import Queue, Empty


class TaskQueue:
    """任务队列管理器"""

    def __init__(self, queue_file: str = "task_queue.json"):
        # 使用脚本所在目录作为基础目录
        script_dir = Path(__file__).parent
        queue_path = Path(queue_file)
        if not queue_path.is_absolute():
            self.queue_file = script_dir / queue_path
        else:
            self.queue_file = queue_path

        self.queue = Queue()
        self._running = False
        self._worker_thread = None
        self._ensure_queue_file()
        
    def _ensure_queue_file(self):
        """确保队列文件存在"""
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.queue_file.exists():
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def add_task(self, task: str) -> Dict[str, Any]:
        """
        添加任务到队列
        
        参数:
            task: 任务描述
            
        返回:
            Dict: 操作结果
        """
        try:
            task_data = {
                "id": int(time.time() * 1000),
                "task": task,
                "status": "pending",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 写入文件
            tasks = self._load_tasks()
            tasks.append(task_data)
            self._save_tasks(tasks)
            
            # 同时添加到内存队列
            self.queue.put(task_data)
            
            return {
                "success": True,
                "task_id": task_data["id"],
                "message": f"任务已添加到队列: {task[:50]}..."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"添加任务失败: {str(e)}"
            }
    
    def get_pending_tasks(self) -> list:
        """获取待处理任务列表(排除正在运行的任务)"""
        return [task for task in self._load_tasks() if task["status"] == "pending"]
    
    def mark_task_started(self, task_id: int) -> bool:
        """标记任务开始执行"""
        tasks = self._load_tasks()
        for task in tasks:
            if task["id"] == task_id:
                task["status"] = "running"
                task["start_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                self._save_tasks(tasks)
                return True
        return False
    
    def mark_task_completed(self, task_id: int, result: str = "") -> bool:
        """标记任务完成"""
        tasks = self._load_tasks()
        for task in tasks:
            if task["id"] == task_id:
                task["status"] = "completed"
                task["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                if result:
                    task["result"] = result
                # 自动清理已完成的任务,防止阻塞新任务
                tasks = [t for t in tasks if t["status"] not in ["completed", "failed"]]
                self._save_tasks(tasks)
                print(f"[任务队列] 任务 {task_id} 已完成并已清理")
                return True
        return False
    
    def mark_task_failed(self, task_id: int, error: str) -> bool:
        """标记任务失败"""
        tasks = self._load_tasks()
        for task in tasks:
            if task["id"] == task_id:
                task["status"] = "failed"
                task["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                task["error"] = error
                # 自动清理已失败的任务,防止阻塞新任务
                tasks = [t for t in tasks if t["status"] not in ["completed", "failed"]]
                self._save_tasks(tasks)
                print(f"[任务队列] 任务 {task_id} 已失败并已清理: {error}")
                return True
        return False
    
    def _load_tasks(self) -> list:
        """从文件加载任务列表"""
        try:
            if self.queue_file.exists():
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载任务队列失败: {e}")
        return []
    
    def _save_tasks(self, tasks: list):
        """保存任务列表到文件"""
        try:
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存任务队列失败: {e}")
    
    def clear_completed_tasks(self):
        """清理已完成的任务"""
        tasks = self._load_tasks()
        tasks = [task for task in tasks if task["status"] in ["pending", "running"]]
        self._save_tasks(tasks)

    def get_running_tasks(self) -> list:
        """获取正在运行的任务列表"""
        return [task for task in self._load_tasks() if task["status"] == "running"]


# 全局任务队列实例
_task_queue = None

def get_task_queue() -> TaskQueue:
    """获取全局任务队列实例"""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue
