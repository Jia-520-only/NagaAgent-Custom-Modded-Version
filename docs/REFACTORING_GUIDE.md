# 弥娅系统重构优化指南

## 📊 重构前状态

### 当前结构问题
- **19个MCP服务**，功能重复严重
- **90+个工具**，维护成本高
- **3个重复的网页服务**
- **3个重复的记忆服务**
- **3个重复的视觉服务**
- 大量测试文件和临时文件

### 重复功能识别

#### 🔴 严重重复
1. **网页服务** (3个)
   - `agent_online_search` (searxng搜索)
   - `agent_crawl4ai` (网页解析)
   - `agent_playwright_master` (浏览器自动化)

2. **记忆服务** (3个)
   - `agent_memory` (知识图谱五元组)
   - `agent_lifebook` (日记记忆)
   - `agent_vcp` (向量数据库+RAG)

3. **视觉服务** (3个)
   - `agent_baodou` (视觉自动化)
   - `agent_vision` (视觉识别+OCR)
   - `agent_vcp` (部分视觉功能)

#### 🟡 中度重复
4. **系统控制** (2个)
   - `system_control` (命令执行、亮度、音量)
   - `agent_baodou` (鼠标键盘控制)

5. **信息获取** (2个)
   - `agent_undefined` (热搜榜、音乐、小说)
   - `agent_betta_fish` (舆情分析、全网搜索)

---

## 🎯 重构目标

### 优化指标
| 指标 | 重构前 | 重构后 | 优化 |
|------|--------|--------|------|
| MCP服务数 | 19 | 12 | -37% |
| 核心服务数 | 19 | 7 | -63% |
| 代码文件数 | 100+ | 70-80 | -30% |
| 冗余代码 | ~30% | <5% | -83% |
| 维护复杂度 | 高 | 中 | -50% |

---

## 🏗️ 重构方案

### 阶段一：清理冗余（1-2天）

#### 1.1 清理测试文件
```bash
# 删除的文件列表
test_baodou_simple.py
test_baodou_integration.py
test_baodou_standalone.py
test_consciousness_simple.py
test_task_reminder.py
test_temporal_fix.py
test_time_awareness_simple.py
test_consciousness.bat
test_output.log
```

#### 1.2 整合文档文件
```bash
# 保留核心文档
README.md
BAODOU_INTEGRATION_GUIDE.md → docs/BAODOU_GUIDE.md
VCP_INTEGRATION_GUIDE.md → docs/VCP_GUIDE.md
INTEGRATION_SUMMARY.md → docs/INTEGRATION_SUMMARY.md
# 删除状态文件和报告文件
BAODOU_INTEGRATION_STATUS.md
VCP_INTEGRATION_STATUS.md
DEPENDENCY_INSTALLATION_FINAL.md
DEPENDENCY_INSTALLATION_REPORT.md
```

#### 1.3 处理外部项目
```bash
# 保留目录但添加说明
betta-fish-main/ → external/betta-fish/ (带README说明)
baodou_AI/ → external/baodou/ (带README说明)
```

---

### 阶段二：合并重复服务（3-5天）

#### 2.1 网页服务合并 (3→1)

**合并前**:
- `agent_online_search` (searxng)
- `agent_crawl4ai` (网页解析)
- `agent_playwright_master` (浏览器)

**合并后**: `agent_web_unified`

**工具列表**:
```json
{
  "tools": [
    {
      "name": "web_search",
      "description": "统一网页搜索，支持多种搜索引擎",
      "parameters": {
        "query": "搜索关键词",
        "engine": "searxng|google|bing",
        "count": "结果数量"
      }
    },
    {
      "name": "web_crawl",
      "description": "智能网页内容抓取，支持静态和动态页面",
      "parameters": {
        "url": "目标URL",
        "mode": "static|dynamic",
        "format": "markdown|html|text"
      }
    },
    {
      "name": "web_browse",
      "description": "浏览器自动化操作，支持点击、输入、滚动",
      "parameters": {
        "url": "起始URL",
        "actions": "操作列表"
      }
    },
    {
      "name": "web_parse",
      "description": "智能内容解析，提取关键信息",
      "parameters": {
        "content": "网页内容",
        "extract_type": "text|links|images|table"
      }
    }
  ]
}
```

**实现要点**:
- 保留各服务的核心功能
- 使用策略模式选择合适的引擎
- 统一错误处理和日志
- 支持多引擎搜索

#### 2.2 记忆服务合并 (3→1)

**合并前**:
- `agent_memory` (知识图谱五元组)
- `agent_lifebook` (日记记忆)
- `agent_vcp` (向量数据库+RAG)

**合并后**: `agent_memory_unified`

**工具列表**:
```json
{
  "tools": [
    {
      "name": "store_memory",
      "description": "统一记忆存储，自动选择最优存储方式",
      "parameters": {
        "content": "记忆内容",
        "type": "auto|knowledge|diary|vector",
        "metadata": "元数据"
      }
    },
    {
      "name": "recall_memory",
      "description": "智能回忆，支持多种查询方式",
      "parameters": {
        "query": "查询内容",
        "mode": "semantic|keyword|graph",
        "limit": "结果数量"
      }
    },
    {
      "name": "generate_summary",
      "description": "生成时间总结（日/周/月/季）",
      "parameters": {
        "period": "day|week|month|quarter",
        "topic": "主题过滤"
      }
    },
    {
      "name": "manage_nodes",
      "description": "知识节点管理",
      "parameters": {
        "action": "create|update|delete|list",
        "node_data": "节点数据"
      }
    }
  ]
}
```

**实现要点**:
- 多存储后端支持（Neo4j/文件/向量数据库）
- 智能路由：根据内容类型选择存储方式
- 统一查询接口
- 跨存储后端融合检索

#### 2.3 视觉服务合并 (3→1)

**合并前**:
- `agent_baodou` (视觉自动化)
- `agent_vision` (视觉识别+OCR)
- `agent_vcp` (部分视觉功能)

**合并后**: `agent_vision_unified`

**工具列表**:
```json
{
  "tools": [
    {
      "name": "capture_screen",
      "description": "屏幕截图",
      "parameters": {
        "region": "屏幕区域",
        "format": "png|jpg",
        "save_path": "保存路径"
      }
    },
    {
      "name": "analyze_screen",
      "description": "智能屏幕分析（OCR+理解）",
      "parameters": {
        "image": "图像或截图",
        "mode": "ocr|object|scene|full"
      }
    },
    {
      "name": "visual_automation",
      "description": "视觉自动化控制",
      "parameters": {
        "task": "任务描述",
        "max_iterations": "最大迭代次数",
        "safe_mode": "安全模式"
      }
    },
    {
      "name": "ocr_text",
      "description": "OCR文字识别",
      "parameters": {
        "image": "图像",
        "language": "语言"
      }
    }
  ]
}
```

**实现要点**:
- 统一屏幕接口
- 多OCR引擎支持
- 智能任务规划（复用baodou的逻辑）
- 安全模式增强

---

### 阶段三：整合工具集（2-3天）

#### 3.1 统一信息获取服务

**合并**: `agent_undefined` + `agent_betta_fish` → `agent_info_unified`

**工具分类**:
- 热搜榜（百度/微博/抖音）
- 音乐搜索和歌词
- 小说搜索
- B站相关
- 舆情分析
- 全网搜索
- 实时信息查询

#### 3.2 整合系统控制

**合并**: `system_control` → `agent_vision_unified` 的子系统

**工具列表**:
- command: 执行系统指令
- brightness: 屏幕亮度
- volume: 系统音量

---

### 阶段四：创建公共工具库（2-3天）

#### 4.1 目录结构
```
mcpserver/common/
├── __init__.py
├── http_client.py       # 统一HTTP客户端
├── cache_manager.py      # 缓存管理
├── error_handler.py     # 错误处理
├── logger.py           # 统一日志
├── tool_base.py        # 工具基类
├── validators.py       # 数据验证
└── metrics.py          # 指标收集
```

#### 4.2 核心功能
- HTTP客户端：连接池、重试、超时
- 缓存：内存缓存、磁盘缓存、LRU
- 错误处理：统一异常类、错误码
- 日志：结构化日志、分级输出
- 工具基类：标准化工具实现

---

### 阶段五：更新配置文件结构（1-2天）

#### 5.1 新配置结构
```json
{
  "services": {
    "core": {
      "memory_unified": {
        "enabled": true,
        "backends": {
          "neo4j": {...},
          "vcp": {...},
          "lifebook": {...}
        }
      },
      "vision_unified": {
        "enabled": true,
        "ocr": {...},
        "automation": {...}
      },
      "web_unified": {
        "enabled": true,
        "search_engines": {...},
        "browser": {...},
        "crawler": {...}
      },
      "info_unified": {
        "enabled": true,
        "hot_search": {...},
        "music": {...},
        "sentiment": {...}
      }
    },
    "social": {
      "qq_wechat": {...}
    },
    "tools": {
      "office_word": {...},
      "comic_downloader": {...},
      "mqtt_tool": {...},
      "weather_time": {...},
      "open_launcher": {...},
      "naga_portal": {...}
    }
  }
}
```

---

## 📋 重构执行清单

### ✅ 阶段一：清理冗余
- [ ] 删除测试文件（8个文件）
- [ ] 整理文档文件（移动6个文件到docs/）
- [ ] 处理外部项目（移动到external/）

### ✅ 阶段二：合并重复服务
- [ ] 创建 agent_web_unified
- [ ] 创建 agent_memory_unified
- [ ] 创建 agent_vision_unified

### ✅ 阶段三：整合工具集
- [ ] 创建 agent_info_unified
- [ ] 整合 system_control

### ✅ 阶段四：创建公共工具库
- [ ] 创建 mcpserver/common/ 目录
- [ ] 实现 http_client.py
- [ ] 实现 cache_manager.py
- [ ] 实现 error_handler.py
- [ ] 实现 logger.py

### ✅ 阶段五：更新配置
- [ ] 重构 config.json
- [ ] 更新 system/config.py
- [ ] 更新各服务的配置加载逻辑

---

## 🚀 重构后架构

### 服务分层
```
┌─────────────────────────────────────┐
│        应用层（API/UI）             │
├─────────────────────────────────────┤
│      服务编排层（Handoff）          │
├─────────────────────────────────────┤
│  ┌─────────┬─────────┬─────────┐    │
│  │ 核心服务 │ 社交服务 │ 工具服务 │    │
│  ├─────────┼─────────┼─────────┤    │
│  │记忆服务 │ QQ/微信  │ Word处理│    │
│  │视觉服务 │          │ 漫画下载│    │
│  │网页服务 │          │ 天气时间│    │
│  │信息服务 │          │ 物联网  │    │
│  └─────────┴─────────┴─────────┘    │
├─────────────────────────────────────┤
│      MCP协议层（统一调用）          │
├─────────────────────────────────────┤
│   nagaagent_core（核心库）          │
└─────────────────────────────────────┘
```

### 最终服务列表（12个）

#### 核心服务（4个）
1. **agent_memory_unified** - 统一记忆服务
2. **agent_vision_unified** - 统一视觉服务
3. **agent_web_unified** - 统一网页服务
4. **agent_info_unified** - 统一信息服务

#### 社交服务（1个）
5. **agent_qq_wechat** - QQ/微信集成

#### 工具服务（7个）
6. **agent_office_word** - Office Word处理
7. **agent_comic_downloader** - 漫画下载
8. **agent_mqtt_tool** - 物联网控制
9. **agent_weather_time** - 天气时间查询
10. **agent_open_launcher** - 应用启动器
11. **agent_naga_portal** - 娜迦充值服务
12. **agent_self_optimization** - 自我优化系统

---

## 📊 预期收益

### 性能提升
- 减少服务调用开销（-40%）
- 降低内存占用（-30%）
- 提高响应速度（+25%）

### 维护性提升
- 代码重复率降低（-83%）
- 文档清晰度提升（+50%）
- 新功能开发速度提升（+40%）

### 可扩展性提升
- 服务间耦合降低（-50%）
- 插件化支持（+100%）
- 配置灵活性提升（+60%）

---

## ⚠️ 注意事项

### 兼容性保证
1. 保留旧服务的API别名
2. 添加版本兼容层
3. 渐进式迁移方案
4. 充分的回滚准备

### 测试要求
1. 单元测试覆盖率 >80%
2. 集成测试覆盖核心流程
3. 性能基准测试
4. 兼容性测试

### 文档要求
1. 每个新服务有完整README
2. API文档自动生成
3. 迁移指南
4. 变更日志

---

## 📅 时间估算

| 阶段 | 工作量 | 预计时间 |
|------|--------|----------|
| 阶段一：清理冗余 | 低 | 1-2天 |
| 阶段二：合并重复服务 | 高 | 3-5天 |
| 阶段三：整合工具集 | 中 | 2-3天 |
| 阶段四：创建公共工具库 | 中 | 2-3天 |
| 阶段五：更新配置文件 | 低 | 1-2天 |
| 测试与验证 | 高 | 2-3天 |
| 文档更新 | 中 | 1-2天 |
| **总计** | - | **12-20天** |

---

## 🎯 成功标准

1. ✅ 服务数量从19个减少到12个（-37%）
2. ✅ 代码重复率从30%降低到<5%
3. ✅ 所有现有功能正常工作
4. ✅ 性能提升至少20%
5. ✅ 文档覆盖率100%
6. ✅ 测试覆盖率>80%

---

**版本**: v1.0.0
**创建日期**: 2026-01-28
**最后更新**: 2026-01-28
