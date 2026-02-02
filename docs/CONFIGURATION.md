# ⚙️ 設定リファレンス

設定ファイル: `~/.kaiwa/config.yaml`

設定ファイルがない場合はデフォルト値が使用されます。

## config.yaml 全項目

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
  watch_dirs:
    - ~/Library/Mobile Documents/com~apple~CloudDocs/Transcripts/raw  # iCloud Drive
    # - ~/Library/CloudStorage/GoogleDrive-yourname@gmail.com/マイドライブ/Transcripts/raw  # Google Drive
    # - ~/Dropbox/Transcripts/raw  # Dropbox
```

## 保存先の変更

デフォルトでは `~/Transcripts/` にすべてのファイルが保存されます。
`~/.kaiwa/config.yaml` の `paths` セクションで保存先を自由に変更できます。

| 設定キー | 保存されるもの | デフォルト |
|---------|--------------|-----------|
| `output` | **要約 Markdown** ← 最終成果物 | `~/Transcripts/` |
| `raw` | 録音ファイル（.wav） | `~/Transcripts/raw/` |
| `work` | 中間成果物（文字起こし JSON 等） | `~/Transcripts/work/` |

**例: Google Drive に保存する場合**

```yaml
paths:
  output: ~/Library/CloudStorage/GoogleDrive-you@gmail.com/マイドライブ/Transcripts
  raw: ~/Library/CloudStorage/GoogleDrive-you@gmail.com/マイドライブ/Transcripts/raw
  work: ~/Library/CloudStorage/GoogleDrive-you@gmail.com/マイドライブ/Transcripts/work
```

> これで要約 Markdown、録音ファイル、中間成果物がすべて Google Drive に保存され、他のデバイスからも閲覧できます。

**Google Drive のパス確認方法：**
1. Finder で Google Drive フォルダを開く
2. フォルダを右クリック →「情報を見る」
3. 「場所」のパスを確認（`~/Library/CloudStorage/GoogleDrive-...` の形式）

> 💡 `paths.raw` を変更すると、録音トグル（ホットキー）の保存先も自動的に変わります。

## iPhone / スマホ連携（クラウドストレージ監視）

> これは**外部デバイスからの音声ファイルの自動取り込み**設定です。要約ファイルの保存先を変更するには上の「[保存先の変更](#保存先の変更)」を参照してください。

iCloud Drive だけでなく、**Google Drive** や **Dropbox** 経由でも自動処理できます。

`~/.kaiwa/config.yaml` の `watch_dirs` にクラウドストレージのパスを追加してください：

```yaml
paths:
  watch_dirs:
    # iCloud Drive
    - ~/Library/Mobile Documents/com~apple~CloudDocs/Transcripts/raw

    # Google Drive（Google Drive for Desktop が必要）
    - ~/Library/CloudStorage/GoogleDrive-あなたのメール@gmail.com/マイドライブ/Transcripts/raw

    # Dropbox
    - ~/Dropbox/Transcripts/raw
```

**Google Drive のパス確認方法：**
1. Finder で Google Drive フォルダを開く
2. 任意のファイルを右クリック → 「情報を見る」
3. 「場所」に表示されるパスを確認

> 💡 `watch_dirs` を変更したら、監視デーモンを再起動してください：
> ```bash
> ./scripts/install-daemon.sh --uninstall
> ./scripts/install-daemon.sh
> ```

## 監視デーモンの管理

```bash
# デーモンの有効化
./scripts/install-daemon.sh

# デーモンの無効化
./scripts/install-daemon.sh --uninstall
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
