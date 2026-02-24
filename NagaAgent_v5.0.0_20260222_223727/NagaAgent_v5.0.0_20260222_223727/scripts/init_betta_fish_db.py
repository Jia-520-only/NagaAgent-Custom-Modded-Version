"""
初始化 BettaFish 数据库表结构
"""

import asyncio
import sys
from pathlib import Path

# 添加 BettaFish 路径
betta_fish_path = Path(__file__).parent / "betta-fish-main"
mind_spider_path = betta_fish_path / "MindSpider" / "schema"

sys.path.insert(0, str(betta_fish_path))
sys.path.insert(0, str(mind_spider_path))

print("=" * 60)
print("初始化 BettaFish 数据库")
print("=" * 60)
print()

# 检查 .env 配置
env_file = betta_fish_path / ".env"
if not env_file.exists():
    print(f"❌ .env 文件不存在: {env_file}")
    print("   请先运行 setup_mysql.bat 配置数据库")
    sys.exit(1)

print("✅ 找到 .env 配置文件")
print()

# 导入初始化模块
try:
    from init_database import main as init_db_main
    print("✅ 导入数据库初始化模块")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("开始创建数据库表结构...")
print("-" * 60)

try:
    asyncio.run(init_db_main())
    print("-" * 60)
    print()
    print("✅ 数据库初始化完成！")
    print()
    print("创建的表包括：")
    print("  - daily_news (每日新闻)")
    print("  - daily_topics (每日话题)")
    print("  - crawling_tasks (爬虫任务)")
    print("  - 以及 MediaCrawler 的各平台数据表")
    print()
    print("下一步：运行 python test_db_connection.py 验证")
except Exception as e:
    print()
    print(f"❌ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
