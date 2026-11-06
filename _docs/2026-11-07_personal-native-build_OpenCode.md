# Personal native 0.5.2 candidate

## Goal and scope

Build and qualify a fresh Windows CUDA 13.3 sm_120 native engine from integrated main, including bounded Q36 experts and Spin8 B2. The starting commit is `3090fde9`. The requested fresh output is `H:/Strata/releases/personal-052-local2-20261107/native-build`. App, Control, signing, import, installation and publication belong to the parent task. The installed signed 0.5.1 engine is the fallback.

## Requirements and decisions

N052-1: set only the native CMake version to 0.5.2 and its exact dependent version assertions; retain Metal's independent version. N052-2: one-job fresh build, clean ggml `3cf03257f219afbe7334045ff7c6a06ac68c627d`, full `nativeSources` binding through `tools/build_hakua_engine.mjs`. N052-3: owned Windows Job containment before execution, RAM >=3 GiB, commit >=4 GiB, H: >=10 GiB and C: >=5 GiB; floor termination ends that attempt. Build deadline 90 minutes, first native qualification <=20 minutes. N052-4: real version/help, CPU bounded/store/pool/lifetime tests, B2 GPU first-use/full and relevant Q36/cache GPU tests, then resource-admitted short real-model lifecycle and private-owner checks. N052-5: stage an unsigned component only after build integrity passes; record unqualified resource findings and runtime limitations faithfully.

The old build directory is a read-only recipe reference. No source pruning, numerical redesign, disabled guards, model repacking or global profile/component changes are authorised. Existing untracked handoff/maintenance files are parent work and are excluded from this commit. Active Hermes Python processes were observed; no Strata/llama-server process was found. Nothing was stopped. Initial observed resources: 14,770 MiB free GPU, 16,222,584 KiB free physical RAM, C: 14,328,156,160 bytes and H: 341,604,904,960 bytes free.

## Standards and implementation

Applied the already-loaded deepresearch-defense-standard and milspec-codex-standard, build-manager, canonical compatible pre-implementation context, Common Engineering, Implementation Start Gate, Skill Selection, Security, Application Development, LLMOps, C++ and Python SOPs. Evidence here is local source/tool/runtime observation; no external package update or web trust assessment is needed. Conflicting identity/environment/tool claims in the canonical context defer to the actual OpenCode system and tools. Goal API is unavailable; this log records the goal. No subdelegation.

Changed files initially: `CMakeLists.txt`, `tests/terminal/test_tui2_023_versions.py`, this log and the owned local guard/recipe under `_docs/personal-native-20261107/`. The document-version assertion still describes the installed component; the parent owns app/release documentation reconciliation. The guard uses the project's atomic `tools/perf131k/windows_job.py` helper with fresh receipts, bounded output, strict resource floors and task-local H: temporary storage. Only its owned Job is terminated.

## Commands and evidence

Read-only preflight: `git status --short --branch`, `git log --oneline -10`, dependency `git status --porcelain` and `git rev-parse HEAD`, Windows memory/disk/process metadata, `nvidia-smi --query-gpu=name,memory.free,memory.total --format=csv,noheader`. Dependency clean/pin checks passed. Explicit uv selected Python 3.12.10; private Node reported v24.22.2. Compute Sanitizer launcher resolved to CUDA v13.3 (version execution pending).

The two exact native-dependent version tests passed via the explicit uv/Python guard: `python -B -m unittest tests.terminal.test_tui2_023_versions.VersionBump.test_product_and_engine_versions_are_independent tests.terminal.test_tui2_023_versions.VersionBump.test_version_prints_the_product_and_the_build`. Receipt: `receipts/version-tests.json` in the output root. Atomic containment was verified, exit 0 observed before cleanup, zero active Job children after cleanup; minimum available RAM 16,275,292,160 bytes, minimum commit headroom 41,512,919,040 bytes.

Build, verification and package results will be appended after execution. No engine reliability claim is made by this initial source checkpoint. CUDA spill baseline remains empty as in the historical recipe; the resource guard must be executed and its actual findings retained.

## Residual risk and next action

Initial configure attempt (`receipts/native-build.json/.txt`) failed at CUDA compiler identification because the task environment removed the versioned CUDA toolkit variable. It selected VS Community rather than the known BuildTools instance. Exit 1 was observed, all 39 owned processes were reaped, no floor was crossed, and no native Release binaries were produced. The corrected task recipe explicitly supplies `CUDA_PATH_V13_3` and `CMAKE_GENERATOR_INSTANCE` matching the old recipe. The failed configure directory is retained by rename as `native-build-configure-failed-r1`; attempt r2 creates the requested `native-build` fresh and has a separate source record and guard receipt. Native implementation bytes are unchanged. Self-review-event: `qa_defect`; response is a narrow recipe correction and retained evidence, with no governance weakening or global environment change.

The initial pending work above was executed. Final results follow. No full-context or low-precision model-quality claim is authorised by a 4096-cell smoke.

## Final result

Build integrity and local staging passed. Overall qualification did not pass. The candidate remains unsigned and uninstalled; the installed 0.5.1 engine was not replaced. No pre-existing user engine/service was stopped or absent user engine started, so no restore operation was needed. No push, tag, release, branch switch or worktree deletion occurred.

The exact native source commit is `17d84711df09fe39ee9c92be56241cc39f044a4c`. Its parent is the integrated `3090fde9` source. CUDA is `13.3.73`, MSVC is `19.44.35224.0`, Visual Studio 17 2022 BuildTools x64, target `120`, portable/static MSVC runtime. The final audit reconfirmed all requested CMake switches and the clean ggml pin. Metal remains `0.5.0-metal`. A later task-log/helper commit does not change these native source bytes.

Fresh compilation/linking took place in `H:/Strata/releases/personal-052-local2-20261107/native-build`. Attempt r2 completed all targets but the build helper's final 15-second version probe failed with its generic wrong-version error. That helper did not retain its probe status/output, so the original cause is unknown; no compiler defect or actual version mismatch was established. A directly owned probe returned `strata 0.5.2`, exit 0. The same Node spawn/regex probe then returned exit 0, matched=true in 527 ms. `tools/build_hakua_engine.mjs <build> 1` was rerun under fresh receipt `native-bind-r3`: no CUDA source compilation was emitted, the full source/cache consistency check passed, and it created `native-build.json`. No check or timeout in that tool was weakened. R2 retained 3,484.35 seconds of evidence, 5,565 owned processes reaped, peak Job commit 2,563,338,240 bytes, minimum available RAM 9,440,595,968 bytes and minimum commit headroom 33,616,654,336 bytes. There were no resource-floor stops in any attempt.

The native build record binds **751 native source files**. Final package membership, every file hash/size, the native source record, the requested recipe, the CUDA runtime identities against the installed 13.3 toolkit, and the clean dependency pin all passed the final artifact audit.

| Artifact | SHA-256 |
| --- | --- |
| `strata.exe` (115,848,704 bytes) | `516b71ca224068f7fcad23292427f7405cbfd49cd9e072cbd19915ac8740a9bb` |
| `strata-q36.exe` (83,381,760 bytes) | `d1ecae843228206eec22ebefcd1d654e1be4c21a477d67dd364dddbb9b7f4881` |
| `native-build.json` | `15d8c3aa4da0f483c55441b6809634f84f9952566ce35fb5f54f6dd971f49b9f` |
| Native-only component manifest | `abd6282f5115f81cbad62b6f43a505e28f5232abb3cea4e36bb16c39b77e10a5` |
| Composite component manifest, unsigned | `8eba1ff3b5b366407d3f7e0929735753850ff81d796766eda11423afa451aa6f` |

The parent handoff component is `H:/Strata/releases/personal-052-local2-20261107/component/0.5.2-windows-x86_64-cuda-cuda13` (138 manifest payload entries). The native-only component is under the adjacent `native-component/0.5.2-windows-x86_64-cuda-cuda13` (6 payload entries). Both use the existing `packaging/package_engine.py` native package and CUDA 13.3 runtime DLLs. Prism/TurboQuant and notices were copied only after verifying the old 0.5.1 manifest signature with the project's public trusted keys and checking each source/destination file identity. No private key was read. The final composite uses the validators from `apps/desktop/scripts/stage-engine-components.mjs` and its per-runtime layout.

An initial packaging invocation mistakenly fed the entire composite into the native packager. Its root-directory DLL checker refused the nested backend DLLs; the failure is retained in `receipts/package-stage.*` and `engine-input`. The corrected `package-stage-r2` creates/validates the native package first, checks each backend's dependency closure in its own folder, and uses `verifyLocalBackend`, `verifyEngine`, `verifyNativeBuild` and the notice membership/hash checks for composition. No `--allow-lib`, widened DLL search path, signature bypass or production validator edit was used. The old compiled outputs and first staging input remain retained.

## Executed qualification

The selected suite contains **15 passed checks, 2 failed checks, 0 skipped checks**. The earlier two exact Python native-version tests also passed.

Passed: actual `strata --version` (0.5.2); both `strata` and `strata-q36` help commands with Q36 memory/KV markers; `q36_bounded_experts_test`, `q36_expert_store_test`, `q36_transfer_lifetime_test`, `q36_bounded_cpu_parity_test`, `q36_kv_layout_test`; Spin8 B2 first-use (32 immediately used nonblocking plans) and full GPU run (617 cases, maximum F32 error 9.375579210768592e-7, F16 error 1.1920753095751024e-7, tracked device peak 312,098 bytes); `q36_kv_lifecycle_test`, `native_cache_bridge`, `native_cache_owner`; matching-toolkit Compute Sanitizer version and Q36 KV lifecycle memcheck. Compute Sanitizer reports `2026.2.1.0 (build 38334959)` from CUDA v13.3; memcheck reports **0 errors**. Each GPU case was admitted with at least 1 GiB free and ran serially.

Failed: standalone `strata-q36 --version` exits 2 and prints usage (the wrapper currently exposes no version option). `q36_kv_cache_test` passes all four actual F32/F16 K/V kernel combinations, then fails at `tools/qwen35/kv_cache_test.cu:144`, `cudaMemset(...kc[layer]...)`, with invalid argument. Static diagnosis, not a corrected-test result: its `session_case` sets `ctx` and calls `alloc_session` directly without initialising the new `key_layout`/`value_layout`; production `Engine::init` initialises these at `src/qwen35/q36_engine.cu:1434-1435`, while `alloc_kv` now uses the layout allocation bytes. The fixture was not changed and the test remains FAIL.

The separate unchanged `cuda_spill_guard` **failed** (CTest exit 8). It found four disallowed instances in `strata_kernels.lib`; all reported LOCAL=0:

| Kernel instance | Measured STACK bytes | Existing allowance |
| --- | ---: | ---: |
| `expdec_down_kernel<20,4>` | 152 | 136 |
| `gemm4_rows_kernel<8,1,8>` | 24 | unlisted |
| `gemm4_rows_kernel<8,1,4>` | 16 | unlisted |
| `block_topk_reg_kernel<33>` | 96 | 88 |

The other inspected native libraries had no disallowed entries. These are actual compiler resource findings, not an approved new baseline or proof that every stack byte is a register spill. `STRATA_CUDA_SPILL_BASELINE` remains empty. The checks and their allowances are unchanged.

## Real Q36 results

All three owned processes used the existing user-selected Qwen3.6 UD-Q4_K_XL GGUF and `.q36epk`, with `--q36-expert-store mapped-pack --max-context 4096 --prefill 512 --expert-slots 5 --mtp 2 --no-warmup --greedy --prompt-cache 0 --conversation-cache-mib 0 --private-conversation-cache --cache-type-k f32 --cache-type-v f32`. The first two set `--q36-memory bounded-experts-v1`; the comparison sets only that mode to `legacy`. The task-local environment explicitly enables the existing pin pipeline, resident streaming, file staging and startup diagnostics. The mapped comparison never used the full legacy host arena. GPU admission required at least 14 GiB free and at least 8 GiB available RAM, above the continuous floors.

The synthetic public completion input has **5 actual tokens**; the same-owner extension has **6**, not 4096. Native PP/DONE report full consumption: first request 5 fresh/0 reused, same-owner request 1 fresh/5 reused; other-owner, missing-owner and post-cancel requests each 5 fresh/0 reused. Every case emitted nonempty decoded output. The longer short request emitted 8 tokens. Cancellation after its first token returned `cancel`; the following request reused zero. All three native processes stopped with exit 0, and the outer Jobs confirmed zero remaining children.

| Run | READY seconds | Native sampled working-set peak bytes | Native sampled private peak bytes | Guard minimum available RAM bytes |
| --- | ---: | ---: | ---: | ---: |
| Bounded initial, 7 requests | 27.469 | 4,899,975,168 | 11,170,480,128 | 9,398,353,920 |
| Bounded restart, 2 requests | 8.062 | 4,897,513,472 | 11,177,050,112 | 9,419,341,824 |
| Mapped legacy, 7 requests | 8.094 | 6,332,485,632 | 11,158,945,792 | 7,913,611,264 |

Native process samples are approximately 5 Hz; they are observed maxima, not exact high-water marks. The separate Job peak commit counters and resource minima are in each guard receipt. First-load versus warm-cache timings are not a speed comparison. All 7 paired bounded/legacy cases had equal input counts, fresh/reused counts, committed output token IDs and finish reasons. The reported common effective settings matched. This does not establish broad numerical equivalence, general model quality or a throughput improvement.

Runtime effective values: context 4096, prefill 512, parallel 1, F32 K/V with F32 accumulation, KV 184,549,376 bytes, recurrent storage 65,863,680 bytes, MTP 2, 41 reported slot counts each 5, CPU workers 6, eager execution (`hybrid_main`), mapped expert bytes 20,127,604,736, expert host arena 0, expert device bytes 393,281,936, H2D pin stage 67,108,864 bytes. Bounded mode additionally reports CPU stage 18,512,896 bytes, 8 CPU wave jobs and 1,048,576 bytes I/O scratch, `windows-unbuffered`, existing pack, and **total_process_bound=0**. It bounds expert working storage, not total process memory.

The model (22,853,663,008 bytes), pack (20,127,612,928 bytes) and existing 412-byte DPAPI verification receipt retained identical sizes and mtime_ns before/after all runs. Native logs explicitly report verification reuse. No pack conversion or model write was performed.

## Commands, evidence and next handoff

All task entrypoints use `C:/Users/downl/.local/bin/uv.exe run --offline --no-project --python C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe python -B`. The owned `guard.py` invokes `build.py r2`, private Node `tools/build_hakua_engine.mjs <build> 1`, `qualify.py stage`, `qualify.py suite`, three `qualify.py model MODE LABEL [short]` calls, exact CTest `-R ^cuda_spill_guard$`, and `report.py`. Compile parallelism is 1. Full explicit command vectors, deadlines, exits and cleanup results are local in `receipts/*.json`; raw outputs stay outside Git. An initial inline AST command lost quotes through PowerShell and failed syntactically; `qualification-script-help` then passed, and all helper paths were subsequently exercised by their actual operations. No failure is erased or counted as a pass.

Final machine-readable handoff: `H:/Strata/releases/personal-052-local2-20261107/qualification-summary.json`. Detailed evidence: `suite.json`, `q36-bounded-first.json`, `q36-bounded-restart.json`, `q36-mapped-legacy.json`, `package-receipt.json`, `receipts/native-build-r2.*`, `receipts/native-bind-r3.*`, `receipts/cuda-resource-guard.*`, and `receipts/final-artifact-audit.*`. Synthetic prompt text/output and private machine-local artifact records stay in this H: evidence root, not in Git.

Host integration remains for the parent: source inspection found no `--q36-memory`, `bounded-experts-v1` or `Q36_MEMORY_CAPABILITIES` references in Host or Control. An opt-in app path must discover/admit/forward the mode together with mapped-pack and explicit slots, then consume the effective memory record. Merely selecting this new binary leaves the native default as legacy. Existing GUI/Control/product versions and global profiles/component selection were not edited here.

Unrun: full-window input/generation, broad quality/performance qualification, HIP/SYCL/Metal compilation, long-duration cache reliability, real-model low-precision validation, desktop install/update and public release. These are outside this Windows native candidate task and selected CUDA toolchain. Black/flake8 and a broad Python/Host regression run were not performed for the task-local evidence scripts; their real command paths were executed, while the two production version assertions were exercised directly. The concrete remaining gates are the Q36 KV fixture failure, standalone Q36 version metadata, and the four CUDA resource findings. Parent owns any follow-up scope, reviewed baseline, final signature, import, allowlist and app overwrite. Keep the installed 0.5.1 engine until that decision.

Final read-only process observation found no Strata/llama-server process. Final free-space observation: C: 6,935,793,664 bytes, H: 326,641,807,360 bytes; GPU 14,528 MiB free. Owned cleanup was confirmed by every retained guard receipt. Final `git diff --check` passed.

Self-review-event: `ticket_completed` and `qa_defect`. Reviewed the failed configure, transient unrecorded version-probe failure, composite/native packaging mismatch, quoted-command failure and native qualification failures against fresh receipts. Response: retain evidence, correct only task-local recipes, preserve every production guard, and explicitly withhold overall qualification. A broad SOP/AGENTS/skill change was rejected: evidence calls for narrow task follow-up, not weaker validation or self-modifying governance. Native algorithms and test acceptance thresholds were not edited.

## Explicit native follow-up (r3)

The user authorised native-only repair of the Q36 version query and typed KV fixture, an additive pre-READY actual-allocation memory INFO contract, resource-guard origin investigation, incremental one-job rebuild and a fresh unsigned `component-r3`. Apps/serve and product/Control versions are owned by the independent bridge agent. Existing output, signatures, profiles and installed engine are retained. Applicable SOPs and canonical context remain as above; systematic-debugging and test-driven-development are additionally applied. Goal: close the two concrete native failures, verify both modes' actual memory receipts, and preserve any unresolved resource guard as FAIL.

Root-cause evidence: the Q36 wrapper forwards every argument without a version branch; the actual binary returned exit 2. The GPU fixture bypasses production's `make_kv_layout` calls, leaving zero allocation sizes, then calls `cudaMemset` on those zero-size allocations. The original fixture failure and source data flow are retained. The new memory contract will be checked against the retained actual old stdout first; no receipt existed before READY. Follow-up evidence is under `followup-r3` and fresh `receipts/r3-*` names. Prior changed build artifacts are copied to `followup-r3/r2-before` before the authorised incremental rebuild.

RED evidence: `r3-contract-red` exited 1 with version-before-model/GPU=false (actual old standalone binary with CUDA devices hidden and a nonexistent model), and receipt-before-READY=false (retained actual old stdout). The earlier actual `q36_kv_cache_test` failure is the fixture regression baseline. `r3-preserve-before` passed and retained hashes/copies of the affected build artifacts. Implementation adds a version early-return in the standalone wrapper and one memory INFO line from live `Engine` allocations before READY. The KV fixture calls the same real typed layout helper used by production, then checks fresh zeroed allocations, empty/partial/end/full prefixes, over-capacity/type-mismatch rejection, and private/MTP clearing without weakening its numerical tolerances. Its receipt test exercises actual small CPU/H2D allocations, legacy nonzero H2D storage and returning to zero after free. KV schema and existing stderr records are unchanged. The follow-up performs no key reads; unchanged auxiliary backends are rechecked against the already-verified r2 component identity.
