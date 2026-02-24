#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自我优化工具类
提供自我优化相关的工具实现
"""

import asyncio
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import ast

logger = logging.getLogger(__name__)


class SelfOptimizationTools:
    """自我优化工具类"""

    def __init__(self):
        """初始化"""
        self.optimizer = None
        self._init_optimizer()

    def _init_optimizer(self):
        """初始化优化器"""
        try:
            from pathlib import Path
            from system.self_optimization import init_global_optimizer
            from system.config import config

            project_root = Path.cwd()
            self.optimizer = init_global_optimizer(str(project_root), config)
            logger.info("[SelfOptimizationTools] 优化器初始化成功")
        except Exception as e:
            logger.error(f"[SelfOptimizationTools] 优化器初始化失败: {e}")

    async def check_system_health(self, args: Dict[str, Any]) -> str:
        """检查系统健康状态"""
        try:
            if not self.optimizer:
                return "自我优化系统未初始化"

            health_report = await self.optimizer.health_monitor.check_health()
            health_summary = self.optimizer.health_monitor.get_health_summary()

            result = f"""🏥 系统健康检查报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 总体状态: {health_summary.get('status', 'unknown').upper()}
⏰ 检查时间: {health_summary.get('timestamp', '')}

📱 系统资源:
  • CPU使用率: {health_summary['details']['system'].get('cpu_usage', 0)}%
  • 内存使用率: {health_summary['details']['system'].get('memory_usage', 0)}%
  • 磁盘使用率: {health_summary['details']['system'].get('disk_usage', 0)}%

🔌 服务状态:"""

            for service_name, status in health_summary['details']['services'].items():
                status_icon = "✅" if status.get('status') == 'healthy' else "❌"
                result += f"\n  {status_icon} {service_name}: {status.get('status', 'unknown')}"

            # 添加告警信息
            active_alerts = health_summary.get('active_alerts', 0)
            if active_alerts > 0:
                result += f"\n\n⚠️  检测到 {active_alerts} 个活动告警"

            # 添加优化建议
            suggestions = self.optimizer.health_monitor.get_optimization_suggestions()
            if suggestions:
                result += "\n\n💡 优化建议:"
                for i, suggestion in enumerate(suggestions[:3], 1):
                    result += f"\n  {i}. [{suggestion.get('severity', 'info')}] {suggestion.get('title', '')}"
                    result += f"\n     {suggestion.get('suggestion', '')}"

            return result.strip()

        except Exception as e:
            logger.error(f"[SelfOptimizationTools] 健康检查失败: {e}", exc_info=True)
            return f"健康检查失败: {str(e)}"

    async def analyze_performance(self, args: Dict[str, Any]) -> str:
        """分析系统性能"""
        try:
            if not self.optimizer:
                return "自我优化系统未初始化"

            operation_name = args.get("operation_name")

            if operation_name:
                report = self.optimizer.performance_profiler.get_report(operation_name)
                return f"""📈 性能分析报告: {operation_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 调用次数: {report.get('count', 0)}
• 平均耗时: {report.get('avg_time', 0)} 秒
• 最小耗时: {report.get('min_time', 0)} 秒
• 最大耗时: {report.get('max_time', 0)} 秒
• 错误率: {report.get('error_rate', 0)}%
• 错误次数: {report.get('errors', 0)}"""
            else:
                report = self.optimizer.performance_profiler.get_report()

                result = f"""📈 性能分析报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 总览:
  • 总操作数: {report['summary'].get('total_operations', 0)}
  • 总调用次数: {report['summary'].get('total_calls', 0)}
  • 总错误次数: {report['summary'].get('total_errors', 0)}
  • 生成时间: {report['summary'].get('generated_at', '')}

🐌 最慢操作（前5）:"""

                top_slowest = report.get('top_slowest', [])
                for i, (name, stats) in enumerate(top_slowest[:5], 1):
                    result += f"\n  {i}. {name}: 平均 {stats.get('avg_time', 0)} 秒 ({stats.get('count', 0)} 次调用)"

                result += "\n\n🔄 最频繁操作（前5）:"
                top_frequent = report.get('top_frequent', [])
                for i, (name, stats) in enumerate(top_frequent[:5], 1):
                    result += f"\n  {i}. {name}: {stats.get('count', 0)} 次调用"

                # 识别瓶颈
                bottlenecks = self.optimizer.performance_profiler.identify_bottlenecks()
                if bottlenecks:
                    result += "\n\n⚠️  性能瓶颈:"
                    for bottleneck in bottlenecks[:3]:
                        result += f"\n  • {bottleneck.get('operation', 'unknown')}: {bottleneck.get('suggestion', '')}"

                return result.strip()

        except Exception as e:
            logger.error(f"[SelfOptimizationTools] 性能分析失败: {e}", exc_info=True)
            return f"性能分析失败: {str(e)}"

    async def run_optimization(self, args: Dict[str, Any]) -> str:
        """运行自动优化"""
        try:
            if not self.optimizer:
                return "自我优化系统未初始化"

            report = await self.optimizer.run_manual_optimization()

            summary = report.get('summary', {})
            status = summary.get('status', 'unknown')

            result = f"""🔧 自动优化报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 状态: {status.upper()}
⏰ 检查时间: {report.get('timestamp', '')}
⏱️  耗时: {summary.get('elapsed_seconds', 0)} 秒

🏥 健康状态: {summary.get('health_status', 'unknown')}"""

            # 优化结果
            optimizations = report.get('optimizations_applied', [])
            if optimizations:
                result += f"\n\n✅ 已应用优化 ({len(optimizations)} 项):"
                for i, opt in enumerate(optimizations, 1):
                    result += f"\n  {i}. [{opt.get('status', 'unknown')}] {opt.get('type', 'unknown')}"
                    if opt.get('message'):
                        result += f"\n     {opt.get('message', '')}"
            else:
                result += "\n\n✓ 未应用优化（系统运行良好）"

            # 优化建议
            recommendations = report.get('recommendations', [])
            if recommendations:
                result += f"\n\n💡 优化建议 ({len(recommendations)} 项):"
                for i, rec in enumerate(recommendations[:5], 1):
                    severity = rec.get('severity', 'info')
                    result += f"\n  {i}. [{severity.upper()}] {rec.get('title', '')}"
                    if rec.get('suggestion'):
                        result += f"\n     {rec.get('suggestion', '')}"

            return result.strip()

        except Exception as e:
            logger.error(f"[SelfOptimizationTools] 优化执行失败: {e}", exc_info=True)
            return f"优化执行失败: {str(e)}"

    async def analyze_code_quality(self, args: Dict[str, Any]) -> str:
        """分析代码质量"""
        try:
            if not self.optimizer:
                return "自我优化系统未初始化"

            result = await self.optimizer.run_code_analysis()

            code_quality = result.get('code_quality', {})
            refactoring_suggestions = result.get('refactoring_suggestions', [])

            output = f"""📝 代码质量分析报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 代码统计:
  • 总文件数: {code_quality.get('complexity', {}).get('total_files', 0)}
  • 总函数数: {code_quality.get('complexity', {}).get('total_functions', 0)}
  • 总类数: {code_quality.get('complexity', {}).get('total_classes', 0)}
  • 总代码行数: {code_quality.get('complexity', {}).get('total_lines', 0)}

⚠️  高复杂度函数: {code_quality.get('complexity', {}).get('high_complexity_count', 0)} 个
🔄 重复代码: {code_quality.get('duplication', {}).get('duplicated_signatures', 0)} 处"""

            # 重构建议
            if refactoring_suggestions:
                output += f"\n\n🔧 重构建议 ({len(refactoring_suggestions)} 项):"
                for i, suggestion in enumerate(refactoring_suggestions[:5], 1):
                    severity = suggestion.get('severity', 'info')
                    output += f"\n  {i}. [{severity.upper()}] {suggestion.get('title', '')}"
                    output += f"\n     文件: {suggestion.get('file', '')}"
                    if suggestion.get('suggestion'):
                        output += f"\n     {suggestion.get('suggestion', '')}"

            # AI建议
            ai_suggestions = result.get('ai_suggestions', [])
            if ai_suggestions:
                output += f"\n\n🤖 AI优化建议 ({len(ai_suggestions)} 项):"
                for i, suggestion in enumerate(ai_suggestions, 1):
                    output += f"\n  {i}. [{suggestion.get('priority', 'medium').upper()}] {suggestion.get('title', '')}"
                    output += f"\n     {suggestion.get('description', '')}"
                    output += f"\n     行动: {suggestion.get('action', '')}"

            return output.strip()

        except Exception as e:
            logger.error(f"[SelfOptimizationTools] 代码质量分析失败: {e}", exc_info=True)
            return f"代码质量分析失败: {str(e)}"

    async def export_reports(self, args: Dict[str, Any]) -> str:
        """导出所有报告"""
        try:
            if not self.optimizer:
                return "自我优化系统未初始化"

            output_path = self.optimizer.export_full_report()

            return f"""📄 报告导出成功
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 完整报告已导出到: {output_path}

报告包含:
• 健康检查报告
• 性能分析报告
• 优化执行报告
• 代码质量报告
• 优化建议汇总"""

        except Exception as e:
            logger.error(f"[SelfOptimizationTools] 报告导出失败: {e}", exc_info=True)
            return f"报告导出失败: {str(e)}"

    async def get_status(self, args: Dict[str, Any]) -> str:
        """获取自我优化系统状态"""
        try:
            if not self.optimizer:
                return "自我优化系统未初始化"

            status = self.optimizer.get_status()

            result = f"""🔍 自我优化系统状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏃 运行状态: {'✅ 运行中' if status.get('running') else '⏹️  已停止'}
⏰ 检查间隔: {status.get('check_interval', 0)} 秒
📊 总运行次数: {status.get('total_runs', 0)}

🏥 健康状态: {status.get('health_status', 'unknown').upper()}"""

            # 最后一次运行
            last_run = status.get('last_run')
            if last_run:
                summary = last_run.get('summary', {})
                result += f"""

📋 最后一次运行:
  • 时间: {last_run.get('timestamp', '')}
  • 状态: {summary.get('status', 'unknown').upper()}
  • 耗时: {summary.get('elapsed_seconds', 0)} 秒
  • 应用优化: {summary.get('optimizations_count', 0)} 项
  • 生成建议: {summary.get('recommendations_count', 0)} 项"""

            return result.strip()

        except Exception as e:
            logger.error(f"[SelfOptimizationTools] 获取状态失败: {e}", exc_info=True)
            return f"获取状态失败: {str(e)}"

    async def fix_code_issues(self, args: Dict[str, Any]) -> str:
        """修复检测到的代码问题（带备份和自动回滚功能）"""
        try:
            if not self.optimizer:
                return "自我优化系统未初始化"

            auto_fix = args.get("auto_fix", False)
            issue_types = args.get("issue_types", [])

            # 获取代码质量数据
            scan_history = self.optimizer.code_quality_monitor.scan_history
            if not scan_history:
                return "❌ 未找到代码质量分析数据，请先运行代码质量分析"

            latest_scan = scan_history[-1]

            # 收集可修复的问题
            issues_found = []
            code_smells = latest_scan.get("code_smells", {}).get("details", {})

            # BOM字符和非打印字符问题
            if not issue_types or "invalid_non_printable" in issue_types:
                issues_found.extend(self._collect_bom_issues())

            # 弃用的转义序列
            if not issue_types or "deprecated_escape_sequence" in issue_types:
                issues_found.extend(self._collect_escape_sequence_issues())

            if not issues_found:
                return "✅ 未发现需要修复的代码问题"

            if not auto_fix:
                # 仅显示问题，不自动修复
                result = f"🔍 检测到 {len(issues_found)} 个代码问题\n\n"

                for i, issue in enumerate(issues_found[:10], 1):
                    result += f"{i}. 【{issue.get('severity', 'info')}】{issue.get('type', 'unknown')}\n"
                    result += f"   文件: {issue.get('file', 'unknown')}\n"
                    if issue.get('line'):
                        result += f"   行号: {issue.get('line', 'unknown')}\n"
                    result += f"   描述: {issue.get('description', 'unknown')}\n\n"

                if len(issues_found) > 10:
                    result += f"... 还有 {len(issues_found) - 10} 个问题未显示\n\n"

                result += "💡 提示: 使用参数 auto_fix=true 可尝试自动修复问题（会自动备份）"
                return result

            # 自动修复模式 - 带备份和回滚
            result = f"🔧 开始自动修复代码问题...\n"
            result += f"📁 将自动备份修改的文件\n"

            backup_dir = self._create_backup_dir()
            backups = []
            fixed_count = 0
            failed_issues = []

            for issue in issues_found:
                try:
                    issue_type = issue.get("type", "")
                    file_path = issue.get("file")
                    line_num = issue.get("line")

                    # 创建文件备份
                    if file_path and Path(file_path).exists():
                        backup_path = self._backup_file(file_path, backup_dir)
                        backups.append({
                            "original": file_path,
                            "backup": backup_path,
                            "issue": issue
                        })

                    # 修复逻辑
                    if issue_type == "deprecated_escape_sequence":
                        if file_path and line_num:
                            await self._fix_escape_sequence(file_path, line_num)
                            fixed_count += 1
                            result += f"✅ 修复: {file_path}:{line_num} - {issue.get('description', '')}\n"

                    elif issue_type == "invalid_non_printable":
                        if file_path:
                            await self._fix_non_printable(file_path)
                            fixed_count += 1
                            result += f"✅ 修复: {file_path} - 移除无效字符\n"

                except Exception as e:
                    logger.warning(f"修复问题失败: {e}")
                    failed_issues.append(issue)
                    result += f"❌ 修复失败: {issue.get('description', '')} - {str(e)}\n"

            # 验证修复
            if backups:
                validation_errors = await self._validate_fixes(backups)

                if validation_errors:
                    result += f"\n⚠️  验证发现 {len(validation_errors)} 个问题，正在回滚...\n"
                    rollback_count = await self._rollback_backups([b["backup"] for b in backups])
                    result += f"🔄 已回滚 {rollback_count} 个文件\n"
                    result += f"\n❌ 修复失败，已恢复原始状态"
                    return result

            result += f"\n🎉 修复完成: 共修复 {fixed_count}/{len(issues_found)} 个问题"
            result += f"\n📦 备份位置: {backup_dir}"

            if failed_issues:
                result += f"\n⚠️ 部分问题修复失败 ({len(failed_issues)} 个)"

            return result

        except Exception as e:
            logger.error(f"[SelfOptimizationTools] 代码修复失败: {e}", exc_info=True)
            return f"代码修复失败: {str(e)}"

    async def _fix_escape_sequence(self, file_path: str, line_num: int):
        """修复转义序列问题"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if line_num <= len(lines):
                line = lines[line_num - 1]

                # 智能修复转义序列问题
                # 只修复正则表达式中的转义序列
                if 're\\.' in line or 're\\s' in line or 're\\.' in line:
                    # 这可能是正则表达式，不做修改
                    return

                # 修复常见的字符串转义序列问题
                # r'\.' 在普通字符串中应替换为 '\\\\.' 表示字面意思的反斜杠加点
                # 但在正则表达式中应该是正确的

                # 只修复明显的问题：在非原始字符串中使用需要转义的字符
                    if r'\.' in line and 'r"' not in line and "r'" not in line:
                        # 检查是否在正则表达式上下文中
                        if 're\\.' in line or 're\\s' in line or 're\\.' in line or 're\\s' in line:
                            # 正则表达式上下文，保持不变
                            pass
                        else:
                            # 可能是错误的转义，使用原始字符串
                            if r'"\."' in line or r"'\.'" in line:
                                # 将 "\." 转换为 r"\."
                                fixed_line = line.replace(r'\.', r'\\.')
                                lines[line_num - 1] = fixed_line

                if r'\s' in line and 'r"' not in line and "r'" not in line:
                    if r'"\s"' in line or r"'\s'" in line:
                        # 将 "\s" 转换为 r"\s"
                        fixed_line = line.replace(r'\s', r'\\s')
                        lines[line_num - 1] = fixed_line

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)

        except Exception as e:
            logger.warning(f"修复转义序列失败 {file_path}:{line_num}: {e}")
            raise

    async def _fix_non_printable(self, file_path: str):
        """移除文件开头的BOM字符"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()

            # 检查并移除UTF-8 BOM
            if content.startswith(b'\xef\xbb\xbf'):
                content = content[3:]
                with open(file_path, 'wb') as f:
                    f.write(content)
                logger.info(f"已移除BOM字符: {file_path}")

        except Exception as e:
            logger.warning(f"移除非打印字符失败 {file_path}: {e}")
            raise

    def _collect_bom_issues(self) -> List[Dict[str, Any]]:
        """收集BOM字符和非打印字符问题"""
        issues = []
        project_root = Path.cwd()

        for py_file in project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, 'rb') as f:
                    content = f.read()
                    if content.startswith(b'\xef\xbb\xbf'):
                        issues.append({
                            "type": "invalid_non_printable",
                            "severity": "medium",
                            "file": str(py_file),
                            "line": 1,
                            "description": "文件包含UTF-8 BOM字符"
                        })
            except Exception:
                continue

        return issues

    def _collect_escape_sequence_issues(self) -> List[Dict[str, Any]]:
        """收集弃用的转义序列问题"""
        issues = []
        project_root = Path.cwd()

        for py_file in project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    # 检测原始字符串中的转义序列
                    if r'\.' in line and not line.strip().startswith('#'):
                        # 确保不是在原始字符串中
                        if not ('r"' in line or "r'" in line):
                            issues.append({
                                "type": "deprecated_escape_sequence",
                                "severity": "low",
                                "file": str(py_file),
                                "line": i,
                                "description": "字符串中包含可能的转义序列问题"
                            })
            except Exception:
                continue

        return issues

    def _create_backup_dir(self) -> str:
        """创建备份目录"""
        backup_base = Path("logs") / "code_fix_backups"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = backup_base / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        return str(backup_dir)

    def _backup_file(self, file_path: str, backup_dir: str) -> str:
        """备份文件"""
        file_path = Path(file_path)
        backup_path = Path(backup_dir) / file_path.name

        # 如果文件名冲突，添加数字后缀
        counter = 1
        while backup_path.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            backup_path = Path(backup_dir) / f"{stem}_{counter}{suffix}"
            counter += 1

        shutil.copy2(file_path, backup_path)

        # 记录备份映射
        self._record_backup_mapping(backup_dir, backup_path.name, str(file_path))

        logger.info(f"已备份: {file_path} -> {backup_path}")
        return str(backup_path)

    def _record_backup_mapping(self, backup_dir: str, backup_name: str, original_path: str):
        """记录备份映射关系"""
        import json
        record_file = Path(backup_dir) / "backup_record.json"

        # 读取现有记录
        if record_file.exists():
            try:
                with open(record_file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            except Exception:
                records = {}
        else:
            records = {}

        # 更新记录
        records[backup_name] = original_path

        # 写入文件
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

    async def _validate_fixes(self, backups: List[Dict[str, Any]]) -> List[str]:
        """验证修复后的文件是否有效"""
        errors = []

        for backup_info in backups:
            original_path = backup_info["original"]

            try:
                with open(original_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 尝试解析为有效的Python代码
                ast.parse(content)

            except SyntaxError as e:
                errors.append(f"{original_path}: {e}")
                logger.error(f"验证失败 {original_path}: {e}")
            except Exception as e:
                errors.append(f"{original_path}: {e}")
                logger.error(f"验证失败 {original_path}: {e}")

        return errors

    async def _rollback_backups(self, backup_paths: List[str]) -> int:
        """回滚备份文件"""
        rollback_count = 0

        for backup_path in backup_paths:
            try:
                backup_path = Path(backup_path)
                original_path = backup_path.name

                # 尝试查找原始文件位置
                project_root = Path.cwd()
                for py_file in project_root.rglob(original_path):
                    # 从备份文件名中移除数字后缀（如果有）
                    if "_" in py_file.stem:
                        original_name = py_file.stem.rsplit('_', 1)[0] + py_file.suffix
                        original_file = py_file.parent / original_name
                    else:
                        original_file = py_file

                    if original_file.exists():
                        shutil.copy2(backup_path, original_file)
                        rollback_count += 1
                        logger.info(f"已回滚: {backup_path} -> {original_file}")

            except Exception as e:
                logger.warning(f"回滚失败 {backup_path}: {e}")

        return rollback_count

    async def rollback_fixes(self, args: Dict[str, Any]) -> str:
        """手动回滚代码修复"""
        try:
            backup_dir = args.get("backup_dir")
            if not backup_dir:
                # 获取最新的备份目录
                backup_base = Path("logs") / "code_fix_backups"
                if not backup_base.exists():
                    return "❌ 未找到备份目录"

                backup_dirs = sorted(backup_base.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
                if not backup_dirs:
                    return "❌ 未找到任何备份"

                backup_dir = str(backup_dirs[0])

            backup_path = Path(backup_dir)
            if not backup_path.exists():
                return f"❌ 备份目录不存在: {backup_dir}"

            # 查找所有备份文件
            backup_files = list(backup_path.glob("*.py"))
            if not backup_files:
                return f"❌ 备份目录中没有Python文件: {backup_dir}"

            result = f"🔄 开始回滚代码修复...\n"
            result += f"📁 备份目录: {backup_dir}\n"
            result += f"📋 找到 {len(backup_files)} 个备份文件\n\n"

            rollback_count = 0
            failed_count = 0

            # 读取备份记录以获取原始路径
            backup_record_file = backup_path / "backup_record.json"
            backup_map = {}
            if backup_record_file.exists():
                try:
                    import json
                    with open(backup_record_file, 'r', encoding='utf-8') as f:
                        backup_map = json.load(f)
                except Exception:
                    pass

            for backup_file in backup_files:
                try:
                    # 使用备份记录查找原始路径
                    original_path = backup_map.get(backup_file.name)

                    if original_path and Path(original_path).exists():
                        shutil.copy2(backup_file, original_path)
                        rollback_count += 1
                        result += f"✅ 已回滚: {original_path}\n"
                    else:
                        # 回退到原来的查找逻辑，但限制查找范围
                        project_root = Path.cwd()
                        found = False

                        # 只查找前几级目录，避免误匹配
                        search_dirs = [
                            project_root / "system",
                            project_root / "ui" / "components",
                            project_root / "ui" / "utils",
                            project_root / "mcpserver",
                            project_root / "agentserver"
                        ]

                        for search_dir in search_dirs:
                            if not search_dir.exists():
                                continue

                            original_file = search_dir / backup_file.name
                            if original_file.exists():
                                shutil.copy2(backup_file, original_file)
                                rollback_count += 1
                                result += f"✅ 已回滚: {original_file}\n"
                                found = True
                                break

                        if not found:
                            result += f"⚠️ 未找到原始文件: {backup_file.name}\n"

                except Exception as e:
                    failed_count += 1
                    result += f"❌ 回滚失败 {backup_file.name}: {e}\n"
                    logger.warning(f"回滚失败 {backup_file}: {e}")

            result += f"\n🎉 回滚完成: {rollback_count}/{len(backup_files)} 个文件"

            if failed_count > 0:
                result += f"\n⚠️ {failed_count} 个文件回滚失败"

            return result

        except Exception as e:
            logger.error(f"[SelfOptimizationTools] 回滚失败: {e}", exc_info=True)
            return f"回滚失败: {str(e)}"

    async def list_backups(self, args: Dict[str, Any]) -> str:
        """列出所有备份"""
        try:
            backup_base = Path("logs") / "code_fix_backups"
            if not backup_base.exists():
                return "❌ 未找到备份目录"

            backup_dirs = sorted(backup_base.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)

            if not backup_dirs:
                return "❌ 未找到任何备份"

            result = f"📂 代码修复备份列表\n"
            result += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            result += f"共找到 {len(backup_dirs)} 个备份\n\n"

            for i, backup_dir in enumerate(backup_dirs, 1):
                backup_files = list(backup_dir.glob("*.py"))
                mtime = datetime.fromtimestamp(backup_dir.stat().st_mtime)

                result += f"{i}. 📁 {backup_dir.name}\n"
                result += f"   📅 创建时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')}\n"
                result += f"   📄 文件数: {len(backup_files)}\n"
                result += f"   📍 路径: {backup_dir}\n\n"

            return result.strip()

        except Exception as e:
            logger.error(f"[SelfOptimizationTools] 列出备份失败: {e}", exc_info=True)
            return f"列出备份失败: {str(e)}"


# 创建全局工具实例
_tools_instance: Optional[SelfOptimizationTools] = None


def get_tools_instance() -> SelfOptimizationTools:
    """获取工具实例"""
    global _tools_instance
    if _tools_instance is None:
        _tools_instance = SelfOptimizationTools()
    return _tools_instance


# 工具注册表
TOOLS_REGISTRY = {
    "check_system_health": {
        "name": "check_system_health",
        "description": "检查系统健康状态，包括CPU、内存、磁盘使用率和各服务状态",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    "analyze_performance": {
        "name": "analyze_performance",
        "description": "分析系统性能，包括各操作的耗时、调用次数和错误率",
        "parameters": {
            "type": "object",
            "properties": {
                "operation_name": {
                    "type": "string",
                    "description": "指定要分析的操作名称，不指定则分析所有操作"
                }
            }
        }
    },
    "run_optimization": {
        "name": "run_optimization",
        "description": "运行自动优化，基于健康检查和性能分析结果自动优化系统",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    "analyze_code_quality": {
        "name": "analyze_code_quality",
        "description": "分析代码质量，检测复杂度、重复代码、代码异味等问题",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    "export_reports": {
        "name": "export_reports",
        "description": "导出所有分析报告到logs目录",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    "get_status": {
        "name": "get_status",
        "description": "获取自我优化系统的运行状态",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    "fix_code_issues": {
        "name": "fix_code_issues",
        "description": "修复检测到的代码问题，支持自动修复BOM字符、转义序列等问题，会自动备份文件并在修复失败时自动回滚",
        "parameters": {
            "type": "object",
            "properties": {
                "auto_fix": {
                    "type": "boolean",
                    "description": "是否自动修复问题，false时仅显示问题列表"
                },
                "issue_types": {
                    "type": "array",
                    "description": "指定要修复的问题类型，如['deprecated_escape_sequence', 'invalid_non_printable']"
                }
            }
        }
    },
    "rollback_fixes": {
        "name": "rollback_fixes",
        "description": "手动回滚代码修复，从备份恢复文件",
        "parameters": {
            "type": "object",
            "properties": {
                "backup_dir": {
                    "type": "string",
                    "description": "指定要回滚的备份目录路径，不指定则回滚最新的备份"
                }
            }
        }
    },
    "list_backups": {
        "name": "list_backups",
        "description": "列出所有代码修复备份",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}


async def call_tool(tool_name: str, args: Dict[str, Any]) -> str:
    """
    调用自我优化工具

    Args:
        tool_name: 工具名称
        args: 工具参数

    Returns:
        工具执行结果
    """
    tools = get_tools_instance()

    tool_methods = {
        "check_system_health": tools.check_system_health,
        "analyze_performance": tools.analyze_performance,
        "run_optimization": tools.run_optimization,
        "analyze_code_quality": tools.analyze_code_quality,
        "export_reports": tools.export_reports,
        "get_status": tools.get_status,
        "fix_code_issues": tools.fix_code_issues,
        "rollback_fixes": tools.rollback_fixes,
        "list_backups": tools.list_backups
    }

    method = tool_methods.get(tool_name)
    if method is None:
        return f"未知工具: {tool_name}"

    return await method(args)
