"""kaiwa.__main__ のテスト"""

from __future__ import annotations

from unittest import mock


def test_main_module_calls_cli_main():
    """__main__.py が kaiwa.cli.main を呼び出すこと"""
    with mock.patch("kaiwa.cli.main") as mock_main:
        # __main__.py の内容を実行
        import runpy
        
        # SystemExit を抑制するために mock を設定
        mock_main.side_effect = SystemExit(0)
        
        try:
            runpy.run_module("kaiwa", run_name="__main__")
        except SystemExit:
            pass
        
        # main が呼ばれたこと
        assert mock_main.called
