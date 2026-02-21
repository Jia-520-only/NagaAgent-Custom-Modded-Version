#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息旁观系统集成脚本
将MessageObserver集成到MessageListener
"""

import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)


def integrate_message_observer(message_listener):
    """
    集成消息旁观器到MessageListener

    Args:
        message_listener: QQWeChatMessageListener实例
    """
    try:
        from .message_observer import MessageObserver, get_message_observer, set_message_observer

        # 检查是否已经集成
        if hasattr(message_listener, 'message_observer'):
            logger.info("[集成] 消息旁观器已存在,跳过集成")
            return False

        # 创建消息旁观器
        observer = MessageObserver(message_listener)
        set_message_observer(observer)

        # 添加到message_listener
        message_listener.message_observer = observer

        # 添加配置项(如果不存在)
        if 'enable_observer' not in message_listener.qq_config:
            message_listener.qq_config['enable_observer'] = True
            logger.info("[集成] 添加enable_observer配置项: True")

        if 'observation_groups' not in message_listener.qq_config:
            message_listener.qq_config['observation_groups'] = []
            logger.info("[集成] 添加observation_groups配置项: []")

        if 'interest_keywords' not in message_listener.qq_config:
            message_listener.qq_config['interest_keywords'] = [
                "喜欢", "讨厌", "爱", "恨", "开心", "难过", "生气",
                "重要", "记得", "记住", "秘密", "悄悄话",
                "建议", "推荐", "分享", "告诉", "提醒"
            ]
            logger.info("[集成] 添加interest_keywords配置项")

        logger.info("[集成] 消息旁观器集成成功")
        return True

    except Exception as e:
        logger.error(f"[集成] 消息旁观器集成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def add_observer_to_message_flow(message_listener):
    """
    在消息处理流程中添加旁观器调用

    需要修改message_listener.py中的handle_qq_message方法

    在处理消息后、生成回复前,添加:
        # 消息旁观记录
        if hasattr(self, 'message_observer'):
            await self.message_observer.observe_message(
                message_type=message_type,
                sender_id=sender_id,
                group_id=group_id,
                message=message,
                raw_data=data
            )
    """
    pass  # 这个函数用于文档说明,实际修改需要手动编辑message_listener.py


def get_integration_instructions() -> str:
    """获取集成说明"""
    return """
消息旁观系统集成说明
===================

1. 自动集成(推荐):
   在message_listener初始化时调用:
   ```
   integrate_message_observer(self)
   ```

2. 手动集成:
   a) 在handle_qq_message方法中添加观察器调用:
      在消息处理开始处添加:
      ```python
      # 消息旁观记录
      if hasattr(self, 'message_observer'):
          recorded = await self.message_observer.observe_message(
              message_type=message_type,
              sender_id=sender_id,
              group_id=group_id,
              message=message,
              raw_data=data
          )
          if recorded:
              logger.info("[消息旁观] 已记录有趣消息")
      ```

3. 配置项(config.json):
   ```json
   "qq": {
     "enable_observer": true,  // 启用消息旁观
     "observation_groups": ["123456", "789012"],  // 观察的群号(空=全部)
     "interest_keywords": ["喜欢", "讨厌", "爱", "恨", ...]  // 兴趣关键词
   }
   ```

4. 功能:
   - 自动旁观群聊/私聊
   - 识别有趣信息
   - 自动记录到记忆系统
   - 避免重复记录
   - 支持配置化
    """


if __name__ == "__main__":
    # 测试集成
    print(get_integration_instructions())
