# NagaAgent 脚本工具

本目录包含 NagaAgent 的各种管理脚本。

---

## 📋 脚本列表

### 📦 安装与更新

| 脚本 | 功能 | 使用方法 |
|------|------|----------|
| `setup.bat` | Windows 自动安装脚本 | 双击运行 |
| `setup.sh` | Linux/macOS 自动安装脚本 | `./setup.sh` |
| `setup.py` | Python 安装脚本 | `python setup.py` |
| `update.bat` | Windows 更新脚本 | 双击运行 |
| `update.py` | Python 更新脚本 | `python update.py` |

### 🚀 启动脚本

| 脚本 | 功能 | 使用方法 |
|------|------|----------|
| `start.bat` | Windows 启动脚本 | 双击运行 |
| `start.sh` | Linux/macOS 启动脚本 | `./start.sh` |
| `start_all.bat` | 启动所有服务 | 双击运行 |

### ⚙️ 配置脚本

| 脚本 | 功能 | 使用方法 |
|------|------|----------|
| `configure_betta_fish.py` | 自动配置 BettaFish | `python configure_betta_fish.py` |
| `switch_database.py` | 切换数据库模式 | `python switch_database.py` |

| `update_env_password.py` | 更新环境变量密码 | `python update_env_password.py` |

### 🧹 清理脚本

| 脚本 | 功能 | 使用方法 |
|------|------|----------|
| `clear.py` | 清理缓存和临时文件 | `python clear.py` |
| `build.py` | 构建项目 | `python build.py` |

---

## 🚀 快速开始

### 首次安装

```bash
# Windows
setup.bat

# Linux/macOS
./setup.sh
```

### 启动应用

```bash
# Windows
start.bat

# Linux/macOS
./start.sh
```

### 配置 BettaFish

```bash
python configure_betta_fish.py
```

### 切换数据库模式

```bash
python switch_database.py
```

---

## 📝 详细说明

### setup.bat / setup.sh

**功能**：自动安装所有依赖和初始化项目

**执行内容**：
1. 检查 Python 版本
2. 创建虚拟环境
3. 安装依赖
4. 检查系统环境
5. 复制配置文件模板

### configure_betta_fish.py

**功能**：自动配置 BettaFish 舆情分析系统

**执行内容**：
1. 检查数据库连接
2. 配置网络搜索 API（Tavily/Bocha）
3. 配置 LLM API（DeepSeek/OpenAI 等）
4. 初始化数据库
5. 测试连接

**使用示例**：

```bash
python configure_betta_fish.py
```

按照提示输入 API 密钥即可。

### switch_consciousness.py

**功能**：切换弥娅的意识模式

**使用示例**：

```bash
python switch_consciousness.py
```

**模式说明**：

1. **Hybrid Mode（混合模式）** ⭐ 推荐
   - 基于记忆和人生书独立思考
   - 需要时调用大模型辅助
   - 类似人类用手机查询信息

2. **Local Mode（本地模式）**
   - 完全基于本地记忆思考
   - 不调用大模型
   - 可以离线运行

3. **AI Mode（AI模式）**
   - 直接调用大模型
   - 兼容旧版行为

详见 [初意识系统文档](../docs/初意识系统.md)

### switch_database.py

**功能**：切换数据库模式（云端/本地/混合）

**使用示例**：

```bash
python switch_database.py
```

选择模式：
1. Cloud Mode - 云端数据库
2. Local Mode - 本地 MySQL（端口 9902）
3. Hybrid Mode - 云端和本地都使用

### update_env_password.py

**功能**：更新环境变量中的密码

**使用示例**：

```bash
python update_env_password.py
```

---

## 🔧 高级用法

### 自定义配置

编辑 `config.json` 文件进行自定义配置：

```json
{
  "api": {
    "api_key": "your_api_key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4"
  }
}
```

### 手动安装依赖

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.\.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 使用 uv 安装（更快）

```bash
# 安装 uv
pip install uv

# 同步依赖
uv sync
```

---

## 🛠️ 故障排查

### 安装失败

1. 检查 Python 版本是否为 3.11
   ```bash
   python --version
   ```

2. 使用国内镜像源安装
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

### 脚本无法运行

1. 检查文件权限
   ```bash
   # Linux/macOS
   chmod +x setup.sh
   chmod +x start.sh
   ```

2. 检查 Python 是否在 PATH 中
   ```bash
   python --version
   ```

3. 尝试使用完整路径
   ```bash
   python e:\NagaAgent\configure_betta_fish.py
   ```

---

## 📚 相关文档

- [快速开始指南](../docs/快速开始.md)
- [配置指南](../docs/配置指南/配置总览.md)
- [故障排查](../docs/故障排查.md)

---

**提示**：所有脚本都支持 `--help` 参数查看帮助信息。
