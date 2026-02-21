"""
QQ/微信集成Agent
处理QQ和微信消息的发送和接收
"""

import json
import logging
from typing import Any, Dict, Optional

from .qq_adapter import QQBotAdapter
from .wechat_adapter import WeChatBotAdapter
from .message_listener import QQWeChatMessageListener, set_message_listener, get_message_listener

logger = logging.getLogger(__name__)


class AgentQQWeChat:
    """QQ/微信集成Agent"""

    name = "agent_qq_wechat"
    instructions = "处理QQ和微信消息，支持发送和接收消息"

    def __init__(self):
        super().__init__()

        # 适配器实例
        self.qq_adapter: Optional[QQBotAdapter] = None
        self.wechat_adapter: Optional[WeChatBotAdapter] = None

        # 配置
        self.config = None

        # 消息监听器
        self.message_listener: Optional[QQWeChatMessageListener] = None

    def _create_response(self, success: bool, message: str, data: dict = None) -> str:
        """创建标准化响应"""
        response = {
            "success": success,
            "message": message,
            "data": data or {}
        }
        return json.dumps(response, ensure_ascii=False)

    async def initialize(self, config: Dict[str, Any]):
        """
        初始化Agent

        Args:
            config: 配置字典，包含qq和wechat配置
        """
        self.config = config

        # 初始化消息监听器
        self.message_listener = QQWeChatMessageListener(config)
        await self.message_listener.start()
        set_message_listener(self.message_listener)

        # 初始化QQ适配器
        qq_config = config.get("qq", {})
        if qq_config.get("enabled", False):
            self.qq_adapter = QQBotAdapter(qq_config)
            await self.qq_adapter.connect()

            # 设置消息回调
            self.qq_adapter.set_message_callback(self.message_listener.handle_qq_message)

            # 启动消息监听
            if qq_config.get("enable_auto_reply", True):
                await self.qq_adapter.start_listening()

        # 初始化微信适配器
        wechat_config = config.get("wechat", {})
        if wechat_config.get("enabled", False):
            self.wechat_adapter = WeChatBotAdapter(wechat_config)
            await self.wechat_adapter.connect()

            # 设置消息回调
            self.wechat_adapter.set_message_callback(self.message_listener.handle_wechat_message)

            # 启动消息监听
            if wechat_config.get("enable_auto_reply", True):
                await self.wechat_adapter.start_listening()

        logger.info("QQ/微信Agent初始化完成，消息监听已启用")

    async def handle_handoff(self, data: dict) -> str:
        """
        统一处理入口

        Args:
            data: 请求数据，包含tool_name字段

        Returns:
            JSON格式的响应字符串
        """
        try:
            tool_name = data.get("tool_name")

            if tool_name == "发送QQ消息":
                return await self._send_qq_message(data)
            elif tool_name == "发送QQ群消息":
                return await self._send_qq_group_message(data)
            elif tool_name == "发送QQ语音":
                return await self._send_qq_audio(data)
            elif tool_name == "发送QQ群语音":
                return await self._send_qq_group_audio(data)
            elif tool_name == "发送合并转发消息":
                return await self._send_forward_message(data)
            elif tool_name == "点赞用户":
                return await self._send_like(data)
            elif tool_name == "获取群消息历史":
                return await self._get_group_history(data)
            elif tool_name == "发送微信消息":
                return await self._send_wechat_message(data)
            elif tool_name == "发送微信群消息":
                return await self._send_wechat_group_message(data)
            elif tool_name == "获取QQ状态":
                return await self._get_qq_status()
            elif tool_name == "获取QQ群列表":
                return await self._get_qq_groups()
            elif tool_name == "获取QQ好友列表":
                return await self._get_qq_friends()
            elif tool_name == "获取微信好友列表":
                return await self._get_wechat_friends()
            elif tool_name == "获取微信群列表":
                return await self._get_wechat_groups()
            else:
                return self._create_response(
                    False,
                    f"未知工具: {tool_name}",
                    {}
                )
        except Exception as e:
            logger.error(f"处理QQ/微信请求错误: {e}")
            return self._create_response(
                False,
                f"处理请求时发生错误: {str(e)}",
                {}
            )

    async def _send_qq_message(self, data: dict) -> str:
        """发送QQ私聊消息"""
        try:
            user_id = data.get("user_id")
            message = data.get("message")

            if not user_id or not message:
                return self._create_response(
                    False,
                    "缺少user_id或message参数",
                    {}
                )

            if not self.qq_adapter:
                return self._create_response(
                    False,
                    "QQ适配器未初始化，请先在config.json中启用QQ并配置",
                    {}
                )

            success = await self.qq_adapter.send_message(user_id, message)

            if success:
                return self._create_response(
                    True,
                    "QQ消息发送成功",
                    {"user_id": user_id, "message": message}
                )
            else:
                return self._create_response(
                    False,
                    "QQ消息发送失败",
                    {}
                )

        except Exception as e:
            logger.error(f"发送QQ消息错误: {e}")
            return self._create_response(
                False,
                f"发送QQ消息失败: {str(e)}",
                {}
            )

    async def _send_qq_group_message(self, data: dict) -> str:
        """发送QQ群消息"""
        try:
            group_id = data.get("group_id")
            message = data.get("message")

            if not group_id or not message:
                return self._create_response(
                    False,
                    "缺少group_id或message参数",
                    {}
                )

            if not self.qq_adapter:
                return self._create_response(
                    False,
                    "QQ适配器未初始化",
                    {}
                )

            success = await self.qq_adapter.send_group_message(group_id, message)

            if success:
                return self._create_response(
                    True,
                    "QQ群消息发送成功",
                    {"group_id": group_id, "message": message}
                )
            else:
                return self._create_response(
                    False,
                    "QQ群消息发送失败",
                    {}
                )

        except Exception as e:
            logger.error(f"发送QQ群消息错误: {e}")
            return self._create_response(
                False,
                f"发送QQ群消息失败: {str(e)}",
                {}
            )

    async def _send_qq_audio(self, data: dict) -> str:
        """发送QQ语音消息"""
        try:
            user_id = data.get("user_id")
            audio_path = data.get("audio_path")
            text = data.get("text", "")  # 可选文本内容

            if not user_id or not audio_path:
                return self._create_response(
                    False,
                    "缺少user_id或audio_path参数",
                    {}
                )

            if not self.qq_adapter:
                return self._create_response(
                    False,
                    "QQ适配器未初始化，请先在config.json中启用QQ并配置",
                    {}
                )

            # 如果只提供了文本，需要先生成语音
            if text and not audio_path:
                try:
                    import sys
                    import os
                    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

                    # 使用语音集成生成音频
                    from voice.output.voice_integration import get_voice_integration
                    voice_integration = get_voice_integration()

                    # 生成音频
                    audio_data = await self._generate_audio_sync(text)
                    if audio_data:
                        # 保存为临时文件
                        import tempfile
                        audio_path = tempfile.mktemp(suffix=".mp3")
                        with open(audio_path, 'wb') as f:
                            f.write(audio_data)
                    else:
                        logger.warning("语音生成失败，仅发送文本消息")
                        audio_path = None

                except Exception as e:
                    logger.error(f"生成语音失败: {e}")
                    audio_path = None

            # 发送语音
            success = False
            if audio_path:
                success = await self.qq_adapter.send_record_audio(user_id, audio_path)

            # 如果语音发送失败或未生成，回退到文本
            if not success and text:
                success = await self.qq_adapter.send_message(user_id, f"[语音]{text}")

            if success:
                return self._create_response(
                    True,
                    "QQ语音消息发送成功",
                    {"user_id": user_id, "audio_path": audio_path}
                )
            else:
                return self._create_response(
                    False,
                    "QQ语音消息发送失败",
                    {}
                )

        except Exception as e:
            logger.error(f"发送QQ语音消息错误: {e}")
            return self._create_response(
                False,
                f"发送QQ语音消息失败: {str(e)}",
                {}
            )

    async def _send_qq_group_audio(self, data: dict) -> str:
        """发送QQ群语音消息"""
        try:
            group_id = data.get("group_id")
            audio_path = data.get("audio_path")
            text = data.get("text", "")  # 可选文本内容

            if not group_id or (not audio_path and not text):
                return self._create_response(
                    False,
                    "缺少group_id、audio_path或text参数",
                    {}
                )

            if not self.qq_adapter:
                return self._create_response(
                    False,
                    "QQ适配器未初始化",
                    {}
                )

            # 如果只提供了文本，需要先生成语音
            if text and not audio_path:
                try:
                    import sys
                    import os
                    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

                    # 使用语音集成生成音频
                    from voice.output.voice_integration import get_voice_integration
                    voice_integration = get_voice_integration()

                    # 生成音频
                    audio_data = await self._generate_audio_sync(text)
                    if audio_data:
                        # 保存为临时文件
                        import tempfile
                        audio_path = tempfile.mktemp(suffix=".mp3")
                        with open(audio_path, 'wb') as f:
                            f.write(audio_data)
                    else:
                        logger.warning("语音生成失败，仅发送文本消息")
                        audio_path = None

                except Exception as e:
                    logger.error(f"生成语音失败: {e}")
                    audio_path = None

            # 发送语音
            success = False
            if audio_path:
                success = await self.qq_adapter.send_group_audio(group_id, audio_path)

            # 如果语音发送失败或未生成，回退到文本
            if not success and text:
                success = await self.qq_adapter.send_group_message(group_id, f"[语音]{text}")

            if success:
                return self._create_response(
                    True,
                    "QQ群语音消息发送成功",
                    {"group_id": group_id, "audio_path": audio_path}
                )
            else:
                return self._create_response(
                    False,
                    "QQ群语音消息发送失败",
                    {}
                )

        except Exception as e:
            logger.error(f"发送QQ群语音消息错误: {e}")
            return self._create_response(
                False,
                f"发送QQ群语音消息失败: {str(e)}",
                {}
            )

    async def _generate_audio_sync(self, text: str) -> bytes:
        """同步生成音频数据 - 使用GPT-SoVITS"""
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

            from voice.output.voice_integration import VoiceIntegration
            voice_integration = VoiceIntegration()
            return await voice_integration._generate_audio_sync(text)
        except Exception as e:
            logger.error(f"生成音频数据异常: {e}")
            return None

    async def _send_wechat_message(self, data: dict) -> str:
        """发送微信消息"""
        try:
            user_id = data.get("user_id")
            friend_name = data.get("friend_name")
            message = data.get("message")

            if not message:
                return self._create_response(
                    False,
                    "缺少message参数",
                    {}
                )

            if not self.wechat_adapter:
                return self._create_response(
                    False,
                    "微信适配器未初始化，请先在config.json中启用微信并配置",
                    {}
                )

            success = False
            if user_id:
                success = await self.wechat_adapter.send_message(user_id, message)
            elif friend_name:
                success = await self.wechat_adapter.send_to_friend(friend_name, message)

            if success:
                return self._create_response(
                    True,
                    "微信消息发送成功",
                    {"message": message}
                )
            else:
                return self._create_response(
                    False,
                    "微信消息发送失败",
                    {}
                )

        except Exception as e:
            logger.error(f"发送微信消息错误: {e}")
            return self._create_response(
                False,
                f"发送微信消息失败: {str(e)}",
                {}
            )

    async def _send_wechat_group_message(self, data: dict) -> str:
        """发送微信群消息"""
        try:
            chatroom_name = data.get("chatroom_name")
            message = data.get("message")

            if not chatroom_name or not message:
                return self._create_response(
                    False,
                    "缺少chatroom_name或message参数",
                    {}
                )

            if not self.wechat_adapter:
                return self._create_response(
                    False,
                    "微信适配器未初始化",
                    {}
                )

            success = await self.wechat_adapter.send_to_chatroom(chatroom_name, message)

            if success:
                return self._create_response(
                    True,
                    "微信群消息发送成功",
                    {"chatroom_name": chatroom_name, "message": message}
                )
            else:
                return self._create_response(
                    False,
                    "微信群消息发送失败",
                    {}
                )

        except Exception as e:
            logger.error(f"发送微信群消息错误: {e}")
            return self._create_response(
                False,
                f"发送微信群消息失败: {str(e)}",
                {}
            )

    async def _get_qq_status(self) -> str:
        """获取QQ状态"""
        try:
            if not self.qq_adapter:
                return self._create_response(
                    False,
                    "QQ适配器未初始化",
                    {}
                )

            status = await self.qq_adapter.get_status()
            return self._create_response(
                True,
                "获取QQ状态成功",
                {"status": status}
            )
        except Exception as e:
            return self._create_response(
                False,
                f"获取QQ状态失败: {str(e)}",
                {}
            )

    async def _get_qq_groups(self) -> str:
        """获取QQ群列表"""
        try:
            if not self.qq_adapter:
                return self._create_response(
                    False,
                    "QQ适配器未初始化",
                    {}
                )

            groups = await self.qq_adapter.get_group_list()
            return self._create_response(
                True,
                f"获取到{len(groups)}个QQ群",
                {"groups": groups}
            )
        except Exception as e:
            return self._create_response(
                False,
                f"获取QQ群列表失败: {str(e)}",
                {}
            )

    async def _get_qq_friends(self) -> str:
        """获取QQ好友列表"""
        try:
            if not self.qq_adapter:
                return self._create_response(
                    False,
                    "QQ适配器未初始化",
                    {}
                )

            friends = await self.qq_adapter.get_friend_list()
            return self._create_response(
                True,
                f"获取到{len(friends)}个QQ好友",
                {"friends": friends}
            )
        except Exception as e:
            return self._create_response(
                False,
                f"获取QQ好友列表失败: {str(e)}",
                {}
            )

    async def _get_wechat_friends(self) -> str:
        """获取微信好友列表"""
        try:
            if not self.wechat_adapter:
                return self._create_response(
                    False,
                    "微信适配器未初始化",
                    {}
                )

            friends = await self.wechat_adapter.get_friends()
            return self._create_response(
                True,
                f"获取到{len(friends)}个微信好友",
                {"friends": friends}
            )
        except Exception as e:
            return self._create_response(
                False,
                f"获取微信好友列表失败: {str(e)}",
                {}
            )

    async def _get_wechat_groups(self) -> str:
        """获取微信群列表"""
        try:
            if not self.wechat_adapter:
                return self._create_response(
                    False,
                    "微信适配器未初始化",
                    {}
                )

            groups = await self.wechat_adapter.get_chat_rooms()
            return self._create_response(
                True,
                f"获取到{len(groups)}个微信群",
                {"groups": groups}
            )
        except Exception as e:
            return self._create_response(
                False,
                f"获取微信群列表失败: {str(e)}",
                {}
            )

    async def _send_forward_message(self, data: dict) -> str:
        """发送合并转发消息"""
        try:
            group_id = data.get("group_id")
            messages = data.get("messages")

            if not group_id or not messages:
                return self._create_response(
                    False,
                    "缺少group_id或messages参数",
                    {}
                )

            if not self.qq_adapter:
                return self._create_response(
                    False,
                    "QQ适配器未初始化",
                    {}
                )

            success = await self.qq_adapter.send_forward_msg(group_id, messages)

            if success:
                return self._create_response(
                    True,
                    "合并转发消息发送成功",
                    {"group_id": group_id, "message_count": len(messages)}
                )
            else:
                return self._create_response(
                    False,
                    "合并转发消息发送失败",
                    {}
                )
        except Exception as e:
            logger.error(f"发送合并转发消息错误: {e}")
            return self._create_response(
                False,
                f"发送合并转发消息失败: {str(e)}",
                {}
            )

    async def _send_like(self, data: dict) -> str:
        """点赞用户"""
        try:
            user_id = data.get("user_id")
            times = data.get("times", 1)

            if not user_id:
                return self._create_response(
                    False,
                    "缺少user_id参数",
                    {}
                )

            if not self.qq_adapter:
                return self._create_response(
                    False,
                    "QQ适配器未初始化",
                    {}
                )

            success = await self.qq_adapter.send_like(user_id, times)

            if success:
                return self._create_response(
                    True,
                    f"已成功给用户{user_id}点赞{times}次",
                    {"user_id": user_id, "times": times}
                )
            else:
                return self._create_response(
                    False,
                    "点赞失败",
                    {}
                )
        except Exception as e:
            logger.error(f"点赞错误: {e}")
            return self._create_response(
                False,
                f"点赞失败: {str(e)}",
                {}
            )

    async def _get_group_history(self, data: dict) -> str:
        """获取群消息历史"""
        try:
            group_id = data.get("group_id")
            count = data.get("count", 500)
            message_seq = data.get("message_seq")

            if not group_id:
                return self._create_response(
                    False,
                    "缺少group_id参数",
                    {}
                )

            if not self.qq_adapter:
                return self._create_response(
                    False,
                    "QQ适配器未初始化",
                    {}
                )

            messages = await self.qq_adapter.get_group_msg_history(
                group_id, message_seq, count
            )

            return self._create_response(
                True,
                f"获取到{len(messages)}条历史消息",
                {"messages": messages, "count": len(messages)}
            )
        except Exception as e:
            logger.error(f"获取群消息历史错误: {e}")
            return self._create_response(
                False,
                f"获取群消息历史失败: {str(e)}",
                {}
            )


def create_qq_wechat_agent() -> AgentQQWeChat:
    """创建QQ/微信Agent实例"""
    return AgentQQWeChat()
