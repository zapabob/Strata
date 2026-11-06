# K1 implementer report

Status: DONE_WITH_CONCERNS — source implementation and scoped CPU/Host checks complete; native compile and GPU qualification NOT_RUN. This does not qualify FP16 model quality, 98304/131072 input generation, or a release.

Worktree: `H:/Strata/worktrees/cuda135-kv-20261106`.
Exact source base: `fdbefe3e7a19443e3b62e3818c2374c5a8ff53bb`.
Exact implementation head: `494032aee4c20799cda30bb2c98a479536aa9588`.
The following documentation-only commit contains this report; the source head above is the tested implementation. Frozen comparison checkout was not changed.

## Requirements and implementation

The existing independent `--cache-type-k/v f32|f16` interface remains canonical, including mixed formats and the F32 default. No redundant `--q36-kv-type` alias was introduced. `kv_layout.hpp` centralises checked multiplication/addition/alignment, row/head/scale strides, plane offsets, payload/scales/padding/allocation bytes and type/version/scale-schema identity. F32/F16 are the only executable types. Q8_0 and native NVFP4 are explicitly proposed layout calculations, reject partial blocks, and cannot enter lifecycle operations or runtime capabilities. Their codec and scale/rounding semantics remain unimplemented.

Q36 sessions carry independent K/V descriptors. Allocation, prefix copy, full private wipe and receipts use those descriptors; session selection and copying reject incompatible identity and out-of-capacity prefixes. `q36_kv_cache.cuh` borrows session-owned device storage and centralises copy/clear. Existing attention append/read dispatch, arithmetic, router top-8, GDN and MTP commit/rollback math were not rewritten. MTP remains logical valid-prefix rollback; the new byte lifecycle fixture does not claim to execute actual speculative decoding.

`Engine::init` checks positive geometry, GQA divisibility, device-index capacity and total persistent KV allocation before its CUDA allocations. CLI context parsing rejects malformed/overflow values instead of using `atoi`. Dense model loading precedes Engine::init in the existing path; this is not a claim that the entire model loader was moved behind a new admission gate. Full-model digest, pack digest/CRC, mapped-pack allowlist and resource admission logic remain in place.

Actual executable support is negotiated using only `--help`, with no model/user arguments or saved environment. A new `Q36_KV_CAPABILITIES` marker has a strict bounded schema and only scalar formats. Old help without the marker is unknown. The generic source already handles `--help` before CUDA device probing; the new unified-binary early path and standalone Q36 path emit the marker before model access. Parent approved the tiny `src/program/generate.cpp` ownership extension because the unified binary otherwise dispatches Q36 only after reading a GGUF header. No actual engine help query was executed in this task.

Host and Python independently enforce 3-second/65536-byte help bounds and reject duplicate markers, malformed schemas, unimplemented formats, timeouts and changed digests. Host rehashes after probing; Python probes its actual resolved child and checks the Host-bound digest, then rehashes immediately before process creation. A replacement in the remaining OS path-to-exec race is not cryptographically prevented; this is a recheck, not an immutable executable handle guarantee. Unknown binaries receive no new cache flags: explicit F32 flags are omitted, and F16 requests fail closed. Top-level settings cannot bypass the argv contract.

Python validates the child's INFO dtype, layout version/schema, geometry and exact persistent allocation before accepting READY for negotiated formats. The production constructor prefix is exercised with mocked process IO, including incorrect READY receipts and changed executables. Requested/planned values remain distinct from child-generation-bound observations. Host recomputes bytes from observed geometry, including the actual attention-state count (rather than assuming MTP is present). Prelaunch default-geometry estimates are labelled theoretical and exclude every other allocation.

The selected-model settings endpoint and actual `NativeSettings.tsx` component now use per-model fields. Q36 shows only F32 when binary capability is unknown, and F32/F16 after negotiation, with an experimental/unqualified notice. Generic Spin8/Turbo/Q8 choices are not shown as Q36 capabilities. While changing models, fields remain empty until the selected response arrives, preventing a transient generic menu. Generic family field choices and numerical implementations remain unchanged. Parent approved this minimal UI ownership extension; there is no restyle.

## Changed files

Native: `include/strata/qwen35/kv_layout.hpp`, `src/qwen35/q36_kv_cache.cuh`, `src/qwen35/q36_engine.cu`, `src/program/generate.cpp`, `CMakeLists.txt`, `tests/qwen35/q36_kv_layout_test.cpp`, `tests/qwen35/q36_kv_lifecycle_test.cu`.

Host/UI: `apps/host/server/q36-kv-capabilities.mjs`, `q36-run-contract.mjs`, `q36-startup-events.mjs`, `native-control.mjs`, `native-settings.mjs`, `run-config-check.mjs`, `index.mjs`; `apps/host/src/components/NativeSettings.tsx`; scoped tests `q36-kv-layout.test.mjs`, `q36-capabilities.test.mjs`, and fixture injection in `tests/helpers/native-fixture.mjs`.

Python: `serve/server.py`, `serve/test_q36_kv_contract.py`.

## Fresh validation

Node executable: `C:/Users/downl/AppData/Local/Programs/Strata/node/node.exe` (24.22.2). Python executable: `C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe`. These task-brief-specified installed runtimes were used without installation or dependency changes. `PYTHONUTF8=1` and `-B` avoid Windows encoding ambiguity and bytecode artifacts during tests.

Final Host command, cwd `H:/Strata/worktrees/cuda135-kv-20261106/apps/host`:

```powershell
& C:/Users/downl/AppData/Local/Programs/Strata/node/node.exe --test tests/q36-kv-layout.test.mjs tests/q36-capabilities.test.mjs tests/q36-run-contract.test.mjs tests/q36-progress.test.mjs tests/q36-private-cache.test.mjs tests/q36-load-lifecycle.test.mjs tests/native-control.test.mjs tests/native-settings.test.mjs tests/run-config-check.test.mjs tests/native-settings-response.test.mjs
```

PASS: exit 0, 58 tests, 58 passed, 0 failed, 0 skipped. This includes strict help negotiation, mixed F32/F16 byte formulas, legacy no-new-flags, observed allocation mismatch, real Host load-config generation with mocked process startup, selected-model fields, existing private cache/isolation, mapped-pack admission and native settings checks.

Final Python command, cwd worktree root:

```powershell
$env:PYTHONUTF8='1'
& C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe -B -m unittest serve.test_q36_kv_contract serve.test_q36_config serve.test_private_cache -v
```

PASS: exit 0, 15 tests. Seven new tests cover strict schemas, bounded/timeout/oversized help IO, digest changes, top-level/argv conflicts, legacy behavior, exact receipts and the real constructor through its pre-READY gate using fake process IO. Existing Q36 configuration (4) and private-cache (4) tests passed.

Controller-owned TypeScript command, cwd Host:

```powershell
& C:/Users/downl/AppData/Local/Programs/Strata/node/node.exe H:/Strata/worktrees/cuda135-kv-20261106/apps/host/node_modules/typescript/bin/tsc --noEmit -p H:/Strata/worktrees/cuda135-kv-20261106/apps/host/tsconfig.json
```

PASS: controller reported exit 0 with empty log; inspected `task-K1-typecheck.json` (finished 2026-11-06 11:36:31 JST). `task-K1-dependency-reuse.json` records a controller-created node_modules junction to the existing release worktree after semantic package-lock comparison. No installation occurred. This result is controller evidence, not a compiler command executed by the implementer. NativeSettings was unchanged after this check.

`git diff --check` and `git diff --cached --check`: PASS, no whitespace errors. Read-only discovery used `Get-Content`, `rg`, `git status`, `git diff` and `git rev-parse` on scoped instructions, audits and callsites.

## Failed attempts and unresolved checks

1. The initial text-edit helper reading `native-control.mjs` hit Python's Windows cp932 decoder before writing. It was rerun with `PYTHONUTF8=1`; no partial edit from that failed invocation occurred.
2. Initial Node new integration fixture failed because the run-config validator still rejected Q36 top-level F32. The validator now accepts F32 only for Q36 configs; final 58-test suite passes.
3. Initial Python invocation included `tests.qwen36.test_startup_log_analysis`, which failed its existing sibling-module import (`startup_log_analysis`). Corrected command: `python.exe -B -m unittest discover -s tests/qwen36 -p test_startup_log_analysis.py -v`.
4. Corrected startup-log suite: 9 passed / 1 failed. The unchanged `test_packaged_evidence_summary_is_historical_not_a_new_run` expects `NOT_IMPLEMENTED_NOT_GPU_TESTED` or `PARTIAL_IMPL_GPU_SPEED_NOT_RUN`, but the existing evidence summary contains `PARTIAL_IMPL_MAPPED_LIVE_READY_T03_PASS_T04_KEEP_DEFAULT_PREVIEW_6_SHIPPED_T06_BLOCKED_T07_PROFILE_PASS_KERNEL_NOT_RUN_T08_REFUSE_PASS_MEASURED_NOT_RUN_T09_PARTIAL`. Neither historical test nor evidence was changed. The real child-generation constructor-prefix and legacy trace-format tests passed.
5. Initial TypeScript attempt could not find worktree `node_modules/typescript/bin/tsc`. Initial broadened Host tests likewise could not import esbuild. Controller reused the existing dependency tree as above. A subsequent root-cwd Host run passed 55 tests but failed two esbuild fixtures with relative `src/...` paths; rerunning from the project-standard `apps/host` cwd passed all 58. These were invocation/dependency failures, not suppressed assertions.

NOT_RUN: native C++/CUDA compilation and CTest, HIP/SYCL builds, Compute Sanitizer, real binary capability queries, GPU lifecycle tests, full-engine FP32 token/logit/state bitwise comparison, actual MTP acceptance/rejection/cancellation, real GUI/server/model launch, Hermes integration, model quality/PPL/KL, long-context generation and performance/resource qualification. The parent owns a sequential native comparison build, and explicitly prohibited a concurrent compiler/GPU/model run. Prepared CMake targets are `q36_kv_layout_test` (CPU) and `q36_kv_lifecycle_test` (CUDA). Existing kernel/cache tests must also be run later; the new raw-byte lifecycle fixture is not an append/attention numerical oracle.

Controller separately planned an isolated component-render check after source freeze. Its result is not claimed here; append its independently produced artifact to the review package when available.

## Concerns and next gate

Native source has not compiled in this task; completion is bounded to implementation and CPU/Host source validation. Existing FP16 overflow/nonfinite input handling and full speculative rollback numerical qualification remain K2 work. Q8_0/NVFP4 are layout proposals only. No performance, 32 GB RAM / 16 GB VRAM fit, full-window generation, release readiness or formal MILSPEC certification is asserted. Unchanged FP32 kernels are source evidence only until an independent exact-output fixture runs.

The minimal GUI override is source/type/mock tested; actual desktop/installed-binary behavior remains unqualified. The probe's sanitized environment may make a binary with nonstandard runtime DLL paths return unknown; this conservatively blocks F16 and keeps the legacy default. Broad formatting/static analyzers were not installed or run. There are no package/version/release/feed changes, no downloads, no cache deletion, no runtime stop or service changes, and no resource-floor reductions.

Rollback is a normal revert of implementation commit `494032aee4c20799cda30bb2c98a479536aa9588` on an isolated branch after coordinating with later changes. No reset/clean/stash is required. Parent should review, schedule the prepared native targets after its active comparison build, and keep all GPU and quality gates separate.

## Standards

Read canonical `C:/Users/downl/_docs/prompts/CLAUDE-FABLE-5.md`, PC/Codex/project AGENTS, task brief and native/KV audits. Applied common engineering, implementation start gate, skill selection, security, LLMOps, C++, Python and TypeScript SOPs; skills `milspec-codex-standard` and `api-and-interface-design`. `codebase-inspection` was inspected but its LOC tooling was inapplicable and was not run. Task brief explicitly selected existing interpreters and prohibited installs, overriding the general uv default. Trust boundaries are config → Host → Python → actual executable → INFO receipts, with no model prompt or credential data in capability probes. The `_docs` companion log records this implementation and links here.
