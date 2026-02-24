#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自主性管理器 - Agency Manager
提供自主性控制接口和管理功能
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from pathlib import Path

from system.config import config, logger
from system.agency_engine import AgencyEngine, AgencyLevel, AutonomousAction, get_agency_engine


class AgencyManager:
    """自主性管理器"""
    
    def __init__(self):
        self.engine = get_agency_engine()
        self.config_path = Path(__file__).parent / "agency_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"[自主性管理] 加载配置失败: {e}")
        
        # 默认配置
        return {
            "agency_level": "HIGH",
            "value_weights": {
                "user_efficiency": 0.35,
                "user_wellbeing": 0.30,
                "helpful": 0.25,
                "non_intrusive": 0.10
            },
            "enabled_features": {
                "predict_needs": True,
                "late_night_reminders": True,
                "learning_help": True,
                "task_suggestions": True,
                "proactive_communication": True
            },
            "quiet_hours": {
                "enabled": True,
                "start": 23,
                "end": 7
            }
        }
    
    def _save_config(self):
        """保存配置"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("[自主性管理] 配置已保存")
        except Exception as e:
            logger.error(f"[自主性管理] 保存配置失败: {e}")
    
    async def start(self):
        """启动自主性系统"""
        # 应用配置
        level = AgencyLevel[self.config["agency_level"]]
        await self.engine.set_agency_level(level)
        
        # 设置价值观权重
        self.engine.value_weights = self.config["value_weights"]
        
        # 启动引擎
        await self.engine.start()
        
        logger.info("[自主性管理] 系统已启动")
    
    async def pause(self, reason: str = "用户手动暂停"):
        """暂停自主性"""
        await self.engine.pause(reason)
        logger.info(f"[自主性管理] 已暂停: {reason}")
    
    async def resume(self):
        """恢复自主性"""
        await self.engine.resume()
        logger.info("[自主性管理] 已恢复")
    
    async def set_level(self, level_name: str):
        """设置自主性等级"""
        try:
            level = AgencyLevel[level_name]
            await self.engine.set_agency_level(level)
            self.config["agency_level"] = level_name
            self._save_config()
            return {"success": True, "message": f"自主等级已设置为: {level_name}"}
        except KeyError:
            return {"success": False, "message": f"无效的自主等级: {level_name}"}
    
    async def toggle_feature(self, feature_name: str, enabled: bool):
        """开关功能"""
        if feature_name in self.config["enabled_features"]:
            self.config["enabled_features"][feature_name] = enabled
            self._save_config()
            return {"success": True, "message": f"功能已{'启用' if enabled else '禁用'}: {feature_name}"}
        else:
            return {"success": False, "message": f"未知功能: {feature_name}"}
    
    async def adjust_value_weight(self, value_name: str, weight: float):
        """调整价值观权重"""
        if value_name in self.config["value_weights"]:
            # 验证权重总和
            new_weights = self.config["value_weights"].copy()
            new_weights[value_name] = weight
            
            total = sum(new_weights.values())
            if abs(total - 1.0) > 0.01:
                return {
                    "success": False, 
                    "message": f"权重总和必须为1.0，当前总和: {total:.2f}"
                }
            
            self.config["value_weights"] = new_weights
            self._save_config()
            self.engine.value_weights = new_weights
            return {"success": True, "message": f"价值观权重已更新: {value_name}={weight}"}
        else:
            return {"success": False, "message": f"未知价值观: {value_name}"}
    
    async def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        engine_status = self.engine.get_status()
        
        return {
            "engine": engine_status,
            "config": self.config,
            "active_features": [k for k, v in self.config["enabled_features"].items() if v],
            "recent_actions": self.engine.action_history[-10:],
            "upcoming_actions": self.engine.action_queue[:5]
        }
    
    async def get_action_history(self, limit: int = 20) -> List[Dict]:
        """获取行动历史"""
        history = self.engine.action_history[-limit:]
        return history
    
    async def clear_history(self):
        """清除历史记录"""
        self.engine.action_history.clear()
        logger.info("[自主性管理] 历史记录已清除")
        return {"success": True, "message": "历史记录已清除"}
    
    async def trigger_manual_action(self, action_type: str, description: str):
        """手动触发行动（用于测试或特殊需求）"""
        action = AutonomousAction(
            action_id=f"manual_{int(datetime.now().timestamp())}",
            action_type=action_type,
            priority=getattr(AutonomousAction.Priority, "MEDIUM"),
            description=description,
            context={"trigger": "manual"},
            requires_approval=False
        )
        
        # 加入队列
        self.engine.action_queue.append(action)
        
        return {"success": True, "message": f"已加入手动行动: {description}"}


# 全局实例
_agency_manager: Optional[AgencyManager] = None


def get_agency_manager() -> AgencyManager:
    """获取自主性管理器实例"""
    global _agency_manager
    if _agency_manager is None:
        _agency_manager = AgencyManager()
    return _agency_manager
