# Hakua / Strata

ローカルの言語モデルをWindowsのデスクトップ画面から使うアプリです。
チャット、モデルの準備と読み込み、ツール、任意のHakuaメモリーを利用できます。
[Niko1221/Strata](https://github.com/Niko1221/Strata)を基にした
[zapabobフォーク](https://github.com/zapabob/Strata)です。

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Windowsプレビューの導入

製品バージョンは **0.4.1-beta.1** です。配布物はsetup EXEとチェックサムです。
Windowsコード署名のない、手動更新用のプレビュー版です。

1. [Windowsインストーラー](https://github.com/zapabob/Strata/releases/download/v0.4.1-beta.1/Strata_0.4.1-beta.1_x64-setup.exe)を取得し、
   [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.1-beta.1/SHA256SUMS.txt)と照合します。
2. 導入済みの場合はトレイも含めてStrataを終了してから実行します。
   モデルと個人データはアプリのインストール先とは別の場所に保存してください。
3. このベータのリリースページから`strata-engine-0.4.1-windows-x86_64-cuda-cuda13.tar.gz`を取得し、準備画面で読み込みます。latest配信先は以前のエンジンを維持しています。専用Node・Pythonを同梱しているため、別途の導入やpip、コンパイラーは不要です。
4. PCに収まるモデルを選びます。手元のGGUFは「ローカルGGUFを使用」から選択できます。

詳しい手順は[導入ガイド](docs/HAKUA_INSTALL.md)、検証条件は[リリース記録](docs/HAKUA_RELEASE.md)、
配布物は[リリースページ](https://github.com/zapabob/Strata/releases/tag/v0.4.1-beta.1)をご覧ください。
このフォーク専用のインストーラーとコンポーネント配信先を使用します。

バージョンは[SemVer 2.0.0](https://semver.org/)に従い、アプリが`0.4.1-beta.1`、ネイティブエンジン／Controlが`0.4.1`です。変更のないPrismML／TurboQuantは`0.4.0`のままです。通常のアプリ導入先はCドライブの`%LOCALAPPDATA%\Programs\Strata`で、モデルの保存先とは別です。既存環境では以前の導入先を引き継ぐ場合があります。

## すでにあるモデルを使う

分割GGUFは、そのうち1ファイルを選択すると一式を確認します。モデルの重みファイルは元の場所に置いたまま使います。
GGUF内の名前が`Hf`などの一般的な値なら、識別できるようファイル名を表示します。
自分で付けた表示名は、再確認やアプリの再起動後も保持します。

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
| GUI / Host | `0.4.1-beta.1` |
| ネイティブエンジン / Control | `0.4.0` |
| 専用ランタイム | Node `24.22.2`、CPython `3.12.15` |
| Hakua-memory | `0.3.5` |
| 署名付きCUDA / PrismML / TurboQuant | [v0.4.0-preview.20261101.1](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261101.1) |
| 参照した上流ソース | `ffa80d73`、上流`0.2.10` |

今回のアプリ更新では、署名付きエンジンの実行ファイルを置き換えません。
別途の実験用Qwen3.6コンポーネントは未署名です。正確な識別情報は[リリース記録](docs/HAKUA_RELEASE.md)に掲載しています。

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
会話の識別子がない要求では再利用しません。対応する検証済み実行ファイルと、起動時の機能確認が必要です。
古いエンジンは引き続き拒否します。初期対応は一度に1件の要求で、共有のプロンプト・会話キャッシュは無効のままです。
mapped expert packや実験用カーネルは任意設定とし、実行ファイルのハッシュ検査も維持しています。
従来のホストメモリー確保方式は約18.7 GiBと予備領域を必要とする場合があり、総RAMが32 GBでも起動できるとは限りません。
実測値と未完了の確認項目はリリース記録を参照してください。
実モデルの品質検査に失敗したTurboQuantのKモードは利用できません。

コンテキスト設定131,072で短い応答が成功しても、全長の入力・生成・品質を検証したことにはなりません。
実測条件、失敗、未実施の項目は[HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md)で区別しています。
Spin(8)、Triality、Query-v3、Bonsaiは任意の実験機能です。

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
