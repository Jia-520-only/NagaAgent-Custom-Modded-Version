#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主动交流系统 - Active Communication
处理AI的主动消息发送
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import json

from system.config import logger


class MessageType(Enum):
    """消息类型"""
    SUGGESTION = "suggestion"      # 建议
    REMINDER = "reminder"          # 提醒
    CHECK_IN = "check_in"          # 问候
    NOTIFICATION = "notification"  # 通知
    QUESTION = "question"          # 提问


@dataclass
class ActiveMessage:
    """主动消息"""
    message_id: str
    message_type: MessageType
    content: str
    priority: int = 5  # 1-10, 10最高
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    delivered: bool = False
    delivered_at: Optional[datetime] = None


class ActiveCommunication:
    """主动交流系统"""
    
    def __init__(self):
        self._message_queue: deque[ActiveMessage] = deque()
        self._subscribers: List[Callable] = []
        self._history: List[ActiveMessage] = []
        self._running = False
        self._dispatch_task = None
        
        # 最大历史记录数
        self._max_history = 100
    
    async def start(self):
        """启动主动交流系统"""
        if self._running:
            return
        
        self._running = True
        self._dispatch_task = asyncio.create_task(self._dispatch_loop())
        
        logger.info("[主动交流] 已启动")
    
    async def stop(self):
        """停止主动交流系统"""
        self._running = False
        
        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass
        
        logger.info("[主动交流] 已停止")
    
    async def _dispatch_loop(self):
        """消息分发循环"""
        while self._running:
            try:
                if self._message_queue:
                    # 取出优先级最高的消息
                    messages = list(self._message_queue)
                    messages.sort(key=lambda m: m.priority, reverse=True)
                    message = messages[0]
                    
                    # 从队列中移除
                    try:
                        self._message_queue.remove(message)
                    except ValueError:
                        pass
                    
                    # 分发消息
                    await self._dispatch_message(message)
                
                # 休眠
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"[主动交流] 分发错误: {e}")
                await asyncio.sleep(5)
    
    async def _dispatch_message(self, message: ActiveMessage):
        """分发消息"""
        try:
            # 调用所有订阅者
            for subscriber in self._subscribers:
                try:
                    if asyncio.iscoroutinefunction(subscriber):
                        await subscriber(message)
                    else:
                        subscriber(message)
                except Exception as e:
                    logger.error(f"[主动交流] 订阅者回调失败: {e}")
            
            # 标记为已投递
            message.delivered = True
            message.delivered_at = datetime.now()
            
            # 加入历史
            self._history.append(message)
            
            # 限制历史数量
            if len(self._history) > self._max_history:
                self._history.pop(0)
            
            logger.info(f"[主动交流] 消息已投递: {message.message_type.value} - {message.content[:30]}...")
            
        except Exception as e:
            logger.error(f"[主动交流] 分发消息失败: {e}")
    
    def subscribe(self, callback: Callable):
        """
        订阅主动消息
        
        回调签名: async def callback(message: ActiveMessage)
        """
        self._subscribers.append(callback)
        logger.info(f"[主动交流] 新订阅者: {callback.__name__}")
    
    def unsubscribe(self, callback: Callable):
        """取消订阅"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            logger.info(f"[主动交流] 取消订阅: {callback.__name__}")
    
    async def send_message(self, 
                           message: str, 
                           message_type: str = "notification",
                           priority: int = 5,
                           context: Optional[Dict[str, Any]] = None):
        """
        发送主动消息
        
        参数:
            message: 消息内容
            message_type: 消息类型 (suggestion, reminder, check_in, notification, question)
            priority: 优先级 (1-10)
            context: 附加上下文
        """
        try:
            msg_type = MessageType(message_type)
        except ValueError:
            msg_type = MessageType.NOTIFICATION
        
        message_obj = ActiveMessage(
            message_id=f"msg_{int(datetime.now().timestamp() * 1000)}",
            message_type=msg_type,
            content=message,
            priority=priority,
            context=context or {}
        )
        
        self._message_queue.append(message_obj)
        
        logger.debug(f"[主动交流] 消息入队: {msg_type.value} - {message[:30]}...")
    
    async def send_topic_suggestion(self, topic: str, context: Optional[Dict[str, Any]] = None):
        """发送话题建议"""
        await self.send_message(
            message=topic,
            message_type="suggestion",
            priority=6,
            context=context
        )
    
    async def send_reminder(self, reminder: str, context: Optional[Dict[str, Any]] = None):
        """发送提醒"""
        await self.send_message(
            message=reminder,
            message_type="reminder",
            priority=9,  # 提醒优先级高
            context=context
        )
    
    async def send_check_in(self, message: str = "有什么需要帮助的吗？", context: Optional[Dict[str, Any]] = None):
        """发送问候"""
        await self.send_message(
            message=message,
            message_type="check_in",
            priority=3,
            context=context or {}
        )

    async def send_context_aware_message(
        self,
        context: Optional[Dict[str, Any]] = None,
        message_type: str = "check_in"
    ):
        """
        发送情境感知的主动消息

        参数:
            context: 情境信息（可选）
            message_type: 消息类型
        """
        # 检查是否启用情境感知
        if not hasattr(config, 'active_communication') or not config.active_communication.get('context_aware', False):
            logger.debug("[主动交流] 情境感知未启用，使用默认消息")
            await self.send_check_in()
            return

        # 如果提供了情境信息，直接使用
        if context:
            logger.debug(f"[主动交流] 使用提供的情境信息: {context.get('strategy', 'unknown')}")
            await self.send_message(
                message=context.get('message', ''),
                message_type=message_type,
                priority=5,
                context=context
            )
        else:
            # 否则回退到默认消息
            logger.debug("[主动交流] 无情境信息，使用默认消息")
            await self.send_check_in()
    
    async def send_notification(self, notification: str, context: Optional[Dict[str, Any]] = None):
        """发送通知"""
        await self.send_message(
            message=notification,
            message_type="notification",
            priority=7,
            context=context
        )
    
    async def send_question(self, question: str, context: Optional[Dict[str, Any]] = None):
        """发送提问"""
        await self.send_message(
            message=question,
            message_type="question",
            priority=8,
            context=context
        )
    
    def get_message_queue(self) -> List[ActiveMessage]:
        """获取消息队列"""
        return list(self._message_queue)
    
    def get_history(self, limit: int = 20) -> List[ActiveMessage]:
        """获取历史消息"""
        return self._history[-limit:]
    
    def clear_queue(self):
        """清空消息队列"""
        self._message_queue.clear()
        logger.info("[主动交流] 消息队列已清空")
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "running": self._running,
            "queue_size": len(self._message_queue),
            "subscribers": len(self._subscribers),
            "history_size": len(self._history),
            "delivered_count": sum(1 for m in self._history if m.delivered)
        }


# 全局实例
_active_communication: Optional[ActiveCommunication] = None


def get_active_communication() -> ActiveCommunication:
    """获取主动交流系统实例"""
    global _active_communication
    if _active_communication is None:
        _active_communication = ActiveCommunication()
    return _active_communication


# 全局访问器别名
ActiveCommunication.get_instance = get_active_communication
