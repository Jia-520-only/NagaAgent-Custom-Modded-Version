#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动弥娅并启用自主性
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from system.config import config, logger
from system.agency_manager import get_agency_manager


async def start_agency():
    """启动自主性系统"""
    logger.info("🤔 正在启动弥娅自主性系统...")
    
    try:
        agency_manager = get_agency_manager()
        await agency_manager.start()
        
        status = await agency_manager.get_status()
        logger.info(f"✅ 自主性系统已启动")
        logger.info(f"   等级: {status['engine']['agency_level']}")
        logger.info(f"   特性: {len(status['config']['enabled_features'])} 个功能已启用")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 自主性系统启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("=" * 60)
    print("🤔 弥娅自主性系统启动器")
    print("=" * 60)
    
    # 1. 启动自主性
    success = await start_agency()
    
    if not success:
        print("自主性系统启动失败，请检查日志")
        return
    
    print("\n" + "=" * 60)
    print("✅ 自主性系统已就绪")
    print("=" * 60)
    print("\n可用命令:")
    print("  /agency status  - 查看自主性状态")
    print("  /agency pause   - 暂停自主性")
    print("  /agency resume  - 恢复自主性")
    print("  /agency level <LEVEL>  - 设置自主等级")
    print("\n自主等级: OFF, LOW, MEDIUM, HIGH, PAUSED")
    print("=" * 60)
    
    # 2. 保持运行
    try:
        # 这里只是演示，实际应该在主系统中集成
        while True:
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        print("\n\n🛑 正在关闭自主性系统...")
        
        agency_manager = get_agency_manager()
        await agency_manager.engine.shutdown()
        
        print("✅ 自主性系统已关闭")


if __name__ == "__main__":
    asyncio.run(main())
