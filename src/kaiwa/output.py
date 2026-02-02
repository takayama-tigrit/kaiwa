"""kaiwa — 出力モジュール

処理結果を Markdown ファイルとして生成・保存する。
"""

from __future__ import annotations

import errno
import logging
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from kaiwa import __version__

logger = logging.getLogger("kaiwa")


def _sanitize_filename(title: str) -> str:
    """タイトルをファイル名に安全な文字列に変換する。"""
    # Unicode正規化 + 制御文字除去
    normalized = unicodedata.normalize('NFKC', title)
    sanitized = ''.join(c for c in normalized if unicodedata.category(c)[0] != 'C')
    
    # ファイルシステム禁止文字の除去
    sanitized = re.sub(r'[\\/:*?"<>|]', '', sanitized)
    sanitized = re.sub(r'\s+', '_', sanitized)  # 連続空白を1つの_に
    sanitized = re.sub(r'_+', '_', sanitized)   # 連続_を1つに
    
    # 拡張子の除去（誤認識防止）
    sanitized = re.sub(r'\.(md|txt|pdf|doc)$', '', sanitized, flags=re.IGNORECASE)
    
    # 長さ制限（Unicodeで50文字）
    if len(sanitized) > 50:
        sanitized = sanitized[:50]
    
    return sanitized.strip('_.-')  # 先頭末尾のゴミ除去


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
*生成: kaiwa v{__version__}*
"""

    try:
        output_file.write_text(md_content, encoding="utf-8")
        logger.info("📄 Markdown 保存先: %s", output_file)
    except OSError as e:
        if e.errno == errno.ENOSPC:  # Disk full
            logger.error("❌ ディスク容量不足: %s", output_file)
            from kaiwa.utils import notify
            notify("kaiwa ❌", "ディスク容量不足")
            # 部分ファイルの削除
            if output_file.exists():
                output_file.unlink()
        raise

    return output_file
