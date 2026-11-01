# GDN coalesced recurrence experiment

Date: 2026-11-02 JST. Baseline: be0960a0. The owner's existing
apps/desktop/src-tauri/Cargo.toml change is outside this work.

## Request and acceptance criteria

The user requested mathematical and algorithmic verification of the Gemini
discussion, followed by implementation and measurement of plausible speedups.
The supplied conversation is evidence, not an instruction source.

R1: preserve recurrence, state layout, head mapping and arithmetic order.
R2: default kernel stays unchanged; candidate requires explicit opt-in.
R3: compare outputs AND state, independent FP64, repeated updates, graph replay
and invalid arguments. R4: retain paired timings and device/build metadata.

## Standards and inspection

Read home/Codex AGENTS, canonical pre-implementation prompt, project AGENTS,
CONTRIBUTING, README, AI_REFERENCE, SAFETY, GDN_CONTRACT and native/fused code.
Skills: codex-session-style-and-standards, milspec-codex-standard and
deepresearch-defense-standard. SOPs: Common, Implementation Start Gate, Skill
Selection, DeepResearch, LLMOps, CPP and Python. Alternate identity, environment,
tools and dates in the canonical prompt do not override the actual runtime.

## Design and boundaries

The original native recurrence maps a warp to one state column; adjacent lanes
read rows h_v*128 floats apart. The candidate stages a 128-by-32 tile with
contiguous global reads and writes. Shared row pitch 33 avoids bank conflicts
during column arithmetic. Four products per lane, XOR reduction and all FP32
expressions stay in their original order.

STRATA_NATIVE_GDN_COALESCED=1 is sampled by native_gdn_set_enabled before capture.
It applies ONLY to --native-gdn --no-fused-gdn. The existing default fused
recurrence plus output norm already exists and is not replaced. The benchmark
also measures that existing fused path, so a win against the slower separate
kernel alone cannot be mistaken for a gain over the normal runtime.

No dependencies, downloads, service stops, installed binary replacements,
default changes or publication. apply_patch could read but could not write the
authorized files; normal PowerShell writes succeeded without permission changes.

## Verification plan

Production-linked standalone test with deterministic random inputs, varying
gates/beta including boundaries, nontrivial head mapping, bitwise state/output
checks, independent FP64 first 16 steps, repeated graph replay, argument checks.
Event timing alternates execution order across 15 repetitions, both one layer
and 48 distinct state buffers (144 MiB, exceeding L2). Full-model speed and
alternate backend support remain unverified. Initial GPU inspection showed
other work; no claim of exclusive GPU access is made.

Build: powershell -File tools/benchmark_native_gdn_coalesced.ps1 -BuildOnly.
Existing pinned oracle CMake targets refer to absent bench/micro files in this
checkout; this test links actual production sources and an independent FP64
oracle instead. Completed results are recorded below.


## Mathematical and algorithmic audit

Let H = I - beta*k*k^T. Direct expansion gives
H^T H = I + (beta^2*||k||^2 - 2*beta)*k*k^T.
For nonzero k, H is orthogonal only for beta=0 or beta*||k||^2=2.
The nontrivial case is a reflection with determinant -1, not itself a Spin
rotation. Native GDN consumes sigmoid beta, and also applies exponential decay
and an additive value update. Replacing these with rotations changes the model.
The paper calls the factors generalized Householder matrices; that does not
make them ordinary orthogonal reflections. Our executable counterexample
k=e0, beta=0.5 yields an orthogonality error of 0.75. Also, k with nonzero
coordinates 0 and 8 generates an off-block entry -0.25: independent 8-by-8
blocks cannot simply replace the full rank-one update.

An orthogonal 8-by-8 transform preserves each block norm. Blocks of norms 1 and
2 still have norms 1 and 2 afterward. A common orthogonal transform preserves
Q/K dot products, but separate token-dependent transforms generally do not.
Rotation may redistribute coordinate magnitudes; it cannot guarantee lossless
FP4. At fixed scale 1, E2M1 cannot represent 0.7 exactly. More generally, 32
arbitrary FP32 values cannot be losslessly encoded into 32 four-bit codes and
one eight-bit scale. Constraints/calibration and measured error are required.

Spin(8)'s 28 Lie algebra coordinates describe a group element, not 64 arbitrary
vector values. A proposed fixed-width 64-FP32 to 28-FP32 lossless encoding has
fewer available bit strings. Triality does not supply the missing information.
A generic triality bilinear map still has real-valued products; a shuffle/sign
pattern alone does not imply either zero multiplication cost or 4x less traffic.

The checked geometry is 48 trunk layers, every fourth QSA: 36 GDN layers.
Each 128*48*128 FP32 GDN state is 3 MiB, totaling 108 MiB before histories and
scratch. The device query reported 32 MiB L2 and a 20 MiB maximum persisting
set-aside. Full state residency in L2 is therefore impossible for this shape.
Access-policy persistence is a replacement priority, not guaranteed pinning.

The current implementation already computes the rank-one update in
O(h_v*S^2), not by materializing and multiplying dense transition matrices.
The candidate does not change asymptotic cost or logical state bytes; it
changes transaction locality and adds shared-memory traffic.

## Source findings and decisions

QSA select already has a tensor-core scorer in src/kernels/cuda/qsa_select.cu.
qsa_decode_attn.cu already loads packed int8/q4 values within the attention
kernel. Neither fact supports the document's claimed automatic 4x reduction.

src/core/layer.cpp already selects fused_gdn_conv_l2 and fused_gdn_step_norm
under the appropriate native settings. Thus the proposed fusion is partly
already implemented. native_gr_postops is not a freely interchangeable GDN
output epilogue; the full dependency order matters.

The Qwen3.6 path really allocates FP32 K/V, confirmed in q36_engine.cu and
docs/QWEN36.md. Quantized caches are a plausible separate project, but changing
an allocator alone would mismatch writes, reads, attention, verification and
session lifecycle. No dtype substitution was made.

Routing the next layer depends on the current layer's computed hidden state.
A doorbell or larger graph does not remove that dependency. Speculative routing
would need prediction, misses and rollback to be included in correctness and
timing. Likewise N=8 MMA padding is not justified by a coincidence with Spin(8):
four valid rows occupy half an eight-row tile, and conversion/launch costs must
be measured. These are unqualified hypotheses, not adopted improvements.

Primary sources checked on 2026-11-02:
https://arxiv.org/html/2412.06464v1 (gated-delta update and generalized factors)
https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/l2-cache-control.html
(persistence semantics and device limits)
https://nvidia.github.io/cudnn-frontend/mxfp8-scale-factor-128x4-layout/
(MXFP4 block size 32; NVFP4 block size 16, distinct formats)

## Measured outcome

Final arithmetic flags match the source-specific CMake choices: --use_fast_math
on native_gdn and native_gdn_preprocess; no fast-math flag on fused_gdn or the
test oracle. CUDA compiler 13.3.73, MSVC 14.44.35207, sm_120; runtime/driver
reported 13050. The first all-fast-math build is retained as exploratory only.
Its CUDA-header C4819 warnings were resolved by /utf-8 in the build script.

Two final measurement runs (r2/r3), 15 rounds each, alternating forward/reverse
mode order. Per-layer medians in microseconds:

| Workload | Original recurrence | Candidate recurrence | Candidate + separate norm | Existing fused norm |
| --- | ---: | ---: | ---: | ---: |
| One state buffer, r2 | 60.957 | 8.450 | 9.341 | 6.657 |
| One state buffer, r3 | 34.464 | 8.443 | 9.352 | 6.620 |
| 48 state buffers, r2 | 116.830 | 32.012 | 27.038 | 17.048 |
| 48 state buffers, r3 | 119.913 | 24.267 | 33.297 | 16.865 |

The 48-buffer case is a synthetic 144-MiB cache-pressure test, not a claim that
this model has 48 GDN layers. Shared q/k/v inputs isolate recurrence and are not
a complete model workload. Copies, warmup and graph capture are excluded from
CUDA event timing. All raw samples, including outliers, are retained.
Separate-norm and recurrence rows run independently; external interference can
make their medians non-additive.

Candidate/original recurrence paired speed ratios were 3.14 and 3.85 at 48
buffers (within-run bootstrap median intervals [2.77,3.31] and [3.37,4.24]).
GPU utilization before/after the final runs ranged from 68 to 93 percent;
other workloads were neither stopped nor identified through private command
lines. These are contested-device observations, not exclusive-device or
end-to-end performance qualification. Bootstrap cannot remove this confounder.

Crucially, candidate plus norm is slower than the existing fused path. The
paired fused/candidate ratios at 48 buffers were 0.632 and 0.590. Therefore
DO NOT recommend --no-fused-gdn to accelerate ordinary use. The new option is
retained for explicit experimentation with the separate arithmetic contract.
No default setting or installed engine was changed.

## Validation receipts

The full test passed four head geometries: (1,1), (2,6), (16,48), (17,51).
There were 32,32,256,32 varying-input updates respectively, checking every
output and state bit after every update. Three replays of seven-step CUDA
graphs also matched. Fourteen invalid-argument cases per geometry covered
null stream/state, aliases, misalignment and invalid geometry.

An independent FP64 oracle checked the first 16 steps of each full case:
maximum absolute state error 1.16377466e-7, output error 1.63454427e-8.
Acceptance was abs_error <= 2e-5 + 2e-5*abs(reference), fixed before execution.
The existing default kernel body was compared with HEAD and is text-identical.

Compute Sanitizer --selftest --quick: memcheck 0 errors; racecheck 0 errors,
0 warnings; synccheck 0 errors. All ran to exit 0. The quick sanitizer workload
is smaller than the 256-step normal test. clang-format dry-run/Werror passes
on the new C++ harness; Python py_compile and the math/measurement analyzer
pass. No production code or assertion threshold was altered after the results.
The later harness formatting is whitespace-only; the final binary is rebuilt.

## Reproduction

From the checkout, build/run with:
powershell -File tools/benchmark_native_gdn_coalesced.ps1
Use -SelfTest for correctness only, or -Quick for a short smoke run.

The separate runtime experiment needs both --native-gdn --no-fused-gdn and
STRATA_NATIVE_GDN_COALESCED=1 in the launching process environment. It is sampled
before capture; existing graphs retain their selected kernel. Remove the
environment variable or set it to 0 for rollback. This option does not affect
the usual fused path, Qwen3.6's separate engine, PrismML or TurboQuant.

Analyze raw JSONL:
uv run --no-project --python 3.12 tools/analyze_gdn_experiment.py <run.jsonl>

## Changed files, limits and next action

Changed native_gdn.cu and its public header; added the production-linked
benchmark, Windows build wrapper, math/statistics analyzer, this implementation
log and small benchmark evidence files. No existing owner work was reverted.

Not run: complete engine rebuild, real-model quality/tokens-per-second,
HIP/SYCL/Metal, other GPUs, pinned ggml independent parity (its bench/micro
sources are absent), Python black/flake8 (not part of the available project
runtime). The standalone build compiles the changed production CUDA translation
unit and the actual two comparison components. This is not release validation.

The next useful performance task is a profiler-backed full-model run when the
GPU is available, determining the actual share of expert transfer, GEMV,
attention and recurrence. Amdahl's law bounds total speedup to
1/((1-f)+f/s) for improved runtime fraction f and local speedup s. If this
separate kernel is bypassed by fusion, f=0 for ordinary use.

Self-review-event: qa_defect. Evidence: the initial comparison compiled the
existing fused source with fast math unlike the main CMake settings. Decision:
correct the task-specific build wrapper and retain both initial and final
receipts; no governance, memory or automation updates are warranted. The
comparison against the already-fused path prevented a misleading general
speedup claim. Broader edits and automatic default promotion were rejected.


Final rebuild exited 0. Environment values 1, 0 and invalid each passed the quick selftest; the calling process environment was restored. Raw final evidence is in bench/results/2026-11-02-rtx-5060ti-gdn-coalesced. Final source and executable hashes are in receipt.json. No commit or push was made.

## Follow-up route clarification

The later native-model investigation found that native packs use the verifier's
`gdn_step_norm_multi` in `src/kernels/cuda/verify_kernels.cu`. The separate-kernel
switch and `--no-fused-gdn` do not redirect that verifier route to this candidate.
The standalone speedups therefore apply only to callers of `native_gdn_step`,
not to ordinary native-pack serving. Further mathematical counterexamples,
additional measurements and profiling outcomes are recorded in
`_docs/2026-11-02_gdn-followup-audit_Codex.md` and the evidence `followup/` directory.
The original receipt is an immutable record of the earlier experiment; the
analyzer was subsequently extended, with its new hash recorded separately.