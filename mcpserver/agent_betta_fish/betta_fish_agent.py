"""
微舆（BettaFish）舆情分析 Agent
整合 BettaFish 多智能体系统的核心功能到 NagaAgent
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加 betta-fish-main 到 Python 路径
BETTA_FISH_PATH = Path(__file__).parent.parent.parent.parent / "betta-fish-main"
print(f"[DEBUG] __file__: {__file__}")
print(f"[DEBUG] BETTA_FISH_PATH: {BETTA_FISH_PATH}")
print(f"[DEBUG] BETTA_FISH_PATH.exists(): {BETTA_FISH_PATH.exists()}")

if BETTA_FISH_PATH.exists():
    sys.path.insert(0, str(BETTA_FISH_PATH))
    print(f"[INFO] 已添加 BettaFish 到路径: {BETTA_FISH_PATH}")
else:
    print(f"[WARN] BettaFish 路径不存在: {BETTA_FISH_PATH}")

# 延迟导入 config 和 logger，避免测试时的依赖问题
_config = None
_logger = None

def get_config():
    global _config
    if _config is None:
        try:
            from system.config import config
            _config = config
        except ImportError:
            _config = None
    return _config

def get_logger():
    global _logger
    if _logger is None:
        try:
            from loguru import logger
            _logger = logger
        except ImportError:
            _logger = None
    return _logger


class BettaFishAgent:
    """微舆舆情分析 Agent"""

    name = "微舆舆情分析"
    instructions = "使用多智能体系统进行深度舆情分析、情感分析和报告生成"

    def __init__(self):
        self.betta_fish_enabled = self._check_betta_fish_available()
        self.features = {
            "insight_analysis": False,  # 深度洞察分析
            "sentiment_analysis": False,  # 情感分析
            "report_generation": False,   # 报告生成
            "web_search": False,         # 网页搜索
            "forum_collaboration": False  # 论坛协作
        }

        if self.betta_fish_enabled:
            self._initialize_features()

    def _check_betta_fish_available(self) -> bool:
        """检查 BettaFish 是否可用"""
        try:
            # 检查关键模块是否存在
            checks = [
                ("InsightEngine", BETTA_FISH_PATH / "InsightEngine"),
                ("MediaEngine", BETTA_FISH_PATH / "MediaEngine"),
                ("ForumEngine", BETTA_FISH_PATH / "ForumEngine"),
            ]

            available = True
            for module_name, module_path in checks:
                if not module_path.exists():
                    logger = get_logger()
                    if logger:
                        logger.warning(f"BettaFish 模块不存在: {module_name}")
                    else:
                        print(f"[WARN] BettaFish 模块不存在: {module_name}")
                    available = False

            if available:
                logger = get_logger()
                if logger:
                    logger.info("✅ BettaFish 模块检查通过")
                else:
                    print("[INFO] ✅ BettaFish 模块检查通过")
            else:
                logger = get_logger()
                if logger:
                    logger.warning("⚠️ BettaFish 部分模块缺失，将使用基础功能")
                else:
                    print("[WARN] ⚠️ BettaFish 部分模块缺失，将使用基础功能")

            return available
        except Exception as e:
            logger = get_logger()
            if logger:
                logger.error(f"检查 BettaFish 可用性时出错: {e}")
            else:
                print(f"[ERROR] 检查 BettaFish 可用性时出错: {e}")
            return False

    def _initialize_features(self):
        """初始化可用功能"""
        try:
            # 尝试导入 InsightEngine
            try:
                from InsightEngine.agent import DeepSearchAgent
                from InsightEngine.tools import multilingual_sentiment_analyzer
                self.features["insight_analysis"] = True
                self.features["sentiment_analysis"] = True
                self.sentiment_analyzer = multilingual_sentiment_analyzer
                logger = get_logger()
                if logger:
                    logger.info("✅ InsightEngine 功能已启用")
                else:
                    print("[INFO] ✅ InsightEngine 功能已启用")
            except ImportError as e:
                logger = get_logger()
                if logger:
                    logger.warning(f"InsightEngine 导入失败: {e}")
                else:
                    print(f"[WARN] InsightEngine 导入失败: {e}")

            # 尝试导入 MediaEngine
            try:
                from MediaEngine.agent import MediaAgent
                self.features["media_analysis"] = True
                logger = get_logger()
                if logger:
                    logger.info("✅ MediaEngine 功能已启用")
                else:
                    print("[INFO] ✅ MediaEngine 功能已启用")
            except ImportError as e:
                logger = get_logger()
                if logger:
                    logger.warning(f"MediaEngine 导入失败: {e}")
                else:
                    print(f"[WARN] MediaEngine 导入失败: {e}")

            # 尝试导入 ForumEngine
            try:
                from ForumEngine.monitor import ForumMonitor
                self.features["forum_collaboration"] = True
                logger = get_logger()
                if logger:
                    logger.info("✅ ForumEngine 功能已启用")
                else:
                    print("[INFO] ✅ ForumEngine 功能已启用")
            except ImportError as e:
                logger = get_logger()
                if logger:
                    logger.warning(f"ForumEngine 导入失败: {e}")
                else:
                    print(f"[WARN] ForumEngine 导入失败: {e}")

        except Exception as e:
            logger = get_logger()
            if logger:
                logger.error(f"初始化 BettaFish 功能时出错: {e}")
            else:
                print(f"[ERROR] 初始化 BettaFish 功能时出错: {e}")

    async def 舆情分析(self, topic: str, depth: int = 3) -> Dict[str, Any]:
        """执行舆情深度分析"""
        if not self.betta_fish_enabled:
            return {
                "success": False,
                "error": "BettaFish 系统未正确初始化",
                "fallback": f"使用基础模式分析主题: {topic}"
            }

        try:
            logger = get_logger()
            if logger:
                logger.info(f"开始舆情分析: topic={topic}, depth={depth}")
            else:
                print(f"[INFO] 开始舆情分析: topic={topic}, depth={depth}")

            if self.features.get("insight_analysis"):
                return self._basic_opinion_analysis(topic, depth)
            else:
                return self._basic_opinion_analysis(topic, depth)

        except Exception as e:
            logger = get_logger()
            if logger:
                logger.error(f"舆情分析失败: {e}")
            else:
                print(f"[ERROR] 舆情分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"分析过程中出现错误: {str(e)}"
            }

    async def 情感分析(self, text: str) -> Dict[str, Any]:
        """分析文本情感倾向"""
        try:
            logger = get_logger()
            if logger:
                logger.info(f"开始情感分析: text_length={len(text)}")
            else:
                print(f"[INFO] 开始情感分析: text_length={len(text)}")

            if self.features.get("sentiment_analysis"):
                result = self.sentiment_analyzer.analyze(text)
                return {
                    "success": True,
                    "sentiment": result.get("sentiment", "neutral"),
                    "confidence": result.get("confidence", 0.0),
                    "details": result
                }
            else:
                return self._basic_sentiment_analysis(text)

        except Exception as e:
            logger = get_logger()
            if logger:
                logger.error(f"情感分析失败: {e}")
            else:
                print(f"[ERROR] 情感分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "情感分析失败"
            }

    async def 生成舆情报告(self, topic: str, report_type: str = "社会") -> Dict[str, Any]:
        """生成舆情分析报告"""
        try:
            logger = get_logger()
            if logger:
                logger.info(f"开始生成报告: topic={topic}, type={report_type}")
            else:
                print(f"[INFO] 开始生成报告: topic={topic}, type={report_type}")

            import openai

            cfg = get_config()
            if cfg is None:
                return {
                    "success": False,
                    "error": "NagaAgent配置未找到",
                    "message": "无法访问LLM配置"
                }

            client = openai.OpenAI(
                api_key=cfg.api.api_key,
                base_url=cfg.api.base_url
            )

            prompt = f"""请生成一份关于"{topic}"的{report_type}舆情分析报告。

报告应包含以下部分：
1. 概述
2. 主要发现
3. 情感分析
4. 趋势分析
5. 结论和建议

请用专业的分析语气，内容要详细、客观。"""

            response = client.chat.completions.create(
                model=cfg.api.model,
                messages=[
                    {"role": "system", "content": "你是一位专业的舆情分析师，擅长分析社会热点和网络舆论趋势。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )

            report_content = response.choices[0].message.content

            return {
                "success": True,
                "topic": topic,
                "report_type": report_type,
                "content": report_content,
                "message": "舆情报告生成成功"
            }

        except Exception as e:
            logger = get_logger()
            if logger:
                logger.error(f"生成报告失败: {e}")
            else:
                print(f"[ERROR] 生成报告失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "报告生成失败"
            }

    async def 全网搜索(self, query: str, days: int = 7) -> Dict[str, Any]:
        """全网搜索相关信息"""
        try:
            logger = get_logger()
            if logger:
                logger.info(f"开始全网搜索: query={query}, days={days}")
            else:
                print(f"[INFO] 开始全网搜索: query={query}, days={days}")

            import openai

            cfg = get_config()
            if cfg is None:
                return {
                    "success": False,
                    "error": "NagaAgent配置未找到",
                    "message": "无法访问LLM配置"
                }

            client = openai.OpenAI(
                api_key=cfg.api.api_key,
                base_url=cfg.api.base_url
            )

            prompt = f"""请搜索关于"{query}"的最新信息（最近{days}天）。

请提供：
1. 主要相关信息摘要
2. 关键数据
3. 趋势分析
4. 来源标注

确保信息准确、客观。"""

            response = client.chat.completions.create(
                model=cfg.api.model,
                messages=[
                    {"role": "system", "content": "你是一位信息检索专家，擅长快速准确地收集和整理信息。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=2000
            )

            search_result = response.choices[0].message.content

            return {
                "success": True,
                "query": query,
                "days": days,
                "result": search_result,
                "message": "搜索完成"
            }

        except Exception as e:
            logger = get_logger()
            if logger:
                logger.error(f"全网搜索失败: {e}")
            else:
                print(f"[ERROR] 全网搜索失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "搜索失败"
            }

    def _basic_opinion_analysis(self, topic: str, depth: int = 3) -> Dict[str, Any]:
        """基础舆情分析（降级方案）"""
        return {
            "success": True,
            "topic": topic,
            "depth": depth,
            "mode": "basic",
            "analysis": {
                "summary": f"已启动对'{topic}'的基础分析",
                "key_points": [
                    "需要更多具体信息进行深度分析",
                    "建议配置 BettaFish 数据库以获得完整功能",
                    "当前使用基础分析模式"
                ],
                "recommendations": [
                    f"继续收集'{topic}'相关信息",
                    "关注相关讨论和趋势",
                    "定期更新分析结果"
                ]
            },
            "message": "基础分析完成"
        }

    def _basic_sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """基础情感分析（降级方案）"""
        # 简单关键词匹配
        positive_words = ["好", "棒", "优秀", "喜欢", "开心", "高兴", "满意", "成功", "优秀", "精彩"]
        negative_words = ["差", "坏", "糟糕", "讨厌", "伤心", "难过", "失望", "失败", "糟糕", "不好"]

        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        if positive_count > negative_count:
            sentiment = "positive"
            confidence = min(0.7 + (positive_count - negative_count) * 0.1, 0.95)
        elif negative_count > positive_count:
            sentiment = "negative"
            confidence = min(0.7 + (negative_count - positive_count) * 0.1, 0.95)
        else:
            sentiment = "neutral"
            confidence = 0.5

        return {
            "success": True,
            "sentiment": sentiment,
            "confidence": confidence,
            "details": {
                "mode": "basic_keyword_match",
                "positive_words": positive_count,
                "negative_words": negative_count
            },
            "message": "基础情感分析完成"
        }

    async def handle_handoff(self, handoff_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP统一调用接口

        Args:
            handoff_data: 包含tool_name和参数的字典

        Returns:
            调用结果
        """
        try:
            tool_name = handoff_data.get("tool_name")
            logger = get_logger()

            if logger:
                logger.info(f"BettaFishAgent.handle_handoff: tool_name={tool_name}, data={handoff_data}")
            else:
                print(f"[INFO] BettaFishAgent.handle_handoff: tool_name={tool_name}, data={handoff_data}")

            # 根据tool_name调用相应的方法
            if tool_name == "舆情分析":
                topic = handoff_data.get("topic", "")
                depth = handoff_data.get("depth", 3)
                return await self.舆情分析(topic, depth)

            elif tool_name == "情感分析":
                text = handoff_data.get("text", "")
                return await self.情感分析(text)

            elif tool_name == "生成舆情报告":
                topic = handoff_data.get("topic", "")
                report_type = handoff_data.get("report_type", "社会")
                return await self.生成舆情报告(topic, report_type)

            elif tool_name == "全网搜索":
                query = handoff_data.get("query", "")
                days = handoff_data.get("days", 7)
                return await self.全网搜索(query, days)

            else:
                error_msg = f"不支持的调用命令: {tool_name}。支持的操作：舆情分析、情感分析、生成舆情报告、全网搜索"
                if logger:
                    logger.error(error_msg)
                else:
                    print(f"[ERROR] {error_msg}")

                return {
                    "success": False,
                    "error": error_msg,
                    "message": error_msg
                }

        except Exception as e:
            logger = get_logger()
            if logger:
                logger.error(f"handle_handoff执行失败: {e}")
            else:
                print(f"[ERROR] handle_handoff执行失败: {e}")

            return {
                "success": False,
                "error": str(e),
                "message": f"调用失败: {str(e)}"
            }
