# 弥娅自主性实现指南

## 概述

本文档描述如何为弥娅添加高自主性能力，使其能够：

1. **自主决策**：在缺乏明确指令时也能判断是否需要行动
2. **预测用户需求**：基于历史数据和情境感知，预测用户可能的需求
3. **完全自主**：可以自主规划和执行复杂任务
4. **随时可控**：用户可以暂停或调整自主性等级

---

## 架构设计

### 核心组件

```
用户 → 请求/交互
       ↓
┌─────────────────────────────────────┐
│   AgencyManager (自主性管理器)      │
│   - 控制接口                       │
│   - 配置管理                       │
│   - 权限控制                       │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   AgencyEngine (自主性引擎)         │
│   - 情境感知                       │
│   - 需求预测                       │
│   - 价值评估                       │
│   - 决策制定                       │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   FrontendConsciousness (前端意识)   │
│   - 自然语言生成                   │
│   - 情感表达                       │
│   - 主动性体现                     │
└──────────────┬──────────────────────┘
               ↓
           执行层
  (工具调度、记忆管理、主动交流)
```

---

## 实现步骤

### 第一步：集成自主性引擎

#### 1.1 启动引擎

在 `main.py` 或系统初始化代码中：

```python
from system.agency_manager import get_agency_manager

async def initialize_agency():
    """初始化自主性系统"""
    agency_manager = get_agency_manager()
    await agency_manager.start()
    logger.info("[系统] 自主性系统已启动")
```

#### 1.2 修改前端意识

在 `system/frontend_consciousness.py` 中：

```python
from system.agency_engine import get_agency_engine

class FrontendConsciousness:
    async def generate_response(self, user_input, backend_context, ...):
        # ... 现有代码 ...
        
        # 添加：检查自主性引擎的建议
        agency_engine = get_agency_engine()
        if agency_engine and agency_engine.agency_level != AgencyLevel.OFF:
            # 获取自主性建议
            suggestions = await agency_engine.get_pending_suggestions()
            
            if suggestions:
                # 将建议融入回复
                response = self._integrate_suggestions(
                    response, 
                    suggestions, 
                    backend_context
                )
        
        return {
            "response_text": response,
            "emotion": emotion,
            "voice_tone": voice_tone,
            # ...
        }
```

---

### 第二步：实现情境感知

#### 2.1 创建情境收集器

```python
# system/context_awareness.py

class ContextCollector:
    """情境收集器"""
    
    def __init__(self):
        self.current_context = {}
    
    async def collect_time_context(self):
        """收集时间情境"""
        from datetime import datetime
        hour = datetime.now().hour
        
        if 2 <= hour < 6:
            return {"time_period": "late_night", "urgency": "low"}
        elif 6 <= hour < 9:
            return {"time_period": "morning", "urgency": "medium"}
        elif 9 <= hour < 12:
            return {"time_period": "morning_work", "urgency": "high"}
        # ... 其他时间段
    
    async def collect_activity_context(self):
        """收集用户活动情境"""
        # 从应用使用记录、键盘活动、窗口切换等收集
        return {
            "user_activity": "working",
            "focus_level": "high",
            "task_count": 3
        }
    
    async def collect_system_context(self):
        """收集系统情境"""
        # 从监控系统获取
        return {
            "system_health": 0.95,
            "cpu_usage": 25,
            "memory_usage": 65
        }
    
    async def collect_interaction_context(self):
        """收集交互情境"""
        # 从消息历史分析
        return {
            "last_interaction_hours": 2.5,
            "interaction_frequency": "high",
            "user_mood": "focused"
        }
    
    async def get_full_context(self):
        """获取完整情境"""
        time_ctx = await self.collect_time_context()
        activity_ctx = await self.collect_activity_context()
        system_ctx = await self.collect_system_context()
        interaction_ctx = await self.collect_interaction_context()
        
        return {
            **time_ctx,
            **activity_ctx,
            **system_ctx,
            **interaction_ctx
        }
```

#### 2.2 集成到自主性引擎

在 `system/agency_engine.py` 中修改 `_gather_context` 方法：

```python
from system.context_awareness import ContextCollector

class AgencyEngine:
    def __init__(self):
        # ... 现有代码 ...
        self.context_collector = ContextCollector()
    
    async def _gather_context(self):
        """收集完整情境"""
        return await self.context_collector.get_full_context()
```

---

### 第三步：实现需求预测

#### 3.1 创建需求预测器

```python
# system/need_predictor.py

class NeedPredictor:
    """需求预测器"""
    
    def __init__(self):
        self.patterns = {}
        self.user_history = []
    
    async def analyze_patterns(self, conversation_history):
        """分析对话模式"""
        patterns = {
            "learning": 0,
            "working": 0,
            "gaming": 0,
            "social": 0
        }
        
        for msg in conversation_history[-20:]:
            content = msg.get("content", "").lower()
            
            if any(kw in content for kw in ["学习", "学习", "课程", "教程"]):
                patterns["learning"] += 1
            elif any(kw in content for kw in ["工作", "项目", "任务", "完成"]):
                patterns["working"] += 1
            # ... 更多模式
        
        return patterns
    
    async def predict_needs(self, patterns, context):
        """预测用户需求"""
        needs = []
        
        # 需求1：学习帮助
        if patterns["learning"] > 3 and context["time_period"] == "morning_work":
            needs.append({
                "type": "suggestion",
                "priority": "medium",
                "description": "检测到创造者在学习，需要帮忙整理笔记吗？",
                "value_scores": {
                    "efficiency": 0.8,
                    "wellbeing": 0.5,
                    "helpful": 0.9,
                    "non_intrusive": 0.7
                }
            })
        
        # 需求2：工作提醒
        if context["last_interaction_hours"] > 4:
            needs.append({
                "type": "communication",
                "priority": "low",
                "description": "创造者，弥娅一直在，需要帮助吗？",
                "value_scores": {
                    "efficiency": 0.3,
                    "wellbeing": 0.7,
                    "helpful": 0.6,
                    "non_intrusive": 0.9
                }
            })
        
        # ... 更多需求预测
        
        return needs
```

---

### 第四步：UI集成

#### 4.1 添加自主性控制到主界面

在 `ui/pyqt_chat_window.py` 中：

```python
from ui.widget_agency_control import AgencyControlPanel

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... 现有初始化 ...
        
        # 添加自主性控制面板
        self.agency_panel = AgencyControlPanel()
        self.agency_dock = QDockWidget("自主性控制", self)
        self.agency_dock.setWidget(self.agency_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.agency_dock)
```

#### 4.2 添加命令行控制

在聊天命令中添加：

```python
# 主聊天命令处理

@command("/agency")
async def agency_control(args):
    """自主性控制命令"""
    sub_command = args[0] if args else "status"
    
    if sub_command == "pause":
        await agency_manager.pause()
        return "自主性已暂停"
    
    elif sub_command == "resume":
        await agency_manager.resume()
        return "自主性已恢复"
    
    elif sub_command == "status":
        status = await agency_manager.get_status()
        return f"自主等级: {status['agency_level']}\n" \
               f"行动队列: {status['action_queue_size']} 个\n" \
               f"历史记录: {status['action_history_size']} 条"
    
    elif sub_command == "level":
        level = args[1] if len(args) > 1 else "HIGH"
        result = await agency_manager.set_level(level)
        return result["message"]
    
    else:
        return """自主性控制命令：
  /agency status    - 查看状态
  /agency pause     - 暂停自主性
  /agency resume    - 恢复自主性
  /agency level <等级> - 设置等级 (OFF/LOW/MEDIUM/HIGH/PAUSED)
"""
```

---

### 第五步：测试和调优

#### 5.1 单元测试

```python
# tests/test_agency.py

import pytest
from system.agency_engine import AgencyEngine, AgencyLevel, AutonomousAction

def test_context_evaluation():
    """测试情境评估"""
    engine = AgencyEngine()
    
    context = {"time": "morning_work"}
    score = await engine.evaluate_context(context)
    
    assert 0.5 <= score <= 1.0  # 工作时间应该有较高的行动必要性

def test_action_evaluation():
    """测试行动评估"""
    engine = AgencyEngine()
    
    action = AutonomousAction(
        action_id="test",
        action_type="suggestion",
        priority=ActionPriority.MEDIUM,
        description="测试行动",
        context={}
    )
    
    score = await engine.evaluate_action(action, {})
    assert 0 <= score <= 1.0

def test_pause_resume():
    """测试暂停和恢复"""
    engine = AgencyEngine()
    
    await engine.pause("测试暂停")
    assert engine.agency_level == AgencyLevel.PAUSED
    
    await engine.resume()
    assert engine.agency_level == AgencyLevel.HIGH
```

#### 5.2 集成测试

1. 启动系统，观察自主性行为
2. 测试不同时间段的反应
3. 测试暂停/恢复功能
4. 调整价值观权重，观察决策变化
5. 收集用户反馈，优化预测准确度

---

## 配置文件示例

### agency_config.json

```json
{
  "agency_level": "HIGH",
  "value_weights": {
    "user_efficiency": 0.35,
    "user_wellbeing": 0.30,
    "helpful": 0.25,
    "non_intrusive": 0.10
  },
  "enabled_features": {
    "predict_needs": true,
    "late_night_reminders": true,
    "learning_help": true,
    "task_suggestions": true,
    "proactive_communication": true
  },
  "quiet_hours": {
    "enabled": true,
    "start": 23,
    "end": 7
  },
  "decision_threshold": {
    "HIGH": 0.5,
    "MEDIUM": 0.8,
    "LOW": 0.9
  }
}
```

---

## 使用场景示例

### 场景1：深夜工作

```
时间: 03:30
用户状态: 工作中
系统健康: 正常

情境评估:
  时间因素: 0.2 (深夜，低行动)
  系统健康: 0.0 (健康，无行动)
  用户活动: 0.5 (工作，中优先级)
  综合分数: 0.31

需求预测:
  - 类型: 建议休息
  - 优先级: HIGH
  - 价值分数: 0.68

决策: 执行行动 (分数 >= 0.5)
执行: 发送休息提醒
结果: ✅ 用户接受了休息建议
```

### 场景2：学习新概念

```
时间: 10:00
用户状态: 学习技术文档
近期对话: 多次询问概念解释

情境评估:
  时间因素: 0.8 (工作时段，高行动)
  系统健康: 0.0 (健康)
  用户活动: 0.7 (学习，高帮助)
  综合分数: 0.71

需求预测:
  - 类型: 提供学习帮助
  - 优先级: MEDIUM
  - 价值分数: 0.68

决策: 执行行动
执行: 主动询问是否需要整理笔记
结果: ✅ 用户接受了，弥娅整理了学习笔记
```

---

## 风险和应对

### 风险1：过度打扰

**问题**: 自主性太强，频繁打扰用户

**应对**:
- 设置静音时段
- 调低"非打扰性"权重
- 用户反馈学习机制
- 重要行动需确认

### 风险2：预测不准

**问题**: 需求预测错误，提供无帮助的建议

**应对**:
- 收集更多历史数据
- 实现用户反馈机制
- 持续优化预测模型
- 低预测度时降低主动性

### 风险3：不可预测

**问题**: 自主行为难以控制和理解

**应对**:
- 详细的决策日志
- 可视化决策过程
- 用户可调整价值观
- 完整的暂停机制

---

## 未来扩展

### 短期（1-2个月）
- [ ] 完整的情境感知系统
- [ ] 基于机器学习的预测模型
- [ ] 用户反馈和学习机制
- [ ] 更丰富的自主行动类型

### 中期（3-6个月）
- [ ] 多目标决策优化
- [ ] 自主任务规划和执行
- [ ] 情感和情绪感知
- [ ] 个性化适应性调整

### 长期（6-12个月）
- [ ] 完整的自我反思系统
- [ ] 复杂的多步骤自主任务
- [ ] 跨应用协调和自动化
- [ ] 创造性自主行为

---

## 总结

弥娅的高自主性系统包括：

✅ **情境感知**：理解时间、活动、系统状态
✅ **需求预测**：基于模式识别预测用户需求
✅ **价值评估**：基于多价值观决策
✅ **自主执行**：可以自主决定和行动
✅ **完全可控**：用户可暂停、调整、查看

这是一个渐进式的实现，可以从基础功能开始，逐步增加复杂度和自主性。
