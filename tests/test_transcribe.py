"""kaiwa.transcribe のテスト"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from kaiwa.transcribe import transcribe


class TestTranscribe:
    """transcribe() のテスト"""

    @mock.patch("kaiwa.transcribe.whisperx")
    @mock.patch("faster_whisper.WhisperModel")
    def test_transcribe_native_mode(
        self, mock_whisper_model, mock_whisperx, tmp_audio_file
    ):
        """native mode（デフォルト）のフロー"""
        # モックの設定
        mock_audio = mock.MagicMock()
        mock_whisperx.load_audio.return_value = mock_audio
        
        # faster_whisper モック
        mock_model = mock.MagicMock()
        mock_whisper_model.return_value = mock_model
        
        # transcribe の戻り値
        mock_word = mock.MagicMock()
        mock_word.word = "こんにちは"
        mock_word.start = 0.0
        mock_word.end = 2.5
        mock_word.probability = 0.9
        
        mock_segment = mock.MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 5.0
        mock_segment.text = "こんにちは世界"
        mock_segment.words = [mock_word]
        
        mock_info = mock.MagicMock()
        mock_info.language = "ja"
        
        mock_model.transcribe.return_value = (iter([mock_segment]), mock_info)
        
        config = {
            "whisper": {
                "device": "cpu",
                "compute_type": "float32",
                "model": "large-v3-turbo",
                "language": "ja",
                "batch_size": 8,
                "use_native_word_timestamps": True,
            }
        }
        
        # 実行
        audio, result = transcribe(tmp_audio_file, config)
        
        # whisperx.load_audio が呼ばれたこと
        mock_whisperx.load_audio.assert_called_once()
        
        # faster_whisper.WhisperModel が呼ばれたこと
        mock_whisper_model.assert_called_once_with(
            "large-v3-turbo", device="cpu", compute_type="float32"
        )
        
        # transcribe が呼ばれたこと
        mock_model.transcribe.assert_called_once()
        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs["language"] == "ja"
        assert call_kwargs["word_timestamps"] is True
        assert call_kwargs["vad_filter"] is True
        
        # 結果が返されること
        assert "segments" in result
        assert len(result["segments"]) == 1
        assert result["segments"][0]["text"] == "こんにちは世界"
        assert result["language"] == "ja"

    @mock.patch("kaiwa.transcribe.whisperx")
    def test_transcribe_whisperx_mode(self, mock_whisperx, tmp_audio_file):
        """whisperx mode（use_native_word_timestamps=false）のフロー"""
        # モックの設定
        mock_audio = mock.MagicMock()
        mock_whisperx.load_audio.return_value = mock_audio
        
        mock_model = mock.MagicMock()
        mock_whisperx.load_model.return_value = mock_model
        
        mock_transcribe_result = {
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "こんにちは世界",
                }
            ]
        }
        mock_model.transcribe.return_value = mock_transcribe_result
        
        mock_align_model = mock.MagicMock()
        mock_align_metadata = mock.MagicMock()
        mock_whisperx.load_align_model.return_value = (mock_align_model, mock_align_metadata)
        
        mock_aligned_result = {
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "こんにちは世界",
                    "words": [
                        {"word": "こんにちは", "start": 0.0, "end": 2.5},
                        {"word": "世界", "start": 2.5, "end": 5.0},
                    ],
                }
            ]
        }
        mock_whisperx.align.return_value = mock_aligned_result
        
        config = {
            "whisper": {
                "device": "cpu",
                "compute_type": "float32",
                "model": "large-v3-turbo",
                "language": "ja",
                "batch_size": 8,
                "use_native_word_timestamps": False,
            }
        }
        
        # 実行
        audio, result = transcribe(tmp_audio_file, config)
        
        # whisperx.load_model が呼ばれたこと
        mock_whisperx.load_model.assert_called_once_with(
            "large-v3-turbo",
            device="cpu",
            compute_type="float32",
            language="ja",
        )
        
        # model.transcribe が呼ばれたこと
        mock_model.transcribe.assert_called_once()
        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs["batch_size"] == 8
        assert call_kwargs["language"] == "ja"
        
        # whisperx.load_align_model が呼ばれたこと
        mock_whisperx.load_align_model.assert_called_once_with(
            language_code="ja", device="cpu"
        )
        
        # whisperx.align が呼ばれたこと
        mock_whisperx.align.assert_called_once()
        
        # 結果が返されること
        assert "segments" in result
        assert len(result["segments"]) == 1

    @mock.patch("kaiwa.transcribe._save_intermediate")
    @mock.patch("kaiwa.transcribe.whisperx")
    @mock.patch("faster_whisper.WhisperModel")
    def test_transcribe_with_work_dir(
        self, mock_whisper_model, mock_whisperx, mock_save, tmp_audio_file, tmp_path
    ):
        """work_dir指定時に中間ファイルが保存されること"""
        # モックの設定
        mock_audio = mock.MagicMock()
        mock_whisperx.load_audio.return_value = mock_audio
        
        mock_model = mock.MagicMock()
        mock_whisper_model.return_value = mock_model
        
        mock_segment = mock.MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 5.0
        mock_segment.text = "こんにちは"
        mock_segment.words = []
        
        mock_info = mock.MagicMock()
        mock_info.language = "ja"
        
        mock_model.transcribe.return_value = (iter([mock_segment]), mock_info)
        
        config = {
            "whisper": {
                "device": "cpu",
                "compute_type": "float32",
                "model": "large-v3-turbo",
                "language": "ja",
                "use_native_word_timestamps": True,
            }
        }
        
        work_dir = tmp_path / "work"
        
        # 実行
        transcribe(tmp_audio_file, config, work_dir=work_dir)
        
        # _save_intermediate が呼ばれたこと
        mock_save.assert_called_once()
        call_args = mock_save.call_args[0]
        assert "01_transcribe.json" in str(call_args[0])

    @mock.patch("kaiwa.transcribe.whisperx")
    @mock.patch("faster_whisper.WhisperModel")
    def test_transcribe_default_config(
        self, mock_whisper_model, mock_whisperx, tmp_audio_file
    ):
        """デフォルト設定が適用されること"""
        # モックの設定
        mock_audio = mock.MagicMock()
        mock_whisperx.load_audio.return_value = mock_audio
        
        mock_model = mock.MagicMock()
        mock_whisper_model.return_value = mock_model
        
        mock_segment = mock.MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 5.0
        mock_segment.text = "こんにちは"
        mock_segment.words = []
        
        mock_info = mock.MagicMock()
        mock_info.language = "ja"
        
        mock_model.transcribe.return_value = (iter([mock_segment]), mock_info)
        
        # 空のconfig
        config = {}
        
        # 実行
        audio, result = transcribe(tmp_audio_file, config)
        
        # デフォルト値が使われること
        mock_whisper_model.assert_called_once_with(
            "large-v3-turbo",  # デフォルト
            device="cpu",      # デフォルト
            compute_type="float32",  # デフォルト
        )
        
        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs["language"] == "ja"  # デフォルト


class TestTranscribeErrorHandling:
    """transcribe() のエラーハンドリングテスト"""

    @mock.patch("faster_whisper.WhisperModel")
    def test_transcribe_model_load_failure(self, mock_whisper_model, tmp_audio_file):
        """モデルロード失敗時のエラーハンドリング"""
        # モデルのインスタンス化に失敗
        mock_whisper_model.side_effect = RuntimeError("モデルのロードに失敗しました")
        
        config = {
            "whisper": {
                "device": "cpu",
                "compute_type": "float32",
                "model": "large-v3-turbo",
                "language": "ja",
                "use_native_word_timestamps": True,
            }
        }
        
        # エラーが伝播すること
        with pytest.raises(RuntimeError) as exc_info:
            transcribe(tmp_audio_file, config)
        
        assert "モデルのロードに失敗しました" in str(exc_info.value)

    @mock.patch("kaiwa.transcribe.whisperx")
    @mock.patch("faster_whisper.WhisperModel")
    def test_transcribe_corrupted_audio(self, mock_whisper_model, mock_whisperx, tmp_path):
        """不正な音声データでのエラーハンドリング"""
        # 不正な音声ファイル
        corrupted = tmp_path / "corrupted.wav"
        corrupted.write_bytes(b"RIFF" + b"\x00" * 100)
        
        # whisperx.load_audio が例外を投げる
        mock_whisperx.load_audio.side_effect = RuntimeError("音声ファイルの読み込みに失敗しました")
        
        config = {
            "whisper": {
                "device": "cpu",
                "compute_type": "float32",
                "model": "large-v3-turbo",
                "language": "ja",
                "use_native_word_timestamps": True,
            }
        }
        
        # エラーが伝播すること
        with pytest.raises(RuntimeError) as exc_info:
            transcribe(corrupted, config)
        
        assert "音声ファイルの読み込みに失敗しました" in str(exc_info.value)

    @mock.patch("kaiwa.transcribe.whisperx")
    @mock.patch("faster_whisper.WhisperModel")
    def test_transcribe_exception_during_transcription(
        self, mock_whisper_model, mock_whisperx, tmp_audio_file
    ):
        """文字起こし中の例外がハンドリングされること"""
        # モックの設定
        mock_audio = mock.MagicMock()
        mock_whisperx.load_audio.return_value = mock_audio
        
        mock_model = mock.MagicMock()
        mock_whisper_model.return_value = mock_model
        
        # transcribeが例外を投げる
        mock_model.transcribe.side_effect = RuntimeError("GPU メモリ不足")
        
        config = {
            "whisper": {
                "device": "cpu",
                "compute_type": "float32",
                "model": "large-v3-turbo",
                "language": "ja",
                "use_native_word_timestamps": True,
            }
        }
        
        # エラーが伝播すること
        with pytest.raises(RuntimeError) as exc_info:
            transcribe(tmp_audio_file, config)
        
        assert "GPU メモリ不足" in str(exc_info.value)
