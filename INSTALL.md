# Strataをインストールする

Windowsアプリを使う場合は、GitHubの配布インストーラーから導入できます。
ソースのビルドや、システムへのPython・Nodeの追加は不要です。

## ダウンロード先

| 配布版 | 入手先 |
| --- | --- |
| 新しいプレビュー `0.5.5-local.1` | **[Windowsインストーラーをダウンロード](https://github.com/zapabob/Strata/releases/download/v0.5.5-local.1/Strata-0.5.5-local.1-windows-x64-setup.exe)** · [エンジン・手順も入った一括パッケージ](https://github.com/zapabob/Strata/releases/download/v0.5.5-local.1/Strata-0.5.5-local.1-windows-x64.tar.7z) · [チェックサム](https://github.com/zapabob/Strata/releases/download/v0.5.5-local.1/SHA256SUMS.txt) |
| 安定版 `0.5.1` | [Windowsインストーラー](https://github.com/zapabob/Strata/releases/download/v0.5.1/Strata-0.5.1-windows-x64-setup.exe) · [リリースとチェックサム](https://github.com/zapabob/Strata/releases/tag/v0.5.1) |

`0.5.5-local.1` は会話履歴の一括削除とブラウザー操作を含み、ビルドと実installed検証が通過しました。
CUDA資源違反は0件です。全文入力・一般品質・公開検索サイトなどは未認定で、
`releaseQualified=false` を維持します。[確認済みの範囲](docs/HAKUA_RELEASE.md)

## 使い始めるまで

1. リリースのチェックサムとダウンロードファイルを照合します。
   更新する場合はモデルをアンロードし、Strataをトレイからも終了します。
2. `Strata-…-windows-x64-setup.exe` を実行します。
3. アプリの準備画面でPCに合うエンジンとモデルを選び、**読み込み**を押します。
   既存のGGUFは「ローカルGGUFを使用」から選べます。

プレビューの一括パッケージは **7z → tar** の順に展開します。
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

Use the [stable Windows installer](https://github.com/zapabob/Strata/releases/tag/v0.5.1)
or the explicitly labelled [preview](https://github.com/zapabob/Strata/releases/tag/v0.5.5-local.1).
Verify checksums, unload models and quit the tray app before updating. Run the EXE,
then select the engine and model in the app. See the [full installation guide](docs/HAKUA_INSTALL.md).
The055 installer includes the measured bulk-delete/browser-tool changes; broader model/public-search quality remains unqualified.
