# 弥娅工具调用优化说明

## 📅 优化日期
2026年1月27日

## 🎯 优化目标
减少重复功能工具,让弥娅按照场景和需求选择最合适的工具,避免一个需求多次调用相同类型的工具导致冗余。

---

## 🔍 问题分析

通过分析 `mcpserver` 目录下所有 Agent 的工具定义,发现存在以下重复功能:

### 1. 天气查询重复
- **agent_weather_time**: `today_weather` (今日天气) + `forecast_weather` (未来天气) + `time` (时间)
- **agent_undefined**: `weather_query` (天气查询) + `get_current_time` (获取时间)

### 2. 网页搜索重复
- **agent_online_search**: `网页搜索` (使用SearXNG)
- **agent_undefined**: `web_search` (使用SearXNG)
- **agent_betta_fish**: `全网搜索` (舆情分析专用)
- **agent_playwright_master**: `search` (浏览器交互)

### 3. 网页解析重复
- **agent_crawl4ai**: `网页解析` (输出Markdown格式,适合AI处理)
- **agent_undefined**: `crawl_webpage` (基础爬取)

---

## ✅ 优化措施

### 删除的重复工具

| Agent来源 | 工具名称 | 删除原因 | 替代工具 |
|----------|---------|---------|---------|
| agent_undefined | weather_query | 功能被 agent_weather_time 覆盖 | agent_weather_time.today_weather / forecast_weather |
| agent_undefined | get_current_time | 功能被 agent_weather_time.time 覆盖 | agent_weather_time.time |
| agent_undefined | web_search | 功能被 agent_online_search 覆盖 | agent_online_search.网页搜索 |
| agent_undefined | crawl_webpage | 功能被 agent_crawl4ai 覆盖 | agent_crawl4ai.网页解析 |

### 删除的文件

1. `e:\NagaAgent\Undefined\src\Undefined\tools\web_search\`
2. `e:\NagaAgent\Undefined\src\Undefined\tools\weather_query\`
3. `e:\NagaAgent\Undefined\src\Undefined\tools\get_current_time\`
4. `e:\NagaAgent\Undefined\src\Undefined\tools\crawl_webpage\`

### 修改的文件

1. `e:\NagaAgent\mcpserver\agent_undefined\agent-manifest.json`
   - 删除了4个重复工具的定义
   - 更新了描述,去掉了"网页搜索、天气查询"字样

---

## 📊 优化效果

### 优化前
- 总工具数: 约84个
- 重复工具: 4个
- agent_undefined 工具数: 17个

### 优化后
- 总工具数: 约80个 (减少4个重复)
- 重复工具: 0个
- agent_undefined 工具数: 13个 (减少4个)

---

## 🎯 保留工具的职责划分

### 天气与时间 (agent_weather_time)
- `today_weather`: 查询今日天气
- `forecast_weather`: 查询未来天气预报
- `time`: 查询当前时间(包含城市信息)

**优势**:
- 功能完整,区分今日和未来天气
- 专业的天气API数据
- 时间查询返回更多上下文信息(城市、省份)

### 网页搜索 (agent_online_search)
- `网页搜索`: 通用网页搜索

**优势**:
- 职责单一,代码维护性好
- 专门用于通用搜索场景

### 网页解析 (agent_crawl4ai)
- `网页解析`: 解析网页,返回Markdown格式

**优势**:
- Markdown输出格式对AI友好
- 支持CSS选择器、等待元素等高级功能
- 支持字符数量限制,可控性强

### agent_undefined 保留的工具
- 热搜榜: `baiduhot`, `weibohot`, `douyinhot`
- B站相关: `bilibili_search`, `bilibili_user_info`
- 音乐相关: `music_global_search`, `music_lyrics`
- AI相关: `ai_draw_one`, `ai_study_helper`
- 工具类: `read_file`, `search_file_content`, `base64`
- 其他: `novel_search`, `gold_price`, `horoscope`

**优势**:
- 这些工具功能独特,无重复
- 涵盖了热搜、娱乐、实用工具等场景

---

## 💡 后续优化建议

### 短期优化
1. **增强 agent_online_search**
   - 添加 `num_results` 参数,控制返回结果数量
   - 吸收 web_search 的优点

2. **改进 agent_weather_time**
   - 优化城市参数格式,自动处理各种输入格式
   - 支持简单的城市名输入(如"北京")

3. **文档更新**
   - 在系统提示词中明确推荐使用的工具
   - 更新相关文档,标注已删除的工具

### 中期优化
1. **工具智能推荐**
   - 根据用户意图自动选择最合适的工具
   - 避免LLM在相似工具间徘徊

2. **工具描述优化**
   - 为每个工具添加更详细的描述
   - 标注工具的适用场景和优缺点

### 长期重构
1. **拆分 agent_undefined**
   将大型工具集拆分为多个专职Agent:
   - `agent_hotsearch`: 热搜榜工具
   - `agent_bilibili`: B站相关工具
   - `agent_music`: 音乐相关工具
   - `agent_utils`: 实用工具类
   - `agent_ai`: AI相关工具

2. **工具分类管理**
   - 按功能类别组织工具
   - 建立工具依赖关系图
   - 优化工具调用链

---

## ⚠️ 注意事项

1. **兼容性问题**
   - 如果有代码直接调用了已删除的工具,需要更新调用逻辑
   - 建议检查历史日志,确认是否有调用记录

2. **测试建议**
   - 测试天气查询功能(确保agent_weather_time正常工作)
   - 测试网页搜索功能(确保agent_online_search正常工作)
   - 测试网页解析功能(确保agent_crawl4ai正常工作)

3. **回滚方案**
   - 如需回滚,可从git历史恢复删除的工具目录
   - 恢复 `agent-manifest.json` 中删除的工具定义

---

## 📝 变更记录

| 日期 | 变更内容 | 负责人 |
|-----|---------|-------|
| 2026-01-27 | 删除4个重复工具,优化工具调用 | AI Assistant |

---

## 🔗 相关文件

- `e:\NagaAgent\mcpserver\agent_undefined\agent-manifest.json` - 工具定义文件
- `e:\NagaAgent\mcpserver\agent_weather_time\agent-manifest.json` - 天气时间Agent
- `e:\NagaAgent\mcpserver\agent_online_search\agent-manifest.json` - 网页搜索Agent
- `e:\NagaAgent\mcpserver\agent_crawl4ai\agent-manifest.json` - 网页解析Agent
