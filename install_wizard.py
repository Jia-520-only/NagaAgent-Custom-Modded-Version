#!/usr/bin/env python3
"""
NagaAgent 一键安装配置向导
支持图形化配置界面
"""

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Dict, Any


class InstallWizard:
    """安装配置向导"""

    def __init__(self):
        script_dir = Path(__file__).parent.resolve()
        self.config_path = script_dir / "config.json"
        self.config_example_path = script_dir / "config.json.example"
        self.script_dir = script_dir
        self.config = {}

    def detect_environment(self) -> Dict[str, Any]:
        """检测运行环境"""
        return {
            "platform": sys.platform,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "project_path": str(self.script_dir),
        }

    def print_banner(self):
        """打印欢迎横幅"""
        banner = """
===========================================================
                                                          
              NagaAgent Configuration Wizard v1.0
                                                          
         Auto Install - GUI Config - Easy Setup
                                                          
===========================================================
        """
        print(banner)

    def get_user_input(self, prompt: str, default: str = "", required: bool = True) -> str:
        """获取用户输入"""
        if default:
            prompt = f"{prompt} [默认: {default}]: "
        else:
            prompt = f"{prompt}: "

        while True:
            value = input(prompt).strip()
            if not value:
                value = default
            if not required or value:
                return value
            print("此项为必填项,请重新输入")

    def get_boolean_input(self, prompt: str, default: bool = True) -> bool:
        """获取布尔值输入"""
        default_str = "Y/n" if default else "y/N"
        while True:
            value = input(f"{prompt} [{default_str}]: ").strip().lower()
            if not value:
                return default
            if value in ['y', 'yes', '是', 'y']:
                return True
            if value in ['n', 'no', '否', 'n']:
                return False
            print("请输入 y/n 或 yes/no")

    def configure_basic_settings(self) -> Dict[str, Any]:
        """配置基础设置"""
        print("\n=== 基础设置 ===")

        return {
            "version": "5.0.0",
            "ai_name": self.get_user_input("AI 名称", "弥娅", False),
            "voice_enabled": self.get_boolean_input("启用语音功能", True),
            "stream_mode": self.get_boolean_input("启用流式输出", True),
            "debug": self.get_boolean_input("调试模式", False),
            "log_level": "INFO",
            "save_prompts": True,
            "active_communication": self.get_boolean_input("启用主动交流", True),
            "voiceprint_enabled": False,
            "voiceprint_owner_name": self.get_user_input("声纹主人昵称", "YourName", False),
            "diary_enabled": self.get_boolean_input("启用日记功能", True),
        }

    def configure_api_settings(self) -> Dict[str, Any]:
        """配置 API 设置"""
        print("\n=== API 设置 ===")

        api_key = self.get_user_input("DeepSeek API Key", "", False)

        return {
            "api_key": api_key if api_key else "your-api-key-here",
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "max_tokens": 4096,
            "temperature": 0.7,
            "timeout": 60,
        }

    def configure_neo4j_settings(self) -> Dict[str, Any]:
        """配置 Neo4j 设置"""
        print("\n=== Neo4j 设置 (知识图谱) ===")

        enable_neo4j = self.get_boolean_input("启用 Neo4j 知识图谱", False)

        if not enable_neo4j:
            return {"enabled": False}

        return {
            "enabled": True,
            "neo4j_uri": self.get_user_input("Neo4j URI", "neo4j://127.0.0.1:7687", False),
            "neo4j_user": self.get_user_input("Neo4j 用户名", "neo4j", False),
            "neo4j_password": self.get_user_input("Neo4j 密码", "your-password", False),
            "enable_autonomous": False,
            "autonomous_threshold": 0.4,
        }

    def configure_tts_settings(self) -> Dict[str, Any]:
        """配置 TTS 设置"""
        print("\n=== TTS 语音设置 ===")

        return {
            "enabled": True,
            "port": 5048,
            "api_key": "",
            "default_engine": "edge_tts",
            "engine": "edge_tts",
            "default_voice": "zh-CN-XiaoxiaoNeural",
            "default_format": "mp3",
            "default_speed": 1.0,
            "gpt_sovits_enabled": False,
            "gpt_sovits_url": "http://127.0.0.1:9880",
            "gpt_sovits_ref_audio_path": "",
            "genie_tts_enabled": False,
            "genie_tts_url": "http://127.0.0.1:8000",
            "genie_tts_ref_free": True,
            "vits_enabled": False,
            "vits_url": "http://127.0.0.1:7860",
        }

    def configure_server_settings(self) -> Dict[str, Any]:
        """配置服务器设置"""
        print("\n=== 服务器设置 ===")

        return {
            "enabled": True,
            "auto_start": True,
            "host": "0.0.0.0",
            "port": 8000,
        }

    def load_example_config(self) -> Dict[str, Any]:
        """从示例配置文件加载"""
        if self.config_example_path.exists():
            try:
                with open(self.config_example_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载示例配置失败: {e}")
        return {}

    def save_config(self, config: Dict[str, Any]):
        """保存配置文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def run(self) -> bool:
        """运行配置向导"""
        self.print_banner()

        # 显示环境信息
        env_info = self.detect_environment()
        print(f"\n环境信息:")
        print(f"  平台: {env_info['platform']}")
        print(f"  Python: {env_info['python_version']}")
        print(f"  路径: {env_info['project_path']}")

        # 加载示例配置作为默认值
        example_config = self.load_example_config()

        # 配置各项设置
        self.config = {
            "system": self.configure_basic_settings(),
            "api": self.configure_api_settings(),
            "grag": self.configure_neo4j_settings(),
            "tts": self.configure_tts_settings(),
            "api_server": self.configure_server_settings(),
        }

        # 合并示例配置中的其他设置
        for key, value in example_config.items():
            if key not in self.config:
                self.config[key] = value

        # 保存配置
        try:
            self.save_config(self.config)
            print("\n配置已保存到:", self.config_path)
            return True
        except Exception as e:
            print(f"\n保存配置失败: {e}")
            return False


def main():
    """主函数"""
    wizard = InstallWizard()
    success = wizard.run()

    if success:
        print("\n" + "=" * 60)
        print("配置完成!")
        print("=" * 60)
        print("\n下一步:")
        print("1. 检查并修改 config.json 配置文件")
        print("2. 安装所需依赖 (如 Neo4j, GPT-SoVITS 等)")
        print("3. 运行 start.bat (Windows) 或 ./start.sh (Linux/Mac) 启动程序")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n配置失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
