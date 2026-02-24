"""异步安全的 IO 工具模块

从 Undefined_new 迁移，提供统一的异步 IO 操作接口
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Optional

# Windows 不支持 fcntl，需要使用 msvcrt
import platform
if platform.system() == 'Windows':
    import msvcrt
    import os
else:
    import fcntl

logger = logging.getLogger(__name__)


async def write_json(file_path: Path | str, data: Any, use_lock: bool = True) -> None:
    """异步安全地写入 JSON 文件

    参数:
        file_path: 文件路径
        data: 要写入的数据
        use_lock: 是否使用文件锁确保并发安全
    """
    p = Path(file_path)
    start_time = time.perf_counter()

    # 估算数据大小
    data_size = len(str(data))
    logger.debug(
        f"[IO] 写入JSON: path={p}, use_lock={use_lock}, size_estimate={data_size} chars"
    )

    def sync_write() -> None:
        p.parent.mkdir(parents=True, exist_ok=True)
        # 用 "w" 模式打开
        with open(p, "w", encoding="utf-8") as f:
            if use_lock:
                logger.debug(f"[IO] 获取排他锁: path={p}")
                _acquire_lock(f)
            try:
                json.dump(data, f, ensure_ascii=False, indent=2)
                # 显式刷新到磁盘
                f.flush()
            finally:
                if use_lock:
                    _release_lock(f)
                    logger.debug(f"[IO] 释放锁: path={p}")

    try:
        await asyncio.to_thread(sync_write)
        elapsed = time.perf_counter() - start_time
        logger.info(f"[IO] 写入成功: path={p}, elapsed={elapsed:.3f}s")
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        logger.error(f"[IO] 写入失败: path={p}, elapsed={elapsed:.3f}s, error={e}")
        raise


async def read_json(file_path: Path | str, use_lock: bool = False) -> Optional[Any]:
    """异步安全地读取 JSON 文件

    参数:
        file_path: 文件路径
        use_lock: 是否使用共享锁读取

    返回:
        解析后的 JSON 数据，如果文件不存在则返回 None
    """
    p = Path(file_path)
    start_time = time.perf_counter()

    logger.debug(f"[IO] 读取JSON: path={p}, use_lock={use_lock}")

    def sync_read() -> Optional[Any]:
        if not p.exists():
            logger.debug(f"[IO] 文件不存在: path={p}")
            return None
        with open(p, "r", encoding="utf-8") as f:
            if use_lock:
                logger.debug(f"[IO] 获取共享锁: path={p}")
                _acquire_lock(f, shared=True)
            try:
                return json.load(f)
            finally:
                if use_lock:
                    _release_lock(f)
                    logger.debug(f"[IO] 释放锁: path={p}")

    try:
        result = await asyncio.to_thread(sync_read)
        elapsed = time.perf_counter() - start_time
        logger.info(f"[IO] 读取成功: path={p}, elapsed={elapsed:.3f}s")
        return result
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        logger.error(f"[IO] 读取失败: path={p}, elapsed={elapsed:.3f}s, error={e}")
        raise


async def append_line(file_path: Path | str, line: str, use_lock: bool = True) -> None:
    """异步安全地向文件追加一行

    参数:
        file_path: 文件路径
        line: 要追加的内容（会自动添加换行符）
        use_lock: 是否使用文件锁
    """
    p = Path(file_path)
    start_time = time.perf_counter()

    if not line.endswith("\n"):
        line += "\n"

    logger.debug(f"[IO] 追加行: path={p}, use_lock={use_lock}, line_length={len(line)}")

    def sync_append() -> None:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            if use_lock:
                logger.debug(f"[IO] 获取排他锁: path={p}")
                _acquire_lock(f)
            try:
                f.write(line)
                f.flush()
            finally:
                if use_lock:
                    _release_lock(f)
                    logger.debug(f"[IO] 释放锁: path={p}")

    try:
        await asyncio.to_thread(sync_append)
        elapsed = time.perf_counter() - start_time
        logger.info(f"[IO] 追加成功: path={p}, elapsed={elapsed:.3f}s")
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        logger.error(f"[IO] 追加失败: path={p}, elapsed={elapsed:.3f}s, error={e}")
        raise


async def exists(file_path: Path | str) -> bool:
    """异步检查文件是否存在"""
    return await asyncio.to_thread(Path(file_path).exists)


async def delete_file(file_path: Path | str) -> bool:
    """异步删除文件"""
    p = Path(file_path)

    def sync_delete() -> bool:
        if p.exists():
            p.unlink()
            return True
        return False

    return await asyncio.to_thread(sync_delete)


# ============================================================================
# 文件锁实现 - 跨平台支持
# ============================================================================

def _acquire_lock(file_obj, shared: bool = False):
    """获取文件锁（跨平台）

    Args:
        file_obj: 文件对象
        shared: 是否为共享锁（仅 Linux/Unix 支持）
    """
    if platform.system() == 'Windows':
        # Windows 使用 msvcrt.locking
        # LOCK_EX = 0x2 (排他锁)
        msvcrt.locking(file_obj.fileno(), msvcrt.LK_LOCK, 1)
    else:
        # Linux/Unix 使用 fcntl
        if shared:
            fcntl.flock(file_obj.fileno(), fcntl.LOCK_SH)
        else:
            fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)


def _release_lock(file_obj):
    """释放文件锁（跨平台）"""
    if platform.system() == 'Windows':
        # Windows 通过 close 自动释放，这里不需要操作
        pass
    else:
        # Linux/Unix 使用 fcntl
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)
