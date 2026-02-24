"""
包豆AI MCP Agent - 视觉自动化控制系统
通过MCP协议将包豆AI的屏幕分析和鼠标键盘自动化能力集成到弥娅中
"""

import json
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
import sys
import time
import os

# 添加baodou_AI模块路径
baodou_path = Path(__file__).parent.parent.parent / "baodou_AI"
baodou_path_abs = baodou_path.resolve()
if str(baodou_path_abs) not in sys.path:
    sys.path.insert(0, str(baodou_path_abs))

try:
    # 导入包豆AI核心模块
    import cv_shot_doubao
    from cv_shot_doubao import capture_screen_and_save, mark_coordinate_on_image
    # 注意: vl_model_test_doubao2 包含GUI相关代码,需要谨慎导入
    has_visual_module = True
except ImportError as e:
    has_visual_module = False
    print(f"[包豆AI] 警告: 无法导入视觉模块: {e}")
    print(f"[包豆AI] 当前模块路径: {baodou_path_abs}")


class BaodouAIController:
    """包豆AI控制器"""

    def __init__(self, config_path: Optional[str] = None, system_enabled: bool = False):
        self.config_path = config_path or str(baodou_path / "config.json")
        self.config = self._load_config()
        # 检查系统配置中的启用状态 + API密钥是否配置
        has_api_key = self.config.get("api_config", {}).get("api_key", "") != ""
        self.is_enabled = system_enabled and has_api_key
        self.current_task = None

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[包豆AI] 加载配置失败: {e}")
            return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            "api_config": {
                "api_key": "",
                "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                "model_name": "doubao-seed-1-6-vision-250815"
            },
            "ai_config": {
                "thinking_type": "disabled"
            },
            "execution_config": {
                "max_visual_model_iterations": 80,
                "default_max_iterations": 80
            },
            "screenshot_config": {
                "optimize_for_speed": True,
                "max_png": 1280,
                "input_path": "imgs/screen.png",
                "previous_image_path": "imgs/previous.png",
                "output_path": "imgs/label"
            },
            "mouse_config": {
                "move_duration": 0.1,
                "failsafe": False,
                "map_coordinates_to_1000": True
            }
        }

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "enabled": self.is_enabled,
            "has_visual_module": has_visual_module,
            "api_configured": bool(self.config.get("api_config", {}).get("api_key")),
            "current_task": self.current_task
        }

    def capture_screen(self, save_path: Optional[str] = None) -> str:
        """截取屏幕"""
        if not has_visual_module:
            return {"success": False, "error": "视觉模块未安装"}

        try:
            if save_path is None:
                save_path = self.config["screenshot_config"]["input_path"]

            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            result = capture_screen_and_save(save_path)
            return {"success": True, "path": save_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def mark_coordinates(self, coords: List[Dict[str, float]],
                       image_path: Optional[str] = None,
                       output_path: Optional[str] = None) -> Dict[str, Any]:
        """在图像上标记坐标点"""
        if not has_visual_module:
            return {"success": False, "error": "视觉模块未安装"}

        try:
            if image_path is None:
                image_path = self.config["screenshot_config"]["input_path"]
            if output_path is None:
                output_path = self.config["screenshot_config"]["output_path"]

            result = mark_coordinate_on_image(
                image_path=image_path,
                coordinates=coords,
                output_dir=output_path
            )
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}


# 全局控制器实例
_controller: Optional[BaodouAIController] = None


def get_controller() -> BaodouAIController:
    """获取控制器单例"""
    global _controller
    if _controller is None:
        _controller = BaodouAIController(system_enabled=False)  # 默认不启用
    return _controller


def initialize_controller(config_path: Optional[str] = None, system_enabled: bool = False):
    """初始化控制器"""
    global _controller
    _controller = BaodouAIController(config_path, system_enabled)
    return _controller
