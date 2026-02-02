"""kaiwa — CLI エントリポイント

argparse ベースのコマンドラインインターフェース。
`python -m kaiwa.cli process <audio_file>` で実行可能。
"""

from __future__ import annotations

import argparse
import sys
import time
import traceback
from pathlib import Path

from kaiwa import __version__
from kaiwa.config import load_config
from kaiwa.utils import (
    format_timestamp,
    get_keychain_password,
    notify,
    setup_logging,
    validate_audio,
)


def cmd_process(args: argparse.Namespace) -> None:
    """音声ファイルを処理するサブコマンド。"""
    logger = setup_logging()
    config = load_config()
    start_time = time.time()

    audio_path = Path(args.audio_file).resolve()

    logger.info("🎙️  kaiwa — 録音処理パイプライン")
    logger.info("入力: %s", audio_path)

    # ----- 音声ファイル検証 -----
    valid, message = validate_audio(audio_path)
    if not valid:
        logger.error("❌ 音声ファイル検証エラー: %s", message)
        notify("kaiwa ❌", f"検証エラー: {message}")
        sys.exit(1)

    # ----- API キー取得 -----
    hf_token = get_keychain_password("kaiwa", "hf-token")
    if not hf_token:
        logger.error("❌ HuggingFace トークンが見つかりません")
        notify("kaiwa ❌", "HFトークンが見つかりません")
        sys.exit(1)

    anthropic_key = get_keychain_password("kaiwa", "anthropic-api-key")
    if anthropic_key:
        logger.info("🔑 Anthropic API キー: 取得済み")
    else:
        logger.info("🔑 Anthropic API キー: 未設定（要約スキップ）")

    # ----- 中間成果物ディレクトリ -----
    work_base = Path(config.get("paths", {}).get("work", "~/Transcripts/work")).expanduser()
    stem = audio_path.stem
    work_dir = work_base / stem
    work_dir.mkdir(parents=True, exist_ok=True)
    logger.info("📁 作業ディレクトリ: %s", work_dir)

    # ----- Step 1-2: 文字起こし + アラインメント -----
    notify("kaiwa", "📝 Step 1: 文字起こし開始...")

    from kaiwa.transcribe import transcribe

    audio, result = transcribe(audio_path, config, work_dir=work_dir)

    notify("kaiwa", f"✅ 文字起こし完了 ({len(result['segments'])}セグメント)")

    # ----- Step 3: 話者分離 -----
    notify("kaiwa", "👥 Step 3: 話者分離中...")

    from kaiwa.diarize import diarize

    result = diarize(audio, result, hf_token, config, work_dir=work_dir)

    notify("kaiwa", "✅ 話者分離完了")

    # ----- 文字起こしテキストの構築 -----
    transcript_lines = []
    for seg in result["segments"]:
        speaker = seg.get("speaker", "UNKNOWN")
        start = format_timestamp(seg.get("start", 0))
        end = format_timestamp(seg.get("end", 0))
        text = seg.get("text", "").strip()
        transcript_lines.append(f"[{start} → {end}] {speaker}: {text}")

    transcript_text = "\n".join(transcript_lines)

    # ----- Step 4: 要約生成 -----
    summary = None
    title = None
    if anthropic_key:
        notify("kaiwa", "🤖 Step 4: Claude で要約生成中...")

        from kaiwa.summarize import summarize

        title, summary = summarize(transcript_text, anthropic_key, config)

        if summary:
            notify("kaiwa", f"✅ 要約生成完了: {title or '(タイトルなし)'}")
        else:
            logger.warning("⚠️ 要約生成に失敗しました")
            notify("kaiwa ⚠️", "要約生成失敗")
    else:
        logger.info("⏭️ 要約スキップ（APIキー未設定）")

    # ----- Step 5: Markdown 生成 -----
    notify("kaiwa", "📄 Step 5: Markdown 生成中...")

    from kaiwa.output import generate_markdown

    elapsed = time.time() - start_time
    output_file = generate_markdown(
        transcript_lines, summary, audio_path, elapsed, config, title=title
    )

    # ----- 完了 -----
    elapsed_min = int(elapsed) // 60
    elapsed_sec = int(elapsed) % 60
    logger.info("🎉 処理完了！（%d分%d秒）", elapsed_min, elapsed_sec)
    notify("kaiwa ✅", f"処理完了！ {output_file.name} ({elapsed_min}分{elapsed_sec}秒)")


def cmd_version(args: argparse.Namespace) -> None:
    """バージョンを表示するサブコマンド。"""
    print(f"kaiwa {__version__}")


def main() -> None:
    """メインエントリポイント。"""
    parser = argparse.ArgumentParser(
        prog="kaiwa",
        description="kaiwa — 対面会話の文字起こし・話者分離・AI要約ツール",
    )
    subparsers = parser.add_subparsers(dest="command", help="サブコマンド")

    # process サブコマンド
    process_parser = subparsers.add_parser("process", help="音声ファイルを処理する")
    process_parser.add_argument("audio_file", help="処理する音声ファイルのパス")
    process_parser.set_defaults(func=cmd_process)

    # version サブコマンド
    version_parser = subparsers.add_parser("version", help="バージョンを表示する")
    version_parser.set_defaults(func=cmd_version)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n中断されました。")
        sys.exit(130)
    except Exception as e:
        logger = setup_logging()
        logger.error("❌ 予期しないエラー: %s", e)
        logger.debug(traceback.format_exc())
        notify("kaiwa ❌", f"エラー: {e}")
        sys.exit(1)
