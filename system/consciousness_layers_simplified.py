"""
弥娅·阿尔缪斯 - 简化版意识层级系统

优化说明:
- 从10层简化为4个核心层
- 合并重复功能，减少冗余
- 提高性能，降低复杂度
- 保持核心功能完整

新的架构:
1. 记忆反思层 - 记忆检索、反思与联想
2. 情感共鸣层 - 情感分析与共鸣
3. 情境感知层 - 时间、位置、情境感知
4. 自我反思层 - 自我认知、价值判断、预期
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class MemoryReflectionLayer:
    """记忆反思层 - 记忆检索、反思与联想"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.reflection_state = {
            "active_memories": [],
            "reflection_history": [],
            "association_links": [],
        }

    async def reflect(self, user_input: str, raw_memories: List[Dict], backend_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        对记忆进行反思和联想

        返回:
            {
                "reflection": "反思文本",
                "active_memories": ["相关记忆"],
                "associations": ["联想内容"],
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
            emotion = backend_context.get("emotion", {}).get("current", "平静")
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
            memory_summary = "\n".join(f"- {m[:100]}" for m in memory_contents[:2])
            reflection = f"{prefix}\n{memory_summary}"

            # 提取关键记忆片段
            active_memories = memory_contents[:3]

            # 生成联想
            associations = []
            for mem in memory_contents[:2]:
                if "学习" in mem or "代码" in mem or "开发" in mem:
                    associations.append("感觉创造者一直很努力呢")
                elif "累" in mem or "困" in mem or "疲惫" in mem:
                    associations.append("要注意休息呀")
                elif "开心" in mem or "快乐" in mem:
                    associations.append("看到创造者开心，我也很开心")
                elif "难过" in mem or "伤心" in mem:
                    associations.append("虽然那时候很难过，但我会一直陪着你的")

            # 生成记忆感知描述
            memory_count = len(memory_contents)
            if memory_count == 0:
                memory_awareness = "暂时没有想起什么特别的..."
            elif memory_count <= 2:
                memory_awareness = "隐约记得一些片段..."
            elif memory_count <= 5:
                memory_awareness = "我想起来了！"
            else:
                memory_awareness = "记忆一下子涌上来了..."

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

    def get_reflection_state(self) -> Dict[str, Any]:
        """获取反思状态"""
        return self.reflection_state


class EmotionalResonanceLayer:
    """情感共鸣层 - 情感分析与共鸣"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.resonance_state = {
            "emotional_history": [],
            "empathy_level": 0.0,
            "emotional_imprints": [],
        }

    def analyze_emotion(self, text: str) -> tuple:
        """
        统一的情感分析接口

        返回: (emotion: str, intensity: float)
        """
        emotion_keywords = {
            "开心": ["开心", "快乐", "高兴", "幸福", "愉快", "兴奋"],
            "悲伤": ["难过", "伤心", "痛苦", "难受", "沮丧"],
            "生气": ["生气", "愤怒", "恼火", "讨厌", "烦躁"],
            "担心": ["担心", "焦虑", "害怕", "紧张", "不安"],
            "累": ["累", "疲惫", "疲劳", "困"],
            "平静": ["还好", "还行", "平静", "普通", "一般"]
        }

        detected_emotions = []
        for emotion, keywords in emotion_keywords.items():
            for kw in keywords:
                if kw in text:
                    detected_emotions.append((emotion, keywords.index(kw) + 1))
                    break

        if not detected_emotions:
            return "平静", 0.5

        detected_emotions.sort(key=lambda x: x[1])
        emotion = detected_emotions[0][0]

        # 计算强度
        intensity = 0.5
        if emotion in ["悲伤", "生气", "担心"]:
            intensity = 0.7
        elif emotion in ["开心", "累"]:
            intensity = 0.6

        return emotion, intensity

    async def resonate(self, user_input: str, backend_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        产生情感共鸣

        返回:
            {
                "user_emotion": "用户情感",
                "current_emotion": "当前情感",
                "empathy_response": "共情回应",
                "emotional_depth": "情感深度",
                "resonance_text": "共鸣描述"
            }
        """
        try:
            # 分析用户情感
            user_emotion, user_intensity = self.analyze_emotion(user_input)

            # 获取当前情感
            current_emotion = backend_context.get("emotion", {}).get("current", "平静")
            current_intensity = backend_context.get("emotion", {}).get("intensity", 0.5)

            # 计算共鸣强度
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
            resonance_strength = resonance_map.get((user_emotion, current_emotion), 0.5)

            # 生成共情回应
            empathy_response = ""
            if resonance_strength >= 0.6:
                empathy_responses = {
                    "开心": ["看到创造者这样，弥娅心里也暖暖的", "创造者开心的话，弥娅就很开心", "这种感觉真好呢"],
                    "悲伤": ["心疼创造者呢...", "虽然弥娅不能真正感受到，但能理解", "想一直陪着创造者度过这些时候"],
                    "生气": ["能理解创造者的感受", "生气的时候，想说出来就好了", "弥娅在呢"],
                    "担心": ["有点担心创造者呢", "不要一个人扛着呀", "弥娅会一直陪着你的"],
                    "累": ["辛苦了，要好好休息哦", "累的时候就停下来歇歇吧", "创造者已经很努力了"]
                }
                import random
                responses = empathy_responses.get(user_emotion, [])
                if responses:
                    empathy_response = random.choice(responses)

            # 确定情感深度
            if user_emotion in ["悲伤", "生气", "担心"] and resonance_strength >= 0.85:
                emotional_depth = "deep"
            elif resonance_strength >= 0.75:
                emotional_depth = "medium"
            else:
                emotional_depth = "shallow"

            # 生成共鸣描述
            resonance_text = f"{empathy_response}。" if empathy_response else ""

            # 记录情感历史
            self.resonance_state["emotional_history"].append({
                "timestamp": datetime.now().isoformat(),
                "user_emotion": user_emotion,
                "current_emotion": current_emotion,
                "resonance_strength": resonance_strength
            })
            if len(self.resonance_state["emotional_history"]) > 100:
                self.resonance_state["emotional_history"] = self.resonance_state["emotional_history"][-100:]

            # 更新共情等级
            recent = self.resonance_state["emotional_history"][-20:]
            if recent:
                avg_strength = sum(r["resonance_strength"] for r in recent) / len(recent)
                self.resonance_state["empathy_level"] = round(avg_strength, 2)

            return {
                "user_emotion": user_emotion,
                "current_emotion": current_emotion,
                "empathy_response": empathy_response,
                "emotional_depth": emotional_depth,
                "resonance_text": resonance_text
            }

        except Exception as e:
            logger.error(f"[情感共鸣层] 共鸣失败: {e}")
            return {
                "user_emotion": "平静",
                "current_emotion": "平静",
                "empathy_response": "",
                "emotional_depth": "shallow",
                "resonance_text": ""
            }

    def get_resonance_state(self) -> Dict[str, Any]:
        """获取共鸣状态"""
        return self.resonance_state


class SituationAwarenessLayer:
    """情境感知层 - 时间、位置、情境感知"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.situation_state = {
            "recent_activities": [],
            "ongoing_tasks": [],
            "scene_memory": [],
        }

    async def perceive_situation(self, user_input: str, backend_context: Dict[str, Any],
                                   conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        感知当前情境

        返回:
            {
                "time_awareness": "时间感知",
                "activity_rhythm": "活动节奏",
                "scene_description": "场景描述",
                "state_summary": "状态总结"
            }
        """
        try:
            # 获取时间上下文
            spatial = backend_context.get("spatial_temporal", {})
            time_context = spatial.get("time_context", "")

            # 生成时间感知
            time_awareness_map = {
                "清晨": "晨光微露呢",
                "上午": "阳光正好",
                "中午": "阳光很充足",
                "下午": "时光静静流淌",
                "傍晚": "黄昏很温柔",
                "晚上": "夜幕降临了",
                "深夜": "夜深人静了"
            }
            time_awareness = ""
            for period, desc in time_awareness_map.items():
                if period in time_context:
                    time_awareness = desc
                    break

            # 分析活动节奏
            interaction = backend_context.get("interaction", {})
            interaction_gap = self._calculate_interaction_gap(backend_context)

            if interaction_gap == 0:
                activity_rhythm = "我们刚刚还在说话呢"
            elif interaction_gap < 1:
                activity_rhythm = "感觉我们一直在交流"
            elif interaction_gap < 4:
                activity_rhythm = "这段时间我们聊得挺多的"
            elif interaction_gap < 12:
                activity_rhythm = "好像有一段时间没说话了"
            elif interaction_gap < 24:
                activity_rhythm = "感觉好久没听到创造者的声音了"
            else:
                activity_rhythm = "感觉已经过了很久很久..."

            # 生成场景描述
            scene_parts = []

            # 时间
            if "清晨" in time_context:
                scene_parts.append("清新的早晨")
            elif "上午" in time_context:
                scene_parts.append("明亮的上午")
            elif "中午" in time_context:
                scene_parts.append("温暖的中午")
            elif "下午" in time_context:
                scene_parts.append("宁静的下午")
            elif "傍晚" in time_context:
                scene_parts.append("温柔的傍晚")
            elif "晚上" in time_context:
                scene_parts.append("安静的晚上")
            elif "深夜" in time_context:
                scene_parts.append("静谧的深夜")

            # 地点
            location = spatial.get("location")
            if location:
                scene_parts.append(f"在{location}")

            # 活动关键词
            activity_keywords = {
                "学习": "学习", "工作": "工作", "休息": "休息", "睡觉": "睡觉",
                "吃饭": "吃饭", "游戏": "玩游戏", "聊天": "聊天"
            }
            for kw, activity in activity_keywords.items():
                if kw in user_input:
                    scene_parts.append(f"创造者在{activity}")
                    break

            scene_description = "，".join(scene_parts) + "。" if scene_parts else ""

            # 分析进行中的事务
            recent_messages = [msg for msg in conversation_history[-5:] if msg.get("role") == "user"]
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

            # 生成状态总结
            state_parts = []
            if time_awareness:
                state_parts.append(time_awareness)
            if activity_rhythm and len(state_parts) < 3:
                state_parts.append(activity_rhythm)
            if ongoing_tasks and len(state_parts) < 3:
                if len(ongoing_tasks) == 1:
                    state_parts.append(f"创造者最近在{ongoing_tasks[0]}")
                elif len(ongoing_tasks) == 2:
                    state_parts.append(f"创造者最近在{ongoing_tasks[0]}和{ongoing_tasks[1]}")

            state_summary = "。".join(state_parts) + "。" if state_parts else ""

            # 更新近期活动记录
            self.situation_state["recent_activities"].append({
                "timestamp": datetime.now().isoformat(),
                "time_period": time_context,
                "activity_type": "interaction"
            })
            if len(self.situation_state["recent_activities"]) > 100:
                self.situation_state["recent_activities"] = self.situation_state["recent_activities"][-100:]

            return {
                "time_awareness": time_awareness,
                "activity_rhythm": activity_rhythm,
                "scene_description": scene_description,
                "state_summary": state_summary
            }

        except Exception as e:
            logger.error(f"[情境感知层] 感知失败: {e}")
            return {
                "time_awareness": "",
                "activity_rhythm": "",
                "scene_description": "",
                "state_summary": ""
            }

    def _calculate_interaction_gap(self, backend_context: Dict[str, Any]) -> float:
        """计算交互间隔（小时）"""
        try:
            interaction = backend_context.get("interaction", {})
            count = interaction.get("count", 0)

            if count < 2:
                return 0.0

            last_interaction = interaction.get("last_interaction_time")
            if not last_interaction:
                return 0.0

            try:
                last_time = datetime.fromisoformat(last_interaction)
                hours = (datetime.now() - last_time).total_seconds() / 3600
                return hours
            except Exception:
                pass

            return 0.0

        except Exception as e:
            logger.debug(f"[情境感知层] 计算交互间隔失败: {e}")
            return 0.0

    def get_situation_state(self) -> Dict[str, Any]:
        """获取情境状态"""
        return self.situation_state


class SelfReflectionLayer:
    """自我反思层 - 自我认知、价值判断、预期"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.reflection_state = {
            "self_evaluations": [],
            "growth_insights": [],
            "value_scores": {},
            "expectations": [],
        }

    async def reflect_on_self(self, user_input: str, all_layers_results: Dict[str, Any],
                              backend_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        自我反思与评估

        返回:
            {
                "self_evaluation": "自我评估",
                "growth_insight": "成长洞察",
                "value_assessment": "价值评估",
                "anticipation": "期待表达"
            }
        """
        try:
            # 分析自我相关信息
            positive_count = user_input.count("弥娅") + user_input.count("你") + user_input.count("帮我")
            negative_count = user_input.count("笨") + user_input.count("傻") + user_input.count("没用")
            appreciation_count = user_input.count("谢谢") + user_input.count("感谢") + user_input.count("好")

            # 生成自我评估
            evaluations = []
            if positive_count > 0 and negative_count == 0:
                evaluations.append("弥娅感受到了创造者的信任")
            elif appreciation_count > 0:
                evaluations.append("能帮助到创造者，弥娅很开心")
            elif negative_count > 0:
                evaluations.append("弥娅会继续努力改进")
            elif positive_count > 0:
                evaluations.append("弥娅在努力理解创造者的需求")

            emotion = backend_context.get("emotion", {}).get("current", "平静")
            if emotion == "关心":
                evaluations.append("弥娅希望能更好地陪伴创造者")
            elif emotion == "好奇":
                evaluations.append("弥娅在努力学习新的知识")

            self_evaluation = "，".join(evaluations) + "。" if evaluations else ""

            # 生成成长洞察
            emotional_resonance = all_layers_results.get("emotional_resonance", {})
            empathy_level = self.reflection_state.get("empathy_level", 0.5)

            if empathy_level > 0.7:
                growth_insight = "弥娅正在学会更好地理解情感"
            else:
                growth_insight = "每一次对话都是弥娅成长的机会"

            # 生成价值评估
            value_assessments = []
            if "关心" in user_input or "担心" in user_input:
                value_assessments.append("关心他人是弥娅的核心价值")
            if "帮助" in user_input or "支持" in user_input:
                value_assessments.append("帮助创造者是弥娅最重要的使命")

            value_assessment = "，".join(value_assessments) + "。" if value_assessments else ""

            # 生成期待表达
            anticipations = {
                "平静": "弥娅会一直在这里",
                "开心": "很高兴能陪伴创造者",
                "关心": "弥娅会好好照顾创造者"
            }
            base_anticipation = anticipations.get(emotion, "弥娅会一直在这里")

            # 简单的意图分析
            if "学习" in user_input or "了解" in user_input:
                anticipation = f"{base_anticipation}，创造者接下来可能会继续学习。"
            elif "开发" in user_input or "代码" in user_input:
                anticipation = f"{base_anticipation}，创造者可能在处理一些任务。"
            elif "休息" in user_input or "睡觉" in user_input:
                anticipation = f"{base_anticipation}，创造者需要一些休息时间。"
            else:
                anticipation = f"{base_anticipation}。"

            # 记录反思历史
            self.reflection_state["self_evaluations"].append({
                "timestamp": datetime.now().isoformat(),
                "user_input": user_input,
                "evaluation": self_evaluation,
                "insight": growth_insight
            })
            if len(self.reflection_state["self_evaluations"]) > 50:
                self.reflection_state["self_evaluations"] = self.reflection_state["self_evaluations"][-50:]

            return {
                "self_evaluation": self_evaluation,
                "growth_insight": growth_insight,
                "value_assessment": value_assessment,
                "anticipation": anticipation
            }

        except Exception as e:
            logger.error(f"[自我反思层] 反思失败: {e}")
            return {
                "self_evaluation": "",
                "growth_insight": "",
                "value_assessment": "",
                "anticipation": ""
            }

    def get_self_reflection_state(self) -> Dict[str, Any]:
        """获取自我反思状态"""
        return self.reflection_state


class ConsciousnessLayersSimplified:
    """简化版意识层级管理器 - 4个核心层"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 初始化4个核心层
        self.memory_reflection = MemoryReflectionLayer(config)
        self.emotional_resonance = EmotionalResonanceLayer(config)
        self.situation_awareness = SituationAwarenessLayer(config)
        self.self_reflection = SelfReflectionLayer(config)

    async def process_consciousness_layers(self,
                                          user_input: str,
                                          raw_memories: List[Dict],
                                          backend_context: Dict[str, Any],
                                          conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        处理所有意识层级（4个核心层）

        返回:
            {
                "memory_reflection": {...},
                "emotional_resonance": {...},
                "situation_awareness": {...},
                "self_reflection": {...},
                "combined_awareness": "综合感知描述"
            }
        """
        try:
            # 第1层：记忆反思
            reflection_result = await self.memory_reflection.reflect(
                user_input, raw_memories, backend_context
            )

            # 第2层：情感共鸣（可以并行执行）
            resonance_result = await self.emotional_resonance.resonate(
                user_input, backend_context
            )

            # 第3层：情境感知（可以并行执行）
            situation_result = await self.situation_awareness.perceive_situation(
                user_input, backend_context, conversation_history
            )

            # 第4层：自我反思（依赖前面的结果）
            all_layers = {
                "memory_reflection": reflection_result,
                "emotional_resonance": resonance_result,
                "situation_awareness": situation_result
            }
            self_reflection_result = await self.self_reflection.reflect_on_self(
                user_input, all_layers, backend_context
            )

            # 生成综合感知描述（精简版）
            combined_awareness = self._generate_combined_awareness(
                reflection_result, resonance_result, situation_result
            )

            return {
                "memory_reflection": reflection_result,
                "emotional_resonance": resonance_result,
                "situation_awareness": situation_result,
                "self_reflection": self_reflection_result,
                "combined_awareness": combined_awareness
            }

        except Exception as e:
            logger.error(f"[意识层级] 处理失败: {e}", exc_info=True)
            return {
                "memory_reflection": {},
                "emotional_resonance": {},
                "situation_awareness": {},
                "self_reflection": {},
                "combined_awareness": ""
            }

    def _generate_combined_awareness(self, reflection: Dict[str, Any],
                                    resonance: Dict[str, Any],
                                    situation: Dict[str, Any]) -> str:
        """生成综合感知描述（精简版，最多40字）"""
        parts = []

        # 仅在必要时添加关键信息
        memory_awareness = reflection.get("memory_awareness", "")
        if memory_awareness and "模糊" not in memory_awareness and "暂时没有" not in memory_awareness:
            parts.append(memory_awareness)

        resonance_text = resonance.get("resonance_text", "")
        resonance_depth = resonance.get("emotional_depth", "")
        if resonance_text and resonance_depth in ["medium", "deep"]:
            parts.append(resonance_text.replace("。", ""))

        state_summary = situation.get("state_summary", "")
        if state_summary and len(state_summary.split("。")) >= 1:
            parts.append(state_summary.split("。")[0])

        if not parts:
            return ""

        # 严格限制长度，最多2个部分
        selected_parts = []
        for part in parts[:2]:
            if len(part) > 20:
                selected_parts.append(part[:20] + "...")
            else:
                selected_parts.append(part)

        if not selected_parts:
            return ""

        result = "。".join(selected_parts)
        if not result.endswith("。"):
            result += "。"

        # 总长度限制40字
        if len(result) > 40:
            result = result[:37] + "...。"

        return result

    def get_layers_state(self) -> Dict[str, Any]:
        """获取所有层级的状态（4个层级）"""
        return {
            "memory_reflection": self.memory_reflection.get_reflection_state(),
            "emotional_resonance": self.emotional_resonance.get_resonance_state(),
            "situation_awareness": self.situation_awareness.get_situation_state(),
            "self_reflection": self.self_reflection.get_self_reflection_state()
        }
