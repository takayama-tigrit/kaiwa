# アーキテクチャ

## システム全体図

```
┌─────────────────────────────────────────────────────────────────┐
│                        kaiwa システム                           │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  Mac 録音     │    │  iPhone 録音  │    │  手動ファイル     │  │
│  │  (sox)        │    │  (ボイスメモ)  │    │  指定            │  │
│  └──────┬───────┘    └──────┬───────┘    └────────┬─────────┘  │
│         │                   │                      │            │
│         ▼                   ▼                      │            │
│  ~/Transcripts/raw   iCloud Drive 同期             │            │
│         │                   │                      │            │
│         │            ┌──────┴───────┐              │            │
│         │            │  fswatch     │              │            │
│         │            │  監視デーモン  │              │            │
│         │            └──────┬───────┘              │            │
│         │                   │                      │            │
│         ▼                   ▼                      ▼            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    kaiwa CLI                              │  │
│  │              python -m kaiwa.cli process                  │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                              │                                  │
│         ┌────────────────────┼────────────────────┐            │
│         ▼                    ▼                    ▼            │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────┐   │
│  │  Step 1       │   │  Step 2-3     │   │  Step 4           │   │
│  │  faster-      │   │  pyannote     │   │  Claude API       │   │
│  │  whisper      │   │  話者分離      │   │  要約生成          │   │
│  │  + word_ts    │   │  + 再分割     │   │  (リトライ付き)    │   │
│  └──────┬──────┘   └──────┬───────┘   └────────┬─────────┘   │
│         │                  │                     │             │
│         ▼                  ▼                     ▼             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Step 5: Markdown 出力                   │  │
│  │                  ~/Transcripts/YYYY-MM-DD_HHMMSS.md       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  中間成果物: ~/Transcripts/work/<recording_stem>/         │  │
│  │    01_transcribe.json → 03_diarize_raw.json              │  │
│  │                       → 03_diarize.json (再分割後)        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## コンポーネント一覧

| コンポーネント | ファイル | 役割 |
|---------------|---------|------|
| CLI | `src/kaiwa/cli.py` | エントリポイント。argparse でサブコマンドを管理 |
| 設定 | `src/kaiwa/config.py` | `~/.kaiwa/config.yaml` の読み込み + デフォルト値マージ |
| 文字起こし | `src/kaiwa/transcribe.py` | faster-whisper による音声→テキスト変換（native word_timestamps） |
| 話者分離 | `src/kaiwa/diarize.py` | pyannote.audio による話者識別 + セグメント再分割 |
| 要約 | `src/kaiwa/summarize.py` | Anthropic SDK を使った Claude 要約（リトライ付き） |
| 出力 | `src/kaiwa/output.py` | Markdown ファイル生成 |
| ユーティリティ | `src/kaiwa/utils.py` | ログ、通知、Keychain、音声検証 |
| 録音トグル | `scripts/toggle-record.sh` | sox による録音の開始/停止 |
| フォルダ監視 | `scripts/watch-recordings.sh` | fswatch による iCloud フォルダ監視 |
| Raycast 連携 | `scripts/raycast-toggle-record.sh` | Raycast Script Command ラッパー |
| デーモン管理 | `scripts/install-daemon.sh` | launchd plist の生成・登録 |

## データフロー

```
音声ファイル (.wav)
    ↓
[検証] サイズ ≥ 1KB, 長さ ≥ 1秒
    ↓
[faster-whisper] 文字起こし + word_timestamps → 01_transcribe.json
    ↓
[pyannote] 話者分離 → 03_diarize_raw.json
    ↓
[セグメント再分割] 話者交代ポイントで分割 → 03_diarize.json
    ↓
[Claude] 要約生成（オプション）
    ↓
[出力] Markdown ファイル → ~/Transcripts/YYYYMMDD_タイトル.md
```

### 2つの文字起こしモード

| | native mode（デフォルト） | whisperx mode |
|---|---|---|
| **エンジン** | faster-whisper 直接 | WhisperX バッチパイプライン |
| **word timestamps** | ✅ cross-attention ベース | wav2vec2 アラインメント |
| **日本語精度** | ◎ トークン単位で安定 | △ 文字レベルで不正確 |
| **処理方式** | シーケンシャル | バッチ（並列処理） |
| **設定** | `use_native_word_timestamps: true` | `use_native_word_timestamps: false` |

## 設計判断

### なぜ faster-whisper 直接モード？（v0.1.0〜）

- WhisperX のバッチパイプラインは `word_timestamps` に非対応（テキストのみ返却）
- WhisperX の wav2vec2 アラインメントは日本語の文字レベルで精度が壊滅的
  - 例: 1文字「今」に26秒分のタイムスタンプが割り当てられ、残り全文字が0.5秒に圧縮される
- faster-whisper の cross-attention ベース word_timestamps はトークン単位で動作し、日本語でも安定
- `large-v3-turbo` モデルは精度とパフォーマンスのバランスが良い

### なぜ CPU？

- **CTranslate2 が MPS (Metal Performance Shaders) 非対応**
- Apple Silicon の CPU でも実用的な速度で動作する（10分の会話で約3-5分）
- GPU 対応は CTranslate2 の MPS サポート待ち

### なぜ Keychain？

- API キーを平文ファイルに保存するのはセキュリティリスク
- macOS Keychain は OS レベルの暗号化ストレージ
- `security` コマンドでプログラムからアクセス可能
- 環境変数よりも安全（プロセスリストに漏洩しない）

### なぜ中間成果物を保存するか？

- 処理パイプラインの途中で失敗しても、完了済みステップの結果は残る
- デバッグ時に各ステップの出力を個別に確認できる
- 再実行時に途中からの再開を可能にする（将来的な拡張）

### なぜ Anthropic SDK？

- `urllib.request` より型安全でエラーハンドリングが充実
- リトライロジックが明確に書ける（`RateLimitError`, `InternalServerError` 等）
- ストリーミング等の将来的な拡張にも対応

### なぜ処理済みログを永続化するか？

- `$TMPDIR` はシステム再起動で消える → 同じファイルを二重処理してしまう
- `~/.kaiwa/processed.log` なら永続的に記録される
- 100 行を超えたら 50 行にローテーションしてファイル肥大化を防ぐ
