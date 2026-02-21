#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自主记忆系统集成脚本
将AutonomousMemory集成到GRAGMemoryManager
"""

import logging

logger = logging.getLogger(__name__)


def integrate_autonomous_memory(memory_manager, llm_client=None):
    """
    集成自主记忆到GRAGMemoryManager

    Args:
        memory_manager: GRAGMemoryManager实例
        llm_client: LLM客户端(可选)
    """
    try:
        from .autonomous_memory import AutonomousMemory, get_autonomous_memory, set_autonomous_memory

        # 检查是否已经集成
        if hasattr(memory_manager, 'autonomous_memory'):
            logger.info("[集成] 自主记忆已存在,跳过集成")
            return False

        # 创建自主记忆系统
        autonomous_memory = AutonomousMemory(llm_client)
        set_autonomous_memory(autonomous_memory)

        # 添加到memory_manager
        memory_manager.autonomous_memory = autonomous_memory

        logger.info("[集成] 自主记忆集成成功")
        return True

    except Exception as e:
        logger.error(f"[集成] 自主记忆集成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_integration_instructions() -> str:
    """获取集成说明"""
    return """
自主记忆系统集成说明
===================

1. 集成到memory_manager:
   在memory_manager初始化时调用:
   ```python
   from summer_memory.autonomous_integration import integrate_autonomous_memory

   async def __init__(self):
       ...
       # 集成自主记忆
       integrate_autonomous_memory(self, llm_client=self.llm_client)
   ```

2. 修改add_conversation_memory方法:
   在记录对话前使用自主评估:
   ```python
   async def add_conversation_memory(self, user_input: str, ai_response: str) -> bool:
       ...
       # 使用自主记忆评估
       if hasattr(self, 'autonomous_memory'):
           should_store = await self.autonomous_memory.autonomous_store(
               user_input=user_input,
               ai_response=ai_response,
               context={"timestamp": datetime.now().isoformat()}
           )
           if not should_store:
               logger.info("[自主记忆] 跳过低价值对话存储")
               return True

       # 继续原有存储逻辑...
   ```

3. 配置项(config.json):
   ```json
   "grag": {
     "enabled": true,
     "auto_extract": true,
     "enable_autonomous": true,  // 启用自主评估
     "autonomous_threshold": 0.4,  // 存储阈值
     ...
   }
   ```

4. 功能:
   - 自动评估对话价值
   - 智能选择存储
   - 支持规则+LLM双模式
   - 记录评估日志
   - 提高记忆质量
    """


if __name__ == "__main__":
    print(get_integration_instructions())
