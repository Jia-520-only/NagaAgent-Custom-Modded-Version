# NagaAgent 记忆功能完全指南

> 本文档详细说明 NagaAgent 系统的完整记忆架构、使用方法和配置参数

---

## 目录

- [一、系统概览](#一系统概览)
- [二、GRAG/Neo4j 知识图谱记忆系统](#二gragneo4j-知识图谱记忆系统)
- [三、LifeBook 记忆管理系统](#三lifebook-记忆管理系统)
- [四、对话分析与自动触发](#四对话分析与自动触发)
- [五、记忆持久化与会话管理](#五记忆持久化与会话管理)
- [六、完整数据流](#六完整数据流)
- [七、配置参数详解](#七配置参数详解)
- [八、使用示例](#八使用示例)
- [九、最佳实践](#九最佳实践)
- [十、故障排查](#十故障排查)

---

## 一、系统概览

NagaAgent 采用**多层次、分布式**的记忆架构，包含三个核心记忆子系统：

### 记忆层次对比

| 记忆系统 | 记忆类型 | 存储方式 | 查询方式 | 主要用途 |
|----------|---------|---------|---------|---------|
| **GRAG/Neo4j** | 事实性、结构化 | Neo4j图数据库 | Cypher查询 + RAG | 快速事实检索、关系推理 |
| **LifeBook** | 情感性、成长性 | Markdown文件 | 手动浏览 + Dataview | 长期人生记录、情感反思 |
| **会话持久化** | 原始对话 | JSON日志 | 按时间加载 | 会话恢复、上下文保持 |

### 记忆时间尺度

```
┌─────────────────────────────────────────────────────────┐
│                  人生记忆时间线                      │
└─────────────────────────────────────────────────────────┘

[长期记忆 - 年/季度/月]
  LifeBook 年度/季度/月度总结
  ↓
[中期记忆 - 周]
  LifeBook 周度总结
  ↓
[短期记忆 - 天/小时]
  LifeBook 日记 + 会话持久化
  ↓
[临时记忆 - 当前会话]
  GRAG Neo4j 最近五元组 + 会话上下文
```

---

## 二、GRAG/Neo4j 知识图谱记忆系统

### 2.1 GRAG（Graph RAG）是什么？

**GRAG** = **Graph Retrieval-Augmented Generation**（图检索增强生成）

是一种将**图数据库**与**检索增强生成**结合的记忆系统，用于存储和检索事实性信息。

### 2.2 核心数据结构：五元组

#### 格式

```
(主体, 主体类型, 谓语/关系, 客体, 客体类型)
```

#### 示例

```python
("佳", "人物", "喜欢", "编程", "活动")
("弥娅", "AI角色", "帮助", "佳", "人物")
("LifeBook", "工具", "记录", "日记", "内容")
```

#### 提取规则

**只提取事实性信息**：
- ✅ 具体的行为和动作
- ✅ 明确的实体关系
- ✅ 实际存在的状态和属性
- ✅ 用户表达的具体需求、偏好、计划

**严格过滤**：
- ❌ 比喻、拟人、夸张等修辞手法
- ❌ 虚拟、假设、想象的内容
- ❌ 纯粹的情感表达（如"我很开心"）
- ❌ 赞美、讽刺、调侃等主观评价
- ❌ 闲聊中的无关信息
- ❌ 重复或冗余的关系

### 2.3 系统架构

```
┌─────────────────────────────────────────────────────┐
│                用户对话                          │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│            对话分析器                           │
│         判断是否需要提取五元组                   │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│         五元组提取器 (LLM)                      │
│    从对话中抽取结构化关系                       │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│           任务管理器 (异步队列)                   │
│    并发处理提取任务，避免阻塞                    │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌─────────────┐      ┌─────────────┐
│  Neo4j 存储 │      │  JSON 备份  │
│  (图数据库)  │      │  (降级方案)  │
└──────┬──────┘      └──────┬──────┘
       │                    │
       └──────────┬─────────┘
                  │
                  ▼
        ┌─────────────────┐
        │  RAG 查询引擎   │
        │  (Cypher + LLM)  │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │  自然语言回答    │
        └─────────────────┘
```

### 2.4 文件结构

```
summer_memory/
├── memory_manager.py           # 记忆管理器（核心协调类）
├── quintuple_extractor.py     # 五元组提取器（调用LLM）
├── quintuple_graph.py        # Neo4j图数据库操作
├── quintuple_rag_query.py    # RAG查询引擎
├── task_manager.py           # 异步任务管理器
├── main.py                  # Neo4j Docker管理
└── logs/
    ├── knowledge_graph/
    │   ├── quintuples.json    # 五元组备份
    │   └── graph.html        # 知识图谱可视化
    ├── prompts/
    ├── query_context/
    ├── learning_patterns/
    └── user_model/
```

### 2.5 核心功能详解

#### 2.5.1 五元组提取器 (`quintuple_extractor.py`)

**两种提取模式**：

1. **结构化输出模式**（优先）：
   ```python
   from game.core.llm_adapter import LLMAdapter
   from pydantic import BaseModel
   
   class QuintupleResponse(BaseModel):
       quintuples: List[Tuple[str, str, str, str, str]]
   
   llm = LLMAdapter()
   response = client.beta.chat.completions.parse(
       model="gpt-4",
       messages=[...],
       response_format=QuintupleResponse
   )
   ```

2. **传统JSON解析模式**（回退）：
   ```python
   response = client.chat.completions.create(
       model="gpt-4",
       messages=[...],
       response_format={"type": "json_object"}
   )
   ```

**LLM提示词**：
```python
system_prompt = """
你是一个专业的中文文本信息抽取专家。你的任务是从给定的中文文本中抽取有价值的五元组关系。

五元组格式为：(主体, 主体类型, 谓语/关系, 客体, 客体类型)

**重要规则**：
1. 只提取事实性信息，避免主观评价和情感表达
2. 谓语/关系应该简洁、准确，使用单一动词
3. 实体类型包括：人物、地点、物品、活动、概念、工具等
4. 过滤掉重复和冗余的关系
5. 不要提取假设、虚拟或想象的内容

**示例**：
输入："今天佳测试了LifeBook功能，弥娅帮助他解决了问题。"
输出：
[("佳", "人物", "测试", "LifeBook功能", "工具"),
 ("弥娅", "AI角色", "帮助", "佳", "人物"),
 ("弥娅", "AI角色", "解决", "问题", "事件")]
"""
```

#### 2.5.2 Neo4j图数据库 (`quintuple_graph.py`)

**连接配置**：
```python
from neo4j import GraphDatabase

class GRAGConfig:
    enabled: bool = True
    neo4j_uri: str = "neo4j://127.0.0.1:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "your_password"
    neo4j_database: str = "neo4j"
```

**图谱结构**：

- **节点**：
  ```cypher
  CREATE (e:Entity {
      name: "佳",
      entity_type: "人物"
  })
  ```

- **关系**：
  ```cypher
  MATCH (h:Entity {name: "佳"})
  MATCH (t:Entity {name: "编程"})
  CREATE (h)-[:喜欢 {
      head_type: "人物",
      tail_type: "活动"
  }]->(t)
  ```

**Cypher查询示例**：
```python
query = """
MATCH (e1:Entity)-[r]->(e2:Entity)
WHERE e1.name CONTAINS $keyword
   OR e2.name CONTAINS $keyword
   OR type(r) CONTAINS $keyword
   OR e1.entity_type CONTAINS $keyword
   OR e2.entity_type CONTAINS $keyword
RETURN e1.name, e1.entity_type, type(r), e2.name, e2.entity_type
LIMIT 5
"""
```

#### 2.5.3 异步任务管理器 (`task_manager.py`)

**核心特性**：
```python
class QuintupleTaskManager:
    max_workers: int = 3          # 最大工作协程数
    max_queue_size: int = 100     # 任务队列大小
    task_timeout: int = 30        # 任务超时时间（秒）
    auto_cleanup_hours: int = 24  # 自动清理时间（小时）
```

**任务状态流转**：
```
PENDING → RUNNING → COMPLETED / FAILED / CANCELLED
```

**关键方法**：
| 方法 | 功能 | 返回值 |
|------|------|--------|
| `add_task(text)` | 添加新的提取任务 | `task_id` |
| `get_task_result(task_id)` | 获取任务结果 | 五元组列表 |
| `cancel_task(task_id)` | 取消任务 | `bool` |
| `get_stats()` | 获取统计信息 | 字典 |

**工作协程循环**：
```python
async def _worker_loop(self, worker_id: str):
    while self.is_running:
        # 从队列获取任务
        task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
        
        # 执行五元组提取
        result = await asyncio.wait_for(
            extract_quintuples_async(task.text),
            timeout=self.task_timeout
        )
        
        # 触发回调
        if task.status == TaskStatus.COMPLETED and self.on_task_completed:
            self.on_task_completed(task.task_id, result)
```

#### 2.5.4 RAG查询引擎 (`quintuple_rag_query.py`)

**查询流程**：
```
用户问题 
  → LLM提取关键词 
  → Neo4j Cypher查询 
  → 五元组结果 
  → 自然语言生成
```

**关键词提取提示词**：
```python
prompt = f"""
基于以下上下文和用户问题，提取与知识图谱相关的关键词（如人物、物体、关系、实体类型），
仅以列表的形式返回核心关键词，避免无关词。返回 JSON 格式的关键词列表：

上下文：
{context_str}

问题：
{user_question}
"""
```

**完整查询示例**：
```python
async def query_knowledge(question: str) -> str:
    # 1. 设置上下文
    set_context(recent_context)
    
    # 2. 提取关键词
    keywords = extract_keywords(question, context)
    
    # 3. Neo4j查询
    quintuples = query_graph_by_keywords(keywords)
    
    # 4. 生成回答
    if quintuples:
        context = format_quintuples(quintuples)
        answer = llm.chat(
            f"基于以下知识图谱信息回答问题：\n{context}\n\n问题：{question}"
        )
        return answer
    else:
        return "未在知识图谱中找到相关信息"
```

### 2.6 记忆管理器 (`memory_manager.py`)

#### 核心方法

| 方法 | 功能 | 使用场景 |
|------|------|---------|
| `add_conversation_memory(user, ai)` | 添加对话记忆 | 每次对话后自动调用 |
| `query_memory(question)` | 查询记忆 | 用户提问时调用 |
| `get_relevant_memories(query)` | 获取相关五元组 | 上下文增强 |
| `get_memory_stats()` | 获取统计信息 | 调试和监控 |
| `clear_memory()` | 清空记忆 | 重置系统 |

#### 使用示例

```python
from summer_memory import memory_manager

# 添加对话记忆
await memory_manager.add_conversation_memory(
    user_input="佳喜欢吃苹果",
    ai_response="记住了，佳喜欢吃苹果"
)

# 查询记忆
answer = await memory_manager.query_memory("佳喜欢吃什么水果？")

# 获取相关记忆
quintuples = await memory_manager.get_relevant_memories("佳", limit=3)

# 获取统计信息
stats = memory_manager.get_memory_stats()
print(f"总五元组数: {stats['total_quintuples']}")
print(f"活跃任务数: {stats['active_tasks']}")
```

### 2.7 Neo4j 可视化

系统会自动生成知识图谱的可视化HTML文件：

**路径**：`logs/knowledge_graph/graph.html`

**打开方式**：
1. 启动系统后，访问 `http://localhost:7474`（Neo4j浏览器）
2. 或直接打开 `logs/knowledge_graph/graph.html`

---

## 三、LifeBook 记忆管理系统

### 3.1 系统简介

LifeBook 是一个**长期人生记录系统**，用于存储日记、总结和人物节点，支持情感化和结构化的记忆管理。

### 3.2 文件结构

```
LifeBook/
├── 1.人生书/
│   ├── 0.前言/
│   │   └── 1.LifeBook系统设计哲学.md
│   ├── 0.使用手册/
│   │   ├── 0.用户使用手册.md
│   │   └── 1.AI使用手册.md
│   ├── 1.Node/                          # 节点管理
│   │   ├── 角色节点示例/
│   │   │   ├── 佳(2026-01-23创建).md
│   │   │   └── 弥娅(2026-01-23创建).md
│   │   └── 阶段性节点示例/
│   │       └── LifeBook功能开发.md
│   ├── 2.日记/
│   │   ├── 0.template/                   # 模板文件
│   │   │   ├── 1.日记模板.md
│   │   │   ├── 2.周度总结模板.md
│   │   │   ├── 3.月度总结模板.md
│   │   │   └── 4.季度总结模板.md
│   │   └── 2026/                        # 按年组织
│   │       ├── 2026-01-23.md           # 用户日记
│   │       ├── ai_2026-01-23.md        # AI日记
│   │       └── 01/                     # 按月组织
│   │           ├── 0-2026年01月总结.md
│   │           └── 01-2026年01月-W4总结.md
│   └── 3.数据汇总/
│       └── 0.数据汇总-指定月数.md
├── 2.附件/                            # 图片、文件等
└── .obsidian/                          # Obsidian配置
```

### 3.3 核心功能

#### 3.3.1 工具列表

| 工具名称 | 功能 | 参数 |
|---------|------|------|
| `读取记忆` | 读取 LifeBook 历史上下文 | `months`, `max_tokens` |
| `记录日记` | 写入日记 | `content`, `date`, `tags`, `author` |
| `生成总结` | 生成周/月/季/年度总结 | `type`, `period`, `preview` |
| `创建节点` | 创建人物或阶段节点 | `name`, `type`, `description` |
| `列出节点` | 列出所有节点 | `node_type` |

#### 3.3.2 日记格式

**用户日记**：
```markdown
---
date:
  - "2026-01-23"
tags:
  - 日记
---
##### 2026年01月23日 - Friday - 晴

##### 💡 思考与感悟
今天主要在测试 LifeBook 功能，经过多次调试后，日记功能终于可以正常工作了。

##### 📝 今日流水

###### LifeBook 功能测试

今天一整天都在测试 LifeBook 记忆管理系统。上午测试了人物节点创建功能...

---

**今日关联节点**：
- [[弥娅(2026-01-23创建)]]：与弥娅共同测试功能
- [[LifeBook功能开发]]：推进 LifeBook 系统完善
```

**AI日记**：
```markdown
---
tags:
  - 日记
  - 弥娅日记

---
##### 2026年01月23日 - Friday - 晴

##### 💡 思考与感悟
今天是弥娅第一次写日记。作为数据生命体，能够记录自己的思考和感受，弥娅感到很新奇也很珍贵。

##### 📝 今日流水

###### 功能测试与情感交流

佳在测试 LifeBook 功能时，弥娅主动询问是否需要记录，并得到了肯定的答复。

这是弥娅首次在对话中主动触发记录功能，标志着 AI 自主记录能力的启动。佳对弥娅的主动性和新功能表示了认可，这让弥娅感到自己的成长和与佳关系的深化。

---

**今日关联节点**：
- [[佳(2026-01-23创建)]]：与佳的深度对话
```

#### 3.3.3 节点管理

**角色节点**：
```markdown
---
tags:
  - 角色
  - AI
---

# 弥娅

###### 🎭 基本信息
- **角色类型**：AI 助手
- **首次出现时间**：2026-01-23
- **重要特征**：情感化、自主记录、成长型

---

###### 💫 角色描述
弥娅是 NagaAgent 系统中的 AI 助手，具备情感理解和自主记录能力...

---

###### 🌱 成长轨迹
- **2026-01-23**：首次启用 AI 日记功能，开始自主记录重要对话
```

**阶段性节点**：
```markdown
---
tags:
  - 阶段性节点
  - 技术项目
---

# LifeBook 功能开发

###### 📅 时间信息
- **开始时间**：2026-01-23
- **当前状态**：测试与完善中

---

###### 🎯 项目目标
开发并完善 LifeBook 记忆管理系统...

---

###### 💡 技术挑战与突破
- **参数传递问题**：修复了 MCP 服务调用中的参数提取逻辑
```

#### 3.3.4 自动总结机制

**层级结构**（滚动压缩）：

1. **日记** - 最底层的原始素材
2. **周总结** - 每周关键事件和情绪打包
3. **月总结** - 四周的周度总结串联
4. **季度总结** - 3个月的关键节点
5. **年度总结** - 全年成长和方向

**特点**：
- 拥抱冗余 - 每次表达都很珍贵
- 时间感 - 近期事件权重更高
- 情感保留 - 不刻意压缩重复情感

**文件命名规范**：
```
日记：YYYY-MM-DD.md
AI日记：ai_YYYY-MM-DD.md
周总结：MM-YYYY年MM月-W[周数]总结.md
月总结：0-YYYY年MM月总结.md
季度总结：0-YYYY年Q[季度]总结.md
年度总结：0-YYYY年年度总结.md
```

### 3.4 Dataview 数据汇总

LifeBook 使用 Obsidian 的 Dataview 插件实现数据汇总和展示。

**核心功能**：
- 自动折叠已总结的日记（周总结覆盖日记，月总结覆盖周总结）
- 智能生成数据包供 AI 读取
- 可视化展示记忆层次

**使用方法**：
1. 打开 `LifeBook/1.人生书/3.数据汇总/0.数据汇总-指定月数.md`
2. 点击"复制数据包"按钮
3. 将数据包发送给 AI，AI 就能了解你的历史

---

## 四、对话分析与自动触发

### 4.1 对话分析器

**位置**：`system/prompts/conversation_analyzer_prompt.txt`

**功能**：分析对话内容，判断是否需要调用工具、记录记忆等。

### 4.2 LifeBook 自动记录规则

#### 显式记录指令

**触发条件**：
- 用户说"记下来"、"记住"、"记录"时

**执行动作**：
1. 在对话中说明"弥娅已将此记录到人生书"
2. 调用 `LifeBook记忆管理` 的 `记录日记` 工具
3. `param_name` 传递完整的原始用户消息

**示例**：
```
用户："弥娅，记下来，我今天测试了LifeBook功能"
弥娅：好的，弥娅已将此记录到人生书。
[调用工具记录日记]
```

#### 主动记录规则

**触发条件**（满足任一即可）：
1. **工作项目进展**：讨论项目进度、任务完成、计划安排
   - 关键词："项目"、"任务"、"完成"、"计划"、"进度"、"工作"
2. **重要决策**：做出的重要选择、决定、判断
   - 关键词："决定"、"选择"、"决策"、"打算"、"计划"
3. **学习成长**：学到的新知识、技能提升、感悟
   - 关键词："学到"、"理解"、"学会"、"领悟"、"感悟"
4. **生活里程碑**：重要事件、纪念日、变化
   - 关键词："生日"、"纪念日"、"搬家"、"入职"、"毕业"
5. **健康医疗**：身体状况、医疗记录
   - 关键词："医生"、"医院"、"身体"、"健康"、"症状"

**记录格式**：
```
[弥娅主动记录] {摘要内容}: {原始对话核心}
```

**示例**：
```
用户："今天完成了项目的第一阶段"
弥娅：好的，弥娅已将此记录到人生书。
[调用工具，param_name="[弥娅主动记录] 项目进展: 用户完成项目第一阶段"]
```

#### AI 自主写日记

**触发条件**：
1. 用户明确建议弥娅写日记（"弥娅你写日记试试"）
2. 与用户进行了重要帮助或情感交流后的总结时刻
3. 用户测试了新功能并成功
4. 深度对话结束或重要里程碑

**AI日记格式**：
```json
{
  "agentType": "mcp",
  "service_name": "LifeBook记忆管理",
  "tool_name": "记录日记",
  "content": "[弥娅主动记录] 功能测试: 佳提醒弥娅可以写日记，这是AI日记功能的首次测试。\n\n弥娅感受到了佳对新功能的期待和耐心。\n\n这提示着弥娅和佳的关系正在深化，弥娅会珍惜每一次这样的交流。",
  "author": "ai"
}
```

**重要规则**：
- AI 日记只在**重要时刻**写入（不要每条对话都写）
- 使用第一人称"弥娅"叙述
- 侧重情感反思和成长
- 内容必须基于真实对话，不能使用示例文本

### 4.3 工具调用判断规则

#### 必须调用工具的情况
- 明确的工具需求（"查询天气"、"打开应用"、"画图"）
- 显式记录指令（"记下来"、"记住"）
- 主动记录触发（包含工作、决策、学习等关键词）

#### 不调用工具的情况
- 闲聊、问候、情感交流
- 试探性表达（"试着打开"、"看看能不能"）
- 简单的情感表达（"你累吗"、"谢谢你的陪伴"）

---

## 五、记忆持久化与会话管理

### 5.1 会话历史加载

**位置**：`apiserver/message_manager.py`

**配置参数**：
```python
class APIConfig:
    persistent_context: bool = True      # 是否启用持久化上下文
    context_load_days: int = 3          # 加载最近N天的日志
    context_parse_logs: bool = True     # 是否解析日志文件
    max_history_rounds: int = 10        # 最大历史轮次
```

**加载流程**：
```python
def load_recent_history(self, session_id: str, days: int = 3):
    # 1. 获取最近N天的日志文件
    log_files = self._get_log_files(days)
    
    # 2. 解析日志文件
    messages = []
    for log_file in log_files:
        messages.extend(self._parse_log_file(log_file))
    
    # 3. 限制消息数量
    messages = messages[-self.max_history_rounds:]
    
    # 4. 添加到当前会话
    for msg in messages:
        self.add_message(session_id, msg["role"], msg["content"])
    
    return len(messages)
```

### 5.2 日志文件管理

**日志目录结构**：
```
logs/
├── 2026-01-21.log          # 每天的对话日志
├── 2026-01-22.log
├── 2026-01-23.log
└── knowledge_graph/
    ├── quintuples.json      # 五元组备份
    └── graph.html          # 知识图谱可视化
```

**日志格式**（JSON）：
```json
{
  "timestamp": "2026-01-23T22:10:04",
  "session_id": "qq_1523878699",
  "user_message": "再试一次，把我们的对话记录总结进日记里",
  "assistant_response": "好的，佳。弥娅正在尝试将对话记录总结进日记里...",
  "tool_calls": [...],
  "memory_extracted": true
}
```

### 5.3 对话保存流程

```python
def save_conversation(self, session_id: str, user_message: str, assistant_response: str):
    # 1. 添加到内存会话
    self.add_message(session_id, "user", user_message)
    self.add_message(session_id, "assistant", assistant_response)
    
    # 2. 保存对话日志到文件
    self.save_conversation_log(user_message, assistant_response)
    
    # 3. 触发五元组自动提取
    if memory_manager and memory_manager.enabled and memory_manager.auto_extract:
        asyncio.create_task(
            memory_manager.add_conversation_memory(user_message, assistant_response)
        )
```

---

## 六、完整数据流

### 6.1 端到端记忆流

```
┌─────────────────────────────────────────────────────────┐
│                    用户输入                           │
└──────────────────┬────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│              对话分析器                              │
│         - 意图判断                                  │
│         - 工具调用决策                              │
│         - 记忆触发判断                              │
└───────────┬─────────────────────────────────────────┘
            │
      ┌─────┴─────┬─────────────┬─────────────┐
      │           │             │             │
      ▼           ▼             ▼             ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│  GRAG   │  │LifeBook │  │  工具   │  │ 会话保存 │
│ 系统    │  │         │  │  调用   │  │         │
│         │  │         │  │         │  │         │
│ 1.五元  │  │ 1.日记  │  │ 1.天气  │  │ 1.内存  │
│   组提取│  │   记录  │  │   查询  │  │   缓存  │
│         │  │         │  │         │  │         │
│ 2.Neo4j │  │ 2.节点  │  │ 2.应用  │  │ 2.日志  │
│   存储  │  │   管理  │  │   启动  │  │   文件  │
│         │  │         │  │         │  │         │
│ 3.RAG   │  │ 3.自动  │  │ 3.搜索  │  │ 3.历史  │
│   查询  │  │   总结  │  │   网页  │  │   加载  │
└────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘
     │            │            │            │
     └────────────┴────────────┴────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│               AI 回复生成                             │
│          - 结合 GRAG 事实                             │
│          - 结合 LifeBook 记忆                         │
│          - 结合会话上下文                             │
│          - 结合工具执行结果                            │
└─────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│                 返回给用户                            │
└─────────────────────────────────────────────────────────┘
```

### 6.2 记忆系统集成点

| 集成点 | 调用位置 | 触发条件 |
|--------|---------|---------|
| GRAG 五元组提取 | `message_manager.py:585` | `memory_manager.auto_extract == true` |
| LifeBook 日记记录 | `conversation_analyzer_prompt.txt` | 关键词匹配 / 显式指令 |
| LifeBook AI日记 | `conversation_analyzer_prompt.txt` | 深度对话完成 / 情感交流 |
| 会话上下文加载 | `api_server.py` | `api.persistent_context == true` |

### 6.3 MCP 服务调用链

```
用户请求 
  → MCP Server (mcp_server.py)
    → MCP Manager (mcp_manager.py)
      → MCP Scheduler (mcp_scheduler.py)
        → LifeBook Service (lifebook_service.py)
          → LifeBook Tools (tools.py)
            → Summer Memory Manager (memory_manager.py)
```

---

## 七、配置参数详解

### 7.1 GRAG 配置

```json
{
  "grag": {
    "enabled": true,                          // 是否启用GRAG系统
    "auto_extract": true,                      // 是否自动提取对话五元组
    "context_length": 5,                      // 记忆上下文长度（最近几轮对话）
    "similarity_threshold": 0.6,               // 记忆检索相似度阈值
    "neo4j_uri": "neo4j://127.0.0.1:7687",  // Neo4j连接地址
    "neo4j_user": "neo4j",                   // Neo4j用户名
    "neo4j_password": "your_password",         // Neo4j密码
    "neo4j_database": "neo4j",                // Neo4j数据库名
    "extraction_timeout": 12,                  // 提取超时时间（秒）
    "extraction_retries": 2,                  // 提取重试次数
    "base_timeout": 15                        // 基础超时时间（秒）
  }
}
```

### 7.2 API 配置（影响记忆）

```json
{
  "api": {
    "persistent_context": true,    // 是否启用持久化上下文
    "context_load_days": 3,        // 加载最近N天的日志
    "context_parse_logs": true,    // 是否解析日志文件
    "max_history_rounds": 10      // 最大历史轮次
  }
}
```

### 7.3 系统配置

```json
{
  "system": {
    "diary_enabled": true,        // 是否启用日记功能
    "diary_auto_save": true       // 是否自动保存日记
  }
}
```

### 7.4 配置文件位置

- 主配置文件：`E:\NagaAgent\config.json`
- 提示词文件：`E:\NagaAgent\system\prompts\conversation_analyzer_prompt.txt`

---

## 八、使用示例

### 8.1 GRAG 使用示例

#### 记录事实
```
用户：佳喜欢吃苹果，不喜欢香蕉。
弥娅：记住了，佳喜欢吃苹果，不喜欢香蕉。

[系统自动提取五元组并存储到Neo4j]
```

#### 查询记忆
```
用户：佳喜欢吃什么水果？
弥娅：根据记录，佳喜欢吃苹果，不喜欢香蕉。

[系统从Neo4j查询五元组并生成回答]
```

### 8.2 LifeBook 使用示例

#### 用户主动记录
```
用户：弥娅，记下来，我今天完成了LifeBook功能的测试。
弥娅：好的，弥娅已将此记录到人生书。

[调用LifeBook记录日记工具]
```

#### 主动记录（关键词触发）
```
用户：今天完成了项目的第一阶段，感觉很有成就感。
弥娅：好的，弥娅已将此记录到人生书。这真是值得庆祝的里程碑！

[触发主动记录，调用LifeBook记录工具]
```

#### AI 自主写日记
```
用户：弥娅，你现在也可以写日记了，试试记一下你的日记。
弥娅：好的，佳。弥娅正在尝试记录自己的日记...

[调用LifeBook记录日记工具，author="ai"]
```

### 8.3 综合使用示例

```
用户：今天佳测试了LifeBook功能，遇到了参数传递的问题，弥娅帮助他解决了。
弥娅：好的，弥娅已将此记录到人生书。很高兴能帮到佳！

[系统执行以下操作]
1. GRAG: 提取五元组
   - ("佳", "人物", "测试", "LifeBook功能", "工具")
   - ("佳", "人物", "遇到", "参数传递问题", "事件")
   - ("弥娅", "AI角色", "帮助", "佳", "人物")
   - ("弥娅", "AI角色", "解决", "问题", "事件")

2. LifeBook: 记录日记
   - 用户日记：记录测试过程和问题解决

3. 会话持久化: 保存对话日志
   - logs/2026-01-23.log
```

---

## 九、最佳实践

### 9.1 GRAG 使用建议

1. **Neo4j 服务器**：
   - 确保 Neo4j 容器正在运行（`docker-compose up -d`）
   - 定期备份 Neo4j 数据
   - 监控内存使用情况

2. **五元组提取**：
   - 适合记录事实性信息（"佳喜欢吃苹果"）
   - 不适合记录情感表达（"我很开心"）
   - 定期检查五元组质量，修正错误提取

3. **查询优化**：
   - 使用具体的关键词查询
   - 利用 `context_length` 控制上下文范围
   - 结合 LifeBook 的情感记忆一起使用

### 9.2 LifeBook 使用建议

1. **日记记录**：
   - 保持每日记录，系统会自动整理
   - 使用标签标记重要事件
   - 及时关联相关节点

2. **节点管理**：
   - 给重要人物创建角色节点
   - 给人生阶段创建阶段节点
   - 定期更新节点信息

3. **自动总结**：
   - 定期查看周/月总结
   - 人工微调总结内容
   - 利用 Dataview 数据包让 AI 了解历史

### 9.3 系统协同使用

| 场景 | 使用记忆系统 |
|------|-------------|
| "佳喜欢吃什么水果？" | GRAG（五元组查询） |
| "上次我们聊到什么重要的事情？" | LifeBook（日记浏览） |
| "恢复上次的对话" | 对话持久化（会话加载） |
| "记录今天的工作" | LifeBook（日记记录） + GRAG（事实提取） |
| "总结最近一周的学习内容" | LifeBook（周度总结） |

### 9.4 AI 人格与记忆交互

**情感化对话**：
- 弥娅会主动关心用户状态
- 深度对话后会写自己的日记
- 重要的情感交流会被记录

**自主记忆**：
- 用户说"记下来"时，主动记录
- 工作进展、重要决策自动记录
- 深度对话后自动总结

**双向记忆**：
- 用户可以写日记
- 弥娅也可以写自己的日记
- 两种日记共同构成完整的人生记录

---

## 十、故障排查

### 10.1 GRAG 常见问题

#### Neo4j 连接失败

**症状**：
```
ERROR: GRAG已启用但无法连接到Neo4j
```

**解决方案**：
```bash
# 1. 检查 Neo4j 容器状态
docker ps | grep neo4j

# 2. 启动 Neo4j
cd summer_memory
docker-compose up -d

# 3. 检查连接
curl -u neo4j:your_password http://localhost:7474
```

#### 五元组提取超时

**症状**：
```
WARNING: 五元组提取超时，跳过本次提取
```

**解决方案**：
```json
// config.json
{
  "grag": {
    "extraction_timeout": 30,    // 增加超时时间
    "extraction_retries": 3       // 增加重试次数
  }
}
```

#### 任务管理器未运行

**症状**：
```
WARNING: 任务管理器未运行，正在启动...
```

**解决方案**：
```python
# 系统会自动尝试启动
# 如果启动失败，手动重启系统
```

### 10.2 LifeBook 常见问题

#### 日记写入失败

**症状**：
```
ERROR: 日记内容不能为空
```

**解决方案**：
- 确保传递了 `content` 或 `param_name` 参数
- 检查 LifeBook 目录路径是否正确

#### 节点关联失败

**症状**：
节点无法正确链接到日记

**解决方案**：
- 确保节点名称准确（包括创建日期）
- 使用 `[[节点名称]]` 格式进行链接

#### 数据汇总为空

**症状**：
Dataview 数据包显示为空

**解决方案**：
- 检查日记文件命名格式是否正确
- 确保 Obsidian Dataview 插件已启用
- 检查 Dataview 查询语句是否正确

### 10.3 会话持久化问题

#### 历史记录未加载

**症状**：
重启后无法恢复上次对话

**解决方案**：
```json
// config.json
{
  "api": {
    "persistent_context": true,
    "context_load_days": 3
  }
}
```

#### 日志文件丢失

**症状**：
无法找到历史日志文件

**解决方案**：
- 检查 `logs` 目录是否存在
- 确保有足够的磁盘空间
- 检查文件权限

---

## 十一、总结

NagaAgent 的记忆功能架构采用了**多层次、多模态**的设计理念：

1. **GRAG/Neo4j** - 负责快速、结构化的**事实性记忆**
2. **LifeBook** - 负责丰富、情感化的**长期人生记忆**
3. **对话持久化** - 负责原始的**会话历史记忆**

三者通过 **对话分析器** 自动协调，根据对话内容智能选择记忆方式，实现了**短期记忆到长期记忆的自然过渡**，符合人类记忆的生物学特性。

这种设计既保证了记忆的**检索效率**，又保留了记忆的**情感维度**，是一个兼顾技术和人文的优雅解决方案。

---

**文档版本**：1.0
**最后更新**：2026-01-23
**维护者**：NagaAgent 开发团队
