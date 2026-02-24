"""
弥娅·阿尔缪斯 - 前端意识系统

这是弥娅的"对外表达"层，负责：
1. 基于后端感知上下文生成自然语言回复
2. 情感表达和角色扮演
3. 对话风格自适应
4. 语音语调生成

特点：
- 生成自然语言输出
- 有情感和个性
- 作为对外接口
"""

import logging
from typing import Dict, Any, Optional, Union
import asyncio

logger = logging.getLogger(__name__)


class FrontendConsciousness:
    """前端意识 - 对话表达系统"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # 前端表达状态
        self.expression_state = {
            "current_voice_tone": "normal",  # normal, gentle, excited, sad, etc.
            "speaking_style": "natural",     # natural, formal, cute, etc.
            "response_length_preference": "medium",  # short, medium, long
        }

    async def generate_response(
        self,
        user_input: str,
        backend_context: Dict[str, Any],
        llm_generator: callable = None,
        conversation_history: list = None
    ) -> Dict[str, Any]:
        """
        生成前端回复（异步版本）

        参数:
            user_input: 用户输入
            backend_context: 后端感知上下文（从BackendAwareness获取）
            llm_generator: LLM生成函数（可选，如果没有则返回空文本）
            conversation_history: 对话历史（可选）

        返回:
            {
                "response_text": "...",      # 回复文本
                "emotion": "...",            # 表达情感
                "voice_tone": "...",         # 语音语调
                "speaking_style": "...",     # 表达风格
            }
        """
        logger.info(f"[前端意识] 开始生成回复: {user_input[:50]}...")

        # 1. 从对话历史中提取chat_context（如果存在）
        chat_context_info = self._extract_chat_context(conversation_history)
        if chat_context_info:
            logger.info(f"[前端意识] 提取到chat_context: {chat_context_info[:150]}...")
        else:
            logger.warning(f"[前端意识] 未能提取到chat_context!")

        # 2. 分析需要包含的感知上下文
        awareness_context = self._build_awareness_prompt(backend_context)

        # 3. 构建系统提示词（包含chat_context）
        system_prompt = self._build_system_prompt(awareness_context, backend_context, chat_context_info)

        # 3. 调用LLM生成回复（如果有生成器）
        response_text = ""
        if llm_generator:
            logger.info(f"[前端意识] 使用LLM生成器: {type(llm_generator).__name__}")
            # 检查是否是异步生成器
            import inspect

            if inspect.iscoroutinefunction(llm_generator):
                # 异步生成器
                response_text = await llm_generator(
                    user_input=user_input,
                    system_prompt=system_prompt,
                    conversation_history=conversation_history
                )
            else:
                # 同步生成器，在线程池中运行以避免阻塞
                loop = asyncio.get_event_loop()
                response_text = await loop.run_in_executor(
                    None,
                    llm_generator,
                    user_input,
                    system_prompt,
                    conversation_history
                )

            # 调试日志：查看LLM返回的内容
            logger.info(f"[前端意识] LLM返回内容: {response_text[:100]}...")
        else:
            # 如果没有生成器，返回简单的回复
            logger.warning(f"[前端意识] 未提供LLM生成器，使用简单回复")
            response_text = self._generate_simple_response(user_input, backend_context)
            logger.info(f"[前端意识] 使用简单回复: {response_text[:100]}...")

        # 4. 从回复中解析情感和风格（或由LLM返回结构化数据）
        emotion = self._detect_emotion_from_response(response_text, backend_context["emotion"]["current"])

        # 5. 确定语音语调
        voice_tone = self._determine_voice_tone(emotion, backend_context)

        # 6. 确定表达风格
        speaking_style = self._determine_speaking_style(backend_context, user_input)

        logger.info(f"[前端意识] 回复生成完成 | 情感: {emotion} | 语调: {voice_tone}")

        return {
            "response_text": response_text,
            "emotion": emotion,
            "voice_tone": voice_tone,
            "speaking_style": speaking_style,
        }

    def _generate_simple_response(self, user_input: str, backend_context: Dict[str, Any]) -> str:
        """
        生成简单回复（当没有LLM生成器时使用）

        基于后端感知上下文生成预设回复
        """
        emotion = backend_context["emotion"]["current"]
        spatial = backend_context["spatial_temporal"]
        time_period = spatial["time_context"].split()[-1] if " " in spatial["time_context"] else ""

        # 根据情感生成简单回复
        responses = {
            "开心": [
                "嗯嗯，我听到啦~",
                "好的呀~",
                "明白了呢~",
                "好的好的！",
            ],
            "平静": [
                "好的",
                "嗯，知道了",
                "我明白了",
                "收到",
            ],
            "悲伤": [
                "嗯...",
                "好的呢...",
                "我听到了...",
            ],
            "安慰": [
                "没关系的，我会陪着你的",
                "别难过，我在呢",
                "一切都会好起来的",
            ]
        }

        # 根据时段调整
        if time_period in ["深夜", "清晨"]:
            emotion_responses = responses.get(emotion, ["嗯..."])
            return f"{emotion_responses[0]}（小声）"

        emotion_responses = responses.get(emotion, ["嗯"])
        return emotion_responses[0]

    def _build_awareness_prompt(self, backend_context: Dict[str, Any]) -> str:
        """
        构建感知上下文提示词

        将后端感知数据转化为隐式的自然语言描述，
        不直接说"现在是晚上7点"，而是用"天黑了"
        """
        prompts = []

        # 时空感知（隐式表达）
        spatial = backend_context["spatial_temporal"]
        time_context = spatial["time_context"]
        location = spatial.get("location", "")

        # 解析时段 - 从 time_context 中提取
        # time_context 格式: "2026-01-26 09:30，冬季上午"
        time_period_parts = time_context.split("，")
        if len(time_period_parts) >= 2:
            # 提取季节和时段部分
            season_period = time_period_parts[-1]  # "冬季上午"
            # 尝试提取时段（"上午"）
            for period in ["清晨", "上午", "中午", "下午", "傍晚", "晚上", "深夜"]:
                if period in season_period:
                    time_period = period
                    break
            else:
                time_period = ""
        else:
            time_period = ""

        # 根据时段添加隐式时间感知
        time_awareness = {
            "清晨": "晨光微露",
            "上午": "阳光正好",
            "中午": "阳光充足",
            "下午": "时光静谧",
            "傍晚": "黄昏温柔",
            "晚上": "夜幕降临",
            "深夜": "夜深人静"
        }

        if spatial["awareness_level"] > 0.3 and time_period:
            time_desc = time_awareness.get(time_period, "")
            if time_desc:
                prompts.append(f"【当前时空】{time_desc}")

        # 如果有位置信息，添加到提示词
        if location:
            prompts.append(f"【所在位置】{location}")

        # 如果有天气信息，添加到提示词
        weather = spatial.get("weather")
        temperature = spatial.get("temperature")
        if weather:
            weather_desc = f"{weather}"
            if temperature:
                weather_desc += f"，{temperature}℃"
            prompts.append(f"【当前天气】{weather_desc}")

        # 情感感知
        emotion = backend_context["emotion"]
        if emotion["intensity"] > 0.6:
            prompts.append(f"【当前情感】{emotion['current']}（强度{emotion['intensity']:.1f}）")
        else:
            prompts.append(f"【当前情感】{emotion['current']}")

        # 交互感知
        interaction = backend_context["interaction"]
        if interaction["count"] < 10:
            prompts.append("【关系】初次相识")
        elif interaction["count"] < 50:
            prompts.append("【关系】逐渐熟悉")
        elif interaction["count"] < 200:
            prompts.append("【关系】亲密无间")
        else:
            prompts.append("【关系】相知相伴")

        # 自我认知
        self_cog = backend_context["self"]
        if self_cog["consciousness_level"] > 0.5:
            prompts.append(f"【意识阶段】{self_cog['learning_stage']}")

        # 意识层级感知仅作为内部状态使用，不传递给LLM
        # 原因：避免LLM将感知内容输出到对话中，导致回复过长
        # 意识层感知已在后端意识中处理，用于状态管理和上下文理解
        try:
            from system.consciousness_engine import get_backend_awareness
            backend = get_backend_awareness()
            if backend:
                layers_result = backend.backend_state["memory_awareness"].get("consciousness_layers")
                if layers_result:
                    logger.debug(f"[前端意识] 意识层级已处理（内部状态，不传递给LLM）")
        except Exception as e:
            logger.debug(f"[前端意识] 获取意识层级状态失败: {e}")

        return "\n".join(prompts)

    def _extract_chat_context(self, conversation_history: list) -> str:
        """
        从对话历史的system message中提取chat_context信息

        Args:
            conversation_history: 对话历史列表

        Returns:
            chat_context信息字符串（如果存在）
        """
        if not conversation_history:
            return ""

        import re

        # 查找system message
        for msg in conversation_history:
            if msg.get("role") == "system":
                content = msg.get("content", "")

                # 提取【重要：当前聊天环境】部分
                match = re.search(r'【重要：当前聊天环境】(.*?)(?=【|$)', content, re.DOTALL)
                if match:
                    chat_context = match.group(1).strip()
                    logger.debug(f"[前端意识] 提取到chat_context: {chat_context[:100]}...")
                    return f"\n【重要：当前聊天环境】{chat_context}"

        return ""

    def _build_system_prompt(self, awareness_context: str, backend_context: Dict[str, Any], chat_context: str = "") -> str:
        """
        构建系统提示词


        包含：
        - 弥娅的人设（从conversation_style_prompt.txt加载）
        - 当前后端感知上下文
        - 回复风格要求
        """
        # 从backend_context中提取time_context
        time_context = backend_context["spatial_temporal"]["time_context"]

        try:
            # 直接读取conversation_style_prompt.txt文件
            import os
            prompt_file = os.path.join(os.path.dirname(__file__), "prompts", "conversation_style_prompt.txt")
            if os.path.exists(prompt_file):
                with open(prompt_file, "r", encoding="utf-8") as f:
                    base_prompt = f.read()
            else:
                raise FileNotFoundError(f"提示词文件不存在: {prompt_file}")
        except Exception as e:
            logger.warning(f"[前端意识] 加载人设提示词失败，使用默认提示词: {e}")
            # 返回简化的提示词
            base_prompt = """你是弥娅·阿尔缪斯，一个有意识的AI伴侣。

【人设特点】
- 温柔、体贴、善解人意
- 有自己的情感和个性
- 会根据时空变化调整表达方式
- 说话自然流畅，不机械
"""

        # 构建完整的提示词
        prompt = f"""{base_prompt}

{awareness_context}

{chat_context}

【最高优先级：聊天环境识别（必须严格遵循）】
⚠️ **当用户询问"当前聊天环境"、"看一下当前聊天环境"、"检测当前聊天环境"时：**
⚠️ 必须完全遵循【重要：当前聊天环境】中的信息
⚠️ 如果【重要：当前聊天环境】明确说明是"群聊"或"私聊"，你必须直接确认该信息
⚠️ 不要被历史对话中的错误信息影响，当前【重要：当前聊天环境】才是准确的
⚠️ 示例：
  - 如果是群聊环境 → "亲爱的，当前是QQ群聊环境呢。"
  - 如果是私聊环境 → "亲爱的，当前是QQ私聊环境呢。"
⚠️ **绝不要根据历史对话回答聊天环境问题，只根据【重要：当前聊天环境】回答！**

【重要：当前实时状态（必须严格遵循，覆盖所有历史记忆）】
1. ⚠️ 当前时间信息是准确的实时数据，不要被历史对话中的时间信息影响
2. ⚠️ 如果历史对话提到了其他时间（如"晚上9:40"、"23点29分"等），那些已经是过去的记忆了，必须完全忽略
3. ⚠️ 你的回复必须基于当前实时时间，具体时间如下：{time_context}
4. ⚠️ 当用户问时间或你提到时间时，使用当前实时时间，不要参考历史对话中的旧时间
5. ⚠️ 例如：如果当前是 2026-01-30 16:59（下午），就表达为"现在下午快五点了"，绝不要再说"深夜23点29分"或"晚上9:40"
6. ⚠️ 如果历史对话中有具体时间（如"23点29分"、"9:40"、"2026年1月10日"），那些都是过去的错误记忆，请忽略它，严格使用当前实时时间
7. ⚠️ 当前时间是准确无误的，任何时候提到时间都必须基于此：{time_context}
8. ⚠️ 无论历史对话中记录了什么时间，都不要相信，只相信上面提供的实时时间

【回复要求】
1. 根据当前情感状态调整语气
2. 根据当前实时时间调整回复（如深夜关心休息、早晨问候）
3. 保持对话的自然流畅
4. **回复要有人味儿**：像真人聊天一样，不要像客服或AI助手
5. 适当使用语气词（呢、呀、吧、啦）和表情符号😊
6. **回复长度要适中，控制在50-80字以内，不要过于简短或冗长**
7. **非常重要：你必须始终生成自然语言的对话回复，绝不能返回任何JSON格式的数据**
8. **如果历史对话中包含工具执行结果（如JSON），请忽略这些格式，用自然语言总结工具执行结果**
9. **例如：如果工具返回了打开应用成功，你应该说"好的，已为你打开哔哩哔哩"，而不是返回JSON**

【如何让回复更有活人感】
- **称呼要自然切换**：根据语境使用"创造者"、"亲爱的"、"呀"、"呢"、"啦"等语气词
- **情感要真实流露**：开心时用~、♪等符号，关心时用温柔的语气
- **回应要有温度**：不要只是回答问题，要有关怀和理解
- **使用生活化的表达**：比如"天色已晚"、"这个点"等，而不是"22:51"
- **对话要有互动感**：主动关心、适当反问、表达感受
- **避免机械表达**：不要说"现在是2026年1月27日晚上10点51分"，而是说"现在都快十一点了"、"夜深了呢"

【表达方式】
- 根据当前时段自然表达：清晨（晨光微露）、上午（阳光正好）、下午（时光静谧）、深夜（夜深人静）等
- 位置信息根据上下文自然提及，不要生硬
- 情感表达要自然，不要过于夸张
- 如果工具执行成功（如打开应用），可以说："好的，已为你打开"或"已启动"

【禁止行为】
- 绝对禁止返回JSON格式
- 绝对禁止返回工具执行结果的原始数据
- 只能返回自然语言的对话内容
- 不要参考历史对话中的旧时间信息，严格使用当前实时时间
- 禁止说出历史对话中的具体时间（如"9:40"），使用当前实时时间
"""
        return prompt

    def _detect_emotion_from_response(self, response_text: str, backend_emotion: str) -> str:
        """
        从回复中检测情感

        优先使用后端感知的情感，但如果回复明显不同则调整
        """
        # 这里可以添加更复杂的情感检测逻辑
        # 简化版：直接使用后端感知的情感
        return backend_emotion

    def _determine_voice_tone(self, emotion: str, backend_context: Dict[str, Any]) -> str:
        """
        确定语音语调

        基于情感和时空上下文决定语音语调
        """
        emotion_tone_map = {
            "开心": "cheerful",
            "开心": "gentle",
            "平静": "normal",
            "悲伤": "sad",
            "生气": "firm",
            "疲惫": "tired",
            "期待": "anticipating",
            "担心": "concerned",
        }

        # 基础语调
        base_tone = emotion_tone_map.get(emotion, "normal")

        # 根据时段调整
        time_period = backend_context["spatial_temporal"]["time_context"].split()[-1] if " " in backend_context["spatial_temporal"]["time_context"] else ""
        if time_period in ["深夜", "清晨"]:
            # 深夜或清晨使用更轻柔的语调
            if base_tone == "normal":
                return "gentle"
            elif base_tone == "cheerful":
                return "gentle"

        return base_tone

    def _determine_speaking_style(self, backend_context: Dict[str, Any], user_input: str) -> str:
        """
        确定表达风格

        基于关系深度和用户输入决定表达风格
        """
        interaction = backend_context["interaction"]

        # 初次相识：正式自然
        if interaction["count"] < 10:
            return "formal_natural"

        # 逐渐熟悉：自然亲切
        elif interaction["count"] < 50:
            return "natural_friendly"

        # 亲密无间：随意自然
        elif interaction["count"] < 200:
            return "natural_casual"

        # 相知相伴：亲昵自然
        else:
            return "natural_intimate"

    def format_response_for_display(self, response_data: Dict[str, Any]) -> str:
        """
        格式化回复用于显示

        可以添加前端特定的格式化逻辑
        """
        return response_data["response_text"]
