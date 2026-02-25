# 🎓 Undefined 项目超级完整学习指南
## 从零开始精通 Python 和这个 QQ 机器人项目

---

## 📚 目录

1. [学习前的准备](#学习前的准备)
2. [第一章:项目是什么](#第一章项目是什么)
3. [第二章:程序如何运行](#第二章程序如何运行)
4. [第三章:配置系统详解](#第三章配置系统详解)
5. [第四章:AI核心系统](#第四章ai核心系统)
6. [第五章:消息处理机制](#第五章消息处理机制)
7. [第六章:技能系统](#第六章技能系统)
8. [第七章:存储系统](#第七章存储系统)
9. [第八章:工具和辅助模块](#第八章工具和辅助模块)
10. [第九章:Python核心知识点总结](#第九章python核心知识点总结)
11. [第十章:实战练习](#第十章实战练习)

---

## 🎯 学习前的准备

### 你需要什么?
- ✅ 一台电脑(Windows/Mac/Linux都可以)
- ✅ Python 3.11 或更高版本
- ✅ 一个代码编辑器(推荐VSCode)
- ✅ 这份学习文档

### 如何使用这份文档?
1. 📖 按顺序阅读每一章
2. 💻 动手实践每章的代码示例
3. 🤔 思考和理解每个概念
4. ✅ 完成每章的练习题

### 学习目标
通过这个项目,你将学会:
- ✅ Python 基础语法
- ✅ 面向对象编程
- ✅ 异步编程(async/await)
- ✅ 网络编程(HTTP/WebSocket)
- ✅ 配置管理
- ✅ AI API 调用
- ✅ 模块化设计
- ✅ 项目实战经验

---

## 第一章:项目是什么

### 1.1 Undefined 是什么?

**Undefined** 是一个智能的 QQ 机器人,它有很多强大的功能:

#### 🤖 核心功能
1. **智能对话** - 使用 AI (如 DeepSeek、Claude、GPT) 和用户聊天
2. **搜索能力** - 可以搜索网络信息
3. **写代码** - 可以帮你写代码、分析代码
4. **文件分析** - 可以分析 PDF、Word、Excel、PPT 等文件
5. **知识库** - 可以存储和查询知识
6. **定时任务** - 可以设置定时提醒
7. **B站视频** - 自动下载 B 站视频
8. **多模态** - 理解图片内容

#### 🏗️ 技术特点
- **异步架构** - 可以同时处理多个请求
- **模块化设计** - 代码组织清晰,易于扩展
- **配置热更新** - 修改配置后不需要重启
- **工具系统** - 可以轻松添加新功能
- **智能 Agent** - 有多个专门的助手分工协作

### 1.2 项目结构总览

```
Undefined/
├── src/Undefined/          # 主要源代码
│   ├── __main__.py         # 程序入口
│   ├── main.py             # 主程序
│   ├── config/             # 配置系统
│   ├── ai/                 # AI 核心系统
│   ├── handlers.py         # 消息处理器
│   ├── onebot.py           # QQ 协议连接
│   ├── skills/             # 技能系统
│   ├── services/           # 核心服务
│   ├── utils/              # 工具函数
│   ├── webui/              # Web 管理界面
│   ├── bilibili/           # B站视频处理
│   └── knowledge/          # 知识库
├── config.toml             # 主配置文件
├── config.toml.example     # 配置示例
├── data/                   # 数据存储目录
├── res/                    # 资源文件
└── docs/                   # 文档
```

### 1.3 核心模块简介

| 模块 | 作用 | 重要程度 |
|------|------|----------|
| `main.py` | 程序入口,启动所有组件 | ⭐⭐⭐⭐⭐ |
| `config/` | 配置加载和管理 | ⭐⭐⭐⭐⭐ |
| `ai/` | AI 对话和工具调用 | ⭐⭐⭐⭐⭐ |
| `handlers.py` | 消息处理和路由 | ⭐⭐⭐⭐⭐ |
| `onebot.py` | QQ 协议连接 | ⭐⭐⭐⭐ |
| `skills/` | 工具和 Agent | ⭐⭐⭐⭐ |
| `services/` | 队列、命令、安全 | ⭐⭐⭐⭐ |
| `utils/` | 工具函数 | ⭐⭐⭐ |

---

## 第二章:程序如何运行

### 2.1 程序启动流程

当你运行 `python -m Undefined` 时,会发生什么?

```
第1步: 执行 __main__.py
    ↓
第2步: 调用 main.py 的 run() 函数
    ↓
第3步: 运行 asyncio.run(main())
    ↓
第4步: 执行 main() 异步函数
    ├─ 设置日志系统
    ├─ 创建必要的目录
    ├─ 检查 Git 更新
    ├─ 加载配置文件
    ├─ 初始化核心组件
    │   ├─ OneBotClient (QQ 连接)
    │   ├─ MemoryStorage (记忆存储)
    │   ├─ AIClient (AI 客户端)
    │   ├─ MessageHandler (消息处理)
    │   └─ 其他组件...
    ├─ 启动配置热更新
    └─ 连接 QQ 并开始运行
```

### 2.2 入口文件详解

#### 文件1: `src/Undefined/__main__.py`

这个文件只有6行代码,非常简单:

```python
"""允许 python -m Undefined 运行"""

from Undefined.main import run

if __name__ == "__main__":
    run()
```

**逐行解释**:

1. `"""允许 python -m Undefined 运行"""` - 文档字符串,说明这个文件的作用
2. `from Undefined.main import run` - 从 `Undefined.main` 模块导入 `run` 函数
3. 空行 - 分隔导入和代码
4. `if __name__ == "__main__":` - 检查文件是否被直接运行
5. `    run()` - 如果是直接运行,就调用 `run()` 函数

**知识点**:
- `__name__` 是 Python 的内置变量
- 当文件被直接运行时,`__name__` 的值是 `"__main__"`
- 当文件被导入时,`__name__` 的值是模块名
- 这行代码确保只有在直接运行时才执行,导入时不会执行

---

#### 文件2: `src/Undefined/main.py`

这是程序的核心入口文件,让我们看看关键代码:

```python
import asyncio
import logging
import time
import sys
from pathlib import Path

from Undefined.ai import AIClient
from Undefined.config import get_config
from Undefined.onebot import OneBotClient
from Undefined.handlers import MessageHandler
# ... 更多导入 ...

def ensure_runtime_dirs() -> None:
    """确保运行时目录存在"""
    runtime_dirs = [
        Path("data"),
        Path("data/history"),
        Path("data/faq"),
        Path("cache"),
        # ... 更多目录
    ]
    for path in runtime_dirs:
        path.mkdir(parents=True, exist_ok=True)

def setup_logging() -> None:
    """设置日志系统"""
    # 创建日志处理器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 文件处理器
    handler = logging.FileHandler("undefined.log")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s"
    ))
    logger.addHandler(handler)

async def main() -> None:
    """主函数"""
    # 步骤1: 设置日志
    setup_logging()

    # 步骤2: 创建目录
    ensure_runtime_dirs()

    # 步骤3: 加载配置
    try:
        config = get_config()
        logger.info(f"机器人QQ: {config.bot_qq}")
    except ValueError as exc:
        logger.error(f"配置错误: {exc}")
        sys.exit(1)

    # 步骤4: 初始化组件
    onebot = OneBotClient(config.onebot_ws_url, config.onebot_token)
    ai = AIClient(
        config.chat_model,
        config.vision_model,
        config.agent_model,
        bot_qq=config.bot_qq,
        runtime_config=config,
    )
    handler = MessageHandler(config, onebot, ai, ...)

    # 步骤5: 启动运行
    logger.info("机器人已准备就绪,开始连接...")
    try:
        await onebot.run_with_reconnect()
    except KeyboardInterrupt:
        logger.info("收到退出信号")
    finally:
        # 清理资源
        await onebot.disconnect()
        await ai.close()

def run() -> None:
    """运行入口"""
    asyncio.run(main())

if __name__ == "__main__":
    run()
```

**关键概念解释**:

1. **异步函数 (`async def`)**
   - `async def main()` 定义了一个异步函数
   - 异步函数内部可以使用 `await` 等待异步操作
   - 适合处理网络请求、文件IO等耗时操作

2. **事件循环 (`asyncio.run`)**
   - `asyncio.run(main())` 启动事件循环
   - 事件循环负责调度和执行异步任务
   - 可以同时处理多个异步操作

3. **路径操作 (`pathlib.Path`)**
   - `Path("data")` 创建路径对象
   - `path.mkdir(parents=True, exist_ok=True)` 创建目录
   - `parents=True` 会创建父目录
   - `exist_ok=True` 如果目录已存在不会报错

4. **错误处理 (`try-except`)**
   - `try:` 尝试执行可能出错的代码
   - `except ValueError:` 捕获特定错误
   - `finally:` 无论是否出错都会执行

5. **日志记录 (`logging`)**
   - `logger.info()` 记录信息日志
   - `logger.error()` 记录错误日志
   - `logger.warning()` 记录警告日志

### 2.3 Python 基础知识点

#### 知识点1: 导入模块

```python
# 方式1: 导入整个模块
import asyncio
asyncio.run(main())

# 方式2: 从模块导入特定函数
from pathlib import Path
path = Path("data")

# 方式3: 导入并重命名
import logging as log
log.info("信息")

# 方式4: 导入多个
from x import a, b, c
```

#### 知识点2: 函数定义

```python
# 无参数函数
def hello():
    print("Hello!")

# 有参数函数
def greet(name):
    print(f"Hello, {name}!")

# 有默认值参数
def greet(name, greeting="Hello"):
    print(f"{greeting}, {name}!")

# 有返回值
def add(a, b):
    return a + b

# 异步函数
async def async_function():
    await asyncio.sleep(1)
    return "完成"
```

#### 知识点3: 类型提示

```python
# 基本类型
def add(a: int, b: int) -> int:
    return a + b

# 可选类型(可能为None)
def get_user(id: int) -> dict | None:
    if id == 0:
        return None
    return {"id": id, "name": "User"}

# 列表类型
def process(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}

# 复杂类型
from typing import Optional, List, Dict

def search(
    query: str,
    limit: int = 10,
    filters: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    pass
```

---

## 第三章:配置系统详解

### 3.1 配置系统概述

**配置系统的作用**:
- 读取配置文件
- 验证配置有效性
- 提供配置给程序使用
- 支持配置热更新

### 3.2 配置文件格式

项目使用 **TOML** 格式的配置文件:

```toml
# 注释: 以 # 开头

# 核心配置
[core]
bot_qq = 123456789              # 机器人QQ号
superadmin_qq = 987654321       # 超级管理员
admin_qq = [111, 222, 333]     # 管理员列表
process_every_message = true    # 是否处理每条消息

# 访问控制
[access]
mode = "off"                    # 访问模式
allowed_group_ids = []          # 允许的群号
blocked_group_ids = []          # 禁止的群号

# OneBot配置
[onebot]
ws_url = "ws://127.0.0.1:3001"  # WebSocket地址
token = ""                      # 访问令牌

# AI模型配置
[models.chat]
api_url = "https://api.openai.com/v1"
api_key = "sk-xxxxx"
model_name = "gpt-4"
max_tokens = 8192
```

**TOML 基本语法**:
- 注释以 `#` 开头
- 键值对用 `=` 连接
- 字符串用双引号
- 布尔值是 `true` 或 `false`
- 列表用 `[]`
- 分组用 `[section]`

### 3.3 数据类 (dataclass)

Python 的 `dataclass` 是一种简化类定义的方式:

```python
from dataclasses import dataclass

# 定义数据类
@dataclass
class Person:
    name: str
    age: int
    email: str = "unknown@example.com"  # 默认值

# 使用
person = Person(name="小明", age=18)
print(person.name)  # 小明
print(person.age)   # 18
print(person.email) # unknown@example.com (默认值)
```

**对比普通类**:

```python
# 普通类(需要写很多代码)
class Person:
    def __init__(self, name: str, age: int, email: str = "unknown@example.com"):
        self.name = name
        self.age = age
        self.email = email

    def __repr__(self):
        return f"Person(name={self.name!r}, age={self.age!r}, email={self.email!r})"

# dataclass(自动生成)
@dataclass
class Person:
    name: str
    age: int
    email: str = "unknown@example.com"
    # __init__ 和 __repr__ 自动生成!
```

**项目中的应用** - `config/models.py`:

```python
@dataclass
class ChatModelConfig:
    """对话模型配置"""

    api_url: str
    api_key: str
    model_name: str
    max_tokens: int
    queue_interval_seconds: float = 1.0
    thinking_enabled: bool = False
    thinking_budget_tokens: int = 20000

@dataclass
class VisionModelConfig:
    """视觉模型配置"""

    api_url: str
    api_key: str
    model_name: str
    queue_interval_seconds: float = 1.0
    thinking_enabled: bool = False
```

### 3.4 配置加载器

配置加载器的核心流程:

```
1. 读取 config.toml
    ↓
2. 解析 TOML 为字典
    ↓
3. 转换为 Config 数据类
    ↓
4. 验证配置有效性
    ↓
5. 返回配置对象
```

**简化版的配置加载器**:

```python
import toml
from pathlib import Path
from typing import Any

class ConfigLoader:
    """配置加载器"""

    def load(self, file_path: str) -> dict[str, Any]:
        """加载配置文件"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            config = toml.load(f)

        # 验证必需字段
        required_fields = ["core", "onebot", "models"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"配置缺少必需字段: {field}")

        return config

# 使用
loader = ConfigLoader()
config = loader.load("config.toml")
print(config["core"]["bot_qq"])
```

### 3.5 配置热更新

**什么是热更新?**
- 程序运行时自动检测配置文件变化
- 不需要重启程序
- 自动重新加载配置

**实现原理**:

```python
import asyncio
from pathlib import Path

class ConfigWatcher:
    """配置文件监控器"""

    def __init__(self, config_path: str, callback):
        self.config_path = Path(config_path)
        self.callback = callback
        self.last_mtime = self._get_mtime()

    def _get_mtime(self) -> float:
        """获取文件修改时间"""
        return self.config_path.stat().st_mtime

    async def watch(self, interval: float = 1.0):
        """开始监控"""
        while True:
            await asyncio.sleep(interval)

            # 检查文件是否修改
            current_mtime = self._get_mtime()
            if current_mtime != self.last_mtime:
                print("检测到配置变化,重新加载...")
                self.last_mtime = current_mtime

                # 调用回调函数
                if self.callback:
                    self.callback()

# 使用
async def on_config_changed():
    print("配置已更新!")
    # 重新加载配置...

watcher = ConfigWatcher("config.toml", on_config_changed)
await watcher.watch()
```

### 3.6 实战练习

**练习1: 创建配置文件**

创建 `my_config.toml`:

```toml
[app]
name = "MyApp"
version = "1.0.0"
debug = true

[server]
host = "127.0.0.1"
port = 8080

[database]
url = "sqlite:///app.db"
max_connections = 10
```

**练习2: 读取配置**

```python
import toml

# 读取配置
with open("my_config.toml", "r", encoding="utf-8") as f:
    config = toml.load(f)

# 访问配置
print(f"应用名称: {config['app']['name']}")
print(f"服务器地址: {config['server']['host']}:{config['server']['port']}")
print(f"数据库URL: {config['database']['url']}")
```

**练习3: 创建配置数据类**

```python
from dataclasses import dataclass

@dataclass
class AppConfig:
    name: str
    version: str
    debug: bool = False

@dataclass
class ServerConfig:
    host: str
    port: int = 8080

@dataclass
class DatabaseConfig:
    url: str
    max_connections: int = 10

# 转换字典为数据类
app_config = AppConfig(**config['app'])
server_config = ServerConfig(**config['server'])
db_config = DatabaseConfig(**config['database'])

print(app_config.name)  # MyApp
print(server_config.port)  # 8080
```

---

## 第四章:AI核心系统

### 4.1 AI 系统架构

AI 系统的核心流程:

```
用户消息
    ↓
AICoordinator 协调器
    ↓
PromptBuilder 构建提示词
    ├─ 注入历史消息
    ├─ 注入长期记忆
    ├─ 注入知识库
    └─ 注入系统提示词
    ↓
ModelRequester 调用 AI API
    ↓
AI 返回回复 + 工具调用
    ↓
ToolManager 执行工具
    ↓
返回最终结果
```

### 4.2 AIClient 核心类

`AIClient` 是 AI 系统的主入口:

```python
class AIClient:
    """AI 模型客户端"""

    def __init__(
        self,
        chat_config: ChatModelConfig,
        vision_config: VisionModelConfig,
        agent_config: AgentModelConfig,
        memory_storage: Optional[MemoryStorage] = None,
        bot_qq: int = 0,
        runtime_config: Config | None = None,
    ):
        # 保存配置
        self.chat_config = chat_config
        self.vision_config = vision_config
        self.agent_config = agent_config
        self.bot_qq = bot_qq

        # 初始化组件
        self._http_client = httpx.AsyncClient(timeout=480.0)
        self._requester = ModelRequester(...)
        self.tool_manager = ToolManager(...)
        self.prompt_builder = PromptBuilder(...)

        # 初始化工具注册表
        self.tool_registry = ToolRegistry(...)
        self.agent_registry = AgentRegistry(...)

    async def process_message(self, message: str, context: dict) -> str:
        """处理消息"""
        # 构建提示词
        prompt = self.prompt_builder.build(message, context)

        # 调用AI
        response = await self._requester.chat(prompt)

        # 处理工具调用
        if response.tool_calls:
            result = await self.tool_manager.execute_tools(
                response.tool_calls
            )
            # 可能需要再次调用AI
            response = await self._requester.chat(prompt + result)

        return response.text
```

### 4.3 PromptBuilder - 提示词构建器

提示词构建器负责组合各种信息:

```python
class PromptBuilder:
    """提示词构建器"""

    def build(self, message: str, context: dict) -> str:
        """构建完整提示词"""

        # 1. 系统提示词
        system_prompt = self._load_system_prompt()

        # 2. 历史消息
        history = self._get_history(context)

        # 3. 长期记忆
        memory = self._get_memory(context)

        # 4. 知识库
        knowledge = self._search_knowledge(message)

        # 5. 工具描述
        tools = self._get_tools_description()

        # 6. 组合所有内容
        full_prompt = f"""
{system_prompt}

# 相关知识
{knowledge}

# 历史对话
{history}

# 用户消息
{message}
"""

        return full_prompt

    def _load_system_prompt(self) -> str:
        """加载系统提示词"""
        return "你是一个智能QQ机器人助手..."

    def _get_history(self, context: dict) -> str:
        """获取历史消息"""
        history = context.get("history", [])
        return "\n".join([f"用户: {msg}" for msg in history])
```

### 4.4 ModelRequester - AI请求器

负责调用 AI API:

```python
class ModelRequester:
    """模型请求器"""

    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client

    async def chat(self, prompt: str) -> ChatResponse:
        """调用AI对话接口"""

        # 构造请求
        request = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "你是一个助手"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 8192,
            "temperature": 0.7
        }

        # 发送HTTP请求
        response = await self.http_client.post(
            "https://api.openai.com/v1/chat/completions",
            json=request,
            headers={
                "Authorization": f"Bearer sk-xxxxx",
                "Content-Type": "application/json"
            }
        )

        # 解析响应
        data = response.json()
        return ChatResponse(
            text=data["choices"][0]["message"]["content"],
            tool_calls=data.get("tool_calls", [])
        )
```

### 4.5 ToolManager - 工具管理器

管理工具的执行:

```python
class ToolManager:
    """工具管理器"""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        agent_registry: AgentRegistry
    ):
        self.tool_registry = tool_registry
        self.agent_registry = agent_registry

    async def execute_tools(self, tool_calls: list) -> dict:
        """执行工具调用"""

        results = {}

        for call in tool_calls:
            tool_name = call["name"]
            arguments = call["arguments"]

            # 获取工具
            tool = self.tool_registry.get_tool(tool_name)

            # 执行工具
            result = await tool.execute(**arguments)

            results[tool_name] = result

        return results
```

### 4.6 工具定义示例

如何定义一个工具:

```python
from Undefined.skills.tools import Tool

@tool
def get_current_time() -> str:
    """获取当前时间

    Returns:
        当前时间字符串
    """
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def calculate(expression: str) -> str:
    """计算数学表达式

    Args:
        expression: 数学表达式,如 "2+2*3"

    Returns:
        计算结果
    """
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"

@tool
def search_web(query: str) -> str:
    """搜索网络信息

    Args:
        query: 搜索关键词

    Returns:
        搜索结果摘要
    """
    # 实现搜索逻辑
    return f"搜索 {query} 的结果..."
```

### 4.7 AI 工具调用机制

**工具调用流程**:

```
1. AI 分析用户消息
    ↓
2. AI 决定需要使用工具
    ↓
3. AI 返回工具调用请求
    {
        "tool_calls": [
            {
                "name": "get_current_time",
                "arguments": {}
            }
        ]
    }
    ↓
4. ToolManager 执行工具
    ↓
5. 返回工具结果
    {
        "get_current_time": "2026-02-22 10:30:00"
    }
    ↓
6. 将结果发送回 AI
    ↓
7. AI 生成最终回复
```

---

## 第五章:消息处理机制

### 5.1 消息处理流程

```
接收QQ消息
    ↓
OneBotClient 接收事件
    ↓
MessageHandler.handle_message()
    ↓
判断消息类型
    ├─ 私聊消息 → handle_private()
    ├─ 群消息 → handle_group()
    └─ 拍一拍 → handle_poke()
    ↓
访问控制检查
    ├─ 白名单检查
    └─ 黑名单检查
    ↓
安全检查
    ├─ 注入检测
    └─ 敏感词过滤
    ↓
保存到历史
    ↓
判断处理类型
    ├─ 命令 → CommandDispatcher
    └─ 普通消息 → AICoordinator
    ↓
AICoordinator 协调处理
    ↓
发送回复
```

### 5.2 MessageHandler 详解

```python
class MessageHandler:
    """消息处理器"""

    def __init__(
        self,
        config: Config,
        onebot: OneBotClient,
        ai: AIClient,
        faq_storage: FAQStorage,
        task_storage: ScheduledTaskStorage,
    ):
        self.config = config
        self.onebot = onebot
        self.ai = ai

        # 初始化组件
        self.history_manager = MessageHistoryManager(...)
        self.sender = MessageSender(...)
        self.security = SecurityService(...)
        self.command_dispatcher = CommandDispatcher(...)
        self.ai_coordinator = AICoordinator(...)

    async def handle_message(self, event: dict) -> None:
        """处理消息事件"""

        post_type = event.get("post_type")

        # 1. 处理拍一拍
        if post_type == "notice" and event.get("notice_type") == "poke":
            await self._handle_poke(event)
            return

        # 2. 处理私聊消息
        if event.get("message_type") == "private":
            await self._handle_private_message(event)
            return

        # 3. 处理群消息
        if event.get("message_type") == "group":
            await self._handle_group_message(event)
            return

    async def _handle_private_message(self, event: dict) -> None:
        """处理私聊消息"""

        sender_id = get_message_sender_id(event)
        message = get_message_content(event)

        # 访问控制
        if not self.config.is_private_allowed(sender_id):
            return

        # 安全检查
        if await self.security.detect_injection(message):
            return

        # 保存历史
        await self.history_manager.add_private_message(...)

        # 发送给AI处理
        await self.ai_coordinator.handle_private_reply(...)

    async def _handle_group_message(self, event: dict) -> None:
        """处理群消息"""

        group_id = event.get("group_id")
        sender_id = get_message_sender_id(event)
        message = get_message_content(event)

        # 访问控制
        if not self.config.is_group_allowed(group_id):
            return

        # 保存历史
        await self.history_manager.add_group_message(...)

        # 检查是否是命令
        if is_command(message):
            await self.command_dispatcher.dispatch(...)
            return

        # AI处理
        await self.ai_coordinator.handle_auto_reply(...)
```

### 5.3 OneBotClient - QQ协议连接

```python
class OneBotClient:
    """OneBot WebSocket 客户端"""

    def __init__(self, ws_url: str, token: str = ""):
        self.ws_url = ws_url
        self.token = token
        self.ws = None
        self._message_handler = None

    async def connect(self) -> None:
        """连接到OneBot WebSocket"""
        self.ws = await websockets.connect(self.ws_url)
        print("连接成功!")

    async def disconnect(self) -> None:
        """断开连接"""
        if self.ws:
            await self.ws.close()

    async def send_private_message(self, user_id: int, message: str) -> None:
        """发送私聊消息"""
        await self._call_api("send_private_msg", {
            "user_id": user_id,
            "message": message
        })

    async def send_group_message(self, group_id: int, message: str) -> None:
        """发送群消息"""
        await self._call_api("send_group_msg", {
            "group_id": group_id,
            "message": message
        })

    async def _call_api(self, action: str, params: dict) -> dict:
        """调用OneBot API"""
        request = {
            "action": action,
            "params": params
        }
        await self.ws.send(json.dumps(request))
        response = await self.ws.recv()
        return json.loads(response)
```

### 5.4 WebSocket 协议

**什么是 WebSocket?**
- WebSocket 是一种全双工通信协议
- 支持服务器主动推送消息
- 适合实时通信场景

**项目中的使用**:

```python
import websockets

async def connect_websocket():
    # 连接WebSocket
    async with websockets.connect("ws://127.0.0.1:3001") as ws:
        # 发送消息
        await ws.send(json.dumps({"action": "get_status"}))

        # 接收消息
        response = await ws.recv()
        print(response)

        # 持续接收
        async for message in ws:
            data = json.loads(message)
            # 处理消息
            handle_message(data)
```

---

## 第六章:技能系统

### 6.1 技能系统概述

技能系统是 Undefined 的核心特性,允许轻松扩展功能:

```
技能系统
├── Tools (工具)
│   └── 单一功能,如获取时间、计算
├── Toolsets (工具集)
│   └── 相关工具的集合
├── Agents (智能体)
│   └── 具有特定能力的AI助手
└── Anthropic Skills
    └── 领域知识注入
```

### 6.2 目录结构

```
skills/
├── tools/                 # 基础工具
│   ├── get_current_time/
│   │   └── tool.py
│   ├── python_interpreter/
│   │   └── tool.py
│   └── ...
├── toolsets/              # 工具集
│   ├── messages/
│   │   └── toolset.py
│   ├── memory/
│   │   └── toolset.py
│   └── ...
├── agents/                # 智能体
│   ├── search_agent/
│   │   ├── agent.py
│   │   └── callable.json
│   ├── code_agent/
│   │   ├── agent.py
│   │   └── callable.json
│   └── ...
└── anthropic_skills/      # Anthropic Skills
    └── ...
```

### 6.3 创建工具

**步骤1**: 创建工具目录

```bash
mkdir -p skills/tools/my_tool
```

**步骤2**: 创建 `tool.py`

```python
from Undefined.skills.tools import Tool

@tool
def my_tool(param1: str, param2: int = 10) -> str:
    """我的工具

    Args:
        param1: 第一个参数
        param2: 第二个参数(可选)

    Returns:
        处理结果
    """
    result = f"处理结果: {param1}, {param2}"
    return result
```

**装饰器 `@tool` 的作用**:
- 自动注册工具到注册表
- 提取工具文档
- 生成工具描述供AI使用

### 6.4 工具集

工具集是相关工具的集合:

```python
from Undefined.skills.toolsets import Toolset, tool

class MyToolset(Toolset):
    """我的工具集"""

    @tool
    def function1(self, param: str) -> str:
        """功能1"""
        return f"结果1: {param}"

    @tool
    def function2(self, a: int, b: int) -> int:
        """功能2"""
        return a + b
```

### 6.5 Agent 智能体

Agent 是具有特定能力的AI助手:

**创建 Agent**:

```python
from Undefined.skills.agents import Agent

@agent(
    name="my_agent",
    description="我的智能体",
    tools=["tool1", "tool2"],
    max_turns=5
)
class MyAgent:
    """Agent类定义"""

    def __init__(self):
        self.conversation_history = []
```

**Agent 配置文件 `callable.json`**:

```json
{
  "enabled": true,
  "description": "我的智能体,专门处理特定任务",
  "tools": ["tool1", "tool2"],
  "can_be_called_by": ["*"],
  "max_consecutive_auto_reply": 5
}
```

### 6.6 工具注册机制

```python
class ToolRegistry:
    """工具注册表"""

    def __init__(self, base_dir: Path):
        self.tools: dict[str, Tool] = {}
        self.base_dir = base_dir

    def discover_tools(self):
        """自动发现工具"""
        # 扫描工具目录
        for tool_dir in self.base_dir.iterdir():
            if tool_dir.is_dir():
                tool_path = tool_dir / "tool.py"
                if tool_path.exists():
                    self._load_tool(tool_path)

    def get_tool(self, name: str) -> Tool:
        """获取工具"""
        return self.tools.get(name)

    def list_tools(self) -> list[str]:
        """列出所有工具"""
        return list(self.tools.keys())
```

---

## 第七章:存储系统

### 7.1 存储系统概述

```
存储系统
├── MessageHistory - 消息历史
├── MemoryStorage - 长期记忆
├── FAQStorage - 常见问题
├── TokenUsageStorage - Token统计
├── ScheduledTaskStorage - 定时任务
└── KnowledgeBase - 知识库
```

### 7.2 消息历史

```python
class MessageHistoryManager:
    """消息历史管理器"""

    def __init__(self, max_records: int = 10000):
        self.max_records = max_records

    async def add_group_message(
        self,
        group_id: int,
        sender_id: int,
        text_content: str,
        ...
    ):
        """添加群消息"""
        history_file = f"data/history/group_{group_id}.json"

        # 读取现有历史
        history = await self._load_history(history_file)

        # 添加新消息
        history.append({
            "sender_id": sender_id,
            "content": text_content,
            "timestamp": datetime.now().isoformat()
        })

        # 限制历史长度
        if len(history) > self.max_records:
            history = history[-self.max_records:]

        # 保存
        await self._save_history(history_file, history)

    async def get_recent_messages(
        self,
        group_id: int,
        limit: int = 20
    ) -> list[dict]:
        """获取最近消息"""
        history_file = f"data/history/group_{group_id}.json"
        history = await self._load_history(history_file)
        return history[-limit:]
```

### 7.3 长期记忆

```python
class MemoryStorage:
    """长期记忆存储"""

    def __init__(self, max_memories: int = 500):
        self.max_memories = max_memories
        self.file_path = "data/memory.json"

    async def add(self, content: str) -> str:
        """添加记忆"""
        memories = await self._load()

        # 生成ID
        memory_id = str(uuid.uuid4())

        # 添加记忆
        memories.append({
            "id": memory_id,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

        # 去重和限制数量
        memories = self._deduplicate(memories)
        memories = memories[-self.max_memories:]

        await self._save(memories)
        return memory_id

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        """搜索记忆"""
        memories = await self._load()

        # 简单的文本匹配
        results = []
        for mem in memories:
            if query.lower() in mem["content"].lower():
                results.append(mem)

        return results[:top_k]
```

### 7.4 Token统计

```python
class TokenUsageStorage:
    """Token使用统计"""

    def __init__(self):
        self.file_path = "data/token_usage.jsonl"

    async def record(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ):
        """记录Token使用"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        }

        # 追加到文件
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    async def get_stats(self, days: int = 7) -> dict:
        """获取统计数据"""
        # 读取最近N天的记录
        # 统计总数、平均值等
        pass
```

---

## 第八章:工具和辅助模块

### 8.1 工具函数库

```python
# utils/common.py - 通用工具函数

def extract_text(message_content: list) -> str:
    """从消息内容中提取纯文本"""
    text_parts = []
    for segment in message_content:
        if segment.get("type") == "text":
            text_parts.append(segment.get("data", {}).get("text", ""))
    return "".join(text_parts)

def redact_string(s: str) -> str:
    """脱敏字符串(隐藏敏感信息)"""
    # 隐藏API密钥等
    import re
    pattern = r"sk-[a-zA-Z0-9]{20,}"
    return re.sub(pattern, "sk-***", s)
```

### 8.2 文件IO工具

```python
# utils/io.py - 异步文件操作

import aiofiles

async def read_json(file_path: str) -> dict:
    """读取JSON文件"""
    async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content)

async def write_json(file_path: str, data: dict):
    """写入JSON文件"""
    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))

async def append_line(file_path: str, line: str):
    """追加一行文本"""
    async with aiofiles.open(file_path, "a", encoding="utf-8") as f:
        await f.write(line + "\n")
```

### 8.3 日志工具

```python
# utils/logging.py - 日志工具

from rich.logging import RichHandler
from rich.console import Console

def setup_logger(name: str, level: str = "INFO"):
    """设置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))

    # Rich控制台处理器
    console = Console()
    handler = RichHandler(
        console=console,
        show_time=True,
        show_path=True,
        rich_tracebacks=True
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    return logger
```

---

## 第九章:Python核心知识点总结

### 9.1 基础语法

#### 变量和数据类型

```python
# 基本类型
name = "小明"        # 字符串
age = 18            # 整数
height = 1.75       # 浮点数
is_student = True   # 布尔值

# 集合类型
fruits = ["苹果", "香蕉", "橙子"]  # 列表
person = {"name": "小明", "age": 18}  # 字典
numbers = {1, 2, 3, 4, 5}         # 集合
```

#### 条件语句

```python
# if-elif-else
if age >= 18:
    print("成年人")
elif age >= 13:
    print("青少年")
else:
    print("儿童")

# 三元运算符
status = "成年" if age >= 18 else "未成年"
```

#### 循环

```python
# for循环
for fruit in fruits:
    print(fruit)

# while循环
count = 0
while count < 10:
    print(count)
    count += 1

# 列表推导式
squares = [x**2 for x in range(10)]
```

### 9.2 函数

```python
# 定义函数
def greet(name: str, greeting: str = "你好") -> str:
    """打招呼函数

    Args:
        name: 名字
        greeting: 问候语

    Returns:
        打招呼的句子
    """
    return f"{greeting}, {name}!"

# 调用函数
result = greet("小明")
print(result)  # 你好, 小明!

result = greet("小明", "Hello")
print(result)  # Hello, 小明!

# 可变参数
def sum_all(*numbers: int) -> int:
    """求和"""
    return sum(numbers)

total = sum_all(1, 2, 3, 4, 5)
print(total)  # 15

# 关键字参数
def create_person(name: str, **kwargs) -> dict:
    """创建人物"""
    person = {"name": name}
    person.update(kwargs)
    return person

person = create_person("小明", age=18, city="北京")
print(person)  # {'name': '小明', 'age': 18, 'city': '北京'}
```

### 9.3 类和对象

```python
# 定义类
class Person:
    """人物类"""

    def __init__(self, name: str, age: int):
        """构造函数"""
        self.name = name  # 实例变量
        self.age = age

    def say_hello(self) -> str:
        """打招呼方法"""
        return f"你好,我是{self.name},今年{self.age}岁"

    def birthday(self):
        """过生日"""
        self.age += 1

# 创建对象
person = Person("小明", 18)
print(person.say_hello())  # 你好,我是小明,今年18岁

# 调用方法
person.birthday()
print(person.age)  # 19
```

### 9.4 异步编程

```python
import asyncio

# 定义异步函数
async def task1():
    print("任务1开始")
    await asyncio.sleep(2)  # 等待2秒
    print("任务1完成")

async def task2():
    print("任务2开始")
    await asyncio.sleep(1)
    print("任务2完成")

async def task3():
    print("任务3开始")
    await asyncio.sleep(3)
    print("任务3完成")

# 串行执行
async def main_serial():
    await task1()
    await task2()
    await task3()

asyncio.run(main_serial())
# 耗时: 2+1+3 = 6秒

# 并发执行
async def main_parallel():
    await asyncio.gather(task1(), task2(), task3())

asyncio.run(main_parallel())
# 耗时: max(2,1,3) = 3秒
```

### 9.5 错误处理

```python
# try-except-else-finally
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"除零错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")
else:
    print("没有错误")
finally:
    print("无论如何都会执行")

# 自定义异常
class MyError(Exception):
    """自定义异常"""
    pass

def check_age(age: int):
    if age < 0:
        raise MyError("年龄不能为负数")

try:
    check_age(-5)
except MyError as e:
    print(f"捕获到异常: {e}")
```

### 9.6 装饰器

```python
# 简单装饰器
def log_decorator(func):
    """日志装饰器"""
    def wrapper(*args, **kwargs):
        print(f"调用函数: {func.__name__}")
        result = func(*args, **kwargs)
        print(f"函数返回: {result}")
        return result
    return wrapper

@log_decorator
def add(a: int, b: int) -> int:
    return a + b

result = add(1, 2)
# 输出:
# 调用函数: add
# 函数返回: 3

# 带参数的装饰器
def repeat(times: int):
    def decorator(func):
        def wrapper(*args, **kwargs):
            results = []
            for _ in range(times):
                result = func(*args, **kwargs)
                results.append(result)
            return results
        return wrapper
    return decorator

@repeat(times=3)
def greet(name: str) -> str:
    return f"你好, {name}!"

results = greet("小明")
print(results)  # ['你好, 小明!', '你好, 小明!', '你好, 小明!']
```

### 9.7 上下文管理器

```python
# 使用with语句
with open("file.txt", "r") as f:
    content = f.read()
# 文件自动关闭

# 自定义上下文管理器
class Timer:
    """计时器上下文管理器"""
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start
        print(f"耗时: {elapsed:.2f}秒")

# 使用
with Timer():
    # 执行一些操作
    sum(range(1000000))
# 输出: 耗时: 0.03秒
```

---

## 第十章:实战练习

### 练习1: 创建简单的QQ机器人

```python
import asyncio
import websockets
import json

class SimpleQQBot:
    """简单的QQ机器人"""

    def __init__(self, ws_url: str):
        self.ws_url = ws_url

    async def connect(self):
        """连接到OneBot"""
        async with websockets.connect(self.ws_url) as ws:
            print("已连接到OneBot")

            # 监听消息
            async for message in ws:
                event = json.loads(message)
                await self.handle_message(event, ws)

    async def handle_message(self, event: dict, ws):
        """处理消息"""
        if event.get("post_type") == "message":
            user_id = event.get("user_id")
            message = event.get("raw_message")

            print(f"收到消息: {message}")

            # 简单回复
            if "你好" in message:
                await self.send_reply(ws, user_id, "你好呀!")

    async def send_reply(self, ws, user_id: int, text: str):
        """发送回复"""
        response = {
            "action": "send_private_msg",
            "params": {
                "user_id": user_id,
                "message": text
            }
        }
        await ws.send(json.dumps(response))

# 运行
async def main():
    bot = SimpleQQBot("ws://127.0.0.1:3001")
    await bot.connect()

asyncio.run(main())
```

### 练习2: 实现配置系统

```python
import toml
from dataclasses import dataclass
from pathlib import Path

@dataclass
class BotConfig:
    """机器人配置"""
    bot_qq: int
    admin_qq: int
    ws_url: str

class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str = "config.toml"):
        self.config_path = Path(config_path)
        self.config = None

    def load(self) -> BotConfig:
        """加载配置"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        # 读取TOML
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = toml.load(f)

        # 转换为数据类
        self.config = BotConfig(
            bot_qq=data["core"]["bot_qq"],
            admin_qq=data["core"]["admin_qq"],
            ws_url=data["onebot"]["ws_url"]
        )

        return self.config

    def save(self):
        """保存配置"""
        data = {
            "core": {
                "bot_qq": self.config.bot_qq,
                "admin_qq": self.config.admin_qq
            },
            "onebot": {
                "ws_url": self.config.ws_url
            }
        }

        with open(self.config_path, "w", encoding="utf-8") as f:
            toml.dump(data, f)

# 使用
manager = ConfigManager()
config = manager.load()
print(f"机器人QQ: {config.bot_qq}")
```

### 练习3: 实现工具系统

```python
from typing import Callable, Any
import inspect

class Tool:
    """工具基类"""

    def __init__(self, func: Callable):
        self.func = func
        self.name = func.__name__
        self.description = func.__doc__ or ""
        self.parameters = self._extract_parameters()

    def _extract_parameters(self) -> dict:
        """提取参数信息"""
        sig = inspect.signature(self.func)
        params = {}
        for name, param in sig.parameters.items():
            params[name] = {
                "type": str(param.annotation),
                "default": param.default if param.default != param.empty else None
            }
        return params

    async def execute(self, **kwargs) -> Any:
        """执行工具"""
        return await self.func(**kwargs)

def tool(func: Callable) -> Tool:
    """工具装饰器"""
    return Tool(func)

# 使用工具装饰器
@tool
def get_current_time() -> str:
    """获取当前时间"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def add_numbers(a: int, b: int) -> int:
    """两个数字相加"""
    return a + b

# 工具注册表
class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self.tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool:
        """获取工具"""
        return self.tools.get(name)

    def list_tools(self) -> list[str]:
        """列出所有工具"""
        return list(self.tools.keys())

# 使用
registry = ToolRegistry()
registry.register(get_current_time)
registry.register(add_numbers)

# 获取工具
time_tool = registry.get_tool("get_current_time")
result = time_tool.execute()
print(result)  # 2026-02-22 10:30:00

# 列出工具
print(registry.list_tools())  # ['get_current_time', 'add_numbers']
```

### 练习4: 实现简单的AI客户端

```python
import httpx
import json
from typing import Optional

class SimpleAIClient:
    """简单的AI客户端"""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def chat(
        self,
        messages: list[dict],
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 1000
    ) -> str:
        """发送聊天请求"""
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens
        }

        response = await self.client.post(url, json=data, headers=headers)
        result = response.json()

        return result["choices"][0]["message"]["content"]

    async def simple_chat(self, user_message: str, system_prompt: str = "") -> str:
        """简单聊天"""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": user_message})

        return await self.chat(messages)

# 使用
async def main():
    client = SimpleAIClient(api_key="sk-xxxxx")

    # 简单对话
    response = await client.simple_chat(
        "你好!",
        system_prompt="你是一个友好的助手"
    )
    print(f"AI回复: {response}")

asyncio.run(main())
```

---

## 🎓 学习总结

通过这个项目,你学到了:

### Python知识
✅ 基础语法(变量、函数、类)
✅ 异步编程(async/await)
✅ 面向对象编程
✅ 类型提示
✅ 装饰器
✅ 上下文管理器
✅ 错误处理

### 实践技能
✅ 配置管理
✅ 网络编程(HTTP/WebSocket)
✅ 文件IO
✅ 日志记录
✅ AI API调用
✅ 工具系统设计

### 项目经验
✅ 模块化设计
✅ 异步架构
✅ 错误处理
✅ 代码组织

---

## 🚀 下一步建议

1. **深入学习Python**
   - 阅读《流畅的Python》
   - 研究Python标准库

2. **实践项目**
   - 修改现有功能
   - 添加新工具
   - 创建新Agent

3. **学习AI**
   - 了解OpenAI API
   - 学习Prompt Engineering
   - 研究Agent开发

4. **参与社区**
   - GitHub贡献代码
   - 报告问题
   - 分享经验

---

**祝你学习愉快,成为Python高手!** 🎉

记住:编程最重要的是实践,多写代码,多思考,多总结!

有任何问题,随时查阅文档和源码,加油! 💪
