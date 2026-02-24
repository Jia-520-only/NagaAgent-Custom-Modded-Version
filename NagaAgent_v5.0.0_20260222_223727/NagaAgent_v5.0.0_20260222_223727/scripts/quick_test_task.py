#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试任务系统
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from system.task_controller import get_task_controller
from system.config import logger


async def test():
    """测试任务系统"""
    print("=" * 60)
    print("快速测试任务系统")
    print("=" * 60)
    
    # 获取控制器
    controller = get_task_controller()
    
    # 初始化
    print("\n1. 初始化任务控制器...")
    try:
        await controller.initialize()
        print("✅ 初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 获取状态
    status = controller.get_status()
    print(f"\n2. 任务控制器状态:")
    print(f"   - 已初始化: {status['initialized']}")
    print(f"   - 任务数量: {status['task_count']}")
    print(f"   - 调度器运行中: {status['scheduler_status']['running']}")
    
    # 测试意图解析
    print("\n3. 测试意图解析...")
    test_inputs = [
        "每30秒提醒我起来走走",
        "一分钟以后提醒我喝水",
        "查看我的提醒",
        "删除1号提醒",
    ]
    
    for i, test_input in enumerate(test_inputs, 1):
        print(f"\n   测试 {i}: '{test_input}'")
        
        result = await controller.process_user_input(test_input)
        
        if result:
            print(f"   ✅ 识别为任务: {result['intent_type']}")
            print(f"   响应: {result['response'][:50]}...")
        else:
            print(f"   ❌ 未识别为任务")
    
    # 等待任务触发
    print("\n4. 等待30秒，查看是否有任务触发...")
    print("   (如果有设置30秒的提醒，应该会看到触发日志)")
    
    try:
        await asyncio.sleep(30)
    except KeyboardInterrupt:
        print("\n\n用户中断")
    
    # 查看任务列表
    print("\n5. 查看当前任务列表...")
    tasks = controller._scheduler.get_all_tasks()
    if tasks:
        print(f"   共 {len(tasks)} 个任务:")
        for i, task in enumerate(tasks, 1):
            print(f"   {i}. {task.title} - {task.scheduled_time} ({'循环' if task.recurring else '一次性'})")
    else:
        print("   没有任务")
    
    # 关闭
    print("\n6. 关闭任务控制器...")
    await controller.shutdown()
    print("✅ 已关闭")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        print("\n\n测试已中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
