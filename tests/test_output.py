"""kaiwa.output のテスト"""

from __future__ import annotations

from pathlib import Path

import pytest

from kaiwa.output import _sanitize_filename, generate_markdown


class TestSanitizeFilename:
    """_sanitize_filename() のテスト"""

    def test_normal_japanese_title(self):
        """通常の日本語タイトル"""
        assert _sanitize_filename("プロジェクト会議") == "プロジェクト会議"

    def test_forbidden_chars(self):
        """禁止文字を含むタイトル"""
        assert _sanitize_filename("file/name:test") == "filenametest"
        assert _sanitize_filename('test"file"') == "testfile"
        assert _sanitize_filename("test<>file") == "testfile"
        assert _sanitize_filename("test|file") == "testfile"
        assert _sanitize_filename("test*file") == "testfile"
        assert _sanitize_filename("test?file") == "testfile"

    def test_long_title(self):
        """長すぎるタイトル"""
        long_title = "A" * 100
        result = _sanitize_filename(long_title)
        assert len(result) == 50

    def test_empty_string(self):
        """空文字列"""
        assert _sanitize_filename("") == ""

    def test_spaces(self):
        """スペースの処理"""
        assert _sanitize_filename("test file") == "test_file"
        assert _sanitize_filename("test　file") == "test_file"  # 全角スペース

    def test_consecutive_spaces(self):
        """連続スペース"""
        # 現在の実装では連続アンダースコアが残る
        result = _sanitize_filename("test  file")
        assert "test" in result
        assert "file" in result

    def test_consecutive_underscores(self):
        """連続アンダースコア"""
        # 現在の実装では連続アンダースコアがそのまま残る
        result = _sanitize_filename("test__file")
        assert "test" in result
        assert "file" in result

    def test_mixed_forbidden_and_spaces(self):
        """禁止文字とスペースの混在"""
        # "/" が削除され、スペースが "_" に置換される
        assert _sanitize_filename("test / file") == "test_file"

    def test_trailing_underscores(self):
        """末尾のアンダースコアの除去"""
        assert _sanitize_filename("test_") == "test"
        assert _sanitize_filename("_test") == "test"


class TestGenerateMarkdown:
    """generate_markdown() のテスト"""

    def test_generate_markdown_basic(
        self,
        tmp_path: Path,
        sample_transcript_lines: list[str],
        sample_config: dict,
    ):
        """基本的なMarkdown生成"""
        # 出力先を tmp_path に設定
        sample_config["paths"]["output"] = str(tmp_path)
        
        audio_path = Path("/tmp/test_audio.wav")
        
        output_file = generate_markdown(
            transcript_lines=sample_transcript_lines,
            summary="これは要約テキストです。",
            audio_path=audio_path,
            elapsed=125.5,
            config=sample_config,
            title="テスト会議",
        )
        
        # ファイルが生成されたか確認
        assert output_file.exists()
        assert output_file.suffix == ".md"
        assert "テスト会議" in output_file.name
        
        # ファイル内容の確認
        content = output_file.read_text(encoding="utf-8")
        assert "# テスト会議" in content
        assert "## 📋 要約" in content
        assert "これは要約テキストです。" in content
        assert "## 💬 全文（話者分離済み）" in content
        assert "SPEAKER_00: こんにちは。今日は会議を始めます。" in content
        assert "処理時間: 2分5秒" in content

    def test_generate_markdown_no_title(
        self,
        tmp_path: Path,
        sample_transcript_lines: list[str],
        sample_config: dict,
    ):
        """タイトルなしの場合"""
        sample_config["paths"]["output"] = str(tmp_path)
        audio_path = Path("/tmp/test_audio.wav")
        
        output_file = generate_markdown(
            transcript_lines=sample_transcript_lines,
            summary="要約",
            audio_path=audio_path,
            elapsed=10.0,
            config=sample_config,
            title=None,
        )
        
        assert output_file.exists()
        # タイトルなしの場合は日時ベースのファイル名
        assert output_file.stem.startswith("202")  # 年で始まる

    def test_generate_markdown_no_summary(
        self,
        tmp_path: Path,
        sample_transcript_lines: list[str],
        sample_config: dict,
    ):
        """要約なしの場合"""
        sample_config["paths"]["output"] = str(tmp_path)
        audio_path = Path("/tmp/test_audio.wav")
        
        output_file = generate_markdown(
            transcript_lines=sample_transcript_lines,
            summary=None,
            audio_path=audio_path,
            elapsed=10.0,
            config=sample_config,
        )
        
        content = output_file.read_text(encoding="utf-8")
        assert "_要約スキップ（APIキー未設定またはエラー）_" in content

    def test_generate_markdown_creates_directory(
        self,
        tmp_path: Path,
        sample_transcript_lines: list[str],
        sample_config: dict,
    ):
        """出力ディレクトリが存在しない場合に作成される"""
        output_dir = tmp_path / "nested" / "output"
        sample_config["paths"]["output"] = str(output_dir)
        audio_path = Path("/tmp/test_audio.wav")
        
        output_file = generate_markdown(
            transcript_lines=sample_transcript_lines,
            summary="要約",
            audio_path=audio_path,
            elapsed=10.0,
            config=sample_config,
        )
        
        assert output_dir.exists()
        assert output_file.exists()
        assert output_file.parent == output_dir

    def test_generate_markdown_special_chars_in_title(
        self,
        tmp_path: Path,
        sample_transcript_lines: list[str],
        sample_config: dict,
    ):
        """タイトルに特殊文字が含まれる場合"""
        sample_config["paths"]["output"] = str(tmp_path)
        audio_path = Path("/tmp/test_audio.wav")
        
        output_file = generate_markdown(
            transcript_lines=sample_transcript_lines,
            summary="要約",
            audio_path=audio_path,
            elapsed=10.0,
            config=sample_config,
            title="テスト/会議:重要",
        )
        
        # 禁止文字が除去されている
        assert "/" not in output_file.name
        assert ":" not in output_file.name
        assert output_file.exists()
