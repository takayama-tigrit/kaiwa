"""kaiwa — 設定読み込みモジュール

~/.kaiwa/config.yaml を読み込み、存在しなければデフォルト値を使用する。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# デフォルト設定
DEFAULTS: dict[str, Any] = {
    "whisper": {
        "model": "large-v3-turbo",
        "device": "cpu",  # cpu のみ対応（CTranslate2 が MPS 非対応のため）
        "compute_type": "float32",
        "language": "ja",
        "batch_size": 8,
        "use_native_word_timestamps": True,  # True=Whisper本体, False=wav2vec2
    },
    "claude": {
        "model": "claude-3-5-haiku-latest",
        "max_tokens": 2048,
        "timeout": 120,
        "max_retries": 3,
    },
    "paths": {
        "output": "~/Transcripts",
        "raw": "~/Transcripts/raw",
        "work": "~/Transcripts/work",
        "watch_dirs": [
            "~/Library/Mobile Documents/com~apple~CloudDocs/Transcripts/raw",
        ],
    },
    "diarize": {
        "min_speakers": None,  # None = 自動推定
        "max_speakers": None,  # None = 自動推定
    },
    "cleanup": {
        "work_retention_days": 7,  # 0 = 即座に削除, -1 = 削除しない
    },
}

CONFIG_PATH = Path.home() / ".kaiwa" / "config.yaml"


def _deep_merge(base: dict, override: dict) -> dict:
    """base に override の値を再帰的にマージする。"""
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _migrate_icloud_watch(cfg: dict) -> dict:
    """旧 icloud_watch 設定を watch_dirs に変換する（後方互換）。"""
    if "paths" in cfg:
        paths = cfg["paths"]
        if "icloud_watch" in paths and "watch_dirs" not in paths:
            paths["watch_dirs"] = [paths["icloud_watch"]]
        paths.pop("icloud_watch", None)
    return cfg


def _expand_paths(cfg: dict) -> dict:
    """paths セクションの ~ をホームディレクトリに展開する。"""
    if "paths" in cfg:
        for key, value in cfg["paths"].items():
            if isinstance(value, str):
                cfg["paths"][key] = str(Path(value).expanduser())
            elif isinstance(value, list):
                cfg["paths"][key] = [
                    str(Path(v).expanduser()) if isinstance(v, str) else v
                    for v in value
                ]
    return cfg


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """設定ファイルを読み込み、デフォルト値とマージして返す。

    Parameters
    ----------
    config_path : Path | None
        設定ファイルのパス。None なら ~/.kaiwa/config.yaml を使用。

    Returns
    -------
    dict[str, Any]
        マージ済みの設定辞書。
    """
    path = config_path or CONFIG_PATH
    config = DEFAULTS.copy()

    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
            if isinstance(user_config, dict):
                config = _deep_merge(DEFAULTS, user_config)
        except (yaml.YAMLError, OSError) as e:
            # 設定ファイル読み込みに失敗してもデフォルトで続行
            import logging

            logging.getLogger("kaiwa").warning(
                "設定ファイルの読み込みに失敗しました (%s): %s — デフォルト値を使用します", path, e
            )

    config = _migrate_icloud_watch(config)
    return _expand_paths(config)
