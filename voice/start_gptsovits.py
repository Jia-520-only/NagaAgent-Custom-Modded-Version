#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPT-SoVITS 语音服务启动脚本
此脚本本身不启动GPT-SoVITS服务器，而是用于初始化集成实例。
"""
import sys
import os
import time

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(__file__))) # NagaAgent root

def initialize_integration():
    """初始化GPT-SoVITS集成"""
    print("🔍 正在初始化 GPT-SoVITS 语音集成...")
    try:
        from voice.gpt_sovits_integration import get_gptsovits_integration, GPTSoVITSIntegration
        
        # 获取集成实例（触发初始化）
        integration: GPTSoVITSIntegration = get_gptsovits_integration()
        
        print("✅ GPT-SoVITS语音集成初始化完成")
        
        # 可选：设置参考文本 (如果需要)
        # integration.set_reference_text("你好，我是NagaAgent。", "")
        
        return integration

    except Exception as e:
        print(f"❌ GPT-SoVITS集成初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    integration_instance = initialize_integration()
    if integration_instance:
        print("\n--- GPT-SoVITS 集成已就绪 ---")
        print("现在可以在其他地方调用 `get_gptsovits_integration()` 来获取实例了。")
        print("请确保 GPT-SoVITS 服务在 http://127.0.0.1:9880 运行。")
        # 这里可以加入一个简单的交互测试，但主要是让模块准备好
        input("\n按 Enter 键退出...")