# NagaAgent Custom Modded Version 🐉

## 项目简介

**NagaAgent Custom Modded Version** 是基于原版 NagaAgent 进行深度魔改的 AI 智能体系统,集成了多种先进功能,包括初意识系统、多端对话、QQ/WeChat 机器人、语音交互、AI 绘图、智能记忆等。

### 核心特性

- 🧠 **初意识系统**: 基于多层次的意识引擎,模拟真实对话思考过程
- 💬 **多端对话**: 支持 Web 界面、桌面客户端、QQ/WeChat 机器人
- 🎤 **语音交互**: 实时语音输入输出,支持多种 TTS 引擎 (GPT-SoVITS、Genie TTS)
- 🎨 **AI 绘图**: 集成在线 (智谱 CogView) 和本地 (Stable Diffusion) 绘图
- 🧩 **MCP 工具系统**: Model Context Protocol 工具调用架构
- 💾 **GRAG 记忆系统**: 基于 Neo4j 的知识图谱记忆 (Graph Retrieval Augmented Generation)
- 🤖 **智能体引擎**: 自动任务规划和执行,支持复杂的多步推理
- 🌤️ **主动交流**: 智能话题生成和基于情境的主动对话
- 🎮 **游戏引导引擎**: 游戏攻略生成和实时指导
- 🌐 **在线搜索**: 集成 SearXNG 搜索引擎
- 🖥️ **计算机控制**: 基于视觉模型的屏幕分析和自动化控制

### 版本信息

- **当前版本**: v5.0.0 Modified
- **Python 版本**: 3.11+
- **主要技术栈**: Python, PyQt5, FastAPI, Neo4j, MCP, WebSocket

---

## 📋 目录结构

```
NagaAgent-main/
├── main.py                 # 主程序入口
├── config.json             # 配置文件
├── config.json.example     # 配置模板
├── requirements.txt        # Python 依赖
├── pyproject.toml         # 项目配置
├── agentserver/           # Agent 服务层
│   ├── agent_server.py    # Agent 服务器
│   ├── agent_manager.py   # Agent 管理器
│   ├── config.py          # Agent 配置
│   ├── task_scheduler.py  # 任务调度器
│   └── tools/             # 工具集
├── apiserver/            # API 服务层
│   ├── api_server.py      # FastAPI 服务器
│   ├── llm_service.py     # LLM 服务
│   ├── message_manager.py # 消息管理器
│   └── static/            # Web 静态文件
├── mcpserver/            # MCP 服务层
│   ├── mcp_server.py      # MCP 服务器
│   ├── mcp_manager.py     # MCP 管理器
│   ├── mcp_scheduler.py   # MCP 调度器
│   ├── agent_qq_wechat/   # QQ/WeChat 机器人 Agent
│   ├── agent_baodou/      # 包豆AI 视觉自动化 Agent
│   ├── agent_betta_fish/  # BettaFish 舆情分析 Agent
│   ├── agent_vcp/         # VCPToolBox 记忆 Agent
│   ├── agent_undefined/   # Undefined QQbot 工具箱
│   ├── agent_online_search/ # 在线搜索 Agent
│   ├── agent_vision/      # 视觉分析 Agent
│   ├── agent_playwright_master/ # 浏览器自动化 Agent
│   ├── agent_open_launcher/     # 应用启动器 Agent
│   └── agent_memory/           # 记忆管理 Agent
├── system/               # 系统核心
│   ├── config.py          # 系统配置
│   ├── consciousness_engine.py  # 初意识引擎
│   ├── agency_engine.py   # 智能体引擎
│   ├── semantic_analyzer.py     # 语义分析器
│   ├── context_analyzer.py      # 上下文分析器
│   ├── active_communication.py   # 主动交流系统
│   ├── conversation_generator.py # 对话生成器
│   ├── topic_generator.py       # 话题生成器
│   ├── task_scheduler.py        # 任务调度器
│   ├── preference_learner.py     # 偏好学习器
│   ├── temporal_perception.py    # 时间感知系统
│   ├── background_analyzer.py    # 后台分析器
│   └── prompts/          # Prompt 模板库
├── ui/                   # 用户界面 (PyQt5)
│   ├── pyqt_chat_window.py # 主窗口
│   ├── components/       # UI 组件
│   ├── controller/       # 控制器
│   ├── styles/           # 样式文件
│   ├── img/              # 图片资源
│   ├── live2d_local/     # Live2D 虚拟形象
│   └── tray/             # 系统托盘
├── voice/                # 语音处理
│   ├── multi_tts_integration.py # 多 TTS 集成
│   ├── gpt_sovits_integration.py # GPT-SoVITS
│   ├── input/            # 语音输入模块
│   └── output/           # 语音输出模块
├── summer_memory/        # GRAG 记忆系统
│   ├── memory_manager.py # 记忆管理器
│   ├── quintuple_graph.py # 五元组图
│   ├── quintuple_extractor.py # 五元组提取器
│   ├── rag_query_tri.py  # 三元组 RAG 查询
│   ├── graph.py          # 图数据库接口
│   ├── autonomous_memory.py     # 自主记忆系统
│   └── docker-compose.yml # Docker 配置
├── external/             # 外部集成
│   └── betta-fish/       # BettaFish 舆情分析系统
├── game/                 # 游戏系统
│   ├── naga_game_system.py # 游戏系统
│   └── core/             # 游戏核心
├── baodou_AI/            # 包豆AI 视觉自动化
├── scripts/              # 脚本工具
│   ├── configure_betta_fish.py  # BettaFish 配置
│   ├── switch_database.py       # 数据库切换
│   └── switch_consciousness.py  # 意识模式切换
├── docs/                 # 完整文档
│   ├── PROJECT_STRUCTURE.md     # 项目结构说明
│   ├── 快速开始.md               # 快速开始指南
│   ├── 功能指南.md               # 功能使用指南
│   ├── 故障排查.md               # 故障排查指南
│   ├── 常见问题.md               # 常见问题解答
│   ├── 初意识系统.md             # 初意识系统说明
│   ├── AGENCY_IMPLEMENTATION.md  # 智能体实现说明
│   ├── CONSCIOUSNESS_ARCHITECTURE.md # 意识架构说明
│   └── NagaAgent记忆功能完全指南.md    # 记忆功能完全指南
└── mqtt_tool/            # MQTT 工具
```

---

## 🚀 快速开始

### 环境要求

- Python 3.11 或更高版本
- Windows / Linux / macOS
- Neo4j 4.4+ (用于记忆系统,可选)

### 安装步骤

#### 1. 克隆项目

```bash
git clone <repository-url>
cd NagaAgent-main
```

#### 2. 安装依赖

**Windows:**
```bash
install.bat
```

**Linux/macOS:**
```bash
./install.sh
```

或手动安装依赖:
```bash
pip install -r requirements.txt
```

#### 3. 配置系统

复制配置模板并编辑:

```bash
cp config.json.example config.json
```

编辑 `config.json` 文件,填写必要的配置:

```json
{
  "api": {
    "api_key": "your-deepseek-api-key",
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat"
  },
  "grag": {
    "neo4j_uri": "neo4j://127.0.0.1:7687",
    "neo4j_user": "neo4j",
    "neo4j_password": "your-neo4j-password"
  }
}
```

#### 4. 启动 Neo4j (可选,用于记忆系统)

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  neo4j:5.15
```

或在本地安装 Neo4j: https://neo4j.com/download/

#### 5. 启动系统

**Windows:**
```bash
start.bat
```

**Linux/macOS:**
```bash
bash start.sh
```

或使用 Python 启动:
```bash
python main.py
```

启动后,系统会自动启动以下服务:
- API Server (http://127.0.0.1:8000)
- Agent Server (http://127.0.0.1:8001)
- MCP Server (http://127.0.0.1:8003)

### 访问界面

- **Web 界面**: http://127.0.0.1:8000
- **API 文档**: http://127.0.0.1:8000/docs
- **桌面客户端**: 自动弹出 PyQt5 窗口

---

## ⚙️ 配置说明

### 核心配置项

| 配置节 | 作用 | 必填 |
|--------|------|------|
| `system` | 系统基础配置 (版本、AI名称、日志等) | 是 |
| `consciousness` | 初意识系统配置 (模式选择) | 否 |
| `api` | LLM API 配置 (密钥、模型、参数) | **是** |
| `api_server` | API 服务器配置 (端口、主机) | 否 |
| `agentserver` | Agent 服务器配置 | 否 |
| `mcpserver` | MCP 服务器配置 | 否 |
| `grag` | GRAG 记忆系统配置 (Neo4j 连接) | 否 |
| `tts` | TTS 语音配置 (支持多引擎) | 否 |
| `voice_realtime` | 实时语音配置 | 否 |
| `qq_wechat` | QQ/WeChat 机器人配置 | 否 |
| `weather` | 天气 API 配置 | 否 |
| `mqtt` | MQTT 物联网配置 | 否 |
| `ui` | UI 配置 | 否 |
| `live2d` | Live2D 虚拟形象配置 | 否 |
| `online_ai_draw` | 在线 AI 绘图配置 | 否 |
| `local_ai_draw` | 本地 AI 绘图配置 | 否 |
| `computer_control` | 计算机控制配置 | 否 |
| `baodou_ai` | 包豆AI 配置 | 否 |
| `guide_engine` | 游戏引导引擎配置 | 否 |
| `memory_server` | 记忆服务器配置 | 否 |
| `embedding` | 嵌入模型配置 | 否 |
| `crawl4ai` | 网页爬虫配置 | 否 |
| `active_communication` | 主动交流配置 | 否 |
| `online_search` | 在线搜索配置 | 否 |

### API 配置示例

```json
{
  "api": {
    "api_key": "sk-your-api-key-here",
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat",
    "temperature": 0.7,
    "max_tokens": 8192,
    "max_history_rounds": 20,
    "persistent_context": true,
    "context_load_days": 3
  }
}
```

支持多种 LLM 提供商:
- DeepSeek (默认)
- OpenAI (GPT-3.5/4)
- 智谱 AI (GLM-4)
- 阿里云 (Qwen)
- 腾讯云 (混元)

### TTS 语音配置

支持多种 TTS 引擎:

1. **GPT-SoVITS** (推荐,高音质)
```json
{
  "tts": {
    "default_engine": "gpt_sovits",
    "gpt_sovits_enabled": true,
    "gpt_sovits_url": "http://127.0.0.1:9880",
    "gpt_sovits_ref_text": "参考文本",
    "gpt_sovits_ref_audio_path": "path/to/reference.wav"
  }
}
```

2. **Genie TTS**
```json
{
  "tts": {
    "default_engine": "genie_tts",
    "genie_tts_enabled": true,
    "genie_tts_url": "http://127.0.0.1:8000"
  }
}
```

3. **VITS**
```json
{
  "tts": {
    "default_engine": "vits",
    "vits_enabled": true,
    "vits_url": "http://127.0.0.1:7860"
  }
}
```

### QQ 机器人配置

需要先安装 [NapCat-Go](https://github.com/NapNeko/NapCatQQ) 或其他 QQ 机器人框架:

```json
{
  "qq_wechat": {
    "qq": {
      "enabled": true,
      "adapter": "napcat-go",
      "ws_url": "ws://127.0.0.1:3001",
      "http_url": "http://127.0.0.1:3000",
      "bot_qq": "your-bot-qq-number",
      "enable_auto_reply": true,
      "reply_mode": "voice",
      "enable_group_reply": true,
      "group_reply_keywords": ["机器人", "AI", "弥娅"]
    }
  }
}
```

### 记忆系统配置

#### 方式 1: Neo4j (推荐)

```json
{
  "grag": {
    "enabled": true,
    "neo4j_uri": "neo4j://127.0.0.1:7687",
    "neo4j_user": "neo4j",
    "neo4j_password": "your-password",
    "similarity_threshold": 0.6,
    "context_length": 5
  }
}
```

#### 方式 2: Docker

```bash
cd summer_memory
docker-compose up -d
```

### AI 绘图配置

#### 在线绘图 (智谱 CogView)

```json
{
  "online_ai_draw": {
    "api_url": "https://open.bigmodel.cn/api/paas/v4",
    "api_key": "your-zhipu-api-key",
    "default_model": "cogview-3",
    "default_size": "1:1",
    "timeout": 120
  }
}
```

#### 本地绘图 (Stable Diffusion)

需要先运行 Stable Diffusion WebUI:

```json
{
  "local_ai_draw": {
    "service_url": "http://127.0.0.1:7860",
    "service_type": "sd_webui",
    "model": "sd1.5anything-v5.safetensors",
    "width": 512,
    "height": 512,
    "steps": 20
  }
}
```

---

## 🎯 核心功能详解

### 1. 初意识系统 (Consciousness Engine)

初意识系统是基于多层次的意识引擎,模拟真实对话思考过程。

#### 意识层结构

- **感知层 (Perception Layer)**: 接收输入信息,进行初步分析
- **理解层 (Understanding Layer)**: 深度语义理解,意图识别
- **思考层 (Thinking Layer)**: 逻辑推理,决策制定
- **表达层 (Expression Layer)**: 生成自然语言回复

#### 运行模式

```json
{
  "consciousness": {
    "enabled": true,
    "mode": "hybrid"
  }
}
```

支持三种模式:
- `simple`: 简单模式,快速响应
- `hybrid`: 混合模式,平衡性能和质量
- `advanced`: 高级模式,深度思考

#### Prompt 自定义

修改 `system/prompts/consciousness_prompt.txt` 自定义意识行为。

### 2. 智能体引擎 (Agency Engine)

智能体引擎支持自动任务规划和执行,可以处理复杂的多步任务。

#### 工作流程

1. **任务接收**: 接收用户任务
2. **任务分解**: 将复杂任务分解为子任务
3. **工具选择**: 自动选择合适的 MCP 工具
4. **执行协调**: 协调多个工具的执行顺序
5. **结果整合**: 整合工具执行结果
6. **回复生成**: 生成最终回复

#### 配置

```json
{
  "handoff": {
    "max_loop_stream": 5,
    "max_loop_non_stream": 5,
    "show_output": false
  }
}
```

### 3. GRAG 记忆系统 (Graph Retrieval Augmented Generation)

基于 Neo4j 的知识图谱记忆系统,支持长期记忆和上下文检索。

#### 五元组数据结构

记忆以五元组形式存储:
- 主体 (Subject)
- 谓词 (Predicate)
- 客体 (Object)
- 时间 (Time)
- 上下文 (Context)

#### 记忆检索

基于相似度的记忆检索:
```json
{
  "grag": {
    "similarity_threshold": 0.6,
    "context_length": 5
  }
}
```

#### 可视化

启动 Neo4j 浏览器访问:
- http://localhost:7474

### 4. 主动交流系统 (Active Communication)

智能话题生成和基于情境的主动对话。

#### 智能模式

```json
{
  "active_communication": {
    "enabled": true,
    "context_aware": true,
    "intelligent_mode": {
      "enabled": true,
      "min_opportunity_score": 0.4,
      "thinking_mode": true,
      "use_context_analyzer": true
    },
    "regulator": {
      "base_interval": 30,
      "min_interval": 10,
      "max_interval": 120
    }
  }
}
```

#### 功能特性

- **情境感知**: 分析当前对话情境
- **话题生成**: 生成相关话题
- **频率调节**: 自动调节主动交流频率
- **机会评估**: 评估主动交流的时机

### 5. MCP 工具系统

MCP (Model Context Protocol) 工具调用架构,支持灵活的工具扩展。

#### 内置工具

| 工具名称 | 功能 | 配置路径 |
|----------|------|----------|
| QQ/WeChat 机器人 | QQ/WeChat 消息收发 | `qq_wechat` |
| 在线搜索 | SearXNG 搜索 | `online_search` |
| AI 绘图 | 在线/本地绘图 | `online_ai_draw` / `local_ai_draw` |
| 视觉分析 | 图像理解和分析 | `agent_vision` |
| 应用启动器 | 自动启动应用 | `agent_open_launcher` |
| 浏览器自动化 | Playwright 自动化 | `agent_playwright_master` |
| 记忆管理 | 记忆读写操作 | `agent_memory` |
| 包豆AI | 视觉屏幕分析 | `baodou_ai` |
| BettaFish | 舆情分析 | `external/betta-fish` |

#### 工具优先级

```json
{
  "tool_priority_manager": {
    "search": 1,
    "draw": 2,
    "vision": 3,
    "memory": 4
  }
}
```

### 6. 语音交互系统

支持实时语音输入和多种 TTS 引擎。

#### 实时语音配置

```json
{
  "voice_realtime": {
    "enabled": true,
    "provider": "local",
    "voice": "Cherry",
    "input_sample_rate": 16000,
    "output_sample_rate": 24000,
    "vad_threshold": 0.02,
    "min_user_interval": 2.0,
    "integrate_with_memory": true
  }
}
```

#### TTS 引擎选择

```json
{
  "tts": {
    "default_engine": "gpt_sovits",
    "gpt_sovits_enabled": true,
    "genie_tts_enabled": false,
    "vits_enabled": false
  }
}
```

---

## 📚 API 文档

### 基础端点

#### 健康检查

```http
GET http://127.0.0.1:8000/health
```

#### 对话接口

```http
POST http://127.0.0.1:8000/api/v1/chat
Content-Type: application/json

{
  "message": "你好",
  "user_id": "user123",
  "stream": true
}
```

#### 工具调用

```http
POST http://127.0.0.1:8000/api/v1/tools/execute
Content-Type: application/json

{
  "tool_name": "search",
  "parameters": {
    "query": "Python 教程"
  }
}
```

#### 记忆查询

```http
GET http://127.0.0.1:8000/api/v1/memory/query?query=昨天聊了什么
```

详细 API 文档请访问: http://127.0.0.1:8000/docs

---

## 🔧 高级配置

### Docker 部署

#### 使用 Docker Compose

```yaml
version: '3.8'
services:
  naga-agent:
    build: .
    ports:
      - "8000:8000"
      - "8001:8001"
      - "8003:8003"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_PASSWORD=your-password
    depends_on:
      - neo4j
      - redis

  neo4j:
    image: neo4j:5.15
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/your-password

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

启动:
```bash
docker-compose up -d
```

### 意识模式切换

使用脚本快速切换意识模式:

```bash
python scripts/switch_consciousness.py --mode advanced
```

### 数据库模式切换

```bash
python scripts/switch_database.py --mode neo4j
```

---

## 🎨 自定义开发

### 添加自定义 MCP 工具

1. 在 `mcpserver/` 下创建新的 Agent 目录:

```bash
mkdir mcpserver/agent_my_tool
cd mcpserver/agent_my_tool
```

2. 创建 `__init__.py`:

```python
from .my_tool import MyToolAgent

def register():
    return MyToolAgent
```

3. 实现工具逻辑 `my_tool.py`:

```python
from typing import Dict, Any

class MyToolAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def execute(self, parameters: Dict[str, Any]) -> str:
        # 实现工具逻辑
        return "执行结果"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "my_tool",
            "description": "工具描述",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
```

4. 在 `config.json` 中配置:

```json
{
  "my_tool": {
    "enabled": true,
    "custom_param": "value"
  }
}
```

### 自定义 Prompt

修改 `system/prompts/` 下的 Prompt 文件:
- `consciousness_prompt.txt`: 意识系统 Prompt
- `conversation_style_prompt.txt`: 对话风格 Prompt
- `conversation_analyzer_prompt.txt`: 对话分析器 Prompt
- `agency_prompt.txt`: 智能体 Prompt

### 自定义 UI 组件

在 `ui/components/` 下创建新组件:

```python
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal

class MyComponent(QWidget):
    data_received = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        # 添加 UI 元素
        self.setLayout(layout)
```

---

## 🐛 故障排查

### 常见问题

#### 1. 端口被占用

```
Error: Port 8000 is already in use
```

**解决方案**: 修改 `config.json` 中的端口配置:

```json
{
  "api_server": {
    "port": 8001
  }
}
```

#### 2. Neo4j 连接失败

```
Failed to connect to Neo4j at bolt://127.0.0.1:7687
```

**解决方案**:
- 检查 Neo4j 是否运行: `docker ps | grep neo4j`
- 验证密码配置
- 确认防火墙设置

#### 3. TTS 无声音

```
TTS error: Connection refused
```

**解决方案**:
- 检查 TTS 服务是否运行
- 验证 URL 配置
- 查看详细日志: `logs/tts_error.log`

#### 4. QQ 机器人无响应

**解决方案**:
- 检查 NapCat-Go 是否运行
- 验证 WebSocket 连接: `ws://127.0.0.1:3001`
- 确认 token 配置正确

### 调试模式

启用调试日志:

```json
{
  "system": {
    "debug": true,
    "log_level": "DEBUG"
  }
}
```

查看日志:
- 系统日志: `logs/naga.log`
- API 日志: `logs/api.log`
- MCP 日志: `logs/mcp.log`

---

## 📈 性能优化

### 内存优化

```json
{
  "api": {
    "max_history_rounds": 10,
    "context_load_days": 1
  }
}
```

### 响应速度优化

```json
{
  "consciousness": {
    "mode": "simple"
  },
  "handoff": {
    "max_loop_stream": 3
  }
}
```

### 并发控制

```json
{
  "api_server": {
    "max_concurrent_requests": 10
  }
}
```

---

## 🤝 贡献指南

### 开发环境设置

1. Fork 项目
2. 创建特性分支: `git checkout -b feature/AmazingFeature`
3. 提交更改: `git commit -m 'Add some AmazingFeature'`
4. 推送到分支: `git push origin feature/AmazingFeature`
5. 开启 Pull Request

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 使用类型注解
- 添加文档字符串
- 编写单元测试

### 提交规范

- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- style: 代码格式调整
- refactor: 重构
- test: 测试相关
- chore: 构建/工具相关

---

## 📄 许可证

本项目基于原版 NagaAgent 进行魔改,遵循 MIT 许可证。

---

## 🙏 致谢

本项目基于多个优秀的开源项目构建,感谢以下项目的作者和贡献者:

### 核心项目
- [原版 NagaAgent](https://github.com/Xxiii8322766509/NagaAgent) - 提供了优秀的 AI 智能体系统基础架构
- [NagaAgent Core](https://github.com/nagaagent/nagaagent-core) - NagaAgent 核心库

### 集成的子项目

#### 1. 包豆AI (Baodou AI)
- [Baodou AI](https://github.com/mini-yifan/baodou_AI) - 基于豆包视觉模型的智能控制系统,实现屏幕分析和自动化操作

#### 2. 舆情分析系统 (BettaFish)
- [Weibo Public Opinion Analysis System](https://github.com/666ghj/Weibo_PublicOpinion_AnalysisSystem) - 多智能体舆情分析系统,支持国内外30+主流社媒分析
- [Deep Search Agent Demo](https://github.com/666ghj/DeepSearchAgent-Demo) - 深度搜索 Agent 演示

#### 3. MCP 服务器
- [Office-Word-MCP-Server](https://github.com/GongRzhe/Office-Word-MCP-Server) - Word 文档处理 MCP 服务

#### 4. 漫画下载
- [JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python) - JM 漫画爬虫
- [plugin-jm-server](https://github.com/hect0x7/plugin-jm-server) - JM 插件服务器

#### 5. 记忆系统工具
- [VCPToolBox](https://github.com/cherry-vip/VCPToolBox) - VCP 工具箱记忆系统

#### 6. QQ/WeChat 机器人
- [NapCat QQ](https://github.com/NapNeko/NapCatQQ) - 现代化的 QQ 机器人框架,基于 OneBot 标准
- [Undefined QQbot](https://github.com/69gg/Undefined.git) - QQbot 框架联动

### 语音合成 (TTS)
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) - 高质量的语音合成引擎,支持少样本克隆
- [Genie-TTS](https://github.com/GeneZC/Genie-TTS) - 通用语音合成服务
- [VITS](https://github.com/jaywalnut310/vits) - 端到端语音合成模型
- [Edge-TTS](https://github.com/rany2/edge-tts) - 微软 Edge 在线语音合成

### 浏览器自动化
- [Playwright](https://github.com/microsoft/playwright-python) - 现代化的浏览器自动化工具
- [crawl4ai](https://github.com/unclecode/crawl4ai) - 智能网页爬虫工具

### 计算机视觉
- [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) - OCR 文字识别引擎
- [OpenCV](https://github.com/opencv/opencv) - 计算机视觉库

### Python 库和框架
- [FastAPI](https://github.com/tiangolo/fastapi) - 现代化、高性能的 Python Web 框架
- [PyQt5](https://github.com/pyqt/pyqt5) - 功能强大的 Python GUI 框架
- [Pydantic](https://github.com/pydantic/pydantic) - 数据验证和设置管理
- [LangChain](https://github.com/langchain-ai/langchain) - LLM 应用开发框架
- [Transformers](https://github.com/huggingface/transformers) - Hugging Face 的 Transformers 库
- [OpenAI](https://github.com/openai/openai-python) - OpenAI Python SDK
- [LiteLLM](https://github.com/BerriAI/litellm) - 统一的 LLM API 接口

### 数据库
- [Neo4j](https://github.com/neo4j/neo4j) - 图数据库,用于知识图谱存储
- [py2neo](https://github.com/neo4j-contrib/py2neo) - Neo4j Python 客户端库

### 异步和并发
- [aiohttp](https://github.com/aio-libs/aiohttp) - 异步 HTTP 客户端/服务器
- [httpx](https://github.com/encode/httpx) - 现代化的 HTTP 客户端
- [websockets](https://github.com/python-websockets/websockets) - WebSocket 库
- [uvicorn](https://github.com/encode/uvicorn) - ASGI 服务器

### 音频处理
- [librosa](https://github.com/librosa/librosa) - 音频分析库
- [sounddevice](https://github.com/spatialaudio/python-sounddevice) - 音频设备接口
- [pydub](https://github.com/jiaaro/pydub) - 音频处理库

### 图像处理
- [Pillow](https://github.com/python-pillow/Pillow) - Python 图像处理库
- [numpy](https://github.com/numpy/numpy) - 科学计算基础库

### 自动化工具
- [PyAutoGUI](https://github.com/asweigart/pyautogui) - GUI 自动化库
- [MSS](https://github.com/BoboTiG/python-mss) - 超快屏幕截图库

### 机器人工具
- [itchat](https://github.com/YoungGer/itchat) - 微信个人号接口
- [bilibili-api](https://github.com/Nemo2011/bilibili-api) - 哔哩哔哩 API 库
- [paho-mqtt](https://github.com/eclipse/paho.mqtt.python) - MQTT 客户端库

### GUI 和界面
- [Live2D](https://github.com/Live2D/Live2D-SDK) - Live2D 虚拟形象
- [live2d-py](https://github.com/guyskk/live2d-py) - Live2D Python 绑定
- [pystray](https://github.com/moses-palmer/pystray) - 系统托盘库
- [Pygame](https://github.com/pygame/pygame) - 游戏开发库
- [PyOpenGL](https://github.com/mcfletch/pyopengl) - OpenGL Python 绑定

### 任务调度
- [APScheduler](https://github.com/agronholm/apscheduler) - 高级 Python 调度器
- [gevent](https://github.com/gevent/gevent) - 协程库

### 日志和调试
- [loguru](https://github.com/Delgan/loguru) - 优雅的 Python 日志库
- [rich](https://github.com/Textualize/rich) - 终端富文本格式化

### 开发工具
- [pytest](https://github.com/pytest-dev/pytest) - Python 测试框架
- [black](https://github.com/psf/black) - Python 代码格式化工具
- [mypy](https://github.com/python/mypy) - Python 静态类型检查
- [PyInstaller](https://github.com/pyinstaller/pyinstaller) - Python 应用打包工具

### 特别感谢

感谢所有为以下项目做出贡献的开发者和社区:
- 所有开源项目的维护者和贡献者
- 提供技术文档和教程的作者
- 在 Stack Overflow、GitHub Issues 等平台提供帮助的开发者
- 测试和反馈的用户

本项目基于上述开源项目构建,遵循各项目的开源协议。我们致力于回馈开源社区,欢迎任何人参与贡献。

---

**开源精神** - "Standing on the shoulders of giants" 🚀

---

## 📞 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [GitHub Issues]
- 讨论区: [GitHub Discussions]

---

## 📖 更多文档

- [快速开始指南](docs/快速开始.md)
- [功能使用指南](docs/功能指南.md)
- [故障排查指南](docs/故障排查.md)
- [常见问题解答](docs/常见问题.md)
- [初意识系统详解](docs/初意识系统.md)
- [智能体实现说明](docs/AGENCY_IMPLEMENTATION.md)
- [意识架构说明](docs/CONSCIOUSNESS_ARCHITECTURE.md)
- [记忆功能完全指南](docs/NagaAgent记忆功能完全指南.md)

---

**NagaAgent Custom Modded Version** - 打造您专属的 AI 智能伴侣 🐉✨
