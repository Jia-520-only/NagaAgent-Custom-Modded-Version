#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务意图解析器 - Task Intent Parser
解析对话中的任务配置意图
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from system.config import logger
from system.temporal_perception import get_temporal_perception
from system.task_scheduler import TaskScheduler, TaskPriority, get_task_scheduler


@dataclass
class TaskIntent:
    """任务意图"""
    intent_type: str  # "add_task", "list_tasks", "remove_task", "toggle_task", "clear_tasks"
    task_title: Optional[str] = None
    task_description: Optional[str] = None
    task_type: str = "reminder"
    priority: TaskPriority = TaskPriority.MEDIUM
    scheduled_time: Optional[datetime] = None
    recurring: bool = False
    recurring_interval: Optional[timedelta] = None
    task_id: Optional[str] = None
    enabled: Optional[bool] = None
    confidence: float = 0.0
    original_input: str = ""  # 原始输入（包含QQ号前缀）


class TaskIntentParser:
    """任务意图解析器"""
    
    def __init__(self):
        self._temporal = get_temporal_perception()
        self._scheduler = get_task_scheduler()
        
        # 意图正则表达式
        self._intent_patterns = {
            # 添加任务
            "add_reminder": [
                r'(?:\d+\s*(?:秒|分钟|min|小时|hour)(?:后|之))提醒我?(.+)',  # 30秒后提醒我喝水
                r'(?:每\s*\d+\s*(?:分钟|min|小时|hour))提醒我?(.+)',  # 每30分钟提醒我喝水
                r'提醒我?(.+?)(?:在|到)?(?:\d+\s*(?:秒|分钟|min|小时|hour)(?:后|之)|每\s*\d+\s*(?:分钟|min|小时|hour))',
                r'(.+?)时(?:候)?(?:提醒|记得)',
                r'(?:帮我|请)?(?:设置|添加|建个)?(?:提醒|闹钟)(?:来)?(.+)',
            ],
            
            # 列出任务
            "list_tasks": [
                r'查看(我)?的?(?:提醒|任务|日程|计划)',
                r'有什么(提醒|任务|日程|计划)',
                r'(显示|列出)(我)?的?(?:提醒|任务)',
            ],
            
            # 移除任务
            "remove_task": [
                r'(?:删除|移除|取消)(?:提醒|任务)(?:\d+号)?',
                r'不要(?:提醒|记住)(.+)',
            ],
            
            # 启用/禁用任务
            "toggle_task": [
                r'(?:暂停|停止)(?:提醒|任务)',
                r'(?:恢复|开启|启用)(?:提醒|任务)',
            ],
            
            # 清除任务
            "clear_tasks": [
                r'清除(?:所有)?(?:提醒|任务)',
                r'删除(?:所有)?(?:提醒|任务)',
            ],
        }
        
        # 时间正则（委托给时间感知系统）
        self._time_patterns = {
            "in_seconds": r'(\d+)\s*(?:秒|second|sec)[后之]?|(?:在|到)\s*(\d+)\s*(?:秒|second|sec)',
            "in_minutes": r'(\d+)\s*(?:分钟|min)[后之]?|(?:在|到)\s*(\d+)\s*(?:分钟|min)',
            "in_hours": r'(\d+)\s*(?:小时|hour)[后之]?|(?:在|到)\s*(\d+)\s*(?:小时|hour)',
            "every_minutes": r'每\s*(\d+)\s*(?:分钟|min)',
            "every_hours": r'每\s*(\d+)\s*(?:小时|hour)',
            "daily": r'每天\s*(\d{1,2})[:：](\d{2})',
            "at_time": r'(\d{1,2})[:：](\d{2})',
        }
        
        # 关键词
        self._priority_keywords = {
            "重要": TaskPriority.HIGH,
            "紧急": TaskPriority.HIGH,
            "一定要": TaskPriority.HIGH,
            "记得": TaskPriority.HIGH,
            "别忘了": TaskPriority.HIGH,
            "可能": TaskPriority.LOW,
            "有空": TaskPriority.LOW,
        }
    
    def parse(self, text: str) -> Optional[TaskIntent]:
        """
        解析用户输入，提取任务意图

        返回: TaskIntent 或 None（如果不是任务相关意图）
        """
        text = text.strip()

        # 检测意图类型
        intent_type, confidence = self._detect_intent_type(text)

        if not intent_type or confidence < 0.4:
            return None

        # 保存原始输入（包含QQ号前缀）
        intent = TaskIntent(intent_type=intent_type, confidence=confidence, original_input=text)

        # 根据意图类型解析详细信息
        if intent_type in ("add_task", "add_reminder"):
            self._parse_add_task(text, intent)
        elif intent_type == "list_tasks":
            self._parse_list_tasks(text, intent)
        elif intent_type == "remove_task":
            self._parse_remove_task(text, intent)
        elif intent_type == "toggle_task":
            self._parse_toggle_task(text, intent)
        elif intent_type == "clear_tasks":
            self._parse_clear_tasks(text, intent)

        return intent
    
    def _detect_intent_type(self, text: str) -> Tuple[Optional[str], float]:
        """检测意图类型"""
        scores = {}
        
        # 检查每个意图模式
        for intent_type, patterns in self._intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 1
            if score > 0:
                scores[intent_type] = score

        if not scores:
            return None, 0.0

        # 返回得分最高的意图
        best_intent = max(scores.keys(), key=lambda k: scores[k])
        # 改进置信度计算：至少匹配2个模式给0.6，1个模式给0.4
        base_confidence = scores[best_intent] * 0.4
        confidence = min(base_confidence + 0.2, 1.0)  # 最低0.6

        return best_intent, confidence
    
    def _parse_add_task(self, text: str, intent: TaskIntent):
        """解析添加任务意图"""
        # 解析时间信息
        logger.debug(f"[任务意图] 开始解析时间: {text}")
        scheduled_time, recurring_interval, time_desc = self._temporal.parse_time_from_text(text)
        logger.debug(f"[任务意图] 时间解析结果: scheduled_time={scheduled_time}, recurring_interval={recurring_interval}, time_desc={time_desc}")

        intent.scheduled_time = scheduled_time
        intent.recurring_interval = recurring_interval
        intent.recurring = recurring_interval is not None

        # 提取任务标题和描述
        # 移除时间相关词语
        cleaned_text = text
        for pattern in self._time_patterns.values():
            cleaned_text = re.sub(pattern, '', cleaned_text)

        # 移除系统前缀（如 [发送者QQ:xxx]）
        cleaned_text = re.sub(r'\[发送者QQ:\d+\]\s*', '', cleaned_text)

        # 移除关键词
        keywords_to_remove = ['提醒', '记得', '帮我', '设置', '添加', '建个', '闹钟', '在', '到']
        for keyword in keywords_to_remove:
            cleaned_text = cleaned_text.replace(keyword, '')

        cleaned_text = cleaned_text.strip()

        if cleaned_text:
            intent.task_title = cleaned_text[:50]  # 限制标题长度
            intent.task_description = cleaned_text

        # 如果没有明确的标题，使用默认标题
        if not intent.task_title:
            if intent.recurring:
                intent.task_title = f"循环提醒 - {time_desc}"
            else:
                intent.task_title = f"提醒 - {time_desc if time_desc else '定时任务'}"

        # 检测优先级
        for keyword, priority in self._priority_keywords.items():
            if keyword in text:
                intent.priority = priority
                break

        logger.debug(f"[任务意图] 添加任务: {intent.task_title} @ {scheduled_time}")
    
    def _parse_list_tasks(self, text: str, intent: TaskIntent):
        """解析列出任务意图"""
        # 这个操作不需要额外信息
        logger.debug("[任务意图] 列出任务")
    
    def _parse_remove_task(self, text: str, intent: TaskIntent):
        """解析移除任务意图"""
        # 尝试提取任务ID（如果是数字）
        match = re.search(r'(\d+)号?|(?:第)(\d+)', text)
        if match:
            num = match.group(1) or match.group(2)
            # 获取任务列表并按索引查找
            tasks = self._scheduler.get_all_tasks()
            try:
                index = int(num) - 1
                if 0 <= index < len(tasks):
                    intent.task_id = tasks[index].task_id
                    intent.task_title = tasks[index].title
            except (ValueError, IndexError):
                pass
        
        # 或者提取任务标题
        if not intent.task_id:
            # 简单的文本匹配
            tasks = self._scheduler.get_all_tasks()
            for task in tasks:
                if task.title in text or task.description in text:
                    intent.task_id = task.task_id
                    intent.task_title = task.title
                    break
        
        logger.debug(f"[任务意图] 移除任务: {intent.task_id}")
    
    def _parse_toggle_task(self, text: str, intent: TaskIntent):
        """解析启用/禁用任务意图"""
        # 检测是启用还是禁用
        if re.search(r'暂停|停止|关闭', text):
            intent.enabled = False
        elif re.search(r'恢复|开启|启用|开始', text):
            intent.enabled = True
        
        # 提取任务
        match = re.search(r'(\d+)号?|(?:第)(\d+)', text)
        if match:
            num = match.group(1) or match.group(2)
            tasks = self._scheduler.get_all_tasks()
            try:
                index = int(num) - 1
                if 0 <= index < len(tasks):
                    intent.task_id = tasks[index].task_id
                    intent.task_title = tasks[index].title
            except (ValueError, IndexError):
                pass
        
        logger.debug(f"[任务意图] 切换任务: {intent.task_id} -> {intent.enabled}")
    
    def _parse_clear_tasks(self, text: str, intent: TaskIntent):
        """解析清除任务意图"""
        # 检查是否是"所有"
        if re.search(r'所有|全部', text):
            intent.context = {"clear_all": True}
        else:
            intent.context = {"clear_all": False}
        
        logger.debug("[任务意图] 清除任务")
    
    def generate_response(self, intent: TaskIntent, result: Dict[str, Any]) -> str:
        """
        生成自然语言响应

        参数:
            intent: 任务意图
            result: 执行结果
        """
        if not result.get("success", False):
            return result.get("message", "抱歉，处理任务时出错了。")

        if intent.intent_type in ("add_task", "add_reminder"):
            time_str = self._format_time(intent.scheduled_time)
            task_title = intent.task_title or "提醒"

            # 如果任务标题以"我"开头，调整为更自然的表述
            if task_title.startswith("我"):
                # 移除"我"，改用其他表述
                if intent.recurring:
                    return f"好的，{time_str}我会提醒你{task_title[1:]}。"
                else:
                    return f"好的，{time_str}我会提醒你{task_title[1:]}。"
            else:
                if intent.recurring:
                    return f"好的，我已经设置了{task_title}，会在{self._format_interval(intent.recurring_interval)}提醒你。"
                else:
                    return f"好的，我已经设置了{task_title}，会在{time_str}提醒你。"

        elif intent.intent_type == "list_tasks":
            tasks = result.get("tasks", [])
            if not tasks:
                return "目前没有设置任何提醒任务哦。"

            response = "这是你设置的提醒任务：\n"
            for i, task in enumerate(tasks, 1):
                time_str = self._format_time(task.scheduled_time)
                status = "（已暂停）" if not task.enabled else ""
                if task.recurring:
                    interval_str = self._format_interval(task.recurring_interval)
                    response += f"{i}. {task.title} - 每{interval_str}{status}\n"
                else:
                    response += f"{i}. {task.title} - {time_str}{status}\n"
            return response

        elif intent.intent_type == "remove_task":
            return f"好的，已经移除了{intent.task_title}的提醒。"

        elif intent.intent_type == "toggle_task":
            action = "暂停" if intent.enabled == False else "恢复"
            return f"好的，已经{action}了{intent.task_title}的提醒。"

        elif intent.intent_type == "clear_tasks":
            if intent.context.get("clear_all", False):
                return "好的，已经清除了所有提醒任务。"
            else:
                return "好的，已经清除了提醒任务。"

        return "好的，我已经处理了你的请求。"
    
    def _format_time(self, dt: Optional[datetime]) -> str:
        """格式化时间"""
        if not dt:
            return "稍后"
        
        now = datetime.now()
        diff = dt - now
        
        if diff.total_seconds() < 60:
            return "马上"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}分钟后"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}小时后"
        elif diff.total_seconds() < 172800:
            return f"明天{dt.hour:02d}:{dt.minute:02d}"
        else:
            return dt.strftime("%m月%d日 %H:%M")
    
    def _format_interval(self, interval: timedelta) -> str:
        """格式化时间间隔"""
        total_seconds = interval.total_seconds()
        
        if total_seconds < 3600:
            minutes = int(total_seconds / 60)
            return f"{minutes}分钟"
        elif total_seconds < 86400:
            hours = int(total_seconds / 3600)
            return f"{hours}小时"
        else:
            days = int(total_seconds / 86400)
            return f"{days}天"


# 全局实例
_task_intent_parser: Optional[TaskIntentParser] = None


def get_task_intent_parser() -> TaskIntentParser:
    """获取任务意图解析器实例"""
    global _task_intent_parser
    if _task_intent_parser is None:
        _task_intent_parser = TaskIntentParser()
    return _task_intent_parser
