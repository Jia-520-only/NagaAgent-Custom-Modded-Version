#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动优化引擎
基于健康检查和性能分析结果自动优化系统
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AutoOptimizer:
    """自动优化引擎"""

    def __init__(self, config: Any = None):
        """
        初始化自动优化引擎

        Args:
            config: 系统配置对象
        """
        self.config = config
        self.optimization_history: List[Dict[str, Any]] = []
        self.rollback_stack: List[Dict[str, Any]] = []
        self.enabled = True
        self.auto_apply_safe_optimizations = True

    async def analyze_and_optimize(
        self,
        health_report: Dict[str, Any],
        performance_report: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        基于健康报告分析和执行优化

        Args:
            health_report: 健康检查报告
            performance_report: 性能分析报告

        Returns:
            执行的优化列表
        """
        if not self.enabled:
            logger.info("[AutoOptimizer] 自动优化已禁用")
            return []

        logger.info("[AutoOptimizer] 开始分析和优化...")

        optimizations = []

        # 1. 基于系统资源优化
        optimizations.extend(await self._optimize_for_resources(health_report))

        # 2. 基于性能报告优化
        if performance_report:
            optimizations.extend(await self._optimize_for_performance(performance_report))

        # 3. 基于配置优化
        optimizations.extend(await self._optimize_configuration(health_report))

        # 执行优化
        results = []
        for opt in optimizations:
            if opt.get("risk_level", "high") == "high" and not self.auto_apply_safe_optimizations:
                logger.warning(f"[AutoOptimizer] 优化 '{opt['type']}' 风险较高，需要人工确认: {opt}")
                continue

            result = await self._apply_optimization(opt)
            results.append(result)

        return results

    async def _optimize_for_resources(self, health_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于系统资源优化"""
        optimizations = []
        system = health_report.get("system", {})

        cpu_usage = system.get("cpu_usage", 0)
        memory_usage = system.get("memory_usage", 0)

        # CPU优化
        if cpu_usage > 70:
            logger.info(f"[AutoOptimizer] CPU使用率过高 ({cpu_usage}%)，生成优化建议")

            # 降低MCP并发数
            optimizations.append({
                "type": "reduce_mcp_concurrency",
                "risk_level": "low",
                "parameter": "mcp_scheduler.max_concurrent",
                "current_value": self._get_config_value("mcp_scheduler.max_concurrent", 10),
                "suggested_value": 5,
                "reason": "降低MCP调度器的并发任务数以减少CPU压力",
                "category": "performance",
                "auto_apply": True
            })

            # 减少历史对话轮数
            current_rounds = self._get_config_value("api.max_history_rounds", 10)
            if current_rounds > 10:
                optimizations.append({
                    "type": "reduce_history_rounds",
                    "risk_level": "low",
                    "parameter": "api.max_history_rounds",
                    "current_value": current_rounds,
                    "suggested_value": 10,
                    "reason": "减少历史对话轮数以降低CPU和内存占用",
                    "category": "performance",
                    "auto_apply": True
                })

        # 内存优化
        if memory_usage > 80:
            logger.info(f"[AutoOptimizer] 内存使用率过高 ({memory_usage}%)，生成优化建议")

            # 减少上下文加载天数
            current_days = self._get_config_value("api.context_load_days", 3)
            if current_days > 1:
                optimizations.append({
                    "type": "reduce_context_days",
                    "risk_level": "low",
                    "parameter": "api.context_load_days",
                    "current_value": current_days,
                    "suggested_value": 1,
                    "reason": "减少上下文加载天数以降低内存占用",
                    "category": "performance",
                    "auto_apply": True
                })

        # 磁盘优化
        disk_usage = system.get("disk_usage", 0)
        if disk_usage > 85:
            logger.warning(f"[AutoOptimizer] 磁盘空间不足 ({disk_usage}%)，建议清理日志")
            optimizations.append({
                "type": "cleanup_logs",
                "risk_level": "medium",
                "reason": "磁盘空间不足，建议清理旧日志文件",
                "category": "storage",
                "auto_apply": False  # 需要人工确认
            })

        return optimizations

    async def _optimize_for_performance(self, performance_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于性能报告优化"""
        optimizations = []

        # 检查是否有性能瓶颈
        bottlenecks = performance_report.get("bottlenecks", [])
        for bottleneck in bottlenecks:
            if bottleneck.get("type") == "slow_operation":
                logger.warning(f"[AutoOptimizer] 检测到慢操作: {bottleneck['operation']}")
                # 这里可以根据具体操作生成优化建议

        return optimizations

    async def _optimize_configuration(self, health_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """优化配置"""
        optimizations = []

        # 检查配置建议
        config_issues = health_report.get("configuration", {}).get("issues", [])

        for issue in config_issues:
            optimizations.append({
                "type": "fix_configuration",
                "risk_level": "low",
                "issue": issue,
                "reason": f"修复配置问题: {issue}",
                "category": "configuration",
                "auto_apply": True
            })

        return optimizations

    async def _apply_optimization(self, opt: Dict[str, Any]) -> Dict[str, Any]:
        """应用单个优化"""
        result = {
            "type": opt.get("type"),
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "message": ""
        }

        try:
            # 处理不同类型的优化
            if opt["type"] == "cleanup_logs":
                result.update(await self._cleanup_logs())
            elif opt["type"] == "reduce_mcp_concurrency":
                result.update(await self._apply_config_change(opt))
            elif opt["type"] == "reduce_history_rounds":
                result.update(await self._apply_config_change(opt))
            elif opt["type"] == "reduce_context_days":
                result.update(await self._apply_config_change(opt))
            elif opt["type"] == "fix_configuration":
                result.update(await self._fix_configuration_issue(opt))
            else:
                result["status"] = "skipped"
                result["message"] = f"未知优化类型: {opt['type']}"

        except Exception as e:
            result["status"] = "failed"
            result["message"] = str(e)
            logger.error(f"[AutoOptimizer] 优化执行失败: {e}", exc_info=True)

        # 记录优化历史
        self.optimization_history.append(result)

        return result

    async def _cleanup_logs(self) -> Dict[str, Any]:
        """清理日志文件"""
        try:
            logs_dir = Path("logs")
            if not logs_dir.exists():
                return {"status": "skipped", "message": "日志目录不存在"}

            # 清理7天前的日志
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=7)

            deleted_count = 0
            freed_space = 0

            for log_file in logs_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_time.timestamp():
                    size = log_file.stat().st_size
                    log_file.unlink()
                    deleted_count += 1
                    freed_space += size

            return {
                "status": "success",
                "message": f"清理了 {deleted_count} 个日志文件，释放 {freed_space / (1024**2):.2f} MB",
                "details": {
                    "deleted_files": deleted_count,
                    "freed_space_mb": round(freed_space / (1024**2), 2)
                }
            }

        except Exception as e:
            return {"status": "failed", "message": str(e)}

    async def _apply_config_change(self, opt: Dict[str, Any]) -> Dict[str, Any]:
        """应用配置变更"""
        try:
            param = opt["parameter"]
            new_value = opt["suggested_value"]

            # 记录当前值用于回滚
            current_value = self._get_config_value(param)
            self.rollback_stack.append({
                "parameter": param,
                "value": current_value,
                "timestamp": datetime.now().isoformat()
            })

            # 应用新值
            self._set_config_value(param, new_value)

            # 保存配置
            if hasattr(self.config, 'save'):
                self.config.save()
                logger.info(f"[AutoOptimizer] 配置已保存: {param} = {new_value}")

            return {
                "status": "success",
                "message": f"配置已更新: {param} = {new_value} (原值: {current_value})",
                "old_value": current_value,
                "new_value": new_value
            }

        except Exception as e:
            return {"status": "failed", "message": str(e)}

    async def _fix_configuration_issue(self, opt: Dict[str, Any]) -> Dict[str, Any]:
        """修复配置问题"""
        issue = opt.get("issue", "")

        # 这里可以根据具体问题类型进行修复
        # 目前仅记录
        return {
            "status": "skipped",
            "message": f"配置问题需要手动修复: {issue}"
        }

    def _get_config_value(self, param_path: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            param_path: 参数路径，如 "api.max_history_rounds"
            default: 默认值

        Returns:
            配置值
        """
        try:
            if not self.config:
                return default

            parts = param_path.split(".")
            value = self.config

            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                elif isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default

            return value

        except Exception as e:
            logger.warning(f"[AutoOptimizer] 获取配置失败 {param_path}: {e}")
            return default

    def _set_config_value(self, param_path: str, value: Any):
        """
        设置配置值

        Args:
            param_path: 参数路径，如 "api.max_history_rounds"
            value: 新值
        """
        try:
            if not self.config:
                raise ValueError("配置对象未初始化")

            parts = param_path.split(".")
            target = self.config

            # 导航到最后一个属性
            for part in parts[:-1]:
                if hasattr(target, part):
                    target = getattr(target, part)
                elif isinstance(target, dict) and part in target:
                    target = target[part]
                else:
                    raise ValueError(f"配置路径不存在: {param_path}")

            # 设置最后一个属性
            setattr(target, parts[-1], value)

        except Exception as e:
            logger.error(f"[AutoOptimizer] 设置配置失败 {param_path}: {e}")
            raise

    async def rollback(self, steps: int = 1) -> bool:
        """
        回滚最近的优化

        Args:
            steps: 回滚步数

        Returns:
            是否成功
        """
        if not self.rollback_stack:
            logger.warning("[AutoOptimizer] 没有可回滚的优化")
            return False

        logger.info(f"[AutoOptimizer] 开始回滚最近的 {steps} 次优化...")

        try:
            for _ in range(steps):
                if not self.rollback_stack:
                    break

                rollback_item = self.rollback_stack.pop()
                param = rollback_item["parameter"]
                value = rollback_item["value"]

                self._set_config_value(param, value)
                logger.info(f"[AutoOptimizer] 已回滚配置: {param} = {value}")

            # 保存配置
            if hasattr(self.config, 'save'):
                self.config.save()

            logger.info("[AutoOptimizer] 回滚完成")
            return True

        except Exception as e:
            logger.error(f"[AutoOptimizer] 回滚失败: {e}", exc_info=True)
            return False

    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """获取优化历史"""
        return self.optimization_history.copy()

    def get_pending_optimizations(
        self,
        health_report: Dict[str, Any],
        performance_report: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取待执行的优化（不执行）

        Args:
            health_report: 健康检查报告
            performance_report: 性能分析报告

        Returns:
            待执行的优化列表
        """
        # 复用分析和优化逻辑，但不实际执行
        return asyncio.run(self.analyze_and_optimize(health_report, performance_report))

    def enable_auto_apply(self):
        """启用自动应用优化"""
        self.auto_apply_safe_optimizations = True
        logger.info("[AutoOptimizer] 已启用自动应用优化")

    def disable_auto_apply(self):
        """禁用自动应用优化"""
        self.auto_apply_safe_optimizations = False
        logger.info("[AutoOptimizer] 已禁用自动应用优化")

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """获取优化建议"""
        recommendations = []

        # 基于历史记录生成建议
        recent_optimizations = self.optimization_history[-10:]

        # 统计优化类型
        opt_types = {}
        for opt in recent_optimizations:
            opt_type = opt.get("type", "unknown")
            if opt_type not in opt_types:
                opt_types[opt_type] = 0
            opt_types[opt_type] += 1

        # 生成建议
        if "reduce_mcp_concurrency" in opt_types:
            recommendations.append({
                "type": "performance",
                "title": "考虑增加系统资源",
                "message": "频繁降低MCP并发数可能表明系统资源不足，考虑增加CPU或内存"
            })

        if "reduce_history_rounds" in opt_types:
            recommendations.append({
                "type": "configuration",
                "title": "优化历史对话管理",
                "message": "频繁减少历史轮数，建议实施更智能的对话压缩或缓存策略"
            })

        return recommendations

    def export_report(self, output_path: Optional[str] = None) -> str:
        """导出优化报告"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(Path("logs") / f"optimization_report_{timestamp}.json")

        report = {
            "generated_at": datetime.now().isoformat(),
            "optimization_history": self.optimization_history,
            "pending_rollback": len(self.rollback_stack),
            "recommendations": self.get_recommendations()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"[AutoOptimizer] 优化报告已导出到: {output_path}")
        return output_path
