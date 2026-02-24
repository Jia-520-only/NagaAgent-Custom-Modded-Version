"""
BettaFish 数据库模式切换工具
支持本地数据库和云数据库之间的快速切换
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录
project_root = Path(__file__).parent
env_file = project_root / ".env"
env_local_file = project_root / ".env.local"

print("=" * 60)
print("BettaFish 数据库模式切换工具")
print("=" * 60)
print()

# 检查文件是否存在
if not env_local_file.exists():
    print(f"⚠️  警告: {env_local_file} 不存在")
    print("   请先配置 .env.local 文件")
    sys.exit(1)

# 加载本地配置
load_dotenv(env_local_file)

# 获取当前模式
current_mode = os.getenv("DB_MODE", "local")
print(f"当前数据库模式: {current_mode}")
print()

# 显示配置状态
print("配置状态:")
print("-" * 60)

# 本地数据库配置
local_configured = all([
    os.getenv("DB_HOST_LOCAL"),
    os.getenv("DB_USER_LOCAL"),
    os.getenv("DB_NAME_LOCAL")
])
print(f"本地数据库: {'✅ 已配置' if local_configured else '⚠️  未配置'}")
if local_configured:
    print(f"  主机: {os.getenv('DB_HOST_LOCAL')}")
    print(f"  数据库: {os.getenv('DB_NAME_LOCAL')}")

# 云数据库配置
cloud_configured = all([
    os.getenv("DB_HOST_CLOUD"),
    os.getenv("DB_USER_CLOUD"),
    os.getenv("DB_NAME_CLOUD")
])
print(f"云数据库:   {'✅ 已配置' if cloud_configured else '⚠️  未配置'}")
if cloud_configured:
    print(f"  主机: {os.getenv('DB_HOST_CLOUD')}")
    print(f"  数据库: {os.getenv('DB_NAME_CLOUD')}")

print("-" * 60)
print()

# 切换功能
if len(sys.argv) > 1:
    command = sys.argv[1].lower()

    if command == "local":
        print("切换到本地数据库模式...")
        _switch_to_local()
    elif command == "cloud":
        print("切换到云数据库模式...")
        _switch_to_cloud()
    elif command == "status":
        print("当前配置状态:")
        print(f"  DB_MODE = {current_mode}")
        sys.exit(0)
    else:
        print(f"未知命令: {command}")
        print_help()
        sys.exit(1)
else:
    print_help()
    sys.exit(0)


def _switch_to_local():
    """切换到本地数据库"""
    if not local_configured:
        print("❌ 本地数据库未配置，请先设置 .env.local")
        sys.exit(1)

    # 读取 .env 文件
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        lines = []

    # 更新配置
    updated = _update_env_lines(lines, {
        'DB_HOST': os.getenv('DB_HOST_LOCAL'),
        'DB_PORT': os.getenv('DB_PORT_LOCAL'),
        'DB_USER': os.getenv('DB_USER_LOCAL'),
        'DB_PASSWORD': os.getenv('DB_PASSWORD_LOCAL'),
        'DB_NAME': os.getenv('DB_NAME_LOCAL'),
        'DB_CHARSET': os.getenv('DB_CHARSET_LOCAL'),
        'DB_DIALECT': os.getenv('DB_DIALECT_LOCAL'),
    })

    # 写回文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(updated)

    print("✅ 已切换到本地数据库")
    print(f"  主机: {os.getenv('DB_HOST_LOCAL')}")
    print(f"  数据库: {os.getenv('DB_NAME_LOCAL')}")
    print()
    print("下一步: 运行 python test_db_connection.py 验证连接")


def _switch_to_cloud():
    """切换到云数据库"""
    if not cloud_configured:
        print("❌ 云数据库未配置，请先设置 .env.local")
        print("   或者联系 670939375@qq.com 申请官方云数据库")
        sys.exit(1)

    # 读取 .env 文件
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        lines = []

    # 更新配置
    updated = _update_env_lines(lines, {
        'DB_HOST': os.getenv('DB_HOST_CLOUD'),
        'DB_PORT': os.getenv('DB_PORT_CLOUD'),
        'DB_USER': os.getenv('DB_USER_CLOUD'),
        'DB_PASSWORD': os.getenv('DB_PASSWORD_CLOUD'),
        'DB_NAME': os.getenv('DB_NAME_CLOUD'),
        'DB_CHARSET': os.getenv('DB_CHARSET_CLOUD'),
        'DB_DIALECT': os.getenv('DB_DIALECT_CLOUD'),
    })

    # 写回文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(updated)

    print("✅ 已切换到云数据库")
    print(f"  主机: {os.getenv('DB_HOST_CLOUD')}")
    print(f"  数据库: {os.getenv('DB_NAME_CLOUD')}")
    print()
    print("下一步: 运行 python test_db_connection.py 验证连接")


def _update_env_lines(lines, config):
    """更新 .env 文件中的配置行"""
    result = []
    updated_keys = set()

    for line in lines:
        stripped = line.strip()
        if '=' in stripped and not stripped.startswith('#'):
            key = stripped.split('=')[0]
            if key in config:
                result.append(f"{key}={config[key]}\n")
                updated_keys.add(key)
            else:
                result.append(line)
        else:
            result.append(line)

    # 添加缺失的配置
    for key, value in config.items():
        if key not in updated_keys:
            result.append(f"{key}={value}\n")

    return result


def print_help():
    """打印帮助信息"""
    print("用法:")
    print()
    print("  python config_db_mode.py local   - 切换到本地数据库")
    print("  python config_db_mode.py cloud  - 切换到云数据库")
    print("  python config_db_mode.py status - 查看当前状态")
    print()
    print("示例:")
    print()
    print("  # 切换到本地数据库")
    print("  python config_db_mode.py local")
    print()
    print("  # 切换到云数据库")
    print("  python config_db_mode.py cloud")
    print()
    print("  # 查看状态")
    print("  python config_db_mode.py status")
