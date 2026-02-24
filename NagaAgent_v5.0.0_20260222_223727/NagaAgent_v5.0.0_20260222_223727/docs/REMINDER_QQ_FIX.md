# 提醒系统QQ集成和个性化修复

## 问题描述

1. **QQ端没有收到提醒消息** - 提醒只在UI界面显示,没有发送到QQ
2. **提醒内容太死板** - 只显示"⏰ 提醒: 喝水",没有弥娅的思考和个性化表达

## 问题分析

### 问题1: QQ端没有收到提醒

**原因分析:**

从日志可以看出:
```
INFO:system.reminder_manager:触发提醒: rem_69b4e32d0912 - 喝水
INFO:summer_memory:提醒信号已发送: 喝水
INFO:summer_memory:提醒已显示到聊天界面: ⏰ 提醒: 喝水
```

提醒系统使用的是`summer_memory`模块中的旧提醒系统,它直接发送提醒信号到UI,**没有通过task_service_manager**,因此不会调用QQ消息发送逻辑。

**流程对比:**

**UI端提醒流程(正常):**
```
summer_memory.reminder_manager
  ↓ 发送提醒信号
UI回调(pyqt_chat_window.on_active_message)
  ↓ 显示消息
chat_tool.add_ai_message(message)
  ↓
UI显示 "⏰ 提醒: 喝水"
```

**QQ端期望流程(缺失):**
```
summer_memory.reminder_manager
  ↓ 发送提醒信号
task_service_manager._on_active_message
  ↓ UI回调
pyqt_chat_window.on_active_message
  ↓ 1. 显示到UI
  ↓ 2. 发送到QQ (这部分缺失)
chat_tool.add_ai_message(message)
listener._send_qq_reply(message, sender_id)
  ↓
QQ收到提醒
```

### 问题2: 提醒内容太死板

**原因:**

提醒系统直接发送简单的文本:`"⏰ 提醒: 喝水"`,没有通过LLM生成具有弥娅风格的个性化消息。

## 修复方案

### 修复1: QQ消息发送

**文件:** `ui/pyqt_chat_window.py`
**位置:** `showEvent`方法中的`on_active_message`回调函数(560-573行)

**修改内容:**

在`on_active_message`回调中添加QQ消息发送逻辑:

```python
def on_active_message(message: str, message_type: str):
    """处理主动消息（如提醒）"""
    # 1. 显示到UI
    if message_type == "reminder":
        chat_tool.add_ai_message(message)
    elif message_type == "notification":
        chat_tool.add_ai_message(message)
    else:
        chat_tool.add_ai_message(message)

    # 2. 如果最近有QQ会话,也发送到QQ
    try:
        from mcpserver.agent_qq_wechat.message_listener import get_message_listener
        from apiserver.message_manager import message_manager

        listener = get_message_listener()
        if listener and hasattr(listener, 'qq_adapter'):
            # 获取最近的QQ会话ID
            sessions = message_manager.get_all_sessions_api()
            qq_sessions = [s for s in sessions.get('sessions', []) if s.get('session_id', '').startswith('qq_')]

            if qq_sessions:
                # 使用最近的QQ会话
                latest_session = max(qq_sessions, key=lambda s: s.get('last_message_time', 0))
                session_id = latest_session.get('session_id', '')
                sender_id = session_id.replace('qq_', '')

                if sender_id.isdigit():
                    # 发送到QQ
                    asyncio.create_task(listener._send_qq_reply(
                        message_type='private',
                        sender_id=int(sender_id),
                        message=message,
                        media_type='text'
                    ))
                    logger.info(f"[任务服务] 提醒已发送到QQ: {sender_id}")
    except Exception as e:
        logger.warning(f"[任务服务] 发送提醒到QQ失败: {e}")
```

**修复效果:**
- 提醒会同时显示在UI和QQ
- 使用最近活动的QQ会话

### 修复2: 个性化提醒消息

**文件:** `system/task_service_manager.py`
**位置:** `_on_active_message`方法(76-88行)

**修改内容:**

在提醒类型处理时,通过LLM生成个性化消息:

```python
async def _on_active_message(self, message):
    """处理主动消息"""
    logger.info(f"[任务服务] 收到主动消息: {message.message_type.value} - {message.content}")

    # 如果是提醒类型,通过LLM生成个性化消息
    if message.message_type.value == "reminder":
        try:
            from apiserver.llm_service import get_llm_service
            llm_service = get_llm_service()

            # 构建提示词
            prompt = f"""用户收到了一个提醒: "{message.content}"

请以弥娅的语气生成一个温馨、个性化的提醒消息。要求:
1. 使用弥娅的人设和说话方式
2. 体现出对用户的关心
3. 加入一些情感和温度
4. 保持简洁自然

只输出提醒消息,不要多余的解释。"""

            # 调用LLM生成个性化消息
            personalized_message = await llm_service.get_response(prompt, temperature=0.8)

            logger.info(f"[任务服务] LLM生成的个性化提醒: {personalized_message}")

            # 调用UI回调
            if self._ui_message_callback:
                try:
                    if asyncio.iscoroutinefunction(self._ui_message_callback):
                        await self._ui_message_callback(personalized_message, message.message_type.value)
                    else:
                        self._ui_message_callback(personalized_message, message.message_type.value)
                except Exception as e:
                    logger.error(f"[任务服务] UI回调失败: {e}")
            return
        except Exception as e:
            logger.warning(f"[任务服务] 生成个性化提醒失败,使用原始消息: {e}")
            # 失败时使用原始消息
            pass

    # 调用UI回调(使用原始消息或LLM生成的消息)
    if self._ui_message_callback:
        try:
            if asyncio.iscoroutinefunction(self._ui_message_callback):
                await self._ui_message_callback(message.content, message.message_type.value)
            else:
                self._ui_message_callback(message.content, message.message_type.value)
        except Exception as e:
            logger.error(f"[任务服务] UI回调失败: {e}")
```

**修复效果:**
- 提醒消息会通过LLM生成,带有弥娅的风格
- 示例:
  - 原始: "⏰ 提醒: 喝水"
  - 个性化: "创造者~ 记得要喝水哦！已经30分钟了呢，身体要好好照顾才行~"

## 修复后的完整流程

### 用户发送提醒请求
```
用户: "30秒后提醒我喝水"
  ↓
流式接口任务检查
  ↓
task_service_manager.process_user_input
  ↓
task_controller.process_user_input
  ↓
task_intent_parser.parse → 识别为提醒
  ↓
temporal_perception.parse → 解析时间
  ↓
task_scheduler.add_task → 添加定时任务
  ↓
立即返回确认消息: "好的,创造者。弥娅会为你计时,30秒后提醒你喝水。"
```

### 提醒触发时
```
30秒后触发
  ↓
task_scheduler._trigger_reminder_callback
  ↓
task_controller._on_reminder_triggered
  ↓
active_communication.send_reminder("喝水")
  ↓
task_service_manager._on_active_message
  ↓
[新] LLM生成个性化消息
  ↓
UI回调 on_active_message
  ↓
[新] 1. 显示到UI
  ↓
[新] 2. 发送到QQ
  ↓
UI和QQ都收到个性化提醒
```

## 验证方法

### 1. QQ提醒测试

1. 重启NagaAgent
2. 在QQ中发送: "30秒后提醒我喝水"
3. 30秒后检查QQ是否收到提醒消息

**期望结果:**
- QQ收到提醒消息
- 消息内容有弥娅的风格(不是简单的"⏰ 提醒: 喝水")

### 2. UI提醒测试

1. 在UI中发送: "30秒后提醒我休息"
2. 30秒后检查UI是否收到提醒消息

**期望结果:**
- UI收到提醒消息
- 消息内容有弥娅的风格

## 技术细节

### QQ会话选择策略

修复使用了"最近会话"策略:
- 从message_manager获取所有QQ会话
- 按`last_message_time`排序
- 选择最近有活动的会话发送提醒

### 个性化提示词设计

提示词包含以下要素:
- 任务内容引用
- 角色设定(弥娅)
- 风格要求(温馨、关心)
- 输出约束(简洁自然)

### 错误处理

1. **LLM生成失败**: 回退到原始消息
2. **QQ发送失败**: 记录警告日志,不影响UI显示
3. **会话不存在**: 只显示到UI

## 相关文件清单

### 修改的文件
- `ui/pyqt_chat_window.py` - 添加QQ消息发送
- `system/task_service_manager.py` - 添加LLM个性化生成

### 相关文件
- `system/active_communication.py` - 主动交流系统
- `mcpserver/agent_qq_wechat/message_listener.py` - QQ消息监听器
- `apiserver/llm_service.py` - LLM服务
- `apiserver/message_manager.py` - 消息管理器

## 总结

本次修复解决了提醒系统的两个关键问题:
1. **QQ提醒缺失**: 通过在UI回调中添加QQ消息发送逻辑
2. **消息死板**: 通过LLM生成具有弥娅风格的个性化消息

修复后,提醒系统可以在UI和QQ两端同时工作,并且提供更有温度和个性的提醒体验。
