#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务控制器 - Task Controller
集成到对话系统，处理任务相关的请求
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from system.config import logger
from system.task_scheduler import TaskScheduler, TaskPriority, get_task_scheduler
from system.task_intent_parser import TaskIntent, TaskIntentParser, get_task_intent_parser


class TaskController:
    """任务控制器"""
    
    def __init__(self):
        self._scheduler: TaskScheduler = get_task_scheduler()
        self._parser: TaskIntentParser = get_task_intent_parser()
        self._initialized = False
    
    async def initialize(self):
        """初始化控制器"""
        if self._initialized:
            return
        
        # 启动任务调度器
        await self._scheduler.start()
        
        # 注册默认回调
        self._scheduler.register_callback("reminder", self._on_reminder_triggered)
        self._scheduler.register_callback("routine", self._on_routine_triggered)
        self._scheduler.register_callback("schedule", self._on_schedule_triggered)
        
        self._initialized = True
        logger.info("[任务控制器] 已初始化")
    
    async def shutdown(self):
        """关闭控制器"""
        await self._scheduler.stop()
        self._initialized = False
        logger.info("[任务控制器] 已关闭")
    
    async def process_user_input(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        处理用户输入

        如果检测到任务相关意图，会自动处理并返回响应
        如果不是任务相关，返回None

        返回: {"response": str, "success": bool, ...} 或 None
        """
        # 解析意图
        intent = self._parser.parse(user_input)

        logger.info(f"[任务控制器] 解析意图: 输入='{user_input}', intent={intent}, confidence={intent.confidence if intent else 'N/A'}")

        if not intent or intent.confidence < 0.4:
            return None
        
        logger.info(f"[任务控制器] 检测到任务意图: {intent.intent_type} (置信度: {intent.confidence:.2f})")
        
        # 根据意图执行操作
        try:
            result = await self._execute_intent(intent)
            
            # 生成响应
            response = self._parser.generate_response(intent, result)
            
            return {
                "response": response,
                "success": result.get("success", True),
                "intent_type": intent.intent_type,
                "task_id": intent.task_id,
                "task_title": intent.task_title
            }
        
        except Exception as e:
            logger.error(f"[任务控制器] 处理意图失败: {e}")
            return {
                "response": "抱歉，处理任务时出错了。",
                "success": False,
                "error": str(e)
            }
    
    async def _execute_intent(self, intent: TaskIntent) -> Dict[str, Any]:
        """执行意图"""
        if intent.intent_type == "add_task":
            return await self._add_task(intent)
        
        elif intent.intent_type == "add_reminder":
            return await self._add_task(intent)
        
        elif intent.intent_type == "list_tasks":
            return await self._list_tasks(intent)
        
        elif intent.intent_type == "remove_task":
            return await self._remove_task(intent)
        
        elif intent.intent_type == "toggle_task":
            return await self._toggle_task(intent)
        
        elif intent.intent_type == "clear_tasks":
            return await self._clear_tasks(intent)
        
        return {"success": False, "message": "未知的意图类型"}
    
    async def _add_task(self, intent: TaskIntent) -> Dict[str, Any]:
        """添加任务"""
        if not intent.scheduled_time:
            return {"success": False, "message": "无法确定提醒时间"}

        # 将原始输入（包含QQ号前缀）保存到context中，用于后续发送QQ消息
        context = {
            "source": "dialogue",
            "original_input": getattr(intent, 'original_input', '')
        }

        task_id = self._scheduler.add_task(
            title=intent.task_title or "提醒",
            description=intent.task_description or "",
            task_type=intent.task_type,
            priority=intent.priority,
            scheduled_time=intent.scheduled_time,
            recurring=intent.recurring,
            recurring_interval=intent.recurring_interval,
            context=context
        )

        logger.info(f"[任务控制器] 添加任务成功: {task_id} - {intent.task_title}")

        return {
            "success": True,
            "task_id": task_id,
            "message": f"任务已添加"
        }
    
    async def _list_tasks(self, intent: TaskIntent) -> Dict[str, Any]:
        """列出任务"""
        tasks = self._scheduler.get_all_tasks(include_disabled=True)
        
        logger.info(f"[任务控制器] 列出任务: 共{len(tasks)}个")
        
        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks)
        }
    
    async def _remove_task(self, intent: TaskIntent) -> Dict[str, Any]:
        """移除任务"""
        if not intent.task_id:
            # 尝试根据标题匹配
            tasks = self._scheduler.get_all_tasks()
            for task in tasks:
                if intent.task_title and intent.task_title in task.title:
                    intent.task_id = task.task_id
                    break
        
        if not intent.task_id:
            return {"success": False, "message": "无法确定要移除的任务"}
        
        success = self._scheduler.remove_task(intent.task_id)
        
        if success:
            logger.info(f"[任务控制器] 移除任务成功: {intent.task_id}")
            return {"success": True, "message": "任务已移除"}
        else:
            return {"success": False, "message": "移除任务失败"}
    
    async def _toggle_task(self, intent: TaskIntent) -> Dict[str, Any]:
        """切换任务状态"""
        if not intent.task_id:
            # 尝试根据标题匹配
            tasks = self._scheduler.get_all_tasks()
            for task in tasks:
                if intent.task_title and intent.task_title in task.title:
                    intent.task_id = task.task_id
                    break
        
        if not intent.task_id or intent.enabled is None:
            return {"success": False, "message": "无法确定要操作的任务"}
        
        success = self._scheduler.toggle_task(intent.task_id, intent.enabled)
        
        if success:
            logger.info(f"[任务控制器] 切换任务状态: {intent.task_id} -> {intent.enabled}")
            return {"success": True, "message": "任务状态已更新"}
        else:
            return {"success": False, "message": "操作失败"}
    
    async def _clear_tasks(self, intent: TaskIntent) -> Dict[str, Any]:
        """清除任务"""
        if intent.context.get("clear_all", False):
            # 获取所有任务ID
            tasks = self._scheduler.get_all_tasks()
            task_ids = [t.task_id for t in tasks]
            
            # 移除所有
            for task_id in task_ids:
                self._scheduler.remove_task(task_id)
            
            logger.info(f"[任务控制器] 清除所有任务: 共{len(task_ids)}个")
            
            return {
                "success": True,
                "message": f"已清除{len(task_ids)}个任务"
            }
        else:
            return {"success": False, "message": "请明确是否要清除所有任务"}
    
    # 任务触发回调
    async def _on_reminder_triggered(self, task):
        """提醒任务触发"""
        logger.info(f"[任务控制器] 提醒触发: {task.title}")

        # 通过任务服务管理器发送，支持情境感知
        try:
            from system.task_service_manager import get_task_service_manager
            task_service = get_task_service_manager()

            # 获取原始输入（包含QQ号前缀）
            original_input = task.context.get("original_input", "")
            reminder_content = original_input if original_input else (task.description or task.title)

            # 准备任务上下文
            task_context = {
                "task_id": task.task_id,
                "task_title": task.title,
                "task_description": task.description,
                "task_content": reminder_content,  # 实际的提醒内容
                "scheduled_time": task.scheduled_time.isoformat(),
                "is_recurring": task.recurring,
                "original_input": original_input
            }

            # 检查是否启用了情境感知
            if task_service._context_aware_enabled:
                logger.info(f"[任务控制器] 使用情境感知系统发送提醒: {task.title}")

                # 通过情境感知系统发送
                await task_service.send_context_aware_message(
                    message_type="reminder",
                    task_context=task_context
                )
            else:
                # 降级：直接通过主动交流发送
                logger.info(f"[任务控制器] 情境感知未启用，使用默认方式: {task.title}")

                from system.active_communication import ActiveCommunication
                comm = ActiveCommunication.get_instance()

                await comm.send_message(
                    message=reminder_content,
                    message_type="reminder",
                    context=task_context
                )
        except Exception as e:
            logger.error(f"[任务控制器] 发送提醒失败: {e}")
    
    async def _on_routine_triggered(self, task):
        """例行任务触发"""
        logger.info(f"[任务控制器] 例行任务触发: {task.title}")
        
        # 例行任务的触发逻辑
        # 可以根据任务类型执行不同的操作
    
    async def _on_schedule_triggered(self, task):
        """日程任务触发"""
        logger.info(f"[任务控制器] 日程任务触发: {task.title}")
        
        # 日程任务的触发逻辑
    
    def get_status(self) -> Dict[str, Any]:
        """获取控制器状态"""
        return {
            "initialized": self._initialized,
            "scheduler_status": self._scheduler.get_status(),
            "task_count": len(self._scheduler.get_all_tasks())
        }


# 全局实例
_task_controller: Optional[TaskController] = None


def get_task_controller() -> TaskController:
    """获取任务控制器实例"""
    global _task_controller
    if _task_controller is None:
        _task_controller = TaskController()
    return _task_controller
