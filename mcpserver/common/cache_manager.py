"""
缓存管理器

支持内存缓存和磁盘缓存，LRU淘汰策略

作者: NagaAgent Team
版本: 1.0.0
"""

import json
import logging
import hashlib
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from pathlib import Path
from collections import OrderedDict

logger = logging.getLogger(__name__)


class CacheManager:
    """缓存管理器"""

    def __init__(
        self,
        max_size: int = 1000,
        ttl: int = 3600,
        disk_cache_dir: Optional[str] = None
    ):
        """初始化

        Args:
            max_size: 最大缓存数量（LRU）
            ttl: 缓存生存时间（秒）
            disk_cache_dir: 磁盘缓存目录
        """
        self.max_size = max_size
        self.ttl = ttl
        self.disk_cache_dir = Path(disk_cache_dir) if disk_cache_dir else None

        # 内存缓存（有序字典，实现LRU）
        self.memory_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()

        # 创建磁盘缓存目录
        if self.disk_cache_dir:
            self.disk_cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info("[CacheManager] 初始化完成")

    def _generate_key(self, *args) -> str:
        """生成缓存键"""
        key_str = str(args)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在返回None
        """
        # 先查内存缓存
        if key in self.memory_cache:
            cache_item = self.memory_cache[key]

            # 检查是否过期
            if datetime.now() < cache_item['expiry']:
                # 移到末尾（标记为最近使用）
                self.memory_cache.move_to_end(key)
                logger.debug(f"[CacheManager] 内存缓存命中: {key}")
                return cache_item['value']
            else:
                # 已过期，删除
                del self.memory_cache[key]

        # 查磁盘缓存
        if self.disk_cache_dir:
            cache_file = self.disk_cache_dir / f"{key}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_item = json.load(f)

                    # 检查是否过期
                    expiry = datetime.fromisoformat(cache_item['expiry'])
                    if datetime.now() < expiry:
                        # 写入内存缓存
                        self.memory_cache[key] = cache_item
                        logger.debug(f"[CacheManager] 磁盘缓存命中: {key}")
                        return cache_item['value']
                    else:
                        # 已过期，删除
                        cache_file.unlink()

                except Exception as e:
                    logger.warning(f"[CacheManager] 读取磁盘缓存失败: {e}")

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），默认使用实例TTL
        """
        ttl = ttl or self.ttl
        expiry = datetime.now() + timedelta(seconds=ttl)

        cache_item = {
            'value': value,
            'expiry': expiry.isoformat(),
            'created': datetime.now().isoformat()
        }

        # 检查容量，淘汰最旧的
        if len(self.memory_cache) >= self.max_size and key not in self.memory_cache:
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]
            logger.debug(f"[CacheManager] LRU淘汰: {oldest_key}")

        # 存入内存
        self.memory_cache[key] = cache_item
        self.memory_cache.move_to_end(key)

        # 存入磁盘
        if self.disk_cache_dir:
            try:
                cache_file = self.disk_cache_dir / f"{key}.json"
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_item, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning(f"[CacheManager] 写入磁盘缓存失败: {e}")

        logger.debug(f"[CacheManager] 缓存已设置: {key}")

    def delete(self, key: str) -> None:
        """删除缓存

        Args:
            key: 缓存键
        """
        if key in self.memory_cache:
            del self.memory_cache[key]

        if self.disk_cache_dir:
            cache_file = self.disk_cache_dir / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink()

        logger.debug(f"[CacheManager] 缓存已删除: {key}")

    def clear(self) -> None:
        """清空所有缓存"""
        self.memory_cache.clear()

        if self.disk_cache_dir and self.disk_cache_dir.exists():
            for cache_file in self.disk_cache_dir.glob("*.json"):
                cache_file.unlink()

        logger.info("[CacheManager] 所有缓存已清空")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息

        Returns:
            统计信息字典
        """
        memory_count = len(self.memory_cache)
        disk_count = 0

        if self.disk_cache_dir and self.disk_cache_dir.exists():
            disk_count = len(list(self.disk_cache_dir.glob("*.json")))

        return {
            'memory_count': memory_count,
            'disk_count': disk_count,
            'max_size': self.max_size,
            'ttl': self.ttl
        }


# 全局缓存管理器实例
_global_cache: Optional[CacheManager] = None


def get_global_cache() -> CacheManager:
    """获取全局缓存管理器"""
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager()
    return _global_cache


def clear_global_cache():
    """清空全局缓存"""
    global _global_cache
    if _global_cache is not None:
        _global_cache.clear()
