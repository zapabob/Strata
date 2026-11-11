# Strataをインストールする

正式版 0.5.8 はアプリ・Terminal・Control・ネイティブエンジンのバージョンを揃え、
残っていた拡張テストを修正した Windows 配布版です。`/btw` のサブエージェント、
`/deepresearch`、ワークフローからのスキル学習と自動適用、RustXNG 0.31.1 Full を含みます。
ソースのビルドや、システムへの Python・Node の追加は不要です。

## ダウンロード先

[インストーラー](https://github.com/zapabob/Strata/releases/download/v0.5.8/Strata-0.5.8-windows-x64-setup.exe) ·
[tar.7z 一括パッケージ](https://github.com/zapabob/Strata/releases/download/v0.5.8/Strata-0.5.8-windows-x64.tar.7z) ·
[チェックサム](https://github.com/zapabob/Strata/releases/download/v0.5.8/SHA256SUMS.txt)。
GitHub Latest と latest タグはこの正式版を示します。同梱のエンジンと Control も
新しくビルド・署名・検証した 0.5.8 です。公開・上書き・実モデル検証の範囲は
[今回の配布記録](_docs/2026-11-11_stable-058-context-ci_Codex.md)をご確認ください。
下表の旧版は、当時の配布物と測定結果を保持しています。

| 配布版 | 入手先 |
| --- | --- |
| 前のプレビュー `0.5.5-local.1` | [Windowsインストーラー](https://github.com/zapabob/Strata/releases/download/v0.5.5-local.1/Strata-0.5.5-local.1-windows-x64-setup.exe) · [エンジン・手順も入った一括パッケージ](https://github.com/zapabob/Strata/releases/download/v0.5.5-local.1/Strata-0.5.5-local.1-windows-x64.tar.7z) · [チェックサム](https://github.com/zapabob/Strata/releases/download/v0.5.5-local.1/SHA256SUMS.txt) |
| 以前の安定版 `0.5.1` | [Windowsインストーラー](https://github.com/zapabob/Strata/releases/download/v0.5.1/Strata-0.5.1-windows-x64-setup.exe) · [リリースとチェックサム](https://github.com/zapabob/Strata/releases/tag/v0.5.1) |

`0.5.5-local.1` は会話履歴の一括削除とブラウザー操作を含み、ビルドと実installed検証が通過しました。
CUDA資源違反は0件です。全文入力・一般品質・公開検索サイトなどは未認定で、
`releaseQualified=false` を維持します。[確認済みの範囲](docs/HAKUA_RELEASE.md)

## 使い始めるまで

1. リリースのチェックサムとダウンロードファイルを照合します。
   更新する場合はモデルをアンロードし、Strataをトレイからも終了します。
2. `Strata-…-windows-x64-setup.exe` を実行します。
3. アプリの準備画面でPCに合うエンジンとモデルを選び、**読み込み**を押します。
   既存のGGUFは「ローカルGGUFを使用」から選べます。

一括パッケージは **7z → tar** の順に展開します。
同梱の署名付きエンジン `tar.gz` は展開せず、準備画面の
**既存のファイルを使用する** から読み込みます。
モデル・会話・メモリーの保存先はアプリ本体と別に保持します。

詳しい操作・更新・戻し方は **[Windows導入ガイド](docs/HAKUA_INSTALL.md)** にまとめています。
EXE自体のWindowsコード署名はなく、エンジンのコンポーネント署名とは別です。

## リポジトリ内の案内

| やりたいこと | 開くファイル・場所 |
| --- | --- |
| アプリのインストール | この `INSTALL.md` → [Windows導入ガイド](docs/HAKUA_INSTALL.md) |
| 左フォルダー・会話・ファイルの操作 | [ワークスペース操作](docs/WORKSPACE_FILES.md) |
| ローカルLLMのWeb検索・ブラウザー操作 | [検索とブラウザー操作](docs/BROWSER_SEARCH.md) |
| ソースから開発・ビルド | [開発者向け導入](docs/SOURCE_INSTALL.md) · [配布物のビルド](packaging/README.md) |
| ビルド・検証の作業記録 | `_docs/`。インストール用ファイルではありません。 |

ルートの `START-HERE.bat`、`SETUP.bat`、`setup.sh` はソース導入用です。
アプリ利用者は上のEXEを使ってください。配布EXE・大きなビルド出力・モデルは
ソース管理に混ぜず、GitHub Releasesと既存のローカル成果物保存先に保持します。

## English

Use the [formal 0.5.8 Windows release](https://github.com/zapabob/Strata/releases/tag/v0.5.8).
App, Terminal, Control and the freshly built signed native component are 0.5.8.
Verify checksums, finish requests, unload models and quit the tray app before
running the EXE in the existing installation folder. For tar.7z, extract 7z then
tar; import the compressed engine package in the app. See the
[installation guide](docs/HAKUA_INSTALL.md) for data paths and rollback. Native
model verification covers sixteen short requests at 4096 capacity; full-window
and general quality remain unqualified. The installer has no Windows
Authenticode signature; component/feed signatures are independent.
