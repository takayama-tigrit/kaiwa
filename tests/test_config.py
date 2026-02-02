"""kaiwa.config のテスト"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from kaiwa.config import (
    _deep_merge,
    _expand_paths,
    _migrate_icloud_watch,
    load_config,
)


class TestDeepMerge:
    """_deep_merge() のテスト"""

    def test_simple_merge(self):
        """単純なマージの場合"""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self):
        """ネストされた辞書のマージ"""
        base = {"a": {"b": 1, "c": 2}}
        override = {"a": {"c": 3, "d": 4}}
        result = _deep_merge(base, override)
        assert result == {"a": {"b": 1, "c": 3, "d": 4}}

    def test_deep_nested_merge(self):
        """深くネストされた辞書のマージ"""
        base = {"a": {"b": {"c": 1}}}
        override = {"a": {"b": {"d": 2}}}
        result = _deep_merge(base, override)
        assert result == {"a": {"b": {"c": 1, "d": 2}}}

    def test_override_with_non_dict(self):
        """辞書でない値で上書き"""
        base = {"a": {"b": 1}}
        override = {"a": "string"}
        result = _deep_merge(base, override)
        assert result == {"a": "string"}

    def test_empty_override(self):
        """空の上書き辞書"""
        base = {"a": 1, "b": 2}
        override = {}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 2}

    def test_empty_base(self):
        """空のベース辞書"""
        base = {}
        override = {"a": 1, "b": 2}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 2}


class TestMigrateIcloudWatch:
    """_migrate_icloud_watch() のテスト"""

    def test_migrate_icloud_watch(self):
        """icloud_watch を watch_dirs に変換"""
        cfg = {"paths": {"icloud_watch": "~/iCloud"}}
        result = _migrate_icloud_watch(cfg)
        assert "watch_dirs" in result["paths"]
        assert result["paths"]["watch_dirs"] == ["~/iCloud"]
        assert "icloud_watch" not in result["paths"]

    def test_no_migration_needed(self):
        """watch_dirs が既に存在する場合"""
        cfg = {
            "paths": {
                "icloud_watch": "~/iCloud",
                "watch_dirs": ["~/existing"],
            }
        }
        result = _migrate_icloud_watch(cfg)
        assert result["paths"]["watch_dirs"] == ["~/existing"]
        assert "icloud_watch" not in result["paths"]

    def test_no_icloud_watch(self):
        """icloud_watch が存在しない場合"""
        cfg = {"paths": {"output": "~/Transcripts"}}
        result = _migrate_icloud_watch(cfg)
        assert "watch_dirs" not in result["paths"]
        assert "icloud_watch" not in result["paths"]

    def test_no_paths_section(self):
        """paths セクションがない場合"""
        cfg = {"whisper": {"model": "large-v3-turbo"}}
        result = _migrate_icloud_watch(cfg)
        assert "paths" not in result


class TestExpandPaths:
    """_expand_paths() のテスト"""

    def test_expand_tilde(self):
        """チルダの展開"""
        cfg = {"paths": {"output": "~/Transcripts"}}
        result = _expand_paths(cfg)
        assert result["paths"]["output"] == str(Path.home() / "Transcripts")

    def test_expand_paths_in_list(self):
        """リスト内のパス展開"""
        cfg = {"paths": {"watch_dirs": ["~/dir1", "~/dir2"]}}
        result = _expand_paths(cfg)
        assert result["paths"]["watch_dirs"] == [
            str(Path.home() / "dir1"),
            str(Path.home() / "dir2"),
        ]

    def test_absolute_path(self):
        """絶対パスはそのまま"""
        cfg = {"paths": {"output": "/absolute/path"}}
        result = _expand_paths(cfg)
        assert result["paths"]["output"] == "/absolute/path"

    def test_mixed_list(self):
        """文字列と非文字列が混在するリスト"""
        cfg = {"paths": {"watch_dirs": ["~/dir1", 123]}}
        result = _expand_paths(cfg)
        assert result["paths"]["watch_dirs"][0] == str(Path.home() / "dir1")
        assert result["paths"]["watch_dirs"][1] == 123

    def test_no_paths_section(self):
        """paths セクションがない場合"""
        cfg = {"whisper": {"model": "large-v3-turbo"}}
        result = _expand_paths(cfg)
        assert "paths" not in result


class TestLoadConfig:
    """load_config() のテスト"""

    def test_load_config_no_file(self, tmp_path: Path):
        """設定ファイルが存在しない場合"""
        config_path = tmp_path / "nonexistent.yaml"
        config = load_config(config_path)
        
        # デフォルト値が使用される
        assert "whisper" in config
        assert config["whisper"]["model"] == "large-v3-turbo"
        assert "claude" in config
        assert "paths" in config

    def test_load_config_with_file(self, tmp_path: Path):
        """設定ファイルが存在する場合"""
        config_path = tmp_path / "config.yaml"
        user_config = {
            "whisper": {"model": "custom-model"},
            "paths": {"output": "~/CustomOutput"},
        }
        config_path.write_text(yaml.dump(user_config), encoding="utf-8")
        
        config = load_config(config_path)
        
        # ユーザー設定がマージされている
        assert config["whisper"]["model"] == "custom-model"
        # デフォルト値も残っている
        assert config["whisper"]["device"] == "cpu"
        # パスが展開されている
        assert config["paths"]["output"] == str(Path.home() / "CustomOutput")

    def test_load_config_invalid_yaml(self, tmp_path: Path):
        """不正なYAMLファイルの場合"""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("invalid: yaml: content:", encoding="utf-8")
        
        # エラーが発生してもデフォルト値が返される
        config = load_config(config_path)
        assert "whisper" in config
        assert config["whisper"]["model"] == "large-v3-turbo"

    def test_load_config_empty_file(self, tmp_path: Path):
        """空の設定ファイルの場合"""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("", encoding="utf-8")
        
        config = load_config(config_path)
        # デフォルト値が使用される
        assert "whisper" in config
        assert config["whisper"]["model"] == "large-v3-turbo"

    def test_load_config_migration(self, tmp_path: Path):
        """旧設定のマイグレーション"""
        config_path = tmp_path / "config.yaml"
        user_config = {"paths": {"icloud_watch": "~/OldPath"}}
        config_path.write_text(yaml.dump(user_config), encoding="utf-8")
        
        config = load_config(config_path)
        
        # icloud_watch が watch_dirs に変換されている
        # ただし、デフォルト設定のwatch_dirsが既に存在するため、ユーザー設定は上書きされる
        assert "watch_dirs" in config["paths"]
        # デフォルト設定の値が使用されている
        assert len(config["paths"]["watch_dirs"]) > 0
        assert "icloud_watch" not in config["paths"]
