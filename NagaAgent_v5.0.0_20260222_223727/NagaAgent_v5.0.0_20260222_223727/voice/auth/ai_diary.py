#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI日记管理模块
AI可以用人设口吻写日记
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("AIDiary")

class AIDiaryManager:
    """AI日记管理器"""

    def __init__(self, config_dir: str = "voice/auth"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.diary_file = self.config_dir / "ai_diary.json"
        self.diary_entries = []

        # 加载已有日记
        self._load_diary()

    def _load_diary(self):
        """加载日记"""
        try:
            if self.diary_file.exists():
                import json
                with open(self.diary_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.diary_entries = data.get('entries', [])
                logger.info(f"已加载 {len(self.diary_entries)} 条日记")
        except Exception as e:
            logger.error(f"加载日记失败: {e}")
            self.diary_entries = []

    def _save_diary(self):
        """保存日记"""
        try:
            import json
            data = {
                'entries': self.diary_entries
            }
            with open(self.diary_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("日记已保存")
        except Exception as e:
            logger.error(f"保存日记失败: {e}")

    def write_diary(self, content: str, auto_save: bool = True) -> bool:
        """
        写日记

        Args:
            content: 日记内容
            auto_save: 是否自动保存

        Returns:
            是否写入成功
        """
        try:
            # 创建日记条目
            entry = {
                'id': len(self.diary_entries) + 1,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'content': content
            }

            # 添加到日记列表
            self.diary_entries.append(entry)

            # 自动保存
            if auto_save:
                self._save_diary()

            logger.info(f"日记已写入: {entry['timestamp']}")
            return True

        except Exception as e:
            logger.error(f"写日记失败: {e}")
            return False

    def get_latest_diary(self, count: int = 10) -> list:
        """获取最近的日记"""
        return self.diary_entries[-count:] if self.diary_entries else []

    def get_diary_by_date(self, date: str) -> list:
        """获取指定日期的日记"""
        return [entry for entry in self.diary_entries if entry['timestamp'].startswith(date)]

    def delete_diary(self, entry_id: int) -> bool:
        """删除日记"""
        try:
            self.diary_entries = [e for e in self.diary_entries if e['id'] != entry_id]
            self._save_diary()
            logger.info(f"日记已删除: {entry_id}")
            return True
        except Exception as e:
            logger.error(f"删除日记失败: {e}")
            return False

    def clear_all_diary(self) -> bool:
        """清空所有日记"""
        try:
            self.diary_entries = []
            self._save_diary()
            logger.info("所有日记已清空")
            return True
        except Exception as e:
            logger.error(f"清空日记失败: {e}")
            return False

    def get_diary_count(self) -> int:
        """获取日记数量"""
        return len(self.diary_entries)

# 全局实例
_ai_diary_manager: Optional[AIDiaryManager] = None

def get_ai_diary_manager() -> AIDiaryManager:
    """获取AI日记管理器实例"""
    global _ai_diary_manager
    if _ai_diary_manager is None:
        _ai_diary_manager = AIDiaryManager()
    return _ai_diary_manager
