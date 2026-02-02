# 🎙️ kaiwa（会話）

**対面会話をAIで自動文字起こし・話者分離・要約するOSSツール**

Macの録音 or iPhoneのボイスメモから、話者分離付き文字起こし＋AI要約をMarkdownで自動生成します。

---

## ✨ 特徴

| | Plaud Note Pro | kaiwa |
|---|---|---|
| **初期費用** | ¥25,900（デバイス） | 無料 |
| **月額** | ¥900/月（AI要約） | Claude API 従量課金のみ（〜¥5/回） |
| **文字起こし** | クラウド処理 | ローカル処理（WhisperX） |
| **話者分離** | ○ | ○（pyannote.audio） |
| **要約** | 定型テンプレート | カスタマイズ自由（Claude） |
| **データ管理** | クラウド | 完全ローカル |
| **カスタマイズ** | ✕ | フルコントロール |

## 📄 デモ — 出力例

```markdown
# 会話メモ — 2026-02-02 15:00

## 📋 要約

- プロジェクトXの進捗を共有。設計フェーズ完了、実装に着手予定
- 来週水曜にクライアントレビュー予定
- **決定事項**: デザインはA案で進行
- **TODO**: 田中さん → API設計書を金曜までに共有

## 💬 全文（話者分離済み）

[00:00 → 00:15] SPEAKER_00: それでは始めましょうか。プロジェクトXの進捗について...
[00:15 → 00:32] SPEAKER_01: はい、設計フェーズは予定通り完了しました。
[00:32 → 00:48] SPEAKER_00: 素晴らしいですね。クライアントレビューはいつ頃...
```

## 🖥️ 必要環境

- **macOS** (Apple Silicon 推奨 — Intel でも動作します)
- **Python 3.10+**
- **Homebrew**
- **約 4GB** のストレージ（WhisperX モデル用）

## 📦 インストール

```bash
# リポジトリをクローン
git clone https://github.com/takayama-tigrit/kaiwa.git
cd kaiwa

# セットアップ（依存関係インストール + venv 作成）
chmod +x setup.sh
./setup.sh
```

`setup.sh` が行うこと：
- `sox`, `fswatch` のインストール（Homebrew）
- `~/.kaiwa/venv` に Python 仮想環境を作成
- WhisperX, Anthropic SDK, PyYAML をインストール
- `~/.kaiwa/config.yaml` をコピー
- 必要なディレクトリを作成

## ⚙️ 初期設定

### 1. HuggingFace トークン（必須）

話者分離に [pyannote.audio](https://github.com/pyannote/pyannote-audio) を使用します。以下のモデルの利用規約に同意してください：

- [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
- [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)

トークンを Keychain に保存：

```bash
security add-generic-password -a kaiwa -s hf-token -w 'hf_YOUR_TOKEN'
```

### 2. Anthropic API キー（オプション — 要約機能に必要）

```bash
security add-generic-password -a kaiwa -s anthropic-api-key -w 'sk-ant-YOUR_KEY'
```

> 💡 API キーは macOS Keychain に暗号化して保存されます。環境変数や平文ファイルには保存しません。

## 🚀 使い方

### Mac で録音してそのまま処理（ホットキー）

1. Raycast に `scripts/` フォルダを Script Commands として登録
2. ホットキーで「kaiwa 録音トグル」を実行
3. もう一度押すと録音停止 → 自動的に処理開始
4. 完了すると macOS 通知でお知らせ

### 手動で処理（CLI）

```bash
# 音声ファイルを処理
PYTHONPATH=/path/to/kaiwa/src ~/.kaiwa/venv/bin/python -m kaiwa.cli process recording.wav

# バージョン表示
PYTHONPATH=/path/to/kaiwa/src ~/.kaiwa/venv/bin/python -m kaiwa.cli version
```

### iPhone 連携（iCloud 自動処理）

1. iPhone のボイスメモを iCloud Drive の `Transcripts/raw/` に保存
2. `install-daemon.sh` で監視デーモンを有効化
3. ファイルが同期されると自動的に処理開始

```bash
# デーモンの有効化
./scripts/install-daemon.sh

# デーモンの無効化
./scripts/install-daemon.sh --uninstall
```

## 🔧 設定

設定ファイル: `~/.kaiwa/config.yaml`

```yaml
whisper:
  model: large-v3-turbo     # WhisperX モデル
  device: cpu                # cpu のみ対応（MPS 非対応）
  compute_type: float32
  language: ja
  batch_size: 8

claude:
  model: claude-3-5-haiku-latest
  max_tokens: 2048
  timeout: 120
  max_retries: 3             # API リトライ回数

paths:
  output: ~/Transcripts      # Markdown 出力先
  raw: ~/Transcripts/raw     # 録音ファイル保存先
  work: ~/Transcripts/work   # 中間成果物保存先
  icloud_watch: ~/Library/Mobile Documents/com~apple~CloudDocs/Transcripts/raw
```

設定ファイルがない場合はデフォルト値が使用されます。

## 🏗️ アーキテクチャ

```
音声ファイル → [検証] → [WhisperX 文字起こし] → [アラインメント]
    → [話者分離] → [Claude 要約] → [Markdown 出力]
```

各ステップの中間成果物は `~/Transcripts/work/<recording_stem>/` に保存されます。処理が途中で失敗しても、完了済みステップの結果は残ります。

詳細: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## ❓ トラブルシューティング

よくある問題と解決策: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

**クイックチェック:**

```bash
# Keychain の確認
security find-generic-password -a kaiwa -s hf-token -w
security find-generic-password -a kaiwa -s anthropic-api-key -w

# ログの確認
cat ~/.kaiwa/logs/$(date +%Y-%m-%d).log

# 中間成果物の確認
ls ~/Transcripts/work/
```

## 📁 ディレクトリ構成

```
~/.kaiwa/
├── config.yaml       # 設定ファイル
├── venv/             # Python 仮想環境
├── logs/             # ログファイル（日次）
├── processed.log     # 処理済みファイル記録
├── recording.pid     # 録音プロセス PID
└── current_recording.txt

~/Transcripts/
├── *.md              # 出力 Markdown
├── raw/              # 録音ファイル
└── work/             # 中間成果物
    └── <recording_stem>/
        ├── 01_transcribe.json
        ├── 02_align.json
        └── 03_diarize.json
```

## 📄 ライセンス

[MIT License](LICENSE) — Copyright (c) 2026 takayama-tigrit

## 🙏 謝辞

- [WhisperX](https://github.com/m-bain/whisperX) — 高精度な文字起こし + 話者分離統合
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) — 話者分離エンジン
- [Anthropic Claude](https://www.anthropic.com/) — AI 要約
- [sox](https://sox.sourceforge.net/) — 録音
- [fswatch](https://github.com/emcrisostomo/fswatch) — ファイル監視
