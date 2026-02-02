# トラブルシューティング

## よくあるエラーと解決策

### 🔴 Critical

#### `torch.load` 関連のエラー

```
FutureWarning: You are using `torch.load` with `weights_only=False`
```

**原因**: PyTorch 2.8+ のデフォルト変更と pyannote の非互換性。

**解決策**: `transcribe.py` の冒頭でパッチが自動適用されます。もしエラーが出る場合は、パッチが正しく読み込まれているか確認してください。

---

#### HuggingFace トークンが見つからない

```
❌ HuggingFace トークンが見つかりません
```

**原因**: Keychain にトークンが登録されていない、または HuggingFace アカウントでモデルライセンスに同意していない。

**解決策**:

**1) Keychain にトークンを登録**
```bash
# トークンを登録
security add-generic-password -a kaiwa -s hf-token -w 'hf_YOUR_TOKEN'

# 確認
security find-generic-password -a kaiwa -s hf-token -w
```

**2) HuggingFace でモデルライセンスに同意**

pyannote.audio のモデルは利用規約への同意が必須です：
- https://huggingface.co/pyannote/speaker-diarization-3.1
- https://huggingface.co/pyannote/segmentation-3.0

各ページで「Agree and access repository」をクリックしてください。

**3) トークンのアクセス権限を確認**

HuggingFace のトークン設定で、以下の権限が必要です：
- Read access to contents of all repos

詳細: https://huggingface.co/settings/tokens

---

#### `DiarizationPipeline` が見つからない

```
AttributeError: module 'whisperx' has no attribute 'DiarizationPipeline'
```

**原因**: `whisperx.DiarizationPipeline` は存在しません。

**解決策**: kaiwa では `from whisperx.diarize import DiarizationPipeline` を使用しています。直接インポートパスを修正した場合はこの形式に合わせてください。

---

### 🟠 High

#### MPS 関連のエラー

```
RuntimeError: MPS backend is not supported
```

**原因**: CTranslate2 が Apple Silicon の MPS (Metal Performance Shaders) に非対応。

**解決策**: `config.yaml` の `whisper.device` を `cpu` に設定してください（デフォルトで `cpu` です）。

```yaml
whisper:
  device: cpu  # MPS は非対応
```

---

#### Claude API レート制限 (429)

```
⚠️ レート制限 (429)
```

**解決策**: kaiwa は自動的に指数バックオフでリトライします（最大3回）。頻繁に発生する場合は：

1. API の利用プランを確認（Free tier は制限が厳しい）
2. `config.yaml` の `claude.max_retries` を増やす
3. 処理の間隔を空ける

---

#### モデルダウンロードが失敗する

```
❌ モデルのロードに失敗: ConnectionError
```

**原因**:
1. ネットワーク接続の問題
2. HuggingFace API のレート制限
3. プロキシ設定の不備
4. ディスク容量不足

**解決策**:

**ネットワーク接続を確認**
```bash
# HuggingFace に接続できるか確認
curl -I https://huggingface.co
```

**プロキシ経由の場合**
```bash
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
./setup.sh
```

**ディスク容量を確認**
```bash
df -h ~
# WhisperX と pyannote のモデルは合計で約 5GB 必要
```

**キャッシュをクリアして再試行**
```bash
rm -rf ~/.cache/huggingface
rm -rf ~/.cache/torch
./setup.sh
```

---

#### ディスク容量不足

```
❌ ディスク容量不足
OSError: [Errno 28] No space left on device
```

**原因**: 出力ディレクトリまたはモデルキャッシュでディスクがフル。

**解決策**:

**1) 空き容量を確認**
```bash
df -h ~
df -h ~/Transcripts
```

**2) 不要なファイルを削除**
```bash
# 古い文字起こし結果を削除
rm -rf ~/Transcripts/*.md

# 中間ファイルを削除
rm -rf ~/Transcripts/work/*

# モデルキャッシュを削除（再ダウンロードが必要になります）
rm -rf ~/.cache/huggingface
rm -rf ~/.cache/torch
```

**3) 出力先を変更**

`~/.kaiwa/config.yaml` で出力先を外付けドライブや容量の大きいディレクトリに変更：
```yaml
paths:
  output: /Volumes/ExternalDrive/Transcripts
  work: /Volumes/ExternalDrive/Transcripts/work
```

---

#### sox が見つからない

```
sox: command not found
```

**解決策**:
```bash
brew install sox
```

---

#### fswatch が見つからない

```
fswatch: command not found
```

**解決策**:
```bash
brew install fswatch
```

---

#### Anthropic API キーが見つからない

```
🔑 Anthropic API キー: 未設定（要約スキップ）
```

**原因**: Keychain に API キーが登録されていない。

**解決策**:
```bash
# API キーを登録
security add-generic-password -a kaiwa -s anthropic-api-key -w 'sk-ant-YOUR_KEY'

# 確認
security find-generic-password -a kaiwa -s anthropic-api-key -w
```

**注意**: API キーは https://console.anthropic.com/settings/keys で取得できます。要約なしで文字起こしだけ実行する場合は、API キーは不要です。

---

#### Keychain アクセスがタイムアウトする

```
❌ Keychainアクセスがタイムアウトしました（10秒）
```

**原因**: macOS の Keychain が応答しない、またはパスワード入力待ち。

**解決策**:

**1) Keychain Access.app でロック解除**
1. アプリケーション → ユーティリティ → キーチェーンアクセス を開く
2. ログインキーチェーンがロックされていないか確認
3. ロックされている場合はパスワードを入力して解除

**2) 自動ロックを無効化（オプション）**
1. キーチェーンアクセス → 環境設定
2. 「一般」タブ → 「アイドル時にロック」のチェックを外す

---

### 🟡 Medium

#### 音声ファイルが短すぎる/小さすぎる

```
❌ 音声ファイル検証エラー: ファイルサイズが小さすぎます
❌ 音声ファイル検証エラー: 音声が短すぎます
```

**原因**: 録音が正常に行われなかった、またはファイルが破損している。

**解決策**:
- 録音が1秒以上あることを確認
- ファイルサイズが1KB以上あることを確認
- `sox` の録音設定を確認

**録音の動作確認**:
```bash
# テスト録音（5秒間）
sox -d -r 16000 -c 1 -b 16 test.wav trim 0 5

# ファイルを確認
ls -lh test.wav
soxi test.wav
```

---

#### iCloud 同期タイムアウト

```
⚠️ 同期タイムアウト: <filename>
```

**原因**: iPhone からの録音ファイルが iCloud Drive で同期完了しなかった。

**解決策**:
1. Wi-Fi 接続を確認
2. iCloud Drive の空き容量を確認
3. iPhone 側で iCloud Drive が有効になっているか確認
4. 手動で `kaiwa process <file>` を実行

---

#### 処理が途中で停止する

**原因**: メモリ不足、長時間音声、またはモデルのクラッシュ。

**解決策**:

**1) メモリ使用量を確認**
```bash
# 処理中にメモリを監視
top -pid $(pgrep -f "kaiwa.cli")
```

**2) バッチサイズを減らす**

`~/.kaiwa/config.yaml` で WhisperX のバッチサイズを調整：
```yaml
whisper:
  batch_size: 8  # デフォルトは 16。メモリ不足なら 4 や 2 に減らす
```

**3) 長時間音声を分割**

2時間以上の音声は分割して処理することを推奨：
```bash
# sox で 30分ごとに分割
sox input.wav output_%02d.wav trim 0 1800 : newfile : restart
```

**4) 中間ファイルから再開**

処理が途中で失敗した場合、`~/Transcripts/work/<filename>/` に中間ファイルが残っています。手動で次のステップから再開できます（現在は未実装、将来の機能）。

---

#### 通知が表示されない

```
# macOS 通知が表示されない
```

**原因**: macOS の通知設定で「ターミナル」または「スクリプトエディタ」の通知が無効。

**解決策**:

1. システム設定 → 通知
2. 「ターミナル」を検索
3. 「通知を許可」を有効化
4. 通知スタイルを「バナー」または「通知」に設定

---

#### ログファイルの場所

処理ログは以下に保存されます：
```
~/.kaiwa/logs/YYYY-MM-DD.log
```

問題が発生した場合はこのログを確認してください。

---

#### 中間成果物の確認

各ステップの結果は以下に保存されます：
```
~/Transcripts/work/<recording_stem>/
├── 01_transcribe.json   # 文字起こし結果
├── 02_align.json        # アラインメント結果
└── 03_diarize.json      # 話者分離結果
```

処理が途中で失敗した場合、ここにある中間ファイルを確認することで、どのステップまで成功したかがわかります。

---

## 設定の確認方法

```bash
# 現在の設定を確認
cat ~/.kaiwa/config.yaml

# Keychain のトークンを確認
security find-generic-password -a kaiwa -s hf-token -w
security find-generic-password -a kaiwa -s anthropic-api-key -w
```

---

## パフォーマンス最適化

### 処理が遅い

**原因**: CPU モードで動作している、またはバッチサイズが小さい。

**解決策**:

**1) デバイス設定を確認**

`~/.kaiwa/config.yaml`:
```yaml
whisper:
  device: cpu  # macOS では cpu が推奨（MPS は非対応）
  compute_type: int8  # float16 より速いが精度は若干低下
  batch_size: 16  # メモリに余裕があれば 32 に増やす
```

**2) モデルサイズを変更**

精度と速度のトレードオフ：
```yaml
whisper:
  model: base  # tiny < base < small < medium < large-v2（デフォルト）
```

| モデル | 速度 | 精度 | メモリ |
|-------|------|------|--------|
| tiny | 🚀🚀🚀 | ⭐ | 1GB |
| base | 🚀🚀 | ⭐⭐ | 1GB |
| small | 🚀 | ⭐⭐⭐ | 2GB |
| medium | 🐢 | ⭐⭐⭐⭐ | 5GB |
| large-v2 | 🐢🐢 | ⭐⭐⭐⭐⭐ | 10GB |

**推奨**: 日本語の場合は `medium` が精度と速度のバランスが良い。

---

## デバッグモード

詳細なログを出力する：

```bash
# デバッグログ有効化
export KAIWA_LOG_LEVEL=DEBUG

# 処理実行
PYTHONPATH=./src ~/.kaiwa/venv/bin/python -m kaiwa.cli process recording.wav

# ログ確認
tail -f ~/.kaiwa/logs/$(date +%Y-%m-%d).log
```

---

## 再インストール

問題が解決しない場合、クリーンインストールを試してください：

```bash
# 完全削除
rm -rf ~/.kaiwa
rm -rf ~/Transcripts
rm -rf ~/.cache/huggingface
rm -rf ~/.cache/torch

# 再インストール
cd /path/to/kaiwa
./setup.sh
```

---

## サポート

それでも問題が解決しない場合は、以下を添えて Issue を作成してください：

1. **エラーメッセージ**（`~/.kaiwa/logs/YYYY-MM-DD.log` から）
2. **環境情報**（macOS バージョン、Python バージョン、kaiwa バージョン）
3. **再現手順**
4. **試した解決策**

Issue テンプレート: [Bug Report](../.github/ISSUE_TEMPLATE/bug_report.md)

**セキュリティ上の問題の場合は、公開 Issue ではなく [GitHub Security Advisories](https://github.com/takayama-tigrit/kaiwa/security/advisories/new) からプライベート報告してください。**
