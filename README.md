# Naga Agent Custom Modded Version

[简体中文](README.md) | [繁體中文](README_tw.md) | [English](README_en.md)

![NagaAgent](https://img.shields.io/badge/NagaAgent-4.1--Modified-purple?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

![UI Preview](ui/img/README.jpg)

---

## 📌 项目简介

**Naga Agent Custom Modded Version** 是基于 [原版 NagaAgent](https://github.com/Xxiii8322766509/NagaAgent) 的自定义魔改版本，专注于修复 QQ/WeChat 集成中的关键问题，并进行了多项性能优化和功能增强。

NagaAgent自定义魔改版。原型来自柏斯阔落大佬的NagaAgent，这是我用腾讯云编程助手改版的。加装了基于NapCat框架的 QQbot的功能，可以调用NagaAgent的子项目Undefined的QQbot工具箱，QQbot的相关配置都可以在Undefined更改（只需要把Undefined项目复制粘贴进Naga的根目录就可以了）。它还可以调用GPT-SoVITS的本地TTS。QQ可以发图片，语音（GPT-SoVITS模型），云端绘图和本地绘图（自定义模型）。
QQbot的思考逻辑依赖Naga agent，QQ端的数据与电脑端互通，可以说是Naga agent程序在QQ上有了一个交互界面。在QQ上输入的命令，也可以调用电脑端的MCP。有一些别的功能，大家可以自己探索，因为我也忘了。

---

## 🎯 核心功能

### 🌟 初意识系统
- 弥娅的原生意识（灵魂）
- 基于记忆和人生书独立思考
- 将大模型作为工具调用
- 三种模式：混合/本地/AI

### ✨ 对话与交互
- 多端对话支持（PC、网页、移动端）
- PyQt5 图形界面
- Live2D 虚拟形象
- 实时语音交互

### 🤖 聊天集成
- QQ 机器人（NapCat 框架）
- 微信机器人
- 群聊智能回复
- 图片识别与表情包支持

### 🎤 语音功能
- GPT-SoVITS 本地 TTS（推荐）
- Edge-TTS 在线 TTS
- VITS 高效 TTS
- 自动分段语音生成

### 🎨 AI 绘图
- 云端 AI 绘图
- 本地模型绘图
- 支持自定义风格

### 🧠 智能记忆
- GRAG 知识图谱
- Neo4j 图数据库
- VCPToolBox 高级记忆系统（TagMemo浪潮算法）
- 元思考系统和语义检索
- 跨场景记忆（群聊/私聊统一）

### 🔧 工具调用
- MCP 协议支持
- 48+ 工具集成（搜索、天气、音乐、绘图等）
- Undefined QQbot 工具箱
- 包豆AI 视觉自动化（屏幕分析和鼠标键盘控制）
- VCPToolBox 高级记忆和RAG功能

### 📊 舆情分析
- BettaFish 多智能体系统
- 深度舆情分析
- 情感分析与报告生成

---

## 📖 文档

详细的文档请查看 [docs](docs/README.md) 目录。

- 🚀 [快速开始](docs/快速开始.md) - 5 分钟上手 NagaAgent
- 📖 [功能指南](docs/功能指南.md) - 详细功能介绍
- ⚙️ [配置指南](docs/配置指南/配置总览.md) - 所有配置选项
- 🔧 [故障排查](docs/故障排查.md) - 解决常见问题
- 🤖 [脚本工具](scripts/README.md) - 管理脚本使用说明

---

## 🎯 快速开始

### 1. 安装依赖

```bash
# Windows
setup.bat

# Linux/macOS
./setup.sh
```

### 2. 配置 API

编辑 `config.json`，填入你的 API 密钥：

```json
{
  "api": {
    "api_key": "your_api_key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4"
  }
}
```

### 3. 启动应用

```bash
# Windows
start.bat

# Linux/macOS
./start.sh
```

详见 [快速开始指南](docs/快速开始.md)。

---

## 🚀 高级功能

### 🖥️ 包豆AI 视觉自动化

包豆AI提供屏幕分析和自动化操作能力。

**快速启用**:
1. 配置豆包API密钥到 `baodou_AI/config.json`
2. 在 `config.json` 中启用 `baodou_ai.enabled: true`
3. 重启弥娅

**使用示例**: "弥娅,帮我打开浏览器并搜索人工智能"

详见 [包豆AI集成指南](BAODOU_INTEGRATION_GUIDE.md)

---

### 📚 VCPToolBox 高级记忆

VCPToolBox提供语义记忆检索和元思考能力。

**快速启用**:
1. 启动VCPToolBox: `cd VCPToolBox && npm start`
2. 在 `config.json` 中启用 `vcp.enabled: true`
3. 重启弥娅

详见 [VCP集成指南](VCP_INTEGRATION_GUIDE.md)

---

## 🎨 功能截图

### 主界面
![UI Preview](ui/img/README.jpg)

---

## 🛠️ 技术架构

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     用户界面层 (UI)                          │
│  PyQt5 GUI  |  Live2D 虚拟形象  |  系统托盘  |  聊天界面       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   核心服务层 (Core Services)                │
│  API服务 :8000  |  Agent服务 :8001  |  MCP服务 :8003  |  TTS   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   业务逻辑层 (Business Logic)                 │
│  博弈论系统  |  GRAG 记忆系统  |  语音处理  |  工具调用        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   数据存储层 (Data Storage)                   │
│  Neo4j 图数据库  |  文件系统  |  内存缓存                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   外部服务层 (External Services)              │
│  LLM 服务商  |  QQ/WeChat  |  MQTT  |  网络爬虫              │
└─────────────────────────────────────────────────────────────┘
```

### 核心技术栈

- **Python 3.11** + PyQt5 + FastAPI
- **Neo4j 图数据库** + GRAG 知识图谱
- **SQLite 向量数据库** + VCPToolBox TagMemo浪潮算法
- **MCP (Model Context Protocol)** 工具调用
- **OpenAI 兼容 API** + 多种 LLM 服务商支持
- **NapCat** - QQ 机器人框架
- **GPT-SoVITS** - TTS 语音合成引擎
- **BettaFish** - 多智能体舆情分析系统
- **包豆AI** - 豆包视觉模型 + PyAutoGUI自动化

---

## 🚀 核心改进

### 🔧 关键 Bug 修复
- ✅ 修复 PC 端重复输出
- ✅ 修复 QQ 端图片识别不按人设
- ✅ 修复消息格式不响应命令
- ✅ 修复长文本输出不完整
- ✅ 修复长文本不分多次发送
- ✅ 修复 MCP 工具参数映射错误

### 🚀 新增功能
- 📝 长文本自动分段（500 字符/段）
- 🎙️ 长语音自动分段（200 字符/段）
- 🧠 智能语意分析器
- 🔀 回复模式切换（文本/语音/图文）
- 👥 群聊回复控制（白名单/黑名单/@触发）
- 📊 BettaFish 舆情分析集成
- 🖥️ 包豆AI 视觉自动化（屏幕操作自动化）
- 📚 VCPToolBox 高级记忆系统（语义检索+元思考）

### ⚡ 性能优化
- 📊 MCP 回调超时：5s → 30s
- 📊 任务去重缓存机制
- 📊 优化回调重试机制

---

## 🎯 QQ/WeChat 集成

### QQ 机器人
详见 [QQ 机器人配置](docs/配置指南/QQ机器人配置.md)。

### 微信机器人
微信机器人通过扫码登录，启动程序后会显示二维码。

---

## 🤖 工具系统

### Undefined 工具集（48 个工具）

提供丰富的在线功能，包括：
- 🔍 搜索查询 - 网页搜索、网页爬取
- 📊 热门榜单 - 百度热搜、微博热搜、抖音热搜
- 🎬 视频娱乐 - B站搜索、视频推荐
- 🎵 音乐相关 - 音乐搜索、歌词查询
- 🌤️ 生活服务 - 天气查询、时间查询、星座运势
- 💰 财经信息 - 黄金价格查询
- 📱 社交相关 - QQ相关功能
- 📂 文件操作 - 读写文件、搜索文件
- 🛠️ 开发工具 - Base64、Hash、网络测试
- 🤖 AI辅助 - AI绘图、学习助手

详见 [功能使用指南](docs/功能指南.md)。

---

## 🎤 语音功能

### 支持的 TTS 引擎

- **Edge-TTS** - 在线免费 TTS
- **GPT-SoVITS** - 本地定制化 TTS（推荐）
- **VITS** - 高效本地 TTS

详见 [语音功能配置](docs/配置指南/语音功能配置.md)。

---

## 📱 移动端访问

### 配置步骤

1. 确认 `config.json` 中 `api_server.host` 为 `"0.0.0.0"`
2. 配置防火墙允许端口 8000
3. 获取电脑 IP 地址：`ipconfig` (Windows) 或 `ifconfig` (Linux/Mac)
4. 在手机浏览器访问：`http://你的电脑IP:8000`

### 功能特性
- ✅ 响应式设计，完美适配手机和平板
- ✅ 流式对话支持
- ✅ 对话历史记忆
- ✅ Markdown 格式化
- ✅ PWA 支持（可添加到主屏幕）

---

## 🔧 智能语意分析

系统会自动分析用户消息的语意，智能判断：
- 是否需要调用工具
- 输出长度
- 回复风格

---

## 🛠️ 故障排查

详见 [故障排查指南](docs/故障排查.md)。

### 常见问题

#### 1. Python 版本不兼容

确保使用 Python 3.11

```bash
python --version
```

#### 2. 端口被占用

检查端口 8000、8001、8003、5048 是否可用

```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

#### 3. QQ 连接失败 (HTTP 403)

清空 `config.json` 中的 `http_token` 和 `ws_token`，确保 NapCat 正在运行。

#### 4. GPT-SoVITS 连接失败 (HTTP 404)

启动 GPT-SoVITS 服务：`python api_v2.py`

---

## 📄 许可证

本项目继承原版 NagaAgent 的 [MIT 许可证](LICENSE)。

---

## 🙏 致谢

- **原项目**：[NagaAgent](https://github.com/Xxiii8322766509/NagaAgent)
- **NapCat**：[NapCat QQ](https://github.com/NapNeko/NapCatQQ) - QQ 机器人框架
- **Undefined**: [Undefined QQbot](https://github.com/69gg/Undefined.git) - QQbot框架联动
- **GPT-SoVITS**：[GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) - TTS 引擎

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📮 更新日志

### v4.2.0 Modified (2026-01-28)

#### 新增集成
- ✅ 集成 **VCPToolBox** 高级记忆系统
  - TagMemo浪潮算法 V4 RAG系统
  - 元思考系统和语义检索
  - 4个MCP工具（RAG检索、记忆存储、元思考、统计信息）
  - 详见 [VCP_INTEGRATION_GUIDE.md](VCP_INTEGRATION_GUIDE.md)

- ✅ 集成 **包豆AI** 视觉自动化系统
  - 豆包视觉模型屏幕分析
  - 鼠标键盘自动化控制
  - 8个MCP工具（截屏、任务分析、鼠标/键盘操作）
  - 详见 [BAODOU_INTEGRATION_GUIDE.md](BAODOU_INTEGRATION_GUIDE.md)

#### 配置增强
- ✅ 新增 VCPConfig 配置类
- ✅ 新增 BaodouAIConfig 配置类
- ✅ 添加 httpx 依赖用于VCP通信

#### 文档完善
- ✅ 集成状态报告文档
- ✅ 完整的融合指南
- ✅ 双层记忆架构对比文档

---

### v4.1.0 Modified (2026-01-25)

#### 结构优化
- ✅ 清理冗余测试文件和文档
- ✅ 创建清晰的文档结构（docs/ 目录）
- ✅ 创建脚本工具目录（scripts/ 目录）
- ✅ 编写完整的文档体系

#### 核心改进
- ✅ 修复 PC 端文本和语音重复输出
- ✅ 修复 QQ 端图片识别不按人设
- ✅ 修复 QQ 端消息格式不按命令响应
- ✅ 修复长文本输出不完整
- ✅ 修复长文本不分多次发送

#### 新增功能
- ✅ 长文本自动分段发送（500 字符/段）
- ✅ 长语音自动分段生成（200 字符/段）
- ✅ 智能语义分割
- ✅ 回复模式切换支持

#### 性能优化
- ✅ MCP 回调超时：5s → 30s
- ✅ 任务去重缓存
- ✅ 优化回调重试机制

#### 代码清理
- ✅ 删除 30+ 个重复/过时文档
- ✅ 删除 16 个测试文件
- ✅ 简化项目结构

---

<div align="center">

**如果这个项目对你有帮助，请给原版和本魔改版一个 Star ⭐**

**NagaAgent Modified Version**

Made with ❤️ by the community

</div>
