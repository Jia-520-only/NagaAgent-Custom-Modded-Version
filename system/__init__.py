"""
系统模块 - 弥娅的意识系统

包含：
- consciousness_engine.py: 原始意识引擎（向后兼容）
- backend_awareness.py: 后端意识（内部感知）
- frontend_consciousness.py: 前端意识（对外表达）
- consciousness_coordinator.py: 意识协调器（整合前后端）
- temporal_perception.py: 时间感知系统
- task_scheduler.py: 任务调度器
- task_intent_parser.py: 任务意图解析
- task_controller.py: 任务控制器
- task_service_manager.py: 任务服务管理器
- active_communication.py: 主动交流系统

使用方式：
    # 推荐方式：双层意识
    from system.consciousness_engine import create_dual_layer_consciousness
    coordinator = create_dual_layer_consciousness(config)
    result = await coordinator.think(...)

    # 传统方式（向后兼容）
    from system.consciousness_engine import create_legacy_consciousness
    engine = create_legacy_consciousness(config)
    result = await engine.think(...)

    # 时间感知
    from system.temporal_perception import get_temporal_perception
    temporal = get_temporal_perception()
    state = temporal.get_state()

    # 任务调度
    from system.task_scheduler import get_task_scheduler
    scheduler = get_task_scheduler()
    await scheduler.start()
    task_id = scheduler.add_task(...)

    # 任务控制器（集成）
    from system.task_service_manager import get_task_service_manager
    manager = get_task_service_manager()
    await manager.initialize()
    result = await manager.process_user_input("每半小时提醒我起来走走")
"""

from .consciousness_engine import (
    ConsciousnessEngine,
    LifeBook,
    MemorySystem,
    CognitionBase,
    create_dual_layer_consciousness,
    create_legacy_consciousness,
)

from .backend_awareness import BackendAwareness
from .frontend_consciousness import FrontendConsciousness
from .consciousness_coordinator import ConsciousnessCoordinator

# 时间感知和任务调度
from .temporal_perception import get_temporal_perception, TemporalPerception
from .task_scheduler import get_task_scheduler, TaskScheduler
from .task_intent_parser import get_task_intent_parser, TaskIntentParser
from .task_controller import get_task_controller, TaskController
from .task_service_manager import get_task_service_manager, TaskServiceManager
from .active_communication import get_active_communication, ActiveCommunication

__all__ = [
    # 工厂函数
    "create_dual_layer_consciousness",
    "create_legacy_consciousness",

    # 主要类 - 意识系统
    "ConsciousnessEngine",
    "ConsciousnessCoordinator",
    "BackendAwareness",
    "FrontendConsciousness",

    # 辅助类 - 意识系统
    "LifeBook",
    "MemorySystem",
    "CognitionBase",

    # 工厂函数 - 时间和任务
    "get_temporal_perception",
    "get_task_scheduler",
    "get_task_intent_parser",
    "get_task_controller",
    "get_task_service_manager",
    "get_active_communication",

    # 主要类 - 时间和任务
    "TemporalPerception",
    "TaskScheduler",
    "TaskIntentParser",
    "TaskController",
    "TaskServiceManager",
    "ActiveCommunication",
]
