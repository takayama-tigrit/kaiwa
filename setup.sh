#!/bin/bash
# kaiwa — ワンコマンドセットアップ
#
# 必要な依存関係のインストール、venv 作成、ディレクトリ構成を行う。

set -euo pipefail

echo "🎙️  kaiwa セットアップ"
echo "=========================="
echo ""

# ── 前提条件チェック ──

# Homebrew
if ! command -v brew &>/dev/null; then
    echo "❌ Homebrew がインストールされていません"
    echo "   インストール: https://brew.sh/"
    exit 1
fi
echo "✅ Homebrew: $(brew --version | head -1)"

# Python 3
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3 がインストールされていません"
    echo "   インストール: brew install python@3.13"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo "✅ Python: $PYTHON_VERSION"

# Python バージョンチェック（3.10+）
PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
if [ "$PYTHON_MINOR" -lt 10 ]; then
    echo "❌ Python 3.10 以上が必要です（現在: $PYTHON_VERSION）"
    exit 1
fi

# ── Homebrew パッケージ ──

echo ""
echo "📦 Homebrew パッケージをインストール..."

for pkg in sox fswatch; do
    if brew list "$pkg" &>/dev/null; then
        echo "  ✅ $pkg: インストール済み"
    else
        echo "  📥 $pkg をインストール中..."
        brew install "$pkg"
    fi
done

# ── ディレクトリ作成 ──

echo ""
echo "📁 ディレクトリを作成..."

KAIWA_DIR="$HOME/.kaiwa"
TRANSCRIPT_DIR="$HOME/Transcripts"

mkdir -p "$KAIWA_DIR/logs"
mkdir -p "$TRANSCRIPT_DIR/raw"
mkdir -p "$TRANSCRIPT_DIR/work"

echo "  ✅ $KAIWA_DIR"
echo "  ✅ $KAIWA_DIR/logs"
echo "  ✅ $TRANSCRIPT_DIR/raw"
echo "  ✅ $TRANSCRIPT_DIR/work"

# ── Python venv ──

echo ""
VENV_DIR="$KAIWA_DIR/venv"

if [ -d "$VENV_DIR" ]; then
    echo "✅ venv: 既に存在 ($VENV_DIR)"
else
    echo "🐍 Python venv を作成中..."
    python3 -m venv "$VENV_DIR"
    echo "  ✅ venv 作成完了: $VENV_DIR"
fi

# pip で依存関係インストール
echo ""
echo "📦 Python パッケージをインストール..."
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install whisperx anthropic pyyaml -q
echo "  ✅ パッケージインストール完了"

# ── 設定ファイル ──

echo ""
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$KAIWA_DIR/config.yaml"

if [ -f "$CONFIG_FILE" ]; then
    echo "✅ 設定ファイル: 既に存在 ($CONFIG_FILE)"
else
    cp "$SCRIPT_DIR/config.example.yaml" "$CONFIG_FILE"
    echo "✅ 設定ファイルをコピー: $CONFIG_FILE"
fi

# ── スクリプト実行権限 ──

echo ""
echo "🔧 スクリプトに実行権限を付与..."
chmod +x "$SCRIPT_DIR/scripts/"*.sh 2>/dev/null || true
echo "  ✅ 完了"

# ── 完了メッセージ ──

echo ""
echo "=========================================="
echo "🎉 セットアップ完了！"
echo "=========================================="
echo ""
echo "📋 次のステップ（手動設定が必要）:"
echo ""
echo "1. HuggingFace トークンを Keychain に保存:"
echo "   security add-generic-password -a kaiwa -s hf-token -w 'YOUR_HF_TOKEN'"
echo ""
echo "   ※ pyannote.audio の利用規約に同意が必要:"
echo "     https://huggingface.co/pyannote/speaker-diarization-3.1"
echo "     https://huggingface.co/pyannote/segmentation-3.0"
echo ""
echo "2. Anthropic API キーを Keychain に保存（要約機能を使う場合）:"
echo "   security add-generic-password -a kaiwa -s anthropic-api-key -w 'YOUR_API_KEY'"
echo ""
echo "3. テスト実行:"
echo "   PYTHONPATH=$SCRIPT_DIR/src $VENV_DIR/bin/python -m kaiwa.cli process <WAVファイル>"
echo ""
echo "4. Raycast Script Command に登録（オプション）:"
echo "   Raycast → Script Commands → Add Script Directory → $SCRIPT_DIR/scripts/"
echo ""
echo "5. iCloud 監視デーモンを有効化（オプション）:"
echo "   $SCRIPT_DIR/scripts/install-daemon.sh"
echo ""
