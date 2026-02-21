#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多引擎TTS部署脚本 - 部署GPT-SoVITS和VITS
"""
import os
import sys
import json
import subprocess
import shutil
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    print("检查Python版本...")
    if sys.version_info < (3, 10) or sys.version_info >= (3, 13):
        print("❌ Python版本不支持，需要3.10-3.12版本")
        return False
    print(f"✅ Python版本: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def check_cuda():
    """检查CUDA是否可用"""
    print("检查CUDA环境...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA可用，版本: {torch.version.cuda}")
            return True
        else:
            print("⚠️ CUDA不可用，将使用CPU模式")
            return False
    except ImportError:
        print("⚠️ PyTorch未安装，无法检查CUDA")
        return None


def install_gpt_sovits():
    """部署GPT-SoVITS"""
    print("\n" + "="*50)
    print("部署GPT-SoVITS...")
    print("="*50)

    gpt_sovits_dir = Path("GPT_SoVITS")

    # 如果目录不存在，提示用户
    if not gpt_sovits_dir.exists():
        print("⚠️ GPT_SoVITS目录不存在")
        print("请手动下载GPT-SoVITS项目:")
        print("git clone https://github.com/RVC-Boss/GPT-SoVITS.git")
        return False

    print(f"✅ GPT_SoVITS目录存在: {gpt_sovits_dir}")

    # 检查requirements.txt
    requirements_file = gpt_sovits_dir / "requirements.txt"
    if requirements_file.exists():
        print(f"✅ 发现requirements.txt: {requirements_file}")
        print("请手动安装依赖:")
        print(f"  cd {gpt_sovits_dir}")
        print("  pip install -r requirements.txt")
    else:
        print("⚠️ requirements.txt不存在，请手动安装依赖")

    # 检查模型文件
    pretrained_dir = gpt_sovits_dir / "pretrained_models"
    if pretrained_dir.exists():
        print(f"✅ 预训练模型目录存在: {pretrained_dir}")
    else:
        print("⚠️ 预训练模型目录不存在，请下载预训练模型")

    return True


def install_vits():
    """部署VITS"""
    print("\n" + "="*50)
    print("部署VITS...")
    print("="*50)

    vits_dir = Path("VITS")

    # 如果目录不存在，提示用户
    if not vits_dir.exists():
        print("⚠️ VITS目录不存在")
        print("请手动下载VITS项目:")
        print("git clone https://github.com/jaywalnut310/vits.git")
        return False

    print(f"✅ VITS目录存在: {vits_dir}")

    # 检查requirements.txt
    requirements_file = vits_dir / "requirements.txt"
    if requirements_file.exists():
        print(f"✅ 发现requirements.txt: {requirements_file}")
        print("请手动安装依赖:")
        print(f"  cd {vits_dir}")
        print("  pip install -r requirements.txt")
    else:
        print("⚠️ requirements.txt不存在，请手动安装依赖")

    # 检查模型文件
    checkpoint_dir = vits_dir / "checkpoint"
    if checkpoint_dir.exists():
        print(f"✅ 模型检查点目录存在: {checkpoint_dir}")
    else:
        print("⚠️ 模型检查点目录不存在，请训练或下载预训练模型")

    return True


def update_config():
    """更新config.json配置"""
    print("\n" + "="*50)
    print("更新配置文件...")
    print("="*50)

    config_path = Path("config.json")
    if not config_path.exists():
        print("❌ config.json不存在")
        return False

    # 读取现有配置
    with open(config_path, 'r', encoding='utf-8') as f:
        try:
            config_data = json.load(f)
        except json.JSONDecodeError:
            # 尝试使用json5
            from nagaagent_core.vendors import json5
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json5.load(f)

    # 添加多引擎TTS配置
    if "tts" not in config_data:
        config_data["tts"] = {}

    # 更新TTS配置
    config_data["tts"].update({
        "default_engine": "edge_tts",
        "gpt_sovits_enabled": True,
        "gpt_sovits_url": "http://127.0.0.1:9880",
        "gpt_sovits_speed": 1.0,
        "gpt_sovits_top_k": 15,
        "gpt_sovits_top_p": 1.0,
        "gpt_sovits_temperature": 1.0,
        "gpt_sovits_ref_free": False,
        "vits_enabled": True,
        "vits_url": "http://127.0.0.1:7860",
        "vits_voice_id": 0,
        "vits_noise_scale": 0.667,
        "vits_noise_scale_w": 0.8,
        "vits_length_scale": 1.0
    })

    # 保存配置
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

    print("✅ 配置文件更新完成")
    return True


def create_start_scripts():
    """创建启动脚本"""
    print("\n" + "="*50)
    print("创建启动脚本...")
    print("="*50)

    # GPT-SoVITS启动脚本
    gpt_sovits_script = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
GPT-SoVITS服务启动脚本
\"\"\"
import subprocess
import sys
from pathlib import Path

gpt_sovits_dir = Path("GPT_SoVITS")
api_script = gpt_sovits_dir / "api_v2.py"

if not api_script.exists():
    print(f"❌ API脚本不存在: {api_script}")
    sys.exit(1)

print("🚀 启动GPT-SoVITS服务...")

subprocess.run([
    sys.executable,
    str(api_script),
    "-a", "127.0.0.1",
    "-p", "9880"
], check=True)
"""

    with open("start_gpt_sovits.py", "w", encoding="utf-8") as f:
        f.write(gpt_sovits_script)
    print("✅ 创建GPT-SoVITS启动脚本: start_gpt_sovits.py")

    # VITS启动脚本
    vits_script = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
VITS服务启动脚本
\"\"\"
import subprocess
import sys
from pathlib import Path

vits_dir = Path("VITS")
api_script = vits_dir / "inference_api.py"

if not api_script.exists():
    # 尝试其他可能的API脚本
    possible_scripts = [
        "serve.py",
        "api.py",
        "server.py"
    ]
    for script_name in possible_scripts:
        api_script = vits_dir / script_name
        if api_script.exists():
            break

if not api_script.exists():
    print(f"❌ VITS API脚本不存在")
    print("请确认VITS目录中有以下任一脚本:")
    print("  - inference_api.py")
    print("  - serve.py")
    print("  - api.py")
    print("  - server.py")
    sys.exit(1)

print("🚀 启动VITS服务...")

subprocess.run([
    sys.executable,
    str(api_script),
    "--host", "127.0.0.1",
    "--port", "7860"
], check=True)
"""

    with open("start_vits.py", "w", encoding="utf-8") as f:
        f.write(vits_script)
    print("✅ 创建VITS启动脚本: start_vits.py")

    # 多引擎测试脚本
    test_script = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
多引擎TTS测试脚本
\"\"\"
import time
from voice.multi_tts_integration import get_multi_tts_engine, TTSEngine

def test_all_engines():
    \"\"\"测试所有TTS引擎\"\"\"
    print("="*50)
    print("测试多引擎TTS系统")
    print("="*50)

    engine = get_multi_tts_engine()
    test_text = "你好，这是一个测试。"

    # 测试Edge-TTS
    print("\n测试Edge-TTS...")
    engine.set_engine(TTSEngine.EDGE_TTS)
    engine.receive_final_text(test_text)
    time.sleep(5)

    # 测试GPT-SoVITS
    print("\n测试GPT-SoVITS...")
    engine.set_engine(TTSEngine.GPT_SOVITS)
    engine.receive_final_text(test_text)
    time.sleep(5)

    # 测试VITS
    print("\n测试VITS...")
    engine.set_engine(TTSEngine.VITS)
    engine.receive_final_text(test_text)
    time.sleep(5)

    print("\n测试完成！")

if __name__ == "__main__":
    test_all_engines()
"""

    with open("test_multi_tts.py", "w", encoding="utf-8") as f:
        f.write(test_script)
    print("✅ 创建测试脚本: test_multi_tts.py")

    return True


def print_guide():
    """打印使用指南"""
    print("\n" + "="*50)
    print("🎉 部署完成！")
    print("="*50)
    print("\n📖 使用指南:")
    print("\n1. 启动GPT-SoVITS服务:")
    print("   python start_gpt_sovits.py")
    print("\n2. 启动VITS服务:")
    print("   python start_vits.py")
    print("\n3. 测试多引擎TTS:")
    print("   python test_multi_tts.py")
    print("\n4. 在代码中使用:")
    print("""
    from voice.multi_tts_integration import get_multi_tts_engine, TTSEngine

    # 获取引擎实例
    engine = get_multi_tts_engine()

    # 切换到GPT-SoVITS
    engine.set_engine(TTSEngine.GPT_SOVITS)
    engine.receive_final_text("你好，世界！")

    # 切换到VITS
    engine.set_engine(TTSEngine.VITS)
    engine.receive_final_text("你好，世界！")

    # 切换到Edge-TTS
    engine.set_engine(TTSEngine.EDGE_TTS)
    engine.receive_final_text("你好，世界！")
    """)
    print("\n📋 配置文件 (config.json):")
    print("  tts.default_engine: 默认引擎 (edge_tts, gpt_sovits, vits)")
    print("  tts.gpt_sovits_enabled: 是否启用GPT-SoVITS")
    print("  tts.vits_enabled: 是否启用VITS")
    print("\n💡 提示:")
    print("  - 确保已下载相应的模型文件")
    print("  - 确保端口9880 (GPT-SoVITS) 和7860 (VITS) 未被占用")
    print("  - 可以通过config.json修改默认引擎和参数")
    print("="*50)


def main():
    """主函数"""
    print("🚀 多引擎TTS部署脚本")
    print("="*50)

    # 检查Python版本
    if not check_python_version():
        return False

    # 检查CUDA
    cuda_available = check_cuda()

    # 部署GPT-SoVITS
    install_gpt_sovits()

    # 部署VITS
    install_vits()

    # 更新配置
    update_config()

    # 创建启动脚本
    create_start_scripts()

    # 打印使用指南
    print_guide()

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
