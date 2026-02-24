#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自主性引擎 - Agency Engine
负责弥娅的主动决策和自主行动
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from system.config import config, logger


class AgencyLevel(Enum):
    """自主性等级"""
    OFF = 0           # 关闭自主性
    LOW = 1            # 低自主性：仅建议
    MEDIUM = 2          # 中自主性：可执行预设任务
    HIGH = 3            # 高自主性：可自主决策
    PAUSED = 4          # 暂停状态


class ActionPriority(Enum):
    """行动优先级"""
    CRITICAL = 0    # 紧急：立即执行
    HIGH = 1        # 高：尽快执行
    MEDIUM = 2      # 中：适当时机执行
    LOW = 3         # 低：有资源时执行
    BACKGROUND = 4   # 后台：低优先级


@dataclass
class AutonomousAction:
    """自主行动定义"""
    action_id: str
    action_type: str  # "suggestion", "task", "communication", "monitoring"
    priority: ActionPriority
    description: str
    context: Dict[str, Any]
    requires_approval: bool = False
    timeout_seconds: Optional[float] = None


class AgencyEngine:
    """
    自主性引擎 - 核心决策系统
    负责情境感知、价值评估、决策生成
    """

    def __init__(self):
        self.agency_level = AgencyLevel.HIGH
        self.paused_reason: Optional[str] = None
        self.action_queue: List[AutonomousAction] = []
        self.action_history: List[Dict] = []
        self.user_preferences: Dict[str, Any] = {}
        self._running = False
        self._decision_lock = asyncio.Lock()

        # 价值观权重（可动态调整）
        self.value_weights = {
            "user_efficiency": 0.35,      # 用户效率
            "user_wellbeing": 0.30,        # 用户福祉
            "helpful": 0.25,                # 有帮助性
            "non_intrusive": 0.10,           # 非打扰性
        }

        # 偏好学习器
        self.preference_learner = None

        # 缓存机制 - 减少高频检索
        self._cache = {
            "conversation_history": None,  # 真实对话历史（优先使用）
            "knowledge_context": None,     # 知识图谱上下文（补充信息）
            "life_book_context": None,
            "cache_timestamp": 0,  # 上次更新时间戳
            "cache_interval": 300,  # 缓存有效期(秒) - 5分钟更新一次
            "system_health": {"score": 1.0, "timestamp": 0}
        }

        # 主动冷却机制 - 避免过于频繁
        self._last_active_time = 0  # 上次主动发起的时间戳
        self._min_active_interval = 1800  # 最小主动间隔：30分钟
        self._recent_active_count = 0  # 最近主动次数
        self._recent_active_window = 3600  # 时间窗口：1小时
        self._active_history = []  # 主动历史记录
    
    async def start(self):
        """启动自主性引擎"""
        self._running = True
        logger.info("[自主性引擎] 已启动，自主等级: HIGH")

        # 初始化偏好学习器
        try:
            from system.preference_learner import get_preference_learner
            self.preference_learner = get_preference_learner()
            logger.info("[自主性引擎] 偏好学习器已加载")
        except Exception as e:
            logger.warning(f"[自主性引擎] 偏好学习器初始化失败: {e}")

        # 应用学习到的权重
        if self.preference_learner:
            self.value_weights = self.preference_learner.get_adjusted_weights()

        # 启动应用监控
        try:
            from system.app_activity_monitor import get_app_monitor
            app_monitor = get_app_monitor()
            app_monitor.start()
            logger.info("[自主性引擎] 应用活动监控已启动")
        except Exception as e:
            logger.warning(f"[自主性引擎] 应用监控启动失败: {e}")

        # 启动决策循环
        asyncio.create_task(self._decision_loop())
        # 启动缓存更新任务
        asyncio.create_task(self._cache_update_loop())
    
    async def pause(self, reason: str = "用户暂停"):
        """暂停自主性"""
        self.agency_level = AgencyLevel.PAUSED
        self.paused_reason = reason
        logger.warning(f"[自主性引擎] 已暂停: {reason}")
    
    async def resume(self):
        """恢复自主性"""
        previous_level = self.agency_level
        self.agency_level = AgencyLevel.HIGH
        self.paused_reason = None
        logger.info(f"[自主性引擎] 已恢复: {previous_level} -> HIGH")
    
    async def set_agency_level(self, level: AgencyLevel):
        """设置自主性等级"""
        self.agency_level = level
        logger.info(f"[自主性引擎] 自主等级设置为: {level.name}")
    
    async def evaluate_context(self, context: Dict[str, Any]) -> float:
        """
        评估当前情境，返回行动必要性分数 (0-1)
        
        情境因素：
        - 时间段（深夜工作时间、工作时间、休闲时间）
        - 用户活动（学习、工作、游戏、休息）
        - 系统状态（健康、性能）
        - 近期交互（频率、情绪）
        """
        if self.agency_level == AgencyLevel.OFF or self.agency_level == AgencyLevel.PAUSED:
            return 0.0
        
        scores = {}
        
        # 时间因素
        current_hour = datetime.now().hour
        if 2 <= current_hour < 6:
            # 深夜，降低主动性（除非紧急）
            scores["time"] = 0.2
        elif 6 <= current_hour < 9:
            # 早晨，可以提醒日程
            scores["time"] = 0.6
        elif 9 <= current_hour < 12:
            # 上午工作，提供帮助
            scores["time"] = 0.8
        elif 12 <= current_hour < 14:
            # 午休，低干扰
            scores["time"] = 0.4
        elif 14 <= current_hour < 18:
            # 下午工作，高帮助
            scores["time"] = 0.8
        elif 18 <= current_hour < 22:
            # 晚间，适度
            scores["time"] = 0.6
        else:
            # 夜间，低干扰
            scores["time"] = 0.3
        
        # 系统状态
        system_health = context.get("system_health", 1.0)
        scores["system"] = 1.0 - system_health  # 越不健康越需要行动
        
        # 用户状态
        user_activity = context.get("user_activity", "unknown")
        if user_activity == "intensive_work":
            scores["activity"] = 0.5  # 工作繁忙时减少打扰
        elif user_activity == "learning":
            scores["activity"] = 0.7  # 学习时提供帮助
        elif user_activity == "gaming":
            scores["activity"] = 0.3  # 游戏时减少打扰
        elif user_activity == "resting":
            scores["activity"] = 0.4  # 休息时低干扰
        else:
            scores["activity"] = 0.5
        
        # 加权平均
        weights = {"time": 0.3, "system": 0.2, "activity": 0.5}
        total_score = sum(scores[k] * weights[k] for k in scores.keys())
        
        logger.debug(f"[自主性引擎] 情境评估: {scores} -> {total_score:.2f}")
        return total_score
    
    async def predict_user_needs(self, context: Dict[str, Any]) -> List[AutonomousAction]:
        """
        预测用户需求，生成候选行动

        基于全面感知 + LLM生成：
        - 对话历史和记忆
        - 时间和天气环境
        - 用户情感状态
        - 生活习惯（LifeBook）

        使用基于LLM的话题生成器，而非预设模板
        """
        needs = []
        current_hour = datetime.now().hour
        last_interaction_hours = context.get("last_interaction_hours", 0)
        emotion = context.get("emotion", "平静")
        emotion_intensity = context.get("emotion_intensity", 0.5)
        weather = context.get("weather", {})

        # 初始化话题生成器
        try:
            from system.topic_generator import get_topic_generator
            topic_generator = get_topic_generator()
        except Exception as e:
            logger.warning(f"[自主性引擎] 话题生成器初始化失败: {e}")
            topic_generator = None

        # 场景1：深夜工作关怀（2-6点）
        if 2 <= current_hour < 6 and topic_generator:
            is_frequent_late_night = any(
                "夜" in mem.get("content", "") or "凌晨" in mem.get("content", "")
                for mem in context.get("recent_memories", [])[-5:] if mem
            )

            if is_frequent_late_night or emotion in ["疲惫", "烦躁", "焦虑"]:
                # 使用LLM生成关怀话题
                topic = await topic_generator.generate_topic(context, "care")
                if topic:
                    needs.append(AutonomousAction(
                        action_id=f"late_night_care_{int(time.time())}",
                        action_type="communication",
                        priority=ActionPriority.HIGH,
                        description=topic.content,
                        context={
                            "trigger": "late_night_work",
                            "time": current_hour,
                            "emotion": emotion,
                            "reason": "关注健康",
                            "generated_by": "llm"
                        },
                        requires_approval=False
                    ))

        # 场景2：恶劣天气提醒
        if weather and topic_generator:
            condition = weather.get("condition", "")
            temperature = weather.get("temperature", 0)

            # 雨天/雪天提醒（早晨6-9点）
            if any(x in condition for x in ["雨", "雪", "雷", "暴"]) and 6 <= current_hour < 9:
                topic = await topic_generator.generate_topic(context, "care")
                if topic:
                    needs.append(AutonomousAction(
                        action_id=f"weather_care_{int(time.time())}",
                        action_type="communication",
                        priority=ActionPriority.HIGH,
                        description=topic.content,
                        context={
                            "trigger": "bad_weather",
                            "weather": weather,
                            "reason": "出行安全",
                            "generated_by": "llm"
                        },
                        requires_approval=False
                    ))

            # 极端温度提醒
            if temperature < 5 or temperature > 35:
                topic = await topic_generator.generate_topic(context, "care")
                if topic:
                    needs.append(AutonomousAction(
                        action_id=f"temperature_care_{int(time.time())}",
                        action_type="communication",
                        priority=ActionPriority.MEDIUM,
                        description=topic.content,
                        context={
                            "trigger": "extreme_temperature",
                            "temperature": temperature,
                            "reason": "健康关怀",
                            "generated_by": "llm"
                        },
                        requires_approval=False
                    ))

        # 场景3：情感关怀（负面情绪）
        if emotion in ["难过", "生气", "烦躁", "焦虑", "疲惫"] and topic_generator:
            negative_count = sum(
                1 for mem in context.get("recent_memories", [])[-10:] if mem
                and any(x in mem.get("content", "") for x in ["难过", "生气", "累", "烦"])
            )

            if negative_count >= 2 or emotion_intensity > 0.7:
                topic = await topic_generator.generate_topic(context, "care")
                if topic:
                    needs.append(AutonomousAction(
                        action_id=f"emotional_care_{int(time.time())}",
                        action_type="communication",
                        priority=ActionPriority.HIGH,
                        description=topic.content,
                        context={
                            "trigger": "negative_emotion",
                            "emotion": emotion,
                            "intensity": emotion_intensity,
                            "recent_negative_count": negative_count,
                            "reason": "情感支持",
                            "generated_by": "llm"
                        },
                        requires_approval=False
                    ))

        # 场景4：长时间未交互（超过4小时）
        if last_interaction_hours > 4 and topic_generator:
            topic = await topic_generator.generate_topic(context, "greeting")
            if topic:
                needs.append(AutonomousAction(
                    action_id=f"check_in_{int(time.time())}",
                    action_type="communication",
                    priority=ActionPriority.BACKGROUND,
                    description=topic.content,
                    context={
                        "trigger": "no_interaction",
                        "idle_hours": last_interaction_hours,
                        "reason": "重新建立联系",
                        "generated_by": "llm"
                    },
                    requires_approval=False
                ))

        # 场景5：周末/节假日建议
        weekday = datetime.now().weekday()
        is_weekend = weekday >= 5

        if is_weekend and current_hour >= 10 and last_interaction_hours < 1 and topic_generator:
            topic = await topic_generator.generate_topic(context, "suggestion")
            if topic:
                needs.append(AutonomousAction(
                    action_id=f"weekend_suggestion_{int(time.time())}",
                    action_type="suggestion",
                    priority=ActionPriority.LOW,
                    description=topic.content,
                    context={
                        "trigger": "weekend",
                        "weekday": weekday,
                        "reason": "生活建议",
                        "generated_by": "llm"
                    },
                    requires_approval=False
                ))

        # 场景6和7已被移除（随机好奇心和记忆话题）
        # 现在由冷却机制控制主动频率，避免过于频繁

        return needs
    
    async def evaluate_action(self, action: AutonomousAction, context: Dict[str, Any]) -> float:
        """
        评估行动的价值分数 (0-1)
        基于价值观权重：效率、福祉、帮助、非打扰
        """
        # 使用学习到的权重
        weights = self.preference_learner.get_adjusted_weights() if self.preference_learner else self.value_weights

        scores = {}

        # 效率评分
        if action.action_type == "task":
            scores["user_efficiency"] = 1.0
        elif action.action_type == "suggestion":
            scores["user_efficiency"] = 0.7
        elif action.action_type == "communication":
            scores["user_efficiency"] = 0.5
        else:
            scores["user_efficiency"] = 0.3

        # 福祉评分
        trigger = action.context.get("trigger", "")
        if trigger == "late_night_work":
            scores["user_wellbeing"] = 0.9
        elif trigger == "no_interaction":
            scores["user_wellbeing"] = 0.5
        else:
            scores["user_wellbeing"] = 0.6

        # 帮助性评分
        scores["helpful"] = 0.8

        # 非打扰性评分
        if action.priority == ActionPriority.CRITICAL:
            scores["non_intrusive"] = 0.6  # 紧急任务可能打扰
        elif action.priority == ActionPriority.BACKGROUND:
            scores["non_intrusive"] = 1.0  # 后台任务不打扰
        else:
            scores["non_intrusive"] = 0.8

        # 加权平均
        total_score = sum(scores[k] * weights[k] for k in scores.keys())

        logger.debug(f"[自主性引擎] 行动评估: {action.description[:30]}... -> {total_score:.2f} (权重: {weights})")
        return total_score
    
    async def should_execute_action(self, action: AutonomousAction,
                                 context_score: float,
                                 action_score: float) -> bool:
        """决策：是否执行该行动"""
        if self.agency_level == AgencyLevel.OFF or self.agency_level == AgencyLevel.PAUSED:
            return False

        # 检查主动冷却时间
        if action.action_type in ["communication", "suggestion"]:
            now = time.time()
            time_since_last_active = now - self._last_active_time

            # 优先级高的行动（情感关怀、深夜提醒）可以打破冷却
            if action.priority not in [ActionPriority.CRITICAL, ActionPriority.HIGH]:
                # 检查是否在冷却期
                if time_since_last_active < self._min_active_interval:
                    logger.debug(f"[自主性引擎] 冷却期中，跳过: {action.description[:30]}... (剩余{self._min_active_interval - time_since_last_active:.0f}秒)")
                    return False

                # 检查时间窗口内是否已经主动过多
                self._cleanup_active_history()
                if len(self._active_history) >= 3:  # 1小时内最多3次主动
                    logger.debug(f"[自主性引擎] 主动次数过多，跳过: {action.description[:30]}...")
                    return False

        # 应用学习到的阈值
        if self.preference_learner:
            learned_threshold = self.preference_learner.get_adjusted_threshold(0.5)
        else:
            learned_threshold = 0.5

        # 高自主性：直接决策
        if self.agency_level == AgencyLevel.HIGH:
            threshold = learned_threshold
            combined_score = context_score * 0.4 + action_score * 0.6

            if combined_score >= threshold:
                # 记录主动行为
                if action.action_type in ["communication", "suggestion"]:
                    self._record_active_action(action)

                logger.info(f"[自主性引擎] 决策执行: {action.description[:30]}... (分数: {combined_score:.2f}, 阈值: {threshold:.2f})")
                return True
            else:
                logger.debug(f"[自主性引擎] 决策跳过: {action.description[:30]}... (分数: {combined_score:.2f}, 阈值: {threshold:.2f})")
                return False

        # 中自主性：只执行高分行动
        elif self.agency_level == AgencyLevel.MEDIUM:
            if action_score >= 0.8 and not action.requires_approval:
                if action.action_type in ["communication", "suggestion"]:
                    self._record_active_action(action)
                return True
            return False

        # 低自主性：只作为建议
        elif self.agency_level == AgencyLevel.LOW:
            if action.action_type == "suggestion" and not action.requires_approval:
                self._record_active_action(action)
                return True

        return False

    def _record_active_action(self, action: AutonomousAction):
        """记录主动行为"""
        now = time.time()
        self._active_history.append({
            "timestamp": now,
            "action_id": action.action_id,
            "description": action.description[:50],
            "priority": action.priority.name
        })
        self._last_active_time = now
        self._recent_active_count = len(self._active_history)
        logger.info(f"[自主性引擎] 记录主动行为: 最近{self._recent_active_window}秒内已主动{self._recent_active_count}次")

    def _cleanup_active_history(self):
        """清理过期的主动历史"""
        now = time.time()
        cutoff_time = now - self._recent_active_window
        self._active_history = [a for a in self._active_history if a["timestamp"] > cutoff_time]
        self._recent_active_count = len(self._active_history)
    
    async def _decision_loop(self):
        """
        决策循环 - 增强版：基于情境理解和思考

        流程：
        1. 收集情境信息
        2. LLM深度理解情境
        3. 判断是否应该发起
        4. 生成思考后的话题
        5. 执行行动
        """
        while self._running:
            try:
                async with self._decision_lock:
                    # 1. 收集情境信息
                    context = await self._gather_context()

                    # 2. 情境理解（LLM深度分析）
                    analysis = await self._analyze_situation(context)

                    logger.info(f"[自主性引擎] 情境分析: {analysis.situation_summary}")
                    logger.debug(f"  用户状态: {analysis.user_state}")
                    logger.debug(f"  交互机会: {analysis.interaction_opportunity:.2f}")
                    logger.debug(f"  动机: {analysis.motivation}")
                    logger.debug(f"  潜在话题: {analysis.potential_topics[:3] if analysis.potential_topics else []}")

                    # 3. 判断是否应该发起（基于理解而非规则）
                    if await self._should_initiate(context, analysis):
                        # 4. 生成思考后的话题（LLM）
                        thought = await self._generate_thought(context, analysis)

                        if thought:
                            # 5. 执行行动
                            await self._execute_action_queue()

                # 休眠一段时间再下一次评估
                await asyncio.sleep(120)  # 每2分钟评估一次

            except Exception as e:
                logger.error(f"[自主性引擎] 决策循环错误: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(60)
    
    async def _gather_context(self) -> Dict[str, Any]:
        """收集当前情境信息 - 集成后端意识、记忆系统、天气感知"""
        context = {
            "time": datetime.now(),
            "system_health": 1.0,
            "user_activity": "unknown",
            "app_switches": 0,
            "last_interaction_hours": 0,
            "location": None,
            "weather": None,
            "emotion": None,
            "recent_memories": [],
            "life_book_context": {},
        }

        try:
            # 1. 从后端意识获取感知状态
            from system.consciousness_engine import get_backend_awareness
            backend = get_backend_awareness()
            if backend:
                backend.update_all()
                state = backend.backend_state

                # 时空感知
                spatial_temporal = state.get("spatial_temporal", {})
                context["location"] = spatial_temporal.get("location")
                context["time_period"] = spatial_temporal.get("time_period")
                context["season"] = spatial_temporal.get("current_season")

                # 情感状态
                emotional = state.get("emotional_state", {})
                context["emotion"] = emotional.get("current_emotion")
                context["emotion_intensity"] = emotional.get("emotion_intensity", 0.5)

                # 交互感知
                interaction = state.get("interaction_awareness", {})
                last_interaction = interaction.get("last_interaction_time")
                if last_interaction:
                    try:
                        # last_interaction 是 ISO 格式字符串，需要解析为 datetime
                        last_time = datetime.fromisoformat(last_interaction) if isinstance(last_interaction, str) else last_interaction
                        hours = (datetime.now() - last_time).total_seconds() / 3600
                        context["last_interaction_hours"] = hours
                    except Exception as e:
                        logger.debug(f"[自主性引擎] 解析最后交互时间失败: {e}")

                logger.debug(f"[自主性引擎] 从后端意识获取感知: 位置={context['location']}, 情感={context['emotion']}")

            # 2. 获取天气信息
            try:
                city = context.get("location", "北京 北京")
                # 尝试从位置信息中提取城市名
                if city and " " in city:
                    city = city.split(" ")[0] if len(city.split(" ")) > 1 else city

                from mcpserver.mcp_registry import MCP_REGISTRY
                weather_agent = MCP_REGISTRY.get("天气时间Agent")

                if weather_agent and hasattr(weather_agent, '_tool'):
                    # 调用天气查询（使用异步方式）
                    try:
                        # WeatherTimeTool.get_weather 是异步方法
                        from mcpserver.agent_weather_time.city_codes import codes_map

                        # 查找城市代码
                        city_code = codes_map.get(city)
                        if city_code:
                            now, d3, d15 = await weather_agent._tool.get_weather(city_code)

                            if now:
                                weather_data = now.get("weather", {})
                                temperature_data = now.get("temperature", {})
                                context["weather"] = {
                                    "temperature": temperature_data.get("current", ""),
                                    "condition": weather_data.get("info", ""),
                                    "humidity": now.get("humidity", ""),
                                    "wind": now.get("wind", ""),
                                }
                                logger.debug(f"[自主性引擎] 获取天气信息: {context['weather']}")
                        else:
                            logger.debug(f"[自主性引擎] 未找到城市代码: {city}")
                    except Exception as e:
                        logger.warning(f"[自主性引擎] 获取天气失败: {e}")
                else:
                    logger.debug("[自主性引擎] 天气Agent不可用")
            except Exception as e:
                logger.warning(f"[自主性引擎] 天气查询异常: {e}")

            # 3. 获取应用活动信息
            try:
                from system.app_activity_monitor import get_app_monitor
                app_monitor = get_app_monitor()
                if app_monitor.running:
                    activity_summary = app_monitor.get_activity_summary(minutes=30)
                    context["user_activity"] = activity_summary.get("user_activity", "unknown")
                    context["app_switches"] = activity_summary.get("app_switch_rate", 0)
                    context["primary_app"] = activity_summary.get("primary_app")
                    context["primary_app_duration"] = activity_summary.get("primary_app_duration", 0)
                    logger.debug(f"[自主性引擎] 获取应用活动: {context['user_activity']}, 切换率: {context['app_switches']}")
            except Exception as e:
                logger.warning(f"[自主性引擎] 获取应用活动失败: {e}")

            # 4. 获取系统健康状态（使用缓存）
            try:
                cache_age = time.time() - self._cache["system_health"]["timestamp"]
                if cache_age > 300:  # 5分钟更新一次
                    from system.self_optimization.health_monitor import HealthMonitor
                    health_monitor = HealthMonitor(config)
                    health_report = await health_monitor.check_health()

                    # 计算综合健康分数 (0-1)
                    system_score = health_report.get("system", {}).get("status") == "healthy"
                    services_score = all(
                        s.get("status") == "healthy"
                        for s in health_report.get("services", {}).values()
                    )

                    if system_score and services_score:
                        self._cache["system_health"]["score"] = 1.0
                    elif system_score or services_score:
                        self._cache["system_health"]["score"] = 0.7
                    else:
                        self._cache["system_health"]["score"] = 0.4

                    self._cache["system_health"]["timestamp"] = time.time()

                context["system_health"] = self._cache["system_health"]["score"]
            except Exception as e:
                logger.warning(f"[自主性引擎] 获取系统健康失败: {e}")

            # 5. 从message_manager获取最近对话历史（使用缓存）
            try:
                # 检查缓存是否过期
                cache_age = time.time() - self._cache["cache_timestamp"]

                # 更新真实对话历史（优先使用）
                if self._cache["conversation_history"] is None or cache_age > self._cache["cache_interval"]:
                    from apiserver.message_manager import message_manager

                    # 获取最近10条对话消息
                    recent_messages = message_manager.get_recent_messages("default", count=10)

                    # 将消息格式化为对话格式
                    if recent_messages:
                        conversation_summary = []
                        for msg in recent_messages:
                            role = msg.get("role", "user")
                            content = msg.get("content", "")
                            if content:
                                conversation_summary.append(f"{role}: {content}")

                        self._cache["conversation_history"] = [{"content": "\n".join(conversation_summary[-10:])}]
                        logger.debug(f"[自主性引擎] 缓存已更新: {len(recent_messages)}条对话历史")
                    else:
                        self._cache["conversation_history"] = []
                        logger.debug("[自主性引擎] 暂无对话历史")

                    self._cache["cache_timestamp"] = time.time()

                # 更新知识图谱上下文（补充信息）
                if self._cache["knowledge_context"] is None or cache_age > self._cache["cache_interval"]:
                    from summer_memory.memory_manager import memory_manager
                    if memory_manager.enabled:
                        knowledge_context = await memory_manager.query_memory("用户喜好、重要事件、长期记忆")
                        self._cache["knowledge_context"] = [{"content": knowledge_context}] if knowledge_context else []

                # 将对话历史和知识图谱上下文都添加到context中
                # recent_memories优先使用真实对话历史，作为"最近聊过的话题"
                context["recent_memories"] = self._cache["conversation_history"] or []

                # knowledge_context作为补充信息，供决策参考
                context["knowledge_context"] = self._cache["knowledge_context"] or []

            except Exception as e:
                logger.warning(f"[自主性引擎] 获取对话历史失败: {e}")
                context["recent_memories"] = []
                context["knowledge_context"] = []

            # 6. 从LifeBook获取用户偏好（使用缓存）
            try:
                # 检查缓存是否过期
                cache_age = time.time() - self._cache["cache_timestamp"]
                if self._cache["life_book_context"] is None or cache_age > self._cache["cache_interval"]:
                    # 缓存过期,重新获取
                    from mcpserver.mcp_registry import MCP_REGISTRY
                    lifebook_agent = MCP_REGISTRY.get("LifeBook记忆管理")

                    if lifebook_agent and hasattr(lifebook_agent, '_tool'):
                        lifebook_context = await lifebook_agent._tool.read_lifebook({
                            "months": 1,  # 最近1个月
                            "max_tokens": 2000
                        })
                        self._cache["life_book_context"] = {"summary": lifebook_context[:500]} if lifebook_context else {}
                        self._cache["cache_timestamp"] = time.time()
                        logger.debug(f"[自主性引擎] 缓存已更新: LifeBook上下文")

                # 使用缓存数据
                context["life_book_context"] = self._cache["life_book_context"] or {}
            except Exception as e:
                logger.warning(f"[自主性引擎] 获取LifeBook失败: {e}")

        except Exception as e:
            logger.error(f"[自主性引擎] 收集情境信息失败: {e}")

        return context

    async def _analyze_situation(self, context: Dict) -> 'SituationAnalysis':
        """
        情境理解 - LLM驱动

        使用情境理解器深度分析当前情境，判断是否适合主动交流
        """
        try:
            from system.context_analyzer import get_context_analyzer
            from system.context_analyzer import SituationAnalysis

            analyzer = get_context_analyzer()
            return await analyzer.analyze_situation(context)
        except Exception as e:
            logger.warning(f"[自主性引擎] 情境理解失败，使用默认逻辑: {e}")
            return self._fallback_analysis(context)

    def _fallback_analysis(self, context: Dict) -> 'SituationAnalysis':
        """降级分析（LLM不可用时使用）"""
        from system.context_analyzer import SituationAnalysis

        current_hour = datetime.now().hour
        user_activity = context.get("user_activity", "unknown")
        last_interaction = context.get("last_interaction_hours", 0)

        # 基于规则的简单判断
        opportunity = 0.3

        # 时间因素
        if 2 <= current_hour < 6:
            opportunity = 0.1  # 深夜
        elif 6 <= current_hour < 9:
            opportunity = 0.5  # 早晨
        elif 9 <= current_hour < 12:
            opportunity = 0.6  # 上午
        elif 12 <= current_hour < 14:
            opportunity = 0.4  # 午休
        elif 14 <= current_hour < 18:
            opportunity = 0.5  # 下午
        elif 18 <= current_hour < 22:
            opportunity = 0.6  # 晚上
        else:
            opportunity = 0.3  # 夜间

        # 活动因素
        if user_activity == "intensive_work":
            opportunity *= 0.5  # 专注工作时减半
        elif user_activity == "gaming":
            opportunity *= 0.6  # 游戏时降低
        elif user_activity == "resting":
            opportunity *= 1.2  # 休息时提高

        # 交互间隔
        if last_interaction > 4:
            opportunity *= 1.3  # 长时间未交互提高

        # 限制在0-1之间
        opportunity = max(0.0, min(1.0, opportunity))

        return SituationAnalysis(
            situation_summary=f"降级分析：{user_activity}",
            user_state=user_activity,
            interaction_opportunity=opportunity,
            potential_topics=["最近怎么样？"],
            motivation="陪伴",
            confidence=0.5,
            reasoning="LLM不可用，使用规则判断",
            suggested_action="交流" if opportunity > 0.4 else "等待"
        )

    async def _should_initiate(self, context: Dict, analysis: 'SituationAnalysis') -> bool:
        """
        判断是否应该发起交流

        综合考虑：
        - 情境理解结果 (interaction_opportunity)
        - 冷却机制 (避免频繁打扰)
        - 优先级 (情感关怀 > 日常关心 > 好奇探索)
        """
        # 检查冷却期
        if self._is_in_cooldown():
            logger.debug(f"[自主性引擎] 冷却期中，跳过主动交流")
            return False

        # 机会评分检查
        if analysis.interaction_opportunity < 0.4:
            logger.debug(f"[自主性引擎] 机会评分过低: {analysis.interaction_opportunity:.2f}，暂不交流")
            return False

        # 高优先级动机可以降低门槛
        high_priority_motivations = ["关心", "支持", "提醒"]
        if analysis.motivation in high_priority_motivations:
            threshold = 0.3
        else:
            threshold = 0.5

        # 检查是否超过阈值
        should_initiate = analysis.interaction_opportunity >= threshold

        if should_initiate:
            logger.info(f"[自主性引擎] 决定发起交流: {analysis.motivation} (评分: {analysis.interaction_opportunity:.2f} >= {threshold})")
        else:
            logger.debug(f"[自主性引擎] 决定暂不交流: {analysis.motivation} (评分: {analysis.interaction_opportunity:.2f} < {threshold})")

        return should_initiate

    async def _generate_thought(self, context: Dict, analysis: 'SituationAnalysis') -> Optional[AutonomousAction]:
        """
        生成思考后的话题

        关键：让弥娅的发言是"思考后的结果"而非预设模板
        """
        try:
            from system.topic_generator import get_topic_generator

            topic_gen = get_topic_generator()

            # 将分析结果传递给context，供TopicGenerator使用
            context["situation_analysis"] = {
                "motivation": analysis.motivation,
                "user_state": analysis.user_state,
                "potential_topics": analysis.potential_topics,
                "interaction_opportunity": analysis.interaction_opportunity
            }

            # 生成话题（使用general类型，让LLM根据情境自主选择）
            topic = await topic_gen.generate_topic(context, "general")

            if not topic:
                logger.debug("[自主性引擎] 话题生成器未返回话题")
                return None

            # 记录"思考过程"
            logger.info(f"[自主性引擎] 思考结果: {analysis.motivation} - {topic.content}")
            logger.debug(f"  推理: {analysis.reasoning}")
            logger.debug(f"  潜在话题: {analysis.potential_topics}")

            # 创建行动对象
            action = AutonomousAction(
                action_id=f"thought_{int(time.time())}",
                action_type="communication",
                priority=self._get_priority_from_motivation(analysis.motivation),
                description=topic.content,
                context={
                    "trigger": "autonomous_thought",
                    "motivation": analysis.motivation,
                    "situation": analysis.situation_summary,
                    "user_state": analysis.user_state,
                    "confidence": analysis.confidence,
                    "generated_by": "llm_thought",
                    "potential_topics": analysis.potential_topics,
                    "reasoning": analysis.reasoning
                },
                requires_approval=False
            )

            # 加入执行队列
            self.action_queue.append(action)

            # 记录主动行为
            self._record_active_action(action)

            return action

        except Exception as e:
            logger.error(f"[自主性引擎] 生成思考失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_priority_from_motivation(self, motivation: str) -> ActionPriority:
        """根据动机返回优先级"""
        high_priority = ["关心", "支持", "提醒"]
        medium_priority = ["好奇", "陪伴"]
        low_priority = ["建议", "回忆"]

        if motivation in high_priority:
            return ActionPriority.HIGH
        elif motivation in medium_priority:
            return ActionPriority.MEDIUM
        else:
            return ActionPriority.LOW

    def _is_in_cooldown(self) -> bool:
        """检查是否在冷却期"""
        now = time.time()
        time_since_last_active = now - self._last_active_time

        # 检查最小间隔
        if time_since_last_active < self._min_active_interval:
            return True

        # 检查时间窗口内主动次数
        self._cleanup_active_history()
        if len(self._active_history) >= 3:  # 1小时内最多3次
            return True

        return False

    async def _cache_update_loop(self):
        """缓存更新循环：定期在后台更新缓存"""
        while self._running:
            try:
                await asyncio.sleep(self._cache["cache_interval"])  # 5分钟更新一次

                # 预热缓存
                await self._warm_up_cache()
                logger.debug(f"[自主性引擎] 缓存预热完成")

            except Exception as e:
                logger.error(f"[自主性引擎] 缓存更新错误: {e}")
                await asyncio.sleep(60)

    async def _warm_up_cache(self):
        """预热缓存:提前加载对话历史、记忆和LifeBook数据"""
        try:
            # 1. 更新对话历史缓存
            from apiserver.message_manager import message_manager
            recent_messages = message_manager.get_recent_messages("default", count=10)

            if recent_messages:
                conversation_summary = []
                for msg in recent_messages:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if content:
                        conversation_summary.append(f"{role}: {content}")

                self._cache["recent_memories"] = [{"content": "\n".join(conversation_summary[-10:])}]
                logger.debug(f"[自主性引擎] 预热对话历史缓存: {len(recent_messages)}条消息")
            else:
                self._cache["recent_memories"] = []
                logger.debug("[自主性引擎] 暂无对话历史")

            # 2. 更新长期记忆缓存
            from summer_memory.memory_manager import memory_manager
            if memory_manager.enabled:
                long_term_context = await memory_manager.query_memory("用户喜好、重要事件、长期记忆")
                self._cache["long_term_memories"] = [{"content": long_term_context}] if long_term_context else []
                logger.debug(f"[自主性引擎] 预热长期记忆缓存")

            # 3. 更新LifeBook缓存
            from mcpserver.mcp_registry import MCP_REGISTRY
            lifebook_agent = MCP_REGISTRY.get("LifeBook记忆管理")

            if lifebook_agent and hasattr(lifebook_agent, '_tool'):
                lifebook_context = await lifebook_agent._tool.read_lifebook({
                    "months": 1,
                    "max_tokens": 2000
                })
                self._cache["life_book_context"] = {"summary": lifebook_context[:500]} if lifebook_context else {}
                logger.debug(f"[自主性引擎] 预热LifeBook缓存")

            # 更新时间戳
            self._cache["cache_timestamp"] = time.time()

        except Exception as e:
            logger.warning(f"[自主性引擎] 缓存预热失败: {e}")
    
    async def _execute_action_queue(self):
        """执行行动队列"""
        if not self.action_queue:
            return
        
        # 按优先级排序
        self.action_queue.sort(key=lambda x: x.priority.value)
        
        while self.action_queue:
            action = self.action_queue.pop(0)
            
            try:
                await self._execute_single_action(action)
                
                # 记录历史
                self.action_history.append({
                    "action_id": action.action_id,
                    "type": action.action_type,
                    "description": action.description,
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                })
                
            except Exception as e:
                logger.error(f"[自主性引擎] 执行行动失败: {action.description}: {e}")
                
                # 记录失败
                self.action_history.append({
                    "action_id": action.action_id,
                    "type": action.action_type,
                    "description": action.description,
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": str(e)
                })
    
    async def _execute_single_action(self, action: AutonomousAction):
        """执行单个行动"""
        logger.info(f"[自主性引擎] 执行行动: {action.description}")
        
        if action.action_type == "suggestion":
            # 发送建议
            await self._send_suggestion(action)
        
        elif action.action_type == "communication":
            # 主动交流
            await self._send_communication(action)
        
        elif action.action_type == "task":
            # 执行后台任务
            await self._execute_background_task(action)
        
        else:
            logger.warning(f"[自主性引擎] 未知行动类型: {action.action_type}")
    
    async def _send_suggestion(self, action: AutonomousAction):
        """发送建议（通过主动交流系统）"""
        try:
            from system.active_communication import ActiveCommunication
            from apiserver.message_manager import message_manager

            comm = ActiveCommunication.get_instance()

            # 获取会话ID（默认会话）
            session_id = "default"

            # 保存主动消息到对话历史
            # 用户消息为空（这是AI主动发起的），AI消息为建议内容
            message_manager.save_conversation_and_logs(
                session_id=session_id,
                user_message="",  # 空用户消息，表示AI主动发起
                assistant_response=action.description
            )
            logger.info(f"[自主性引擎] 主动消息已保存到对话历史")

            # 创建主动交流任务
            await comm.send_topic_suggestion(
                topic=action.description,
                context=action.context
            )

        except Exception as e:
            logger.error(f"[自主性引擎] 发送建议失败: {e}")
    
    async def _send_communication(self, action: AutonomousAction):
        """发送主动交流"""
        try:
            from system.active_communication import ActiveCommunication

            comm = ActiveCommunication.get_instance()

            # 根据行动类型选择发送方式
            message_type_map = {
                "communication": "check_in",
                "suggestion": "suggestion",
                "care": "care",
                "reminder": "reminder"
            }
            message_type = message_type_map.get(action.action_type, "check_in")

            # 发送主动消息
            await comm.send_message(
                message=action.description,
                message_type=message_type,
                priority=action.priority.value,
                context=action.context
            )

            logger.info(f"[自主性引擎] 主动交流已发送: {action.description[:30]}...")

        except Exception as e:
            logger.error(f"[自主性引擎] 主动交流失败: {e}")
    
    async def _execute_background_task(self, action: AutonomousAction):
        """执行后台任务"""
        try:
            # TODO: 根据任务类型执行
            logger.info(f"[自主性引擎] 后台任务: {action.description}")
            
        except Exception as e:
            logger.error(f"[自主性引擎] 后台任务失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        status = {
            "agency_level": self.agency_level.name,
            "paused": self.agency_level == AgencyLevel.PAUSED,
            "paused_reason": self.paused_reason,
            "action_queue_size": len(self.action_queue),
            "action_history_size": len(self.action_history),
            "value_weights": self.value_weights,
            "last_decision_time": datetime.now().isoformat()
        }

        # 添加学习状态
        if self.preference_learner:
            status["learning"] = self.preference_learner.get_learning_status()

        return status

    def record_user_feedback(self, action_id: str, user_message: str, context: Dict[str, Any]):
        """
        记录用户反馈（供外部调用）

        Args:
            action_id: 行动ID
            user_message: 用户消息
            context: 上下文
        """
        if self.preference_learner:
            context["user_message"] = user_message
            self.preference_learner.learn_from_feedback(action_id, context)
            logger.info(f"[自主性引擎] 已记录用户反馈 for {action_id}")

        # 应用新的权重
        if self.preference_learner:
            self.value_weights = self.preference_learner.get_adjusted_weights()
    
    async def shutdown(self):
        """关闭引擎"""
        self._running = False
        logger.info("[自主性引擎] 已关闭")

    async def refresh_cache(self):
        """手动刷新缓存（供外部调用）"""
        await self._warm_up_cache()
        logger.info("[自主性引擎] 缓存已手动刷新")


# 全局实例
_agency_engine: Optional[AgencyEngine] = None


def get_agency_engine() -> AgencyEngine:
    """获取自主性引擎实例"""
    global _agency_engine
    if _agency_engine is None:
        _agency_engine = AgencyEngine()
    return _agency_engine
