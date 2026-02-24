# Undefined MCP Server

将Undefined作为MCP工具集成到NagaAgent，使NagaAgent可以调用Undefined的所有50+工具和6个Agent。

## 功能特性

### Undefined工具集

**信息查询类 (info_agent)**
- `weather_query` - 天气查询
- `get_current_time` - 获取当前时间
- `gold_price` - 黄金价格
- `horoscope` - 星座运势
- `news_tencent` - 腾讯新闻
- `renjian` - 人间日报
- `*hot` - 各类热搜榜（百度、微博、抖音）
- `bilibili_*` - B站搜索、用户信息

**网络搜索类 (web_agent)**
- `web_search` - 网页搜索
- `crawl_webpage` - 网页抓取
- MCP Playwright集成

**文件处理类 (file_analysis_agent)**
- `extract_*` - 提取PDF/Word/Excel/PPT内容
- `analyze_code` - 代码分析
- `analyze_multimodal` - 多模态分析
- `read_file` - 读取文件
- `search_file_content` - 搜索文件

**娱乐类 (entertainment_agent)**
- `ai_draw_one` - AI绘图
- `video_random_recommend` - 视频推荐

**代码交付类 (code_delivery_agent)**
- Docker容器隔离
- Git仓库克隆
- 代码编写验证
- 打包上传

**Naga代码分析 (naga_code_analysis_agent)**
- `read_file` - NagaAgent代码读取
- `glob` - 文件搜索
- `search_file_content` - 内容搜索

**基础工具集**
- `group.*` - 群组管理（成员列表、荣誉信息、文件）
- `messages.*` - 消息管理（发送、转发、获取历史）
- `memory.*` - 记忆管理（增删查改）
- `notices.*` - 公告管理
- `render.*` - 渲染（HTML/LaTeX/Markdown）
- `scheduler.*` - 定时任务

## 安装配置

### 1. 确保Undefined已正确安装

Undefined应该位于项目根目录下的`Undefined/`文件夹中。

### 2. 配置Undefined

复制`Undefined/config.toml.example`为`Undefined/config.toml`并配置：

```toml
[core]
bot_qq = "你的机器人QQ号"
superadmin_qq = "你的管理员QQ号"

[onebot]
ws_url = "ws://127.0.0.1:3001"
token = ""  # NapCat的token（如果有的话）

[models.chat]
api_url = "https://api.deepseek.com/v1"
api_key = "你的API密钥"
model_name = "deepseek-v3.2"
```

### 3. 启动NapCat

确保NapCat正在运行并已登录QQ机器人账号。

### 4. 注册MCP Agent

在`mcpserver/mcp_manager.py`中注册：

```python
from .undefined_mcp_server.agent_undefined_mcp import AgentUndefinedMCP

# 在AgentManager的__init__中添加
self._agents["agent_undefined_mcp"] = AgentUndefinedMCP()
```

### 5. 初始化MCP Agent

在`mcpserver/mcp_server.py`的`on_startup`中：

```python
async def on_startup():
    undefined_mcp_agent = agent_manager.get_agent("agent_undefined_mcp")
    if undefined_mcp_agent:
        await undefined_mcp_agent.initialize({})
```

### 6. 在config.json中启用

```json
{
  "mcpserver": {
    "enabled": true,
    "host": "127.0.0.1",
    "port": 8003,
    "auto_start": true,
    "agent_discovery": true
  }
}
```

## 使用方法

### 通过对话调用

在NagaAgent的对话中，AI会自动识别需要使用的Undefined工具：

```
你: 今天北京的天气怎么样？
AI: 正在查询天气信息...
    [调用 undefined.toolset.weather_query]
AI: 北京今天天气晴，气温15-25度，空气质量良。
```

```
你: 搜索一下AI技术最新动态
AI: 正在搜索信息...
    [调用 undefined.agent.web_agent]
AI: 根据搜索结果，AI技术最新动态包括...
```

```
你: 帮我搜索Python教程文件
AI: 正在搜索文件...
    [调用 undefined.toolset.search_file_content]
AI: 找到以下Python教程文件...
```

### 工具调用格式

所有Undefined工具都通过`undefined.`前缀调用：

- **工具集调用**: `undefined.toolset.<工具集名>`
- **Agent调用**: `undefined.agent.<Agent名>`

示例：
- `undefined.toolset.weather_query` - 天气查询
- `undefined.toolset.bilibili_search` - B站搜索
- `undefined.agent.web_agent` - 网络搜索Agent
- `undefined.agent.file_analysis_agent` - 文件分析Agent

## 配置整合建议

### 保留NagaAgent的配置

以下NagaAgent的特色配置需要保留：

```json
{
  "system": {
    "ai_name": "弥娅",
    "voice_enabled": true,
    "voiceprint_enabled": true,
    "diary_enabled": true
  },
  "tts": {
    "default_engine": "gpt_sovits",
    "gpt_sovits_enabled": true,
    "gpt_sovits_ref_text": "...",
    "gpt_sovits_ref_audio_path": "..."
  },
  "voice_realtime": {
    "enabled": true,
    "auto_play": true
  },
  "baodou_ai": {
    "enabled": true
  },
  "online_ai_draw": {...},
  "local_ai_draw": {...},
  "active_communication": {...}
}
```

### 使用Undefined的QQ通信

可以移除或禁用`qq_wechat`配置，因为Undefined已经处理了QQ通信：

```json
{
  "qq_wechat": {
    "qq": {
      "enabled": false,  // 禁用NagaAgent的QQ集成
      "enable_undefined_tools": false  // 不再需要此配置
    }
  }
}
```

## 架构说明

```
NagaAgent (主体)
    ├── AI对话核心
    ├── 记忆系统 (summer_memory)
    ├── 语音系统 (TTS/ASR)
    ├── 主动交流系统
    └── MCP工具层
        ├── agent_undefined_mcp (Undefined集成)
        │   ├── 50+ 工具
        │   ├── 6个Agent
        │   └── QQ通信层
        ├── 其他MCP工具
        └── NagaAgent自有工具
```

### 消息流程

1. QQ用户发送消息
2. Undefined的OneBot客户端接收消息
3. Undefined转发给NagaAgent
4. NagaAgent调用AI生成响应
5. AI识别需要调用的Undefined工具
6. 通过MCP协议调用Undefined工具
7. 返回结果给用户

### 优势

- **单一管理入口**: 所有配置集中在NagaAgent
- **功能最大化**: 继承Undefined所有50+工具
- **无缝集成**: 通过MCP协议实现透明调用
- **保持特色**: 保留NagaAgent的语音、记忆等核心功能
- **易于扩展**: 可以继续添加其他MCP工具

## 故障排查

### Undefined无法加载

检查：
1. Undefined路径是否正确
2. Python版本是否为3.11-3.13
3. Undefined依赖是否安装完成

### 工具调用失败

查看日志确认：
1. Undefined配置是否正确
2. NapCat是否正常运行
3. API密钥是否有效

### 配置冲突

如果NagaAgent和Undefined的配置有冲突（如AI模型配置）：
- 优先使用NagaAgent的配置
- Undefined可以使用相同的API配置

## 未来规划

1. **消息监听集成**: 将Undefined的消息监听完全集成到NagaAgent
2. **配置统一化**: 提供配置迁移工具，自动合并配置
3. **WebUI集成**: 将Undefined的WebUI功能集成到NagaAgent
4. **工具优先级**: 定义NagaAgent工具和Undefined工具的调用优先级

## 许可证

MIT License
