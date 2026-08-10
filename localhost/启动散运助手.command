#!/bin/bash
cd "$(dirname "$0")/.."

echo "🌊 散运助手 · 本地服务启动中..."

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "⚠️ 未找到虚拟环境，使用系统 Python"
fi

# 确保 Flask 已安装
python3 -c "import flask" 2>/dev/null || pip3 install flask --quiet

echo "✅ 服务启动: http://localhost:8899"
echo ""

# 启动服务 + 打开浏览器
sleep 1 && open http://localhost:8899 &
python3 localhost_server.py
