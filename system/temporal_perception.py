#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时间感知系统 - Temporal Perception
扩展后端意识，提供时间相关的感知能力
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import re

from system.config import config, logger


class TimeUnit(Enum):
    """时间单位"""
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class TimeContext(Enum):
    """时间上下文"""
    EARLY_MORNING = "early_morning"  # 5-8点
    MORNING = "morning"               # 8-12点
    NOON = "noon"                    # 12-14点
    AFTERNOON = "afternoon"           # 14-18点
    EVENING = "evening"               # 18-22点
    NIGHT = "night"                   # 22-24点
    LATE_NIGHT = "late_night"         # 0-5点


@dataclass
class TemporalEvent:
    """时间事件"""
    event_id: str
    event_type: str  # "reminder", "routine", "schedule", "deadline"
    title: str
    description: str
    scheduled_time: datetime
    recurring: bool = False
    recurring_interval: Optional[timedelta] = None
    enabled: bool = True
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TimeAwareness:
    """时间感知状态"""
    current_time: datetime
    time_context: TimeContext
    hour: int
    minute: int
    weekday: int
    is_weekend: bool
    time_of_day: str
    day_period: str
    season: str
    year: int
    month: int
    day: int


class TemporalPerception:
    """时间感知系统"""
    
    def __init__(self):
        self._current_state: Optional[TimeAwareness] = None
        self._events: List[TemporalEvent] = []
        self._event_check_interval = 10  # 秒
        self._running = False
        self._check_task = None
        
        # 时间正则表达式
        # 中文数字映射
        self._chinese_numbers = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '两': 2, '半': 0.5
        }

        self._time_patterns = {
            "in_seconds": re.compile(r'(\d+)\s*秒后|(\d+)\s*秒之后'),
            "in_minutes": re.compile(r'(\d+)\s*分钟后|(\d+)\s*分钟之后'),
            "in_hours": re.compile(r'(\d+)\s*小时后|(\d+)\s*小时之后'),
            "at_time": re.compile(r'(\d{1,2})[:：](\d{2})'),
            "every_interval": re.compile(r'每\s*(\d+)\s*(秒|分钟|小时|天)'),
            "daily": re.compile(r'每天\s*(\d{1,2})[:：](\d{2})'),
        }
        
        self.update_state()
    
    def update_state(self) -> TimeAwareness:
        """更新时间感知状态"""
        now = datetime.now()
        
        # 时间上下文
        hour = now.hour
        if 5 <= hour < 8:
            context = TimeContext.EARLY_MORNING
            time_of_day = "早晨"
        elif 8 <= hour < 12:
            context = TimeContext.MORNING
            time_of_day = "上午"
        elif 12 <= hour < 14:
            context = TimeContext.NOON
            time_of_day = "中午"
        elif 14 <= hour < 18:
            context = TimeContext.AFTERNOON
            time_of_day = "下午"
        elif 18 <= hour < 22:
            context = TimeContext.EVENING
            time_of_day = "晚上"
        elif 22 <= hour < 24:
            context = TimeContext.NIGHT
            time_of_day = "夜间"
        else:
            context = TimeContext.LATE_NIGHT
            time_of_day = "深夜"
        
        # 白天/黑夜
        day_period = "白天" if 6 <= hour < 19 else "黑夜"
        
        # 季节
        month = now.month
        if month in [12, 1, 2]:
            season = "冬季"
        elif month in [3, 4, 5]:
            season = "春季"
        elif month in [6, 7, 8]:
            season = "夏季"
        else:
            season = "秋季"
        
        # 构建状态
        self._current_state = TimeAwareness(
            current_time=now,
            time_context=context,
            hour=hour,
            minute=now.minute,
            weekday=now.weekday(),
            is_weekend=now.weekday() >= 5,
            time_of_day=time_of_day,
            day_period=day_period,
            season=season,
            year=now.year,
            month=month,
            day=now.day
        )
        
        logger.debug(f"[时间感知] 更新: {self._get_time_description()}")
        
        return self._current_state
    
    def _get_time_description(self) -> str:
        """获取时间描述（用于日志）"""
        if not self._current_state:
            return "未知"
        
        state = self._current_state
        return f"{state.season} {state.time_of_day} {state.hour:02d}:{state.minute:02d}"
    
    def get_state(self) -> Optional[TimeAwareness]:
        """获取当前时间状态"""
        return self._current_state
    
    def get_context_description(self) -> str:
        """获取时间上下文描述（用于前端意识）"""
        if not self._current_state:
            return ""
        
        state = self._current_state
        
        # 自然语言描述
        descriptions = []
        
        # 时间段
        if state.time_context in [TimeContext.EARLY_MORNING, TimeContext.LATE_NIGHT]:
            descriptions.append(f"现在是{state.time_of_day}")
            if state.time_context == TimeContext.LATE_NIGHT:
                descriptions.append("夜深了")
        elif state.time_context == TimeContext.NOON:
            descriptions.append(f"{state.time_of_day}休息时间")
        else:
            descriptions.append(f"{state.season}{state.time_of_day}")
        
        # 周末
        if state.is_weekend:
            descriptions.append("今天是周末")
        
        # 具体时间
        descriptions.append(f"{state.hour:02d}点{state.minute:02d}分")
        
        return "，".join(descriptions)
    
    def parse_time_from_text(self, text: str) -> Tuple[Optional[datetime], Optional[timedelta], str]:
        """
        从文本中解析时间

        返回: (scheduled_time, recurring_interval, description)
        """
        logger.debug(f"[时间感知] 开始解析: {text}")
        now = datetime.now()
        scheduled_time = None
        recurring_interval = None
        description = ""

        # 辅助函数：将中文数字转换为阿拉伯数字
        def convert_chinese_number(num_str: str) -> Optional[int]:
            """将中文数字转换为阿拉伯数字"""
            result = 0
            temp = 0
            for char in num_str:
                if char in self._chinese_numbers:
                    val = self._chinese_numbers[char]
                    if char == '十' and temp == 0:
                        result += 10
                    elif char == '十':
                        result += val + temp
                        temp = 0
                    else:
                        temp = val
                else:
                    # 可能是混合，如"15"这种数字
                    try:
                        return int(num_str)
                    except:
                        return None
            return result + temp

        # 辅助函数：从匹配中提取数字（支持中文数字）
        def extract_number(match, group_index: int = 1) -> Optional[int]:
            """从正则匹配中提取数字"""
            num_str = match.group(group_index)
            if num_str:
                if num_str.isdigit():
                    return int(num_str)
                else:
                    return convert_chinese_number(num_str)
            return None

        # 1. 优先匹配 "每X秒/分钟/小时"（循环任务）
        match = self._time_patterns["every_interval"].search(text)
        if match:
            num_str = match.group(1)
            unit = match.group(2)

            # 尝试转换数字（支持中文数字）
            interval = int(num_str) if num_str.isdigit() else convert_chinese_number(num_str)
            if interval is None:
                interval = 1  # 默认值

            if unit == "秒":
                recurring_interval = timedelta(seconds=interval)
                description = f"每{interval}秒"
            elif unit == "分钟":
                recurring_interval = timedelta(minutes=interval)
                description = f"每{interval}分钟"
            elif unit == "小时":
                recurring_interval = timedelta(hours=interval)
                description = f"每{interval}小时"
            elif unit == "天":
                recurring_interval = timedelta(days=interval)
                description = f"每{interval}天"

            scheduled_time = now + recurring_interval
            logger.debug(f"[时间感知] 循环任务: {description}")
            return scheduled_time, recurring_interval, description

        # 2. 匹配相对时间（X秒/分钟/小时后），支持中文数字
        # 先尝试阿拉伯数字，如果失败再尝试中文数字
        time_matchers = [
            ("秒", "in_seconds", lambda n: timedelta(seconds=n)),
            ("分钟", "in_minutes", lambda n: timedelta(minutes=n)),
            ("小时", "in_hours", lambda n: timedelta(hours=n)),
        ]

        for unit_name, pattern_key, td_func in time_matchers:
            # 尝试阿拉伯数字
            match = self._time_patterns[pattern_key].search(text)
            if not match:
                # 尝试中文数字模式
                chinese_pattern = re.compile(f'([一二三四五六七八九十两半]+)\\s*{unit_name}后|([一二三四五六七八九十两半]+)\\s*{unit_name}之后')
                match = chinese_pattern.search(text)

            if match:
                num = extract_number(match, 1) or extract_number(match, 2)
                if num is not None:
                    scheduled_time = now + td_func(num)
                    description = f"{num}{unit_name}后"
                    logger.debug(f"[时间感知] 相对时间匹配: {description}")
                    return scheduled_time, recurring_interval, description

        # 3. 匹配 "每天HH:MM"
        match = self._time_patterns["daily"].search(text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))

            # 计算今天或明天的这个时间
            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if scheduled_time <= now:
                scheduled_time += timedelta(days=1)

            recurring_interval = timedelta(days=1)
            description = f"每天{hour:02d}:{minute:02d}"
            return scheduled_time, recurring_interval, description

        # 匹配 "HH:MM"
        match = self._time_patterns["at_time"].search(text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))

            # 计算今天或明天的这个时间
            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if scheduled_time <= now:
                scheduled_time += timedelta(days=1)

            description = f"{hour:02d}:{minute:02d}"
            return scheduled_time, recurring_interval, description

        return scheduled_time, recurring_interval, description
    
    def add_event(self, event: TemporalEvent) -> str:
        """添加时间事件"""
        event_id = event.event_id or self._generate_event_id()
        event.event_id = event_id
        
        self._events.append(event)
        logger.info(f"[时间感知] 添加事件: {event.title} @ {event.scheduled_time}")
        
        return event_id
    
    def remove_event(self, event_id: str) -> bool:
        """移除时间事件"""
        for i, event in enumerate(self._events):
            if event.event_id == event_id:
                self._events.pop(i)
                logger.info(f"[时间感知] 移除事件: {event.title}")
                return True
        return False
    
    def toggle_event(self, event_id: str, enabled: bool) -> bool:
        """启用/禁用事件"""
        for event in self._events:
            if event.event_id == event_id:
                event.enabled = enabled
                logger.info(f"[时间感知] 事件 {event.title} 已{'启用' if enabled else '禁用'}")
                return True
        return False
    
    def get_due_events(self) -> List[TemporalEvent]:
        """获取到期事件"""
        now = datetime.now()
        due_events = []
        
        for event in self._events:
            if not event.enabled:
                continue
            
            if event.scheduled_time <= now:
                due_events.append(event)
        
        return due_events
    
    def update_recurring_event(self, event: TemporalEvent) -> Optional[datetime]:
        """更新循环事件的时间"""
        if not event.recurring or not event.recurring_interval:
            return None
        
        now = datetime.now()
        new_time = event.scheduled_time + event.recurring_interval
        
        # 确保新时间在未来
        while new_time <= now:
            new_time += event.recurring_interval
        
        event.scheduled_time = new_time
        logger.info(f"[时间感知] 更新循环事件: {event.title} -> {new_time}")
        
        return new_time
    
    def get_upcoming_events(self, limit: int = 10) -> List[TemporalEvent]:
        """获取即将到来的事件"""
        now = datetime.now()
        enabled_events = [e for e in self._events if e.enabled]
        sorted_events = sorted(enabled_events, key=lambda x: x.scheduled_time)
        
        return [e for e in sorted_events if e.scheduled_time > now][:limit]
    
    def get_all_events(self) -> List[TemporalEvent]:
        """获取所有事件"""
        return self._events.copy()
    
    async def start_monitoring(self):
        """开始监控时间事件"""
        if self._running:
            return
        
        self._running = True
        self._check_task = asyncio.create_task(self._monitoring_loop())
        logger.info("[时间感知] 开始监控时间事件")
    
    async def stop_monitoring(self):
        """停止监控"""
        self._running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        logger.info("[时间感知] 停止监控")
    
    async def _monitoring_loop(self):
        """监控循环"""
        while self._running:
            try:
                # 更新时间状态
                self.update_state()
                
                # 检查到期事件
                due_events = self.get_due_events()
                
                for event in due_events:
                    logger.info(f"[时间感知] 事件触发: {event.title}")
                    
                    # 触发回调
                    await self._trigger_event(event)
                    
                    # 更新循环事件
                    if event.recurring:
                        self.update_recurring_event(event)
                    else:
                        # 移除一次性事件
                        self.remove_event(event.event_id)
                
                # 休眠
                await asyncio.sleep(self._event_check_interval)
                
            except Exception as e:
                logger.error(f"[时间感知] 监控错误: {e}")
                await asyncio.sleep(30)
    
    async def _trigger_event(self, event: TemporalEvent):
        """触发事件（由子类或外部系统实现）"""
        # 这个方法会被任务调度系统重写
        logger.info(f"[时间感知] 触发事件: {event.title} - {event.description}")
    
    def _generate_event_id(self) -> str:
        """生成事件ID"""
        return f"event_{int(datetime.now().timestamp() * 1000)}"
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "current_time": self._current_state.current_time.isoformat() if self._current_state else None,
            "time_context": self._current_state.time_context.value if self._current_state else None,
            "monitoring": self._running,
            "total_events": len(self._events),
            "enabled_events": len([e for e in self._events if e.enabled]),
            "upcoming_events": len(self.get_upcoming_events()),
            "due_events": len(self.get_due_events())
        }


# 全局实例
_temporal_perception: Optional[TemporalPerception] = None


def get_temporal_perception() -> TemporalPerception:
    """获取时间感知实例"""
    global _temporal_perception
    if _temporal_perception is None:
        _temporal_perception = TemporalPerception()
    return _temporal_perception
