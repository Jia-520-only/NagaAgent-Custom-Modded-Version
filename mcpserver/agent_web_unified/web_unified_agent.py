"""
统一网页服务

整合了以下三个服务的功能：
- agent_online_search (searxng搜索)
- agent_crawl4ai (网页解析)
- agent_playwright_master (浏览器自动化)

提供统一的网页处理接口，支持：
1. 网页搜索（多引擎）
2. 网页抓取（静态/动态）
3. 浏览器自动化
4. 智能内容解析

作者: NagaAgent Team
版本: 1.0.0
创建日期: 2026-01-28
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

# 配置日志
logger = logging.getLogger(__name__)


class SearchEngine(Enum):
    """搜索引擎类型"""
    SEARXNG = "searxng"
    GOOGLE = "google"
    BING = "bing"
    BAIDU = "baidu"
    DUCKDUCKGO = "duckduckgo"


class CrawlMode(Enum):
    """抓取模式"""
    STATIC = "static"      # 静态页面（使用requests）
    DYNAMIC = "dynamic"    # 动态页面（使用Playwright）
    AUTO = "auto"          # 自动选择


class ContentFormat(Enum):
    """内容格式"""
    MARKDOWN = "markdown"
    HTML = "html"
    TEXT = "text"
    JSON = "json"


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    url: str
    snippet: str
    engine: str
    rank: int


@dataclass
class CrawlResult:
    """抓取结果"""
    url: str
    content: str
    format: str
    mode: str
    status_code: int
    error: Optional[str] = None


class WebUnifiedAgent:
    """统一网页服务Agent"""

    def __init__(self, config: Dict[str, Any]):
        """初始化

        Args:
            config: 配置字典
        """
        self.config = config
        self.search_config = config.get('online_search', {})
        self.browser_config = config.get('browser', {})
        self.crawl_config = config.get('crawl4ai', {})

        # 初始化搜索引擎
        self.searxng_url = self.search_config.get('searxng_url')
        self.default_engine = self.search_config.get('default_engine', 'searxng')
        self.result_count = self.search_config.get('result_count', 5)
        self.engines = self.search_config.get('engines', ['google'])

        # 初始化浏览器
        self.headless = self.browser_config.get('headless', True)
        self.timeout = self.crawl_config.get('timeout', 30000)

        # 延迟加载组件（按需）
        self._playwright_browser = None
        self._searxng_client = None

        logger.info("[统一网页] 初始化完成")

    # ==================== 搜索功能 ====================

    async def web_search(
        self,
        query: str,
        engine: str = None,
        count: int = None,
        language: str = "zh-CN"
    ) -> List[SearchResult]:
        """统一网页搜索

        Args:
            query: 搜索关键词
            engine: 搜索引擎 (默认: 配置中的default_engine)
            count: 结果数量 (默认: 配置中的result_count)
            language: 语言设置

        Returns:
            搜索结果列表
        """
        engine = engine or self.default_engine
        count = count or self.result_count

        logger.info(f"[统一网页] 执行搜索: query={query}, engine={engine}, count={count}")

        try:
            if engine == SearchEngine.SEARXNG.value:
                return await self._search_searxng(query, count, language)
            elif engine == SearchEngine.GOOGLE.value:
                return await self._search_google(query, count, language)
            else:
                return await self._search_generic(query, engine, count, language)
        except Exception as e:
            logger.error(f"[统一网页] 搜索失败: {e}")
            raise

    async def _search_searxng(
        self,
        query: str,
        count: int,
        language: str
    ) -> List[SearchResult]:
        """使用SearXNG搜索"""
        try:
            import httpx

            if not self.searxng_url:
                raise ValueError("SearXNG URL未配置")

            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    'q': query,
                    'format': 'json',
                    'language': language,
                    'engines': ','.join(self.engines)
                }
                response = await client.get(f"{self.searxng_url}/search", params=params)
                response.raise_for_status()

                data = response.json()

                results = []
                for i, item in enumerate(data.get('results', [])[:count]):
                    results.append(SearchResult(
                        title=item.get('title', ''),
                        url=item.get('url', ''),
                        snippet=item.get('content', ''),
                        engine='searxng',
                        rank=i + 1
                    ))

                logger.info(f"[统一网页] SearXNG搜索完成: {len(results)}条结果")
                return results

        except Exception as e:
            logger.error(f"[统一网页] SearXNG搜索失败: {e}")
            return []

    async def _search_google(self, query: str, count: int, language: str) -> List[SearchResult]:
        """使用Google搜索（占位）"""
        # TODO: 实现Google搜索
        logger.warning("[统一网页] Google搜索暂未实现，返回空结果")
        return []

    async def _search_generic(self, query: str, engine: str, count: int, language: str) -> List[SearchResult]:
        """通用搜索（占位）"""
        # TODO: 实现其他搜索引擎
        logger.warning(f"[统一网页] {engine}搜索暂未实现，返回空结果")
        return []

    # ==================== 抓取功能 ====================

    async def web_crawl(
        self,
        url: str,
        mode: str = CrawlMode.AUTO.value,
        format: str = ContentFormat.MARKDOWN.value,
        timeout: int = None
    ) -> CrawlResult:
        """智能网页内容抓取

        Args:
            url: 目标URL
            mode: 抓取模式 (static/dynamic/auto)
            format: 输出格式 (markdown/html/text/json)
            timeout: 超时时间（毫秒）

        Returns:
            抓取结果
        """
        timeout = timeout or self.timeout

        logger.info(f"[统一网页] 抓取网页: url={url}, mode={mode}, format={format}")

        try:
            # 自动选择模式
            if mode == CrawlMode.AUTO.value:
                mode = await self._detect_best_mode(url)

            if mode == CrawlMode.DYNAMIC.value:
                return await self._crawl_dynamic(url, format, timeout)
            else:
                return await self._crawl_static(url, format, timeout)

        except Exception as e:
            logger.error(f"[统一网页] 抓取失败: {e}")
            return CrawlResult(
                url=url,
                content="",
                format=format,
                mode=mode,
                status_code=0,
                error=str(e)
            )

    async def _detect_best_mode(self, url: str) -> str:
        """检测最佳抓取模式"""
        # TODO: 实现智能检测逻辑
        # 简单规则：已知需要JS渲染的网站使用动态模式
        js_heavy_sites = ['spa', 'app', 'react', 'vue', 'angular']
        if any(site in url.lower() for site in js_heavy_sites):
            return CrawlMode.DYNAMIC.value
        return CrawlMode.STATIC.value

    async def _crawl_static(
        self,
        url: str,
        format: str,
        timeout: int
    ) -> CrawlResult:
        """静态页面抓取"""
        try:
            import httpx
            from html2text import HTML2Text

            async with httpx.AsyncClient(timeout=timeout/1000) as client:
                response = await client.get(url)
                response.raise_for_status()

                if format == ContentFormat.HTML.value:
                    content = response.text
                elif format == ContentFormat.MARKDOWN.value:
                    h = HTML2Text()
                    h.ignore_links = False
                    content = h.handle(response.text)
                else:  # TEXT
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    content = soup.get_text()

                return CrawlResult(
                    url=url,
                    content=content,
                    format=format,
                    mode=CrawlMode.STATIC.value,
                    status_code=response.status_code
                )

        except Exception as e:
            logger.error(f"[统一网页] 静态抓取失败: {e}")
            raise

    async def _crawl_dynamic(
        self,
        url: str,
        format: str,
        timeout: int
    ) -> CrawlResult:
        """动态页面抓取（使用Playwright）"""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page()

                await page.goto(url, timeout=timeout)
                await page.wait_for_load_state('networkidle')

                if format == ContentFormat.HTML.value:
                    content = await page.content()
                elif format == ContentFormat.MARKDOWN.value:
                    html = await page.content()
                    from html2text import HTML2Text
                    h = HTML2Text()
                    content = h.handle(html)
                else:  # TEXT
                    content = await page.inner_text('body')

                await browser.close()

                return CrawlResult(
                    url=url,
                    content=content,
                    format=format,
                    mode=CrawlMode.DYNAMIC.value,
                    status_code=200
                )

        except Exception as e:
            logger.error(f"[统一网页] 动态抓取失败: {e}")
            raise

    # ==================== 浏览器自动化 ====================

    async def web_browse(
        self,
        url: str,
        actions: List[Dict[str, Any]] = None,
        screenshot: bool = False
    ) -> Dict[str, Any]:
        """浏览器自动化操作

        Args:
            url: 起始URL
            actions: 操作列表
                例如: [{"type": "click", "selector": "button"}, {"type": "input", "selector": "input", "value": "hello"}]
            screenshot: 是否截图

        Returns:
            操作结果
        """
        logger.info(f"[统一网页] 浏览器自动化: url={url}, actions={len(actions) if actions else 0}")

        try:
            from playwright.async_api import async_playwright
            import base64

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page()

                await page.goto(url)

                results = []

                if actions:
                    for action in actions:
                        action_type = action.get('type')

                        if action_type == 'click':
                            await page.click(action.get('selector'))
                            results.append({'action': 'click', 'success': True})

                        elif action_type == 'input':
                            await page.fill(action.get('selector'), action.get('value', ''))
                            results.append({'action': 'input', 'success': True})

                        elif action_type == 'scroll':
                            await page.evaluate(f'window.scrollTo(0, {action.get("y", 0)})')
                            results.append({'action': 'scroll', 'success': True})

                        elif action_type == 'wait':
                            await page.wait_for_timeout(action.get('ms', 1000))
                            results.append({'action': 'wait', 'success': True})

                screenshots = []
                if screenshot:
                    screenshot_data = await page.screenshot(full_page=False)
                    screenshots.append(base64.b64encode(screenshot_data).decode())

                await browser.close()

                return {
                    'success': True,
                    'results': results,
                    'screenshots': screenshots
                }

        except Exception as e:
            logger.error(f"[统一网页] 浏览器自动化失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def web_open(
        self,
        url: str,
        browser_type: str = "edge"
    ) -> Dict[str, Any]:
        """打开浏览器（简化接口）"""
        logger.info(f"[统一网页] 打开浏览器: url={url}, browser={browser_type}")

        try:
            from playwright.async_api import async_playwright

            # 支持的浏览器映射
            browser_map = {
                'edge': 'chromium',
                'chrome': 'chromium',
                'firefox': 'firefox',
                'webkit': 'webkit'
            }

            launch_browser = browser_map.get(browser_type.lower(), 'chromium')

            async with async_playwright() as p:
                browser = await p[launch_browser].launch(headless=False)
                page = await browser.new_page()
                await page.goto(url)

                # 获取页面标题
                title = await page.title()

                logger.info(f"[统一网页] 浏览器已打开: {title}")

                # 保持浏览器打开
                return {
                    'success': True,
                    'url': url,
                    'title': title,
                    'browser': browser_type,
                    'message': f'成功打开网页: {title}'
                }

        except Exception as e:
            logger.error(f"[统一网页] 打开浏览器失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== 内容解析 ====================

    async def web_parse(
        self,
        content: str,
        extract_type: str = "text"
    ) -> Dict[str, Any]:
        """智能内容解析

        Args:
            content: 网页内容
            extract_type: 提取类型 (text|links|images|table|all)

        Returns:
            提取结果
        """
        logger.info(f"[统一网页] 解析内容: type={extract_type}")

        try:
            from bs4 import BeautifulSoup
            import re

            soup = BeautifulSoup(content, 'html.parser')

            result = {}

            if extract_type in ['text', 'all']:
                # 清理文本
                text = soup.get_text(separator='\n', strip=True)
                result['text'] = text

            if extract_type in ['links', 'all']:
                # 提取链接
                links = []
                for a in soup.find_all('a', href=True):
                    links.append({
                        'text': a.get_text(strip=True),
                        'url': a['href']
                    })
                result['links'] = links

            if extract_type in ['images', 'all']:
                # 提取图片
                images = []
                for img in soup.find_all('img'):
                    images.append({
                        'src': img.get('src', ''),
                        'alt': img.get('alt', '')
                    })
                result['images'] = images

            if extract_type in ['table', 'all']:
                # 提取表格
                tables = []
                for table in soup.find_all('table'):
                    rows = []
                    for tr in table.find_all('tr'):
                        cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                        if cells:
                            rows.append(cells)
                    if rows:
                        tables.append(rows)
                result['tables'] = tables

            return {
                'success': True,
                'data': result
            }

        except Exception as e:
            logger.error(f"[统一网页] 内容解析失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== 工具方法 ====================

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'service': 'WebUnifiedAgent',
            'version': '1.0.0',
            'searxng_url': self.searxng_url,
            'default_engine': self.default_engine,
            'headless': self.headless,
            'engines': self.engines,
            'status': 'running'
        }


# ==================== MCP工具注册 ====================

def get_tools():
    """获取工具列表（用于MCP注册）"""
    return {
        'web_search': {
            'description': '统一网页搜索，支持多种搜索引擎',
            'parameters': {
                'query': {'type': 'string', 'description': '搜索关键词'},
                'engine': {'type': 'string', 'description': '搜索引擎 (searxng/google/bing/baidu)', 'default': 'searxng'},
                'count': {'type': 'integer', 'description': '结果数量', 'default': 5},
                'language': {'type': 'string', 'description': '语言设置', 'default': 'zh-CN'}
            }
        },
        'web_crawl': {
            'description': '智能网页内容抓取，支持静态和动态页面',
            'parameters': {
                'url': {'type': 'string', 'description': '目标URL'},
                'mode': {'type': 'string', 'description': '抓取模式 (static/dynamic/auto)', 'default': 'auto'},
                'format': {'type': 'string', 'description': '输出格式 (markdown/html/text)', 'default': 'markdown'},
                'timeout': {'type': 'integer', 'description': '超时时间（毫秒）', 'default': 30000}
            }
        },
        'web_browse': {
            'description': '浏览器自动化操作，支持点击、输入、滚动等',
            'parameters': {
                'url': {'type': 'string', 'description': '起始URL'},
                'actions': {'type': 'array', 'description': '操作列表'},
                'screenshot': {'type': 'boolean', 'description': '是否截图', 'default': False}
            }
        },
        'web_open': {
            'description': '使用浏览器打开网页（简化接口）',
            'parameters': {
                'url': {'type': 'string', 'description': '目标URL'},
                'browser_type': {'type': 'string', 'description': '浏览器类型 (edge/chrome/firefox)', 'default': 'edge'}
            }
        },
        'web_parse': {
            'description': '智能内容解析，提取关键信息',
            'parameters': {
                'content': {'type': 'string', 'description': '网页内容'},
                'extract_type': {'type': 'string', 'description': '提取类型 (text/links/images/table/all)', 'default': 'text'}
            }
        }
    }


if __name__ == '__main__':
    # 测试代码
    import asyncio

    async def test():
        config = {
            'online_search': {
                'searxng_url': 'https://searxng.pylindex.top',
                'default_engine': 'searxng',
                'result_count': 5,
                'engines': ['google']
            },
            'browser': {
                'headless': True
            },
            'crawl4ai': {
                'timeout': 30000
            }
        }

        agent = WebUnifiedAgent(config)

        # 测试搜索
        print("\n=== 测试搜索 ===")
        results = await agent.web_search("人工智能", count=3)
        for r in results:
            print(f"{r.rank}. {r.title}")
            print(f"   {r.url}")

        # 测试抓取
        print("\n=== 测试抓取 ===")
        result = await agent.web_crawl("https://www.baidu.com", mode="static")
        print(f"状态码: {result.status_code}")
        print(f"内容长度: {len(result.content)}")

        # 测试状态
        print("\n=== 服务状态 ===")
        status = agent.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))

    asyncio.run(test())
