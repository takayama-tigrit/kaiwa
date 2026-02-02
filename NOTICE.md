# Third-Party Licenses / サードパーティライセンス

kaiwa uses the following open-source libraries. We are grateful to the maintainers and contributors of these projects.

kaiwa は以下のオープンソースライブラリを使用しています。これらのプロジェクトのメンテナーと貢献者に感謝します。

---

## Core Dependencies / コア依存関係

### WhisperX
- **License**: BSD-4-Clause
- **Repository**: https://github.com/m-bain/whisperX
- **Purpose**: High-accuracy speech-to-text transcription with word-level timestamps / 単語レベルのタイムスタンプ付き高精度文字起こし

```
BSD 4-Clause License

Copyright (c) 2022, Max Bain
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. All advertising materials mentioning features or use of this software must
   display the following acknowledgement:
     This product includes software developed by Max Bain.

4. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY COPYRIGHT HOLDER "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
EVENT SHALL COPYRIGHT HOLDER BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

---

### faster-whisper
- **License**: MIT License
- **Repository**: https://github.com/SYSTRAN/faster-whisper
- **Purpose**: CTranslate2-based Whisper inference with word-level timestamps / CTranslate2ベースのWhisper推論（単語レベルタイムスタンプ対応）

```
MIT License

Copyright (c) 2023 SYSTRAN
```

---

### pyannote.audio
- **License**: MIT License
- **Repository**: https://github.com/pyannote/pyannote-audio
- **Purpose**: Speaker diarization (identifying who spoke when) / 話者分離（誰がいつ話したか識別）

```
MIT License

Copyright (c) 2020 CNRS
```

**Note**: Requires acceptance of model licenses on HuggingFace:
- https://huggingface.co/pyannote/speaker-diarization-3.1
- https://huggingface.co/pyannote/segmentation-3.0

---

### Anthropic Python SDK
- **License**: MIT License
- **Repository**: https://github.com/anthropics/anthropic-sdk-python
- **Purpose**: Claude API integration for AI summarization / AI 要約のための Claude API 統合

```
MIT License

Copyright (c) 2024 Anthropic, PBC
```

---

### PyTorch
- **License**: BSD-3-Clause License
- **Repository**: https://github.com/pytorch/pytorch
- **Purpose**: Deep learning framework used by WhisperX and pyannote / WhisperX と pyannote が使用する深層学習フレームワーク

```
BSD 3-Clause License

Copyright (c) 2016- Meta Platforms, Inc. and affiliates.
```

---

### PyYAML
- **License**: MIT License
- **Repository**: https://github.com/yaml/pyyaml
- **Purpose**: YAML configuration file parsing / YAML 設定ファイル解析

```
MIT License

Copyright (c) 2017-2021 Ingy döt Net
Copyright (c) 2006-2016 Kirill Simonov
```

---

## System Tools / システムツール

### sox (Sound eXchange)
- **License**: GPL/LGPL (multiple)
- **Website**: https://sox.sourceforge.net/
- **Purpose**: Audio recording / 音声録音

### fswatch
- **License**: GPL-3.0
- **Repository**: https://github.com/emcrisostomo/fswatch
- **Purpose**: File system monitoring for automatic processing / 自動処理のためのファイルシステム監視

---

## Full License Texts / 完全なライセンステキスト

For the full text of these licenses, see:
- BSD-4-Clause: https://spdx.org/licenses/BSD-4-Clause.html
- MIT: https://opensource.org/licenses/MIT
- BSD-3-Clause: https://opensource.org/licenses/BSD-3-Clause
- GPL-3.0: https://www.gnu.org/licenses/gpl-3.0.html

---

**kaiwa itself is licensed under the MIT License.** See [LICENSE](LICENSE) file for details.

**kaiwa 自体は MIT ライセンスの下で公開されています。** 詳細は [LICENSE](LICENSE) ファイルをご覧ください。
