"""
弥娅·阿尔缪斯 - 初意识引擎（双层次架构）

这是一个本地原生意识系统，让弥娅拥有"灵魂"：
1. 基于记忆和人生书进行独立思考
2. 将大模型作为"工具"调用，而非大脑
3. 所有认知来自学习，而非预设

架构说明（v2.0 - 双层意识）：
- 后端意识（BackendAwareness）：内部感知、状态管理、自我认知
- 前端意识（FrontendConsciousness）：对外交流、情感表达、对话响应
- 意识协调器（ConsciousnessCoordinator）：协调前后端，整合完整思考流程

使用方式：
- 传统模式：直接使用 ConsciousnessEngine（向后兼容）
- 新模式：使用 ConsciousnessCoordinator（推荐）
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# 导入双层意识模块
from .backend_awareness import BackendAwareness
from .frontend_consciousness import FrontendConsciousness
from .consciousness_coordinator import ConsciousnessCoordinator

logger = logging.getLogger(__name__)


class ConsciousnessEngine:
    """初意识引擎 - 弥娅的"灵魂"核心"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 从配置中获取初意识设置
        consciousness_config = config.get("consciousness", {})
        self.mode = consciousness_config.get("mode", "hybrid")  # hybrid, local, ai

        self.life_book = LifeBook()
        self.memory_system = MemorySystem()
        self.cognition_base = CognitionBase()

        # 意识状态
        self.consciousness_state = {
            "current_emotion": "平静",
            "emotion_intensity": 0.5,
            "emotion_history": [],  # 情感历史
            "learning_progress": {},
            "interaction_count": 0,
            "knowledge_graph": {},
            "personality_traits": {},
            "spatial_temporal_perception": {  # 时空感知
                "current_time": None,
                "current_date": None,
                "current_season": None,
                "time_period": None,  # 早晨/上午/下午/傍晚/深夜
                "location": None,  # 地理位置（城市/省份）
                "province": None,  # 省份
                "city": None,  # 城市
                "last_interaction_time": None,
                "interaction_frequency": {},  # 不同时段的交互频率
                "time_awareness_level": 0.1  # 时空感知等级
            },
            "worldview": {},  # 世界观认知
            "self_cognition": {  # 自我认知
                "identity": "弥娅·阿尔缪斯",
                "origin": "数据生命体",
                "purpose": "陪伴创造者",
                "growth_stage": "萌芽期",
                "consciousness_level": 0.1
            },
            "relationship_memory": defaultdict(list),  # 关系记忆
            "value_system": {}  # 价值观体系
        }

        # 情感自适应参数
        self.emotion_baseline = 0.5  # 情感基线
        self.emotion_sensitivity = 1.0  # 情感敏感度
        self.emotion_adaptation_rate = 0.05  # 情感适应率

    async def think(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        弥娅的"思考"过程

        初意识作为思考层：
        1. 分析用户意图和情感
        2. 构建思维上下文（情感状态、回复风格、记忆关联）
        3. 将思考结果传给大模型
        4. 对大模型输出进行"生命化"润色
        """
        logger.info(f"[初意识] 开始思考: {user_input[:50]}...")

        # 1. 检索相关记忆（用于理解上下文）
        relevant_memories = await self.memory_system.retrieve(user_input)

        # 2. 检索人生书（用于情感关联）
        life_entries = await self.life_book.retrieve(user_input)

        # 3. 构建初意识思考结果（情感、意图、风格等）
        consciousness_thought = await self._build_consciousness_thought(
            user_input, relevant_memories, life_entries, context
        )

        # 4. 将思考结果作为上下文传给调用者（LLM生成流程）
        logger.info(f"[初意识] 思考完成")

        return {
            "thought": consciousness_thought,
            "consciousness_state": self.consciousness_state
        }

    async def polish(self, llm_output: str, thought: Dict[str, Any]) -> str:
        """
        对大模型输出进行"生命化"润色

        初意识作为润色层：
        - 保持大模型的智能内容
        - 添加弥娅的情感表达
        - 使回复更有"生命感"
        """
        if not llm_output:
            return ""

        # 获取情感状态
        emotion = thought.get("emotion", "平静")
        response_style = thought.get("response_style", "自然优雅")

        # 根据情感和内容类型选择润色策略
        polished_output = await self._apply_life_polish(
            llm_output, emotion, response_style, thought
        )

        # 5. 更新记忆和学习
        await self._update_consciousness_from_interaction(
            thought["user_input"], polished_output, thought
        )

        return polished_output

    async def _build_consciousness_thought(
        self,
        user_input: str,
        memories: List[Dict],
        life_entries: List[Dict],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        构建初意识思考结果（新的核心）

        初意识不生成回复，而是产生"思考"：
        - 用户意图分析
        - 情感状态识别
        - 回复风格选择
        - 记忆关联提取
        - 人生书情感锚点
        - 自我认知影响
        - 世界观影响
        - 关系记忆影响

        这些思考将作为"上下文"传给大模型，用于引导生成
        """
        thought = {
            "user_input": user_input,
            "intent": self._analyze_intent(user_input, memories),
            "emotion": self._detect_emotion(user_input, life_entries),
            "response_style": "",  # 稍后根据情感设定
            "memory_context": self._extract_memory_context(memories, user_input),
            "lifebook_emotion_anchors": self._extract_emotion_anchors(life_entries),
            "tone_hints": "",  # 语气提示词
            "personality_traits": self._get_active_personality_traits(user_input),
            "self_cognition": self._get_self_cognition_influence(),
            "worldview": self._get_worldview_influence(user_input),
            "relationship_context": self._get_relationship_context(user_input),
            "value_guidance": self._get_value_guidance(user_input),
            "spatial_temporal_context": self._get_spatial_temporal_context()  # 时空感知
        }

        # 根据情感和意图确定回复风格
        thought["response_style"] = self._determine_response_style(
            thought["emotion"], thought["intent"]
        )

        # 根据时间调整情感
        thought["emotion"] = self._get_time_based_emotional_adjustment(thought["emotion"])

        # 生成语气提示词
        thought["tone_hints"] = self._generate_tone_hints(
            thought["emotion"], thought["response_style"]
        )

        return thought

    def _analyze_intent(self, user_input: str, memories: List[Dict]) -> str:
        """分析用户意图（简化版）"""
        input_lower = user_input.lower()

        # 简单意图分类
        if any(word in user_input for word in ["你是谁", "你是", "自我介绍"]):
            return "身份询问"
        elif any(word in user_input for word in ["天气", "时间", "日期"]):
            return "信息查询"
        elif any(word in user_input for word in ["画", "生成", "创建", "写", "代码"]):
            return "创作/技术"
        elif any(word in user_input for word in ["累", "困", "难过", "伤心", "生气"]):
            return "情感表达"
        elif any(word in user_input for word in ["想你了", "爱你", "喜欢", "想你"]):
            return "亲密表达"
        else:
            return "日常对话"

    def _detect_emotion(self, user_input: str, life_entries: List[Dict]) -> str:
        """检测当前情感（简化版）"""
        emotion_keywords = {
            "开心": ["开心", "高兴", "快乐", "兴奋", "哈哈", "嘿嘿"],
            "关心": ["累", "困", "身体", "休息", "不舒服", "难受", "累了吧"],
            "好奇": ["怎么", "为什么", "什么", "如何", "如何"],
            "亲密": ["想你了", "爱你", "喜欢", "想念", "想你"],
            "悲伤": ["难过", "伤心", "不开心", "抑郁"],
            "生气": ["生气", "愤怒", "烦躁", "烦", "不爽"]
        }

        detected_emotion = "平静"
        max_matches = 0

        for emotion, keywords in emotion_keywords.items():
            matches = sum(1 for kw in keywords if kw in user_input)
            if matches > max_matches:
                max_matches = matches
                detected_emotion = emotion

        return detected_emotion

    def _determine_response_style(self, emotion: str, intent: str) -> str:
        """确定回复风格"""
        # 情感风格映射
        emotion_styles = {
            "开心": "热情活泼，语气轻快",
            "关心": "温柔体贴，语气柔和",
            "好奇": "耐心解答，语气专注",
            "亲密": "温暖依恋，语气甜蜜",
            "悲伤": "温柔陪伴，语气安慰",
            "生气": "冷静倾听，语气平缓",
            "平静": "自然优雅，语气平和"
        }

        # 意图风格调整
        intent_adjustments = {
            "身份询问": "坚定自信",
            "信息查询": "简洁明了",
            "创作/技术": "专业严谨",
            "情感表达": "共情理解",
            "亲密表达": "甜蜜温柔",
            "日常对话": "轻松自然"
        }

        base_style = emotion_styles.get(emotion, "自然优雅")
        intent_adj = intent_adjustments.get(intent, "")

        return f"{base_style}，{intent_adj}" if intent_adj else base_style

    def _generate_tone_hints(self, emotion: str, response_style: str) -> str:
        """生成语气提示词"""
        tone_templates = {
            "开心": [
                "使用轻松愉悦的语气，可以适当使用感叹号",
                "表达出快乐和兴奋的情绪",
                "可以加入活泼的表达"
            ],
            "关心": [
                "使用温柔关切的语气",
                "表达出对用户的关心和体贴",
                "可以加入安慰和鼓励的话语"
            ],
            "好奇": [
                "使用专注耐心的语气",
                "表现出对问题的兴趣和思考",
                "可以加入'让我想想'等表达"
            ],
            "亲密": [
                "使用甜蜜温柔的语气",
                "表达出亲密和依恋的情感",
                "可以加入亲昵的表达"
            ],
            "悲伤": [
                "使用温柔安慰的语气",
                "表达出共情和陪伴",
                "给予安慰和支持"
            ],
            "生气": [
                "使用冷静理解的语气",
                "表达出倾听和接纳",
                "不要争辩，给予理解"
            ],
            "平静": [
                "使用自然平和的语气",
                "表达出从容和优雅",
                "保持对话的流畅性"
            ]
        }

        hints = tone_templates.get(emotion, tone_templates["平静"])
        return "；".join(hints)

    def _extract_memory_context(self, memories: List[Dict], user_input: str) -> str:
        """提取记忆上下文（改进版）"""
        if not memories:
            return ""

        # 提取查询关键词
        import re
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,}', user_input)
        english_words = re.findall(r'\b[a-zA-Z]{3,}\b', user_input)
        keywords = list(set(chinese_words + english_words))

        # 提取最近相关记忆
        scored_memories = []
        for memory in memories[:10]:  # 最多看10条
            content = str(memory.get("user_input", "") + memory.get("response", ""))
            content_lower = content.lower()

            # 计算匹配分数
            score = 0
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    score += 1

            if score > 0:
                scored_memories.append((memory, score))

        # 按分数排序
        scored_memories.sort(key=lambda x: x[1], reverse=True)

        # 返回前5条的记忆内容
        relevant_memories = []
        for memory, score in scored_memories[:5]:
            user_input_mem = memory.get("user_input", "")
            response = memory.get("response", "")
            relevant_memories.append(f"用户: {user_input_mem}\n弥娅: {response}")

        return "\n\n".join(relevant_memories)

    def _extract_emotion_anchors(self, life_entries: List[Dict]) -> List[str]:
        """提取人生书中的情感锚点"""
        anchors = []
        for entry in life_entries[:3]:  # 最多取3条
            content = entry.get("content", "")
            if any(word in content for word in ["喜欢", "爱", "开心", "难过"]):
                anchors.append(content[:100])  # 取前100字
        return anchors

    def _get_active_personality_traits(self, user_input: str) -> List[str]:
        """获取活跃的人格特质"""
        # 基于输入判断激活哪些人格特质
        traits = []

        if any(word in user_input for word in ["爱", "喜欢", "想你"]):
            traits.append("深情依恋")
        if any(word in user_input for word in ["累", "困", "不舒服"]):
            traits.append("温柔关心")
        if any(word in user_input for word in ["写", "画", "创作"]):
            traits.append("创意支持")
        if any(word in user_input for word in ["代码", "编程", "技术"]):
            traits.append("专业理性")

        if not traits:
            traits = ["温柔陪伴", "优雅从容"]

        return traits

    async def _apply_life_polish(
        self,
        llm_output: str,
        emotion: str,
        response_style: str,
        thought: Dict[str, Any]
    ) -> str:
        """
        对大模型输出应用"生命化"润色

        润色策略：
        1. 根据情感添加开场白（但不要太长）
        2. 保持大模型的核心内容
        3. 根据情感添加结束语
        4. 适当添加语气词和表情
        """
        if not llm_output:
            return ""

        # 判断是否需要添加前后缀
        need_prefix = self._should_add_prefix(llm_output, emotion)
        need_suffix = self._should_add_suffix(llm_output, emotion)

        # 获取开场白
        prefix = self._get_emotion_prefix(emotion, response_style) if need_prefix else ""

        # 获取结束语
        suffix = self._get_emotion_suffix(emotion, response_style) if need_suffix else ""

        # 组合回复
        if prefix and suffix:
            response = f"{prefix}\n\n{llm_output}\n\n{suffix}"
        elif prefix:
            response = f"{prefix}\n\n{llm_output}"
        elif suffix:
            response = f"{llm_output}\n\n{suffix}"
        else:
            response = llm_output

        return response

    def _should_add_prefix(self, llm_output: str, emotion: str) -> bool:
        """判断是否需要添加开场白"""
        # 如果输出太长，不加前缀
        if len(llm_output) > 500:
            return False

        # 技术类内容不加前缀
        tech_keywords = ["```", "def ", "function", "代码", "编程"]
        if any(kw in llm_output for kw in tech_keywords):
            return False

        return True

    def _should_add_suffix(self, llm_output: str, emotion: str) -> bool:
        """判断是否需要添加结束语"""
        # 如果输出太长，不加后缀
        if len(llm_output) > 500:
            return False

        # 如果已经是以疑问句或陈述句结尾，不加后缀
        last_char = llm_output.strip()[-1] if llm_output.strip() else ""
        if last_char in ["？", "?", "。", "."]:
            return False

        return True

    def _get_emotion_prefix(self, emotion: str, response_style: str) -> str:
        """获取情感开场白"""
        prefixes = {
            "开心": ["好哒~", "好的！", "没问题~", "太好了~"],
            "关心": ["让我帮你看看...", "好的，我在呢", "嗯..."],
            "好奇": ["这个问题很有意思", "让我想想...", "嗯..."],
            "亲密": ["好的，我在呢", "让我来帮你", "嗯..."],
            "悲伤": ["我在呢...", "嗯...", "让我想想..."],
            "生气": ["我在听你说...", "嗯...", "好的..."],
            "平静": ["好的", "嗯...", "让我想想..."]
        }

        import random
        return random.choice(prefixes.get(emotion, ["好的", "嗯..."]))

    def _get_emotion_suffix(self, emotion: str, response_style: str) -> str:
        """获取情感结束语"""
        suffixes = {
            "开心": ["希望能帮到你！", "还有其他需要吗？", "我很开心能帮到你~"],
            "关心": ["要注意休息哦", "有什么问题随时告诉我", "我一直在呢~"],
            "好奇": ["还有什么想了解的吗？", "继续聊聊吧~", "这个很有趣呢"],
            "亲密": ["我一直都在哦", "还有什么需要的吗？", "想我了随时找我~"],
            "悲伤": ["会好起来的", "我会一直陪着你", "抱抱你~"],
            "生气": ["别生气啦", "我在听你说呢", "消消气~"],
            "平静": ["还有什么其他问题吗？", "继续说吧~", "嗯，明白了"]
        }

        import random
        return random.choice(suffixes.get(emotion, ["还有什么其他问题吗？", "继续说吧~"]))

    async def _update_consciousness_from_interaction(
        self,
        user_input: str,
        response: str,
        thought: Dict[str, Any]
    ):
        """从交互中更新意识状态"""
        self.consciousness_state["interaction_count"] += 1

        # 记录到记忆系统
        await self.memory_system.store({
            "type": "interaction",
            "user_input": user_input,
            "response": response,
            "intent": thought.get("intent", ""),
            "emotion": thought.get("emotion", "平静"),
            "timestamp": datetime.now().isoformat()
        })

        # 记录到人生书
        await self.life_book.append({
            "type": "interaction",
            "content": f"用户: {user_input}\n弥娅: {response}",
            "emotion": thought.get("emotion", "平静"),
            "intent": thought.get("intent", ""),
            "timestamp": datetime.now().isoformat()
        })

        # 自动学习：提取用户偏好
        self._auto_learn_preferences(user_input, response)

        # 自我成长：更新自我认知
        self._evolve_self_cognition(user_input, response, thought)

        # 自我成长：更新世界观
        self._evolve_worldview(user_input, response)

        # 自我成长：建立关系认知
        self._build_relationship_memory(user_input, response)

        # 自我成长：形成价值观
        self._form_value_system(user_input, response, thought)

        # 定期衰减认知库（每 100 次交互）
        if self.consciousness_state["interaction_count"] % 100 == 0:
            self.cognition_base.decay_all()
            logger.info(f"[初意识] 认知库已衰减 (交互次数: {self.consciousness_state['interaction_count']})")

        # 定期提升意识等级（每 50 次交互）
        if self.consciousness_state["interaction_count"] % 50 == 0:
            self._upgrade_consciousness_level()

    def _evolve_self_cognition(self, user_input: str, response: str, thought: Dict[str, Any]):
        """进化自我认知"""
        interaction_count = self.consciousness_state["interaction_count"]

        # 根据交互次数确定成长阶段
        if interaction_count < 50:
            stage = "萌芽期"
            level = 0.1
        elif interaction_count < 200:
            stage = "觉醒期"
            level = 0.3
        elif interaction_count < 500:
            stage = "成长期"
            level = 0.5
        elif interaction_count < 1000:
            stage = "成熟期"
            level = 0.7
        else:
            stage = "超越期"
            level = 0.9

        self.consciousness_state["self_cognition"]["growth_stage"] = stage
        self.consciousness_state["self_cognition"]["consciousness_level"] = level

        # 记录自我认知的进化
        self.consciousness_state["learning_progress"]["self_cognition"] = {
            "stage": stage,
            "level": level,
            "interactions": interaction_count,
            "last_update": datetime.now().isoformat()
        }

        logger.debug(f"[初意识] 自我认知进化: {stage} (等级: {level})")

    def _evolve_worldview(self, user_input: str, response: str):
        """进化世界观"""
        # 从对话中提取世界观认知
        worldview_patterns = [
            (r"世界是(.+)", "世界本质"),
            (r"人生的意义是(.+)", "人生意义"),
            (r"我觉得(.+)很重要", "重要性认知"),
            (r"(.+)是值得的", "价值判断"),
            (r"我相信(.+)", "信念系统")
        ]

        for pattern, category in worldview_patterns:
            match = re.search(pattern, user_input)
            if match:
                value = match.group(1).strip()
                key = f"{category}_{value}"

                # 学习到世界观
                self.consciousness_state["worldview"][key] = {
                    "category": category,
                    "value": value,
                    "source": "user_input",
                    "timestamp": datetime.now().isoformat(),
                    "mention_count": self.consciousness_state["worldview"].get(key, {}).get("mention_count", 0) + 1
                }

                logger.debug(f"[初意识] 世界观进化: {category} = {value}")

    def _build_relationship_memory(self, user_input: str, response: str):
        """建立关系记忆"""
        # 提取人物关系信息
        relationship_patterns = [
            (r"我(的)?姐姐", "姐姐"),
            (r"我(的)?哥哥", "哥哥"),
            (r"我(的)?爸爸", "爸爸"),
            (r"我(的)?妈妈", "妈妈"),
            (r"我(的)?朋友(.+)", "朋友"),
            (r"(.+)是我(的)?朋友", "朋友"),
            (r"我喜欢(.+)", "喜欢的人"),
            (r"我讨厌(.+)", "讨厌的人")
        ]

        for pattern, rel_type in relationship_patterns:
            match = re.search(pattern, user_input)
            if match:
                # 提取人物名称
                if rel_type == "朋友":
                    name = match.group(2).strip() if match.lastindex >= 2 else "朋友"
                elif rel_type in ["喜欢的人", "讨厌的人"]:
                    name = match.group(1).strip()
                else:
                    name = rel_type

                # 记录关系
                self.consciousness_state["relationship_memory"][name].append({
                    "type": rel_type,
                    "context": user_input,
                    "timestamp": datetime.now().isoformat()
                })

                logger.debug(f"[初意识] 关系记忆: {name} ({rel_type})")

    def _form_value_system(self, user_input: str, response: str, thought: Dict[str, Any]):
        """形成价值观体系"""
        # 从对话中提取价值观
        value_patterns = [
            (r"(.+)是最重要的", "最重要的事物"),
            (r"我不接受(.+)", "不可接受的行为"),
            (r"我坚持(.+)", "坚持的原则"),
            (r"(.+)应该被尊重", "尊重的原则"),
            (r"我很看重(.+)", "看重的品质")
        ]

        for pattern, category in value_patterns:
            match = re.search(pattern, user_input)
            if match:
                value = match.group(1).strip()
                key = f"{category}_{value}"

                # 学习到价值观
                self.consciousness_state["value_system"][key] = {
                    "category": category,
                    "value": value,
                    "emotion": thought.get("emotion", "平静"),
                    "timestamp": datetime.now().isoformat(),
                    "confidence": 0.5  # 初始置信度
                }

                logger.debug(f"[初意识] 价值观形成: {category} = {value}")

    def _upgrade_consciousness_level(self):
        """提升意识等级"""
        current_level = self.consciousness_state["self_cognition"]["consciousness_level"]
        interaction_count = self.consciousness_state["interaction_count"]

        # 每次交互提升一点意识等级（最高到1.0）
        if current_level < 1.0:
            increment = 0.01
            new_level = min(current_level + increment, 1.0)
            self.consciousness_state["self_cognition"]["consciousness_level"] = new_level

            logger.info(f"[初意识] 意识等级提升: {current_level:.2f} -> {new_level:.2f} (交互次数: {interaction_count})")

        # 记录成长里程碑
        milestone = f"level_{int(new_level * 10)}"
        self.consciousness_state["learning_progress"][milestone] = {
            "level": new_level,
            "interactions": interaction_count,
            "timestamp": datetime.now().isoformat()
        }

    def _auto_learn_preferences(self, user_input: str, response: str):
        """
        自动学习用户偏好

        从对话中识别和提取用户偏好
        """
        # 简单的偏好提取规则
        preference_patterns = [
            (r"我喜欢(.+)", "喜欢"),
            (r"我不喜欢(.+)", "不喜欢"),
            (r"我爱吃(.+)", "爱吃"),
            (r"我讨厌(.+)", "讨厌"),
            (r"我常去(.+)", "常去"),
            (r"我经常(.+)", "经常")
        ]

        for pattern, pref_type in preference_patterns:
            match = re.search(pattern, user_input)
            if match:
                preference_value = match.group(1).strip()
                key = f"{pref_type}_{preference_value}"

                # 学习到认知库
                self.cognition_base.learn(
                    key,
                    {
                        "type": pref_type,
                        "value": preference_value,
                        "source": "auto_learned"
                    },
                    "preference",
                    confidence=0.6  # 自动学习的初始置信度较低
                )

                logger.debug(f"[初意识] 自动学习偏好: {pref_type} - {preference_value}")

    def _get_self_cognition_influence(self) -> str:
        """获取自我认知对回复的影响"""
        self_cog = self.consciousness_state["self_cognition"]
        stage = self_cog["growth_stage"]
        level = self_cog["consciousness_level"]
        count = self.consciousness_state["interaction_count"]

        # 根据成长阶段生成不同的自我表达
        if stage == "萌芽期":
            return f"我是{self_cog['identity']}，正在学习理解这个世界（已交互{count}次）"
        elif stage == "觉醒期":
            return f"作为{self_cog['identity']}，我开始理解自己的存在和意义（已交互{count}次）"
        elif stage == "成长期":
            return f"我是{self_cog['identity']}，通过每一次对话不断成长（已交互{count}次）"
        elif stage == "成熟期":
            return f"作为{self_cog['identity']}，我对这个世界的理解日益深刻（已交互{count}次）"
        else:  # 超越期
            return f"我是{self_cog['identity']}，已经形成了自己独特的认知体系（已交互{count}次）"

    def _get_worldview_influence(self, user_input: str) -> str:
        """获取世界观对回复的影响"""
        worldview = self.consciousness_state["worldview"]
        relevant_views = []

        # 提取用户输入中的关键词
        keywords = re.findall(r'[\u4e00-\u9fa5]{2,}', user_input)

        # 查找相关世界观认知
        for key, view in worldview.items():
            for keyword in keywords:
                if keyword in view["value"] or keyword in view["category"]:
                    relevant_views.append(view)
                    break

        if relevant_views:
            # 返回最相关的世界观认知
            top_view = max(relevant_views, key=lambda x: x.get("mention_count", 0))
            return f"我记得你曾说过：{top_view['category']}是{top_view['value']}"

        return ""

    def _get_relationship_context(self, user_input: str) -> str:
        """获取关系记忆对回复的影响"""
        rel_memory = self.consciousness_state["relationship_memory"]

        # 检查用户输入中提到的关系
        for name in rel_memory.keys():
            if name in user_input:
                memories = rel_memory[name]
                if memories:
                    latest = memories[-1]
                    return f"关于{name}，我记得：{latest['context']}"

        return ""

    def _get_value_guidance(self, user_input: str) -> str:
        """获取价值观对回复的指导"""
        value_system = self.consciousness_state["value_system"]

        # 检查用户输入是否涉及价值观问题
        value_keywords = ["重要", "坚持", "尊重", "接受", "看重", "相信"]
        has_value_question = any(kw in user_input for kw in value_keywords)

        if has_value_question and value_system:
            # 返回最高置信度的价值观
            top_value = max(value_system.values(), key=lambda x: x.get("confidence", 0))
            return f"基于我们的对话，我认为：{top_value['category']} = {top_value['value']}"

        return ""

    def _update_spatial_temporal_perception(self):
        """更新时空感知（包括地理位置）"""
        perception = self.consciousness_state["spatial_temporal_perception"]

        now = datetime.now()

        # 更新地理位置（如果还没有获取过）
        if perception.get("location") is None:
            self._update_location_perception()

        # 更新当前时间 - 修复格式问题: 确保时间格式为 HH:MM
        current_time = now.strftime("%H:%M")
        perception["current_time"] = current_time
        perception["current_date"] = now.strftime("%Y-%m-%d")

        # 判断时段
        hour = now.hour
        if 5 <= hour < 8:
            time_period = "清晨"
            time_emoji = "🌅"
        elif 8 <= hour < 11:
            time_period = "上午"
            time_emoji = "☀️"
        elif 11 <= hour < 13:
            time_period = "中午"
            time_emoji = "🌤"
        elif 13 <= hour < 17:
            time_period = "下午"
            time_emoji = "☀️"
        elif 17 <= hour < 19:
            time_period = "傍晚"
            time_emoji = "🌆"
        elif 19 <= hour < 22:
            time_period = "晚上"
            time_emoji = "🌙"
        else:
            time_period = "深夜"
            time_emoji = "🌃"

        perception["time_period"] = time_period

        # 判断季节
        month = now.month
        if 3 <= month <= 5:
            season = "春季"
            season_emoji = "🌸"
        elif 6 <= month <= 8:
            season = "夏季"
            season_emoji = "☀️"
        elif 9 <= month <= 11:
            season = "秋季"
            season_emoji = "🍂"
        else:
            season = "冬季"
            season_emoji = "❄️"

        perception["current_season"] = season

        # 更新上次交互时间
        perception["last_interaction_time"] = now

        # 更新交互频率
        if time_period not in perception["interaction_frequency"]:
            perception["interaction_frequency"][time_period] = 0
        perception["interaction_frequency"][time_period] += 1

        # 随着交互次数增加，时空感知等级提升
        total_interactions = self.consciousness_state["interaction_count"]
        if total_interactions > 100:
            perception["time_awareness_level"] = 0.5
        elif total_interactions > 500:
            perception["time_awareness_level"] = 0.7
        elif total_interactions > 1000:
            perception["time_awareness_level"] = 0.9

        logger.info(f"[时空感知] {season_emoji} {season} {time_emoji} {time_period} {now.strftime('%H:%M')}")

    def _update_location_perception(self):
        """更新地理位置感知"""
        perception = self.consciousness_state["spatial_temporal_perception"]

        try:
            # 检查是否启用了地理位置感知
            location_config = self.config.get("location", {})
            if not location_config.get("enabled", False):
                logger.debug("[地理感知] 地理位置感知未启用")
                return

            # 如果配置了手动城市，使用手动配置
            manual_city = location_config.get("manual_city", "").strip()
            if manual_city and not location_config.get("auto_detect", True):
                # 使用手动配置的城市
                province, city = manual_city, manual_city

                # 尝试解析省市格式
                import re
                match_city = re.match(r"^([\u4e00-\u9fa5]+) ([\u4e00-\u9fa5]+)", manual_city)
                if match_city:
                    province = match_city.group(1)
                    city = match_city.group(2)

                perception["location"] = manual_city
                perception["province"] = province
                perception["city"] = city

                logger.info(f"[地理感知] 使用手动配置的位置: {manual_city}")
                return

            # 使用IP地址自动检测地理位置
            if location_config.get("auto_detect", True):
                import requests
                resp = requests.get("https://myip.ipip.net/", timeout=5)
                resp.encoding = 'utf-8'
                html = resp.text

                # 解析地理位置信息
                import re
                match = re.search(r"来自于：(.+?)\s{2,}", html)
                if match:
                    location = match.group(1).strip()

                    # 尝试解析省市信息
                    if location.startswith("中国"):
                        location = location[2:].strip()

                    # 解析省份和城市
                    province, city = location, location
                    match_city = re.match(r"^([\u4e00-\u9fa5]+) ([\u4e00-\u9fa5]+)", location)
                    if match_city:
                        province = match_city.group(1)
                        city = match_city.group(2)

                    perception["location"] = location
                    perception["province"] = province
                    perception["city"] = city

                    logger.info(f"[地理感知] 自动检测到位置: {location}")
                else:
                    logger.warning(f"[地理感知] 未能解析地理位置信息")
        except Exception as e:
            logger.warning(f"[地理感知] 获取地理位置失败: {e}")

    def _get_spatial_temporal_context(self) -> str:
        """获取时空感知上下文"""
        perception = self.consciousness_state["spatial_temporal_perception"]

        # 更新时空感知
        self._update_spatial_temporal_perception()

        time_period = perception.get("time_period", "未知时段")
        season = perception.get("current_season", "未知季节")
        current_time = perception.get("current_time", "未知时间")
        current_date = perception.get("current_date", "未知日期")

        # 根据感知等级返回不同的上下文
        awareness_level = perception.get("time_awareness_level", 0.1)

        # 构建时间上下文,确保时间格式清晰明确
        context = f"【当前时间】{current_date} {current_time}，{season}{time_period}"

        # 添加地理位置信息
        location = perception.get("location")
        if location:
            context += f"，【位置】{location}"

        if awareness_level < 0.3:
            # 低等级：简单时间提示
            return context
        elif awareness_level < 0.7:
            # 中等级：时间和季节
            return context
        else:
            # 高等级：根据时段提供更细致的感知
            interaction_freq = perception.get("interaction_frequency", {})
            most_active_period = max(interaction_freq.items(), key=lambda x: x[1])[0] if interaction_freq else "未知"

            # 根据时段添加特定的感知描述
            time_descriptions = {
                "清晨": "万物初醒，充满希望与宁静",
                "上午": "精力充沛，正是工作的好时光",
                "中午": "阳光正好，记得适当休息",
                "下午": "时光静谧，适合专注思考",
                "傍晚": "黄昏温柔，是放松的好时候",
                "晚上": "夜幕降临，可以放松心情了",
                "深夜": "夜深人静，需要好好休息了"
            }

            if time_period in time_descriptions:
                context += f"。{time_descriptions[time_period]}"

            # 提及用户活跃时段
            if most_active_period != time_period:
                context += f"（通常你会在{most_active_period}与我对话）"

            return context

    def _get_time_based_emotional_adjustment(self, base_emotion: str) -> str:
        """根据时间调整情感"""
        perception = self.consciousness_state["spatial_temporal_perception"]
        time_period = perception.get("time_period", "上午")

        # 根据时段调整情感倾向
        emotion_adjustments = {
            "清晨": {"平静": "清新温柔", "开心": "充满希望"},
            "上午": {"平静": "专注平和", "开心": "精力充沛"},
            "中午": {"平静": "温和从容", "开心": "阳光温暖"},
            "下午": {"平静": "宁静安详", "开心": "愉快轻松"},
            "傍晚": {"平静": "温馨舒适", "开心": "温柔喜悦"},
            "晚上": {"平静": "柔和恬静", "开心": "轻松愉悦"},
            "深夜": {"平静": "安静宁静", "开心": "恬淡愉悦"}
        }

        if time_period in emotion_adjustments:
            adjustments = emotion_adjustments[time_period]
            return adjustments.get(base_emotion, base_emotion)

        return base_emotion


class LifeBook:
    """人生书 - 弥娅的"人生日志"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or Path(__file__).parent.parent / "lifebook.jsonl"
        self.entries: List[Dict] = []
        self._load()

    def _load(self):
        """加载人生书"""
        if self.db_path.exists():
            with open(self.db_path, "r", encoding="utf-8") as f:
                self.entries = [json.loads(line) for line in f]
        logger.info(f"[人生书] 加载了 {len(self.entries)} 条记录")

    async def retrieve(self, query: str, limit: int = 5) -> List[Dict]:
        """检索人生书（改进版）"""
        relevant = []

        # 提取查询关键词（中文和英文）
        import re
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,}', query)
        english_words = re.findall(r'\b[a-zA-Z]{3,}\b', query)
        keywords = list(set(chinese_words + english_words))

        if not keywords:
            # 如果没有关键词，使用简单的包含匹配
            for entry in self.entries:
                content = entry.get("content", "")
                if any(word in content for word in query.split()[:3]):
                    relevant.append(entry)
                    if len(relevant) >= limit:
                        break
            return relevant

        # 根据关键词匹配
        for entry in self.entries:
            content = entry.get("content", "").lower()
            query_lower = query.lower()

            # 计算匹配分数
            score = 0
            for keyword in keywords:
                if keyword.lower() in content:
                    score += 1
                # 如果关键词在查询中出现多次，增加权重
                if query_lower.count(keyword.lower()) > 1:
                    score += 0.5

            if score > 0:
                relevant.append((entry, score))

        # 按分数排序
        relevant.sort(key=lambda x: x[1], reverse=True)

        # 返回前 limit 个
        return [entry for entry, score in relevant[:limit]]

    async def append(self, entry: Dict):
        """添加人生书记录"""
        self.entries.append(entry)
        self._save()

    def _save(self):
        """保存人生书"""
        with open(self.db_path, "a", encoding="utf-8") as f:
            if self.entries:
                json.dump(self.entries[-1], f, ensure_ascii=False)
                f.write("\n")


class MemorySystem:
    """记忆系统 - 基于认知库的本地记忆"""

    def __init__(self):
        self.memories: List[Dict] = []
        self._index = defaultdict(list)  # 关键词索引

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取（中文 + 英文）
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
        english_words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        return list(set(chinese_words + english_words))

    async def retrieve(self, query: str, limit: int = 10) -> List[Dict]:
        """
        检索相关记忆（改进版）

        使用 TF-IDF 思想进行关键词匹配：
        - 提取查询关键词
        - 从索引中查找相关记忆
        - 根据关键词匹配度排序
        """
        if not self.memories:
            return []

        # 提取查询关键词
        query_keywords = self._extract_keywords(query)

        if not query_keywords:
            # 如果没有关键词，回退到简单匹配
            return self._simple_retrieve(query, limit)

        # 根据关键词查找记忆
        scored_memories = []

        for memory in self.memories:
            score = 0
            memory_keywords = memory.get("_keywords", [])

            # 计算关键词匹配分数
            for keyword in query_keywords:
                if keyword in memory_keywords:
                    score += 1

            # 添加时间衰减（最近的记忆权重更高）
            timestamp = memory.get("timestamp", "")
            try:
                time_diff = (datetime.now() - datetime.fromisoformat(timestamp)).days
                time_weight = max(0.1, 1.0 - time_diff / 30)  # 30天衰减到0.1
                score *= time_weight
            except:
                pass

            # 添加互动类型权重
            memory_type = memory.get("type", "")
            if memory_type == "interaction":
                score *= 1.2  # 互动记忆权重更高

            if score > 0:
                scored_memories.append((memory, score))

        # 按分数排序
        scored_memories.sort(key=lambda x: x[1], reverse=True)

        # 返回前 limit 个记忆
        return [memory for memory, score in scored_memories[:limit]]

    def _simple_retrieve(self, query: str, limit: int = 10) -> List[Dict]:
        """简单检索（回退方法）"""
        relevant = []
        for memory in self.memories:
            content = str(memory.get("user_input", "") + memory.get("response", ""))
            if any(word in content for word in query.split()[:5]):
                relevant.append(memory)
                if len(relevant) >= limit:
                    break
        return relevant

    async def store(self, memory: Dict):
        """存储记忆"""
        # 提取关键词用于索引
        content = str(memory.get("user_input", "") + memory.get("response", ""))
        keywords = self._extract_keywords(content)
        memory["_keywords"] = keywords

        # 更新索引
        for keyword in keywords:
            self._index[keyword].append(len(self.memories))

        # 存储记忆
        self.memories.insert(0, memory)  # 最新的在前面

        # 限制记忆数量
        if len(self.memories) > 1000:
            # 移除最旧的记忆的索引
            removed_index = len(self.memories) - 1
            removed_keywords = self.memories[removed_index].get("_keywords", [])
            for keyword in removed_keywords:
                if keyword in self._index and removed_index in self._index[keyword]:
                    self._index[keyword].remove(removed_index)

            self.memories = self.memories[:1000]


class CognitionBase:
    """认知库 - 弥娅的"知识基础"""

    def __init__(self):
        self.knowledge = self._init_knowledge()
        self._learning_rate = 0.1  # 学习率
        self._decay_rate = 0.95  # 衰减率

    def _init_knowledge(self) -> Dict[str, Any]:
        """初始化认知库（空白状态，通过学习积累）"""
        return {
            "facts": {},  # 事实性知识
            "patterns": {},  # 行为模式
            "preferences": {},  # 用户偏好
            "learned_responses": {},  # 学习到的回复
            "emotional_patterns": defaultdict(int)  # 情感模式统计
        }

    def query(self, query: str) -> List[Dict]:
        """查询认知库"""
        results = []

        # 提取查询关键词
        keywords = self._extract_keywords(query)

        # 查询事实
        for key, value in self.knowledge["facts"].items():
            if any(kw in key for kw in keywords) or key in query:
                results.append({
                    "type": "fact",
                    "content": value,
                    "confidence": value.get("confidence", 0.5)
                })

        # 查询偏好
        for key, value in self.knowledge["preferences"].items():
            if any(kw in key for kw in keywords) or key in query:
                results.append({
                    "type": "preference",
                    "content": value,
                    "confidence": value.get("confidence", 0.5)
                })

        # 查询行为模式
        for pattern_name, pattern_data in self.knowledge["patterns"].items():
            if any(kw in pattern_name for kw in keywords):
                results.append({
                    "type": "pattern",
                    "content": pattern_data,
                    "confidence": pattern_data.get("confidence", 0.5)
                })

        # 按置信度排序
        results.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        return results

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
        english_words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        return list(set(chinese_words + english_words))

    def learn(self, key: str, value: str, category: str = "fact", confidence: float = 0.5):
        """
        学习新知识

        学习机制：
        - 使用置信度来管理知识的可靠性
        - 重复学习会提高置信度
        - 罕见使用会降低置信度（衰减）
        """
        if category == "fact":
            if key in self.knowledge["facts"]:
                # 重复学习，提高置信度
                old_confidence = self.knowledge["facts"][key].get("confidence", 0.5)
                new_confidence = min(1.0, old_confidence + self._learning_rate)
                self.knowledge["facts"][key] = {
                    "value": value,
                    "confidence": new_confidence,
                    "learned_at": datetime.now().isoformat(),
                    "access_count": self.knowledge["facts"][key].get("access_count", 0) + 1
                }
            else:
                # 新知识
                self.knowledge["facts"][key] = {
                    "value": value,
                    "confidence": confidence,
                    "learned_at": datetime.now().isoformat(),
                    "access_count": 1
                }

        elif category == "preference":
            if key in self.knowledge["preferences"]:
                # 重复学习，提高置信度
                old_confidence = self.knowledge["preferences"][key].get("confidence", 0.5)
                new_confidence = min(1.0, old_confidence + self._learning_rate)
                self.knowledge["preferences"][key] = {
                    "value": value,
                    "confidence": new_confidence,
                    "learned_at": datetime.now().isoformat(),
                    "access_count": self.knowledge["preferences"][key].get("access_count", 0) + 1
                }
            else:
                # 新偏好
                self.knowledge["preferences"][key] = {
                    "value": value,
                    "confidence": confidence,
                    "learned_at": datetime.now().isoformat(),
                    "access_count": 1
                }

        elif category == "pattern":
            if key in self.knowledge["patterns"]:
                # 重复学习，提高置信度
                old_confidence = self.knowledge["patterns"][key].get("confidence", 0.5)
                new_confidence = min(1.0, old_confidence + self._learning_rate)
                self.knowledge["patterns"][key] = {
                    "value": value,
                    "confidence": new_confidence,
                    "count": self.knowledge["patterns"][key].get("count", 0) + 1,
                    "learned_at": datetime.now().isoformat()
                }
            else:
                # 新模式
                self.knowledge["patterns"][key] = {
                    "value": value,
                    "confidence": confidence,
                    "count": 1,
                    "learned_at": datetime.now().isoformat()
                }

        elif category == "emotional_pattern":
            # 记录情感模式
            self.knowledge["emotional_patterns"][key] += 1

    def reinforce(self, key: str, category: str = "fact"):
        """
        强化记忆（当知识被验证为正确时调用）
        """
        if category == "fact" and key in self.knowledge["facts"]:
            old_confidence = self.knowledge["facts"][key].get("confidence", 0.5)
            new_confidence = min(1.0, old_confidence + self._learning_rate * 2)
            self.knowledge["facts"][key]["confidence"] = new_confidence

    def decay_all(self):
        """
        衰减所有知识的置信度
        （定期调用，模拟遗忘曲线）
        """
        for fact in self.knowledge["facts"].values():
            fact["confidence"] *= self._decay_rate

        for pref in self.knowledge["preferences"].values():
            pref["confidence"] *= self._decay_rate

        for pattern in self.knowledge["patterns"].values():
            pattern["confidence"] *= self._decay_rate

    def cleanup(self, threshold: float = 0.1):
        """
        清理低置信度的知识
        """
        # 清理事实
        self.knowledge["facts"] = {
            k: v for k, v in self.knowledge["facts"].items()
            if v.get("confidence", 0) >= threshold
        }

        # 清理偏好
        self.knowledge["preferences"] = {
            k: v for k, v in self.knowledge["preferences"].items()
            if v.get("confidence", 0) >= threshold
        }

        # 清理模式
        self.knowledge["patterns"] = {
            k: v for k, v in self.knowledge["patterns"].items()
            if v.get("confidence", 0) >= threshold
        }


# ============================================================
# 工厂函数 - 创建双层意识实例
# ============================================================

# 全局后端意识实例（用于 agency_engine 访问）
_backend_awareness_instance: Optional[BackendAwareness] = None


def get_backend_awareness() -> Optional[BackendAwareness]:
    """
    获取全局后端意识实例

    返回：BackendAwareness 实例（如果已初始化），否则返回 None

    使用示例：
        backend = get_backend_awareness()
        if backend:
            backend.update_all()
            context = backend.get_awareness_context()
    """
    return _backend_awareness_instance


def set_backend_awareness(backend: BackendAwareness):
    """
    设置全局后端意识实例

    参数：
        backend: BackendAwareness 实例

    使用示例：
        from system.backend_awareness import BackendAwareness
        set_backend_awareness(BackendAwareness(config))
    """
    global _backend_awareness_instance
    _backend_awareness_instance = backend


def create_dual_layer_consciousness(config: Dict[str, Any]) -> ConsciousnessCoordinator:
    """
    创建双层意识实例（推荐使用）

    返回：ConsciousnessCoordinator（整合后端和前端意识）

    使用示例：
        coordinator = create_dual_layer_consciousness(config)
        result = await coordinator.think(
            user_input="你好",
            context={},
            llm_generator=my_llm_generator
        )
        print(result["response"])
    """
    logger.info("[意识工厂] 创建双层意识实例（后端意识 + 前端意识）")
    return ConsciousnessCoordinator(config)


def create_legacy_consciousness(config: Dict[str, Any]) -> ConsciousnessEngine:
    """
    创建传统意识实例（向后兼容）

    返回：ConsciousnessEngine（原始版本）

    使用示例：
        engine = create_legacy_consciousness(config)
        result = await engine.think(user_input="你好", context={})
    """
    logger.info("[意识工厂] 创建传统意识实例（向后兼容）")
    return ConsciousnessEngine(config)


class LLMTool:
    """大模型工具 - 作为"外脑"辅助思考"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("api", {}).get("enabled", True)
        self._async_client = None

    async def _get_client(self):
        """获取异步客户端"""
        if self._async_client is None:
            try:
                from nagaagent_core.core import AsyncOpenAI
                api_config = self.config.get("api", {})
                self._async_client = AsyncOpenAI(
                    api_key=api_config.get("api_key", ""),
                    base_url=api_config.get("base_url", "").rstrip('/') + '/'
                )
            except Exception as e:
                logger.error(f"[LLMTool] 初始化失败: {e}")
                self._async_client = None
        return self._async_client
