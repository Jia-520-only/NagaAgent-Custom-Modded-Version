"""
弥娅·阿尔缪斯 - 双层意识架构使用示例

演示如何使用双层意识系统
"""

import asyncio
from system.consciousness_engine import create_dual_layer_consciousness


async def example_dual_layer_consciousness():
    """双层意识使用示例"""

    # 配置
    config = {
        "consciousness": {
            "enabled": True,
            "mode": "dual_layer"
        },
        "location": {
            "enabled": True,
            "auto_detect": True,
            "manual_city": ""
        }
    }

    # 1. 创建双层意识实例
    coordinator = create_dual_layer_consciousness(config)

    # 2. 定义LLM生成函数（模拟）
    async def mock_llm_generator(user_input: str, system_prompt: str, conversation_history: list = None) -> str:
        """
        模拟LLM生成函数

        实际使用时，替换为真实的LLM API调用
        """
        # 这里可以调用真实的LLM API
        # 例如：return await call_openai_api(user_input, system_prompt, conversation_history)

        # 模拟返回
        responses = {
            "你好": "你好呀！很高兴见到你~",
            "我点了一碗羊肉粉": "羊肉粉听起来很温暖呢，记得趁热吃哦！",
            "现在几点了": "天色已晚，夜幕降临了呢~"
        }
        return responses.get(user_input, "我理解了你的意思~")

    # 3. 调用思考流程
    print("=" * 60)
    print("双层意识示例")
    print("=" * 60)

    user_inputs = [
        "你好，弥娅",
        "我点了一碗羊肉粉",
        "现在几点了"
    ]

    for user_input in user_inputs:
        print(f"\n用户: {user_input}")

        result = await coordinator.think(
            user_input=user_input,
            context={
                "conversation_history": [],
            },
            llm_generator=mock_llm_generator
        )

        print(f"弥娅: {result['response']}")
        print(f"情感: {result['emotion']} | 语调: {result['voice_tone']}")
        print(f"思考耗时: {result['thinking_time']:.3f}秒")

    # 4. 查看后端状态（调试用）
    print("\n" + "=" * 60)
    print("后端感知状态（调试信息）")
    print("=" * 60)

    backend_state = coordinator.get_backend_state()

    # 时空感知
    spatial = backend_state["spatial_temporal"]
    print(f"\n[时空感知]")
    print(f"  时间: {spatial['current_date']} {spatial['current_time']}")
    print(f"  季节: {spatial['current_season']} {spatial['time_period']}")
    print(f"  位置: {spatial['location'] or '未知'}")

    # 情感状态
    emotion = backend_state["emotional_state"]
    print(f"\n[情感状态]")
    print(f"  当前情感: {emotion['current_emotion']} (强度: {emotion['emotion_intensity']:.2f})")
    print(f"  情感趋势: {emotion['emotion_trend']}")

    # 交互感知
    interaction = backend_state["interaction_awareness"]
    print(f"\n[交互感知]")
    print(f"  总交互次数: {interaction['interaction_count']}")
    print(f"  活跃时段: {interaction['interaction_frequency']}")

    # 自我认知
    self_cog = backend_state["self_cognition"]
    print(f"\n[自我认知]")
    print(f"  意识等级: {self_cog['consciousness_level']:.1f}")
    print(f"  学习阶段: {self_cog['learning_stage']}")

    # 5. 查看会话统计
    print("\n" + "=" * 60)
    print("会话统计")
    print("=" * 60)

    stats = coordinator.get_session_stats()
    print(f"\n总交互次数: {stats['total_interactions']}")
    print(f"总思考时间: {stats['total_thinking_time']:.3f}秒")
    if stats['total_interactions'] > 0:
        print(f"平均思考时间: {stats['total_thinking_time'] / stats['total_interactions']:.3f}秒")


async def example_backend_awareness():
    """后端意识单独使用示例"""

    config = {
        "location": {
            "enabled": True,
            "auto_detect": True,
            "manual_city": ""
        }
    }

    from system.backend_awareness import BackendAwareness

    backend = BackendAwareness(config)

    # 更新所有感知
    backend.update_all()

    # 记录交互
    backend.record_interaction(intent="日常对话", sentiment="积极")

    # 更新情感
    backend.update_emotion(emotion="开心", intensity=0.7)

    # 获取感知上下文
    context = backend.get_awareness_context()

    print("\n后端感知上下文：")
    print(f"时空: {context['spatial_temporal']}")
    print(f"情感: {context['emotion']}")
    print(f"交互: {context['interaction']}")
    print(f"自我: {context['self']}")


async def example_frontend_consciousness():
    """前端意识单独使用示例"""

    config = {}

    from system.frontend_consciousness import FrontendConsciousness

    frontend = FrontendConsciousness(config)

    # 模拟后端上下文
    backend_context = {
        "spatial_temporal": {
            "time_context": "2026-01-25 19:49，冬季晚上",
            "location": "贵州 黔南布依族苗族自治州",
            "awareness_level": 0.3
        },
        "emotion": {
            "current": "开心",
            "intensity": 0.7,
            "trend": "rising"
        },
        "interaction": {
            "count": 50,
            "frequency": {"晚上": 30, "下午": 20},
            "recent_intent": "日常对话",
            "recent_sentiment": "积极"
        },
        "self": {
            "consciousness_level": 0.3,
            "learning_stage": "成长期",
            "relationship_depth": 0.5
        }
    }

    # 模拟LLM生成函数
    async def mock_llm_generator(user_input: str, system_prompt: str, conversation_history: list = None) -> str:
        return "天色已晚，夜幕降临，记得注意保暖哦~"

    # 生成回复
    result = frontend.generate_response(
        user_input="现在几点了",
        backend_context=backend_context,
        llm_generator=mock_llm_generator,
        conversation_history=[]
    )

    print("\n前端回复：")
    print(f"文本: {result['response_text']}")
    print(f"情感: {result['emotion']}")
    print(f"语调: {result['voice_tone']}")
    print(f"风格: {result['speaking_style']}")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_dual_layer_consciousness())
    # asyncio.run(example_backend_awareness())
    # asyncio.run(example_frontend_consciousness())
