"""
BettaFish 完整配置助手
帮助用户配置网络搜索 API 和独立 LLM
"""

import sys
from pathlib import Path

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_section(title):
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}")

def configure_tavily():
    """配置 Tavily 搜索"""
    print_section("步骤 1: 配置 Tavily 网络搜索")

    print("\n📝 Tavily 注册步骤:")
    print("  1. 访问: https://tavily.com/")
    print("  2. 注册账号（免费 1,000 次/月）")
    print("  3. 获取 API Key (格式: tvly-...)")

    api_key = input("\n请输入 Tavily API Key: ").strip()
    if api_key:
        update_env("TAVILY_API_KEY", api_key)
        print("✅ Tavily API Key 已配置")
    else:
        print("⏭️  跳过 Tavily 配置")

def configure_bocha():
    """配置 Bocha 搜索"""
    print_section("步骤 2: 配置 Bocha 网络搜索（中文优化）")

    print("\n📝 Bocha 注册步骤:")
    print("  1. 访问: https://open.bochaai.com/")
    print("  2. 注册账号")
    print("  3. 获取 API Key")

    use_bocha = input("\n是否配置 Bocha (y/n, 默认 n): ").strip().lower()
    if use_bocha == 'y':
        api_key = input("请输入 Bocha API Key: ").strip()
        if api_key:
            update_env("BOCHA_WEB_SEARCH_API_KEY", api_key)
            update_env("BOCHA_BASE_URL", "https://api.bochaai.com")
            print("✅ Bocha API Key 已配置")

def configure_llms():
    """配置 LLM APIs"""
    print_section("步骤 3: 配置 LLM APIs")

    llm_configs = [
        {
            "name": "InsightEngine (Kimi)",
            "api_key": "INSIGHT_ENGINE_API_KEY",
            "base_url": "INSIGHT_ENGINE_BASE_URL",
            "model": "INSIGHT_ENGINE_MODEL_NAME",
            "url": "https://platform.moonshot.cn/",
            "default_base": "https://api.moonshot.cn/v1",
            "default_model": "kimi-k2-0711-preview"
        },
        {
            "name": "MediaEngine (Gemini)",
            "api_key": "MEDIA_ENGINE_API_KEY",
            "base_url": "MEDIA_ENGINE_BASE_URL",
            "model": "MEDIA_ENGINE_MODEL_NAME",
            "url": "https://www.chataiapi.com/",
            "default_base": "https://api.chataiapi.com/v1",
            "default_model": "gemini-2.5-pro"
        },
        {
            "name": "QueryEngine (DeepSeek)",
            "api_key": "QUERY_ENGINE_API_KEY",
            "base_url": "QUERY_ENGINE_BASE_URL",
            "model": "QUERY_ENGINE_MODEL_NAME",
            "url": "https://www.deepseek.com/",
            "default_base": "https://api.deepseek.com/v1",
            "default_model": "deepseek-reasoner"
        },
        {
            "name": "ReportEngine (Gemini)",
            "api_key": "REPORT_ENGINE_API_KEY",
            "base_url": "REPORT_ENGINE_BASE_URL",
            "model": "REPORT_ENGINE_MODEL_NAME",
            "url": "https://www.chataiapi.com/",
            "default_base": "https://api.chataiapi.com/v1",
            "default_model": "gemini-2.5-pro"
        },
        {
            "name": "ForumEngine (Qwen3)",
            "api_key": "FORUM_HOST_API_KEY",
            "base_url": "FORUM_HOST_BASE_URL",
            "model": "FORUM_HOST_MODEL_NAME",
            "url": "https://cloud.siliconflow.cn/",
            "default_base": "https://api.siliconflow.cn/v1",
            "default_model": "Qwen/Qwen3-235B-A22B-Instruct-2507"
        },
        {
            "name": "KeywordOptimizer (DeepSeek)",
            "api_key": "KEYWORD_OPTIMIZER_API_KEY",
            "base_url": "KEYWORD_OPTIMIZER_BASE_URL",
            "model": "KEYWORD_OPTIMIZER_MODEL_NAME",
            "url": "https://www.deepseek.com/",
            "default_base": "https://api.deepseek.com/v1",
            "default_model": "deepseek-chat"
        }
    ]

    print("\n需要配置 6 个 LLM API:")
    print("  💡 提示: 如果没有 API Key，可以输入 'demo' 跳过")
    print()

    for i, config in enumerate(llm_configs, 1):
        print(f"\n[{i}/6] {config['name']}")
        print(f"    注册地址: {config['url']}")

        api_key = input(f"    请输入 API Key: ").strip()

        if api_key and api_key.lower() != 'demo':
            update_env(config['api_key'], api_key)
            use_custom_base = input(f"    使用默认 Base URL ({config['default_base']})? (Y/n): ").strip().lower()
            if use_custom_base == 'n':
                custom_base = input("    请输入自定义 Base URL: ").strip()
                if custom_base:
                    update_env(config['base_url'], custom_base)
            else:
                update_env(config['base_url'], config['default_base'])

            use_custom_model = input(f"    使用默认模型 ({config['default_model']})? (Y/n): ").strip().lower()
            if use_custom_model == 'n':
                custom_model = input("    请输入自定义模型名称: ").strip()
                if custom_model:
                    update_env(config['model'], custom_model)
            else:
                update_env(config['model'], config['default_model'])

            print(f"    ✅ 已配置")
        else:
            print(f"    ⏭️  跳过")

def update_env(key, value):
    """更新 .env 文件"""
    env_file = Path(__file__).parent / "betta-fish-main" / ".env"
    if not env_file.exists():
        print(f"❌ 文件不存在: {env_file}")
        return

    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    updated = False
    for i, line in enumerate(lines):
        if line.startswith(f'{key}='):
            lines[i] = f'{key}={value}\n'
            updated = True
            break

    if not updated:
        lines.append(f'{key}={value}\n')

    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def show_summary():
    """显示配置摘要"""
    print_section("配置摘要")

    env_file = Path(__file__).parent / "betta-fish-main" / ".env"
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    search_keys = ['TAVILY_API_KEY', 'BOCHA_WEB_SEARCH_API_KEY']
    llm_keys = ['INSIGHT_ENGINE_API_KEY', 'MEDIA_ENGINE_API_KEY',
                'QUERY_ENGINE_API_KEY', 'REPORT_ENGINE_API_KEY',
                'FORUM_HOST_API_KEY', 'KEYWORD_OPTIMIZER_API_KEY']

    print("\n🔍 网络搜索配置:")
    for key in search_keys:
        for line in lines:
            if line.startswith(key):
                value = line.split('=', 1)[1].strip()
                status = "✅" if value and not value.startswith('#') else "❌"
                print(f"  {status} {key}: {'已配置' if value and not value.startswith('#') else '未配置'}")

    print("\n🤖 LLM 配置:")
    for key in llm_keys:
        for line in lines:
            if line.startswith(key):
                value = line.split('=', 1)[1].strip()
                status = "✅" if value and not value.startswith('#') else "❌"
                print(f"  {status} {key}: {'已配置' if value and not value.startswith('#') else '未配置'}")

    print("\n" + "=" * 70)
    print("配置完成！下一步:")
    print("  1. 运行测试: python test_betta_fish_apis.py")
    print("  2. 启动 BettaFish: cd betta-fish-main && python app.py")
    print("  3. 访问: http://localhost:5000")
    print("=" * 70)

def main():
    print_header("BettaFish 完整配置助手")

    print("\n本助手将帮你配置:")
    print("  ✅ 第三阶段: 网络搜索 API (Tavily/Bocha)")
    print("  ✅ 第四阶段: 独立 LLM (6个Agent)")
    print("  ✅ 爬虫支持 (Crawl4ai)")

    print("\n配置文件: betta-fish-main/.env")

    input("\n按 Enter 继续...")

    # 第三阶段：网络搜索
    configure_tavily()
    configure_bocha()

    # 第四阶段：LLM
    configure_llms()

    # 摘要
    show_summary()

if __name__ == '__main__':
    main()
