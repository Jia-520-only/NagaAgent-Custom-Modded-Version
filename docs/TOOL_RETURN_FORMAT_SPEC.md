# 工具返回格式规范

本文档定义了所有 Undefined 工具和 MCP 工具的统一返回格式规范。

## 标准返回格式

### 推荐格式（TypedDict）

```python
from typing import TypedDict

class ToolResult(TypedDict):
    """工具执行结果的标准格式"""
    success: bool  # 工具是否执行成功
    result: str   # 执行结果的字符串描述
```

### 示例

#### 成功执行
```python
{
    "success": True,
    "result": "🔍 B站搜索 '熊出没' 结果:\n- 熊出没之环球大冒险\n  UP主: 动画乐园\n  链接: https://www.bilibili.com/video/BV123..."
}
```

#### 执行失败
```python
{
    "success": False,
    "result": "搜索失败: 网络连接超时"
}
```

## 实际实现说明

### Undefined 工具

Undefined 工具通常直接返回字符串，MCP Manager 会自动将其包装为标准格式：

```python
# Undefined 工具（bilibili_search/handler.py）
async def execute(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    # ... 执行逻辑 ...
    return output  # 直接返回字符串

# MCP Manager 自动包装（mcp_manager.py:401-406）
result = {"success": True, "result": str(result)}
```

### MCP 工具

MCP 工具应该直接返回标准格式：

```python
# MCP 工具应返回
{
    "success": True,
    "result": "执行结果字符串"
}
```

## 回调处理流程

### tool_result_callback 处理逻辑

位置：`apiserver/api_server.py:1304-1402`

1. **接收回调 payload**
   ```python
   {
       "session_id": "qq_123456789",  # 或 "ui_session_xxx"
       "task_id": "task_uuid",
       "result": {
           "results": [
               {
                   "tool": "bilibili_search",
                   "success": True,
                   "result": {"success": True, "result": "实际结果字符串"}
               }
           ],
           "message": "执行完成"
       },
       "success": True
   }
   ```

2. **解析工具结果**
   - 支持字典格式：`{'success': True, 'result': '...'}`
   - 支持字符串格式：直接的结果文本
   
3. **判断会话类型**
   - QQ 会话：`session_id` 以 `'qq_'` 开头 → 直接发送工具结果给 QQ 用户
   - UI 会话：仅记录日志，不重复生成回复（前端意识已处理）

4. **结果解析代码**
   ```python
   if isinstance(tool_result, dict):
       result_to_send = tool_result.get('result', str(tool_result))
       logger.debug(f"[工具回调] 字典格式结果解析: keys={list(tool_result.keys())}")
   else:
       result_to_send = str(tool_result)
       logger.debug(f"[工具回调] 字符串格式结果: result_type={type(tool_result)}")
   ```

## 类型定义

### 在 `apiserver/api_server.py` 中定义

```python
from typing import TypedDict, Union

# 工具结果标准格式
class ToolResult(TypedDict):
    """工具执行结果的标准格式
    
    所有Undefined工具和MCP工具应遵循此返回格式
    """
    success: bool
    result: str

# 回调payload格式
class CallbackPayload(TypedDict):
    """工具回调payload的标准格式"""
    session_id: str
    task_id: str
    result: Dict[str, Any]
    success: bool

# 单个工具执行结果
class ToolExecutionResult(TypedDict):
    """单个工具的执行结果"""
    tool: str
    success: bool
    result: Union[str, Dict[str, Any]]
```

### 在 `mcpserver/mcp_manager.py` 中定义

```python
from typing import TypedDict

class ToolResult(TypedDict):
    """工具执行结果的标准格式
    
    所有Undefined工具和MCP工具应遵循此返回格式
    """
    success: bool
    result: str
```

## 日志记录改进

### 增强的调试日志

```python
# 记录工具名称
logger.info(f"[工具回调] 工具名称: {tool_name}")

# 详细的结果解析日志
if isinstance(tool_result, dict):
    result_to_send = tool_result.get('result', str(tool_result))
    logger.debug(f"[工具回调] 字典格式结果解析: keys={list(tool_result.keys())}, result_type={type(tool_result.get('result'))}")
else:
    result_to_send = str(tool_result)
    logger.debug(f"[工具回调] 字符串格式结果: result_type={type(tool_result)}")

# 记录发送的消息长度
logger.info(f"[工具回调] 准备发送的消息长度: {len(result_to_send)}")

# 记录发送结果
logger.info(f"[工具回调] 工具结果已发送到QQ: {qq_number}, 消息长度: {len(result_to_send)}")
```

## 最佳实践

1. **统一返回格式**：所有工具应返回 `ToolResult` 格式（或字符串，让 Manager 包装）
2. **详细的日志**：在关键步骤添加调试日志，便于排查问题
3. **类型提示**：使用 TypedDict 提高代码可读性和 IDE 支持
4. **异常处理**：工具应捕获异常并返回友好的错误消息
5. **结果验证**：在发送前验证结果的格式和有效性

## 相关文件

- `apiserver/api_server.py` - 工具回调处理逻辑
- `mcpserver/mcp_manager.py` - MCP Manager 和工具执行包装
- `Undefined/src/Undefined/tools/*/handler.py` - Undefined 工具实现

## 版本历史

- **v1.0** (2026-02-15) - 初始版本，定义统一的工具返回格式规范
