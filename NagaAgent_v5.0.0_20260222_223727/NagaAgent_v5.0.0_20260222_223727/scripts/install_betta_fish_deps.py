"""
安装 BettaFish 所需依赖
"""

import subprocess
import sys

def install_package(package):
    """安装单个包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])
        print(f"  ✅ {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"  ❌ {package}")
        return False

def main():
    print("=" * 70)
    print("BettaFish 依赖安装")
    print("=" * 70)

    packages = [
        # 网络搜索
        "tavily-python>=0.3.0",

        # LLM
        "openai>=1.3.0",

        # 爬虫
        "playwright>=1.45.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",

        # 数据处理
        "pandas>=2.0.0",
        "numpy>=1.24.0",

        # 数据库
        "pymysql>=1.1.0",
        "aiomysql>=0.2.0",
        "aiopg>=1.4.0",
        "asyncpg>=0.29.0",
        "redis>=4.6.0",
        "SQLAlchemy>=2.0.0",

        # Web
        "flask>=2.3.0",
        "streamlit>=1.28.0",
        "fastapi>=0.110.0",
        "uvicorn>=0.29.0",

        # 工具
        "python-dotenv>=1.0.0",
        "tenacity>=8.2.0",
        "loguru>=0.7.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.2.0",
    ]

    print(f"\n需要安装 {len(packages)} 个包\n")

    success_count = 0
    for package in packages:
        if install_package(package):
            success_count += 1

    # 安装 Playwright 浏览器
    print("\n安装 Playwright 浏览器...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("  ✅ Playwright 浏览器")
    except:
        print("  ❌ Playwright 浏览器")

    print("\n" + "=" * 70)
    print(f"安装完成: {success_count}/{len(packages)} 个包")
    print("=" * 70)

    print("\n下一步:")
    print("  1. 配置 API: python configure_betta_fish.py")
    print("  2. 测试连接: python test_betta_fish_apis.py")

if __name__ == '__main__':
    main()
