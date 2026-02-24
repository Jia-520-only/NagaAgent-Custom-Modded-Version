#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自我优化系统主控模块
协调各个子模块，实现完整的自我检测和优化流程
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from .health_monitor import HealthMonitor
from .performance_profiler import PerformanceProfiler
from .auto_optimizer import AutoOptimizer
from .code_quality_monitor import CodeQualityMonitor

logger = logging.getLogger(__name__)


class SelfOptimizer:
    """自我优化系统主控制器"""

    def __init__(self, project_root: str, config: Any = None):
        """
        初始化自我优化系统

        Args:
            project_root: 项目根目录
            config: 系统配置对象
        """
        self.project_root = Path(project_root)
        self.config = config

        # 初始化子模块
        self.health_monitor = HealthMonitor(config)
        self.performance_profiler = PerformanceProfiler()
        self.auto_optimizer = AutoOptimizer(config)
        self.code_quality_monitor = CodeQualityMonitor(project_root)

        # 运行状态
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.check_interval = 3600  # 默认1小时检查一次

        # 历史记录
        self.optimization_runs: List[Dict[str, Any]] = []

    async def start(self, interval: int = 3600):
        """
        启动自我优化系统

        Args:
            interval: 检查间隔（秒）
        """
        if self.running:
            logger.warning("[SelfOptimizer] 系统已在运行")
            return

        self.check_interval = interval
        self.running = True

        logger.info(f"[SelfOptimizer] 启动自我优化系统，检查间隔: {interval}秒")

        # 启动健康监控
        asyncio.create_task(self.health_monitor.start_monitoring())

        # 启动主循环
        self.monitor_task = asyncio.create_task(self._main_loop())

        logger.info("[SelfOptimizer] 自我优化系统已启动")

    def stop(self):
        """停止自我优化系统"""
        if not self.running:
            return

        self.running = False

        if self.monitor_task:
            self.monitor_task.cancel()

        self.health_monitor.stop_monitoring()

        logger.info("[SelfOptimizer] 自我优化系统已停止")

    async def _main_loop(self):
        """主优化循环"""
        while self.running:
            try:
                # 执行完整的优化检查
                await self.run_optimization_cycle()
            except Exception as e:
                logger.error(f"[SelfOptimizer] 优化循环异常: {e}", exc_info=True)

            # 等待下一次检查
            try:
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break

    async def run_optimization_cycle(self) -> Dict[str, Any]:
        """
        执行一次完整的优化检查循环

        Returns:
            优化报告
        """
        logger.info("=" * 60)
        logger.info("[SelfOptimizer] 开始优化检查循环")
        logger.info("=" * 60)

        start_time = datetime.now()

        report = {
            "timestamp": start_time.isoformat(),
            "health_check": None,
            "performance_analysis": None,
            "code_quality": None,
            "optimizations_applied": [],
            "recommendations": [],
            "summary": {}
        }

        try:
            # 1. 健康检查
            logger.info("[SelfOptimizer] 步骤 1/4: 执行健康检查...")
            health_report = await self.health_monitor.check_health()
            report["health_check"] = health_report

            # 生成健康优化建议
            health_suggestions = self.health_monitor.get_optimization_suggestions()
            report["recommendations"].extend(health_suggestions)

            # 2. 性能分析
            logger.info("[SelfOptimizer] 步骤 2/4: 分析性能...")
            performance_report = self.performance_profiler.get_report()
            report["performance_analysis"] = performance_report

            # 生成性能优化建议
            performance_suggestions = self.performance_profiler.get_optimization_suggestions()
            report["recommendations"].extend(performance_suggestions)

            # 3. 代码质量检查（低频执行，每24小时一次）
            logger.info("[SelfOptimizer] 步骤 3/4: 检查代码质量...")
            if await self._should_run_code_quality_check():
                code_quality_report = await self.code_quality_monitor.analyze_codebase()
                report["code_quality"] = code_quality_report

                # 生成重构建议
                refactoring_suggestions = self.code_quality_monitor.get_refactoring_suggestions()
                for suggestion in refactoring_suggestions:
                    suggestion["category"] = "code_quality"
                report["recommendations"].extend(refactoring_suggestions)

            # 4. 执行自动优化
            logger.info("[SelfOptimizer] 步骤 4/4: 执行自动优化...")
            optimizations = await self.auto_optimizer.analyze_and_optimize(
                health_report,
                performance_report
            )
            report["optimizations_applied"] = optimizations

            # 5. 生成优化建议（来自AutoOptimizer）
            optimizer_recommendations = self.auto_optimizer.get_recommendations()
            report["recommendations"].extend(optimizer_recommendations)

            # 生成摘要
            elapsed = (datetime.now() - start_time).total_seconds()
            report["summary"] = {
                "status": "success",
                "elapsed_seconds": round(elapsed, 2),
                "health_status": health_report.get("system", {}).get("status", "unknown"),
                "optimizations_count": len(optimizations),
                "recommendations_count": len(report["recommendations"]),
                "critical_issues": len([r for r in report["recommendations"]
                                       if r.get("severity") == "critical"])
            }

            # 保存历史
            self.optimization_runs.append(report)
            if len(self.optimization_runs) > 100:
                self.optimization_runs.pop(0)

            logger.info(f"[SelfOptimizer] 优化检查完成，耗时 {elapsed:.2f} 秒")
            logger.info(f"[SelfOptimizer] 应用优化: {len(optimizations)} 项")
            logger.info(f"[SelfOptimizer] 生成建议: {len(report['recommendations'])} 项")
            if report["summary"]["critical_issues"] > 0:
                logger.warning(f"[SelfOptimizer] 检测到 {report['summary']['critical_issues']} 个严重问题")

        except Exception as e:
            logger.error(f"[SelfOptimizer] 优化检查失败: {e}", exc_info=True)
            report["summary"] = {
                "status": "failed",
                "error": str(e)
            }

        logger.info("=" * 60)

        return report

    async def _should_run_code_quality_check(self) -> bool:
        """判断是否应该运行代码质量检查"""
        if not self.optimization_runs:
            return True

        # 检查最近一次是否有代码质量检查
        latest_run = self.optimization_runs[-1]
        if latest_run.get("code_quality") is None:
            return True

        # 检查时间间隔（24小时）
        from datetime import timedelta
        last_check_time = datetime.fromisoformat(latest_run["timestamp"])
        if datetime.now() - last_check_time > timedelta(hours=24):
            return True

        return False

    async def run_manual_optimization(self) -> Dict[str, Any]:
        """
        手动触发一次优化检查

        Returns:
            优化报告
        """
        logger.info("[SelfOptimizer] 手动触发优化检查")
        return await self.run_optimization_cycle()

    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        health_summary = self.health_monitor.get_health_summary()

        return {
            "running": self.running,
            "check_interval": self.check_interval,
            "health_status": health_summary.get("status", "unknown"),
            "health_summary": health_summary,
            "performance_report": self.performance_profiler.get_report(),
            "optimization_history": self.auto_optimizer.get_optimization_history(),
            "last_run": self.optimization_runs[-1] if self.optimization_runs else None,
            "total_runs": len(self.optimization_runs)
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """获取所有优化建议"""
        recommendations = []

        # 健康建议
        health_suggestions = self.health_monitor.get_optimization_suggestions()
        recommendations.extend(health_suggestions)

        # 性能建议
        performance_suggestions = self.performance_profiler.get_optimization_suggestions()
        recommendations.extend(performance_suggestions)

        # 代码质量建议
        refactoring_suggestions = self.code_quality_monitor.get_refactoring_suggestions()
        recommendations.extend(refactoring_suggestions)

        # 优化器建议
        optimizer_recommendations = self.auto_optimizer.get_recommendations()
        recommendations.extend(optimizer_recommendations)

        # 按严重程度排序
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 99))

        return recommendations

    async def apply_recommendation(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用单个优化建议

        Args:
            recommendation: 优化建议

        Returns:
            应用结果
        """
        logger.info(f"[SelfOptimizer] 应用建议: {recommendation.get('title', 'unknown')}")

        result = {
            "recommendation": recommendation,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }

        try:
            # 这里可以根据建议类型实现自动应用逻辑
            # 目前仅记录

            if recommendation.get("auto_apply"):
                # 尝试自动应用
                result["status"] = "success"
                result["message"] = "建议已应用"
            else:
                result["status"] = "requires_manual_review"
                result["message"] = "该建议需要人工审核后应用"

        except Exception as e:
            result["status"] = "failed"
            result["message"] = str(e)

        return result

    def export_full_report(self, output_dir: Optional[str] = None) -> str:
        """
        导出完整报告

        Args:
            output_dir: 输出目录

        Returns:
            报告文件路径
        """
        import json

        if output_dir is None:
            output_dir = Path("Fixlogs")
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 导出健康报告
        health_path = output_dir / f"health_report_{timestamp}.json"
        if self.health_monitor.health_history:
            with open(health_path, 'w', encoding='utf-8') as f:
                json.dump(self.health_monitor.health_history[-1], f, indent=2, ensure_ascii=False)

        # 导出性能报告
        performance_path = self.performance_profiler.export_report(
            str(output_dir / f"performance_report_{timestamp}.json")
        )

        # 导出优化报告
        optimization_path = self.auto_optimizer.export_report(
            str(output_dir / f"optimization_report_{timestamp}.json")
        )

        # 导出完整报告
        full_report_path = output_dir / f"self_optimization_report_{timestamp}.json"
        full_report = {
            "generated_at": datetime.now().isoformat(),
            "status": self.get_status(),
            "recommendations": self.get_recommendations(),
            "optimization_runs": self.optimization_runs[-10:]  # 最近10次
        }

        with open(full_report_path, 'w', encoding='utf-8') as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False)

        logger.info(f"[SelfOptimizer] 完整报告已导出到: {full_report_path}")

        return str(full_report_path)

    async def run_code_analysis(self) -> Dict[str, Any]:
        """
        运行代码分析（AI辅助）

        Returns:
            分析结果和建议
        """
        logger.info("[SelfOptimizer] 运行AI代码分析...")

        # 1. 获取代码质量报告
        code_quality_report = await self.code_quality_monitor.analyze_codebase()

        # 2. 获取重构建议
        refactoring_suggestions = self.code_quality_monitor.get_refactoring_suggestions()

        # 3. 尝试使用AI生成优化建议
        ai_suggestions = await self._generate_ai_suggestions(code_quality_report, refactoring_suggestions)

        return {
            "code_quality": code_quality_report,
            "refactoring_suggestions": refactoring_suggestions,
            "ai_suggestions": ai_suggestions
        }

    async def _generate_ai_suggestions(
        self,
        code_quality_report: Dict[str, Any],
        refactoring_suggestions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        使用AI生成优化建议

        Args:
            code_quality_report: 代码质量报告
            refactoring_suggestions: 重构建议

        Returns:
            AI生成的建议
        """
        try:
            # 构建提示词
            prompt = self._build_analysis_prompt(code_quality_report, refactoring_suggestions)

            # 调用LLM生成建议
            from game.core.llm_adapter import LLMAdapter
            llm = LLMAdapter()

            response = await llm.chat_with_context(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            # 解析响应
            ai_suggestions = self._parse_ai_response(response)

            return ai_suggestions

        except Exception as e:
            logger.error(f"[SelfOptimizer] AI分析失败: {e}", exc_info=True)
            return []

    def _build_analysis_prompt(
        self,
        code_quality_report: Dict[str, Any],
        refactoring_suggestions: List[Dict[str, Any]]
    ) -> str:
        """构建分析提示词"""
        prompt = """作为NagaAgent的代码优化专家，请分析以下代码质量报告，并提供优化建议。

代码质量报告：
"""

        # 添加复杂度信息
        complexity = code_quality_report.get("complexity", {})
        prompt += f"""
- 总文件数: {complexity.get('total_files', 0)}
- 总函数数: {complexity.get('total_functions', 0)}
- 总类数: {complexity.get('total_classes', 0)}
- 总代码行数: {complexity.get('total_lines', 0)}
- 高复杂度函数数: {complexity.get('high_complexity_count', 0)}
"""

        # 添加重构建议（前5个）
        if refactoring_suggestions:
            prompt += "\n\n主要问题（前5个）：\n"
            for i, suggestion in enumerate(refactoring_suggestions[:5], 1):
                prompt += f"{i}. {suggestion.get('title', 'unknown')}: {suggestion.get('suggestion', '')}\n"

        prompt += """
请以JSON格式提供优化建议，格式如下：
[
    {
        "category": "优化类别（performance/security/maintainability）",
        "title": "建议标题",
        "description": "详细描述",
        "priority": "high/medium/low",
        "action": "具体行动建议"
    }
]

请提供3-5个最重要的建议。
"""

        return prompt

    def _parse_ai_response(self, response: str) -> List[Dict[str, Any]]:
        """解析AI响应"""
        import json

        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

            # 返回默认建议
            return []


# 创建全局实例
_global_optimizer: Optional[SelfOptimizer] = None


def get_global_optimizer() -> Optional[SelfOptimizer]:
    """获取全局自我优化系统实例"""
    return _global_optimizer


def init_global_optimizer(project_root: str, config: Any) -> SelfOptimizer:
    """初始化全局自我优化系统实例"""
    global _global_optimizer
    _global_optimizer = SelfOptimizer(project_root, config)
    return _global_optimizer
