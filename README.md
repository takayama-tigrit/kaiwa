# 🎙️ kaiwa（会話）

**対面会話をAIで自動文字起こし・話者分離・要約するOSSツール**

Macの録音 or iPhoneのボイスメモから、話者分離付き文字起こし＋AI要約をMarkdownで自動生成します。

---

## ✨ 特徴

### Plaud Note Pro との違い

[Plaud Note Pro](https://jp.plaud.ai/) は高品質なAIボイスレコーダーで、専用ハードウェア・4つのMEMSマイク・GPT-5.1ベースの要約など、**完成度の高いオールインワン体験**を提供しています。

kaiwa は、そんな Plaud Note Pro のような体験を**初期投資ゼロ・低ランニングコスト**で実現したい人のためのOSSツールです。

| | Plaud Note Pro | kaiwa |
|---|---|---|
| **初期費用** | ¥27,500〜（専用デバイス） | 無料（Mac + マイクで動作） |
| **ランニングコスト** | スタータープラン無料（月300分）/ プロプラン 年16,800円 | Claude API 従量課金のみ（〜¥5/回） |
| **手軽さ** | ◎ ボタン一つで録音→自動要約 | △ 初期セットアップが必要 |
| **録音品質** | ◎ 専用マイク4基、5m収音 | Mac/iPhoneのマイク依存 |
| **文字起こし** | クラウド（GPT-5.1） | ローカル（WhisperX） |
| **話者分離** | ○ | ○（pyannote.audio） |
| **要約** | ◎ 10,000+テンプレート、多角的要約 | カスタマイズ自由（Claude） |
| **データ管理** | クラウド（ISO 27001/GDPR準拠） | 完全ローカル |
| **カスタマイズ** | テンプレート選択・用語集登録 | プロンプト・モデル等フルコントロール |

> 💡 **kaiwa はこんな人向け**: 手持ちのMacとマイクで、サブスクなしで文字起こし+要約がしたい人。Plaud Note Pro は完成度と手軽さで圧倒的なので、予算があるなら素直にそちらがおすすめです。

## 📄 出力例

```markdown
# 会話メモ — 2026-02-02 15:00

## 📋 要約
- プロジェクトXの進捗を共有。設計フェーズ完了、実装に着手予定
- **決定事項**: デザインはA案で進行
- **TODO**: 田中さん → API設計書を金曜までに共有

## 💬 全文（話者分離済み）
[00:00 → 00:15] SPEAKER_00: それでは始めましょうか。プロジェクトXの進捗について...
[00:15 → 00:32] SPEAKER_01: はい、設計フェーズは予定通り完了しました。
```

## 🚀 クイックスタート

### 必要環境
- macOS (Apple Silicon 推奨)
- Python 3.10+
- Homebrew

### インストール

```bash
git clone https://github.com/takayama-tigrit/kaiwa.git
cd kaiwa
./setup.sh
```

### 初期設定

HuggingFace トークンと Anthropic API キーを macOS Keychain に登録します。

```bash
security add-generic-password -a kaiwa -s hf-token -w 'hf_YOUR_TOKEN'
security add-generic-password -a kaiwa -s anthropic-api-key -w 'sk-ant-YOUR_KEY'
```

> 📖 詳細な手順（HFアカウント作成、モデルライセンス同意）: [docs/SETUP.md](docs/SETUP.md)

## 🎤 使い方

### ホットキーで録音（Mac）

ホットキーを押すだけで録音開始/停止。停止後に自動で文字起こし＋要約。

1. ホットキーを設定（3つの方法から選択）
2. ホットキー → 🔴 録音開始
3. もう一度 → ⏹ 停止 → 自動処理 → Markdown出力

> 📖 ホットキーの設定方法: [docs/HOTKEY.md](docs/HOTKEY.md)

### コマンドラインで処理

```bash
PYTHONPATH=./src ~/.kaiwa/venv/bin/python -m kaiwa.cli process recording.wav
```

### iPhone連携

iPhoneで録音 → クラウドストレージ経由で Mac に自動同期 → 自動処理。iCloud / Google Drive / Dropbox に対応。

```bash
./scripts/install-daemon.sh  # 監視デーモン有効化
```

> 📖 詳細な設定: [docs/CONFIGURATION.md](docs/CONFIGURATION.md#iphone--スマホ連携クラウドストレージ監視)

## ⚙️ 設定

設定ファイル `~/.kaiwa/config.yaml` で、モデル、保存先、クラウドストレージ連携などをカスタマイズできます。

> 📖 設定リファレンス: [docs/CONFIGURATION.md](docs/CONFIGURATION.md)

主な設定項目:
- **保存先の変更** — Google Drive や任意のフォルダに出力可能
- **クラウドストレージ監視** — iCloud / Google Drive / Dropbox
- **モデル / 言語** — WhisperX のモデルや言語を変更
- **要約 AI** — Claude のモデルやリトライ回数

## 📖 ドキュメント

| ドキュメント | 内容 |
|------------|------|
| [SETUP.md](docs/SETUP.md) | インストール・初期設定の詳細 |
| [HOTKEY.md](docs/HOTKEY.md) | ホットキー設定（Raycast / ショートカット / Automator） |
| [CONFIGURATION.md](docs/CONFIGURATION.md) | 設定ファイルの全リファレンス |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | システム設計・データフロー |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | よくある問題と解決策 |

## 🤝 コントリビュート

PRやIssueを歓迎しています！詳細は [CONTRIBUTING.md](CONTRIBUTING.md) をご覧ください。

## 📄 ライセンス

[MIT License](LICENSE) — Copyright (c) 2026 takayama-tigrit

サードパーティライセンスの詳細: [NOTICE.md](NOTICE.md)

## 🙏 謝辞

- [WhisperX](https://github.com/m-bain/whisperX) — 高精度な文字起こし + 話者分離統合
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) — 話者分離エンジン
- [Anthropic Claude](https://www.anthropic.com/) — AI 要約
- [sox](https://sox.sourceforge.net/) — 録音
- [fswatch](https://github.com/emcrisostomo/fswatch) — ファイル監視
