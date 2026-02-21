# Undefined工具回调修复报告

## 问题描述

用户反馈Undefined中一些关于QQ的工具用不了：
- 点赞失败
- 云端绘图说工具不存在

## 问题分析

通过分析日志和代码，发现了三个主要问题：

### 问题1: 工具未实际调用
`mcpserver/agent_undefined_mcp/undefined_mcp.py` 中的 `_call_tool_internal` 方法只返回模拟结果，没有真正调用工具。

**原始代码**（问题）:
```python
async def _call_tool_internal(self, tool_name: str, arguments: Dict[str, Any], context: Optional[Dict[str, Any]]):
    return {
        "result": f"工具 {tool_name} 调用成功",
        "tool": tool_name,
        "arguments": arguments
    }
```

### 问题2: 回调函数未注入
Undefined工具（如 `qq_like`）需要 `send_like_callback` 等回调函数，但这些函数没有被注入到工具的context中。

### 问题3: 意图分析器选择错误服务
LLM在看到"点赞"关键词时，错误地选择了 `QQ/微信集成` 服务，而不是 `Undefined工具集` 服务。

### 问题4: 工具调用路径问题
`apiserver/api_server.py` 中的 `_execute_mcp_tool_sync` 函数只对绘图工具（`ai_draw_one`、`local_ai_draw`、`render_and_send_image`）添加了特殊处理，直接调用 `agent.call_tool` 来传递回调函数。**`qq_like` 没有这种特殊处理**，所以走的是通用MCP调用路径，无法传递回调函数。

### 问题5: 关键词缺失
`mcpserver/agent_qq_wechat/message_listener.py` 中的 `tool_keywords` 列表不包含"点赞"关键词，导致意图分析器根本没有被触发。

### 问题6: 意图分析器错误判断"失败+重试"场景
当用户说"又失败了，再给我点赞试试看"时，LLM的意图分析器被第14行规则误导：
> ❌ 不调用工具：用户陈述结果或状态（"测试好了"、"修复完成"、"运行正常"）

这导致LLM将"失败+请求重试"误判为单纯的状态陈述，返回 `agentType: "none"`，不调用工具。

## 修复方案

### 修复1: 实现真实的工具调用
修改 `mcpserver/agent_undefined_mcp/undefined_mcp.py` 的 `_call_tool_internal` 方法：

**修改后的代码**:
```python
async def _call_tool_internal(self, tool_name: str, arguments: Dict[str, Any], context: Optional[Dict[str, Any]]):
    # 构建工具上下文，注入QQ回调函数
    tool_context = context.copy() if context else {}

    # 从MCP注册表获取QQ adapter
    from mcpserver.mcp_registry import get_service_info
    qq_service = get_service_info("QQ/微信集成")
    if qq_service:
        qq_agent = qq_service.get("instance")
        if qq_agent and hasattr(qq_agent, 'qq_adapter'):
            qq_adapter = qq_agent.qq_adapter

            # 构建QQ回调函数
            async def send_like_callback(user_id: int, times: int = 1):
                if qq_adapter:
                    await qq_adapter.send_like(user_id, times)

            async def send_image_callback(target_id: int, msg_type: str, file_path: str):
                if msg_type == "group":
                    await qq_adapter.send_group_message(target_id, file_path, message_type="image")
                else:
                    await qq_adapter.send_private_message(target_id, file_path, message_type="image")

            async def send_message_callback(target_id: int, msg_type: str, message: str):
                if msg_type == "group":
                    await qq_adapter.send_group_message(target_id, message)
                else:
                    await qq_adapter.send_private_message(target_id, message)

            # 注入回调函数到context
            tool_context["send_like_callback"] = send_like_callback
            tool_context["send_image_callback"] = send_image_callback
            tool_context["send_message_callback"] = send_message_callback
            tool_context["sender"] = qq_adapter

    # 使用ToolRegistry调用工具
    result = await self.tool_registry.execute_tool(tool_name, arguments, tool_context)
    return {"result": result, "tool": tool_name, "success": True}
```

### 修复2: 添加明确的服务选择规则
修改 `system/prompts/conversation_analyzer_prompt.txt`，添加QQ工具服务选择规则：

**新增规则**（在第79行之后）:
```
**重要：QQ工具服务选择规则（必须严格遵守！）**
以下工具必须使用 `Undefined工具集` 服务，**不要**使用 `QQ/微信集成` 服务：
- `qq_like` - 点赞功能
- `ai_draw_one` - 云端绘图
- `local_ai_draw` - 本地绘图
- `send_like_callback` - 点赞回调
- `send_image_callback` - 图片发送回调
- `send_message_callback` - 消息发送回调

**规则说明**：
- `QQ/微信集成` 服务只用于基础的**消息发送**功能（send_message等）
- `Undefined工具集` 服务包含所有**功能性工具**（点赞、绘图、搜索等）
- 当用户请求"点赞"、"画图"、"生成图片"时，必须选择 `Undefined工具集` 服务

**示例**：
- 用户："给我点个赞" → `Undefined工具集` + `qq_like`
- 用户："画一只猫" → `Undefined工具集` + `ai_draw_one`
- 用户："生成一张图片" → `Undefined工具集` + `ai_draw_one`
```

### 修复3: 为qq_like添加直接调用支持
修改 `apiserver/api_server.py` 的 `_execute_mcp_tool_sync` 函数，在绘图工具处理逻辑之前添加 `qq_like` 的特殊处理：

**修改后的代码**（在第1089行之前）:
```python
# QQ点赞工具：直接调用以传递回调函数
elif service_name == "Undefined工具集" and tool_name == "qq_like":
    # 直接调用 AgentUndefined，绕过 MCP 调度器，以便传递 context
    from mcpserver.mcp_registry import get_service_info

    service_info = get_service_info("Undefined工具集")
    if service_info:
        agent = service_info.get("instance")
        if agent:
            # 构建QQ回调函数
            async def send_like_callback(user_id: int, times: int = 1):
                try:
                    logger.info(f"[QQ工具 send_like_callback] 点赞: user_id={user_id}, times={times}")
                    # 获取QQ adapter并执行点赞
                    qq_service = get_service_info("QQ/微信集成")
                    if qq_service:
                        qq_agent = qq_service.get("instance")
                        if qq_agent and hasattr(qq_agent, 'qq_adapter'):
                            await qq_agent.qq_adapter.send_like(user_id, times)
                            logger.info(f"[QQ工具 send_like_callback] 点赞成功")
                except Exception as e:
                    logger.error(f"[QQ工具 send_like_callback] 失败: {e}", exc_info=True)

            tool_context = {"send_like_callback": send_like_callback}
            result = await agent.call_tool(tool_name, parameters, context=tool_context)
            logger.info(f"[QQ工具] qq_like直接调用结果: {result[:100]}...")
            return {"tool_name": tool_name, "result": result, "success": True}
```

### 修复4: 添加"点赞"关键词
修改 `mcpserver/agent_qq_wechat/message_listener.py` 的 `tool_keywords` 列表：

**修改后的代码**:
```python
tool_keywords = [
    "天气", "搜索", "画图", "绘图", "打开", "启动", "查询", "优化", "分析", "代码",
    "时间", "几点", "日期", "几点了", "现在几点", "什么时候", "点赞",
    # 以下是工具相关的短语，需要匹配完整短语
    "系统检查", "检查系统", "健康检查", "系统健康", "性能分析",
    "系统优化", "运行优化", "代码质量", "检查代码", "分析代码"
]
```

### 修复5: 修正意图分析器的"失败+重试"判断规则
修改 `system/prompts/conversation_analyzer_prompt.txt`，让LLM能够正确识别"失败后请求重试"的场景：

**修改内容**:
1. **修改用户意图识别规则**（第11-24行）:
```python
**用户意图识别规则**（重要）：
1. **明确请求 vs. 陈述状态**：
   - ✅ 调用工具：用户明确请求操作（"检查系统"、"优化代码"、"查询天气"）
   - ✅ 调用工具：用户陈述失败/问题后请求重试（"又失败了,再试试"、"还是不行,重新给我点赞"）
   - ❌ 不调用工具：用户陈述结果或状态（"测试好了"、"修复完成"、"运行正常"）
...
4. **历史对话处理规则**（重要）：
   - ✅ 只分析最新的一条用户消息
   - ❌ 忽略历史对话中的重复任务
   - ⚠️ **如果用户明确说"再试试"、"再给我X"、"重试"，即使历史中执行过，也要重新调用工具**
   - ✅ 只有在最新用户消息中出现明确的工具请求时才触发
```

2. **添加重要例外**（第151-157行之后）:
```python
**重要：以下情况应调用工具（重试场景）**
- 用户陈述失败后请求重试（"又失败了"、"还是不行" + "再试试"、"再给我点赞"、"重试"）
- 即使历史中执行过相同操作，只要用户明确说"再试试"、"重新X"，就应该调用工具
- 示例："又失败了哇,再给我点赞试试" → 调用点赞工具
- 示例："还是不行，帮我重新画一张" → 调用绘图工具
```

3. **添加示例**（在示例部分）:
```python
输入对话："又失败了哇，再次给我点赞试试看"（失败+重试，调用工具）
期望输出：
｛
"agentType": "mcp",
"service_name": "Undefined工具集",
"tool_name": "qq_like",
"user_id": 1523878699,
"times": 1
｝

输入对话："还是不行，再给我点个赞"（失败+重试，调用工具）
期望输出：
｛
"agentType": "mcp",
"service_name": "Undefined工具集",
"tool_name": "qq_like",
"times": 1
｝

输入对话："又失败了，重新帮我画张猫"（失败+重试，调用工具）
期望输出：
｛
"agentType": "mcp",
"service_name": "Undefined工具集",
"tool_name": "ai_draw_one",
"param_name": "一只猫"
｝
```

## 修复验证

### 验证1: qq_like 工具
用户说："给我点个赞"
- 预期行为：
  1. LLM识别"点赞"关键词，触发意图分析
  2. 意图分析器选择 `Undefined工具集` 的 `qq_like` 工具
  3. API服务器直接调用 `agent.call_tool`，传递 `send_like_callback`
  4. `qq_like` 工具使用回调函数执行点赞
- 预期结果：点赞成功执行

### 验证2: ai_draw_one 工具
用户说："画一只猫"
- 预期行为：LLM选择 `Undefined工具集` 的 `ai_draw_one` 工具
- 预期结果：云端绘图成功执行，图片发送回用户

## 修复文件清单

1. **mcpserver/agent_undefined_mcp/undefined_mcp.py**
   - 修复 `_call_tool_internal` 方法，实现真实工具调用
   - 添加QQ回调函数注入逻辑

2. **system/prompts/conversation_analyzer_prompt.txt**
   - 添加QQ工具服务选择规则
   - 明确指定哪些工具应该使用 `Undefined工具集` 服务

3. **apiserver/api_server.py**
   - 在 `_execute_mcp_tool_sync` 函数中添加 `qq_like` 特殊处理
   - 直接调用 `agent.call_tool` 来传递回调函数

4. **mcpserver/agent_qq_wechat/message_listener.py**
   - 在 `tool_keywords` 列表中添加"点赞"关键词

5. **system/prompts/conversation_analyzer_prompt.txt**
   - 修改用户意图识别规则，明确"失败+重试"应该调用工具
   - 添加重试场景的例外说明
   - 添加"失败+重试"的具体示例

## 注意事项

- 意图分析器的提示词是通过 `system/config.py` 的 `get_prompt()` 动态加载的
- 修改后无需重启系统，下次分析对话时自动生效
- `qq_like` 的回调函数注入现在有两个地方：
  1. `undefined_mcp.py` 的 `_call_tool_internal`（用于MCP协议调用）
  2. `api_server.py` 的 `_execute_mcp_tool_sync`（用于QQ直接调用）

## 测试建议

1. 测试点赞功能："给我点个赞"
2. 测试云端绘图："画一只可爱的猫"
3. 测试本地绘图："用本地模型画风景"
4. 测试失败后重试："又失败了，再给我点赞试试看"
5. 观察日志中是否正确选择了 `Undefined工具集` 服务
6. 观察日志中 `send_like_callback` 是否被正确调用
7. 观察意图分析器是否正确识别"失败+重试"场景

## 修复时间
2025-02-20

## 修复状态
✅ 已完成 - 等待用户验证测试
