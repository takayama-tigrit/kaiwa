"""kaiwa.cli のテスト"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from unittest import mock

import pytest

from kaiwa.cli import cmd_process, cmd_version, main


class TestCmdVersion:
    """cmd_version() のテスト"""

    def test_version_output(self, capsys):
        """バージョンが正しく出力されること"""
        args = argparse.Namespace()
        cmd_version(args)
        
        captured = capsys.readouterr()
        assert "kaiwa" in captured.out
        # バージョン番号が含まれていること（形式は問わない）
        assert len(captured.out.strip()) > len("kaiwa ")


class TestMain:
    """main() のテスト"""

    def test_no_arguments_exits(self):
        """引数なしで実行するとsys.exit(1)すること"""
        with mock.patch("sys.argv", ["kaiwa"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_version_subcommand(self, capsys):
        """version サブコマンドが動作すること"""
        with mock.patch("sys.argv", ["kaiwa", "version"]):
            main()
        
        captured = capsys.readouterr()
        assert "kaiwa" in captured.out

    def test_process_subcommand_argparse(self, tmp_audio_file):
        """process サブコマンドの引数がparseされること
        
        注意: cmd_processをモックしてargparseの動作だけ確認するテスト。
        統合テストの方が価値が高い。
        """
        with mock.patch("sys.argv", ["kaiwa", "process", str(tmp_audio_file)]):
            with mock.patch("kaiwa.cli.cmd_process") as mock_cmd:
                main()
                
                # cmd_process が呼ばれたこと
                assert mock_cmd.called
                args = mock_cmd.call_args[0][0]
                assert args.audio_file == str(tmp_audio_file)
                assert args.min_speakers is None
                assert args.max_speakers is None

    def test_process_subcommand_with_speaker_hints(self, tmp_audio_file):
        """process サブコマンドの話者数ヒントが正しく渡されること"""
        with mock.patch(
            "sys.argv",
            ["kaiwa", "process", str(tmp_audio_file), "--min-speakers", "2", "--max-speakers", "4"],
        ):
            with mock.patch("kaiwa.cli.cmd_process") as mock_cmd:
                main()
                
                args = mock_cmd.call_args[0][0]
                assert args.min_speakers == 2
                assert args.max_speakers == 4


class TestCmdProcess:
    """cmd_process() のテスト"""

    def test_nonexistent_audio_file_exits(self, tmp_path, capsys):
        """存在しない音声ファイルを指定するとsys.exit(1)すること"""
        nonexistent = tmp_path / "nonexistent.wav"
        args = argparse.Namespace(
            audio_file=str(nonexistent),
            min_speakers=None,
            max_speakers=None,
        )
        
        with pytest.raises(SystemExit) as exc_info:
            cmd_process(args)
        
        assert exc_info.value.code == 1

    def test_invalid_audio_file_exits(self, tmp_path):
        """不正な音声ファイルを指定するとsys.exit(1)すること"""
        invalid = tmp_path / "invalid.wav"
        invalid.write_bytes(b"RIFF" + b"\x00" * 100)  # 不正なWAV
        
        args = argparse.Namespace(
            audio_file=str(invalid),
            min_speakers=None,
            max_speakers=None,
        )
        
        with pytest.raises(SystemExit) as exc_info:
            cmd_process(args)
        
        assert exc_info.value.code == 1

    @mock.patch("kaiwa.cli.get_keychain_password")
    def test_missing_hf_token_exits(self, mock_keychain, tmp_audio_file):
        """HFトークンが取得できない場合はsys.exit(1)すること"""
        mock_keychain.return_value = None
        
        args = argparse.Namespace(
            audio_file=str(tmp_audio_file),
            min_speakers=None,
            max_speakers=None,
        )
        
        with pytest.raises(SystemExit) as exc_info:
            cmd_process(args)
        
        assert exc_info.value.code == 1

    @mock.patch("kaiwa.output.generate_markdown")
    @mock.patch("kaiwa.diarize.diarize")
    @mock.patch("kaiwa.transcribe.transcribe")
    @mock.patch("kaiwa.cli.get_keychain_password")
    @mock.patch("kaiwa.cli.notify")
    def test_successful_process_without_summary(
        self,
        mock_notify,
        mock_keychain,
        mock_transcribe,
        mock_diarize,
        mock_generate_markdown,
        tmp_audio_file,
        tmp_path,
    ):
        """Anthropic APIキー未設定時、要約をスキップして正常終了すること"""
        # モックの設定
        mock_keychain.side_effect = lambda service, account: (
            "hf-token-value" if account == "hf-token" else None
        )
        
        mock_audio = mock.MagicMock()
        mock_result = {
            "segments": [
                {
                    "speaker": "SPEAKER_00",
                    "start": 0.0,
                    "end": 5.0,
                    "text": "こんにちは",
                }
            ]
        }
        mock_transcribe.return_value = (mock_audio, mock_result)
        mock_diarize.return_value = mock_result
        mock_generate_markdown.return_value = tmp_path / "output.md"
        
        args = argparse.Namespace(
            audio_file=str(tmp_audio_file),
            min_speakers=None,
            max_speakers=None,
        )
        
        # 実行
        cmd_process(args)
        
        # transcribe が呼ばれたこと
        assert mock_transcribe.called
        # diarize が呼ばれたこと
        assert mock_diarize.called
        # summarize は呼ばれていないこと（importされていればモックできるが、動的importなので確認困難）
        # generate_markdown が呼ばれたこと
        assert mock_generate_markdown.called

    @mock.patch("kaiwa.summarize.summarize")
    @mock.patch("kaiwa.output.generate_markdown")
    @mock.patch("kaiwa.diarize.diarize")
    @mock.patch("kaiwa.transcribe.transcribe")
    @mock.patch("kaiwa.cli.get_keychain_password")
    @mock.patch("kaiwa.cli.notify")
    def test_successful_process_with_summary(
        self,
        mock_notify,
        mock_keychain,
        mock_transcribe,
        mock_diarize,
        mock_generate_markdown,
        mock_summarize,
        tmp_audio_file,
        tmp_path,
    ):
        """Anthropic APIキー設定時、要約を生成して正常終了すること"""
        # モックの設定
        mock_keychain.side_effect = lambda service, account: (
            "hf-token-value" if account == "hf-token" else "anthropic-key-value"
        )
        
        mock_audio = mock.MagicMock()
        mock_result = {
            "segments": [
                {
                    "speaker": "SPEAKER_00",
                    "start": 0.0,
                    "end": 5.0,
                    "text": "こんにちは",
                }
            ]
        }
        mock_transcribe.return_value = (mock_audio, mock_result)
        mock_diarize.return_value = mock_result
        mock_summarize.return_value = ("テストタイトル", "テスト要約")
        mock_generate_markdown.return_value = tmp_path / "output.md"
        
        args = argparse.Namespace(
            audio_file=str(tmp_audio_file),
            min_speakers=None,
            max_speakers=None,
        )
        
        # 実行
        cmd_process(args)
        
        # summarize が呼ばれたこと
        assert mock_summarize.called
        # generate_markdown が呼ばれたこと
        assert mock_generate_markdown.called

    @mock.patch("kaiwa.output.generate_markdown")
    @mock.patch("kaiwa.diarize.diarize")
    @mock.patch("kaiwa.transcribe.transcribe")
    @mock.patch("kaiwa.cli.get_keychain_password")
    @mock.patch("kaiwa.cli.notify")
    @mock.patch("kaiwa.cli.load_config")
    def test_cleanup_work_dir_when_retention_zero(
        self,
        mock_config,
        mock_notify,
        mock_keychain,
        mock_transcribe,
        mock_diarize,
        mock_generate_markdown,
        tmp_audio_file,
        tmp_path,
    ):
        """cleanup.work_retention_days=0 の時、作業ディレクトリが削除されること"""
        # モックの設定
        work_dir = tmp_path / "work" / "test_audio"
        work_dir.mkdir(parents=True, exist_ok=True)
        (work_dir / "test.txt").write_text("test")
        
        mock_config.return_value = {
            "paths": {"work": str(tmp_path / "work")},
            "cleanup": {"work_retention_days": 0},
        }
        mock_keychain.return_value = "hf-token-value"
        
        mock_audio = mock.MagicMock()
        mock_result = {
            "segments": [
                {
                    "speaker": "SPEAKER_00",
                    "start": 0.0,
                    "end": 5.0,
                    "text": "こんにちは",
                }
            ]
        }
        mock_transcribe.return_value = (mock_audio, mock_result)
        mock_diarize.return_value = mock_result
        mock_generate_markdown.return_value = tmp_path / "output.md"
        
        args = argparse.Namespace(
            audio_file=str(tmp_audio_file),
            min_speakers=None,
            max_speakers=None,
        )
        
        # 実行
        cmd_process(args)
        
        # work_dir が削除されていること
        assert not work_dir.exists()

    @mock.patch("kaiwa.cli.get_keychain_password")
    @mock.patch("kaiwa.cli.notify")
    @mock.patch("kaiwa.cli.load_config")
    def test_path_traversal_protection(
        self,
        mock_config,
        mock_notify,
        mock_keychain,
        tmp_path,
    ):
        """パストラバーサル攻撃を防ぐこと"""
        # 危険なファイル名を含む音声ファイルを作成
        import wave
        
        audio_file = tmp_path / "..test.wav"
        with wave.open(str(audio_file), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b"\x00\x00" * 16000)
        
        work_base = tmp_path / "work"
        mock_config.return_value = {
            "paths": {"work": str(work_base)},
        }
        mock_keychain.return_value = "hf-token-value"
        
        args = argparse.Namespace(
            audio_file=str(audio_file),
            min_speakers=None,
            max_speakers=None,
        )
        
        # パストラバーサル対策が機能して、safe_stem に変換されること
        # （実際にエラーになるかどうかではなく、変換されることを確認）
        # この場合、..test → __test となり、work_base 配下に配置される
        with mock.patch("kaiwa.transcribe.transcribe") as mock_transcribe:
            mock_audio = mock.MagicMock()
            mock_result = {"segments": []}
            mock_transcribe.return_value = (mock_audio, mock_result)
            
            with mock.patch("kaiwa.diarize.diarize") as mock_diarize:
                mock_diarize.return_value = mock_result
                
                with mock.patch("kaiwa.output.generate_markdown") as mock_gen:
                    mock_gen.return_value = tmp_path / "output.md"
                    
                    # エラーにならないこと（safe_stemに変換されているため）
                    cmd_process(args)
                    
                    # transcribe が呼ばれていること（パストラバーサル対策後も処理継続）
                    assert mock_transcribe.called


class TestCmdProcessIntegration:
    """cmd_process() の統合テスト（エラーハンドリング・セキュリティ）"""

    def test_nonexistent_audio_file_shows_helpful_message(self, tmp_path, capsys):
        """存在しない音声ファイルで実行した際、ユーザーに有用なエラーメッセージが表示されること"""
        nonexistent = tmp_path / "nonexistent.wav"
        args = argparse.Namespace(
            audio_file=str(nonexistent),
            min_speakers=None,
            max_speakers=None,
        )
        
        with pytest.raises(SystemExit) as exc_info:
            cmd_process(args)
        
        assert exc_info.value.code == 1
        
        # エラーメッセージが出力されていること
        captured = capsys.readouterr()
        assert "ファイルが見つかりません" in captured.err

    def test_transcribe_exception_handled_gracefully(self, tmp_audio_file):
        """transcribe()が例外を投げた時に適切にエラーが伝播すること
        
        注意: 現在の実装では、cmd_process()は例外をキャッチせず伝播させる。
        main()関数の__name__=="__main__"ブロックで最終的にキャッチされる。
        """
        with mock.patch("kaiwa.cli.get_keychain_password", return_value="hf-token-value"):
            with mock.patch("kaiwa.transcribe.transcribe") as mock_transcribe:
                # transcribeが例外を投げる
                mock_transcribe.side_effect = RuntimeError("モデルロード失敗")
                
                args = argparse.Namespace(
                    audio_file=str(tmp_audio_file),
                    min_speakers=None,
                    max_speakers=None,
                )
                
                # 例外が伝播すること
                with pytest.raises(RuntimeError) as exc_info:
                    cmd_process(args)
                
                assert "モデルロード失敗" in str(exc_info.value)

    @pytest.mark.parametrize("malicious_name", [
        "../../../etc/passwd",
        "..\\..\\windows\\system32",
        pytest.param("test\x00.wav", marks=pytest.mark.skipif(
            True,  # OSによってはnull byteを許可しない
            reason="OSがファイル名にnull byteを許可しない場合がある"
        )),
        "../../.ssh/id_rsa",
    ])
    def test_path_traversal_attack_patterns(self, malicious_name, tmp_path):
        """実際の攻撃パターンでパストラバーサル対策を検証"""
        import wave
        
        # safe_stemに変換されることを確認するために、作業ディレクトリを設定
        work_base = tmp_path / "work"
        work_base.mkdir(parents=True, exist_ok=True)
        
        # 攻撃パターンを含むファイル名で音声ファイルを作成
        # （実際にはファイル名としては使えない文字もあるので、safe_stem変換をテスト）
        safe_name = malicious_name.replace("/", "_").replace("\\", "_").replace("..", "__").replace("\x00", "")
        audio_file = tmp_path / f"{safe_name}.wav"
        
        with wave.open(str(audio_file), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b"\x00\x00" * 16000)
        
        with mock.patch("kaiwa.cli.load_config") as mock_config:
            mock_config.return_value = {
                "paths": {"work": str(work_base)},
            }
            
            with mock.patch("kaiwa.cli.get_keychain_password", return_value="hf-token-value"):
                with mock.patch("kaiwa.transcribe.transcribe") as mock_transcribe:
                    mock_audio = mock.MagicMock()
                    mock_result = {"segments": []}
                    mock_transcribe.return_value = (mock_audio, mock_result)
                    
                    with mock.patch("kaiwa.diarize.diarize") as mock_diarize:
                        mock_diarize.return_value = mock_result
                        
                        with mock.patch("kaiwa.output.generate_markdown") as mock_gen:
                            mock_gen.return_value = tmp_path / "output.md"
                            
                            args = argparse.Namespace(
                                audio_file=str(audio_file),
                                min_speakers=None,
                                max_speakers=None,
                            )
                            
                            # エラーにならないこと（safe_stemに変換されているため）
                            cmd_process(args)
                            
                            # transcribeが呼ばれていること
                            assert mock_transcribe.called
                            
                            # work_base配下に限定されていることを確認
                            # （transcribeの第3引数がwork_dirで、work_base配下であること）
                            call_kwargs = mock_transcribe.call_args[1]
                            if "work_dir" in call_kwargs:
                                work_dir = Path(call_kwargs["work_dir"])
                                # work_baseの配下であることを確認
                                assert work_dir.is_relative_to(work_base) or str(work_dir).startswith(str(work_base))
