"""pytest フィクスチャ定義"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_audio_file(tmp_path: Path) -> Path:
    """テスト用のダミー音声ファイル（WAV）を作成する。"""
    import wave

    audio_file = tmp_path / "test_audio.wav"
    
    # 1秒間の無音WAVファイルを生成
    with wave.open(str(audio_file), "wb") as wf:
        wf.setnchannels(1)  # モノラル
        wf.setsampwidth(2)  # 16bit
        wf.setframerate(16000)  # 16kHz
        # 1秒分のフレーム（無音）
        wf.writeframes(b"\x00\x00" * 16000)
    
    return audio_file


@pytest.fixture
def sample_config() -> dict:
    """テスト用の設定辞書を返す。"""
    return {
        "whisper": {
            "model": "large-v3-turbo",
            "device": "cpu",
            "compute_type": "float32",
            "language": "ja",
            "batch_size": 8,
        },
        "claude": {
            "model": "claude-3-5-haiku-latest",
            "max_tokens": 2048,
            "timeout": 120,
            "max_retries": 3,
        },
        "paths": {
            "output": "/tmp/test_output",
            "raw": "/tmp/test_raw",
            "work": "/tmp/test_work",
        },
    }


@pytest.fixture
def sample_transcript_lines() -> list[str]:
    """テスト用の文字起こし行リストを返す。"""
    return [
        "[00:00 → 00:05] SPEAKER_00: こんにちは。今日は会議を始めます。",
        "[00:05 → 00:10] SPEAKER_01: よろしくお願いします。",
        "[00:10 → 00:15] SPEAKER_00: まず最初の議題についてです。",
    ]
