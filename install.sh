#!/bin/bash

# NagaAgent 一键安装脚本 (Linux/Mac)

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_banner() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                           ║${NC}"
    echo -e "${BLUE}║              NagaAgent 一键安装脚本 v1.0                  ║${NC}"
    echo -e "${BLUE}║                                                           ║${NC}"
    echo -e "${BLUE}║         自动安装 · 环境检测 · 依赖配置                    ║${NC}"
    echo -e "${BLUE}║                                                           ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_info() {
    echo -e "${BLUE}[信息]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[√]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[错误]${NC} $1"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查 Python
check_python() {
    print_info "检查 Python 环境..."

    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "未检测到 Python，请先安装 Python 3.11 或更高版本"
        echo "Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-venv"
        echo "macOS: brew install python@3.11"
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_success "Python 版本: $PYTHON_VERSION"

    # 检查 Python 版本
    MAJOR_VERSION=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major)')
    MINOR_VERSION=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')

    if [ "$MAJOR_VERSION" -lt 3 ] || [ "$MAJOR_VERSION" -eq 3 -a "$MINOR_VERSION" -lt 11 ]; then
        print_error "Python 版本过低，需要 3.11 或更高版本"
        exit 1
    fi

    echo ""
}

# 检查 pip
check_pip() {
    print_info "检查 pip..."

    if command_exists pip3; then
        PIP_CMD="pip3"
    elif command_exists pip; then
        PIP_CMD="pip"
    else
        print_error "未检测到 pip"
        exit 1
    fi

    PIP_VERSION=$($PIP_CMD --version 2>&1 | awk '{print $2}')
    print_success "pip 版本: $PIP_VERSION"
    echo ""
}

# 检查虚拟环境
check_venv() {
    print_info "检查虚拟环境..."

    if [ -d "venv" ]; then
        print_warning "检测到已存在的虚拟环境"
        read -p "是否删除并重新创建? [y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "删除现有虚拟环境..."
            rm -rf venv
            print_info "创建新虚拟环境..."
            $PYTHON_CMD -m venv venv
            if [ $? -ne 0 ]; then
                print_error "创建虚拟环境失败"
                exit 1
            fi
        else
            print_info "保留现有虚拟环境"
        fi
    else
        print_info "创建虚拟环境..."
        $PYTHON_CMD -m venv venv
        if [ $? -ne 0 ]; then
            print_error "创建虚拟环境失败"
            exit 1
        fi
    fi

    print_success "虚拟环境创建成功"
    echo ""
}

# 激活虚拟环境
activate_venv() {
    print_info "激活虚拟环境..."

    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_success "虚拟环境已激活"
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
        print_success "虚拟环境已激活"
    else
        print_error "找不到虚拟环境激活脚本"
        exit 1
    fi

    echo ""
}

# 升级 pip
upgrade_pip() {
    print_info "升级 pip..."
    python -m pip install --upgrade pip -q
    print_success "pip 已升级到最新版本"
    echo ""
}

# 安装依赖
install_dependencies() {
    print_info "安装项目依赖..."

    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            print_error "依赖安装失败"
            exit 1
        fi
        print_success "依赖安装成功"
    else
        print_warning "未找到 requirements.txt，跳过依赖安装"
    fi

    echo ""
}

# 运行配置向导
run_wizard() {
    print_info "启动配置向导..."
    echo ""
    python install_wizard.py
}

# 主函数
main() {
    print_banner

    # 检查 Python
    check_python

    # 检查 pip
    check_pip

    # 检查虚拟环境
    check_venv

    # 激活虚拟环境
    activate_venv

    # 升级 pip
    upgrade_pip

    # 安装依赖
    install_dependencies

    # 运行配置向导
    run_wizard

    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    print_success "安装流程已完成!"
    echo ""
    echo "下一步操作:"
    echo "  1. 根据配置向导提示完成配置"
    echo "  2. 如需 Neo4j，请先安装并启动 Neo4j 服务"
    echo "  3. 如需 GPT-SoVITS，请先安装并启动 GPT-SoVITS 服务"
    echo "  4. 启动程序:"
    echo "     - ./start.sh      (启动主程序)"
    echo "     - source venv/bin/activate (激活虚拟环境)"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo ""
}

# 运行主函数
main "$@"
