"""kaiwa — 要約モジュール

Anthropic SDK を使用した Claude による会話要約。
429/500 エラー時の指数バックオフリトライ付き。
"""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("kaiwa")

# 要約プロンプト
SUMMARIZE_PROMPT = """以下は対面会話の文字起こしです。話者分離されています。

## 指示
1. **最初の行**に、この会話の内容を端的に表すタイトルを出力してください。形式: `TITLE: タイトル名`
   - 日本語で10〜20文字程度
   - ファイル名に使うので簡潔に（例: 「プロジェクトX進捗会議」「採用面接_田中さん」「ブレスト_新機能アイデア」）
2. 空行の後、会話の要点を箇条書きでまとめてください
3. 決定事項があれば明記してください
4. TODO/アクションアイテムがあれば抽出してください
5. 重要な発言は引用形式で残してください

## 文字起こし
"""


def _parse_title_and_summary(response: str) -> tuple[str | None, str]:
    """APIレスポンスからタイトルと要約本文を分離する。

    Parameters
    ----------
    response : str
        Claude APIのレスポンステキスト。

    Returns
    -------
    tuple[str | None, str]
        (タイトル, 要約本文)。タイトルが見つからなければ (None, 元のテキスト)。
    """
    lines = response.strip().split("\n")
    title = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.upper().startswith("TITLE:") or stripped.startswith("TITLE:"):
            title = stripped.split(":", 1)[1].strip()
            # タイトル行とその直後の空行を除去して要約本文を返す
            remaining = lines[i + 1 :]
            # 先頭の空行をスキップ
            while remaining and not remaining[0].strip():
                remaining.pop(0)
            return title, "\n".join(remaining)

    return None, response


def summarize(
    transcript_text: str,
    api_key: str,
    config: dict[str, Any],
) -> tuple[str | None, str | None]:
    """Claude API で会話の要約とタイトルを生成する。

    Parameters
    ----------
    transcript_text : str
        話者分離済みの文字起こしテキスト。
    api_key : str
        Anthropic API キー。
    config : dict
        設定辞書（claude セクションを使用）。

    Returns
    -------
    tuple[str | None, str | None]
        (タイトル, 要約テキスト)。失敗時は (None, None)。
    """
    import anthropic

    claude_cfg = config.get("claude", {})
    model = claude_cfg.get("model", "claude-3-5-haiku-latest")
    max_tokens = claude_cfg.get("max_tokens", 2048)
    timeout = claude_cfg.get("timeout", 120)
    max_retries = claude_cfg.get("max_retries", 3)

    client = anthropic.Anthropic(api_key=api_key, timeout=timeout)

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "🤖 Claude API 呼び出し (attempt %d/%d, model=%s)",
                attempt,
                max_retries,
                model,
            )

            message = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": SUMMARIZE_PROMPT + transcript_text,
                    }
                ],
            )

            raw_text = message.content[0].text
            title, summary_body = _parse_title_and_summary(raw_text)
            logger.info(
                "  ✅ 要約生成完了 (%d 文字, タイトル: %s)",
                len(summary_body),
                title or "(なし)",
            )
            return title, summary_body

        except anthropic.RateLimitError as e:
            # 429: 指数バックオフ
            wait_time = 2**attempt
            logger.warning(
                "  ⚠️ レート制限 (429): %s — %d秒後にリトライ",
                e,
                wait_time,
            )
            if attempt < max_retries:
                time.sleep(wait_time)
            else:
                logger.error("  ❌ リトライ上限に達しました (429)")
                return None, None

        except anthropic.InternalServerError as e:
            # 500: リトライ
            wait_time = 2**attempt
            logger.warning(
                "  ⚠️ サーバーエラー (500): %s — %d秒後にリトライ",
                e,
                wait_time,
            )
            if attempt < max_retries:
                time.sleep(wait_time)
            else:
                logger.error("  ❌ リトライ上限に達しました (500)")
                return None, None

        except anthropic.APIError as e:
            # その他の API エラーはリトライしない
            logger.error("  ❌ Claude API エラー: %s", e)
            return None, None

        except Exception as e:
            logger.error("  ❌ 予期しないエラー: %s", e)
            return None, None

    return None, None
