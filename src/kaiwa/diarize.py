"""kaiwa — 話者分離モジュール

pyannote.audio を使用した話者分離（ダイアライゼーション）処理。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("kaiwa")


def diarize(
    audio: Any,
    result: dict[str, Any],
    hf_token: str,
    config: dict[str, Any],
    work_dir: Path | None = None,
) -> dict[str, Any]:
    """話者分離を実行し、セグメントに話者情報を付与する。

    Parameters
    ----------
    audio : Any
        whisperx.load_audio() で読み込んだ音声データ。
    result : dict
        アラインメント済みの結果辞書（segments を含む）。
    hf_token : str
        HuggingFace のアクセストークン。
    config : dict
        設定辞書。
    work_dir : Path | None
        中間成果物の保存先ディレクトリ。None なら保存しない。

    Returns
    -------
    dict
        話者情報が付与された結果辞書。
    """
    import whisperx
    from whisperx.diarize import DiarizationPipeline

    device = config.get("whisper", {}).get("device", "cpu")

    if work_dir:
        work_dir.mkdir(parents=True, exist_ok=True)

    logger.info("👥 話者分離開始...")

    diarize_model = DiarizationPipeline(use_auth_token=hf_token, device=device)
    diarize_segments = diarize_model(audio)

    result = whisperx.assign_word_speakers(diarize_segments, result)

    logger.info("  ✅ 話者分離完了")

    # 中間成果物を保存
    if work_dir:
        _save_intermediate(work_dir / "03_diarize.json", result)

    return result


def _save_intermediate(path: Path, data: dict) -> None:
    """中間成果物を JSON ファイルとして保存する。"""
    try:
        serializable = _make_serializable(data)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)
        logger.debug("  中間成果物を保存: %s", path)
    except (TypeError, OSError) as e:
        logger.warning("  中間成果物の保存に失敗: %s — %s", path, e)


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
