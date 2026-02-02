"""kaiwa.utils のテスト"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from kaiwa.utils import (
    _escape_applescript,
    _make_serializable,
    _save_intermediate,
    format_timestamp,
    get_keychain_password,
    validate_audio,
)


class TestFormatTimestamp:
    """format_timestamp() のテスト"""

    def test_seconds_only(self):
        """秒のみの場合"""
        assert format_timestamp(45) == "00:45"
        assert format_timestamp(5) == "00:05"

    def test_minutes(self):
        """分単位の場合"""
        assert format_timestamp(90) == "01:30"
        assert format_timestamp(125) == "02:05"

    def test_over_one_hour(self):
        """1時間を超える場合"""
        assert format_timestamp(3661) == "1:01:01"
        assert format_timestamp(7384) == "2:03:04"

    def test_exact_hour(self):
        """ちょうど1時間の場合"""
        assert format_timestamp(3600) == "1:00:00"


class TestValidateAudio:
    """validate_audio() のテスト"""

    def test_nonexistent_file(self, tmp_path: Path):
        """存在しないファイルの場合"""
        nonexistent = tmp_path / "nonexistent.wav"
        valid, message = validate_audio(nonexistent)
        assert not valid
        assert "ファイルが見つかりません" in message

    def test_empty_file(self, tmp_path: Path):
        """空ファイルの場合"""
        empty_file = tmp_path / "empty.wav"
        empty_file.touch()
        valid, message = validate_audio(empty_file)
        assert not valid
        assert "ファイルサイズが小さすぎます" in message

    def test_too_small_file(self, tmp_path: Path):
        """ファイルサイズが1KB未満の場合"""
        small_file = tmp_path / "small.wav"
        small_file.write_bytes(b"x" * 512)  # 512 bytes
        valid, message = validate_audio(small_file)
        assert not valid
        assert "ファイルサイズが小さすぎます" in message

    def test_valid_wav_file(self, tmp_audio_file: Path):
        """正常なWAVファイルの場合"""
        valid, message = validate_audio(tmp_audio_file)
        assert valid
        assert message == "OK"

    def test_invalid_wav_file(self, tmp_path: Path):
        """不正なWAVファイル（ヘッダーのみ）の場合"""
        invalid_wav = tmp_path / "invalid.wav"
        # WAVファイルとして不正なデータを書き込む
        invalid_wav.write_bytes(b"RIFF" + b"\x00" * 2000)
        valid, message = validate_audio(invalid_wav)
        assert not valid
        assert "WAV ファイルの読み込みに失敗しました" in message

    def test_too_short_audio(self, tmp_path: Path):
        """音声が短すぎる場合（1秒未満）"""
        import wave

        short_audio = tmp_path / "short.wav"
        with wave.open(str(short_audio), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            # 0.5秒分のフレーム
            wf.writeframes(b"\x00\x00" * 8000)

        valid, message = validate_audio(short_audio)
        assert not valid
        assert "音声が短すぎます" in message

    def test_non_wav_file_large_enough(self, tmp_path: Path):
        """WAV以外のファイル（十分なサイズ）の場合"""
        # MP3等の実際のフォーマットチェックはWhisperXに任せる
        mp3_file = tmp_path / "audio.mp3"
        mp3_file.write_bytes(b"x" * 10000)  # 10KB
        valid, message = validate_audio(mp3_file)
        assert valid
        assert message == "OK"


class TestEscapeApplescript:
    """_escape_applescript() のテスト"""

    def test_no_special_chars(self):
        """特殊文字なしの場合"""
        assert _escape_applescript("Hello World") == "Hello World"

    def test_double_quotes(self):
        """ダブルクォートを含む場合"""
        assert _escape_applescript('Say "Hello"') == 'Say \\"Hello\\"'

    def test_backslash(self):
        """バックスラッシュを含む場合"""
        assert _escape_applescript("C:\\path\\to\\file") == "C:\\\\path\\\\to\\\\file"

    def test_both_special_chars(self):
        """両方の特殊文字を含む場合"""
        assert _escape_applescript('Path: "C:\\Users"') == 'Path: \\"C:\\\\Users\\"'

    def test_empty_string(self):
        """空文字列の場合"""
        assert _escape_applescript("") == ""

    def test_japanese_text(self):
        """日本語テキストの場合"""
        assert _escape_applescript("こんにちは「世界」") == "こんにちは「世界」"


class TestMakeSerializable:
    """_make_serializable() のテスト"""

    def test_basic_types(self):
        """基本型がそのまま返される"""
        assert _make_serializable(42) == 42
        assert _make_serializable("hello") == "hello"
        assert _make_serializable(True) is True
        assert _make_serializable(None) is None
        assert _make_serializable(3.14) == 3.14

    def test_nan_value(self):
        """NaN値がNoneに変換される"""
        assert _make_serializable(float("nan")) is None

    def test_list_conversion(self):
        """リストが再帰的に変換される"""
        result = _make_serializable([1, "test", float("nan"), None])
        assert result == [1, "test", None, None]

    def test_dict_conversion(self):
        """辞書が再帰的に変換される"""
        result = _make_serializable({
            "a": 1,
            "b": "test",
            "c": float("nan"),
            "d": None,
        })
        assert result == {"a": 1, "b": "test", "c": None, "d": None}

    def test_nested_structure(self):
        """ネストした構造が正しく変換される"""
        result = _make_serializable({
            "segments": [
                {
                    "text": "hello",
                    "score": float("nan"),
                    "words": [
                        {"word": "hello", "start": 0.0},
                    ],
                },
            ],
        })
        assert result["segments"][0]["score"] is None
        assert result["segments"][0]["words"][0]["word"] == "hello"

    def test_non_serializable_object(self):
        """シリアライズ不可能なオブジェクトが文字列に変換される"""
        class CustomObject:
            def __str__(self):
                return "CustomObject"

        obj = CustomObject()
        result = _make_serializable({"obj": obj})
        assert result["obj"] == "CustomObject"

    def test_tuple_conversion(self):
        """タプルがリストに変換される"""
        result = _make_serializable((1, 2, 3))
        assert result == [1, 2, 3]
        assert isinstance(result, list)


class TestSaveIntermediate:
    """_save_intermediate() のテスト"""

    def test_save_basic_data(self, tmp_path):
        """基本的なデータが保存される"""
        path = tmp_path / "test.json"
        data = {"key": "value", "number": 42}
        
        _save_intermediate(path, data)
        
        assert path.exists()
        import json
        with open(path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        assert saved == data

    def test_save_with_nan(self, tmp_path):
        """NaN値を含むデータが保存される"""
        path = tmp_path / "test_nan.json"
        data = {"score": float("nan"), "value": 1.0}
        
        _save_intermediate(path, data)
        
        assert path.exists()
        import json
        with open(path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        assert saved["score"] is None
        assert saved["value"] == 1.0

    def test_save_creates_directory(self, tmp_path):
        """ディレクトリが自動作成される"""
        path = tmp_path / "subdir" / "nested" / "test.json"
        data = {"test": "data"}
        
        _save_intermediate(path, data)
        
        assert path.exists()
        assert path.parent.exists()

    def test_save_handles_errors_gracefully(self, tmp_path):
        """書き込みエラーが発生しても例外を投げない（warningのみ）"""
        # 存在しないディレクトリへの書き込みで、open()が失敗するケース
        # （ディレクトリ自動作成前にopen()をモックして失敗させる）
        import json as json_module
        
        path = tmp_path / "test.json"
        data = {"test": "data"}
        
        # json.dump が失敗するケースをシミュレート
        with mock.patch.object(json_module, "dump", side_effect=OSError("Write error")):
            # エラーが発生してもSystemExitしない
            _save_intermediate(path, data)
        
        # ファイルは作成されているが、内容は書き込まれていない可能性がある
        # （エラーハンドリングが正しく動作していること自体を確認）

    def test_save_complex_structure(self, tmp_path):
        """複雑なネスト構造が保存される"""
        path = tmp_path / "complex.json"
        data = {
            "segments": [
                {
                    "text": "hello",
                    "start": 0.0,
                    "end": 5.0,
                    "words": [
                        {"word": "hello", "start": 0.0, "score": float("nan")},
                    ],
                },
            ],
            "language": "ja",
        }
        
        _save_intermediate(path, data)
        
        assert path.exists()
        import json
        with open(path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        assert saved["segments"][0]["words"][0]["score"] is None


class TestGetKeychainPasswordSecurity:
    """get_keychain_password() のセキュリティテスト"""

    @mock.patch("subprocess.run")
    def test_keychain_timeout(self, mock_run):
        """Keychainアクセスのタイムアウト（10秒制限）"""
        import subprocess
        
        # TimeoutExpiredを投げる
        mock_run.side_effect = subprocess.TimeoutExpired("security", 10)
        
        result = get_keychain_password("kaiwa", "hf-token")
        
        # タイムアウト時はNoneを返すこと
        assert result is None
        
        # subprocess.runがtimeout=10で呼ばれていること
        assert mock_run.called
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("timeout") == 10

    @mock.patch("subprocess.run")
    def test_keychain_command_failure(self, mock_run):
        """Keychainコマンド実行失敗時のエラーハンドリング"""
        import subprocess
        
        # CalledProcessErrorを投げる
        mock_result = mock.MagicMock()
        mock_result.stderr = "could not be found"
        mock_run.side_effect = subprocess.CalledProcessError(1, "security")
        mock_run.side_effect.stderr = "could not be found"
        
        result = get_keychain_password("kaiwa", "hf-token")
        
        # エラー時はNoneを返すこと
        assert result is None

    @mock.patch("subprocess.run")
    def test_keychain_unexpected_error(self, mock_run):
        """Keychainアクセス時の予期しないエラーのハンドリング"""
        # 予期しない例外を投げる
        mock_run.side_effect = OSError("予期しないエラー")
        
        result = get_keychain_password("kaiwa", "hf-token")
        
        # エラー時はNoneを返すこと
        assert result is None


class TestLogFileSecurity:
    """ログファイルのセキュリティテスト"""

    def test_log_directory_permissions(self, tmp_path, monkeypatch):
        """ログディレクトリが0o700で作成されること"""
        import kaiwa.utils
        
        # LOG_DIRをtmp_pathに変更
        log_dir = tmp_path / "logs"
        monkeypatch.setattr(kaiwa.utils, "LOG_DIR", log_dir)
        
        # setup_loggingを実行
        kaiwa.utils.setup_logging()
        
        # ディレクトリが作成されていること
        assert log_dir.exists()
        
        # パーミッションが0o700であること（所有者のみアクセス可）
        import stat
        mode = log_dir.stat().st_mode
        # ディレクトリビットを除いた下位9ビットを取得
        perms = stat.S_IMODE(mode)
        assert perms == 0o700, f"Expected 0o700, got {oct(perms)}"

    def test_log_file_permissions(self, tmp_path, monkeypatch):
        """ログファイルが0o600で作成されること"""
        import kaiwa.utils
        from datetime import datetime
        import logging
        
        # LOG_DIRをtmp_pathに変更
        log_dir = tmp_path / "logs"
        monkeypatch.setattr(kaiwa.utils, "LOG_DIR", log_dir)
        
        # 既存のloggerのハンドラーをクリア（他のテストの影響を排除）
        logger = logging.getLogger("kaiwa")
        logger.handlers.clear()
        
        # setup_loggingを実行
        logger = kaiwa.utils.setup_logging()
        
        # ログファイルパスを取得
        log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        
        # ログファイルに何か書き込む
        logger.info("Test log message")
        
        # ハンドラーをフラッシュしてファイルに書き込みを確実にする
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.flush()
        
        # ファイルが作成されていること
        assert log_file.exists(), f"Log file {log_file} does not exist"
        
        # パーミッションが0o600であること（所有者のみ読み書き可）
        import stat
        mode = log_file.stat().st_mode
        perms = stat.S_IMODE(mode)
        assert perms == 0o600, f"Expected 0o600, got {oct(perms)}"
