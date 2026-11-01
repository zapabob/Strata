# GDN CUDA resource audit and bounded specialization experiment

2026-11-02 JST / Codex / source HEAD `be0960a0707ab2e7fc1a90d5a7888ffd149c9858`

結論は、通常native経路の一部に実際のレジスタスピルがあり、単一セッションで不要な分岐をコンパイル時に取り除く試作で解消できた、というものです。既存参照とのビット一致と、memcheck・racecheck・synccheckも通りました。ただし共有GPUでの時間測定は条件が安定せず、実モデルの高速化は未確認です。今回の試作はビルド用ディレクトリ内に留め、本番の `verify_kernels.cu`、既定値、Expert配分には適用していません。

この作業より前の `native_gdn.cu` / `native_gdn.hpp` の実験変更と、利用者の `apps/desktop/src-tauri/Cargo.toml` の変更は維持しました。サービス停止、GPU設定変更、モデルの再配置、インストール、commit、pushは行っていません。

## 実際に検査した対象

RTX 5060 Ti、sm_120、36 SMに対し、CUDA 13.3のnvccで現在のソースを単独コンパイルしました。コンパイラの主結果は `build/gdn-resource-qualified`、最終の時間測定は同じオブジェクトを使った `build/gdn-resource-runtime-r2` の記録です。C++20、O2、Windows Releaseの静的CRT `/MT`、`STRATA_VERIFY_MAX_T=8` を指定し、GDNには `--use_fast_math` を付けていません。`ptxas -v` のspill load/storeと、`cuobjdump --dump-resource-usage` のSTACK/LOCAL/REGを照合しています。フルエンジンのビルドや、前回使用した既存エンジンexeそのものの解析ではありません。

`fused_gdn.cu` の単発融合版と、`verify.cpp:1648` から使う `verify_kernels.cu` の複数トークン版は別のカーネルです。前回の15.7〜15.9 usを、後者の実測値として引用してはいけません。

| sm_120の版 | registers/thread | stack B | spill stores B | spill loads B |
|---|---:|---:|---:|---:|
| 単発 `gdn_step_norm_kernel`、sigmoid / SiLU | 128 | 0 | 0 | 0 |
| multi `ALL_OUT=true, Q=false` | 84 | 0 | 0 | 0 |
| multi `ALL_OUT=true, Q=true` | 84 | 0 | 0 | 0 |
| multi `ALL_OUT=false, Q=false` | 128 | 0 | 0 | 0 |
| multi `ALL_OUT=false, Q=true` | 128 | 8 | 16 | 8 |
| 上記の対象だけを単一セッション用に特殊化した試作 | 128 | 0 | 0 | 0 |

`ALL_OUT=false` は状態commitだけでなく、出力開始位置をずらした検証にも使われます。`n_keep == nullptr` があり得るため、そのnull検査を単純に削除する変更は不正です。今回の試作はnull検査を維持しています。

この表のspill値はコンパイラが報告する静的な値で、実行全体のDRAM転送量ではありません。また、元の対象版はLOCAL=0でも実際にはspillを持っていました。lmemやLOCALの1項目だけで判定するのは不十分です。

## 実装した試作と比較

`tools/audit_gdn_cuda_resources.ps1 -CompareUngroupedQuantized` が、現在のソースから次の3箇所だけを変えた一時ソースを作ります。kernel templateに既定falseの `UNGROUPED` を足し、グループ処理の条件を `!UNGROUPED && grp.n > 0` にし、通常の非group呼び出しのうち `ALL_OUT=false,Q=true` だけ `UNGROUPED=true` を渡します。

その呼び出しはもともと `GdnGroups` を省略し、既定の `grp.n=0` を渡しています。したがって取り除くのは実行されない分岐です。状態更新、FMA、加算順序、Q8_1の丸め、状態保存の条件は変更していません。group呼び出しと、ほかの3つの通常版は従来の分岐を残しています。主結果では、ほかの3版のレジスタ・stack・spill値も元と同じでした。

別の比較として `__launch_bounds__(512,2)` を全multi版に指定しました。対象の `false,true` は64 registers・spill 0になりましたが、残り3版にspillが発生しました。`true,false` は44 B store / 40 B load、`true,true` は24 / 20、`false,false` は8 / 8です。一律の常駐ブロック数増加は採用していません。この比較版はコンパイル検査のみで、実行速度・正しさの検証対象にはしていません。

NVIDIAの説明でも、常駐ブロック数の制約からレジスタ上限を下げると、local memoryや命令が増える場合があるとされています。launch boundsの指定はスピル除去を保証しません。[CUDA Programming Guide, Launch Bounds](https://docs.nvidia.com/cuda/cuda-programming-guide/05-appendices/cpp-language-extensions.html#launch-bounds)

## 正しさと時間測定

現在の `src/kernels/gdn_parity.cpp` を、元版と試作版それぞれのverify/fusedオブジェクトにリンクしました。その他のカーネルは、既存 `H:/Strata/releases/hakua040-native-upstream-r1/Release/strata_kernels.lib` で解決しています。そのライブラリ、テストソース、実行ファイルのハッシュを記録しています。現在の全カーネルを再ビルドした結果ではありません。

両方とも実モデルと同じS=128、H_k=16、H_v=48で失敗0でした。T=1〜8のGDN出力・状態・Q8_1画像を含む79ケースがビット一致し、alpha/betaの8ケース、5層分のcommitをまとめる8ケースも通りました。これは固定された合成入力による検証であり、実モデルのlogits・生成品質の評価ではありません。

`bench/gdn_multi_resource_bench.cpp` は、以前の単発融合版ではなく、実際の `gdn_step_norm_multi` の `ALL_OUT=false,Q=true` 分岐を呼びます。n_keep=T、t_out_begin=0、T=1/2/4/8で、CUDA GraphとCUDA Eventを使いました。元版→試作、試作→元版の順序を交互に4組実行し、各組・各条件15試行、最終測定だけで計960件を保存しています。初回の960件も別に保持しました。非blocking streamを使う測定コードの初期化について、cudaMemcpy/cudaMemset完了を明示的に待つ処理を追加し、最終測定を取り直しています。両版のparityも再度通りました。時刻は1カーネル呼び出し当たりで、T>1の場合は1トークン当たりではありません。

| 状態バッファ数 | T | 元版 us/call | 試作 us/call |
|---:|---:|---:|---:|
| 1（3 MiB） | 1 | 7.471 | 6.946 |
| 1（3 MiB） | 2 | 9.259 | 8.899 |
| 1（3 MiB） | 4 | 13.017 | 12.787 |
| 1（3 MiB） | 8 | 20.987 | 20.544 |
| 48（144 MiB） | 1 | 25.831 | 26.133 |
| 48（144 MiB） | 2 | 26.953 | 26.271 |
| 48（144 MiB） | 4 | 30.936 | 32.389 |
| 48（144 MiB） | 8 | 49.607 | 49.375 |

値は各実行の中央値4個の中央値です。最終測定の全実行の値もruntime-r2/summary.jsonに残しており、不利な実行を除外していません。同一バッファはキャッシュ再利用のある条件ですが、全ロードがL2 hitであることを測ったわけではありません。48バッファも全DRAM missの証明ではありません。入力は繰り返し使用され、状態は更新を継続しています。

最終測定の最初のbeforeはGPU利用率97%、試作の最後のafterは99%でした。この値は外部処理と自分のベンチを区別しません。外部GPU処理を止めておらず、クロックも固定していません。144 MiB・T=1の元版の各実行中央値は26.081 / 25.838 / 19.282 / 25.823 usと大きく動いています。この状況で平均値の差や統計処理だけから安定した高速化を認定することはできません。`performance_qualified` はfalseです。実モデルのms/token、tok/s、DRAM帯域比率は未測定です。

## メモリと他の提案の確認

`src/program/generate.cpp:6971` 付近には、残りVRAMと後続の確保分を考慮する `--expert-cache auto` が既にあります。`ExpertCache::open` にも空きVRAM確認があります。GPUキャッシュを増やすだけで、ファイルマップやホストバッファが同量解放されるわけではありません。今回も他のGPU処理が約11 GiB以上を使用しており、16 GiB全体が利用可能な状態ではありませんでした。

このpackの最大Expert blobは1,382,400 Bです。512枠は675 MiB、256枠は337.5 MiBです。枠数半減の直接の差は337.5 MiBのデバイス用キャッシュで、数GiBのホストRAM削減という根拠にはなりません。キャッシュmiss、CPU処理、マップしたページの参照量も変わり得るため、別のA/B実験として扱う必要があります。

`FileExpertSource::claim_stage` は、3層経過または256回の組み立てを再利用条件とし、使用中のバッファを避け、DMAイベントも確認しています。pinningは利用可能RAMで判定する既存処理です。固定2〜4層の厳密な容量上限ではなく、並行使用数によって増え得ますが、全層分を無条件で確保する構造でもありません。`FileExpertSource::blob` にはマップを直接渡す経路もあります。前回のログとプロセスメモリ値だけでは、StagePoolがRAM不足の主因かは判定できません。

`native_mmvq.cu:1292` 付近には、重みを `F::load` した後、各入力列に `F::apply` するループがあり、2〜8列のdispatchも実装されています。元から重みを再利用する経路に、再度1/M削減を適用することはできません。また1/Mは条件付きの重み読み出し量の議論であり、全DRAM通信量や実行時間の保証ではありません。Tensor Coreへの置換も、演算形式・丸め・加算順序の契約を別途検証する必要があります。

`native_mmvq.cu` 自体も参考としてsm_120コンパイルしました。1003 entry中277 entryはSTACKまたはLOCALが非ゼロでした。これはテンプレートや実装選択を含む一覧で、全てが実行されるわけではなく、STACKだけから全てをspillと呼ぶこともできません。どの型・shape・列数が実モデルで時間を占めたかは今回未確認です。この参考コンパイルは初期の `/MD` 設定で、runtime検証に使ったGDNの `/MT` 再ビルドとは区別しています。

入力のconst/restrict指定もGDNに既にあります。さらに `pdl.hpp` では、同期前の読み出しを避けるためCUDAのactivation/outputにrestrictを付けない設計があります。全入力へ一律に `__ldg` / restrictを追加する変更は行っていません。

前回のbaseline-r2はOOMではなく、空きRAM 2 GiBの安全下限を下回った際のコントローラ停止です。今回も実モデル再実行の開始条件であるRAM 16 GiB、VRAM 8 GiBを満たしませんでした。開始条件自体が完走保証ではない点も変わりません。モデルの再実行、MTPを含む完走、E2Eのプロファイル内訳は未実施です。

## 再現と記録

新規ディレクトリを指定して、PowerShell 7で次を実行できます。既存の証拠ディレクトリに重ねることは拒否します。

```powershell
./tools/audit_gdn_cuda_resources.ps1 -OutputDirectory build/gdn-resource-repeat -CompareTwoBlockBound -CompareUngroupedQuantized
./tools/benchmark_gdn_resources.ps1 -AuditDirectory build/gdn-resource-repeat
uv run --no-project --python 3.12 python tools/analyze_gdn_resources.py build/gdn-resource-repeat --output build/gdn-resource-repeat/summary.json
```

参考MMVQのコンパイルを含める場合は最初のコマンドに `-IncludeNativeMmvq` を付けます。実行用のscriptは、子プロセスのSTRATA_*設定を除き、各試験に120秒の上限を設けます。実モデルや稼働中サービスは起動・停止しません。試作のmemcheck/racecheck/synccheckは全て失敗0で、完了状態は証拠ディレクトリのvalidation.jsonに記載しています。これらは同一CUDAオブジェクトの初回parity実行ファイルに対して行った検査で、測定コードの初期化待ち追加後にsanitizerを再実行したものではありません。

最初のリンク試行では、実験オブジェクトの `/MD` と既存ライブラリの `/MT` が不一致でリンクに失敗しました。主結果ではReleaseに合わせて `/MT` で再コンパイルし、リンク・実行に成功しています。失敗ログはdiagnosticsに保存し、成功結果に混ぜていません。

証拠は `bench/results/2026-11-02-rtx-5060ti-gdn-coalesced/resource-audit/`、再実行用のコードは `tools/audit_gdn_cuda_resources.ps1`、`tools/benchmark_gdn_resources.ps1`、`tools/analyze_gdn_resources.py`、`bench/gdn_multi_resource_bench.cpp` です。CUDAだけを検査しました。HIP/SYCL/Metal、フルエンジン、実モデル品質、専有GPUでの性能確認は未実施です。