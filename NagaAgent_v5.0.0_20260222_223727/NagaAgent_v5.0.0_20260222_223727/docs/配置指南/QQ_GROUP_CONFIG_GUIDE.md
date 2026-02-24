# NagaAgent Modified Version - QQ 群聊配置和 MCP 优化指南

## 📋 问题分析

根据日志分析，发现以下问题：

### 问题 1: MCP 响应速度慢
- **现象**: 应用启动工具需要约 75 秒才响应
- **原因**: 应用启动扫描首次使用时会扫描整个系统（注册表 + 快捷方式），找到 240 个应用
- **影响**: 用户长时间等待，体验不佳

### 问题 2: Undefined 工具箱没有群聊管理功能
- **现象**: 当前 49 个工具中，没有群聊相关的管理工具（禁言、踢人、设置管理员等）
- **原因**: Undefined 工具箱专注于在线功能和文件操作，不包含 QQ 群管理功能
- **影响**: 无法通过工具控制群聊行为

---

## 🔧 解决方案

### 解决方案 1: 优化 MCP 超时时间

**已优化** ✓

已将 MCP 回调超时时间从 30 秒增加到 120 秒，避免长时间工具（如应用启动）超时。

**修改文件**: `mcpserver/mcp_scheduler.py`

```python
# 修改前
async with session.post(callback_url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:

# 修改后
async with session.post(callback_url, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as response:
```

---

### 解决方案 2: 添加 QQ 群聊回复控制配置

#### 配置项说明

在 `config.json` 的 `qq` 配置段中添加以下配置：

```json
{
  "qq": {
    "enabled": true,
    "bot_qq": "your_bot_qq_number",
    "http_url": "http://127.0.0.1:3000",
    "http_token": "",
    
    // ====== 群聊回复控制 ======
    
    // 是否启用群聊自动回复（默认 true）
    "enable_group_reply": true,
    
    // 群聊回复模式（默认 "intelligent"）
    // - "all": 回复所有群消息
    // - "intelligent": 智能判断是否回复（推荐）
    // - "at_only": 只回复@机器人的消息
    // - "none": 不回复群消息
    "group_reply_mode": "intelligent",
    
    // 群聊白名单（只回复这些群的）
    // 留空表示不限制
    "group_whitelist": [],
    
    // 群聊黑名单（不回复这些群的）
    // 留空表示不限制
    "group_blacklist": [],
    
    // 群聊回复触发关键词（仅在 intelligent 模式下生效）
    // 留空表示回复所有消息
    "group_reply_keywords": [],
    
    // 群聊回复冷却时间（秒，默认 5 秒）
    "group_reply_cooldown": 5,
    
    // 是否在群聊中启用工具调用（默认 true）
    "enable_group_tools": true,
    
    // 群聊中禁用的工具列表
    "group_disabled_tools": [],
    
    // ====== 其他配置 ======
    
    "enable_undefined_tools": true,
    "enable_voice": true,
    "reply_mode": "both"
  }
}
```

#### 配置详细说明

##### 1. enable_group_reply

是否启用群聊自动回复。

- `true`: 启用群聊自动回复
- `false`: 禁用群聊自动回复

##### 2. group_reply_mode

群聊回复模式，控制机器人在群聊中的回复行为。

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `all` | 回复所有群消息 | 活跃的群聊，机器人参与度要求高 |
| `intelligent` | 智能判断是否回复 | 推荐模式，平衡活跃度和打扰 |
| `at_only` | 只回复@机器人的消息 | 减少打扰，只响应特定请求 |
| `none` | 不回复群消息 | 机器人只响应私聊 |

##### 3. group_whitelist

群聊白名单，只回复这些群的 ID。

```json
"group_whitelist": [
  "123456789",
  "987654321"
]
```

- 留空 `[]`: 不限制，回复所有群（受其他配置限制）
- 填写群 ID: 只回复指定的群

##### 4. group_blacklist

群聊黑名单，不回复这些群的 ID。

```json
"group_blacklist": [
  "111222333",
  "444555666"
]
```

- 留空 `[]`: 不限制
- 填写群 ID: 不回复指定的群

**注意**: `group_whitelist` 和 `group_blacklist` 同时存在时，白名单优先。

##### 5. group_reply_keywords

群聊回复触发关键词（仅在 `intelligent` 模式下生效）。

```json
"group_reply_keywords": [
  "天气",
  "搜索",
  "画",
  "帮忙",
  "弥娅"
]
```

- 留空 `[]`: 回复所有消息（智能模式下仍会判断是否需要回复）
- 填写关键词: 只有消息包含关键词时才会触发回复

##### 6. group_reply_cooldown

群聊回复冷却时间（秒）。

```json
"group_reply_cooldown": 5
```

- 默认: 5 秒
- 建议: 3-10 秒，避免刷屏

##### 7. enable_group_tools

是否在群聊中启用工具调用。

```json
"enable_group_tools": true
```

- `true`: 群聊中可以使用工具（天气、搜索等）
- `false`: 群聊中禁用工具，只回复普通对话

##### 8. group_disabled_tools

群聊中禁用的工具列表。

```json
"group_disabled_tools": [
  "ai_draw_one",
  "bilibili_search"
]
```

- 留空 `[]`: 不限制工具
- 填写工具名: 禁用指定的工具

---

### 解决方案 3: 添加群聊指令

在 `message_listener.py` 中添加群聊控制指令：

```
# ====== 群聊管理指令 ======
/群回复 [all/intelligent/at_only/none] - 设置群回复模式
/群冷却 [秒数] - 设置群回复冷却时间
/群开启 - 启用群聊回复
/群关闭 - 禁用群聊回复
/群工具开启 - 启用群聊工具
/群工具关闭 - 禁用群聊工具
/群状态 - 查看当前群聊配置
```

---

## 📝 配置示例

### 示例 1: 默认配置（推荐）

```json
{
  "qq": {
    "enable_group_reply": true,
    "group_reply_mode": "intelligent",
    "group_whitelist": [],
    "group_blacklist": [],
    "group_reply_keywords": [],
    "group_reply_cooldown": 5,
    "enable_group_tools": true,
    "group_disabled_tools": []
  }
}
```

**特点**:
- 智能判断是否回复
- 无群限制
- 工具全部启用
- 5 秒冷却

---

### 示例 2: 只回复特定群

```json
{
  "qq": {
    "enable_group_reply": true,
    "group_reply_mode": "all",
    "group_whitelist": [
      "123456789",
      "987654321"
    ],
    "group_blacklist": [],
    "group_reply_keywords": [],
    "group_reply_cooldown": 3,
    "enable_group_tools": true,
    "group_disabled_tools": []
  }
}
```

**特点**:
- 只回复指定的 2 个群
- 回复所有消息
- 3 秒冷却（更快）

---

### 示例 3: 只响应 @ 机器人

```json
{
  "qq": {
    "enable_group_reply": true,
    "group_reply_mode": "at_only",
    "group_whitelist": [],
    "group_blacklist": [],
    "group_reply_keywords": [],
    "group_reply_cooldown": 10,
    "enable_group_tools": true,
    "group_disabled_tools": []
  }
}
```

**特点**:
- 只回复 @ 机器人的消息
- 10 秒冷却（避免重复 @）
- 适用于大型群聊

---

### 示例 4: 关键词触发

```json
{
  "qq": {
    "enable_group_reply": true,
    "group_reply_mode": "intelligent",
    "group_whitelist": [],
    "group_blacklist": [],
    "group_reply_keywords": [
      "天气",
      "搜索",
      "画",
      "帮忙",
      "弥娅"
    ],
    "group_reply_cooldown": 5,
    "enable_group_tools": true,
    "group_disabled_tools": []
  }
}
```

**特点**:
- 只回复包含关键词的消息
- 减少不必要的回复
- 智能模式配合关键词使用

---

### 示例 5: 禁用某些工具

```json
{
  "qq": {
    "enable_group_reply": true,
    "group_reply_mode": "intelligent",
    "group_whitelist": [],
    "group_blacklist": [],
    "group_reply_keywords": [],
    "group_reply_cooldown": 5,
    "enable_group_tools": true,
    "group_disabled_tools": [
      "ai_draw_one",
      "bilibili_search",
      "music_global_search"
    ]
  }
}
```

**特点**:
- 禁用 AI 绘图（避免刷屏）
- 禁用 B站搜索
- 禁用音乐搜索
- 保留天气、搜索等实用工具

---

## 🚀 使用方法

### 1. 编辑配置文件

打开 `config.json`，找到 `qq` 配置段，添加或修改群聊控制配置。

```json
{
  "qq": {
    "enabled": true,
    "bot_qq": "your_bot_qq_number",
    "http_url": "http://127.0.0.1:3000",
    "http_token": "",
    "enable_undefined_tools": true,
    "enable_voice": true,
    "reply_mode": "both",
    
    // 添加以下配置
    "enable_group_reply": true,
    "group_reply_mode": "intelligent",
    "group_whitelist": [],
    "group_blacklist": [],
    "group_reply_keywords": [],
    "group_reply_cooldown": 5,
    "enable_group_tools": true,
    "group_disabled_tools": []
  }
}
```

### 2. 重启程序

```bash
# Windows
start.bat

# Linux/macOS
./start.sh
```

### 3. 测试群聊回复

在 QQ 群中发送消息，观察机器人是否按配置回复。

---

## 🎯 最佳实践

### 推荐配置

对于大多数场景，推荐以下配置：

```json
{
  "qq": {
    "enable_group_reply": true,
    "group_reply_mode": "intelligent",
    "group_whitelist": [],
    "group_blacklist": [],
    "group_reply_keywords": [],
    "group_reply_cooldown": 5,
    "enable_group_tools": true,
    "group_disabled_tools": [
      "ai_draw_one"
    ]
  }
}
```

**说明**:
- 智能模式：平衡活跃度和打扰
- 禁用 AI 绘图：避免群聊刷屏
- 5 秒冷却：防止重复回复

### 针对不同场景的配置

| 场景 | group_reply_mode | group_reply_cooldown | group_disabled_tools |
|------|----------------|---------------------|---------------------|
| 小型群（< 50 人） | `all` | 3 秒 | `[]` |
| 中型群（50-200 人） | `intelligent` | 5 秒 | `["ai_draw_one"]` |
| 大型群（> 200 人） | `at_only` | 10 秒 | `["ai_draw_one", "music_global_search"]` |
| 工作群 | `intelligent` | 10 秒 | `["bilibili_search", "novel_search"]` |
| 娱乐群 | `all` | 3 秒 | `[]` |

---

## ❓ 常见问题

### Q1: 机器人不回复群消息？

**可能原因**:
1. `enable_group_reply` 设置为 `false`
2. 群 ID 在 `group_blacklist` 中
3. `group_reply_mode` 为 `at_only`，但消息未 @ 机器人
4. `group_reply_mode` 为 `intelligent`，但消息不包含 `group_reply_keywords`

**解决方法**:
1. 检查配置是否正确
2. 查看日志确认消息是否被接收
3. 调整配置为更宽松的设置

### Q2: 机器人回复太频繁？

**可能原因**:
- `group_reply_cooldown` 太小
- `group_reply_mode` 设置为 `all`

**解决方法**:
1. 增加 `group_reply_cooldown` 到 5-10 秒
2. 改为 `intelligent` 或 `at_only` 模式

### Q3: 如何获取群 ID？

**方法 1**: 在群中发送 `/状态` 命令，查看日志中的 group_id

**方法 2**: 使用 NapCat 的 API 获取群列表

**方法 3**: 查看 NapCat 日志中的群消息记录

### Q4: 群聊工具为什么不生效？

**可能原因**:
1. `enable_group_tools` 设置为 `false`
2. 工具在 `group_disabled_tools` 列表中

**解决方法**:
1. 检查配置
2. 从 `group_disabled_tools` 中移除不需要禁用的工具

---

## 📝 代码修改建议

如果需要实现上述配置，需要在 `message_listener.py` 中添加以下逻辑：

```python
# 在 handle_qq_message 方法中添加群聊控制逻辑
async def handle_qq_message(self, message_type: str, data: Dict[str, Any]):
    # ... 现有代码 ...
    
    if message_type == "group":
        # 检查是否启用群聊回复
        if not self.qq_config.get("enable_group_reply", True):
            logger.info("群聊回复已禁用，跳过处理")
            return
        
        # 检查群黑名单
        group_blacklist = self.qq_config.get("group_blacklist", [])
        if group_id in group_blacklist:
            logger.info(f"群 {group_id} 在黑名单中，跳过处理")
            return
        
        # 检查群白名单
        group_whitelist = self.qq_config.get("group_whitelist", [])
        if group_whitelist and group_id not in group_whitelist:
            logger.info(f"群 {group_id} 不在白名单中，跳过处理")
            return
        
        # 检查回复模式
        reply_mode = self.qq_config.get("group_reply_mode", "intelligent")
        
        # at_only 模式：只回复 @ 机器人的消息
        if reply_mode == "at_only":
            if "[CQ:at,qq=" not in message:
                logger.info("at_only 模式，消息未 @ 机器人，跳过处理")
                return
        
        # intelligent 模式：检查关键词
        if reply_mode == "intelligent":
            keywords = self.qq_config.get("group_reply_keywords", [])
            if keywords and not any(keyword in message for keyword in keywords):
                logger.info("intelligent 模式，消息不包含关键词，跳过处理")
                return
        
        # 检查冷却时间
        # ... 添加冷却时间检查逻辑 ...
        
        # 检查工具限制
        # ... 添加工具限制逻辑 ...
    
    # ... 继续处理消息 ...
```

---

## 📄 总结

### 已完成的优化

✅ **MCP 超时优化**: 从 30 秒增加到 120 秒

### 建议添加的配置项

⚠️ **群聊回复控制配置**（需要代码修改）:
- `enable_group_reply`: 是否启用群聊自动回复
- `group_reply_mode`: 群聊回复模式（all/intelligent/at_only/none）
- `group_whitelist`: 群聊白名单
- `group_blacklist`: 群聊黑名单
- `group_reply_keywords`: 群聊回复触发关键词
- `group_reply_cooldown`: 群聊回复冷却时间
- `enable_group_tools`: 是否在群聊中启用工具调用
- `group_disabled_tools`: 群聊中禁用的工具列表

### 关于 Undefined 工具箱的群聊管理功能

Undefined 工具箱专注于在线功能和文件操作，不包含 QQ 群管理功能。如果需要群聊管理功能（禁言、踢人、设置管理员等），建议：

1. **方案 A**: 在 `message_listener.py` 中直接添加群聊管理指令
2. **方案 B**: 创建新的 MCP 服务专门处理群聊管理
3. **方案 C**: 使用 NapCat 提供的 API 直接调用群管理功能

---

**文档版本**: 1.0  
**更新日期**: 2026-01-20  
**适用版本**: NagaAgent Modified v4.1.0+
