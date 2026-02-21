#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能分析器
收集和分析系统性能指标
"""

import time
import asyncio
import logging
from contextlib import contextmanager
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PerformanceProfiler:
    """性能分析器"""

    def __init__(self, max_history: int = 1000):
        """
        初始化性能分析器

        Args:
            max_history: 最大历史记录数
        """
        self.call_stats = defaultdict(lambda: {
            "count": 0,
            "total_time": 0.0,
            "max_time": 0.0,
            "min_time": float('inf'),
            "errors": 0
        })
        self.call_history = []
        self.max_history = max_history
        self.enabled = True

    @contextmanager
    def profile(self, operation_name: str):
        """
        性能分析上下文管理器

        Args:
            operation_name: 操作名称

        Example:
            async with profiler.profile("api_call"):
                # 执行操作
                pass
        """
        if not self.enabled:
            yield
            return

        start_time = time.time()
        success = True

        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            elapsed = time.time() - start_time
            self._record_call(operation_name, elapsed, success)

    def _record_call(self, operation_name: str, elapsed: float, success: bool):
        """记录单次调用"""
        stats = self.call_stats[operation_name]
        stats["count"] += 1
        stats["total_time"] += elapsed
        stats["max_time"] = max(stats["max_time"], elapsed)
        stats["min_time"] = min(stats["min_time"], elapsed) if stats["count"] == 1 else min(stats["min_time"], elapsed)

        if not success:
            stats["errors"] += 1

        # 记录历史
        self.call_history.append({
            "operation": operation_name,
            "duration": elapsed,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })

        # 清理历史
        if len(self.call_history) > self.max_history:
            self.call_history = self.call_history[-self.max_history:]

    def get_report(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """
        生成性能报告

        Args:
            operation_name: 指定操作名称，None表示全部

        Returns:
            性能报告字典
        """
        if operation_name:
            return self._get_operation_report(operation_name)
        else:
            return self._get_full_report()

    def _get_operation_report(self, operation_name: str) -> Dict[str, Any]:
        """获取单个操作的报告"""
        stats = self.call_stats.get(operation_name, {
            "count": 0,
            "total_time": 0.0,
            "max_time": 0.0,
            "min_time": 0.0,
            "errors": 0
        })

        if stats["count"] == 0:
            return {
                "operation": operation_name,
                "status": "no_data"
            }

        avg_time = stats["total_time"] / stats["count"]
        error_rate = stats["errors"] / stats["count"]

        return {
            "operation": operation_name,
            "count": stats["count"],
            "avg_time": round(avg_time, 3),
            "min_time": round(stats["min_time"], 3),
            "max_time": round(stats["max_time"], 3),
            "total_time": round(stats["total_time"], 3),
            "errors": stats["errors"],
            "error_rate": round(error_rate * 100, 2)
        }

    def _get_full_report(self) -> Dict[str, Any]:
        """获取完整报告"""
        report = {
            "summary": {
                "total_operations": sum(s["count"] for s in self.call_stats.values()),
                "total_calls": sum(s["count"] for s in self.call_stats.values()),
                "total_errors": sum(s["errors"] for s in self.call_stats.values()),
                "generated_at": datetime.now().isoformat()
            },
            "operations": {},
            "top_slowest": [],
            "top_frequent": [],
            "top_error_prone": []
        }

        # 按操作汇总
        for name, stats in self.call_stats.items():
            if stats["count"] > 0:
                report["operations"][name] = self._get_operation_report(name)

        # 排序
        operations_with_stats = [
            (name, self._get_operation_report(name))
            for name, stats in self.call_stats.items()
            if stats["count"] > 0
        ]

        # 最慢的操作（按平均时间）
        report["top_slowest"] = sorted(
            operations_with_stats,
            key=lambda x: x[1]["avg_time"],
            reverse=True
        )[:10]

        # 最频繁的操作
        report["top_frequent"] = sorted(
            operations_with_stats,
            key=lambda x: x[1]["count"],
            reverse=True
        )[:10]

        # 错误率最高的操作
        report["top_error_prone"] = sorted(
            [x for x in operations_with_stats if x[1]["error_rate"] > 0],
            key=lambda x: x[1]["error_rate"],
            reverse=True
        )[:10]

        return report

    def get_performance_trends(self, operation_name: str, hours: int = 24) -> Dict[str, Any]:
        """
        获取性能趋势

        Args:
            operation_name: 操作名称
            hours: 时间范围（小时）

        Returns:
            趋势数据
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        relevant_calls = [
            call for call in self.call_history
            if (call["operation"] == operation_name and
                datetime.fromisoformat(call["timestamp"]) >= cutoff_time)
        ]

        if not relevant_calls:
            return {"status": "no_data", "operation": operation_name}

        # 按小时分组
        hourly_stats = defaultdict(lambda: {"count": 0, "total_time": 0.0})

        for call in relevant_calls:
            hour = datetime.fromisoformat(call["timestamp"]).strftime("%Y-%m-%d %H:00")
            hourly_stats[hour]["count"] += 1
            hourly_stats[hour]["total_time"] += call["duration"]

        # 生成趋势数据
        trends = []
        for hour, stats in sorted(hourly_stats.items()):
            avg_time = stats["total_time"] / stats["count"] if stats["count"] > 0 else 0
            trends.append({
                "hour": hour,
                "count": stats["count"],
                "avg_time": round(avg_time, 3)
            })

        return {
            "operation": operation_name,
            "period_hours": hours,
            "trends": trends
        }

    def identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """识别性能瓶颈"""
        bottlenecks = []

        for name, stats in self.call_stats.items():
            if stats["count"] < 10:  # 样本太少，不分析
                continue

            avg_time = stats["total_time"] / stats["count"]

            # 慢操作
            if avg_time > 5.0:  # 超过5秒
                bottlenecks.append({
                    "type": "slow_operation",
                    "operation": name,
                    "avg_time": round(avg_time, 3),
                    "max_time": round(stats["max_time"], 3),
                    "count": stats["count"],
                    "severity": "high" if avg_time > 10.0 else "medium",
                    "suggestion": f"操作 '{name}' 平均耗时过长，建议检查实现或添加缓存"
                })

            # 错误率高
            error_rate = stats["errors"] / stats["count"]
            if error_rate > 0.1:  # 错误率超过10%
                bottlenecks.append({
                    "type": "high_error_rate",
                    "operation": name,
                    "error_rate": round(error_rate * 100, 2),
                    "errors": stats["errors"],
                    "count": stats["count"],
                    "severity": "high" if error_rate > 0.2 else "medium",
                    "suggestion": f"操作 '{name}' 错误率过高，建议检查异常处理和重试逻辑"
                })

        # 按严重程度排序
        bottlenecks.sort(key=lambda x: x["severity"], reverse=True)

        return bottlenecks

    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """生成优化建议"""
        suggestions = []

        bottlenecks = self.identify_bottlenecks()

        for bottleneck in bottlenecks:
            suggestions.append({
                "category": "performance",
                "severity": bottleneck["severity"],
                "title": f"性能问题: {bottleneck['type']}",
                "operation": bottleneck["operation"],
                "details": bottleneck,
                "suggestion": bottleneck["suggestion"]
            })

        # 添加通用建议
        total_calls = sum(s["count"] for s in self.call_stats.values())
        total_errors = sum(s["errors"] for s in self.call_stats.values())

        if total_calls > 0:
            overall_error_rate = total_errors / total_calls
            if overall_error_rate > 0.05:  # 整体错误率超过5%
                suggestions.append({
                    "category": "reliability",
                    "severity": "medium",
                    "title": "整体错误率偏高",
                    "current_error_rate": round(overall_error_rate * 100, 2),
                    "suggestion": "系统整体错误率偏高，建议检查日志和异常处理"
                })

        return suggestions

    def clear_history(self):
        """清空历史记录"""
        self.call_history.clear()
        self.call_stats.clear()
        logger.info("[PerformanceProfiler] 性能历史记录已清空")

    def export_report(self, output_path: Optional[str] = None) -> str:
        """
        导出性能报告到文件

        Args:
            output_path: 输出文件路径，None表示默认路径

        Returns:
            导出文件路径
        """
        import json

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(Path("logs") / f"performance_report_{timestamp}.json")

        report = self.get_report()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"[PerformanceProfiler] 性能报告已导出到: {output_path}")
        return output_path

    def enable(self):
        """启用性能分析"""
        self.enabled = True
        logger.info("[PerformanceProfiler] 性能分析已启用")

    def disable(self):
        """禁用性能分析"""
        self.enabled = False
        logger.info("[PerformanceProfiler] 性能分析已禁用")


# 创建全局性能分析器实例
_global_profiler = PerformanceProfiler()


def get_global_profiler() -> PerformanceProfiler:
    """获取全局性能分析器实例"""
    return _global_profiler
