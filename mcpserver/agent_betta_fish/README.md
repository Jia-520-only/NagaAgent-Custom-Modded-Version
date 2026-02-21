# 微舆舆情分析 Agent (BettaFish)

将多智能体舆情分析系统融合到NagaAgent中。

## 功能特性

### 基础功能（默认启用）

- ✅ **舆情分析**: 使用LLM生成深度舆情分析
- ✅ **情感分析**: 基于关键词的情感倾向判断
- ✅ **报告生成**: 生成专业舆情分析报告
- ✅ **全网搜索**: 整合NagaAgent搜索能力

### 高级功能（可选配置）

- 🔧 **深度洞察**: 使用InsightEngine进行数据库深度挖掘
- 🔧 **多模态分析**: 使用MediaEngine分析图文视频内容
- 🔧 **论坛协作**: 使用ForumEngine进行Agent辩论
- 🔧 **多源搜索**: 使用QueryEngine聚合多平台搜索

## 可用工具

| 工具名称 | 描述 | 参数 |
|---------|------|------|
| `舆情分析` | 执行舆情深度分析 | `topic`, `depth` |
| `情感分析` | 分析文本情感倾向 | `text` |
| `生成舆情报告` | 生成舆情分析报告 | `topic`, `report_type` |
| `全网搜索` | 全网信息搜索 | `query`, `days` |

## 使用示例

### 对话中使用

```
用户: "帮我分析一下最近AI发展的网络舆情"
用户: "分析这句话的情感：今天心情很好"
用户: "生成一份关于ChatGPT的舆情报告"
用户: "全网搜索人工智能的最新动态"
```

### MCP API调用

```json
{
  "tool_name": "舆情分析",
  "topic": "人工智能",
  "depth": 3
}
```

## 配置说明

### 默认配置（无需配置）

Agent会自动使用NagaAgent的LLM配置，开箱即用。

### 高级配置（可选）

如需使用完整BettaFish功能，配置 `betta-fish-main/.env`：

```env
# MySQL数据库（用于深度分析）
DB_HOST=localhost
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=your_database

# LLM配置（可选，不配置则使用NagaAgent的）
INSIGHT_ENGINE_API_KEY=your_key
MEDIA_ENGINE_API_KEY=your_key
QUERY_ENGINE_API_KEY=your_key
```

详细配置请参考：[BETTA_FISH_INTEGRATION_GUIDE.md](../../../BETTA_FISH_INTEGRATION_GUIDE.md)

## 依赖安装

### 基础模式

无需额外安装，直接使用NagaAgent依赖即可。

### 完整模式

如需使用BettaFish全部功能：

```bash
cd betta-fish-main
pip install -r requirements.txt
```

## 文件结构

```
mcpserver/agent_betta_fish/
├── __init__.py                  # 模块初始化
├── agent-manifest.json          # MCP服务清单
├── betta_fish_agent.py         # Agent主实现
└── README.md                   # 本文档
```

## 工作模式

### 基础模式（默认）

- 使用NagaAgent的LLM（DeepSeek）
- 基础情感分析（关键词匹配）
- LLM模板生成报告
- 无需额外配置

### 完整模式（可选）

- 使用独立BettaFish LLM
- 多语言情感分析模型
- 专业报告引擎
- 需要配置数据库和API密钥

### 混合模式（推荐）

- 根据任务类型智能选择
- 简单任务使用基础模式
- 复杂任务使用完整模式
- 平衡性能和效果

## 故障排查

### 问题：Agent未注册

**检查**：
1. `agent-manifest.json` 文件是否存在
2. JSON格式是否正确
3. 重启NagaAgent

### 问题：工具调用失败

**检查**：
1. 查看日志中的详细错误
2. 检查网络连接
3. 验证API密钥

### 问题：BettaFish模块导入失败

**说明**：这不影响基础功能，Agent会自动降级到基础模式。

如需完整功能，请参考 [BETTA_FISH_INTEGRATION_GUIDE.md](../../../BETTA_FISH_INTEGRATION_GUIDE.md) 进行配置。

## 更新日志

### v1.0.0 (2026-01-24)

- ✅ 初始版本发布
- ✅ 基础功能实现
- ✅ 4个核心工具
- ✅ 对话提示词集成
- ✅ 支持基础模式和完整模式

## 相关文档

- [BettaFish 官方文档](../../../betta-fish-main/README.md)
- [融合集成指南](../../../BETTA_FISH_INTEGRATION_GUIDE.md)
- [NagaAgent MCP开发文档](../../README.md)

## 许可证

本Agent遵循NagaAgent项目的许可证。

BettaFish原项目遵循GPL-2.0许可证。
