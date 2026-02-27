# Undefined 依赖安装指南

## 快速安装

### Windows 系统

1. 双击运行 `install_dependencies.bat`
2. 等待安装完成
3. 编辑 `config.toml` 配置文件
4. 运行 `uv run Undefined` 启动

### Linux/macOS 系统

1. 运行 `bash install_dependencies.sh`
2. 等待安装完成
3. 编辑 `config.toml` 配置文件
4. 运行 `uv run Undefined` 启动

## 手动安装

如果自动安装失败，可以手动执行以下步骤：

### 1. 安装 uv 包管理器

```bash
python -m pip install uv
```

### 2. 同步依赖

```bash
uv sync
```

### 3. 安装 Playwright 浏览器

```bash
uv run playwright install chromium
```

### 4. 创建配置文件

```bash
# Windows
copy config.toml.example config.toml

# Linux/macOS
cp config.toml.example config.toml
```

## 依赖说明

Undefined 依赖的主要包包括：

- **核心依赖**：websockets, httpx, openai, langchain-community
- **文档处理**：pymupdf, python-docx, python-pptx, openpyxl
- **网络爬虫**：crawl4ai, playwright
- **图像处理**：pillow, imgkit, matplotlib
- **任务调度**：APScheduler, croniter
- **其他工具**：rich, psutil, chromadb

## 常见问题

### 1. Python 版本要求

Undefined 需要 Python 3.11 或更高版本（< 3.14）

### 2. uv 安装失败

如果 uv 安装失败，可以使用 pip 直接安装依赖：

```bash
pip install -e .
```

### 3. Playwright 安装失败

Playwright 浏览器安装可能需要较长时间或下载失败。可以：

- 检查网络连接
- 使用代理下载
- 手动指定下载源

### 4. 依赖冲突

如果遇到依赖冲突，可以创建新的虚拟环境：

```bash
# 使用 uv 创建虚拟环境
uv venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# 安装依赖
uv sync
```

## 使用国内镜像源

如果下载速度慢，可以配置使用国内镜像源：

### PyPI 镜像

```bash
uv pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 环境变量配置

Windows:
```cmd
set UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

Linux/macOS:
```bash
export UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

## 启动 Undefined

安装完成后，可以使用以下命令启动：

```bash
# 命令行模式
uv run Undefined

# WebUI 模式
uv run Undefined-webui
```

## 获取帮助

如果遇到问题，请：

1. 查看 Undefined README.md
2. 提交 Issue 到 GitHub
3. 参考官方文档：https://github.com/69gg/Undefined
