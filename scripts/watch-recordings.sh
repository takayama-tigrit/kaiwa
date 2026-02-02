#!/bin/bash
# kaiwa — iCloud フォルダ監視スクリプト
#
# iCloud Drive の録音フォルダを監視し、新しい WAV ファイルを検出したら
# 自動的に処理パイプラインを起動する。
#
# 処理済みログは ~/.kaiwa/processed.log に永続化し、
# 100 行を超えたら 50 行にローテーションする。

set -euo pipefail

# Homebrew PATH（Apple Silicon）
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# ── 設定 ──
KAIWA_DIR="$HOME/.kaiwa"
WATCH_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Transcripts/raw"
VENV_PYTHON="$KAIWA_DIR/venv/bin/python"
KAIWA_SRC="$(cd "$(dirname "$0")/.." && pwd)/src"
PROCESSED_LOG="$KAIWA_DIR/processed.log"

mkdir -p "$KAIWA_DIR" "$WATCH_DIR"
touch "$PROCESSED_LOG"

# ── ヘルパー関数 ──

notify() {
    osascript <<KAIWA_NOTIFY_EOF
display notification "$2" with title "$1"
KAIWA_NOTIFY_EOF
}

rotate_log() {
    local line_count
    line_count=$(wc -l < "$PROCESSED_LOG")
    if [ "$line_count" -gt 100 ]; then
        echo "🔄 処理済みログをローテーション ($line_count → 50行)"
        tail -50 "$PROCESSED_LOG" > "$PROCESSED_LOG.tmp"
        mv "$PROCESSED_LOG.tmp" "$PROCESSED_LOG"
    fi
}

wait_for_sync() {
    local file="$1"
    local prev_size=0
    local attempts=0
    local max_attempts=60

    while [ $attempts -lt $max_attempts ]; do
        # iCloud プレースホルダーファイルが存在する場合は待機
        local icloud_file
        icloud_file="$(dirname "$file")/.$(basename "$file").icloud"
        if [ -f "$icloud_file" ]; then
            sleep 2
            attempts=$((attempts + 1))
            continue
        fi

        local curr_size
        curr_size=$(stat -f%z "$file" 2>/dev/null || echo 0)
        if [[ "$curr_size" -gt 0 && "$curr_size" -eq "$prev_size" ]]; then
            return 0
        fi
        prev_size=$curr_size
        sleep 2
        attempts=$((attempts + 1))
    done

    echo "⚠️ 同期タイムアウト: $file"
    return 1
}

# ── メイン処理 ──

echo "👀 kaiwa — フォルダ監視開始: $WATCH_DIR"
notify "kaiwa" "フォルダ監視を開始しました"

fswatch -0 --event Created "$WATCH_DIR" | while read -d "" event; do
    if [[ "$event" == *.wav || "$event" == *.aiff || "$event" == *.mp3 ]]; then
        # 重複チェック
        if grep -qF "$event" "$PROCESSED_LOG" 2>/dev/null; then
            continue
        fi

        echo "$event" >> "$PROCESSED_LOG"
        echo "🎤 新しい録音を検出: $event"
        notify "kaiwa" "新しい録音を検出: $(basename "$event")"

        # ログローテーション
        rotate_log

        # iCloud 同期完了を待つ
        if wait_for_sync "$event"; then
            PYTHONPATH="$KAIWA_SRC" "$VENV_PYTHON" -m kaiwa.cli process "$event" &
        else
            notify "kaiwa ⚠️" "同期タイムアウト: $(basename "$event")"
        fi
    fi
done
