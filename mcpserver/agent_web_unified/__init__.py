"""
统一网页服务

整合了以下三个服务的功能：
- agent_online_search (searxng搜索)
- agent_crawl4ai (网页解析)
- agent_playwright_master (浏览器自动化)

提供统一的网页处理接口

作者: NagaAgent Team
版本: 1.0.0
创建日期: 2026-01-28
"""

from .web_unified_agent import WebUnifiedAgent, get_tools

__all__ = ['WebUnifiedAgent', 'get_tools']
