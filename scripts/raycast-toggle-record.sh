#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title kaiwa 録音トグル
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 🎙️
# @raycast.packageName kaiwa

# Documentation:
# @raycast.description 対面会話の録音を開始/停止する。停止時に自動で文字起こし＋要約。

# 本体スクリプトを呼び出す
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/toggle-record.sh"
