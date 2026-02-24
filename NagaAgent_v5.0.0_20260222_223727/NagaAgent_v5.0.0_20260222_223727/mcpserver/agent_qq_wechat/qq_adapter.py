"""
QQ机器人适配器
支持NapCat-Go和go-cqhttp协议（OneBot v11）
基于Undefined项目的OneBotClient实现
"""

import asyncio
import aiohttp
import json
import logging
from typing import Optional, Callable, Dict, Any, List

logger = logging.getLogger(__name__)


class QQBotAdapter:
    """QQ机器人适配器（OneBot v11 WebSocket客户端）"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化QQ适配器

        Args:
            config: 配置字典，包含:
                - adapter: 适配器类型 (napcat-go, go-cqhttp)
                - ws_url: WebSocket地址 (默认 ws://127.0.0.1:3001)
                - http_url: HTTP API地址 (默认 http://127.0.0.1:3000)
                - bot_qq: 机器人QQ号
                - access_token: 访问令牌 (可选，用于HTTP和WebSocket)
                - http_token: HTTP访问令牌 (可选，优先于access_token)
                - ws_token: WebSocket访问令牌 (可选，优先于access_token)
                - auto_reconnect: 是否自动重连 (默认 True)
                - reconnect_interval: 重连间隔 (默认 5秒)
        """
        self.config = config
        self.adapter_type = config.get("adapter", "napcat-go")
        self.ws_url = config.get("ws_url", "ws://127.0.0.1:3001")
        self.http_url = config.get("http_url", "http://127.0.0.1:3000")
        self.bot_qq = config.get("bot_qq", "")
        
        # 支持分别配置HTTP和WebSocket的Token
        self.access_token = config.get("access_token", "")
        self.http_token = config.get("http_token", self.access_token)
        self.ws_token = config.get("ws_token", self.access_token)
        
        self.auto_reconnect = config.get("auto_reconnect", True)
        self.reconnect_interval = config.get("reconnect_interval", 5.0)

        self.ws_client: Optional[aiohttp.ClientSession] = None
        self.http_client: Optional[aiohttp.ClientSession] = None
        self.on_message_callback: Optional[Callable] = None
        self.listening = False
        self._should_stop = False
        self._listen_task = None

        # WebSocket 连接对象
        self._ws = None
        self._message_id = 0
        self._pending_responses: Dict[str, asyncio.Future] = {}
        self._message_tasks: set = set()  # 后台任务集合

    async def connect(self):
        """连接到QQ服务器"""
        try:
            self.http_client = aiohttp.ClientSession()

            # 测试HTTP连接
            status = await self.get_status()
            if status:
                logger.info(f"✓ QQ HTTP API连接成功 (Bot: {self.bot_qq})")
                return True
            else:
                logger.warning("QQ HTTP API连接失败，但继续尝试")
                return False
        except Exception as e:
            logger.error(f"QQ连接错误: {e}")
            return False

    async def disconnect(self):
        """断开连接"""
        self._should_stop = True
        self.listening = False

        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        if self._ws:
            await self._ws.close()
            self._ws = None

        if self.http_client:
            await self.http_client.close()
            self.http_client = None

        if self.ws_client:
            await self.ws_client.close()
            self.ws_client = None

        # 等待所有后台任务完成
        if self._message_tasks:
            await asyncio.gather(*self._message_tasks, return_exceptions=True)

    async def send_message(self, user_id: str, message: str) -> bool:
        """
        发送私聊消息

        Args:
            user_id: 目标QQ号
            message: 消息内容

        Returns:
            是否发送成功
        """
        try:
            # 优先使用WebSocket API
            if self._ws:
                await self._call_api("send_private_msg", {
                    "user_id": int(user_id),
                    "message": message
                })
                logger.debug(f"✓ QQ私聊消息已发送至 {user_id}")
                return True
            else:
                # 回退到HTTP API
                url = f"{self.http_url}/send_private_msg"
                data = {"user_id": int(user_id), "message": message}

                # 使用请求头传递Token
                headers = {}
                if self.http_token:
                    headers["Authorization"] = f"Bearer {self.http_token}"

                async with self.http_client.post(url, json=data, headers=headers) as resp:
                    result = await resp.json()

                    if result.get("status") == "ok" or result.get("retcode") == 0:
                        logger.debug(f"✓ QQ私聊消息已发送至 {user_id}")
                        return True
                    else:
                        logger.error(f"✗ QQ私聊消息发送失败: {result}")
                        return False

        except Exception as e:
            logger.error(f"发送QQ私聊消息错误: {e}")
            return False

    async def send_group_message(self, group_id: str, message: str) -> bool:
        """
        发送群消息

        Args:
            group_id: 群号
            message: 消息内容

        Returns:
            是否发送成功
        """
        try:
            # 优先使用WebSocket API
            if self._ws:
                await self._call_api("send_group_msg", {
                    "group_id": int(group_id),
                    "message": message
                })
                logger.debug(f"✓ QQ群消息已发送至群 {group_id}")
                return True
            else:
                # 回退到HTTP API
                url = f"{self.http_url}/send_group_msg"
                data = {"group_id": int(group_id), "message": message}

                # 使用请求头传递Token
                headers = {}
                if self.http_token:
                    headers["Authorization"] = f"Bearer {self.http_token}"

                async with self.http_client.post(url, json=data, headers=headers) as resp:
                    result = await resp.json()

                    if result.get("status") == "ok" or result.get("retcode") == 0:
                        logger.debug(f"✓ QQ群消息已发送至群 {group_id}")
                        return True
                    else:
                        logger.error(f"✗ QQ群消息发送失败: {result}")
                        return False

        except Exception as e:
            logger.error(f"发送QQ群消息错误: {e}")
            return False

    async def send_forward_message(self, user_id: str, messages: List[str]) -> bool:
        """
        发送转发消息（合并转发）

        Args:
            user_id: 目标QQ号
            messages: 消息列表

        Returns:
            是否发送成功
        """
        try:
            # 构建转发消息节点
            nodes = []
            for msg in messages:
                node = {
                    "type": "node",
                    "data": {
                        "name": "NagaAgent AI助手",
                        "uin": int(self.bot_qq),
                        "content": msg
                    }
                }
                nodes.append(node)

            url = f"{self.http_url}/send_private_forward_msg"
            data = {
                "user_id": int(user_id),
                "messages": nodes
            }

            if self.http_token:
                data["access_token"] = self.http_token

            async with self.http_client.post(url, json=data) as resp:
                result = await resp.json()
                return result.get("status") == "ok" or result.get("retcode") == 0

        except Exception as e:
            logger.error(f"发送QQ转发消息错误: {e}")
            return False

    async def get_status(self) -> Optional[Dict[str, Any]]:
        """获取机器人状态"""
        try:
            url = f"{self.http_url}/get_status"
            headers = {}
            if self.http_token:
                headers["Authorization"] = f"Bearer {self.http_token}"

            async with self.http_client.get(url, headers=headers) as resp:
                return await resp.json()
        except Exception as e:
            logger.error(f"获取QQ状态错误: {e}")
            return None

    async def get_group_list(self) -> List[Dict[str, Any]]:
        """获取群列表"""
        try:
            url = f"{self.http_url}/get_group_list"
            headers = {}
            if self.http_token:
                headers["Authorization"] = f"Bearer {self.http_token}"

            async with self.http_client.get(url, headers=headers) as resp:
                result = await resp.json()
                if result.get("status") == "ok" or result.get("retcode") == 0:
                    return result.get("data", [])
                return []
        except Exception as e:
            logger.error(f"获取QQ群列表错误: {e}")
            return []

    async def get_friend_list(self) -> List[Dict[str, Any]]:
        """获取好友列表"""
        try:
            url = f"{self.http_url}/get_friend_list"
            headers = {}
            if self.http_token:
                headers["Authorization"] = f"Bearer {self.http_token}"

            async with self.http_client.get(url, headers=headers) as resp:
                result = await resp.json()
                if result.get("status") == "ok" or result.get("retcode") == 0:
                    return result.get("data", [])
                return []
        except Exception as e:
            logger.error(f"获取QQ好友列表错误: {e}")
            return []

    async def get_group_msg_history(
        self,
        group_id: str,
        message_seq: Optional[int] = None,
        count: int = 500
    ) -> List[Dict[str, Any]]:
        """获取群消息历史

        Args:
            group_id: 群号
            message_seq: 起始消息序号，None表示从最新消息开始
            count: 获取的消息数量

        Returns:
            消息列表
        """
        try:
            params: Dict[str, Any] = {"group_id": int(group_id), "count": count}
            if message_seq is not None:
                params["message_seq"] = message_seq

            response = await self._call_api("get_group_msg_history", params)
            messages = response.get("data", {}).get("messages", [])
            logger.debug(f"获取到{len(messages)}条历史消息")
            return messages
        except Exception as e:
            logger.error(f"获取群消息历史错误: {e}")
            return []

    async def send_forward_msg(self, group_id: str, messages: List[Dict[str, Any]]) -> bool:
        """发送合并转发消息到群聊

        Args:
            group_id: 群号
            messages: 消息节点列表，每个节点格式为:
                {
                    "type": "node",
                    "data": {
                        "name": "发送者昵称",
                        "uin": "发送者QQ号",
                        "content": "消息内容（字符串或消息段数组）",
                        "time": "时间戳（可选）"
                    }
                }

        Returns:
            是否发送成功
        """
        try:
            await self._call_api("send_forward_msg", {
                "group_id": int(group_id),
                "messages": messages
            })
            logger.debug(f"✓ 合并转发消息已发送至群 {group_id}")
            return True
        except Exception as e:
            logger.error(f"发送合并转发消息错误: {e}")
            return False

    async def send_like(self, user_id: str, times: int = 1) -> bool:
        """给用户点赞

        Args:
            user_id: 对方QQ号
            times: 赞的次数（默认1次）

        Returns:
            是否发送成功
        """
        try:
            await self._call_api("send_like", {
                "user_id": int(user_id),
                "times": times
            })
            logger.debug(f"✓ 已给用户{user_id}点赞{times}次")
            return True
        except Exception as e:
            logger.error(f"点赞错误: {e}")
            return False

    async def send_record_audio(self, user_id: str, audio_path: str) -> bool:
        """发送私聊语音消息

        Args:
            user_id: 目标QQ号
            audio_path: 音频文件路径

        Returns:
            是否发送成功
        """
        try:
            import os

            if not os.path.exists(audio_path):
                logger.error(f"音频文件不存在: {audio_path}")
                return False

            # 优先使用WebSocket API
            if self._ws:
                await self._call_api("send_private_msg", {
                    "user_id": int(user_id),
                    "message": [{
                        "type": "record",
                        "data": {
                            "file": audio_path
                        }
                    }]
                })
                logger.debug(f"✓ QQ私聊语音已发送至 {user_id}")
                return True
            else:
                # 回退到HTTP API - 需要上传文件
                url = f"{self.http_url}/send_private_msg"
                data = {"user_id": int(user_id)}

                # 使用请求头传递Token
                headers = {}
                if self.http_token:
                    headers["Authorization"] = f"Bearer {self.http_token}"

                # 准备multipart/form-data
                import aiohttp
                with open(audio_path, 'rb') as f:
                    form_data = aiohttp.FormData()
                    form_data.add_field('user_id', str(int(user_id)))
                    form_data.add_field('message', audio_path,
                                       filename=os.path.basename(audio_path),
                                       content_type='audio/mpeg')

                    async with self.http_client.post(url, data=form_data, headers=headers) as resp:
                        result = await resp.json()

                        if result.get("status") == "ok" or result.get("retcode") == 0:
                            logger.debug(f"✓ QQ私聊语音已发送至 {user_id}")
                            return True
                        else:
                            logger.error(f"✗ QQ私聊语音发送失败: {result}")
                            return False

        except Exception as e:
            logger.error(f"发送QQ私聊语音错误: {e}")
            return False

    async def send_group_audio(self, group_id: str, audio_path: str) -> bool:
        """发送群语音消息

        Args:
            group_id: 群号
            audio_path: 音频文件路径

        Returns:
            是否发送成功
        """
        try:
            import os

            if not os.path.exists(audio_path):
                logger.error(f"音频文件不存在: {audio_path}")
                return False

            # 优先使用WebSocket API
            if self._ws:
                await self._call_api("send_group_msg", {
                    "group_id": int(group_id),
                    "message": [{
                        "type": "record",
                        "data": {
                            "file": audio_path
                        }
                    }]
                })
                logger.debug(f"✓ QQ群语音已发送至群 {group_id}")
                return True
            else:
                # 回退到HTTP API - 需要上传文件
                url = f"{self.http_url}/send_group_msg"
                data = {"group_id": int(group_id)}

                # 使用请求头传递Token
                headers = {}
                if self.http_token:
                    headers["Authorization"] = f"Bearer {self.http_token}"

                # 准备multipart/form-data
                import aiohttp
                with open(audio_path, 'rb') as f:
                    form_data = aiohttp.FormData()
                    form_data.add_field('group_id', str(int(group_id)))
                    form_data.add_field('message', audio_path,
                                       filename=os.path.basename(audio_path),
                                       content_type='audio/mpeg')

                    async with self.http_client.post(url, data=form_data, headers=headers) as resp:
                        result = await resp.json()

                        if result.get("status") == "ok" or result.get("retcode") == 0:
                            logger.debug(f"✓ QQ群语音已发送至群 {group_id}")
                            return True
                        else:
                            logger.error(f"✗ QQ群语音发送失败: {result}")
                            return False

        except Exception as e:
            logger.error(f"发送QQ群语音错误: {e}")
            return False

    def set_message_callback(self, callback: Callable):
        """
        设置消息接收回调

        Args:
            callback: 回调函数，签名: async callback(message_type, data)
        """
        self.on_message_callback = callback

    async def start_listening(self):
        """开始监听消息（通过WebSocket，支持自动重连）"""
        if not self.on_message_callback:
            logger.warning("未设置消息回调，跳过监听")
            return

        self.listening = True
        self._should_stop = False

        if self.auto_reconnect:
            self._listen_task = asyncio.create_task(self._listen_with_reconnect())
        else:
            self._listen_task = asyncio.create_task(self._listen_loop())

    async def _listen_with_reconnect(self):
        """带自动重连的监听循环"""
        while not self._should_stop:
            try:
                await self._connect_ws()
                await self._listen_loop()
            except Exception as e:
                logger.error(f"WebSocket连接错误: {e}")

            if self._should_stop:
                break

            logger.info(f"{self.reconnect_interval}秒后重连...")
            await asyncio.sleep(self.reconnect_interval)

    async def _connect_ws(self):
        """建立WebSocket连接"""
        # 构建带 token 的 URL
        url = self.ws_url
        if self.ws_token:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}access_token={self.ws_token}"

        logger.info(f"正在连接到 {url}")

        # 请求头传递token
        extra_headers = {}
        if self.ws_token:
            extra_headers["Authorization"] = f"Bearer {self.ws_token}"

        self.ws_client = aiohttp.ClientSession()
        self._ws = await self.ws_client.ws_connect(
            url,
            headers=extra_headers if extra_headers else None,
        )
        logger.info("QQ WebSocket连接成功")

    async def _listen_loop(self):
        """WebSocket监听循环"""
        if not self._ws:
            raise RuntimeError("WebSocket未连接")

        try:
            async for msg in self._ws:
                if not self.listening:
                    break

                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        # 处理消息（不阻塞接收循环）
                        await self._dispatch_message(data)
                    except json.JSONDecodeError:
                        logger.warning(f"无法解析WebSocket消息: {msg.data}")
                    except Exception as e:
                        logger.error(f"处理QQ消息错误: {e}")

                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.warning("QQ WebSocket连接已关闭")
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"QQ WebSocket错误: {self._ws.exception()}")
                    break
        except Exception as e:
            logger.error(f"WebSocket监听错误: {e}")
        finally:
            self.listening = False

    async def _dispatch_message(self, data: Dict[str, Any]):
        """分发消息（API响应同步处理，事件异步处理）"""
        # 检查是否是API响应
        echo = data.get("echo")
        if echo is not None:
            echo_str = str(echo)
            if echo_str in self._pending_responses:
                logger.debug(f"收到API响应: echo={echo_str}")
                self._pending_responses[echo_str].set_result(data)
                return

        # 处理事件类型的消息
        post_type = data.get("post_type")
        if post_type == "message":
            message_type = data.get("message_type", "unknown")  # private, group
            sender = data.get("sender", {}).get("user_id", "unknown")
            logger.info(f"收到QQ消息: type={message_type}, sender={sender}")

            if self.on_message_callback:
                # 创建后台任务处理消息
                task = asyncio.create_task(self._safe_handle_message(message_type, data))
                self._message_tasks.add(task)
                task.add_done_callback(self._message_tasks.discard)
        elif post_type == "notice":
            notice_type = data.get("notice_type", "")
            sub_type = data.get("sub_type", "")
            # 处理bot掉线事件
            if notice_type == "bot_offline":
                logger.warning("QQ机器人掉线，将尝试重连...")
                # 关闭当前连接，触发自动重连
                if self._ws:
                    await self._ws.close()
                    self._ws = None
            # 处理拍一拍事件
            elif notice_type == "notify" and sub_type == "poke":
                target_id = data.get("target_id", 0)
                sender_id = data.get("user_id", 0)
                group_id = data.get("group_id", 0)
                logger.info(f"收到拍一拍: sender={sender_id}, target={target_id}, group={group_id}")

                if target_id == int(self.bot_qq) and self.on_message_callback:
                    # 将poke事件转换为消息格式
                    poke_event = {
                        "post_type": "notice",
                        "notice_type": "poke",
                        "group_id": group_id,
                        "user_id": sender_id,
                        "sender": {"user_id": sender_id},
                        "target_id": target_id,
                        "message": [],
                    }
                    task = asyncio.create_task(self._safe_handle_message("poke", poke_event))
                    self._message_tasks.add(task)
                    task.add_done_callback(self._message_tasks.discard)
            else:
                logger.debug(f"收到通知事件: notice_type={notice_type}, sub_type={sub_type}")

    async def _safe_handle_message(self, message_type: str, data: Dict[str, Any]):
        """安全地处理消息（捕获异常）"""
        try:
            if self.on_message_callback:
                await self.on_message_callback(message_type, data)
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")

    async def _call_api(self, action: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """通过WebSocket调用OneBot API"""
        if not self._ws:
            raise RuntimeError("WebSocket未连接")

        self._message_id += 1
        echo = str(self._message_id)

        request = {
            "action": action,
            "params": params or {},
            "echo": echo,
        }

        logger.debug(f"API调用: {action}, params={params}, echo={echo}")

        # 创建Future等待响应
        future: asyncio.Future = asyncio.Future()
        self._pending_responses[echo] = future

        try:
            await self._ws.send_json(request)
            logger.debug(f"API请求已发送: {action}")
            # 等待响应，超时30秒
            response = await asyncio.wait_for(future, timeout=30.0)

            # 检查响应状态
            status = response.get("status")
            if status == "failed":
                retcode = response.get("retcode", -1)
                msg = response.get("message", "未知错误")
                logger.error(f"API调用失败: {action}, retcode={retcode}, message={msg}")
                raise RuntimeError(f"API调用失败: {msg} (retcode={retcode})")

            logger.debug(f"API响应: {action}, status={status}")
            return response
        except asyncio.TimeoutError:
            logger.error(f"API调用超时: {action}, echo={echo}")
            raise
        finally:
            self._pending_responses.pop(echo, None)
