#!/bin/bash

# 设置编码
export LANG=zh_CN.UTF-8

echo "======================================================"
echo "  VCPToolBox 高级记忆系统"
echo "  端口: 6005"
echo "  AI Provider: DeepSeek"
echo "======================================================"
echo ""

# 检查 Node.js 是否安装
if ! command -v node &> /dev/null; then
    echo "❌ 未检测到 Node.js，请先安装 Node.js"
    echo "   下载地址: https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js 版本:"
node --version
echo ""

# 检查是否已安装依赖
if [ ! -d "node_modules" ]; then
    echo "📦 首次运行，正在安装依赖..."
    echo "   这可能需要几分钟，请耐心等待..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
    echo ""
    echo "✅ 依赖安装完成"
    echo ""
fi

# 检查配置文件
if [ ! -f "config.env" ]; then
    echo "❌ 未找到配置文件 config.env"
    echo "   请确保配置文件存在"
    exit 1
fi

echo "🚀 正在启动 VCPToolBox..."
echo ""
echo "服务地址: http://127.0.0.1:6005"
echo "按 Ctrl+C 停止服务"
echo ""
echo "======================================================"
echo ""

npm start

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 服务启动失败"
fi
