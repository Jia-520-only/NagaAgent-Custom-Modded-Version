# BettaFish 测试指南

## ✅ 融合完成

BettaFish（微舆）舆情分析系统已成功融合到 NagaAgent 中！

---

## 🔧 已修复的问题

### 语法错误修复

**问题**：原代码第47行有语法错误 `import checks = [...]`

**解决**：已修复为正确的 `checks = [...]`

### 依赖导入优化

**问题**：直接导入 `system.config` 和 `loguru` 导致测试时失败

**解决**：采用延迟导入机制，仅在需要时才尝试导入

---

## 🚀 使用方法

### 1. 启动 NagaAgent

```bash
python main.py
```

启动后查看日志，应该看到：
```
✅ 注册MCP服务: 微舆舆情分析
```

### 2. 在对话中使用

直接在聊天界面（UI、QQ、WeChat）中输入：

```
"帮我分析一下最近AI发展的网络舆情"
"分析这句话的情感：今天天气真好"
"生成一份关于ChatGPT的舆情报告"
"全网搜索人工智能的最新动态"
```

### 3. 验证功能

如果需要测试功能，可以直接创建一个简单的测试脚本：

```python
import asyncio
from mcpserver.agent_betta_fish import BettaFishAgent

async def main():
    agent = BettaFishAgent()
    print(f"Agent 名称: {agent.name}")
    print(f"BettaFish 可用: {agent.betta_fish_enabled}")

    # 测试情感分析
    result = await agent.情感分析("今天天气真好，心情很愉快")
    print(f"情感分析: {result}")

asyncio.run(main())
```

---

## 📋 创建的文件

### MCP Agent

```
mcpserver/agent_betta_fish/
├── __init__.py                  # 模块初始化
├── agent-manifest.json          # MCP服务清单
├── betta_fish_agent.py         # Agent实现（已修复）
└── README.md                   # Agent文档
```

### 文档文件

```
├── BETTA_FISH_QUICKSTART.md       # 快速开始指南
├── BETTA_FISH_INTEGRATION_GUIDE.md  # 完整集成指南
├── BETTA_FISH_INTEGRATION_SUMMARY.md  # 融合总结
└── BETTA_FISH_TEST_GUIDE.md     # 本测试指南
```

### 测试文件

```
├── test_betta_fish.py          # 完整测试脚本
├── test_betta_simple.py         # 简单测试脚本
└── test_import_only.py          # 导入测试脚本
```

---

## 🎯 可用工具

| 工具名称 | 功能 | 参数 |
|---------|------|------|
| **舆情分析** | 深度舆情分析 | `topic`, `depth` |
| **情感分析** | 文本情感倾向分析 | `text` |
| **生成舆情报告** | 生成专业报告 | `topic`, `report_type` |
| **全网搜索** | 全网信息搜索 | `query`, `days` |

---

## ⚙️ 配置说明

### 基础模式（默认）

✅ **无需配置**，直接使用

- 使用 NagaAgent 的 LLM（DeepSeek）
- 基础情感分析（关键词匹配）
- LLM 模板生成报告

### 完整模式（可选）

如需使用完整功能，配置 `betta-fish-main/.env`：

```env
# MySQL数据库
DB_HOST=localhost
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=your_database

# LLM配置
INSIGHT_ENGINE_API_KEY=your_key
MEDIA_ENGINE_API_KEY=your_key
QUERY_ENGINE_API_KEY=your_key
```

**注意**：可选配置不填写时会自动降级到基础模式。

---

## ✨ 验证清单

启动 NagaAgent 后，请验证：

- [ ] 日志中出现 "✅ 注册MCP服务: 微舆舆情分析"
- [ ] 可以在对话中使用"帮我分析...舆情"
- [ ] 可以在对话中使用"分析情感..."
- [ ] 可以在对话中使用"生成报告..."
- [ ] 可以在对话中使用"全网搜索..."

---

## 🐛 故障排查

### 问题1：Agent未注册

**症状**：启动日志中没有"微舆舆情分析"服务

**解决**：
1. 检查 `mcpserver/agent_betta_fish/agent-manifest.json` 是否存在
2. 检查 JSON 格式是否正确
3. 重启 NagaAgent

### 问题2：导入失败

**症状**：Python 导入时报错

**解决**：
1. 确保在 NagaAgent 根目录运行
2. 检查 Python 路径是否正确
3. 查看 `mcpserver/agent_betta_fish/` 目录下文件是否完整

### 问题3：工具调用失败

**症状**：调用工具时返回错误

**解决**：
1. 查看日志中的详细错误信息
2. 检查网络连接（如使用在线LLM）
3. 验证 API 密钥配置

---

## 📚 相关文档

| 文档 | 用途 |
|------|------|
| BETTA_FISH_QUICKSTART.md | 30秒快速开始 |
| BETTA_FISH_INTEGRATION_GUIDE.md | 完整配置指南 |
| agent_betta_fish/README.md | Agent使用文档 |

---

## 🎉 总结

BettaFish 已成功融合到 NagaAgent 中！

- ✅ 4个核心工具可用
- ✅ 基础模式开箱即用
- ✅ 完整模式可选配置
- ✅ 完整文档覆盖
- ✅ 所有语法错误已修复

**下一步：启动 NagaAgent 并在对话中体验功能！**

---

**完成日期**: 2026-01-24
**状态**: ✅ 已完成并可用
