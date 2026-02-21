"""
统一HTTP客户端

提供连接池、重试、超时、代理等功能

作者: NagaAgent Team
版本: 1.0.0
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class HttpClient:
    """统一HTTP客户端"""

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        pool_connections: int = 100,
        enable_proxy: bool = False,
        proxy_url: Optional[str] = None
    ):
        """初始化

        Args:
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            pool_connections: 连接池大小
            enable_proxy: 是否启用代理
            proxy_url: 代理URL
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_proxy = enable_proxy
        self.proxy_url = proxy_url

        # 配置客户端
        limits = httpx.Limits(
            max_keepalive_connections=pool_connections,
            max_connections=pool_connections,
            keepalive_expiry=300.0
        )

        proxy = proxy_url if enable_proxy else None

        self.async_client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            proxy=proxy,
            follow_redirects=True
        )

        logger.info("[HttpClient] 初始化完成")

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry: bool = True
    ) -> httpx.Response:
        """发送GET请求

        Args:
            url: 请求URL
            params: 查询参数
            headers: 请求头
            retry: 是否重试

        Returns:
            响应对象
        """
        for attempt in range(self.max_retries if retry else 1):
            try:
                response = await self.async_client.get(
                    url,
                    params=params,
                    headers=headers
                )
                return response
            except httpx.RequestError as e:
                logger.warning(f"[HttpClient] GET请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise

        raise httpx.RequestError(f"GET请求失败: {url}")

    async def post(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry: bool = True
    ) -> httpx.Response:
        """发送POST请求

        Args:
            url: 请求URL
            json: JSON数据
            data: 表单数据
            headers: 请求头
            retry: 是否重试

        Returns:
            响应对象
        """
        for attempt in range(self.max_retries if retry else 1):
            try:
                response = await self.async_client.post(
                    url,
                    json=json,
                    data=data,
                    headers=headers
                )
                return response
            except httpx.RequestError as e:
                logger.warning(f"[HttpClient] POST请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise

        raise httpx.RequestError(f"POST请求失败: {url}")

    async def close(self):
        """关闭客户端"""
        await self.async_client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# 全局客户端实例
_global_client: Optional[HttpClient] = None


def get_global_client() -> HttpClient:
    """获取全局HTTP客户端"""
    global _global_client
    if _global_client is None:
        _global_client = HttpClient()
    return _global_client


async def close_global_client():
    """关闭全局HTTP客户端"""
    global _global_client
    if _global_client is not None:
        await _global_client.close()
        _global_client = None
