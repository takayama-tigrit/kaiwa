"""kaiwa.__main__ のテスト

注意: このテストは __main__.py の1行をテストするもので、
実質的には「Pythonの仕様確認」に過ぎない。
カバレッジのために残しているが、テストの価値は低い。
"""

from __future__ import annotations

from unittest import mock


def test_main_module_calls_cli_main():
    """__main__.py が kaiwa.cli.main を呼び出すこと
    
    注意: このテストはカバレッジのためのものであり、テストの価値は低い。
    """
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
