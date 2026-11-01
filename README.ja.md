# Hakua / Strata

Strataを基盤とするHakuaチャットボット。 [zapabob/Strata](https://github.com/zapabob/Strata) · [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## TLDR · 30秒で導入手順

このフォークのWindowsインストーラーを取得して実行します。初回起動時にアプリが案内する対応エンジンをインストールし、モデルを選んで読み込みます。サイドバーのHakua memoryから記憶チャットを開けます。操作手順は約30秒です。アプリ・エンジン・モデルのダウンロード、インストール、読み込みの待ち時間は別にかかります。

Windowsプレビュー0.4.0です。確認した試験と対応範囲は[リリース検証記録](docs/HAKUA_RELEASE.md)をご覧ください。

[Windows EXE](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Strata_0.4.0-preview.20261101.1_x64-setup.exe) · [7z](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Hakua-Strata-0.4.0-preview.20261101.1-windows-x64-sm120.7z) · [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/SHA256SUMS.txt)

7zには同じインストーラーが入っています。展開してからセットアップ用のEXEを実行してください。

## このフォークの独自機能

Hakuaは、そのリクエストで同意した場合だけ記憶を参照し、会話要約を保存します。参照と保存の同意は独立しており、リクエストごとに解除されます。対応するネイティブモデルを読み込むと、アプリがローカルの記憶プロファイルを自動で作成します。Hakua memoryを開き、ダイアログの専用キーをコピーし、記憶ページで記憶のチェック欄を選択してから、About → Settingsに貼り付けてください。ソース版の設定を含む詳しい手順は[記憶ガイド](serve/MEMORY_HARNESS.md)にあります。

PrismML/PQ2_0とTurboQuantでも、モデルを読み込み、サイドバーのHakua memoryから記憶チャットを開けます。追加経路のダイアログは本人用のローカルキーを自動で使い、参照・保存は毎回別々のチェック欄で選びます。最初に開く際は、処理中のリクエストを終えてください。アプリが管理するサーバーを認証付き・共有キャッシュ無効の設定で起動し直します。ネイティブと追加経路は同じローカル記憶を使います。起動時にはGUI・Host・デスクトップ本体の版を照合し、混在や読み込み失敗時は復旧手順を表示します。

Hermesの運用ツールは、承認済みSOUL.md / MEMORY.mdの同期、Ebbinghaus記憶、意味グラフ、Obsidian書き出し、sleepによる整理に対応します。これらはチャット画面とは別の機能です。追加のRAG・埋め込み依存は基本インストーラーに含みません。

ローカルのPQ2_0 GGUFは、モデルの詳細設定でllama-serverのバックエンドを`PrismML`にします。通常のGGUFでTurboQuantを使う場合は`TurboQuant`を選び、Kキャッシュを`FP16`、Vを`TURBO2`・`TURBO3`・`TURBO4`のいずれかに設定します。K側のTurboQuantは実モデルで返答の崩れが再現したため、この版では選択できません。変更後はモデルを読み込み直してください。各バックエンドは専用の実行ファイルとライブラリを使用します。PQ2_0とTurboQuantは別々の実行経路です。[設定と制限](docs/LOCAL_LLAMA_BACKENDS.md)を確認してください。

Spin(8)/Triality、Query-v3、Bonsaiの実験機能は、対応する設定を明示的に選んで使用します。全環境での高速化や品質向上は保証していません。

公式アプリと同じ構成で、インストーラーには専用Node・Pythonと固定したHakua-memory 0.3.5を同梱します。GPUエンジンは別配布です。初回にインストールを選ぶと署名付きHakuaエンジンコンポーネントを取得でき、取得済みファイルからの導入にも対応します。このコンポーネントにネイティブCUDA・PrismML・TurboQuantの各実行環境が入ります。モデル重みはさらに別途取得します。公開アプリの実行にシステム側のNode・Python、pip、コンパイラーは不要です。

## 対応環境と更新

このWindows配布物はNVIDIA RTX 50シリーズ向けのCUDA sm_120版です。他のGPU、Linux、macOSには個別の対応パッケージが必要です。上流版インストーラーには本フォークの変更は含まれません。モデル重みは別途必要で、数十〜数百GBになる場合があります。対応するモデルが収まる場合、ISTA-DASLab、Unsloth、Gyroの順で選定します。

別配布のネイティブエンジンはテキストチャット用です。このプレビューには、ネイティブの画像入力機能とDeepSeek専用のネイティブエンジンは含まれません。

モデルと個人の記憶はアプリのフォルダー外で保持します。個人の記憶、プロファイルキー、モデル重みは配布物に含めません。更新前にアプリを終了してください。戻す場合はデータのバックアップを保持し、以前のフォーク版をインストールします。

トレイ収納が有効な場合、×は画面を隠します。更新前はトレイのStrataアイコンを右クリックし、Strata を終了を選んで完全に終了してください。

[Models](docs/MODELS.md) · [Install](docs/HAKUA_INSTALL.md) · [Hermes tools](tools/hakua_hermes_memory_stack.py)

## 版番号と検証

| | |
| --- | --- |
| GUI / Product | `0.4.0-preview.20261101.1` |
| Engine | `0.4.0` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Upstream | `c62d5e3a` · 0.2.9 |

<!-- App version in this preview tree: `0.4.0-preview.20261101.1` -->

WindowsインストーラーにはWindowsのコード署名がありません。導入前にSHA256SUMS.txtと照合してください。別配布のエンジンコンポーネントと更新フィードには署名があり、アプリが検証します。アプリ本体はインストーラーで手動更新します。アプリ本体の署名付き自動更新は未検証です。実モデルでの記憶試験を含む結果と制約は、[リリース検証記録](docs/HAKUA_RELEASE.md)に記載します。

## 開発とサポート

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Build](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/zapabob/Strata/issues)

Strataを基盤とするMITライセンスのフォークです。Hakua-memoryとモデル重みには個別のライセンスがあります。原作者と上流への帰属を保持します。

上流の約480KBの制御ベクトルは既定でOFFです。[Qwen Community License 1.0](data/experimental-speed-projection/LICENSE)の原文を同梱しています。推論用モデル本体は別途取得します。
