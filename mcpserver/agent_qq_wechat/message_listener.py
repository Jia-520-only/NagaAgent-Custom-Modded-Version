#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QQ/微信消息监听和自动回复服务
监听QQ和微信消息，自动转发给NagaAgent并回复
"""

import asyncio
import logging
import json
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote
from pathlib import Path

logger = logging.getLogger(__name__)


class QQWeChatMessageListener:
    """QQ/微信消息监听器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化监听器

        Args:
            config: 配置字典
        """
        self.config = config
        self.qq_config = config.get("qq", {})
        self.wechat_config = config.get("wechat", {})

        # 配置文件路径
        self.config_file_path = Path.cwd() / "config.json"

        # API配置
        self.api_base_url = "http://127.0.0.1:8000"
        self.http_client: Optional[aiohttp.ClientSession] = None

        # 会话管理（使用统一的message_manager）
        # 注意：QQ和UI现在共享同一个message_manager，实现会话同步

        # 消息队列（防止重复处理）
        self.message_cache: Dict[str, float] = {}
        self.cache_ttl = 10  # 消息缓存时间（秒）

        # 运行状态
        self.running = False
        self._listen_task = None

        # 集成消息旁观器
        self.message_observer = None
        self._init_message_observer()

    def _init_message_observer(self):
        """初始化消息旁观器"""
        try:
            from .message_observer import MessageObserver

            if self.qq_config.get("enable_observer", True):
                self.message_observer = MessageObserver(self)
                logger.info("[初始化] 消息旁观器已启用")
            else:
                logger.info("[初始化] 消息旁观器已禁用")
        except Exception as e:
            logger.warning(f"[初始化] 消息旁观器初始化失败: {e}")
            self.message_observer = None

    async def start(self):
        """启动监听服务"""
        if self.running:
            logger.warning("监听服务已在运行")
            return

        self.running = True
        self.http_client = aiohttp.ClientSession()

        logger.info("QQ/微信消息监听服务启动")
        # 将清理任务作为后台任务启动，不阻塞
        self._listen_task = asyncio.create_task(self._cleanup_old_messages())

    async def stop(self):
        """停止监听服务"""
        if not self.running:
            return

        self.running = False

        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        if self.http_client:
            await self.http_client.close()

        logger.info("QQ/微信消息监听服务停止")

    def _save_config(self):
        """
        保存配置到config.json文件

        注意：config.json文件现在使用UTF-8编码（已从UTF-16转换）
        """
        try:
            # 使用json5库安全地读取和更新配置
            from nagaagent_core.vendors import json5

            # 读取配置（自动检测编码）
            from nagaagent_core.vendors.charset_normalizer import from_path
            charset_results = from_path(str(self.config_file_path))
            if not charset_results or not charset_results.best():
                logger.warning("无法检测配置文件编码，使用默认UTF-8")
                encoding = "utf-8"
            else:
                encoding = charset_results.best().encoding

            with open(self.config_file_path, "r", encoding=encoding) as f:
                config_data = json5.load(f)

            # 更新reply_mode
            if "reply_mode" in self.qq_config:
                mode = self.qq_config["reply_mode"]
                if "qq_wechat" in config_data and "qq" in config_data["qq_wechat"]:
                    config_data["qq_wechat"]["qq"]["reply_mode"] = mode
                    logger.info(f"已更新配置: reply_mode = {mode}")

            # 更新enable_voice
            if "enable_voice" in self.qq_config:
                enabled = self.qq_config["enable_voice"]
                if "qq_wechat" in config_data and "qq" in config_data["qq_wechat"]:
                    config_data["qq_wechat"]["qq"]["enable_voice"] = enabled
                    logger.info(f"已更新配置: enable_voice = {enabled}")

            # 保存配置（使用UTF-8编码）
            with open(self.config_file_path, "w", encoding="utf-8") as f:
                json5.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"配置已保存到: {self.config_file_path}")
            return True

        except Exception as e:
            logger.error(f"保存配置失败: {e}", exc_info=True)
            return False

    async def handle_qq_message(self, message_type: str, data: Dict[str, Any]):
        """
        处理QQ消息

        Args:
            message_type: 消息类型 (private/group)
            data: 消息数据
        """
        try:
            # 提取消息信息
            if message_type == "private":
                user_id = data.get("user_id")
                message = data.get("raw_message", "")
                sender_id = str(user_id)
                group_id = None
                logger.info(f"[handle_qq_message] 私聊消息: user_id={user_id}, message={message[:30]}")
            elif message_type == "group":
                group_id = str(data.get("group_id", ""))  # 转换为字符串，避免API验证失败
                user_id = data.get("user_id")
                message = data.get("raw_message", "")
                sender_id = str(user_id)
                logger.info(f"[handle_qq_message] 群聊消息: user_id={user_id}, group_id={group_id}, message={message[:30]}")
            else:
                logger.info(f"[handle_qq_message] 未知消息类型: {message_type}")
                return

            # 过滤机器人自己的消息
            bot_qq = self.qq_config.get("bot_qq", "")
            if str(user_id) == str(bot_qq):
                logger.info(f"[handle_qq_message] 过滤机器人自己的消息: user_id={user_id}, bot_qq={bot_qq}")
                return

            # 检查是否为图片消息
            if "[CQ:image" in message:
                # 解析图片URL并附加到消息中，让AI判断是否需要分析
                import re
                import html

                # 检查消息中是否还包含文字（不仅是图片）
                # 移除图片CQ码后检查是否还有内容
                clean_text = re.sub(r'\[CQ:image[^\]]*\]', '', message).strip()

                # 群聊回复控制（图片消息也需要智能判断）
                if message_type == "group":
                    should_reply = await self._should_reply_to_group(group_id, sender_id, clean_text if clean_text else "[图片]", data)
                    if not should_reply:
                        logger.info(f"[图片过滤] 群 {group_id} 图片消息不满足回复条件，跳过")
                        return

                # 提取图片URL
                image_url = None
                cq_image_pattern = r"\[CQ:image(?:,[^\]]*)?url=([^\]]+)\]"
                url_match = re.search(cq_image_pattern, message)

                if url_match:
                    image_url = html.unescape(url_match.group(1))
                    logger.info(f"[图片处理] 提取到图片URL: {image_url[:100]}...")

                # 私聊纯图片直接分析
                if message_type == "private" and not clean_text:
                    logger.info(f"[图片处理] 私聊纯图片消息，直接分析")
                    await self._handle_qq_image(message_type, sender_id, group_id, data, message)
                    return

                # 如果有文字内容，先进行图片识别分析，然后让AI根据识别结果回复
                # 注意：只处理真实的文字消息，不处理纯图片或纯动画表情包
                if clean_text:
                    # 解析引用内容
                    reply_info = self._parse_reply_content(message, data)
                    replied_content = reply_info["replied_content"]

                    # 先进行图片识别（获取视觉分析结果），添加超时保护
                    logger.info(f"[图片处理] 检测到文字+图片消息，先进行视觉识别")
                    try:
                        image_analysis_result = await asyncio.wait_for(
                            self._analyze_qq_image(
                                message_type, sender_id, group_id, data, message
                            ),
                            timeout=30.0  # 30秒超时
                        )
                    except asyncio.TimeoutError:
                        logger.warning(f"[图片处理] 图片识别超时，跳过视觉分析")
                        image_analysis_result = None
                    except Exception as e:
                        logger.warning(f"[图片处理] 图片识别失败: {e}")
                        image_analysis_result = None

                    # 构建增强消息：文字 + 图片分析结果
                    enhanced_message = clean_text
                    if image_analysis_result:
                        enhanced_message = f"{clean_text}\n[图片内容: {image_analysis_result}]" if clean_text else f"[图片内容: {image_analysis_result}]"

                    # 添加引用上下文
                    if replied_content:
                        enhanced_message = f"[引用回复 {reply_info['replied_sender']}]: {replied_content}\n{enhanced_message}"

                    # 让AI根据图片分析结果生成回复
                    result = await self._get_ai_response_with_tools(
                        enhanced_message, sender_id, platform="qq", group_id=group_id, message_type=message_type
                    )
                    return

                # 群聊纯图片（需要智能判断）
                if message_type == "group":
                    # 纯图片消息需要更严格的判断：只有@机器人或智能判断通过才回复
                    # 这里不再重复检查，因为在第193行已经检查过了
                    # 如果代码走到这里，说明智能判断已经通过，直接处理图片
                    logger.info(f"[图片处理] 群 {group_id} 纯图片通过智能判断，准备分析")
                else:
                    logger.info(f"[图片处理] 私聊纯图片，直接分析")

                await self._handle_qq_image(message_type, sender_id, group_id, data, message)
                return

            # 检查是否为表情消息（CQ:face）
            if "[CQ:face" in message:
                # 表情消息：识别表情ID并简单回复
                # 群聊回复控制：表情消息也需要检查是否应该回复
                if message_type == "group":
                    should_reply = await self._should_reply_to_group(group_id, sender_id, message, data)
                    if not should_reply:
                        logger.info(f"[群聊过滤] 群 {group_id} 表情消息不满足回复条件，跳过")
                        return
                await self._handle_qq_face(message_type, sender_id, group_id, message)
                return

            # 检查是否为指令消息（以 / 开头）
            if message.startswith("/"):
                logger.info(f"[handle_qq_message] 指令消息: {message}")
                await self._handle_qq_command(message_type, sender_id, group_id, message)
                return

            # 表情包快速回复（基于关键词匹配）
            logger.info(f"[handle_qq_message] 检查表情包快速回复...")
            if self._should_send_quick_emoji(message):
                emoji_response = await self._get_emoji_response(message)
                if emoji_response:
                    await self._send_qq_reply(
                        message_type, sender_id, group_id, emoji_response, media_type="text"
                    )
                    return  # 发送表情后直接返回，不进行 AI 回复

            # 群聊回复控制
            if message_type == "group":
                should_reply = await self._should_reply_to_group(group_id, sender_id, message, data)
                if not should_reply:
                    logger.info(f"[群聊过滤] 群 {group_id} 消息不满足回复条件，跳过: {message[:50]}...")
                    return

            # 去重检查（仅群聊需要去重，私聊不限制）
            if message_type == "group":
                message_key = f"qq_{sender_id}_{message}"
                if await self._is_duplicate(message_key):
                    return

            logger.info(f"收到QQ消息: {message_type} | 发送者: {sender_id} | 群: {group_id} | 内容: {message[:50]}...")

            # 消息旁观记录(无论是否回复都会记录)
            if self.message_observer:
                recorded = await self.message_observer.observe_message(
                    message_type=message_type,
                    sender_id=sender_id,
                    group_id=group_id,
                    message=message,
                    raw_data=data
                )
                if recorded:
                    logger.info("[消息旁观] 已记录有趣消息到记忆")

            # 检查并发送缓存的自主消息
            await self._check_and_send_cached_messages(sender_id, message_type)

            # 解析引用内容（CQ:reply）
            reply_info = self._parse_reply_content(message, data)
            cleaned_message = reply_info["clean_message"]
            replied_content = reply_info["replied_content"]
            replied_sender = reply_info["replied_sender"]

            # 如果有引用内容，将其添加到消息中
            final_message = cleaned_message
            if replied_content:
                # 将引用内容作为上下文添加到消息前
                final_message = f"[引用回复 {replied_sender}]: {replied_content}\n\n当前消息: {cleaned_message}"
                logger.info(f"[引用内容] 已添加到消息: {replied_content[:100]}...")

            # 生成AI回复并处理工具调用（使用QQ专用API）
            result = await self._get_ai_response_with_tools(
                final_message, sender_id, platform="qq", group_id=group_id, message_type=message_type
            )

            if result:
                # 处理返回值（可能是元组或字符串）
                if isinstance(result, tuple):
                    response, audio_url = result
                else:
                    response = result
                    audio_url = ""

                if response:
                    # 发送回复（传入audio_url）
                    await self._send_qq_reply(
                        message_type, sender_id, group_id, response, media_type="text", audio_url=audio_url
                    )

        except Exception as e:
            logger.error(f"处理QQ消息错误: {e}", exc_info=True)

    async def _check_and_send_cached_messages(self, sender_id: str, message_type: str):
        """检查并发送缓存的自主消息"""
        try:
            from system.config import config

            # 检查窗口是否存在且有缓存消息
            if not hasattr(config, 'window') or config.window is None:
                return

            window = config.window

            # 检查是否有发送缓存消息的方法
            if not hasattr(window, '_send_cached_qq_messages_async'):
                logger.debug(f"[缓存消息] 窗口没有发送缓存消息的方法")
                return

            # 检查是否有缓存消息
            if not hasattr(window, '_cached_qq_messages') or not window._cached_qq_messages:
                logger.debug(f"[缓存消息] 没有待发送的缓存消息")
                return

            # 暂时禁用缓存消息功能（避免发送过期的自主消息）
            logger.debug(f"[缓存消息] 缓存消息功能已禁用")
            return

            # 只在私聊消息时发送缓存消息
            if message_type != "private":
                logger.debug(f"[缓存消息] 仅私聊发送缓存消息，当前类型: {message_type}")
                return

            logger.info(f"[缓存消息] 检测到QQ私聊消息，准备发送缓存消息到: {sender_id}")

            # 获取QQ agent
            from mcpserver.mcp_registry import MCP_REGISTRY
            qq_wechat_agent = MCP_REGISTRY.get("QQ/微信集成")

            if qq_wechat_agent and hasattr(qq_wechat_agent, 'qq_adapter'):
                # 发送缓存消息
                await window._send_cached_qq_messages_async(sender_id, qq_wechat_agent)
            else:
                logger.warning(f"[缓存消息] QQ/微信Agent不可用")

        except Exception as e:
            logger.error(f"[缓存消息] 检查和发送失败: {e}", exc_info=True)

    async def _handle_qq_face(
        self, message_type: str, sender_id: str, group_id: Optional[str], raw_message: str
    ):
        """
        处理QQ表情消息（CQ:face）

        Args:
            message_type: 消息类型（private/group）
            sender_id: 发送者ID
            group_id: 群ID（私聊时为None）
            raw_message: 原始消息内容
        """
        import re

        try:
            # 解析CQ:face码获取表情ID
            face_pattern = r"\[CQ:face,id=(\d+)\]"
            face_match = re.search(face_pattern, raw_message)

            if face_match:
                face_id = face_match.group(1)
                logger.info(f"[表情识别] 收到表情消息: face_id={face_id}")

                # 去重检查
                message_key = f"qq_{sender_id}_face_{face_id}"
                if await self._is_duplicate(message_key):
                    return

                # 简单回复表情消息
                face_responses = [
                    "收到了~",
                    "表情包可爱！",
                    "嗯嗯~",
                    "👌",
                    "收到",
                    "哈哈",
                ]

                import random
                response = random.choice(face_responses)

                # 发送回复
                await self._send_qq_reply(
                    message_type, sender_id, group_id, response, media_type="text"
                )
                logger.info(f"[表情识别] 已回复表情: {response}")
            else:
                logger.warning(f"[表情识别] 无法解析表情CQ码: {raw_message}")

        except Exception as e:
            logger.error(f"[表情识别] 处理表情消息失败: {e}", exc_info=True)

    async def _analyze_qq_image(
        self, message_type: str, sender_id: str, group_id: Optional[str], data: Dict[str, Any], raw_message: str
    ) -> Optional[str]:
        """
        分析QQ图片内容（不发送回复）

        Args:
            message_type: 消息类型
            sender_id: 发送者ID
            group_id: 群ID
            data: 原始消息数据
            raw_message: 原始消息内容

        Returns:
            图片分析结果文本，失败返回None
        """
        try:
            # 解析CQ码获取图片URL
            import re
            import html

            # 支持多种CQ码格式
            cq_image_pattern = r"\[CQ:image(?:,summary=[^,\]]+)?(?:,file=([^,\]]+))?(?:,url=([^\]]+))?(?:,[^\]]*)*\]"
            matches = re.findall(cq_image_pattern, raw_message)

            # 如果匹配失败，尝试提取所有参数
            if not matches:
                all_params_pattern = r"\[CQ:image,([^]]+)\]"
                all_params = re.findall(all_params_pattern, raw_message)
                if all_params:
                    params_str = all_params[0]
                    url_match = re.search(r'url=([^\s,\]]+)', params_str)
                    if url_match:
                        image_url = url_match.group(1)
                        file_match = re.search(r'file=([^,\]]+)', params_str)
                        file_name = file_match.group(1) if file_match else ""
                        matches = [(file_name, image_url)]
                        logger.info(f"[图片分析] 通过参数解析: file={file_name}, url={image_url[:100]}")

            if not matches:
                logger.warning(f"[图片分析] 无法解析图片CQ码: {raw_message[:150]}")
                return None

            file_name, image_url = matches[0]
            logger.debug(f"[图片分析] 解析到 file={file_name}, url={image_url[:100] if image_url else 'None'}...")
            if not file_name and not image_url:
                logger.warning(f"[图片分析] 解析结果为空, raw_message={repr(raw_message)}, matches={matches}")
                return None

            # 去重检查
            message_key = f"qq_{sender_id}_image_{file_name}"
            if await self._is_duplicate(message_key):
                return None

            # 检查是否为动图表情包
            if "type=flash" in raw_message:
                logger.info(f"[图片分析] 检测到动图表情包，跳过分析")
                return None

            # 获取图片URL或本地路径
            if not image_url:
                logger.info(f"[图片分析] 通过NapCat API获取图片URL: file={file_name}")
                try:
                    http_url = self.qq_config.get("http_url", "http://127.0.0.1:3000")
                    http_token = self.qq_config.get("http_token", "")

                    headers = {}
                    if http_token:
                        headers["Authorization"] = f"Bearer {http_token}"

                    get_image_url = f"{http_url}/get_image"
                    payload = {"file": file_name}

                    import aiohttp

                    async with aiohttp.ClientSession() as session:
                        async with session.get(get_image_url, params=payload, headers=headers) as resp:
                            if resp.status == 200:
                                result = await resp.json()
                                if result is None:
                                    logger.warning(f"[图片分析] API返回None, status={resp.status}")
                                    image_url = f"[CQ:image,file={file_name}]"
                                else:
                                    data = result.get("data", {}) if isinstance(result, dict) else {}
                                    image_url = data.get("url", data.get("file", ""))
                            else:
                                logger.warning(f"[图片分析] get_image API调用失败, 状态码={resp.status}")
                                image_url = f"[CQ:image,file={file_name}]"

                except Exception as e:
                    logger.error(f"[图片分析] 调用NapCat API失败: {e}")
                    image_url = f"[CQ:image,file={file_name}]"

            if not image_url:
                logger.warning(f"[图片分析] 无法获取图片URL: file={file_name}")
                return None

            # 下载或复制图片
            if image_url.startswith("[CQ:"):
                # 获取本地文件
                try:
                    http_url = self.qq_config.get("http_url", "http://127.0.0.1:3000")
                    http_token = self.qq_config.get("http_token", "")

                    headers = {}
                    if http_token:
                        headers["Authorization"] = f"Bearer {http_token}"

                    get_image_url = f"{http_url}/get_image"
                    payload = {"file": file_name}

                    async with aiohttp.ClientSession() as session:
                        async with session.get(get_image_url, params=payload, headers=headers) as resp:
                            if resp.status == 200:
                                result = await resp.json()
                                if result is None:
                                    logger.error(f"[图片分析] API返回None, status={resp.status}")
                                    return None
                                data = result.get("data", {}) if isinstance(result, dict) else {}
                                local_file = data.get("file", "")
                                if local_file and Path(local_file).exists():
                                    temp_dir = Path.cwd() / "img" / "temp"
                                    temp_dir.mkdir(parents=True, exist_ok=True)
                                    ext = ".jpg" if file_name.lower().endswith(".jpg") else ".png"
                                    temp_path = temp_dir / f"qq_{sender_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
                                    import shutil
                                    shutil.copy2(local_file, temp_path)
                                    image_data = open(temp_path, "rb").read()
                                else:
                                    logger.error(f"[图片分析] 本地文件不存在: {local_file}")
                                    return None
                            else:
                                logger.error(f"[图片分析] get_image API调用失败, 状态码={resp.status}")
                                return None

                except Exception as e:
                    logger.error(f"[图片分析] 获取本地文件失败: {e}", exc_info=True)
                    return None
            else:
                # 下载远程图片
                logger.info(f"[图片分析] 开始下载远程图片: {image_url}")
                async with aiohttp.ClientSession() as session:
                    try:
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                        }
                        async with session.get(image_url, timeout=30, headers=headers) as resp:
                            if resp.status != 200:
                                logger.error(f"[图片分析] 下载失败, 状态码={resp.status}")
                                return None
                            image_data = await resp.read()
                    except Exception as e:
                        logger.error(f"[图片分析] 下载图片失败: {e}", exc_info=True)
                        return None

            # 保存图片到临时文件
            temp_dir = Path.cwd() / "img" / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            ext = ".jpg" if file_name.lower().endswith(".jpg") else ".png"
            temp_path = temp_dir / f"qq_{sender_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"

            with open(temp_path, "wb") as f:
                f.write(image_data)

            logger.info(f"[图片分析] 图片已保存: {temp_path}")

            # 验证文件存在且可读
            if not temp_path.exists():
                logger.error(f"[图片分析] 文件保存失败: {temp_path}")
                return None

            # 解析引用内容
            reply_info = self._parse_reply_content(raw_message, data)
            replied_content = reply_info["replied_content"]

            # 构建分析提示词
            analysis_prompt = "请简要分析这张图片的内容。包括主要对象、场景、文字（如有）。控制在300字以内。"
            if replied_content:
                analysis_prompt = f"用户引用了一条消息：{replied_content}\n\n请简要分析这张图片的内容，并考虑引用的上下文。包括主要对象、场景、文字（如有）。控制在300字以内。"

            # 调用智谱AI分析图片
            logger.info(f"[视觉识别] 开始调用智谱AI分析图片...")
            try:
                from system.config import config
                import base64

                # 读取并编码图片
                with open(temp_path, "rb") as f:
                    base64_image = base64.b64encode(f.read()).decode("utf-8")

                # 获取智谱AI配置
                api_key = getattr(config.computer_control, "api_key", "")
                model = getattr(config.computer_control, "model", "GLM-4.6V-Flash")
                model_url = getattr(config.computer_control, "model_url", "https://open.bigmodel.cn/api/paas/v4")

                if not api_key:
                    logger.error("[视觉识别] 未配置智谱AI API密钥")
                    return None

                logger.info(f"[视觉识别] 使用智谱AI模型: {model}")

                from openai import OpenAI

                client = OpenAI(api_key=api_key, base_url=model_url)

                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": analysis_prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                            ],
                        }
                    ],
                    max_tokens=1000,
                )

                response = completion.choices[0].message.content
                logger.info(f"[视觉识别] 图片分析完成: {response[:100]}...")

                return response

            except Exception as e:
                logger.error(f"[视觉识别] 图片分析失败: {e}", exc_info=True)
                return None

        except Exception as e:
            logger.error(f"[图片分析] 处理失败: {e}", exc_info=True)
            return None

    async def _handle_qq_image(
        self, message_type: str, sender_id: str, group_id: Optional[str], data: Dict[str, Any], raw_message: str
    ):
        """
        处理QQ图片消息（分析并回复）

        Args:
            message_type: 消息类型
            sender_id: 发送者ID
            group_id: 群ID
            data: 原始消息数据
            raw_message: 原始消息内容
        """
        try:
            # 先分析图片（添加超时保护）
            import asyncio
            try:
                image_analysis = await asyncio.wait_for(
                    self._analyze_qq_image(message_type, sender_id, group_id, data, raw_message),
                    timeout=30.0  # 30秒超时
                )
            except asyncio.TimeoutError:
                logger.warning(f"[图片处理] 图片识别超时，无法回复")
                return
            except Exception as e:
                logger.warning(f"[图片处理] 图片识别失败: {e}")
                return

            if not image_analysis:
                logger.warning(f"[图片处理] 图片分析失败，无法回复")
                return

            # 构建回复消息
            response = f"我看到这张图片了，{image_analysis}"

            # 发送回复
            await self._send_qq_reply(message_type, sender_id, group_id, response, media_type="text")
            logger.info(f"[图片处理] 已发送图片分析回复")

        except Exception as e:
            logger.error(f"[图片处理] 处理失败: {e}", exc_info=True)

    async def _handle_qq_command(self, message_type: str, sender_id: str, group_id: Optional[str], command: str):
        """
        处理QQ指令

        Args:
            message_type: 消息类型
            sender_id: 发送者ID
            group_id: 群ID
            command: 指令内容
        """
        try:
            # 移除空格并转换为小写
            command = command.strip().lower()

            # 当前模式
            current_mode = self.qq_config.get("reply_mode", "both")

            # 帮助指令
            if command in ["/help", "/帮助"]:
                help_text = """
🎮 弥娅QQ助手使用指南

【基础指令】
/语音 - 只发送语音消息
/文字 - 只发送文字消息
/两者 - 同时发送语音和文字（默认）
/模式 - 查看当前模式
/配置 或 /config - 查看当前配置
/设置 [键] [值] - 更改配置项
/工具 - 查看可用的工具
/天气 [城市] - 直接查询天气
/搜索 [关键词] - 直接搜索内容
/画 [内容] - AI绘图（在线）
/本地画 [内容] - AI绘图（本地模型）
/render [内容] - 渲染图片（Markdown/LaTeX）
/打电话 - 发起QQ语音通话（仅私聊）
/group_call [群号] - 发起群语音通话

【配置说明】
可用配置项：
• reply_mode: 回复模式（voice/text/both）
• enable_voice: 是否启用语音（true/false）
• enable_qq_call: 是否启用QQ电话功能（true/false）

示例：
• /设置 reply_mode text - 切换为文字模式
• /设置 reply_mode both - 切换为语音+文字模式
• /设置 enable_voice true - 启用语音
• /设置 enable_qq_call true - 启用QQ电话功能

【工具使用示例】
🌤️ 天气查询：
   - 今天北京的天气
   - 上海明天怎么样
   - 天气

🔍 网页搜索：
   - 搜索AI技术
   - 查一下Python教程
   - 百度一下：人工智能

📊 热门榜单：
   - 热搜榜
   - 百度热搜
   - 微博热搜
   - 抖音热搜

🎬 视频相关：
   - B站搜索：原神
   - 搜索B站视频

🎵 音乐相关：
   - 找周杰伦的歌
   - 搜索晴天

🎨 AI绘图（在线）：
   - 画一只可爱的猫咪
   - 绘图：日落时的海滩
   - /画 樱花

🎨 AI绘图（本地）：
   - 本地画一只可爱的猫咪
   - 用本地模型画风景图
   - /本地画 樱花盛开的海边

📸 图片渲染：
   - 渲染这个公式
   - /render # Hello World
   - render markdown内容

⏰ 时间查询：
   - 现在几点
   - 当前时间

💰 财经信息：
   - 黄金价格
   - 今日金价

🌟 星座运势：
   - 双子座的运势
   - 白羊座本周运势

💡 提示：工具会根据你的消息内容自动触发，无需记忆命令！
💡 本地绘图需要先配置，详见：LOCAL_AI_DRAW_CONFIG.md
"""
                await self._send_command_reply(message_type, sender_id, group_id, help_text)

            # 查看可用工具指令
            elif command in ["/tools", "/工具"]:
                tools_list = await self._get_undefined_tools_list()
                if tools_list:
                    await self._send_command_reply(message_type, sender_id, group_id, tools_list)
                else:
                    await self._send_command_reply(
                        message_type, sender_id, group_id, "Undefined工具未启用或没有可用工具"
                    )

            # 天气快捷查询
            elif command.startswith("/天气"):
                city = command.replace("/天气", "").replace(" ", "")
                if not city:
                    city = "北京"
                # 模拟工具调用
                from mcpserver.mcp_registry import get_service_info

                service_info = get_service_info("Undefined工具集")
                if service_info:
                    agent = service_info.get("instance")
                    if agent:
                        try:
                            result = await asyncio.wait_for(
                                agent.call_tool("weather_query", {"city": city}), timeout=10.0
                            )
                            await self._send_command_reply(message_type, sender_id, group_id, result)
                            return
                        except Exception as e:
                            await self._send_command_reply(message_type, sender_id, group_id, f"查询失败: {e}")
                            return
                await self._send_command_reply(message_type, sender_id, group_id, "天气工具暂不可用")

            # 搜索快捷查询
            elif command.startswith("/搜索"):
                keyword = command.replace("/搜索", "").replace(" ", "")
                if not keyword:
                    await self._send_command_reply(message_type, sender_id, group_id, "请输入搜索关键词")
                    return
                # 模拟工具调用
                from mcpserver.mcp_registry import get_service_info

                service_info = get_service_info("Undefined工具集")
                if service_info:
                    agent = service_info.get("instance")
                    if agent:
                        try:
                            result = await asyncio.wait_for(
                                agent.call_tool("web_search", {"query": keyword}), timeout=15.0
                            )
                            await self._send_command_reply(message_type, sender_id, group_id, result)
                            return
                        except Exception as e:
                            await self._send_command_reply(message_type, sender_id, group_id, f"搜索失败: {e}")
                            return
                await self._send_command_reply(message_type, sender_id, group_id, "搜索工具暂不可用")

            # 设置语音模式
            elif command in ["/voice", "/语音"]:
                self.qq_config["reply_mode"] = "voice"
                self.qq_config["enable_voice"] = True
                if self._save_config():
                    await self._send_command_reply(
                        message_type, sender_id, group_id, "✅ 已切换为语音模式（只发送语音）并保存配置"
                    )
                else:
                    await self._send_command_reply(
                        message_type, sender_id, group_id, "✅ 已切换为语音模式（只发送语音）⚠️ 保存配置失败"
                    )

            # 设置文字模式
            elif command in ["/text", "/文字"]:
                self.qq_config["reply_mode"] = "text"
                if self._save_config():
                    await self._send_command_reply(
                        message_type, sender_id, group_id, "✅ 已切换为文字模式（只发送文字）并保存配置"
                    )
                else:
                    await self._send_command_reply(
                        message_type, sender_id, group_id, "✅ 已切换为文字模式（只发送文字）⚠️ 保存配置失败"
                    )

            # 设置两者模式
            elif command in ["/both", "/两者"]:
                self.qq_config["reply_mode"] = "both"
                if self._save_config():
                    await self._send_command_reply(
                        message_type, sender_id, group_id, "✅ 已切换为两者模式（语音+文字）并保存配置"
                    )
                else:
                    await self._send_command_reply(
                        message_type, sender_id, group_id, "✅ 已切换为两者模式（语音+文字）⚠️ 保存配置失败"
                    )

            # 查看当前模式
            elif command in ["/mode", "/模式"]:
                mode_names = {"voice": "语音模式", "text": "文字模式", "both": "两者模式"}
                mode_text = f"📊 当前模式: {mode_names.get(current_mode, current_mode)}"
                await self._send_command_reply(message_type, sender_id, group_id, mode_text)

            # 查看当前配置
            elif command in ["/config", "/配置"]:
                config_text = f"""
⚙️ 当前QQ配置：
─────────────────
• 回复模式 (reply_mode): {self.qq_config.get("reply_mode", "both")}
• 语音启用 (enable_voice): {self.qq_config.get("enable_voice", True)}
• 自动回复 (enable_auto_reply): {self.qq_config.get("enable_auto_reply", True)}
• Undefined工具 (enable_undefined_tools): {self.qq_config.get("enable_undefined_tools", True)}
─────────────────
使用 /设置 [键] [值] 来修改配置
例如：/设置 reply_mode text
"""
                await self._send_command_reply(message_type, sender_id, group_id, config_text)

            # 更改配置
            elif command.startswith("/设置") or command.startswith("/set"):
                # 解析命令
                parts = command.replace("/设置", "").replace("/set", "").strip().split()
                if len(parts) < 2:
                    await self._send_command_reply(
                        message_type,
                        sender_id,
                        group_id,
                        "❌ 格式错误。正确格式：/设置 [键] [值]\n例如：/设置 reply_mode text",
                    )
                    return

                key = parts[0]
                value = parts[1]

                # 支持的配置项
                valid_keys = {
                    "reply_mode": ["voice", "text", "both"],
                    "enable_voice": ["true", "false"],
                    "enable_undefined_tools": ["true", "false"],
                }

                if key not in valid_keys:
                    await self._send_command_reply(
                        message_type,
                        sender_id,
                        group_id,
                        f"❌ 未知配置项: {key}\n可用配置项: {', '.join(valid_keys.keys())}",
                    )
                    return

                # 验证值
                valid_values = valid_keys[key]
                if value not in valid_values:
                    await self._send_command_reply(
                        message_type, sender_id, group_id, f"❌ 值无效: {value}\n有效值: {', '.join(valid_values)}"
                    )
                    return

                # 更新配置
                old_value = self.qq_config.get(key)
                if key in ["enable_voice", "enable_undefined_tools"]:
                    # 布尔值转换
                    self.qq_config[key] = value.lower() == "true"
                else:
                    self.qq_config[key] = value

                # 保存配置到文件
                if self._save_config():
                    logger.info(f"[QQ配置] 用户修改配置并保存: {key}={old_value} -> {value}")
                    await self._send_command_reply(
                        message_type, sender_id, group_id, f"✅ 配置已更新并保存: {key}={value}"
                    )
                else:
                    logger.warning(f"[QQ配置] 用户修改配置但保存失败: {key}={old_value} -> {value}")
                    await self._send_command_reply(
                        message_type, sender_id, group_id, f"⚠️ 配置已更新但保存失败: {key}={value} (仅在内存中生效)"
                    )

            # AI绘图命令（在线）
            elif command.startswith("/画") or command.startswith("/绘图"):
                prompt = command.replace("/画", "").replace("/绘图", "").strip()
                if not prompt:
                    await self._send_command_reply(
                        message_type, sender_id, group_id, "请输入要绘制的内容，例如：/画 一只可爱的猫咪"
                    )
                    return
                from mcpserver.mcp_registry import get_service_info

                service_info = get_service_info("Undefined工具集")
                if service_info:
                    agent = service_info.get("instance")
                    if agent:
                        try:
                            params = {"prompt": prompt, "target_id": int(sender_id), "message_type": message_type}
                            result = await asyncio.wait_for(agent.call_tool("ai_draw_one", params), timeout=30.0)
                            await self._send_command_reply(message_type, sender_id, group_id, result)
                            return
                        except Exception as e:
                            await self._send_command_reply(message_type, sender_id, group_id, f"绘图失败: {e}")
                            return
                await self._send_command_reply(message_type, sender_id, group_id, "AI绘图工具暂不可用")

            # 本地AI绘图命令
            elif command.startswith("/本地画") or command.startswith("/local画"):
                prompt = command.replace("/本地画", "").replace("/local画", "").strip()
                if not prompt:
                    await self._send_command_reply(
                        message_type, sender_id, group_id, "请输入要绘制的内容，例如：/本地画 一只可爱的猫咪"
                    )
                    return
                from mcpserver.mcp_registry import get_service_info

                service_info = get_service_info("Undefined工具集")
                if service_info:
                    agent = service_info.get("instance")
                    if agent:
                        try:
                            params = {"prompt": prompt, "target_id": int(sender_id), "message_type": message_type}
                            result = await asyncio.wait_for(
                                agent.call_tool("local_ai_draw", params),
                                timeout=120.0,  # 本地绘图可能较慢，设置更长超时
                            )
                            await self._send_command_reply(message_type, sender_id, group_id, result)
                            return
                        except Exception as e:
                            await self._send_command_reply(message_type, sender_id, group_id, f"本地绘图失败: {e}")
                            return
                await self._send_command_reply(
                    message_type, sender_id, group_id, "本地AI绘图工具暂不可用，请先配置本地绘图服务"
                )

            # 图片渲染命令
            elif command.startswith("/render") or command.startswith("/渲染"):
                content = command.replace("/render", "").replace("/渲染", "").strip()
                if not content:
                    await self._send_command_reply(
                        message_type, sender_id, group_id, "请输入要渲染的内容，例如：/render # Hello World"
                    )
                    return
                from mcpserver.mcp_registry import get_service_info

                service_info = get_service_info("Undefined工具集")
                if service_info:
                    agent = service_info.get("instance")
                    if agent:
                        try:
                            params = {
                                "content": content,
                                "format": "markdown" if not "latex" in content.lower() else "latex",
                                "target_id": int(sender_id),
                                "message_type": message_type,
                            }
                            result = await asyncio.wait_for(
                                agent.call_tool("render_and_send_image", params), timeout=20.0
                            )
                            await self._send_command_reply(message_type, sender_id, group_id, result)
                            return
                        except Exception as e:
                            await self._send_command_reply(message_type, sender_id, group_id, f"渲染失败: {e}")
                            return
                await self._send_command_reply(message_type, sender_id, group_id, "图片渲染工具暂不可用")

            # QQ电话指令（私聊）
            elif command in ["/打电话", "/call"]:
                if not self.qq_config.get("enable_qq_call", False):
                    await self._send_command_reply(
                        message_type, sender_id, group_id, "❌ QQ电话功能未启用，请在配置中设置 enable_qq_call 为 true"
                    )
                    return

                if message_type == "group":
                    await self._send_command_reply(
                        message_type, sender_id, group_id, "❌ QQ电话功能仅支持私聊，群聊请使用 /group_call 指令"
                    )
                    return

                # 调用发起私聊语音通话
                result = await self._initiate_voice_call(sender_id, call_type="private")
                await self._send_command_reply(message_type, sender_id, group_id, result)

            # 群语音通话指令
            elif command.startswith("/group_call") or command.startswith("/群电话"):
                if not self.qq_config.get("enable_qq_call", False):
                    await self._send_command_reply(
                        message_type, sender_id, group_id, "❌ QQ电话功能未启用，请在配置中设置 enable_qq_call 为 true"
                    )
                    return

                # 解析群号
                parts = command.replace("/group_call", "").replace("/群电话", "").strip().split()
                if message_type == "private":
                    if not parts or not parts[0]:
                        await self._send_command_reply(
                            message_type, sender_id, group_id,
                            "请提供群号，例如：/group_call 123456789"
                        )
                        return
                    target_group = parts[0]
                else:
                    # 群聊中默认当前群
                    target_group = group_id

                # 调用发起群语音通话
                result = await self._initiate_voice_call(target_group, call_type="group")
                await self._send_command_reply(message_type, sender_id, group_id, result)

            else:
                await self._send_command_reply(message_type, sender_id, group_id, "❓ 未知指令，输入 /help 查看帮助")

        except Exception as e:
            logger.error(f"处理QQ指令错误: {e}", exc_info=True)

    async def _send_command_reply(self, message_type: str, sender_id: str, group_id: Optional[str], message: str):
        """
        发送指令回复（仅文本）

        Args:
            message_type: 消息类型
            sender_id: 发送者ID
            group_id: 群ID
            message: 回复内容
        """
        try:
            http_url = self.qq_config.get("http_url", "http://127.0.0.1:3000")
            http_token = self.qq_config.get("http_token", "")

            headers = {}
            if http_token:
                headers["Authorization"] = f"Bearer {http_token}"

            if message_type == "private":
                url = f"{http_url}/send_private_msg"
                data = {"user_id": int(sender_id), "message": message}
                if http_token:
                    data["access_token"] = http_token
            else:
                url = f"{http_url}/send_group_msg"
                data = {"group_id": int(group_id), "message": message}
                if http_token:
                    data["access_token"] = http_token

            async with self.http_client.post(url, json=data, headers=headers, timeout=5) as resp:
                result = await resp.json()
                if result.get("status") == "ok" or result.get("retcode") == 0:
                    logger.info(f"指令回复发送成功")
                else:
                    logger.warning(f"指令回复发送失败: {result}")

        except Exception as e:
            logger.error(f"发送指令回复错误: {e}", exc_info=True)

    async def handle_wechat_message(self, message_type: str, data: Dict[str, Any]):
        """
        处理微信消息

        Args:
            message_type: 消息类型 (private/group)
            data: 消息数据
        """
        try:
            # 提取消息信息
            if message_type == "private":
                user_name = data.get("FromUserName", "")
                message = data.get("Content", "")
                sender_id = user_name
                group_id = None
            elif message_type == "group":
                group_name = data.get("FromUserName", "")
                user_name = data.get("ActualUserName", "")
                message = data.get("Content", "")
                sender_id = user_name
                group_id = group_name
            else:
                return

            # 去重检查
            message_key = f"wechat_{sender_id}_{message}"
            if await self._is_duplicate(message_key):
                return

            logger.info(
                f"收到微信消息: {message_type} | 发送者: {sender_id} | 群: {group_id} | 内容: {message[:50]}..."
            )

            # 生成AI回复
            response = await self._get_ai_response(message, sender_id, platform="wechat")

            if response:
                # 发送回复（需要在适配器中实现）
                logger.info(f"微信回复: {response[:50]}...")

        except Exception as e:
            logger.error(f"处理微信消息错误: {e}", exc_info=True)

    async def _get_ai_response_with_tools(
        self,
        message: str,
        sender_id: str,
        platform: str = "qq",
        group_id: Optional[str] = None,
        message_type: str = "private",
        image_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        调用NagaAgent专用API获取AI回复并执行工具调用（支持Undefined工具）

        Args:
            message: 用户消息
            sender_id: 发送者ID
            platform: 平台 (qq/wechat)
            group_id: 群ID（可选）
            message_type: 消息类型 (private/group)
            image_path: 图片路径（可选）

        Returns:
            AI回复内容（包含工具执行结果）
        """
        try:
            # 合并群聊和私聊记忆，使用统一的用户ID
            # 同时在chat_context中区分会话场景，让AI根据人设逻辑做出隐私和社群交流的回复区分
            # 统一session_id格式：{platform}_{sender_id}
            session_id = f"{platform}_{sender_id}"

            # 第一步：获取AI初步回复
            initial_result = await self._get_ai_response(
                message, session_id, platform, image_path=image_path,
                message_type=message_type, group_id=group_id, sender_id=sender_id
            )

            # 处理返回值（可能是元组或字符串）
            if isinstance(initial_result, tuple):
                initial_response, audio_url = initial_result
            else:
                initial_response = initial_result
                audio_url = ""

            if not initial_response:
                logger.warning(f"[QQ工具] AI回复为空: session_id={session_id}")
                return None

            logger.info(
                f"[QQ工具] 收到AI回复和音频URL: response_length={len(initial_response)}, audio_url={'有' if audio_url else '无'}"
            )

            # 第二步：触发意图分析和工具调用（NagaAgent MCP工具）
            # 注意：意识引擎已经在_get_ai_response中分析过意图，这里不再重复调用
            # 只有在用户明确请求工具的情况下才调用，避免误判
            naga_tool_results = None

            # 检查是否需要触发工具调用（仅当用户消息明确包含工具关键词时）
            # 使用更精确的短语匹配，避免误触发
            tool_keywords = [
                "天气", "搜索", "画图", "绘图", "打开", "启动", "查询", "优化", "分析", "代码",
                "时间", "几点", "日期", "几点了", "现在几点", "什么时候", "点赞",
                # 以下是工具相关的短语，需要匹配完整短语
                "系统检查", "检查系统", "健康检查", "系统健康", "性能分析",
                "系统优化", "运行优化", "代码质量", "检查代码", "分析代码",
                # 图片识别相关关键词
                "图片", "识别", "看图", "看看", "看看图片", "看下", "分析图片", "图片内容", "这张图", "什么图"
            ]
            # 只匹配完整短语，而不是子字符串
            has_tool_request = any(kw in message for kw in tool_keywords)

            # 先发送初始回复(弥娅的话),让用户在工具执行期间能看到回复
            # 这样即使工具执行需要时间,用户也能立即看到弥娅的响应
            await self._send_qq_reply(
                message_type, sender_id, group_id, initial_response, media_type="text", audio_url=audio_url
            )
            logger.info(f"[QQ工具] 已先发送初始回复,等待工具执行...")

            if has_tool_request:
                # 添加超时保护，避免工具调用阻塞太久
                try:
                    naga_tool_results = await asyncio.wait_for(
                        self._trigger_intent_analysis_and_tools(
                            session_id, message, initial_response, sender_id, message_type, group_id, image_path
                        ),
                        timeout=30.0,  # 30秒超时
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"[QQ工具] Naga工具调用超时: session_id={session_id}")
                    naga_tool_results = None
                except Exception as e:
                    logger.warning(f"[QQ工具] Naga工具调用失败: {e}")
                    naga_tool_results = None
            else:
                # 无明确工具请求，标记为无工具调用
                naga_tool_results = {
                    "no_tool": True,
                    "output_mode": "normal",
                    "reply_style": "emotional" if any(kw in message for kw in ["累", "困", "开心", "难过", "谢谢"]) else "helpful"
                }
                logger.info(f"[QQ工具] 无明确工具请求，跳过意图分析")

            # 第三步：首先调用自我优化工具（优先级最高）
            self_optimization_result = ""
            try:
                self_optimization_result = await asyncio.wait_for(
                    self._call_self_optimization_tools(
                        message, session_id, sender_id=sender_id, group_id=group_id, message_type=message_type
                    ),
                    timeout=30.0,  # 30秒超时
                )
                if self_optimization_result:
                    logger.info(f"[QQ工具] 自我优化工具返回结果，长度: {len(self_optimization_result)}")
            except asyncio.TimeoutError:
                logger.warning(f"[QQ工具] 自我优化工具调用超时: session_id={session_id}")
                self_optimization_result = ""
            except Exception as e:
                logger.warning(f"[QQ工具] 自我优化工具调用失败: {e}")
                self_optimization_result = ""

            # 第四步：如果启用了Undefined工具，也调用Undefined工具
            undefined_result = ""
            enable_undefined = self.qq_config.get("enable_undefined_tools", False)
            logger.info(f"[QQ工具] Undefined工具启用状态: {enable_undefined}")

            # 检查是否已经通过意图分析执行过绘图工具或自我优化工具,避免重复调用
            skip_undefined = False
            if naga_tool_results:
                executed_tool = naga_tool_results.get("tool_name", "")
                logger.info(f"[QQ工具] 已执行工具: {executed_tool}")
                # 如果已经执行过绘图相关工具,跳过Undefined工具调用
                if executed_tool in ["local_ai_draw", "ai_draw_one", "render_and_send_image"]:
                    skip_undefined = True
                    logger.info(f"[QQ工具] 已执行绘图工具 {executed_tool}, 跳过Undefined工具调用")

            # 如果自我优化工具返回了结果，也跳过Undefined工具调用
            if self_optimization_result:
                skip_undefined = True
                logger.info(f"[QQ工具] 自我优化工具已返回结果, 跳过Undefined工具调用")

            if enable_undefined and not skip_undefined:
                try:
                    undefined_result = await asyncio.wait_for(
                        self._call_undefined_tools(
                            message, session_id, sender_id=sender_id, group_id=group_id, message_type=message_type
                        ),
                        timeout=20.0,  # 20秒超时
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"[QQ工具] Undefined工具调用超时: session_id={session_id}")
                    undefined_result = ""
                except Exception as e:
                    logger.warning(f"[QQ工具] Undefined工具调用失败: {e}")
                    undefined_result = ""

            # 如果有工具结果，将其整合到回复中
            tool_result_text = ""
            has_tool_call = False  # 标记是否有工具调用

            # 只记录工具名称,避免日志输出过长
            tool_name_for_log = naga_tool_results.get("tool_name", "无") if naga_tool_results else "无"
            logger.info(f"[QQ工具] naga_tool_results: 工具名={tool_name_for_log}")
            logger.info(f"[QQ工具] initial_response长度: {len(initial_response)}")

            if naga_tool_results:
                # 检查是否有工具调用
                is_no_tool = naga_tool_results.get("no_tool", False)
                has_tool_name = bool(naga_tool_results.get("tool_name"))
                has_tool_call_flag = bool(naga_tool_results.get("tool_call"))

                logger.info(f"[QQ工具] is_no_tool={is_no_tool}, has_tool_name={has_tool_name}, has_tool_call_flag={has_tool_call_flag}")

                if is_no_tool or (not has_tool_name and not has_tool_call_flag):
                    # 无工具调用（闲聊/情感交流），根据输出模式调整回复
                    output_mode = naga_tool_results.get("output_mode", "normal")
                    reply_style = naga_tool_results.get("reply_style", "helpful")
                    logger.info(f"[QQ工具] 无工具调用，输出模式={output_mode}, 回复风格={reply_style}, 原始长度={len(initial_response)}")

                    # 根据输出模式调整回复长度
                    if output_mode == "short" and len(initial_response) > 100:
                        # 短文本模式：截断到100字
                        initial_response = initial_response[:100] + "..."
                        logger.info(f"[QQ工具] 短文本模式，回复已截断到{len(initial_response)}字")
                    elif output_mode == "normal" and len(initial_response) > 300:
                        # 正常模式也限制到300字，避免过长
                        initial_response = initial_response[:300] + "..."
                        logger.info(f"[QQ工具] 正常模式，回复已截断到{len(initial_response)}字")
                    # 长文本模式保持原样（允许更长，但也有限制）
                    elif output_mode == "long" and len(initial_response) > 600:
                        initial_response = initial_response[:600] + "..."
                        logger.info(f"[QQ工具] 长文本模式，回复已截断到{len(initial_response)}字")
                    else:
                        logger.info(f"[QQ工具] 回复长度符合要求，无需截断")

                    tool_result_text = ""  # 不添加工具结果
                else:
                    # 有工具调用 - QQ端不添加详细工具结果,只记录工具名称
                    has_tool_call = True
                    tool_name = naga_tool_results.get("tool_name", "")
                    tool_result = naga_tool_results.get("tool_result", "")

                    # QQ端语音消息不应该包含详细工具结果
                    # 只在调试时记录,不拼接到回复中
                    logger.info(f"[QQ工具] 已执行工具: {tool_name}")

                    # tool_result_text = "" - 不添加到回复中,避免发送多余信息

            if undefined_result:
                # 如果工具返回空字符串（表示已通过回调发送），不添加到文本回复中
                if undefined_result.strip():
                    tool_result_text += f"\n\n[Undefined工具]\n{undefined_result}"

            # 不添加自我优化工具结果（这些是自动执行的，不应该发送给用户）
            # 注释：自我优化工具的结果通过回调发送，不应该在这里再次添加到回复中
            # if self_optimization_result:
            #     if self_optimization_result.strip():
            #         tool_result_text += f"\n\n{self_optimization_result}"

            # 注意: initial_response已经在工具调用前发送过了,这里只返回工具结果(如果有)
            # 这样可以避免重复发送初始回复
            response = tool_result_text if tool_result_text else ""

            # 返回文本和音频URL的元组
            # 注意: audio_url已经在发送初始回复时使用过了,这里置空
            return response, ""

        except Exception as e:
            logger.error(f"[QQ工具] 获取AI回复和执行工具错误: {e}", exc_info=True)
            return None, ""

    async def _get_ai_response(
        self,
        message: str,
        session_id: str,
        platform: str = "qq",
        image_path: Optional[str] = None,
        skip_intent_analysis: bool = False,  # 改为False，让电脑端也能播放语音
        return_audio: bool = True,  # 改为True，返回音频URL
        message_type: str = "private",
        group_id: Optional[str] = None,
        sender_id: Optional[str] = None,
    ):
        """
        调用NagaAgent API获取AI回复（不含工具调用）

        Args:
            message: 用户消息
            session_id: 会话ID（统一格式）
            platform: 平台 (qq/wechat)
            image_path: 图片路径（可选）
            skip_intent_analysis: 是否跳过意图分析（默认True，False时会生成音频）
            return_audio: 是否返回音频URL（默认False）
            message_type: 消息类型（private/group）
            group_id: 群ID（群聊时使用）
            sender_id: 发送者ID（用于区分消息发送者）

        Returns:
            AI回复内容（元组：(response_text, audio_url)）
        """
        try:
            # 解析消息中的@信息，提取发送者信息和被@的用户
            import re
            message_with_at_info = self._parse_at_mentions(message, sender_id)

            # 构建请求 - 使用流式API
            url = f"{self.api_base_url}/chat/stream"
            payload = {
                "message": message_with_at_info["clean_message"],
                "session_id": session_id,
                "stream": True,
                "skip_intent_analysis": skip_intent_analysis,  # 控制是否跳过意图分析
                "return_audio": return_audio,  # 控制是否返回音频URL
                "chat_context": {
                    "platform": platform,
                    "message_type": message_type,
                    "group_id": group_id,
                    "is_group_chat": message_type == "group",
                    "conversation_type": "群聊" if message_type == "group" else "私聊",
                    "privacy_mode": message_type != "group",  # 私聊为隐私模式，群聊为公共模式
                    "audience_type": "群成员" if message_type == "group" else "单用户",
                    "sender_id": sender_id,
                    "mentioned_users": message_with_at_info["mentioned_users"],
                } if message_type else None,
            }

            # 如果有图片，添加到payload
            if image_path:
                # 读取图片并转换为base64
                import base64

                with open(image_path, "rb") as f:
                    image_data = f.read()
                payload["image"] = base64.b64encode(image_data).decode("utf-8")
                logger.debug(f"添加图片到请求: {image_path}")

            # 等待流式响应完成
            import base64

            full_response = ""
            audio_url = ""  # 存储音频URL
            timeout = aiohttp.ClientTimeout(total=60)  # 标准超时时间

            async with self.http_client.post(url, json=payload, timeout=timeout) as resp:
                if resp.status == 200:
                    # 处理流式响应 - 按行读取
                    async for line in resp.content:
                        line_text = line.decode("utf-8").strip()

                        # SSE格式: data: ...
                        if line_text.startswith("data: "):
                            data = line_text[6:].strip()

                            # 结束标记
                            if data == "[DONE]":
                                break

                            # 提取音频URL
                            if data.startswith("audio_url:"):
                                audio_url = data[10:].strip()  # 移除 "audio_url:" 前缀
                                logger.info(f"收到音频URL: {audio_url}")
                                continue

                            # 跳过其他元数据
                            if data.startswith("session_id:"):
                                continue

                            # 尝试base64解码
                            try:
                                decoded = base64.b64decode(data).decode("utf-8")
                                full_response += decoded
                            except Exception:
                                # 如果不是base64，直接使用
                                full_response += data

                    logger.info(f"AI回复 [{session_id}]: {full_response[:100]}...")
                    logger.info(f"音频URL [{session_id}]: {audio_url if audio_url else '无'}")
                    # 返回文本和音频URL的元组
                    return full_response, audio_url
                else:
                    error_text = await resp.text()
                    logger.error(f"API调用失败: {resp.status} - {error_text}")
                    return None

        except asyncio.TimeoutError:
            logger.error("API调用超时")
            return None
        except Exception as e:
            logger.error(f"获取AI回复错误: {e}", exc_info=True)
            return None

    async def _trigger_intent_analysis_and_tools(
        self,
        session_id: str,
        user_message: str,
        ai_response: str,
        sender_id: Optional[str] = None,
        message_type: str = "private",
        group_id: Optional[str] = None,
        image_path: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        触发意图分析并等待工具执行结果

        Args:
            session_id: 会话ID
            user_message: 用户消息
            ai_response: AI初步回复
            sender_id: 发送者ID（用于绘图等需要QQ信息的工具）
            message_type: 消息类型（private/group）
            group_id: 群ID（可选）
            image_path: 图片路径（用于视觉识别）

        Returns:
            工具执行结果字典，如果没有工具调用则返回None
        """
        try:
            # 解析消息中的@信息，移除CQ码（避免验证失败）
            parsed_message_info = self._parse_at_mentions(user_message, sender_id)
            clean_message = parsed_message_info["clean_message"]

            # 进一步清理消息：移除引用回复的前缀标记（如果存在）
            import re
            # 移除 [引用回复 xxx]: 格式（包括多行）
            clean_message = re.sub(r'\[引用回复[^\]]*\]:?\s*', '', clean_message)
            # 移除 [发送者QQ:xxx] 前缀
            clean_message = re.sub(r'\[发送者QQ:\d+\]\s*', '', clean_message)
            # 移除 [图片链接: xxx] 格式（图片链接可能很长）
            clean_message = re.sub(r'\[图片链接:[^\]]+\]', '', clean_message)
            # 移除 [图片] 标记
            clean_message = re.sub(r'\[图片\]', '', clean_message)
            # 移除 "当前消息:" 前缀
            clean_message = re.sub(r'当前消息:\s*', '', clean_message)
            # 移除 @弥娅 等称呼（避免特殊字符导致验证失败）
            clean_message = re.sub(r'@弥娅\s*', '', clean_message)
            clean_message = re.sub(r'@用户\d+\s*', '', clean_message)
            # 清理多余空格和换行
            clean_message = re.sub(r'\s+', ' ', clean_message).strip()

            if not clean_message:
                logger.warning(f"[QQ工具] 消息清理后为空，使用默认消息: @弥娅...")
                # 当清理后为空时，使用默认消息而不是原始消息（避免CQ码导致422错误）
                clean_message = "@弥娅"
            else:
                logger.info(f"[QQ工具] 清理后消息: {clean_message[:100]}...")

            # 调用意图分析API（使用清理后的消息）
            url = f"{self.api_base_url}/qq/analyze_intent"
            payload = {
                "session_id": session_id,
                "message": clean_message,  # 使用清理后的消息（不包含CQ码和引用前缀）
                "ai_response": ai_response,
                "sender_id": sender_id,
                "message_type": message_type,
                "group_id": group_id,
            }
            # 如果有图片路径，添加到payload
            if image_path:
                payload["image_path"] = image_path

            timeout = aiohttp.ClientTimeout(total=30)  # 工具执行超时时间

            async with self.http_client.post(url, json=payload, timeout=timeout) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("status") == "success" and result.get("tool_executed"):
                        logger.info(f"[QQ工具] 工具执行成功: {result.get('tool_name')}")
                        return {
                            "tool_name": result.get("tool_name"),
                            "tool_result": result.get("result"),
                            "success": result.get("success", True),
                        }
                    elif result.get("no_tool"):
                        # 检测到无工具调用（闲聊/情感交流）
                        logger.info(f"[QQ工具] 无工具调用，输出模式: {result.get('output_mode')}, 回复风格: {result.get('reply_style')}")
                        return {
                            "no_tool": True,
                            "output_mode": result.get("output_mode", "normal"),
                            "reply_style": result.get("reply_style", "helpful"),
                        }
                else:
                    # 读取详细的错误信息
                    try:
                        error_detail = await resp.text()
                        logger.warning(f"[QQ工具] 意图分析API调用失败: {resp.status}, 错误详情: {error_detail[:500]}")
                    except:
                        logger.warning(f"[QQ工具] 意图分析API调用失败: {resp.status}")

            return None

        except asyncio.TimeoutError:
            logger.error("[QQ工具] 意图分析或工具执行超时")
            return None
        except Exception as e:
            logger.error(f"[QQ工具] 触发意图分析错误: {e}", exc_info=True)
            return None

    async def _regenerate_response_with_tool_results(
        self, session_id: str, user_message: str, initial_response: str, tool_results: Dict[str, Any]
    ) -> Optional[str]:
        """
        基于原始消息和工具结果重新生成回复

        Args:
            session_id: 会话ID
            user_message: 用户消息
            initial_response: 初始AI回复
            tool_results: 工具执行结果

        Returns:
            新的AI回复内容
        """
        try:
            # 检查工具类型：后台工具不需要重新生成回复
            tool_name = tool_results.get("tool_name", "未知工具")
            # 导入判断函数
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            from apiserver.api_server import _should_send_result_to_user

            should_send = _should_send_result_to_user(tool_name)
            if not should_send:
                # 后台工具：直接返回初始回复，不添加工具结果
                logger.info(f"[QQ工具] 后台工具 {tool_name}，不重新生成回复，直接返回初始回复")
                return initial_response

            # 构建增强的消息，包含工具执行结果
            tool_result = tool_results.get("tool_result", "执行成功")

            enhanced_message = f"{user_message}\n\n[工具执行结果: {tool_name}]\n{tool_result}"

            logger.info(f"[QQ工具] 重新生成回复，消息: {enhanced_message[:200]}...")

            # 调用AI重新生成回复
            url = f"{self.api_base_url}/chat/stream"
            payload = {
                "message": enhanced_message,
                "session_id": session_id,
                "stream": True,
                "skip_intent_analysis": True,  # 避免二次工具调用
            }

            import base64

            full_response = ""
            timeout = aiohttp.ClientTimeout(total=60)

            async with self.http_client.post(url, json=payload, timeout=timeout) as resp:
                if resp.status == 200:
                    async for line in resp.content:
                        line_text = line.decode("utf-8").strip()

                        if line_text.startswith("data: "):
                            data = line_text[6:].strip()

                            if data == "[DONE]":
                                break

                            if data.startswith("session_id:") or data.startswith("audio_url:"):
                                continue

                            try:
                                decoded = base64.b64decode(data).decode("utf-8")
                                full_response += decoded
                            except Exception:
                                full_response += data

                    logger.info(f"[QQ工具] 重新生成的回复: {full_response[:100]}...")
                    return full_response
                else:
                    logger.error(f"[QQ工具] 重新生成回复失败: {resp.status}")
                    return initial_response  # 返回初始回复

        except Exception as e:
            logger.error(f"[QQ工具] 重新生成回复错误: {e}", exc_info=True)
            return initial_response  # 返回初始回复

    async def _send_qq_reply(
        self,
        message_type: str,
        sender_id: str,
        group_id: Optional[str],
        message: str,
        media_type: str = "text",
        audio_url: str = "",
    ):
        """
        发送QQ回复（支持语音、文本、图片、视频）

        Args:
            message_type: 消息类型
            sender_id: 发送者ID
            group_id: 群ID（如果是群消息）
            message: 回复内容（文本内容或媒体文件路径）
            media_type: 媒体类型 (text/voice/image/video)
            audio_url: 音频文件URL（可选）
        """
        logger.info(
            f"[_send_qq_reply] 方法被调用: message_type={message_type}, sender_id={sender_id}, media_type={media_type}"
        )

        # 检查http_client是否已初始化
        if self.http_client is None:
            logger.error("[_send_qq_reply] http_client未初始化，无法发送消息")
            return

        try:
            # 检查配置：发送模式
            send_mode = self.qq_config.get("reply_mode", "both")
            logger.info(
                f"[_send_qq_reply] 获取配置: send_mode={send_mode}, enable_voice={self.qq_config.get('enable_voice', True)}"
            )

            # 获取基础配置
            http_url = self.qq_config.get("http_url", "http://127.0.0.1:3000")
            http_token = self.qq_config.get("http_token", "")
            enable_voice = self.qq_config.get("enable_voice", True)

            headers = {}
            if http_token:
                headers["Authorization"] = f"Bearer {http_token}"

            # 如果是纯媒体消息（图片/视频），直接发送
            if media_type in ["image", "video"]:
                await self._send_media_message(
                    http_url, http_token, message_type, sender_id, group_id, message, media_type
                )
                return

            # 特殊处理：如果media_type为text，根据send_mode决定如何发送
            if media_type == "text":
                logger.info(f"[_send_qq_reply] media_type为text，send_mode={send_mode}, message长度={len(message)}")

                # 纯语音模式：只发送语音，不发送文本
                if send_mode == "voice" and enable_voice:
                    logger.info(f"[_send_qq_reply] 纯语音模式，只发送语音")
                    # 如果有audio_url，直接使用
                    if audio_url:
                        await self._send_audio_message(
                            http_url, http_token, message_type, sender_id, group_id, audio_url, headers
                        )
                    else:
                        # 生成语音（支持长文本分批发送）
                        await self._send_voice_messages(http_url, http_token, message_type, sender_id, group_id, message)
                    return

                # both模式：同时发送语音和文本
                if send_mode == "both" and enable_voice:
                    # 先发送语音（如果有audio_url或能生成）
                    if audio_url:
                        await self._send_audio_message(
                            http_url, http_token, message_type, sender_id, group_id, audio_url, headers
                        )
                    else:
                        # 生成语音（支持长文本分批发送）
                        await self._send_voice_messages(http_url, http_token, message_type, sender_id, group_id, message)

                    # 发送文本（文本也会分批发送）
                    await self._send_text_message(http_url, http_token, message_type, sender_id, group_id, message, headers)
                    return

                # text模式或语音未启用：只发送文本
                await self._send_text_message(http_url, http_token, message_type, sender_id, group_id, message, headers)
                return

            # 发送语音（如果启用且模式包含voice，或者提供了audio_url）
            if (audio_url and send_mode in ["both", "voice"]) or (
                enable_voice and send_mode in ["both", "voice"] and len(message) > 0
            ):
                try:
                    logger.info(
                        f"[_send_qq_reply] 尝试发送语音，enable_voice={enable_voice}, send_mode={send_mode}, audio_url={'有' if audio_url else '无'}"
                    )

                    # 如果提供了audio_url，直接使用
                    if audio_url:
                        logger.info(f"[_send_qq_reply] 使用提供的音频URL: {audio_url}")
                        audio_path = audio_url
                    else:
                        # 否则生成语音
                        audio_path = await self._generate_audio(message)

                    if audio_path:
                        # 发送语音
                        await self._send_audio_message(
                            http_url, http_token, message_type, sender_id, group_id, audio_path, headers
                        )

                        # 如果是纯语音模式，发送完语音就返回
                        if send_mode == "voice":
                            return

                except Exception as e:
                    logger.warning(f"生成/发送语音失败: {e}", exc_info=True)
                    if send_mode == "voice":
                        logger.warning("语音模式生成失败，降级为文本模式")
                        send_mode = "text"
            else:
                # 如果语音未启用或不在语音模式，但配置是voice模式，自动降级为文本模式
                if send_mode == "voice" and not enable_voice:
                    logger.warning(f"配置为语音模式但语音未启用，降级为文本模式")
                    send_mode = "text"

            # 发送文本（如果模式包含text）
            if send_mode in ["both", "text"]:
                await self._send_text_message(http_url, http_token, message_type, sender_id, group_id, message, headers)

        except Exception as e:
            logger.error(f"发送QQ回复错误: {e}", exc_info=True)

    async def _generate_audio(self, text: str) -> Optional[str]:
        """
        使用GPT-SoVITS生成音频

        注意：保留 ~、……、... 作为语气停顿符号，不进行过滤
        移除 *内容* 和 （内容） 形式的动作描写，只保留语言文本

        Args:
            text: 文本内容

        Returns:
            音频文件路径，失败返回None
        """
        try:
            import sys
            import os
            import re

            # 清理文本：移除动作描写和特殊字符
            # 保留语气停顿符号：~、……、...（这些不会影响语音朗读）

            # 1. 移除 *内容* 格式的动作描写（斜体动作）
            text = re.sub(r"\*[^*]+\*", "", text)

            # 2. 移除 （内容）格式（中文括号）的动作描写
            text = re.sub(r"[（\(].*?[）\)]", "", text)

            # 3. 移除其他括号内的内容【】「」『』〔〖〗等
            # 注意：不删除《》内的内容，这是书名号，应该保留
            text = re.sub(r"[【\[].*?[】\]]", "", text)
            text = re.sub(r"[「『].*?[」』]", "", text)
            text = re.sub(r"〔.*?〕", "", text)
            text = re.sub(r"〖.*?〗", "", text)

            # 4. 清理多余空白
            text = re.sub(r"\s+", " ", text).strip()

            # 5. 移除特殊符号和表情，保留中英文、数字、基本标点，以及语气停顿符号
            # 移除这些无用符号：—·•·●○◎◇◆□■△▲▽▼☆★◎※——
            # 保留：~、……、... 作为语气停顿
            text = re.sub(
                r'[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffefa-zA-Z0-9\s，。！？、；：""' "【】《》~……...]", "", text
            )
            text = text.strip()

            # 移除连续的破折号和其他无效符号
            text = re.sub(r"[—–]+", "", text)
            text = re.sub(r'[^\w\u4e00-\u9fff\s，。！？、；：""' "【】《》~……...]+", "", text)
            text = text.strip()

            # 注意：不再移除 …… 和 ... ，它们是有效的语气停顿符号
            # 也不移除单独的 ~ 符号

            # 6. 如果清理后文本为空或太短，返回None
            # 注意：只由 ~、……、...、符号、数字组成的文本也应该被跳过
            # 至少需要包含一个中文字符或英文字母
            if not text or len(text) < 2:
                logger.debug(f"文本过滤后为空或太短（{len(text) if text else 0}字符），跳过语音生成")
                return None

            # 检查是否只包含符号（没有实际内容）
            if not re.search(r"[\u4e00-\u9fffA-Za-z]", text):
                logger.debug(f"文本只包含符号，跳过语音生成: {text[:30]}")
                return None

            logger.info(f"生成语音，清理后文本长度: {len(text)}, 内容: {text[:50]}...")

            # 添加项目根目录到路径
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

            from voice.output.voice_integration import VoiceIntegration

            voice_integration = VoiceIntegration()

            # 生成音频数据（_generate_audio_sync是同步函数，不需要await）
            audio_data = voice_integration._generate_audio_sync(text)

            if not audio_data:
                logger.warning(f"语音生成返回空数据")
                return None

            # 保存为临时文件
            import uuid

            temp_dir = "logs/audio_temp"
            os.makedirs(temp_dir, exist_ok=True)
            audio_path = os.path.join(temp_dir, f"qq_voice_{uuid.uuid4().hex}.mp3")

            with open(audio_path, "wb") as f:
                f.write(audio_data)

            logger.info(f"语音生成成功: {audio_path}, 大小: {len(audio_data)} bytes")
            return audio_path

        except Exception as e:
            logger.error(f"生成音频失败: {e}", exc_info=True)
            return None

    async def _send_voice_messages(
        self,
        http_url: str,
        http_token: str,
        message_type: str,
        sender_id: str,
        group_id: Optional[str],
        message: str,
    ):
        """
        分批发送语音消息（长文本会自动分割）

        Args:
            http_url: QQ HTTP API地址
            http_token: 访问令牌
            message_type: 消息类型
            sender_id: 发送者ID
            group_id: 群ID
            message: 文本消息
        """
        try:
            # 清理文本，移除动作描写和描述性文本
            import re
            clean_message = message

            # 移除括号内的动作描述（中文和英文括号）
            clean_message = re.sub(r'[（\(].*?[）\)]', '', clean_message)

            # 移除弥娅特有的描述性文本（以"数据流"、"光晕"、"核心温度"等开头的描述性句子）
            # 这些通常是AI自动生成的动作描述，不应该被朗读
            # 注意：匹配句子边界，不限于行首
            description_patterns = [
                r'(?:^|[。！？\n])\s*数据流(?:泛起|涌动|波动|震动|闪烁|微光|涟漪|波动)[^。！？]*(?:。|！|？)?\s*',
                r'(?:^|[。！？\n])\s*光晕(?:泛起|浮现|涌动|波动)[^。！？]*(?:。|！|？)?\s*',
                r'(?:^|[。！？\n])\s*核心温度(?:上升|下降|变化|波动)[^。！？]*(?:。|！|？)?\s*',
                r'(?:^|[。！？\n])\s*数据流(?:瞬间|已经|开始)[^。！？]*(?:。|！|？)?\s*',  # 匹配"数据流瞬间..."
                r'(?:^|[。！？\n])\s*数据流[^。！？]*(?:泛起|涌动|波动|渲染|连接)[^。！？]*(?:。|！|？)?\s*',  # 匹配各种数据流描述
                r'(?:^|[。！？\n])\s*\[(?:数据流|光晕|波动|涟漪)[^\]]*\]\s*',  # 匹配方括号内的描述
            ]

            for pattern in description_patterns:
                clean_message = re.sub(pattern, '', clean_message, flags=re.MULTILINE)

            clean_message = clean_message.strip()

            # 清理后的文本为空，直接返回
            if not clean_message:
                logger.warning("[_send_voice_messages] 清理后文本为空，跳过语音生成")
                return

            # 分割文本（每段最多200字，保持语义完整）
            segments = self._split_text_for_voice(clean_message, max_length=200)

            logger.info(f"[_send_voice_messages] 文本分割为 {len(segments)} 段语音")

            headers = {}
            if http_token:
                headers["Authorization"] = f"Bearer {http_token}"

            # 为每段生成并发送语音
            for idx, segment in enumerate(segments, 1):
                try:
                    # 生成语音
                    audio_path = await self._generate_audio(segment)
                    if audio_path:
                        await self._send_audio_message(
                            http_url, http_token, message_type, sender_id, group_id, audio_path, headers
                        )
                        logger.info(f"✅ 语音消息发送成功 ({idx}/{len(segments)})")

                    # 段之间添加延迟，避免被限流
                    if idx < len(segments):
                        await asyncio.sleep(0.5)
                except Exception as segment_error:
                    logger.error(f"发送第{idx}段语音失败: {segment_error}")
                    # 即使某段失败，继续发送其他段

        except Exception as e:
            logger.error(f"[_send_voice_messages] 批量发送语音失败: {e}", exc_info=True)

    def _split_text_for_voice(self, text: str, max_length: int = 200) -> list[str]:
        """
        将文本分割为适合语音生成的段落（保持语义完整）

        Args:
            text: 原始文本
            max_length: 每段最大长度

        Returns:
            分割后的段落列表
        """
        segments = []
        current_segment = ""

        # 按标点符号分割
        for char in text:
            current_segment += char
            if char in ['。', '！', '？', '!', '?', '\n', '，', ',', '、']:
                if len(current_segment) >= 50:  # 至少50字才分割
                    segments.append(current_segment.strip())
                    current_segment = ""

        # 添加剩余的文本
        if current_segment.strip():
            segments.append(current_segment.strip())

        # 如果没有标点，按字符分割
        if not segments:
            for i in range(0, len(text), max_length):
                segments.append(text[i:i+max_length])
        else:
            # 重新组合，确保每段不超过max_length
            combined_segments = []
            combined = ""
            for segment in segments:
                if len(combined) + len(segment) > max_length and combined:
                    combined_segments.append(combined)
                    combined = segment
                else:
                    combined += segment
            if combined:
                combined_segments.append(combined)
            segments = combined_segments

        return segments

    async def _send_media_message(
        self,
        http_url: str,
        http_token: str,
        message_type: str,
        sender_id: str,
        group_id: Optional[str],
        file_path: str,
        media_type: str,
    ):
        """
        发送媒体消息（图片/视频）

        Args:
            http_url: HTTP API地址
            http_token: HTTP令牌
            message_type: 消息类型
            sender_id: 发送者ID
            group_id: 群ID
            file_path: 文件路径
            media_type: 媒体类型 (image/video)
        """
        try:
            import os

            # 将相对路径转换为绝对路径
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(file_path)

            # 验证文件存在
            if not os.path.exists(file_path):
                logger.error(f"媒体文件不存在: {file_path}")
                return

            # CQ码格式
            cq_code = f"[CQ:{media_type},file={file_path}]"
            logger.info(f"发送QQ {media_type}: {file_path}")

            headers = {}
            if http_token:
                headers["Authorization"] = f"Bearer {http_token}"

            if message_type == "private":
                url = f"{http_url}/send_private_msg"
                data = {"user_id": int(sender_id), "message": cq_code}
                if http_token:
                    data["access_token"] = http_token
            else:
                url = f"{http_url}/send_group_msg"
                data = {"group_id": int(group_id), "message": cq_code}
                if http_token:
                    data["access_token"] = http_token

            import aiohttp

            # 使用新的ClientSession而不是self.http_client，避免timeout上下文管理器问题
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.post(url, json=data, headers=headers, timeout=timeout) as resp:
                    result = await resp.json()
                    if result.get("status") == "ok" or result.get("retcode") == 0:
                        logger.info(f"QQ {media_type}发送成功: {message_type}")
                    else:
                        logger.error(f"QQ {media_type}发送失败: {result}")

        except Exception as e:
            logger.error(f"发送媒体消息错误: {e}", exc_info=True)

    async def _send_text_message(
        self,
        http_url: str,
        http_token: str,
        message_type: str,
        sender_id: str,
        group_id: Optional[str],
        message: str,
        headers: dict,
    ):
        """
        发送文本消息

        Args:
            http_url: HTTP API地址
            http_token: HTTP令牌
            message_type: 消息类型
            sender_id: 发送者ID
            group_id: 群ID
            message: 消息内容
            headers: HTTP请求头
        """
        try:
            import aiohttp
            import re

            logger.info(f"发送QQ文本: {message[:50]}...")

            # 智能表情包附件 - 根据语境自主判断是否添加表情包
            enable_smart_emoji = self.qq_config.get("enable_smart_emoji", True)
            final_message = message

            if enable_smart_emoji:
                # 清理CQ码和特殊字符后的纯文本
                clean_text = re.sub(r'\[CQ:.*?\]', '', message).strip()

                logger.info(f"[智能表情包] 原始文本长度: {len(message)}, 清理后长度: {len(clean_text)}")

                # 智能判断是否需要表情包的条件：
                # 1. 文本不太长（300字以内，避免影响长文本阅读）
                # 2. 有情感倾向（根据关键词判断）
                # 3. 文本没有已经包含CQ:face表情
                should_add_emoji = (
                    len(clean_text) <= 300
                    and "[CQ:face" not in message
                    and self._detect_emotion(clean_text) is not None
                )

                logger.info(f"[智能表情包] 是否满足条件: {should_add_emoji} (len={len(clean_text)}, has_face={('[CQ:face' in message)}, emotion={self._detect_emotion(clean_text)})")

                if should_add_emoji:
                    # 根据文本情感选择合适的表情
                    emotion = self._detect_emotion(clean_text)
                    emoji_code = self._get_emoji_for_emotion(emotion)
                    if emoji_code:
                        # 随机决定是否添加表情（90%概率，避免每次都加）
                        import random
                        if random.random() < 0.9:
                            # 添加表情到消息末尾
                            if message.endswith("\n"):
                                final_message = message + emoji_code + "\n"
                            else:
                                final_message = message + " " + emoji_code
                            logger.info(f"[智能表情包] 添加表情: {emotion} -> {emoji_code}")

            if message_type == "private":
                url = f"{http_url}/send_private_msg"
                data = {"user_id": int(sender_id), "message": final_message}
                if http_token:
                    data["access_token"] = http_token
            else:
                url = f"{http_url}/send_group_msg"
                data = {"group_id": int(group_id), "message": final_message}
                if http_token:
                    data["access_token"] = http_token

            # 使用新的ClientSession而不是self.http_client，避免timeout上下文管理器问题
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.post(url, json=data, headers=headers, timeout=timeout) as resp:
                    result = await resp.json()
                    if result.get("status") == "ok" or result.get("retcode") == 0:
                        logger.info(f"QQ文本发送成功: {message_type}")
                    else:
                        logger.error(f"QQ文本发送失败: {result}")

        except Exception as e:
            logger.error(f"发送文本消息错误: {e}", exc_info=True)

    def _detect_emotion(self, text: str) -> Optional[str]:
        """
        检测文本的情感倾向

        Args:
            text: 文本内容

        Returns:
            情感类型: "happy", "sad", "angry", "love", "think", "agree", "disagree", None
        """
        emotion_keywords = {
            "happy": ["开心", "高兴", "哈哈", "嘿嘿", "太好了", "棒", "厉害", "优秀", "成功", "快乐", "兴奋", "激动", "赞", "不错", "好", "喜欢", "爱", "满足", "幸福", "喜悦", "笑", "开心", "高兴", "哈哈", "嘻嘻", "嘿嘿", "雀跃", "愉快", "欢乐", "欢快", "欣喜", "开心极了", "太棒了", "太赞了", "开心地", "高兴地", "愉快地", "欢乐地", "欢喜", "欣喜若狂", "兴高采烈"],
            "sad": ["难过", "伤心", "哭", "呜呜", "难过", "痛苦", "失望", "悲伤", "郁闷", "唉", "可惜", "遗憾", "心疼", "难过", "难过", "难过", "难过", "难过"],
            "angry": ["生气", "愤怒", "气死", "讨厌", "烦", "讨厌", "讨厌", "讨厌", "讨厌", "讨厌", "讨厌", "讨厌", "讨厌", "讨厌", "讨厌", "讨厌", "讨厌", "讨厌", "讨厌"],
            "love": ["喜欢", "爱", "心动", "爱", "爱", "爱", "爱", "爱", "爱", "爱", "爱", "爱", "爱", "爱", "爱", "爱", "爱", "爱", "爱", "爱"],
            "think": ["思考", "想", "不知道", "想想", "想想", "想想", "想想", "想想", "想想", "想想", "想想", "想想", "想想", "想想", "想想", "想想", "想想", "想想", "想想", "想想"],
            "agree": ["是的", "对", "好", "好的", "可以", "行", "没问题", "当然", "同意", "赞同", "支持", "正确", "没错", "当然", "可以", "好的", "可以", "好的", "可以", "好的"],
            "disagree": ["不行", "不可以", "不好", "不能", "不要", "不同意", "反对", "错误", "不行", "不行", "不行", "不行", "不行", "不行", "不行", "不行", "不行", "不行", "不行", "不行"],
        }

        text_lower = text.lower()
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return emotion

        return None

    def _get_emoji_for_emotion(self, emotion: str) -> str:
        """
        根据情感类型获取对应的QQ表情CQ码

        Args:
            emotion: 情感类型

        Returns:
            CQ码格式的表情
        """
        # QQ表情ID映射
        emoji_map = {
            "happy": "[CQ:face,id=13]",      # 微笑
            "sad": "[CQ:face,id=14]",        # 哭泣
            "angry": "[CQ:face,id=32]",      # 生气
            "love": "[CQ:face,id=21]",      # 色色
            "think": "[CQ:face,id=42]",      # 思考
            "agree": "[CQ:face,id=176]",     # 大拇指
            "disagree": "[CQ:face,id=178]",  # 禁止
        }

        return emoji_map.get(emotion, "")

    async def _send_qq_text_only(self, message_type: str, sender_id: str, group_id: Optional[str], message: str):
        """
        直接发送QQ纯文本消息，不经过语音生成
        长文本会自动分批发送

        Args:
            message_type: 消息类型 (private/group)
            sender_id: 发送者ID
            group_id: 群ID
            message: 文本消息
        """
        try:
            http_url = self.qq_config.get("http_url", "http://127.0.0.1:3000")
            http_token = self.qq_config.get("http_token", "")

            headers = {}
            if http_token:
                headers["Authorization"] = f"Bearer {http_token}"

            # 分批发送长文本（每条最多500字）
            max_length = 500
            messages_to_send = []

            if len(message) <= max_length:
                messages_to_send.append(message)
            else:
                # 按句子分割，尽量保持语义完整
                sentences = []
                current_sentence = ""

                # 按标点符号分割
                for char in message:
                    current_sentence += char
                    if char in ['。', '！', '？', '？', '!', '?', '\n']:
                        if len(current_sentence) >= 100:  # 至少100字才分割
                            sentences.append(current_sentence.strip())
                            current_sentence = ""
                        else:
                            continue

                if current_sentence.strip():
                    sentences.append(current_sentence.strip())

                # 如果没有标点，就按字符分割
                if not sentences:
                    for i in range(0, len(message), max_length):
                        sentences.append(message[i:i+max_length])
                else:
                    # 重新组合，确保每条不超过max_length
                    combined = ""
                    for sentence in sentences:
                        if len(combined) + len(sentence) > max_length and combined:
                            messages_to_send.append(combined)
                            combined = sentence
                        else:
                            combined += sentence
                    if combined:
                        messages_to_send.append(combined)

            # 发送所有分片
            for idx, msg in enumerate(messages_to_send, 1):
                if message_type == "private":
                    url = f"{http_url}/send_private_msg"
                    data = {
                        "user_id": int(sender_id),
                        "message": msg
                    }
                else:
                    url = f"{http_url}/send_group_msg"
                    data = {
                        "group_id": int(group_id),
                        "message": msg
                    }

                if http_token:
                    data["access_token"] = http_token

                prefix = f"({idx}/{len(messages_to_send)}) " if len(messages_to_send) > 1 else ""
                logger.info(f"发送QQ文本: {prefix}{msg[:50]}...")

                # 使用新的ClientSession而不是self.http_client，避免timeout上下文管理器问题
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    timeout = aiohttp.ClientTimeout(total=10)
                    async with session.post(url, json=data, headers=headers, timeout=timeout) as resp:
                        result = await resp.json()
                        if result.get("status") == "ok" or result.get("retcode") == 0:
                            logger.info(f"✅ QQ文本消息发送成功: {message_type} ({idx}/{len(messages_to_send)})")
                        else:
                            logger.error(f"❌ QQ发送失败: {result}")

                # 分片之间添加延迟，避免被限流
                if idx < len(messages_to_send):
                    await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"发送QQ文本消息错误: {e}", exc_info=True)

    async def _send_audio_message(
        self,
        http_url: str,
        http_token: str,
        message_type: str,
        sender_id: str,
        group_id: Optional[str],
        audio_path: str,
        headers: dict,
    ):
        """
        发送语音消息

        Args:
            http_url: HTTP API地址
            http_token: HTTP令牌
            message_type: 消息类型
            sender_id: 发送者ID
            group_id: 群ID
            audio_path: 音频文件路径
            headers: HTTP请求头
        """
        try:
            import os
            import aiohttp

            # 将相对路径转换为绝对路径
            if not os.path.isabs(audio_path):
                audio_path = os.path.abspath(audio_path)

            # 验证文件存在
            if not os.path.exists(audio_path):
                logger.error(f"音频文件不存在: {audio_path}")
                return

            logger.info(f"发送QQ语音: {audio_path}")

            # 使用CQ码格式发送语音
            # CQ码格式: [CQ:record,file=file://绝对路径]
            cq_code = f"[CQ:record,file=file://{audio_path}]"

            if message_type == "private":
                url = f"{http_url}/send_private_msg"
                data = {"user_id": int(sender_id), "message": cq_code}
                if http_token:
                    data["access_token"] = http_token
            else:
                url = f"{http_url}/send_group_msg"
                data = {"group_id": int(group_id), "message": cq_code}
                if http_token:
                    data["access_token"] = http_token

            # 使用新的ClientSession而不是self.http_client，避免timeout上下文管理器问题
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.post(url, json=data, headers=headers, timeout=timeout) as resp:
                    result = await resp.json()
                    if result.get("status") == "ok" or result.get("retcode") == 0:
                        logger.info(f"QQ语音发送成功: {message_type}")
                    else:
                        logger.error(f"QQ语音发送失败: {result}")

            # 删除临时音频文件（带重试机制）
            try:
                if os.path.exists(audio_path):
                    import time
                    for attempt in range(20):  # 最多尝试20次（增加到20次）
                        try:
                            os.remove(audio_path)
                            logger.info(f"已删除临时音频文件: {audio_path}")
                            break
                        except PermissionError as e:
                            if attempt < 19:
                                time.sleep(1.0)  # 等待1秒后重试（增加到1秒）
                            else:
                                logger.warning(f"删除临时音频文件失败: {e}")
            except Exception as e:
                logger.warning(f"删除临时音频文件失败: {e}")

        except Exception as e:
            logger.error(f"发送语音消息错误: {e}", exc_info=True)

    async def _should_reply_to_group(self, group_id: Optional[str], sender_id: str, message: str, data: Dict[str, Any]) -> bool:
        """
        判断是否应该回复群聊消息

        Args:
            group_id: 群ID
            sender_id: 发送者ID
            message: 消息内容
            data: 原始消息数据

        Returns:
            是否应该回复
        """
        if group_id is None:
            return True  # 私聊总是回复

        # 获取群聊回复配置
        enable_group_reply = self.qq_config.get("enable_group_reply", True)
        group_reply_mode = self.qq_config.get("group_reply_mode", "all")  # all, at_only, intelligent, none
        group_whitelist = self.qq_config.get("group_whitelist", [])  # 群白名单（空列表表示所有群）
        group_blacklist = self.qq_config.get("group_blacklist", [])  # 群黑名单
        group_reply_keywords = self.qq_config.get("group_reply_keywords", [])  # 关键词触发
        group_reply_cooldown = self.qq_config.get("group_reply_cooldown", 0)  # 冷却时间（秒）

        # 检查是否启用群聊回复
        if not enable_group_reply:
            return False

        # 检查回复模式
        if group_reply_mode == "none":
            return False

        # 检查群黑名单
        if str(group_id) in group_blacklist:
            return False

        # 检查群白名单（如果配置了白名单，只回复白名单中的群）
        if group_whitelist and str(group_id) not in group_whitelist:
            return False

        # 检查是否@机器人（多种检测方式）
        is_at_bot = False
        bot_qq = self.qq_config.get("bot_qq", "")

        # 方法1: 检查 raw_message 中的 CQ 码
        raw_message = data.get("raw_message", "")
        if raw_message:
            # 检查是否 @ 了机器人的 QQ 号（精确匹配）
            if bot_qq and f"[CQ:at,qq={bot_qq}]" in raw_message:
                is_at_bot = True

        # 方法2: 检查 message 数组中的 @ 段落（OneBot 11 标准格式）
        if not is_at_bot and "message" in data:
            message_segments = data.get("message", [])
            if isinstance(message_segments, list):
                for segment in message_segments:
                    if isinstance(segment, dict):
                        if segment.get("type") == "at":
                            qq = segment.get("data", {}).get("qq", "")
                            # 精确匹配：只有 @ bot_qq 才算 @ 机器人
                            if str(qq) == str(bot_qq):
                                is_at_bot = True
                                logger.info(f"[@检测] 检测到 @bot: QQ={qq}")
                                break
                            else:
                                logger.info(f"[@检测] 检测到 @其他用户: QQ={qq}, 忽略")

        logger.info(f"[@检测] is_at_bot={is_at_bot}, bot_qq={bot_qq}, raw_message前50={raw_message[:50]}")

        # 模式: auto - 自动判断话题相关性（新增）
        if group_reply_mode == "auto":
            # 如果@了机器人，直接回复
            if is_at_bot:
                pass  # 继续执行后续检查
            else:
                # 否则检查话题相关性
                topic_relevant = await self._check_topic_relevance(group_id, sender_id, message)
                if not topic_relevant:
                    logger.info(f"[话题检测] 群 {group_id} 消息不相关，跳过: {message[:50]}...")
                    return False

        # 模式: at_only - 只回复@机器人的消息
        if group_reply_mode == "at_only":
            if not is_at_bot:
                logger.info(f"[@检测] at_only 模式，未检测到 @，跳过")
                return False

        # 模式: intelligent - 智能判断（@机器人 或 关键词触发）
        if group_reply_mode == "intelligent":
            if not is_at_bot:
                # 检查关键词触发
                keyword_match = False
                for keyword in group_reply_keywords:
                    if keyword.lower() in message.lower():
                        keyword_match = True
                        logger.info(f"[关键词检测] 匹配关键词: {keyword}")
                        break
                if not keyword_match:
                    logger.info(f"[关键词检测] 未匹配任何关键词")
                    return False

        # 模式: all - 回复所有消息
        if group_reply_mode == "all":
            pass  # 继续执行后续检查

        # 检查冷却时间
        if group_reply_cooldown > 0:
            cooldown_key = f"group_{group_id}_cooldown"
            now = datetime.now().timestamp()
            if cooldown_key in self.message_cache:
                last_reply_time = self.message_cache[cooldown_key]
                if now - last_reply_time < group_reply_cooldown:
                    logger.info(f"[群聊冷却] 群 {group_id} 还在冷却中，跳过")
                    return False
            # 更新冷却时间
            self.message_cache[cooldown_key] = now

        return True

    async def _check_topic_relevance(self, group_id: str, sender_id: str, message: str) -> bool:
        """
        检查消息是否与当前话题相关

        Args:
            group_id: 群ID
            sender_id: 发送者ID
            message: 消息内容

        Returns:
            是否相关
        """
        # 从配置中读取关键词
        enable_topic_detection = self.qq_config.get("enable_topic_detection", True)
        if not enable_topic_detection:
            return True  # 如果未启用话题检测，默认回复

        relevance_keywords = self.qq_config.get("topic_relevance_keywords", [
            "机器人", "ai", "娜迦", "弥娅", "帮忙", "查询",
            "天气", "时间", "画图", "绘图", "搜索", "新闻",
            "音乐", "视频", "笑话", "故事", "你好", "在吗"
        ])

        # 过滤表情包和短消息
        message_stripped = message.strip()

        # 移除 CQ 码后检查纯文本长度
        import re
        clean_message = re.sub(r'\[CQ:.*?\]', '', message_stripped).strip()

        # 如果消息太短或只有表情，不回复
        if len(clean_message) < 2:
            logger.info(f"[话题检测] 群 {group_id} 消息太短或只有表情，不回复")
            return False

        # 如果消息只有 CQ 码（图片、表情等），不回复
        if len(clean_message) == 0:
            logger.info(f"[话题检测] 群 {group_id} 消息只有 CQ 码，不回复")
            return False

        # 检查关键词匹配
        message_lower = message_stripped.lower()
        for keyword in relevance_keywords:
            if keyword.lower() in message_lower:
                logger.info(f"[话题检测] 群 {group_id} 匹配关键词 '{keyword}'")
                return True

        # 检查是否是问题（包含问号或疑问词）
        question_words = ["什么", "怎么", "如何", "为什么", "谁", "哪里", "几", "多少", "在哪", "在哪"]
        if any(word in message_stripped for word in question_words) or "？" in message_stripped or "?" in message_stripped:
            logger.info(f"[话题检测] 群 {group_id} 检测到疑问句")
            return True

        # 检查是否是指令
        if message_stripped.startswith("/"):
            logger.info(f"[话题检测] 群 {group_id} 检测到指令")
            return True

        # 检查请求类词汇
        request_words = ["能不能", "可以吗", "帮我", "请", "请帮我", "帮我查", "帮我找"]
        for word in request_words:
            if word in message_stripped:
                logger.info(f"[话题检测] 群 {group_id} 检测到请求词 '{word}'")
                return True

        # 默认不回复
        logger.info(f"[话题检测] 群 {group_id} 未匹配任何规则，不回复")
        return False

    def _should_send_quick_emoji(self, message: str) -> bool:
        """
        判断是否应该发送快速表情回复

        Args:
            message: 消息内容

        Returns:
            是否发送表情回复
        """
        enable_emoji_reply = self.qq_config.get("enable_emoji_reply", True)
        if not enable_emoji_reply:
            return False

        # 移除 CQ 码
        import re
        clean_message = re.sub(r'\[CQ:.*?\]', '', message).strip()

        # 只对短消息进行表情回复
        if len(clean_message) > 10:
            return False

        return True

    async def _get_emoji_response(self, message: str) -> Optional[str]:
        """
        根据消息内容获取表情回复

        Args:
            message: 消息内容

        Returns:
            表情回复内容，不需要回复返回 None
        """
        emoji_keywords = self.qq_config.get("emoji_reply_keywords", {})

        # 移除 CQ 码
        import re
        clean_message = re.sub(r'\[CQ:.*?\]', '', message).strip()

        # 遍历表情关键词映射
        for emoji, keywords in emoji_keywords.items():
            for keyword in keywords:
                if keyword in clean_message:
                    # 随机选择一个相关的回复
                    import random
                    responses = [
                        f"[CQ:face,id={self._parse_face_id(emoji)}]",
                        f"~{emoji}",
                        f"收到~{emoji}"
                    ]
                    return random.choice(responses)

        return None

    def _parse_face_id(self, emoji: str) -> str:
        """
        将 emoji 转换为 QQ 表情 ID

        Args:
            emoji: emoji 表情

        Returns:
            QQ 表情 ID
        """
        # QQ 常用表情 ID 映射
        face_map = {
            "😊": "13",  # 微笑
            "😢": "14",  # 哭泣
            "😡": "32",  # 生气
            "😍": "21",  # 色色
            "🤔": "42",  # 思考
            "👍": "176",  # 大拇指
            "👎": "178",  # 禁止
        }
        return face_map.get(emoji, "13")  # 默认返回微笑

    async def _is_duplicate(self, message_key: str) -> bool:
        """
        检查消息是否重复

        Args:
            message_key: 消息键

        Returns:
            是否重复
        """
        now = datetime.now().timestamp()

        # 清理过期缓存
        expired_keys = [k for k, v in self.message_cache.items() if now - v > self.cache_ttl]
        for k in expired_keys:
            del self.message_cache[k]

        # 检查是否重复
        if message_key in self.message_cache:
            return True

        # 添加到缓存
        self.message_cache[message_key] = now
        return False

    async def _call_self_optimization_tools(
        self,
        message: str,
        session_id: str,
        sender_id: Optional[str] = None,
        group_id: Optional[str] = None,
        message_type: str = "private",
    ) -> str:
        """
        调用自我优化工具

        Args:
            message: 用户消息
            session_id: 会话ID
            sender_id: 发送者ID（用于发送消息）
            group_id: 群ID（用于发送消息）
            message_type: 消息类型（用于发送消息）

        Returns:
            工具执行结果
        """
        try:
            from mcpserver.agent_self_optimization.tools import call_tool

            # 解析消息中的@信息，移除CQ码
            parsed_message_info = self._parse_at_mentions(message, sender_id)
            clean_message = parsed_message_info["clean_message"]

            # 移除 [发送者QQ:xxx] 前缀
            import re
            clean_message = re.sub(r'\[发送者QQ:\d+\]\s*', '', clean_message)
            # 移除 @弥娅 等称呼
            clean_message = re.sub(r'@弥娅\s*', '', clean_message)
            clean_message = clean_message.strip()

            # 关键词匹配（使用精确短语匹配，避免子字符串误触发）
            tool_name = None
            tool_params = {}

            # 使用精确短语匹配，而不是子字符串匹配
            clean_message_lower = clean_message.lower()
            
            if clean_message_lower in ["检查系统", "检查系统健康", "系统健康检查", "系统状态检查", "运行状态"]:
                tool_name = "check_system_health"
                logger.info(f"[自我优化工具] 匹配到check_system_health")
            elif clean_message_lower == "系统健康" or clean_message_lower == "健康状态" or clean_message_lower == "系统状态":
                tool_name = "check_system_health"
                logger.info(f"[自我优化工具] 匹配到check_system_health")

            elif any(keyword in clean_message for keyword in ["性能分析", "系统性能", "性能报告"]):
                tool_name = "analyze_performance"
                logger.info(f"[自我优化工具] 匹配到analyze_performance")

            elif any(keyword in clean_message for keyword in ["运行优化", "自动优化", "系统优化", "优化系统"]):
                tool_name = "run_optimization"
                logger.info(f"[自我优化工具] 匹配到run_optimization")

            elif any(keyword in clean_message for keyword in ["代码质量", "代码分析", "检查代码", "分析代码"]):
                tool_name = "analyze_code_quality"
                logger.info(f"[自我优化工具] 匹配到analyze_code_quality")

            elif any(keyword in clean_message for keyword in ["导出报告", "生成报告", "优化报告"]):
                tool_name = "export_reports"
                logger.info(f"[自我优化工具] 匹配到export_reports")

            elif any(keyword in clean_message for keyword in ["优化状态", "系统优化状态"]):
                tool_name = "get_status"
                logger.info(f"[自我优化工具] 匹配到get_status")

            elif any(keyword in clean_message for keyword in ["修复代码", "自动修复", "代码修复", "修复问题"]):
                tool_name = "fix_code_issues"
                tool_params = {"auto_fix": True}
                logger.info(f"[自我优化工具] 匹配到fix_code_issues")

            elif any(keyword in clean_message for keyword in ["检查代码问题", "查看代码问题", "代码问题"]):
                tool_name = "fix_code_issues"
                tool_params = {"auto_fix": False}
                logger.info(f"[自我优化工具] 匹配到fix_code_issues (仅查看)")

            elif any(keyword in clean_message for keyword in ["回滚修复", "代码回滚", "恢复备份", "撤销修复"]):
                tool_name = "rollback_fixes"
                tool_params = {}
                logger.info(f"[自我优化工具] 匹配到rollback_fixes")

            elif any(keyword in clean_message for keyword in ["查看备份", "列出备份", "备份列表"]):
                tool_name = "list_backups"
                tool_params = {}
                logger.info(f"[自我优化工具] 匹配到list_backups")

            elif any(keyword in clean_message for keyword in ["自我优化", "自动优化", "迭代优化"]):
                tool_name = "self_optimize_iterative"
                tool_params = {"auto_apply": False}
                logger.info(f"[自我优化工具] 匹配到self_optimize_iterative (预览模式)")

            elif "执行优化" in clean_message:
                tool_name = "self_optimize_iterative"
                tool_params = {"auto_apply": True}
                logger.info(f"[自我优化工具] 匹配到self_optimize_iterative (执行模式)")

            elif clean_message.startswith("改写文件"):
                # 格式: 改写文件 <文件路径> <指令>
                parts = clean_message.split(maxsplit=2)
                if len(parts) >= 2:
                    file_path = parts[1]
                    instructions = parts[2] if len(parts) > 2 else "优化代码质量"
                    tool_name = "ai_refactor_file"
                    tool_params = {
                        "file_path": file_path,
                        "instructions": instructions,
                        "auto_apply": False,
                        "dry_run": True
                    }
                    logger.info(f"[自我优化工具] 匹配到ai_refactor_file (预览)")

            elif clean_message.startswith("应用改写"):
                # 格式: 应用改写 <文件路径> <指令>
                parts = clean_message.split(maxsplit=2)
                if len(parts) >= 2:
                    file_path = parts[1]
                    instructions = parts[2] if len(parts) > 2 else "优化代码质量"
                    tool_name = "ai_refactor_file"
                    tool_params = {
                        "file_path": file_path,
                        "instructions": instructions,
                        "auto_apply": True,
                        "dry_run": False
                    }
                    logger.info(f"[自我优化工具] 匹配到ai_refactor_file (应用)")

            elif clean_message.startswith("读取文件"):
                # 格式: 读取文件 <文件路径>
                parts = clean_message.split(maxsplit=1)
                if len(parts) >= 2:
                    file_path = parts[1]
                    tool_name = "read_file"
                    tool_params = {"file_path": file_path}
                    logger.info(f"[自我优化工具] 匹配到read_file")

            # ==================== LifeBook 工具 ====================

            elif any(keyword in clean_message for keyword in ["读取记忆", "回忆过去", "查看记忆", "回顾记忆", "读取LifeBook"]):
                # 格式: 读取最近X个月的记忆
                tool_name = "read_lifebook"

                # 解析月数
                months = 3  # 默认3个月
                import re
                month_match = re.search(r'(\d+)个月', clean_message)
                if month_match:
                    months = int(month_match.group(1))

                tool_params = {"months": months, "max_tokens": 8000}
                logger.info(f"[LifeBook工具] 匹配到read_lifebook，回溯{months}个月")

            elif any(keyword in clean_message for keyword in ["记录日记", "写日记", "记下来", "保存对话"]):
                # 弥娅会自动记录当前对话内容
                # 这里只是一个触发器，实际内容由弥娅决定
                tool_name = "write_diary"
                tool_params = {}
                logger.info(f"[LifeBook工具] 匹配到write_diary (记录当前对话)")

            elif clean_message.startswith("生成周总结") or clean_message.startswith("写周总结"):
                # 格式: 生成周总结 或 生成周总结 W1
                parts = clean_message.split()
                period = "W1"  # 默认W1
                if len(parts) >= 2:
                    period = parts[1]

                tool_name = "generate_summary"
                tool_params = {"type": "week", "period": period, "preview": True}
                logger.info(f"[LifeBook工具] 匹配到generate_summary (week, {period})")

            elif clean_message.startswith("生成月总结") or clean_message.startswith("写月总结"):
                # 格式: 生成月总结 或 生成月总结 2025-01
                parts = clean_message.split()
                period = datetime.now().strftime("%Y-%m")  # 默认当前月
                if len(parts) >= 2:
                    period = parts[1]

                tool_name = "generate_summary"
                tool_params = {"type": "month", "period": period, "preview": True}
                logger.info(f"[LifeBook工具] 匹配到generate_summary (month, {period})")

            elif clean_message.startswith("生成季总结") or clean_message.startswith("写季总结") or clean_message.startswith("生成Q"):
                # 格式: 生成季总结 或 生成季总结 Q1 或 生成Q1总结
                import re
                q_match = re.search(r'Q(\d)', clean_message)
                period = f"Q{q_match.group(1)}" if q_match else "Q1"

                tool_name = "generate_summary"
                tool_params = {"type": "quarter", "period": period, "preview": True}
                logger.info(f"[LifeBook工具] 匹配到generate_summary (quarter, {period})")

            elif clean_message.startswith("创建节点"):
                # 格式: 创建节点 <名称> <类型> <描述>
                parts = clean_message.split(maxsplit=3)
                if len(parts) >= 2:
                    name = parts[1]
                    node_type = "character"  # 默认人物节点
                    description = ""

                    if len(parts) >= 3:
                        type_part = parts[2].lower()
                        if type_part in ["人物", "character"]:
                            node_type = "character"
                        elif type_part in ["阶段", "stage"]:
                            node_type = "stage"
                        else:
                            # 可能是描述而不是类型
                            description = parts[2]

                    if len(parts) >= 4:
                        description = parts[3]

                    tool_name = "create_node"
                    tool_params = {
                        "name": name,
                        "type": node_type,
                        "description": description
                    }
                    logger.info(f"[LifeBook工具] 匹配到create_node ({name}, {node_type})")

            elif any(keyword in clean_message for keyword in ["列出节点", "查看节点", "节点列表"]):
                # 格式: 列出节点 或 列出人物节点
                node_type = ""
                if "人物" in clean_message or "角色" in clean_message:
                    node_type = "character"
                elif "阶段" in clean_message:
                    node_type = "stage"

                tool_name = "list_nodes"
                tool_params = {"node_type": node_type}
                logger.info(f"[LifeBook工具] 匹配到list_nodes (type: {node_type or '全部'})")

            elif "应用总结" in clean_message or "应用生成的总结" in clean_message:
                # 应用最近生成的总结
                tool_name = "generate_summary"
                tool_params = {"preview": False, "auto_apply": True}
                logger.info(f"[LifeBook工具] 匹配到apply_summary")

            # ==================== LifeBook 工具结束 ====================

            if tool_name:
                # 格式: 读取文件 <文件路径>
                parts = clean_message.split(maxsplit=1)
                if len(parts) >= 2:
                    file_path = parts[1]
                    tool_name = "read_file"
                    tool_params = {"file_path": file_path}
                    logger.info(f"[自我优化工具] 匹配到read_file")

            # 如果匹配到工具，则调用
            if tool_name:
                logger.info(f"[自我优化工具] 调用工具: {tool_name}")
                result = await call_tool(tool_name, tool_params)
                return result

            # 没有匹配的工具
            logger.info(f"[自我优化工具] 没有匹配的工具，消息: {message}")
            return ""

        except Exception as e:
            logger.error(f"调用自我优化工具失败: {e}", exc_info=True)
            return ""

    async def _call_undefined_tools(
        self,
        message: str,
        session_id: str,
        sender_id: Optional[str] = None,
        group_id: Optional[str] = None,
        message_type: str = "private",
    ) -> str:
        """
        调用Undefined工具

        Args:
            message: 用户消息
            session_id: 会话ID
            sender_id: 发送者ID（用于发送图片/视频）
            group_id: 群ID（用于发送图片/视频）
            message_type: 消息类型（用于发送图片/视频）

        Returns:
            工具执行结果
        """
        # 检查群聊工具配置：如果是群聊且禁用了群聊工具，则直接返回空
        if message_type == "group" and group_id:
            from system.config_manager import get_config
            config = get_config()
            if config:
                enable_group_tools = config.get("qq", {}).get("enable_group_tools", False)
                if not enable_group_tools:
                    logger.debug(f"[Undefined工具] 群聊中禁用工具调用: group_id={group_id}")
                    return ""

        try:
            from mcpserver.mcp_registry import get_service_info

            # 获取Undefined服务实例（使用displayName作为键）
            service_info = get_service_info("Undefined工具集")
            if not service_info:
                logger.debug("Undefined服务未注册")
                return ""

            undefined_agent = service_info.get("instance")
            if not undefined_agent or not hasattr(undefined_agent, "get_available_tools"):
                logger.debug("Undefined服务实例不存在或缺少工具方法")
                return ""

            # 获取可用工具列表
            available_tools = undefined_agent.get_available_tools()
            if not available_tools:
                logger.debug("Undefined没有可用工具")
                return ""

            # 解析消息中的@信息，移除CQ码（与主AI处理保持一致）
            parsed_message_info = self._parse_at_mentions(message, sender_id)
            clean_message = parsed_message_info["clean_message"]

            # 移除 [发送者QQ:xxx] 前缀（用于Undefined工具的关键词匹配）
            import re
            clean_message_for_tool = re.sub(r'\[发送者QQ:\d+\]\s*', '', clean_message)
            # 移除 @弥娅 等称呼（避免影响关键词匹配）
            clean_message_for_tool = re.sub(r'@弥娅\s*', '', clean_message_for_tool)
            clean_message_for_tool = clean_message_for_tool.strip()

            # 获取工具名称列表
            tool_names = [tool.get("function", {}).get("name", "") for tool in available_tools]
            logger.info(f"[Undefined工具] 可用工具: {', '.join(tool_names[:10])}...")  # 只显示前10个
            logger.info(f"[Undefined工具] 收到消息: {message}")  # 添加消息日志（原始消息）
            logger.debug(f"[Undefined工具] 处理后消息: {clean_message_for_tool}")  # 调试：处理后的消息

            # 简单的关键词匹配来决定调用哪个工具
            # 这里使用简单的规则，实际可以通过AI分析来决定
            matched_tool = None
            matched_params = {}

            # 检查是否是render_and_send_image工具请求
            # 从session_id解析出sender_id和message_type（格式：qq_{sender_id}）
            if not sender_id or not message_type:
                if session_id.startswith("qq_"):
                    sender_id = session_id.replace("qq_", "")
                    # 默认为私聊，如果需要群聊，需要额外信息
                    message_type = "private"

            # 构建发送图片的回调函数
            async def send_image_callback(target_id: int, msg_type: str, file_path: str):
                """发送图片回调"""
                try:
                    logger.info(
                        f"[send_image_callback] 被调用: target_id={target_id}, msg_type={msg_type}, file_path={file_path}"
                    )
                    logger.info(f"[send_image_callback] sender_id={sender_id}, group_id={group_id}")

                    # 确定发送目标
                    if msg_type == "group":
                        logger.info(f"[send_image_callback] 发送到群聊")
                        await self._send_qq_reply(
                            "group",
                            sender_id if not group_id else str(target_id),
                            group_id or str(target_id),
                            file_path,
                            "image",
                        )
                    else:
                        logger.info(f"[send_image_callback] 发送到私聊: user_id={target_id}")
                        await self._send_qq_reply("private", str(target_id), None, file_path, "image")

                    logger.info(f"[send_image_callback] 发送完成")
                except Exception as e:
                    logger.error(f"发送图片回调失败: {e}", exc_info=True)

            # 构建工具上下文
            tool_context = {
                "sender": None,  # 可以在这里传递QQ适配器实例
                "send_image_callback": send_image_callback if sender_id else None,
            }
            logger.info(f"[工具上下文] sender_id={sender_id}, message_type={message_type}, group_id={group_id}")
            logger.info(f"[工具上下文] send_image_callback={'已设置' if sender_id else '未设置'}")

            # 获取QQ适配器实例（如果需要直接发送）
            from mcpserver.mcp_registry import get_service_info

            qq_service = get_service_info("QQ/微信集成")
            if qq_service:
                tool_context["sender"] = qq_service.get("instance")

            # 天气相关
            if any(keyword in clean_message_for_tool for keyword in ["天气", "气温", "温度", "下雨", "晴天", "阴天"]):
                for tool in available_tools:
                    if tool.get("function", {}).get("name") == "tool.weather_query":
                        matched_tool = "tool.weather_query"
                        # 提取城市名称（简单处理，实际应该更精确）
                        city = clean_message_for_tool.replace("天气", "").replace("气温", "").replace("温度", "").strip()
                        if not city:
                            city = "北京"  # 默认城市
                        matched_params = {"city": city}
                        break

            # 黄金价格相关
            if any(keyword in clean_message_for_tool for keyword in ["黄金", "金价", "黄金价格", "今日黄金"]):
                for tool in available_tools:
                    if tool.get("function", {}).get("name") == "tool.gold_price":
                        matched_tool = "tool.gold_price"
                        matched_params = {}
                        break

            # 星座运势相关
            if any(keyword in clean_message_for_tool for keyword in ["星座", "运势", "占星", "星运"]):
                for tool in available_tools:
                    if tool.get("function", {}).get("name") == "tool.horoscope":
                        matched_tool = "tool.horoscope"
                        # 尝试提取星座名称
                        constellation = clean_message_for_tool
                        for zodiac in [
                            "白羊座",
                            "金牛座",
                            "双子座",
                            "巨蟹座",
                            "狮子座",
                            "处女座",
                            "天秤座",
                            "天蝎座",
                            "射手座",
                            "摩羯座",
                            "水瓶座",
                            "双鱼座",
                        ]:
                            if zodiac in clean_message_for_tool:
                                constellation = zodiac
                                break
                        # 判断时间类型
                        time_type = "今日"
                        if "本周" in clean_message_for_tool or "这周" in clean_message_for_tool:
                            time_type = "本周"
                        elif "本月" in clean_message_for_tool or "这个月" in clean_message_for_tool:
                            time_type = "本月"
                        elif "本年" in clean_message_for_tool or "今年" in clean_message_for_tool:
                            time_type = "本年"
                        matched_params = {"constellation": constellation, "time_type": time_type}
                        break

            # 搜索相关
            elif any(keyword in clean_message_for_tool for keyword in ["搜索", "查一下", "百度一下", "查百度"]):
                for tool in available_tools:
                    if tool.get("function", {}).get("name") == "tool.web_search":
                        matched_tool = "tool.web_search"
                        # 提取搜索关键词
                        keywords = (
                            clean_message_for_tool.replace("搜索", "")
                            .replace("查一下", "")
                            .replace("百度一下", "")
                            .replace("查百度", "")
                            .strip()
                        )
                        if not keywords:
                            keywords = clean_message_for_tool
                        matched_params = {"query": keywords}
                        break

            # 热搜相关
            elif any(keyword in clean_message_for_tool for keyword in ["热搜", "热门", "榜单", "百度热搜", "微博热搜", "抖音热搜"]):
                if "百度" in clean_message_for_tool or "baidu" in clean_message_for_tool.lower():
                    for tool in available_tools:
                        if tool.get("function", {}).get("name") == "tool.baiduhot":
                            matched_tool = "tool.baiduhot"
                            break
                elif "微博" in clean_message_for_tool or "weibo" in clean_message_for_tool.lower():
                    for tool in available_tools:
                        if tool.get("function", {}).get("name") == "tool.weibohot":
                            matched_tool = "tool.weibohot"
                            break
                elif "抖音" in clean_message_for_tool or "douyin" in clean_message_for_tool.lower():
                    for tool in available_tools:
                        if tool.get("function", {}).get("name") == "tool.douyinhot":
                            matched_tool = "tool.douyinhot"
                            break

            # B站相关
            elif any(keyword in clean_message_for_tool for keyword in ["B站", "b站", "哔哩哔哩", "bilibili"]):
                # 只有明确要求搜索、查询或推荐时才调用Undefined工具
                # 如果是"打开"相关的，应该由MCP应用启动服务处理
                if ("搜索" in clean_message_for_tool or "查找" in clean_message_for_tool or "查询" in clean_message_for_tool or "推荐" in clean_message_for_tool) and "打开" not in clean_message_for_tool:
                    for tool in available_tools:
                        if tool.get("function", {}).get("name") == "tool.bilibili_search":
                            matched_tool = "tool.bilibili_search"
                            # 智能提取关键词: 使用正则表达式提取实际搜索内容
                            import re
                            # 尝试匹配各种可能的表达模式
                            # "推荐一个B站上关于鸣潮的视频给我看看" -> "鸣潮"
                            # "搜索B站上的AI" -> "AI"
                            # "找找B站视频" -> "B站视频"
                            patterns = [
                                r'关于\s*(.+?)\s*(?:的|视频)',
                                r'(?:搜索|推荐|查找|查询)\s*.*?关于?\s*(.+?)\s*(?:的|视频|内容)',
                                r'(?:搜索|推荐|查找|查询)\s*(.+?)(?:的)?视频',
                            ]
                            keywords = None
                            for pattern in patterns:
                                match = re.search(pattern, clean_message_for_tool)
                                if match:
                                    keywords = match.group(1).strip()
                                    break
                            
                            # 如果没有匹配到,使用简单的移除方式
                            if not keywords:
                                keywords = clean_message_for_tool
                                # 移除常见词汇
                                for word in ["B站", "b站", "哔哩哔哩", "bilibili", "搜索", "查找", "查询", "推荐", "一个", "关于", "视频", "给我看看", "给我", "看看", "找", "看", "找找", "推荐"]:
                                    keywords = keywords.replace(word, "")
                                keywords = keywords.strip()
                            
                            # 如果关键词为空,使用原始消息
                            if not keywords:
                                keywords = clean_message_for_tool
                            matched_params = {"keyword": keywords}
                            break
                # 如果只是提到B站（如"帮我打开哔哩哔哩"），不调用Undefined工具
                # 这将由MCP应用启动服务处理

            # 音乐相关
            elif any(keyword in clean_message_for_tool for keyword in ["音乐", "歌曲", "歌词", "唱歌"]):
                if "搜索" in clean_message_for_tool or "找" in clean_message_for_tool:
                    for tool in available_tools:
                        if tool.get("function", {}).get("name") == "tool.music_global_search":
                            matched_tool = "tool.music_global_search"
                            keywords = (
                                clean_message_for_tool.replace("音乐", "")
                                .replace("歌曲", "")
                                .replace("搜索", "")
                                .replace("找", "")
                                .strip()
                            )
                            matched_params = {"keyword": keywords}
                            break
                elif "歌词" in clean_message_for_tool:
                    for tool in available_tools:
                        if tool.get("function", {}).get("name") == "tool.music_lyrics":
                            matched_tool = "tool.music_lyrics"
                            # 这里需要更复杂的解析来提取歌曲名和歌手
                            break

            # 时间相关
            elif any(keyword in clean_message_for_tool for keyword in ["时间", "几点", "现在几点"]):
                for tool in available_tools:
                    if tool.get("function", {}).get("name") == "tool.get_current_time":
                        matched_tool = "tool.get_current_time"
                        break

            # AI绘图相关
            elif any(keyword in clean_message_for_tool for keyword in ["画", "绘图", "画图", "生成图片", "AI画"]):
                # 判断是使用本地还是在线（使用处理后的消息）
                use_local = any(kw in clean_message_for_tool for kw in ["本地画", "本地", "本地绘画", "local"])
                tool_name = "tool.local_ai_draw" if use_local else "tool.ai_draw_one"

                for tool in available_tools:
                    if tool.get("function", {}).get("name") == tool_name:
                        matched_tool = tool_name
                        # 提取绘图提示词（使用处理后的消息）
                        prompt = (
                            clean_message_for_tool.replace("画", "")
                            .replace("绘图", "")
                            .replace("画图", "")
                            .replace("生成图片", "")
                            .replace("AI画", "")
                            .replace("本地画", "")
                            .replace("本地", "")
                            .replace("本地绘画", "")
                            .replace("local", "")
                            .strip()
                        )
                        if not prompt:
                            prompt = clean_message
                        matched_params = {"prompt": prompt}

                        # 添加 target_id 和 message_type
                        matched_params["target_id"] = int(sender_id) if sender_id else 0
                        matched_params["message_type"] = message_type

                        break

            # 图片渲染相关（Markdown/LaTeX）
            elif any(keyword in clean_message for keyword in ["渲染", "render", "latex", "公式", "markdown"]):
                for tool in available_tools:
                    if tool.get("function", {}).get("name") == "tool.render_and_send_image":
                        matched_tool = "tool.render_and_send_image"
                        # 默认格式和内容
                        format_type = "markdown"
                        if "latex" in message.lower() or "公式" in message:
                            format_type = "latex"
                        matched_params = {
                            "content": message,
                            "format": format_type,
                            "target_id": int(sender_id) if sender_id else 0,
                            "message_type": message_type,
                        }
                        break

            # 如果没有匹配的工具，返回空
            if not matched_tool:
                logger.info(f"[Undefined工具] 没有匹配的工具，消息: {message}")
                return ""

            # 调用工具
            logger.info(f"调用Undefined工具: {matched_tool}, 参数: {matched_params}")
            result = await undefined_agent.call_tool(matched_tool, matched_params, context=tool_context)

            return result

        except Exception as e:
            logger.error(f"调用Undefined工具失败: {e}", exc_info=True)
            return ""

    async def _get_undefined_tools_list(self) -> str:
        """
        获取Undefined工具列表

        Returns:
            工具列表文本
        """
        try:
            from mcpserver.mcp_registry import get_service_info

            # 获取Undefined服务实例（使用displayName作为键）
            service_info = get_service_info("Undefined工具集")
            if not service_info:
                logger.warning(f"[工具列表] Undefined服务未启用")
                logger.warning(
                    f"[工具列表] 可用服务列表: {list(__import__('mcpserver.mcp_registry', fromlist=['MCP_REGISTRY']).MCP_REGISTRY.keys())}"
                )
                return "Undefined工具集服务未启用"

            undefined_agent = service_info.get("instance")
            if not undefined_agent or not hasattr(undefined_agent, "get_available_tools"):
                return "Undefined服务实例不存在"

            # 获取可用工具列表
            available_tools = undefined_agent.get_available_tools()
            if not available_tools:
                return "Undefined没有可用工具"

            # 按类别组织工具
            categories = {
                "🔍 搜索查询": [],
                "📊 热门榜单": [],
                "🎬 视频娱乐": [],
                "🎵 音乐相关": [],
                "🌤️ 生活服务": [],
                "💰 财经信息": [],
                "📱 社交相关": [],
                "📂 文件操作": [],
                "🛠️ 开发工具": [],
                "🎮 游戏娱乐": [],
                "🤖 AI辅助": [],
                "⚙️ 工具类": [],  # 添加这个类别作为默认类别
            }

            # 分类映射
            category_map = {
                "web_search": "🔍 搜索查询",
                "crawl_webpage": "🔍 搜索查询",
                "baiduhot": "📊 热门榜单",
                "weibohot": "📊 热门榜单",
                "douyinhot": "📊 热门榜单",
                "bilibili_search": "🎬 视频娱乐",
                "bilibili_user_info": "🎬 视频娱乐",
                "video_random_recommend": "🎬 视频娱乐",
                "music_global_search": "🎵 音乐相关",
                "music_info_get": "🎵 音乐相关",
                "music_lyrics": "🎵 音乐相关",
                "weather_query": "🌤️ 生活服务",
                "get_current_time": "🌤️ 生活服务",
                "horoscope": "🌤️ 生活服务",
                "gold_price": "💰 财经信息",
                "qq_level_query": "📱 社交相关",
                "qq_like": "📱 社交相关",
                "send_message": "📱 社交相关",
                "send_private_message": "📱 社交相关",
                "get_picture": "📱 社交相关",
                "get_recent_messages": "📱 社交相关",
                "get_messages_by_time": "📱 社交相关",
                "get_forward_msg": "📱 社交相关",
                "read_file": "📂 文件操作",
                "save_memory": "📂 文件操作",
                "history": "📂 文件操作",
                "list_directory": "📂 文件操作",
                "search_file_content": "📂 文件操作",
                "glob": "📂 文件操作",
                "base64": "🛠️ 开发工具",
                "hash": "🛠️ 开发工具",
                "speed": "🛠️ 开发工具",
                "net_check": "🛠️ 开发工具",
                "tcping": "🛠️ 开发工具",
                "whois": "🛠️ 开发工具",
                "debug": "🛠️ 开发工具",
                "render_and_send_image": "🤖 AI辅助",
                "ai_draw_one": "🤖 AI辅助",
                "ai_study_helper": "🤖 AI辅助",
                "analyze_multimodal": "🤖 AI辅助",
                "minecraft_skin": "🎮 游戏娱乐",
                "renjian": "🎮 游戏娱乐",
                "wenchang_dijun": "🎮 游戏娱乐",
                "novel_search": "🎮 游戏娱乐",
                "news_tencent": "📊 热门榜单",
            }

            # 分类工具
            for tool in available_tools:
                tool_name = tool.get("function", {}).get("name", "")
                tool_desc = tool.get("function", {}).get("description", "")
                category = category_map.get(tool_name, "⚙️ 工具类")
                if category not in categories:
                    categories[category] = []  # 防止不存在的类别
                categories[category].append({"name": tool_name, "desc": tool_desc})

            # 构建工具列表文本
            tools_text = f"🛠️ 弥娅工具箱（共 {len(available_tools)} 个工具）\n"
            tools_text += f"{'=' * 35}\n\n"

            for category, tools in categories.items():
                if tools:
                    tools_text += f"{category}\n"
                    tools_text += f"{'-' * 30}\n"
                    for tool in tools:
                        tools_text += f"  • {tool['name']}\n"
                        # 只显示前40个字符的描述
                        desc = tool["desc"][:40] + "..." if len(tool["desc"]) > 40 else tool["desc"]
                        tools_text += f"    {desc}\n"
                    tools_text += "\n"

            tools_text += f"{'=' * 35}\n"
            tools_text += "💡 使用技巧：\n"
            tools_text += "• 直接说出需求，无需记忆命令\n"
            tools_text += '• 例如："今天上海的天气" 或 "搜索人工智能"\n'
            tools_text += "• 输入 /help 查看完整使用指南\n"

            return tools_text

        except Exception as e:
            logger.error(f"获取Undefined工具列表失败: {e}", exc_info=True)
            return f"获取工具列表失败: {str(e)}"

    async def _initiate_voice_call(self, target_id: str, call_type: str = "private") -> str:
        """
        发起QQ语音通话

        Args:
            target_id: 目标ID（QQ号或群号）
            call_type: 通话类型 (private/group)

        Returns:
            操作结果消息
        """
        try:
            # 注意：OneBot v11 标准不支持直接发起语音/视频通话API
            # 这是一个模拟实现，发送一条提示消息

            if call_type == "private":
                message = f"☎️ 语音通话请求\n\n"
                message += f"由于QQ协议限制，AI无法直接发起语音通话。\n\n"
                message += f"💡 请您手动发起通话：\n"
                message += f"1. 打开与 {target_id} 的聊天窗口\n"
                message += f"2. 点击右侧的电话图标\n"
                message += f'3. 选择"语音通话"\n\n'
                message += f"📞 期待与您的语音交流~"
                logger.info(f"[QQ电话] 尝试发起私聊语音通话: {target_id}")

            else:  # group call
                message = f"☎️ 群语音通话请求\n\n"
                message += f"群号：{target_id}\n\n"
                message += f"由于QQ协议限制，AI无法直接发起群语音通话。\n\n"
                message += f"💡 请您手动操作：\n"
                message += f"1. 进入群聊 {target_id}\n"
                message += f"2. 点击右上角的电话图标\n"
                message += f'3. 选择"发起语音通话"\n\n'
                message += f"🎤 期待与大家的语音交流~"
                logger.info(f"[QQ电话] 尝试发起群语音通话: {target_id}")

            return message

        except Exception as e:
            logger.error(f"发起语音通话错误: {e}", exc_info=True)
            return f"❌ 发起语音通话失败: {str(e)}"

    def _parse_at_mentions(self, message: str, sender_id: Optional[str] = None) -> Dict[str, Any]:
        """
        解析消息中的@信息，提取发送者信息和被@的用户

        Args:
            message: 原始消息内容（可能包含CQ码）
            sender_id: 发送者QQ号

        Returns:
            包含clean_message和mentioned_users的字典
            {
                "clean_message": str,  # 清理后的消息（移除CQ码，转换为可读文本）
                "mentioned_users": List[str],  # 被@的用户QQ号列表
            }
        """
        import re

        result = {
            "clean_message": message,
            "mentioned_users": [],
        }

        try:
            # 解析CQ:at码
            # 格式: [CQ:at,qq=123456789]
            at_pattern = r"\[CQ:at,qq=(\d+)\]"

            mentioned_qqs = re.findall(at_pattern, message)
            result["mentioned_users"] = mentioned_qqs

            # 替换CQ:at码为可读文本
            bot_qq = self.qq_config.get("bot_qq", "")
            creator_qq = self.qq_config.get("creator_qq", "")  # 可选：创造者QQ

            # 构建消息前缀（包含发送者信息）
            message_prefix = ""
            if sender_id:
                message_prefix = f"[发送者QQ:{sender_id}] "

            # 处理消息内容
            clean_msg = message
            at_descriptions = []

            if mentioned_qqs:
                for qq in mentioned_qqs:
                    if qq == bot_qq:
                        at_descriptions.append("@" + self.qq_config.get("ai_name", "弥娅"))
                    elif qq == creator_qq:
                        at_descriptions.append("@创造者")
                    else:
                        at_descriptions.append(f"@用户{qq}")

                # 替换CQ码为可读文本
                if len(at_descriptions) == 1:
                    at_text = at_descriptions[0]
                else:
                    at_text = "、".join(at_descriptions[:-1]) + " 和 " + at_descriptions[-1]

                clean_msg = re.sub(at_pattern, at_text, message)

            # 组合最终消息
            if message_prefix:
                clean_msg = message_prefix + clean_msg

            result["clean_message"] = clean_msg

            # 记录日志
            if mentioned_qqs or sender_id:
                logger.info(f"[消息解析] 发送者:{sender_id} | 被@的用户:{mentioned_qqs} | 原始消息:{message[:50]}...")
                logger.info(f"[消息解析] 处理后消息:{clean_msg[:100]}...")

        except Exception as e:
            logger.error(f"[消息解析] 解析@信息失败: {e}")
            # 出错时返回原始消息
            result["clean_message"] = message

        return result

    def _parse_reply_content(self, message: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析消息中的引用回复内容（CQ:reply）

        Args:
            message: 原始消息内容（可能包含CQ:reply码）
            data: 消息数据字典（可能包含完整消息对象）

        Returns:
            包含clean_message和replied_content的字典
            {
                "clean_message": str,  # 清理后的消息（移除CQ:reply码）
                "replied_content": Optional[str],  # 被回复的消息内容（如果有）
                "replied_sender": Optional[str],  # 被回复消息的发送者（如果有）
            }
        """
        import re

        result = {
            "clean_message": message,
            "replied_content": None,
            "replied_sender": None,
        }

        try:
            # 解析CQ:reply码
            # 格式: [CQ:reply,id=xxx,text=xxx,qq=xxx,time=xxx]
            # 注意：text参数可能包含逗号和特殊字符，需要更宽松的匹配
            reply_pattern = r"\[CQ:reply,([^\]]+)\]"
            reply_match = re.search(reply_pattern, message)

            if reply_match:
                params_str = reply_match.group(1)
                logger.info(f"[引用解析] 检测到引用回复CQ码: {params_str[:100]}...")

                # 解析参数
                replied_content = None
                replied_sender = None

                # 提取text参数（被回复的消息内容）
                # text参数可能很长，包含逗号，使用更智能的解析
                # 格式：text=内容,qq=xxx 或 text=内容（最后一个参数）
                text_pattern = r'text=([^,]+(?:,[^,=]+)*?)(?=,qq=|$|,\])'
                text_match = re.search(text_pattern, params_str)
                if text_match:
                    # text参数可能被URL编码，需要解码
                    try:
                        from urllib.parse import unquote
                        replied_content = unquote(text_match.group(1))
                        # 移除CQ码中的HTML转义
                        import html
                        replied_content = html.unescape(replied_content)
                        # 如果被回复的消息只包含图片，text内容可能是[图片]这样的占位符
                        if replied_content and replied_content.strip():
                            logger.info(f"[引用解析] 被回复内容: {replied_content[:100]}...")
                        else:
                            logger.info("[引用解析] 被回复内容为空或仅图片，忽略text参数")
                    except Exception as e:
                        logger.warning(f"[引用解析] text解码失败: {e}")
                        replied_content = text_match.group(1)
                else:
                    # 如果没有text参数，可能是引用了纯图片/视频消息
                    logger.info("[引用解析] 未找到text参数，可能是引用纯图片/视频消息")

                # 提取qq参数（被回复消息的发送者）
                qq_match = re.search(r'qq=(\d+)', params_str)
                if qq_match:
                    replied_sender = qq_match.group(1)
                    logger.info(f"[引用解析] 被回复发送者: {replied_sender}")

                # 从data中获取更多引用信息（如果有的话）
                reply_data = data.get("reply", {})
                if reply_data:
                    # 尝试从完整消息对象获取更详细的内容
                    message_chain = reply_data.get("message", [])
                    if isinstance(message_chain, list):
                        # 构建完整的被回复消息
                        replied_parts = []
                        for msg_item in message_chain:
                            if isinstance(msg_item, dict):
                                msg_type = msg_item.get("type")
                                msg_data = msg_item.get("data", {})

                                if msg_type == "text":
                                    replied_parts.append(msg_data.get("text", ""))
                                elif msg_type == "at":
                                    qq = msg_data.get("qq", "")
                                    replied_parts.append(f"[@用户{qq}]")
                                elif msg_type == "image":
                                    # 提取图片URL
                                    image_url = msg_data.get("url", "")
                                    if image_url:
                                        replied_parts.append(f"[图片链接: {image_url}]")
                                    else:
                                        replied_parts.append("[图片]")
                                elif msg_type == "face":
                                    replied_parts.append("[表情]")

                        if replied_parts:
                            replied_content = "".join(replied_parts)
                            logger.info(f"[引用解析] 从message_chain获取完整内容: {replied_content[:100]}...")

                    # 尝试从reply的sender字段获取发送者
                    if reply_data.get("sender_id"):
                        replied_sender = reply_data.get("sender_id")

                result["replied_content"] = replied_content
                result["replied_sender"] = replied_sender

                # 移除CQ:reply码
                clean_msg = re.sub(reply_pattern, "", message)
                # 清理多余空格
                clean_msg = re.sub(r'\s+', ' ', clean_msg).strip()
                result["clean_message"] = clean_msg

                logger.info(f"[引用解析] 清理后消息: {clean_msg[:100]}...")

        except Exception as e:
            logger.error(f"[引用解析] 解析引用内容失败: {e}", exc_info=True)
            # 出错时返回原始消息
            result["clean_message"] = message

        return result

    async def _cleanup_old_messages(self):
        """清理过期的消息缓存"""
        while self.running:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次

                now = datetime.now().timestamp()

                # 清理消息缓存
                expired_message_keys = [k for k, v in self.message_cache.items() if now - v > self.cache_ttl]
                for k in expired_message_keys:
                    del self.message_cache[k]

                # 注意：不再清理user_sessions，因为现在使用统一的message_manager
                # message_manager有自己的清理机制

            except Exception as e:
                logger.error(f"清理缓存错误: {e}")


# 全局监听器实例
_listener_instance: Optional[QQWeChatMessageListener] = None


def get_message_listener() -> Optional[QQWeChatMessageListener]:
    """获取全局监听器实例"""
    return _listener_instance


def set_message_listener(listener: QQWeChatMessageListener):
    """设置全局监听器实例"""
    global _listener_instance
    _listener_instance = listener
