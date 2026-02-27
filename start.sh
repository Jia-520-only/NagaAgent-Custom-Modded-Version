#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DIR/.venv"
VENV_PY="$VENV/bin/python"

if [ -x "$VENV_PY" ]; then
    # 将所有传入参数传给 main.py
    exec "$VENV_PY" "$DIR/main.py" "$@"
else
    echo "❌ 未检测到虚拟环境，请先运行安装脚本：" >&2
    echo "   Windows: install.bat" >&2
    echo "   Linux/Mac: ./install.sh" >&2
    echo "或手动创建：" >&2
    echo "   python3 -m venv .venv" >&2
    echo "   source .venv/bin/activate" >&2
    echo "   pip install -r requirements.txt" >&2
    exit 2
fi