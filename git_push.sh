#!/bin/bash
# ==============================================================
# 一键提交 & 推送脚本（含自动重试）
# 用法：
#   ./git_push.sh "提交信息"
#   ./git_push.sh          （自动生成提交信息）
# ==============================================================

set -e
cd "$(dirname "$0")"

# 检查是否有变更（含未跟踪文件）
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    echo "📭 没有需要提交的变更"
    exit 0
fi

# 提交信息
if [ -n "$1" ]; then
    MSG="$1"
else
    MSG="更新 $(date '+%Y-%m-%d %H:%M')"
fi

echo "📦 正在提交: $MSG"
git add -A
git commit -m "$MSG"

# 推送（最多重试 5 次，间隔递增）
echo ""
MAX_RETRIES=5
for i in $(seq 1 $MAX_RETRIES); do
    echo "📡 推送中 (第 $i/$MAX_RETRIES 次)..."
    if git push 2>&1; then
        echo "✅ 提交并推送完成"
        exit 0
    fi
    if [ $i -lt $MAX_RETRIES ]; then
        WAIT=$((i * 5))
        echo "⚠️  推送失败，${WAIT}s 后重试..."
        sleep $WAIT
    fi
done

echo ""
echo "❌ 推送失败，已重试 $MAX_RETRIES 次。可能原因："
echo "   1. 网络问题 — 尝试打开 VPN/代理后手动执行 git push"
echo "   2. 如果持续失败 — 切换为 SSH: git remote set-url origin git@github.com:jiang-yu-24/cosco-shipping-ai-agent.git"
exit 1
