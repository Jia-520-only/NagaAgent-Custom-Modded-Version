# BettaFish 完整配置指南

## 第三阶段：配置网络搜索 API

### 选项 A：Tavily 搜索（推荐）

1. **注册 Tavily**
   - 访问：https://tavily.com/
   - 注册账号获取免费 API Key
   - 免费额度：每月 1,000 次搜索

2. **配置 API Key**
   编辑 `betta-fish-main/.env`:
   ```env
   TAVILY_API_KEY=tvly-你的密钥
   ```

### 选项 B：Bocha 搜索（中文优化）

1. **注册 Bocha**
   - 访问：https://open.bochaai.com/
   - 注册账号获取 API Key
   - 中文搜索效果更好

2. **配置 API Key**
   编辑 `betta-fish-main/.env`:
   ```env
   BOCHA_BASE_URL=https://api.bochaai.com
   BOCHA_WEB_SEARCH_API_KEY=你的密钥
   ```

---

## 第四阶段：配置独立 LLM（多 Agent 协作）

BettaFish 需要 6 个 LLM API，支持以下厂商：

### 推荐厂商（中转 API，便宜好用）

| Agent | 推荐 API | 购买地址 | 说明 |
|-------|----------|----------|------|
| InsightEngine | Kimi | https://platform.moonshot.cn/ | 主分析引擎 |
| MediaEngine | Gemini 2.0 | https://www.chataiapi.com/ | 媒体分析 |
| QueryEngine | DeepSeek | https://www.deepseek.com/ | 查询引擎 |
| ReportEngine | Gemini 2.0 | https://www.chataiapi.com/ | 报告生成 |
| ForumEngine | Qwen3 | https://cloud.siliconflow.cn/ | 论坛协作 |
| KeywordOptimizer | DeepSeek | https://www.deepseek.com/ | SQL优化 |

### 配置步骤

1. **获取 API Keys**
   - 按照上表注册账号并购买/获取 API Key

2. **填写 .env 配置**
   编辑 `betta-fish-main/.env`:
   ```env
   # Insight Engine (Kimi)
   INSIGHT_ENGINE_API_KEY=sk-xxx
   INSIGHT_ENGINE_BASE_URL=https://api.moonshot.cn/v1
   INSIGHT_ENGINE_MODEL_NAME=kimi-k2-0711-preview

   # Media Engine (Gemini)
   MEDIA_ENGINE_API_KEY=sk-xxx
   MEDIA_ENGINE_BASE_URL=https://api.chataiapi.com/v1
   MEDIA_ENGINE_MODEL_NAME=gemini-2.5-pro

   # Query Engine (DeepSeek)
   QUERY_ENGINE_API_KEY=sk-xxx
   QUERY_ENGINE_BASE_URL=https://api.deepseek.com/v1
   QUERY_ENGINE_MODEL_NAME=deepseek-reasoner

   # Report Engine (Gemini)
   REPORT_ENGINE_API_KEY=sk-xxx
   REPORT_ENGINE_BASE_URL=https://api.chataiapi.com/v1
   REPORT_ENGINE_MODEL_NAME=gemini-2.5-pro

   # Forum Host (Qwen3)
   FORUM_HOST_API_KEY=sk-xxx
   FORUM_HOST_BASE_URL=https://api.siliconflow.cn/v1
   FORUM_HOST_MODEL_NAME=Qwen/Qwen3-235B-A22B-Instruct-2507

   # Keyword Optimizer (DeepSeek)
   KEYWORD_OPTIMIZER_API_KEY=sk-xxx
   KEYWORD_OPTIMIZER_BASE_URL=https://api.deepseek.com/v1
   KEYWORD_OPTIMIZER_MODEL_NAME=deepseek-chat
   ```

---

## 自动化配置

运行配置助手：
```bash
python configure_betta_fish.py
```

---

## 验证配置

### 1. 测试网络搜索
```bash
cd betta-fish-main
python -c "from QueryEngine.tools.search import TavilyNewsAgency; client = TavilyNewsAgency(); print(client.basic_search_news('测试'))"
```

### 2. 测试 LLM 连接
```bash
python test_betta_fish_apis.py
```

---

## 多 Agent 协作说明

### Agent 架构

```
用户输入
    ↓
InsightEngine (深度洞察)
    ↓
QueryEngine (网络搜索) → Tavily/Bocha
    ↓
MediaEngine (媒体分析)
    ↓
MindSpider (数据存储)
    ↓
ReportEngine (报告生成)
    ↑
ForumEngine (论坛协作)
```

### 各 Agent 功能

| Agent | 功能 | 输入 | 输出 |
|-------|------|------|------|
| InsightEngine | 深度洞察分析 | 话题/关键词 | 分析框架 |
| QueryEngine | 网络信息搜索 | 搜索词 | 搜索结果 |
| MediaEngine | 媒体内容分析 | 链接/内容 | 情感/主题 |
| MindSpider | 数据存储管理 | 结构化数据 | 存储结果 |
| ReportEngine | 报告生成 | 分析数据 | HTML/Markdown |
| ForumEngine | 论坛协作 | 研究任务 | 协作讨论 |

---

## 成本估算

| API | 用量 | 单价 | 月成本 |
|-----|------|------|--------|
| Kimi | 10万 tokens | ¥0.012/1K | ¥1.2 |
| Gemini 2.0 | 20万 tokens | ¥0.01/1K | ¥2 |
| DeepSeek | 30万 tokens | ¥0.001/1K | ¥0.3 |
| Qwen3 | 5万 tokens | ¥0.0005/1K | ¥0.025 |
| **总计** | - | - | **~¥3.5** |

*估算基于每月 10 次深度分析*

---

## 快速开始

配置完成后，运行：
```bash
cd betta-fish-main
python app.py
```

访问 http://localhost:5000 开始使用
