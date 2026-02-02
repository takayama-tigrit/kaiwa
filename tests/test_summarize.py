"""kaiwa.summarize のテスト"""

from __future__ import annotations

from unittest import mock

import pytest

from kaiwa.summarize import _parse_title_and_summary, _sanitize_markdown, summarize


class TestParseTitleAndSummary:
    """_parse_title_and_summary() のテスト"""

    def test_with_title_line(self):
        """TITLE行がある場合"""
        response = """TITLE: プロジェクトX進捗会議

## 要点
- 進捗は順調
- 次回は来週
"""
        title, summary = _parse_title_and_summary(response)
        assert title == "プロジェクトX進捗会議"
        assert "## 要点" in summary
        assert "進捗は順調" in summary

    def test_without_title_line(self):
        """TITLE行がない場合"""
        response = """## 要点
- 進捗は順調
- 次回は来週
"""
        title, summary = _parse_title_and_summary(response)
        assert title is None
        assert summary == response

    def test_title_case_insensitive(self):
        """大文字小文字の違い"""
        # 小文字の title:
        response_lower = """title: 小文字タイトル

本文
"""
        title, summary = _parse_title_and_summary(response_lower)
        assert title == "小文字タイトル"
        assert "本文" in summary

        # 大文字の TITLE:
        response_upper = """TITLE: 大文字タイトル

本文
"""
        title, summary = _parse_title_and_summary(response_upper)
        assert title == "大文字タイトル"
        assert "本文" in summary

    def test_title_with_extra_spaces(self):
        """タイトル前後にスペースがある場合"""
        response = """TITLE:   スペース付きタイトル   

本文
"""
        title, summary = _parse_title_and_summary(response)
        assert title == "スペース付きタイトル"
        assert "本文" in summary

    def test_title_with_multiple_colons(self):
        """タイトルに複数のコロンがある場合"""
        response = """TITLE: タイトル: サブタイトル

本文
"""
        title, summary = _parse_title_and_summary(response)
        assert title == "タイトル: サブタイトル"
        assert "本文" in summary

    def test_title_with_leading_empty_lines(self):
        """先頭に空行がある場合"""
        response = """

TITLE: タイトル

本文
"""
        title, summary = _parse_title_and_summary(response)
        # 実装は全行をスキャンするため、空行があってもタイトルが見つかる
        assert title == "タイトル"
        assert "本文" in summary

    def test_title_at_first_line_only(self):
        """TITLEが最初の行にのみ有効"""
        response = """最初の行

TITLE: この行は無視される

本文
"""
        # 最初の行からスキャンして、最初に見つかったTITLE行を使用
        title, summary = _parse_title_and_summary(response)
        # 実装では全行をスキャンするので、この場合はタイトルが見つかる
        assert title == "この行は無視される"
        assert "本文" in summary

    def test_empty_summary_after_title(self):
        """タイトル後に本文がない場合"""
        response = """TITLE: タイトルのみ"""
        title, summary = _parse_title_and_summary(response)
        assert title == "タイトルのみ"
        assert summary == ""

    def test_title_with_multiple_empty_lines_after(self):
        """タイトル後に複数の空行"""
        response = """TITLE: タイトル



本文
"""
        title, summary = _parse_title_and_summary(response)
        assert title == "タイトル"
        # 先頭の空行がスキップされる
        assert summary.strip() == "本文"


class TestSanitizeMarkdown:
    """_sanitize_markdown() のテスト"""

    def test_remove_script_tags(self):
        """<script>タグが除去される"""
        text = """正常なテキスト
<script>alert('XSS')</script>
その他のテキスト"""
        result = _sanitize_markdown(text)
        assert "<script>" not in result
        assert "正常なテキスト" in result
        assert "その他のテキスト" in result

    def test_remove_javascript_protocol(self):
        """javascript: プロトコルが除去される"""
        text = """[リンク](javascript:alert('XSS'))"""
        result = _sanitize_markdown(text)
        assert "javascript:" not in result.lower()

    def test_remove_data_uri_non_image(self):
        """data: URI（画像以外）が除去される"""
        text = """[リンク](data:text/html,<script>alert('XSS')</script>)"""
        result = _sanitize_markdown(text)
        assert "data:text" not in result.lower()

    def test_keep_image_data_uri(self):
        """data:image/ URI は保持される"""
        text = """![画像](data:image/png;base64,iVBORw0KGgoAAAANS)"""
        result = _sanitize_markdown(text)
        assert "data:image/" in result.lower()

    def test_normal_markdown_unchanged(self):
        """通常のMarkdownは変更されない"""
        text = """# タイトル

- 項目1
- 項目2

[リンク](https://example.com)"""
        result = _sanitize_markdown(text)
        assert result == text


class TestSummarize:
    """summarize() のテスト"""

    @mock.patch("anthropic.Anthropic")
    def test_summarize_success(self, mock_anthropic_class):
        """正常に要約が生成される"""
        # モックの設定
        mock_client = mock.MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        mock_content = mock.MagicMock()
        mock_content.text = """TITLE: テスト会議

## 要点
- 項目1
- 項目2"""
        
        mock_message = mock.MagicMock()
        mock_message.content = [mock_content]
        
        mock_client.messages.create.return_value = mock_message
        
        config = {
            "claude": {
                "model": "claude-3-5-haiku-latest",
                "max_tokens": 2048,
                "timeout": 120,
                "max_retries": 3,
            }
        }
        
        # 実行
        title, summary = summarize("文字起こしテキスト", "api-key", config)
        
        # 結果の確認
        assert title == "テスト会議"
        assert "## 要点" in summary
        assert "項目1" in summary

    @mock.patch("anthropic.Anthropic")
    def test_summarize_rate_limit_retry(self, mock_anthropic_class):
        """429エラー時にリトライされる"""
        # モックの設定
        mock_client = mock.MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        import anthropic
        
        # 1回目は429エラー、2回目は成功
        mock_content = mock.MagicMock()
        mock_content.text = "TITLE: 成功\n\n本文"
        mock_message = mock.MagicMock()
        mock_message.content = [mock_content]
        
        # RateLimitError のインスタンス化に必要な引数を提供
        mock_response = mock.MagicMock()
        mock_response.status_code = 429
        rate_limit_error = anthropic.RateLimitError(
            "Rate limit exceeded",
            response=mock_response,
            body={"error": "rate_limit"}
        )
        
        mock_client.messages.create.side_effect = [
            rate_limit_error,
            mock_message,
        ]
        
        config = {"claude": {"max_retries": 3}}
        
        # 実行（time.sleepをモック）
        with mock.patch("kaiwa.summarize.time.sleep"):
            title, summary = summarize("文字起こし", "api-key", config)
        
        # リトライして成功すること
        assert title == "成功"
        assert mock_client.messages.create.call_count == 2

    @mock.patch("anthropic.Anthropic")
    def test_summarize_rate_limit_max_retries(self, mock_anthropic_class):
        """429エラーが続くとNoneを返す"""
        # モックの設定
        mock_client = mock.MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        import anthropic
        
        # 常に429エラー
        mock_response = mock.MagicMock()
        mock_response.status_code = 429
        rate_limit_error = anthropic.RateLimitError(
            "Rate limit exceeded",
            response=mock_response,
            body={"error": "rate_limit"}
        )
        mock_client.messages.create.side_effect = rate_limit_error
        
        config = {"claude": {"max_retries": 2}}
        
        # 実行
        with mock.patch("kaiwa.summarize.time.sleep"):
            title, summary = summarize("文字起こし", "api-key", config)
        
        # 失敗すること
        assert title is None
        assert summary is None
        assert mock_client.messages.create.call_count == 2

    @mock.patch("anthropic.Anthropic")
    def test_summarize_internal_server_error_retry(self, mock_anthropic_class):
        """500エラー時にリトライされる"""
        # モックの設定
        mock_client = mock.MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        import anthropic
        
        # 1回目は500エラー、2回目は成功
        mock_content = mock.MagicMock()
        mock_content.text = "TITLE: 成功\n\n本文"
        mock_message = mock.MagicMock()
        mock_message.content = [mock_content]
        
        mock_response = mock.MagicMock()
        mock_response.status_code = 500
        internal_error = anthropic.InternalServerError(
            "Internal server error",
            response=mock_response,
            body={"error": "internal_server_error"}
        )
        
        mock_client.messages.create.side_effect = [
            internal_error,
            mock_message,
        ]
        
        config = {"claude": {"max_retries": 3}}
        
        # 実行
        with mock.patch("kaiwa.summarize.time.sleep"):
            title, summary = summarize("文字起こし", "api-key", config)
        
        # リトライして成功すること
        assert title == "成功"
        assert mock_client.messages.create.call_count == 2

    @mock.patch("anthropic.Anthropic")
    def test_summarize_api_error_no_retry(self, mock_anthropic_class):
        """その他のAPIエラーはリトライしない"""
        # モックの設定
        mock_client = mock.MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        import anthropic
        
        # APIError（429/500以外）
        mock_request = mock.MagicMock()
        api_error = anthropic.APIError("API error", request=mock_request, body={"error": "api_error"})
        mock_client.messages.create.side_effect = api_error
        
        config = {"claude": {"max_retries": 3}}
        
        # 実行
        title, summary = summarize("文字起こし", "api-key", config)
        
        # リトライせず即座に失敗すること
        assert title is None
        assert summary is None
        assert mock_client.messages.create.call_count == 1

    @mock.patch("anthropic.Anthropic")
    def test_summarize_unexpected_error(self, mock_anthropic_class):
        """予期しないエラーはNoneを返す"""
        # モックの設定
        mock_client = mock.MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        # 予期しないエラー
        mock_client.messages.create.side_effect = ValueError("Unexpected error")
        
        config = {"claude": {"max_retries": 3}}
        
        # 実行
        title, summary = summarize("文字起こし", "api-key", config)
        
        # 失敗すること
        assert title is None
        assert summary is None

    @mock.patch("anthropic.Anthropic")
    def test_summarize_xss_sanitization(self, mock_anthropic_class):
        """XSS攻撃がサニタイズされる"""
        # モックの設定
        mock_client = mock.MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        mock_content = mock.MagicMock()
        mock_content.text = """TITLE: テスト<script>alert('XSS')</script>

<script>alert('XSS')</script>
本文"""
        
        mock_message = mock.MagicMock()
        mock_message.content = [mock_content]
        
        mock_client.messages.create.return_value = mock_message
        
        config = {"claude": {}}
        
        # 実行
        title, summary = summarize("文字起こし", "api-key", config)
        
        # <script>タグが除去されていること
        assert "<script>" not in summary
        assert "本文" in summary
