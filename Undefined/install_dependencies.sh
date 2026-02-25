#!/bin/bash
# Undefined 依赖安装脚本 (Linux/macOS)

set -e  # 遇到错误立即退出

cd "$(dirname "$0")"

echo "========================================"
echo "     Undefined 依赖安装脚本"
echo "========================================"
echo ""

# 检查 Python
echo "[1/5] 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "[错误] 未找到 Python"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

$PYTHON_CMD --version || {
    echo "[错误] Python 版本检查失败"
    exit 1
}

echo ""
echo "[2/5] 升级 pip 到最新版本..."
$PYTHON_CMD -m pip install --upgrade pip

echo ""
echo "[3/5] 安装核心依赖..."
if [ -f "requirements.txt" ]; then
    $PYTHON_CMD -m pip install -r requirements.txt --upgrade
else
    echo "[警告] 未找到 requirements.txt"
fi

echo ""
echo "[4/5] 安装可选依赖 (如果有)..."
if [ -f "requirements-optional.txt" ]; then
    $PYTHON_CMD -m pip install -r requirements-optional.txt --upgrade
else
    echo "[提示] 未找到 requirements-optional.txt (可选)"
fi

echo ""
echo "[5/5] 验证安装..."
$PYTHON_CMD -c "import httpx; import aiofiles; import tomllib; print('[OK] 核心依赖验证成功')" || {
    echo "[错误] 依赖安装验证失败"
    exit 1
}

echo ""
echo "========================================"
echo "     安装完成！"
echo "========================================"
echo ""
echo "提示："
echo "  - 核心依赖已安装在当前 Python 环境"
echo "  - 如果需要虚拟环境，请先激活 venv"
echo "  - 查看 requirements.txt 了解依赖列表"
echo ""
