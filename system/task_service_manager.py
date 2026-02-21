#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务服务管理器 - 集成情境感知的主动交流系统
"""

import asyncio
import threading
from typing import Dict, Any, Optional
from datetime import datetime

from system.task_controller import get_task_controller
from system.active_communication import get_active_communication
from system.config import logger, config


class TaskServiceManager:
    """任务服务管理器 - 集成情境感知的主动交流系统"""

    def __init__(self):
        self._controller = get_task_controller()
        self._communication = get_active_communication()
        self._initialized = False
        self._ui_message_callback = None

        # 新增：情境感知组件
        self._context_analyzer = None
        self._conversation_generator = None
        self._frequency_regulator = None

        # 情境感知配置
        self._context_aware_enabled = False
        self._last_context_analysis_time = None
    
    async def initialize(self):
        """初始化任务服务"""
        if self._initialized:
            return

        logger.info("[任务服务] 正在初始化...")

        try:
            # 初始化任务控制器
            await self._controller.initialize()

            # 启动主动交流系统
            await self._communication.start()

            # 订阅主动消息
            self._communication.subscribe(self._on_active_message)

            # 初始化情境感知组件
            await self._init_context_aware_components()

            self._initialized = True
            logger.info("[任务服务] 初始化完成")

        except Exception as e:
            logger.error(f"[任务服务] 初始化失败: {e}")
            raise

    async def _init_context_aware_components(self):
        """初始化情境感知组件"""
        try:
            # 检查配置
            if not hasattr(config, 'active_communication') or not config.active_communication.context_aware:
                logger.info("[任务服务] 情境感知功能未启用")
                return

            # 初始化情境分析器
            from system.context_analyzer import get_context_analyzer
            self._context_analyzer = await get_context_analyzer()
            logger.info("[任务服务] 情境分析器已加载")

            # 初始化对话生成器
            from system.conversation_generator import get_conversation_generator
            self._conversation_generator = await get_conversation_generator()
            logger.info("[任务服务] 对话生成器已加载")

            # 初始化频率调节器
            from system.frequency_regulator import get_frequency_regulator
            self._frequency_regulator = get_frequency_regulator()
            logger.info("[任务服务] 频率调节器已加载")

            self._context_aware_enabled = True
            logger.info("[任务服务] 情境感知功能已启用")

        except ImportError as e:
            logger.warning(f"[任务服务] 情境感知组件导入失败: {e}")
        except Exception as e:
            logger.error(f"[任务服务] 初始化情境感知组件失败: {e}")
    
    async def shutdown(self):
        """关闭任务服务"""
        if not self._initialized:
            return

        logger.info("[任务服务] 正在关闭...")

        try:
            await self._controller.shutdown()
            await self._communication.stop()

            # 清理情境感知组件
            self._context_analyzer = None
            self._conversation_generator = None
            self._frequency_regulator = None
            self._context_aware_enabled = False

            self._initialized = False
            logger.info("[任务服务] 已关闭")

        except Exception as e:
            logger.error(f"[任务服务] 关闭失败: {e}")
    
    def set_ui_message_callback(self, callback):
        """
        设置UI消息回调
        
        参数:
            callback: 回调函数，签名: callback(message: str, message_type: str)
        """
        self._ui_message_callback = callback
        logger.info("[任务服务] UI消息回调已设置")
    
    async def _on_active_message(self, message):
        """处理主动消息"""
        logger.info(f"[任务服务] 收到主动消息: {message.message_type.value} - {message.content}")

        # 获取原始输入（用于提取QQ号）
        original_input = message.context.get("original_input", "") if message.context else ""
        logger.info(f"[任务服务] 原始输入: {original_input}")

        # 检查消息是否已经通过情境感知处理
        is_context_aware = message.context.get("context_aware", False) if message.context else False

        if is_context_aware:
            # 消息已经通过情境感知处理，直接使用
            final_message = message.content
            logger.info(f"[任务服务] 使用情境感知消息: {final_message[:50]}...")
        else:
            # 旧逻辑：如果消息不是通过情境感知生成的，才进行LLM处理
            # 提取真正的任务内容（去除QQ号前缀等）
            import re
            match = re.search(r'\[发送者QQ:\d+\]\s*(.+)', original_input)
            if match:
                task_content = match.group(1)
            else:
                task_content = message.content

            final_message = message.content  # 默认使用原始消息

            # 如果是提醒类型，通过LLM生成个性化消息（仅用于降级场景）
            if message.message_type.value == "reminder":
                try:
                    from apiserver.llm_service import get_llm_service
                    llm_service = get_llm_service()

                    # 构建提示词 - 使用提取出的任务内容，而不是消息内容
                    prompt = f"""用户收到了一个提醒: "{task_content}"

请以弥娅的语气生成一个温馨、个性化的提醒消息。要求:
1. 使用弥娅的人设和说话方式
2. 体现出对用户的关心
3. 加入一些情感和温度
4. 保持简洁自然

只输出提醒消息,不要多余的解释。"""

                    # 调用LLM生成个性化消息
                    personalized_message = await llm_service.get_response(prompt, temperature=0.8)

                    logger.info(f"[任务服务] LLM生成的个性化提醒: {personalized_message}")

                    # 使用个性化消息
                    final_message = personalized_message
                except Exception as e:
                    logger.warning(f"[任务服务] 生成个性化提醒失败,使用原始消息: {e}")
                    # 失败时使用原始消息
                    final_message = task_content

        # 调用UI回调（传递完整消息对象，包含语音生成信息）
        if self._ui_message_callback:
            try:
                # 支持两种调用方式：旧方式（一个参数）和新方式（三个参数）
                # 新方式应该能处理消息对象，从而实现语音/文本模式的发送
                if asyncio.iscoroutinefunction(self._ui_message_callback):
                    # 尝试新方式：传递完整消息对象
                    try:
                        await self._ui_message_callback(message)
                    except TypeError:
                        # 回退到旧方式：传递三个参数
                        await self._ui_message_callback(final_message, message.message_type.value, original_input)
                else:
                    # 尝试新方式：传递完整消息对象
                    try:
                        self._ui_message_callback(message)
                    except TypeError:
                        # 回退到旧方式：传递三个参数
                        self._ui_message_callback(final_message, message.message_type.value, original_input)
            except Exception as e:
                logger.error(f"[任务服务] UI回调失败: {e}")
    
    async def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户输入

        返回:
            None: 不是任务相关
            Dict: 任务相关，包含响应信息
        """
        if not self._initialized:
            return None

        # 检查是否是提醒系统触发的消息（避免无限循环）
        # 只有当消息同时满足以下条件时才跳过：
        # 1. 包含 [发送者QQ:xxx] 前缀（这是提醒系统的原始任务内容）
        # 2. 不包含"提醒"相关的动作词（说明是原始任务内容，不是新的提醒请求）
        # 3. 长度较短（少于30个字符）
        import re
        if re.match(r'\[发送者QQ:\d+\]', user_input):
            # 这是来自QQ的消息，检查是否是新的提醒请求
            # 如果包含"提醒"、"记住"、"别忘记"等动作词，说明是新的提醒请求
            action_keywords = ["后提醒", "提醒我", "记得要", "别忘记", "不要忘了", "一定记得"]
            is_reminder_request = any(keyword in user_input for keyword in action_keywords)

            # 如果是提醒请求，继续处理；否则跳过
            if not is_reminder_request:
                logger.info(f"[任务服务] 跳过非提醒消息: {user_input[:50]}...")
                return None

        # 检查是否是 LLM 生成的提醒回复（包含"记得"等关键词）
        # 但排除包含"提醒我"、"记得要"等新请求的消息
        skip_keywords = ["记得了", "已提醒", "正在提醒", "已经提醒", "提醒时间"]
        is_new_request = any(keyword in user_input for keyword in ["提醒我", "记得要", "别忘记", "不要忘了"])

        if any(keyword in user_input for keyword in skip_keywords) and len(user_input) < 100 and not is_new_request:
            # 可能是 LLM 生成的提醒回复，跳过处理
            logger.info(f"[任务服务] 跳过可能为LLM生成的提醒: {user_input}")
            return None

        return await self._controller.process_user_input(user_input)
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        status = {
            "initialized": self._initialized,
            "controller": self._controller.get_status(),
            "communication": self._communication.get_status(),
            "context_aware": {
                "enabled": self._context_aware_enabled,
                "analyzer_loaded": self._context_analyzer is not None,
                "generator_loaded": self._conversation_generator is not None,
                "regulator_loaded": self._frequency_regulator is not None
            }
        }

        # 如果频率调节器可用，添加统计信息
        if self._frequency_regulator:
            status["frequency_regulator"] = self._frequency_regulator.get_stats()

        return status

    async def send_context_aware_message(self, message_type: str = "check_in", task_context: Optional[Dict[str, Any]] = None):
        """
        发送情境感知的主动消息

        参数:
            message_type: 消息类型
            task_context: 任务上下文（用于提醒等场景）

        重要：定时任务（reminder/routine/schedule）不受频率调节器限制，
        因为它们本身就是主观能动性的体现，由用户主动设置。
        """
        if not self._context_aware_enabled:
            logger.warning("[任务服务] 情境感知功能未启用，使用默认消息")
            await self._communication.send_check_in()
            return

        # 只有非任务类型的主动交流（如主动问候）才受频率调节器限制
        is_task_message = message_type in ["reminder", "routine", "schedule"]

        if not is_task_message and self._frequency_regulator:
            if self._frequency_regulator.should_pause_during_busy():
                logger.info("[任务服务] 用户忙碌，跳过主动交流")
                return

            if not self._frequency_regulator.should_trigger_now():
                logger.debug("[任务服务] 未到触发时间，跳过")
                return

            self._frequency_regulator.record_trigger()
            logger.info(f"[任务服务] 频率调节器已触发（主动交流类型: {message_type}）")
        elif is_task_message:
            logger.info(f"[任务服务] 定时任务不受频率调节器限制（任务类型: {message_type}）")

        try:
            # 分析情境
            context = await self._context_analyzer.analyze_context()

            # 如果有任务上下文，将其添加到情境中
            if task_context:
                context["task"] = task_context
                logger.info(f"[任务服务] 添加任务上下文: {task_context.get('task_title')}")

            # 推荐生成策略
            strategy = self._conversation_generator.recommend_strategy(context)
            logger.info(f"[任务服务] 使用策略: {strategy}")

            # 生成对话 - 使用TopicGenerator或ConversationGenerator
            if message_type == "check_in" or message_type == "suggestion":
                # 主动交流时使用TopicGenerator
                from system.topic_generator import get_topic_generator
                topic_generator = get_topic_generator()

                # 根据策略选择话题类型
                topic_type_map = {
                    "time_greeting": "greeting",
                    "weather_care": "care",
                    "emotional_support": "care",
                    "topic_suggestion": "suggestion",
                    "memory_recall": "memory",
                    "curiosity": "curiosity"
                }
                topic_type = topic_type_map.get(strategy, "general")

                logger.info(f"[任务服务] 使用TopicGenerator生成话题: {topic_type}")
                generated_topic = await topic_generator.generate_topic(context, topic_type)

                if generated_topic:
                    message = generated_topic.content
                    logger.info(f"[任务服务] TopicGenerator生成话题: {message}")
                else:
                    # TopicGenerator失败，降级到ConversationGenerator
                    logger.warning("[任务服务] TopicGenerator生成失败，降级到ConversationGenerator")
                    message = await self._conversation_generator.generate_conversation(
                        context=context,
                        strategy=strategy
                    )
            else:
                # 其他类型使用ConversationGenerator
                logger.info(f"[任务服务] 使用ConversationGenerator生成对话")
                message = await self._conversation_generator.generate_conversation(
                    context=context,
                    strategy=strategy
                )

            # 发送消息
            await self._communication.send_message(
                message=message,
                message_type=message_type,
                priority=5,
                context={"context_aware": True, "strategy": strategy}
            )

            logger.info(f"[任务服务] 情境感知消息已发送: {message}")

        except Exception as e:
            logger.error(f"[任务服务] 发送情境感知消息失败: {e}")
            import traceback
            traceback.print_exc()
            # 降级到默认消息
            await self._communication.send_check_in()

    def record_user_response(self, user_response: str, message_type: str):
        """
        记录用户响应用于频率调节

        参数:
            user_response: 用户回复内容
            message_type: 消息类型
        """
        if self._frequency_regulator:
            score = self._frequency_regulator.record_interaction(
                user_response=user_response,
                message_type=message_type
            )
            logger.info(f"[任务服务] 记录用户响应: 评分={score:.2f}")

    def get_frequency_stats(self) -> Dict[str, Any]:
        """获取频率调节统计"""
        if self._frequency_regulator:
            return self._frequency_regulator.get_stats()
        return {"enabled": False}

    def adjust_frequency_manually(self, interval: int):
        """
        手动调整主动交流频率

        参数:
            interval: 新的间隔（分钟）
        """
        if self._frequency_regulator:
            self._frequency_regulator.adjust_interval_manually(interval)
            logger.info(f"[任务服务] 手动调整频率: {interval}分钟")


# 全局实例
_task_service_manager: TaskServiceManager = None


def get_task_service_manager() -> TaskServiceManager:
    """获取任务服务管理器实例"""
    global _task_service_manager
    if _task_service_manager is None:
        _task_service_manager = TaskServiceManager()
    return _task_service_manager


# ============================================================================
# 集成到 main.py 的示例代码
# ============================================================================

"""
# 在 main.py 中添加以下代码：

# 1. 导入
from task_service_manager import get_task_service_manager

# 2. 在 ServiceManager.__init__ 中添加
def __init__(self):
    # ... 现有代码 ...
    self.task_service = get_task_service_manager()

# 3. 在 _init_background_services 中初始化
async def _init_background_services(self):
    logger.info("正在启动后台服务...")
    try:
        # ... 现有代码 ...
        
        # 初始化任务服务
        await self.task_service.initialize()
        
        # ... 现有代码 ...
    except Exception as e:
        logger.error(f"后台服务异常: {e}")

# 4. 在 ChatWindow 中集成

class ChatWindow:
    def __init__(self, parent=None):
        # ... 现有代码 ...
        
        # 获取任务服务管理器
        self.task_service = get_task_service_manager()
        
        # 设置UI消息回调
        self.task_service.set_ui_message_callback(self.on_active_message)
    
    def on_active_message(self, message: str, message_type: str):
        \"\"\"处理主动消息\"\"\"
        # 在UI中显示主动消息
        self.add_message(
            role="assistant",
            content=message,
            message_type=message_type
        )
    
    def process_user_message(self, message: str):
        \"\"\"处理用户消息\"\"\"
        
        # 先检查是否是任务相关
        result = asyncio.run_coroutine_threadsafe(
            self.task_service.process_user_input(message),
            self.task_service._controller._scheduler._temporal._temporal_loop or asyncio.get_event_loop()
        ).result()
        
        if result and result.get("success"):
            # 是任务相关，直接显示响应
            self.add_message(
                role="assistant",
                content=result["response"]
            )
            return
        
        # 不是任务相关，正常处理对话
        # ... 现有代码 ...

# 5. 启动示例
if __name__ == "__main__":
    # 创建服务管理器
    service_manager = ServiceManager()
    
    # 启动后台服务
    service_manager.start_background_services()
    
    # 创建并显示UI
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    
    sys.exit(app.exec_())
"""


# ============================================================================
# 独立测试代码
# ============================================================================

async def test_task_service():
    """测试任务服务"""
    from datetime import timedelta
    
    # 创建管理器
    manager = TaskServiceManager()
    
    # 设置UI回调
    def on_message(message: str, message_type: str):
        print(f"\n[UI显示] {message_type.upper()}: {message}\n")
    
    manager.set_ui_message_callback(on_message)
    
    # 初始化
    await manager.initialize()
    
    print("任务服务已启动，可以测试以下功能：")
    print("1. 添加提醒: '每30分钟提醒我起来走走'")
    print("2. 添加提醒: '一小时后提醒我喝水'")
    print("3. 查看提醒: '查看我的提醒'")
    print("4. 删除提醒: '删除1号提醒'")
    print("5. 暂停提醒: '暂停所有提醒'")
    print("6. 退出: '退出'")
    
    # 模拟对话
    while True:
        user_input = input("\n用户: ").strip()
        
        if user_input in ["退出", "exit", "quit"]:
            break
        
        if not user_input:
            continue
        
        # 处理输入
        result = await manager.process_user_input(user_input)
        
        if result:
            print(f"\n弥娅: {result['response']}")
        else:
            print("\n弥娅: (这不是任务相关的输入，需要正常的对话处理)")
    
    # 关闭
    await manager.shutdown()
    print("任务服务已关闭")


if __name__ == "__main__":
    asyncio.run(test_task_service())
