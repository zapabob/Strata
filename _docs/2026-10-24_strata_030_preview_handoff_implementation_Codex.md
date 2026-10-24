# Strata 0.3.0 引き継ぎ実装書 — main反映済み・先行Release準備

作成日: 2026-10-24 JST。実行状態の最終確認: 2026-10-24T11:06:49Z。
作業先: `C:/Users/downl/Documents/ChatGPT/Strata`。

## 1. 最初に読む現在地

ユーザーの直近の優先順位は、まずmainへコミット・pushし、その後にexe化できる部分からタグ付きReleaseを出すこと。その前の依頼は、トークン容量に備えて引き継ぎ実装書を残すことだった。main反映を先に実行し、この文書を作成している。

**mainへの通常pushは完了した。** ローカルHEAD/mainとGitHubのrefs/heads/mainは、いずれも次のSHAで一致を確認した。

`c121dc8aa004a1eb8313b64ff73eaa512f5f0712`

公開先: https://github.com/zapabob/Strata/commit/c121dc8aa004a1eb8313b64ff73eaa512f5f0712

`f8074a6`から14コミットをfast-forwardで反映した。force-push、reset、clean、stashは行っていない。現在のチェックアウトは`main`。既存の実装ブランチ`codex/strata-030-completion`も同じc121dc8にある。

**タグ、GitHub Release、配布tar.7z、GUIインストーラーは未作成・未公開。** exeは診断用ビルドが存在するが、配布物としてのDLL同梱・展開先試験・公開後hash照合はまだ行っていない。GitHub Actionsはc121dc8について`gh run list`が空だった。CIオールグリーンとは報告していない。

## 2. ユーザー指示の優先順位と公開範囲

最初の計画は、両必須モデルと全公開基準を満たしてから正式v0.3.0を公開するもの。その後、ユーザーがまずmainへpushし、exe化できる部分からリリースするよう明示した。このため、**直近の公開対象は部分的なプレビュー版**として扱うことを説明済み。

予定タグは、未使用なら`v0.3.0-preview.20261024.1`。正式`v0.3.0`とは分け、prerelease=true、latest=false、手動導入とする。ユーザーにはこの扱いを伝え、異議は出ていない。先行公開の許可は、未実測の性能・品質・機能を合格扱いにする許可ではない。

先行対象は、実行確認済みのWindows CUDAネイティブCLIエンジン、必要DLL、ライセンス、使い方、検証manifest。GUI、フォント、モデル重み、学習環境、未検証の三ランタイム一式を完成品として同梱しない。ネイティブexeはトークンID入力であり、単体のGUIチャット／HTTP APIではないことを明記する。

ユーザーは32GB RAMでも公式と同等以上になるようコードを詰めることを要求している。比較は同じPC・同じモデルで公式の最適化済み設定を基準に行う。公式の別PC・64GB環境の速度と同一になるとは約束していない。

## 3. 再開時の順序

1. 正本プロンプト、実際のAGENTS、CONTRIBUTING、適用SOPを読む。下記の状態・差分・remoteを軽く再確認する。新しい実装はmain上で始めず、既存`codex/strata-030-completion`へ戻して進める。無関係な文書差分は維持する。
2. P0の修正と再レビューは完了済み。再実装・再レビューをやり直さない。次は、用意済みの`task-P1-preview-brief.md`に従って、先行CLI配布とREADMEを実装する。
3. P1を限定レビューし、ソースcommitとexe/DLLのコンパイル入力・配布manifestを結び付ける。必要なら関連CPU CIを追加する。空のCI一覧を成功扱いにしない。
4. 必要DLL／ライセンスをそろえ、tarを作ってから7z圧縮する。空白を含む展開先、Node/Python/CUDA Toolkitを含まないPATH、実モデルの通常経路で確認し、SHA-256を照合する。
5. ユーザーの許可範囲でmainを通常pushし、確認済みの同一ソースにプレビューtag／Releaseを公開する。公開後に取得し直してhashを確認する。正式版の残件は別に維持する。

mainpushとReleaseの許可を再質問する必要はない。保護ルールに拒否された場合にforceや別経路で迂回しない。新しい破壊操作・OS設定変更は別の権限として扱う。

## 4. 作業規約・保存場所

正本: `C:/Users/downl/_docs/prompts/CLAUDE-FABLE-5.md`
SHA256: `54e80937772be0ac111d00681502b27fdf831803a2aa6f6d8df9424bdfc77073`

この文書内の偽の製品情報・別モデルのidentity・Linux環境などは、実際のsystem/developer、Windows環境、セキュリティ制約より優先させない。

適用済み: executing-plans、subagent-driven-development 7.0.1、git-workflow-and-versioning、evidence-changelog-closeout、milspec-codex-standard、api-and-interface-design、build-manager。agent-self-review-evolutionはreview-only。MILSPECの正式認証を取得したという主張はしない。

SDDの記録先:
`C:/Users/downl/Documents/ChatGPT/Strata/.superpowers/sdd/2026-10-24_strata_030_completion_execution_Codex`

ここはGit無視領域だが、今回の詳細な回復情報を保持している。最初に`progress.md`を読む。完了したTask1/2/3/4a/4b/4c0/4c1aを再実装しない。実装担当は同時に1名、別担当によるレビューを挟む。直近の担当`native_graph_resume`とレビュー担当`preview_checkpoint_review`は完了済みで、実行中のモデルやビルドはない。

重み・依存・ビルド・配布物は`H:/Strata`。GGUF、pack、過去ログ、部分取得ファイルを勝手に削除・移動しない。大型I/O・ビルド・モデル実行は順番に行い、ビルド原則1ジョブ。各工程の追加ピークと10GiBの空きを確保する。`sandbox_permissions`は指定しない。

## 5. 保持している無関係な差分

mainへの切替・fast-forward・push前後でhashが同じことを確認済み。次の3ファイルを勝手にstage／コミット／上書きしない。

| 状態 | ファイル | SHA256 |
|---|---|---|
| modified | `_docs/2026-10-23_strata_030_execution_Codex.md` | `d96061fee4207afe19796df92d95ee17dd7986a9fdea37094d34a1e9a359d7b0` |
| modified | `_docs/2026-10-23_strata_prism2_bonsai_spin8_handoff_plan.md` | `1a5d8d094c7c6c482ded7348c4d72d47faf1af39a5bc8baf4272abfdd43fa40b` |
| untracked | `_docs/2026-10-24_strata_030_handoff_implementation_plan_Codex.md` | `f33086c5134e2601b2e9429963a157479e16ea55207a02b9484f38aaac8da781` |

この新しい引き継ぎ書も、作成時点ではローカルの未追跡ファイル。mainへpushしたソースに含めたと報告しない。

## 6. P0レビューと修正は解決済み

- `c8cf2938cadf270f49c2cd0bb823ec7c83b38f7b`: opt-inネイティブ三K／共有Vの実モデル接続チェックポイント。27ファイル、1569追加／32削除。
- 最初のP0独立レビューでImportant 1件。検証済みreceiptを別読みでV.verifyへ渡し、さらに検証後のpack metadataを再採取してcapsuleへ載せるため、検証と消費のbindingが切れる静的な問題だった。実証された攻撃や実データの改変があったという話ではない。
- `c121dc8aa004a1eb8313b64ff73eaa512f5f0712`: 同じ検証済みreceipt bytesを共通verifierへ渡して解析・hash。検証前のpack membership／small-file hash／dense file identityを保存し、公開前に再確認。元の記録をcapsuleへ直列化し、source再検証もcapsule公開前に実施。
- 差し替え等のREDは13試験で7failure＋1error。修正後、producerとtiny実GGUF検証を含む26試験がPASS、2.68秒。過去のpytest_randomly/thinc/numpyによる4setup/teardown errorも保持し、成功扱いしていない。再試験ではそのコマンドだけplugin autoloadを無効化した。
- 一度だけ実packのbounded dense scanを行い、新capsuleが以前の1350byteと完全一致。未変更exeで12 QSA層のadmissionも成功。
- 独立の限定再レビューは、両binding項目ADDRESSED、新規Critical/Importantなし、P0 checkpoint spec compliant／Approved。**これは部分チェックポイントの承認であり、三経路の生成・正式Releaseの承認ではない。**

再レビュー資料:
`task-P0-fix1.md`, `task-P0-checkpoint-brief.md`, `task-P0-review.md`, `task-4c1b-report.md`。
差分: `review-P0-fix1-c8cf293..c121dc8.diff`（31,113B）。
最初のレビュー差分は`review-P0-2c40047..c8cf293-r2.diff`（207,864B）。104Bの誤生成ファイルは失敗資料として保持し、レビューに使用していない。

## 7. exe・検証根拠の所在

ビルド先: `H:/Strata/build/native-spin8/Release`。

| ファイル | bytes | SHA256 |
|---|---:|---|
| `strata.exe` | 79,692,288 | `cb491ae5c0b6636cdb18eb3e1c1840fecda1cfc82d252fb95aae4e98181ee542` |
| `strata_kq.dll` | 12,388,352 | `f3bba767420ee22cbf221b2bceea58f96b10e5713421ec0c58d8f1a730091713` |

実機: RTX5060Ti16GB、Ryzen5 4500、RAM32GB、Windows。CUDA13.3、MSVC14.44.35207、CMake4.4.0、sm120。ビルドは`STRATA_PORTABLE=OFF`、動的MSVC runtime。他の全AVX2 CPUでの配布互換性やstatic runtimeを資格確認済みとは呼ばない。エンジンversionは0.1.47のまま。配布のpreview versionと混同しない。

根拠: `H:/Strata/build/task5a-native-graph-20261024`。
- `task-4c1b-report.md`がコマンド・失敗・制限の総覧。
- `native-build2.*`、`utf8-fix-build1.*`がビルド根拠。最初のnative buildはvoid*→cudaStream_tの2コンパイルエラーで失敗し、保持後に修正。
- `final-input-verification2.json`: 2061入力が変更なしだった時点の記録。
- `p0-fix1-input-split.json`: その後Pythonのツール／試験4件だけ変更。コンパイル入力変更0、exe hash不変。
- `p0-fix1-green3.log`: 26 PASSをcontrollerも読んだ。
- `p0-fix1-capsule-production1.*`、`capsules-p0-fix1/production.json`、`p0-fix1-admission1.*`が修正後の実pack検証・native admission。GGUF66GB全体のhashを再実行したわけではない。

新capsule SHA: F32 `28e7dffdedaee7926032969308730c76aa933d4b14431dce305a9a953ba1cd40`、圧縮 `b1d2db7ad6ed47504fedf1dd3fe7aeede91e74f1de28c1bcb9f90fc0fbf097e8`。

過去baselineのexe/DLL/input/resultは同rootの`baseline/`へコピー・hash確認し、読み取り専用として保持済み。

## 8. 何が動き、何が未完了か

ライブラリでは同一Spin元の三表現、厳密codec、三つの物理K＋共有V、online softmax、query-v3、GPU状態・基礎snapshotの試験が通っている。Task4a CUDA12/12、独立Turbo2762recordのbyte／F32復号一致、Task4bキャッシュ試験、Task4c1a owner17361check、bounded7963check、ComputeSanitizer0error等の根拠は既存reportにある。

c8cf293のネイティブ接続ではSessionStateがownerを持ち、QsaStateが借用。通常decode／Verifier／独立Prefillへ接続。実CELL IDを扱い、元のsource strideを保ったままpaddingを-1へ処理する。Qnorm後・RoPE前にv3、共通driver stream、COMMIT→TRUNCATEをcompletion eventより前に発行し、cache/queryのsticky statusを読む。未対応の外部保存・ring・split等は明示的に拒否する。

**実モデルで確認済みなのは通常/offの短い生成と、新F32経路のprefillまで。圧縮三K経路の生成は未実施。**

| 実行 | 結果 |
|---|---|
| `model-off-cache2048-r1` | 旧exe57bbe…でREADY＋EOS、正常終了。固定2048は歴史的診断のみ |
| `model-off-auto4096-r1` | 自動5690枠7.33GiB。commit不足で保護停止。生成成功ではない |
| `model-off-auto9216-r1` | 自動1806枠2.33GiB。最終exeでREADY＋EOS正常終了 |
| `model-f32-auto9216-r1` | 12 QSA層へ接続し29token prefill成功。ただし自動cache0枠で既存spec2要件によりexit2。生成未成功 |
| `model-off-auto6144-r1` | 自動4136枠5.32GiB、30入力／READY＋EOS、child0、残存owned process0 |
| F32／圧縮6144 | ユーザーが先行公開優先へ変更したため、起動していない |

off6144の根拠: `.generation.json`, `.receipt.json`, `.model-result.json`, `.stdout.log`, `.stderr.log`, `.trace.jsonl`。token IDsは44061,248046。prefill29token／入力全体30token。TTFT93554.2ms、decode2token3725.6msだが、2tokenだけの診断であり性能採用判定には使わない。

最小空きは物理1,064,701,952B／commit11,524,370,432B。これはsampled headroomであり、process peak／VRAM peakを測った値ではない。

## 9. expert-cache／メモリの指示

一度2048固定で比較するよう指定されたが、その後の**公式リポジトリ準拠**が最新指示。公式固定版の`auto`算定・確保後再確認・縮小処理は変更していない。容量の余裕は公式の`--vram-reserve-mib`で指定する。

直近の短い診断で通った設定は`--expert-cache auto --vram-reserve-mib 6144`。6144はMiBのreserveで、cache slotsではない。製品の新default・最速値・正式比較の最適値とは認定していない。9216ではF32側cache0になりspec生成不可。4096ではTTS稼働中にメモリ不足になった。条件を混ぜず記録する。

model起動の最低空き: physical4GiB／commit8GiB。runtimeはcommit2GiB未満で即停止、physical256MiB未満が30秒継続すると停止。変更していない。失敗したprerequisiteから次のモデルを起動しない。新しい試験はunique labelで、以前の証拠を上書きしない。

ページファイルはC:/pagefile.sys、固定32GiB（initial=max32768MiB）。読み取り時点で使用7423MiB／boot peak16370MiB。OS設定やdriver policyは変更していない。仮想メモリはcommit容量と安定性に役立つが、頻繁なpagingを速度向上と同一視しない。file-backed GGUFのpage faultとpagefile I/Oを分けて測る。

以前ユーザーがUnity／irodoriTTSを終了してよいと明示。今回、メモリ不足後にirodoriのwrapper49080／main13316を、パス・生成時刻・保持Process handleで識別して終了確認。Unity Editorはその時点で存在しなかった。PIDだけの再利用危険を避けた。CIM時刻は100nsがmicrosecondへ丸められるため、最初の厳密比較は安全に拒否し、実Processの100ns値を確認してから実施した。他アプリは終了していない。これを新しい無関係アプリを終了する許可へ拡張しない。

最終確認時H空き147,545,198,592B、C空き17,030,545,408B。RAM空き12,360,928KiB／virtual空き24,512,744KiB。モデル／compiler processなし、8080 listenerなし。これらは変化するため再開時に再確認する。

## 10. 優先する32GB向け調査候補

F32接続時の空きVRAMは7.93GiB、offは11.33GiB。session計算だけでは説明しきれない差がある。静的候補は`tqcodec/src/cache_cuda.cu:151`の監査kernel内`float f[128*128]`。compile結果でlocal66560B/thread、1block1thread launch。CUDA contextのlocal-memory予約が差に関係する可能性があるが、**原因は未実証**。

先行公開後、隔離した同条件processでaudit前後の実メモリを測る。原因が確認できたら、同じ128基底・FP64 Gram・Det・drift・故障検出を維持したまま、64KiB shared memory等へ作業領域を移す候補を評価する。sm120のopt-in shared容量を実照会し、quiescent init時に設定する。監査を弱めたり隠して速度を作らない。

通常/offの短い診断ではhost dispatch／expert I/O時間も大きい。公式Windowsの`STRATA_FILE_RELEASE`、既存batched PrefetchVirtualMemory、pin headroom等を確認してから重複実装を避ける。FILE_RELEASEは過去の別PCでは空きRAM改善があってもcommitやSSD readを減らしたとは限らず、このPCで試験未実施。詳細は`task-4-performance-outline.md`。

## 11. P1先行配布の準備状況

**まだ担当をdispatchしていない。** 完成済みbrief:
`.superpowers/sdd/2026-10-24_strata_030_completion_execution_Codex/task-P1-preview-brief.md`

予定成果物: `Strata-0.3.0-preview.20261024.1-windows-x64-sm120-engine.tar.7z`。
作業候補: `H:/Strata/releases/0.3.0-preview.20261024.1`、`H:/Strata/build/preview-package-20261024`。存在を確認し、新しい領域で進める。

GitHub connectorにはRelease asset upload機能が見つからなかったため、公開はgh CLIを使う方針。`gh`2.96.0、zapabobアカウント、repo ADMINを確認済み。tokenを出力・ファイル保存しない。

7z: `C:/Program Files/7-Zip/7z.exe`。tar: `C:/Windows/system32/tar.exe`。必要DLLはdumpbinで調べた。
- CUDA `cublas64_13.dll`とdynamic dependencyの`cublasLt64_13.dll`を確認・同梱する必要がある。
- MSVCP140、MSVCP140_ATOMIC_WAIT、VCRUNTIME140、VCRUNTIME140_1が必要。app-local redistributableを適切なlicenseとともに扱う。
- CUDA SDK `C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3/bin/x64`。cuBLAS約52.7MB、cuBLASLt約463.7MB。EULA.txt／LICENSEを読む。
- MSVC redist: `C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Redist/MSVC/14.44.35112/x64/Microsoft.VC143.CRT`。
- driver DLLやSystem32のOS DLLをコピーしない。cuBLASの間接／dynamic依存と実際のロード元を検査する。

既存`packaging/package_engine.py`と`binary_deps.py`を利用できる。ただし前者は既存partialディレクトリや失敗stageを削除する処理がある。既存証拠を失わない新しいstageを使うか、pure helperだけ利用する。配布manifestは自身をhash対象から除外し、外側SHA256で最終archiveを対象にする。署名なしとSHAの意味を区別する。

README／Release冒頭は80〜100語British English TL;DR。実装済み・実機確認済み・失敗・未実施を分ける。既存READMEはまだ更新していない。上流GUIの案内と、このforkのengine previewの導入を区別する。

## 12. PoC図表・データ

ユーザーは提供PoC図表の使用を許可している。
`H:/Strata/reference/triality-paper-20261023/paper/figures/tiny_vocab_kl.png`
同rootの`evidence/tiny_lm_summary.csv`, `summary.json`, `tiny_lm/results.json`, `environment.json`が元データ。

Linux CPU、合成tiny LM、独立教師3seed。Windows／27Bの測定に置き換えない。single6 KL≈0.0000306145、triality3x2≈0.0279132、trained Q≈0.0236220。改善の探索的95%CI[-0.0048985,0.0134808]は0を含む。single6優位を省かない。

`scripts/build_summary.py`は集計とCIを再生成するが、元PNGのplot scriptではない。元rasterのbitwise再生成を保証したと書かない。許可済みPNGをsource hash／captionと共に使うか、標準plotting toolで保存データから別図を再生成する。61ファイル全体や生の個人path付きログを配布に混ぜない。

## 13. 重要なモデル・依存pin

Hikari:
`C:/Users/downl/Desktop/SO8T/gguf_models/zapabobouj/Hikari-Bonsai-27B-Nimble-LoRA-GGUF/Hikari-LoRA-fixed-scale-PQ2_0.gguf`
7,206,168,928B、SHA `0ab2a1f237b73e5002ecd8c9b764249b90ee59eca749a6226c44bb43b1036a13`。
qwen35、64層、通常Attention16／再帰48、Q24/KV4/d256。別Hikari07モデルに無言で置き換えない。

Q2:
`H:/Strata/models/q2_0/Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00001-of-00002.gguf`
37,623,740,192B、SHA `69820c02ec7d0b45ef2ebb19d6620299db749fe2aded7f39f93c6b88b199b720`。
第二shard 28,800,138,432B、SHA `316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113`。
pack: `H:/Strata/models/q2_0/native-pack-030-20261023`。experts.binなし、元GGUFのmmap。qwen4exp48層、QSA12／GDN36、Q24/KV2/d256。

独立source receipt: `H:/Strata/build/completion-resources-20261024/q2-model-source-hashes.json`、SHA `560fcb1126d0e65d0b4f0a7ea1802c2cf1b4cf1c2c35dfeafb1e4d559648f553`。
pack binding: `H:/Strata/build/task5a-pack-binding-20261024-01/binding-final.json`、SHA `57445eeb434049ae7c3f9d00712a2b758c9475e9cee9a002918b6fcc16dc89fb`。

| 対象 | 固定SHA |
|---|---|
| Strata upstream | `011c9e600a93bbc9fd451c563501b5831c32bbca` |
| zapabob/llama.cpp | `2c8e9655cdc6ea31051d4437a71492e717d046a4` |
| PrismML/llama.cpp | `73bfe6cc485554822f80c473a3c0c4f25e80f41b` |
| Turboquant-CUDA | `d85c787733f6a973d7cfe953d11276701a3c09e0` |
| 上記llama参照 | `81b08be15c554918a8cfe20d5f0846038082430f` |
| TheTom/llama-cpp-turboquant | `643956891dfdf51aecdbd05ca508dd21e21e8195` |
| TheTom/turboquant_plus | `ba52ad107d1fdd02bc9be8fd85308226b75c905b` |
| native GGML | `3cf03257f219afbe7334045ff7c6a06ac68c627d` |

依存やGGMLを別forkへ一括置換しない。Prism weight codecとTurbo KV codecを混同しない。

## 14. 正式版へ残る作業

本物のF32／圧縮三K生成、キャッシュ保存・復元・複製・prefix・位置処理とGDN/PLEを含む全状態、実GPU fault時の停止、load/profile全監査と1024 accepted tokenまたは60秒の巡回監査は未完了部分がある。frozen cでA(c)を監査し、入力依存写像全体のJacobian直交性とは区別する。

Prism/Hikari16通常層、TheTom、配布版Control／GUIの独立K/V設定、Q adapter、元PQ2重みの層単位蒸留、capture1GiB制限、Fisher較正、QJL既定β=0、学習／較正／選択／最終評価の分離も残る。

正式版は両必須モデルで入力4096／32768token＋生成枠、3warmup／10交互pair。速度中央値5%以上改善、TTFT悪化5%以内、PPL増加1%以内、新規機能失敗0、監視cost1%以内が目標。総metadata/scratch込みの容量を合わせ、高精度single-view6bitとも比較する。tinyモデル原3seedと追加固定3..12seedは別集計。全条件未達で正式v0.3.0完成とは報告しない。

準備済みoutline: task-4c2-outline.md、task-4e-prism-consumer-outline.md、task-5-control-routing-outline.md、task-6-calibration-outline.md、task-6-preregistration.md、task-6-dataset-candidates.md、task-7a-overlay-build-cache-outline.md、task-8-source-freeze-outline.md。P1先行公開が直近優先。

## 15. 過去の拒否・ツール上の注意

過去の一時ファイル削除:
`H:/Strata/build/task5a-gateA-spin8-20261023/scripts/__pycache__/compare.cpython-312.pyc`
は自動承認で拒否され、理由は`blocked by policy`のみだった。別経路で削除していない。ファイルを保持して試験対象から除外した。これは実装全体を止める現在のblockerではない。

apply_patchはWindows絶対pathで書込みtransport失敗があり、通常の権限でPowerShellのliteral here-string＋IO.File書込みは成功した。ACLや権限を変更していない。resource preflightの不合格やProcess生成時刻不一致による自主拒否は、自動承認の拒否と混同しない。

## 16. 今回の引き継ぎ時点の結論

ソースはmainへpush済み、差し替え防止修正の独立レビューは解決済み。次はP1の先行配布。mainpushを再実行するために空コミットを作らない。新しいP1の変更だけを専用branchで実装・確認して通常反映する。配布、タグ、Release、正式な速度／品質改善、三K実生成の完成を済んだものとして扱わない。