# Skills 工具示例

本目录包含已整合的工具示例。

## 已整合工具

### get_current_time

获取当前系统时间的示例工具。

**使用示例:**

```python
from common.skills import ToolRegistry

# 初始化
registry = ToolRegistry("common/skills/tools")
registry.load_items()

# 执行
result = await registry.execute("get_current_time", {}, {})
print(result)  # 2024-01-15 10:30:45
```

## 添加自定义工具

### 1. 创建目录

```bash
mkdir common/skills/tools/my_tool
```

### 2. 创建配置文件 `config.json`

```json
{
  "type": "function",
  "function": {
    "name": "my_tool",
    "description": "工具描述",
    "parameters": {
      "type": "object",
      "properties": {
        "param1": {
          "type": "string",
          "description": "参数描述"
        }
      },
      "required": ["param1"]
    }
  }
}
```

### 3. 创建处理器 `handler.py`

```python
async def execute(args: dict, context: dict) -> str:
    """执行工具逻辑"""
    param1 = args.get("param1", "")
    # 处理逻辑
    return f"处理结果: {param1}"
```

### 4. 重新加载工具

```python
registry.load_items()
```

## 工具开发最佳实践

1. **参数验证**: 在 `execute` 函数中验证必需参数
2. **错误处理**: 使用 try-except 捕获异常并返回友好消息
3. **日志记录**: 使用 `logging` 模块记录执行日志
4. **上下文使用**: 通过 `context` 参数获取请求上下文信息

## 示例：带日志的工具

```python
import logging
from common.context import get_request_id

logger = logging.getLogger(__name__)

async def execute(args: dict, context: dict) -> str:
    """带日志的工具示例"""
    request_id = get_request_id()
    logger.info(f"[{request_id}] 执行工具: my_tool")

    try:
        # 业务逻辑
        return "成功"
    except Exception as e:
        logger.error(f"[{request_id}] 工具执行失败: {e}")
        return f"执行失败: {str(e)}"
```
