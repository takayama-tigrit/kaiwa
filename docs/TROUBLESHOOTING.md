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

**解決策**:
```bash
# Keychain にトークンを登録
security add-generic-password -a kaiwa -s hf-token -w 'hf_YOUR_TOKEN'

# 確認
security find-generic-password -a kaiwa -s hf-token -w
```

**注意**: pyannote.audio のモデルは利用規約への同意が必要です：
- https://huggingface.co/pyannote/speaker-diarization-3.1
- https://huggingface.co/pyannote/segmentation-3.0

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

## 再インストール

問題が解決しない場合、クリーンインストールを試してください：

```bash
# venv を再作成
rm -rf ~/.kaiwa/venv
cd /path/to/kaiwa
./setup.sh
```
