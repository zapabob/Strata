# Hakua / Strata

このソースツリーでは0.5.1（`Strata-0.5.1-windows-x64-setup.exe`）を準備しています。起動時のモデル自動読み込みを停止し、Qwen3.6の起動処理を修正します。この候補版は未公開で、実モデルの起動確認も未完了です。以下の公開済みダウンロードは0.5.0です。

ローカルの言語モデルをWindowsのデスクトップ画面から使うアプリです。
チャット、モデルの準備と読み込み、ツール、任意のHakuaメモリーを利用できます。
[Niko1221/Strata](https://github.com/Niko1221/Strata)を基にした
[zapabobフォーク](https://github.com/zapabob/Strata)です。

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Windows版の導入

0.5.0にはネイティブQwen3.6の起動に既知の制限があります。4K設定の試験は6分以内に起動完了せず、会話キャッシュ分離の実機要求は未実施です。導入前に[検証結果と制限](docs/HAKUA_RELEASE.md)をご確認ください。

Windows x64 CUDA sm_120向けのリリースです。RTX 5060 Ti（VRAM 16GB）・RAM 32GBの実機で確認しました。導入前に[検証結果と残っている制限](docs/HAKUA_RELEASE.md)をご覧ください。

製品バージョンは **0.5.0** です。配布物はsetup EXEとチェックサムです。
Windowsコード署名のない、手動更新用のリリースです。

1. [Windowsインストーラー](https://github.com/zapabob/Strata/releases/download/v0.5.0/Strata-0.5.0-windows-x64-setup.exe)を取得し、
   [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.5.0/SHA256SUMS.txt)と照合します。
2. 導入済みの場合はトレイも含めてStrataを終了してから実行します。
   モデルと個人データはアプリのインストール先とは別の場所に保存してください。
3. 準備画面から署名済みCUDAコンポーネントを導入します。latest配信先、または同梱の`strata-engine-0.5.0-windows-x86_64-cuda-cuda13.tar.gz`を使用できます。専用Node・Pythonを同梱しているため、別途の導入やpip、コンパイラーは不要です。
4. PCに収まるモデルを選びます。手元のGGUFは「ローカルGGUFを使用」から選択できます。

詳しい手順は[導入ガイド](docs/HAKUA_INSTALL.md)、検証条件は[リリース記録](docs/HAKUA_RELEASE.md)、
配布物は[リリースページ](https://github.com/zapabob/Strata/releases/tag/v0.5.0)をご覧ください。
このフォーク専用のインストーラーとコンポーネント配信先を使用します。

バージョンは[SemVer 2.0.0](https://semver.org/)に従い、アプリが`0.5.0`、ネイティブエンジンが`0.5.0`、Controlが`0.5.0`です。変更のないPrismML／TurboQuantは`0.4.0`のままです。通常のアプリ導入先はCドライブの`%LOCALAPPDATA%\Programs\Strata`で、モデルの保存先とは別です。既存環境では以前の導入先を引き継ぐ場合があります。

NSISインストーラーは、署名済みCUDAコンポーネント、Control、チェックサム、導入手順と一緒に[tar.7z一括パッケージ](https://github.com/zapabob/Strata/releases/download/v0.5.0/Strata-0.5.0-windows-x64.tar.7z)にも収録します。モデルの重みや個人データは含みません。公開には`v0.5.0`、同じコミットを指す`latest`タグ、GitHubのLatest指定を使用します。

## すでにあるモデルを使う

分割GGUFは、そのうち1ファイルを選択すると一式を確認します。モデルの重みファイルは元の場所に置いたまま使います。
GGUF内の名前が`Hf`などの一般的な値なら、識別できるようファイル名を表示します。
自分で付けた表示名は、再確認やアプリの再起動後も保持します。

登録済みのローカルモデルの設定画面は、別のモデル一覧を取得している間も開けます。

カタログからモデルを準備するときも、選択したモデルフォルダー内のサブフォルダーまで既存GGUFを確認します。
選択したモデルと一致する有効な一式が1つあれば再利用します。複数ある場合はファイルの選択を求め、
異なる追加学習モデルを自動で選ぶことはありません。標準のダウンロード先では従来の整合性検査と途中再開を行います。

ネイティブモデルには、GGUFを取得した後に初回のパック変換が必要な場合があります。
パック作成処理が進捗を報告する場合は、完了した層数を表示します。
省メモリーパックの変換を再開するときは、一時ファイルがすでに使用しているディスク容量を考慮します。
エンジンや任意のドラフト層の取得は、モデル本体のGGUF再利用とは別に扱います。

| モデルの種類 | 読み込み方法 |
| --- | --- |
| 対応するQwen / Swiftのネイティブ形式 | Strataエンジン用に準備して読み込みます。 |
| Hikariなど、対応するPQ2_0 GGUF | 「Strataで読み込む」からPrismMLを使用します。ネイティブQ2_0パックへの変換は不要です。 |
| 通常の対応GGUFでTurboQuantキャッシュを使用 | TurboQuantを選び、K=`FP16`、V=`TURBO2` / `TURBO3` / `TURBO4`で再読み込みします。 |

ファイル検査は構造と対応情報の確認です。実際のメモリー確保とモデル対応は、エンジンの起動時にも確認します。
エンジンが失敗・停止した場合は読み込み中の表示を解除します。[追加エンジンの詳細](docs/LOCAL_LLAMA_BACKENDS.md)

## 構成とHakuaメモリー

| 構成 | バージョン・配布先 |
| --- | --- |
| GUI / Host | `0.5.0` |
| ネイティブエンジン | `0.5.0` |
| Control | `0.5.0` |
| 専用ランタイム | Node `24.22.2`、CPython `3.12.15` |
| Hakua-memory | `0.3.5` |
| CUDA / PrismML / TurboQuantの配布候補 | [リリース状況](docs/HAKUA_RELEASE.md) |
| 参照した上流ソース | `5d37280d`、上流`0.2.11` |

0.5.0は公式0.2.11と`5d37280d`までの修正を取り込みます。チャットごとのファイル保存、生成中の再接続、IME入力と画面復旧、モデル一覧、ストリーム分離、Pillow 13の更新を含みます。Hakuaメモリ、既存GGUFの再利用、Qwen3.6のプライベートキャッシュは維持します。新しいCUDAビルドは個別に検証し、過去の0.4.1の測定値を新しい既定値の実績として扱いません。ネイティブでの全文入力は未検証です。[検証・公開状況](docs/HAKUA_RELEASE.md)をご覧ください。

対応モデルを読み込んだ後、サイドバーのHakuaメモリーを開きます。
記憶の読み取りと保存は、それぞれの発言で個別に選択します。
PrismML / TurboQuantでメモリーを開くと、認証とプライベートキャッシュ設定を適用して所有サーバーを再起動します。
実行中の応答を終えてから開いてください。[メモリーガイド](serve/MEMORY_HARNESS.md)

## 対応範囲と制限

Windows x64、RTX 5060 Ti、CUDA sm_120、システムRAM 32 GBで確認しているプレビューです。
他のGPU・OS、ネイティブ画像入力、独立したネイティブDeepSeekエンジンの動作保証は含みません。
使用できるモデルや準備時間は、RAM、VRAM、ディスクの速度と空き容量によって変わります。

新しいQwen3.6のプライベートキャッシュ経路では、同じ認証済み会話の中で状態を保持し、続きの要求で再利用します。
別の会話や別ユーザーには引き継ぎません。会話の切り替え、中断、エラー、5分間の無操作で消去します。
会話の識別子がない要求では再利用しません。Hostにあった起動前の拒否分岐2か所を削除しました。
サーバーは起動したエンジンのINFO応答で機能を確認し、互換性のあるローカルビルドも扱います。初期対応は一度に1件の要求で、共有のプロンプト・会話キャッシュは無効のままです。
mapped expert packや実験用カーネルは任意設定とし、実行ファイルのハッシュ検査も維持しています。
従来のホストメモリー確保方式は約18.7 GiBと予備領域を必要とする場合があり、総RAMが32 GBでも起動できるとは限りません。
実測値と未完了の確認項目はリリース記録を参照してください。
実モデルの品質検査に失敗したTurboQuantのKモードは利用できません。

コンテキスト設定131,072で短い応答が成功しても、全長の入力・生成・品質を検証したことにはなりません。
実測条件、失敗、未実施の項目は[HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md)で区別しています。
Spin(8)、Triality、Query-v3、Bonsaiは任意の実験機能です。

## 16GB GPUで96K〜128Kを使う

画面から96K（98,304）と128K（131,072）を選べます。RTX 5060 Ti 16GB・RAM 32GBの実機では、Qwen3.6 UD-Q4_K_XLをPrismML、Q8 K/V、CPU側のMoE 28層で動かし、130,792トークンを省略せず処理して、離れた3か所のコードをすべて取得できました。この1回の要求は約29分かかりました。他のモデルの品質や速度を保証する結果ではありません。[設定と全長入力の検証結果](docs/WINDOWS_16GB_CONTEXT.md)をご覧ください。

## 開発

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[モデル参照](docs/AI_REFERENCE.md) · [ビルド](packaging/README.md) ·
[貢献手順](CONTRIBUTING.md) · [セキュリティー](SECURITY.md)

StrataはMITライセンスです。モデル、Hakua-memory、同梱依存物にはそれぞれのライセンスと表記が適用されます。
小容量の任意制御ベクトルは既定で無効であり、[Qwen Community License 1.0](data/experimental-speed-projection/LICENSE)に従います。

## 公式 Strata を支えてくださる方々

Strata を支えてくださるすべての方に感謝します。

<!-- supporters:start (one line per public supporter, newest last; copy a line and change the GitHub name in all four places) -->
<a href="https://github.com/ryan4yin"><img src="https://github.com/ryan4yin.png?size=96" width="48" height="48" alt="ryan4yin" title="ryan4yin"></a>
<!-- supporters:end -->
