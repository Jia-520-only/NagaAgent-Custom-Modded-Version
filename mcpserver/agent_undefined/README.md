# Undefined工具集成

## 功能说明

这个Agent将Undefined项目中的50+个工具集成到NagaAgent的MCP系统中，使其可以通过QQ消息使用这些工具。

## 支持的工具

Undefined提供了大量实用工具，包括但不限于：

### 搜索类
- `web_search` - 网页搜索（使用SearXNG）
- `baiduhot` - 百度热搜榜
- `weibohot` - 微博热搜榜
- `douyinhot` - 抖音热搜榜
- `bilibili_search` - B站视频搜索
- `bilibili_user_info` - B站用户信息
- `music_global_search` - 音乐搜索
- `music_lyrics` - 歌词查询

### 信息查询类
- `weather_query` - 天气查询
- `get_current_time` - 获取当前时间
- `gold_price` - 黄金价格
- `horoscope` - 星座运势
- `news_tencent` - 腾讯新闻
- `renjian` - 人间日报

### 工具类
- `base64` - Base64编码/解码
- `hash` - 哈希计算
- `tcping` - TCP连通性测试
- `speed` - 网速测试
- `net_check` - 网络检查
- `whois` - 域名查询

### 文件类
- `read_file` - 读取文件
- `search_file_content` - 搜索文件内容
- `list_directory` - 列出目录

### AI类
- `ai_draw_one` - AI绘图（Midjourney）
- `ai_study_helper` - AI学习助手
- `analyze_multimodal` - 多模态分析

## 配置方法

在 `config.json` 中启用Undefined工具：

```json
{
  "qq_wechat": {
    "qq": {
      "enabled": true,
      "enable_undefined_tools": true  // 启用Undefined工具
    }
  }
}
```

## QQ使用方法

### 自动调用

当你在QQ中发送消息时，如果消息内容匹配到某个工具的触发条件，系统会自动调用相应工具：

- **天气查询**：发送 "今天北京的天气" 或 "上海天气"
- **网页搜索**：发送 "搜索AI技术" 或 "查一下人工智能"
- **热搜榜**：发送 "热搜榜"、"百度热搜"、"微博热搜"、"抖音热搜"
- **B站搜索**：发送 "搜索原神视频" 或 "B站找明日方舟"
- **音乐搜索**：发送 "找周杰伦的歌曲" 或 "搜索音乐 稻香"
- **查询时间**：发送 "现在几点" 或 "当前时间"

### 查看可用工具

发送 `/工具` 命令查看所有可用的Undefined工具列表。

### 查看帮助

发送 `/help` 命令查看所有可用的QQ交互指令。

## 示例对话

```
你: 今天北京的天气
机器人: [AI回复] 北京今天天气晴，气温15-25度，空气质量良。

[Naga工具: 天气查询]
北京今天天气晴，气温15-25度，空气质量良。
```

```
你: 搜索AI技术
机器人: [AI回复] 我来帮你搜索AI技术相关信息。

[Undefined工具]
搜索结果:
1. 人工智能技术发展现状...
2. 2024年AI技术趋势...
3. 机器学习最新进展...
```

## 注意事项

1. 部分工具可能需要额外的配置：
   - `web_search` 需要配置 `online_search.searxng_url`
   - `ai_draw_one` 需要配置Midjourney相关参数

2. 工具调用会消耗API调用额度，请注意控制使用频率。

3. 工具执行结果会自动附加在AI回复之后。

## 工作原理

1. QQ消息监听器收到消息
2. 调用AI生成初步回复
3. 触发Undefined工具匹配逻辑
4. 如果匹配到工具，自动调用并获取结果
5. 将工具结果附加到AI回复中发送回QQ

## 故障排查

### Undefined工具未启用

检查 `config.json` 中 `qq_wechat.qq.enable_undefined_tools` 是否为 `true`。

### 工具调用失败

查看日志，确认：
1. Undefined路径是否正确
2. 工具注册表是否成功加载
3. 工具依赖的服务是否可用（如搜索引擎等）

### 搜索功能不可用

确认 `config.json` 中配置了 `online_search.searxng_url`，并且langchain_community已安装。
