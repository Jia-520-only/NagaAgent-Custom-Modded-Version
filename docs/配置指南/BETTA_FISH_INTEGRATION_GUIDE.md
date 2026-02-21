# BettaFish（微舆）融合到NagaAgent集成指南

## 📋 概述

BettaFish（微舆）是一个多智能体舆情分析系统，已成功融合到NagaAgent中作为MCP服务。本指南详细说明融合内容、使用方法和配置说明。

## 🎯 融合内容

### 1. MCP Agent 创建

已创建新的MCP Agent：`mcpserver/agent_betta_fish/`

**文件结构：**
```
mcpserver/agent_betta_fish/
├── __init__.py                  # 模块初始化
├── agent-manifest.json          # 服务清单
└── betta_fish_agent.py         # Agent主实现
```

### 2. 可用工具

| 工具名称 | 功能 | 参数 | 示例 |
|---------|------|------|------|
| **舆情分析** | 深度舆情分析 | `topic`（主题）<br>`depth`（深度1-5） | `{"tool_name":"舆情分析","topic":"武汉大学","depth":3}` |
| **情感分析** | 文本情感倾向分析 | `text`（待分析文本） | `{"tool_name":"情感分析","text":"今天心情很好"}` |
| **生成舆情报告** | 生成专业舆情报告 | `topic`（主题）<br>`report_type`（类型） | `{"tool_name":"生成舆情报告","topic":"AI技术","report_type":"科技"}` |
| **全网搜索** | 全网信息搜索 | `query`（搜索内容）<br>`days`（天数） | `{"tool_name":"全网搜索","query":"AI进展","days":7}` |

### 3. 对话提示词更新

已更新 `system/prompts/conversation_analyzer_prompt.txt`，添加：

1. **工具选择规则**：识别舆情分析相关关键词
2. **示例对话**：4个实际使用示例
3. **参数映射**：明确各工具的参数要求

## 🚀 使用方法

### 方式一：通过对话直接使用

用户可以自然地提出需求，弥娅会自动识别并调用相应工具：

```
用户: "帮我分析一下最近AI发展的网络舆情"
弥娅: 自动调用"舆情分析"工具，返回分析结果

用户: "分析这句话的情感：今天天气真好"
弥娅: 自动调用"情感分析"工具，返回情感结果

用户: "生成一份关于ChatGPT的舆情报告"
弥娅: 自动调用"生成舆情报告"工具，生成专业报告
```

### 方式二：明确指定工具

用户可以明确要求使用特定工具：

```
用户: "弥娅，用微舆分析一下'新能源汽车'的舆情"
弥娅: 调用舆情分析工具
```

### 方式三：通过其他渠道调用

- **QQ/微信**：直接发送消息即可
- **API**：通过MCP API调用
- **UI界面**：在聊天界面使用

## ⚙️ 配置说明

### 基础模式（默认）

无需额外配置，BettaFish Agent会自动以"基础模式"工作：

- ✅ 使用NagaAgent现有LLM（DeepSeek）
- ✅ 基础情感分析（关键词匹配）
- ✅ 简单舆情分析（LLM生成）
- ✅ 报告生成（使用LLM模板）

### 完整模式（可选）

如需使用BettaFish的全部功能，需要配置以下内容：

#### 1. 数据库配置（可选）

BettaFish支持MySQL数据库存储舆情数据，用于深度分析。

在 `betta-fish-main/.env` 中配置：

```env
# MySQL数据库配置
DB_DIALECT=mysql
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_db_name
DB_CHARSET=utf8mb4
```

**注意**：NagaAgent无需此配置也能使用BettaFish基础功能。

#### 2. BettaFish LLM配置（可选）

如需为BettaFish使用独立的LLM，在 `betta-fish-main/.env` 配置：

```env
# Insight Agent（推荐Kimi）
INSIGHT_ENGINE_API_KEY=your_key
INSIGHT_ENGINE_BASE_URL=https://api.moonshot.cn/v1
INSIGHT_ENGINE_MODEL_NAME=kimi-k2-0711-preview

# Media Agent（推荐Gemini）
MEDIA_ENGINE_API_KEY=your_key
MEDIA_ENGINE_BASE_URL=https://api.siliconflow.cn/v1
MEDIA_ENGINE_MODEL_NAME=gemini-2.5-pro

# Query Agent（推荐DeepSeek）
QUERY_ENGINE_API_KEY=your_key
QUERY_ENGINE_BASE_URL=https://api.deepseek.com
QUERY_ENGINE_MODEL_NAME=deepseek-reasoner
```

**注意**：不配置时，BettaFish会使用NagaAgent的统一LLM配置。

#### 3. 依赖安装（可选）

如需启用高级功能（如InsightEngine深度分析），安装BettaFish依赖：

```bash
cd betta-fish-main
pip install -r requirements.txt
```

**注意**：基础功能无需额外安装。

## 📊 功能对比

| 功能 | 基础模式 | 完整模式 |
|------|---------|---------|
| 舆情分析 | ✅ LLM生成分析 | ✅ 多Agent协同分析 |
| 情感分析 | ✅ 关键词匹配 | ✅ 多语言模型分析 |
| 报告生成 | ✅ LLM模板生成 | ✅ 专业报告引擎 |
| 全网搜索 | ✅ 基础搜索 | ✅ 多源聚合搜索 |
| 论坛协作 | ❌ 不支持 | ✅ Agent辩论机制 |
| 数据库挖掘 | ❌ 不支持 | ✅ MySQL深度查询 |

## 🔧 启动说明

### NagaAgent启动

正常启动NagaAgent即可，BettaFish Agent会自动注册：

```bash
python main.py
```

启动后会在日志中看到：

```
✅ 注册MCP服务: 微舆舆情分析 (来自 mcpserver\agent_betta_fish\agent-manifest.json)
MCP注册完成，共注册 X 个服务: [..., '微舆舆情分析', ...]
```

### BettaFish独立使用（可选）

如需独立使用BettaFish完整系统：

```bash
cd betta-fish-main
python app.py
```

访问 http://localhost:5000 使用完整Web界面。

## 🎨 使用示例

### 示例1：舆情分析

```
用户: "弥娅，帮我分析一下最近'人工智能'的网络舆情"

弥娅:
[开始分析]
正在调用舆情分析工具...
分析主题：人工智能
分析深度：3（中等深度）

[分析结果]
概述：近期关于人工智能的讨论持续升温，主要集中在技术突破、应用场景和伦理讨论三个方面...

主要发现：
1. 技术层面：大模型能力提升明显
2. 应用层面：AI助手普及加速
3. 伦理层面：数据安全引发关注

情感倾向：
- 正面：65%（技术创新、效率提升）
- 中性：25%（客观报道）
- 负面：10%（担忧失业、隐私问题）
```

### 示例2：情感分析

```
用户: "分析这句话的情感：今天考试通过了，真是太高兴了！"

弥娅:
[情感分析]
文本：今天考试通过了，真是太高兴了！

分析结果：
- 情感倾向：积极（positive）
- 置信度：0.92
- 关键词：高兴、通过（积极情感词汇）
- 强度：高强度（感叹号、双重肯定）

结论：表达强烈的积极情绪，反映了用户的喜悦心情。
```

### 示例3：生成舆情报告

```
用户: "生成一份关于'电动汽车'的行业舆情报告"

弥娅:
[生成报告]
正在生成电动汽车行业舆情分析报告...

报告类型：商业舆情
主题：电动汽车行业
生成时间：2026-01-24

[报告摘要]
1. 行业概述
   电动汽车行业正处于快速发展阶段，市场规模持续扩大...

2. 主要舆情点
   - 技术创新：电池技术、自动驾驶
   - 市场竞争：传统车企vs新势力
   - 政策影响：补贴政策、环保法规

3. 消费者反馈
   - 正面：环保、智能化、驾驶体验
   - 中性：价格、续航焦虑
   - 负面：充电设施、安全问题

4. 趋势预测
   - 市场渗透率持续提升
   - 技术创新加速
   - 政策支持力度加大

5. 建议
   - 加强基础设施建设
   - 关注消费者需求变化
   - 提升技术研发投入
```

## 🔍 技术架构

### 数据流

```
用户请求
    ↓
ConversationAnalyzer (意图识别)
    ↓
MCPScheduler (任务调度)
    ↓
BettaFishAgent (工具执行)
    ↓
┌─────────────┬─────────────┬─────────────┐
│ 基础模式      │ 完整模式      │ 混合模式      │
│ (默认)       │ (可选)       │ (推荐)       │
├─────────────┼─────────────┼─────────────┤
│ NagaLLM    │ BettaLLM    │ 智能切换     │
│ 基础分析     │ 多Agent     │ 任务路由     │
│ 关键词匹配    │ 模型分析     │ 最优选择     │
└─────────────┴─────────────┴─────────────┘
    ↓
返回结果
    ↓
用户界面展示
```

### 模块依赖

```
BettaFishAgent
    ├─ NagaAgent LLM (必需)
    │   ├─ DeepSeek (默认)
    │   └─ 配置在 config.json
    │
    ├─ InsightEngine (可选)
    │   ├─ MySQL数据库
    │   ├─ 情感分析模型
    │   └─ 深度搜索能力
    │
    ├─ MediaEngine (可选)
    │   ├─ 多模态分析
    │   └─ Gemini API
    │
    ├─ QueryEngine (可选)
    │   ├─ Tavily搜索
    │   └─ 网页抓取
    │
    └─ ReportEngine (可选)
        ├─ 报告模板
        └─ HTML生成
```

## 🐛 故障排查

### 问题1：Agent未注册

**症状**：启动日志中没有"微舆舆情分析"服务

**解决**：
1. 检查文件是否存在：`mcpserver/agent_betta_fish/agent-manifest.json`
2. 检查JSON格式是否正确
3. 重启NagaAgent

### 问题2：工具调用失败

**症状**：调用工具时返回错误

**解决**：
1. 查看日志中的详细错误信息
2. 检查网络连接（如使用在线LLM）
3. 验证API密钥配置

### 问题3：BettaFish模块导入失败

**症状**：日志显示"BettaFish 部分模块缺失"

**解决**：
- 这是正常的，不影响基础功能使用
- 如需完整功能，安装BettaFish依赖
- 参考"完整模式"配置说明

## 📈 扩展建议

### 短期扩展

1. **增加更多舆情源**
   - 整合NagaAgent现有搜索（searxng）
   - 添加RSS订阅
   - 支持社交媒体API

2. **优化报告生成**
   - 添加更多报告模板
   - 支持导出为PDF
   - 可视化数据图表

3. **增强情感分析**
   - 集成NLP模型
   - 支持细粒度情感分类
   - 添加情感趋势分析

### 长期扩展

1. **多Agent协作**
   - 启用ForumEngine辩论机制
   - 实现复杂任务拆解
   - 智能Agent调度

2. **知识图谱融合**
   - 整合NagaAgent的Neo4j
   - 舆情知识图谱
   - 实体关系分析

3. **预测分析**
   - 时序预测模型
   - 趋势预测
   - 风险预警

## 📞 技术支持

如有问题，请：

1. 查看日志：`logs/` 目录
2. 检查配置：`config.json` 和 `betta-fish-main/.env`
3. 参考本文档

---

**最后更新**: 2026-01-24
**版本**: 1.0.0
**作者**: NagaAgent Team
