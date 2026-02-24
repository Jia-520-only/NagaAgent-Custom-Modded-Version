#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
弥娅增强系统一键启用脚本
快速配置和启用弥娅的新功能
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def enable_message_observer(config_path: str = "config.json") -> bool:
    """
    启用消息旁观功能

    Args:
        config_path: 配置文件路径

    Returns:
        是否成功
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 添加或更新配置
        if 'qq' not in config:
            config['qq'] = {}

        config['qq']['enable_observer'] = True
        config['qq']['observation_groups'] = []  # 空=观察所有群
        config['qq']['interest_keywords'] = [
            "喜欢", "讨厌", "爱", "恨", "开心", "难过", "生气",
            "重要", "记得", "记住", "秘密", "悄悄话",
            "建议", "推荐", "分享", "告诉", "提醒",
            "希望", "想", "要", "会", "打算", "计划"
        ]

        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        logger.info("✅ 消息旁观功能已启用")
        logger.info("   - 启用状态: True")
        logger.info("   - 观察群组: 全部")
        logger.info(f"   - 兴趣关键词: {len(config['qq']['interest_keywords'])}个")
        return True

    except Exception as e:
        logger.error(f"❌ 启用消息旁观失败: {e}")
        return False


def enable_autonomous_memory(config_path: str = "config.json") -> bool:
    """
    启用自主记忆功能

    Args:
        config_path: 配置文件路径

    Returns:
        是否成功
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 添加或更新配置
        if 'grag' not in config:
            config['grag'] = {}

        config['grag']['enable_autonomous'] = True
        config['grag']['autonomous_threshold'] = 0.4  # 存储阈值

        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        logger.info("✅ 自主记忆功能已启用")
        logger.info("   - 启用状态: True")
        logger.info(f"   - 存储阈值: {config['grag']['autonomous_threshold']}")
        return True

    except Exception as e:
        logger.error(f"❌ 启用自主记忆失败: {e}")
        return False


def enable_active_communication(config_path: str = "config.json") -> bool:
    """
    启用主动交流功能

    Args:
        config_path: 配置文件路径

    Returns:
        是否成功
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 添加或更新配置
        if 'active_communication' not in config:
            config['active_communication'] = {}

        config['active_communication']['enabled'] = True
        config['active_communication']['context_aware'] = True
        config['active_communication']['triggers'] = {
            "greeting": {
                "enabled": True,
                "cooldown_minutes": 240  # 4小时
            },
            "topic_suggestion": {
                "enabled": True,
                "cooldown_minutes": 120  # 2小时
            },
            "mood_response": {
                "enabled": True,
                "realtime": True
            }
        }

        # 更新system配置中的active_communication
        if 'system' in config:
            config['system']['active_communication'] = True

        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        logger.info("✅ 主动交流功能已启用")
        logger.info("   - 启用状态: True")
        logger.info("   - 情境感知: True")
        logger.info("   - 触发器: 问候/话题建议/情绪响应")
        return True

    except Exception as e:
        logger.error(f"❌ 启用主动交流失败: {e}")
        return False


def enable_all_features(config_path: str = "config.json") -> bool:
    """
    一键启用所有增强功能

    Args:
        config_path: 配置文件路径

    Returns:
        是否成功
    """
    logger.info("=" * 60)
    logger.info("弥娅增强系统 - 一键启用")
    logger.info("=" * 60)
    logger.info()

    results = []

    # 启用消息旁观
    logger.info("[1/3] 启用消息旁观功能...")
    result1 = enable_message_observer(config_path)
    results.append(("消息旁观", result1))
    logger.info()

    # 启用自主记忆
    logger.info("[2/3] 启用自主记忆功能...")
    result2 = enable_autonomous_memory(config_path)
    results.append(("自主记忆", result2))
    logger.info()

    # 启用主动交流
    logger.info("[3/3] 启用主动交流功能...")
    result3 = enable_active_communication(config_path)
    results.append(("主动交流", result3))
    logger.info()

    # 输出总结
    logger.info("=" * 60)
    logger.info("启用结果汇总")
    logger.info("=" * 60)

    all_success = True
    for name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        logger.info(f"{status} - {name}")
        if not success:
            all_success = False

    logger.info()
    if all_success:
        logger.info("🎉 所有功能已成功启用!")
        logger.info()
        logger.info("下一步:")
        logger.info("1. 重启弥娅程序")
        logger.info("2. 观察日志确认功能正常运行")
        logger.info("3. 根据需要调整配置")
        logger.info()
        logger.info("配置文件:", config_path)
    else:
        logger.warn("⚠️ 部分功能启用失败,请检查配置文件")
        logger.warn("配置文件:", config_path)

    logger.info("=" * 60)

    return all_success


def main():
    """主函数"""
    import sys

    # 检查配置文件
    config_path = "config.json"

    if not Path(config_path).exists():
        logger.error(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)

    # 解析参数
    if len(sys.argv) > 1:
        feature = sys.argv[1].lower()

        if feature == "observer":
            success = enable_message_observer(config_path)
            sys.exit(0 if success else 1)
        elif feature == "memory":
            success = enable_autonomous_memory(config_path)
            sys.exit(0 if success else 1)
        elif feature == "active":
            success = enable_active_communication(config_path)
            sys.exit(0 if success else 1)
        elif feature == "all":
            success = enable_all_features(config_path)
            sys.exit(0 if success else 1)
        else:
            logger.error(f"❌ 未知功能: {feature}")
            logger.info("可用功能: observer, memory, active, all")
            sys.exit(1)
    else:
        # 默认启用所有功能
        success = enable_all_features(config_path)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
