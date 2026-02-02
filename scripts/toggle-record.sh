#!/bin/bash
# kaiwa — 録音トグルスクリプト
#
# 録音の開始/停止を制御する。停止時には自動的に処理パイプラインを起動する。
# PID 管理を改善: kill -0 確認 → kill -INT → 最大10秒待機 → 強制終了

set -euo pipefail

# Homebrew PATH（Apple Silicon）
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# ── 設定 ──
KAIWA_DIR="$HOME/.kaiwa"
PID_FILE="$KAIWA_DIR/recording.pid"
CURRENT_FILE="$KAIWA_DIR/current_recording.txt"
VENV_PYTHON="$KAIWA_DIR/venv/bin/python"
KAIWA_SRC="$(cd "$(dirname "$0")/.." && pwd)/src"

# config.yaml から raw path を取得
RAW_PATH="$HOME/Transcripts/raw"  # デフォルト
if [ -f "$KAIWA_DIR/config.yaml" ]; then
    _raw=$(grep "^  raw:" "$KAIWA_DIR/config.yaml" 2>/dev/null | sed 's/^  raw: *//' | sed 's/#.*//' | xargs)
    if [ -n "$_raw" ]; then
        RAW_PATH="${_raw/#\~/$HOME}"
    fi
fi
OUTPUT_DIR="$RAW_PATH"

mkdir -p "$KAIWA_DIR" "$OUTPUT_DIR"

# ── ヘルパー関数 ──

notify() {
    osascript <<KAIWA_NOTIFY_EOF
display notification "$2" with title "$1"
KAIWA_NOTIFY_EOF
}

stop_recording() {
    local pid="$1"
    local waited=0
    local max_wait=10

    # kill -0 でプロセス存在確認
    if ! kill -0 "$pid" 2>/dev/null; then
        echo "⚠️  PID $pid はすでに終了しています"
        rm -f "$PID_FILE"
        return 0
    fi

    # INT シグナルで停止要求
    kill -INT "$pid" 2>/dev/null

    # 最大10秒待機
    while [ $waited -lt $max_wait ]; do
        if ! kill -0 "$pid" 2>/dev/null; then
            echo "✅ 録音プロセス (PID $pid) が正常終了しました"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done

    # タイムアウト → 強制終了
    echo "⚠️  タイムアウト — SIGKILL で強制終了"
    kill -KILL "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
    return 0
}

# ── メイン処理 ──

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")

    # 録音中 → 停止
    stop_recording "$PID"

    notify "⏹ kaiwa" "録音を停止しました。処理を開始します..."
    afplay /System/Library/Sounds/Pop.aiff &

    # 処理パイプライン起動
    if [ -f "$CURRENT_FILE" ]; then
        RECORDING_FILE=$(cat "$CURRENT_FILE")
        if [ -f "$RECORDING_FILE" ]; then
            PYTHONPATH="$KAIWA_SRC" nohup "$VENV_PYTHON" -m kaiwa.cli process "$RECORDING_FILE" > /dev/null 2>&1 &
        else
            notify "kaiwa ⚠️" "録音ファイルが見つかりません: $RECORDING_FILE"
        fi
    fi
else
    # 停止中 → 録音開始
    FILENAME="$OUTPUT_DIR/recording_$(date +%Y%m%d_%H%M%S).wav"
    echo "$FILENAME" > "$CURRENT_FILE"

    nohup sox -d -r 16000 -c 1 -b 16 "$FILENAME" > /dev/null 2>&1 &
    echo $! > "$PID_FILE"

    notify "🔴 kaiwa" "録音を開始しました"
    afplay /System/Library/Sounds/Tink.aiff &
fi
