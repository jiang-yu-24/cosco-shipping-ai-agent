#!/bin/bash
# ==============================================================
# 一键提交 & 推送脚本
# 用法：
#   ./git_push.sh "提交信息"
#   ./git_push.sh          （不传参数则自动生成带时间戳的信息）
# ==============================================================

set -e

cd "$(dirname "$0")"

# 检查是否有变更（含未跟踪文件）
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    echo "📭 没有需要提交的变更"
    exit 0
fi

# 提交信息：优先使用参数，否则自动生成
if [ -n "$1" ]; then
    MSG="$1"
else
    MSG="更新 $(date '+%Y-%m-%d %H:%M')"
fi

echo "📦 正在提交: $MSG"
git add -A
git commit -m "$MSG"
git push

echo "✅ 提交并推送完成"
