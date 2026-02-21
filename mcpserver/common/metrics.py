"""
指标收集器

收集和统计工具调用指标

作者: NagaAgent Team
版本: 1.0.0
"""

import time
import logging
from typing import Dict, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class Metrics:
    """指标收集器"""

    def __init__(self, max_history: int = 1000):
        """初始化

        Args:
            max_history: 最大历史记录数
        """
        self.max_history = max_history

        # 计数器
        self.counters: Dict[str, int] = defaultdict(int)

        # 计时器
        self.timers: Dict[str, list] = defaultdict(list)

        # 成功率统计
        self.success_stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {'success': 0, 'failure': 0}
        )

        # 最近调用记录
        self.recent_calls: list = []

        logger.info("[Metrics] 指标收集器初始化完成")

    def increment(self, name: str, value: int = 1) -> None:
        """增加计数器

        Args:
            name: 指标名称
            value: 增加值
        """
        self.counters[name] += value
        logger.debug(f"[Metrics] 计数器 {name} += {value} (当前: {self.counters[name]})")

    def record_time(self, name: str, duration: float) -> None:
        """记录时间

        Args:
            name: 指标名称
            duration: 持续时间（秒）
        """
        self.timers[name].append(duration)

        # 限制历史记录数
        if len(self.timers[name]) > self.max_history:
            self.timers[name] = self.timers[name][-self.max_history:]

        logger.debug(f"[Metrics] 计时器 {name} 记录: {duration:.3f}s")

    def record_success(self, name: str) -> None:
        """记录成功

        Args:
            name: 工具或服务名称
        """
        self.success_stats[name]['success'] += 1

    def record_failure(self, name: str, error: Optional[str] = None) -> None:
        """记录失败

        Args:
            name: 工具或服务名称
            error: 错误信息（可选）
        """
        self.success_stats[name]['failure'] += 1
        logger.debug(f"[Metrics] 失败记录: {name} - {error}")

    def record_call(self, tool_name: str, success: bool, duration: float) -> None:
        """记录一次调用

        Args:
            tool_name: 工具名称
            success: 是否成功
            duration: 持续时间（秒）
        """
        self.increment(f"call.{tool_name}")
        self.record_time(tool_name, duration)

        if success:
            self.record_success(tool_name)
        else:
            self.record_failure(tool_name)

        # 记录最近调用
        call_record = {
            'tool_name': tool_name,
            'success': success,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }

        self.recent_calls.append(call_record)

        # 限制历史记录数
        if len(self.recent_calls) > self.max_history:
            self.recent_calls = self.recent_calls[-self.max_history:]

    def get_counter(self, name: str) -> int:
        """获取计数器值

        Args:
            name: 指标名称

        Returns:
            计数器值
        """
        return self.counters.get(name, 0)

    def get_timer_stats(self, name: str) -> Dict[str, float]:
        """获取计时器统计

        Args:
            name: 指标名称

        Returns:
            统计信息字典
        """
        times = self.timers.get(name, [])

        if not times:
            return {
                'count': 0,
                'min': 0,
                'max': 0,
                'avg': 0,
                'sum': 0
            }

        return {
            'count': len(times),
            'min': min(times),
            'max': max(times),
            'avg': sum(times) / len(times),
            'sum': sum(times)
        }

    def get_success_rate(self, name: str) -> float:
        """获取成功率

        Args:
            name: 工具或服务名称

        Returns:
            成功率（0-1）
        """
        stats = self.success_stats.get(name, {})
        total = stats.get('success', 0) + stats.get('failure', 0)

        if total == 0:
            return 0.0

        return stats.get('success', 0) / total

    def get_recent_calls(
        self,
        tool_name: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """获取最近的调用记录

        Args:
            tool_name: 工具名称（可选，None表示全部）
            since: 起始时间（可选）
            limit: 最大记录数

        Returns:
            调用记录列表
        """
        calls = self.recent_calls

        # 按工具名称过滤
        if tool_name:
            calls = [c for c in calls if c['tool_name'] == tool_name]

        # 按时间过滤
        if since:
            calls = [c for c in calls if datetime.fromisoformat(c['timestamp']) >= since]

        # 按数量限制
        return calls[-limit:]

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有统计信息

        Returns:
            统计信息字典
        """
        return {
            'counters': dict(self.counters),
            'timers': {name: self.get_timer_stats(name) for name in self.timers},
            'success_rates': {
                name: self.get_success_rate(name)
                for name in self.success_stats
            },
            'recent_call_count': len(self.recent_calls)
        }

    def reset(self) -> None:
        """重置所有统计"""
        self.counters.clear()
        self.timers.clear()
        self.success_stats.clear()
        self.recent_calls.clear()
        logger.info("[Metrics] 所有统计已重置")


# 全局指标收集器实例
_global_metrics: Optional[Metrics] = None


def get_global_metrics() -> Metrics:
    """获取全局指标收集器"""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = Metrics()
    return _global_metrics


# 上下文管理器：自动记录时间
class Timer:
    """计时器上下文管理器"""

    def __init__(self, metrics: Metrics, name: str):
        """初始化

        Args:
            metrics: 指标收集器
            name: 指标名称
        """
        self.metrics = metrics
        self.name = name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        success = exc_type is None
        self.metrics.record_call(self.name, success, duration)
        return False  # 不抑制异常
