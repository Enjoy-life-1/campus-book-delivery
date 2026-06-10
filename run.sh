#!/usr/bin/env bash
# 开发模式：Flask :5000 + Vite :5173
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

command -v python3 >/dev/null || command -v python >/dev/null || { echo "需要 Python"; exit 1; }
command -v node >/dev/null || { echo "需要 Node.js"; exit 1; }

PY="$(command -v python3 2>/dev/null || command -v python)"
[ -d node_modules ] || npm install --silent
[ -f .env ] || [ ! -f .env.example ] || cp .env.example .env

cleanup() { kill "$FLASK_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

echo "[INFO] 启动 Flask :5000 ..."
"$PY" app.py &
FLASK_PID=$!
sleep 1

echo "[INFO] 启动 Vite  :5173 ..."
echo "[INFO] 浏览器 http://localhost:5173"
echo "[INFO] 管理后台 http://localhost:5173/admin/login"
npm run dev
