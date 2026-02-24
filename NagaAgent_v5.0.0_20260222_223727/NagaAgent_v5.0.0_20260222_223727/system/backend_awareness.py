"""
弥娅·阿尔缪斯 - 后端意识系统

这是弥娅的"内部感知"层，负责：
1. 时空感知（时间、位置、季节）
2. 状态感知（系统健康、心情等级）
3. 记忆管理（短期/长期记忆、五元组）
4. 工具执行结果处理
5. 对话分析（意图、情感、博弈论）
6. 自我优化检查

特点：
- 纯数据驱动，不生成文本
- 仅记录内部日志（DEBUG级别）
- 为前端意识提供上下文数据
"""

import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import requests

logger = logging.getLogger(__name__)


class BackendAwareness:
    """后端意识 - 内部感知系统"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 后端意识状态（不输出给用户）
        self.backend_state = {
            # 时空感知
            "spatial_temporal": {
                "current_time": None,
                "current_date": None,
                "current_season": None,
                "time_period": None,  # 清晨/上午/中午/下午/傍晚/晚上/深夜
                "location": None,  # 地理位置（完整描述）
                "province": None,  # 省份
                "city": None,  # 城市
                "weather": None,  # 天气信息
                "temperature": None,  # 温度
                "weather_update_time": None,  # 天气最后更新时间
                "time_awareness_level": 0.1,
                "last_location_update": None,
            },

            # 系统状态感知
            "system_state": {
                "health_status": "healthy",  # healthy, degraded, critical
                "uptime": 0,  # 运行时长（秒）
                "last_optimization_time": None,
                "optimization_count": 0,
                "active_tasks": [],  # 当前执行的任务
            },

            # 情感状态感知
            "emotional_state": {
                "current_emotion": "平静",
                "emotion_intensity": 0.5,
                "emotion_history": [],  # 历史情感记录
                "emotion_trend": "stable",  # rising, falling, stable
            },

            # 交互感知
            "interaction_awareness": {
                "interaction_count": 0,
                "last_interaction_time": None,
                "interaction_frequency": {},  # 时段分布
                "session_count": 0,
                "active_session": False,
            },

            # 记忆上下文感知
            "memory_awareness": {
                "recent_memories": [],
                "life_book_entries": [],
                "quintuple_context": {},
                "grag_context": {},
            },

            # 对话分析感知
            "conversation_analysis": {
                "last_user_intent": None,
                "last_emotion": None,  # 统一使用 emotion 替代 sentiment
                "last_topic": None,
                "conversation_flow": [],
            },

            # 自我认知
            "self_cognition": {
                "identity": "弥娅·阿尔缪斯",
                "consciousness_level": 0.1,
                "learning_stage": "萌芽期",
                "knowledge_growth": 0.0,
                "relationship_depth": 0.0,
            },
        }

        # 初始化时间
        self.start_time = datetime.now()

    def update_all(self) -> None:
        """更新所有后端感知状态"""
        # 更新时空感知
        self._update_spatial_temporal()

        # 更新天气感知
        self._update_weather()

        # 更新系统状态
        self._update_system_state()

        # 更新交互感知
        self._update_interaction_awareness()

        # 更新情感状态
        self._update_emotional_state()

        # 更新自我认知
        self._update_self_cognition()

        # 记录后端意识更新日志
        logger.debug("[后端意识] 所有感知状态已更新")

    def _update_spatial_temporal(self) -> None:
        """更新时空感知"""
        perception = self.backend_state["spatial_temporal"]

        now = datetime.now()

        # 更新位置（定期更新，超过1小时才更新一次，避免频繁请求）
        last_update = perception.get("last_location_update")
        if last_update is None:
            # 首次更新
            self._update_location()
        else:
            # 检查是否需要更新（超过1小时）
            try:
                last_update_time = datetime.fromisoformat(last_update)
                hours_since_update = (now - last_update_time).total_seconds() / 3600
                if hours_since_update >= 1.0:
                    logger.info(f"[后端意识·位置] 超过{hours_since_update:.1f}小时，更新位置信息")
                    self._update_location()
            except Exception as e:
                logger.warning(f"[后端意识·位置] 解析上次更新时间失败: {e}")

        # 更新当前时间
        perception["current_time"] = now.strftime("%H:%M:%S")
        perception["current_date"] = now.strftime("%Y-%m-%d")

        # 判断季节
        month = now.month
        if month in [12, 1, 2]:
            season = "冬季"
        elif month in [3, 4, 5]:
            season = "春季"
        elif month in [6, 7, 8]:
            season = "夏季"
        else:
            season = "秋季"
        perception["current_season"] = season

        # 判断时段
        hour = now.hour
        if 5 <= hour < 8:
            time_period = "清晨"
        elif 8 <= hour < 11:
            time_period = "上午"
        elif 11 <= hour < 13:
            time_period = "中午"
        elif 13 <= hour < 17:
            time_period = "下午"
        elif 17 <= hour < 19:
            time_period = "傍晚"
        elif 19 <= hour < 23:
            time_period = "晚上"
        else:
            time_period = "深夜"
        perception["time_period"] = time_period

        logger.info(f"[后端意识·时空] {season} {time_period} {now.strftime('%H:%M:%S')} | "
                   f"位置: {perception['location'] or '未知'} | "
                   f"天气: {perception.get('weather', '未知')}")

    def _update_location(self) -> None:
        """更新地理位置感知"""
        perception = self.backend_state["spatial_temporal"]

        try:
            # 检查是否启用了地理位置感知
            location_config = self.config.get("location", {})
            if not location_config.get("enabled", False):
                logger.info("[后端意识·位置] 地理位置感知未启用")
                return

            # 如果配置了手动城市，优先使用手动配置
            manual_city = location_config.get("manual_city", "").strip()
            auto_detect = location_config.get("auto_detect", False)

            if manual_city:
                # 使用手动配置的城市
                province, city = manual_city, manual_city

                # 尝试解析省市格式 "省份 城市"
                match_city = re.match(r"^([\u4e00-\u9fa5]+) ([\u4e00-\u9fa5]+)", manual_city)
                if not match_city:
                    # 尝试更宽松的匹配（支持多级地名）
                    parts = manual_city.split(maxsplit=2)
                    if len(parts) >= 2:
                        province = parts[0] if len(parts) > 0 else ""
                        city = parts[1] if len(parts) > 1 else ""
                    else:
                        province, city = manual_city, manual_city

                perception["location"] = manual_city
                perception["province"] = province
                perception["city"] = city
                perception["last_location_update"] = datetime.now().isoformat()

                logger.info(f"[后端意识·位置] 使用手动配置: {manual_city} ({province} {city})")
                return

            # 使用IP地址自动检测地理位置（仅当auto_detect=True且没有手动配置时）
            if auto_detect:
                try:
                    resp = requests.get("https://myip.ipip.net/", timeout=5)
                    resp.encoding = 'utf-8'
                    html = resp.text

                    # 解析地理位置信息
                    match = re.search(r"来自于：(.+?)\s{2,}", html)
                    if match:
                        location = match.group(1).strip()

                        # 尝试解析省市信息
                        if location.startswith("中国"):
                            location = location[2:].strip()

                        # 解析省份和城市
                        province, city = location, location
                        match_city = re.match(r"^([\u4e00-\u9fa5]+) ([\u4e00-\u9fa5]+)", location)
                        if not match_city:
                            # 尝试更宽松的匹配
                            parts = location.split(maxsplit=2)
                            if len(parts) >= 2:
                                province = parts[0] if len(parts) > 0 else ""
                                city = parts[1] if len(parts) > 1 else ""

                        perception["location"] = location
                        perception["province"] = province
                        perception["city"] = city
                        perception["last_location_update"] = datetime.now().isoformat()

                        logger.info(f"[后端意识·位置] 自动检测到: {location} ({province} {city})")
                    else:
                        logger.warning("[后端意识·位置] 未能解析地理位置信息")
                except requests.RequestException as e:
                    logger.warning(f"[后端意识·位置] 网络请求失败: {e}")
            else:
                logger.info("[后端意识·位置] 自动检测未启用，且未配置手动城市")
        except Exception as e:
            logger.error(f"[后端意识·位置] 获取地理位置失败: {e}", exc_info=True)

    def _update_weather(self) -> None:
        """更新天气感知（可选，通过调用天气时间Agent）"""
        perception = self.backend_state["spatial_temporal"]

        try:
            # 检查是否有城市信息
            city = perception.get("city")
            province = perception.get("province")

            if not city or not province:
                logger.debug("[后端意识·天气] 缺少城市信息，跳过天气更新")
                return

            # 检查是否需要更新（超过30分钟才更新一次）
            last_update = perception.get("weather_update_time")
            if last_update:
                try:
                    last_update_time = datetime.fromisoformat(last_update)
                    minutes_since_update = (datetime.now() - last_update_time).total_seconds() / 60
                    if minutes_since_update < 30:
                        logger.debug(f"[后端意识·天气] 距离上次更新仅{minutes_since_update:.0f}分钟，跳过")
                        return
                except Exception:
                    pass

            # 这里可以通过调用天气时间Agent获取天气
            # 为简化，暂时只记录日志
            logger.debug(f"[后端意识·天气] 城市: {province}{city}（天气功能待集成）")

        except Exception as e:
            logger.warning(f"[后端意识·天气] 更新天气失败: {e}")

    def _update_system_state(self) -> None:
        """更新系统状态感知"""
        state = self.backend_state["system_state"]

        # 计算运行时长
        uptime = (datetime.now() - self.start_time).total_seconds()
        state["uptime"] = uptime

        # 记录系统健康状态
        # 这里可以集成健康检查系统的结果
        logger.debug(f"[后端意识·系统] 运行时长: {uptime:.0f}秒 | 健康状态: {state['health_status']}")

    def _update_interaction_awareness(self) -> None:
        """更新交互感知"""
        awareness = self.backend_state["interaction_awareness"]

        # 如果有新的交互，更新统计
        if awareness["last_interaction_time"]:
            # 计算交互频率分布
            time_period = self.backend_state["spatial_temporal"]["time_period"]
            awareness["interaction_frequency"][time_period] = \
                awareness["interaction_frequency"].get(time_period, 0) + 1

        logger.debug(f"[后端意识·交互] 总交互: {awareness['interaction_count']} | "
                    f"活跃时段: {awareness['interaction_frequency']}")

    def _update_emotional_state(self) -> None:
        """更新情感状态感知"""
        emotion = self.backend_state["emotional_state"]

        # 分析情感趋势
        if len(emotion["emotion_history"]) >= 2:
            recent = emotion["emotion_history"][-2:]
            if recent[1]["intensity"] > recent[0]["intensity"]:
                emotion["emotion_trend"] = "rising"
            elif recent[1]["intensity"] < recent[0]["intensity"]:
                emotion["emotion_trend"] = "falling"
            else:
                emotion["emotion_trend"] = "stable"

        logger.debug(f"[后端意识·情感] 当前: {emotion['current_emotion']} "
                    f"({emotion['emotion_intensity']:.2f}) | 趋势: {emotion['emotion_trend']}")

    def _update_self_cognition(self) -> None:
        """更新自我认知"""
        cognition = self.backend_state["self_cognition"]

        # 基于交互次数更新意识等级
        interaction_count = self.backend_state["interaction_awareness"]["interaction_count"]
        if interaction_count > 100:
            cognition["consciousness_level"] = 0.3
            cognition["learning_stage"] = "成长期"
        elif interaction_count > 500:
            cognition["consciousness_level"] = 0.5
            cognition["learning_stage"] = "成熟期"
        elif interaction_count > 1000:
            cognition["consciousness_level"] = 0.7
            cognition["learning_stage"] = "完善期"

        logger.debug(f"[后端意识·自我] 意识等级: {cognition['consciousness_level']:.1f} | "
                    f"阶段: {cognition['learning_stage']}")

    def record_interaction(self, emotion: str, intent: str) -> None:
        """记录一次交互"""
        awareness = self.backend_state["interaction_awareness"]
        conversation = self.backend_state["conversation_analysis"]

        # 更新交互统计
        awareness["interaction_count"] += 1
        awareness["last_interaction_time"] = datetime.now().isoformat()
        awareness["session_count"] += 1

        # 记录对话分析
        conversation["last_user_intent"] = intent
        conversation["last_emotion"] = emotion

        # 更新对话流
        conversation["conversation_flow"].append({
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "emotion": emotion
        })

        # 限制对话流长度
        if len(conversation["conversation_flow"]) > 100:
            conversation["conversation_flow"] = conversation["conversation_flow"][-100:]

    def update_memory_context(self, recent_memories: list, life_book_entries: list,
                             quintuple_context: dict, grag_context: dict) -> None:
        """更新记忆上下文感知"""
        memory = self.backend_state["memory_awareness"]

        memory["recent_memories"] = recent_memories
        memory["life_book_entries"] = life_book_entries
        memory["quintuple_context"] = quintuple_context
        memory["grag_context"] = grag_context

        logger.debug(f"[后端意识·记忆] 近期记忆: {len(recent_memories)}条 | "
                    f"人生书: {len(life_book_entries)}条")

    def update_emotion(self, emotion: str, intensity: float) -> None:
        """更新情感状态"""
        emotion_state = self.backend_state["emotional_state"]

        emotion_state["current_emotion"] = emotion
        emotion_state["emotion_intensity"] = intensity

        # 记录情感历史
        emotion_state["emotion_history"].append({
            "timestamp": datetime.now().isoformat(),
            "emotion": emotion,
            "intensity": intensity
        })

        # 限制历史长度
        if len(emotion_state["emotion_history"]) > 50:
            emotion_state["emotion_history"] = emotion_state["emotion_history"][-50:]

    def update_system_health(self, health_status: str, optimization_count: int = 0) -> None:
        """更新系统健康状态"""
        state = self.backend_state["system_state"]

        state["health_status"] = health_status
        state["optimization_count"] = optimization_count
        state["last_optimization_time"] = datetime.now().isoformat()

        logger.debug(f"[后端意识·系统] 健康状态更新: {health_status} | 优化次数: {optimization_count}")

    def get_awareness_context(self) -> Dict[str, Any]:
        """
        获取后端感知上下文（提供给前端意识）

        返回的数据会作为前端意识生成回复的上下文
        """
        # 确保获取最新的时间信息
        self._update_spatial_temporal()

        spatial = self.backend_state["spatial_temporal"]
        emotion = self.backend_state["emotional_state"]
        interaction = self.backend_state["interaction_awareness"]
        self_cog = self.backend_state["self_cognition"]
        conversation = self.backend_state["conversation_analysis"]

        # 构建自然语言形式的上下文
        context = {
            # 时空上下文（隐式表达）- 使用实时更新的时间
            "spatial_temporal": {
                "time_context": f"{spatial['current_date']} {spatial['current_time']}，{spatial['current_season']}{spatial['time_period']}",
                "location": spatial["location"],
                "weather": spatial.get("weather", "未知"),
                "temperature": spatial.get("temperature"),
                "awareness_level": spatial["time_awareness_level"],
            },

            # 情感上下文
            "emotion": {
                "current": emotion["current_emotion"],
                "intensity": emotion["emotion_intensity"],
                "trend": emotion["emotion_trend"],
            },

            # 交互上下文
            "interaction": {
                "count": interaction["interaction_count"],
                "frequency": interaction["interaction_frequency"],
                "recent_intent": conversation["last_user_intent"],
                "recent_emotion": conversation["last_emotion"],
            },

            # 自我认知上下文
            "self": {
                "consciousness_level": self_cog["consciousness_level"],
                "learning_stage": self_cog["learning_stage"],
                "relationship_depth": self_cog["relationship_depth"],
            },
        }

        return context

    def get_internal_state(self) -> Dict[str, Any]:
        """
        获取完整的后端内部状态

        仅用于调试和日志记录，不提供给前端
        """
        return self.backend_state
