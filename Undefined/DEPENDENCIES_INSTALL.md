# Undefined 依赖安装说明

## 一键安装脚本

### Windows 用户
双击运行 `Undefined/install_dependencies.bat`

### Linux/macOS 用户
```bash
cd Undefined
chmod +x install_dependencies.sh
./install_dependencies.sh
```

## 脚本功能

该脚本会自动完成以下步骤：

1. 检查 Python 版本
2. 升级 pip 到最新版本
3. 安装核心依赖 (`requirements.txt`)
4. 安装可选依赖 (`requirements-optional.txt`，如果存在)
5. 验证依赖安装是否成功

## 核心依赖列表

主要依赖包括：
- `httpx` - HTTP 客户端
- `aiofiles` - 异步文件操作
- `tomllib` (Python 3.11+) / `tomli` (Python 3.10-) - TOML 解析
- `aiohttp` - 异步 HTTP
- `anthropic` - Anthropic API 客户端
- `openai` - OpenAI 兼容 API 客户端
- 等等...

完整列表请查看 `Undefined/requirements.txt`

## 可选依赖

可选依赖包括：
- `playwright` - 浏览器自动化
- `pillow` - 图像处理
- `pydub` - 音频处理
- `neo4j` - 图数据库
- 等等...

完整列表请查看 `Undefined/requirements-optional.txt`（如果存在）

## 故障排除

### 错误：未找到 Python
请先安装 Python 3.11 或更高版本：
- Windows: https://www.python.org/downloads/
- Linux: `sudo apt install python3.11` 或 `sudo yum install python3.11`

### 错误：pip 安装失败
尝试以下方法：
```bash
# 方法1：使用国内镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 方法2：使用 conda
conda install --file requirements.txt

# 方法3：手动升级 pip
python -m ensurepip --upgrade
```

### 权限错误
如果遇到权限问题：
- Windows: 以管理员身份运行 CMD
- Linux/macOS: 使用 `sudo`

## 虚拟环境建议

推荐使用虚拟环境安装依赖：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
Windows:
venv\Scripts\activate
Linux/macOS:
source venv/bin/activate

# 运行安装脚本
./install_dependencies.sh  # 或 install_dependencies.bat
```

## 注意事项

1. **Python 版本要求**: Python 3.11 或更高版本
2. **网络连接**: 需要稳定的网络连接以下载依赖包
3. **磁盘空间**: 至少需要 500MB 可用空间
4. **重启应用**: 安装完成后建议重启 NagaAgent 以加载新依赖

## 手动安装

如果自动脚本无法使用，可以手动安装：

```bash
pip install -r requirements.txt
```

或逐个安装依赖：

```bash
pip install httpx aiofiles tomli aiohttp anthropic openai ...
```
