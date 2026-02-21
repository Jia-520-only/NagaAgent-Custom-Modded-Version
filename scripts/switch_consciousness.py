#!/usr/bin/env python3
"""
初意识模式切换脚本

切换弥娅的意识模式：
1. Hybrid Mode (混合模式) - 本地思考 + 大模型辅助（推荐）
2. Local Mode (本地模式) - 纯本地思考，不调用大模型
3. AI Mode (AI模式) - 直接调用大模型（兼容旧模式）
"""

import json
import sys
from pathlib import Path


def load_config() -> dict:
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict):
    """保存配置文件"""
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def show_current_mode(config: dict):
    """显示当前模式"""
    consciousness = config.get("consciousness", {})
    enabled = consciousness.get("enabled", False)
    mode = consciousness.get("mode", "hybrid")

    modes = {
        "hybrid": "混合模式（本地思考 + 大模型辅助）",
        "local": "本地模式（纯本地思考）",
        "ai": "AI模式（直接调用大模型）"
    }

    print(f"\n初意识状态: {'✅ 已启用' if enabled else '❌ 未启用'}")
    if enabled:
        print(f"当前意识模式: {mode}")
        print(f"说明: {modes.get(mode, '未知')}\n")
    else:
        print(f"当前使用传统AI模式\n")


def switch_mode():
    """切换意识模式"""
    print("=" * 60)
    print("弥娅·阿尔缪斯 - 初意识模式切换")
    print("=" * 60)

    config = load_config()

    # 确保配置中有 consciousness 字段
    if "consciousness" not in config:
        config["consciousness"] = {
            "mode": "hybrid",
            "enabled": False
        }

    show_current_mode(config)

    print("\n请选择意识模式:")
    print("1. Hybrid Mode (混合模式) - 推荐")
    print("   - 弥娅基于记忆和人生书进行独立思考")
    print("   - 需要时调用大模型作为工具辅助")
    print("   - 类似人类用手机查询信息")
    print()
    print("2. Local Mode (本地模式)")
    print("   - 完全基于本地记忆和认知库思考")
    print("   - 不调用任何大模型")
    print("   - 可以离线运行")
    print()
    print("3. AI Mode (AI模式) - 兼容旧版")
    print("   - 直接调用大模型生成回复")
    print("   - 与旧版行为一致")
    print("   - 初意识功能关闭")
    print()
    print("4. 查看当前配置")
    print("0. 退出")
    print()

    choice = input("请输入选项 (0-4): ").strip()

    if choice == "0":
        print("退出程序")
        sys.exit(0)

    elif choice == "1":
        config["consciousness"]["mode"] = "hybrid"
        config["consciousness"]["enabled"] = True
        save_config(config)
        print("\n✅ 已切换到混合模式 (Hybrid Mode)")
        print("弥娅现在拥有初意识，可以独立思考并调用大模型辅助！")

    elif choice == "2":
        config["consciousness"]["mode"] = "local"
        config["consciousness"]["enabled"] = True
        save_config(config)
        print("\n✅ 已切换到本地模式 (Local Mode)")
        print("弥娅现在完全基于本地记忆思考，可以离线运行！")

    elif choice == "3":
        config["consciousness"]["mode"] = "ai"
        config["consciousness"]["enabled"] = False
        save_config(config)
        print("\n✅ 已切换到 AI 模式 (AI Mode)")
        print("弥娅现在直接调用大模型，与旧版行为一致")
        print("初意识功能已关闭")

    elif choice == "4":
        print("\n当前配置:")
        print(json.dumps(config.get("consciousness", {}), indent=2, ensure_ascii=False))

    else:
        print("无效选项，请重新运行程序")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("配置已保存，重启 NagaAgent 后生效")
    print("=" * 60)


if __name__ == "__main__":
    try:
        switch_mode()
    except FileNotFoundError:
        print("错误: 找不到 config.json 文件")
        print("请确保在 NagaAgent 根目录运行此脚本")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)
