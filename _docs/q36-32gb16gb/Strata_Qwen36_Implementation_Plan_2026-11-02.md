# Strata Qwen36・RAM 32GB / VRAM 16GB 起動・推論改善 実装計画書

> **For agentic workers:** 実装時は `superpowers:executing-plans`、または利用可能なら `superpowers:subagent-driven-development` を使い、以下のtask単位でTDD・レビュー・証拠保存を行う。並列化は独立ファイル／別worktreeに限定する。

**Goal:** 同一のQwen3.6-35B-A3B UD-Q4_K_XLと64K contextを維持し、起動失敗・約10分の初期化・不明瞭な進捗を改善し、RAM 32GB / RTX 5060 Ti 16GBで継続利用できる推論経路を作る。

**Architecture:** 既存Host → Control → Python server → native Qwen36の境界を維持する。最初にrun identity・能力契約・起動stage・停止所有権を整え、次に並べ替え済みread-only expert backingと上限付きpinned stagingをopt-inで追加する。CUDAは実測でcritical pathと確認されたQwen36専用経路のみを、小さな差分で最適化する。

**Tech Stack:** 既存TypeScript / Node Host、Python Control/server、C++ / CUDA、Windowsのprocess/file/memory API、既存CTest・Node test・Python test。現在のsm_120配布条件と固定CUDA toolchainを引き継ぐ。

**Spec:** 同梱 `DESIGN.md`。先に読むこと。数値証跡は `evidence-summary.json`、根拠は本書末尾。

**Status:** **PARTIAL_IMPL / GPU mapped-live BLOCKED / T04–T08 NOT_RUN**。Host契約・startup stage・mapped-pack+pin-pool・installer `.5` までは実装済。Windows GPU の mapped-pack live と paired 速度は **未実行**（偽速度禁止）。完了宣言しない。

| Gate / task | 2026-11-04 時点 | 注記 |
|---|---|---|
| Host Q36 node tests | PASS 19/19 | non-GPU; cache を C: に退避して再実行可 |
| T03 GUI refuse (private-cache) | PARTIAL | chatbot on; 強制解除なし |
| T03 chat → stop → restart | **NOT_RUN** | Q36 serve 未成立 |
| mapped-pack live (UD-Q4_K_XL / ctx65536 / MTP2) | **BLOCKED** | Hermes llama-server が VRAM 占有; DESIGN #6 で未殺 |
| T04 / T06 / T07 / T08 paired speed | **NOT_RUN** | live 前提が未達 |
| H: disk for live/release | FreeGB **14.2** (was ~0–1) | 2026-11-04 reclaim; remnant npm lock ~0.58 GB |
| Goal complete | **false** | UpdateGoal complete しない |

**基準日:** 2026-11-02 JST  
**公開main確認SHA:** `170e0d330edd9c03b5dcddfc64b77e498387ff86`  
**実装先の推奨:** `_docs/Strata_Qwen36_Implementation_Plan_2026-11-02.md`。関連仕様・証跡は同一作業ブランチへ置く。

## Global Constraints

- 主対象はWindows native Qwen36。Hikari/PrismML、TurboQuant、Flash-Next、Hakua記憶を巻き込む再設計をしない。
- 主baseline: 同一GGUF、context 65,536、MTP 2、parallel 1、実効prefill 2,048、現行FP32 persistent KV。元のauto要求と実効値を両方保存する。
- Context短縮、KV量子化、top-k削減、expert pruning、別モデルへの置換、MTP無効化は主改善に混ぜない。
- Windowsの専用VRAM、shared GPU memory、process private commit、working set、file-backed resident pages、system commitを分ける。
- `--no-warmup`だけでREADYを早めても、最初の有用tokenまでが改善しなければ起動高速化に数えない。
- 新経路はopt-in、旧経路を残す。source/binary/quant/layout identityが不明なら新経路へ進めない。
- unsupportedな明示設定は事前拒否。認証・private-cache要求を削除して動作したように見せない。
- 他アプリのserverは停止しない。モデル原本、個人記憶、設定、署名済み配布物を直接上書きしない。
- 設定・パス・能力を検証した同じsnapshotから実際のargvを作る。検証後の再読込をしない。
- mainへ直接push/merge/releaseしない。今回の成果物は計画であり、PC操作・リリースの許可ではない。

## Review Focus

1. C/H配下のjunction、同名別モデル、モデルの書換え、途中移動 → T01/T05でfile handle identity・digest・TOCTOUテスト。
2. `--prompt-cache 0`等をQwen36が無視 → T01でprivate要求をfail closedし、既存他backendを保持。
3. loading中のcancel、PID再利用、stale ready、旧process残留 → T03でgeneration/job identityの回帰・故障注入。
4. CPU read／CUDA DMA中のcache eviction・unmap・buffer再利用 → T05/T06でleaseとeventを故障注入。
5. READYだけ高速化、64Kのcapacityだけで長文合格、短文だけ速い → T04/T09で初回応答・実長文・paired性能を検証。

---

## 0. 採用する方針と、今回やらないこと

本計画は「GPU使用率を100%にする」計画ではない。**同じ出力契約で、待ち時間・不要なコピー・メモリ圧迫を減らす**計画である。

推奨する順序:

```text
T00 基準固定
  → T01 パス・能力・実効設定
  → T02 起動stageの観測
  → T03 起動許可・停止・重複防止
  → T04 warmupを分解・比較
  → T05 expert backing / 小容量pin
  → T06 転送・配置アルゴリズム
  → T07 実測hotspotのCUDA kernel
  → T09 製品統合・署名・E2E

T08 KV保存精度の変更は独立の任意試験。T09の必須前提ではない。
```

T01–T03は正確性・診断性として独立採用できる。T04–T08は性能と品質の実機証拠がない限り既定化しない。大規模リファクタ、別ランタイムへの乗換え、全backend共通allocatorの新設は範囲外。

## 1. 歴史的baselineと重要な訂正

### 1.1 添付ログ

同じSHA-256の添付2件を一つの証跡として扱う。詳細は `evidence-summary.json`。

| 項目 | 観測 | 計画への反映 |
|---|---|---|
| 起動記録22件 | host allocation失敗14、VRAM不足2 | 同じ実効設定での高コスト再試行を防止 |
| 完了したstage | 初期28.6s、配置266.0s、warmup306.6s | 各stageを別々に計測・最適化 |
| Host expert | 全18.75GiBがpageable | 全量匿名arenaと巨大pin試行を本線の改善対象にする |
| GPU expert | 各層41/256、計3.00GiB | slot比率とrouting hit rateを混同しない |
| 転送用staging | 1.10GiB | これはGPU側のstage pair。新host pinned poolと別集計 |
| 論理入力パス | 全て `--native H:\...gguf` | resolved path / file IDを起動前後で照合 |
| 最終要求統計 | 0 of 0 | decode速度・仕事量は未計測 |

記録3区間の和601.2秒は重複しないtimerの単純和。初期化全体・API readiness・初回応答を含むwall timeではない。588秒のserver待機ログと厳密に同一時計へ結び付けない。

### 1.2 ソースで確認した境界

`src/qwen35/q36_engine.cu`:

- `load()`（約960–1120行）: GGUFを既にmap。dense等をGPUへ転送。`want_mtp`は使わず、ファイルにMTPがあれば読込む。
- `expert_blob()`: gate/up/downを既存quant形式のまま並べ替える。
- `Engine::init()`（約1460–1520行に末尾）: state・KV・scratch等を確保し、context/chunk/free VRAMを出す。
- `warmup()`（約2753–2785行）: full chunk、小GEMM、decode、speculative probe、同期・reset。
- `place_experts()`（約2795–3010行）: 内部reserve 768MiBを基準にhybrid判定。全量host arena、CPU pool、GPU slots、GPU staging pair。
- `run()`（約3730–3890行）: `--no-warmup`は既存。未対応flagはserve modeで警告して読み飛ばす。
- main hybridでは `E.use_graph=false`。全体をCUDA Graph化すれば解決するとは扱わない。

したがって「GGUFのmmapを初めて導入する」ではなく、**既にmapしたGGUFから追加生成する全expert arenaをどう減らすか**が対象である。

`--mtp 0`は現行ではMTP weight/KVの確保削減にならない。MTP allocationのlazy化は別の配置・精度検証が必要であり、本計画では標準採用しない。

## 2. ファイル責務と再利用

下表の既存ファイルは既存責務を延長する。新規名は提案であり、同じ責務の実装が最新mainにあれば再利用し、並行した第二の設定系を作らない。

| 領域 | 既存変更候補 | 追加する小さな単位（提案） |
|---|---|---|
| Model選択・argv | `apps/host/server/native-control.mjs`, `native-resources.mjs`, `native-settings.mjs`, `setup.py` | `apps/host/server/q36-run-contract.mjs` |
| 見積もり・観測 | `model-memory.mjs`, `run-observation.mjs`, `vram-observation.mjs`, `apps/host/src/lib/native-fit.ts` | Qwen36用geometry/観測を既存schemaへ追加 |
| Server状態 | `serve/server.py`, `strata_control/runtime.py`, `apps/host/server/control-runtime.mjs` | `serve/q36_startup_events.py` |
| UI | `apps/host/src/components/NativeModels.tsx`, `NativeLocalModel.tsx`, `apps/host/src/lib/native-monitor.ts` | stage / requested-effective差分表示 |
| Engine | `src/qwen35/q36_engine.cu`, `src/qwen35/q36_kernels.cuh` | `include/strata/qwen35/expert_store.hpp`, `src/qwen35/expert_store.cpp`, `include/strata/qwen35/startup_trace.hpp` |
| Test | `apps/host/tests/`, `tests/`, `tools/qwen35/`, `CMakeLists.txt` | `tests/qwen36/`, `tests/qwen35/`以下の小fixture |
| Benchmark | 既存`bench/strata-16gb/`、既存q36 gate | `bench/q36-32gb16gb/`, `tools/qwen35/q36_startup_bench.py` |

I/Oと所有権はCPUで単体試験できるC++へ切り出す。CUDAの巨大ファイル全体を整理し直さない。共通kernelに変更が必要になった時点で、affected backendを追加し、CUDA/HIP/SYCLの検証範囲を再設定する。

## 3. 共通interface（すべて提案）

### 3.1 Q36RunContract

`q36-run-contract.mjs` に次を定義する。既存RunPlanがある場合はそのQwen36 variantとして実装する。

```ts
type Q36RunContract = {
  schemaVersion: 1;
  runId: string;
  generation: string;
  backend: { family: 'qwen36'; binarySha256: string; capabilityRevision: string };
  model: {
    requestedPath: string; resolvedPath: string;
    fileId: string; volumeId: string;
    sizeBytes: string; contentSha256: string;
    geometryDigest: string; tokenizerDigest: string;
  };
  requested: { context: number; prefill: 'auto' | number; mtp: number; parallel: number };
  effective: {
    context: number; prefill: number | null; mtp: number; parallel: number;
    persistentKv: 'fp32'; warmupMode: string; expertStoreMode: string;
  };
  securityPolicyDigest: string;
  argv: string[];
  configDigest: string;
  warnings: Array<{ code: string; message: string }>;
};
```

`buildQ36RunContract(input, capabilities, modelIdentity, policy)` は成功contractまたはtyped validation errorを返す。JSONのbytesはdecimal stringとし、計算途中はBigInt/uint64を使う。秘密を含むpath/argvはローカル表示用。公開benchmarkは別のredacted serializationを使う。

### 3.2 起動event

```text
Q36_STARTUP { schema:1, run_id, generation, stage, state,
              elapsed_ms, stage_elapsed_ms, bytes_done, bytes_total,
              model_identity_digest, measurements, error_code }
```

出力先はstderr。既存stdout `READY/GEN/T/DONE`を壊さない。`state=begin|progress|end|error|cancelled`、不明値はnull。stageは `identity, dense_load, buffers, expert_host_alloc, expert_repack, expert_upload, warmup_prefill, warmup_decode, warmup_spec, engine_ready`。HTTP ready、GUI ready、first useful tokenはserver/Host側で別記録する。

### 3.3 ExpertStore

```cpp
struct ExpertKey { uint32_t layer; uint32_t expert; };
struct ExpertSpan { const std::byte* data; uint64_t bytes; };
class ExpertLease {
public:
    ExpertSpan span() const;
    // move-only RAII。copyは禁止。参照中のmapping/cache evictionを禁止。
};
class ExpertStore {
public:
    ExpertLease acquire(ExpertKey key);
    uint64_t committed_bytes() const;
    uint64_t mapped_bytes() const;
};
```

CPU workerが保持するleaseはjob完了まで、DMAに使うpinned slotはcopy completion eventまで保持する。host pointerの寿命とdevice staging slotの寿命は別管理。

---

## T00 / PR-0: 実装基準と再現fixtureを固定する

**変更:** `bench/q36-32gb16gb/README.md`, `workload.json`, `tests/qwen36/test_startup_log_analysis.py`。元ログはローカル保管し、リポジトリには合成または匿名化fixtureだけを入れる。

**入力:** `DESIGN.md`、今回のログ、実装時のworking tree。  
**出力:** source/binary/model/hardware bindings、baselineとNOT_RUNの区別、再現用fixture。

- [ ] `git status --short`, `git remote -v`, `git rev-parse HEAD`を保存。dirty treeをresetしない。最新remoteとの差分を確認し、承認されたbaseから隔離worktreeを作る。
- [ ] RED: 合成fixtureで「重複uploadを一回だけ数える」「後続なしはunknown」「0/0はhit rate=null」「異なるgenerationの時間を足さない」をassertする。
- [ ] fixture parserだけを最小実装しGREEN。既存ログ22/14/2/2/1との集計を手元で照合する。これは性能検証とは呼ばない。
- [ ] 実機のCPU、RAM、GPU、driver、toolkit、PCIe、専用/共有VRAM、process commit、C/H volume identity、disk残量を取得。modelのSHA・quant・tokenizer・インストール版EXE/DLL digestをbindingへ記録する。
- [ ] baselineは記憶アクセスを伴わない通常テキスト推論をモデル単独で計測する。未認定のprivate経路は性能baselineに使わない。他serverは一覧表示まで。停止は所有確認と明示的な運用許可の範囲内。GPU試験中に大規模buildを同時実行しない。

**検証予定:** `python -m unittest discover -s tests/qwen36 -p 'test_startup_log_analysis.py' -v`。期待: fixture合格。Windows baseline未実行ならNOT_RUN。

**commit案:** `test(q36): bind startup evidence and baseline conditions`

## T01 / PR-1: パス・モデル同一性・backend能力を同じ実行計画へ固定

**変更:** `q36-run-contract.mjs`（新規候補）、`native-control.mjs`, `native-resources.mjs`, `native-settings.mjs`, `setup.py`。  
**Test:** `apps/host/tests/q36-run-contract.test.mjs`, `q36-capabilities.test.mjs`。

**入力:** T00のbinding、ユーザーが選んだモデルファイル、既存user argsとprivacy policy。  
**出力:** §3.1のcontract、capability error、requested/effective差分。

- [ ] RED: C指定がHへ差し替わらない／同名別hashを拒否／空白・日本語path／junction同一fileを二重起動しない／検証後の設定変更をargvへ混入しない、のテストを作る。
- [ ] ファイルをopenして最終pathとfile IDを取得。Windowsではfinal path API等でreparse先を確認する。path文字列や`realpath`だけでphysical volumeを断定しない。same basenameをsame model扱いしない。
- [ ] binary digestに束縛したQwen36能力表を用意。既存支持flagは `--max-context`, `--prefill`, `--mtp`, `--pool-workers/--cpu-threads`, `--batch`, `--expert-vram`, `--expert-slots`, `--hybrid-rows`, `--no-warmup`等。実装時に固定parserと一致を再確認する。
- [ ] RED→GREEN: 明示された `--cache-type-v turbo3`、`--cache-type-k q8_0`、`--spin8-mode consensus`を「適用済み」にしない。明示unsupportedは停止前のvalidation error。Host自身が誤注入したperformance flagは元設定をbackupし、未適用と説明してQwen36のargvから除く。保存値を黙って消さない。
- [ ] **privacy例外:** `--prompt-cache 0` / `--conversation-cache-mib 0`等がsecurity policy由来なら、削除して続行しない。Qwen36が同等の隔離契約を満たす証拠がなければ、そのprivate経路を起動前に拒否する。通常chatと別backendの既存private経路は維持。
- [ ] qwen36では効かない `--resident-budget-gib` の削減を自動retry案にしない。`--vram-reserve-mib`も受理されない旧binaryでは「確保済み」と出さない。`--expert-vram`は等価なreserve flagではないため単純置換しない。

**検証予定:** `node --test apps/host/tests/q36-run-contract.test.mjs apps/host/tests/q36-capabilities.test.mjs`、既存native-settings/resource/launch回帰。

**受入:** 同じcontractからvalidation・UI説明・argv・bench identityが生成される。Cのactual pathは起動後のnative観測とも一致。既存モデルを止めた後に「実は非対応」と判明しない。

**commit案:** `fix(q36): bind model identity and reject unsupported runtime settings`

## T02 / PR-2: 266秒と306秒の内部を見えるようにする

**変更:** `q36_engine.cu`, `startup_trace.hpp`（新規候補）、`serve/q36_startup_events.py`, `serve/server.py`, `run-observation.mjs`, `native-monitor.ts`。  
**Test:** `tests/qwen36/test_startup_events.py`, `apps/host/tests/q36-progress.test.mjs`。

**入力:** run/generation ID。  
**出力:** §3.2のevent stream、stage別wall duration、計測欠損の理由。

- [ ] RED: stageの順序、部分行、旧形式stderr、unknown stage、異なるgeneration、engine error後のstale progress、timestamp欠損をfixture化。後続の進捗でerrorをloadingへ戻さない。
- [ ] `place_experts()`を、巨大pin試行／fallback malloc／zero-fill／source read+repack／H2D／slots+CPU pool初期化へ分割して計測する。**allocation成功と全pageのtouch完了を区別**する。
- [ ] warmupのfull-chunk、小GEMM、decode、speculative、resetを個別計測。通常のcounterとは別のwarmup counterを残す。実際のroute entriesと転送bytesを記録する。
- [ ] wall timeはsteady clock、CUDA durationはCUDA eventsで記録。異なるprocessのmonotonic値を直引きしない。必要な同期は診断armのみとし、通常armへ全kernel同期を混入しない。
- [ ] 1秒程度ごとの低頻度resource samplingで、process private/working set、system available/commit、専用/共有VRAM、取得可能ならhard faultsとdisk readを取得。取得不可はnull。process I/O bytesを物理disk readそのものと呼ばない。
- [ ] `Saving the model's settings` / `still starting`を実stageで更新。engine-readyとHTTP-readyとGUI-readyを区別し、計測されていない残り秒数を捏造しない。

**検証予定:** `python -m unittest discover -s tests/qwen36 -p 'test_startup_events.py' -v`、`node --test apps/host/tests/q36-progress.test.mjs`。計測ON/OFFのpaired runでoverheadも記録。

**受入:** 「expert_host_alloc 失敗」「warmup_prefill 実行中」「HTTP-ready待ち」が区別できる。sourceに処理があるだけで段階を完了扱いしない。

**commit案:** `feat(q36): expose stage-bound startup and memory telemetry`

## T03 / PR-3: 二重起動・停止期限・メモリ不足の再試行を正す

**変更:** `native-control.mjs`, `control-runtime.mjs`, `strata_control/runtime.py`, `serve/server.py`, Qwen36起動制御。  
**Test:** `apps/host/tests/q36-load-lifecycle.test.mjs`, `tests/qwen36/test_admission.py`, `test_stop_generation.py`。

**入力:** validated contract、process ownership、T02観測。  
**出力:** admission decisionとgeneration-bound state machine。

状態遷移:

```text
validating → stopping_previous → preflight → loading → warming → ready
      └error       └stop_failed     └rejected   └failed / cancelling → cancelled
```

- [ ] RED: load連打、load/cancel/load競合、同一モデルへの同時要求、古いready通知、PID再利用、他アプリの同名serverを用意。一つのgenerationにつき一つの所有engineしかspawnしないことをassert。
- [ ] pre-stop validationとpost-stop resource recheckを分ける。非対応model/flagは現在のengineを止める前に拒否。新allocation直前には実空き容量を再取得する。
- [ ] memory admissionは§4のbyte-basedモデルを使う。legacyの18.75GiB arena要求がsystem commit余裕を超える場合はspawn前に説明。不明なworkspaceを0にしてfits=trueにしない。mapped storeでは全file bytesをprivate commitに足さず、window/cache/pin/scratchを別計算。
- [ ] 正常停止の期限超過と所有processの停止確認を別結果にする。timeout後に本当にjob tree・port・runtime claimが解放済みなら `stopped_with_escalation` として次段階を許可できる。未確認なら停止し、エラーを単純に握りつぶさない。
- [ ] 起動中は現行stdin readerがまだ始まっていない可能性がある。新cancel経路は単一reader/単一authorityで設計し、readerを二重化しない。repack chunk・転送境界・warmup probe間にcancel点を置く。CUDA kernelの即時安全preemptは保証せず、最後は所有jobだけを期限付きで回収。
- [ ] 同一configDigestの自動再試行を禁止。容量不足はcontextや精度を無断変更せず失敗理由を返す。unsupported RAM-budgetを変えただけのretryをmutation testで検出する。

**検証予定:** 上記Node/Python unit + Windows owned-child integration。最初は少量メモリのfake engineで行い、最後に実Qwen36のcancel/reloadを1系列ずつ実施。

**受入:** stop_failedの状態で新loadを開始しない。terminated jobだけを再利用し、旧PID文字列の使い回しをしない。強制終了しても元モデル・記憶DB・設定が破損しない。

**commit案:** `fix(q36): gate loading on memory admission and verified stop completion`

## T04 / PR-4: warmupを小さくする前に、費用の移動を検出する

**変更:** `q36_engine.cu::warmup`, capability表、native settings。  
**Test:** `tests/qwen35/q36_warmup_contract_test.cpp`, `tests/qwen36/test_warmup_benchmark.py`。

**入力:** T02のphase timings、T01のcontract。  
**出力:** capability-gated warmup policy（新規案 `--q36-warmup-mode legacy|bounded`、`--q36-warmup-token-limit N`）。既存 `--no-warmup` はdiagnostic armだけに残す。

- [ ] RED: warmup後のGDN/conv state、pos、session token history、MTP proposal state、RNG・resident slot tableが規定のfresh状態と一致するfixture。ctx=256やchunk>=ctxでも範囲外にならない。
- [ ] legacyの2048 full-chunk、9-token GEMM probe、decode、speculativeを個別に測る。streaming分岐に入る最小長と実転送量も記録する。
- [ ] bounded候補は9/32/128/512 tokensを別armで比較。CPU-hybrid閾値128を越えるprobeがないarmでは、streamingをwarm済みと報告しない。probeを短くしても全layer expertがstreamされれば転送費用は減らないことを評価に入れる。
- [ ] **READY後へ未実施probeを勝手に裏回ししない。** 必要kernelの初回遅延を `first_request_compile/transfer/compute` として測る。persistent metadataだけでCUDA contextが温まっていると見なさない。
- [ ] legacy、bounded、no-warmupを、同一context・重み・MTPで比較する。採否は `load_request→first_useful_token`、first full response、2回目TTFTで判断し、ready秒数だけの比較を禁止する。
- [ ] 5組以上のpaired runと同一route/slot条件のlogit/token parity。新policyでstate汚染、初回品質低下、長文prefillの大幅悪化があればlegacyへ戻す。

**受入:** 待ちの初回リクエストへの移動でない実改善を示す。改善しなければ計測だけ採用し、policyは既定化しない。

**commit案:** `perf(q36): add measured bounded warmup policy without false readiness`

## T05 / PR-5: 再packを繰り返さないread-only ExpertStore

**変更:** `expert_store.hpp/.cpp`（§2の新規候補）、`q36_engine.cu::expert_blob/place_experts`、`CMakeLists.txt`。  
**Test:** `tests/qwen35/q36_expert_store_test.cpp`, `q36_transfer_lifetime_test.cpp`。  
**入力:** verified GGUF handle・geometry・既存NativeExpertLayout。  
**出力:** §3.3のExpertStore、バイト同一のpack artifact、bounded staging。

### T05-A: まず保存形式とバイト一致を作る

- [ ] RED: Q4_K/Q6_K等のgate/up/down混在fixtureを既存 `expert_blob()` と比較し、全byte同一・stride alignment同一・padding/tailゼロをassertする。初期対象は実UD-Q4_K_XLに現れる形式全てであり、ファイル名がQ4だから全tensorが4bitとは仮定しない。
- [ ] `.q36epk`（新形式案）を `source SHA256 + layout version + geometry + quant types + endianness` に束縛。headerにlayer/expert index、offset、payload bytes、stride、tail、chunk checksumを記録する。ファイル名だけでcacheを選ばない。
- [ ] pack生成は上限付きchunkで行い、最大でも設定した作業bufferしか確保しない。原本→巨大host arena→packという全量二重コピーを作らない。初回生成費用・整合性検査費用・追加disk容量をcold-build時間へ必ず計上。
- [ ] 同じcache keyへの同時生成は一つに制限。`.partial`へ生成・flush・検証後にatomic publication。途中終了・checksum不一致・disk不足・index overflow・部分書込・未知versionは使用拒否し、元ファイルは変更しない。
- [ ] sourceのsize/mtime一致だけを同一性の証拠にしない。初回は全digestを検証し、使用中は同じhandleに束縛する。再利用ではsourceの改変を防ぐopen/ownership契約を確認できない場合に再検証する。安全な検証費用を隠さない。
- [ ] TDDで小fixtureをGREENにしてから実packを生成する。cache容量はモデルにより約expert payload規模が追加されるため、C/Hどちらにも勝手に作らず保存先・空きreserveを確認する。

### T05-B: 巨大匿名arenaを置き換える

- [ ] 新規案 `--q36-expert-store legacy|mapped-pack` をcapabilityへ追加。既定はlegacy。mapped-pack時はread-only file-backed viewから必要expertを取得し、全18.75GiBの `cudaHostAlloc` と `malloc` は実行しない。
- [ ] Windowsのmapping offset granularityとexpert payload alignmentを分け、aligned view＋offsetで扱う。CPU workerが読む間のviewをleaseで固定する。source mappingとpack mappingとown cacheを別に集計する。
- [ ] 最初のpinned host staging提案は2×32MiB、合計64MiB。16/64/256MiBの候補を独立比較する。これは**host pin pool**であり、旧GPU staging 1.10GiBとは別物。pin失敗時は上限を縮めて再判定し、pageable同期転送へ戻す場合は明示する。
- [ ] DMAは `HOST_FILLING→H2D_IN_FLIGHT→REUSABLE`、device slotは `COPYING→READY→COMPUTING→REUSABLE` の二つの寿命で管理。CPU leaseはCPU job完了まで、host stageはcopy eventまで、device stageはcompute eventまで再利用禁止。
- [ ] 旧 `L.hblobs` の全量生pointer前提を、CPU read、initial GPU upload、slot replacement、prefill streamの全call siteで監査する。一箇所だけmapped pointerへ差し替えない。半端なstageで取消されてもRAIIで所有資源を回収する。
- [ ] cache corruption時のfallbackはadmissionを再通過。旧arenaが収まらないのに自動で全量allocationへ戻さない。in-flight転送に使うfile/viewをcache cleanupで削除しない。

**検証予定:** 新CTest `q36_expert_store`, `q36_transfer_lifetime`。Windows file locking/junction/atomic replace、CPU reference、Compute Sanitizerを別実行。構造テストで「mapped-pack時に全payloadサイズの匿名arena allocationが0回」をassertする。

**受入:** repack bytesが旧実装と同一。新modeは全量匿名arenaなし。pinnedと独自cacheの予算超過なし。file-backed working set増加、OS page cache、hard faultsも含めて実機報告。private commitが減っただけで推論も速いとは言わない。

**commit案:** `feat(q36): add byte-exact mapped expert store with bounded pinned staging`

## T06 / PR-6: 転送とexpert配置を測定値で最適化

**変更:** `q36_engine.cu` の `stream_kick`, `moe_hybrid_gpu`, `moe_hybrid_cpu`, `rebalance`等（実装前に名前・全call siteを再検索）、T05 store、benchmark。  
**Test:** `tests/qwen35/q36_stage_scheduler_test.cpp`, `q36_residency_test.cpp`。  
**入力:** ExpertStore、実route ID、実測CPU/GPUコスト、同一memory budget。  
**出力:** streaming strategyとresident slot policy。routingのtop-kとweight自体は変えない。

- [ ] RED: CPU/GPUに分けた各route entryがちょうど一度だけ処理され、欠落・重複がないことをassert。空route、全hit、全miss、重複expert、ragged token数、MTP追加layerを含める。
- [ ] 現行のCPU-hybrid小batchとGPU-stream大chunkを分けて計測。routing件数、distinct experts、CPU queue待ち、H2D bytes、copy wait、GPU compute、promotion/demotion数を分離する。
- [ ] 最初は**同じslot table・同じ演算経路**のままT05のbufferとeventを使い、メモリ所有権の変更を数値変更から切り離す。
- [ ] 次に、全layer転送と選択expertだけのgather転送を比較する。選択集合が小さい場合だけcompact indexを作り、元route entryへの逆対応を保持。index取得のD2H同期とgather費用を隠さない。条件は§5.2。
- [ ] dynamic residencyは既存rebalanceを最小拡張する。単なる人気順より「CPU時間の節約−転送費用」をbyte当たりで評価。hysteresis、移動bytes上限、eviction lease、最小滞在期間を設ける。**未選択expertを計算から削らない**。
- [ ] cache更新でCPU/GPU担当が変わると丸めが変わり得るため、fixed-slot parityとdynamic-slot qualityを別gateにする。private session由来のrouting profileを勝手に永続化・公開しない。

**受入:** same-routeの処理重複/欠落0、race0。paired E2Eでcopy waitかCPU待ちが減り、token latencyが改善する。全layer方式が速いshapeでは元dispatchを選ぶ。

**commit案:** `perf(q36): schedule expert transfers by observed reuse and compute cost`

## T07 / PR-7: Qwen36専用CUDA kernelをhotspotごとに改善

**変更:** 最初は `q36_engine.cu` / `q36_kernels.cuh` 内だけ。shared `native_moe` / `native_mmvq`へ変更する場合は別PRへ分割。  
**Test:** `tests/qwen35/q36_kernel_parity_test.cu`、既存`STRATA_Q36_VERIFY`、既存q36 correctness gate。  
**入力:** T02/T06で得たkernel shape・時間・resource使用。  
**出力:** shape/device/quantを条件にしたopt-in dispatchと旧kernel fallback。

候補を全て一度に実装しない。原則は直近プロファイルのcritical path上で最大の候補を一つ選ぶ。

| 候補 | 適用条件 | 最初の実装 | 不変条件 |
|---|---|---|---|
| Expert MMVQ / grouped小batch | decodeのGPU演算が律速 | coalesced読込、vector load、量子化復元＋積和融合、shape別block幅 | Q4_K/Q6_K等のscale/min/offset、route順、FP32 accumulation |
| Expert MMQ大chunk | prefillの計算が律速 | expert別gather/grouping再利用、gate/upの既存融合を維持しlayout/tilesを調整 | FP16全面展開をグローバルへ追加しない、scratch上限 |
| GDN `k_gdn_seq_cols` | GDNのGPU時間が大きい | column group・row group・register/shared量の限定autotune | recurrence順、state128、mask/reset、MTP verify/commitの意味 |
| GDN `k_gdn_seq` | decode/verifyで律速 | coalescingとregister pressureを測定しtile候補を比較 | FMA/reduction順を変更した場合はbitwiseを偽装しない |
| Attention | 長contextでscore/KV読込が律速 | 既存split-K/mergeの最適化。tiled online softmaxは別候補 | causal/GQA/RoPE/state同一、長文品質 |

- [ ] RED: GPU referenceとの差分試験を先に作る。token数1,2,7,8,9,127,128,129,511,512,513,2048、実モデルにあるquant/geometry、部分tile、zero input、NaN処理契約、maskを含める。
- [ ] Nsight Systemsでcritical pathを確認し、権限がある場合のみNsight Computeで帯域・occupancy・register spill・warp stallを調べる。権限不足はCUDA events/host timingで代替し、hardware counter未取得と記録。driver権限を無断変更しない。
- [ ] CUDA 13.3/sm_120等の実配布bindingを保つ。B200用sm_100a命令や未確認のarchitecture-specific FP4 MMAを流用しない。Q4_K/PQ2_0とNVFP4は異なる形式であり、4bitという理由で互換扱いしない。
- [ ] 旧kernelをreference/fallbackとして残し、`STRATA_Q36_VERIFY=1`相当の比較を通す。bitwiseを保つ変更は全比較一致。演算順を変える変更は別numerical armで、既存許容誤差を拡げず品質を比較する。
- [ ] `compute-sanitizer --tool memcheck` と `racecheck`、必要に応じ `synccheck`。PTXAS register/local/stack量は既存guardに照合し、数値が悪化した時は理由と実速度をレビューする。budgetファイルを自動的に緩めて通さない。
- [ ] microbenchmark→native生成→HTTP→GUIの順で比較する。kernelだけ速くてcritical pathやp95 token gapが改善しなければ既定化しない。

**受入:** 既定経路を変更しない状態でfallback可能。対象shapeの同日paired計測、モデル品質、long-context・cancel regressionが揃う。Flash-Next向けGDN実験をQwen36の速度証拠へ転用しない。

**commit案:** `perf(q36): optimize <measured-hotspot> on sm120 behind validated dispatch`

## T08 / 任意PR: FP16 KV等の容量削減を別armで研究

**必須順序に含めない。** T00–T07の精度不変改善と混ぜない。

**変更候補:** `q36_engine.cu` のKV allocation、write、prefill/decode read、session copy、graph binding、MTP state。  
**Test:** `tests/qwen35/q36_kv_storage_test.cu`、長文参照比較。

- [ ] FP32 referenceを保持し、新規案 `--q36-kv-storage fp32|fp16` をdigest-bound能力として定義する。単にllama-serverの `--cache-type-*` を通す変更ではない。
- [ ] RED: K/V位置、causal、GQA、RoPE、slot reuse、session handoff、prefix、MTP rollback、context終端の一致契約を作る。
- [ ] 64Kのpersistent KVは理論2.75→1.375GiB、128Kは5.5→2.75GiB。これはその領域だけの数値で、既存FP16 scratchやrecurrent state等は別途計上。
- [ ] FP32 accumulationを維持し、必要tileだけ復元する。FP16 KV→full FP32 temporaryを毎回作って節約を消さない。
- [ ] 保存精度変更のため、固定teacher-forced logits、perplexity/タスク、長文回収、日本語、tool JSONを別に評価。旧FP32と完全同一だとは宣伝しない。
- [ ] 品質gate未定義または未合格ならfeatureはexperimental/offのまま。本線の「同品質で速くなった」に含めない。

**commit案:** `feat(q36): add opt-in fp16 kv storage with independent quality gates`

## T09 / PR-8: GUI・配布・実機E2Eを閉じる

**変更:** NativeModels/NativeLocalModel/monitor、能力manifest、現行packaging手順、release qualification文書。  
**入力:** 各PRの検証結果とrollback manifest。  
**出力:** 実際に検証されたcomponentだけを選べるGUI、readiness・配布digestが一致した認定記録。

- [ ] RED: GPU全体実測とモデル予測を別ラベルにする。`fits`は未知分があればunknown、private commitやpage-backed量を区別し、「RAM 11.6GBだから収まる」をQwen36へ誤用しない。
- [ ] model panelに選択GGUF・resolved drive/volume・backend・actual context/KV・slot数・host modeを出す。raw pathはローカルUIだけ。ログ・公開resultへ秘密をコピーしない。
- [ ] loaded / loading / warming / readyを分ける。error codeを平文説明へ変換し、stop escalation完了とstop failureを分けて表示。取消中にload buttonを有効化しない。
- [ ] source/EXE/strata_kq.dll/追加DLL/Control/Host/capabilityのdigestを一組で固定。旧binaryに新argsを送る組合せを拒否する。signed engine feed/componentの検証を迂回しない。
- [ ] 新engineだけ差し替えたscratch componentで起動・chat・stop・restart・rollbackを確認。既存インストールのliveファイルは直接上書きしない。署名手段や承認がない場合はpackageをlocal candidateとして止める。
- [ ] §7の全gateを実施し、PASSED / FAILED / SKIPPED / NOT_RUNを別記録。GitHub Actionsが無効ならremote CIはNOT_RUNであり、ローカルpassをremote passへ置き換えない。

**受入:** インストールした実物のbinary identityとベンチしたidentityが同じ。元のHakua memory/Prism/TurboQuant/普通のchatを壊さず、切り戻し後に元componentを再選択できる。

**commit案:** `feat(gui): qualify q36 startup telemetry and memory-aware runtime selection`

---

## 4. メモリ予算を数式とbyteで決める

### 4.1 GPU側

予算は公称16GBからではなく、同時刻の実測専用VRAMから計算する。

\[
V_{engine}=W_{dense}+W_{expert,G}+KV(C,S)+R_{state}+A_{workspace}+B_{stage,G}+G_{graph}+V_{other}
\]

\[
\Delta V_{additional}\le V_{free,dedicated}-V_{reserve}-V_{uncertainty}
\]

現在すでにengineが持っているallocationは増分だけ計上し、二重控除を避ける。shared GPU memoryは足さない。`cudaMemGetInfo`、Windows budget、他process使用の差があれば観測元付きで残す。

ログと現行Qwen36構造でのMTP込みpersistent KV:

\[
KV(C,S)=C\,S\,(10+1)\,2\,256\,(4+4)=45,056\,C\,S\quad\text{bytes}.
\]

| capacity / one sequence | FP32 persistent K+V |
|---:|---:|
| 16,384 | 0.6875GiB |
| 32,768 | 1.375GiB |
| 65,536 | 2.75GiB |
| 131,072 | 5.5GiB |

実装ではmetadataと実layer mapで算出し、11を全model共通定数にしない。scratch用FP16 K/V、recurrent state、MTP hidden、padding、parallel分を別に計上する。

現行Qwen36の内部reserveは768MiBであり、GUIの1536MiB指定が旧parserで無視される点に注意。**新たに1536MiBを実効化する安全変更は、baselineとの差分として明示する**。そのぶんexpert slotsが減る可能性があり、性能改善と一括比較しない。reserve=0への自動変更は禁止。

### 4.2 Host側

legacy:

\[
H_{private}=W_{all\ experts}+H_{workspace}+H_{pin,other}+H_{runtime},
\quad W_{all\ experts}\simeq18.75\,GiB.
\]

mapped-pack提案:

\[
H_{private,new}\lesssim H_{owned\ cache}+H_{pinned\ stage}+H_{workspace}+H_{runtime}.
\]

ただし実RAM圧力はこれにfile-backed working setとOS cacheが加わる。`mapped_bytes`はvirtual range、`resident_bytes`はphysical residency、`committed_bytes`はprivate backingを要する量として区別する。

admissionでは少なくとも以下を比較する。

```text
commit_headroom >= projected_incremental_commit + uncertainty
available_physical >= projected_required_resident_increment + physical_reserve
free_dedicated_vram >= projected_gpu_increment + gpu_reserve + uncertainty
free_cache_disk >= pack_build_peak_disk + existing_storage_reserve
```

初期physical reserve提案は通常4GiB、work profileはmax(4GiB, RAMの20%)。これは新policyであり既存値の事実ではない。mmapの全resident上限はOS任せなので、独自cache budgetだけでRAMを完全制限したとは言わない。計測が不明なら「不明」とし、ユーザーへの説明なく楽観的にloadを繰り返さない。

### 4.3 予算fixture

- Qwen36 65,536 / 1 seq / FP32 K,V → 2,952,790,016 bytes。
- 同条件 / 2 seq → 5,905,580,032 bytes。
- 131,072 / 1 seq / FP32 → 5,905,580,032 bytes。
- Hikariのlayer mapを与えてQwen36固定式を適用しない。
- negative/NaN/overflow、geometry欠損、unsupported precisionはvalidation error。
- 18.75GiB要求にcommit余裕11.89GiBのlegacy planは不足。過去の51.99/63.87GiBは現在の観測と混ぜない。

## 5. 数理・アルゴリズム上の選択基準

### 5.1 読込・計算・転送を分ける

stageの下限モデル:

\[
T_{stage}\gtrsim\max\{D_{disk}/B_{disk,eff},\ D_{H2D}/B_{link,eff},\ F/P_{compute,eff}\}
\]

これは完全なoverlapを仮定した下限であり、実際には依存・CPU repack・page fault・queue待ちが加算される。GPUのpeak FLOPSやVRAM帯域だけから266秒／306秒を説明しない。H→Cの変更も、同じファイル・同じcache状態・同じ実効設定で測る。

cold pack生成、既存pack起動、OS file-cache cold/warm、CUDA context cold/warm、同一engineでの会話再利用は別の測定群。再起動しただけでdisk-coldとは呼ばない。

### 5.2 選択expert転送の採否

あるlayer/chunkで必要なexpert集合を \(U\)、全expert集合を \(E\) とする。

\[
D_{full}=\sum_{e\in E}b_e,\quad D_{selected}=\sum_{e\in U}b_e.
\]

選択転送を採る条件は、概念的に

\[
(D_{full}-D_{selected})/B_{link,eff}
> T_{index}+T_{gather}+T_{extra\ sync}+T_{cache\ lookup}.
\]

routeがほぼ全expertへ分散するchunkではfull-layer転送が有利かもしれない。全shapeで選択転送を強制しない。route indexの並べ替えと出力scatterは元のtoken/expert/weight対応を保存する。

### 5.3 CPU/GPU配置

expertごとの使用見込み \(q_e\)、CPU/GPU計算費用 \(t_{c,e},t_{g,e}\)、昇格費用 \(t_{p,e}\) を観測する。

\[
\max_{z_e\in\{0,1\}}\sum_e z_e\{q_e(t_{c,e}-t_{g,e})-\rho_e t_{p,e}\}
\quad\mathrm{s.t.}\quad\sum_e z_e b_e\le B_{expert,G}.
\]

\(\rho_e\)は評価窓内の入替頻度。最初はbyte当たり利益のgreedy＋hysteresisで十分。巨大solverや学習routerを追加しない。CPU/GPU枝が重なる場合、削減できるのはcritical path側の費用であり、両枝の時間を単純に足してspeedupを予測しない。

41/256から計算できるのはresident capacity比のみ。実hit rateは `gpu_route_entries/(gpu_route_entries+cpu_route_entries)` を実測し、別途GPU-stream prefillのroute/bytesも数える。

### 5.4 GDN kernel

sourceのstateを \(S\)（key方向が行、value方向が列）とすると、概念的な更新は

\[
\delta_t=\beta_t(v_t-g_t S_{t-1}^{\top}k_t),\quad
S_t=g_t S_{t-1}+k_t\delta_t^{\top},\quad
u_t=S_t^{\top}q_t/\sqrt d.
\]

その後にRMSNormとSiLU gateがある。各value列の独立性を使うcolumn tilingは候補だが、同じ列内のreduction/FMA順、state更新順、verify時にstateを書かない契約を保つ。形式的にaffine scanへ変形できることだけでは高速化にならず、中間行列・演算量・丸め誤差が増える方式は本線へ入れない。

### 5.5 改善率の上限

対象kernel群がend-to-end時間の割合 \(f\) を占め、そこだけ \(s\) 倍になったとき、理想的にも

\[
Speedup\le\frac{1}{(1-f)+f/s}.
\]

\(f\)はprofileから取る。expertの全量配置時間が残ったまま、小kernelの倍率だけで「起動10倍」を主張しない。

## 6. TDD・mutation・回帰の必須マトリクス

各taskは「REDを実行して適切な理由で失敗→最小実装→GREEN→該当回帰→小commit」。既存テストの削除、assertionの弱体化、timeoutの無条件拡大は修正とみなさない。

| Gate | 必須内容 | 検出すべきmutation |
|---|---|---|
| Path identity | exact model、same file via junction、hash違い、入替競合 | basenameだけで一致させる／Hへ黙ってfallback |
| Capability | context/KV/private cache/Spin8/新flagのdigest binding | unsupportedをsuccess扱い／private guard削除 |
| Admission | commit/physical/GPU/diskの別budget、unknown | shared VRAMを足す／reserveを0にする／unknownを0にする |
| Lifecycle | cancellation、generation、owned tree、ready順序 | stale ready受理／PID単独kill／stop failure後spawn |
| Store | bit-exact pack、padding、checksum、atomic publish | tail未初期化／up/down offset変更／partial利用 |
| Transfer | host/device slotとCPU leaseの寿命 | copy/compute event wait除去／CPU join前unmap |
| Warmup | fresh state、ctx端、first responseまでの費用 | reset省略／READY前倒しを速度合格扱い |
| CUDA | shape境界、既存tolerance、partial tile、MTP | mask削除／off-by-one／scale/min誤り／reduction順誤り |
| Privacy | principal/session/model/policy境界、consent | 異なるsessionのKV再利用／routing履歴の無断保存 |
| Report | same identity、aborted、NOT_RUN、capacity vs actual input | failed run除外／短文で128K合格／microbenchをE2Eへ転用 |

mutationは本番へ入れない。イベントrace等の非決定的問題はdeterministic fake event schedulerでも検査し、実CUDA試験を置き換えない。survived mutantは理由付きレビューし、都合の悪いmutationを集計から削除しない。

### 実行コマンドの扱い

以下は**実装後に実行する予定**であり、本書作成時に成功した記録ではない。

```powershell
# Node/Python: リポジトリ指定のprivate環境・scratch HOMEを使用する
node --version
npm --prefix apps/host test
npm --prefix apps/host run typecheck
npm --prefix apps/host run build
python -m unittest discover -s tests/qwen36 -p 'test_*.py' -v

# GPU build: 現行の正式Windows sm_120 configure手順/presetを優先する
# 同じCUDA、MSVC runtime、strata_kq依存、署名対象を維持して別build directoryへ生成
cmake --build build/q36-32gb16gb --config Release --parallel 2
ctest --test-dir build/q36-32gb16gb -C Release --output-on-failure

# 既存model gateは実際のhelpから必要引数を取得し、実行した完全argvをreceiptへ保存
python tools/qwen35/q36_solo_gate.py --help
python tools/qwen35/q36_cmp_gate.py --help
python tools/qwen35/q36_proto_edge.py --help

# 新規runnerの提案interface（T09までに実装）
python tools/qwen35/q36_startup_bench.py --manifest bench/q36-32gb16gb/workload.json --arm baseline --output bench/q36-32gb16gb/results/baseline.jsonl
```

`build/q36-32gb16gb`は作業用の新規build directory。configure未完了の場所へ上記buildを投げない。`--help`を取得しただけではgate合格ではない。新CTestはCMake登録を必須とし、0件実行をPASSとしない。

## 7. 実機ベンチマークと合格条件

### 7.1 比較arm

| Arm | 変更点 | 固定点・目的 |
|---|---|---|
| A0 | 現行実装、観測のみ | 64K、MTP2、FP32 KV、実効chunk2048、同一モデル |
| A1 | 正しいfile identity / capability | 実際の選択先と起動先一致。H/Cの物理driveは解決してから比較 |
| A2 | bounded warmup | A1の他条件固定。readyとfirst tokenを両方測る |
| A3-cold | mapped pack初回生成＋起動 | source hash確認・cache生成・disk費用を含む |
| A3-warm | 検証済みmapped pack再起動 | OS cache状態を明示。初回生成との平均にしない |
| A4 | 同slot tableで小容量pin / transfer | backing・コピーの効果を演算変更から分離 |
| A5 | 選択expert転送／配置policy | 実route hit、bytes、数値差を独立評価 |
| A6 | 一つのCUDA hotspot最適化 | 同shape・同slot・同backendでpaired比較 |
| X1 | chunk512/1024 | 2048からの設定変更として明記。長文速度も測る |
| X2 | context32K/16K、MTP0 | 診断用。64K同条件の成果へ混ぜない |
| X3 | FP16 KV | 品質変更arm、独立認定 |

各armでcold/warm区別と順序を記録し、A→B→B→A等で偏りを減らす。重いモデルを同時loadして比較しない。profile有効runと通常timing runを混ぜない。

### 7.2 Workload

最初はsyntheticな短文で機能確認し、次に2K、8K、32K、64K近傍の実入力へ進む。64K近傍はtokenizerで実token数を数え、system/templateと生成余白512以上を容量から引く。capacity=65,536で短文を投げただけでは64K実入力合格にしない。

生成は原則256 tokens以上を計測。EOSが早ければactual生成数を保存。greedy correctness、seed固定sampling、2回目会話、cancel、再ロードを分ける。機密のHakua記憶や実ユーザー会話ではなく合成promptを使う。

### 7.3 保存する指標

- identity: source commit、EXE/DLL/manifest digest、model/tokenizer digest、geometry、hardware、driver/toolkit、requested/effective設定。
- load: request時刻、spawn、dense、buffers、host_alloc、repack、upload、warmup各probe、engine/API/GUI-ready、first useful token、first response complete。
- memory: allocated dedicated VRAM、Windows shared GPU memory、private commit、working set、system commit headroom、available physical、map size/active windows、owned cache、pin pool、disk cache peak。
- inference: new/cached prefill tokens、prefill tok/s、decode tok/s、inter-token gaps、route hit、CPU/GPU時間、H2D bytes、copy wait、swap counts、実行したkernel/shape。
- outcomes: success/aborted/cancelled/timeout/OOM、quality、parity、temperature、background load、取得不可の理由。

`first_useful_token`はrole eventや空chunkでなく、非空text deltaの到着。server `READY`は代用不可。各runに少なくともelapsed_msとmonotonic durationを保存し、複数process間のwall clock差に注意する。

### 7.4 採否

| 項目 | 必須条件 |
|---|---|
| 正確性 | 元model/quant/context維持、stage/identity一致、normal/private経路を混同しない |
| 完了性 | clean環境で5回中5回のload→生成→stopが完了。途中取消は別試験 |
| メモリ | mapped-storeで全expert匿名arenaを新設しない。pin/own cacheがbudget内。system pressureを別報告 |
| 性能目標（提案） | 同条件paired中央値でload request→first useful tokenを30%以上短縮 |
| 回帰guard（提案） | steady decode中央値を5%超悪化させない。差の不確実性が大きければ追加計測・非採用 |
| 品質 | I/O/packのみ変更はbyte/token parity。同slot kernelは既存許容値。配置・精度変更は独立評価 |
| 停止 | 正常cancelとescalationが区別され、owned process/claim解放を確認。第三者processへの影響0 |
| 報告 | 全run・失敗・ばらつきを保持。少数起動sampleのP95を安定推定として扱わない |

目標30%は将来の採否基準であって、601.2秒からの達成予測ではない。各段階で改善が再現しなければ研究経路をoffのまま残すか差分を戻す。正確性修正だけでも独立成果として記録する。

## 8. リスク・ロールバック

| リスク | 検出 | 対応 |
|---|---|---|
| mapped packでdisk fault増加 | hard faults、disk待ち、token gap | resident cache/window/pinを再配分。元modeへ戻す前にadmission |
| 小stageで転送回数増加 | H2D call count、transfer bytes、wall | coalesce、batch stage調整。全量pinには戻さない |
| dynamic cacheの丸め差 | fixed-slot比較、teacher-forced logits | policyをoff。重みやroutingを改変して帳尻を合わせない |
| warmup費用の先送り | first-request TTFT | bounded policy不採用。readyだけを成功指標にしない |
| cache改ざん/部分書込 | header/chunk checksum、file identity | artifactを隔離、使用拒否。元GGUFとpersonal dataを保持 |
| 新flagと旧component不整合 | capability digest mismatch | 起動前拒否・元component選択 |
| GPU/CPU競合 | sampleとprocess ownership | 現存状態を説明。外部processを自動killしない |

rollbackはtask単位のcommitとfeature flagで行う。schema追加は後方互換、旧設定のbackup、元component pinを保持。cacheを消すときもactive leaseがないartifactだけを対象とし、モデルrootを再帰削除しない。

## 9. 実装者への最終チェックリスト

- [ ] 最新mainとの差分と既存PRを確認し、二重実装・競合を避けた。
- [ ] 旧main・配布component・モデルの実SHAが記録された。
- [ ] C/Hの論理pathとphysical volumeを混同していない。
- [ ] 64K/同一precisionの本線と設定変更armが分離されている。
- [ ] unsupported flagの黙認と無効なmemory retryを止めた。
- [ ] private-cache制約を削除して起動成功にしていない。
- [ ] 起動timeをdense/alloc/repack/upload/warmup/readyへ分解できる。
- [ ] 同一generation二重spawn、stale ready、owned stop漏れがない。
- [ ] mmap済みGGUFからの全expert匿名copyを、新modeでは作らない。
- [ ] ExpertStoreのbytes、alignment、tail、lease、DMA lifetimeを試験した。
- [ ] CPU/GPU slot容量比を仕事量と偽っていない。
- [ ] CUDA最適化のmicro結果とE2Eを分け、Windows実機で比較した。
- [ ] `READY`の早期化だけでなく最初の有用応答が改善した。
- [ ] 新署名componentとテスト対象binaryが一致する。
- [ ] NOT_RUNを残し、merge/release判断を証跡付きで別に行う。

## 10. Cursor / Codexへ渡す指示

> この計画とDESIGN.mdを読み、zapabob/Strataの現main・AGENTS.md・CONTRIBUTING.md・既存PRを確認してbaseを凍結する。既存dirty treeをresetせず、隔離worktreeでT00から順番にTDDで進める。主対象はQwen3.6-35B-A3B UD-Q4_K_XL / Windows / RTX5060Ti16GB / RAM32GB。context65536、同じ重み・tokenizer・FP32 KV・MTP2を本線で維持する。実効prefill2048のbaselineを固定し、ログの28.6s/266.0s/306.6sは単発の歴史的観測として扱う。最初にpath/能力/起動stage/停止所有権を直し、その後で既存mapped GGUFから追加生成する全expert host arenaを、byte-exactなmapped packとbounded pinned stagingで置換する。warmupは初回応答への費用移動を防ぎ、CUDAは実測critical pathのQwen36経路に限定する。明示unsupported設定は拒否し、private-cache制約を除去して起動させない。他serverを無断停止しない。CUDA build、CPU fixture、GPU parity、Windows実モデル、API/GUI、配布署名を別に検証し、未実行はNOT_RUN。各taskは独立commit/PRでrollback可能にし、mainへの直接push/merge/releaseやインストール済みcomponentの直接上書きをしない。

## 11. 根拠と参照

### A. ユーザー提供資料

- `貼り付けたテキスト（1）(1).txt` と `(2).txt`。同じ85行、17,159 bytes、SHA-256 `8953c82d982a50f6d546c551f9bff3edb2bcb40fb8fc4f525cc79a5d954a14cb`。
- 主要原本行: 42–49 VRAM不足、58–65 host失敗、66–69最初の配置完了、73–78完了timer、82–84最終の未完了抜粋。
- 会話中のWindows memory/process出力とGUI画像。現在値ではなく時点観測として使用。原本に個人pathがあるため同梱JSONは最小化した集計だけ。

### B. 読取基準source

以下のURLは全て今回の公開main基準。配布binaryとの一致は別途T00で検証する。

- https://github.com/zapabob/Strata/tree/170e0d330edd9c03b5dcddfc64b77e498387ff86
- https://github.com/zapabob/Strata/blob/170e0d330edd9c03b5dcddfc64b77e498387ff86/AGENTS.md
- https://github.com/zapabob/Strata/blob/170e0d330edd9c03b5dcddfc64b77e498387ff86/CONTRIBUTING.md
- https://github.com/zapabob/Strata/blob/170e0d330edd9c03b5dcddfc64b77e498387ff86/src/qwen35/q36_engine.cu#L960-L1125
- https://github.com/zapabob/Strata/blob/170e0d330edd9c03b5dcddfc64b77e498387ff86/src/qwen35/q36_engine.cu#L2753-L3010
- https://github.com/zapabob/Strata/blob/170e0d330edd9c03b5dcddfc64b77e498387ff86/src/qwen35/q36_engine.cu#L3730-L3890
- https://github.com/zapabob/Strata/blob/170e0d330edd9c03b5dcddfc64b77e498387ff86/apps/host/server/native-resources.mjs
- https://github.com/zapabob/Strata/blob/170e0d330edd9c03b5dcddfc64b77e498387ff86/apps/host/src/lib/native-fit.ts
- https://github.com/zapabob/Strata/blob/170e0d330edd9c03b5dcddfc64b77e498387ff86/apps/host/src/components/NativeModels.tsx
- https://github.com/zapabob/Strata/blob/170e0d330edd9c03b5dcddfc64b77e498387ff86/apps/host/server/model-memory.mjs
- https://github.com/zapabob/Strata/blob/170e0d330edd9c03b5dcddfc64b77e498387ff86/docs/QWEN36.md
- https://github.com/zapabob/Strata/blob/170e0d330edd9c03b5dcddfc64b77e498387ff86/docs/HAKUA_RELEASE.md

### C. 設計を補助する外部一次資料（実測結果の代替ではない）

- NVIDIA CUDA Best Practices: pinned memory、transfer overlap、profile優先、memory hierarchy。大量pinは無条件の高速化ではない。  
  https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html
- Microsoft GetFinalPathNameByHandleW: openしたhandleからのfinal path解決。物理volume対応は別途確認。  
  https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfinalpathnamebyhandlew
- Microsoft Working Set: resident pagesと仮想mappingの区別。  
  https://learn.microsoft.com/en-us/windows/win32/memory/working-set

本書の方式比較、予算提案、30%/5%採否閾値、将来interface・flag・test名は設計提案であり、上記資料がそのまま実装済みと保証しているものではない。
