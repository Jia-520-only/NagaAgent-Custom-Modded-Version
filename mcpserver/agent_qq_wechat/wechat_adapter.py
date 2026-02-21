"""
微信机器人适配器
支持itchat协议
"""

import asyncio
import logging
from typing import Optional, Callable, Dict, Any, List

# 可选导入 itchat
try:
    import itchat
    from itchat.content import TEXT, FRIENDS, MAP, CARD, NOTE, SHARING, PICTURE
    ICHAT_AVAILABLE = True
except ImportError:
    ICHAT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("itchat 未安装，微信功能将不可用。安装方法: pip install itchat")

logger = logging.getLogger(__name__)


class WeChatBotAdapter:
    """微信机器人适配器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化微信适配器

        Args:
            config: 配置字典，包含:
                - auto_login: 是否自动登录
                - enable_login_qrcode: 是否在终端显示二维码
                - save_chat_history: 是否保存聊天记录
        """
        self.config = config
        self.auto_login = config.get("auto_login", True)
        self.enable_login_qrcode = config.get("enable_login_qrcode", True)

        self.on_message_callback: Optional[Callable] = None
        self.listening = False
        self._login_status = False

    async def connect(self):
        """连接到微信服务器"""
        if not ICHAT_AVAILABLE:
            logger.error("itchat 未安装，无法连接微信")
            return False

        try:
            # 在后台线程运行itchat
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._login_itchat)

            if self._login_status:
                logger.info("✓ 微信适配器连接成功")
                return True
            else:
                logger.warning("微信适配器连接失败")
                return False
        except Exception as e:
            logger.error(f"微信适配器连接错误: {e}")
            return False

    def _login_itchat(self):
        """同步登录itchat"""
        if not ICHAT_AVAILABLE:
            logger.error("itchat 未安装")
            self._login_status = False
            return

        try:
            # 登录选项
            # enableCmdQR: 2=缩小二维码(适合手机扫码), True=正常大小, False=不显示
            login_options = {
                "enableCmdQR": 2 if self.enable_login_qrcode else False,
                "hotReload": True  # 保留登录状态
            }

            logger.info("正在尝试登录微信...")
            logger.info("提示：如果扫码后出现错误，可能是微信限制或网络问题")

            if self.auto_login:
                itchat.auto_login(**login_options)
            else:
                itchat.login(**login_options)

            # 注册消息处理器
            @itchat.msg_register(TEXT)
            def handle_text_message(msg):
                """处理文本消息"""
                if self.on_message_callback and self.listening:
                    data = {
                        "message_type": "private",
                        "user_id": msg['FromUserName'],
                        "user_name": msg['User'].get('NickName', 'Unknown'),
                        "message": msg['Text'],
                        "is_self": msg['ToUserName'] == msg['FromUserName']
                    }

                    # 使用异步回调
                    try:
                        loop = asyncio.get_event_loop()
                        loop.create_task(self.on_message_callback("private", data))
                    except:
                        pass

            self._login_status = True
            logger.info("✓ 微信登录成功")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"itchat登录错误: {e}")
            logger.error(f"错误类型: {type(e).__name__}")

            # 提供更详细的错误信息和解决建议
            if "mismatched tag" in error_msg:
                logger.error("这是一个itchat库的XML解析错误，可能是:")
                logger.error("1. itchat库与当前微信版本不兼容")
                logger.error("2. 微信协议已更新导致登录接口变化")
                logger.error("建议: 暂时禁用微信，使用QQ功能")
            elif "hotReload" in error_msg:
                logger.error("热重载登录失败，请尝试删除 itchat.pkl 文件后重试")
            elif "timeout" in error_msg.lower():
                logger.error("登录超时，请检查网络连接")

            self._login_status = False

    async def disconnect(self):
        """断开连接"""
        self.listening = False
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, itchat.logout)
            logger.info("微信已断开连接")
        except Exception as e:
            logger.error(f"微信断开连接错误: {e}")

    async def send_message(self, user_id: str, message: str) -> bool:
        """
        发送消息

        Args:
            user_id: 目标用户ID (FromUserName)
            message: 消息内容

        Returns:
            是否发送成功
        """
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: itchat.send(message, toUserName=user_id)
            )
            logger.debug(f"✓ 微信消息已发送至 {user_id}")
            return True
        except Exception as e:
            logger.error(f"发送微信消息错误: {e}")
            return False

    async def send_to_friend(self, friend_name: str, message: str) -> bool:
        """
        根据好友昵称发送消息

        Args:
            friend_name: 好友昵称
            message: 消息内容

        Returns:
            是否发送成功
        """
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: itchat.send(message, toUserName=friend_name)
            )
            logger.debug(f"✓ 微信消息已发送至好友 {friend_name}")
            return True
        except Exception as e:
            logger.error(f"发送微信好友消息错误: {e}")
            return False

    async def get_friends(self) -> List[Dict[str, Any]]:
        """获取好友列表"""
        try:
            loop = asyncio.get_event_loop()
            friends = await loop.run_in_executor(None, itchat.get_friends)

            # 转换为标准格式
            result = []
            for friend in friends[1:]:  # 跳过自己
                result.append({
                    "user_id": friend.get("UserName"),
                    "name": friend.get("NickName"),
                    "remark": friend.get("RemarkName"),
                    "province": friend.get("Province"),
                    "city": friend.get("City")
                })

            return result
        except Exception as e:
            logger.error(f"获取微信好友列表错误: {e}")
            return []

    async def get_chat_rooms(self) -> List[Dict[str, Any]]:
        """获取群聊列表"""
        try:
            loop = asyncio.get_event_loop()
            chat_rooms = await loop.run_in_executor(None, itchat.get_chatrooms)

            result = []
            for room in chat_rooms:
                result.append({
                    "user_id": room.get("UserName"),
                    "name": room.get("NickName"),
                    "member_count": room.get("MemberCount", 0)
                })

            return result
        except Exception as e:
            logger.error(f"获取微信群聊列表错误: {e}")
            return []

    async def send_to_chatroom(self, chatroom_name: str, message: str) -> bool:
        """
        发送群聊消息

        Args:
            chatroom_name: 群聊名称
            message: 消息内容

        Returns:
            是否发送成功
        """
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: itchat.send(message, toUserName=chatroom_name)
            )
            logger.debug(f"✓ 微信群聊消息已发送至 {chatroom_name}")
            return True
        except Exception as e:
            logger.error(f"发送微信群聊消息错误: {e}")
            return False

    def set_message_callback(self, callback: Callable):
        """
        设置消息接收回调

        Args:
            callback: 回调函数，签名: async callback(message_type, data)
        """
        self.on_message_callback = callback

    async def start_listening(self):
        """开始监听消息"""
        if not self.on_message_callback:
            logger.warning("未设置消息回调，跳过监听")
            return

        self.listening = True
        # itchat的消息处理器已在_connect中注册，这里只需要标记状态
        logger.info("微信消息监听已启动")
