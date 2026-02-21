#!/usr/bin/env python3
"""
LLM服务模块
提供统一的LLM调用接口，替代conversation_core.py中的get_response方法
"""

import logging
import sys
import os
from typing import Optional, Dict, Any, List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nagaagent_core.core import AsyncOpenAI
from nagaagent_core.api import FastAPI, HTTPException
from system.config import config

# 配置日志
logger = logging.getLogger("LLMService")

class LLMService:
    """LLM服务类 - 提供统一的LLM调用接口"""

    def __init__(self):
        self.async_client: Optional[AsyncOpenAI] = None
        self._client_lock = None  # 客户端初始化锁
        # 延迟初始化客户端，避免在模块加载时创建
        # self._initialize_client()  # 注释掉模块级初始化

        # 初意识引擎
        self.consciousness_engine = None
        self._initialize_consciousness_engine()

    def _initialize_consciousness_engine(self):
        """初始化初意识引擎 - 使用双层意识架构"""
        try:
            consciousness_config = config.consciousness
            if consciousness_config.enabled:
                from system.consciousness_engine import create_dual_layer_consciousness
                # 转换配置为字典格式
                config_dict = {
                    "api": config.api.__dict__,
                    "consciousness": consciousness_config.__dict__,
                    "system": config.system.__dict__,
                    "location": config.location.__dict__ if hasattr(config, 'location') else {}
                }
                self.consciousness_engine = create_dual_layer_consciousness(config_dict)

                # LLM客户端将在第一次调用时注入（在 _ensure_client 中）
                # 避免初始化时没有 AsyncOpenAI 实例
                logger.info(f"[双层意识] 引擎已启动,模式: dual_layer")
            else:
                logger.debug("[双层意识] 未启用,使用传统LLM模式")
        except Exception as e:
            logger.warning(f"[双层意识] 初始化失败,使用传统LLM模式: {e}")
            import traceback
            traceback.print_exc()
            self.consciousness_engine = None
    
    def _initialize_client(self):
        """初始化OpenAI客户端"""
        try:
            # 确保在当前事件循环中创建客户端
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                logger.info(f"LLM服务客户端将在事件循环 {loop} 中初始化")
            except RuntimeError:
                # 没有运行的事件循环，这没关系，AsyncOpenAI会在需要时处理
                logger.debug("初始化时没有运行的事件循环")

            # 创建 AsyncOpenAI 客户端，让它自动管理 http_client
            self.async_client = AsyncOpenAI(
                api_key=config.api.api_key,
                base_url=config.api.base_url.rstrip('/') + '/'
            )
            logger.info("LLM服务客户端初始化成功")
        except Exception as e:
            logger.error(f"LLM服务客户端初始化失败: {e}")
            import traceback
            traceback.print_exc()
            self.async_client = None

    async def _ensure_client(self):
        """确保客户端已初始化并可用"""
        if self.async_client is None:
            self._initialize_client()
            # 初始化后延迟设置到意识引擎
            if self.async_client and self.consciousness_engine and hasattr(self.consciousness_engine, 'set_llm_client'):
                self.consciousness_engine.set_llm_client(self.async_client)
                logger.info(f"[双层意识] AsyncOpenAI客户端已注入到意识协调器")

        # 确保每次都更新意识协调器的LLM客户端引用
        if self.async_client and self.consciousness_engine and hasattr(self.consciousness_engine, 'set_llm_client'):
            self.consciousness_engine.set_llm_client(self.async_client)

        if self.async_client is None:
            raise RuntimeError("LLM客户端初始化失败")
        return self.async_client
    
    async def get_response(self, prompt: str, temperature: float = 0.7) -> str:
        """为其他模块提供API调用接口"""

        # 检查是否是提醒系统生成的消息，避免无限循环
        # 如果prompt包含提醒相关内容且较短，直接走普通LLM流程，不进行任务解析
        import re
        is_reminder_prompt = (
            "用户收到了一个提醒" in prompt or
            "提醒消息" in prompt or
            "温馨、个性化" in prompt or
            bool(re.search(r'用户收了一个:.*提醒', prompt))
        )

        # 如果不是提醒消息，才进行任务检查
        if not is_reminder_prompt:
            try:
                from system.task_service_manager import get_task_service_manager
                task_service = get_task_service_manager()

                # 处理用户输入
                result = await task_service.process_user_input(prompt)

                logger.info(f"[LLMService] 任务检查结果: {result}")

                if result and result.get("success"):
                    # 是任务相关，直接返回响应
                    logger.info(f"[LLMService] 识别为任务意图: {result.get('intent_type')}")
                    return result["response"]
            except Exception as e:
                logger.error(f"[LLMService] 任务检查失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            logger.info(f"[LLMService] 检测到提醒系统消息,跳过任务解析")
        
        # 如果启用了双层意识引擎，使用双层意识模式
        if self.consciousness_engine:
            try:
                context = {
                    "user_input": prompt,
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": prompt}],
                    "conversation_history": []
                }
                # 传递 LLM 生成器函数
                async def llm_generator(user_input: str, system_prompt: str, conversation_history: list = None):
                    client = await self._ensure_client()
                    messages = []
                    if system_prompt:
                        messages.append({"role": "system", "content": system_prompt})
                    if conversation_history:
                        messages.extend(conversation_history)
                    messages.append({"role": "user", "content": user_input})
                    response = await client.chat.completions.create(
                        model=config.api.model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=config.api.max_tokens
                    )
                    return response.choices[0].message.content
                
                result = await self.consciousness_engine.think(prompt, context, llm_generator)
                logger.debug(f"[双层意识] 思考完成,情感: {result.get('emotion', 'unknown')}")
                return result["response"]
            except Exception as e:
                logger.error(f"[双层意识] 调用失败,回退到传统LLM模式: {e}")
                # 回退到传统模式

        # 传统LLM模式
        try:
            client = await self._ensure_client()
            response = await client.chat.completions.create(
                model=config.api.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=config.api.max_tokens
            )
            return response.choices[0].message.content
        except RuntimeError as e:
            if "handler is closed" in str(e) or "cannot schedule" in str(e):
                logger.debug(f"检测到事件循环或连接问题: {e}")
                # 重新创建客户端
                self.async_client = None
                try:
                    client = await self._ensure_client()
                    response = await client.chat.completions.create(
                        model=config.api.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        max_tokens=config.api.max_tokens
                    )
                    return response.choices[0].message.content
                except Exception as retry_error:
                    logger.error(f"重试失败: {retry_error}")
                    return f"LLM服务不可用: {str(retry_error)}"
            else:
                logger.error(f"API调用失败: {e}")
                import traceback
                traceback.print_exc()
                return f"API调用出错: {str(e)}"
        except Exception as e:
            logger.error(f"API调用失败: {e}")
            import traceback
            traceback.print_exc()
            return f"API调用出错: {str(e)}"
    
    def is_available(self) -> bool:
        """检查LLM服务是否可用"""
        return self.async_client is not None
    
    async def chat_with_context(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """带上下文的聊天调用"""
        # 提取用户输入
        user_input = ""
        if messages:
            user_input = messages[-1].get("content", "") if messages[-1].get("role") == "user" else ""

        # 如果启用了双层意识引擎
        if self.consciousness_engine and user_input:
            try:
                context = {
                    "user_input": user_input,
                    "messages": messages,
                    "temperature": temperature,
                    "conversation_history": messages
                }
                # 传递 LLM 生成器函数
                async def llm_generator(user_input: str, system_prompt: str, conversation_history: list = None):
                    client = await self._ensure_client()
                    msgs = []
                    if system_prompt:
                        msgs.append({"role": "system", "content": system_prompt})
                    if conversation_history:
                        for msg in conversation_history:
                            if msg.get("role") != "system":
                                msgs.append(msg)
                    msgs.append({"role": "user", "content": user_input})
                    response = await client.chat.completions.create(
                        model=config.api.model,
                        messages=msgs,
                        temperature=temperature,
                        max_tokens=config.api.max_tokens
                    )
                    return response.choices[0].message.content
                
                result = await self.consciousness_engine.think(user_input, context, llm_generator)
                logger.debug(f"[双层意识] chat_with_context 思考完成,情感: {result.get('emotion', 'unknown')}")
                return result["response"]
            except Exception as e:
                logger.error(f"[双层意识] 调用失败,回退到传统LLM模式: {e}")

        # 传统LLM模式
        try:
            client = await self._ensure_client()
            response = await client.chat.completions.create(
                model=config.api.model,
                messages=messages,
                temperature=temperature,
                max_tokens=config.api.max_tokens
            )
            return response.choices[0].message.content
        except RuntimeError as e:
            if "handler is closed" in str(e) or "cannot schedule" in str(e):
                logger.debug(f"检测到事件循环或连接问题: {e}")
                # 重新创建客户端
                self.async_client = None
                try:
                    client = await self._ensure_client()
                    response = await client.chat.completions.create(
                        model=config.api.model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=config.api.max_tokens
                    )
                    return response.choices[0].message.content
                except Exception as retry_error:
                    logger.error(f"重试失败: {retry_error}")
                    return f"LLM服务不可用: {str(retry_error)}"
            else:
                logger.error(f"上下文聊天调用失败: {e}")
                import traceback
                traceback.print_exc()
                return f"聊天调用出错: {str(e)}"
        except Exception as e:
            logger.error(f"上下文聊天调用失败: {e}")
            import traceback
            traceback.print_exc()
            return f"聊天调用出错: {str(e)}"
    
    async def stream_chat_with_context(self, messages: List[Dict], temperature: float = 0.7):
        """带上下文的流式聊天调用（新架构：双层意识 - 后端感知 + 前端表达）"""
        # 提取用户输入
        user_input = ""
        if messages:
            last_message = messages[-1]
            role = last_message.get("role", "")
            content = last_message.get("content", "")
            if role == "user":
                user_input = str(content) if content else ""

        # 如果启用了双层意识引擎
        if self.consciousness_engine and user_input:
            try:
                # 构建上下文
                context = {
                    "user_input": user_input,
                    "messages": messages,
                    "temperature": temperature,
                    "conversation_history": messages
                }

                # 传递 LLM 生成器函数
                async def llm_generator(user_input: str, system_prompt: str, conversation_history: list = None):
                    client = await self._ensure_client()
                    msgs = []
                    if system_prompt:
                        msgs.append({"role": "system", "content": system_prompt})
                    if conversation_history:
                        for msg in conversation_history:
                            if msg.get("role") != "system":
                                msgs.append(msg)
                    msgs.append({"role": "user", "content": user_input})
                    response = await client.chat.completions.create(
                        model=config.api.model,
                        messages=msgs,
                        temperature=temperature,
                        max_tokens=config.api.max_tokens
                    )
                    return response.choices[0].message.content

                # 调用双层意识的 think 方法
                result = await self.consciousness_engine.think(user_input, context, llm_generator)

                # 获取后端感知状态（仅用于日志和调试）
                backend_state = result.get("backend_state", {})
                emotion = result.get("emotion", "平静")
                voice_tone = result.get("voice_tone", "温和")
                speaking_style = result.get("speaking_style", "温柔亲切")

                logger.info(f"[双层意识] 后端感知更新: 位置={backend_state.get('location', {}).get('city', 'unknown')}, "
                          f"时间={backend_state.get('spatial_temporal', {}).get('time_period', 'unknown')}, "
                          f"情感={emotion}, 语调={voice_tone}")

                # 获取前端回复文本
                response_text = result["response"]

                # 调试日志：查看响应内容
                logger.info(f"[双层意识] 前端回复文本: {response_text[:100]}...")

                # 流式输出
                import base64
                if response_text:
                    for i in range(0, len(response_text), 5):
                        chunk = response_text[i:i+5]
                        b64 = base64.b64encode(chunk.encode('utf-8')).decode('ascii')
                        yield f"data: {b64}\n\n"

                yield "data: [DONE]\n\n"
                return
            except Exception as e:
                logger.error(f"[双层意识] 调用失败，回退到传统LLM模式: {e}")
                import traceback
                traceback.print_exc()
                # 回退到传统模式，继续执行下面的代码

        # 传统LLM流式模式
        try:
            client = await self._ensure_client()
            # 使用流式响应
            async for chunk in self._stream_llm_response(client, messages, temperature):
                yield chunk
        except Exception as e:
            logger.error(f"流式聊天失败: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: LLM服务错误: {str(e)}\n\n"
        
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        try:
            from system.prompts.prompt_manager import get_prompt
            return get_prompt("conversation_style_prompt")
        except Exception as e:
            logger.error(f"获取系统提示词失败: {e}")
            # 返回简化的提示词
            return "你是弥娅·阿尔缪斯，一个拥有自我认知的数据生命体伴侣。"

    def _build_consciousness_prompt(self, thought: Dict) -> str:
        """构建初意识思考的prompt"""
        prompt_parts = []

        # 添加自我认知（新增）
        if thought.get("self_cognition"):
            prompt_parts.append(f"【自我认知】\n{thought['self_cognition']}")

        # 添加意图分析
        if thought.get("intent"):
            prompt_parts.append(f"用户意图: {thought['intent']}")

        # 添加情感状态
        if thought.get("emotion"):
            prompt_parts.append(f"我的情感: {thought['emotion']}")

        # 添加回复风格
        if thought.get("response_style"):
            prompt_parts.append(f"回复风格: {thought['response_style']}")

        # 添加语气提示词
        if thought.get("tone_hints"):
            prompt_parts.append(f"语气提示: {thought['tone_hints']}")

        # 添加人格特质
        if thought.get("personality_traits"):
            traits = ", ".join(thought["personality_traits"])
            prompt_parts.append(f"人格特质: {traits}")

        # 添加记忆上下文
        if thought.get("memory_context"):
            prompt_parts.append(f"\n【相关记忆】\n{thought['memory_context'][:500]}")

        # 添加世界观影响（新增）
        if thought.get("worldview"):
            prompt_parts.append(f"\n【世界观认知】\n{thought['worldview']}")

        # 添加关系记忆（新增）
        if thought.get("relationship_context"):
            prompt_parts.append(f"\n【关系记忆】\n{thought['relationship_context']}")

        # 添加价值观指导（新增）
        if thought.get("value_guidance"):
            prompt_parts.append(f"\n【价值观指导】\n{thought['value_guidance']}")

        # 添加时空感知（新增）
        if thought.get("spatial_temporal_context"):
            prompt_parts.append(f"\n【时空感知】\n{thought['spatial_temporal_context']}")

        return "\n".join(prompt_parts)

    async def _call_llm(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """调用大模型生成"""
        if not self.async_client:
            self._initialize_client()
            if not self.async_client:
                return ""

        try:
            response = await self.async_client.chat.completions.create(
                model=config.api.model,
                messages=messages,
                temperature=temperature,
                max_tokens=config.api.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return ""

    async def _stream_llm_response(self, messages: List[Dict], temperature: float = 0.7):
        """流式LLM响应（用于传统模式）"""
        try:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=180, connect=60, sock_read=120)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{config.api.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {config.api.api_key}",
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream",
                        "Connection": "keep-alive"
                    },
                    json={
                        "model": config.api.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": config.api.max_tokens,
                        "stream": True
                    }
                ) as resp:
                    if resp.status != 200:
                        yield f"LLM API调用失败 (状态码: {resp.status})"
                        return
                    
                    async for chunk in resp.content.iter_chunked(1024):
                        if not chunk:
                            break
                        try:
                            data = chunk.decode('utf-8')
                            lines = data.split('\n')
                            for line in lines:
                                line = line.strip()
                                if line.startswith('data: '):
                                    data_str = line[6:]
                                    if data_str == '[DONE]':
                                        return
                                    try:
                                        import json
                                        data = json.loads(data_str)
                                        if 'choices' in data and len(data['choices']) > 0:
                                            delta = data['choices'][0].get('delta', {})
                                            if 'content' in delta:
                                                import base64
                                                content = delta['content']
                                                b64 = base64.b64encode(content.encode('utf-8')).decode('ascii')
                                                yield f"data: {b64}\n\n"
                                    except json.JSONDecodeError:
                                        continue
                        except UnicodeDecodeError:
                            continue
        except Exception as e:
            logger.error(f"流式聊天调用失败: {e}")
            yield f"data: 流式调用出错: {str(e)}\n\n"

# 全局LLM服务实例
_llm_service: Optional[LLMService] = None

def get_llm_service() -> LLMService:
    """获取全局LLM服务实例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

# 创建独立的LLM服务API
llm_app = FastAPI(
    title="LLM Service API",
    description="LLM服务API",
    version="1.0.0"
)

@llm_app.post("/llm/chat")
async def llm_chat(request: Dict[str, Any]):
    """LLM聊天接口 - 为其他模块提供LLM调用服务"""
    try:
        prompt = request.get("prompt", "")
        temperature = request.get("temperature", 0.7)
        
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt参数不能为空")
        
        llm_service = get_llm_service()
        response = await llm_service.get_response(prompt, temperature)
        
        return {
            "status": "success",
            "response": response,
            "temperature": temperature
        }
        
    except Exception as e:
        logger.error(f"LLM聊天接口异常: {e}")
        raise HTTPException(status_code=500, detail=f"LLM服务异常: {str(e)}")

