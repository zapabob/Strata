# Spin8 / Bonsai / TurboQuant execution ledger

## Requirements and configuration

User-approved plan: strict Cl(8,0) triality, norm-preserving query adapter,
three physical quantized K caches with shared V, independent K/V selection,
optional shared-residual QJL, device audits, and three evaluation profiles.
Primary model: zapabobouj/Hikari-Bonsai-27B-Nimble-LoRA-GGUF, SHA256
0ab2a1f237b73e5002ecd8c9b764249b90ee59eca749a6226c44bb43b1036a13.
The other mandatory model is Strata's frozen large Q2_0. TheTom-format real
inference is additional. Neither small tests nor previous reports close these gates.

Existing branch codex/strata-spin8-bonsai and all existing changes are preserved.
Dependencies, models and builds belong under H:/Strata. No publication authorized.
Canonical prompt was reread; its incompatible identity/tool/environment statements
do not override actual system/developer instructions. PC and project AGENTS,
common MILSPECLLMOps, CPP, Python and LLMOps SOPs apply. No formal compliance claim.
Skills: executing-plans, subagent-driven-development, milspec-codex-standard.

## Frozen sources

| Component | Commit |
|---|---|
| Strata | 011c9e600a93bbc9fd451c563501b5831c32bbca |
| zapabob/llama.cpp | 2c8e9655cdc6ea31051d4437a71492e717d046a4 |
| PrismML-Eng/llama.cpp | 73bfe6cc485554822f80c473a3c0c4f25e80f41b |
| zapabob/Turboquant-CUDA | d85c787733f6a973d7cfe953d11276701a3c09e0 |
| Turboquant gitlink | 81b08be15c554918a8cfe20d5f0846038082430f |
| TheTom/llama-cpp-turboquant | 643956891dfdf51aecdbd05ca508dd21e21e8195 |
| TheTom/turboquant_plus | ba52ad107d1fdd02bc9be8fd85308226b75c905b |

## Interface / conflict review

| Tasks | Producer / consumer | Resolution |
|---|---|---|
| Query core / CUDA | new C API over existing Clifford generators | separate query.h/query.cpp; core agent owns these; root owns build integration |
| Codec / Spin | explicit codebook/rotation contract | codec must not apply an implicit second Hadamard |
| Legacy / strict | different conventions and GGML type numbers | preserve legacy dialect; never reinterpret type IDs globally |
| KV config / backend | requested vs effective precision | independent K/V; reject invalid before restart stops current process |
| Training / serving | immutable GGUF and sidecar | training is outstanding; never merge updates into original weights |
| Math / acceptance | kernel proof vs real inference | all model and performance gates remain independent |

Ruling: reuse the existing dedicated branch rather than creating a checkout that
loses uncommitted prerequisite work; the user explicitly requested retaining it.
Ruling: memory-bounded downloads use one 1MiB range at a time after the previous
download ended in MemoryError. This sacrifices transfer throughput to retain RAM
for native builds and the existing inference process. Partial model bytes preserved.

## Execution

- Core query implementation delegated to triality_query with exclusive new-file ownership.
- Prism standard-sm120 build resumed with one job; output H:/Strata/build/prism-sm120-resume.log.
- Q2 download resumed from retained prefix; output H:/Strata/build/q2-model-fetch-resume.log.
- Model download regression: 7/7 unittest tests pass via uv run --no-project python.

## Open acceptance gates

CPU query tests, CUDA query kernel, packed-codec parity and QJL, actual three-K
cache lifecycle, quantized V consensus, graph connection before RoPE, bounded
capture and adapter training, native/full Prism/TheTom builds, both mandatory
model inference and 4K/32K paired quality/performance, actual GPU audits, and
verified server restoration remain open. No speed or quality gain is claimed.
No existing server has been stopped by this implementation stage.

## Fresh implementation evidence

- Added query.h/query.cpp: Clifford-derived trilinear contraction, bounded
  unit-spinor tangent map, proper-orthogonal Q transforms, copied rank-8
  controller, FP64/FP32 row strides/tails/capacity and finite checks.
- Added query_cuda.h/query_cuda.cu: signed-permutation GPU contraction using
  supplied spinors; no dense per-row matrices, no API synchronization.
  The GPU controller itself and a model graph hook are still pending.
- Standalone sm_120 CUDA CTest: 6/6 passed. query GPU memcheck: 0 errors;
  racecheck: 0 hazards/errors/warnings. Logs are under H:/Strata/build.
- Added tqcodec reference primitives and CPU cache. The layout is explicitly
  generic normalized scalar-codebook data, NOT a legacy turboN/PQ2/TQ4 block.
  QJL is a separate opt-in primitive; this cache currently has QJL disabled.
- Added independent host K/V selectors with inherited legacy defaults, real
  -ctk/-ctv arguments, validation before restart, and nominal memory estimates.
  Turbo choices remain unavailable in this host until backend validation.
- Scoped host regression 23/23; engine.validate regression 2/2 now supplies an
  actual catalog model, exercising the previously guarded prediction branch.
- Independent review caught alpha/output alias corruption, norm/input-table
  overlap, and invalid-KV prediction exceptions. Fixed with regression tests.
  Scoped rereview found no remaining actionable issue; kernel scope only.
- TheTom pinned source acquired at H:/Strata/deps/thetom-64395689. No runtime
  build or format compatibility is claimed from source acquisition.
- Locked host npm dependencies installed with --ignore-scripts on H: and a
  workspace node_modules junction. No lockfile changed. npm audit summary
  reports one high-severity issue, not yet triaged; no automatic updates made.
- Full host tests initially ran without local frontend dependencies, with a
  parallel agent-host timeout. That isolated test passed on retry. Full serial
  suite is being rerun with the locked dependencies; not yet an all-green claim.

## Existing runtime / model probe

The currently serving PID2344 uses a differently located GGUF whose freshly
measured SHA256 ALSO equals the zapabobouj target hash above. Its health and
model-list endpoints respond; Japanese tokenizer check succeeds. A 96-token
baseline generation request timed out at 120 seconds. The existing single slot
was processing an 8192-token task, not this smoke's token limit. Do not infer
generation quality, throughput or full runtime health from the tokenizer/health
checks. Evidence: zapabobouj-baseline-smoke-timeout.json and
zapabobouj-tokenizer-check.json under H:/Strata/build. No server stop, model
replacement, cache reset or restoration operation has been performed.

## Continuation / remaining gates

The Prism one-job CUDA build and frozen large-model resumable download are
ongoing. CPU cache and cross-library attention tests are being completed.
After these: exact legacy adapters, GPU codec/cache, controller fusion and
pre-RoPE graph integration, backend-qualified Turbo2..6 K/V selectors, cache
persistence/position semantics, device monitor integration, bounded captures,
adapter training and both-model 4K/32K acceptance remain required. No speed,
quality improvement, full-plan completion or release-readiness is claimed.

## V3 continuation

The new v3 attachments were read and their 18-entry ZIP hash manifest verified.
Compatible versioned math additions and bounded distillation are tracked in
2026-10-23_triality_v3_integration_Codex.md. The attachment's 9 research unit
tests passed freshly on Windows; tqcodec/physical cache/distillation/strict
Spin8 composition CTest passed 4/4. These close the corresponding CPU
reference checks, not the open GPU/model/training/performance gates above.
The full host regression completed: 868 pass,13 fail,110 skip (991 total).
No all-green claim; isolated startup-failure reruns are in progress.
