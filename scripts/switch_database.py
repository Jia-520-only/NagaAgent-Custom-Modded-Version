"""
BettaFish 数据库切换工具
支持切换本地和云数据库
"""

import sys
from pathlib import Path

def switch_to_local():
    """切换到本地数据库"""
    print("\n=== 切换到本地数据库 ===")
    print("配置信息:")
    print("  主机: localhost:9902")
    print("  用户: root")
    print("  密码: Aa316316")
    print("  数据库: mindspider")

    # 更新 .env
    env_file = Path(__file__).parent / "betta-fish-main" / ".env"
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        updated = []
        for line in lines:
            if line.startswith('DB_PORT='):
                updated.append('DB_PORT=9902\n')
            elif line.startswith('DB_PASSWORD='):
                updated.append('DB_PASSWORD=Aa316316\n')
            elif line.startswith('DB_HOST='):
                updated.append('DB_HOST=localhost\n')
            elif line.startswith('DB_USER='):
                updated.append('DB_USER=root\n')
            else:
                updated.append(line)

        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(updated)
        print("✅ .env 文件已更新")

    # 更新 .env.local
    env_local = Path(__file__).parent / "betta-fish-main" / ".env.local"
    if env_local.exists():
        with open(env_local, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        updated = []
        for line in lines:
            if line.startswith('DB_MODE='):
                updated.append('DB_MODE=local\n')
            else:
                updated.append(line)

        with open(env_local, 'w', encoding='utf-8') as f:
            f.writelines(updated)
        print("✅ .env.local 已设置为 local 模式")

    print("\n请重启 NagaAgent 使配置生效")

def switch_to_cloud():
    """切换到云数据库"""
    print("\n=== 切换到云数据库 ===")

    # 读取云数据库配置
    env_local = Path(__file__).parent / "betta-fish-main" / ".env.local"
    if not env_local.exists():
        print("❌ .env.local 文件不存在")
        return

    cloud_config = {}
    with open(env_local, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('DB_HOST_CLOUD='):
                cloud_config['DB_HOST'] = line.split('=', 1)[1].strip()
            elif line.startswith('DB_PORT_CLOUD='):
                cloud_config['DB_PORT'] = line.split('=', 1)[1].strip()
            elif line.startswith('DB_USER_CLOUD='):
                cloud_config['DB_USER'] = line.split('=', 1)[1].strip()
            elif line.startswith('DB_PASSWORD_CLOUD='):
                cloud_config['DB_PASSWORD'] = line.split('=', 1)[1].strip()

    if not all(k in cloud_config for k in ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD']):
        print("⚠️  云数据库配置不完整，请在 .env.local 中填写:")
        print("   DB_HOST_CLOUD=")
        print("   DB_PORT_CLOUD=")
        print("   DB_USER_CLOUD=")
        print("   DB_PASSWORD_CLOUD=")
        return

    print("配置信息:")
    print(f"  主机: {cloud_config['DB_HOST']}:{cloud_config['DB_PORT']}")
    print(f"  用户: {cloud_config['DB_USER']}")
    print(f"  数据库: mindspider")

    # 更新 .env
    env_file = Path(__file__).parent / "betta-fish-main" / ".env"
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        updated = []
        for line in lines:
            if line.startswith('DB_PORT='):
                updated.append(f"DB_PORT={cloud_config['DB_PORT']}\n")
            elif line.startswith('DB_PASSWORD='):
                updated.append(f"DB_PASSWORD={cloud_config['DB_PASSWORD']}\n")
            elif line.startswith('DB_HOST='):
                updated.append(f"DB_HOST={cloud_config['DB_HOST']}\n")
            elif line.startswith('DB_USER='):
                updated.append(f"DB_USER={cloud_config['DB_USER']}\n")
            else:
                updated.append(line)

        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(updated)
        print("✅ .env 文件已更新")

    # 更新 .env.local
    with open(env_local, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    updated = []
    for line in lines:
        if line.startswith('DB_MODE='):
            updated.append('DB_MODE=cloud\n')
        else:
            updated.append(line)

    with open(env_local, 'w', encoding='utf-8') as f:
        f.writelines(updated)
    print("✅ .env.local 已设置为 cloud 模式")

    print("\n请重启 NagaAgent 使配置生效")

def main():
    print("=" * 60)
    print("BettaFish 数据库切换工具")
    print("=" * 60)

    # 显示当前配置
    env_local = Path(__file__).parent / "betta-fish-main" / ".env.local"
    if env_local.exists():
        with open(env_local, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('DB_MODE='):
                    current_mode = line.split('=', 1)[1].strip()
                    print(f"\n当前模式: {current_mode}")
                    break

    print("\n请选择:")
    print("  1. 本地数据库 (Docker, 端口 9902)")
    print("  2. 云数据库 (BettaFish 官方)")
    print("\n命令行参数:")
    print("  python switch_database.py --local")
    print("  python switch_database.py --cloud")

    if len(sys.argv) > 1:
        if sys.argv[1] == '--local':
            switch_to_local()
        elif sys.argv[1] == '--cloud':
            switch_to_cloud()
        return

    choice = input("\n请输入选项 (1 或 2): ").strip()
    if choice == '1':
        switch_to_local()
    elif choice == '2':
        switch_to_cloud()
    else:
        print("无效选项")

if __name__ == '__main__':
    main()
