# NagaAgent 一键安装包使用说明

## 📦 安装包内容

安装包包含以下内容:

### 核心文件
- `install_wizard.py` - 图形化配置向导
- `install.bat` - Windows 自动安装脚本
- `install.sh` - Linux/Mac 自动安装脚本
- `start.bat` - Windows 启动脚本
- `start.sh` - Linux/Mac 启动脚本
- `start_all.bat` - 启动所有服务
- `main.py` - 主程序入口

### 项目源码
- `agentserver/` - 智能体服务器
- `apiserver/` - API 服务器
- `mcpserver/` - MCP 服务器
- `ui/` - 用户界面
- `voice/` - 语音模块
- `system/` - 系统核心
- 等等...

### 配置文件
- `config.json.example` - 配置文件模板
- `requirements.txt` - Python 依赖列表
- `安装说明.txt` - 简要安装说明

## 🚀 快速开始

### Windows 用户

1. **解压安装包**
   ```
   将 NagaAgent_vX.X.X_YYYYMMDD_HHMM.zip 解压到任意目录
   ```

2. **运行安装脚本**
   ```
   双击运行 install.bat
   ```

3. **按提示配置**
   - 安装脚本会自动检测 Python 环境
   - 创建虚拟环境
   - 安装依赖
   - 启动配置向导

4. **配置向导**
   - 按照 install_wizard.py 的提示填写配置信息
   - 配置内容包括: API Key、Neo4j、TTS 引擎等

5. **启动程序**
   ```
   双击运行 start.bat
   ```

### Linux/Mac 用户

1. **解压安装包**
   ```bash
   unzip NagaAgent_vX.X.X_YYYYMMDD_HHMM.zip
   cd NagaAgent_vX.X.X_YYYYMMDD_HHMM
   ```

2. **运行安装脚本**
   ```bash
   bash install.sh
   ```

3. **启动程序**
   ```bash
   ./start.sh
   ```

## ⚙️ 手动安装

如果自动安装脚本无法使用,可以手动安装:

### 1. 检查 Python 版本

确保安装了 Python 3.11 或更高版本:

```bash
python --version  # Windows
python3 --version  # Linux/Mac
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置程序

运行配置向导:

```bash
python install_wizard.py
```

或手动复制并编辑配置:

```bash
cp config.json.example config.json
# 编辑 config.json 填写配置信息
```

### 5. 启动程序

```bash
python main.py
```

## 🔧 配置说明

配置文件 `config.json` 包含以下主要配置项:

### 必需配置

1. **API Key** (DeepSeek)
   ```json
   "api": {
     "api_key": "your-deepseek-api-key",
     "base_url": "https://api.deepseek.com/v1",
     "model": "deepseek-chat"
   }
   ```

2. **Neo4j** (知识图谱)
   ```json
   "grag": {
     "enabled": true,
     "neo4j_uri": "neo4j://127.0.0.1:7687",
     "neo4j_user": "neo4j",
     "neo4j_password": "your-neo4j-password"
   }
   ```

3. **TTS 引擎** (语音合成)
   - **GPT-SoVITS**
     ```json
     "tts": {
       "gpt_sovits_enabled": true,
       "gpt_sovits_url": "http://127.0.0.1:9880",
       "gpt_sovits_ref_audio_path": "path/to/reference.wav"
     }
     ```
   - **Genie-TTS**
     ```json
     "tts": {
       "genie_tts_enabled": true,
       "genie_tts_url": "http://127.0.0.1:8000"
     }
     ```

### 可选配置

1. **QQ 机器人**
   ```json
   "qq_wechat": {
     "qq": {
       "enabled": true,
       "bot_qq": "your-bot-qq-number",
       "http_url": "http://127.0.0.1:3000",
       "ws_url": "ws://127.0.0.1:3001"
     }
   }
   ```

2. **实时语音**
   ```json
   "voice_realtime": {
     "enabled": true,
     "provider": "local",
     "api_key": "your-dashscope-api-key"
   }
   ```

3. **AI 绘图**
   ```json
   "online_ai_draw": {
     "api_key": "your-zhipu-api-key"
   }
   ```

## 📋 前置依赖

### 必需软件

1. **Python 3.11+**
   - Windows: https://www.python.org/downloads/
   - Linux: `sudo apt-get install python3 python3-pip`
   - macOS: `brew install python@3.11`

### 可选软件

1. **Neo4j 5.x** (知识图谱)
   - 下载: https://neo4j.com/download/
   - 默认端口: 7474 (HTTP), 7687 (Bolt)

2. **GPT-SoVITS** (语音合成)
   - GitHub: https://github.com/RVC-Boss/GPT-SoVITS
   - 默认端口: 9880

3. **Genie-TTS** (语音合成)
   - 默认端口: 8000

4. **NapCat** (QQ 机器人)
   - GitHub: https://github.com/NapNeko/NapCatQQ
   - 默认端口: 3000 (HTTP), 3001 (WebSocket)

## 🎯 常见问题

### Q1: 安装脚本提示找不到 Python

**A:** 请确保已安装 Python 3.11+ 并添加到系统 PATH

### Q2: 依赖安装失败

**A:** 尝试升级 pip:
```bash
python -m pip install --upgrade pip
```

### Q3: 配置向导无法启动

**A:** 手动复制 `config.json.example` 为 `config.json` 并编辑

### Q4: 启动时提示端口被占用

**A:** 修改 `config.json` 中的端口号:
```json
"api_server": {
  "port": 8000  // 修改为其他端口
}
```

### Q5: Neo4j 连接失败

**A:** 检查:
- Neo4j 服务是否启动
- 配置的 URI、用户名、密码是否正确
- 防火墙是否允许 7687 端口

### Q6: 语音功能无法使用

**A:** 检查:
- TTS 服务是否启动 (GPT-SoVITS/Genie-TTS)
- 配置的 URL 和端口是否正确
- 参考音频文件路径是否存在

### Q7: QQ 机器人无法连接

**A:** 检查:
- NapCat 是否启动
- HTTP/WS 端口配置是否正确
- Token 是否配置

## 📚 更多信息

- **详细文档**: 查看 `README_MODDED.md`
- **快速开始**: 查看 `START_GUIDE.md`
- **项目主页**: 访问项目 GitHub 页面

## 💡 使用建议

1. **首次使用**
   - 建议只配置基础功能 (API Key)
   - 其他功能可以后续逐步启用

2. **生产环境**
   - 设置 `debug: false`
   - 配置适当的日志级别
   - 定期备份数据

3. **性能优化**
   - 根据机器配置调整 `max_history_rounds`
   - 合理设置并发数量
   - 启用必要的缓存功能

4. **数据安全**
   - 不要将 `config.json` 提交到版本控制
   - 定期清理日志文件
   - 妥善保管 API Key 和密码

## 🆘 获取帮助

如果遇到问题:

1. 查看日志文件 `logs/*.log`
2. 检查配置文件是否正确
3. 参考项目文档
4. 提交 Issue 到项目仓库

---

祝您使用愉快! 🎉
