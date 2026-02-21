#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统健康监控器
实时监控系统和服务的健康状态
"""

import asyncio
import logging
import socket
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class HealthMonitor:
    """系统健康监控器"""

    def __init__(self, config: Any = None):
        """
        初始化健康监控器

        Args:
            config: 系统配置对象
        """
        self.config = config
        self.check_interval = 300  # 5分钟检查一次
        self.alert_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "task_failure_rate": 0.1
        }
        self.health_history = []
        self.alerts = []
        self.running = False

    async def start_monitoring(self):
        """启动健康监控"""
        if self.running:
            logger.warning("[HealthMonitor] 监控已在运行")
            return

        self.running = True
        logger.info("[HealthMonitor] 开始系统健康监控")

        while self.running:
            try:
                health_report = await self.check_health()
                await self._process_health_report(health_report)
            except Exception as e:
                logger.error(f"[HealthMonitor] 健康检查失败: {e}", exc_info=True)
            await asyncio.sleep(self.check_interval)

    def stop_monitoring(self):
        """停止健康监控"""
        self.running = False
        logger.info("[HealthMonitor] 健康监控已停止")

    async def check_health(self) -> Dict[str, Any]:
        """
        执行完整的健康检查

        Returns:
            健康报告字典
        """
        logger.info("[HealthMonitor] 执行健康检查...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "system": await self._check_system_resources(),
            "services": await self._check_services(),
            "tasks": await self._check_tasks(),
            "dependencies": await self._check_dependencies(),
            "configuration": await self._check_configuration()
        }

        # 保存历史
        self.health_history.append(report)
        if len(self.health_history) > 100:  # 最多保留100条历史
            self.health_history.pop(0)

        return report

    async def _check_system_resources(self) -> Dict[str, Any]:
        """检查系统资源使用情况"""
        try:
            import psutil

            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(Path.cwd().anchor)

            return {
                "status": "healthy" if cpu < self.alert_thresholds["cpu_usage"] else "warning",
                "cpu_usage": cpu,
                "cpu_cores": psutil.cpu_count(),
                "memory_usage": memory.percent,
                "memory_total_gb": memory.total / (1024**3),
                "memory_available_gb": memory.available / (1024**3),
                "disk_usage": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
                "disk_total_gb": disk.total / (1024**3)
            }
        except ImportError:
            logger.warning("[HealthMonitor] psutil未安装，跳过资源检查")
            return {"status": "unknown", "error": "psutil not installed"}
        except Exception as e:
            logger.error(f"[HealthMonitor] 系统资源检查失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _check_services(self) -> Dict[str, Any]:
        """检查服务状态"""
        services = {}

        # 检查各个服务端口
        service_ports = {
            "api_server": 8000,
            "agent_server": 8001,
            "mcp_server": 8003,
            "tts_server": 5046
        }

        for service_name, port in service_ports.items():
            try:
                status = self._check_port("127.0.0.1", port)
                services[service_name] = {
                    "status": "healthy" if status else "down",
                    "port": port
                }
            except Exception as e:
                services[service_name] = {
                    "status": "error",
                    "error": str(e)
                }

        return services

    def _check_port(self, host: str, port: int) -> bool:
        """检查端口是否在监听"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                result = s.connect_ex((host, port))
                return result == 0
        except Exception:
            return False

    async def _check_tasks(self) -> Dict[str, Any]:
        """检查任务执行情况"""
        try:
            # 从MCP调度器获取任务统计
            from mcpserver.mcp_scheduler import MCPScheduler

            # 注意：这里需要访问调度器实例，可能需要修改调度器以提供统计接口
            return {
                "status": "healthy",
                "note": "任务统计功能需要集成到调度器"
            }
        except ImportError:
            return {"status": "unknown", "error": "MCP scheduler not available"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _check_dependencies(self) -> Dict[str, Any]:
        """检查依赖项"""
        dependencies = {}

        # 检查关键依赖
        required_packages = [
            "fastapi",
            "pydantic",
            "aiohttp",
            "openai",
            "asyncio"
        ]

        for package in required_packages:
            try:
                __import__(package)
                dependencies[package] = {"status": "available"}
            except ImportError:
                dependencies[package] = {"status": "missing"}

        # 检查可选依赖
        optional_packages = ["psutil", "radon"]
        for package in optional_packages:
            try:
                __import__(package)
                dependencies[package] = {"status": "available"}
            except ImportError:
                dependencies[package] = {"status": "optional_missing"}

        all_available = all(d["status"] in ["available", "optional_missing"]
                            for d in dependencies.values())

        return {
            "status": "healthy" if all_available else "warning",
            "dependencies": dependencies
        }

    async def _check_configuration(self) -> Dict[str, Any]:
        """检查配置有效性"""
        try:
            if not self.config:
                return {"status": "warning", "error": "配置对象未初始化"}

            issues = []

            # 检查API配置
            if hasattr(self.config, 'api'):
                if not self.config.api.api_key:
                    issues.append("API密钥未配置")
                if not self.config.api.base_url:
                    issues.append("API基础URL未配置")

            # 检查Neo4j配置
            if hasattr(self.config, 'grag'):
                if self.config.grag.enabled:
                    if not self.config.grag.neo4j_uri:
                        issues.append("Neo4j URI未配置")
                    if not self.config.grag.neo4j_password:
                        issues.append("Neo4j密码未配置")

            return {
                "status": "healthy" if not issues else "warning",
                "issues": issues
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _process_health_report(self, report: Dict[str, Any]):
        """处理健康报告，生成告警"""
        alerts = []

        # 检查CPU使用率
        if report["system"].get("cpu_usage", 0) > self.alert_thresholds["cpu_usage"]:
            alerts.append({
                "type": "cpu_high",
                "severity": "warning",
                "message": f"CPU使用率过高: {report['system']['cpu_usage']}%",
                "timestamp": datetime.now().isoformat()
            })

        # 检查内存使用率
        if report["system"].get("memory_usage", 0) > self.alert_thresholds["memory_usage"]:
            alerts.append({
                "type": "memory_high",
                "severity": "warning",
                "message": f"内存使用率过高: {report['system']['memory_usage']}%",
                "timestamp": datetime.now().isoformat()
            })

        # 检查服务状态
        for service_name, status in report["services"].items():
            if status.get("status") == "down":
                alerts.append({
                    "type": "service_down",
                    "severity": "critical",
                    "message": f"服务 {service_name} 未响应 (端口 {status.get('port')})",
                    "timestamp": datetime.now().isoformat()
                })

        # 检查配置问题
        config_issues = report.get("configuration", {}).get("issues", [])
        if config_issues:
            alerts.append({
                "type": "configuration_warning",
                "severity": "warning",
                "message": f"配置问题: {', '.join(config_issues)}",
                "timestamp": datetime.now().isoformat()
            })

        # 保存告警
        self.alerts.extend(alerts)
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

        # 发送告警通知
        if alerts:
            await self._send_alerts(alerts)

    async def _send_alerts(self, alerts: List[Dict[str, Any]]):
        """发送告警通知"""
        logger.warning(f"[HealthMonitor] 检测到 {len(alerts)} 个告警:")
        for alert in alerts:
            logger.warning(f"  [{alert['severity'].upper()}] {alert['message']}")

    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康摘要"""
        if not self.health_history:
            return {"status": "unknown", "message": "暂无健康检查数据"}

        latest_report = self.health_history[-1]

        # 计算总体健康状态
        status = "healthy"
        reasons = []

        if latest_report["system"].get("status") != "healthy":
            status = "warning"
            reasons.append("系统资源异常")

        down_services = [name for name, info in latest_report["services"].items()
                        if info.get("status") != "healthy"]
        if down_services:
            status = "critical"
            reasons.append(f"服务宕机: {', '.join(down_services)}")

        if latest_report["configuration"].get("issues"):
            status = "warning"
            reasons.append("配置问题")

        return {
            "status": status,
            "timestamp": latest_report["timestamp"],
            "active_alerts": len([a for a in self.alerts
                                if a["timestamp"] >= latest_report["timestamp"]]),
            "details": latest_report,
            "reasons": reasons
        }

    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """基于健康报告生成优化建议"""
        suggestions = []

        if not self.health_history:
            return suggestions

        latest = self.health_history[-1]

        # CPU使用率优化建议
        cpu_usage = latest["system"].get("cpu_usage", 0)
        if cpu_usage > 60:
            suggestions.append({
                "category": "performance",
                "severity": "info" if cpu_usage < 80 else "warning",
                "title": "CPU使用率优化",
                "current": f"{cpu_usage}%",
                "suggestion": "考虑降低MCP调度器的并发数或减少历史对话轮数"
            })

        # 内存使用率优化建议
        memory_usage = latest["system"].get("memory_usage", 0)
        if memory_usage > 70:
            suggestions.append({
                "category": "performance",
                "severity": "info" if memory_usage < 85 else "warning",
                "title": "内存使用率优化",
                "current": f"{memory_usage}%",
                "suggestion": "考虑减少历史对话轮数或清理缓存"
            })

        # 磁盘空间优化建议
        disk_usage = latest["system"].get("disk_usage", 0)
        if disk_usage > 80:
            suggestions.append({
                "category": "storage",
                "severity": "warning",
                "title": "磁盘空间不足",
                "current": f"{disk_usage}%",
                "suggestion": "清理日志文件和临时文件"
            })

        # 服务状态建议
        down_services = [name for name, info in latest["services"].items()
                        if info.get("status") == "down"]
        if down_services:
            suggestions.append({
                "category": "reliability",
                "severity": "critical",
                "title": "服务不可用",
                "details": down_services,
                "suggestion": "检查服务日志并重启相关服务"
            })

        return suggestions
