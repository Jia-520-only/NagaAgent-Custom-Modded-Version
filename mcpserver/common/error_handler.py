"""
错误处理

提供统一的异常类和错误处理机制

作者: NagaAgent Team
版本: 1.0.0
"""

import logging
from typing import Optional, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)


# ==================== 自定义异常类 ====================

class MCPError(Exception):
    """MCP基础异常"""

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ServiceNotFoundError(MCPError):
    """服务未找到错误"""
    def __init__(self, service_name: str):
        super().__init__(
            message=f"服务未找到: {service_name}",
            code="SERVICE_NOT_FOUND",
            details={'service_name': service_name}
        )


class ToolNotFoundError(MCPError):
    """工具未找到错误"""
    def __init__(self, tool_name: str):
        super().__init__(
            message=f"工具未找到: {tool_name}",
            code="TOOL_NOT_FOUND",
            details={'tool_name': tool_name}
        )


class ToolExecutionError(MCPError):
    """工具执行错误"""
    def __init__(self, tool_name: str, error: str):
        super().__init__(
            message=f"工具执行失败: {tool_name} - {error}",
            code="TOOL_EXECUTION_ERROR",
            details={'tool_name': tool_name, 'error': error}
        )


class ValidationError(MCPError):
    """参数验证错误"""
    def __init__(self, param_name: str, reason: str):
        super().__init__(
            message=f"参数验证失败: {param_name} - {reason}",
            code="VALIDATION_ERROR",
            details={'param_name': param_name, 'reason': reason}
        )


class ExternalServiceError(MCPError):
    """外部服务错误"""
    def __init__(self, service_name: str, error: str):
        super().__init__(
            message=f"外部服务错误: {service_name} - {error}",
            code="EXTERNAL_SERVICE_ERROR",
            details={'service_name': service_name, 'error': error}
        )


class ConfigurationError(MCPError):
    """配置错误"""
    def __init__(self, config_key: str, reason: str):
        super().__init__(
            message=f"配置错误: {config_key} - {reason}",
            code="CONFIGURATION_ERROR",
            details={'config_key': config_key, 'reason': reason}
        )


# ==================== 错误处理装饰器 ====================

def handle_errors(
    default_return: Any = None,
    log_error: bool = True,
    raise_exception: bool = False
):
    """错误处理装饰器

    Args:
        default_return: 发生错误时的默认返回值
        log_error: 是否记录错误日志
        raise_exception: 是否抛出异常
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except MCPError as e:
                if log_error:
                    logger.error(f"[{func.__name__}] MCP错误: {e.message} (code: {e.code})")
                if raise_exception:
                    raise
                return default_return
            except Exception as e:
                if log_error:
                    logger.error(f"[{func.__name__}] 未知错误: {e}")
                if raise_exception:
                    raise MCPError(
                        message=str(e),
                        code="INTERNAL_ERROR"
                    )
                return default_return

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except MCPError as e:
                if log_error:
                    logger.error(f"[{func.__name__}] MCP错误: {e.message} (code: {e.code})")
                if raise_exception:
                    raise
                return default_return
            except Exception as e:
                if log_error:
                    logger.error(f"[{func.__name__}] 未知错误: {e}")
                if raise_exception:
                    raise MCPError(
                        message=str(e),
                        code="INTERNAL_ERROR"
                    )
                return default_return

        # 根据函数类型选择包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def retry_on_error(
    max_retries: int = 3,
    exceptions: tuple = (Exception,),
    backoff_factor: float = 1.0
):
    """重试装饰器

    Args:
        max_retries: 最大重试次数
        exceptions: 需要重试的异常类型
        backoff_factor: 退避因子（秒）
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            import asyncio

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        logger.error(f"[{func.__name__}] 重试 {max_retries} 次后仍失败: {e}")
                        raise

                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"[{func.__name__}] 失败，{wait_time}秒后重试 (尝试 {attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(wait_time)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        logger.error(f"[{func.__name__}] 重试 {max_retries} 次后仍失败: {e}")
                        raise

                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"[{func.__name__}] 失败，{wait_time}秒后重试 (尝试 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(wait_time)

        # 根据函数类型选择包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ==================== 错误信息格式化 ====================

def format_error_response(
    error: Exception,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """格式化错误响应

    Args:
        error: 异常对象
        request_id: 请求ID

    Returns:
        格式化的错误响应
    """
    if isinstance(error, MCPError):
        return {
            'success': False,
            'error': {
                'code': error.code,
                'message': error.message,
                'details': error.details
            },
            'request_id': request_id
        }
    else:
        return {
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': str(error),
                'details': {}
            },
            'request_id': request_id
        }
