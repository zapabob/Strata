# Hakua / Strata

Strataを基盤とするHakuaチャットボット. [zapabob/Strata](https://github.com/zapabob/Strata) · [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## TLDR · 30秒で導入手順

このフォークのWindowsインストーラーを取得して実行し、対応モデルを選んで読み込みます。サイドバーのHakua memoryから記憶チャットを開けます。操作手順は約30秒です。ダウンロード、インストール、モデル読み込みの待ち時間は別にかかります。

[Windows EXE](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/Strata_0.3.3-preview.20261030.1_x64-setup.exe) · [7z](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/Hakua-Strata-0.3.3-preview.20261030.1-windows-x64-sm120.7z) · [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/SHA256SUMS.txt)

7zには同じインストーラーが入っています。展開してからセットアップ用のEXEを実行してください。

## このフォークの独自機能

Hakuaは、そのリクエストで同意した場合だけ記憶を参照し、会話要約を保存します。参照と保存の同意は独立しており、リクエストごとに解除されます。記憶チャットには有効な`hakua_harness`プロファイルと専用キーが必要です。通常チャットのキーとは異なります。[記憶設定ガイド](serve/MEMORY_HARNESS.md)に沿って設定してください。

Hermesの運用ツールは、承認済みSOUL.md / MEMORY.mdの同期、Ebbinghaus記憶、意味グラフ、Obsidian書き出し、sleepによる整理に対応します。これらはチャット画面とは別の機能です。追加のRAG・埋め込み依存は基本インストーラーに含みません。

ローカルのPQ2_0 GGUFは、モデルの詳細設定でllama-serverのバックエンドを`PrismML`にします。通常のGGUFでTurboQuantを使う場合は`TurboQuant`を選び、Kキャッシュを`FP16`、Vを`TURBO2`・`TURBO3`・`TURBO4`のいずれかに設定します。K側のTurboQuantは実モデルで返答の崩れが再現したため、この版では選択できません。変更後はモデルを読み込み直してください。各バックエンドは専用の実行ファイルとライブラリを使用します。PQ2_0とTurboQuantは別々の実行経路です。[設定と制限](docs/LOCAL_LLAMA_BACKENDS.md)を確認してください。

Spin(8)/Triality、Query-v3、Bonsaiの実験機能は、対応する設定を明示的に選んで使用します。全環境での高速化や品質向上は保証していません。

専用Node・Python、固定したHakua-memory 0.3.5、フォークからビルドしたCUDAエンジンを同梱します。モデルの起動時にPython依存のインストールやコンパイルは行いません。

## 対応環境と更新

このWindows配布物はNVIDIA RTX 50シリーズ向けのCUDA sm_120版です。他のGPU、Linux、macOSには個別の対応パッケージが必要です。上流版インストーラーには本フォークの変更は含まれません。モデル重みは別途必要で、数十〜数百GBになる場合があります。対応するモデルが収まる場合、ISTA-DASLab、Unsloth、Gyroの順で選定します。

モデルと個人の記憶はアプリのフォルダー外で保持します。個人の記憶、プロファイルキー、モデル重みは配布物に含めません。更新前にアプリを終了してください。戻す場合はデータのバックアップを保持し、以前のフォーク版をインストールします。

[Models](docs/MODELS.md) · [Install](docs/INSTALL.md) · [Hermes tools](tools/hakua_hermes_memory_stack.py)

## 版番号と検証

| | |
| --- | --- |
| GUI / Product | `0.3.3-preview.20261030.1` |
| Engine | `0.3.3` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Upstream | `46c152a1` · 2026-10-28 |

<!-- App version in this preview tree: `0.3.3-preview.20261030.1` -->

このプレビューは未署名です。導入前にSHA256SUMS.txtと照合してください。[リリース検証記録](docs/HAKUA_RELEASE.md)に実際の試験結果と制約を記載します。ビルド成功だけで推論の正常動作を確認したとはしません。 この未署名プレビューはインストーラーで手動更新してください。署名付き自動更新は未検証です。

## 開発とサポート

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Build](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/zapabob/Strata/issues)

Strataを基盤とするMITライセンスのフォークです。Hakua-memoryとモデル重みには個別のライセンスがあります。原作者と上流への帰属を保持します。
