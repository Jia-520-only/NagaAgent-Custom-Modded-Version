"""公共模块 - 整合 Undefined_new 的优秀特性

此目录包含从 Undefined_new 迁移的核心模块：
- io: 异步安全 IO 操作
- context: 请求上下文管理
- skills: Skills 插件系统
- services: 核心服务（队列、安全等）
"""

from . import io
from . import context
from .skills import registry

# 添加 time_stamp 工具函数 (用于 jmcomic)
import time as _time
def time_stamp():
    return int(_time.time() * 1000)

def format_ts():
    import datetime
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def current_thread():
    import threading
    return threading.current_thread()

def str_to_list(s):
    if isinstance(s, (list, tuple)):
        return list(s)
    elif isinstance(s, str):
        return [s]
    return []

# 添加 field_cache 和 ProxyBuilder 占位符
class ProxyBuilder:
    pass

field_cache = {}

__all__ = ['io', 'context', 'registry', 'time_stamp', 'format_ts', 'current_thread',
           'str_to_list', 'field_cache', 'ProxyBuilder']
