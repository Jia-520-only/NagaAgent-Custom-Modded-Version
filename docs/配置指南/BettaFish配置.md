# BettaFish 舆情分析系统配置指南

BettaFish 是一个多智能体协作的舆情分析系统，集成在 NagaAgent 中。

---

## 📋 功能介绍

BettaFish 包含 6 个智能引擎：

| 引擎 | 功能 |
|------|------|
| **InsightEngine** | 深度舆情分析 |
| **MediaEngine** | 媒体内容分析 |
| **QueryEngine** | 查询引擎 |
| **ReportEngine** | 报告生成 |
| **ForumEngine** | 情感分析 |
| **KeywordOptimizer** | 关键词优化 |

---

## 🚀 快速开始

### 前置条件

1. 已安装 Docker（推荐）或本地 MySQL
2. 已配置网络搜索 API（Tavily 或 Bocha）
3. 已配置 LLM API（DeepSeek、OpenAI 等）

### 自动配置（推荐）

运行自动化配置脚本：

```bash
python configure_betta_fish.py
```

按照提示输入你的 API 密钥即可。

---

## 📝 手动配置

### 1. 配置 BettaFish 环境

#### 方式一：使用 Docker MySQL（推荐）

确保 MySQL Docker 容器正在运行：

```bash
# 启动 MySQL 容器
docker run -d \
  --name naga-mysql \
  -e MYSQL_ROOT_PASSWORD=Aa316316 \
  -e MYSQL_DATABASE=betta_fish \
  -p 9902:3306 \
  mysql:8.0
```

#### 方式二：使用本地 MySQL

确保本地 MySQL 正在运行，端口为 9902。

### 2. 配置 BettaFish .env 文件

编辑 `betta-fish-main/.env` 文件：

```bash
# API Keys
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
BOCHA_API_KEY=your_bocha_key

# Database
DB_HOST=127.0.0.1
DB_PORT=9902
DB_USER=root
DB_PASSWORD=Aa316316
DB_NAME=betta_fish
```

### 3. 安装依赖

```bash
cd betta-fish-main
pip install -r requirements.txt
```

### 4. 初始化数据库

```bash
python init_betta_fish_db.py
```

### 5. 启动 BettaFish

```bash
python app.py
```

BettaFish 将在 `http://127.0.0.1:5000` 启动。

---

## 🔧 配置 LLM Agents

### 支持的 LLM 提供商

| 提供商 | 环境变量 |
|--------|----------|
| DeepSeek | `DEEPSEEK_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Claude | `ANTHROPIC_API_KEY` |
| Azure | `AZURE_OPENAI_API_KEY` |

### 配置示例

编辑 `betta-fish-main/.env`：

```bash
# 主 LLM（推荐 DeepSeek）
OPENAI_API_KEY=sk-xxxxxxxxxx
OPENAI_BASE_URL=https://api.deepseek.com/v1

# 备用 LLM
DEEPSEEK_API_KEY=sk-xxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxx
```

---

## 🔍 配置网络搜索 API

### Tavily API（推荐）

1. 访问 [Tavily](https://tavily.com/) 注册账号
2. 获取 API Key
3. 配置到 `.env`：

```bash
TAVILY_API_KEY=tvly-xxxxxxxxxx
```

### Bocha API

1. 访问 [Bocha](https://bochaai.com/) 注册账号
2. 获取 API Key
3. 配置到 `.env`：

```bash
BOCHA_API_KEY=sk-xxxxxxxxxx
```

---

## 🔄 数据库模式切换

### 切换脚本

运行数据库模式切换脚本：

```bash
python betta-fish-main/config_db_mode.py
```

**模式说明**：
- **Cloud Mode** - 使用云端数据库
- **Local Mode** - 使用本地 MySQL（端口 9902）
- **Hybrid Mode** - 云端和本地都使用

---

## 📊 使用 BettaFish

### 通过 Web 界面

访问 `http://127.0.0.1:5000`：

1. 输入要分析的关键词或话题
2. 选择分析类型（深度分析/情感分析/媒体分析等）
3. 点击"开始分析"
4. 查看生成的报告

### 通过 NagaAgent 集成

在 NagaAgent 聊天中直接使用：

```
用户：帮我分析一下"人工智能"的舆情
弥娅：[调用 BettaFish] 好的，我正在分析"人工智能"的舆情...
```

---

## 🛠️ 故障排查

### 问题 1: 数据库连接失败

**现象**：提示无法连接到数据库

**解决**：
1. 检查 MySQL 容器是否运行：`docker ps`
2. 检查端口 9902 是否可用：`netstat -ano | findstr :9902`
3. 检查 `.env` 中的数据库配置是否正确

### 问题 2: API 密钥无效

**现象**：提示 API 密钥错误

**解决**：
1. 检查 `.env` 中的 API Key 是否正确
2. 确认 API 账户有足够的余额
3. 尝试使用其他 LLM 提供商

### 问题 3: 网络搜索失败

**现象**：无法搜索网络内容

**解决**：
1. 检查 Tavily/Bocha API Key 是否有效
2. 检查网络连接是否正常
3. 尝试切换到另一个搜索 API

---

## 📚 相关文档

- [BettaFish 官方文档](https://github.com/your-repo/betta-fish)
- [API 配置指南](./API配置.md)
- [快速开始](../快速开始.md)

---

## 💡 高级配置

### 自定义 Agent 配置

编辑 `betta-fish-main/config.py`：

```python
# 配置 InsightEngine
INSIGHT_ENGINE_CONFIG = {
    "model": "deepseek-chat",
    "temperature": 0.7,
    "max_tokens": 2000
}

# 配置 MediaEngine
MEDIA_ENGINE_CONFIG = {
    "model": "gpt-4",
    "temperature": 0.5,
    "max_tokens": 1500
}
```

### 自定义报告模板

编辑 `betta-fish-main/templates/` 目录下的报告模板文件。

---

## 🔗 集成到 NagaAgent

BettaFish 已集成到 NagaAgent，可以通过 MCP 协议调用。

使用示例：

```
用户：分析一下"新能源汽车"的舆情
弥娅：[调用 BettaFish] 好的，我正在分析...

深度分析结果：
- 搜索结果：10 篇相关文章
- 情感倾向：正面 60%，中性 30%，负面 10%
- 媒体分析：主流媒体报道 5 篇，自媒体 3 篇...
```

---

## ✅ 配置检查清单

完成以下检查确保配置正确：

- [ ] MySQL Docker 容器正在运行（端口 9902）
- [ ] BettaFish `.env` 文件已配置
- [ ] LLM API Key 已配置（至少一个）
- [ ] 网络搜索 API 已配置（Tavily 或 Bocha）
- [ ] 依赖已安装：`pip install -r requirements.txt`
- [ ] 数据库已初始化：`python init_betta_fish_db.py`
- [ ] BettaFish 服务正在运行：`python app.py`

---

**如有问题，请参考 [故障排查](../故障排查.md)**
