#!/bin/bash

# Undefined 一键安装依赖脚本 (Linux/macOS)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "\033[1;36m========================================"
echo -e "     Undefined 一键安装依赖脚本"
echo -e "========================================\033[0m"
echo

# 检查 Python 版本
echo -e "\033[1;33m[1/4] 检查 Python 版本...\033[0m"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[错误] 未找到 Python3，请先安装 Python 3.11 或更高版本${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}[成功] 检测到 Python $PYTHON_VERSION${NC}"
echo

# 检查是否在 Undefined 目录下
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}[错误] 未找到 pyproject.toml，请确保在 Undefined 根目录下运行此脚本${NC}"
    exit 1
fi

# 检查并安装 uv
echo -e "\033[1;33m[2/4] 检查 uv 包管理器...\033[0m"
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}[提示] 未检测到 uv，正在安装 uv...${NC}"
    python3 -m pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple
    if [ $? -ne 0 ]; then
        echo -e "${RED}[错误] uv 安装失败${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}[成功] uv 已安装${NC}"
fi
echo

# 使用 uv 同步依赖
echo -e "\033[1;33m[3/4] 正在安装 Undefined 依赖...${NC}"
echo "这可能需要几分钟时间，请耐心等待..."
echo

uv sync
if [ $? -ne 0 ]; then
    echo -e "${RED}[错误] 依赖安装失败${NC}"
    echo
    echo -e "${YELLOW}[提示] 如果遇到网络问题，可以尝试：${NC}"
    echo "1. 使用国内镜像源"
    echo "2. 手动运行: uv pip install -e ."
    exit 1
fi
echo

# 安装 Playwright 浏览器
echo -e "\033[1;33m[4/4] 安装 Playwright 浏览器...${NC}"
uv run playwright install chromium
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}[警告] Playwright 浏览器安装失败，部分功能可能无法使用${NC}"
    echo -e "${YELLOW}[提示] 可以稍后手动运行: uv run playwright install chromium${NC}"
else
    echo -e "${GREEN}[成功] Playwright 浏览器安装完成${NC}"
fi
echo

# 创建配置文件
echo -e "\033[1;33m[配置] 检查配置文件...${NC}"
if [ ! -f "config.toml" ]; then
    if [ -f "config.toml.example" ]; then
        echo -e "${YELLOW}[提示] 复制 config.toml.example 为 config.toml${NC}"
        cp config.toml.example config.toml
        echo -e "${GREEN}[成功] 配置文件已创建，请根据需要修改 config.toml${NC}"
    fi
fi

echo -e "\033[1;36m========================================"
echo -e "         安装完成！"
echo -e "========================================\033[0m"
echo
echo "下一步："
echo "1. 编辑 config.toml 配置文件，填入你的 API Key 和 QQ 号"
echo "2. 启动 Undefined: uv run Undefined"
echo "3. 或使用 WebUI: uv run Undefined-webui"
echo
