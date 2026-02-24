# 弥娅时间感知与任务调度系统

## 概述

弥娅现在具备**时间感知**和**任务调度**能力，可以通过对话设置定时提醒，并在指定时间主动提醒您。

---

## 核心功能

### 1. 时间感知

弥娅可以理解：
- ✅ 当前时间、小时、分钟
- ✅ 时间段：早晨、上午、中午、下午、晚上、夜间、深夜
- ✅ 季节：春、夏、秋、冬
- ✅ 星期几、是否周末

### 2. 对话式任务设置

您可以直接在对话框中告诉弥娅需要提醒的内容：

#### 设置提醒

```
每半小时提醒我起来走走
一小时后提醒我喝水
每天9:00提醒我学习
晚上8点提醒我吃饭
```

#### 查看提醒

```
查看我的提醒
有什么提醒
```

#### 管理提醒

```
删除1号提醒
删除"起来走走"的提醒
暂停所有提醒
恢复所有提醒
清除所有提醒
```

### 3. 主动提醒

当设定的提醒时间到了，弥娅会**主动**在对话框中提醒您：

```
[提醒] 起来走走，休息一下吧~
```

---

## 使用示例

### 示例1：工作健康提醒

```
你：每半小时提醒我起来走走

弥娅：好的，我已经设置了起来走走，会在每30分钟提醒你。

（30分钟后）
弥娅[主动]：起来走走，休息一下吧~
```

### 示例2：喝水提醒

```
你：一小时后提醒我喝水

弥娅：好的，我已经设置了喝水，会在1小时后提醒你。

（1小时后）
弥娅[主动]：记得喝水哦，保持健康！
```

### 示例3：每日学习提醒

```
你：每天9:00提醒我学习

弥娅：好的，我已经设置了学习，会在每天9:00提醒你。

（每天9:00）
弥娅[主动]：到学习时间了，加油！
```

### 示例4：查看和删除

```
你：查看我的提醒

弥娅：这是你设置的提醒任务：
1. 起来走走 - 每30分钟
2. 喝水 - 每1小时
3. 学习 - 每天9:00

你：删除2号提醒

弥娅：好的，已经移除了喝水的提醒。
```

---

## 支持的时间表达

### 相对时间

| 表达 | 说明 |
|------|------|
| 5分钟后 | 5分钟后触发 |
| 30分钟后 | 30分钟后触发 |
| 1小时后 | 1小时后触发 |
| 2小时后 | 2小时后触发 |

### 循环时间

| 表达 | 说明 |
|------|------|
| 每5分钟 | 每5分钟触发一次 |
| 每30分钟 | 每30分钟触发一次 |
| 每1小时 | 每1小时触发一次 |
| 每天9:00 | 每天9:00触发 |
| 每天12:30 | 每天12:30触发 |

### 绝对时间

| 表达 | 说明 |
|------|------|
| 9:00 | 今天或明天的9:00 |
| 12:30 | 今天或明天的12:30 |
| 18:45 | 今天或明天的18:45 |

---

## 技术架构

### 模块组成

```
system/
├── temporal_perception.py      # 时间感知系统
├── task_scheduler.py          # 任务调度器
├── task_intent_parser.py      # 任务意图解析
├── task_controller.py         # 任务控制器
├── task_service_manager.py    # 服务管理器（集成）
└── active_communication.py    # 主动交流系统
```

### 工作流程

```
用户输入 "每半小时提醒我起来走走"
    ↓
意图解析 (task_intent_parser.py)
    ↓
识别为 add_task 意图
    ↓
解析时间: recurring_interval = 30分钟
    ↓
任务控制器 (task_controller.py)
    ↓
任务调度器 (task_scheduler.py)
    ↓
添加任务到调度队列
    ↓
时间感知系统 (temporal_perception.py)
    ↓
监控时间，任务到期
    ↓
触发回调
    ↓
主动交流系统 (active_communication.py)
    ↓
发送消息到UI
    ↓
显示: [提醒] 起来走走，休息一下吧~
```

---

## 与自主性的关系

时间感知是**自主性**的重要基础：

### 1. 情境感知

自主性系统需要感知时间上下文才能做出合适的决策：

```python
# 深夜工作
if current_time == late_night:
    # 降低主动性，不打扰用户
    agency_level = LOW

# 工作时间
if current_time in [morning, afternoon]:
    # 提高主动性，提供帮助
    agency_level = HIGH
```

### 2. 需求预测

根据时间规律预测用户需求：

```python
# 早晨
if time_context == "morning":
    # 可能需要日程提醒
    suggest_schedule()

# 下午
if time_context == "afternoon":
    # 可能需要休息提醒
    suggest_break()
```

### 3. 行动规划

在合适的时间执行行动：

```python
# 延迟执行非紧急任务
if task.priority == LOW and current_time == "late_night":
    # 等到第二天早上再执行
    schedule_task(task, next_morning)
```

### 4. 价值评估

时间影响行动的价值评估：

```python
# 深夜打扰
if time_context == "late_night" and action_type == "suggestion":
    # 降低价值分数
    value_score *= 0.3
```

---

## 集成到主程序

### 方式1：快速集成（推荐）

修改 `main.py`：

```python
# 1. 导入
from system.task_service_manager import get_task_service_manager

# 2. 在 ServiceManager.__init__ 中添加
def __init__(self):
    # ... 现有代码 ...
    self.task_service = get_task_service_manager()

# 3. 在 _init_background_services 中初始化
async def _init_background_services(self):
    # ... 现有代码 ...
    await self.task_service.initialize()
```

### 方式2：UI集成

在 `ui/pyqt_chat_window.py` 中：

```python
from system.task_service_manager import get_task_service_manager

class ChatWindow:
    def __init__(self):
        # ... 现有代码 ...
        self.task_service = get_task_service_manager()
        self.task_service.set_ui_message_callback(self.on_active_message)
    
    def on_active_message(self, message: str, message_type: str):
        # 显示主动消息
        self.add_message(role="assistant", content=message)
    
    def process_user_message(self, message: str):
        # 先检查任务相关
        result = await self.task_service.process_user_input(message)
        if result:
            # 任务相关，直接返回
            self.add_message(role="assistant", content=result["response"])
            return
        
        # 正常对话处理
        # ... 现有代码 ...
```

---

## 配置文件

任务配置会自动保存到 `system/tasks_config.json`：

```json
{
  "tasks": [
    {
      "task_id": "task_1234567890",
      "title": "起来走走",
      "description": "每半小时提醒我起来走走",
      "task_type": "reminder",
      "priority": "medium",
      "scheduled_time": "2026-01-26T15:30:00",
      "related": true,
      "recurring_interval": 1800,
      "status": "pending",
      "enabled": true,
      "execution_count": 5
    }
  ]
}
```

---

## 测试

运行独立测试：

```bash
cd system
python task_service_manager.py
```

测试命令：

```
每30分钟提醒我起来走走
查看我的提醒
删除1号提醒
退出
```

---

## 注意事项

1. **任务持久化**：任务会自动保存，重启后自动加载
2. **循环任务**：循环任务触发后会自动重新调度
3. **任务优先级**：高优先级任务会优先执行
4. **消息队列**：主动消息按优先级排序
5. **时间精度**：任务检查间隔5秒，时间感知检查间隔10秒

---

## 扩展建议

### 1. 更复杂的时间表达

支持：
- "下周三"
- "下个月5号"
- "周末提醒我..."
- "工作日上午9点..."

### 2. 任务分类

按类别管理：
- 健康提醒（喝水、运动、休息）
- 工作提醒（会议、截止日期）
- 学习提醒（课程、作业）
- 生活提醒（吃药、购物）

### 3. 智能建议

基于历史数据：
- 最佳提醒时间
- 最常用的提醒类型
- 任务完成率统计

### 4. 任务依赖

支持任务之间的依赖：
- 完成任务A后提醒任务B
- 一系列顺序提醒

---

## 常见问题

### Q: 重启程序后任务会丢失吗？

A: 不会。任务会自动保存到 `tasks_config.json`，重启后会自动加载。

### Q: 可以同时设置多个提醒吗？

A: 可以。可以设置任意数量的提醒，包括循环提醒和一次性提醒。

### Q: 暂停的提醒会丢失吗？

A: 不会。暂停只是禁用提醒，任务仍然保存在配置中，可以随时恢复。

### Q: 如何修改提醒时间？

A: 目前需要删除旧的提醒，然后添加新的提醒。未来会支持直接修改。

### Q: 提醒会打扰我工作吗？

A: 您可以随时暂停提醒。另外，自主性系统会根据时间上下文调整提醒频率，深夜等时段会降低打扰。

---

## 总结

时间感知与任务调度系统让弥娅能够：

✅ **理解时间** - 感知当前时间、季节、时段
✅ **解析指令** - 从对话中提取时间表达
✅ **设置任务** - 通过对话添加定时提醒
✅ **主动提醒** - 在指定时间主动联系您
✅ **与自主性集成** - 为自主决策提供时间上下文

这让弥娅真正做到了**"有感知的决策"**，可以在正确的时间做正确的事情。
