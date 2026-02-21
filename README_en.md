# NagaAgent Modified Version

[简体中文](README.md) | [繁體中文](README_tw.md) | [English](README_en.md)

![NagaAgent](https://img.shields.io/badge/NagaAgent-4.1--Modified-purple?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

![UI Preview](ui/img/README.jpg)

---

## 📌 Project Overview

**NagaAgent Modified Version** is a modified version based on the [original NagaAgent](https://github.com/Xxiii8322766509/NagaAgent), focusing on fixing critical issues in QQ/WeChat integration and adding various performance optimizations and feature enhancements.

---

## 🎯 Key Improvements

### 🔧 Critical Bug Fixes

- ✅ **Fixed PC duplicate output** - Resolved UI message duplication through task deduplication cache
- ✅ **Fixed QQ image recognition not following persona** - Ensures image recognition responses match character settings
- ✅ **Fixed message format not responding to commands** - Supports correct text/voice/both mode responses based on commands
- ✅ **Fixed incomplete long text output** - Implemented intelligent segmentation to avoid content truncation
- ✅ **Fixed long text not sending in multiple messages** - Automatic segmented sending to avoid QQ message length limits
- ✅ **Fixed MCP tool parameter mapping error** - Supports multiple parameter sources (param_name → command/app)

### 🚀 New Features

- 📝 **Automatic long text segmentation** - 500 chars/segment with semantic integrity (minimum 100 chars)
- 🎙️ **Automatic long voice segmentation** - 200 chars/segment with intelligent semantic splitting (minimum 50 chars)
- 🧠 **Intelligent Semantic Analyzer** - Automatically determines if tool calling is needed, adjusts output length and style
- 🔀 **Reply mode switching** - Supports text-only / voice-only / combined modes

### ⚡ Performance Optimizations

- 📊 MCP callback timeout: 5s → 30s to prevent LLM generation timeout
- 📊 Task deduplication cache to avoid duplicate UI displays
- 📊 Optimized callback retry mechanism for improved stability

---

## 🛠️ Technical Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  User Interface Layer (UI)                   │
│  PyQt5 GUI  |  Live2D Avatar  |  System Tray  |  Chat UI     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Core Services Layer                         │
│  API :8000  |  Agent :8001  |  MCP :8003  |  TTS :5048     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Business Logic Layer                        │
│  Game Theory  |  GRAG Memory  |  Voice Processing  |  Tools  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Data Storage Layer                          │
│  Neo4j Graph DB  |  File System  |  Memory Cache             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  External Services Layer                     │
│  LLM Providers  |  QQ/WeChat  |  MQTT  |  Web Crawler        │
└─────────────────────────────────────────────────────────────┘
```

### Core Tech Stack

- **Python 3.11** + PyQt5 + FastAPI
- **Neo4j Graph Database** + GRAG Knowledge Graph
- **MCP (Model Context Protocol)** for Tool Calling
- **OpenAI-Compatible API** + Support for multiple LLM providers
- **NapCat** - QQ Bot Framework
- **GPT-SoVITS** - TTS Voice Synthesis Engine

---

## 📦 Quick Start

### System Requirements

- Python 3.11
- Optional: `uv` tool (for faster dependency installation)

### 1. Install Dependencies

#### Using Auto-Install Script

```bash
# Windows
setup.bat

# Linux/macOS
./setup.sh

# Or using Python script
python setup.py
```

#### Manual Installation

```bash
# Without uv
python -m venv .venv

# Linux/macOS
source .venv/bin/activate
# Windows
.\.venv\Scripts\activate

pip install -r requirements.txt

# Using uv
uv sync
```

### 2. Configuration File

Copy and edit configuration file:

```bash
# Copy configuration template
cp config.json.example config.json

# Edit configuration file, fill in your API information
```

#### Basic Configuration

```json
{
  "api": {
    "api_key": "your_api_key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4"
  },
  "api_server": {
    "enabled": true,
    "host": "0.0.0.0",
    "port": 8000,
    "auto_start": true
  }
}
```

#### QQ/WeChat Integration Configuration

```json
{
  "qq": {
    "enabled": true,
    "bot_qq": "your_bot_qq_number",
    "http_url": "http://127.0.0.1:3000",
    "http_token": "",
    "enable_undefined_tools": true,
    "enable_voice": true,
    "reply_mode": "both"
  }
}
```

#### Optional: Neo4j Knowledge Graph

```json
{
  "grag": {
    "enabled": true,
    "neo4j_uri": "neo4j://127.0.0.1:7687",
    "neo4j_user": "neo4j",
    "neo4j_password": "your_neo4j_password"
  }
}
```

### 3. Start Application

```bash
# Windows
start.bat

# Linux/macOS
./start.sh

# Or run directly
python main.py
```

---

## 🎯 QQ/WeChat Integration

### QQ Bot

#### Configure NapCat

1. Install and start [NapCat](https://github.com/NapNeko/NapCatQQ)
2. Ensure NapCat runs on `http://127.0.0.1:3000`
3. If using Token, fill in `http_token` in `config.json`

#### QQ Commands

| Command | Function |
|---------|----------|
| `/help` | Show help information |
| `/text` | Switch to text mode |
| `/voice` | Switch to voice mode |
| `/both` | Switch to both mode |
| `/mode` | View current configuration |
| `/tools` | View all available tools |

#### Reply Modes

| Mode | Description |
|------|-------------|
| `text` | Send text only (long text auto-segmented) |
| `voice` | Send voice only (long voice auto-segmented) |
| `both` | Send both voice and text (both auto-segmented) |

### WeChat Bot

WeChat bot uses QR code login. After starting the program, a QR code will be displayed. Scan it with WeChat mobile app.

---

## 🤖 Tool System

### Undefined Tool Set (48 tools)

Provides rich online features including:

- **🔍 Search Query** - Web search, web scraping
- **📊 Hot Lists** - Baidu Hot, Weibo Hot, Douyin Hot
- **🎬 Video Entertainment** - Bilibili search, video recommendations
- **🎵 Music Related** - Music search, lyrics query
- **🌤️ Life Services** - Weather query, time query, horoscope
- **💰 Financial Info** - Gold price query
- **📱 Social Related** - QQ related features
- **📂 File Operations** - Read/write files, search files
- **🛠️ Dev Tools** - Base64, Hash, network testing
- **🤖 AI Assistant** - AI drawing, study helper

### Common Tool Usage Examples

#### Weather Query

```
What's the weather like in Beijing today?
Will it rain in Shanghai tomorrow?
/天气 Guangzhou
```

#### Web Search

```
Search for latest AI advancements
Look up Python tutorial
/搜索 quantum computing
```

#### AI Drawing

```
Draw a cute cat
AI drawing: beach at sunset
/画 cherry blossoms by the sea
```

#### Image Rendering

```
Render this markdown content
/render # Hello World
Render formula: E=mc²
```

---

## 🎤 Voice Features

### Supported TTS Engines

- **Edge-TTS** - Online free TTS
- **GPT-SoVITS** - Local customized TTS (recommended)
- **VITS** - Efficient local TTS

### GPT-SoVITS Configuration

```json
{
  "tts": {
    "default_engine": "gpt_sovits",
    "gpt_sovits_url": "http://127.0.0.1:9880",
    "gpt_sovits_ref_text": "Reference text",
    "gpt_sovits_ref_audio_path": "Reference audio path"
  }
}
```

### Start GPT-SoVITS

```bash
cd GPT-SoVITS directory
python api_v2.py
```

---

## 📱 Mobile Access

### Configuration Steps

1. Ensure `api_server.host` in `config.json` is `"0.0.0.0"`
2. Configure firewall to allow port 8000
3. Get computer IP: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)
4. Access from mobile browser: `http://your_computer_IP:8000`

### Features

- ✅ Responsive design, perfect for phones and tablets
- ✅ Streaming conversation support
- ✅ Conversation history memory
- ✅ Markdown formatting
- ✅ PWA support (can be added to home screen)

---

## 🔧 Intelligent Semantic Analysis

### Feature Description

The system automatically analyzes the semantic meaning of user messages and intelligently determines:

- **Whether tool calling is needed** - Avoid triggering tools during casual chat
- **Output length** - Automatically choose short/long/normal length based on content
- **Reply style** - Intelligently select concise/detailed/emotional/helpful style

### Semantic Analysis Examples

```
User: Hello
Analysis: No tool needed, use short text + warm style

User: What's the weather like today?
Analysis: Need to call weather tool, use normal length + detailed style

User: Help me search for AI
Analysis: Need to call search tool, use normal length + helpful style
```

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. Python Version Incompatible

**Problem**: Python version error提示

**Solution**: Ensure using Python 3.11

```bash
python --version
```

#### 2. Port Already in Use

**Problem**: Port occupied提示 at startup

**Solution**: Check if ports 8000, 8001, 8003, 5048 are available

```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

#### 3. QQ Connection Failed (HTTP 403)

**Problem**: QQ bot cannot connect

**Solution**:
1. Clear `http_token` and `ws_token` in `config.json`
2. Ensure NapCat is running
3. Check if NapCat configuration matches

#### 4. GPT-SoVITS Connection Failed (HTTP 404)

**Problem**: Voice features not working

**Solution**:
1. Start GPT-SoVITS service: `python api_v2.py`
2. Ensure port 9880 is not occupied
3. Test connection: `curl http://127.0.0.1:9880/`

#### 5. Mobile Access Failed

**Problem**: Cannot access web interface from mobile

**Solution**:
1. Ensure `api_server.host` is `"0.0.0.0"`
2. Configure firewall to allow port 8000
3. Ensure mobile and computer are on the same Wi-Fi network

#### 6. Neo4j Connection Failed

**Problem**: Knowledge graph not working

**Solution**:
1. Ensure Neo4j service is running
2. Check if connection parameters are correct
3. If always failing, temporarily disable GRAG feature

---

## 📝 Configuration Reference

### Complete Configuration Example

```json
{
  "api": {
    "api_key": "your_api_key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 4000
  },
  "api_server": {
    "enabled": true,
    "host": "0.0.0.0",
    "port": 8000,
    "auto_start": true
  },
  "qq": {
    "enabled": true,
    "bot_qq": "your_bot_qq_number",
    "http_url": "http://127.0.0.1:3000",
    "http_token": "",
    "ws_token": "",
    "enable_undefined_tools": true,
    "enable_voice": true,
    "enable_auto_reply": true,
    "reply_mode": "both"
  },
  "wechat": {
    "enabled": false
  },
  "grag": {
    "enabled": false,
    "neo4j_uri": "neo4j://127.0.0.1:7687",
    "neo4j_user": "neo4j",
    "neo4j_password": "your_password"
  },
  "tts": {
    "default_engine": "gpt_sovits",
    "gpt_sovits_url": "http://127.0.0.1:9880",
    "gpt_sovits_ref_text": "Reference text",
    "gpt_sovits_ref_audio_path": "Reference audio path"
  },
  "online_search": {
    "searxng_url": "https://searxng.pylindex.top"
  },
  "system": {
    "voice_enabled": true,
    "voiceprint_enabled": false,
    "voiceprint_owner_name": "Username"
  },
  "voice_realtime": {
    "enabled": true,
    "voice_mode": "windows",
    "tts_voice": "zh-CN-XiaoyiNeural"
  },
  "live2d": {
    "enabled": false,
    "model_path": "ui/live2d_local/live2d_models/重音テト/重音テト.model3.json",
    "fallback_image": "ui/img/standby.png",
    "auto_switch": true,
    "animation_enabled": true,
    "touch_interaction": true
  }
}
```

---

## 📊 Modified Files List

### Core Modified Files

| File | Modifications |
|------|--------------|
| `mcpserver/agent_qq_wechat/message_listener.py` | Core: long text/voice segmentation, reply mode switching |
| `apiserver/api_server.py` | Task deduplication cache, audio playback optimization, smart parameter mapping |
| `mcpserver/mcp_scheduler.py` | MCP callback timeout adjustment: 5s → 30s |
| `system/semantic_analyzer.py` | New: intelligent semantic analyzer |
| `system/prompts/conversation_analyzer_prompt.txt` | Updated: supports `agentType: "none"` mode |

---

## 📄 License

This project inherits the [MIT License](LICENSE) from the original NagaAgent.

---

## 🙏 Credits

- **Original Project**: [NagaAgent](https://github.com/Xxiii8322766509/NagaAgent)
- **NapCat**: [NapCat QQ](https://github.com/NapNeko/NapCatQQ) - QQ Bot Framework
- **GPT-SoVITS**: [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) - TTS Engine

---

## 🤝 Contributing

Issues and Pull Requests are welcome!

---

## 📮 Changelog

### v4.1.0 Modified (2026-01-19)

#### Core Improvements
- ✅ Fixed PC text and voice duplicate output
- ✅ Fixed QQ image recognition not following persona
- ✅ Fixed QQ message format not responding to commands
- ✅ Fixed incomplete long text output
- ✅ Fixed long text not sending in multiple messages

#### New Features
- ✅ Automatic long text segmentation (500 chars/segment)
- ✅ Automatic long voice segmentation (200 chars/segment)
- ✅ Intelligent semantic splitting
- ✅ Reply mode switching support

#### Performance Optimizations
- ✅ MCP callback timeout: 5s → 30s
- ✅ Task deduplication cache
- ✅ Optimized callback retry mechanism

#### Code Cleanup
- ✅ Deleted 30+ duplicate/obsolete documentation
- ✅ Deleted 16 test files
- ✅ Simplified project structure

---

<div align="center">

**If this project helps you, please give a Star to both the original and this modified version ⭐**

**NagaAgent Modified Version**

Made with ❤️ by the community

</div>
