# Contributing to kaiwa

[English](#english) | [日本語](#japanese)

---

<a name="english"></a>
## English

Thank you for your interest in contributing to kaiwa! We welcome contributions from the community.

### Development Environment Setup

```bash
git clone https://github.com/takayama-tigrit/kaiwa.git
cd kaiwa
./setup.sh
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/kaiwa --cov-report=html

# Type checking
mypy src/kaiwa/

# Linting
ruff check src/

# Code formatting
ruff format src/
```

### Pull Request Guidelines

1. **Branch Naming**: Create a PR from `feature/your-feature-name` or `fix/your-fix-name`
2. **Commit Messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/)
   - `feat: add new feature`
   - `fix: fix bug`
   - `docs: update documentation`
   - `test: add tests`
   - `refactor: refactor code`
   - `chore: update dependencies`
3. **Tests**: Add or update tests for new features
4. **Code Style**: Format code with `ruff format`
5. **Documentation**: Update relevant documentation if needed

### Code Review Process

1. Submit a PR with a clear description
2. Maintainers will review within 1-2 weeks
3. Address feedback and update the PR
4. Once approved, a maintainer will merge

### Reporting Security Vulnerabilities

**DO NOT** open a public issue for security vulnerabilities. Instead, please use **GitHub Security Advisories** for private reporting:

🔒 [**Report a vulnerability**](https://github.com/takayama-tigrit/kaiwa/security/advisories/new)

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will respond within 48 hours and work with you to address the issue.

---

<a name="japanese"></a>
## 日本語

kaiwa への貢献に興味を持っていただき、ありがとうございます！コミュニティからの貢献を歓迎します。

### 開発環境のセットアップ

```bash
git clone https://github.com/takayama-tigrit/kaiwa.git
cd kaiwa
./setup.sh
```

### テストの実行

```bash
# 全テストを実行
pytest tests/

# カバレッジ付きで実行
pytest tests/ --cov=src/kaiwa --cov-report=html

# 型チェック
mypy src/kaiwa/

# Linter
ruff check src/

# コード整形
ruff format src/
```

### Pull Request のガイドライン

1. **ブランチ名**: `feature/機能名` または `fix/修正内容` から PR を作成
2. **コミットメッセージ**: [Conventional Commits](https://www.conventionalcommits.org/) に従う
   - `feat: 新機能追加`
   - `fix: バグ修正`
   - `docs: ドキュメント更新`
   - `test: テスト追加`
   - `refactor: リファクタリング`
   - `chore: 依存関係更新など`
3. **テスト**: 新機能には必ずテストを追加
4. **コードスタイル**: `ruff format` で整形
5. **ドキュメント**: 必要に応じて関連ドキュメントを更新

### コードレビュープロセス

1. 明確な説明付きで PR を送信
2. メンテナーが 1〜2 週間以内にレビュー
3. フィードバックに対応し、PR を更新
4. 承認されたら、メンテナーがマージ

### セキュリティ脆弱性の報告

セキュリティ上の問題を発見した場合は、**公開 Issue を作成しないでください**。代わりに **GitHub Security Advisories** からプライベート報告してください：

🔒 [**脆弱性を報告する**](https://github.com/takayama-tigrit/kaiwa/security/advisories/new)

以下の情報を含めてください：
- 脆弱性の説明
- 再現手順
- 潜在的な影響
- 修正案（あれば）

48 時間以内に返信し、問題に対処します。

---

## Development Guidelines / 開発ガイドライン

### Code Style

- Follow PEP 8
- Use type hints where possible
- Keep functions focused and single-purpose
- Document complex logic with comments

### Testing

- Write unit tests for new functions
- Test edge cases and error handling
- Maintain >80% code coverage

### Documentation

- Update docstrings for public functions
- Add examples where helpful
- Keep README.md and docs/ up to date

---

## Contact Policy / 連絡方針

Please use [GitHub Issues](https://github.com/takayama-tigrit/kaiwa/issues) or [Discussions](https://github.com/takayama-tigrit/kaiwa/discussions) for all project-related communication. **Please do not contact contributors directly via email.**

プロジェクトに関する連絡は [GitHub Issues](https://github.com/takayama-tigrit/kaiwa/issues) または [Discussions](https://github.com/takayama-tigrit/kaiwa/discussions) をご利用ください。**コントリビューターへの直接のメール連絡はご遠慮ください。**

---

Thank you for contributing! / ご協力ありがとうございます！
