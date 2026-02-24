#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务调度系统 - Task Scheduler
管理定时提醒和任务调度
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from system.config import config, logger
from system.temporal_perception import (
    TemporalPerception, TemporalEvent, get_temporal_perception,
    TimeUnit
)


class TaskPriority(Enum):
    """任务优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    TRIGGERED = "triggered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """定时任务"""
    task_id: str
    title: str
    description: str
    task_type: str  # "reminder", "routine", "schedule", "custom"
    priority: TaskPriority
    scheduled_time: datetime
    recurring: bool = False
    recurring_interval: Optional[timedelta] = None
    status: TaskStatus = TaskStatus.PENDING
    enabled: bool = True
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    triggered_at: Optional[datetime] = None
    last_executed: Optional[datetime] = None
    execution_count: int = 0


class TaskScheduler:
    """任务调度系统"""
    
    def __init__(self):
        self._temporal: TemporalPerception = get_temporal_perception()
        self._tasks: Dict[str, ScheduledTask] = {}
        self._task_callbacks: Dict[str, List[Callable]] = {}
        self._running = False
        self._check_task = None
        
        # 配置文件路径
        self._config_path = Path(__file__).parent / "tasks_config.json"
        
        # 加载已保存的任务
        self._load_tasks()
    
    def _load_tasks(self):
        """从配置文件加载任务"""
        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    for task_data in data.get("tasks", []):
                        # 转换为ScheduledTask
                        task = self._deserialize_task(task_data)
                        self._tasks[task.task_id] = task
                    
                    logger.info(f"[任务调度] 加载了 {len(self._tasks)} 个任务")
            except Exception as e:
                logger.error(f"[任务调度] 加载任务失败: {e}")
    
    def _save_tasks(self):
        """保存任务到配置文件"""
        try:
            data = {
                "tasks": [self._serialize_task(task) for task in self._tasks.values()],
                "saved_at": datetime.now().isoformat()
            }
            
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"[任务调度] 保存了 {len(self._tasks)} 个任务")
        except Exception as e:
            logger.error(f"[任务调度] 保存任务失败: {e}")
    
    def _serialize_task(self, task: ScheduledTask) -> Dict[str, Any]:
        """序列化任务"""
        return {
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "task_type": task.task_type,
            "priority": task.priority.value,
            "scheduled_time": task.scheduled_time.isoformat(),
            "recurring": task.recurring,
            "recurring_interval": task.recurring_interval.total_seconds() if task.recurring_interval else None,
            "status": task.status.value,
            "enabled": task.enabled,
            "context": task.context,
            "created_at": task.created_at.isoformat(),
            "triggered_at": task.triggered_at.isoformat() if task.triggered_at else None,
            "last_executed": task.last_executed.isoformat() if task.last_executed else None,
            "execution_count": task.execution_count
        }
    
    def _deserialize_task(self, data: Dict[str, Any]) -> ScheduledTask:
        """反序列化任务"""
        return ScheduledTask(
            task_id=data["task_id"],
            title=data["title"],
            description=data["description"],
            task_type=data["task_type"],
            priority=TaskPriority(data["priority"]),
            scheduled_time=datetime.fromisoformat(data["scheduled_time"]),
            recurring=data["recurring"],
            recurring_interval=timedelta(seconds=data["recurring_interval"]) if data.get("recurring_interval") else None,
            status=TaskStatus(data.get("status", "pending")),
            enabled=data.get("enabled", True),
            context=data.get("context", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            triggered_at=datetime.fromisoformat(data["triggered_at"]) if data.get("triggered_at") else None,
            last_executed=datetime.fromisoformat(data["last_executed"]) if data.get("last_executed") else None,
            execution_count=data.get("execution_count", 0)
        )
    
    async def start(self):
        """启动任务调度器"""
        if self._running:
            return

        self._running = True

        # 启动检查循环（独立的时间检查，不依赖TemporalPerception的事件系统）
        self._check_task = asyncio.create_task(self._scheduler_loop())

        logger.info("[任务调度] 已启动")
    
    async def stop(self):
        """停止任务调度器"""
        self._running = False

        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass

        # 保存任务
        self._save_tasks()

        logger.info("[任务调度] 已停止")
    
    async def _scheduler_loop(self):
        """调度循环"""
        while self._running:
            try:
                # 检查到期的任务
                due_tasks = self._get_due_tasks()
                
                for task in due_tasks:
                    await self._execute_task(task)
                
                # 休眠
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"[任务调度] 调度错误: {e}")
                await asyncio.sleep(30)
    
    def _get_due_tasks(self) -> List[ScheduledTask]:
        """获取到期的任务"""
        now = datetime.now()
        due_tasks = []

        logger.debug(f"[任务调度] 检查到期任务 - 当前时间: {now}, 任务总数: {len(self._tasks)}")

        for task in self._tasks.values():
            if not task.enabled or task.status != TaskStatus.PENDING:
                logger.debug(f"[任务调度] 跳过任务: {task.title} (enabled={task.enabled}, status={task.status.value})")
                continue

            time_diff = (task.scheduled_time - now).total_seconds()
            logger.debug(f"[任务调度] 任务 {task.title}: 计划时间={task.scheduled_time}, 差值={time_diff}秒")

            if task.scheduled_time <= now:
                logger.info(f"[任务调度] 发现到期任务: {task.title}")
                due_tasks.append(task)

        # 按优先级排序
        priority_order = {TaskPriority.HIGH: 0, TaskPriority.MEDIUM: 1, TaskPriority.LOW: 2}
        due_tasks.sort(key=lambda t: priority_order[t.priority])

        return due_tasks
    
    async def _execute_task(self, task: ScheduledTask):
        """执行任务"""
        logger.info(f"[任务调度] 执行任务: {task.title}")
        
        try:
            # 更新状态
            task.status = TaskStatus.TRIGGERED
            task.triggered_at = datetime.now()
            task.execution_count += 1
            
            # 执行回调
            await self._trigger_callbacks(task)
            
            # 更新为已完成
            task.status = TaskStatus.COMPLETED
            task.last_executed = datetime.now()
            
            # 处理循环任务
            if task.recurring and task.recurring_interval:
                # 重新调度
                task.scheduled_time = task.scheduled_time + task.recurring_interval
                task.status = TaskStatus.PENDING

                # 确保新时间在未来
                now = datetime.now()
                while task.scheduled_time <= now:
                    task.scheduled_time += task.recurring_interval

                logger.info(f"[任务调度] 循环任务重新调度: {task.title} @ {task.scheduled_time}")
            else:
                # 一次性任务，标记为完成并删除
                logger.info(f"[任务调度] 一次性任务完成，正在删除: {task.title}")
                self.remove_task(task.task_id)
                return  # 提前返回，不需要再保存任务
            
            # 保存任务
            self._save_tasks()
            
        except Exception as e:
            logger.error(f"[任务调度] 执行任务失败: {task.title}: {e}")
            task.status = TaskStatus.PENDING  # 重置为待执行，稍后重试
    
    async def _trigger_callbacks(self, task: ScheduledTask):
        """触发任务回调"""
        callbacks = self._task_callbacks.get(task.task_type, [])
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(task)
                else:
                    callback(task)
            except Exception as e:
                logger.error(f"[任务调度] 回调执行失败: {e}")
    
    def _on_temporal_event(self, event: TemporalEvent):
        """时间事件触发（由时间感知系统调用）"""
        logger.debug(f"[任务调度] 收到时间事件: {event.title}")
    
    def add_task(self, 
                title: str, 
                description: str,
                task_type: str = "reminder",
                priority: TaskPriority = TaskPriority.MEDIUM,
                scheduled_time: Optional[datetime] = None,
                recurring: bool = False,
                recurring_interval: Optional[timedelta] = None,
                context: Optional[Dict[str, Any]] = None) -> str:
        """
        添加定时任务
        
        参数:
            title: 任务标题
            description: 任务描述
            task_type: 任务类型
            priority: 优先级
            scheduled_time: 计划时间（默认为当前时间）
            recurring: 是否循环
            recurring_interval: 循环间隔
            context: 附加上下文
        
        返回: 任务ID
        """
        if scheduled_time is None:
            scheduled_time = datetime.now()
        
        task_id = f"task_{int(datetime.now().timestamp() * 1000)}"
        
        task = ScheduledTask(
            task_id=task_id,
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            scheduled_time=scheduled_time,
            recurring=recurring,
            recurring_interval=recurring_interval,
            status=TaskStatus.PENDING,
            enabled=True,
            context=context or {}
        )
        
        self._tasks[task_id] = task
        self._save_tasks()
        
        logger.info(f"[任务调度] 添加任务: {title} @ {scheduled_time}")
        
        return task_id
    
    def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        if task_id in self._tasks:
            task = self._tasks.pop(task_id)
            self._save_tasks()
            logger.info(f"[任务调度] 移除任务: {task.title}")
            return True
        return False
    
    def toggle_task(self, task_id: str, enabled: bool) -> bool:
        """启用/禁用任务"""
        if task_id in self._tasks:
            self._tasks[task_id].enabled = enabled
            self._save_tasks()
            logger.info(f"[任务调度] 任务 {self._tasks[task_id].title} 已{'启用' if enabled else '禁用'}")
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取任务"""
        return self._tasks.get(task_id)
    
    def get_all_tasks(self, include_disabled: bool = False) -> List[ScheduledTask]:
        """获取所有任务"""
        tasks = list(self._tasks.values())
        
        if not include_disabled:
            tasks = [t for t in tasks if t.enabled]
        
        # 按时间排序
        tasks.sort(key=lambda t: t.scheduled_time)
        
        return tasks
    
    def get_upcoming_tasks(self, limit: int = 10) -> List[ScheduledTask]:
        """获取即将到来的任务"""
        now = datetime.now()
        upcoming = [
            t for t in self._tasks.values()
            if t.enabled and t.status == TaskStatus.PENDING and t.scheduled_time > now
        ]
        
        # 按时间排序
        upcoming.sort(key=lambda t: t.scheduled_time)
        
        return upcoming[:limit]
    
    def register_callback(self, task_type: str, callback: Callable):
        """注册任务回调
        
        当任务执行时会调用这个回调函数
        回调签名: async def callback(task: ScheduledTask)
        """
        if task_type not in self._task_callbacks:
            self._task_callbacks[task_type] = []
        
        self._task_callbacks[task_type].append(callback)
        logger.info(f"[任务调度] 注册回调: {task_type}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        now = datetime.now()
        
        return {
            "running": self._running,
            "total_tasks": len(self._tasks),
            "enabled_tasks": len([t for t in self._tasks.values() if t.enabled]),
            "pending_tasks": len([t for t in self._tasks.values() if t.status == TaskStatus.PENDING and t.enabled]),
            "upcoming_tasks": len(self.get_upcoming_tasks()),
            "due_tasks": len(self._get_due_tasks()),
            "registered_callbacks": {k: len(v) for k, v in self._task_callbacks.items()},
            "current_time": now.isoformat(),
            "next_task_time": self.get_upcoming_tasks(1)[0].scheduled_time.isoformat() if self.get_upcoming_tasks(1) else None
        }


# 全局实例
_task_scheduler: Optional[TaskScheduler] = None


def get_task_scheduler() -> TaskScheduler:
    """获取任务调度器实例"""
    global _task_scheduler
    if _task_scheduler is None:
        _task_scheduler = TaskScheduler()
    return _task_scheduler
