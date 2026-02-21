#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用活动检测器
实时监控用户的应用使用情况，为自主性引擎提供活动上下文
"""

import asyncio
import logging
import threading
import time
from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ActivityType(Enum):
    """活动类型"""
    WORK = "work"           # 工作类应用
    ENTERTAINMENT = "entertainment"  # 娱乐类应用
    COMMUNICATION = "communication"  # 通讯类应用
    BROWSER = "browser"     # 浏览器
    SYSTEM = "system"       # 系统工具
    UNKNOWN = "unknown"     # 未知


@dataclass
class AppActivity:
    """应用活动记录"""
    app_name: str
    window_title: str
    activity_type: ActivityType
    start_time: datetime
    duration_seconds: float = 0.0


class AppActivityMonitor:
    """应用活动监控器"""

    # 应用分类映射
    APP_CATEGORIES = {
        # 工作类
        "code": ActivityType.WORK,
        "vscode": ActivityType.WORK,
        "visual studio": ActivityType.WORK,
        "intellij": ActivityType.WORK,
        "pycharm": ActivityType.WORK,
        "sublime": ActivityType.WORK,
        "notepad": ActivityType.WORK,
        "excel": ActivityType.WORK,
        "word": ActivityType.WORK,
        "powerpoint": ActivityType.WORK,
        "office": ActivityType.WORK,

        # 娱乐类
        "game": ActivityType.ENTERTAINMENT,
        "steam": ActivityType.ENTERTAINMENT,
        "bilibili": ActivityType.ENTERTAINMENT,
        "b站": ActivityType.ENTERTAINMENT,
        "qqmusic": ActivityType.ENTERTAINMENT,
        "netease": ActivityType.ENTERTAINMENT,
        "网易云": ActivityType.ENTERTAINMENT,
        "kugou": ActivityType.ENTERTAINMENT,

        # 通讯类
        "wechat": ActivityType.COMMUNICATION,
        "微信": ActivityType.COMMUNICATION,
        "qq": ActivityType.COMMUNICATION,
        "discord": ActivityType.COMMUNICATION,
        "telegram": ActivityType.COMMUNICATION,
        "钉钉": ActivityType.COMMUNICATION,
        "feishu": ActivityType.COMMUNICATION,

        # 浏览器
        "chrome": ActivityType.BROWSER,
        "edge": ActivityType.BROWSER,
        "firefox": ActivityType.BROWSER,
        "safari": ActivityType.BROWSER,

        # 系统工具
        "explorer": ActivityType.SYSTEM,
        "file explorer": ActivityType.SYSTEM,
        "settings": ActivityType.SYSTEM,
        "任务管理器": ActivityType.SYSTEM,
        "cmd": ActivityType.SYSTEM,
        "terminal": ActivityType.SYSTEM,
    }

    def __init__(self, check_interval: float = 2.0):
        """
        初始化活动监控器

        Args:
            check_interval: 检查间隔（秒）
        """
        self.check_interval = check_interval
        self.running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # 活动记录
        self.current_activity: Optional[AppActivity] = None
        self.activity_history: List[AppActivity] = []
        self.max_history = 500  # 最多保留500条记录

        # 统计数据
        self.app_usage_time: Dict[str, float] = defaultdict(float)
        self.daily_app_usage: Dict[str, float] = defaultdict(float)
        self.activity_type_stats: Dict[ActivityType, float] = defaultdict(float)

        # 最近窗口变化（用于检测应用切换频率）
        self.window_changes: deque = deque(maxlen=20)
        self.last_window = None

        # Windows API 初始化
        self._win32gui = None
        self._win32process = None
        self._init_windows_api()

    def _init_windows_api(self):
        """初始化Windows API"""
        try:
            import win32gui
            import win32process
            self._win32gui = win32gui
            self._win32process = win32process
            logger.info("[AppMonitor] Windows API 初始化成功")
        except ImportError:
            logger.warning("[AppMonitor] win32gui 未安装，应用监控功能受限")
        except Exception as e:
            logger.error(f"[AppMonitor] Windows API 初始化失败: {e}")

    def start(self):
        """启动监控"""
        if self.running:
            logger.warning("[AppMonitor] 监控已在运行")
            return

        if not self._win32gui:
            logger.error("[AppMonitor] Windows API 不可用，无法启动监控")
            return

        self.running = True
        self._stop_event.clear()

        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        logger.info("[AppMonitor] 应用活动监控已启动")

    def stop(self):
        """停止监控"""
        if not self.running:
            return

        self.running = False
        self._stop_event.set()

        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

        # 保存最后一条记录
        if self.current_activity:
            self._finish_current_activity()

        logger.info("[AppMonitor] 应用活动监控已停止")

    def _monitor_loop(self):
        """监控循环"""
        while not self._stop_event.is_set():
            try:
                self._check_window()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"[AppMonitor] 监控循环错误: {e}")
                time.sleep(5)

    def _check_window(self):
        """检查当前窗口"""
        try:
            # 获取前台窗口句柄
            hwnd = self._win32gui.GetForegroundWindow()

            # 获取窗口标题
            window_title = self._win32gui.GetWindowText(hwnd)
            if not window_title:
                return

            # 获取进程信息
            _, pid = self._win32process.GetWindowThreadProcessId(hwnd)

            # 获取进程名
            try:
                import psutil
                process = psutil.Process(pid)
                process_name = process.name().lower()
            except:
                process_name = "unknown"

            # 应用名称优先使用进程名，如果没有则用窗口标题
            app_name = process_name
            if not app_name or app_name == "unknown":
                app_name = window_title[:50]

            # 判断是否切换了窗口
            current_window_id = f"{app_name}_{window_title[:30]}"
            if self.last_window != current_window_id:
                self._on_window_change(app_name, window_title, pid)
                self.last_window = current_window_id
                self.window_changes.append(datetime.now())

            # 更新当前活动时长
            if self.current_activity:
                self.current_activity.duration_seconds += self.check_interval

        except Exception as e:
            logger.debug(f"[AppMonitor] 窗口检查失败: {e}")

    def _on_window_change(self, app_name: str, window_title: str, pid: int):
        """窗口变化处理"""
        # 完成上一条记录
        if self.current_activity:
            self._finish_current_activity()

        # 创建新记录
        activity_type = self._classify_app(app_name, window_title)
        self.current_activity = AppActivity(
            app_name=app_name,
            window_title=window_title,
            activity_type=activity_type,
            start_time=datetime.now()
        )

        logger.debug(f"[AppMonitor] 切换到: {app_name} ({activity_type.value})")

    def _finish_current_activity(self):
        """完成当前活动记录"""
        if not self.current_activity:
            return

        # 添加到历史
        self.activity_history.append(self.current_activity)
        if len(self.activity_history) > self.max_history:
            self.activity_history.pop(0)

        # 更新统计
        duration = self.current_activity.duration_seconds
        self.app_usage_time[self.current_activity.app_name] += duration
        self.activity_type_stats[self.current_activity.activity_type] += duration

        logger.debug(f"[AppMonitor] {self.current_activity.app_name} 使用时长: {duration:.1f}秒")

    def _classify_app(self, app_name: str, window_title: str) -> ActivityType:
        """分类应用类型"""
        app_name_lower = app_name.lower()

        # 关键词匹配
        for keyword, activity_type in self.APP_CATEGORIES.items():
            if keyword in app_name_lower:
                return activity_type

        # 窗口标题分析
        title_lower = window_title.lower()
        if any(kw in title_lower for kw in ["github", "gitlab", "代码", "programming"]):
            return ActivityType.WORK
        if any(kw in title_lower for kw in ["video", "播放", "音乐", "game", "游戏"]):
            return ActivityType.ENTERTAINMENT
        if any(kw in title_lower for kw in ["chat", "消息", "群聊"]):
            return ActivityType.COMMUNICATION
        if any(kw in title_lower for kw in ["http", "www", "浏览"]):
            return ActivityType.BROWSER

        return ActivityType.UNKNOWN

    def get_current_activity(self) -> Optional[Dict[str, Any]]:
        """获取当前活动"""
        if not self.current_activity:
            return None

        return {
            "app_name": self.current_activity.app_name,
            "window_title": self.current_activity.window_title,
            "activity_type": self.current_activity.activity_type.value,
            "duration": self.current_activity.duration_seconds,
            "start_time": self.current_activity.start_time.isoformat()
        }

    def get_activity_summary(self, minutes: int = 30) -> Dict[str, Any]:
        """获取活动摘要"""
        if not self.activity_history:
            return {
                "total_activities": 0,
                "primary_app": None,
                "primary_type": None,
                "window_switch_count": 0,
                "app_switch_rate": 0.0
            }

        # 过滤最近N分钟的活动
        cutoff_time = datetime.now().timestamp() - (minutes * 60)
        recent_activities = [
            a for a in self.activity_history
            if a.start_time.timestamp() > cutoff_time
        ]

        if not recent_activities:
            return {
                "total_activities": 0,
                "primary_app": self.current_activity.app_name if self.current_activity else None,
                "primary_type": self.current_activity.activity_type.value if self.current_activity else None,
                "window_switch_count": 0,
                "app_switch_rate": 0.0
            }

        # 统计主要应用
        app_time = defaultdict(float)
        type_time = defaultdict(float)

        for activity in recent_activities:
            app_time[activity.app_name] += activity.duration_seconds
            type_time[activity.activity_type] += activity.duration_seconds

        primary_app = max(app_time.items(), key=lambda x: x[1])
        primary_type = max(type_time.items(), key=lambda x: x[1])

        # 窗口切换频率
        recent_changes = [
            t for t in self.window_changes
            if t.timestamp() > cutoff_time
        ]
        switch_rate = len(recent_changes) / minutes if minutes > 0 else 0

        # 判断用户状态
        user_activity = "unknown"
        if primary_type[0] == ActivityType.WORK:
            user_activity = "working" if switch_rate < 2 else "multitasking"
        elif primary_type[0] == ActivityType.ENTERTAINMENT:
            user_activity = "gaming" if "game" in primary_app[0].lower() else "entertainment"
        elif primary_type[0] == ActivityType.COMMUNICATION:
            user_activity = "communicating"
        elif primary_type[0] == ActivityType.BROWSER:
            user_activity = "browsing"

        return {
            "total_activities": len(recent_activities),
            "primary_app": primary_app[0],
            "primary_app_duration": primary_app[1],
            "primary_type": primary_type[0].value,
            "primary_type_duration": primary_type[1],
            "window_switch_count": len(recent_changes),
            "app_switch_rate": switch_rate,  # 每分钟切换次数
            "user_activity": user_activity,
            "time_range_minutes": minutes
        }

    def get_app_switch_frequency(self) -> float:
        """获取应用切换频率（次/分钟）"""
        if len(self.window_changes) < 2:
            return 0.0

        time_span = (self.window_changes[-1] - self.window_changes[0]).total_seconds()
        if time_span == 0:
            return 0.0

        return (len(self.window_changes) - 1) / (time_span / 60)

    def reset_daily_stats(self):
        """重置每日统计"""
        self.daily_app_usage.clear()
        logger.info("[AppMonitor] 每日统计已重置")

    def get_status(self) -> Dict[str, Any]:
        """获取监控器状态"""
        return {
            "running": self.running,
            "check_interval": self.check_interval,
            "current_activity": self.get_current_activity(),
            "activity_history_count": len(self.activity_history),
            "window_switch_frequency": self.get_app_switch_frequency()
        }


# 全局实例
_app_monitor: Optional[AppActivityMonitor] = None


def get_app_monitor() -> AppActivityMonitor:
    """获取应用监控器实例"""
    global _app_monitor
    if _app_monitor is None:
        _app_monitor = AppActivityMonitor()
    return _app_monitor
