#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码质量监控器
持续监控代码库质量，检测问题
"""

import logging
import subprocess
import ast
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class CodeQualityMonitor:
    """代码质量监控器"""

    def __init__(self, project_root: str):
        """
        初始化代码质量监控器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root)
        self.baseline_metrics: Optional[Dict[str, Any]] = None
        self.issues: List[Dict[str, Any]] = []
        self.scan_history: List[Dict[str, Any]] = []

    async def analyze_codebase(self) -> Dict[str, Any]:
        """
        分析整个代码库质量

        Returns:
            分析报告
        """
        logger.info("[CodeQualityMonitor] 开始分析代码库...")

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "complexity": await self._analyze_complexity(),
            "duplication": await self._detect_duplication(),
            "code_smells": await self._detect_code_smells(),
            "security_issues": await self._detect_security_issues(),
            "file_structure": await self._analyze_file_structure(),
            "dependencies": await self._analyze_dependencies()
        }

        # 与基线对比
        if self.baseline_metrics:
            metrics["comparison"] = self._compare_with_baseline(metrics)

        # 保存历史
        self.scan_history.append(metrics)
        if len(self.scan_history) > 50:
            self.scan_history.pop(0)

        # 设置基线（首次运行）
        if self.baseline_metrics is None:
            self.baseline_metrics = metrics
            logger.info("[CodeQualityMonitor] 已设置基线指标")

        return metrics

    async def _analyze_complexity(self) -> Dict[str, Any]:
        """分析代码复杂度"""
        logger.info("[CodeQualityMonitor] 分析代码复杂度...")

        total_files = 0
        total_functions = 0
        total_classes = 0
        total_lines = 0
        high_complexity_functions = []

        try:
            for py_file in self.project_root.rglob("*.py"):
                # 跳过venv和__pycache__
                if "venv" in str(py_file) or "__pycache__" in str(py_file):
                    continue

                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    total_files += 1
                    total_lines += len(content.splitlines())

                    # 解析AST
                    tree = ast.parse(content)

                    # 统计类和函数
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            total_functions += 1
                            # 计算圈复杂度（简化版）
                            complexity = self._calculate_complexity(node)
                            if complexity > 10:
                                high_complexity_functions.append({
                                    "file": str(py_file.relative_to(self.project_root)),
                                    "function": node.name,
                                    "line": node.lineno,
                                    "complexity": complexity
                                })
                        elif isinstance(node, ast.ClassDef):
                            total_classes += 1

                except (SyntaxError, UnicodeDecodeError) as e:
                    logger.warning(f"[CodeQualityMonitor] 无法解析文件 {py_file}: {e}")
                    continue

        except Exception as e:
            logger.error(f"[CodeQualityMonitor] 复杂度分析失败: {e}")

        high_complexity_ratio = len(high_complexity_functions) / total_functions if total_functions > 0 else 0

        return {
            "total_files": total_files,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "total_lines": total_lines,
            "high_complexity_count": len(high_complexity_functions),
            "high_complexity_ratio": round(high_complexity_ratio * 100, 2),
            "high_complexity_functions": high_complexity_functions[:20]  # 只保留前20个
        }

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """计算函数的圈复杂度"""
        complexity = 1  # 基础复杂度

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With,
                                  ast.AsyncWith, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    async def _detect_duplication(self) -> Dict[str, Any]:
        """检测重复代码"""
        logger.info("[CodeQualityMonitor] 检测重复代码...")

        # 简化版检测：查找相似的函数签名
        function_signatures = defaultdict(list)

        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # 简化的签名：函数名 + 参数数量
                        sig = f"{node.name}_{len(node.args.args)}"
                        function_signatures[sig].append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": node.lineno
                        })

            except (SyntaxError, UnicodeDecodeError):
                continue

        # 找出重复的
        duplicated = {sig: locs for sig, locs in function_signatures.items() if len(locs) > 1}

        return {
            "duplicated_signatures": len(duplicated),
            "examples": [
                {
                    "signature": sig,
                    "locations": locs
                }
                for sig, locs in list(duplicated.items())[:10]
            ]
        }

    async def _detect_code_smells(self) -> Dict[str, Any]:
        """检测代码异味"""
        logger.info("[CodeQualityMonitor] 检测代码异味...")

        smells = {
            "long_functions": [],
            "long_classes": [],
            "too_many_params": [],
            "deep_nesting": []
        }

        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                content = ''.join(lines)
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    # 长函数（超过100行）
                    if isinstance(node, ast.FunctionDef):
                        func_lines = node.end_lineno - node.lineno if node.end_lineno else 0
                        if func_lines > 100:
                            smells["long_functions"].append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "function": node.name,
                                "line": node.lineno,
                                "length": func_lines
                            })

                        # 参数过多（超过5个）
                        if len(node.args.args) > 5:
                            smells["too_many_params"].append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "function": node.name,
                                "line": node.lineno,
                                "params_count": len(node.args.args)
                            })

                    # 长类
                    elif isinstance(node, ast.ClassDef):
                        class_lines = node.end_lineno - node.lineno if node.end_lineno else 0
                        if class_lines > 300:
                            smells["long_classes"].append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "class": node.name,
                                "line": node.lineno,
                                "length": class_lines
                            })

            except (SyntaxError, UnicodeDecodeError):
                continue

        return {
            "long_functions_count": len(smells["long_functions"]),
            "long_classes_count": len(smells["long_classes"]),
            "too_many_params_count": len(smells["too_many_params"]),
            "details": {k: v[:10] for k, v in smells.items()}  # 只保留前10个
        }

    async def _detect_security_issues(self) -> Dict[str, Any]:
        """检测安全问题"""
        logger.info("[CodeQualityMonitor] 检测安全问题...")

        issues = {
            "hardcoded_credentials": [],
            "insecure_eval": [],
            "sql_injection_risk": [],
            "debug_statements": []
        }

        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    # 硬编码凭证（简单检测）
                    if "password" in line.lower() and "=" in line and '"' in line:
                        issues["hardcoded_credentials"].append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": i,
                            "code": line.strip()
                        })

                    # 不安全的eval
                    if "eval(" in line:
                        issues["insecure_eval"].append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": i,
                            "code": line.strip()
                        })

                    # SQL注入风险
                    if "execute(" in line and "format" in line or "%" in line:
                        issues["sql_injection_risk"].append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": i,
                            "code": line.strip()
                        })

                    # 调试语句
                    if "print(" in line and "debug" in line.lower():
                        issues["debug_statements"].append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": i,
                            "code": line.strip()
                        })

            except UnicodeDecodeError:
                continue

        return {
            "hardcoded_credentials_count": len(issues["hardcoded_credentials"]),
            "insecure_eval_count": len(issues["insecure_eval"]),
            "sql_injection_risk_count": len(issues["sql_injection_risk"]),
            "debug_statements_count": len(issues["debug_statements"]),
            "details": {k: v[:10] for k, v in issues.items()}
        }

    async def _analyze_file_structure(self) -> Dict[str, Any]:
        """分析文件结构"""
        logger.info("[CodeQualityMonitor] 分析文件结构...")

        structure = {
            "total_python_files": 0,
            "directories": defaultdict(int),
            "files_by_directory": defaultdict(list)
        }

        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            structure["total_python_files"] += 1

            # 统计目录
            parent = py_file.parent.relative_to(self.project_root)
            structure["directories"][str(parent)] += 1
            structure["files_by_directory"][str(parent)].append(py_file.name)

        return structure

    async def _analyze_dependencies(self) -> Dict[str, Any]:
        """分析依赖关系"""
        logger.info("[CodeQualityMonitor] 分析依赖关系...")

        imports = defaultdict(set)
        external_imports = set()

        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module = alias.name.split('.')[0]
                            imports[str(py_file.relative_to(self.project_root))].add(module)
                            if not module.startswith('.'):
                                external_imports.add(module)

                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            module = node.module.split('.')[0]
                            imports[str(py_file.relative_to(self.project_root))].add(module)
                            if not module.startswith('.'):
                                external_imports.add(module)

            except (SyntaxError, UnicodeDecodeError):
                continue

        return {
            "total_external_imports": len(external_imports),
            "external_imports": sorted(list(external_imports)),
            "internal_dependencies": {
                file: sorted(list(mods))
                for file, mods in list(imports.items())[:20]
            }
        }

    def _compare_with_baseline(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """与基线对比"""
        comparison = {
            "complexity_change": {},
            "new_issues": [],
            "fixed_issues": []
        }

        if not self.baseline_metrics:
            return comparison

        baseline_complexity = self.baseline_metrics.get("complexity", {})
        current_complexity = current_metrics.get("complexity", {})

        # 复杂度变化
        comparison["complexity_change"] = {
            "total_functions_change": current_complexity.get("total_functions", 0) -
                                      baseline_complexity.get("total_functions", 0),
            "high_complexity_change": current_complexity.get("high_complexity_count", 0) -
                                       baseline_complexity.get("high_complexity_count", 0)
        }

        return comparison

    async def run_linter(self) -> Dict[str, Any]:
        """
        运行代码检查工具（如果可用）

        Returns:
            检查结果
        """
        logger.info("[CodeQualityMonitor] 运行代码检查工具...")

        results = {
            "pylint": None,
            "flake8": None,
            "mypy": None
        }

        # 尝试运行pylint
        try:
            result = subprocess.run(
                ["pylint", str(self.project_root), "--output-format=json"],
                capture_output=True,
                text=True,
                timeout=60
            )

            try:
                import json
                pylint_results = json.loads(result.stdout)
                results["pylint"] = {
                    "status": "success",
                    "issues_count": len(pylint_results),
                    "issues": pylint_results[:50]  # 只保留前50个
                }
            except json.JSONDecodeError:
                results["pylint"] = {
                    "status": "error",
                    "message": "无法解析pylint输出"
                }

        except FileNotFoundError:
            results["pylint"] = {"status": "not_installed"}
        except subprocess.TimeoutExpired:
            results["pylint"] = {"status": "timeout"}
        except Exception as e:
            results["pylint"] = {"status": "error", "message": str(e)}

        # 尝试运行flake8
        try:
            result = subprocess.run(
                ["flake8", str(self.project_root), "--format=json"],
                capture_output=True,
                text=True,
                timeout=60
            )

            try:
                import json
                flake8_results = json.loads(result.stdout)
                results["flake8"] = {
                    "status": "success",
                    "issues_count": len(flake8_results),
                    "issues": flake8_results[:50]
                }
            except json.JSONDecodeError:
                results["flake8"] = {
                    "status": "error",
                    "message": "无法解析flake8输出"
                }

        except FileNotFoundError:
            results["flake8"] = {"status": "not_installed"}
        except subprocess.TimeoutExpired:
            results["flake8"] = {"status": "timeout"}
        except Exception as e:
            results["flake8"] = {"status": "error", "message": str(e)}

        return results

    def get_refactoring_suggestions(self) -> List[Dict[str, Any]]:
        """获取重构建议"""
        if not self.scan_history:
            return []

        latest = self.scan_history[-1]
        suggestions = []

        # 高复杂度函数
        complexity = latest.get("complexity", {})
        high_complexity = complexity.get("high_complexity_functions", [])

        for func in high_complexity[:5]:
            suggestions.append({
                "type": "refactor",
                "severity": "medium" if func["complexity"] < 20 else "high",
                "title": "函数复杂度过高",
                "file": func["file"],
                "function": func["function"],
                "line": func["line"],
                "complexity": func["complexity"],
                "suggestion": f"函数 '{func['function']}' 的复杂度为 {func['complexity']}，建议拆分为更小的函数"
            })

        # 长函数
        smells = latest.get("code_smells", {})
        long_functions = smells.get("long_functions", [])

        for func in long_functions[:5]:
            suggestions.append({
                "type": "refactor",
                "severity": "medium" if func["length"] < 150 else "high",
                "title": "函数过长",
                "file": func["file"],
                "function": func["function"],
                "line": func["line"],
                "length": func["length"],
                "suggestion": f"函数 '{func['function']}' 有 {func['length']} 行，建议拆分"
            })

        # 参数过多
        too_many_params = smells.get("too_many_params", [])

        for func in too_many_params[:5]:
            suggestions.append({
                "type": "refactor",
                "severity": "low",
                "title": "参数过多",
                "file": func["file"],
                "function": func["function"],
                "line": func["line"],
                "params_count": func["params_count"],
                "suggestion": f"函数 '{func['function']}' 有 {func['params_count']} 个参数，考虑使用参数对象"
            })

        return suggestions

    def export_report(self, output_path: Optional[str] = None) -> str:
        """导出代码质量报告"""
        import json

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(Path("logs") / f"code_quality_report_{timestamp}.json")

        if not self.scan_history:
            raise ValueError("没有代码质量分析数据")

        report = {
            "latest_analysis": self.scan_history[-1],
            "refactoring_suggestions": self.get_refactoring_suggestions(),
            "baseline": self.baseline_metrics
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"[CodeQualityMonitor] 代码质量报告已导出到: {output_path}")
        return output_path
