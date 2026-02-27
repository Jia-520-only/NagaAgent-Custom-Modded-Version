"""调试 Undefined MCP Server 初始化问题"""
import sys
from pathlib import Path

# 添加路径
UNDEFINED_PATH = Path(__file__).parent.parent / "Undefined"
UNDEFINED_SRC_PATH = UNDEFINED_PATH / "src"
sys.path.insert(0, str(UNDEFINED_SRC_PATH))

print(f"Undefined路径: {UNDEFINED_PATH}")
print(f"Undefined源码路径: {UNDEFINED_SRC_PATH}")
print(f"路径存在: {UNDEFINED_SRC_PATH.exists()}")

# 尝试导入模块
try:
    from Undefined.ai import AIClient
    print("[OK] 导入 AIClient 成功")
except Exception as e:
    print(f"[FAIL] 导入 AIClient 失败: {e}")
    sys.exit(1)

try:
    from Undefined.config import Config
    print("[OK] 导入 Config 成功")
except Exception as e:
    print(f"[FAIL] 导入 Config 失败: {e}")
    sys.exit(1)

try:
    from Undefined.skills.tools import ToolRegistry as NewToolRegistry
    print("[OK] 导入 NewToolRegistry 成功")
except Exception as e:
    print(f"[FAIL] 导入 NewToolRegistry 失败: {e}")
    sys.exit(1)

try:
    from Undefined.tools import ToolRegistry as OldToolRegistry
    print("[OK] 导入 OldToolRegistry 成功")
except Exception as e:
    print(f"[FAIL] 导入 OldToolRegistry 失败: {e}")
    sys.exit(1)

try:
    from Undefined.skills.agents import AgentRegistry
    print("[OK] 导入 AgentRegistry 成功")
except Exception as e:
    print(f"[FAIL] 导入 AgentRegistry 失败: {e}")
    sys.exit(1)

try:
    from Undefined.memory import MemoryStorage
    print("[OK] 导入 MemoryStorage 成功")
except Exception as e:
    print(f"[FAIL] 导入 MemoryStorage 失败: {e}")
    sys.exit(1)

try:
    from Undefined.end_summary_storage import EndSummaryStorage
    print("[OK] 导入 EndSummaryStorage 成功")
except Exception as e:
    print(f"[FAIL] 导入 EndSummaryStorage 失败: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("尝试加载配置...")

# 切换到Undefined目录
import os
original_dir = os.getcwd()
print(f"当前目录: {original_dir}")
os.chdir(str(UNDEFINED_PATH))
print(f"切换到: {UNDEFINED_PATH}")

try:
    config = Config.load(config_path=UNDEFINED_PATH / "config.toml", strict=False)
    print(f"✓ 配置加载成功")
    print(f"  - bot_qq: {config.bot_qq}")
    print(f"  - superadmin_qq: {config.superadmin_qq}")
except Exception as e:
    print(f"✗ 配置加载失败: {e}")
    import traceback
    traceback.print_exc()
    os.chdir(original_dir)
    sys.exit(1)

# 恢复原目录
os.chdir(original_dir)

print("\n" + "="*50)
print("尝试初始化组件...")

try:
    memory_storage = MemoryStorage()
    print("✓ MemoryStorage 初始化成功")
except Exception as e:
    print(f"✗ MemoryStorage 初始化失败: {e}")
    import traceback
    traceback.print_exc()

try:
    end_summary_storage = EndSummaryStorage()
    print("✓ EndSummaryStorage 初始化成功")
except Exception as e:
    print(f"✗ EndSummaryStorage 初始化失败: {e}")
    import traceback
    traceback.print_exc()

try:
    ai_client = AIClient(
        chat_config=config.chat_model,
        vision_config=config.vision_model,
        agent_config=config.agent_model,
        memory_storage=memory_storage,
        end_summary_storage=end_summary_storage,
        bot_qq=config.bot_qq,
        runtime_config=config
    )
    print("✓ AIClient 初始化成功")
except Exception as e:
    print(f"✗ AIClient 初始化失败: {e}")
    import traceback
    traceback.print_exc()

try:
    new_tools_dir = UNDEFINED_SRC_PATH / "Undefined" / "skills" / "tools"
    new_tool_registry = NewToolRegistry(new_tools_dir)
    print(f"✓ NewToolRegistry 初始化成功 ({len(new_tool_registry._items)} 个工具)")
except Exception as e:
    print(f"✗ NewToolRegistry 初始化失败: {e}")
    import traceback
    traceback.print_exc()

try:
    old_tool_registry = OldToolRegistry()
    print(f"✓ OldToolRegistry 初始化成功 ({len(old_tool_registry._tools_handlers)} 个工具)")
except Exception as e:
    print(f"✗ OldToolRegistry 初始化失败: {e}")
    import traceback
    traceback.print_exc()

try:
    agent_registry = AgentRegistry()
    agent_registry.load_agents()
    print(f"✓ AgentRegistry 初始化成功 ({len(agent_registry._items)} 个Agent)")
except Exception as e:
    print(f"✗ AgentRegistry 初始化失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
print("所有组件初始化完成！")
