#!/usr/bin/env python3
"""
NagaAgent API服务器
提供RESTful API接口访问NagaAgent功能
"""

import asyncio
import json
import sys
import traceback
import os
import logging
import uuid
import time
import threading
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, AsyncGenerator, Any, TypedDict, Union

# 类型定义：工具结果格式
class ToolResult(TypedDict):
    """工具执行结果的标准格式
    
    所有Undefined工具和MCP工具应遵循此返回格式
    """
    success: bool
    result: str

# 类型定义：回调payload格式
class CallbackPayload(TypedDict):
    """工具回调payload的标准格式"""
    session_id: str
    task_id: str
    result: Dict[str, Any]
    success: bool

# 类型定义：工具执行结果项
class ToolExecutionResult(TypedDict):
    """单个工具的执行结果"""
    tool: str
    success: bool
    result: Union[str, Dict[str, Any]]

# 在导入其他模块前先设置HTTP库日志级别
logging.getLogger("httpcore.http11").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore.connection").setLevel(logging.WARNING)

# 创建logger实例
logger = logging.getLogger(__name__)

# 去重缓存：防止工具回调重试导致重复显示AI回复
_task_callback_cache = set()  # 存储已处理的task_id

# 定期清理旧的任务ID缓存（保留最近1小时的）
def _cleanup_task_cache():
    """定期清理已过期的任务ID缓存"""
    global _task_callback_cache
    # 简单的清理策略：如果缓存过大，清空一半
    if len(_task_callback_cache) > 1000:
        _task_callback_cache = set(list(_task_callback_cache)[500:])
        logger.info(f"[工具回调] 已清理任务缓存，剩余: {len(_task_callback_cache)}")

    # 每小时执行一次清理
    threading.Timer(3600.0, _cleanup_task_cache).start()

# 启动清理任务
_cleanup_task_cache()

# 工具类型判断：决定工具执行结果是否需要发送给用户
def _should_send_result_to_user(tool_name: str) -> bool:
    """
    判断工具执行结果是否需要发送给用户

    需要发送的工具类型：
    - 信息搜集类：搜索、查询、读取等
    - 内容输出类：绘图、翻译、文本生成等

    不需要发送的工具类型（只记录日志）：
    - 记忆管理类：LifeBook、五元组记忆等
    - 任务管理类：创建任务、更新任务等
    - 系统控制类：启动应用、系统命令等
    - 屏幕控制类：包豆AI视觉自动化等
    """
    # 定义需要发送给用户的工具列表
    user_facing_tools = {
        # 信息搜集类
        "搜索", "web_search", "web_browse", "bilibili_search", "bilibili_user_info",
        "info_agent", "entertainment_agent", "get_current_time", "get_weather",

        # 内容输出类
        "ai_draw_one", "local_ai_draw", "render_and_send_image",
        "翻译", "translate", "summarize",

        # 其他面向用户的工具
        "音乐播放", "music_global_search", "music_info_get", "music_lyrics",
        "聊天", "chat",
    }

    # 明确定义不需要发送给用户的工具（后台工具）
    # 记忆管理
    if any(keyword in tool_name.lower() for keyword in ["记录日记", "write_diary", "读取记忆", "read_lifebook",
                                                      "创建节点", "create_node", "人生书", "lifebook"]):
        return False

    # 包豆AI视觉自动化
    if any(keyword in tool_name.lower() for keyword in ["baodou", "包豆", "capture_screen", "analyze_task",
                                                      "mouse_move", "mouse_click", "keyboard_type",
                                                      "keyboard_press"]):
        return False

    # 任务管理
    if any(keyword in tool_name.lower() for keyword in ["创建任务", "update_task", "任务管理"]):
        return False

    # 系统控制（启动应用除外，需要返回执行结果）
    if any(keyword in tool_name.lower() for keyword in ["系统控制", "system_control", "command"]):
        return False
    # 注意：启动应用需要返回执行结果，所以不在此处过滤

    # 检查工具名称是否在用户面向工具列表中
    for user_tool in user_facing_tools:
        if user_tool.lower() in tool_name.lower() or tool_name.lower() in user_tool.lower():
            return True

    # 默认不发送（只记录日志）
    return False

from nagaagent_core.api import uvicorn
from nagaagent_core.api import FastAPI, HTTPException, Request, UploadFile, File, Form
from nagaagent_core.api import CORSMiddleware
from nagaagent_core.api import StreamingResponse
from nagaagent_core.api import StaticFiles
from nagaagent_core.api import HTMLResponse
from pydantic import BaseModel
from nagaagent_core.core import aiohttp
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 流式文本处理模块（仅用于TTS）
from .message_manager import message_manager  # 导入统一的消息管理器

from .llm_service import get_llm_service  # 导入LLM服务

# 导入配置系统
try:
    from system.config import config, AI_NAME  # 使用新的配置系统
    from system.config import get_prompt  # 导入提示词仓库
except ImportError:
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from system.config import config, AI_NAME  # 使用新的配置系统
    from system.config import get_prompt  # 导入提示词仓库
from ui.utils.response_util import extract_message  # 导入消息提取工具

# 任务调度系统
try:
    from system.task_service_manager import get_task_service_manager
    _task_service_available = True
except ImportError:
    _task_service_available = False
    logger.warning("[任务调度] 任务服务模块不可用，提醒功能将不可用")

# 对话核心功能已集成到apiserver


# 统一后台意图分析触发函数 - 已整合到message_manager
def _trigger_background_analysis(session_id: str):
    """统一触发后台意图分析 - 委托给message_manager"""
    message_manager.trigger_background_analysis(session_id)


# 统一保存对话与日志函数 - 已整合到message_manager
def _save_conversation_and_logs(session_id: str, user_message: str, assistant_response: str):
    """统一保存对话历史与日志 - 委托给message_manager"""
    message_manager.save_conversation_and_logs(session_id, user_message, assistant_response)


# 回调工厂类已移除 - 功能已整合到streaming_tool_extractor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    try:
        print("[INFO] 正在初始化API服务器...")
        # 对话核心功能已集成到apiserver
        print("[SUCCESS] API服务器初始化完成")
        yield
    except Exception as e:
        print(f"[ERROR] API服务器初始化失败: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("[INFO] 正在清理资源...")
        # MCP服务现在由mcpserver独立管理，无需清理


# 创建FastAPI应用
app = FastAPI(title="NagaAgent API", description="智能对话助手API服务", version="4.0.0", lifespan=lifespan)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# 请求模型
class ChatRequest(BaseModel):
    message: str
    stream: bool = False
    session_id: Optional[str] = None
    use_self_game: bool = False
    disable_tts: bool = False  # V17: 支持禁用服务器端TTS
    return_audio: bool = False  # V19: 支持返回音频URL供客户端播放
    skip_intent_analysis: bool = False  # 新增：跳过意图分析
    chat_context: Optional[dict] = None  # 新增：聊天上下文（群聊/私聊信息）


class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str] = None
    status: str = "success"


class SystemInfoResponse(BaseModel):
    version: str
    status: str
    available_services: List[str]
    api_key_configured: bool


class FileUploadResponse(BaseModel):
    filename: str
    file_path: str
    file_size: int
    file_type: str
    upload_time: str
    status: str = "success"
    message: str = "文件上传成功"


class DocumentProcessRequest(BaseModel):
    file_path: str
    action: str = "read"  # read, analyze, summarize
    session_id: Optional[str] = None


class QQIntentAnalysisRequest(BaseModel):
    session_id: str
    message: str
    ai_response: str
    sender_id: Optional[str] = None  # 发送者ID（QQ号）
    message_type: Optional[str] = "private"  # 消息类型：private 或 group
    group_id: Optional[str] = None  # 群ID（群聊时使用）
    image_path: Optional[str] = None  # 图片路径（用于视觉识别）


# API路由
@app.get("/", response_class=HTMLResponse)
async def root():
    """API根路径 - 重定向到移动端聊天界面"""
    html_path = os.path.join(static_dir, "mobile_chat.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            content=f"""
        <!DOCTYPE html>
        <html>
        <head><title>NagaAgent</title></head>
        <body>
            <h1>NagaAgent API</h1>
            <p>API服务器正在运行</p>
            <p><a href="/docs">查看API文档</a></p>
            <p><a href="/static/mobile_chat.html">移动端聊天</a></p>
        </body>
        </html>
        """
        )


@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    """聊天页面"""
    html_path = os.path.join(static_dir, "mobile_chat.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(content="<h1>聊天页面未找到</h1>", status_code=404)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "agent_ready": True, "timestamp": str(asyncio.get_event_loop().time())}


@app.get("/system/info", response_model=SystemInfoResponse)
async def get_system_info():
    """获取系统信息"""

    return SystemInfoResponse(
        version="4.0.0",
        status="running",
        available_services=[],  # MCP服务现在由mcpserver独立管理
        api_key_configured=bool(config.api.api_key and config.api.api_key != "sk-placeholder-key-not-set"),
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """普通对话接口 - 仅处理纯文本对话"""

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    try:
        # 先检查是否是任务相关的请求
        if _task_service_available:
            try:
                from system.task_service_manager import get_task_service_manager
                task_service = get_task_service_manager()
                
                # 处理用户输入
                result = await task_service.process_user_input(request.message)
                
                if result and result.get("success"):
                    # 是任务相关，直接返回响应
                    # 保存对话历史
                    session_id = message_manager.create_session(request.session_id)
                    _save_conversation_and_logs(session_id, request.message, result["response"])
                    
                    # 触发后台分析
                    if not request.skip_intent_analysis:
                        _trigger_background_analysis(session_id=session_id)
                    
                    return ChatResponse(
                        response=result["response"],
                        session_id=session_id,
                        status="success"
                    )
            except Exception as e:
                logger.warning(f"[任务调度] 处理任务请求失败: {e}")
                # 继续正常对话流程
        
        # 分支: 启用博弈论流程（非流式，返回聚合文本）
        if request.use_self_game:
            # 配置项控制：失败时可跳过回退到普通对话 #
            skip_on_error = getattr(getattr(config, "game", None), "skip_on_error", True)  # 兼容无配置情况 #
            enabled = getattr(getattr(config, "game", None), "enabled", False)  # 控制总开关 #
            if enabled:
                try:
                    # 延迟导入以避免启动时循环依赖 #
                    from game.naga_game_system import NagaGameSystem  # 博弈系统入口 #
                    from game.core.models.config import GameConfig  # 博弈系统配置 #

                    # 创建系统并执行用户问题处理 #
                    system = NagaGameSystem(GameConfig())
                    system_response = await system.process_user_question(
                        user_question=request.message, user_id=request.session_id or "api_user"
                    )
                    return ChatResponse(
                        response=system_response.content, session_id=request.session_id, status="success"
                    )
                except Exception as e:
                    print(
                        f"[WARNING] 博弈论流程失败，将{'回退到普通对话' if skip_on_error else '返回错误'}: {e}"
                    )  # 运行时警告 #
                    if not skip_on_error:
                        raise HTTPException(status_code=500, detail=f"博弈论流程失败: {str(e)}")
                    # 否则继续走普通对话流程 #
            # 若未启用或被配置跳过，则直接回退到普通对话分支 #

        # 获取或创建会话ID
        session_id = message_manager.create_session(request.session_id)

        # 构建系统提示词（只使用对话风格提示词）
        system_prompt = get_prompt("conversation_style_prompt")

        # 使用消息管理器构建完整的对话消息（纯聊天，不触发工具）
        messages = message_manager.build_conversation_messages(
            session_id=session_id, system_prompt=system_prompt, current_message=request.message,
            chat_context=request.chat_context
        )

        # 使用整合后的LLM服务
        llm_service = get_llm_service()
        response_text = await llm_service.chat_with_context(messages, config.api.temperature)

        # 处理语音（非流式模式）
        if config.system.voice_enabled and not request.disable_tts and config.voice_realtime.voice_mode != "hybrid":
            try:
                from voice.output.voice_integration import get_voice_integration

                voice_integration = get_voice_integration()
                voice_integration.receive_final_text(response_text)
                # 检查是否是QQ消息，用于日志记录
                is_qq_message = session_id and session_id.startswith('qq_')
                location = "电脑端和QQ端" if is_qq_message else "电脑端"
                logger.info(f"[API Server] 非流式模式：语音集成已收到完整文本，播放位置: {location}，长度: {len(response_text)}")
            except Exception as e:
                logger.error(f"[API Server] 非流式语音处理失败: {e}")

        # 处理完成
        # 统一保存对话历史与日志
        _save_conversation_and_logs(session_id, request.message, response_text)

        # 在用户消息保存到历史后触发后台意图分析（除非明确跳过）
        if not request.skip_intent_analysis:
            _trigger_background_analysis(session_id=session_id)

        return ChatResponse(
            response=extract_message(response_text) if response_text else response_text,
            session_id=session_id,
            status="success",
        )
    except Exception as e:
        print(f"对话处理错误: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式对话接口 - 流式文本处理交给streaming_tool_extractor用于TTS"""

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    async def generate_response() -> AsyncGenerator[str, None]:
        complete_text = ""  # V19: 用于累积完整文本以生成音频
        # 创建任务列表，用于等待所有文本块处理完成
        processing_tasks = []
        try:
            # 先检查是否是任务相关的请求
            if _task_service_available:
                try:
                    from system.task_service_manager import get_task_service_manager
                    task_service = get_task_service_manager()

                    # 处理用户输入
                    result = await task_service.process_user_input(request.message)

                    logger.info(f"[API Server 流式] 任务检查结果: {result}")

                    if result and result.get("success"):
                        # 是任务相关，直接返回响应
                        logger.info(f"[API Server 流式] 识别为任务意图: {result.get('intent_type')}")

                        # 创建会话ID并保存对话
                        session_id = message_manager.create_session(request.session_id)
                        yield f"data: session_id: {session_id}\n\n"

                        # 返回任务响应
                        response_text = result["response"]

                        # 流式输出任务响应
                        import base64
                        for i in range(0, len(response_text), 5):
                            chunk = response_text[i:i+5]
                            b64 = base64.b64encode(chunk.encode('utf-8')).decode('ascii')
                            yield f"data: {b64}\n\n"

                        # 如果需要返回音频，生成音频
                        if request.return_audio:
                            try:
                                logger.info(f"[API Server V19] 任务响应生成音频，文本长度: {len(response_text)}")

                                from voice.output.voice_integration import VoiceIntegration
                                voice_integration = VoiceIntegration()
                                audio_data = voice_integration._generate_audio_sync(response_text)

                                if audio_data:
                                    import uuid
                                    temp_dir = "logs/audio_temp"
                                    os.makedirs(temp_dir, exist_ok=True)
                                    audio_file = os.path.join(temp_dir, f"tts_{uuid.uuid4().hex}.mp3")

                                    with open(audio_file, "wb") as f:
                                        f.write(audio_data)

                                    logger.info(f"[API Server V19] 任务音频生成成功: {audio_file}")
                                    yield f"data: audio_url: {audio_file}\n\n"

                                    # 播放给UI端
                                    is_qq_message = session_id and session_id.startswith('qq_')
                                    is_tool_callback = request.skip_intent_analysis or ("[工具结果]" in response_text)
                                    if not is_tool_callback:
                                        try:
                                            voice_integration.receive_audio_url(audio_file)
                                            ui_location = "电脑端和QQ端都播放" if is_qq_message else "UI端播放"
                                            logger.info(f"[API Server V19] 任务音频已发送到{ui_location}")
                                        except Exception as e:
                                            logger.error(f"[API Server V19] UI端音频播放失败: {e}")
                            except Exception as e:
                                logger.error(f"[API Server V19] 任务音频生成失败: {e}")

                        # 保存对话历史
                        _save_conversation_and_logs(session_id, request.message, response_text)

                        # 触发后台分析
                        if not request.skip_intent_analysis:
                            _trigger_background_analysis(session_id)

                        yield "data: [DONE]\n\n"
                        return
                except Exception as e:
                    logger.warning(f"[任务调度] 流式任务检查失败: {e}")
                    import traceback
                    traceback.print_exc()
                    # 继续正常对话流程

            # 获取或创建会话ID
            session_id = message_manager.create_session(request.session_id)

            # 发送会话ID信息
            yield f"data: session_id: {session_id}\n\n"

            # 注意：这里不触发后台分析，将在对话保存后触发

            # 构建系统提示词（只使用对话风格提示词）
            system_prompt = get_prompt("conversation_style_prompt")

            # 使用消息管理器构建完整的对话消息
            messages = message_manager.build_conversation_messages(
                session_id=session_id, system_prompt=system_prompt, current_message=request.message,
                chat_context=request.chat_context
            )

            # 初始化语音集成（根据voice_mode和return_audio决定）
            # V19: 如果客户端请求返回音频，则在服务器端生成
            voice_integration = None

            # 检查是否是QQ消息 - 用于区分日志记录和音频播放策略
            is_qq_message = session_id and session_id.startswith('qq_')

            # V19: 混合模式下，如果请求return_audio，则在服务器生成音频
            # 修复：非流式模式也需要启用TTS，通过receive_final_text接收完整文本
            # 修改：QQ消息也启用TTS，让电脑端和QQ端都能播放语音
            should_enable_tts = (
                config.system.voice_enabled
                and config.voice_realtime.voice_mode != "hybrid"
                and not request.disable_tts  # 兼容旧版本的disable_tts
            )

            if should_enable_tts:
                if is_qq_message:
                    logger.info("[API Server] QQ消息，启用TTS处理（电脑端+QQ端都播放）")
            elif should_enable_tts:
                try:
                    from voice.output.voice_integration import get_voice_integration

                    voice_integration = get_voice_integration()
                    logger.info(
                        f"[API Server] 语音集成已启用 (stream={request.stream}, return_audio={request.return_audio}, voice_mode={config.voice_realtime.voice_mode})"
                    )
                except Exception as e:
                    print(f"语音集成初始化失败: {e}")
            else:
                if config.voice_realtime.voice_mode == "hybrid":
                    logger.info("[API Server] 混合模式，不处理TTS")
                elif request.disable_tts:
                    logger.info("[API Server] 客户端禁用了TTS (disable_tts=True)")
                elif not config.system.voice_enabled:
                    logger.info("[API Server] 语音功能未启用")

            # 初始化流式文本切割器（仅用于TTS处理）
            # 始终创建tool_extractor以累积文本内容，确保日志保存
            tool_extractor = None
            try:
                from .streaming_tool_extractor import StreamingToolCallExtractor

                tool_extractor = StreamingToolCallExtractor()
                # 流式模式：实时TTS；非流式模式：仅在最后处理完整文本
                if voice_integration and request.stream:
                    tool_extractor.set_callbacks(
                        on_text_chunk=None,  # 不需要回调，直接处理TTS
                        voice_integration=voice_integration,
                    )
            except Exception as e:
                print(f"流式文本切割器初始化失败: {e}")

            # 使用整合后的流式处理
            llm_service = get_llm_service()
            async for chunk in llm_service.stream_chat_with_context(messages, config.api.temperature):
                # V19: 如果需要返回音频，累积文本
                if request.return_audio and chunk.startswith("data: "):
                    try:
                        import base64

                        data_str = chunk[6:].strip()
                        if data_str != "[DONE]":
                            decoded = base64.b64decode(data_str).decode("utf-8")
                            complete_text += decoded
                    except Exception:
                        pass

                # 立即发送到流式文本切割器进行TTS处理（不阻塞文本流）
                if tool_extractor and chunk.startswith("data: "):
                    try:
                        import base64

                        data_str = chunk[6:].strip()
                        if (
                            data_str != "[DONE]"
                            and not data_str.startswith("session_id:")
                            and not data_str.startswith("audio_url:")
                        ):
                            # LLM服务已经对内容进行了base64编码，需要解码
                            decoded = base64.b64decode(data_str).decode("utf-8")
                            # 异步调用TTS处理，不阻塞文本流
                            task = asyncio.create_task(tool_extractor.process_text_chunk(decoded))
                            processing_tasks.append(task)
                    except Exception as e:
                        logger.error(f"[API Server] 流式文本切割器处理错误: {e}")

                yield chunk

            # 处理完成

            # V19: 如果请求返回音频，在这里生成并返回音频URL
            if request.return_audio and complete_text:
                try:
                    logger.info(f"[API Server V19] 生成音频，文本长度: {len(complete_text)}")

                    # 使用voice_integration生成音频（支持GPT-SoVITS）
                    from voice.output.voice_integration import VoiceIntegration

                    voice_integration = VoiceIntegration()

                    # 生成音频数据
                    audio_data = voice_integration._generate_audio_sync(complete_text)

                    if not audio_data:
                        logger.warning(f"[API Server V19] 语音生成返回空数据")
                        return

                    # 保存音频文件
                    import uuid

                    temp_dir = "logs/audio_temp"
                    os.makedirs(temp_dir, exist_ok=True)
                    audio_file = os.path.join(temp_dir, f"tts_{uuid.uuid4().hex}.mp3")

                    with open(audio_file, "wb") as f:
                        f.write(audio_data)

                    logger.info(f"[API Server V19] 音频生成成功: {audio_file}, 大小: {len(audio_data)} bytes")

                    # 总是返回audio_url给客户端，让客户端决定是否播放
                    yield f"data: audio_url: {audio_file}\n\n"
                    logger.info(f"[API Server V19] 音频URL已返回给客户端: {audio_file}")

                    # 播放给UI端（电脑端）
                    # QQ消息和非QQ消息都播放给电脑端，让两边都能听到
                    is_tool_callback = request.skip_intent_analysis or ("[工具结果]" in complete_text)
                    if not is_tool_callback:
                        try:
                            voice_integration.receive_audio_url(audio_file)
                            logger.info(f"[API Server V19] 音频已发送到UI端: {audio_file}")
                        except Exception as e:
                            logger.error(f"[API Server V19] UI端音频播放失败: {e}")
                    else:
                        reason = "工具回调" if is_tool_callback else "其他"
                        logger.info(f"[API Server V19] {reason}模式，跳过UI端音频播放")

                except Exception as e:
                    logger.error(f"[API Server V19] 音频生成失败: {e}")
                    # traceback已经在文件顶部导入，直接使用
                    traceback.print_exc()

            # 非流式模式：通过voice_integration的receive_final_text处理完整文本
            if voice_integration and not request.stream:
                try:
                    logger.info(f"[API Server] 非流式模式，发送完整文本到语音系统: {len(complete_text)}字符")
                    voice_integration.receive_final_text(complete_text)
                except Exception as e:
                    logger.error(f"[API Server] 非流式语音处理失败: {e}")

            # 完成流式文本切割器处理（仅流式模式）
            if tool_extractor and request.stream:
                try:
                    # 1. 等待所有文本块处理任务完成（确保文本完整累积）
                    if processing_tasks:
                        await asyncio.gather(*processing_tasks, return_exceptions=True)
                    # 2. 将剩余文本发送到voice_integration中的缓冲区
                    await tool_extractor.finish_processing()
                    pass
                except Exception as e:
                    print(f"流式文本切割器完成处理错误: {e}")

            # 完成语音处理（仅流式模式）
            if voice_integration and request.stream:  # 非流式模式已在前面处理
                try:
                    threading.Thread(target=voice_integration.finish_processing, daemon=True).start()
                except Exception as e:
                    print(f"语音集成完成处理错误: {e}")

            # 流式处理完成后，获取完整文本用于保存
            complete_response = ""
            if tool_extractor:
                try:
                    # 获取完整文本内容
                    complete_response = tool_extractor.get_complete_text()
                except Exception as e:
                    print(f"获取完整响应文本失败: {e}")
            elif request.return_audio:
                # V19: 如果是return_audio模式，使用累积的文本
                complete_response = complete_text

            # 统一保存对话历史与日志
            _save_conversation_and_logs(session_id, request.message, complete_response)

            # 在用户消息保存到历史后触发后台意图分析（除非明确跳过）
            if not request.skip_intent_analysis:
                _trigger_background_analysis(session_id)

            yield "data: [DONE]\n\n"

        except Exception as e:
            print(f"流式对话处理错误: {e}")
            # 使用顶部导入的traceback
            traceback.print_exc()
            yield f"data: 错误: {str(e)}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "X-Accel-Buffering": "no",  # 禁用nginx缓冲
        },
    )


@app.get("/memory/stats")
async def get_memory_stats():
    """获取记忆统计信息"""

    try:
        # 记忆系统现在由main.py直接管理
        try:
            from summer_memory.memory_manager import memory_manager

            if memory_manager and memory_manager.enabled:
                stats = memory_manager.get_memory_stats()
                return {"status": "success", "memory_stats": stats}
            else:
                return {"status": "success", "memory_stats": {"enabled": False, "message": "记忆系统未启用"}}
        except ImportError:
            return {"status": "success", "memory_stats": {"enabled": False, "message": "记忆系统模块未找到"}}
    except Exception as e:
        print(f"获取记忆统计错误: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取记忆统计失败: {str(e)}")


@app.get("/sessions")
async def get_sessions():
    """获取所有会话信息 - 委托给message_manager"""
    try:
        return message_manager.get_all_sessions_api()
    except Exception as e:
        print(f"获取会话信息错误: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}")
async def get_session_detail(session_id: str):
    """获取指定会话的详细信息 - 委托给message_manager"""
    try:
        return message_manager.get_session_detail_api(session_id)
    except Exception as e:
        if "会话不存在" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        print(f"获取会话详情错误: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除指定会话 - 委托给message_manager"""
    try:
        return message_manager.delete_session_api(session_id)
    except Exception as e:
        if "会话不存在" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        print(f"删除会话错误: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions")
async def clear_all_sessions():
    """清空所有会话 - 委托给message_manager"""
    try:
        return message_manager.clear_all_sessions_api()
    except Exception as e:
        print(f"清空会话错误: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload/document", response_model=FileUploadResponse)
async def upload_document(file: UploadFile = File(...), description: str = Form(None)):
    """上传文档接口"""
    try:
        # 确保上传目录存在
        upload_dir = Path("uploaded_documents")
        upload_dir.mkdir(exist_ok=True)

        # 使用原始文件名
        filename = file.filename
        file_path = upload_dir / filename

        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 获取文件信息
        stat = file_path.stat()

        return FileUploadResponse(
            filename=filename,
            file_path=str(file_path.absolute()),
            file_size=stat.st_size,
            file_type=file_path.suffix,
            upload_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
        )
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@app.post("/qq/analyze_intent")
async def qq_analyze_intent(request: QQIntentAnalysisRequest):
    """
    QQ专用意图分析接口 - 同步执行工具调用并返回结果

    这个接口专为QQ聊天设计，提供同步的工具调用机制：
    1. 执行意图分析，识别需要调用的MCP工具
    2. 同步等待工具执行完成
    3. 直接返回工具执行结果

    Args:
        request: 包含session_id、message和ai_response的请求

    Returns:
        工具执行结果
    """
    try:
        logger.info(f"[QQ分析] 收到意图分析请求，会话: {request.session_id}")

        # 保存对话到会话历史（使用批量添加避免中间截断）
        message_manager.add_message_pair(request.session_id, request.message, request.ai_response)

        # 获取最近对话历史
        from system.background_analyzer import get_background_analyzer
        from system.config import config

        background_analyzer = get_background_analyzer()

        # 获取所有消息，然后取最后N条，确保包含当前对话
        all_messages = message_manager.get_messages(request.session_id)
        intent_rounds = getattr(config.api, "intent_analysis_rounds", config.api.max_history_rounds)
        max_messages = intent_rounds * 2
        recent_messages = all_messages[-max_messages:] if len(all_messages) > max_messages else all_messages

        # 调试：打印会话中的消息数量和最近消息数量
        logger.info(f"[QQ分析] 会话总消息数: {len(all_messages)}, 获取最近消息数: {len(recent_messages)}")
        if recent_messages:
            logger.info(f"[QQ分析] 最早消息: {recent_messages[0]['content'][:50]}...")
            logger.info(f"[QQ分析] 最新消息: {recent_messages[-1]['content'][:50]}...")
            # 打印最后5条消息的详细内容
            logger.info(f"[QQ分析] 最后5条消息:")
            for i, msg in enumerate(recent_messages[-5:]):
                role = msg.get('role', 'unknown')
                content_preview = msg.get('content', '')[:60].replace('\n', ' ')
                logger.info(f"  {i+1}. [{role}] {content_preview}...")

        logger.info(f"[QQ分析] 开始分析对话...")

        # 执行意图分析（同步等待工具结果）
        analysis = await _analyze_intent_sync(recent_messages, request.session_id)

        if analysis and analysis.get("tool_calls"):
            # 找到了工具调用，同步执行并等待结果
            logger.info(f"[QQ分析] 发现 {len(analysis['tool_calls'])} 个工具调用，开始执行...")

            # 同步执行MCP工具调用，传递QQ相关参数和图片路径
            tool_result = await _execute_mcp_tool_sync(
                analysis["tool_calls"],
                request.session_id,
                request.sender_id,
                request.message_type,
                request.group_id,
                request.image_path,
            )

            if tool_result:
                return {
                    "status": "success",
                    "tool_executed": True,
                    "tool_name": tool_result.get("tool_name", "未知"),
                    "result": tool_result.get("result", ""),
                    "success": tool_result.get("success", True),
                }
            else:
                return {"status": "success", "tool_executed": False, "message": "工具执行失败或超时"}
        elif analysis and analysis.get("no_tool"):
            # 检测到无工具调用（闲聊/情感交流）
            logger.info(f"[QQ分析] 无工具调用，AI直接回复即可")
            return {
                "status": "success",
                "tool_executed": False,
                "no_tool": True,
                "output_mode": analysis.get("output_mode", "normal"),
                "reply_style": analysis.get("reply_style", "helpful"),
                "message": "无需工具调用"
            }
        else:
            # 没有发现工具调用
            return {"status": "success", "tool_executed": False, "message": "未发现需要执行的工具"}

    except Exception as e:
        logger.error(f"[QQ分析] 意图分析失败: {e}", exc_info=True)
        return {"status": "error", "tool_executed": False, "message": str(e)}


async def _analyze_intent_sync(messages: List[Dict[str, str]], session_id: str) -> Optional[Dict]:
    """同步执行意图分析"""
    try:
        from system.background_analyzer import get_background_analyzer

        background_analyzer = get_background_analyzer()

        # 使用内部的analyzer直接执行分析（不触发工具调度）
        import asyncio

        loop = asyncio.get_running_loop()

        try:
            analysis = await asyncio.wait_for(
                loop.run_in_executor(None, background_analyzer.analyzer.analyze, messages), timeout=30.0
            )
            logger.info(f"[QQ分析] 意图分析完成: {analysis.get('tool_calls', [])}")

            # 检查是否为无工具调用情况（agentType: "none"）
            if analysis.get('tool_calls'):
                tool_call = analysis['tool_calls'][0]
                if tool_call.get('agentType') == 'none':
                    logger.info(f"[QQ分析] 检测到无工具调用，输出模式: {tool_call.get('output_mode')}, 回复风格: {tool_call.get('reply_style')}")
                    # 返回分析结果，但标记为不执行工具
                    return {
                        'tool_calls': [],
                        'no_tool': True,
                        'output_mode': tool_call.get('output_mode', 'normal'),
                        'reply_style': tool_call.get('reply_style', 'helpful')
                    }

            return analysis
        except asyncio.TimeoutError:
            logger.error(f"[QQ分析] 意图分析超时")
            return None
        except Exception as e:
            logger.error(f"[QQ分析] 意图分析失败: {e}")
            return None

    except Exception as e:
        logger.error(f"[QQ分析] 分析意图失败: {e}")
        return None


@app.post("/qq/send_media")
async def qq_send_media(request: dict):
    """发送媒体消息（图片/视频）到QQ"""
    try:
        sender_id = request.get("sender_id")
        message_type = request.get("message_type", "private")
        group_id = request.get("group_id")
        file_path = request.get("file_path")
        media_type = request.get("media_type", "image")

        if not sender_id or not file_path:
            return {"status": "error", "message": "缺少必要参数"}

        # 获取 MCP 服务
        from mcpserver.mcp_registry import get_service_info

        service_info = get_service_info("QQ/微信集成")
        if not service_info:
            return {"status": "error", "message": "QQ服务未注册"}

        agent = service_info.get("instance")
        if not agent or not hasattr(agent, "message_listener"):
            return {"status": "error", "message": "QQ服务未初始化或缺少message_listener"}

        message_listener = agent.message_listener
        if not message_listener:
            return {"status": "error", "message": "message_listener未初始化"}

        # 使用message_listener发送媒体消息
        try:
            await message_listener._send_qq_reply(message_type, sender_id, group_id, file_path, media_type)
            logger.info(f"[QQ发送媒体] 成功发送 {media_type} 到 {message_type} {sender_id}: {file_path}")
            return {"status": "success", "message": "媒体发送成功"}
        except Exception as send_error:
            logger.error(f"[QQ发送媒体] 发送失败: {send_error}", exc_info=True)
            return {"status": "error", "message": f"发送失败: {str(send_error)}"}

    except Exception as e:
        logger.error(f"[QQ发送媒体] 失败: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


async def _execute_mcp_tool_sync(
    tool_calls: List[Dict[str, Any]],
    session_id: str,
    sender_id: Optional[str] = None,
    message_type: str = "private",
    group_id: Optional[str] = None,
    image_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """同步执行MCP工具调用 - 通过MCP服务器API调用，支持批量执行"""
    try:
        if not tool_calls:
            return None

        # 🔄 支持批量执行 - 复合操作处理
        if len(tool_calls) > 1:
            logger.info(f"[批量MCP] 检测到复合操作，共 {len(tool_calls)} 个步骤")
            return await _execute_batch_mcp_tools(
                tool_calls, session_id, sender_id, message_type, group_id, image_path
            )

        # 单个工具调用（保持向后兼容）
        tool_call = tool_calls[0]
        service_name = tool_call.get("service_name")
        tool_name = tool_call.get("tool_name")

        # 获取参数 - 兼容两种格式:
        # 1. 标准格式: {"parameters": {"prompt": "..."}}
        # 2. 简化格式(意图分析器): {"param_name": "...", "tool_name": "..."}
        parameters = tool_call.get("parameters", {})

        # 如果parameters为空,检查tool_call中是否有直接的参数字段
        if not parameters:
            parameters = {}
            for key, value in tool_call.items():
                if key not in ["agentType", "service_name", "tool_name", "parameters"]:
                    parameters[key] = value

        logger.info(
            f"[QQ工具] 执行MCP工具: {service_name}.{tool_name}, 原始参数: {list(tool_call.keys())}, 处理后参数: {list(parameters.keys())}"
        )

        # 智能参数映射：根据工具类型映射不同的参数字段
        # 系统控制服务：param_name -> command
        if service_name == "系统控制服务" and tool_name == "command":
            if "param_name" in parameters and "command" not in parameters:
                parameters["command"] = parameters.pop("param_name")
                logger.info(f"[QQ工具] 参数映射: param_name -> command = {parameters['command']}")
        # 应用启动服务：param_name -> app
        elif service_name == "应用启动服务" and tool_name == "启动应用":
            if "param_name" in parameters and "app" not in parameters:
                parameters["app"] = parameters.pop("param_name")
                logger.info(f"[QQ工具] 参数映射: param_name -> app = {parameters['app']}")
        # QQ点赞工具：直接调用以传递回调函数
        elif service_name == "Undefined工具集" and tool_name == "qq_like":
            # 直接调用 AgentUndefined，绕过 MCP 调度器，以便传递 context
            from mcpserver.mcp_registry import get_service_info

            service_info = get_service_info("Undefined工具集")
            if service_info:
                agent = service_info.get("instance")
                if agent:
                    # 构建QQ回调函数
                    async def send_like_callback(user_id: int, times: int = 1):
                        try:
                            logger.info(f"[QQ工具 send_like_callback] 点赞: user_id={user_id}, times={times}")
                            # 获取QQ adapter并执行点赞
                            qq_service = get_service_info("QQ/微信集成")
                            if qq_service:
                                qq_agent = qq_service.get("instance")
                                if qq_agent and hasattr(qq_agent, 'qq_adapter'):
                                    await qq_agent.qq_adapter.send_like(user_id, times)
                                    logger.info(f"[QQ工具 send_like_callback] 点赞成功")
                        except Exception as e:
                            logger.error(f"[QQ工具 send_like_callback] 失败: {e}", exc_info=True)

                    tool_context = {"send_like_callback": send_like_callback}
                    # 参数映射: user_id -> target_user_id
                    if "user_id" in parameters:
                        parameters["target_user_id"] = parameters.pop("user_id")
                    result = await agent.call_tool(tool_name, parameters)
                    logger.info(f"[QQ工具] qq_like直接调用结果: {result[:100]}...")
                    return {"tool_name": tool_name, "result": result, "success": True}
        # 绘图工具：param_name -> prompt
        elif tool_name in ["ai_draw_one", "local_ai_draw", "render_and_send_image"]:
            if sender_id:
                parameters["target_id"] = int(sender_id)
            parameters["message_type"] = message_type
            if group_id:
                parameters["group_id"] = int(group_id)
            logger.info(f"[QQ工具] 为绘图工具添加QQ参数: target_id={sender_id}, message_type={message_type}")

            if "param_name" in parameters and "prompt" not in parameters:
                parameters["prompt"] = parameters.pop("param_name")
                logger.info(f"[QQ工具] 参数映射: param_name -> prompt = {parameters['prompt'][:50]}...")
            # 同时兼容旧的 parameters 格式
            if "parameters" in parameters and isinstance(parameters["parameters"], dict):
                inner_params = parameters["parameters"]
                if "param_name" in inner_params:
                    inner_params["prompt"] = inner_params.pop("param_name")
                # 将内层参数提升到外层
                parameters.update(inner_params)
                parameters.pop("parameters")

            # 直接调用 AgentUndefined，绕过 MCP 调度器，以便传递 context
            from mcpserver.mcp_registry import get_service_info

            service_info = get_service_info("Undefined工具集")
            if service_info:
                agent = service_info.get("instance")
                if agent:
                    # 构建 send_image_callback
                    async def send_image_callback(target_id: int, msg_type: str, file_path: str):
                        try:
                            logger.info(
                                f"[QQ工具 send_image_callback] 发送图片: target_id={target_id}, msg_type={msg_type}, file_path={file_path}"
                            )
                            import httpx
                            from system.config import get_server_port

                            http_url = f"http://localhost:{get_server_port('api_server')}/qq/send_media"
                            payload = {
                                "sender_id": str(target_id),
                                "message_type": msg_type,
                                "group_id": str(group_id) if group_id else None,
                                "file_path": file_path,
                                "media_type": "image",
                            }
                            async with httpx.AsyncClient(timeout=10.0) as client:
                                response = await client.post(http_url, json=payload)
                                logger.info(f"[QQ工具 send_image_callback] 响应: {response.status_code}")
                        except Exception as e:
                            logger.error(f"[QQ工具 send_image_callback] 失败: {e}", exc_info=True)

                    tool_context = {"send_image_callback": send_image_callback}
                    result = await agent.call_tool(tool_name, parameters, context=tool_context)

                    # 安全地处理result日志（处理dict和str类型）
                    if isinstance(result, dict):
                        result_str = str(result)
                        logger.info(f"[QQ工具] 直接调用结果: {result_str[:100]}...")
                    elif isinstance(result, str):
                        logger.info(f"[QQ工具] 直接调用结果: {result[:100]}...")
                    else:
                        logger.info(f"[QQ工具] 直接调用结果: {type(result)}...")
                    return {"tool_name": tool_name, "result": result, "success": True}

        # 为视觉识别工具处理图片路径
        if tool_name == "vision_pipeline":
            # 直接使用传入的 image_path 参数（如果有）
            if image_path:
                parameters["filename"] = image_path
                logger.info(f"[QQ工具] 为vision_pipeline添加图片路径: {parameters['filename']}")
            else:
                # 如果没有提供 image_path，从会话历史中查找（兼容旧逻辑）
                try:
                    all_messages = message_manager.get_recent_messages(session_id, count=10)
                    for msg in reversed(all_messages):
                        if msg.get("role") == "user" and "[图片分析]" in msg.get("content", ""):
                            # 查找最近的图片路径记录（保存在img/temp目录下）
                            import os
                            from pathlib import Path

                            temp_dir = Path.cwd() / "img" / "temp"
                            if temp_dir.exists():
                                # 获取最新的图片文件
                                image_files = list(temp_dir.glob(f"qq_{sender_id}_*.jpg")) + list(
                                    temp_dir.glob(f"qq_{sender_id}_*.png")
                                )
                                if image_files:
                                    # 按修改时间排序，取最新的
                                    latest_image = max(image_files, key=lambda p: p.stat().st_mtime)
                                    parameters["filename"] = str(latest_image)
                                    logger.info(
                                        f"[QQ工具] 为vision_pipeline从历史添加图片路径: {parameters['filename']}"
                                    )
                            break
                except Exception as e:
                    logger.warning(f"[QQ工具] 从历史获取图片路径失败: {e}")

            # 参数映射: param_name -> user_content (兼容意图分析器的输出)
            if "param_name" in parameters and "user_content" not in parameters:
                parameters["user_content"] = parameters.pop("param_name")
                logger.info(f"[QQ工具] 参数映射: param_name -> user_content")

        import httpx
        from system.config import get_server_port
        import uuid

        # 构建MCP服务器请求 - 与background_analyzer相同的格式
        mcp_payload = {
            "query": f"QQ MCP工具调用: {service_name}.{tool_name}",
            "tool_calls": [tool_call],
            "session_id": session_id,
            "request_id": str(uuid.uuid4()),
            "skip_callback": True,  # QQ需要同步等待结果
        }

        mcp_server_url = f"http://localhost:{get_server_port('mcp_server')}/schedule"

        logger.info(f"[QQ工具] 发送MCP请求到: {mcp_server_url}")

        # 增加超时时间到60秒，避免应用启动超时
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(mcp_server_url, json=mcp_payload)

            if response.status_code == 200:
                result = response.json()
                logger.info(f"[QQ工具] MCP请求成功: {result}")

                # 尝试提取工具执行结果
                if result.get("success"):
                    tool_result = result.get("result", "")

                    # 如果result是字符串，直接使用
                    # 如果是字典，尝试提取output/result/message字段
                    if isinstance(tool_result, dict):
                        tool_result = tool_result.get(
                            "output",
                            tool_result.get(
                                "result", tool_result.get("message", json.dumps(tool_result, ensure_ascii=False))
                            ),
                        )

                    # 确保tool_result不是None或空字符串
                    if not tool_result or tool_result == "None":
                        tool_result = ""

                    # 检查工具类型：后台工具不发送结果给用户
                    should_send = _should_send_result_to_user(tool_name)
                    logger.info(f"[QQ工具] 工具类型判断: {tool_name} -> should_send={should_send}")

                    if should_send:
                        # 用户面向工具：返回结果
                        return {"tool_name": tool_name, "result": str(tool_result), "success": True}
                    else:
                        # 后台工具：记录日志，返回空结果（避免发送给用户）
                        logger.info(f"[QQ工具] 后台工具执行成功，结果已记录到日志: {str(tool_result)[:200]}")
                        return {"tool_name": tool_name, "result": "", "success": True}
                else:
                    error_msg = result.get("error", result.get("message", "执行失败"))
                    logger.error(f"[QQ工具] MCP执行失败: {error_msg}")
                    return None
            else:
                logger.error(f"[QQ工具] MCP请求失败: {response.status_code} - {response.text}")
                return None

    except Exception as e:
        logger.error(f"[QQ工具] 执行MCP工具失败: {e}", exc_info=True)
        return None


async def _execute_batch_mcp_tools(
    tool_calls: List[Dict[str, Any]],
    session_id: str,
    sender_id: Optional[str] = None,
    message_type: str = "private",
    group_id: Optional[str] = None,
    image_path: Optional[str] = None,
) -> Dict[str, Any]:
    """批量执行MCP工具调用 - 支持复合操作"""
    import httpx
    from system.config import get_server_port
    import uuid

    results = []
    errors = []

    logger.info(f"[批量MCP] 开始执行 {len(tool_calls)} 个工具调用")

    for i, tool_call in enumerate(tool_calls):
        try:
            logger.info(f"[批量MCP] 执行第 {i+1}/{len(tool_calls)} 个工具")

            service_name = tool_call.get("service_name")
            tool_name = tool_call.get("tool_name")

            # 构建参数（复用现有逻辑）
            parameters = tool_call.get("parameters", {})

            if not parameters:
                parameters = {}
                for key, value in tool_call.items():
                    if key not in ["agentType", "service_name", "tool_name", "parameters"]:
                        parameters[key] = value

            # 简化的MCP调用（避免重复复杂的参数处理）
            mcp_payload = {
                "query": f"批量MCP {i+1}/{len(tool_calls)}: {service_name}.{tool_name}",
                "tool_calls": [tool_call],
                "session_id": session_id,
                "request_id": str(uuid.uuid4()),
                "skip_callback": True,
            }

            mcp_server_url = f"http://localhost:{get_server_port('mcp_server')}/schedule"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(mcp_server_url, json=mcp_payload)

                if response.status_code == 200:
                    result = response.json()
                    # 检查工具类型，过滤后台工具的结果
                    should_send = _should_send_result_to_user(tool_name)
                    logger.info(f"[批量MCP] 工具类型判断: {tool_name} -> should_send={should_send}")

                    if should_send:
                        results.append({
                            "tool": f"{service_name}.{tool_name}",
                            "result": result,
                            "success": True
                        })
                    else:
                        # 后台工具：只记录日志，不添加到返回结果
                        logger.info(f"[批量MCP] 后台工具已执行: {tool_name}, 结果已记录到日志")
                    logger.info(f"[批量MCP] 第 {i+1} 个工具执行成功")
                else:
                    errors.append(f"工具 {i+1}: HTTP {response.status_code}")
                    logger.error(f"[批量MCP] 第 {i+1} 个工具执行失败: {response.status_code}")

        except Exception as e:
            error_msg = f"工具 {i+1}: {str(e)}"
            errors.append(error_msg)
            logger.error(f"[批量MCP] 第 {i+1} 个工具执行异常: {e}")

    # 返回批量结果
    batch_result = {
        "tool_name": "batch_execution",
        "result": results,
        "success": len(errors) == 0,
        "total": len(tool_calls),
        "successful": len(results),
        "failed": len(errors),
        "errors": errors
    }

    logger.info(
        f"[批量MCP] 执行完成: 成功 {len(results)}/{len(tool_calls)}, 失败 {len(errors)}"
    )

    return batch_result


# 挂载LLM服务路由以支持 /llm/chat
from .llm_service import llm_app

app.mount("/llm", llm_app)


# 新增：日志解析相关API接口
@app.get("/logs/context/statistics")
async def get_log_context_statistics(days: int = 7):
    """获取日志上下文统计信息"""
    try:
        statistics = message_manager.get_context_statistics(days)
        return {"status": "success", "statistics": statistics}
    except Exception as e:
        print(f"获取日志上下文统计错误: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@app.get("/logs/context/load")
async def load_log_context(days: int = 3, max_messages: int = None):
    """加载日志上下文"""
    try:
        messages = message_manager.load_recent_context(days=days, max_messages=max_messages)
        return {"status": "success", "messages": messages, "count": len(messages), "days": days}
    except Exception as e:
        print(f"加载日志上下文错误: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"加载上下文失败: {str(e)}")


@app.post("/tool_notification")
async def tool_notification(payload: Dict[str, Any]):
    """接收工具调用状态通知，只显示工具调用状态，不显示结果"""
    try:
        session_id = payload.get("session_id")
        tool_calls = payload.get("tool_calls", [])
        message = payload.get("message", "")

        if not session_id:
            raise HTTPException(400, "缺少session_id")

        # 记录工具调用状态（不处理结果，结果由tool_result_callback处理）
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool_name", "未知工具")
            service_name = tool_call.get("service_name", "未知服务")
            status = tool_call.get("status", "starting")
            logger.info(f"工具调用状态: {tool_name} ({service_name}) - {status}")

        # 这里可以添加WebSocket通知UI的逻辑，让UI显示工具调用状态
        # 目前先记录日志，UI可以通过其他方式获取工具调用状态

        return {
            "success": True,
            "message": "工具调用状态通知已接收",
            "tool_calls": tool_calls,
            "display_message": message,
        }

    except Exception as e:
        logger.error(f"工具调用通知处理失败: {e}")
        raise HTTPException(500, f"处理失败: {str(e)}")


@app.post("/tool_result_callback")
async def tool_result_callback(payload: Dict[str, Any]):
    """接收MCP工具执行结果回调
    
    回调处理流程：
    1. 检测会话类型（QQ会话 或 UI会话）
    2. 对于QQ会话：解析工具结果并直接发送给QQ用户
    3. 对于UI会话：仅记录日志，不重复生成回复（前端意识已处理）
    
    工具结果格式说明：
    - Undefined工具：直接返回字符串（MCP Manager会自动包装为 {'success': True, 'result': '...'}）
    - MCP工具：返回 {'success': True, 'result': '...'} 格式
    
    Args:
        payload: CallbackPayload类型，包含session_id, task_id, result, success等信息
    """
    try:
        session_id = payload.get("session_id")
        task_id = payload.get("task_id")
        result = payload.get("result", {})
        success = payload.get("success", False)

        if not session_id:
            raise HTTPException(400, "缺少session_id")

        # 去重检查：如果task_id已处理过，直接返回成功
        if task_id in _task_callback_cache:
            logger.info(f"[工具回调] 任务ID已处理过，跳过: {task_id}")
            return {
                "success": True,
                "message": "任务结果已处理（去重）",
                "task_id": task_id,
                "session_id": session_id,
            }

        # 标记任务ID为已处理
        _task_callback_cache.add(task_id)

        logger.info(f"[工具回调] 开始处理工具回调，会话: {session_id}, 任务ID: {task_id}")
        logger.info(f"[工具回调] 回调内容: {result}")

        # 获取工具执行结果
        # 回调格式: {"success": True, "results": [{"tool": "xxx", "success": True, "result": "..."}], "message": "..."}
        if success and "results" in result and len(result["results"]) > 0:
            # 从results数组中提取第一个工具的结果
            tool_result = result["results"][0].get("result", "执行成功")
            tool_name = result["results"][0].get("tool", "未知工具")
            logger.info(f"[工具回调] 工具名称: {tool_name}")
        else:
            tool_result = result.get("error", "未知错误") if not success else "执行成功"
            tool_name = "未知工具"

        logger.info(f"[工具回调] 工具执行结果: {str(tool_result)[:200] if len(str(tool_result)) > 200 else str(tool_result)}")

        # 解析tool_result，提取实际的结果字符串
        # 支持两种格式：
        # 1. 字典格式: {'success': True, 'result': "实际结果字符串"}
        # 2. 字符串格式: 直接的结果文本
        if isinstance(tool_result, dict):
            result_to_send = tool_result.get('result', str(tool_result))
            logger.debug(f"[工具回调] 字典格式结果解析: keys={list(tool_result.keys())}, result_type={type(tool_result.get('result'))}")
        else:
            result_to_send = str(tool_result)
            logger.debug(f"[工具回调] 字符串格式结果: result_type={type(tool_result)}")

        logger.info(f"[工具回调] 准备发送的消息长度: {len(result_to_send)}")

        # 判断是否为QQ会话
        is_qq_session = session_id and session_id.startswith('qq_')

        # 判断工具类型：信息搜集和输出类型的工具才需要将结果发送给用户
        # 其他类型的工具（如记忆、任务、控制等）只记录日志
        should_send_to_user = _should_send_result_to_user(tool_name)
        logger.info(f"[工具回调] 工具类型判断: {tool_name} -> should_send_to_user={should_send_to_user}")

        if is_qq_session and should_send_to_user:
            # QQ会话：直接发送工具结果到QQ
            try:
                # 从session_id中提取QQ号和消息类型
                # 格式: qq_[QQ号]
                qq_number = session_id.replace('qq_', '')
                message_type = 'private'
                group_id = None

                logger.info(f"[工具回调] QQ会话检测到，准备发送结果到: {qq_number}")

                # 获取QQ listener
                from mcpserver.mcp_registry import get_service_info
                service_info = get_service_info("QQ/微信集成")
                if service_info:
                    agent = service_info.get("instance")
                    if agent and hasattr(agent, "message_listener"):
                        message_listener = agent.message_listener
                        if message_listener:
                            # 直接发送工具结果（确保是字符串）
                            await message_listener._send_qq_reply(
                                message_type, qq_number, group_id, result_to_send, 'text'
                            )
                            logger.info(f"[工具回调] 工具结果已发送到QQ: {qq_number}, 消息长度: {len(result_to_send)}")
                        else:
                            logger.warning(f"[工具回调] QQ message_listener未初始化")
                    else:
                        logger.warning(f"[工具回调] QQ服务未初始化或缺少message_listener")
                else:
                    logger.warning(f"[工具回调] QQ服务未注册")

            except Exception as e:
                logger.error(f"[工具回调] 发送工具结果到QQ失败: {e}", exc_info=True)
        else:
            # UI会话：只记录工具结果，不重复生成回复（前端意识已处理）
            if should_send_to_user:
                logger.info(f"[工具回调] UI会话，用户面向工具结果已记录，前端意识已处理回复")
            else:
                logger.info(f"[工具回调] UI会话，后台工具结果已记录到日志，不发送给用户")

        logger.info(f"[工具回调] 工具结果处理完成")
        return {
            "success": True,
            "message": "工具结果已记录",
            "task_id": task_id,
            "session_id": session_id,
        }
        logger.info(f"[工具回调] UI会话，将AI回复发送给UI...")
        await _notify_ui_refresh(session_id, response_text)

        logger.info(f"[工具回调] 工具结果处理完成")

        return {
            "success": True,
            "message": "工具结果已通过主AI处理并返回给UI",
            "response": response_text,
            "task_id": task_id,
            "session_id": session_id,
        }

    except Exception as e:
        logger.error(f"[工具回调] 工具结果回调处理失败: {e}")
        raise HTTPException(500, f"处理失败: {str(e)}")


@app.post("/tool_result")
async def tool_result(payload: Dict[str, Any]):
    """接收工具执行结果并显示在UI上"""
    try:
        session_id = payload.get("session_id")
        result = payload.get("result", "")
        notification_type = payload.get("type", "")
        ai_response = payload.get("ai_response", "")

        if not session_id:
            raise HTTPException(400, "缺少session_id")

        logger.info(f"工具执行结果: {result}")

        # 如果是工具完成后的AI回复，通过信号机制通知UI线程显示
        if notification_type == "tool_completed_with_ai_response" and ai_response:
            try:
                # 使用Qt信号机制在主线程中安全地更新UI
                from ui.controller.tool_chat import chat

                # 直接发射信号，确保在主线程中执行
                chat.tool_ai_response_received.emit(ai_response)
                logger.info(f"[UI] 已通过信号机制通知UI显示AI回复，长度: {len(ai_response)}")
            except Exception as e:
                logger.error(f"[UI] 调用UI控制器显示AI回复失败: {e}")

        return {"success": True, "message": "工具结果已接收", "result": result, "session_id": session_id}

    except Exception as e:
        logger.error(f"处理工具结果失败: {e}")
        raise HTTPException(500, f"处理失败: {str(e)}")


@app.post("/save_tool_conversation")
async def save_tool_conversation(payload: Dict[str, Any]):
    """保存工具对话历史"""
    try:
        session_id = payload.get("session_id")
        user_message = payload.get("user_message", "")
        assistant_response = payload.get("assistant_response", "")

        if not session_id:
            raise HTTPException(400, "缺少session_id")

        logger.info(f"[保存工具对话] 开始保存工具对话历史，会话: {session_id}")

        # 保存用户消息（工具执行结果）
        if user_message:
            message_manager.add_message(session_id, "user", user_message)

        # 保存AI回复
        if assistant_response:
            message_manager.add_message(session_id, "assistant", assistant_response)

        logger.info(f"[保存工具对话] 工具对话历史已保存，会话: {session_id}")

        return {"success": True, "message": "工具对话历史已保存", "session_id": session_id}

    except Exception as e:
        logger.error(f"[保存工具对话] 保存工具对话历史失败: {e}")
        raise HTTPException(500, f"保存失败: {str(e)}")


@app.post("/ui_notification")
async def ui_notification(payload: Dict[str, Any]):
    """UI通知接口 - 用于直接控制UI显示"""
    try:
        session_id = payload.get("session_id")
        action = payload.get("action", "")
        ai_response = payload.get("ai_response", "")

        if not session_id:
            raise HTTPException(400, "缺少session_id")

        logger.info(f"UI通知: {action}, 会话: {session_id}")

        # 处理显示工具AI回复的动作
        if action == "show_tool_ai_response" and ai_response:
            try:
                from ui.controller.tool_chat import chat

                # 直接发射信号，确保在主线程中执行
                chat.tool_ai_response_received.emit(ai_response)
                logger.info(f"[UI通知] 已通过信号机制显示工具AI回复，长度: {len(ai_response)}")
                return {"success": True, "message": "AI回复已显示"}
            except Exception as e:
                logger.error(f"[UI通知] 显示工具AI回复失败: {e}")
                raise HTTPException(500, f"显示AI回复失败: {str(e)}")

        return {"success": True, "message": "UI通知已处理"}

    except Exception as e:
        logger.error(f"处理UI通知失败: {e}")
        raise HTTPException(500, f"处理失败: {str(e)}")


async def _trigger_chat_stream_no_intent(session_id: str, response_text: str):
    """触发聊天流式响应但不触发意图分析 - 发送纯粹的AI回复到UI"""
    try:
        logger.info(f"[UI发送] 开始发送AI回复到UI，会话: {session_id}")
        logger.info(f"[UI发送] 发送内容: {response_text[:200]}...")

        # 直接调用现有的流式对话接口，但跳过意图分析
        import httpx

        # 构建请求数据 - 使用纯粹的AI回复内容，并跳过意图分析
        chat_request = {
            "message": response_text,  # 直接使用AI回复内容，不加标记
            "stream": True,
            "session_id": session_id,
            "use_self_game": False,
            "disable_tts": False,
            "return_audio": False,
            "skip_intent_analysis": True,  # 关键：跳过意图分析
        }

        # 调用现有的流式对话接口
        from system.config import get_server_port

        api_url = f"http://localhost:{get_server_port('api_server')}/chat/stream"

        async with httpx.AsyncClient() as client:
            async with client.stream("POST", api_url, json=chat_request) as response:
                if response.status_code == 200:
                    # 处理流式响应，包括TTS切割
                    async for chunk in response.aiter_text():
                        if chunk.strip():
                            # 这里可以进一步处理流式响应
                            # 或者直接让UI处理流式响应
                            pass

                    logger.info(f"[UI发送] AI回复已成功发送到UI: {session_id}")
                    logger.info(f"[UI发送] 成功显示到UI")
                else:
                    logger.error(f"[UI发送] 调用流式对话接口失败: {response.status_code}")

    except Exception as e:
        logger.error(f"[UI发送] 触发聊天流式响应失败: {e}")


async def _notify_ui_refresh(session_id: str, response_text: str):
    """通知UI刷新会话历史"""
    try:
        import httpx

        # 通过UI通知接口直接显示AI回复
        ui_notification_payload = {
            "session_id": session_id,
            "action": "show_tool_ai_response",
            "ai_response": response_text,
        }

        from system.config import get_server_port

        api_url = f"http://localhost:{get_server_port('api_server')}/ui_notification"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(api_url, json=ui_notification_payload)
            if response.status_code == 200:
                logger.info(f"[UI通知] AI回复显示通知发送成功: {session_id}")
            else:
                logger.error(f"[UI通知] AI回复显示通知失败: {response.status_code}")

    except Exception as e:
        logger.error(f"[UI通知] 通知UI刷新失败: {e}")


async def _send_ai_response_directly(session_id: str, response_text: str):
    """直接发送AI回复到UI"""
    try:
        import httpx

        # 使用非流式接口发送AI回复
        chat_request = {
            "message": f"[工具结果] {response_text}",  # 添加标记让UI知道这是工具结果
            "stream": False,
            "session_id": session_id,
            "use_self_game": False,
            "disable_tts": False,
            "return_audio": False,
            "skip_intent_analysis": True,
        }

        from system.config import get_server_port

        api_url = f"http://localhost:{get_server_port('api_server')}/chat"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(api_url, json=chat_request)
            if response.status_code == 200:
                logger.info(f"[直接发送] AI回复已通过非流式接口发送到UI: {session_id}")
            else:
                logger.error(f"[直接发送] 非流式接口发送失败: {response.status_code}")

    except Exception as e:
        logger.error(f"[直接发送] 直接发送AI回复失败: {e}")


# 工具执行结果已通过LLM总结并保存到对话历史中
# UI可以通过查询历史获取工具执行结果
