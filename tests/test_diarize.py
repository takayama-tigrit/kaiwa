"""kaiwa.diarize のテスト"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from kaiwa.diarize import _split_segments_by_speaker, diarize


class TestSplitSegmentsBySpeaker:
    """_split_segments_by_speaker() のテスト"""

    def test_no_words(self):
        """単語データがないセグメントはそのまま返す"""
        segments = [
            {
                "start": 0.0,
                "end": 5.0,
                "text": "こんにちは",
                "speaker": "SPEAKER_00",
            }
        ]
        result = _split_segments_by_speaker(segments)
        assert len(result) == 1
        assert result[0] == segments[0]

    def test_no_speaker_info(self):
        """話者情報がない単語はそのまま返す"""
        segments = [
            {
                "start": 0.0,
                "end": 5.0,
                "text": "こんにちは",
                "speaker": "SPEAKER_00",
                "words": [
                    {"word": "こんにちは", "start": 0.0, "end": 5.0}
                ],
            }
        ]
        result = _split_segments_by_speaker(segments)
        assert len(result) == 1
        assert result[0] == segments[0]

    def test_single_speaker(self):
        """単一話者のセグメントは分割しない"""
        segments = [
            {
                "start": 0.0,
                "end": 5.0,
                "text": "こんにちは世界",
                "speaker": "SPEAKER_00",
                "words": [
                    {"word": "こんにちは", "start": 0.0, "end": 2.5, "speaker": "SPEAKER_00"},
                    {"word": "世界", "start": 2.5, "end": 5.0, "speaker": "SPEAKER_00"},
                ],
            }
        ]
        result = _split_segments_by_speaker(segments)
        assert len(result) == 1

    def test_multiple_speakers(self):
        """複数話者のセグメントは話者交代ポイントで分割する"""
        segments = [
            {
                "start": 0.0,
                "end": 10.0,
                "text": "こんにちはこんばんは",
                "speaker": "SPEAKER_00",
                "words": [
                    {"word": "こんにちは", "start": 0.0, "end": 5.0, "speaker": "SPEAKER_00"},
                    {"word": "こんばんは", "start": 5.0, "end": 10.0, "speaker": "SPEAKER_01"},
                ],
            }
        ]
        result = _split_segments_by_speaker(segments)
        
        assert len(result) == 2
        
        # 最初のセグメント（SPEAKER_00）
        assert result[0]["speaker"] == "SPEAKER_00"
        assert result[0]["text"] == "こんにちは"
        assert result[0]["start"] == 0.0
        assert result[0]["end"] == 5.0
        
        # 2番目のセグメント（SPEAKER_01）
        assert result[1]["speaker"] == "SPEAKER_01"
        assert result[1]["text"] == "こんばんは"
        assert result[1]["start"] == 5.0
        assert result[1]["end"] == 10.0

    def test_word_without_speaker_inherits_previous(self):
        """話者情報なしの単語は直前の話者を引き継ぐ"""
        segments = [
            {
                "start": 0.0,
                "end": 15.0,
                "text": "こんにちは世界です",
                "speaker": "SPEAKER_00",
                "words": [
                    {"word": "こんにちは", "start": 0.0, "end": 5.0, "speaker": "SPEAKER_00"},
                    {"word": "世界", "start": 5.0, "end": 10.0},  # 話者情報なし
                    {"word": "です", "start": 10.0, "end": 15.0, "speaker": "SPEAKER_00"},
                ],
            }
        ]
        result = _split_segments_by_speaker(segments)
        
        # 全て同じ話者なので分割されない
        assert len(result) == 1
        assert result[0]["speaker"] == "SPEAKER_00"

    def test_word_without_timing_skipped(self):
        """タイミング情報なしの単語グループはスキップ"""
        segments = [
            {
                "start": 0.0,
                "end": 10.0,
                "text": "こんにちはこんばんは",
                "speaker": "SPEAKER_00",
                "words": [
                    {"word": "こんにちは", "speaker": "SPEAKER_00"},  # start/end なし
                    {"word": "こんばんは", "start": 5.0, "end": 10.0, "speaker": "SPEAKER_01"},
                ],
            }
        ]
        result = _split_segments_by_speaker(segments)
        
        # タイミング情報がないグループはスキップされる
        assert len(result) == 1
        assert result[0]["speaker"] == "SPEAKER_01"
        assert result[0]["text"] == "こんばんは"

    def test_empty_text_skipped(self):
        """空テキストのグループはスキップ"""
        segments = [
            {
                "start": 0.0,
                "end": 10.0,
                "text": "こんにちは",
                "speaker": "SPEAKER_00",
                "words": [
                    {"word": "", "start": 0.0, "end": 5.0, "speaker": "SPEAKER_00"},
                    {"word": "こんにちは", "start": 5.0, "end": 10.0, "speaker": "SPEAKER_01"},
                ],
            }
        ]
        result = _split_segments_by_speaker(segments)
        
        # 空テキストはスキップされる
        assert len(result) == 1
        assert result[0]["text"] == "こんにちは"

    def test_complex_speaker_changes(self):
        """複数回話者が交代する場合"""
        segments = [
            {
                "start": 0.0,
                "end": 20.0,
                "text": "ABCD",
                "speaker": "SPEAKER_00",
                "words": [
                    {"word": "A", "start": 0.0, "end": 5.0, "speaker": "SPEAKER_00"},
                    {"word": "B", "start": 5.0, "end": 10.0, "speaker": "SPEAKER_01"},
                    {"word": "C", "start": 10.0, "end": 15.0, "speaker": "SPEAKER_00"},
                    {"word": "D", "start": 15.0, "end": 20.0, "speaker": "SPEAKER_01"},
                ],
            }
        ]
        result = _split_segments_by_speaker(segments)
        
        assert len(result) == 4
        assert result[0]["speaker"] == "SPEAKER_00"
        assert result[1]["speaker"] == "SPEAKER_01"
        assert result[2]["speaker"] == "SPEAKER_00"
        assert result[3]["speaker"] == "SPEAKER_01"


class TestDiarize:
    """diarize() のテスト"""

    @mock.patch("whisperx.assign_word_speakers")
    @mock.patch("whisperx.diarize.DiarizationPipeline")
    def test_diarize_basic(self, mock_pipeline_class, mock_assign_speakers):
        """基本的な話者分離が動作すること"""
        # モックの設定
        mock_pipeline = mock.MagicMock()
        mock_pipeline_class.return_value = mock_pipeline
        mock_pipeline.return_value = mock.MagicMock()  # diarize_segments
        
        mock_result = {
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "こんにちは",
                    "speaker": "SPEAKER_00",
                    "words": [
                        {"word": "こんにちは", "start": 0.0, "end": 5.0, "speaker": "SPEAKER_00"}
                    ],
                }
            ]
        }
        mock_assign_speakers.return_value = mock_result
        
        audio = mock.MagicMock()
        result = {"segments": []}
        config = {"whisper": {"device": "cpu"}, "diarize": {}}
        
        # 実行
        output = diarize(audio, result, "hf-token", config)
        
        # DiarizationPipeline がインスタンス化されたこと
        mock_pipeline_class.assert_called_once_with(use_auth_token="hf-token", device="cpu")
        
        # diarize_model が呼ばれたこと
        assert mock_pipeline.called
        
        # assign_word_speakers が呼ばれたこと
        assert mock_assign_speakers.called
        
        # 結果が返されること
        assert "segments" in output

    @mock.patch("kaiwa.diarize._save_intermediate")
    @mock.patch("whisperx.assign_word_speakers")
    @mock.patch("whisperx.diarize.DiarizationPipeline")
    def test_diarize_with_work_dir(
        self, mock_pipeline_class, mock_assign_speakers, mock_save, tmp_path
    ):
        """work_dir指定時に中間ファイルが保存されること"""
        # モックの設定
        mock_pipeline = mock.MagicMock()
        mock_pipeline_class.return_value = mock_pipeline
        mock_pipeline.return_value = mock.MagicMock()
        
        mock_result = {
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "こんにちは",
                    "speaker": "SPEAKER_00",
                    "words": [
                        {"word": "こんにちは", "start": 0.0, "end": 5.0, "speaker": "SPEAKER_00"}
                    ],
                }
            ]
        }
        mock_assign_speakers.return_value = mock_result
        
        audio = mock.MagicMock()
        result = {"segments": []}
        config = {"whisper": {"device": "cpu"}, "diarize": {}}
        work_dir = tmp_path / "work"
        
        # 実行
        diarize(audio, result, "hf-token", config, work_dir=work_dir)
        
        # _save_intermediate が2回呼ばれたこと（分割前と分割後）
        assert mock_save.call_count == 2

    @mock.patch("whisperx.assign_word_speakers")
    @mock.patch("whisperx.diarize.DiarizationPipeline")
    def test_diarize_with_speaker_hints(self, mock_pipeline_class, mock_assign_speakers):
        """min_speakers/max_speakers のヒントが渡されること"""
        # モックの設定
        mock_pipeline = mock.MagicMock()
        mock_pipeline_class.return_value = mock_pipeline
        mock_pipeline.return_value = mock.MagicMock()
        
        mock_result = {"segments": []}
        mock_assign_speakers.return_value = mock_result
        
        audio = mock.MagicMock()
        result = {"segments": []}
        config = {"whisper": {"device": "cpu"}, "diarize": {}}
        
        # 実行
        diarize(
            audio,
            result,
            "hf-token",
            config,
            min_speakers=2,
            max_speakers=4,
        )
        
        # diarize_model が min_speakers/max_speakers 付きで呼ばれたこと
        call_kwargs = mock_pipeline.call_args[1]
        assert call_kwargs["min_speakers"] == 2
        assert call_kwargs["max_speakers"] == 4

    @mock.patch("whisperx.assign_word_speakers")
    @mock.patch("whisperx.diarize.DiarizationPipeline")
    def test_diarize_config_speaker_hints(self, mock_pipeline_class, mock_assign_speakers):
        """configから話者数ヒントが取得されること"""
        # モックの設定
        mock_pipeline = mock.MagicMock()
        mock_pipeline_class.return_value = mock_pipeline
        mock_pipeline.return_value = mock.MagicMock()
        
        mock_result = {"segments": []}
        mock_assign_speakers.return_value = mock_result
        
        audio = mock.MagicMock()
        result = {"segments": []}
        config = {
            "whisper": {"device": "cpu"},
            "diarize": {"min_speakers": 3, "max_speakers": 5},
        }
        
        # 実行（CLI引数なし）
        diarize(audio, result, "hf-token", config)
        
        # config の値が使われること
        call_kwargs = mock_pipeline.call_args[1]
        assert call_kwargs["min_speakers"] == 3
        assert call_kwargs["max_speakers"] == 5

    @mock.patch("whisperx.assign_word_speakers")
    @mock.patch("whisperx.diarize.DiarizationPipeline")
    def test_diarize_cli_overrides_config(self, mock_pipeline_class, mock_assign_speakers):
        """CLI引数がconfigより優先されること"""
        # モックの設定
        mock_pipeline = mock.MagicMock()
        mock_pipeline_class.return_value = mock_pipeline
        mock_pipeline.return_value = mock.MagicMock()
        
        mock_result = {"segments": []}
        mock_assign_speakers.return_value = mock_result
        
        audio = mock.MagicMock()
        result = {"segments": []}
        config = {
            "whisper": {"device": "cpu"},
            "diarize": {"min_speakers": 3, "max_speakers": 5},
        }
        
        # 実行（CLI引数で上書き）
        diarize(audio, result, "hf-token", config, min_speakers=2)
        
        # CLI引数が優先されること
        call_kwargs = mock_pipeline.call_args[1]
        assert call_kwargs["min_speakers"] == 2
        assert call_kwargs["max_speakers"] == 5  # configの値
