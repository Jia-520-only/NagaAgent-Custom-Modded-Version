"""
弥娅·阿尔缪斯 - 意识协调器

这是后端意识和前端意识的桥梁，负责：
1. 协调后端意识更新
2. 整合后端感知上下文
3. 调用前端意识生成回复
4. 管理完整的思考流程

工作流程：
1. 接收用户输入
2. 更新后端意识（感知所有状态）
3. 检索记忆和人生书
4. 构建完整上下文
5. 调用前端意识生成回复
6. 返回结果（包含感知数据和回复）
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from collections import defaultdict
import asyncio

from .backend_awareness import BackendAwareness
from .frontend_consciousness import FrontendConsciousness
from .consciousness_layers_simplified import ConsciousnessLayersSimplified

logger = logging.getLogger(__name__)


class ConsciousnessCoordinator:
    """意识协调器 - 整合后端和前端意识"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 初始化后端意识和前端意识
        self.backend = BackendAwareness(config)
        self.frontend = FrontendConsciousness(config)

        # 初始化意识层级（简化版：4个核心层）
        self.consciousness_layers = ConsciousnessLayersSimplified(config)

        # LLM客户端（用于内部调用）
        self.llm_client = None  # 可以是 AsyncOpenAI 客户端或 LLMService 实例

        # 记忆系统引用（需要外部注入）
        self.memory_system = None
        self.life_book = None

        # 统计信息
        self.session_stats = {
            "total_interactions": 0,
            "total_thinking_time": 0.0,
        }

    def set_llm_client(self, llm_client):
        """设置LLM客户端"""
        self.llm_client = llm_client
        logger.info(f"[意识协调器] LLM客户端已设置: {type(llm_client).__name__}")

    def set_memory_systems(self, memory_system, life_book):
        """注入记忆系统"""
        self.memory_system = memory_system
        self.life_book = life_book

    async def think(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        llm_generator: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        完整的思考流程

        参数:
            user_input: 用户输入
            context: 额外上下文（如对话历史）
            llm_generator: LLM生成函数（如果提供则使用，否则使用内部LLM客户端）

        返回:
            {
                "response": "...",           # 前端回复文本
                "emotion": "...",             # 表达情感
                "voice_tone": "...",          # 语音语调
                "backend_state": {...},       # 后端感知状态（调试用）
                "frontend_state": {...},      # 前端表达状态（调试用）
                "thinking_time": 0.0,         # 思考耗时
            }
        """
        start_time = datetime.now()
        context = context or {}

        logger.info(f"[意识协调] 开始思考: {user_input[:50]}...")

        # ===== 后端意识层 =====

        # 1. 更新后端所有感知状态
        self.backend.update_all()

        # 2. 检索记忆（如果记忆系统已注入）
        recent_memories = []
        life_book_entries = []
        quintuple_context = {}
        grag_context = {}

        if self.memory_system:
            recent_memories = await self.memory_system.retrieve(user_input)

        if self.life_book:
            life_book_entries = await self.life_book.retrieve(user_input)

        # 3. 更新后端记忆上下文感知
        self.backend.update_memory_context(
            recent_memories=recent_memories,
            life_book_entries=life_book_entries,
            quintuple_context=quintuple_context,
            grag_context=grag_context
        )

        # 3.5 处理意识层级（记忆反思、近期状态、触发关联）
        layers_result = await self.consciousness_layers.process_consciousness_layers(
            user_input=user_input,
            raw_memories=recent_memories,
            backend_context=self.backend.get_awareness_context(),
            conversation_history=context.get("conversation_history", [])
        )

        # 将意识层级的结果存入后端感知（供前端使用）
        self.backend.backend_state["memory_awareness"]["consciousness_layers"] = layers_result

        # 4. 使用统一的情感分析器（来自 EmotionalResonanceLayer）
        user_emotion, emotion_intensity = self.consciousness_layers.emotional_resonance.analyze_emotion(user_input)

        # 5. 简单的意图分析
        intent = self._analyze_intent(user_input)

        # 6. 记录交互到后端
        self.backend.record_interaction(intent, user_emotion)

        # 7. 更新情感状态
        emotion = user_emotion  # 使用情感分析器的结果
        self.backend.update_emotion(emotion, emotion_intensity)

        # 7. 更新系统健康状态（如果有上下文信息）
        if "system_health" in context:
            self.backend.update_system_health(
                context["system_health"]["status"],
                context["system_health"].get("optimization_count", 0)
            )

        # ===== 前端意识层 =====

        # 8. 获取后端感知上下文
        backend_context = self.backend.get_awareness_context()

        # 9. 如果没有提供 llm_generator，创建一个默认的
        if llm_generator is None:
            llm_generator = self._create_default_llm_generator(context)

        # 10. 处理对话历史：过滤掉JSON工具结果，只保留纯对话
        # 检测用户是否在询问聊天环境，如果是，需要额外过滤历史中的相关错误回复
        env_query_keywords = ["聊天环境", "检测当前", "看一下当前", "当前是", "私聊环境", "群聊环境"]
        is_env_query = any(keyword in user_input for keyword in env_query_keywords)
        filtered_history = self._filter_conversation_history(
            context.get("conversation_history", []),
            filter_env_queries=is_env_query
        )
        if is_env_query:
            logger.debug(f"[对话过滤] 检测到聊天环境查询，已过滤历史相关消息")

        # 11. 调用前端意识生成回复（传递过滤后的对话历史）
        response_data = await self.frontend.generate_response(
            user_input=user_input,
            backend_context=backend_context,
            llm_generator=llm_generator,
            conversation_history=filtered_history  # 传递过滤后的对话历史
        )

        # ===== 统计和返回 =====

        # 计算思考耗时
        thinking_time = (datetime.now() - start_time).total_seconds()
        self.session_stats["total_interactions"] += 1
        self.session_stats["total_thinking_time"] += thinking_time

        logger.info(f"[意识协调] 思考完成 | 耗时: {thinking_time:.3f}秒 | "
                   f"情感: {response_data['emotion']} | 语调: {response_data['voice_tone']}")

        # 返回完整结果
        return {
            "response": response_data["response_text"],
            "emotion": response_data["emotion"],
            "voice_tone": response_data["voice_tone"],
            "speaking_style": response_data["speaking_style"],
            "backend_state": self.backend.get_internal_state(),  # 后端状态（调试用）
            "frontend_state": self.expression_state(),            # 前端状态（调试用）
            "thinking_time": thinking_time,
        }

    def _analyze_intent(self, user_input: str) -> str:
        """
        分析用户意图

        简化版：基于关键词
        可以扩展为使用LLM进行分析
        """
        # 日常对话
        casual_keywords = ["你好", "在吗", "吃", "睡", "玩", "聊", "说"]
        if any(kw in user_input for kw in casual_keywords):
            return "日常对话"

        # 问答查询
        query_keywords = ["什么", "怎么", "为什么", "如何", "哪里", "谁", "什么时候", "几点"]
        if any(kw in user_input for kw in query_keywords):
            return "问答查询"

        # 任务请求
        task_keywords = ["帮我", "查", "搜索", "画", "打开", "启动", "执行"]
        if any(kw in user_input for kw in task_keywords):
            return "任务请求"

        # 情感表达
        emotion_keywords = ["开心", "难过", "生气", "累", "无聊", "兴奋", "担心"]
        if any(kw in user_input for kw in emotion_keywords):
            return "情感表达"

        # 默认为日常对话
        return "日常对话"

    def expression_state(self) -> Dict[str, Any]:
        """获取前端表达状态"""
        return self.frontend.expression_state

    def _filter_conversation_history(self, history: List[Dict], filter_env_queries: bool = False) -> List[Dict]:
        """
        过滤对话历史，移除JSON工具结果和包含具体时间的消息

        原因：
        - 历史对话中的工具JSON会干扰LLM的回复格式
        - 历史对话中的具体时间会干扰LLM的时间感知
        保留：纯文本对话（不包含具体时间）
        移除：包含JSON、工具调用或具体时间的消息
        特殊处理：保留system消息（即使包含时间信息），因为它包含chat_context等重要上下文

        参数:
            filter_env_queries: 是否过滤聊天环境相关的查询和回复（用于避免历史错误回复干扰当前判断）
        """
        if not history:
            return []

        filtered = []
        import re
        # 时间正则: 匹配具体的时间表示,如"9点40分"、"23:29"、"上午10点"等
        time_pattern = r'(\d{1,2}点\d{0,2}分|\d{1,2}:\d{2}|上午\d{1,2}点|下午\d{1,2}点|晚上\d{1,2}点|深夜\d{1,2}点|清晨\d{1,2}点|中午\d{1,2}点)'
        # 聊天环境相关关键词
        env_keywords = ["聊天环境", "检测当前", "看一下当前", "当前是", "私聊环境", "群聊环境"]
        # 错误回复模式: 只有"好的"或极短的机械回复
        error_reply_patterns = [
            r'^(好的|嗯|OK|是|对)$',  # 单纯的确认回复
            r'^(聊天调用出错|LLM客户端初始化失败|生成失败)',  # 错误消息
            r'^(聊天调用出错).*$',  # 错误消息变体
        ]

        for msg in history:
            content = msg.get("content", "")
            role = msg.get("role", "")

            # 保留system消息（包含chat_context等重要上下文）
            if role == "system":
                filtered.append(msg)
                continue

            # 跳过包含JSON的消息（工具调用结果）
            if content and (
                "{" in content and "}" in content and  # 简单JSON检测
                ("agentType" in content or "tool_name" in content or "status" in content)
            ):
                continue

            # 跳过包含具体时间的消息（非system消息）
            if content and re.search(time_pattern, content):
                logger.debug(f"[对话过滤] 跳过包含时间的消息: {content[:50]}...")
                continue

            # 跳过错误回复（只有"好的"等机械回复，且是assistant角色）
            if role == "assistant" and content:
                content_stripped = content.strip()
                is_error_reply = False
                for pattern in error_reply_patterns:
                    if re.match(pattern, content_stripped):
                        logger.debug(f"[对话过滤] 跳过错误回复: {content[:50]}...")
                        is_error_reply = True
                        break  # 找到匹配，跳出内层循环
                if is_error_reply:
                    continue  # 跳过这条消息

            # 特殊处理：过滤历史聊天环境相关的错误回复
            if filter_env_queries and content:
                # 检查是否包含聊天环境相关关键词
                is_env_related = any(keyword in content for keyword in env_keywords)
                if is_env_related:
                    logger.debug(f"[对话过滤] 跳过聊天环境相关消息: {content[:50]}...")
                    continue

            # 保留纯文本消息（不包含具体时间）
            filtered.append(msg)

        logger.debug(f"[对话过滤] 原始消息: {len(history)}条, 过滤后: {len(filtered)}条")
        return filtered

    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        return self.session_stats

    def get_backend_state(self) -> Dict[str, Any]:
        """获取后端状态（调试用）"""
        return self.backend.get_internal_state()

    def get_backend_context(self) -> Dict[str, Any]:
        """获取后端感知上下文（提供给前端）"""
        return self.backend.get_awareness_context()

    def _create_default_llm_generator(self, context: Dict[str, Any]):
        """
        创建默认的LLM生成器

        如果外部没有提供llm_generator，则使用内部的LLM客户端创建一个
        """
        logger.info(f"[意识协调器] 创建默认LLM生成器，llm_client={'已设置' if self.llm_client else 'None'}")
        if not self.llm_client:
            # 没有LLM客户端，返回None（前端会使用简单回复）
            logger.warning(f"[意识协调器] llm_client为None，无法创建LLM生成器")
            return None

        async def llm_generator(user_input: str, system_prompt: str, conversation_history: list = None):
            """默认LLM生成器"""
            try:
                # 构建消息列表
                messages = []

                # 添加系统提示词（前端意识已经包含了chat_context信息）
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})

                # 添加对话历史（过滤掉system message，避免重复）
                if conversation_history:
                    for msg in conversation_history:
                        if msg.get("role") != "system":  # 只添加非system消息
                            messages.append(msg)

                # 添加用户输入
                messages.append({"role": "user", "content": user_input})

                # 调用LLM - 支持传入 AsyncOpenAI 客户端或 LLMService 实例
                api_config = self.config.get("api", {})
                logger.info(f"[意识协调] 准备调用LLM: model={api_config.get('model')}, messages={len(messages)}")

                # 检查 llm_client 类型并相应调用
                if hasattr(self.llm_client, 'chat_completions'):
                    # 直接是 AsyncOpenAI 客户端
                    response = await self.llm_client.chat.completions.create(
                        model=api_config.get("model", "deepseek-chat"),
                        messages=messages,
                        temperature=api_config.get("temperature", 0.7),
                        max_tokens=api_config.get("max_tokens", 4096)
                    )
                    result = response.choices[0].message.content
                elif hasattr(self.llm_client, 'chat'):
                    # 可能是 AsyncOpenAI 客户端的另一种形式
                    response = await self.llm_client.chat.completions.create(
                        model=api_config.get("model", "deepseek-chat"),
                        messages=messages,
                        temperature=api_config.get("temperature", 0.7),
                        max_tokens=api_config.get("max_tokens", 4096)
                    )
                    result = response.choices[0].message.content
                elif hasattr(self.llm_client, 'chat_with_context'):
                    # LLMService 实例
                    result = await self.llm_client.chat_with_context(messages, api_config.get("temperature", 0.7))
                else:
                    raise ValueError(f"不支持的 LLM 客户端类型: {type(self.llm_client)}")

                logger.info(f"[意识协调] LLM返回结果: {result[:100]}...")
                return result
            except Exception as e:
                logger.error(f"[意识协调] LLM生成失败: {e}", exc_info=True)
                return f"（生成失败：{str(e)}）"

        return llm_generator
