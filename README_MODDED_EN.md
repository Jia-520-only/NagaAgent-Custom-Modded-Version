# NagaAgent Custom Modded Version 🐉

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com)

## Introduction

**NagaAgent Custom Modded Version** is a deeply customized AI agent system based on the original NagaAgent, integrating multiple advanced features including consciousness engine, multi-platform chat, QQ/WeChat bots, voice interaction, AI drawing, and intelligent memory.

### Key Features

- 🧠 **Consciousness Engine**: Multi-layer consciousness engine simulating real conversation thinking process
- 💬 **Multi-platform Chat**: Web interface, desktop client, QQ/WeChat bots
- 🎤 **Voice Interaction**: Real-time voice input/output, supporting multiple TTS engines (GPT-SoVITS, Genie TTS)
- 🎨 **AI Drawing**: Online (Zhipu CogView) and local (Stable Diffusion) drawing
- 🧩 **MCP Tool System**: Model Context Protocol tool calling architecture
- 💾 **GRAG Memory System**: Neo4j-based knowledge graph memory (Graph Retrieval Augmented Generation)
- 🤖 **Agency Engine**: Automatic task planning and execution, supporting complex multi-step reasoning
- 🌤️ **Active Communication**: Intelligent topic generation and context-based active dialogue
- 🎮 **Game Guide Engine**: Game strategy generation and real-time guidance
- 🌐 **Online Search**: Integrated SearXNG search engine
- 🖥️ **Computer Control**: Vision model-based screen analysis and automation

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Windows / Linux / macOS
- Neo4j 4.4+ (for memory system, optional)

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd NagaAgent-main
```

2. **Install dependencies**

**Windows:**
```bash
setup.bat
```

**Linux/macOS:**
```bash
bash setup.sh
```

Or manually:
```bash
pip install -r requirements.txt
```

3. **Configure the system**

```bash
cp config.json.example config.json
```

Edit `config.json`:

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

4. **Start Neo4j (optional)**

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  neo4j:5.15
```

5. **Launch the system**

**Windows:**
```bash
start.bat
```

**Linux/macOS:**
```bash
bash start.sh
```

Or:
```bash
python main.py
```

### Access the Interface

- **Web Interface**: http://127.0.0.1:8000
- **API Documentation**: http://127.0.0.1:8000/docs
- **Desktop Client**: PyQt5 window launches automatically

## Project Structure

```
NagaAgent-main/
├── main.py                 # Main entry point
├── config.json             # Configuration file
├── config.json.example     # Configuration template
├── requirements.txt        # Python dependencies
├── agentserver/           # Agent service layer
├── apiserver/            # API service layer
├── mcpserver/            # MCP service layer
│   ├── agent_qq_wechat/   # QQ/WeChat bot agent
│   ├── agent_baodou/      # BaodouAI vision automation agent
│   ├── agent_betta_fish/  # BettaFish sentiment analysis agent
│   └── agent_vcp/         # VCPToolBox memory agent
├── system/               # System core
│   ├── consciousness_engine.py  # Consciousness engine
│   ├── agency_engine.py   # Agency engine
│   ├── semantic_analyzer.py     # Semantic analyzer
│   └── active_communication.py   # Active communication
├── ui/                   # User interface (PyQt5)
├── voice/                # Voice processing
├── summer_memory/        # GRAG memory system
├── external/             # External integrations
├── game/                 # Game system
├── scripts/              # Utility scripts
└── docs/                 # Documentation
```

## Configuration

### Core Configuration

| Section | Purpose | Required |
|---------|---------|----------|
| `api` | LLM API configuration (key, model, parameters) | **Yes** |
| `grag` | GRAG memory system (Neo4j connection) | No |
| `tts` | TTS voice configuration | No |
| `qq_wechat` | QQ/WeChat bot configuration | No |
| `online_ai_draw` | Online AI drawing configuration | No |
| `local_ai_draw` | Local AI drawing configuration | No |
| `active_communication` | Active communication settings | No |

### Supported LLM Providers

- DeepSeek (default)
- OpenAI (GPT-3.5/4)
- Zhipu AI (GLM-4)
- Alibaba Cloud (Qwen)
- Tencent Cloud (Hunyuan)

### TTS Engines

1. **GPT-SoVITS** (Recommended, high quality)
2. **Genie TTS**
3. **VITS**

### QQ Bot Configuration

Requires [NapCat-Go](https://github.com/NapNeko/NapCatQQ) or other QQ bot framework:

```json
{
  "qq_wechat": {
    "qq": {
      "enabled": true,
      "adapter": "napcat-go",
      "ws_url": "ws://127.0.0.1:3001",
      "http_url": "http://127.0.0.1:3000",
      "bot_qq": "your-bot-qq-number"
    }
  }
}
```

## Core Features

### 1. Consciousness Engine

Multi-layer consciousness engine simulating real conversation thinking process.

**Consciousness Layers:**
- **Perception Layer**: Receive input information
- **Understanding Layer**: Deep semantic understanding
- **Thinking Layer**: Logical reasoning and decision making
- **Expression Layer**: Generate natural language responses

**Modes:**
- `simple`: Fast response
- `hybrid`: Balanced performance and quality
- `advanced`: Deep thinking

### 2. Agency Engine

Automatic task planning and execution supporting complex multi-step tasks.

**Workflow:**
1. Task reception
2. Task decomposition
3. Tool selection
4. Execution coordination
5. Result integration
6. Response generation

### 3. GRAG Memory System

Neo4j-based knowledge graph memory system supporting long-term memory and context retrieval.

**Data Structure:**
Quintuple format: Subject - Predicate - Object - Time - Context

### 4. Active Communication System

Intelligent topic generation and context-based active dialogue.

**Features:**
- Context awareness
- Topic generation
- Frequency regulation
- Opportunity evaluation

### 5. MCP Tool System

Model Context Protocol tool calling architecture supporting flexible tool extensions.

**Built-in Tools:**
- QQ/WeChat Bot
- Online Search
- AI Drawing (Online/Local)
- Vision Analysis
- App Launcher
- Browser Automation
- Memory Management
- BaodouAI
- BettaFish

### 6. Voice Interaction System

Real-time voice input and multiple TTS engine support.

## API Documentation

### Health Check

```http
GET http://127.0.0.1:8000/health
```

### Chat Interface

```http
POST http://127.0.0.1:8000/api/v1/chat
Content-Type: application/json

{
  "message": "Hello",
  "user_id": "user123",
  "stream": true
}
```

### Tool Execution

```http
POST http://127.0.0.1:8000/api/v1/tools/execute
Content-Type: application/json

{
  "tool_name": "search",
  "parameters": {
    "query": "Python tutorial"
  }
}
```

Full API documentation: http://127.0.0.1:8000/docs

## Troubleshooting

### Port Already in Use

Change port in `config.json`:

```json
{
  "api_server": {
    "port": 8001
  }
}
```

### Neo4j Connection Failed

- Check if Neo4j is running: `docker ps | grep neo4j`
- Verify password configuration
- Check firewall settings

### TTS No Sound

- Check if TTS service is running
- Verify URL configuration
- Check logs: `logs/tts_error.log`

### QQ Bot Not Responding

- Check if NapCat-Go is running
- Verify WebSocket connection
- Confirm token configuration

## Development

### Adding Custom MCP Tools

1. Create new agent directory in `mcpserver/`
2. Implement tool logic
3. Register in `config.json`

See documentation for detailed guide.

### Custom Prompts

Modify prompts in `system/prompts/`:
- `consciousness_prompt.txt`: Consciousness system
- `conversation_style_prompt.txt`: Conversation style
- `agency_prompt.txt`: Agency system

## Contributing

1. Fork the project
2. Create feature branch: `git checkout -b feature/AmazingFeature`
3. Commit changes: `git commit -m 'Add some AmazingFeature'`
4. Push to branch: `git push origin feature/AmazingFeature`
5. Open Pull Request

## License

This project is based on the original NagaAgent and follows the MIT License.

## Acknowledgments

This project is built upon several excellent open source projects. We would like to thank the authors and contributors of the following projects:

### Core Projects
- [Original NagaAgent](https://github.com/Xxiii8322766509/NagaAgent) - Provided an excellent AI agent system foundation
- [NagaAgent Core](https://github.com/nagaagent/nagaagent-core) - NagaAgent core library

### Integrated Sub-Projects

#### 1. Baodou AI
- [Baodou AI](https://github.com/mini-yifan/baodou_AI) - AI intelligent control system based on Doubao vision model for screen analysis and automation

#### 2. Sentiment Analysis (BettaFish)
- [Weibo Public Opinion Analysis System](https://github.com/666ghj/Weibo_PublicOpinion_AnalysisSystem) - Multi-agent sentiment analysis system supporting 30+ mainstream social media platforms
- [Deep Search Agent Demo](https://github.com/666ghj/DeepSearchAgent-Demo) - Deep search agent demo

#### 3. MCP Servers
- [Office-Word-MCP-Server](https://github.com/GongRzhe/Office-Word-MCP-Server) - Word document processing MCP server

#### 4. Comic Download
- [JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python) - JM comic crawler
- [plugin-jm-server](https://github.com/hect0x7/plugin-jm-server) - JM plugin server

#### 5. Memory System Tools
- [VCPToolBox](https://github.com/cherry-vip/VCPToolBox) - VCP toolbox memory system

#### 6. QQ/WeChat Bots
- [NapCat QQ](https://github.com/NapNeko/NapCatQQ) - Modern QQ bot framework based on OneBot standard
- [Undefined QQbot](https://github.com/69gg/Undefined.git) - QQbot framework integration

### Text-to-Speech (TTS)
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) - High-quality speech synthesis engine with few-shot cloning
- [Genie-TTS](https://github.com/GeneZC/Genie-TTS) - General TTS service
- [VITS](https://github.com/jaywalnut310/vits) - End-to-end speech synthesis model
- [Edge-TTS](https://github.com/rany2/edge-tts) - Microsoft Edge online TTS

### Browser Automation
- [Playwright](https://github.com/microsoft/playwright-python) - Modern browser automation tool
- [crawl4ai](https://github.com/unclecode/crawl4ai) - Intelligent web scraping tool

### Computer Vision
- [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) - OCR text recognition engine
- [OpenCV](https://github.com/opencv/opencv) - Computer vision library

### Python Libraries and Frameworks
- [FastAPI](https://github.com/tiangolo/fastapi) - Modern, high-performance Python web framework
- [PyQt5](https://github.com/pyqt/pyqt5) - Powerful Python GUI framework
- [Pydantic](https://github.com/pydantic/pydantic) - Data validation and settings management
- [LangChain](https://github.com/langchain-ai/langchain) - LLM application development framework
- [Transformers](https://github.com/huggingface/transformers) - Hugging Face Transformers library
- [OpenAI](https://github.com/openai/openai-python) - OpenAI Python SDK
- [LiteLLM](https://github.com/BerriAI/litellm) - Unified LLM API interface

### Databases
- [Neo4j](https://github.com/neo4j/neo4j) - Graph database for knowledge graph storage
- [py2neo](https://github.com/neo4j-contrib/py2neo) - Neo4j Python client library

### Async and Concurrency
- [aiohttp](https://github.com/aio-libs/aiohttp) - Asynchronous HTTP client/server
- [httpx](https://github.com/encode/httpx) - Modern HTTP client
- [websockets](https://github.com/python-websockets/websockets) - WebSocket library
- [uvicorn](https://github.com/encode/uvicorn) - ASGI server

### Audio Processing
- [librosa](https://github.com/librosa/librosa) - Audio analysis library
- [sounddevice](https://github.com/spatialaudio/python-sounddevice) - Audio device interface
- [pydub](https://github.com/jiaaro/pydub) - Audio processing library

### Image Processing
- [Pillow](https://github.com/python-pillow/Pillow) - Python image processing library
- [numpy](https://github.com/numpy/numpy) - Scientific computing base library

### Automation Tools
- [PyAutoGUI](https://github.com/asweigart/pyautogui) - GUI automation library
- [MSS](https://github.com/BoboTiG/python-mss) - Ultra-fast screen capture library

### Bot Tools
- [itchat](https://github.com/YoungGer/itchat) - WeChat personal account interface
- [bilibili-api](https://github.com/Nemo2011/bilibili-api) - Bilibili API library
- [paho-mqtt](https://github.com/eclipse/paho.mqtt.python) - MQTT client library

### GUI and Interface
- [Live2D](https://github.com/Live2D/Live2D-SDK) - Live2D virtual avatar
- [live2d-py](https://github.com/guyskk/live2d-py) - Live2D Python binding
- [pystray](https://github.com/moses-palmer/pystray) - System tray library
- [Pygame](https://github.com/pygame/pygame) - Game development library
- [PyOpenGL](https://github.com/mcfletch/pyopengl) - OpenGL Python binding

### Task Scheduling
- [APScheduler](https://github.com/agronholm/apscheduler) - Advanced Python scheduler
- [gevent](https://github.com/gevent/gevent) - Coroutine library

### Logging and Debugging
- [loguru](https://github.com/Delgan/loguru) - Elegant Python logging library
- [rich](https://github.com/Textualize/rich) - Terminal rich text formatting

### Development Tools
- [pytest](https://github.com/pytest-dev/pytest) - Python testing framework
- [black](https://github.com/psf/black) - Python code formatter
- [mypy](https://github.com/python/mypy) - Python static type checker
- [PyInstaller](https://github.com/pyinstaller/pyinstaller) - Python application packaging tool

### Special Thanks

Thanks to all developers and communities who have contributed to the following projects:
- All maintainers and contributors of open source projects
- Authors who provide technical documentation and tutorials
- Developers who provide help on Stack Overflow, GitHub Issues, and other platforms
- Users who test and provide feedback

This project is built upon the above open source projects and follows their open source licenses. We are committed to giving back to the open source community and welcome anyone to contribute.

---

**Open Source Spirit** - "Standing on the shoulders of giants" 🚀

## More Documentation

- [Quick Start Guide](docs/快速开始.md) (Chinese)
- [Feature Guide](docs/功能指南.md) (Chinese)
- [Troubleshooting Guide](docs/故障排查.md) (Chinese)
- [Consciousness System](docs/初意识系统.md) (Chinese)
- [Agency Implementation](docs/AGENCY_IMPLEMENTATION.md) (Chinese)
- [Memory System](docs/NagaAgent记忆功能完全指南.md) (Chinese)

---

**NagaAgent Custom Modded Version** - Create your own AI intelligent companion 🐉✨
