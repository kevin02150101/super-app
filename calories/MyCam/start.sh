#!/usr/bin/env bash
# MyCam 一鍵啟動腳本
# 用法：bash start.sh
#       PORT=8080 bash start.sh    （自訂 port）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── 1. 建立虛擬環境（若尚未存在）────────────────────────
if [ ! -f ".venv/bin/activate" ]; then
    echo "[MyCam] 建立虛擬環境 .venv ..."
    python3 -m venv .venv
fi

# ── 2. 啟用虛擬環境 ─────────────────────────────────────
source .venv/bin/activate

# ── 3. 安裝 / 更新依賴套件 ──────────────────────────────
if [ -f "requirements.txt" ]; then
    echo "[MyCam] 確認套件是否最新 ..."
    pip install -q -r requirements.txt
fi

# ── 4. 建立 .env（若尚未存在）──────────────────────────
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo "[MyCam] 已從 .env.example 複製 .env，請填入真實的 GEMINI_API_KEY"
fi

# ── 5. 釋放佔用的 port（若有）──────────────────────────
PORT="${PORT:-5001}"
OCCUPIED=$(lsof -ti tcp:"$PORT" 2>/dev/null || true)
if [ -n "$OCCUPIED" ]; then
    echo "[MyCam] Port $PORT 被佔用，正在釋放 ..."
    echo "$OCCUPIED" | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# ── 6. 啟動 Flask server ────────────────────────────────
echo "[MyCam] 啟動 http://127.0.0.1:${PORT}"
export PORT
python run.py
