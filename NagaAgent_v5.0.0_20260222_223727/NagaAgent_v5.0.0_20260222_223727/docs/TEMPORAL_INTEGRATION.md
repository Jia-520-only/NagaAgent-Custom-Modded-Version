# 时间感知与任务调度系统集成文档

## 概述

本文档描述了弥娅的时间感知和任务调度系统，它让弥娅能够：

1. **感知时间** - 理解当前时间、时间段、季节等
2. **解析时间指令** - 从对话中提取"30分钟后"、"每半小时"、"每天9:00"等时间表达
3. **设置定时任务** - 在对话中设置提醒、例行任务、日程安排
4. **自主触发** - 在指定时间主动提醒用户

---

## 系统架构

### 核心模块

```
system/
├── temporal_perception.py      # 时间感知系统
├── task_scheduler.py          # 任务调度器
├── task_intent_parser.py      # 任务意图解析
├── task_controller.py         # 任务控制器
└── active_communication.py    # 主动交流系统
```

### 数据流

```
用户输入 → 意图解析 → 任务控制器 → 任务调度器
                                      ↓
                              时间感知系统
                                      ↓
                         任务触发 → 主动交流系统 → 用户
```

---

## 功能说明

### 1. 时间感知系统 (`temporal_perception.py`)

**功能**：
- 感知当前时间、小时、分钟、星期几、是否周末
- 识别时间上下文：早晨、上午、中午、下午、晚上、夜间、深夜
- 识别季节：春、夏、秋、冬
- 解析时间表达（自然语言）

**时间解析示例**：
- "30分钟后" → `datetime.now() + 30分钟`
- "一小时后" → `datetime.now() + 1小时`
- "每半小时" → 循环，间隔30分钟
- "每天9:00" → 循环，每天9:00
- "9:30" → 今天或明天的9:30

**API**：
```python
from system.temporal_perception import get_temporal_perception

temporal = get_temporal_perception()

# 获取当前时间状态
state = temporal.get_state()
print(f"{state.season} {state.time_of_day} {state.hour:02d}:{state.minute:02d}")

# 解析时间表达
scheduled_time, interval, desc = temporal.parse_time_from_text("30分钟后起来走走")

# 添加时间事件
event = TemporalEvent(...)
temporal.add_event(event)

# 启动监控
await temporal.start_monitoring()
```

---

### 2. 任务调度器 (`task_scheduler.py`)

**功能**：
- 管理定时任务
- 支持一次性任务和循环任务
- 任务优先级管理
- 任务回调机制
- 任务持久化

**任务类型**：
- `reminder` - 提醒
- `routine` - 例行任务
- `schedule` - 日程安排
- `custom` - 自定义任务

**优先级**：
- `HIGH` - 高优先级（重要、紧急）
- `MEDIUM` - 中优先级（默认）
- `LOW` - 低优先级（可能、有空）

**API**：
```python
from system.task_scheduler import get_task_scheduler, TaskPriority

scheduler = get_task_scheduler()

# 启动调度器
await scheduler.start()

# 添加任务
task_id = scheduler.add_task(
    title="起来走走",
    description="每半小时提醒我起来走走",
    task_type="reminder",
    priority=TaskPriority.HIGH,
    scheduled_time=scheduled_time,
    recurring=True,
    recurring_interval=timedelta(minutes=30)
)

# 获取任务列表
tasks = scheduler.get_all_tasks()

# 移除任务
scheduler.remove_task(task_id)

# 注册回调
async def on_reminder(task):
    print(f"提醒: {task.title}")

scheduler.register_callback("reminder", on_reminder)
```

---

### 3. 任务意图解析器 (`task_intent_parser.py`)

**功能**：
- 从对话中识别任务相关意图
- 提取任务信息（标题、描述、时间、优先级）
- 生成自然语言响应

**支持的意图**：
- `add_task` - 添加任务
- `list_tasks` - 列出任务
- `remove_task` - 移除任务
- `toggle_task` - 启用/禁用任务
- `clear_tasks` - 清除任务

**示例解析**：
- "每半小时提醒我起来走走" → 添加循环提醒
- "一小时后提醒我喝水" → 添加一次性提醒
- "查看我的提醒" → 列出任务
- "删除1号提醒" → 移除任务
- "暂停所有提醒" → 禁用任务

**API**：
```python
from system.task_intent_parser import get_task_intent_parser

parser = get_task_intent_parser()

# 解析意图
intent = parser.parse("每半小时提醒我起来走走")

# 生成响应
result = await controller._execute_intent(intent)
response = parser.generate_response(intent, result)
```

---

### 4. 任务控制器 (`task_controller.py`)

**功能**：
- 集成任务调度和意图解析
- 处理用户输入
- 协调各模块工作
- 响应任务触发

**API**：
```python
from system.task_controller import get_task_controller

controller = get_task_controller()

# 初始化
await controller.initialize()

# 处理用户输入
result = await controller.process_user_input("每半小时提醒我起来走走")
if result:
    # 这是任务相关的输入
    print(result["response"])
else:
    # 不是任务相关的输入
    pass
```

---

### 5. 主动交流系统 (`active_communication.py`)

**功能**：
- 管理主动消息队列
- 分发消息给订阅者
- 支持多种消息类型

**消息类型**：
- `suggestion` - 建议
- `reminder` - 提醒
- `check_in` - 问候
- `notification` - 通知
- `question` - 提问

**API**：
```python
from system.active_communication import get_active_communication

comm = get_active_communication()

# 启动
await comm.start()

# 订阅消息
async def on_message(message):
    print(f"收到消息: {message.content}")

comm.subscribe(on_message)

# 发送消息
await comm.send_reminder("起来走走，休息一下吧")
await comm.send_check_in("有什么需要帮助的吗？")
```

---

## 集成到现有系统

### 方式1：在对话处理流程中集成

在 `apiserver/api_server.py` 或 `ui/controller/tool_chat.py` 中：

```python
from system.task_controller import get_task_controller

# 初始化
controller = get_task_controller()
await controller.initialize()

# 在处理用户输入时
async def handle_user_input(user_input: str):
    # 先检查是否是任务相关
    result = await controller.process_user_input(user_input)

    if result:
        # 是任务相关，直接返回响应
        return result["response"]
    else:
        # 不是任务相关，正常处理对话
        return await normal_chat_process(user_input)
```

### 方式2：订阅主动消息

在UI层订阅主动消息：

```python
from system.active_communication import get_active_communication

comm = get_active_communication()

# 订阅
async def on_active_message(message):
    # 在UI中显示主动消息
    display_message(message.content, message_type=message.message_type.value)

comm.subscribe(on_active_message)

# 启动
await comm.start()
```

### 方式3：扩展自主性引擎

在 `system/agency_engine.py` 中集成任务调度：

```python
from system.task_scheduler import get_task_scheduler

class AgencyEngine:
    def __init__(self):
        self.scheduler = get_task_scheduler()

    async def _execute_single_action(self, action):
        if action.action_type == "reminder":
            # 添加提醒任务
            self.scheduler.add_task(...)
```

---

## 使用示例

### 示例1：用户设置提醒

**用户输入**：
```
每半小时提醒我起来走走
```

**系统处理**：
1. 意图解析器识别为 `add_task` 意图
2. 提取时间信息：`recurring_interval=30分钟`
3. 任务控制器添加任务到调度器
4. 返回响应："好的，我已经设置了起来走走，会在每30分钟提醒你。"

**执行流程**：
```
用户输入 → 意图解析 → 任务控制器 → 调度器 → 时间感知 → 任务触发 → 主动交流 → UI显示
```

### 示例2：任务触发

**30分钟后**：
1. 时间感知系统检测到任务到期
2. 任务调度器执行任务
3. 触发回调 `_on_reminder_triggered`
4. 主动交流系统发送消息
5. UI显示："起来走走，休息一下吧~"

### 示例3：查看任务

**用户输入**：
```
查看我的提醒
```

**系统响应**：
```
这是你设置的提醒任务：
1. 起来走走 - 每30分钟
2. 喝水 - 每1小时
3. 吃饭 - 12:00
```

---

## 配置文件

任务配置会保存在 `system/tasks_config.json`：

```json
{
  "tasks": [
    {
      "task_id": "task_1737888000000",
      "title": "起来走走",
      "description": "每半小时提醒我起来走走",
      "task_type": "reminder",
      "priority": "medium",
      "scheduled_time": "2026-01-26T15:30:00",
      "recurring": true,
      "recurring_interval": 1800,
      "status": "pending",
      "enabled": true,
      "created_at": "2026-01-26T15:00:00",
      "execution_count": 5
    }
  ],
  "saved_at": "2026-01-26T15:30:00"
}
```

---

## 启动脚本

创建 `scripts/start_with_tasks.py`：

```python
#!/usr/bin/env python3
import asyncio
from system.task_controller import get_task_controller

async def main():
    # 初始化任务控制器
    controller = get_task_controller()
    await controller.initialize()

    print("任务调度系统已启动")
    print("你可以对我说：")
    print("- '每半小时提醒我起来走走'")
    print("- '一小时后提醒我喝水'")
    print("- '每天9:00提醒我学习'")
    print("- '查看我的提醒'")

    # 保持运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await controller.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 时间感知与自主性的关系

### 时间感知是自主性的基础

时间感知让自主性系统能够：

1. **理解时间上下文** - 知道现在是早晨、晚上、深夜
2. **预测需求** - 根据时间规律预测用户需求
3. **规划行动** - 在合适的时间执行行动
4. **感知紧迫性** - 判断任务的紧急程度

### 集成到自主性引擎

在 `agency_engine.py` 中：

```python
async def evaluate_context(self, context: Dict[str, Any]) -> float:
    # 使用时间感知系统
    temporal = get_temporal_perception()
    state = temporal.get_state()

    # 根据时间上下文调整主动性
    if state.time_context in [TimeContext.LATE_NIGHT]:
        # 深夜降低主动性
        scores["time"] = 0.2
    elif state.time_context in [TimeContext.MORNING, TimeContext.AFTERNOON]:
        # 工作时间提高主动性
        scores["time"] = 0.8

    return total_score
```

---

## 注意事项

1. **任务持久化**：任务会自动保存到 `tasks_config.json`，重启后自动加载
2. **循环任务**：循环任务会在触发后自动重新调度
3. **任务优先级**：高优先级任务会先执行
4. **消息队列**：主动消息会按优先级排序分发
5. **性能考虑**：任务检查间隔为5秒，时间感知检查间隔为10秒

---

## 扩展建议

1. **自然语言时间**：支持更复杂的时间表达（如"下周三"、"下个月5号"）
2. **任务分类**：按类别管理任务（健康、工作、学习等）
3. **任务统计**：记录任务完成情况、执行频率
4. **智能建议**：基于历史数据建议最佳提醒时间
5. **任务依赖**：支持任务之间的依赖关系

---

## 总结

时间感知与任务调度系统为弥娅提供了：

- ✅ 时间感知能力
- ✅ 对话式任务配置
- ✅ 定时提醒功能
- ✅ 自主触发机制
- ✅ 与自主性系统集成

这让弥娅能够在正确的时间做正确的事情，真正做到"有感知的决策"。
