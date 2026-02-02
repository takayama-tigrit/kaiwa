# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-02-02

### Added
- 初期リリース
- WhisperX による音声文字起こし機能
- pyannote.audio による話者分離機能
- Claude API による要約生成機能
- ファイル監視による自動処理
- セキュアなトークン管理（macOS Keychain 統合）
- 中間成果物の自動保存
- マークダウン形式での出力

### Security
- Keychain を使用した HuggingFace トークンの安全な保管
- 環境変数を使用した Claude API キーの管理
- セキュアなログ出力（トークンのマスキング）
