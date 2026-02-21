"""配置模型定义"""

from dataclasses import dataclass


@dataclass
class ChatModelConfig:
    """对话模型配置"""

    api_url: str
    api_key: str
    model_name: str
    max_tokens: int
    queue_interval_seconds: float = 1.0
    thinking_enabled: bool = False  # 是否启用 thinking
    thinking_budget_tokens: int = 20000  # 思维预算 token 数量
    thinking_include_budget: bool = True  # 是否在请求中发送 budget_tokens
    thinking_tool_call_compat: bool = (
        False  # 思维链 + 工具调用兼容（回传 reasoning_content）
    )


@dataclass
class VisionModelConfig:
    """视觉模型配置"""

    api_url: str
    api_key: str
    model_name: str
    queue_interval_seconds: float = 1.0
    thinking_enabled: bool = False  # 是否启用 thinking
    thinking_budget_tokens: int = 20000  # 思维预算 token 数量
    thinking_include_budget: bool = True  # 是否在请求中发送 budget_tokens
    thinking_tool_call_compat: bool = (
        False  # 思维链 + 工具调用兼容（回传 reasoning_content）
    )


@dataclass
class SecurityModelConfig:
    """安全模型配置（用于防注入检测和注入后的回复生成）"""

    api_url: str
    api_key: str
    model_name: str
    max_tokens: int
    queue_interval_seconds: float = 1.0
    thinking_enabled: bool = False  # 是否启用 thinking
    thinking_budget_tokens: int = 0  # 思维预算 token 数量
    thinking_include_budget: bool = True  # 是否在请求中发送 budget_tokens
    thinking_tool_call_compat: bool = (
        False  # 思维链 + 工具调用兼容（回传 reasoning_content）
    )


@dataclass
class AgentModelConfig:
    """Agent 模型配置（用于执行 agents）"""

    api_url: str
    api_key: str
    model_name: str
    max_tokens: int = 4096
    queue_interval_seconds: float = 1.0
    thinking_enabled: bool = False  # 是否启用 thinking
    thinking_budget_tokens: int = 0  # 思维预算 token 数量
    thinking_include_budget: bool = True  # 是否在请求中发送 budget_tokens
    thinking_tool_call_compat: bool = (
        False  # 思维链 + 工具调用兼容（回传 reasoning_content）
    )


@dataclass
class InflightSummaryModelConfig:
    """进行中任务摘要模型配置。"""

    api_url: str
    api_key: str
    model_name: str
    max_tokens: int = 128
    queue_interval_seconds: float = 1.5
    thinking_enabled: bool = False
    thinking_budget_tokens: int = 0
    thinking_include_budget: bool = False
    thinking_tool_call_compat: bool = False


@dataclass
class OnlineAIDrawConfig:
    """在线AI绘图配置"""

    api_url: str = "https://open.bigmodel.cn/api/paas/v4"
    api_key: str = ""
    default_model: str = "cogview-3"
    default_size: str = "1:1"
    provider: str = "zhipu"
    timeout: int = 120


@dataclass
class LocalAIDrawConfig:
    """本地AI绘图配置（Stable Diffusion）"""

    service_url: str = "http://127.0.0.1:7860"
    service_type: str = "sd_webui"
    model: str = ""
    width: int = 512
    height: int = 512
    steps: int = 20
    cfg_scale: float = 7.0
    sampler: str = "DPM++ 2M Karras"
    timeout: int = 300
