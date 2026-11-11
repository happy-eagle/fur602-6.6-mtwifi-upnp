#!/usr/bin/env bash
# 用法: ./push-to-github.sh https://github.com/<user>/<repo>.git
set -euo pipefail
REPO="${1:-}"
if [ -z "$REPO" ]; then
  echo "用法: ./push-to-github.sh <空仓库的 git 地址>" >&2
  exit 1
fi
cd "$(dirname "$0")"
if [ ! -d .git ]; then git init -q; fi
git add -A
if git diff --cached --quiet; then
  echo "无变更，跳过提交"
else
  git commit -qm "FUR-602: ImmortalWrt 6.6 + mtwifi + UPnP cloud build"
fi
git branch -M main
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO"
echo "==> 推送到 $REPO （push 会自动触发 Actions 编译）"
git push -u origin main
echo "==> 完成。去仓库 Actions 页查看进度。"
