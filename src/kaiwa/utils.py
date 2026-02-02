"""kaiwa — ユーティリティモジュール

ログ設定、macOS 通知、Keychain アクセス、音声検証など共通機能を提供する。
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import wave
from datetime import datetime
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# セキュアな文字列ラッパー
# ---------------------------------------------------------------------------


class SecureString:
    """セキュアな文字列ラッパー（ログ出力時にマスク）"""

    def __init__(self, value: str):
        self._value = value

    def get(self) -> str:
        return self._value

    def __str__(self) -> str:
        return "***REDACTED***"

    def __repr__(self) -> str:
        return "SecureString(***)"

# ---------------------------------------------------------------------------
# ログ設定
# ---------------------------------------------------------------------------

LOG_DIR = Path.home() / ".kaiwa" / "logs"


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """ファイル + stdout の二系統ロガーを設定する。

    ログファイルは ~/.kaiwa/logs/YYYY-MM-DD.log に出力される。

    Returns
    -------
    logging.Logger
        設定済みの 'kaiwa' ロガー。
    """
    # ディレクトリを 0o700 で作成（所有者のみアクセス可能）
    LOG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)

    logger = logging.getLogger("kaiwa")
    logger.setLevel(level)

    # 既にハンドラーがあれば追加しない
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # stdout ハンドラー
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # ファイルハンドラー（日次ローテーション）
    log_file = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # ファイル作成前に umask を設定（0o600 = 所有者のみ読み書き）
    old_umask = os.umask(0o077)
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    finally:
        os.umask(old_umask)
    
    # 既存ファイルのパーミッションも修正
    if log_file.exists():
        log_file.chmod(0o600)

    return logger


# ---------------------------------------------------------------------------
# macOS 通知
# ---------------------------------------------------------------------------


def notify(title: str, message: str) -> None:
    """macOS 通知を表示する。heredoc でエスケープ安全に処理する。"""
    try:
        # heredoc を使い、タイトルとメッセージの特殊文字をエスケープ不要にする
        script = f"""osascript <<'KAIWA_NOTIFY_EOF'
display notification "{_escape_applescript(message)}" with title "{_escape_applescript(title)}"
KAIWA_NOTIFY_EOF"""
        subprocess.run(
            ["bash", "-c", script],
            check=False,
            capture_output=True,
            timeout=5,
        )
    except Exception:
        pass


def _escape_applescript(text: str) -> str:
    """AppleScript 文字列内の特殊文字をエスケープする。"""
    return text.replace("\\", "\\\\").replace('"', '\\"')


# ---------------------------------------------------------------------------
# Keychain アクセス
# ---------------------------------------------------------------------------


def get_keychain_password(account: str, service: str) -> str | None:
    """macOS Keychain からパスワードを取得する。

    Parameters
    ----------
    account : str
        Keychain のアカウント名（例: "kaiwa"）。
    service : str
        Keychain のサービス名（例: "hf-token"）。

    Returns
    -------
    str | None
        パスワード文字列。見つからなければ None。
    """
    logger = logging.getLogger("kaiwa")
    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-a",
                account,
                "-s",
                service,
                "-w",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        logger.error("❌ Keychainアクセスがタイムアウトしました（10秒）")
        return None
    except subprocess.CalledProcessError as e:
        if "could not be found" in e.stderr:
            logger.debug("Keychainにキーが見つかりません: account=%s, service=%s", account, service)
        else:
            logger.error("❌ Keychainアクセスエラー: %s", e.stderr)
        return None
    except Exception as e:
        logger.error("❌ 予期しないKeychainエラー: %s", e)
        return None


# ---------------------------------------------------------------------------
# タイムスタンプ
# ---------------------------------------------------------------------------


def format_timestamp(seconds: float) -> str:
    """秒数を MM:SS または H:MM:SS 形式にフォーマットする。

    1 時間を超える場合は H:MM:SS 形式になる。
    """
    total = int(seconds)
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


# ---------------------------------------------------------------------------
# 音声ファイル検証
# ---------------------------------------------------------------------------

MIN_FILE_SIZE = 1024  # 1KB
MIN_DURATION_SECONDS = 1.0


def validate_audio(path: Path) -> tuple[bool, str]:
    """音声ファイルの基本的な妥当性を検証する。

    Parameters
    ----------
    path : Path
        音声ファイルのパス。

    Returns
    -------
    tuple[bool, str]
        (検証結果, メッセージ)。
    """
    if not path.exists():
        return False, f"ファイルが見つかりません: {path}"

    # サイズチェック（1KB 未満は拒否）
    file_size = path.stat().st_size
    if file_size < MIN_FILE_SIZE:
        return False, f"ファイルサイズが小さすぎます: {file_size} bytes（最小 {MIN_FILE_SIZE} bytes）"

    # WAV ファイルの読み込みテスト + 長さチェック
    if path.suffix.lower() == ".wav":
        try:
            with wave.open(str(path), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate <= 0:
                    return False, "無効なサンプルレートです"
                duration = frames / rate
                if duration < MIN_DURATION_SECONDS:
                    return False, f"音声が短すぎます: {duration:.1f}秒（最小 {MIN_DURATION_SECONDS}秒）"
        except wave.Error as e:
            return False, f"WAV ファイルの読み込みに失敗しました: {e}"
    else:
        # WAV 以外のフォーマットは基本的なサイズチェックのみ
        # WhisperX の load_audio が対応しているかは実行時に判明する
        pass

    return True, "OK"


# ---------------------------------------------------------------------------
# 中間成果物の保存
# ---------------------------------------------------------------------------


def _save_intermediate(path: Path, data: dict) -> None:
    """中間成果物を JSON ファイルとして保存する。"""
    logger = logging.getLogger("kaiwa")
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
