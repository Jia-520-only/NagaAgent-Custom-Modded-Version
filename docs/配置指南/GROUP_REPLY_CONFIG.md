# QQ 群聊回复控制配置指南

## 📋 概述

NagaAgent 的 QQ 机器人现在支持精细化的群聊回复控制，可以通过配置文件控制机器人在群聊中的回复行为。

## 🔧 配置项说明

在 `config.json` 文件的 `qq_wechat.qq` 配置段中，可以设置以下群聊回复控制选项：

### 1. enable_group_reply
**是否启用群聊自动回复**

```json
"enable_group_reply": true
```

- `true` - 启用群聊回复（根据 `group_reply_mode` 判断）
- `false` - 禁用群聊回复（只回复私聊）

**默认值**: `true`

---

### 2. group_reply_mode
**群聊回复模式**

```json
"group_reply_mode": "at_only"
```

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `all` | 回复所有消息 | 小型群、测试群 |
| `at_only` | 只回复@机器人的消息 | 中大型群（推荐） |
| `intelligent` | 智能判断：@机器人 或 关键词触发时回复 | 中型群、工作群 |
| `none` | 不回复群聊消息 | 大型群、禁言模式 |

**默认值**: `at_only`

**详细说明**：

#### `all` - 全部回复模式
- 回复群中的所有消息
- 适用于小型群（< 50 人）或测试群
- **注意**: 可能会在大群中刷屏

#### `at_only` - @触发模式（推荐）
- 只回复@机器人的消息
- 适用于中大型群（50-200 人）
- **优点**: 避免刷屏，只有明确需要机器人时才会回复

#### `intelligent` - 智能判断模式
- 满足以下任一条件时回复：
  - 消息中@了机器人
  - 消息包含关键词（见 `group_reply_keywords`）
- 适用于中型群、工作群
- **优点**: 平衡自动回复和避免刷屏

#### `none` - 不回复模式
- 不回复任何群聊消息
- 适用于大型群（> 200 人）或需要禁言的群
- **注意**: 此时机器人不会响应群聊

---

### 3. group_whitelist
**群白名单**

```json
"group_whitelist": ["123456789", "987654321"]
```

- 只回复白名单中的群
- 空列表 `[]` 表示不限制（回复所有群）
- 群号以字符串形式存储

**默认值**: `[]`

**使用场景**：
- 只在特定的几个群中启用机器人
- 保护隐私，避免在无关群中回复

**示例**：
```json
"group_whitelist": ["123456789", "987654321"]  // 只在这两个群回复
```

---

### 4. group_blacklist
**群黑名单**

```json
"group_blacklist": ["111111111", "222222222"]
```

- 不回复黑名单中的群
- 优先级高于 `group_whitelist`
- 群号以字符串形式存储

**默认值**: `[]`

**使用场景**：
- 在大部分群启用机器人，但排除特定群
- 禁止机器人回复某些群

**示例**：
```json
"group_blacklist": ["111111111", "222222222"]  // 不在这两个群回复
```

---

### 5. group_reply_keywords
**群聊回复触发关键词**

```json
"group_reply_keywords": ["机器人", "AI", "娜迦", "弥娅"]
```

- 只在 `intelligent` 模式下有效
- 当消息中包含任一关键词时触发回复
- 关键词匹配不区分大小写

**默认值**: `["机器人", "AI", "娜迦", "弥娅"]`

**使用场景**：
- `intelligent` 模式下的关键词触发
- 当有人提到机器人相关话题时自动回复

**示例**：
```json
"group_reply_keywords": ["机器人", "AI", "帮忙", "查询"]
```

---

### 6. group_reply_cooldown
**群聊回复冷却时间（秒）**

```json
"group_reply_cooldown": 5
```

- 同一群中两次回复的最小间隔时间
- 避免机器人频繁回复
- 如果在冷却时间内收到消息，直接跳过

**默认值**: `5` 秒

**使用场景**：
- 控制机器人的回复频率
- 避免在活跃群中刷屏

**建议值**：
- 小型群（< 50 人）: `0-3` 秒
- 中型群（50-200 人）: `5-10` 秒
- 大型群（> 200 人）: `10-30` 秒

---

### 7. enable_group_tools
**是否在群聊中启用工具调用**

```json
"enable_group_tools": false
```

- `true` - 群聊消息会触发工具调用（如天气查询、搜索等）
- `false` - 群聊消息不会触发工具调用（仅生成文本/语音回复）

**默认值**: `false`

**重要提示**：
- ⚠️ 在群聊中启用工具调用可能导致意外行为
- ⚠️ 某些工具（如 `send_message`）可能不适合在群聊中使用
- 建议配合 `group_disabled_tools` 使用

---

### 8. group_disabled_tools
**群聊中禁用的工具列表**

```json
"group_disabled_tools": ["send_message", "send_private_message"]
```

- 在群聊中禁用的工具列表
- 适用于 `enable_group_tools: true` 的情况
- 防止某些不适合群聊的工具被调用

**默认值**: `["send_message", "send_private_message"]`

**常见禁用工具**：
- `send_message` - 发送消息（避免群中刷屏）
- `send_private_message` - 发送私聊（保护隐私）
- `local_ai_draw` - 本地AI绘图（避免消耗资源）

**示例**：
```json
"enable_group_tools": true,
"group_disabled_tools": [
  "send_message",
  "send_private_message",
  "local_ai_draw",
  "ai_draw_one"
]
```

---

## 📊 配置示例

### 示例 1: 默认配置（推荐）

```json
{
  "qq_wechat": {
    "qq": {
      "enable_group_reply": true,
      "group_reply_mode": "at_only",
      "group_whitelist": [],
      "group_blacklist": [],
      "group_reply_keywords": ["机器人", "AI", "娜迦", "弥娅"],
      "group_reply_cooldown": 5,
      "enable_group_tools": false,
      "group_disabled_tools": ["send_message", "send_private_message"]
    }
  }
}
```

**适用场景**: 大部分场景，避免刷屏

---

### 示例 2: 只在特定群回复

```json
{
  "qq_wechat": {
    "qq": {
      "enable_group_reply": true,
      "group_reply_mode": "all",
      "group_whitelist": ["123456789", "987654321"],
      "group_blacklist": [],
      "group_reply_cooldown": 3,
      "enable_group_tools": false,
      "group_disabled_tools": ["send_message"]
    }
  }
}
```

**适用场景**: 只在少数几个群中启用机器人

---

### 示例 3: 智能判断模式

```json
{
  "qq_wechat": {
    "qq": {
      "enable_group_reply": true,
      "group_reply_mode": "intelligent",
      "group_whitelist": [],
      "group_blacklist": ["111111111"],
      "group_reply_keywords": ["机器人", "AI", "帮忙", "查询", "天气"],
      "group_reply_cooldown": 8,
      "enable_group_tools": false,
      "group_disabled_tools": ["send_message", "send_private_message"]
    }
  }
}
```

**适用场景**: 中型群，需要平衡自动回复和避免刷屏

---

### 示例 4: 只回复@机器人（大型群推荐）

```json
{
  "qq_wechat": {
    "qq": {
      "enable_group_reply": true,
      "group_reply_mode": "at_only",
      "group_whitelist": [],
      "group_blacklist": [],
      "group_reply_cooldown": 10,
      "enable_group_tools": false,
      "group_disabled_tools": ["send_message", "send_private_message"]
    }
  }
}
```

**适用场景**: 大型群（> 200 人），避免刷屏

---

### 示例 5: 禁用群聊回复

```json
{
  "qq_wechat": {
    "qq": {
      "enable_group_reply": false,
      "group_reply_mode": "none",
      "group_whitelist": [],
      "group_blacklist": [],
      "group_reply_cooldown": 0,
      "enable_group_tools": false,
      "group_disabled_tools": []
    }
  }
}
```

**适用场景**: 只使用私聊功能，不回复群聊

---

## 🎯 不同场景的推荐配置

### 小型群（< 50 人）

```json
{
  "enable_group_reply": true,
  "group_reply_mode": "all",
  "group_whitelist": [],
  "group_blacklist": [],
  "group_reply_cooldown": 2,
  "enable_group_tools": false,
  "group_disabled_tools": []
}
```

**特点**:
- 回复所有消息
- 冷却时间短
- 适合活跃的小群

---

### 中型群（50-200 人）

```json
{
  "enable_group_reply": true,
  "group_reply_mode": "at_only",
  "group_whitelist": [],
  "group_blacklist": [],
  "group_reply_cooldown": 5,
  "enable_group_tools": false,
  "group_disabled_tools": ["send_message", "send_private_message"]
}
```

**特点**:
- 只回复@机器人
- 适中的冷却时间
- 避免刷屏

---

### 大型群（> 200 人）

```json
{
  "enable_group_reply": true,
  "group_reply_mode": "at_only",
  "group_whitelist": [],
  "group_blacklist": [],
  "group_reply_cooldown": 15,
  "enable_group_tools": false,
  "group_disabled_tools": ["send_message", "send_private_message", "local_ai_draw"]
}
```

**特点**:
- 只回复@机器人
- 较长的冷却时间
- 禁用不适合群聊的工具

---

### 工作群

```json
{
  "enable_group_reply": true,
  "group_reply_mode": "intelligent",
  "group_whitelist": ["123456789"],
  "group_blacklist": [],
  "group_reply_keywords": ["机器人", "AI", "查询", "天气", "时间"],
  "group_reply_cooldown": 10,
  "enable_group_tools": false,
  "group_disabled_tools": ["send_message", "send_private_message"]
}
```

**特点**:
- 智能判断模式
- 白名单限制
- 关键词触发
- 适中的冷却时间

---

### 娱乐群

```json
{
  "enable_group_reply": true,
  "group_reply_mode": "intelligent",
  "group_whitelist": [],
  "group_blacklist": [],
  "group_reply_keywords": ["机器人", "AI", "娜迦", "弥娅", "笑话", "故事"],
  "group_reply_cooldown": 5,
  "enable_group_tools": false,
  "group_disabled_tools": ["send_message", "send_private_message"]
}
```

**特点**:
- 智能判断模式
- 多种娱乐关键词
- 适中的冷却时间

---

## 🔍 日志说明

当群聊消息被过滤时，会在日志中显示：

```
[群聊过滤] 群 813905307 消息不满足回复条件，跳过: 1...
```

常见过滤原因：
- 消息不是@机器人（`at_only` 模式）
- 消息不包含关键词（`intelligent` 模式）
- 群在黑名单中
- 群不在白名单中
- 群聊回复未启用（`enable_group_reply: false`）
- 还在冷却时间内（`group_reply_cooldown`）

---

## ⚠️ 注意事项

1. **群聊回复控制仅对文本消息有效**，图片、语音等消息的回复逻辑不受此控制
2. **白名单和黑名单同时配置时，黑名单优先级更高**
3. **冷却时间是按群计算的**，不同群之间不会相互影响
4. **@机器人检测是通过 `[CQ:at,qq=...]` CQ码实现的**
5. **群聊中启用工具调用需要谨慎**，建议先在私聊中测试

---

## 📝 快速开始

### 步骤 1: 打开配置文件

编辑 `config.json` 文件

### 步骤 2: 找到 QQ 配置段

找到 `qq_wechat.qq` 配置段

### 步骤 3: 修改群聊回复配置

根据你的需求修改以下配置项：

```json
{
  "qq_wechat": {
    "qq": {
      "enable_group_reply": true,
      "group_reply_mode": "at_only",
      "group_whitelist": [],
      "group_blacklist": [],
      "group_reply_keywords": ["机器人", "AI", "娜迦", "弥娅"],
      "group_reply_cooldown": 5,
      "enable_group_tools": false,
      "group_disabled_tools": ["send_message", "send_private_message"]
    }
  }
}
```

### 步骤 4: 保存并重启程序

保存 `config.json` 文件并重启 NagaAgent

### 步骤 5: 测试群聊回复

在群聊中发送消息测试机器人是否按预期回复

---

## 🆘 常见问题

### Q: 为什么机器人在群聊中没有回复？

A: 检查以下几点：
1. `enable_group_reply` 是否为 `true`
2. `group_reply_mode` 是否正确（如 `at_only` 模式需要@机器人）
3. 群是否在 `group_blacklist` 中
4. 群是否不在 `group_whitelist` 中（如果配置了白名单）
5. 是否还在冷却时间内
6. 查看日志中的 `[群聊过滤]` 提示

### Q: 如何让机器人在所有群中都回复？

A: 使用以下配置：

```json
{
  "enable_group_reply": true,
  "group_reply_mode": "all",
  "group_whitelist": [],
  "group_blacklist": [],
  "group_reply_cooldown": 3
}
```

### Q: 如何让机器人只在特定群中回复？

A: 配置白名单：

```json
{
  "enable_group_reply": true,
  "group_reply_mode": "all",
  "group_whitelist": ["123456789", "987654321"],
  "group_blacklist": []
}
```

### Q: 如何禁止机器人在特定群中回复？

A: 配置黑名单：

```json
{
  "enable_group_reply": true,
  "group_reply_mode": "all",
  "group_whitelist": [],
  "group_blacklist": ["111111111", "222222222"]
}
```

### Q: 如何让机器人只在@时回复？

A: 使用 `at_only` 模式：

```json
{
  "enable_group_reply": true,
  "group_reply_mode": "at_only"
}
```

### Q: 如何让机器人智能判断是否回复？

A: 使用 `intelligent` 模式并配置关键词：

```json
{
  "enable_group_reply": true,
  "group_reply_mode": "intelligent",
  "group_reply_keywords": ["机器人", "AI", "帮忙", "查询"]
}
```

---

## 📚 更多信息

- [主 README](README.md)
- [QQ_GROUP_CONFIG_GUIDE.md](QQ_GROUP_CONFIG_GUIDE.md)
- [问题排查指南](README.md#🛠️-故障排查)
