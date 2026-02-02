#!/bin/bash
# kaiwa — LaunchAgent インストール/アンインストール
#
# 使い方:
#   ./install-daemon.sh              # インストール
#   ./install-daemon.sh --uninstall  # アンインストール

set -euo pipefail

PLIST_NAME="jp.tigrit.kaiwa.watch"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$PLIST_DIR/$PLIST_NAME.plist"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WATCH_SCRIPT="$SCRIPT_DIR/watch-recordings.sh"
LOG_DIR="$HOME/.kaiwa/logs"

mkdir -p "$LOG_DIR"

# ── アンインストール ──

if [[ "${1:-}" == "--uninstall" ]]; then
    echo "🗑️  LaunchAgent をアンインストールします..."

    if launchctl list | grep -q "$PLIST_NAME"; then
        launchctl unload "$PLIST_FILE" 2>/dev/null || true
        echo "  ✅ アンロード完了"
    fi

    if [ -f "$PLIST_FILE" ]; then
        rm "$PLIST_FILE"
        echo "  ✅ plist 削除完了"
    fi

    echo "🎉 アンインストール完了"
    exit 0
fi

# ── インストール ──

echo "📦 LaunchAgent をインストールします..."

# watch-recordings.sh が存在するか確認
if [ ! -f "$WATCH_SCRIPT" ]; then
    echo "❌ watch-recordings.sh が見つかりません: $WATCH_SCRIPT"
    exit 1
fi

# 既存の plist をアンロード
if launchctl list | grep -q "$PLIST_NAME"; then
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
fi

# plist 生成
mkdir -p "$PLIST_DIR"
cat > "$PLIST_FILE" <<PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$WATCH_SCRIPT</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/watch-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/watch-stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
PLIST_EOF

echo "  ✅ plist 生成完了: $PLIST_FILE"

# ロード
launchctl load "$PLIST_FILE"
echo "  ✅ LaunchAgent ロード完了"

echo ""
echo "🎉 インストール完了！"
echo "   状態確認: launchctl list | grep kaiwa"
echo "   アンインストール: $0 --uninstall"
