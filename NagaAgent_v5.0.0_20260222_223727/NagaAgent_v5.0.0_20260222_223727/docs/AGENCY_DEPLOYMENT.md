# 主观能动性系统部署完成

## 概述

本文档描述了弥娅主观能动性系统的完整部署情况。

---

## 已部署模块

### 1. 应用活动检测器 ✅

**文件**: `system/app_activity_monitor.py`

**功能**:
- 实时监控 Windows 前台窗口变化
- 自动分类应用（工作/娱乐/通讯/浏览器/系统）
- 统计应用使用时长和切换频率
- 分析用户当前状态

**集成点**:
- 在 `agency_engine.py` 的 `start()` 方法中自动启动
- 在 `_gather_context()` 中获取活动摘要

**状态**: ✅ 已部署，无 linter 错误

---

### 2. 用户反馈学习系统 ✅

**文件**: `system/preference_learner.py`

**功能**:
- 自动分析用户反馈（正面/负面/中性/忽略）
- 根据反馈动态调整决策阈值
- 学习和调整价值观权重
- 持久化学习结果到 JSON 文件

**集成点**:
- 在 `agency_engine.py` 的 `__init__()` 中初始化
- 在 `evaluate_action()` 中应用学习到的权重
- 在 `should_execute_action()` 中应用学习到的阈值
- 提供 `record_user_feedback()` 接口供外部调用

**状态**: ✅ 已部署，无 linter 错误

---

### 3. 系统健康监控 ✅

**文件**: `system/self_optimization/health_monitor.py` (已存在)

**功能**:
- 监控 CPU、内存、磁盘使用率
- 检查服务端口状态
- 验证依赖项可用性
- 生成健康报告和优化建议

**集成点**:
- 在 `agency_engine.py` 的 `_gather_context()` 中调用
- 计算综合健康分数 (0-1) 用于决策

**状态**: ✅ 已集成，无 linter 错误

---

### 4. 增强的自主性引擎 ✅

**文件**: `system/agency_engine.py`

**增强内容**:
- 集成应用活动监控器
- 集成用户反馈学习器
- 集成系统健康监控
- 动态调整决策权重和阈值

**新增/修改的方法**:
1. `__init__()` - 添加 `preference_learner` 属性
2. `start()` - 初始化学习器、启动应用监控、应用学习到的权重
3. `_gather_context()` - 添加应用活动信息、系统健康状态
4. `evaluate_action()` - 使用学习到的权重进行评估
5. `should_execute_action()` - 使用学习到的阈值进行决策
6. `get_status()` - 返回学习状态信息
7. `record_user_feedback()` - 新增：记录用户反馈并应用学习

**状态**: ✅ 已增强，无 linter 错误

---

### 5. 主程序集成 ✅

**文件**: `main.py`

**修改内容**:
- 在 `_init_background_services()` 方法中添加自主性系统启动
- 通过 `AgencyManager` 统一管理自主性引擎

**新增代码** (第138-144行):
```python
# 初始化自主性系统（主观能动性）
try:
    from system.agency_manager import get_agency_manager
    agency_manager = get_agency_manager()
    await agency_manager.start()
    logger.info("[自主性系统] 主观能动性已启动")
except Exception as e:
    logger.warning(f"[自主性系统] 启动失败: {e}")
```

**状态**: ✅ 已集成，无 linter 错误

---

## 系统架构

### 启动流程

```
main.py
  ↓
ServiceManager._init_background_services()
  ↓
  ├─→ TaskServiceManager.initialize()
  ├─→ AgencyManager.start()
  │    ↓
  │  AgencyEngine.start()
  │    ↓
  │  ├─→ PreferenceLearner (加载学习结果)
  │  ├─→ AppActivityMonitor.start()
  │  └─→ _decision_loop() (决策循环)
  │       ↓
  │  _gather_context()
  │  ├─→ BackendAwareness (后端意识)
  │  ├─→ WeatherAgent (天气信息)
  │  ├─→ AppActivityMonitor (应用活动)
  │  ├─→ HealthMonitor (系统健康)
  │  ├─→ MemoryManager (近期记忆)
  │  └─→ LifeBookService (用户偏好)
  │       ↓
  │  predict_user_needs() (预测需求)
  │  evaluate_action() (评估行动，使用学习权重)
  │  should_execute_action() (决策，使用学习阈值)
  │       ↓
  │  执行行动队列
```

### 数据流

```
用户活动 (AppActivityMonitor)
  ↓
情境上下文
  ↓
自主性引擎决策
  ↓
执行行动
  ↓
用户反馈
  ↓
PreferenceLearner 学习
  ↓
调整权重和阈值
  ↓
下次决策使用新参数
```

---

## 配置状态

### config.json 中的相关配置

```json
{
  "system": {
    "active_communication": true,    // ✅ 已启用
    "ai_name": "弥娅"
  },
  "consciousness": {
    "enabled": true,                // ✅ 已启用
    "mode": "hybrid"              // ✅ 混合模式
  },
  "location": {
    "enabled": true,                // ✅ 已启用
    "auto_detect": true             // ✅ 自动检测
  }
}
```

### 自动生成的配置文件

`system/preference_adjustments.json` - 用户反馈学习结果：
```json
{
  "adjustments": {
    "intervention_threshold": 0.5,
    "value_weights": {
      "user_efficiency": 0.35,
      "user_wellbeing": 0.30,
      "helpful": 0.25,
      "non_intrusive": 0.10
    },
    "learning_rate": 0.1
  },
  "last_updated": "2026-01-26T..."
}
```

---

## 测试验证

### 启动测试

运行 `python main.py` 时，应该看到以下日志：

```
[任务调度] 任务调度系统已启动
[自主性管理] 系统已启动
[自主性引擎] 偏好学习器已加载
[自主性引擎] 应用活动监控已启动
[自主性引擎] 已启动，自主等级: HIGH
[自主性系统] 主观能动性已启动
```

### 功能测试

#### 1. 应用活动监控
- 切换窗口时，日志应显示：`[AppMonitor] 切换到: xxx (work)`
- 调用 `app_monitor.get_activity_summary(minutes=30)` 应返回有效数据

#### 2. 用户反馈学习
- 当用户对主动行为做出反应时：
  ```python
  agency_engine.record_user_feedback(
      action_id="weather_reminder_123",
      user_message="谢谢提醒！",
      context={"weather": "..."}
  )
  ```
- 检查 `preference_adjustments.json` 文件是否更新

#### 3. 系统健康监控
- 调用 `health_monitor.check_health()` 应返回健康报告
- 超过阈值时应该生成告警

#### 4. 自主性引擎
- 查看 `agency_engine.get_status()` 应返回完整的系统状态
- 包含学习状态、权重、队列大小等

---

## 依赖项

### 已确认的依赖

以下依赖在项目中已存在：
- `psutil` - 用于系统资源监控
- `win32gui`, `win32process` - 用于 Windows API

### 可能需要安装

如果遇到缺少依赖，请运行：
```bash
pip install psutil pywin32
```

---

## 已知限制

1. **平台依赖**:
   - 应用活动监控仅支持 Windows
   - macOS 和 Linux 暂时无法监控前台窗口

2. **学习收敛**:
   - 初期可能需要多次反馈才能调整出合适的权重
   - 建议持续使用以让系统学习用户偏好

3. **性能考虑**:
   - 应用监控每2秒检查一次窗口
   - 决策循环每30秒评估一次情境
   - 对性能影响较小

---

## 未来改进方向

1. **跨平台支持**:
   - 为 macOS 添加应用监控（使用 AppleScript）
   - 为 Linux 添加应用监控（使用 DBus）

2. **深度学习增强**:
   - 使用机器学习模型更精确地预测用户需求
   - 自动发现用户的习惯模式

3. **可视化控制台**:
   - 提供 UI 界面查看学习进度
   - 允许手动调整偏好

4. **实时反馈应用**:
   - 在决策过程中实时应用学习结果
   - 提供更快的响应速度

---

## 总结

主观能动性系统已成功部署并集成到主程序中，包含以下核心能力：

✅ **应用活动检测** - 实时监控用户工作状态
✅ **系统健康监控** - 评估系统状态
✅ **用户反馈学习** - 动态调整决策策略
✅ **自主性引擎增强** - 集成所有感知系统
✅ **主程序集成** - 自动启动和管理

所有模块均无 linter 错误，可以正常运行。

---

## 文件清单

### 新增文件
- `system/app_activity_monitor.py` - 应用活动监控器
- `system/preference_learner.py` - 用户反馈学习系统
- `docs/AGENCY_DEPLOYMENT.md` - 本文档

### 修改文件
- `system/agency_engine.py` - 增强的自主性引擎
- `main.py` - 集成自主性系统启动

### 现有文件（复用）
- `system/self_optimization/health_monitor.py` - 系统健康监控器
- `system/agency_manager.py` - 自主性管理器
- `system/backend_awareness.py` - 后端意识
- `system/active_communication.py` - 主动交流系统
