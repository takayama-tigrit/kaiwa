# 📦 インストール・初期設定

## 🖥️ 必要環境

- **macOS** (Apple Silicon 推奨 — Intel でも動作します)
- **Python 3.10+**
- **Homebrew**
- **約 4GB** のストレージ（WhisperX モデル用）

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/takayama-tigrit/kaiwa.git
cd kaiwa

# セットアップ（依存関係インストール + venv 作成）
chmod +x setup.sh
./setup.sh
```

### setup.sh が行うこと

- `sox`, `fswatch` のインストール（Homebrew）
- `~/.kaiwa/venv` に Python 仮想環境を作成
- WhisperX, Anthropic SDK, PyYAML をインストール
- `~/.kaiwa/config.yaml` をコピー
- 必要なディレクトリを作成

## ⚙️ 初期設定

### 1. HuggingFace トークン（必須）

話者分離に [pyannote.audio](https://github.com/pyannote/pyannote-audio) を使用します。以下の手順で設定してください。

#### ① HuggingFace アカウントの作成

[huggingface.co](https://huggingface.co/) でアカウントを作成します。

#### ② モデルの利用規約に同意

以下のモデルページにアクセスし、それぞれ利用規約に同意してください：

- [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
- [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)

#### ③ トークンの生成

1. [HuggingFace Settings > Access Tokens](https://huggingface.co/settings/tokens) にアクセス
2. 「New token」でトークンを作成（Read 権限で OK）

#### ④ Keychain に保存

```bash
security add-generic-password -a kaiwa -s hf-token -w 'hf_YOUR_TOKEN'
```

### 2. Anthropic API キー（オプション — 要約機能に必要）

```bash
security add-generic-password -a kaiwa -s anthropic-api-key -w 'sk-ant-YOUR_KEY'
```

### API キーの管理について

> 💡 API キーは macOS Keychain に暗号化して保存されます。環境変数や平文ファイルには保存しません。

**Keychain の確認:**

```bash
# トークンの確認
security find-generic-password -a kaiwa -s hf-token -w
security find-generic-password -a kaiwa -s anthropic-api-key -w
```

**トークンの更新:**

```bash
# 既存のトークンを削除してから再登録
security delete-generic-password -a kaiwa -s hf-token
security add-generic-password -a kaiwa -s hf-token -w 'hf_NEW_TOKEN'
```
