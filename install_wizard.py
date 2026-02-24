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
            "temperature": 0.7,
            "max_tokens": 8192,
            "max_history_rounds": 20,
            "persistent_context": self.get_boolean_input("启用持久化上下文", True),
            "context_load_days": 3,
            "context_parse_logs": True,
            "applied_proxy": False,
        }

    def configure_tts_settings(self) -> Dict[str, Any]:
        """配置 TTS 设置"""
        print("\n=== 语音合成 (TTS) 设置 ===")

        print("请选择 TTS 引擎:")
        print("1. GPT-SoVITS (推荐)")
        print("2. Genie-TTS")
        print("3. VITS")

        choice = input("选择引擎 [1]: ").strip() or "1"

        ref_audio_path = ""
        if choice == "1":
            ref_audio_path = self.get_user_input(
                "参考音频文件路径 (用于音色克隆)",
                "path/to/your/reference/audio.wav",
                False
            )

        return {
            "api_key": "",
            "port": 5046,
            "default_voice": "zh-CN-XiaoxiaoNeural",
            "default_format": "mp3",
            "default_speed": 1.0,
            "default_language": "zh-CN",
            "remove_filter": False,
            "expand_api": True,
            "require_api_key": False,
            "default_engine": "gpt_sovits",
            "gpt_sovits_enabled": choice == "1",
            "gpt_sovits_url": "http://127.0.0.1:9880",
            "gpt_sovits_speed": 1.0,
            "gpt_sovits_top_k": 15,
            "gpt_sovits_top_p": 1.0,
            "gpt_sovits_temperature": 1.0,
            "gpt_sovits_ref_free": False,
            "gpt_sovits_ref_text": "参考文本，用于音色克隆",
            "gpt_sovits_ref_audio_path": ref_audio_path,
            "gpt_sovits_filter_brackets": True,
            "gpt_sovits_filter_special_chars": True,
            "genie_tts_enabled": choice == "2",
            "genie_tts_url": "http://127.0.0.1:8000",
            "genie_tts_speed": 1.0,
            "genie_tts_top_k": 15,
            "genie_tts_top_p": 1.0,
            "genie_tts_temperature": 1.0,
            "genie_tts_ref_free": False,
            "genie_tts_ref_text": "",
            "genie_tts_ref_audio_path": "",
            "genie_tts_timeout": 60,
            "vits_enabled": choice == "3",
            "vits_url": "http://127.0.0.1:7860",
            "vits_voice_id": 0,
            "vits_noise_scale": 0.667,
            "vits_noise_scale_w": 0.8,
            "vits_length_scale": 1.0,
        }

    def configure_neo4j_settings(self) -> Dict[str, Any]:
        """配置 Neo4j 设置"""
        print("\n=== Neo4j 图数据库设置 ===")

        enabled = self.get_boolean_input("启用知识图谱功能", True)

        if not enabled:
            return {
                "enabled": False,
                "auto_extract": False,
                "context_length": 5,
                "similarity_threshold": 0.6,
                "neo4j_uri": "neo4j://127.0.0.1:7687",
                "neo4j_user": "neo4j",
                "neo4j_password": "your-neo4j-password",
                "neo4j_database": "neo4j",
                "extraction_timeout": 12,
                "extraction_retries": 2,
                "base_timeout": 15,
            }

        return {
            "enabled": True,
            "auto_extract": self.get_boolean_input("自动提取知识", True),
            "context_length": 5,
            "similarity_threshold": 0.6,
            "neo4j_uri": "neo4j://127.0.0.1:7687",
            "neo4j_user": "neo4j",
            "neo4j_password": self.get_user_input("Neo4j 密码", "your-neo4j-password", False),
            "neo4j_database": "neo4j",
            "extraction_timeout": 12,
            "extraction_retries": 2,
            "base_timeout": 15,
        }

    def configure_qq_wechat_settings(self) -> Dict[str, Any]:
        """配置 QQ/微信 设置"""
        print("\n=== QQ/微信 机器人设置 ===")

        qq_enabled = self.get_boolean_input("启用 QQ 机器人", False)

        qq_config = {
            "enabled": qq_enabled,
            "adapter": "napcat-go",
            "ws_url": "ws://127.0.0.1:3001",
            "http_url": "http://127.0.0.1:3000",
            "bot_qq": self.get_user_input("机器人 QQ 号", "your-bot-qq-number", False),
            "access_token": "",
            "http_token": self.get_user_input("HTTP Token", "your-http-token", False),
            "ws_token": self.get_user_input("WS Token", "your-ws-token", False),
            "auto_reconnect": True,
            "reconnect_interval": 5,
            "enable_auto_reply": True,
            "reply_mode": "voice",
            "enable_voice": True,
            "enable_undefined_tools": True,
            "enable_group_reply": True,
            "group_reply_mode": "auto",
            "group_whitelist": [],
            "group_blacklist": [],
            "group_reply_keywords": ["机器人", "AI", "赛博老婆", "弥娅"],
            "group_reply_cooldown": 5,
            "enable_group_tools": False,
            "group_disabled_tools": ["send_message", "send_private_message"],
            "enable_topic_detection": True,
            "topic_relevance_keywords": [
                "机器人", "AI", "有人吗", "弥娅", "帮忙", "查询", "天气",
                "亲爱的", "宝贝", "老婆", "时间", "画图", "绘图", "搜索",
                "新闻", "音乐", "视频", "笑话", "故事", "你好", "在吗", "喜欢我", "喜欢"
            ],
            "enable_emoji_reply": False,
            "emoji_reply_keywords": {
                "😊": ["开心", "高兴", "哈哈", "嘿嘿"],
                "😢": ["难过", "伤心", "哭", "呜呜"],
                "😡": ["生气", "愤怒", "气死"],
                "😍": ["喜欢", "爱", "心动"],
                "🤔": ["思考", "想", "不知道"],
                "👍": ["赞", "棒", "好", "厉害"],
                "👎": ["差", "不行", "不好"]
            },
            "enable_smart_emoji": True,
            "merge_group_private_memory": True,
            "enable_qq_call": True,
        }

        wechat_enabled = self.get_boolean_input("启用微信机器人", False)

        return {
            "qq": qq_config,
            "wechat": {
                "enabled": wechat_enabled,
                "auto_login": True,
                "enable_login_qrcode": True,
                "enable_auto_reply": True,
            }
        }

    def generate_config(self) -> Dict[str, Any]:
        """生成完整配置"""
        env = self.detect_environment()

        print(f"\n检测到运行环境:")
        print(f"  平台: {env['platform']}")
        print(f"  Python 版本: {env['python_version']}")
        print(f"  项目路径: {env['project_path']}")

        config = {}

        # 基础设置
        config["system"] = self.configure_basic_settings()

        # 意识设置
        config["consciousness"] = {
            "enabled": self.get_boolean_input("启用意识系统", True),
            "mode": "hybrid"
        }

        # 位置设置
        config["location"] = {
            "enabled": self.get_boolean_input("启用位置功能", True),
            "auto_detect": True,
            "manual_city": ""
        }

        # API 设置
        config["api"] = self.configure_api_settings()

        # 服务设置
        config["api_server"] = {
            "enabled": True,
            "host": "0.0.0.0",
            "port": 8000,
            "auto_start": True,
            "docs_enabled": True,
        }

        config["agentserver"] = {
            "enabled": True,
            "host": "127.0.0.1",
            "port": 8001,
            "auto_start": True,
        }

        config["mcpserver"] = {
            "enabled": True,
            "host": "127.0.0.1",
            "port": 8003,
            "auto_start": True,
            "agent_discovery": True,
        }

        # Neo4j 设置
        config["grag"] = self.configure_neo4j_settings()

        # 其他设置
        config["handoff"] = {
            "max_loop_stream": 5,
            "max_loop_non_stream": 5,
            "show_output": False,
        }

        config["browser"] = {
            "playwright_headless": False,
        }

        # TTS 设置
        config["tts"] = self.configure_tts_settings()

        # 其他配置 (使用默认值)
        config["game"] = {"enabled": False, "skip_on_error": True}

        config["voice_realtime"] = {
            "enabled": self.get_boolean_input("启用实时语音交互", True),
            "provider": "local",
            "api_key": "your-dashscope-api-key-here",
            "model": "qwen3-omni-flash-realtime",
            "tts_model": "qwen-tts-realtime",
            "asr_model": "qwen3-asr-realtime",
            "voice": "Cherry",
            "voice_mode": "auto",
            "tts_voice": "zh-CN-XiaoyiNeural",
            "input_sample_rate": 16000,
            "output_sample_rate": 24000,
            "chunk_size_ms": 200,
            "vad_threshold": 0.02,
            "echo_suppression": True,
            "min_user_interval": 2.0,
            "cooldown_duration": 1.0,
            "max_user_speech": 30.0,
            "debug": False,
            "integrate_with_memory": True,
            "show_in_chat": True,
            "use_api_server": True,
            "auto_play": True,
        }

        config["weather"] = {
            "api_key": self.get_user_input("天气 API Key (可选)", "", False)
        }

        config["mqtt"] = {
            "enabled": False,
            "broker": "mqtt-broker-address",
            "port": 1883,
            "topic": "naga/agent/topic",
            "client_id": "naga-agent-client",
            "username": "mqtt-username",
            "password": "mqtt-password",
            "keepalive": 60,
            "qos": 1,
        }

        config["ui"] = {
            "user_name": self.get_user_input("用户昵称", "YourName", False),
            "bg_alpha": 0.81,
            "window_bg_alpha": 128,
            "mac_btn_size": 36,
            "mac_btn_margin": 16,
            "mac_btn_gap": 12,
            "animation_duration": 600,
        }

        config["naga_portal"] = {
            "portal_url": "https://naga.furina.chat/",
            "username": "your-portal-username",
            "password": "your-portal-password",
        }

        config["online_search"] = {
            "searxng_url": "https://searxng.pylindex.top",
            "engines": ["google"],
            "num_results": 5,
        }

        config["computer_control"] = {
            "enabled": False,
            "model": "GLM-4.6V-Flash",
            "model_url": "https://open.bigmodel.cn/api/paas/v4",
            "api_key": "your-zhipu-api-key",
            "grounding_model": "GLM-4.6V-Flash",
            "grounding_url": "https://open.bigmodel.cn/api/paas/v4",
            "grounding_api_key": "your-zhipu-api-key",
            "screen_width": 1920,
            "screen_height": 1080,
            "max_dim_size": 1920,
            "dpi_awareness": True,
            "safe_mode": True,
        }

        config["guide_engine"] = {
            "enabled": False,
            "gamedata_dir": "./data",
            "embedding_api_base_url": "",
            "embedding_api_key": "",
            "embedding_api_model": "text-embedding-3-small",
            "game_guide_llm_api_base_url": "",
            "game_guide_llm_api_key": "",
            "game_guide_llm_api_model": "",
            "game_guide_llm_api_type": "openai",
            "prompt_dir": "./guide_engine/game_prompts",
            "neo4j_uri": "neo4j://127.0.0.1:7687",
            "neo4j_user": "neo4j",
            "neo4j_password": "your_password",
            "screenshot_monitor_index": 1,
            "auto_screenshot_on_guide": True,
        }

        config["memory_server"] = {
            "url": "http://localhost:8004",
            "token": None,
        }

        config["embedding"] = {
            "model": "tongyi-embedding",
            "api_base": "",
            "api_key": "",
        }

        config["crawl4ai"] = {
            "headless": True,
            "timeout": 30000,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "viewport_width": 1280,
            "viewport_height": 720,
        }

        config["live2d"] = {
            "enabled": False,
            "model_path": "ui/live2d_local/live2d_models/重音テト/重音テト.model3.json",
            "fallback_image": "ui/img/standby.png",
            "auto_switch": True,
            "animation_enabled": True,
            "touch_interaction": True,
        }

        config["baodou_ai"] = {
            "enabled": self.get_boolean_input("启用宝斗AI视觉", True),
            "config_path": "baodou_AI/config.json",
            "api_key": "",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model_name": "doubao-seed-1-6-vision-250815",
            "max_iterations": 80,
            "safe_mode": True,
        }

        config["system_check"] = {
            "passed": True,
            "timestamp": self.get_user_input("安装时间", "", False),
            "python_version": env["python_version"],
            "project_path": env["project_path"],
            "system": "Windows" if sys.platform == "win32" else "Linux",
        }

        config["pypi"] = {
            "token_name": "RTGS",
            "api": "pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        }

        # QQ/微信设置
        config["qq_wechat"] = self.configure_qq_wechat_settings()

        config["online_ai_draw"] = {
            "api_url": "https://open.bigmodel.cn/api/paas/v4",
            "api_key": "your-zhipu-api-key",
            "default_model": "cogview-3",
            "default_size": "1:1",
            "provider": "zhipu",
            "timeout": 120,
        }

        config["local_ai_draw"] = {
            "service_url": "http://127.0.0.1:7860",
            "service_type": "sd_webui",
            "model": "sd1.5anything-v5.safetensors [7f96a1a9ca]",
            "width": 512,
            "height": 512,
            "steps": 20,
            "cfg_scale": 7.0,
            "sampler": "DPM++ 2M Karras",
            "timeout": 300,
        }

        config["active_communication"] = {
            "enabled": True,
            "context_aware": True,
            "generator": {
                "temperature": 0.8,
                "max_tokens": 150,
                "use_memory": True,
                "use_weather": True,
                "use_time_context": True,
            },
            "regulator": {
                "base_interval": 30,
                "min_interval": 10,
                "max_interval": 120,
                "adjustment_factor": 0.2,
                "response_window": 600,
            },
            "intelligent_mode": {
                "enabled": True,
                "min_opportunity_score": 0.4,
                "thinking_mode": True,
                "log_thought_process": True,
                "use_context_analyzer": True,
            },
        }

        return config

    def save_config(self, config: Dict[str, Any]):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"\n✅ 配置已保存到: {self.config_path.absolute()}")
        except Exception as e:
            print(f"\n❌ 保存配置失败: {e}")
            sys.exit(1)

    def show_summary(self, config: Dict[str, Any]):
        """显示配置摘要"""
        print("\n" + "=" * 60)
        print("配置摘要")
        print("=" * 60)
        print(f"AI 名称: {config['system']['ai_name']}")
        print(f"语音功能: {'启用' if config['system']['voice_enabled'] else '禁用'}")
        print(f"流式输出: {'启用' if config['system']['stream_mode'] else '禁用'}")
        print(f"API Key: {'已配置' if config['api']['api_key'] != 'your-api-key-here' else '未配置'}")
        print(f"TTS 引擎: {'GPT-SoVITS' if config['tts']['default_engine'] == 'gpt_sovits' else config['tts']['default_engine']}")
        print(f"知识图谱: {'启用' if config['grag']['enabled'] else '禁用'}")
        print(f"QQ 机器人: {'启用' if config['qq_wechat']['qq']['enabled'] else '禁用'}")
        print(f"微信机器人: {'启用' if config['qq_wechat']['wechat']['enabled'] else '禁用'}")
        print(f"实时语音: {'启用' if config['voice_realtime']['enabled'] else '禁用'}")
        print("=" * 60)

    def run(self):
        """运行安装向导"""
        try:
            from datetime import datetime

            self.print_banner()

            # 检查是否已存在配置
            if self.config_path.exists():
                print(f"\n[TIP] Existing config file found: {self.config_path}")
                choice = input("Overwrite existing configuration? [y/N]: ").strip().lower()
                if choice not in ['y', 'yes', '是']:
                    print("Skipping configuration wizard")
                    print("If you want to reconfigure later, run: python install_wizard.py")
                    return  # Return instead of exit

            # 生成配置
            config = self.generate_config()

            # 显示摘要
            self.show_summary(config)

            # 确认
            print("\n请确认上述配置是否正确")
            choice = input("保存配置? [Y/n]: ").strip().lower()
            if choice in ['n', 'no', '否']:
                print("取消安装")
                sys.exit(0)

            # 保存配置
            self.save_config(config)

            print("\n" + "🎉" * 20)
            print("安装配置完成!")
            print("🎉" * 20)
            print("\n下一步:")
            print("1. 确保已安装 Python 3.11+")
            print("2. 安装依赖: pip install -r requirements.txt")
            print("3. 如需 Neo4j,请先安装并启动 Neo4j 服务")
            print("4. 如需 GPT-SoVITS,请先安装并启动 GPT-SoVITS 服务")
            print("5. 启动程序: python main.py")
            print("\n或使用启动脚本:")
            if sys.platform == "win32":
                print("  start.bat - 启动程序")
                print("  start_all.bat - 启动所有服务")
            else:
                print("  ./start.sh - 启动程序")
            print("\n感谢使用 NagaAgent!")

        except KeyboardInterrupt:
            print("\n\n用户取消安装")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ 安装失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """主函数"""
    wizard = InstallWizard()
    wizard.run()


if __name__ == "__main__":
    main()
