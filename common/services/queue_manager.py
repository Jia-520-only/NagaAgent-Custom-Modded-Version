"""AI 请求队列管理服务

从 Undefined_new 迁移的"车站-列车"队列模型
提供四级优先级队列和非阻塞调度
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


@dataclass
class ModelQueue:
    """单个模型的优先队列组"""

    model_name: str
    superadmin_queue: asyncio.Queue[dict[str, Any]] = field(
        default_factory=asyncio.Queue
    )
    private_queue: asyncio.Queue[dict[str, Any]] = field(default_factory=asyncio.Queue)
    group_mention_queue: asyncio.Queue[dict[str, Any]] = field(
        default_factory=asyncio.Queue
    )
    group_normal_queue: asyncio.Queue[dict[str, Any]] = field(
        default_factory=asyncio.Queue
    )

    def trim_normal_queue(self) -> None:
        """如果群聊普通队列超过10个，仅保留最新的2个"""
        queue_size = self.group_normal_queue.qsize()
        if queue_size > 10:
            logger.info(
                f"[队列修剪][{self.model_name}] 群聊普通队列长度 {queue_size} 超过阈值(10)，正在修剪..."
            )
            # 取出所有元素
            all_requests: list[dict[str, Any]] = []
            while not self.group_normal_queue.empty():
                all_requests.append(self.group_normal_queue.get_nowait())
            # 只保留最新的2个
            latest_requests = all_requests[-2:]
            # 放回队列
            for req in latest_requests:
                self.group_normal_queue.put_nowait(req)
            logger.info(
                f"[队列修剪][{self.model_name}] 修剪完成，保留最新 {len(latest_requests)} 个请求"
            )


class QueueManager:
    """负责 AI 请求的队列管理和调度

    采用"站台-列车"模型：
    1. 每个模型有独立的队列组（站台）
    2. 每个模型每秒发车一次（列车），带走一个请求
    3. 请求处理是异步不阻塞的（不管前一个是否结束）
    """

    def __init__(self, ai_request_interval: float = 1.0) -> None:
        self.ai_request_interval = ai_request_interval

        # 按模型名称区分的队列组
        self._model_queues: dict[str, ModelQueue] = {}

        # 处理任务映射 model_name -> Task
        self._processor_tasks: dict[str, asyncio.Task[None]] = {}

        self._request_handler: (
            Callable[[dict[str, Any]], Coroutine[Any, Any, None]] | None
        ) = None

    def start(
        self, request_handler: Callable[[dict[str, Any]], Coroutine[Any, Any, None]]
    ) -> None:
        """启动队列处理任务"""
        self._request_handler = request_handler
        logger.info("[队列服务] 队列管理器已就绪")

    async def stop(self) -> None:
        """停止所有队列处理任务"""
        logger.info("[队列服务] 正在停止所有队列处理任务...")
        for name, task in self._processor_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self._processor_tasks.clear()
        logger.info("[队列服务] 所有队列处理任务已停止")

    def _get_or_create_queue(self, model_name: str) -> ModelQueue:
        """获取或创建指定模型的队列，并确保处理任务已启动"""
        if model_name not in self._model_queues:
            self._model_queues[model_name] = ModelQueue(model_name=model_name)
            # 启动该模型的处理任务
            if self._request_handler:
                task = asyncio.create_task(self._process_model_loop(model_name))
                self._processor_tasks[model_name] = task
                logger.info(f"[队列服务] 已启动模型 [{model_name}] 的处理循环")
        return self._model_queues[model_name]

    async def add_superadmin_request(
        self, request: dict[str, Any], model_name: str = "default"
    ) -> None:
        """添加超级管理员请求"""
        queue = self._get_or_create_queue(model_name)
        await queue.superadmin_queue.put(request)
        logger.info(
            f"[队列入队][{model_name}] 超级管理员私聊: 队列长度={queue.superadmin_queue.qsize()}"
        )

    async def add_private_request(
        self, request: dict[str, Any], model_name: str = "default"
    ) -> None:
        """添加普通私聊请求"""
        queue = self._get_or_create_queue(model_name)
        await queue.private_queue.put(request)
        logger.info(
            f"[队列入队][{model_name}] 普通私聊: 队列长度={queue.private_queue.qsize()}"
        )

    async def add_group_mention_request(
        self, request: dict[str, Any], model_name: str = "default"
    ) -> None:
        """添加群聊被@请求"""
        queue = self._get_or_create_queue(model_name)
        await queue.group_mention_queue.put(request)
        logger.info(
            f"[队列入队][{model_name}] 群聊被@: 队列长度={queue.group_mention_queue.qsize()}"
        )

    async def add_group_normal_request(
        self, request: dict[str, Any], model_name: str = "default"
    ) -> None:
        """添加群聊普通请求 (会自动裁剪)"""
        queue = self._get_or_create_queue(model_name)
        queue.trim_normal_queue()
        await queue.group_normal_queue.put(request)
        logger.info(
            f"[队列入队][{model_name}] 群聊普通: 队列长度={queue.group_normal_queue.qsize()}"
        )

    async def _process_model_loop(self, model_name: str) -> None:
        """单个模型的处理循环（列车调度）"""
        model_queue = self._model_queues[model_name]
        queues = [
            model_queue.superadmin_queue,
            model_queue.private_queue,
            model_queue.group_mention_queue,
            model_queue.group_normal_queue,
        ]
        
        # 轮询索引和计数
        queue_idx = 0
        processed_count = 0
        max_per_queue = 2  # 每个队列最多连续处理2个请求（防饿死）
        
        logger.info(
            f"[队列服务][{model_name}] 车站-列车调度循环已启动 (1Hz)"
        )
        
        while True:
            cycle_start_time = time.perf_counter()
            
            try:
                # 按优先级轮询获取请求
                request = None
                for i in range(4):
                    idx = (queue_idx + i) % 4
                    q = queues[idx]
                    
                    if not q.empty():
                        request = await q.get()
                        processed_count += 1
                        
                        # 检查是否切换队列
                        if processed_count >= max_per_queue:
                            queue_idx = (queue_idx + 1) % 4
                            processed_count = 0
                        
                        break
                
                if request and self._request_handler:
                    # 异步执行，不阻塞
                    asyncio.create_task(self._safe_handle_request(request))
                    logger.debug(
                        f"[队列服务][{model_name}] 发车: request_id={request.get('request_id', 'unknown')}"
                    )
                
                # 确保固定频率 (1Hz)
                elapsed = time.perf_counter() - cycle_start_time
                wait_time = max(0.0, self.ai_request_interval - elapsed)
                await asyncio.sleep(wait_time)
                
            except asyncio.CancelledError:
                logger.info(f"[队列服务][{model_name}] 调度循环已停止")
                break
            except Exception as e:
                logger.error(
                    f"[队列服务][{model_name}] 调度循环异常: {e}",
                    exc_info=True
                )
                await asyncio.sleep(1.0)  # 出错后等待1秒

    async def _safe_handle_request(self, request: dict[str, Any]) -> None:
        """安全处理请求（捕获异常）"""
        try:
            await self._request_handler(request)
        except Exception as e:
            logger.error(
                f"[队列服务] 请求处理异常: request={request.get('request_id', 'unknown')}, error={e}",
                exc_info=True
            )

    def get_queue_status(self, model_name: str = "default") -> dict[str, int]:
        """获取队列状态"""
        if model_name not in self._model_queues:
            return {}
        
        q = self._model_queues[model_name]
        return {
            "superadmin": q.superadmin_queue.qsize(),
            "private": q.private_queue.qsize(),
            "group_mention": q.group_mention_queue.qsize(),
            "group_normal": q.group_normal_queue.qsize(),
        }
