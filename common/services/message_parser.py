"""统一消息解析器

提供一次性消息解析，避免重复处理
"""

import logging
import re
from typing import Optional, List

logger = logging.getLogger(__name__)


class MessageParser:
    """统一消息解析器"""
    
    @staticmethod
    def parse_qq_message(event: dict) -> dict:
        """解析QQ消息事件
        
        Args:
            event: OneBot消息事件
            
        Returns:
            解析后的消息字典，包含:
                - message_type: 消息类型
                - sender_id: 发送者QQ
                - group_id: 群ID（群聊）
                - content: 消息内容
                - original_content: 原始内容
                - media_type: 媒体类型
                - is_mentioned: 是否@机器人
                - mentioned_users: @的用户列表
        """
        # 提取基础信息
        post_type = event.get("post_type", "message")
        message_type = event.get("message_type", "")
        sender_id = event.get("user_id", 0)
        group_id = event.get("group_id")
        
        # 提取消息内容
        message_data = event.get("message", [])
        content_parts = []
        media_types = set()
        
        # 处理消息片段
        if isinstance(message_data, list):
            for segment in message_data:
                if segment.get("type") == "text":
                    text = segment.get("data", {}).get("text", "")
                    content_parts.append(text)
                elif segment.get("type") == "image":
                    media_types.add("image")
                elif segment.get("type") == "record":
                    media_types.add("audio")
                elif segment.get("type") == "video":
                    media_types.add("video")
        
        content = "".join(content_parts).strip()
        
        # 确定媒体类型
        if len(media_types) == 0:
            media_type = "text"
        elif len(media_types) == 1:
            media_type = list(media_types)[0]
        else:
            media_type = "mixed"
        
        # 检查@提及
        is_mentioned = False
        mentioned_users = []
        
        # 从 message 段落提取@信息
        if isinstance(message_data, list):
            for segment in message_data:
                if segment.get("type") == "at":
                    qq = segment.get("data", {}).get("qq")
                    if qq:
                        mentioned_users.append(qq)
                        if qq == event.get("self_id", 0):
                            is_mentioned = True
        
        # 构建解析结果
        parsed = {
            "message_type": message_type,  # "private" | "group"
            "sender_id": sender_id,
            "group_id": group_id,
            "content": content,
            "original_content": content,
            "media_type": media_type,
            "is_mentioned": is_mentioned,
            "mentioned_users": mentioned_users,
            "raw_message": message_data,
        }
        
        logger.debug(
            f"[MessageParser] 解析消息: "
            f"type={message_type}, sender={sender_id}, "
            f"group={group_id}, mentioned={is_mentioned}"
        )
        
        return parsed
    
    @staticmethod
    def is_superadmin(parsed: dict, superadmin_qq: int = 0) -> bool:
        """判断是否为超级管理员"""
        return parsed["sender_id"] == superadmin_qq
    
    @staticmethod
    def get_priority_level(parsed: dict, superadmin_qq: int = 0) -> int:
        """获取消息优先级
        
        Returns:
            0: 超级管理员私聊（最高）
            1: 普通私聊
            2: 群聊被@
            3: 群聊普通（最低）
        """
        if parsed["message_type"] == "private":
            if MessageParser.is_superadmin(parsed, superadmin_qq):
                return 0
            return 1
        
        # 群聊
        if parsed["is_mentioned"]:
            return 2
        return 3


class MessageDeduplicator:
    """消息去重器"""
    
    def __init__(self, ttl: int = 60):
        """
        Args:
            ttl: 去重时间窗口（秒）
        """
        self._recent_messages: dict[str, float] = {}
        self._ttl = ttl
    
    def is_duplicate(self, sender_id: int, content: str) -> bool:
        """检查是否为重复消息
        
        Args:
            sender_id: 发送者ID
            content: 消息内容
            
        Returns:
            True if duplicate, False otherwise
        """
        import time
        
        key = f"{sender_id}:{content[:100]}"  # 只使用前100字符
        current_time = time.time()
        
        if key in self._recent_messages:
            if current_time - self._recent_messages[key] < self._ttl:
                logger.debug(f"[MessageDeduplicator] 检测到重复消息: {key[:50]}...")
                return True
        
        self._recent_messages[key] = current_time
        
        # 清理过期记录
        self._cleanup(current_time)
        
        return False
    
    def _cleanup(self, current_time: float):
        """清理过期记录"""
        expired_keys = [
            k for k, v in self._recent_messages.items()
            if current_time - v > self._ttl * 2  # 清理2倍TTL的记录
        ]
        for key in expired_keys:
            del self._recent_messages[key]
        
        if expired_keys:
            logger.debug(f"[MessageDeduplicator] 清理了 {len(expired_keys)} 条过期记录")
