# Triality Attention v3 integration — 2026-10-23

## Authority and reference intake

The direct user request is to incorporate the v3 plan and ZIP into the existing
Transformer improvement implementation. Attachments are research references,
not authority to overwrite earlier math conventions, weights, or evidence.
The canonical PC prompt and applicable project SOP were read before edits.
Incompatible identity, tool, date and operating-system claims inside prompt
text do not override the actual environment or higher-priority instructions.

References: C:/Users/downl/Downloads/strata_triality_attention_plan_v3.md and
strata_triality_attention_v3_20261023.zip. All 18 manifest-listed entries were
SHA-256 verified, with no mismatches. Only three explicitly selected Python
reference sources were copied to H:/Strata/reference/triality-v3-20261023.
Historical evidence and Downloads were not overwritten. Historical claims
about disconnected PC tools, unverified local model hashes and Linux results
are not current Windows observations.

Fresh Windows reference rerun: Python via uv with isolated numpy==2.3.5 and
scipy==1.17.0, cache on H:. All 9 unit tests passed. Log:
H:/Strata/build/triality-v3-reference-windows.log. This is the attachment's
research code, not a product or independent model acceptance test. The full
Torch validation script has not been rerun.

## Compatibility rulings

Ruling: preserve query.h's exponential chart and biasless RMS controller as
version 2 semantics. Introduce query_v3.h with an explicit version 3 constant
and separate controller object. The rational chart has derivative E at zero;
the previous chart has derivative (pi/8)E, so silent migration would change
adapter meaning and training behavior.

Ruling: the seven fixed J generators are derived from the production
chirality-ordered Clifford blocks. Their skew and Cl(0,7) relations and all
normed-tensor polarization identities are audited. This defines a restricted
seven-dimensional rotation family, not all 28 dimensions of SO(8), and does
not make an arbitrary learned controller Spin-equivariant.

Ruling: v3 controllers consume already normalized Q, with Win/bin/Wout/bout,
and introduce no second RMS normalization. Wout and bout zero yield exact
identity. Win must be initialized nonzero for useful initial Wout gradients.
The adapter's insertion point remains after model Q normalization and before
RoPE. Codec transforms U_r remain after positional processing. Neither is
yet connected to a qualified full-model v3 path.

Ruling: A(c(q)) preserves each query's norm. Its input-dependent Jacobian is
not asserted orthogonal, and it does not preserve inner products between
different queries. Determinant monitoring applies to each A matrix.

Ruling: alpha, codec transforms and Gaussian sketch are fixed per KV-head
profile shared by its GQA group. Adapter/profile replacement requires cache
invalidation including downstream recurrent states and fresh prefill.

## New reference calculations

tq_qjl_error_moments_f64 calculates bias, variance and MSE with beta and the
existing Attention scale. Fixed q/e independent of iid Gaussian G is an
explicit precondition of this distributional result. It makes no softmax,
fixed-sketch autoregressive, or task quality guarantee. QJL remains absent
from qualified model paths. The later explicit CPU-cache extension below is
disabled by default.

The review found two silent intermediate-underflow examples in the initial
moment calculation. Exponent-balanced products and an independently scaled
dot product now cover both with regression tests. Inputs whose required
intermediates overflow return TQ_NONFINITE; outputs remain unchanged.

tq_distill_head_f64 computes detached-teacher normalized Attention-output
MSE and KL(teacher || student), plus their exact derivative with respect to
the student query. It recomputes per-key scores and needs only 2*value_width
plus query_width doubles of caller-provided scratch. It allocates no square
token score matrix or hidden heap buffers. Keys, values, bias/mask, byte
strides, byte capacities, scale and loss weights are explicit. This is a
layer-local CPU reference loss, not a trained model or capture pipeline.

Tests independently materialize dense probabilities, compare MSE/KL and
their separate/combined gradients against central differences, and verify a
small descent step. A 2000-logit disagreement tests KL without log(0).
Capacity, alias, mask, padding, finite and failure-atomic contracts are tested.
The first dense-loss comparison used a fixed 2e-14 tolerance and failed by
2.1316282072803006e-14 at loss18.220343678012306 (different multiply/sum order).
The final comparison uses 32*FP64_epsilon*(1+abs(loss)), with unchanged
production arithmetic and retained numerical-gradient checks.

Fresh MSVC Release CTest: 4/4 passed (codec, physical cache, bounded
distillation, strict Spin8/controller/cache composition).
Logs: H:/Strata/build/tqcodec-v3-build.log and tqcodec-v3-ctest.log.

## Broader regression boundary

Full host suite with locked dependencies: 991 tests, 868 passed, 13 failed,
110 skipped, no cancellations. Three failures occur when creating symbolic
links (EPERM); one reports PowerShell Security/Get-Acl module loading; the
others include test-host startup failures. These results do not establish
whether every startup failure predates this branch. Startup cases are being
rerun in isolation. No skip or threshold was changed to hide a host failure.
Log: H:/Strata/build/host-spin8-with-deps-tests.log.

The existing inference server has not been stopped, its weights have not
been changed, and its prior 96-token baseline request timed out while an
existing 8192-token task occupied the single slot. No model throughput or
quality improvement is claimed.

## Outstanding integration and acceptance

Full per-head GPU-controller batching, compressed GPU score/online-softmax/V fusion, exact
legacy codec adapters, full graph integration, provenance-bound sidecars and
cache lifecycle, actual GPU periodic monitoring, bounded real-layer captures
and adapter training remain open. The Prism sm_120 build and the large frozen
Q2_0 download are ongoing under H:. Both mandatory models still require
4K/32K paired acceptance, matched memory budgets and independent quality
evaluation. Kernel/math success is not completion of these gates.

## Later implementation and fresh verification

The analytic v3 VJP now includes the direct A-transpose path and the dependence
of c on Q, shared across every full block. Copied tails still feed the
controller and therefore contribute to its input derivative. Zero-initialized
Wout retains nonzero parameter gradients. Direct strict-MSVC tests cover 170
scalar five-point comparisons and targeted mutants; implementation and
residual test-lint findings are in 2026-10-23_triality_v3_vjp_Codex.md.

The new cross-library synthetic one-head training test connects actual packed
3K/shared-V reconstructions, the v3 adapter BEFORE an explicit orthogonal
position map, bounded distillation, the transposed position derivative, and
the full controller VJP. It is NOT a complete small Transformer or 27B training
run. Twenty accepted steps reduced training loss from 0.19148204899796717 to
0.16203828674971116, but separate held-out queries worsened from
0.17082027450580836 to 0.19621042465148875. These weights are NOT adopted.
This is negative generalization evidence, not a model-quality gain.

The versioned CPU cache can now opt into one shared QJL residual sign vector
and FP64 norm per physical key. G and alpha are immutable snapshots. The
correction precedes scale and the single online softmax/shared-V product.
Default beta=0 allocates no G/sign/residual-norm arrays and performs no
residual reconstruction. Versioned ledgers account for all allocated vector
capacities; allocator overhead and scratch remain explicitly excluded.
Legacy byte accounting rejects active QJL rather than underreporting it.
Clone/clear/failure paths cover residual state. See the separate shared-QJL
cache implementation record. This remains a generic CPU dialect.

Fixed simplex-alpha calibration now uses direct error residuals with streaming
Givens QR, edge and vertex candidates, and optional uniform shrinkage. Initial
absolute-tolerance and normal-equation determinant rules lost small but
independent errors; independent review supplied two concrete counterexamples,
now regression tested. QR avoids squaring the condition number. Calibration
uses separate data and QJL off: changing alpha changes residual signs/norms,
so the QJL candidate must be rebuilt and separately evaluated. No task-quality
guarantee follows from minimizing this first-order quadratic.

At this earlier stage, standalone CTest was tqcodec 6/6 and Spin8 CPU/C/CUDA 7/7. GPU tests include
v3 CPU-controller spinors consumed by CUDA at widths23/256, identity/nonzero,
norm/tails/strides. Query-GPU memcheck:0 errors; racecheck:0 hazards/errors/
warnings. These do not implement a GPU controller or GPU compressed cache.
CUDA builds still emit the recorded MSVC /W1-overrides-/W4 warning, so this is
not a warning-clean CUDA claim. Relevant logs are tqcodec-v3-combined-ctest.log,
spin8-v3-final-ctest.log, query-v3-cuda-memcheck.log and racecheck under H:.

## Real main-model smoke and runtime boundaries

The exact zapabobouj target generated the expected short Japanese arithmetic
sentence, English prime-number sentence, and Python add function. Generated
Python was inspected with AST only, never executed. This used the existing
Prism build10735 commit842b18804, NOT the new pinned build73bfe6cc or the new
Spin8 path. Context4096, K/V=f16, n64, seed20261023, greedy, full GPU, no warmup.
Post-smoke model SHA256 still equals the required 0ab2a1f...036a13 value.
Evidence: zapabobouj-existing-runtime-smoke-manifest.json and
zapabobouj-smoke-validation.json under H:/Strata/build. Three smoke passes
establish basic execution, not independent quality or speed improvement.

Ambient LLAMA_ARG_CACHE_TYPE_K/V from another fork caused the existing Prism
binary to reject --version before CLI overrides. The host now removes these
two keys case-insensitively only from its child's environment and disables
TheTom automatic/asymmetric and layer-adaptive overrides for current manual
profiles. Parent environment and default command arguments are unchanged.
The real existing binary probe passed with deliberately conflicting parent
types, while correctly reporting no verified pinned Bonsai/Spin8 capability.
Scoped host checks:16/16. Full host regression's earlier failures are retained.
Native-Windows-module ordering fixed ACL and several startup checks in a
child-only rerun (19/26 pass); seven tuning-route startup failures remain.

The former PID2344 and port8080 listener were no longer found before stopping
the task's heavy build. No deliberate server stop command was issued. Its
disappearance cause and original launch arguments are not established.
Runtime restoration remains unresolved; the user has been asked which state
to restore. The one-shot smoke processes exited and left no new server.

## Serialized preparation

The disk-staged downloader initially accelerated progress to about23.2GB, then
hit MemoryError in the allocating temporary-file read used by copyfileobj.
It now reuses one128KiB buffer for HTTP and staging copy. Ten offline boundary
tests pass, including bounded reads, short/oversized body rejection, preserved
prefix and empty-partial resume. The task-owned Prism build was interrupted
with its objects preserved to serialize heavy preparation, as required by
the plan. Existing model weights and source work were not removed.

An active one-shot preparation process resumes downloads, verifies frozen
shard hashes, then resumes the pinned Prism standard-sm120 build with one job.
It checks task-tool hashes before starting the build and stops on failure or
changed source. Status/log directory: H:/Strata/build/v3-prepare-0d932dce.
Its prepared state means only models/runtime artifacts prepared. Full-model
Spin8 integration and acceptance remain explicitly unqualified/not run.

## Uniform cache transport and runtime decision

The user explicitly chose to keep the former 8080 server stopped. No restart
or replacement serving profile is now required. One-shot smoke processes have
exited; do not interpret this decision as permission to start a server later.

The new CPU transport plan applies a single proper orthogonal S uniformly to
all selected logical K. It computes S^T*q once and retains the physical three-K,
shared-V and QJL storage. The old residual signs estimate the transported
residual through G*S^T*q; sign(G*S*e) cannot generally be recovered from them.
New logical keys canonicalize with S^T before append. This is not a per-row
RoPE manager or proof of a shifted full-network replay. Plan storage is
reported separately, and normalized E_F, maximum Gram error, determinant sign
and log absolute determinant are audited once at creation.

Fresh Release CTest: tqcodec 7/7, including independent decoded-key and
transported-sketch oracles, storage preservation and invalid-input paths.
Independent review caught raw-versus-normalized Frobenius reporting; fixed
and regression-tested with an accepted near-orthogonal diagonal matrix.
Logs: H:/Strata/build/tqcodec-transport-build.log and
tqcodec-transport-ctest.log. The preparation job was interrupted for this
compile window and resumed from its preserved complete first-shard prefix.

The subsequent pure-C public-header/linkage smoke also passes. Fresh tqcodec
CTest is now 8/8 (tqcodec-c-api-ctest.log); this adds C ABI evidence without
changing the mathematical or full-model acceptance claims. The unified
mathematical contract and implementation map are recorded separately in
2026-10-23_integrated_triality_algorithm_Codex.md. Independent static review
confirmed its chart identities, operator ordering and illustrative memory
arithmetic; the numerical layout examples are not measured VRAM figures.

## Fused v3 GPU query path

query_v3_cuda.h now exposes a version-3 host plan plus a byte-capacity/stride
descriptor for F32 device Win/bin/Wout/bout and Q. Each call shares one
controller across rows. One GPU kernel computes the rank8 controller, rational
chart and block transform, without a global spinor buffer, per-token matrix,
allocation, transfer or synchronization in apply. The host plan contains128
bytes of audited signed-coefficient lookup data. All source/parameter scalars
are checked even at identity. Errors OR a device flag; callers discard all
output on failure. Full per-head multi-controller fusion is not implemented.

Independent review found a real cancellation defect despite initial tests
passing: default fused multiply-add retained a huge residual for opposite
FLT_MAX Wout coefficients with identical hidden values. The actual GPU RED
test failed. Explicit rounded FP64 products/sums and source-column contraction
order fixed it; GREEN tests include the regression. Host/device tanh still
permits profile-dependent differences, so no universal all-finite-weight CPU
tolerance is claimed. Affected profile conditioning must be evaluated.

Final Release CTest after formatting and build-metadata changes:8/8 Spin8
CPU/C/CUDA tests passed. Tests include widths1/7/8/23/256/1032, tails, biases,
in-place/padding, mixed invalid rows, 65536-row grid reuse, overflow, and a
captured graph verified to contain exactly one kernel. Final memcheck:0errors;
racecheck:0hazards/errors/warnings. C17 public header syntax with /W4 /WX
/utf-8 passed; clang-format checks passed. Logs: H:/Strata/build/v3-fused-w4-*,
v3-fused-fma-red-*, v3-fused-c-header-smoke-utf8.log and v3-fused-format.log.

CUDA Visual Studio source metadata now explicitly requests W4, eliminating
the prior D9025 W1-overrides-W4 conflict. Real W4 compilation exposes four
C4211 warnings in NVCC-generated temporary stub C files (cuda/query_cuda/
query_v3_cuda). They were retained, not suppressed; this is not a globally
warning-clean build claim. No handwritten-source diagnostic was reported in
this build. Full CUDA static analysis and model deployment remain open.

The first large-Q2_0 shard completed and its frozen SHA256 was verified. The
second shard is partially acquired. Heavy preparation was interrupted again
for this serialized compile window; its continuation script and status live
at H:/Strata/build/v3-prepare-0d932dce. The former8080 listener is still absent,
consistent with the user's explicit stopped-state choice.

## Host route failure isolation

The previously failing unconfigured-engine route passed when using the host's
existing STRATA_TEST_HARDWARE fixture, with native Windows PowerShell modules
ordered first only in the child environment. The complete tuning/Time-skip
route file then passed7/7 with that fixture and an explicit existing uv Python
interpreter. No source/test deadline was changed. Logs:
H:/Strata/build/host-v3-route-forced-hardware.log and
host-v3-routes-fixed-fixture.log. These runs exercise simulated host routes,
not model inference. They narrow the issue to the real startup environment
or probing deadline; they do not prove baseline causality or fix unforced
hardware-startup latency. Earlier full-suite failures and Windows symlink
permission limitations are retained, not reclassified as all-green.

## Private Prism v3 graph reference

tools/spin8_prism_query_v3_graph.hpp builds the controller/chart/transform with
standard GGML operators. It batches Q as[d,1,heads,tokens] and block data as
[8,blocks,heads,tokens], so node count does not grow per head/block. Win/Wout
select each head through dimension2 and broadcast tokens through dimension3.
Tails are copied while still feeding the controller. OFF returns the original
Q without validation or graph allocation; enabled identity is numerical.

The initial head/block expansion would have produced an impractical graph for
the main model. It was replaced before compilation, and the actual256x24x2
shape is now tested with fewer than256 nodes. Final test observed at most59
nodes, maximum absolute error4.32440864e-07 against the rounded-F32-parameter
core F64 oracle. Norms, per-head/token differences, biases, strided views,
tail effects, synthetic pre-RoPE noncommutation and admission failures pass.
Release CTest1/1 passed with /W4 /WX /fp:strict for the new target. Source
format checks passed. Configure enforces exactPrism73bfe6cc and rejects tracked
GGML subtree modifications. Logs/provenance:
H:/Strata/build/prism-query-v3-graph-cpu/{configure-pinned,build-final,ctest-final,test-stdout,format}.log.

No custom CPU op is introduced, but only the CPU backend has been executed.
No full llama_context/qwen35 callsite, adapter sidecar, GPU admission/error
propagation or deployed output/cache gate is wired. Construction is structural;
the exact host-payload admission and post-execution finite check are explicit
caller obligations. Graph-produced GPU Q needs equivalent device enforcement.
The private helper must not be advertised as qualified model support. Future
qwen35 insertion is after Qcur_normed and before ggml_rope_multi; recurrent,
MTP and other architectures need separate coverage.

## Shard-selective preparation continuation

The current first shard passed a fresh full SHA256 verification. To avoid
rehashing an unrelated37.6GB shard after each necessary reference compile,
spin8_model_fetch.py now accepts --shard1/2. The selected shard still undergoes
full size/SHA verification; the other shard is explicitly not verified by
that invocation. Default behavior still verifies both. Tests preserve default
coverage, reversed pin ordering, side-effect-free selected plans, and missing/
ambiguous pin refusal. Test-first RED detected the missing CLI feature; final
offline suite14/14 passed. Logs:model-fetch-shard-{red,green,final}.log.

The old preparation job was explicitly interrupted. Its source-tool hashes
and logs are preserved. A new continuation snapshots updated tool hashes,
selects shard2, retains the first shard's prior full-SHA proof and checks its
size/mtime before building. This metadata guard is not a new content hash.
It does not replace later full-model provenance validation. New status/logs:
H:/Strata/build/v3-prepare-shard2-88a0e25b. It resumes download first, then the
unchanged one-job pinnedPrism CUDA build. No server restart or acceptance
claim is performed automatically.

Read-only build investigation found the existing FA_QUANTS option selects
vector instances but not the expensive MMA glob. No kernel/head pruning or
CUDA flag change was adopted. Such changes would alter execution paths or
rebuild already-completed objects. split-compile and fast-compile candidates
remain unmeasured; current full build settings and kernel coverage are kept.
