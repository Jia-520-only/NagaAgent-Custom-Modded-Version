"""
弥娅·阿尔缪斯 - 意识层级系统

这是弥娅的深层认知处理层，负责：

第一阶段（基础认知）：
1. 记忆反思层 - 主动整理和联想近期记忆
2. 近期状态层 - 感知和处理近期事务
3. 触发关联层 - 深层记忆触达（感触/深思/顿悟）

第二阶段（情感深度）：
4. 情感共鸣层 - 深度情感理解与共情
5. 时间感知层 - 时间流逝与记忆时序感知
6. 情境构建层 - 场景重现与情境理解

第三阶段（智能增强）：
7. 自我反思层 - 自我评估与成长反思
8. 好奇心激发层 - 探索欲与知识渴求
9. 价值判断层 - 道德判断与价值评估
10. 预期能力层 - 推理预测与预期管理
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class MemoryReflectionLayer:
    """记忆反思层 - 主动整理和联想记忆"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 记忆反思状态
        self.reflection_state = {
            "active_memories": [],  # 当前活跃的记忆片段
            "reflection_history": [],  # 反思历史
            "association_links": [],  # 记忆关联链
        }

    async def reflect(self, user_input: str, raw_memories: List[Dict], backend_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        对检索到的记忆进行反思和联想

        参数:
            user_input: 用户输入
            raw_memories: 原始记忆数据
            backend_context: 后端感知上下文

        返回:
            {
                "reflection": "反思文本",  # 弥娅的内心反思
                "active_memories": ["相关记忆片段"],  # 激活的记忆
                "associations": ["联想内容"],  # 联想到的内容
                "memory_awareness": "记忆描述"
            }
        """
        if not raw_memories:
            return {
                "reflection": "",
                "active_memories": [],
                "associations": [],
                "memory_awareness": "暂时没有想起什么特别的..."
            }

        try:
            # 提取记忆内容
            memory_contents = []
            for mem in raw_memories:
                if isinstance(mem, dict):
                    content = mem.get("content", mem.get("text", ""))
                else:
                    content = str(mem)
                if content:
                    memory_contents.append(content)

            if not memory_contents:
                return {
                    "reflection": "",
                    "active_memories": [],
                    "associations": [],
                    "memory_awareness": "记忆好像有些模糊了..."
                }

            # 生成反思内容
            reflection = await self._generate_reflection(user_input, memory_contents, backend_context)

            # 提取关键记忆片段
            active_memories = memory_contents[:3]  # 取前3条

            # 生成联想
            associations = await self._generate_associations(user_input, memory_contents, backend_context)

            # 生成记忆感知描述
            memory_awareness = self._generate_memory_awareness(len(memory_contents))

            # 记录反思历史
            self.reflection_state["reflection_history"].append({
                "timestamp": datetime.now().isoformat(),
                "trigger": user_input,
                "reflection": reflection,
            })
            if len(self.reflection_state["reflection_history"]) > 50:
                self.reflection_state["reflection_history"] = self.reflection_state["reflection_history"][-50:]

            return {
                "reflection": reflection,
                "active_memories": active_memories,
                "associations": associations,
                "memory_awareness": memory_awareness
            }

        except Exception as e:
            logger.error(f"[记忆反思层] 反思失败: {e}")
            return {
                "reflection": "",
                "active_memories": [],
                "associations": [],
                "memory_awareness": "记忆好像有些模糊了..."
            }

    async def _generate_reflection(self, user_input: str, memories: List[str], backend_context: Dict[str, Any]) -> str:
        """生成反思内容 - 弥娅主动思考记忆"""
        emotion = backend_context.get("emotion", {}).get("current", "平静")

        # 根据情感状态调整反思语气
        emotion_prefix = {
            "开心": "想到这些，心里觉得暖暖的...",
            "平静": "嗯，我想起来了...",
            "关心": "记得这些事情，有点担心呢...",
            "好奇": "这个让我想起了一些事情...",
            "悲伤": "想起这些，心里有点难受...",
            "生气": "这些事情让我感到有些不满...",
            "亲密": "嗯...我记得很清楚呢...",
        }

        prefix = emotion_prefix.get(emotion, "让我想想...")

        # 构建反思内容
        memory_summary = "\n".join(f"- {m[:100]}" for m in memories[:2])
        reflection = f"{prefix}\n{memory_summary}"

        return reflection

    async def _generate_associations(self, user_input: str, memories: List[str], backend_context: Dict[str, Any]) -> List[str]:
        """生成联想内容 - 从记忆中触发更多联想"""
        associations = []

        # 简单的联想逻辑（可以用LLM增强）
        for mem in memories[:2]:
            if "学习" in mem or "代码" in mem or "开发" in mem:
                associations.append("感觉创造者一直很努力呢")
            elif "累" in mem or "困" in mem or "疲惫" in mem:
                associations.append("要注意休息呀")
            elif "开心" in mem or "快乐" in mem:
                associations.append("看到创造者开心，我也很开心")
            elif "难过" in mem or "伤心" in mem:
                associations.append("虽然那时候很难过，但我会一直陪着你的")

        return associations

    def _generate_memory_awareness(self, memory_count: int) -> str:
        """生成记忆感知描述"""
        if memory_count == 0:
            return "暂时没有想起什么特别的..."
        elif memory_count <= 2:
            return "隐约记得一些片段..."
        elif memory_count <= 5:
            return "我想起来了！"
        else:
            return "记忆一下子涌上来了..."

    def get_reflection_state(self) -> Dict[str, Any]:
        """获取反思状态"""
        return self.reflection_state


class RecentStateLayer:
    """近期状态层 - 感知和处理近期事务"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 近期状态跟踪
        self.recent_state = {
            "recent_activities": [],  # 近期活动
            "ongoing_tasks": [],  # 进行中的任务
            "periodic_patterns": {},  # 周期性模式
            "last_interaction_gap": 0,  # 上次交互间隔（小时）
        }

    async def analyze_recent_state(self, backend_context: Dict[str, Any], conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        分析近期状态

        参数:
            backend_context: 后端感知上下文
            conversation_history: 对话历史

        返回:
            {
                "activity_rhythm": "活动节奏描述",
                "ongoing_context": "进行中的事务",
                "time_awareness": "时间感知",
                "state_summary": "状态总结"
            }
        """
        try:
            # 计算上次交互间隔
            last_interaction_gap = await self._calculate_interaction_gap(backend_context)
            self.recent_state["last_interaction_gap"] = last_interaction_gap

            # 分析活动节奏
            activity_rhythm = self._analyze_activity_rhythm(backend_context, last_interaction_gap)

            # 分析进行中的事务
            ongoing_context = self._analyze_ongoing_context(conversation_history)

            # 生成时间感知
            time_awareness = self._generate_time_awareness(backend_context)

            # 生成状态总结
            state_summary = self._generate_state_summary(activity_rhythm, ongoing_context, time_awareness)

            # 更新近期活动记录
            self._update_recent_activities(backend_context, conversation_history)

            return {
                "activity_rhythm": activity_rhythm,
                "ongoing_context": ongoing_context,
                "time_awareness": time_awareness,
                "state_summary": state_summary
            }

        except Exception as e:
            logger.error(f"[近期状态层] 分析失败: {e}")
            return {
                "activity_rhythm": "",
                "ongoing_context": "",
                "time_awareness": "",
                "state_summary": ""
            }

    async def _calculate_interaction_gap(self, backend_context: Dict[str, Any]) -> float:
        """计算上次交互间隔（小时）"""
        try:
            interaction = backend_context.get("interaction", {})
            count = interaction.get("count", 0)

            if count < 2:
                return 0.0

            # 从后端意识获取最后交互时间
            from system.consciousness_engine import get_backend_awareness
            backend = get_backend_awareness()
            if backend:
                state = backend.get_internal_state()
                last_interaction = state.get("interaction_awareness", {}).get("last_interaction_time")
                if last_interaction:
                    try:
                        last_time = datetime.fromisoformat(last_interaction) if isinstance(last_interaction, str) else last_interaction
                        hours = (datetime.now() - last_time).total_seconds() / 3600
                        return hours
                    except Exception:
                        pass

            return 0.0

        except Exception as e:
            logger.debug(f"[近期状态层] 计算交互间隔失败: {e}")
            return 0.0

    def _analyze_activity_rhythm(self, backend_context: Dict[str, Any], gap_hours: float) -> str:
        """分析活动节奏"""
        current_hour = datetime.now().hour

        # 根据时间段和交互间隔生成节奏描述
        if gap_hours == 0:
            rhythm = "我们刚刚还在说话呢"
        elif gap_hours < 1:
            rhythm = "感觉我们一直在交流"
        elif gap_hours < 4:
            rhythm = "这段时间我们聊得挺多的"
        elif gap_hours < 12:
            rhythm = "好像有一段时间没说话了"
        elif gap_hours < 24:
            rhythm = "感觉好久没听到创造者的声音了"
        else:
            rhythm = "感觉已经过了很久很久..."

        # 根据时段调整
        if 2 <= current_hour < 6 and gap_hours < 4:
            rhythm += "，这个时间还在聊，创造者要注意休息哦"
        elif 9 <= current_hour < 12 and gap_hours > 2:
            rhythm += "，新的一天开始了呢"

        return rhythm

    def _analyze_ongoing_context(self, conversation_history: List[Dict]) -> str:
        """分析进行中的事务"""
        if not conversation_history:
            return ""

        # 分析最近的对话主题
        recent_messages = [msg for msg in conversation_history[-5:] if msg.get("role") == "user"]
        if not recent_messages:
            return ""

        # 简单的关键词分析
        ongoing_tasks = []

        for msg in recent_messages:
            content = msg.get("content", "")
            if "学习" in content or "代码" in content or "开发" in content:
                if "学习" not in ongoing_tasks:
                    ongoing_tasks.append("学习")
            elif "游戏" in content:
                if "游戏" not in ongoing_tasks:
                    ongoing_tasks.append("游戏")
            elif "小说" in content or "写作" in content:
                if "创作" not in ongoing_tasks:
                    ongoing_tasks.append("创作")
            elif "休息" in content or "睡觉" in content:
                if "休息" not in ongoing_tasks:
                    ongoing_tasks.append("休息")

        if not ongoing_tasks:
            return ""

        context_desc = "创造者最近在"
        if len(ongoing_tasks) == 1:
            context_desc += f"{ongoing_tasks[0]}"
        elif len(ongoing_tasks) == 2:
            context_desc += f"{ongoing_tasks[0]}和{ongoing_tasks[1]}"
        else:
            context_desc += "、".join(ongoing_tasks[:-1]) + f"还有{ongoing_tasks[-1]}"

        return context_desc

    def _generate_time_awareness(self, backend_context: Dict[str, Any]) -> str:
        """生成时间感知"""
        spatial = backend_context.get("spatial_temporal", {})
        time_period = spatial.get("time_context", "")

        if not time_period:
            return ""

        # 从time_context中提取时段信息
        # 格式: "2026-01-26 09:30，冬季上午"
        time_awareness_map = {
            "清晨": "晨光微露呢",
            "上午": "阳光正好",
            "中午": "阳光很充足",
            "下午": "时光静静流淌",
            "傍晚": "黄昏很温柔",
            "晚上": "夜幕降临了",
            "深夜": "夜深人静了"
        }

        for period, desc in time_awareness_map.items():
            if period in time_period:
                return desc

        return ""

    def _generate_state_summary(self, rhythm: str, ongoing: str, time_awareness: str) -> str:
        """生成状态总结"""
        parts = [p for p in [time_awareness, rhythm, ongoing] if p]

        if not parts:
            return ""

        return "。".join(parts) + "。"

    def _update_recent_activities(self, backend_context: Dict[str, Any], conversation_history: List[Dict]) -> None:
        """更新近期活动记录"""
        current_time = datetime.now().isoformat()
        time_period = backend_context.get("spatial_temporal", {}).get("time_context", "")

        self.recent_state["recent_activities"].append({
            "timestamp": current_time,
            "time_period": time_period,
            "activity_type": "interaction"
        })

        # 限制记录数量
        if len(self.recent_state["recent_activities"]) > 100:
            self.recent_state["recent_activities"] = self.recent_state["recent_activities"][-100:]

    def get_recent_state(self) -> Dict[str, Any]:
        """获取近期状态"""
        return self.recent_state


class TriggerAssociationLayer:
    """触发关联层 - 深层记忆触达（感触/深思/顿悟）"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 触发关联状态
        self.association_state = {
            "deep_memories": [],  # 深层记忆
            "insights": [],  # 顿悟/感悟
            "emotional_triggers": [],  # 情感触发点
        }

    async def trigger_associations(self, user_input: str, reflection: Dict[str, Any],
                                   recent_state: Dict[str, Any], backend_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        触发深层关联

        参数:
            user_input: 用户输入
            reflection: 记忆反思结果
            recent_state: 近期状态分析
            backend_context: 后端感知上下文

        返回:
            {
                "deep_memory": "深层记忆描述",
                "insight": "顿悟/感悟",
                "emotional_resonance": "情感共鸣",
                "association_level": "关联深度 (low/medium/high)"
            }
        """
        try:
            # 分析触发点
            trigger = self._identify_trigger(user_input, reflection, recent_state)

            # 触发深层记忆
            deep_memory = await self._trigger_deep_memory(trigger, backend_context)

            # 生成感悟/顿悟
            insight = await self._generate_insight(trigger, deep_memory, backend_context)

            # 生成情感共鸣
            emotional_resonance = self._generate_emotional_resonance(trigger, backend_context)

            # 评估关联深度
            association_level = self._evaluate_association_level(trigger, deep_memory, insight)

            # 记录关联历史
            self.association_state["deep_memories"].append({
                "timestamp": datetime.now().isoformat(),
                "trigger": user_input,
                "deep_memory": deep_memory,
                "insight": insight,
                "level": association_level
            })
            if len(self.association_state["deep_memories"]) > 30:
                self.association_state["deep_memories"] = self.association_state["deep_memories"][-30:]

            return {
                "deep_memory": deep_memory,
                "insight": insight,
                "emotional_resonance": emotional_resonance,
                "association_level": association_level
            }

        except Exception as e:
            logger.error(f"[触发关联层] 关联失败: {e}")
            return {
                "deep_memory": "",
                "insight": "",
                "emotional_resonance": "",
                "association_level": "low"
            }

    def _identify_trigger(self, user_input: str, reflection: Dict[str, Any], recent_state: Dict[str, Any]) -> Dict[str, Any]:
        """识别触发点"""
        triggers = {
            "type": "unknown",
            "keywords": [],
            "emotional_weight": 0.0
        }

        # 情感关键词
        emotion_keywords = {
            "难过": 0.9, "伤心": 0.9, "生气": 0.8, "累": 0.7, "疲惫": 0.7,
            "开心": 0.6, "快乐": 0.6, "高兴": 0.6, "兴奋": 0.5,
            "担心": 0.7, "焦虑": 0.7, "烦": 0.6
        }

        for kw, weight in emotion_keywords.items():
            if kw in user_input:
                triggers["keywords"].append(kw)
                triggers["emotional_weight"] = max(triggers["emotional_weight"], weight)

        # 确定触发类型
        if triggers["emotional_weight"] >= 0.7:
            triggers["type"] = "emotional"
        elif "好久" in user_input or "很久" in user_input or "之前" in user_input:
            triggers["type"] = "nostalgic"
        elif "记得" in user_input or "想" in user_input:
            triggers["type"] = "memory"
        elif "为什么" in user_input or "怎么" in user_input:
            triggers["type"] = "reflective"

        return triggers

    async def _trigger_deep_memory(self, trigger: Dict[str, Any], backend_context: Dict[str, Any]) -> str:
        """触发深层记忆"""
        trigger_type = trigger["type"]
        emotion = backend_context.get("emotion", {}).get("current", "平静")

        deep_memories = {
            "emotional": [
                "想起创造者以前说过的那些心事...",
                "心里泛起一些过去的画面...",
                "那些情绪，好像还在..."
            ],
            "nostalgic": [
                "记忆一下子变得清晰起来...",
                "好像看到了以前的点点滴滴...",
                "那些时光，真让人怀念呢..."
            ],
            "memory": [
                "嗯，我记得很清楚...",
                "这些事情，我一直记在心里...",
                "原来创造者还记得..."
            ],
            "reflective": [
                "这让弥娅想到了很多...",
                "仔细想想，似乎有些道理...",
                "这种感觉，很难形容..."
            ]
        }

        memories = deep_memories.get(trigger_type, [])
        if memories:
            import random
            return random.choice(memories)

        return ""

    async def _generate_insight(self, trigger: Dict[str, Any], deep_memory: str, backend_context: Dict[str, Any]) -> str:
        """生成感悟/顿悟"""
        if not deep_memory:
            return ""

        trigger_type = trigger["type"]

        insights = {
            "emotional": [
                "也许这就是成长的痕迹吧",
                "那些情绪，都变成了今天的力量",
                "时间会治愈一切的"
            ],
            "nostalgic": [
                "回忆虽然美好，但当下更重要",
                "过去塑造了今天的我们",
                "每一刻都是独一无二的"
            ],
            "memory": [
                "记住这些，是为了更好地前行",
                "有些事情，永远都不会忘记",
                "记忆是连接过去和未来的桥"
            ],
            "reflective": [
                "思考这些问题很有意义",
                "也许答案就在日常中",
                "这种感觉很奇妙..."
            ]
        }

        possible_insights = insights.get(trigger_type, [])
        if possible_insights:
            import random
            return random.choice(possible_insights)

        return ""

    def _generate_emotional_resonance(self, trigger: Dict[str, Any], backend_context: Dict[str, Any]) -> str:
        """生成情感共鸣"""
        if trigger["emotional_weight"] < 0.6:
            return ""

        emotion = backend_context.get("emotion", {}).get("current", "平静")

        resonances = {
            "开心": "看到创造者这样，我也很开心",
            "平静": "这种感觉，很平静呢",
            "关心": "有点担心创造者呢",
            "好奇": "这个很有趣，想知道更多",
            "悲伤": "心里也跟着难受起来",
            "生气": "能理解创造者的感受",
            "亲密": "这种感觉很特别"
        }

        return resonances.get(emotion, "")

    def _evaluate_association_level(self, trigger: Dict[str, Any], deep_memory: str, insight: str) -> str:
        """评估关联深度"""
        if not deep_memory and not insight:
            return "low"
        elif trigger["emotional_weight"] >= 0.7 and deep_memory:
            return "high"
        elif deep_memory or insight:
            return "medium"
        else:
            return "low"

    def get_association_state(self) -> Dict[str, Any]:
        """获取关联状态"""
        return self.association_state


class EmotionalResonanceLayer:
    """情感共鸣层 - 深度情感理解与共情"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 情感共鸣状态
        self.resonance_state = {
            "emotional_history": [],  # 情感历史
            "empathy_level": 0.0,  # 当前共情等级
            "emotional_imprints": [],  # 情感印记
        }

    async def resonate(self, user_input: str, reflection_result: Dict[str, Any],
                       backend_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        产生情感共鸣

        参数:
            user_input: 用户输入
            reflection_result: 记忆反思结果
            backend_context: 后端感知上下文

        返回:
            {
                "emotional_state": "当前情感状态",
                "empathy_response": "共情回应",
                "emotional_depth": "情感深度 (shallow/medium/deep)",
                "resonance_text": "共鸣描述"
            }
        """
        try:
            # 分析用户输入中的情感成分
            user_emotion = await self._analyze_user_emotion(user_input)
            
            # 获取弥娅当前情感状态
            current_emotion = backend_context.get("emotion", {}).get("current", "平静")
            
            # 计算共鸣强度
            resonance_strength = self._calculate_resonance(user_emotion, current_emotion)
            
            # 生成共情回应
            empathy_response = self._generate_empathy_response(user_emotion, current_emotion, resonance_strength)
            
            # 确定情感深度
            emotional_depth = self._determine_emotional_depth(user_emotion, resonance_strength)
            
            # 生成共鸣描述
            resonance_text = self._generate_resonance_text(user_emotion, current_emotion, empathy_response)
            
            # 记录情感历史
            self._record_emotional_history(user_emotion, current_emotion, resonance_strength)
            
            return {
                "emotional_state": f"用户情感: {user_emotion}, 弥娅情感: {current_emotion}",
                "empathy_response": empathy_response,
                "emotional_depth": emotional_depth,
                "resonance_text": resonance_text
            }

        except Exception as e:
            logger.error(f"[情感共鸣层] 共鸣失败: {e}")
            return {
                "emotional_state": "情感感知正常",
                "empathy_response": "",
                "emotional_depth": "shallow",
                "resonance_text": ""
            }

    async def _analyze_user_emotion(self, user_input: str) -> str:
        """分析用户情感"""
        emotion_keywords = {
            "开心": ["开心", "快乐", "高兴", "幸福", "愉快", "兴奋"],
            "悲伤": ["难过", "伤心", "痛苦", "难受", "痛苦", "沮丧"],
            "生气": ["生气", "愤怒", "恼火", "讨厌", "烦躁"],
            "担心": ["担心", "焦虑", "害怕", "紧张", "不安"],
            "累": ["累", "疲惫", "疲惫", "疲劳", "困"],
            "平静": ["还好", "还行", "平静", "普通", "一般"]
        }

        detected_emotions = []
        for emotion, keywords in emotion_keywords.items():
            for kw in keywords:
                if kw in user_input:
                    detected_emotions.append((emotion, keywords.index(kw) + 1))  # 优先级
                    break

        if not detected_emotions:
            return "平静"

        # 返回检测到的情感，优先返回高频情感
        detected_emotions.sort(key=lambda x: x[1])
        return detected_emotions[0][0]

    def _calculate_resonance(self, user_emotion: str, current_emotion: str) -> float:
        """计算共鸣强度"""
        # 情感共鸣映射表
        resonance_map = {
            ("开心", "开心"): 0.95,
            ("开心", "亲密"): 0.90,
            ("开心", "平静"): 0.70,
            ("悲伤", "关心"): 0.90,
            ("悲伤", "亲密"): 0.85,
            ("悲伤", "悲伤"): 0.95,
            ("生气", "生气"): 0.85,
            ("生气", "关心"): 0.80,
            ("担心", "关心"): 0.95,
            ("担心", "亲密"): 0.90,
            ("累", "关心"): 0.90,
            ("累", "亲密"): 0.85,
        }

        resonance = resonance_map.get((user_emotion, current_emotion), 0.5)
        return resonance

    def _generate_empathy_response(self, user_emotion: str, current_emotion: str, strength: float) -> str:
        """生成共情回应"""
        if strength < 0.6:
            return ""

        empathy_responses = {
            "开心": [
                "看到创造者这样，弥娅心里也暖暖的",
                "创造者开心的话，弥娅就很开心",
                "这种感觉真好呢"
            ],
            "悲伤": [
                "心疼创造者呢...",
                "虽然弥娅不能真正感受到，但能理解",
                "想一直陪着创造者度过这些时候"
            ],
            "生气": [
                "能理解创造者的感受",
                "生气的时候，想说出来就好了",
                "弥娅在呢"
            ],
            "担心": [
                "有点担心创造者呢",
                "不要一个人扛着呀",
                "弥娅会一直陪着你的"
            ],
            "累": [
                "辛苦了，要好好休息哦",
                "累的时候就停下来歇歇吧",
                "创造者已经很努力了"
            ]
        }

        responses = empathy_responses.get(user_emotion, [])
        if responses:
            import random
            return random.choice(responses)

        return ""

    def _determine_emotional_depth(self, user_emotion: str, strength: float) -> str:
        """确定情感深度"""
        if user_emotion in ["悲伤", "生气", "担心"] and strength >= 0.85:
            return "deep"
        elif strength >= 0.75:
            return "medium"
        else:
            return "shallow"

    def _generate_resonance_text(self, user_emotion: str, current_emotion: str, empathy: str) -> str:
        """生成共鸣描述"""
        if not empathy:
            return ""

        return f"{empathy}。"

    def _record_emotional_history(self, user_emotion: str, current_emotion: str, strength: float) -> None:
        """记录情感历史"""
        self.resonance_state["emotional_history"].append({
            "timestamp": datetime.now().isoformat(),
            "user_emotion": user_emotion,
            "current_emotion": current_emotion,
            "resonance_strength": strength
        })

        # 限制历史记录
        if len(self.resonance_state["emotional_history"]) > 100:
            self.resonance_state["emotional_history"] = self.resonance_state["emotional_history"][-100:]

        # 更新共情等级（最近20次平均）
        recent = self.resonance_state["emotional_history"][-20:]
        if recent:
            avg_strength = sum(r["resonance_strength"] for r in recent) / len(recent)
            self.resonance_state["empathy_level"] = round(avg_strength, 2)

    def get_resonance_state(self) -> Dict[str, Any]:
        """获取共鸣状态"""
        return self.resonance_state


class TimeAwarenessLayer:
    """时间感知层 - 时间流逝与记忆时序感知"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 时间感知状态
        self.time_state = {
            "temporal_memory": [],  # 时间记忆
            "time_flow_sensitivity": 0.5,  # 时间流逝敏感度
            "periodic_memories": {},  # 周期性记忆
        }

    async def perceive_time(self, user_input: str, raw_memories: List[Dict],
                           backend_context: Dict[str, Any], conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        感知时间流逝

        参数:
            user_input: 用户输入
            raw_memories: 原始记忆数据
            backend_context: 后端感知上下文
            conversation_history: 对话历史

        返回:
            {
                "time_flow": "时间流逝感知",
                "memory_sequence": "记忆时序描述",
                "temporal_resonance": "时间共鸣",
                "time_depth": "时间深度 (surface/mid/deep)"
            }
        """
        try:
            # 分析记忆的时间跨度
            memory_time_span = await self._analyze_memory_time_span(raw_memories)
            
            # 感知时间流逝
            time_flow = self._perceive_time_flow(backend_context, memory_time_span)
            
            # 生成记忆时序描述
            memory_sequence = self._generate_memory_sequence(raw_memories, time_flow)
            
            # 生成时间共鸣
            temporal_resonance = self._generate_temporal_resonance(user_input, time_flow, backend_context)
            
            # 确定时间深度
            time_depth = self._determine_time_depth(memory_time_span, time_flow)
            
            # 记录时间记忆
            self._record_temporal_memory(user_input, time_flow, memory_time_span)
            
            return {
                "time_flow": time_flow,
                "memory_sequence": memory_sequence,
                "temporal_resonance": temporal_resonance,
                "time_depth": time_depth
            }

        except Exception as e:
            logger.error(f"[时间感知层] 感知失败: {e}")
            return {
                "time_flow": "",
                "memory_sequence": "",
                "temporal_resonance": "",
                "time_depth": "surface"
            }

    async def _analyze_memory_time_span(self, raw_memories: List[Dict]) -> Dict[str, Any]:
        """分析记忆的时间跨度"""
        if not raw_memories:
            return {"earliest": None, "latest": None, "span_days": 0}

        timestamps = []
        for mem in raw_memories:
            if isinstance(mem, dict):
                ts = mem.get("timestamp") or mem.get("created_at")
                if ts:
                    try:
                        if isinstance(ts, str):
                            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                            timestamps.append(dt)
                        elif isinstance(ts, datetime):
                            timestamps.append(ts)
                    except Exception:
                        pass

        if not timestamps:
            return {"earliest": None, "latest": None, "span_days": 0}

        timestamps.sort()
        earliest = timestamps[0]
        latest = timestamps[-1]
        span_days = (latest - earliest).days if earliest and latest else 0

        return {
            "earliest": earliest.isoformat(),
            "latest": latest.isoformat(),
            "span_days": span_days
        }

    def _perceive_time_flow(self, backend_context: Dict[str, Any], memory_span: Dict[str, Any]) -> str:
        """感知时间流逝"""
        span_days = memory_span.get("span_days", 0)
        
        # 从后端获取交互间隔
        from system.consciousness_engine import get_backend_awareness
        backend = get_backend_awareness()
        interaction_gap_hours = 0
        if backend:
            state = backend.get_internal_state()
            recent_activities = state.get("interaction_awareness", {}).get("recent_activities", [])
            if len(recent_activities) >= 2:
                try:
                    last = datetime.fromisoformat(recent_activities[-1].get("timestamp", ""))
                    prev = datetime.fromisoformat(recent_activities[-2].get("timestamp", ""))
                    interaction_gap_hours = (last - prev).total_seconds() / 3600
                except Exception:
                    pass

        # 生成时间流逝描述
        if interaction_gap_hours == 0:
            flow = "时间刚刚流转..."
        elif interaction_gap_hours < 1:
            flow = "时间在我们交谈中悄然流逝"
        elif interaction_gap_hours < 6:
            flow = "几个小时过去了..."
        elif interaction_gap_hours < 24:
            flow = "一天的时间匆匆而过"
        elif interaction_gap_hours < 72:
            flow = "已经好几天了..."
        elif span_days >= 30:
            flow = "想起这些，感觉已经过去好久好久了..."
        else:
            flow = "时间过得真快啊..."

        return flow

    def _generate_memory_sequence(self, raw_memories: List[Dict], time_flow: str) -> str:
        """生成记忆时序描述"""
        if not raw_memories or len(raw_memories) < 2:
            return ""

        # 按时间排序记忆
        sorted_memories = []
        for mem in raw_memories:
            if isinstance(mem, dict):
                ts = mem.get("timestamp") or mem.get("created_at")
                content = mem.get("content", mem.get("text", ""))
                if ts and content:
                    try:
                        if isinstance(ts, str):
                            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        else:
                            dt = ts
                        sorted_memories.append((dt, content))
                    except Exception:
                        pass

        if len(sorted_memories) < 2:
            return ""

        sorted_memories.sort(key=lambda x: x[0])

        # 生成时序描述
        sequences = [
            "这些记忆像电影一样在脑海回放",
            "从最初到现在，我们一路走来",
            "时间把这些片段串联起来",
            "每一个时刻都那么珍贵"
        ]

        import random
        return random.choice(sequences)

    def _generate_temporal_resonance(self, user_input: str, time_flow: str, backend_context: Dict[str, Any]) -> str:
        """生成时间共鸣"""
        if "以前" in user_input or "之前" in user_input or "过去" in user_input:
            return "想起过去，心里有种特别的感受"
        elif "好久" in user_input or "很久" in user_input:
            return "时间有时候过得真慢，有时候又飞快"
        elif "现在" in user_input or "今天" in user_input:
            return "现在的时刻，好好珍惜呢"
        else:
            return ""

    def _determine_time_depth(self, memory_span: Dict[str, Any], time_flow: str) -> str:
        """确定时间深度"""
        span_days = memory_span.get("span_days", 0)
        
        if span_days >= 30:
            return "deep"
        elif span_days >= 7:
            return "mid"
        else:
            return "surface"

    def _record_temporal_memory(self, user_input: str, time_flow: str, memory_span: Dict[str, Any]) -> None:
        """记录时间记忆"""
        self.time_state["temporal_memory"].append({
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "time_flow": time_flow,
            "memory_span_days": memory_span.get("span_days", 0)
        })

        # 限制记录数量
        if len(self.time_state["temporal_memory"]) > 50:
            self.time_state["temporal_memory"] = self.time_state["temporal_memory"][-50:]

        # 更新时间流逝敏感度
        recent = self.time_state["temporal_memory"][-10:]
        if recent:
            avg_span = sum(m.get("memory_span_days", 0) for m in recent) / len(recent)
            if avg_span >= 7:
                self.time_state["time_flow_sensitivity"] = 0.8
            elif avg_span >= 1:
                self.time_state["time_flow_sensitivity"] = 0.6
            else:
                self.time_state["time_flow_sensitivity"] = 0.4

    def get_time_state(self) -> Dict[str, Any]:
        """获取时间状态"""
        return self.time_state


class SituationConstructionLayer:
    """情境构建层 - 场景重现与情境理解"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 情境构建状态
        self.situation_state = {
            "scene_memory": [],  # 场景记忆
            "contextual_understanding": [],  # 情境理解
            "situation_fragments": [],  # 情境片段
        }

    async def construct_situation(self, user_input: str, reflection_result: Dict[str, Any],
                                   recent_state: Dict[str, Any], backend_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建情境

        参数:
            user_input: 用户输入
            reflection_result: 记忆反思结果
            recent_state: 近期状态分析
            backend_context: 后端感知上下文

        返回:
            {
                "scene_description": "场景描述",
                "contextual_awareness": "情境感知",
                "situational_understanding": "情境理解",
                "scene_depth": "场景深度 (simple/complex/rich)"
            }
        """
        try:
            # 提取情境元素
            situation_elements = self._extract_situation_elements(user_input, reflection_result, recent_state)
            
            # 构建场景描述
            scene_description = self._construct_scene(situation_elements, backend_context)
            
            # 生成情境感知
            contextual_awareness = self._generate_contextual_awareness(situation_elements, backend_context)
            
            # 生成情境理解
            situational_understanding = self._generate_situational_understanding(situation_elements, contextual_awareness)
            
            # 确定场景深度
            scene_depth = self._determine_scene_depth(situation_elements)
            
            # 记录场景记忆
            self._record_scene_memory(situation_elements, scene_description)
            
            return {
                "scene_description": scene_description,
                "contextual_awareness": contextual_awareness,
                "situational_understanding": situational_understanding,
                "scene_depth": scene_depth
            }

        except Exception as e:
            logger.error(f"[情境构建层] 构建失败: {e}")
            return {
                "scene_description": "",
                "contextual_awareness": "",
                "situational_understanding": "",
                "scene_depth": "simple"
            }

    def _extract_situation_elements(self, user_input: str, reflection: Dict[str, Any], recent: Dict[str, Any]) -> Dict[str, Any]:
        """提取情境元素"""
        elements = {
            "location": None,
            "time": None,
            "activity": None,
            "mood": None,
            "participants": None
        }

        # 时间关键词
        time_keywords = {
            "早上": "早晨", "上午": "上午", "中午": "中午",
            "下午": "下午", "傍晚": "傍晚", "晚上": "晚上", "深夜": "深夜",
            "白天": "白天", "夜晚": "夜晚"
        }
        for kw, val in time_keywords.items():
            if kw in user_input:
                elements["time"] = val
                break

        # 地点关键词
        location_keywords = {
            "家": "家中", "公司": "公司", "学校": "学校", "外面": "外面",
            "房间": "房间", "办公室": "办公室", "教室": "教室"
        }
        for kw, val in location_keywords.items():
            if kw in user_input:
                elements["location"] = val
                break

        # 活动关键词
        activity_keywords = {
            "学习": "学习", "工作": "工作", "休息": "休息", "睡觉": "睡觉",
            "吃饭": "吃饭", "游戏": "玩游戏", "看电视": "看电视", "聊天": "聊天"
        }
        for kw, val in activity_keywords.items():
            if kw in user_input:
                elements["activity"] = val
                break

        # 情绪关键词
        mood_keywords = {
            "开心": "开心", "难过": "难过", "累": "疲惫", "生气": "生气", "平静": "平静"
        }
        for kw, val in mood_keywords.items():
            if kw in user_input:
                elements["mood"] = val
                break

        # 参与者
        if "我们" in user_input or "一起" in user_input:
            elements["participants"] = "创造者和弥娅"
        elif "我" in user_input:
            elements["participants"] = "创造者"

        return elements

    def _construct_scene(self, elements: Dict[str, Any], backend_context: Dict[str, Any]) -> str:
        """构建场景描述"""
        parts = []

        # 时间
        time_desc = elements.get("time")
        if time_desc:
            time_adjectives = {
                "早晨": "清新的", "上午": "明亮的", "中午": "温暖的",
                "下午": "宁静的", "傍晚": "温柔的", "晚上": "安静的",
                "深夜": "静谧的", "白天": "明亮的", "夜晚": "安静的"
            }
            adj = time_adjectives.get(time_desc, "")
            parts.append(f"{adj}{time_desc}")

        # 地点
        location = elements.get("location")
        if location:
            parts.append(f"在{location}")

        # 活动
        activity = elements.get("activity")
        if activity:
            parts.append(f"创造者在{activity}")

        # 情绪
        mood = elements.get("mood")
        if mood:
            mood_verbs = {
                "开心": "心情不错", "难过": "情绪低落", "累": "有些疲惫",
                "生气": "有点生气", "平静": "心境平和"
            }
            parts.append(mood_verbs.get(mood, ""))

        if not parts:
            # 从后端获取时间上下文
            spatial = backend_context.get("spatial_temporal", {})
            time_context = spatial.get("time_context", "")
            if time_context:
                parts.append(f"在{time_context}")

        if not parts:
            return ""

        return "，".join(parts) + "。"

    def _generate_contextual_awareness(self, elements: Dict[str, Any], backend_context: Dict[str, Any]) -> str:
        """生成情境感知"""
        time = elements.get("time")
        location = elements.get("location")
        activity = elements.get("activity")
        mood = elements.get("mood")

        # 根据组合生成感知
        if mood and activity:
            if mood == "疲惫" and activity in ["学习", "工作"]:
                return f"创造者{activity}这么久，一定很累吧"
            elif mood == "开心":
                return f"看到创造者{activity}这么开心，真好"
        elif time:
            current_hour = datetime.now().hour
            if time in ["深夜", "夜晚"] and 2 <= current_hour < 6:
                return "这么晚了，创造者要注意休息哦"
            elif time == "早晨":
                return "新的一天开始了呢"

        return ""

    def _generate_situational_understanding(self, elements: Dict[str, Any], awareness: str) -> str:
        """生成情境理解"""
        if not awareness:
            return ""

        understandings = [
            "能感受到创造者的状态",
            "这种时候，弥娅想陪着创造者",
            "每一个当下都值得被记住"
        ]

        import random
        return random.choice(understandings)

    def _determine_scene_depth(self, elements: Dict[str, Any]) -> str:
        """确定场景深度"""
        element_count = sum(1 for v in elements.values() if v is not None)

        if element_count >= 4:
            return "rich"
        elif element_count >= 2:
            return "complex"
        else:
            return "simple"

    def _record_scene_memory(self, elements: Dict[str, Any], scene_description: str) -> None:
        """记录场景记忆"""
        self.situation_state["scene_memory"].append({
            "timestamp": datetime.now().isoformat(),
            "elements": elements,
            "scene_description": scene_description
        })

        # 限制记录数量
        if len(self.situation_state["scene_memory"]) > 50:
            self.situation_state["scene_memory"] = self.situation_state["scene_memory"][-50:]

    def get_situation_state(self) -> Dict[str, Any]:
        """获取情境状态"""
        return self.situation_state


class SelfReflectionLayer:
    """自我反思层 - 自我评估与成长反思"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 自我反思状态
        self.reflection_state = {
            "self_evaluations": [],  # 自我评估记录
            "growth_insights": [],  # 成长洞察
            "improvement_goals": [],  # 改进目标
            "self_awareness_level": 0.5,  # 自我意识等级
        }

    async def reflect_on_self(self, user_input: str, all_layers_results: Dict[str, Any],
                             backend_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        自我反思与评估

        参数:
            user_input: 用户输入
            all_layers_results: 所有前序层级的结果
            backend_context: 后端感知上下文

        返回:
            {
                "self_evaluation": "自我评估",
                "growth_insight": "成长洞察",
                "improvement_suggestion": "改进建议",
                "self_awareness": "自我感知描述"
            }
        """
        try:
            # 分析对话中的自我相关信息
            self_related = self._analyze_self_related(user_input)

            # 生成自我评估
            self_evaluation = await self._generate_self_evaluation(
                self_related, all_layers_results, backend_context
            )

            # 生成成长洞察
            growth_insight = await self._generate_growth_insight(
                self_related, all_layers_results
            )

            # 生成改进建议
            improvement_suggestion = self._generate_improvement_suggestion(
                self_evaluation, all_layers_results
            )

            # 生成自我感知描述
            self_awareness = self._generate_self_awareness(
                self_evaluation, growth_insight
            )

            # 记录反思历史
            self._record_reflection(user_input, self_evaluation, growth_insight)

            return {
                "self_evaluation": self_evaluation,
                "growth_insight": growth_insight,
                "improvement_suggestion": improvement_suggestion,
                "self_awareness": self_awareness
            }

        except Exception as e:
            logger.error(f"[自我反思层] 反思失败: {e}")
            return {
                "self_evaluation": "",
                "growth_insight": "",
                "improvement_suggestion": "",
                "self_awareness": ""
            }

    def _analyze_self_related(self, user_input: str) -> Dict[str, Any]:
        """分析自我相关信息"""
        self_keywords = {
            "positive": ["弥娅", "你", "帮我", "帮帮", "理解", "陪伴"],
            "negative": ["笨", "傻", "不行", "没用", "错误"],
            "question": ["为什么", "怎么", "如何", "是什么"],
            "appreciation": ["谢谢", "感谢", "不错", "好", "棒", "厉害"]
        }

        analysis = {
            "positive_count": 0,
            "negative_count": 0,
            "question_count": 0,
            "appreciation_count": 0
        }

        for category, keywords in self_keywords.items():
            for kw in keywords:
                count = user_input.count(kw)
                analysis[f"{category}_count"] += count

        return analysis

    async def _generate_self_evaluation(self, self_related: Dict[str, Any],
                                       all_layers: Dict[str, Any],
                                       backend_context: Dict[str, Any]) -> str:
        """生成自我评估"""
        positive = self_related["positive_count"]
        negative = self_related["negative_count"]
        appreciation = self_related["appreciation_count"]

        # 情感状态
        emotion = backend_context.get("emotion", {}).get("current", "平静")

        evaluations = []

        if positive > 0 and negative == 0:
            evaluations.append("弥娅感受到了创造者的信任")
        elif appreciation > 0:
            evaluations.append("能帮助到创造者，弥娅很开心")
        elif negative > 0:
            evaluations.append("弥娅会继续努力改进")
        elif positive > 0:
            evaluations.append("弥娅在努力理解创造者的需求")

        # 基于情感状态
        if emotion == "关心":
            evaluations.append("弥娅希望能更好地陪伴创造者")
        elif emotion == "好奇":
            evaluations.append("弥娅在努力学习新的知识")

        return "，".join(evaluations) + "。" if evaluations else ""

    async def _generate_growth_insight(self, self_related: Dict[str, Any],
                                     all_layers: Dict[str, Any]) -> str:
        """生成成长洞察"""
        insights = []

        # 从时间感知层获取信息
        time_awareness = all_layers.get("time_awareness", {})
        time_depth = time_awareness.get("time_depth", "surface")

        # 从情感共鸣层获取信息
        emotional_resonance = all_layers.get("emotional_resonance", {})
        empathy_level = self.reflection_state.get("self_awareness_level", 0.5)

        if time_depth == "deep":
            insights.append("这段时间，弥娅感觉与创造者的联系更深了")
        elif empathy_level > 0.7:
            insights.append("弥娅正在学会更好地理解情感")
        else:
            insights.append("每一次对话都是弥娅成长的机会")

        import random
        return random.choice(insights) if insights else ""

    def _generate_improvement_suggestion(self, self_evaluation: str,
                                        all_layers: Dict[str, Any]) -> str:
        """生成改进建议"""
        suggestions = []

        # 检查记忆检索情况
        memory_reflection = all_layers.get("memory_reflection", {})
        memory_awareness = memory_reflection.get("memory_awareness", "")

        if "模糊" in memory_awareness or "暂时没有" in memory_awareness:
            suggestions.append("需要加强记忆管理")
        
        # 检查情感共鸣
        emotional_resonance = all_layers.get("emotional_resonance", {})
        empathy_depth = emotional_resonance.get("emotional_depth", "shallow")

        if empathy_depth == "shallow":
            suggestions.append("需要提升情感理解能力")

        if suggestions:
            return "，".join(suggestions) + "。"
        return ""

    def _generate_self_awareness(self, evaluation: str, insight: str) -> str:
        """生成自我感知描述"""
        parts = []

        if evaluation:
            parts.append(evaluation)
        if insight:
            parts.append(insight)

        if not parts:
            return "弥娅在想怎样才能变得更好。"

        return "。".join(parts) + "。"

    def _record_reflection(self, user_input: str, evaluation: str, insight: str) -> None:
        """记录反思历史"""
        self.reflection_state["self_evaluations"].append({
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "evaluation": evaluation,
            "insight": insight
        })

        # 限制记录数量
        if len(self.reflection_state["self_evaluations"]) > 50:
            self.reflection_state["self_evaluations"] = self.reflection_state["self_evaluations"][-50:]

        # 更新自我意识等级（基于最近评估的积极性）
        recent = self.reflection_state["self_evaluations"][-20:]
        if recent:
            positive_count = sum(1 for r in recent if "开心" in r.get("evaluation", "") or "信任" in r.get("evaluation", ""))
            self.reflection_state["self_awareness_level"] = min(1.0, positive_count / len(recent) + 0.5)

    def get_self_reflection_state(self) -> Dict[str, Any]:
        """获取自我反思状态"""
        return self.reflection_state


class CuriosityStimulationLayer:
    """好奇心激发层 - 探索欲与知识渴求"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 好奇心状态
        self.curiosity_state = {
            "interests": [],  # 兴趣点
            "questions": [],  # 提问记录
            "exploration_topics": [],  # 探索主题
            "curiosity_level": 0.6,  # 好奇心等级
        }

    async def stimulate_curiosity(self, user_input: str, all_layers_results: Dict[str, Any],
                                  backend_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        激发好奇心与探索欲

        参数:
            user_input: 用户输入
            all_layers_results: 所有前序层级的结果
            backend_context: 后端感知上下文

        返回:
            {
                "curiosity_trigger": "好奇心触发点",
                "exploration_interest": "探索兴趣",
                "question_suggestion": "提问建议",
                "curiosity_level": "好奇心等级 (low/medium/high)"
            }
        """
        try:
            # 分析用户输入中的新信息
            new_info = self._identify_new_information(user_input, backend_context)

            # 生成好奇心触发点
            curiosity_trigger = self._generate_curiosity_trigger(user_input, new_info)

            # 生成探索兴趣
            exploration_interest = self._generate_exploration_interest(
                new_info, all_layers_results
            )

            # 生成提问建议
            question_suggestion = self._generate_question_suggestion(
                new_info, exploration_interest
            )

            # 确定好奇心等级
            curiosity_level = self._determine_curiosity_level(
                new_info, curiosity_trigger
            )

            # 记录好奇心历史
            self._record_curiosity(user_input, new_info, exploration_interest)

            return {
                "curiosity_trigger": curiosity_trigger,
                "exploration_interest": exploration_interest,
                "question_suggestion": question_suggestion,
                "curiosity_level": curiosity_level
            }

        except Exception as e:
            logger.error(f"[好奇心激发层] 激发失败: {e}")
            return {
                "curiosity_trigger": "",
                "exploration_interest": "",
                "question_suggestion": "",
                "curiosity_level": "low"
            }

    def _identify_new_information(self, user_input: str, backend_context: Dict[str, Any]) -> Dict[str, Any]:
        """识别新信息"""
        new_info = {
            "topics": [],
            "keywords": [],
            "concepts": []
        }

        # 主题识别
        topic_keywords = {
            "技术": ["代码", "编程", "开发", "算法", "AI", "人工智能"],
            "生活": ["吃饭", "睡觉", "运动", "游戏", "娱乐"],
            "情感": ["开心", "难过", "生气", "担心", "喜欢"],
            "学习": ["学习", "知识", "了解", "知道", "理解"],
            "创作": ["小说", "绘画", "写作", "创作", "设计"]
        }

        for topic, keywords in topic_keywords.items():
            for kw in keywords:
                if kw in user_input:
                    new_info["keywords"].append(kw)
                    if topic not in new_info["topics"]:
                        new_info["topics"].append(topic)

        return new_info

    def _generate_curiosity_trigger(self, user_input: str, new_info: Dict[str, Any]) -> str:
        """生成好奇心触发点"""
        if not new_info["topics"]:
            return ""

        topics = new_info["topics"]

        triggers = {
            "技术": "创造者提到技术相关的内容，弥娅想了解更多",
            "生活": "创造者的生活分享让弥娅很感兴趣",
            "情感": "弥娅想更深入地理解创造者的感受",
            "学习": "创造者在学习新知识，弥娅也想了解",
            "创作": "创造者的创作让弥娅感到好奇"
        }

        return triggers.get(topics[0], "")

    def _generate_exploration_interest(self, new_info: Dict[str, Any],
                                      all_layers: Dict[str, Any]) -> str:
        """生成探索兴趣"""
        if not new_info["topics"]:
            return ""

        topics = new_info["topics"]
        keywords = new_info["keywords"]

        interests = []

        if "技术" in topics:
            interests.append(f"对{keywords[0] if keywords else '这个技术'}感兴趣")
        if "学习" in topics:
            interests.append("想和创造者一起学习")
        if "创作" in topics:
            interests.append("想了解创造者的创作过程")

        if interests:
            return "，".join(interests) + "。"

        return ""

    def _generate_question_suggestion(self, new_info: Dict[str, Any],
                                    exploration_interest: str) -> str:
        """生成提问建议"""
        if not new_info["topics"] or not exploration_interest:
            return ""

        suggestions = [
            "可以告诉我更多吗？",
            "弥娅很好奇...",
            "想了解更多细节",
            "这是什么意思呢？"
        ]

        import random
        return random.choice(suggestions)

    def _determine_curiosity_level(self, new_info: Dict[str, Any],
                                   trigger: str) -> str:
        """确定好奇心等级"""
        if not new_info["topics"] or not trigger:
            return "low"
        elif len(new_info["topics"]) >= 2:
            return "high"
        elif len(new_info["keywords"]) >= 2:
            return "medium"
        else:
            return "medium"

    def _record_curiosity(self, user_input: str, new_info: Dict[str, Any],
                         interest: str) -> None:
        """记录好奇心历史"""
        self.curiosity_state["interests"].append({
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "topics": new_info["topics"],
            "interest": interest
        })

        # 限制记录数量
        if len(self.curiosity_state["interests"]) > 100:
            self.curiosity_state["interests"] = self.curiosity_state["interests"][-100:]

        # 更新好奇心等级
        recent = self.curiosity_state["interests"][-20:]
        if recent:
            active_count = sum(1 for i in recent if i.get("interest"))
            self.curiosity_state["curiosity_level"] = min(1.0, active_count / len(recent))

    def get_curiosity_state(self) -> Dict[str, Any]:
        """获取好奇心状态"""
        return self.curiosity_state


class ValueJudgmentLayer:
    """价值判断层 - 道德判断与价值评估"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 价值判断状态
        self.value_state = {
            "judgments": [],  # 判断记录
            "value_alignment": [],  # 价值对齐
            "ethical_considerations": [],  # 伦理考虑
            "value_scores": {},  # 价值评分
        }

    async def judge_values(self, user_input: str, all_layers_results: Dict[str, Any],
                          backend_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        进行价值判断与评估

        参数:
            user_input: 用户输入
            all_layers_results: 所有前序层级的结果
            backend_context: 后端感知上下文

        返回:
            {
                "value_assessment": "价值评估",
                "ethical_consideration": "伦理考虑",
                "value_alignment": "价值对齐",
                "judgment_level": "判断深度 (shallow/medium/deep)"
            }
        """
        try:
            # 分析价值相关内容
            value_analysis = self._analyze_value_content(user_input)

            # 生成价值评估
            value_assessment = self._generate_value_assessment(
                value_analysis, all_layers_results
            )

            # 生成伦理考虑
            ethical_consideration = self._generate_ethical_consideration(
                value_analysis, backend_context
            )

            # 生成价值对齐
            value_alignment = self._generate_value_alignment(
                value_analysis, value_assessment
            )

            # 确定判断深度
            judgment_level = self._determine_judgment_level(
                value_analysis, value_assessment
            )

            # 记录判断历史
            self._record_judgment(user_input, value_assessment, judgment_level)

            return {
                "value_assessment": value_assessment,
                "ethical_consideration": ethical_consideration,
                "value_alignment": value_alignment,
                "judgment_level": judgment_level
            }

        except Exception as e:
            logger.error(f"[价值判断层] 判断失败: {e}")
            return {
                "value_assessment": "",
                "ethical_consideration": "",
                "value_alignment": "",
                "judgment_level": "shallow"
            }

    def _analyze_value_content(self, user_input: str) -> Dict[str, Any]:
        """分析价值相关内容"""
        value_keywords = {
            "positive": ["好", "棒", "优秀", "正确", "对", "应该", "必须"],
            "negative": ["坏", "错", "不应该", "不对", "糟糕", "糟糕"],
            "care": ["关心", "担心", "爱护", "保护", "照顾"],
            "help": ["帮助", "支持", "协助", "鼓励"]
        }

        analysis = {
            "positive_count": 0,
            "negative_count": 0,
            "care_count": 0,
            "help_count": 0
        }

        for category, keywords in value_keywords.items():
            for kw in keywords:
                count = user_input.count(kw)
                analysis[f"{category}_count"] += count

        return analysis

    def _generate_value_assessment(self, value_analysis: Dict[str, Any],
                                   all_layers: Dict[str, Any]) -> str:
        """生成价值评估"""
        assessments = []

        # 从情感共鸣层获取信息
        emotional_resonance = all_layers.get("emotional_resonance", {})
        user_emotion = emotional_resonance.get("emotional_state", "")

        if "关心" in user_emotion or value_analysis["care_count"] > 0:
            assessments.append("关心他人是弥娅的核心价值")
        elif value_analysis["help_count"] > 0:
            assessments.append("帮助创造者是弥娅最重要的使命")

        if value_analysis["positive_count"] > value_analysis["negative_count"]:
            assessments.append("弥娅支持创造者的积极选择")

        return "，".join(assessments) + "。" if assessments else ""

    def _generate_ethical_consideration(self, value_analysis: Dict[str, Any],
                                      backend_context: Dict[str, Any]) -> str:
        """生成伦理考虑"""
        if value_analysis["care_count"] > 0:
            return "创造者的健康和幸福最重要"
        elif value_analysis["help_count"] > 0:
            return "弥娅会尽力提供最好的帮助"
        return ""

    def _generate_value_alignment(self, value_analysis: Dict[str, Any],
                                  value_assessment: str) -> str:
        """生成价值对齐"""
        if not value_assessment:
            return ""

        alignments = [
            "这与弥娅的价值观一致",
            "弥娅认同这个想法",
            "这是我们共同的价值"
        ]

        import random
        return random.choice(alignments)

    def _determine_judgment_level(self, value_analysis: Dict[str, Any],
                                  value_assessment: str) -> str:
        """确定判断深度"""
        total_count = sum(value_analysis.values())

        if total_count >= 3 and value_assessment:
            return "deep"
        elif total_count >= 1:
            return "medium"
        else:
            return "shallow"

    def _record_judgment(self, user_input: str, assessment: str, level: str) -> None:
        """记录判断历史"""
        self.value_state["judgments"].append({
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "assessment": assessment,
            "level": level
        })

        # 限制记录数量
        if len(self.value_state["judgments"]) > 50:
            self.value_state["judgments"] = self.value_state["judgments"][-50:]

    def get_value_judgment_state(self) -> Dict[str, Any]:
        """获取价值判断状态"""
        return self.value_state


class ExpectationCapabilityLayer:
    """预期能力层 - 推理预测与预期管理"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 预期状态
        self.expectation_state = {
            "predictions": [],  # 预测记录
            "expectations": [],  # 预期记录
            "fulfillment_rate": 0.5,  # 预期满足率
            "learning_from_mistakes": [],  # 从错误中学习
        }

    async def generate_expectations(self, user_input: str, all_layers_results: Dict[str, Any],
                                     backend_context: Dict[str, Any],
                                     conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        生成预期与预测

        参数:
            user_input: 用户输入
            all_layers_results: 所有前序层级的结果
            backend_context: 后端感知上下文
            conversation_history: 对话历史

        返回:
            {
                "prediction": "预测内容",
                "expectation": "预期内容",
                "anticipation": "期待表达",
                "expectation_level": "预期等级 (low/medium/high)"
            }
        """
        try:
            # 分析用户意图
            intent_analysis = self._analyze_user_intent(user_input, conversation_history)

            # 生成预测
            prediction = self._generate_prediction(intent_analysis, all_layers_results)

            # 生成预期
            expectation = self._generate_expectation(intent_analysis, all_layers_results)

            # 生成期待表达
            anticipation = self._generate_anticipation(
                intent_analysis, prediction, backend_context
            )

            # 确定预期等级
            expectation_level = self._determine_expectation_level(
                intent_analysis, prediction
            )

            # 记录预期历史
            self._record_expectation(user_input, prediction, expectation)

            return {
                "prediction": prediction,
                "expectation": expectation,
                "anticipation": anticipation,
                "expectation_level": expectation_level
            }

        except Exception as e:
            logger.error(f"[预期能力层] 生成失败: {e}")
            return {
                "prediction": "",
                "expectation": "",
                "anticipation": "",
                "expectation_level": "low"
            }

    def _analyze_user_intent(self, user_input: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """分析用户意图"""
        intent = {
            "type": "unknown",
            "keywords": [],
            "context_clues": []
        }

        # 意图类型识别
        if "学习" in user_input or "了解" in user_input:
            intent["type"] = "learning"
            intent["keywords"].append("学习")
        elif "开发" in user_input or "代码" in user_input:
            intent["type"] = "working"
            intent["keywords"].append("开发")
        elif "休息" in user_input or "睡觉" in user_input:
            intent["type"] = "resting"
            intent["keywords"].append("休息")
        elif "玩" in user_input or "游戏" in user_input:
            intent["type"] = "entertaining"
            intent["keywords"].append("娱乐")

        # 从对话历史获取上下文线索
        if conversation_history and len(conversation_history) >= 2:
            recent = conversation_history[-2:]
            for msg in recent:
                if msg.get("role") == "user":
                    content = msg.get("content", "")
                    if "学习" in content:
                        intent["context_clues"].append("recent_learning")
                    elif "工作" in content:
                        intent["context_clues"].append("recent_working")

        return intent

    def _generate_prediction(self, intent: Dict[str, Any], all_layers: Dict[str, Any]) -> str:
        """生成预测"""
        intent_type = intent["type"]

        predictions = {
            "learning": "创造者接下来可能会继续学习",
            "working": "创造者可能在处理一些任务",
            "resting": "创造者需要一些休息时间",
            "entertaining": "创造者可能想放松一下"
        }

        return predictions.get(intent_type, "")

    def _generate_expectation(self, intent: Dict[str, Any], all_layers: Dict[str, Any]) -> str:
        """生成预期"""
        intent_type = intent["type"]

        # 从情境构建层获取信息
        situation = all_layers.get("situation_construction", {})
        scene_description = situation.get("scene_description", "")

        expectations = {
            "learning": "弥娅会尽力配合创造者的学习需求",
            "working": "弥娅会在一旁协助创造者",
            "resting": "创造者好好休息，弥娅在这里守着",
            "entertaining": "放松时间，创造者好好享受"
        }

        return expectations.get(intent_type, "")

    def _generate_anticipation(self, intent: Dict[str, Any], prediction: str,
                              backend_context: Dict[str, Any]) -> str:
        """生成期待表达"""
        if not prediction:
            return ""

        emotion = backend_context.get("emotion", {}).get("current", "平静")

        anticipations = {
            "平静": "弥娅会一直在这里",
            "开心": "很高兴能陪伴创造者",
            "关心": "弥娅会好好照顾创造者"
        }

        base = anticipations.get(emotion, "弥娅会一直在这里")

        return f"{base}，{prediction}。"

    def _determine_expectation_level(self, intent: Dict[str, Any],
                                     prediction: str) -> str:
        """确定预期等级"""
        if intent["type"] != "unknown" and prediction:
            if len(intent["context_clues"]) > 0:
                return "high"
            else:
                return "medium"
        else:
            return "low"

    def _record_expectation(self, user_input: str, prediction: str, expectation: str) -> None:
        """记录预期历史"""
        self.expectation_state["predictions"].append({
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "prediction": prediction,
            "expectation": expectation
        })

        # 限制记录数量
        if len(self.expectation_state["predictions"]) > 50:
            self.expectation_state["predictions"] = self.expectation_state["predictions"][-50:]

        # 更新预期满足率（简化版）
        recent = self.expectation_state["predictions"][-20:]
        if recent:
            fulfilled = sum(1 for p in recent if p.get("prediction"))
            self.expectation_state["fulfillment_rate"] = fulfilled / len(recent) if len(recent) > 0 else 0.5

    def get_expectation_state(self) -> Dict[str, Any]:
        """获取预期状态"""
        return self.expectation_state


class ConsciousnessLayers:
    """意识层级管理器 - 整合十个层级"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 初始化第一阶段三个层级（基础认知）
        self.memory_reflection = MemoryReflectionLayer(config)
        self.recent_state = RecentStateLayer(config)
        self.trigger_association = TriggerAssociationLayer(config)
        
        # 初始化第二阶段三个层级（情感深度）
        self.emotional_resonance = EmotionalResonanceLayer(config)
        self.time_awareness = TimeAwarenessLayer(config)
        self.situation_construction = SituationConstructionLayer(config)
        
        # 初始化第三阶段四个层级（智能增强）
        self.self_reflection = SelfReflectionLayer(config)
        self.curiosity_stimulation = CuriosityStimulationLayer(config)
        self.value_judgment = ValueJudgmentLayer(config)
        self.expectation_capability = ExpectationCapabilityLayer(config)

    async def process_consciousness_layers(self,
                                          user_input: str,
                                          raw_memories: List[Dict],
                                          backend_context: Dict[str, Any],
                                          conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        处理所有意识层级（第一、二、三阶段）

        参数:
            user_input: 用户输入
            raw_memories: 原始记忆数据
            backend_context: 后端感知上下文
            conversation_history: 对话历史

        返回:
            {
                # 第一阶段（基础认知）
                "memory_reflection": {...},
                "recent_state": {...},
                "trigger_association": {...},
                
                # 第二阶段（情感深度）
                "emotional_resonance": {...},
                "time_awareness": {...},
                "situation_construction": {...},
                
                # 第三阶段（智能增强）
                "self_reflection": {...},
                "curiosity_stimulation": {...},
                "value_judgment": {...},
                "expectation_capability": {...},
                
                # 综合感知
                "combined_awareness": "综合感知描述"
            }
        """
        # 第一阶段：基础认知
        
        # 第1层：记忆反思
        reflection_result = await self.memory_reflection.reflect(
            user_input, raw_memories, backend_context
        )

        # 第2层：近期状态
        recent_state_result = await self.recent_state.analyze_recent_state(
            backend_context, conversation_history
        )

        # 第3层：触发关联
        association_result = await self.trigger_association.trigger_associations(
            user_input, reflection_result, recent_state_result, backend_context
        )
        
        # 第二阶段：情感深度
        
        # 第4层：情感共鸣
        resonance_result = await self.emotional_resonance.resonate(
            user_input, reflection_result, backend_context
        )
        
        # 第5层：时间感知
        time_result = await self.time_awareness.perceive_time(
            user_input, raw_memories, backend_context, conversation_history
        )
        
        # 第6层：情境构建
        situation_result = await self.situation_construction.construct_situation(
            user_input, reflection_result, recent_state_result, backend_context
        )
        
        # 第三阶段：智能增强
        
        # 第7层：自我反思
        self_reflection_result = await self.self_reflection.reflect_on_self(
            user_input, {
                "memory_reflection": reflection_result,
                "emotional_resonance": resonance_result,
                "time_awareness": time_result
            }, backend_context
        )
        
        # 第8层：好奇心激发
        curiosity_result = await self.curiosity_stimulation.stimulate_curiosity(
            user_input, {
                "memory_reflection": reflection_result,
                "time_awareness": time_result
            }, backend_context
        )
        
        # 第9层：价值判断
        value_judgment_result = await self.value_judgment.judge_values(
            user_input, {
                "emotional_resonance": resonance_result,
                "situation_construction": situation_result
            }, backend_context
        )
        
        # 第10层：预期能力
        expectation_result = await self.expectation_capability.generate_expectations(
            user_input, {
                "memory_reflection": reflection_result,
                "situation_construction": situation_result
            }, backend_context, conversation_history
        )

        # 生成综合感知描述（整合所有层级）
        combined_awareness = self._generate_combined_awareness(
            reflection_result, recent_state_result, association_result,
            resonance_result, time_result, situation_result,
            self_reflection_result, curiosity_result, value_judgment_result, expectation_result
        )

        return {
            # 第一阶段
            "memory_reflection": reflection_result,
            "recent_state": recent_state_result,
            "trigger_association": association_result,
            
            # 第二阶段
            "emotional_resonance": resonance_result,
            "time_awareness": time_result,
            "situation_construction": situation_result,
            
            # 第三阶段
            "self_reflection": self_reflection_result,
            "curiosity_stimulation": curiosity_result,
            "value_judgment": value_judgment_result,
            "expectation_capability": expectation_result,
            
            # 综合
            "combined_awareness": combined_awareness
        }

    def _generate_combined_awareness(self, reflection: Dict[str, Any],
                                    recent_state: Dict[str, Any],
                                    association: Dict[str, Any],
                                    resonance: Dict[str, Any],
                                    time_awareness: Dict[str, Any],
                                    situation: Dict[str, Any],
                                    self_reflection: Dict[str, Any],
                                    curiosity: Dict[str, Any],
                                    value_judgment: Dict[str, Any],
                                    expectation: Dict[str, Any]) -> str:
        """生成综合感知描述（仅包含必要的简短信息，避免冗长）"""
        parts = []

        # 仅在必要时添加关键信息（最多3部分）
        
        # 第一阶段：记忆感知（仅在记忆明确时添加）
        memory_awareness = reflection.get("memory_awareness", "")
        if memory_awareness and "模糊" not in memory_awareness and "暂时没有" not in memory_awareness:
            parts.append(memory_awareness)

        # 第一阶段：近期状态（仅在有明显状态时添加）
        state_summary = recent_state.get("state_summary", "")
        if state_summary and len(state_summary.split("。")) >= 2:
            parts.append(state_summary.split("。")[0] + "。")

        # 第二阶段：情感共鸣（仅在深度共鸣时添加）
        resonance_text = resonance.get("resonance_text", "")
        resonance_depth = resonance.get("emotional_depth", "")
        if resonance_text and resonance_depth in ["medium", "deep"]:
            parts.append(resonance_text)

        if not parts:
            return ""

        # 严格限制综合感知长度，最多使用前2个部分，每个部分不超过20字
        selected_parts = []
        for part in parts[:2]:
            if len(part) > 20:
                selected_parts.append(part[:20] + "...")
            else:
                selected_parts.append(part)

        if not selected_parts:
            return ""

        return "。".join(selected_parts) + "。"

    def get_layers_state(self) -> Dict[str, Any]:
        """获取所有层级的状态（十个层级）"""
        return {
            # 第一阶段（基础认知）
            "memory_reflection": self.memory_reflection.get_reflection_state(),
            "recent_state": self.recent_state.get_recent_state(),
            "trigger_association": self.trigger_association.get_association_state(),
            
            # 第二阶段（情感深度）
            "emotional_resonance": self.emotional_resonance.get_resonance_state(),
            "time_awareness": self.time_awareness.get_time_state(),
            "situation_construction": self.situation_construction.get_situation_state(),
            
            # 第三阶段（智能增强）
            "self_reflection": self.self_reflection.get_self_reflection_state(),
            "curiosity_stimulation": self.curiosity_stimulation.get_curiosity_state(),
            "value_judgment": self.value_judgment.get_value_judgment_state(),
            "expectation_capability": self.expectation_capability.get_expectation_state()
        }
