"""
LifeBook MCP Tools - AI记忆管理工具集
实现弥娅的长期记忆能力
"""

import os
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import aiofiles

class LifeBookTools:
    """LifeBook 工具集 - 为弥娅提供记忆能力"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 LifeBook 工具

        Args:
            config: 配置字典
        """
        self.config = config
        self.lifebook_path = Path(config.get("lifebook_path", "LifeBook"))
        self.diary_dir = self.lifebook_path / "1.人生书/2.日记"
        self.template_dir = self.diary_dir / "0.template"
        self.node_dir = self.lifebook_path / "1.人生书/1.Node"

        # 确保目录存在
        self._ensure_directories()

    def _ensure_directories(self):
        """确保必要的目录存在"""
        dirs = [
            self.lifebook_path,
            self.diary_dir,
            self.template_dir,
            self.node_dir
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    async def read_lifebook_context(self, args: Dict[str, Any]) -> str:
        """
        读取 LifeBook 历史上下文

        Args:
            args: 参数字典
                - months: 回溯月数，默认为 3
                - max_tokens: 最大 token 数限制，默认为 8000

        Returns:
            包含历史上下文的文本
        """
        try:
            months = args.get("months", 3)
            max_tokens = args.get("max_tokens", 8000)

            # 计算截止日期
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)

            # 构建上下文
            context = []
            context.append(f"# 📖 LifeBook 历史回顾")
            context.append(f"⏰ 回溯范围: {months} 个月")
            context.append(f"📅 开始日期: {start_date.strftime('%Y-%m-%d')}")
            context.append(f"📅 结束日期: {end_date.strftime('%Y-%m-%d')}")
            context.append("")

            # 1. 读取年度总结（最近的）
            year_summary = await self._get_year_summary()
            if year_summary:
                context.append("## 👑 年度总结")
                context.append(year_summary)
                context.append("---\n")

            # 2. 读取季度总结
            quarter_summaries = await self._get_quarter_summaries(start_date)
            for qs in quarter_summaries:
                context.append("## 🏆 季度总结")
                context.append(qs)
                context.append("---\n")

            # 3. 读取月度总结（回溯月份内的）
            month_summaries = await self._get_month_summaries(start_date)
            for ms in month_summaries:
                context.append("## 🌙 月度总结")
                context.append(ms)
                context.append("---\n")

            # 4. 读取周度总结（回溯月份内的）
            week_summaries = await self._get_week_summaries(start_date)
            for ws in week_summaries:
                context.append("## 📆 周度总结")
                context.append(ws)
                context.append("---\n")

            # 5. 读取最近的日记（最多7天）
            daily_entries = await self._get_daily_entries(start_date, days=7)
            for de in daily_entries:
                context.append("## 📝 日记")
                context.append(de)
                context.append("---\n")

            full_text = "\n".join(context)

            # Token 限制处理
            if max_tokens and len(full_text) > max_tokens * 1.5:
                # 简单截断（实际应该更智能地折叠）
                full_text = full_text[:int(max_tokens * 1.5)] + "\n\n[内容已截断]"

            return full_text

        except Exception as e:
            return f"❌ 读取 LifeBook 失败: {str(e)}"

    async def write_diary(self, args: Dict[str, Any]) -> str:
        """
        写入日记

        Args:
            args: 参数字典
                - content: 日记内容（必填）
                - date: 日期，格式 YYYY-MM-DD，默认为今天
                - tags: 标签列表，如 ["#重要", "#和弥娅聊天"]
                - author: 作者，"user" 或 "ai"，默认为 "user"
                - weather: 天气，可选

        Returns:
            写入结果
        """
        try:
            # 调试日志
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[LifeBook] write_diary 调用, args: {args}")

            # 获取作者（用户或AI）
            author = args.get("author", "user")

            # 支持 content 和 param_name 两种参数名称
            content = args.get("content", "") or args.get("param_name", "")
            logger.info(f"[LifeBook] 原始 content: '{content}', author: {author}")

            # AI 日记不处理前缀（保持原始格式）
            if author == "ai":
                # AI 日记直接使用原始内容，不做前缀处理
                pass
            elif content:
                # 用户日记去除指令前缀
                prefixes_to_remove = [
                    "弥娅，记下来，",
                    "记下来，",
                    "弥娅，记住，",
                    "记住，",
                    "弥娅，记录，",
                    "记录，",
                    "弥娅，记：",
                    "记：",
                ]
                for prefix in prefixes_to_remove:
                    if content.startswith(prefix):
                        content = content[len(prefix):]
                        break

                # 去除"我今天"这类时间前缀（只在前面没有匹配到时才处理）
                if content.startswith("我今天"):
                    content = content[3:]
                elif content.startswith("今天"):
                    content = content[2:]

            logger.info(f"[LifeBook] 处理后 content: '{content}'")

            if not content or not content.strip():
                logger.warning(f"[LifeBook] 日记内容为空, 原始: '{args.get('content', '') or args.get('param_name', '')}'")
                return "❌ 日记内容不能为空"

            # 处理日期
            date_str = args.get("date", "")
            if not date_str:
                date_str = datetime.now().strftime("%Y-%m-%d")
            else:
                # 验证日期格式
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    return f"❌ 日期格式错误，应为 YYYY-MM-DD"

            # 处理标签
            tags = args.get("tags", [])
            if author == "ai":
                tags = ["弥娅日记"] + tags
            tags_str = " ".join(tags) if tags else ""

            # 获取天气（可选）
            weather = args.get("weather", "")

            # 构建文件路径
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            year = date_obj.strftime("%Y")
            month = date_obj.strftime("%m")
            day_str = date_obj.strftime("%d")
            date_only = date_obj.strftime("%Y-%m-%d")

            year_dir = self.diary_dir / year
            year_dir.mkdir(exist_ok=True)

            # AI 日记使用专门的目录结构：年/月-日/AI/
            if author == "ai":
                date_dir = year_dir / f"{month}-{day_str}"
                date_dir.mkdir(exist_ok=True)
                ai_dir = date_dir / "AI"
                ai_dir.mkdir(exist_ok=True)
                filename = f"ai_{date_only}.md"
                filepath = ai_dir / filename
            else:
                # 用户日记：年/月-日/日期.md
                date_dir = year_dir / f"{month}-{day_str}"
                date_dir.mkdir(exist_ok=True)
                filename = f"{date_only}.md"
                filepath = date_dir / filename

            # 读取模板（如果存在）
            template_path = self.template_dir / "1.日记模板.md"
            template_content = ""
            if template_path.exists():
                async with aiofiles.open(template_path, encoding="utf-8") as f:
                    template_content = await f.read()

            # 构建日记内容
            weekday = date_obj.strftime("%A")

            if author == "ai":
                # AI 日记格式
                diary_header = f"##### {date_obj.strftime('%Y年%m月%d日')} - {weekday} - 弥娅日记"
                if weather:
                    diary_header += f" - {weather}"
            else:
                # 用户日记格式
                diary_header = f"##### {date_obj.strftime('%Y年%m月%d日')} - {weekday}"
                if weather:
                    diary_header += f" - {weather}"

            # 如果文件已存在，追加内容
            if filepath.exists():
                async with aiofiles.open(filepath, encoding="utf-8") as f:
                    existing_content = await f.read()
                new_content = existing_content + f"\n\n{diary_header}\n\n{content}"
            else:
                # 使用模板或简单格式
                if template_content:
                    # 替换所有模板占位符
                    new_content = template_content.replace(
                        "{{date:YYYY-MM-DD}}",
                        date_obj.strftime('%Y-%m-%d')
                    ).replace(
                        "{{date:YYYY年MM月DD日}}",
                        date_obj.strftime('%Y年%m月%d日')
                    ).replace(
                        "{{date:dddd}}",
                        weekday
                    ).replace(
                        "天气",
                        weather if weather else ""
                    )

                    # 插入内容到思考与感悟或今日流水
                    if "💡 思考与感悟" in new_content:
                        new_content = new_content.replace(
                            "*在这里写下你对今天事件的解构和思考。*",
                            content
                        )
                    elif "📝 今日流水" in new_content:
                        new_content = new_content.replace(
                            "**正文：**",
                            f"**正文：**\n\n{content}"
                        )

                    # AI日记不需要模板头部，直接使用简单格式
                    if author == "ai":
                        new_content = f"---\n{diary_header}\n\n{content}"
                else:
                    new_content = f"---\n{diary_header}\n\n{content}"

                # 添加标签
                if tags_str and author != "ai":
                    new_content = f"---\ntags:\n  - 日记\n  - {tags_str.replace('#', '')}\n\n{new_content}"

            # 写入文件
            async with aiofiles.open(filepath, mode='w', encoding="utf-8") as f:
                await f.write(new_content)

            return f"✅ 日记已写入: {filepath}"

        except Exception as e:
            return f"❌ 写入日记失败: {str(e)}"

    async def generate_summary(self, args: Dict[str, Any]) -> str:
        """
        生成总结（周度/月度/季度）

        Args:
            args: 参数字典
                - type: 总结类型，可选 "week", "month", "quarter", "year"
                - period: 时期，格式根据类型不同
                    * week: YYYY-MM-Wn 或 Wn
                    * month: YYYY-MM
                    * quarter: YYYY-Qn 或 Qn
                    * year: YYYY
                - preview: 预览模式，默认为 true
                - auto_apply: 自动应用，默认为 false

        Returns:
            生成的总结内容
        """
        try:
            summary_type = args.get("type", "week")
            period = args.get("period", "")
            preview = args.get("preview", True)
            auto_apply = args.get("auto_apply", not preview)

            # 读取 AI 使用手册了解规则
            ai_manual_path = self.lifebook_path / "1.人生书/0.使用手册/1.AI使用手册.md"
            ai_manual = ""
            if ai_manual_path.exists():
                async with aiofiles.open(ai_manual_path, encoding="utf-8") as f:
                    ai_manual = await f.read()

            # 根据类型收集输入数据
            input_data = ""
            template_path = ""

            if summary_type == "week":
                input_data = await self._get_weekly_diaries(period)
                template_path = self.template_dir / "2.周度总结模板.md"
            elif summary_type == "month":
                input_data = await self._get_monthly_weeks(period)
                template_path = self.template_path / "3.月度总结模板.md"
            elif summary_type == "quarter":
                input_data = await self._get_quarterly_months(period)
                template_path = self.template_path / "4.季度总结模板.md"
            elif summary_type == "year":
                input_data = await self._get_yearly_quarters(period)
            else:
                return f"❌ 不支持的总结类型: {summary_type}"

            # 读取模板
            template = ""
            if template_path and template_path.exists():
                async with aiofiles.open(template_path, encoding="utf-8") as f:
                    template = await f.read()

            # 如果没有数据，返回提示
            if not input_data or input_data in ["[周度日记数据]", "[月度周总结数据]", "[季度月总结数据]", "[年度季度总结数据]"]:
                return f"⚠️ {summary_type} 没有找到相关数据，请先记录日记"

            # 构建提示词让 LLM 生成总结
            prompt = f"""请根据以下日记数据生成{summary_type}总结：

【模板格式】
{template}

【AI使用手册】
{ai_manual}

【日记数据】
{input_data}

【要求】
1. 使用模板格式
2. 总结重要事件、感悟和成长
3. 保持简洁但全面
4. 用第一人称"我"来写"""

            # 导入 LLM 客户端
            try:
                from game.core.llm_adapter import LLMAdapter
                llm = LLMAdapter()
                summary_content = await llm.chat(prompt)
            except Exception as e:
                logger.warning(f"调用 LLM 生成总结失败: {e}")
                return f"⚠️ 无法自动生成总结，原始数据：\n{input_data}"

            # 如果是预览模式，返回预览
            if preview:
                result = {
                    "type": summary_type,
                    "period": period,
                    "summary": summary_content,
                    "preview_mode": preview
                }
                return json.dumps(result, ensure_ascii=False, indent=2)

            # 如果自动应用，写入文件
            # 确定文件路径
            date_obj = datetime.now()
            if summary_type == "week":
                year = date_obj.strftime("%Y")
                month = date_obj.strftime("%m")
                # 简单周数计算
                week_num = (date_obj.day - 1) // 7 + 1
                filename = f"0-{year}年第{week_num}周总结.md"
                filepath = self.diary_dir / year / month / filename
            elif summary_type == "month":
                year = date_obj.strftime("%Y")
                month = date_obj.strftime("%m")
                filename = f"0-{month}月总结.md"
                filepath = self.diary_dir / year / month / filename
            elif summary_type == "quarter":
                year = date_obj.strftime("%Y")
                quarter = (date_obj.month - 1) // 3 + 1
                filename = f"0-{year}年Q{quarter}总结.md"
                filepath = self.diary_dir / year / filename
            elif summary_type == "year":
                year = date_obj.strftime("%Y")
                filename = f"0-{year}年度总结.md"
                filepath = self.diary_dir / filename
            else:
                return f"❌ 不支持的总结类型: {summary_type}"

            # 写入文件
            filepath.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(filepath, mode='w', encoding="utf-8") as f:
                await f.write(summary_content)

            return f"✅ {summary_type}总结已生成并保存: {filepath}"

        except Exception as e:
            return f"❌ 生成总结失败: {str(e)}"

    async def create_node(self, args: Dict[str, Any]) -> str:
        """
        创建节点（人物节点或阶段性节点）

        Args:
            args: 参数字典
                - name: 节点名称
                - type: 节点类型，"character" 或 "stage"
                - description: 节点描述
                - create_date: 创建日期，默认为今天

        Returns:
            创建结果
        """
        try:
            # 支持 param_name 和显式参数
            param_name = args.get("param_name", "")
            name = args.get("name", "")
            node_type = args.get("type", "character")
            description = args.get("description", "")
            create_date = args.get("create_date", datetime.now().strftime("%Y-%m-%d"))

            # 如果提供了 param_name，尝试解析自然语言
            if param_name and not name and not description:
                # 去除常见的指令前缀
                prefixes_to_remove = [
                    "弥娅，创建人物节点，",
                    "创建人物节点，",
                    "创建人物节点：",
                    "创建节点，",
                    "创建节点：",
                    "弥娅，创建节点，",
                    "弥娅，创建节点：",
                ]
                for prefix in prefixes_to_remove:
                    if param_name.startswith(prefix):
                        param_name = param_name[len(prefix):]
                        break

                # 简单解析：假设格式为 "XXX，YYY" 或 "XXX：YYY"
                if "，" in param_name or "," in param_name:
                    parts = re.split('[，,]', param_name)
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        description = parts[1].strip()
                    else:
                        name = param_name.strip()
                elif "：" in param_name or ":" in param_name:
                    parts = re.split('[：:]', param_name)
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        description = parts[1].strip()
                    else:
                        name = param_name.strip()
                else:
                    name = param_name.strip()
                    description = ""

            if not name:
                return "❌ 节点名称不能为空"

            # 确定子目录
            if node_type == "character":
                subdir = self.node_dir / "角色节点示例"
            elif node_type == "stage":
                subdir = self.node_dir / "阶段性节点示例"
            else:
                return f"❌ 不支持的节点类型: {node_type}"

            subdir.mkdir(exist_ok=True)

            # 构建文件名
            filename = f"{name}({create_date}创建).md"
            filepath = subdir / filename

            # 检查是否已存在
            if filepath.exists():
                return f"⚠️ 节点已存在: {filepath}"

            # 构建节点内容
            content = f"""---
type: {node_type}
created: {create_date}
---

# {name}

{description}

## 关联事件
<!-- 这里会自动关联到相关的日记文件 -->
"""

            # 写入文件
            async with aiofiles.open(filepath, mode='w', encoding="utf-8") as f:
                await f.write(content)

            return f"✅ 节点已创建: {filepath}"

        except Exception as e:
            return f"❌ 创建节点失败: {str(e)}"

    async def list_nodes(self, args: Dict[str, Any]) -> str:
        """
        列出所有节点

        Args:
            args: 参数字典
                - node_type: 节点类型过滤，可选 "character", "stage"

        Returns:
            节点列表
        """
        try:
            node_type = args.get("node_type", "")
            nodes = []

            # 遍历节点目录
            for subdir in ["角色节点示例", "阶段性节点示例"]:
                dir_path = self.node_dir / subdir
                if not dir_path.exists():
                    continue

                for file in dir_path.glob("*.md"):
                    # 类型过滤
                    if node_type:
                        if node_type == "character" and "角色" not in subdir:
                            continue
                        if node_type == "stage" and "阶段" not in subdir:
                            continue

                    nodes.append({
                        "name": file.stem,
                        "path": str(file.relative_to(self.lifebook_path)),
                        "type": subdir
                    })

            if not nodes:
                return "📭 暂无节点"

            result = ["# 📋 节点列表"]
            for node in nodes:
                result.append(f"- **{node['name']}** ({node['type']})")
                result.append(f"  路径: `{node['path']}`")
                result.append("")

            return "\n".join(result)

        except Exception as e:
            return f"❌ 列出节点失败: {str(e)}"

    # ==================== 内部辅助方法 ====================

    async def _get_year_summary(self) -> Optional[str]:
        """获取最近的年度总结"""
        year_dir = self.diary_dir
        if not year_dir.exists():
            return None

        # 查找年度总结文件
        year_summaries = list(year_dir.glob("*/0-*年度总结.md"))
        if not year_summaries:
            return None

        # 读取最新的
        latest = sorted(year_summaries, reverse=True)[0]
        async with aiofiles.open(latest, encoding="utf-8") as f:
            return await f.read()

    async def _get_quarter_summaries(self, start_date: datetime) -> List[str]:
        """获取季度总结"""
        summaries = []

        year_dir = self.diary_dir
        if not year_dir.exists():
            return summaries

        # 查找季度总结文件
        for year_folder in year_dir.iterdir():
            if not year_folder.is_dir():
                continue

            q_files = list(year_folder.glob("0-*Q*总结.md"))
            for qf in q_files:
                # 解析日期判断是否在范围内
                match = re.search(r'(\d{4})年Q(\d)', qf.name)
                if match:
                    year, quarter = int(match.group(1)), int(match.group(2))
                    quarter_end_month = quarter * 3
                    quarter_date = datetime(year, quarter_end_month, 1) + timedelta(days=31)

                    if quarter_date >= start_date:
                        async with aiofiles.open(qf, encoding="utf-8") as f:
                            summaries.append(await f.read())

        return sorted(summaries, reverse=True)

    async def _get_month_summaries(self, start_date: datetime) -> List[str]:
        """获取月度总结"""
        summaries = []

        # 遍历月份目录
        for year in range(start_date.year, datetime.now().year + 1):
            year_dir = self.diary_dir / str(year)
            if not year_dir.exists():
                continue

            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue

                month_file = month_dir / "0-*月总结.md"
                if month_file.exists():
                    async with aiofiles.open(month_file, encoding="utf-8") as f:
                        summaries.append(await f.read())

        return sorted(summaries, reverse=True)

    async def _get_week_summaries(self, start_date: datetime) -> List[str]:
        """获取周度总结"""
        summaries = []

        for year in range(start_date.year, datetime.now().year + 1):
            for month in range(1, 13):
                month_dir = self.diary_dir / f"{year:04d}/{month:02d}"
                if not month_dir.exists():
                    continue

                week_files = list(month_dir.glob("*W*总结.md"))
                for wf in week_files:
                    async with aiofiles.open(wf, encoding="utf-8") as f:
                        summaries.append(await f.read())

        return sorted(summaries, reverse=True)

    async def _get_daily_entries(self, start_date: datetime, days: int = 7) -> List[str]:
        """获取最近的日记条目"""
        entries = []
        cutoff_date = datetime.now() - timedelta(days=days)

        for date_offset in range(days):
            entry_date = datetime.now() - timedelta(days=date_offset)
            if entry_date < start_date:
                continue

            date_str = entry_date.strftime("%Y-%m-%d")
            year = entry_date.strftime("%Y")
            month = entry_date.strftime("%m")

            diary_file = self.diary_dir / year / month / f"{date_str}.md"
            if diary_file.exists():
                async with aiofiles.open(diary_file, encoding="utf-8") as f:
                    entries.append(await f.read())

        return entries

    async def _get_weekly_diaries(self, period: str) -> str:
        """获取一周的日记用于生成周总结"""
        # 这里应该解析 period 并返回对应的日记
        return "[周度日记数据]"

    async def _get_monthly_weeks(self, period: str) -> str:
        """获取一月内的周总结用于生成月总结"""
        return "[月度周总结数据]"

    async def _get_quarterly_months(self, period: str) -> str:
        """获取一季度的月总结用于生成季总结"""
        return "[季度月总结数据]"

    async def _get_yearly_quarters(self, period: str) -> str:
        """获取一年内的季度总结用于生成年总结"""
        return "[年度季度总结数据]"

    # 工具方法映射
    async def read_lifebook(self, args: Dict[str, Any]) -> str:
        """别名：读取 LifeBook"""
        return await self.read_lifebook_context(args)

    async def record_diary(self, args: Dict[str, Any]) -> str:
        """别名：记录日记"""
        return await self.write_diary(args)

    async def auto_summary(self, args: Dict[str, Any]) -> str:
        """别名：自动总结"""
        return await self.generate_summary(args)
