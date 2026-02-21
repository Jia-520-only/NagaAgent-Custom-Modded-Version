# VCP记忆工具 - 弥娅与VCPToolBox的桥接层

## 概述

这个模块将VCPToolBox的高级记忆功能集成到弥娅中,通过MCP协议实现无缝对接。

## VCPToolBox核心能力

### 1. TagMemo "浪潮"算法 V4

VCP的RAG检索核心,包含以下高级特性:

- **EPA模块(Embedding Projection Analysis)**:
  - 逻辑深度判断
  - 世界观门控
  - 跨域共振检测

- **残差金字塔(Residual Pyramid)**:
  - 多级语义剥离
  - 微弱信号捕获
  - 相干性分析

- **知识库管理器**:
  - 核心标签特权
  - 逻辑拉回
  - 语义去重

- **偏振语义舵(PSR)**:
  - 犹豫度检测
  - 辩证对冲

### 2. VCP元思考系统

超动态递归思维链,实现结构化深度思考:

- 词元组捕网系统
- 元逻辑模块库
- 超动态递归融合

### 3. 向量数据库

- **存储**: SQLite + better-sqlite3
- **向量索引**: Usearch(或Vexus-Lite Rust引擎)
- **实时监控**: Chokidar文件监控
- **热调参**: 支持RAG参数动态调整

## 融合架构

```
弥娅(NagaAgent)
    ↓ MCP协议
MCP Server
    ↓ HTTP调用
VCPToolBox (Port 6005)
    ↓
VCP TagMemo RAG系统
    ↓
向量数据库(knowledge_base.sqlite)
```

## 安装步骤

### 1. 启动VCPToolBox

```bash
cd VCPToolBox
# 配置环境变量
cp config.env.example config.env
# 编辑config.env,设置API密钥等

# 安装依赖
npm install

# 启动服务
npm start
```

### 2. 配置弥娅

在弥娅的`config.json`中添加:

```json
{
  "vcp": {
    "enabled": true,
    "base_url": "http://127.0.0.1:6005",
    "key": "YOUR_VCP_KEY",
    "auto_sync": true
  }
}
```

### 3. 注册MCP工具

弥娅会自动发现并注册VCP工具:

- `vcp_rag_query`: 使用TagMemo浪潮算法检索记忆
- `vcp_store_memory`: 存储记忆到VCP向量数据库
- `vcp_meta_thinking`: 使用元思考系统进行深度推理
- `vcp_get_stats`: 获取向量数据库统计信息

## 使用示例

### 示例1: 检索相关记忆

用户输入: "我记得上次你提到过关于时间管理的方法"

弥娅会自动调用:
```python
vcp_rag_query(
    query="时间管理的方法",
    top_k=5,
    use_tags=""
)
```

VCP返回:
```json
{
  "success": true,
  "results": [
    {
      "content": "番茄工作法: 25分钟专注 + 5分钟休息",
      "similarity": 0.92,
      "tags": ["效率", "时间管理"],
      "diary_name": "弥娅记忆",
      "timestamp": "2026-01-25T10:30:00"
    }
  ]
}
```

### 示例2: 存储记忆

对话过程中,弥娅自动识别重要信息并存储:

```python
vcp_store_memory(
    content="用户今天测试了VCPToolBox功能,创建了第一个记忆条目",
    tags=["VCP", "记忆", "测试"],
    diary_name="弥娅记忆"
)
```

### 示例3: 元思考推理

当用户需要深度思考时:

用户: "帮我分析一下AI与人类的关系"

弥娅调用:
```python
vcp_meta_thinking(
    theme="problem_solving",
    enable_group=True
)
```

## 与现有记忆系统的关系

### 双层记忆架构

```
现有GRAG系统 (summer_memory/)
    ↓
Neo4j图数据库 (五元组)
    ↓
图谱查询 + 关系推理

VCP记忆系统 (mcpserver/agent_vcp/)
    ↓
SQLite向量数据库 (embedding)
    ↓
TagMemo浪潮RAG + 元思考
```

### 互补优势

| 特性 | GRAG系统 | VCP系统 |
|------|----------|---------|
| 存储格式 | 五元组(图) | 向量(embedding) |
| 检索方式 | 关系遍历 | 语义相似度 |
| 优势 | 结构化关系 | 语义理解 |
| 适用场景 | 事实查询 | 语义检索 |
| 高级特性 | 图谱推理 | 元思考 |

### 协同策略

1. **优先级**: 语义检索(VCP) > 关系查询(GRAG)
2. **混合使用**: 先用VCP找相关记忆,再用GRAG找关联关系
3. **统一接口**: 通过MCP协议统一访问

## 避免冲突的机制

### 1. 数据隔离

- VCP使用独立数据库: `VCPToolBox/knowledge_base.sqlite`
- GRAG使用独立数据库: `neo4j`
- 两者数据互不干扰

### 2. 配置分离

```python
# system/config.py
class VCPConfig(BaseModel):
    enabled: bool = Field(default=False, description="是否启用VCP记忆")
    base_url: str = Field(default="http://127.0.0.1:6005")
    key: str = Field(default="")
    auto_sync: bool = Field(default=True)
```

### 3. 懒加载

VCP代理只在第一次使用时初始化:

```python
_vcp_agent: Optional[VCPAgent] = None

def get_vcp_agent() -> VCPAgent:
    global _vcp_agent
    if _vcp_agent is None:
        _vcp_agent = VCPAgent(...)
    return _vcp_agent
```

## 故障排查

### 问题1: VCP连接失败

检查:
1. VCPToolBox是否启动 (`http://127.0.0.1:6005`)
2. config.json中VCP配置是否正确
3. 防火墙是否允许端口6005

### 问题2: 向量检索无结果

检查:
1. VCP中是否有已存储的记忆
2. embedding模型是否配置正确
3. 向量维度是否匹配

### 问题3: 与GRAG冲突

解决:
- 两个系统独立运行,不会冲突
- 可以选择性启用/禁用任一系统
- 通过MCP统一管理调用

## 未来扩展

### 计划中的功能

1. **双向同步**: GRAG五元组自动同步到VCP
2. **混合检索**: 结合图谱和向量的优势
3. **统一管理面板**: 在弥娅UI中管理VCP记忆
4. **本地VCP**: 将VCP核心移植到Python,集成到弥娅

## 许可证

本模块遵循NagaAgent的许可证。

## 致谢

VCPToolBox原项目: https://github.com/cherry-vip/VCPToolBox

感谢VCPToolBox作者提供的强大记忆系统。
