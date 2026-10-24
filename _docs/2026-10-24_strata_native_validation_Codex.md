# Source-bound native validation, Task 3

Working branch: `codex/strata-030-completion`. Baseline:
`f128266deca5cd5160aace11132f71db4e867a86`. Task 3 is complete for this bounded
diagnostic scope, with the concerns and wider open gates recorded below.
No release qualification follows from a diagnostic build or short generation.

## Requirements and controls

Bind the existing no-experts.bin native pack to the original, already hashed
large Q2 GGUF shards, regenerate exact pinned codec oracles, run CPU and CUDA
checks sequentially, resume the source-matched native build with one compiler
job, and retain real generated token IDs and text with the real tokenizer.
PLE remains enabled. No model download, repack, deletion, dependency change,
AppData preset change, port 8080 listener, push, tag or release is authorized.

The canonical prompt, home/Codex/repository AGENTS and implementer contract
were read. Incompatible identity, tool and environment assertions defer to the
actual system/developer instructions. Applied SOPs: Common Engineering,
Implementation Start Gate, Skill Selection, Security, LLMOps, Application
Development, Python, CPP and C. Skills: milspec-codex-standard,
evidence-changelog-closeout and agent-self-review-evolution. These are internal
engineering controls; no formal MILSPEC certification is claimed.

Every bounded command uses the reviewed `verify_codec_dialects_build.ps1` in
a fresh actual Windows PowerShell 5.1 process. The reserve is at least 10 GiB.
Expected peak includes all writes, including retained native build objects
outside the evidence root; output allowance covers the evidence root only.
Partial logs and actual child exit remain separate from guard status.
Python uses existing uv offline/no-project with installed Python 3.12.10,
`python -B`, `PYTHONDONTWRITEBYTECODE=1`, and disabled pytest plugin autoload.
Existing uv dangling-directory warnings remain visible and are not repaired.

## Owned changes

`tools/verify_native_pack_binding.py` reads existing pack/model inputs only.
It validates all index fields, original shard bounds, all native-expert rows,
unconverted dense bytes in 8 MiB chunks, tokenizer vocabulary IDs, merge order,
types, special IDs, configuration and exact chat template. It refuses conversion
packs and experts.bin because those require separate payload validation.
`tools/test_verify_native_pack_binding.py` contains negative controls.
`tools/run_native_validation_step.py` and its focused test file add the durable
sequential launch gate required after the sequencing errors described below.
This record is the only owned durable documentation file.

## Pack binding

Receipt: `H:/Strata/build/task5a-pack-binding-20261024-01/binding.json`.
The full-shard hash receipt at
`H:/Strata/build/completion-resources-20261024/q2-model-source-hashes.json`
was reused only after exact size and 100 ns mtime checks before and after.
No redundant 66 GB hash scan was performed. Validation of all 1,079 index rows,
48 expert rows and the stored dense spans passed. The validator writes an
exclusive new receipt, with source receipt and validator/metadata hashes.
Resource allowance: additional 256 MiB, aggregate output 128 MiB, 600 seconds.
Actual child exit 0, guard reason null, zero owned processes after cleanup.

## CPU codec group

Evidence root: `H:/Strata/build/task5a-codec-20261024-01`.
Resource allowance per bounded command: additional 2 GiB, aggregate output
1 GiB, reserve 10 GiB. MSVC Visual Studio 17 2022 x64 builds use Release and
one job, `/p:BuildInParallel=false /p:CL_MPCount=1`.
Pristine source pins: TheTom `643956891dfdf51aecdbd05ca508dd21e21e8195`,
Prism `73bfe6cc485554822f80c473a3c0c4f25e80f41b`, native GGML
`3cf03257f219afbe7334045ff7c6a06ac68c627d`; each was clean at start.
The existing generator prepared independent C sources, built them, and emitted
3,084 / 931 / 225 records. The regenerated 86,204-byte golden SHA-256 is
`326ec8f6e7c17b626a1b7c13845e5b547703f7ec2568a0b4f69b64964ae1d755`.
The codec build enables `TQCODEC_DIALECTS=ON`, `TQCODEC_SPIN8_TESTS=ON` and
points `TQCODEC_ORACLE_FIXTURES` at this fresh oracle directory. Verbose CTest
passed 11/11 in 14.52 seconds, including all 4,240 fresh oracle records, 98
golden records, checked capacities/aliasing, codec/cache/transport, calibration,
Spin8 composition and synthetic distillation. The six separate mutants from
`verify_codec_dialect_faults.py` built and were all detected by ordinary CHECK,
byte or F32 mismatches; CTest WILL_FAIL passed 6/6 in 11.78 seconds. These tests
are CPU evidence. The synthetic distillation held-out loss worsened and its
passing mechanics test is not evidence of useful model adaptation.

## CUDA kernel group

Evidence: `H:/Strata/build/task5a-cuda-20261024-01`. Fresh Spin8 configuration:
`SPIN8_ENABLE_CUDA=ON`, `CMAKE_CUDA_ARCHITECTURES=120`, Visual Studio 17 2022
x64 with CUDA 13.3.73, MSVC 19.44.35224.0 and the existing Python 3.12 executable
for CMake's sidecar test. Release, one job. Additional peak 2 GiB, aggregate
output 1 GiB, reserve 10 GiB. Build completed with four retained C4211 warnings
in nvcc-generated host stubs; no warnings were suppressed or repaired.
Verbose CTest passed 10/10 in 44.30 seconds on the RTX 5060 Ti. This includes
CPU/query/ABI/sidecar tests, CUDA transform/attention, query/v3 batch and native
GQA adapter. Native GQA max absolute error versus the CPU F64 reference was
`2.748827807041998e-08`; the tested 24-head batched width-256/tail query path
reported max absolute error zero versus its CPU per-head reference.

Negative cases target invalid host transform coefficients, host-side layout,
capacity, overlap, overflow and version values; actual device input/parameter,
tail, identity-row and result nonfinite data; arithmetic overflow and sticky
status flags. The native adapter emits coefficient-F64/F32 audits. These tests
do not prove monitoring of actual deployed GPU coefficients, inference stopping,
cache/RNN invalidation, complete cache lifecycle, or full G1/G4 monitor closure.
Those implementations and GPU fault tests belong to Task 4.

One orchestration sequencing error is preserved: `cuda-build` was issued before
the asynchronous configure finished. It exited 1 immediately with missing
CMakeCache.txt and launched no compiler. After configure's final receipt showed
child exit 0 and zero remaining owned processes, `cuda-build-2` completed 0.
All dependent transitions thereafter require the final receipt and true exit 0.
No product-code defect or capacity failure is inferred from that failed label.

## Native build preflight

Evidence: `H:/Strata/build/task5a-native-20261024-01`. The old resume runner
was inspected but never executed. All 476 native-scope paths and SHA-256 values
match the retained object manifest; that source scope is clean. The pinned GGML
checkout is clean at `3cf03257f219afbe7334045ff7c6a06ac68c627d`. `input.json`
retains current source HEAD, all hashes, exact command, compiler hashes and the
cache snapshot/hash. The cache has CUDA 120, Spin8 and native experts on, HIP
and SYCL off, and `STRATA_PORTABLE=OFF`. Retained build size was 246,238,441 B.
This is a diagnostic build, not portable distribution qualification.
The resumed target is `strata`, Release, one job, with MSBuild parallelism off.
Additional peak is conservatively 6 GiB for further objects, compiler temporaries
and logs, against approximately 26.6 GiB free; aggregate evidence allowance is
256 MiB, reserve 10 GiB, timeout 7,200 seconds. The owned guard retains the real
child exit and partial logs. Existing C4819 code-page warnings remain visible.

The diagnostic prompt uses the real pack tokenizer through
`tools/strata_tokenizer.py` and `serve.frontend.ChatTemplate`, including the
model template's generation prefix, with thinking explicitly disabled. Its
30 token IDs, rendered prompt and source hashes are in `prompt.json` and
`tokens.txt`. Requested output is at most 32 tokens, context capacity 256.
The first plan disabled MTP, speculation, vision and Spin8 transformations.
That plan was refused before setup; the supported minimum-window plan below
keeps MTP/vision/Spin8 off and required PLE on. No short diagnostic establishes full context,
quality or an optimized production performance baseline.

## Validator verification

Validator RED: pytest collection failed with ModuleNotFoundError for the absent
validator. First GREEN: 3 passed in 0.99 s. Final focused suite: 13 passed in
1.80 seconds (`validator-tests.xml` and `.console.txt` beside the binding).
Tests cover multi-chunk mismatch/truncation, duplicate/malformed index rows,
100 ns mtime precision, vocabulary/type/special/template/merge corruption and
a full tiny actual-GGUF/pack fixture with dense, index offset, expert-row and
source-receipt corruption. The original tiny GGUF stays byte-identical.
Self-review added rejection of unrecorded quantized conversions and checking
the shipped tokenizer pre-pattern against the real tokenizer implementation.
The final real binding run passed after those validator changes.
Final formatting/lint and source/artifact checks passed as recorded below.

## Completed native diagnostic and actual output

Native build finished at 05:18:15Z, child exit 0, no guard reason and zero
remaining owned processes. All 476 source hashes/path names and the cache hash
remained unchanged. Native build size became 424,609,222 B, an increase of
178,370,781 B, below the 6 GiB estimate. `result.json` contains the executable,
local DLL/library, generated-overlay and source/toolchain identities.
`strata.exe` is 78,199,808 B, SHA-256
`1d324ba7b1b0f292a91843b159ab53169c5a3fa3aa8d824e5c3ccbd979dd8eb9`.
Dumpbin dependencies and CUDA 13.3 cublas/cublasLt candidate hashes are retained.
The model child prepended the explicit CUDA 13.3 bin/x64 directory to its own
PATH and used a task-local CUDA cache. Those are scoped child environment
settings; no global environment or AppData setting changed. Vendor DLL hashes
are candidate/path evidence, not a live loaded-module enumeration claim.

Final pack validation passed in `binding-final.json` with the final validator
source hashes. The first direct run, `model-generate`, ended 2 before model
setup because native packs require `--spec T` with T >= 2 (generate.cpp3729).
Its record and original plan remain intact. The controller authorized the
supported minimum `--spec 2 --suffix-draft 0 --lookup-chain 0`, without MTP.
The successful plan is `plan.spec2-approved.json`. It is a required-window
greedy diagnostic; it must not be described as speculation off.

The successful real native run, `model-generate-spec2`, used PLE ON, original
GGUF experts in place, actual 30 prompt token IDs, capacity 256 and maximum
32 new tokens. It generated `[44061, 248046]`. The actual tokenizer decodes
them as `READY<|im_end|>`; content is `READY`, termination is EOS. The actual
input IDs exactly equal the prepared prompt. `generation.json` binds output,
tokenizer/template, prompt, executable, guard receipt and unchanged model
size/100 ns timestamps. The original full model hashes were not repeated.
The guard ended naturally at 05:27:51Z with child exit 0, guard/error null and
zero owned processes after cleanup. No unrelated process was terminated.

Profile filling took 212.4 seconds. Auto cache shrank 8267 proposed slots to
5034 / 6.48 GiB. During input processing at 05:27:28.852Z, available physical
RAM was 64,659,456 B and available commit 6,279,233,536 B, while GPU free was
4473 MiB. This actual pressure observation is retained; no sustained-30-second
pressure claim is made. The run ended naturally about 22 seconds later, before
the requested short safety-stop observation needed action. Postflight at
05:28:56Z showed 12,760,715,264 B physical / 20,741,160,960 B commit available,
15467 MiB GPU free and zero owned job members. Its reported 0.61 tok/s and
65.6 s TTFT are excluded from performance/adoption claims. The minimum-window
run proves this short source-bound diagnostic, not 4K/32K context or quality.

## Sequencing defects and durable prevention

A second sequencing error occurred before the successful model run. PowerShell
7's JSON reader converted ISO timestamp strings to DateTime, causing the
string comparison to report a false model-metadata failure. The separately
dispatched launch still ran. Immediate `-DateKind String` plus exact UTC-tick
checks confirmed both source sizes and timestamps unchanged. This is recorded
as a failed preflight and a post-launch correction, never as a passed preflight.
`preflight-failure-correction.json` preserves that distinction. The earlier
successful final binder independently bound the same inputs before the run.

The new sequential launcher performs all checks synchronously before it can
call the reviewed guard. Every prerequisite must explicitly report terminal
finished, integer child exit zero, no guard/error, contained-before-resume true
and integer active-process count zero. It rejects boolean substitutes. It
checks executable hash and explicit disk budgets, optionally checks exact
model metadata and current RAM/commit/VRAM, writes a preflight receipt, and
starts a fresh Windows PowerShell 5.1. That host rechecks the successful
preflight and hashes the same plan bytes before invoking the unchanged guard.
Literal task5a root/label constraints and exclusive new files preserve old
evidence. Failed/unfinished checks cannot be followed by a queued guard call.
This is a trusted local-plan launcher, not a security sandbox or a continuous
runtime RAM monitor. Controller ownership and the underlying guard remain
separate requirements.

Launcher RED: absent module, retained in `sequential-red.console.txt`. GREEN:
seven invalid prerequisite controls plus failed executable/resource preflights
all prove zero child/guard attempts, 9/9 passing. Actual positive smoke used
three completed real prerequisites and fresh model metadata/resource checks,
then ran only the lightweight output decoder through a fresh guard; child 0,
cleanup 0, exact READY/EOS result. No second large-model run was performed.
All subsequent final formatting, tests and lint used this entry point with
successful prior receipts. Combined suite: 22/22 passed in 1.95 s; black --check
and flake8 (`--max-line-length=100 --extend-ignore=E203,W503`) passed for all
four owned Python files. Earlier long-line lint findings remain recorded.
Final evidence: `H:/Strata/build/task5a-sequential-tests-20261024`.

Self-review-event: type=qa_defect scope=native-validation-orchestration category=dependent-stage-dispatch evidence=H:/Strata/build/task5a-native-run-20261024-01/preflight-failure-correction.json

Self-review-event: type=local_fix scope=tools/run_native_validation_step.py category=sequential-gate evidence=H:/Strata/build/task5a-sequential-tests-20261024/combined-tests.xml

The response is a narrow launcher and regression tests. No SOP, skill or
AGENTS rewrite, weakened gate or source repair was needed. Current native
kernel/short-model results leave G1 runtime monitoring, G2 HTTP and >512 prompt
tokens, G3 quality/adoption, Task 4 physical compressed cache/integration,
portable distribution, wider context/performance and formal release open.

Rollback is a scoped revert of this task's owned commit; preserve all evidence
and unrelated working-tree changes. Independent review belongs to the controller.
