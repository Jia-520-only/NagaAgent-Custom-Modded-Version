"""
统一日志模块

提供结构化日志输出

作者: NagaAgent Team
版本: 1.0.0
"""

import logging
import sys
from typing import Optional
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }

    def format(self, record):
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        return super().format(record)


def get_logger(
    name: Optional[str] = None,
    level: int = logging.INFO,
    use_color: bool = True
) -> logging.Logger:
    """获取日志记录器

    Args:
        name: 日志记录器名称，默认使用调用模块名
        level: 日志级别
        use_color: 是否使用彩色输出

    Returns:
        日志记录器
    """
    if name is None:
        import inspect
        name = inspect.currentframe().f_back.f_globals.get('__name__', 'root')

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加处理器
    if not logger.handlers:
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # 格式化器
        log_format = (
            '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
        )
        date_format = '%Y-%m-%d %H:%M:%S'

        if use_color and sys.stdout.isatty():
            formatter = ColoredFormatter(log_format, date_format)
        else:
            formatter = logging.Formatter(log_format, date_format)

        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def setup_file_logger(
    name: str,
    log_file: str,
    level: int = logging.INFO,
    rotation: Optional[int] = None
) -> logging.Logger:
    """设置文件日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        level: 日志级别
        rotation: 日志轮转大小（字节）

    Returns:
        日志记录器
    """
    logger = get_logger(name, level, use_color=False)

    # 文件处理器
    if rotation:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=rotation,
            backupCount=5,
            encoding='utf-8'
        )
    else:
        file_handler = logging.FileHandler(
            log_file,
            encoding='utf-8'
        )

    file_handler.setLevel(level)

    # 格式化器
    log_format = (
        '%(asctime)s - %(name)s - [%(levelname)s] - %(funcName)s:%(lineno)d - %(message)s'
    )
    date_format = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(log_format, date_format)

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# 便捷函数
def debug(message: str, name: Optional[str] = None):
    """记录DEBUG日志"""
    get_logger(name).debug(message)


def info(message: str, name: Optional[str] = None):
    """记录INFO日志"""
    get_logger(name).info(message)


def warning(message: str, name: Optional[str] = None):
    """记录WARNING日志"""
    get_logger(name).warning(message)


def error(message: str, name: Optional[str] = None):
    """记录ERROR日志"""
    get_logger(name).error(message)


def critical(message: str, name: Optional[str] = None):
    """记录CRITICAL日志"""
    get_logger(name).critical(message)


# 装饰器：记录函数调用
def log_call(logger: Optional[logging.Logger] = None):
    """记录函数调用的装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            _logger = logger or get_logger(func.__module__)

            _logger.debug(f"[{func.__name__}] 调用开始: args={args}, kwargs={kwargs}")

            try:
                result = func(*args, **kwargs)
                _logger.debug(f"[{func.__name__}] 调用成功")
                return result
            except Exception as e:
                _logger.error(f"[{func.__name__}] 调用失败: {e}")
                raise

        return wrapper
    return decorator
