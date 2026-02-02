"""kaiwa — 出力モジュール

処理結果を Markdown ファイルとして生成・保存する。
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("kaiwa")


def _sanitize_filename(title: str) -> str:
    """タイトルをファイル名に安全な文字列に変換する。"""
    import re
    # ファイル名に使えない文字を除去/置換
    sanitized = re.sub(r'[\\/:*?"<>|]', '', title)
    sanitized = sanitized.replace(" ", "_").replace("　", "_")
    # 長すぎる場合は切り詰め
    if len(sanitized) > 50:
        sanitized = sanitized[:50]
    return sanitized.strip("_")


def generate_markdown(
    transcript_lines: list[str],
    summary: str | None,
    audio_path: Path,
    elapsed: float,
    config: dict[str, Any],
    title: str | None = None,
) -> Path:
    """処理結果を Markdown ファイルとして保存する。

    Parameters
    ----------
    transcript_lines : list[str]
        話者分離済みの文字起こし行リスト。
    summary : str | None
        Claude による要約テキスト。None なら要約セクションをスキップ表記にする。
    audio_path : Path
        元の音声ファイルのパス。
    elapsed : float
        処理にかかった秒数。
    config : dict
        設定辞書。
    title : str | None
        会話のタイトル。ファイル名に使用。None なら日時のみ。

    Returns
    -------
    Path
        生成された Markdown ファイルのパス。
    """
    now = datetime.now()
    output_dir = Path(config.get("paths", {}).get("output", "~/Transcripts")).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    # ファイル名: YYYYMMDD_タイトル.md（タイトルなしなら YYYYMMDD_HHMMSS.md）
    date_prefix = now.strftime('%Y%m%d')
    if title:
        safe_title = _sanitize_filename(title)
        output_file = output_dir / f"{date_prefix}_{safe_title}.md"
    else:
        output_file = output_dir / f"{date_prefix}_{now.strftime('%H%M%S')}.md"

    elapsed_min = int(elapsed) // 60
    elapsed_sec = int(elapsed) % 60

    transcript_text = "\n".join(transcript_lines)
    summary_text = summary if summary else "_要約スキップ（APIキー未設定またはエラー）_"

    whisper_model = config.get("whisper", {}).get("model", "large-v3-turbo")
    claude_model = config.get("claude", {}).get("model", "claude-3-5-haiku-latest")

    heading_title = title if title else now.strftime('%Y-%m-%d %H:%M')
    md_content = f"""# {heading_title}

## 📋 要約

{summary_text}

## 💬 全文（話者分離済み）

{transcript_text}

---
*処理: WhisperX {whisper_model} + Claude {claude_model}*
*元ファイル: {audio_path.name}*
*処理時間: {elapsed_min}分{elapsed_sec}秒*
*生成: kaiwa v0.1.0*
"""

    output_file.write_text(md_content, encoding="utf-8")
    logger.info("📄 Markdown 保存先: %s", output_file)

    return output_file
