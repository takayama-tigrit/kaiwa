"""kaiwa — 文字起こしモジュール

WhisperX を使用した音声文字起こし + アラインメント処理。
"""

from __future__ import annotations

# ============================================================
# torch.load パッチ（PyTorch 2.8 + pyannote 互換性のため）
# 必ず他の import より前に適用すること
# ============================================================
import torch
import warnings

_original_torch_load = torch.load


def _patched_torch_load(*args, **kwargs):
    # セキュリティ警告（初回のみ）
    warnings.warn(
        "torch.load で weights_only=False を使用しています。"
        "信頼できるモデルソース（HuggingFace公式）のみを使用してください。",
        category=RuntimeWarning,
        stacklevel=2
    )
    kwargs["weights_only"] = False
    return _original_torch_load(*args, **kwargs)


torch.load = _patched_torch_load

# ============================================================
# 通常の import（torch.load パッチの後に配置する必要がある）
# ============================================================
import logging  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

import whisperx  # noqa: E402

from kaiwa.utils import _save_intermediate  # noqa: E402

logger = logging.getLogger("kaiwa")


def transcribe(
    audio_path: Path,
    config: dict[str, Any],
    work_dir: Path | None = None,
) -> tuple[Any, dict[str, Any]]:
    """音声ファイルを WhisperX で文字起こし + アラインメントする。

    Parameters
    ----------
    audio_path : Path
        入力音声ファイルのパス。
    config : dict
        設定辞書（whisper セクションを使用）。
    work_dir : Path | None
        中間成果物の保存先ディレクトリ。None なら保存しない。

    Returns
    -------
    tuple[Any, dict]
        (audio データ, アラインメント済み result 辞書)。
    """
    whisper_cfg = config.get("whisper", {})
    device = whisper_cfg.get("device", "cpu")
    compute_type = whisper_cfg.get("compute_type", "float32")
    model_name = whisper_cfg.get("model", "large-v3-turbo")
    language = whisper_cfg.get("language", "ja")
    batch_size = whisper_cfg.get("batch_size", 8)

    if work_dir:
        work_dir.mkdir(parents=True, exist_ok=True)

    use_native_timestamps = whisper_cfg.get("use_native_word_timestamps", True)

    # whisperx.load_audio は diarize.py でも使うので常に実行
    audio = whisperx.load_audio(str(audio_path))

    if use_native_timestamps:
        # ----- faster-whisper 直接モード（word_timestamps 対応） -----
        result = _transcribe_with_native_timestamps(
            audio_path, audio, model_name, device, compute_type, language,
        )
    else:
        # ----- WhisperX バッチモード + wav2vec2 アラインメント -----
        result = _transcribe_with_whisperx(
            audio, audio_path, model_name, device, compute_type, language, batch_size,
        )

    logger.info("  ✅ 文字起こし完了: %d セグメント", len(result["segments"]))

    # 中間成果物を保存
    if work_dir:
        _save_intermediate(work_dir / "01_transcribe.json", result)

    return audio, result


def _transcribe_with_native_timestamps(
    audio_path: Path,
    audio: Any,
    model_name: str,
    device: str,
    compute_type: str,
    language: str,
) -> dict[str, Any]:
    """faster-whisper を直接使い、cross-attention ベースの word_timestamps を取得する。

    WhisperX のバッチパイプラインは word_timestamps に対応していないため、
    faster-whisper の transcribe() を直接呼び出す。
    """
    import faster_whisper

    logger.info(
        "📝 文字起こし開始 — native word_timestamps (model=%s, device=%s)",
        model_name, device,
    )

    model = faster_whisper.WhisperModel(
        model_name, device=device, compute_type=compute_type,
    )

    segments_gen, info = model.transcribe(
        str(audio_path),
        language=language,
        word_timestamps=True,
        vad_filter=True,  # VAD でノイズ区間をスキップ
    )

    segments: list[dict[str, Any]] = []
    for seg in segments_gen:
        words = []
        if seg.words:
            for w in seg.words:
                words.append({
                    "word": w.word,
                    "start": w.start,
                    "end": w.end,
                    "score": w.probability,
                })

        segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
            "words": words,
        })

    logger.info("  ⏱️  アラインメント不要（native word_timestamps 使用）")

    return {"segments": segments, "language": info.language}


def _transcribe_with_whisperx(
    audio: Any,
    audio_path: Path,
    model_name: str,
    device: str,
    compute_type: str,
    language: str,
    batch_size: int,
) -> dict[str, Any]:
    """WhisperX バッチパイプライン + wav2vec2 アラインメント（従来方式）。"""
    logger.info(
        "📝 文字起こし開始 — WhisperX batch + wav2vec2 align (model=%s, device=%s)",
        model_name, device,
    )

    model = whisperx.load_model(
        model_name,
        device=device,
        compute_type=compute_type,
        language=language,
    )

    result = model.transcribe(audio, batch_size=batch_size, language=language)

    logger.info("⏱️  アラインメント開始（wav2vec2）...")

    align_model, align_metadata = whisperx.load_align_model(
        language_code=language, device=device,
    )
    result = whisperx.align(
        result["segments"],
        align_model,
        align_metadata,
        audio,
        device=device,
        return_char_alignments=False,
    )

    logger.info("  ✅ アラインメント完了")

    return result
