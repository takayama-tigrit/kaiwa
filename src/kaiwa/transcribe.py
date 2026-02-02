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
    # セキュリティ警告
    warnings.warn(
        "torch.load で weights_only=False を使用しています。"
        "信頼できるモデルソース（HuggingFace公式）のみを使用してください。",
        category=SecurityWarning,
        stacklevel=2
    )
    kwargs["weights_only"] = False
    return _original_torch_load(*args, **kwargs)


torch.load = _patched_torch_load

# ============================================================
# 通常の import
# ============================================================
import json
import logging
from pathlib import Path
from typing import Any

import whisperx

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

    # ----- Step 1: 文字起こし -----
    logger.info("📝 文字起こし開始 (model=%s, device=%s)", model_name, device)

    model = whisperx.load_model(
        model_name,
        device=device,
        compute_type=compute_type,
        language=language,
    )

    audio = whisperx.load_audio(str(audio_path))
    result = model.transcribe(audio, batch_size=batch_size, language=language)

    logger.info("  ✅ 文字起こし完了: %d セグメント", len(result["segments"]))

    # 中間成果物を保存
    if work_dir:
        _save_intermediate(work_dir / "01_transcribe.json", result)

    # ----- Step 2: アラインメント -----
    logger.info("⏱️  アラインメント開始...")

    align_model, align_metadata = whisperx.load_align_model(
        language_code=language, device=device
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

    # 中間成果物を保存
    if work_dir:
        _save_intermediate(work_dir / "02_align.json", result)

    return audio, result


def _save_intermediate(path: Path, data: dict) -> None:
    """中間成果物を JSON ファイルとして保存する。"""
    try:
        # ディレクトリが存在しない場合は作成
        path.parent.mkdir(parents=True, exist_ok=True)
        # segments 内の非シリアライズ可能なオブジェクトを除外
        serializable = _make_serializable(data)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)
        logger.debug("  中間成果物を保存: %s", path)
    except (TypeError, OSError) as e:
        logger.warning("  中間成果物の保存に失敗: %s — %s", path, e)
        # 重要: メイン処理は続行する（中間ファイル保存は非必須）


def _make_serializable(obj: Any) -> Any:
    """JSON シリアライズ不可能なオブジェクトを変換する。"""
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_serializable(item) for item in obj]
    elif isinstance(obj, float):
        if obj != obj:  # NaN check
            return None
        return obj
    elif isinstance(obj, (int, str, bool, type(None))):
        return obj
    else:
        return str(obj)
