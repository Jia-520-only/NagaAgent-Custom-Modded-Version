# QQ/微信集成Agent

为NagaAgent提供QQ和微信消息发送能力。

## 功能特性

- ✅ 支持QQ私聊消息
- ✅ 支持QQ群聊消息
- ✅ 支持微信好友消息
- ✅ 支持微信群聊消息
- ✅ 支持查询好友/群列表
- ✅ 支持获取机器人状态

## 安装步骤

### 1. 安装依赖

```bash
cd mcpserver/agent_qq_wechat
pip install -r requirements.txt
```

### 2. QQ配置（使用NapCat-Go）

#### 下载并安装NapCat-Go

NapCat-Go 是一个基于 OneBot 11 协议的QQ机器人框架。

1. 下载 NapCat-Go: https://github.com/NapNeko/NapCatQQ

2. 配置 NapCat-Go：
   - 修改 `config/config.json` 设置你的QQ号
   - 启用正向WebSocket和HTTP API
   - 设置端口（默认WS: 3001, HTTP: 3000）

3. 启动 NapCat-Go:
   ```bash
   ./NapCat-Go.exe  # Windows
   # 或
   ./NapCat-Go     # Linux/macOS
   ```

4. 扫码登录QQ

### 3. 微信配置（使用itchat）

微信集成不需要额外安装软件，直接使用 Python 的 itchat 库。

首次运行时，会显示二维码，用微信扫码登录即可。

### 4. 配置NagaAgent

编辑 `config.json`，添加以下配置：

```json
{
  "qq_wechat": {
    "qq": {
      "enabled": true,
      "adapter": "napcat-go",
      "ws_url": "ws://127.0.0.1:3001",
      "http_url": "http://127.0.0.1:3000",
      "bot_qq": "你的机器人QQ号",
      "access_token": ""
    },
    "wechat": {
      "enabled": true,
      "auto_login": true,
      "enable_login_qrcode": true
    }
  }
}
```

### 5. 注册Agent

在 `mcpserver/mcp_manager.py` 中注册这个Agent：

```python
from .agent_qq_wechat import AgentQQWeChat

# 在 AgentManager 的 __init__ 中添加
self._agents["agent_qq_wechat"] = AgentQQWeChat()
```

### 6. 初始化Agent

在 `mcpserver/mcp_server.py` 的 `on_startup` 中初始化：

```python
async def on_startup():
    qq_wechat_agent = agent_manager.get_agent("agent_qq_wechat")
    if qq_wechat_agent:
        await qq_wechat_agent.initialize(config.qq_wechat)
```

## 使用方法

### 通过对话调用

在NagaAgent的对话中，直接使用工具调用：

```
帮我给QQ号123456789发送消息："你好，我是AI助手"
```

AI会自动解析并调用工具。

### 通过API调用

```bash
curl -X POST http://127.0.0.1:8003/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "agentType": "mcp",
    "service_name": "agent_qq_wechat",
    "tool_name": "发送QQ消息",
    "user_id": "123456789",
    "message": "你好，我是AI助手"
  }'
```

## 可用工具

| 工具名 | 参数 | 说明 |
|--------|------|------|
| 发送QQ消息 | user_id, message | 发送QQ私聊 |
| 发送QQ群消息 | group_id, message | 发送QQ群聊 |
| 发送微信消息 | friend_name, message | 发送微信好友消息 |
| 发送微信群消息 | chatroom_name, message | 发送微信群聊 |
| 获取QQ状态 | - | 查询QQ连接状态 |
| 获取QQ群列表 | - | 获取所有QQ群 |
| 获取QQ好友列表 | - | 获取所有QQ好友 |
| 获取微信好友列表 | - | 获取所有微信好友 |
| 获取微信群列表 | - | 获取所有微信群 |

## 示例对话

### 示例1：发送QQ消息
```
你: 帮我给QQ号123456789发送消息："你好，在吗？"
AI: 好的，正在发送QQ消息...
AI: ✅ 消息已发送成功！
```

### 示例2：发送微信消息
```
你: 告诉张三："今晚8点开会"
AI: 好的，正在给张三发送微信消息...
AI: ✅ 消息已发送成功！
```

### 示例3：查询好友列表
```
你: 我的QQ好友列表有哪些？
AI: 正在查询QQ好友列表...
AI: 找到了125个好友，包括：
- 测试1 (123456)
- 测试2 (234567)
...
```

## 常见问题

### Q: QQ消息发送失败？
A: 检查以下几点：
1. NapCat-Go是否正常运行
2. config.json中的端口配置是否正确
3. QQ号是否正确
4. QQ机器人是否有发送消息的权限

### Q: 微信登录失败？
A:
1. 确保网络连接正常
2. 扫码后等待几秒
3. 如果频繁失败，可能需要等待一段时间后重试
4. 考虑使用 wechaty 替代 itchat

### Q: 如何避免被风控？
A:
1. 控制发送频率，不要短时间内大量发送
2. 避免发送敏感内容
3. 使用真实的QQ号和微信号
4. 不要频繁登录登出

### Q: 能否接收QQ/微信消息？
A: 当前版本主要支持发送消息。接收功能需要实现消息监听和回传机制，可以在后续版本中添加。

## 技术架构

```
NagaAgent (核心)
    ↓
MCP Server (调度层)
    ↓
agent_qq_wechat (集成层)
    ↓
├── qq_adapter (QQ协议适配)
│   └── NapCat-Go (OneBot 11)
└── wechat_adapter (微信协议适配)
    └── itchat / wechaty
```

## 扩展开发

如需添加新功能，参考以下步骤：

1. 在对应的adapter中添加方法
2. 在 agent_qq_wechat.py 中添加处理函数
3. 在 agent-manifest.json 中注册工具
4. 更新 README.md

## 许可证

MIT License
