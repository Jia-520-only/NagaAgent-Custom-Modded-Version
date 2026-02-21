#!/bin/bash
# VCP集成安装脚本

echo "======================================"
echo "VCP记忆系统集成 - 安装脚本"
echo "======================================"

# 1. 安装Python依赖
echo ""
echo "[1/3] 安装Python依赖..."
pip install httpx>=0.24.0

# 2. 检查VCPToolBox是否存在
echo ""
echo "[2/3] 检查VCPToolBox..."
if [ -d "VCPToolBox" ]; then
    echo "✅ VCPToolBox目录已存在"
else
    echo "❌ VCPToolBox目录不存在,请先下载VCPToolBox"
    echo "   下载地址: https://github.com/cherry-vip/VCPToolBox"
    exit 1
fi

# 3. 检查VCP配置文件
echo ""
echo "[3/3] 检查VCP配置..."
if [ -f "VCPToolBox/config.env" ]; then
    echo "✅ VCP配置文件已存在"
else
    echo "⚠️  VCP配置文件不存在,正在创建..."
    cp VCPToolBox/config.env.example VCPToolBox/config.env
    echo "   请编辑 VCPToolBox/config.env,设置API密钥等参数"
fi

echo ""
echo "======================================"
echo "✅ 安装完成!"
echo ""
echo "下一步:"
echo "1. 编辑 VCPToolBox/config.env,配置必要的参数"
echo "2. 启动VCPToolBox: cd VCPToolBox && npm start"
echo "3. 编辑弥娅的config.json,启用VCP:"
echo "   {"
echo '     "vcp": {'
echo '       "enabled": true,'
echo '       "base_url": "http://127.0.0.1:6005",'
echo '       "key": "YOUR_VCP_KEY"'
echo "     }"
echo "   }"
echo "4. 重启弥娅: python main.py"
echo ""
echo "======================================"
