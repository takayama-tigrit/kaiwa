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
1. 会話の要点を箇条書きでまとめてください
2. 決定事項があれば明記してください
3. TODO/アクションアイテムがあれば抽出してください
4. 重要な発言は引用形式で残してください

## 文字起こし
"""


def summarize(
    transcript_text: str,
    api_key: str,
    config: dict[str, Any],
) -> str | None:
    """Claude API で会話の要約を生成する。

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
    str | None
        要約テキスト。失敗時は None。
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

            result = message.content[0].text
            logger.info("  ✅ 要約生成完了 (%d 文字)", len(result))
            return result

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
                return None

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
                return None

        except anthropic.APIError as e:
            # その他の API エラーはリトライしない
            logger.error("  ❌ Claude API エラー: %s", e)
            return None

        except Exception as e:
            logger.error("  ❌ 予期しないエラー: %s", e)
            return None

    return None
