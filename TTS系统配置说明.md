# 弥娅 AI - TTS语音系统配置说明

## 概述

弥娅 AI 支持多种TTS（文本转语音）引擎，可以根据需求灵活切换：

1. **Edge-TTS** - 在线免费，速度快（默认）
2. **GPT-SoVITS** - 本地定制化，高质量
3. **Genie-TTS** - GPT-SoVITS ONNX版本，轻量级
4. **VITS** - 高效本地TTS引擎

---

## 配置文件位置

所有TTS配置位于 `config.json` 的 `tts` 部分。

---

## TTS引擎对比

| 引擎 | 类型 | 特点 | 端口 | 状态 |
|------|------|------|------|------|
| **Edge-TTS** | 在线 | 免费、速度快、多语音 | - | ✅ 默认启用 |
| **GPT-SoVITS** | 本地 | 定制化、高质量、需要模型 | 9880 | ⚠️ 需单独启动 |
| **Genie-TTS** | 本地 | ONNX版本、轻量级 | 8000 | ⚠️ 需单独启动 |
| **VITS** | 本地 | 高效、需要模型 | 7860 | ⚠️ 需单独启动 |

---

## 完整配置说明

### 基础配置

```json
{
  "tts": {
    // 基础设置
    "enabled": true,                    // 是否启用TTS功能
    "port": 5048,                        // TTS服务端口
    "api_key": "",                       // API密钥（可选）

    // 默认引擎设置
    "default_engine": "edge_tts",        // 默认引擎: edge_tts, gpt_sovits, genie_tts, vits
    "engine": "edge_tts",                // 当前使用的引擎

    // Edge-TTS 设置
    "default_voice": "zh-CN-XiaoxiaoNeural",  // 默认语音
    "default_format": "mp3",             // 默认音频格式
    "default_speed": 1.0,                // 默认语速
    "default_language": "zh-CN",         // 默认语言

    // 高级设置
    "remove_filter": false,              // 是否移除过滤器
    "expand_api": true,                  // 是否扩展API
    "require_api_key": false,            // 是否需要API密钥
    "keep_audio_files": false            // 是否保留音频文件（调试用）
  }
}
```

### GPT-SoVITS 配置

```json
{
  "tts": {
    // GPT-SoVITS 设置
    "gpt_sovits_enabled": false,         // 是否启用GPT-SoVITS
    "gpt_sovits_url": "http://127.0.0.1:9880",  // GPT-SoVITS服务地址
    "gpt_sovits_speed": 1.0,              // 语速 (0.1-3.0)
    "gpt_sovits_top_k": 15,               // Top-K参数 (1-50)
    "gpt_sovits_top_p": 1.0,              // Top-P参数 (0.0-1.0)
    "gpt_sovits_temperature": 1.0,        // 温度参数 (0.1-2.0)
    "gpt_sovits_ref_free": false,        // 是否免参考模式
    "gpt_sovits_ref_text": "",           // 参考文本
    "gpt_sovits_ref_audio_path": "",     // 参考音频路径
    "gpt_sovits_filter_brackets": false,  // 是否过滤括号
    "gpt_sovits_filter_special_chars": false  // 是否过滤特殊字符
  }
}
```

### Genie-TTS 配置

```json
{
  "tts": {
    // Genie-TTS 设置
    "genie_tts_enabled": false,          // 是否启用Genie-TTS
    "genie_tts_url": "http://127.0.0.1:8000",  // Genie-TTS服务地址
    "genie_tts_timeout": 60              // 超时时间（秒）
  }
}
```

### VITS 配置

```json
{
  "tts": {
    // VITS 设置
    "vits_enabled": false,               // 是否启用VITS
    "vits_url": "http://127.0.0.1:7860/api/tts",  // VITS服务地址
    "vits_voice_id": 0                   // 默认说话人ID
  }
}
```

---

## 快速启用指南

### 使用 Edge-TTS（默认，推荐）

无需额外配置，系统已默认使用Edge-TTS。

```bash
# 直接启动即可
start.bat
```

### 启用 GPT-SoVITS

#### 步骤1: 安装 GPT-SoVITS

1. 下载 GPT-SoVITS 项目
   ```bash
   git clone https://github.com/RVC-Boss/GPT-SoVITS.git
   ```

2. 进入项目目录并安装依赖
   ```bash
   cd GPT-SoVITS
   pip install -r requirements.txt
   ```

3. 下载或训练模型（参考官方文档）

#### 步骤2: 启动 GPT-SoVITS 服务

在 GPT-SoVITS 项目目录中启动推理服务：
```bash
python api_v2.py
```

服务将在端口 9880 运行。

#### 步骤3: 配置弥娅 AI

编辑 `config.json`:
```json
{
  "tts": {
    "gpt_sovits_enabled": true,
    "default_engine": "gpt_sovits",
    "gpt_sovits_url": "http://127.0.0.1:9880",
    "gpt_sovits_speed": 1.0,
    "gpt_sovits_ref_text": "这是参考文本",
    "gpt_sovits_ref_audio_path": "path/to/ref_audio.wav"
  }
}
```

#### 步骤4: 重启主程序

```bash
start.bat
```

### 启用 Genie-TTS

#### 步骤1: 安装 Genie-TTS

1. 下载 Genie-TTS 项目
   ```bash
   git clone https://github.com/GeneZC/Genie-TTS.git
   ```

2. 安装依赖
   ```bash
   cd Genie-TTS
   pip install -r requirements.txt
   ```

#### 步骤2: 启动 Genie-TTS 服务

```bash
python server.py --port 8000
```

#### 步骤3: 配置弥娅 AI

编辑 `config.json`:
```json
{
  "tts": {
    "genie_tts_enabled": true,
    "default_engine": "genie_tts",
    "genie_tts_url": "http://127.0.0.1:8000"
  }
}
```

### 启用 VITS

#### 步骤1: 安装 VITS

1. 下载 VITS 项目
   ```bash
   git clone https://github.com/jaywalnut310/vits.git
   ```

2. 安装依赖并下载模型

#### 步骤2: 启动 VITS 服务

```bash
python server.py --port 7860
```

#### 步骤3: 配置弥娅 AI

编辑 `config.json`:
```json
{
  "tts": {
    "vits_enabled": true,
    "default_engine": "vits",
    "vits_url": "http://127.0.0.1:7860/api/tts",
    "vits_voice_id": 0
  }
}
```

---

## 参数详细说明

### GPT-SoVITS 参数

| 参数 | 类型 | 范围 | 默认值 | 说明 |
|------|------|------|--------|------|
| `gpt_sovits_speed` | float | 0.1-3.0 | 1.0 | 语速，1.0为正常速度 |
| `gpt_sovits_top_k` | int | 1-50 | 15 | Top-K采样参数 |
| `gpt_sovits_top_p` | float | 0.0-1.0 | 1.0 | Top-P采样参数 |
| `gpt_sovits_temperature` | float | 0.1-2.0 | 1.0 | 温度参数，影响随机性 |
| `gpt_sovits_ref_free` | bool | - | false | 免参考模式 |
| `gpt_sovits_ref_text` | string | - | "" | 参考文本（用于克隆声线）|
| `gpt_sovits_ref_audio_path` | string | - | "" | 参考音频路径 |
| `gpt_sovits_filter_brackets` | bool | - | false | 过滤括号内容 |
| `gpt_sovits_filter_special_chars` | bool | - | false | 过滤特殊字符 |

### Edge-TTS 语音列表

部分常用语音（更多参考官方文档）：

| 语音代码 | 说明 |
|---------|------|
| `zh-CN-XiaoxiaoNeural` | 晓晓（女，默认）|
| `zh-CN-YunxiNeural` | 云希（男）|
| `zh-CN-YunjianNeural` | 云健（男）|
| `zh-CN-XiaoyiNeural` | 晓伊（女）|
| `zh-CN-YunyangNeural` | 云扬（男）|
| `zh-CN-XiaohanNeural` | 晓涵（女）|
| `zh-CN-XiaomengNeural` | 晓梦（女）|
| `zh-CN-XiaoxuanNeural` | 晓萱（女）|
| `zh-CN-XiaomoNeural` | 晓墨（女）|

---

## 启动脚本说明

### start_gptsovits.bat

**功能**: GPT-SoVITS 配置检查和集成测试

**使用方法**:
```bash
start_gptsovits.bat
```

**功能说明**:
- 检查 Python 环境
- 检查 config.json 配置
- 显示 GPT-SoVITS 配置状态
- 测试 GPT-SoVITS 集成
- 提供配置参数说明

---

## 故障排查

### 问题1: GPT-SoVITS 无声音

**可能原因**:
1. GPT-SoVITS 服务未启动
2. 端口配置错误
3. 模型未加载

**解决方案**:
1. 检查 GPT-SoVITS 服务是否运行在 9880 端口
2. 检查 config.json 中的 `gpt_sovits_url` 配置
3. 确认模型已正确加载

### 问题2: 切换引擎后仍使用旧引擎

**可能原因**:
配置未生效，需要重启

**解决方案**:
```bash
# 修改 config.json 后重启
start.bat
```

### 问题3: Edge-TTS 语音切换无效

**可能原因**:
语音代码错误

**解决方案**:
1. 检查语音代码是否正确
2. 使用标准语音代码（见上文列表）
3. 参考 Edge-TTS 官方文档

### 问题4: 语速调节无效

**可能原因**:
参数范围超出限制

**解决方案**:
确保速度参数在 0.1-3.0 范围内

---

## 性能优化建议

### Edge-TTS
- ✅ 速度最快，无需本地资源
- ✅ 适合日常使用
- ⚠️ 需要网络连接

### GPT-SoVITS
- ✅ 语音质量最高
- ✅ 可定制化
- ⚠️ 需要较好的硬件（GPU推荐）
- ⚠️ 首次启动慢

### Genie-TTS
- ✅ 轻量级
- ✅ ONNX版本，部署简单
- ⚠️ 质量略低于GPT-SoVITS

### VITS
- ✅ 高效
- ⚠️ 需要训练模型
- ⚠️ 配置较复杂

---

## 使用场景推荐

### 日常对话
推荐使用 **Edge-TTS**
- 响应快
- 无需额外配置
- 语音质量良好

### 追求高质量语音
推荐使用 **GPT-SoVITS**
- 可以克隆特定声线
- 语音自然度高
- 适合定制化需求

### 离线环境
推荐使用 **Genie-TTS** 或 **VITS**
- 完全离线运行
- 不依赖网络
- 适合隐私敏感场景

---

## API接口说明

### 切换TTS引擎

通过对话或API调用切换引擎：

```
"请使用GPT-SoVITS语音"
"切换到Edge-TTS"
"使用VITS引擎"
```

### 调整语速

```
"语速快一点"
"语速慢一点"
"语速恢复正常"
```

### 更换语音（Edge-TTS）

```
"更换为云希的声音"
"使用男声"
"使用女声"
```

---

## 注意事项

1. **端口占用**: 确保配置的端口未被占用
2. **模型路径**: 参考音频路径必须是绝对路径
3. **网络连接**: Edge-TTS 需要网络连接
4. **硬件要求**: GPT-SoVITS 推荐使用 GPU
5. **权限问题**: 确保有读取音频文件的权限

---

## 更新日志

### v4.0 Modified (2026-02-20)
- 添加完整的TTS配置
- 支持4种TTS引擎
- 创建GPT-SoVITS配置脚本
- 创建详细的配置说明文档

---

## 相关文档

- `voice/README.md` - 语音系统文档
- `系统功能修复报告.md` - 系统修复报告
- `功能状态汇总.md` - 功能状态总览

---

**最后更新**: 2026-02-20
