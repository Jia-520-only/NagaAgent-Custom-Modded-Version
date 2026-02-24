# 弥娅·阿尔缪斯 - 双层意识架构快速开始

## 🚀 5分钟快速上手

### 1. 配置文件更新

在 `config.json` 中添加地理位置感知配置：

```json
{
  "location": {
    "enabled": true,
    "auto_detect": true,
    "manual_city": ""
  }
}
```

---

### 2. 基本使用

```python
from system.consciousness_engine import create_dual_layer_consciousness

# 创建协调器
coordinator = create_dual_layer_consciousness(config)

# 定义LLM生成函数
async def my_llm_generator(user_input: str, system_prompt: str, conversation_history: list = None) -> str:
    # 调用你的LLM API
    return await call_llm_api(user_input, system_prompt, conversation_history)

# 调用思考流程
result = await coordinator.think(
    user_input="你好，弥娅",
    context={},
    llm_generator=my_llm_generator
)

# 获取结果
print(result["response"])    # 回复文本
print(result["emotion"])     # 情感
print(result["voice_tone"])  # 语调
```

---

### 3. 运行示例

```bash
cd NagaAgent
python scripts/example_consciousness.py
```

---

## 📚 详细文档

- `docs/CONSCIOUSNESS_ARCHITECTURE.md` - 完整架构文档
- `docs/CONSCIOUSNESS_SUMMARY.md` - 总结文档
- `scripts/example_consciousness.py` - 使用示例

---

## 🎯 核心特性

### 后端意识（不可见）
- 时空感知（时间、位置、季节）
- 系统状态感知
- 情感状态感知
- 交互感知
- 自我认知

### 前端意识（可见）
- 基于后端感知生成对话
- 情感表达和角色扮演
- 隐式表达感知内容
- 自适应对话风格

---

## 💡 示例对比

### 直接播报（传统）
```
弥娅: "现在是晚上7点49分，我在贵州。"
```

### 隐式表达（双层意识）
```
弥娅: "天色已晚，这里的夜晚有些凉，记得多穿点衣服哦~"
```

---

## 🔗 相关链接

- 架构文档：`docs/CONSCIOUSNESS_ARCHITECTURE.md`
- 使用示例：`scripts/example_consciousness.py`
- 配置示例：`config.json`

---

## ❓ 常见问题

**Q: 如何启用地理位置感知？**
A: 在 `config.json` 中添加 `location` 配置块并设置 `enabled: true`

**Q: 后端感知会输出给用户吗？**
A: 不会。后端感知使用 `DEBUG` 日志级别，仅用于调试

**Q: 如何自定义感知模块？**
A: 在 `backend_awareness.py` 中添加新的感知方法，并在 `update_all()` 中调用

**Q: 如何兼容旧版本？**
A: 使用 `create_legacy_consciousness()` 创建传统意识实例

---

## 📞 获取帮助

查看完整文档：
- `docs/CONSCIOUSNESS_ARCHITECTURE.md`
- `docs/CONSCIOUSNESS_SUMMARY.md`

运行示例代码：
- `scripts/example_consciousness.py`
