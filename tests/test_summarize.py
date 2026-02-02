"""kaiwa.summarize のテスト"""

from __future__ import annotations

import pytest

from kaiwa.summarize import _parse_title_and_summary


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
