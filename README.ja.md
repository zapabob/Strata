# Hakua / Strata

<!-- skills-057 -->
## 正式版 0.5.7

`/btw` は実際のサブエージェントへ質問を渡します。専用の親セッションからツールを持たない子を起動し、本題の会話と停止操作を分離します。スキル画面では、完了した作業から再利用できるSKILL.mdを学ぶ機能と、条件が合うスキルを実行ワークフローへ自動適用する機能を個別に有効化できます。手動編集、ワークスペースの範囲、承認設定を尊重します。

[インストーラー](https://github.com/zapabob/Strata/releases/download/v0.5.7/Strata-0.5.7-windows-x64-setup.exe) · [tar.7z一括パッケージ](https://github.com/zapabob/Strata/releases/download/v0.5.7/Strata-0.5.7-windows-x64.tar.7z) · [導入と手順](docs/WORKFLOW_SKILLS.md)

RustXNG 0.31.1 Full / native 0.5.5 / Control 0.5.6. [0.5.7 delivery status](_docs/2026-11-11_stable-057-release_Codex.md). Stable / GitHub Latest: 0.5.7.


## 前のプレビュー 0.5.6-local.1

`/btw 質問` で本題と別の回答を開き、`/deepresearch 調査内容` で検索とページ閲覧を伴う調査を始められます。調査に必要な資料が集まらなかった場合は、その制限を回答に明記します。設定 → ツール → Web検索で **RustXNG Full（キー不要）** を選択できます。

[Windowsインストーラー・127 MB](https://github.com/zapabob/Strata/releases/download/v0.5.6-local.1/Strata-0.5.6-local.1-windows-x64-setup.exe) · [tar.7z一括パッケージ・1.67 GB](https://github.com/zapabob/Strata/releases/download/v0.5.6-local.1/Strata-0.5.6-local.1-windows-x64.tar.7z) · [チェックサム](https://github.com/zapabob/Strata/releases/download/v0.5.6-local.1/SHA256SUMS.txt)

この版はアプリの更新です。署名付きnative 0.5.5とControl 0.5.6は変更していません。上書きインストールと実アプリの画面・実検索を確認しました。画面の生成テストには専用APIを用いており、実モデルの品質やGPU同時処理性能の認定は行っていません。EXEはWindowsコード未署名で、安定版は引き続き0.5.1です。[今回の検証記録](_docs/2026-11-11_btw-deepresearch-rustxng_Codex.md)。

以下の0.5.5・0.5.1の配布物と測定値は、それぞれの旧版の記録として保持しています。

**[Windows版をインストールする](INSTALL.md)** · [Web検索・ブラウザー操作](docs/BROWSER_SEARCH.md)

Windowsプレビューは `0.5.5-local.1`／native `0.5.5`／Control `0.5.6` です。
ソース固定ビルドと実installed検証が通過しました。会話の一括削除、Prismの
エージェント応答、変更していないCUDA資源検査を含みます。

ローカルの言語モデルをWindowsのデスクトップ画面から使うアプリです。
チャット、手元のGGUFの再利用、ワークスペースのファイル編集、同意に基づくHakuaメモリーを利用できます。
[Niko1221/Strata](https://github.com/Niko1221/Strata)を基にした
[zapabobフォーク](https://github.com/zapabob/Strata)で、公式 **0.2.13** と独自機能を統合しています。

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Windowsプレビューをダウンロード

**[0.5.5-local.1 プレリリース](https://github.com/zapabob/Strata/releases/tag/v0.5.5-local.1)** は
Windows x64／CUDA `sm_120` 向けです。RTX 5060 Ti（VRAM 16 GB）・RAM 32 GBで確認しました。
driver621.14で、**変更していないCUDA資源検査が違反0件で通過しました。**
全文入力などの未認定範囲があるため、`releaseQualified=false` は維持します。
旧0.5.4のPrism timeoutは原因未確定の記録として保持します。
[検証範囲と残る制限](docs/HAKUA_RELEASE.md)をご確認ください。

| ダウンロード | 内容 |
| --- | --- |
| [Windowsインストーラー](https://github.com/zapabob/Strata/releases/download/v0.5.5-local.1/Strata-0.5.5-local.1-windows-x64-setup.exe)・112 MB | Tauri NSISアプリ、専用Node・Python、Control。GPUエンジンは別配布です。 |
| [tar.7z一括パッケージ](https://github.com/zapabob/Strata/releases/download/v0.5.5-local.1/Strata-0.5.5-local.1-windows-x64.tar.7z)・1.65 GB | 同じEXE、署名付きエンジン、Control、署名付き配信情報、チェックサム、日英の手順。 |
| [署名付きCUDAエンジン](https://github.com/zapabob/Strata/releases/download/v0.5.5-local.1/strata-engine-0.5.5-windows-x86_64-cuda-cuda13.tar.gz)・1.47 GB | 圧縮したままアプリの準備画面で読み込みます。 |
| [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.5.5-local.1/SHA256SUMS.txt) | 実行・展開前の照合用です。 |

公式と同じWindows配布構成を使ったフォーク版です。コンポーネントはフォークの鍵で署名します。
EXEのWindowsコード署名とTauri更新署名はなく、更新は手動です。
従来の安定版 [0.5.1](https://github.com/zapabob/Strata/releases/tag/v0.5.1) が
GitHub Latestと既定のstable配信に残ります。

### 4ステップで導入

1. 一括パッケージとチェックサムを取得し、**7z、tarの順に展開**します。
   内側の `BUNDLE-SHA256SUMS.txt` も照合します。モデル本体や個人データは含みません。
2. 応答を終了し、モデルをアンロード、アプリデータをバックアップして、トレイも含めStrataを終了します。
   `Strata-0.5.5-local.1-windows-x64-setup.exe` を一度実行します。
3. 準備画面で既存エンジンファイルの選択肢を開き、同じリリースの
   `strata-engine-0.5.5-windows-x86_64-cuda-cuda13.tar.gz` を圧縮したまま選びます。
   署名と全ファイルのハッシュ確認後に有効化します。
4. PCに収まるモデル、または「ローカルGGUFを使用」を選び、**読み込み**を開始します。
   起動時のモデル読み込みは手動です。システムのPython・Node・pip・コンパイラーは不要です。

通常の導入先は `%LOCALAPPDATA%\Programs\Strata` で、以前の場所を引き継ぐ場合があります。
モデル・会話・記憶の保存先は別に保持します。[導入とロールバック](docs/HAKUA_INSTALL.md)

## このフォークの機能

- **手元のモデルを再利用。** 分割GGUFは一つを選ぶと一式を確認します。
  カタログ準備でも一意の有効なローカルファイルを再利用し、複数候補なら選択を求めます。
  モデル、表示名、検証済みexpert packは保持します。
- **ワークスペースファイル。** 必要時だけ開くサイドバーで、登録済みフォルダーの読取・編集・作成・名前変更ができます。
  削除は復元可能なゴミ箱を使い、古い内容からの上書きは拒否します。[操作ガイド](docs/WORKSPACE_FILES.md)
- **会話履歴の一括削除。** 左フォルダーの「…」から対象件数を確認して一度に削除できます。
  アーカイブも対象です。ファイル・他のフォルダー・確認後に作られた会話は保持します。
- **積極的なWeb検索とブラウザー操作。** ローカルエージェントは最新情報や不確かな事実を検索で確認する方針です。
  有効にした隔離ブラウザーでページ情報・座標操作を使い、確認設定を維持します。[検索ガイド](docs/BROWSER_SEARCH.md)
- **会話単位のプライベートキャッシュ。** 対応Qwen3.6では認証された同じ会話だけがprefixを再利用します。
  所有者変更・中断・エラー・待機期限で消去し、共有キャッシュは無効のままです。
- **Hakuaメモリー。** 各発言で読取と保存を別々に許可できます。
  対応モデルの読み込み後に開きます。PrismML／TurboQuantでは認証付きサーバーの再起動を伴う場合があります。
  [メモリーガイド](serve/MEMORY_HARNESS.md)
- **任意のモデル制御。** Spin(8)、Triality、TurboQuantキャッシュ、対応Qwen3.8の拒否方向制御は選択式です。
  小容量のライセンス付き制御ベクトルは既定で無効です。Qwen3.8への実適用は未認定です。

ネイティブモデルは初回のexpert pack変換が必要な場合があります。
対応する変換では進捗表示と既存ファイルの再利用を行います。
エンジンや任意ドラフト層の取得は、GGUF本体の再利用とは別です。

| モデルの種類 | 読み込み方法 |
| --- | --- |
| 対応するQwen / Swiftのネイティブ形式 | Strataエンジン用に準備して読み込みます。 |
| Hikariなど、対応するPQ2_0 GGUF | 「Strataで読み込む」からPrismMLを使用します。ネイティブQ2_0パックへの変換は不要です。 |
| 通常の対応GGUFでTurboQuantキャッシュを使用 | TurboQuantを選び、K=`FP16`、V=`TURBO2` / `TURBO3` / `TURBO4`で再読み込みします。 |

ファイル検査は構造と対応情報の確認です。実際のメモリー確保とモデル対応は、エンジンの起動時にも確認します。
エンジンが失敗・停止した場合は読み込み中の表示を解除します。[追加エンジンの詳細](docs/LOCAL_LLAMA_BACKENDS.md)

## バージョンとソース

| 構成 | バージョン・配布先 |
| --- | --- |
| GUI / Host | `0.5.5-local.1` |
| ネイティブCUDAエンジン | `0.5.5` |
| Control / Terminal | `0.5.6` |
| PrismML / TurboQuant | `0.4.1` / `0.4.0` |
| 専用ランタイム | Node `24.22.2`、CPython `3.12.15` |
| Hakua-memory | `0.3.5` |
| 公式統合元 | `v0.2.13` / `f33c8c30` |
| アプリ・Controlのビルド元 | `35863dea` |
| 別途固定したnativeソース | `b995af13` |

製品・Control・エンジンのバージョンは独立しています。
配布物の `SOURCE.json` に完全なコミットIDと成果物の識別情報を記録します。
[0.2.13統合記録](docs/UPSTREAM_0213.md)にAPI変更と検証をまとめています。

## 検証した範囲

5並列の差分ビルド、CPU・GPU・sanitizer検査、4096容量での短いネイティブ要求
（bounded 7件、legacy 7件、restart 2件）が通過しました。
インストーラーは起動検査13件、成果物29,544ファイルの一致、上書き時のバックアップ済み
ユーザーファイル4,078件の保持を確認しました。実installed WebView2でQwen3.6・Prism・
エージェント応答・再起動・26件の会話一括削除が通過しました。

資源検査と21件の最終数値検証が通過しました。全文生成、一般品質・低精度品質、他GPU・backend、
Qwen3.8への実projectionは未認定です。ブラウザーの入力・送信・座標操作は通過しましたが、
公開検索サイトは未認定です（Bingの結果リンク未確認、DuckDuckGoの認証チャレンジ）。
旧版の全件探索・翻訳・追加メモリーUIの失敗記録も保持します。
[通過・失敗・未実施の詳細](docs/HAKUA_RELEASE.md)

このWindows配布物にネイティブ画像入力と独立したネイティブDeepSeekエンジンは含みません。
mapped expert packは実行ファイルの識別検査を維持し、品質試験で失敗したTurboQuant K設定は無効です。
各モデルはRAM・VRAM・ディスク容量にも制約されます。
[過去の96K〜128K結果](docs/WINDOWS_16GB_CONTEXT.md)は当時の成果物に対するもので、今回の認定ではありません。

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
<a href="https://github.com/themactep"><img src="https://github.com/themactep.png?size=96" width="48" height="48" alt="themactep" title="themactep"></a>
<a href="https://github.com/macintog"><img src="https://github.com/macintog.png?size=96" width="48" height="48" alt="macintog" title="macintog"></a>
<a href="https://github.com/bisonbet"><img src="https://github.com/bisonbet.png?size=96" width="48" height="48" alt="bisonbet" title="bisonbet"></a>
<a href="https://github.com/vizv"><img src="https://github.com/vizv.png?size=96" width="48" height="48" alt="vizv" title="vizv"></a>
<a href="https://github.com/kod88vn"><img src="https://github.com/kod88vn.png?size=96" width="48" height="48" alt="kod88vn" title="kod88vn"></a>
<a href="https://github.com/seoulworker"><img src="https://github.com/seoulworker.png?size=96" width="48" height="48" alt="seoulworker" title="seoulworker"></a>
<a href="https://github.com/jackyini"><img src="https://github.com/jackyini.png?size=96" width="48" height="48" alt="jackyini" title="jackyini"></a>
<a href="https://github.com/router0mail"><img src="https://github.com/router0mail.png?size=96" width="48" height="48" alt="router0mail" title="router0mail"></a>
<!-- supporters:end -->

## 謝辞

[Strata](https://github.com/Niko1221/Strata)の開発者の皆さまへ、ローカル推論と使いやすいデスクトップ体験を丁寧に作り続けてくださっていることに、深く敬意を表します。このフォークは、その充実した実装と積み重ねに支えられています。

[llama.cpp](https://github.com/ggml-org/llama.cpp)と貢献者の皆さまには、C/C++によるモデル推論を多くの開発者や利用者に開いてくださったことへ、心から感謝します。また、[RustXNG](https://github.com/sahenjp/RustXNG)の、ローカルAIから利用できる検索と資料収集の仕組みを高く評価しています。それぞれの技術と、継続的な保守への取り組みに賛辞を送ります。

このフォークの統合・変更は独立して保守しています。上記の謝辞は、各プロジェクトによる推薦や承認を意味しません。
