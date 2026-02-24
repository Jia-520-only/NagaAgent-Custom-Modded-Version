#!/bin/bash
set -euo pipefail

# 检查Python版本
PYTHON_VERSION=$(python --version 2>&1 | grep -oP '\d+\.\d+')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
    echo "✅ Python版本检查通过: $PYTHON_VERSION"
    python setup.py
else
    echo "❌ 需要Python 3.11或更高版本，当前版本: $PYTHON_VERSION"
    exit 1
fi

