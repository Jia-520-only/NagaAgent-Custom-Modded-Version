"""获取当前时间工具"""

from datetime import datetime


async def execute(args: dict, context: dict) -> str:
    """获取当前系统时间

    Args:
        args: 参数字典（此工具不需要参数）
        context: 请求上下文

    Returns:
        格式化的当前时间字符串
    """
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")
