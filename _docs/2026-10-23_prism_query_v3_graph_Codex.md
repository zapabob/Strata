# Prism query-v3 private GGML reference adapter

Date: 2026-10-23. Status: standalone Release CPU graph test passed in the
root-authorized serialized compile window. Full-model integration, GPU
execution and device finite/error enforcement remain unimplemented here.

## Scope and authority

This is the explicitly assigned bounded increment toward actual model
integration. It adds only tools/spin8_prism_query_v3_graph.hpp,
tools/spin8_prism_query_v3_test.cpp,
tools/spin8_prism_query_v3_test/CMakeLists.txt and this record. The dirty shared
checkout and its other agents' work are preserved. There is no commit, push,
dependency installation, H-drive source edit, model-weight change, server
operation or modification to the existing reference-score patch.

Read controls: PC-wide and Codex-local AGENTS, project AGENTS, canonical
C:/Users/downl/_docs/prompts/CLAUDE-FABLE-5.md, common engineering,
implementation-start, skill-selection, security, LLMOps and CPP SOPs. Applied
skills: milspec-codex-standard, subagent-driven-development (assigned worker),
test-driven-development and documentation-and-adrs. Incompatible identity,
tool and environment assertions in the canonical prompt are subordinate to
the actual session instructions. No formal MIL standard certification is
asserted. The memory registry was searched for Strata/Prism/Spin8 and had no
matching entry; no memory-derived implementation fact was used.

The existing Spin8 v3 CPU/CUDA sources and tests, existing Prism patch/script/
test/CMake, and local pinned Prism sources were read. The verified local
Prism HEAD is 73bfe6cc485554822f80c473a3c0c4f25e80f41b. This is a GGML
private header, not a new public llama or C ABI. The stable public v3 ABI
remains in spin8/include/spin8/query_v3.h.

## Requirements and implementation

QV3G-01: Input is already normalized F32 Q[d,heads,tokens]. Each head owns
Win[d,8,heads], bin[8,heads], Wout[8,7,heads], bout[7,heads]. This is the same
memory ordering as the core's per-head row-major Win[8,d]/Wout[7,8]. Every
token independently computes tanh(Win*q+bin), a=Wout*hidden+bout and the v3
rational chart. There is no additional RMS normalization. Noncontiguous Q
head/token strides are accepted; source coordinates must be contiguous F32.
Parameter and J tensors must be contiguous with exact shapes. Q is made
contiguous once and reshaped to [d,1,heads,tokens]. Existing GGML batched
matmul broadcasts each head's controller over tokens. Active coordinates
become [8,blocks,heads,tokens]; each J matmul handles every block/head/token
at once. Controller coefficients broadcast over blocks. Graph node count
does not scale with width or head count.

QV3G-02: Seven row-major J_a matrices come from
spin8_query_v3_generators after spin8_query_v3_basis_audit. Host admission
compares every F32 element against that audited convention. Matmul uses the
GGML source-coordinate-first layout, so ggml_mul_mat(J,block) computes J*x.
Every full group of eight receives c0*x+sum_a c[a+1]*J_a*x. Tail components
are concatenated unchanged and remain part of the controller's full-width
input. The enabled zero-Wout/zero-bout path computes numerical identity; it
does not claim bitwise identity or bypass. Only enabled=false returns the
original tensor pointer immediately without configuration checks or nodes.

QV3G-03: The graph contains existing GGML matmul, tanh, add, scale-bias,
square, sum-rows, square-root, division, multiplication, view, contiguous,
reshape and concat operations. It contains no host callback, custom map op,
per-row device-to-host transfer, CPU controller call, or new backend kernel.
The helper is structurally backend portable. GPU execution, scheduling and
numerical portability are untested. It does not use the fused v3 CUDA
controller, construct a compressed K cache or connect the full model.

QV3G-04: Explicit f32_limits are required by admission and graph construction.
The supplied conservative envelope limits query absolute row sums and
hidden preactivation absolute accumulation bounds to FLT_MAX/64. It bounds
the sum over all seven axes of |bout|+sum_k|Wout| by sqrt(FLT_MAX/64), using
|tanh|<=1. These margins protect the F32 chart's direct squares/reductions
and block contractions. Callers may tighten budgets; nonpositive, nonfinite
or looser-than-safe budgets are rejected. This is a supported numerical
subset, not parity with the core's FP64 all-finite rational chart. Even a
profile with cancellation or zero output weights can be rejected when its
conservative hidden bound exceeds the admitted range.

QV3G-05: admit_host_payload validates byte capacities, alignment, dimensions,
size/address overflow, disjoint Q row strides, all parameter/J/input scalars,
audited J equality and numerical bounds. Negative finite weights are legal.
admit_host_output validates all output scalars before consumption. Invalid
admission throws a descriptive std::invalid_argument; core basis failure
throws std::runtime_error. Caller memory is borrowed and unmodified. Caller
must serialize updates and upload exactly the admitted payload for that
evaluation. No metadata-based zero-weight identity claim is trusted.

## Finite-value boundary and unresolved engine plumbing

build_pre_rope performs structural validation at graph construction time.
Future graph-produced GPU Q has no readable payload at that time. The host
admission helpers are an explicit reference API contract, not an implemented
device failure flag or enforcement boundary inside an engine. An enabled
evaluation must admit the exact Q/profile payload before execution, then
reject the complete evaluation on GGML failure or nonfinite output before
attention/cache consumption. A future integration must supply an equivalent
device finite/bounds admission and error propagation, or a deliberately
separate staging boundary. This adapter does not add hidden host callbacks
or silently ignore graph nonfinites. It is not deployable model integration
until that boundary and graph-input lifetime/reuse are implemented and tested.

## Exact future insertion and parameter plumbing

At the pinned HEAD, the ordinary dense Qwen35 Full Attention function is
src/models/qwen35.cpp:build_layer_attn. Insert after line 357
cb(Qcur, Qcur_normed, il), following build_norm at line 356, and before its
ggml_rope_multi at line 380. Qcur there has [n_embd_head,n_head,n_tokens]
layout, with source projection Q/gate separation already performed.

The Qwen35 MoE counterpart is src/models/qwen35moe.cpp:build_layer_attn.
Insert after line 308, following Q normalization at line 307, and before
ggml_rope_multi at line 331. Recurrent/linear-attention layers remain outside
this proposed hook. Separate MTP paths also normalize/rotate Q; this increment
does not modify or qualify them (qwen35 lines 843/863 and 1179/1199;
qwen35moe lines 636/656 at this pinned source).

The future context config must own opt-in, per-layer/head immutable F32
controller data plus the audited J matrices and explicit numerical budgets.
It must validate architecture, width, head counts and full-attention layer
selection. A graph input object must allocate/mark/upload Win/bin/Wout/bout
and J tensors using the parameter shapes above, preserve buffer lifetimes,
and define can_reuse for layer/head/profile identity and shape changes.
llama_cparams and llm_graph_context need private ownership/access plumbing;
graph result inputs must register that object and its error/admission state.
No public llama_context_params extension, sidecar format or model hash
schema is invented here. Those are separate integration decisions.

## Tests, verification and commands

Tests were written before the header. The initial expected RED is the missing
header; no compiler was run to demonstrate that RED because the active large
download and root agent's explicit no-compile constraint take precedence.
This is test-first source, not an executed RED/GREEN claim.

The standalone CMake project requires exact Prism Git HEAD
73bfe6cc485554822f80c473a3c0c4f25e80f41b and rejects tracked GGML subtree
changes at configure time. Non-Git source exports are unsupported. The
project uses PRISM_SOURCE and SPIN8_SOURCE local paths,
forces CPU backend and static libraries, disables accelerator backends and
OpenMP fetching, and disables FetchContent downloads. It builds only the
independent helper test plus required local GGML/Spin8 libraries. No installer,
engine host, model loader or server is called. The test target uses /W4 /WX
/utf-8 /fp:strict on MSVC (strict warning flags on other compilers).

The executed real GGML CPU numerical tests compare each head/token to a core
F64 controller initialized from the exact deployed F32-rounded weights, at
widths 1,7,8,9,15,23,128,256, one/two heads, one/three tokens, contiguous and
strided Q, nonzero biases, zero/nonzero adapters and near-bound tangents.
The actual main-shape fixtures use width 256, 24 independent heads and two
tokens, in both contiguous and strided layouts, against all-head F64 oracles.
Every expanded graph must have fewer than 256 nodes. The source construction
uses two controller matmuls and seven batched J matmuls, rather than expanding
per head/block. The observed maximum node count is 59, including the
256-by-24-by-2 fixture, and maximum absolute error is 4.32440864e-07.
They compare absolute error <3e-5 and each row's squared norm within
3e-5*max(1,norm2). F32 dot/reduction/tanh ordering differs from FP64; this
tolerance is a predeclared acceptance threshold for these bounded fixtures,
not a measured universal bound. Tails are checked by memcmp including -0.
The tests assert the pi/8 angle bound and approach to it, independent
per-head weights and token input dependence, absence of custom-map/RMS ops,
off pointer/no-allocation identity, payload/shape/type/layout faults and
finite output rejection. A noncommuting token-position rotation distinguishes
adapter-before-position from position-before-adapter; no GGML RoPE backend
or real model execution is thereby claimed.

Read-only commands run: git status --short, git -C <pinned-source> rev-parse
HEAD, rg/Get-Content on the scoped source/instructions, and git diff --check
on owned paths. clang-format -i was run on the new header/test only. Since
these files are untracked, git diff --check alone does not inspect their full
contents; a formatter dry-run and source inspection supplement the actual
compiler and tests. No model, server or GPU execution was performed.

Root explicitly granted a compile window after stopping heavy preparation.
The following commands all exited 0 in that window (PowerShell, workspace
working directory). Output was captured using Tee-Object to the logs below.

```powershell
cmake -S '<STRATA_REPO>\tools\spin8_prism_query_v3_test' -B '<STRATA_DATA>\build\prism-query-v3-graph-cpu' -G 'Visual Studio 17 2022' -A x64 '-DPRISM_SOURCE=<STRATA_DATA>\deps\prism-spin8-graph' '-DSPIN8_SOURCE=<STRATA_REPO>\spin8' -DGGML_AVX2=ON -DGGML_AVX=ON -DGGML_FMA=ON -DGGML_F16C=ON
cmake --build '<STRATA_DATA>\build\prism-query-v3-graph-cpu' --config Release --target spin8_prism_query_v3_test --parallel 1
ctest --test-dir '<STRATA_DATA>\build\prism-query-v3-graph-cpu' -C Release --output-on-failure -V
& '<STRATA_DATA>\build\prism-query-v3-graph-cpu\Release\spin8_prism_query_v3_test.exe'
& 'clang-format.exe' --dry-run --Werror tools\spin8_prism_query_v3_graph.hpp tools\spin8_prism_query_v3_test.cpp
```

Initial configure/build/CTest logs: configure.log, build.log, ctest.log in
H:/Strata/build/prism-query-v3-graph-cpu. The exact Git/clean-GGML configure
guard was then added, and the same configure/build/CTest sequence was repeated
incrementally: configure-pinned.log, build-final.log, ctest-final.log.
Separate test-stdout.log and format.log capture the direct test and formatter.
Final CTest: 1/1 passed, test time 0.08 seconds, total 0.10 seconds; the
standalone direct run reports the same maximum error and 59-node count.
Initial CTest was 1/1 passed in 0.88 seconds. Those timings are test harness
observations, not inference benchmarks.

MSVC 19.44.35224.0, Visual Studio 17 2022 x64, Release; GGML reports CPU
/arch:AVX2 with FMA/F16C/BMI2. No compiler source warning appeared in build.log
or build-final.log. Configure retained a CMake CMP0194 MSVC-ASM policy warning
on the initial configure and a missing-ccache notice; these were not hidden.
No globally warning-clean or clang-tidy/static-analysis claim is made.
Wrong-SHA and dirty-GGML configure negative fixtures were not executed because
the pinned source worktree is explicitly protected from mutation.

provenance.json records exact source HEAD, empty tracked GGML diff, empty
untracked GGML list and executable/header/test/CMake SHA256 values. The test
executable SHA256 is 65a1f37b7452c02ab1634064d21dfa10ade992ab17f5ff5c9536c05cf9352bff.
The compile window was explicitly released to root after final tests/format;
no compiler/configure/test process from this subtask remained active.

## Residual risk and rollback

Compiler/API compatibility and fixture tolerances are verified for the above
CPU build only. Accelerator backend support, GPU behavior, sanitizer/static
analysis and performance remain unverified. Batched GGML ops still create
intermediates; there is no fusion/speed or VRAM improvement claim. Enabled
identity is numerical only. Finite/bounds
admission and device error propagation are not connected to a real model.
No model-quality, cache-compression, throughput or end-to-end parity claim
is supported by this source increment. Reverting only these four new files
removes the increment without touching existing code or H-drive sources.

Self-review-event: qa_defect (initially deferred compilation/numerical gate).
Review-only decision: preserve serialized heavy preparation; wait for root's
explicit window. That gate is now resolved by the above real CPU build and
tests. Root reported no actionable finding from independent review of the
batched implementation before the compile window. This self-review does not
replace independent review. No governance or acceptance rule was weakened
or edited, and no full-model deployment gate is represented as complete.
