"""kaiwa — 話者分離モジュール

pyannote.audio を使用した話者分離（ダイアライゼーション）処理。
単語レベルの話者割り当てに基づくセグメント再分割を含む。
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
    min_speakers: int | None = None,
    max_speakers: int | None = None,
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
    min_speakers : int | None
        最小話者数。None なら自動推定。
    max_speakers : int | None
        最大話者数。None なら自動推定。

    Returns
    -------
    dict
        話者情報が付与された結果辞書。
    """
    import whisperx
    from whisperx.diarize import DiarizationPipeline

    device = config.get("whisper", {}).get("device", "cpu")
    diarize_cfg = config.get("diarize", {})

    # CLI引数 > config > 自動推定（None）の優先順位
    _min_speakers = min_speakers or diarize_cfg.get("min_speakers")
    _max_speakers = max_speakers or diarize_cfg.get("max_speakers")

    if work_dir:
        work_dir.mkdir(parents=True, exist_ok=True)

    logger.info("👥 話者分離開始...")
    if _min_speakers or _max_speakers:
        logger.info(
            "  話者数ヒント: min=%s, max=%s",
            _min_speakers or "auto",
            _max_speakers or "auto",
        )

    diarize_model = DiarizationPipeline(use_auth_token=hf_token, device=device)

    diarize_kwargs: dict[str, Any] = {}
    if _min_speakers is not None:
        diarize_kwargs["min_speakers"] = _min_speakers
    if _max_speakers is not None:
        diarize_kwargs["max_speakers"] = _max_speakers

    diarize_segments = diarize_model(audio, **diarize_kwargs)

    result = whisperx.assign_word_speakers(diarize_segments, result)

    logger.info("  ✅ 話者分離完了")

    # 中間成果物を保存（分割前）
    if work_dir:
        _save_intermediate(work_dir / "03_diarize_raw.json", result)

    # ----- セグメント再分割 -----
    original_count = len(result.get("segments", []))
    result["segments"] = _split_segments_by_speaker(result.get("segments", []))
    new_count = len(result["segments"])

    if new_count != original_count:
        logger.info(
            "  ✂️  セグメント再分割: %d → %d セグメント", original_count, new_count
        )

    # 中間成果物を保存（分割後）
    if work_dir:
        _save_intermediate(work_dir / "03_diarize.json", result)

    return result


def _split_segments_by_speaker(segments: list[dict]) -> list[dict]:
    """単語レベルの話者情報に基づき、話者交代ポイントでセグメントを分割する。

    WhisperX は単語ごとに話者を割り当てるが、セグメント単位では多数決で
    1人の話者に集約してしまう。この関数はその情報を活かして、話者が
    変わるポイントで新しいセグメントに分割する。

    Parameters
    ----------
    segments : list[dict]
        WhisperX の assign_word_speakers 出力セグメント。
        各セグメントは words リストを持ち、各 word に speaker が付与されている。

    Returns
    -------
    list[dict]
        話者交代ポイントで分割されたセグメントのリスト。
    """
    new_segments: list[dict] = []

    for seg in segments:
        words = seg.get("words", [])

        # 単語データがない場合はそのまま保持
        if not words:
            new_segments.append(seg)
            continue

        # 話者情報を持つ単語がない場合もそのまま保持
        has_speaker_info = any(w.get("speaker") for w in words)
        if not has_speaker_info:
            new_segments.append(seg)
            continue

        # 連続する同一話者の単語をグループ化
        groups: list[list[dict]] = []
        current_group: list[dict] = []
        current_speaker: str | None = None

        for word in words:
            word_speaker = word.get("speaker")

            # 話者情報がない単語は直前の話者を引き継ぐ
            if word_speaker is None:
                word_speaker = current_speaker

            if word_speaker != current_speaker and current_group:
                groups.append(current_group)
                current_group = []

            current_speaker = word_speaker
            current_group.append(word)

        if current_group:
            groups.append(current_group)

        # グループが1つなら分割不要
        if len(groups) <= 1:
            new_segments.append(seg)
            continue

        # 各グループから新しいセグメントを作成
        for group in groups:
            words_with_timing = [w for w in group if "start" in w and "end" in w]

            if words_with_timing:
                start = words_with_timing[0]["start"]
                end = words_with_timing[-1]["end"]
            else:
                # タイミング情報がない場合はスキップ
                continue

            text = "".join(w.get("word", "") for w in group).strip()
            if not text:
                continue

            speaker = group[0].get("speaker", seg.get("speaker", "UNKNOWN"))

            new_seg = {
                "start": start,
                "end": end,
                "text": text,
                "speaker": speaker,
                "words": group,
            }
            new_segments.append(new_seg)

    return new_segments


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
