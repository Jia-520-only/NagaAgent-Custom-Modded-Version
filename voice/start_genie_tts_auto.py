#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genie-TTS 自动启动器 - 由 main.py 调用
根据配置自动启动 Genie-TTS 服务器
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# 设置控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def start_genie_tts():
    """启动 Genie-TTS 服务器"""
    project_root = Path(__file__).parent.parent
    genie_dir = project_root / "Genie-TTS"

    # 添加 Genie-TTS 路径
    genie_src = str(genie_dir / "src")
    if genie_src not in sys.path:
        sys.path.insert(0, genie_src)

    try:
        print("   📦 加载 Genie-TTS 模块...")
        import genie_tts as genie
        print("   ✅ Genie-TTS 模块加载成功")

        # 服务器配置
        host = "127.0.0.1"
        port = 8000

        print(f"   🚀 Genie-TTS 服务器: 正在启动 on {host}:{port}...")
        print(f"      模式: ONNX 推理引擎")
        print(f"      API: http://{host}:{port}")

        # 启动服务器
        genie.start_server(host=host, port=port, workers=1)

    except ImportError as e:
        print(f"   ❌ Genie-TTS 依赖缺失: {e}")
        print("   💡 请运行: python install_genie_tts.py 安装依赖")
        return False
    except Exception as e:
        print(f"   ❌ Genie-TTS 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    start_genie_tts()
