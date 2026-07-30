#!/bin/bash
# ==============================================================
# MacBook (Apple Silicon) 一键环境配置脚本
# 适用于：macOS + M系列芯片 (M1/M2/M3/M4)
# 项目：中远海运散货 AI Agent「远航助手」
# ==============================================================

set -e  # 遇到错误立即退出

echo "🚀 正在为MacBook配置Python虚拟环境..."
echo "========================================"
echo ""

# 检查 Python3 是否已安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 未检测到 python3，请先安装 Python 3.10+"
    echo "   推荐使用 Homebrew: brew install python@3.12"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ 检测到 $PYTHON_VERSION"
echo ""

# 创建虚拟环境
echo "📦 正在创建虚拟环境 venv/ ..."
python3 -m venv venv
echo "✅ 虚拟环境创建完成"
echo ""

# 激活虚拟环境（Mac 专用路径）
echo "🔌 正在激活虚拟环境..."
source venv/bin/activate
echo "✅ 虚拟环境已激活"
echo ""

# 升级 pip
echo "⬆️  正在升级 pip..."
pip install --upgrade pip --quiet
echo "✅ pip 已升级到最新版本"
echo ""

# 安装依赖
echo "📥 正在安装项目依赖 (适配 Apple Silicon)..."
pip install -r requirements.txt --quiet
echo "✅ 所有依赖安装完成"
echo ""

echo "========================================"
echo "✅ 环境配置完成！"
echo ""
echo "📋 下一步操作："
echo "   1. 确认虚拟环境已激活: source venv/bin/activate"
echo "   2. 创建 .env 文件并配置 API Key:"
echo "      cp .env.example .env"
echo "      nano .env  # 填入你的 DEEPSEEK_API_KEY"
echo "   3. 启动应用: streamlit run app.py"
echo ""
echo "🌐 启动后浏览器访问: http://localhost:8501"
echo "========================================"
