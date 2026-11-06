# B2 bounded CUDA attention_v2 evidence

## Goal, scope and start gate

Implement the standalone actual CUDA attention_v2 reference on e959b84f, branch
feat/spin8-cuda135-20261106. Owned paths are the new CUDA header, implementation,
test, CUDA guide, this log and necessary additive spin8/CMakeLists.txt entries.
B1 ABI, v1 numerical sources and parent docs/plans/logs are preserved.

Applied the supplied MILSPECLLMOps skill and Common, Start Gate, Skill Selection,
Security (caller-memory boundaries), Application Development, LLMOps, C and CPP
SOPs. Read canonical CLAUDE-FABLE-5 context subject to the actual higher-priority
identity, tools, platform and task constraints. Selected test-driven-development
for vertical RED/GREEN. Local B1/v1 source, headers, tests, README and B1 evidence
are the implementation sources. No dependency or external factual claim is needed.

## Requirements and prospective acceptance

B2-ABI: reuse B1 geometry/semantic descriptors in a separate versioned CUDA ABI;
immutable device-bound plan, exact headers, zero reserved, copied mapping and
audited coefficients. B2-MEM: positive checked byte strides/capacities, independent
K/V F32/F16, F32 Q/output, caller workspace, no enqueue allocations. B2-ASYNC:
explicit stream, host enqueue success distinct from completed device status;
global staged commit prevents nonfinite/all-masked publication. B2-MATH: original
scale, required mask, finite optional bias/gate, both softcap orders, one softmax,
actual fixed Spin8/H128 with tails and inverse V before gate. B2-QA: independent
FP64 oracle of actual rounded inputs, absolute tolerance <=2e-5 for both F32 and
F16 predeclared BEFORE runs; host/device sentinel tests, graph and independent
streams, small allocations below 256 MiB and resource floors RAM >=3 GiB,
GPU free >=1 GiB. All phase B, runtime integration and qualification stay pending
separate review.

## Initial observations

Target HEAD verified e959b84fd5de69a6b3090034730ac757e5efc8c6. Initial untracked
entries: parent's `_docs/2026-11-06_spin8-cuda135_Hermes.md` and `docs/plans/`.
Build parent exists; unique b2-opencode-cuda135 directory absent. No ancestor
AGENTS at H:/, H:/Strata or H:/Strata/worktrees; no nested spin8 AGENTS.
Available RAM 8077740 KiB; RTX 5060 Ti, driver 621.01, GPU free 4533 MiB.
No nvcc/cl/MSBuild processes were returned by the initial process check.

## Execution ledger

All commands ran in `H:/Strata/worktrees/spin8-cuda135-20261106`. The build parent
was checked before generation. Build commands checked available RAM >=3 GiB.
The test executable checks available physical RAM and CUDA free memory before
its explicit device allocations and plan creation. A resource failure returns
77 with `BLOCKED`, not a numerical pass. No resource gate was bypassed.

### Configure and actual initial RED

```powershell
cmake -S spin8 -B H:/Strata/validation/spin8-cuda135-20261106/b2-opencode-cuda135 -G 'Visual Studio 17 2022' -A x64 -T 'cuda=H:/Strata/builds/cuda135-comparison-20261106/toolkit-13.5-vs-view' -DSPIN8_ENABLE_CUDA=ON -DSPIN8_BUILD_TESTS=ON -DCMAKE_CUDA_ARCHITECTURES=120 -DCUDAToolkit_ROOT=H:/Strata/builds/cuda135-comparison-20261106/toolkit-13.5-vs-view
cmake --build H:/Strata/validation/spin8-cuda135-20261106/b2-opencode-cuda135 --config Release --target spin8_attention_v2_cuda_test --parallel 1
```

Configure identified NVCC 13.5.37, MSVC 19.44.35224.0, Windows SDK 10.0.26100.0
and MSBuild 17.14.40. The initial caller test was written before the CUDA API.
It compiled through the existing spin8/spin8_cuda libraries and failed at
`attention_v2_cuda_test.cu(1)` with C1083: missing `spin8/attention_v2_cuda.h`.
Only test-target registration existed at this point. This was an actual compile
RED, not a source-pattern assertion.

### Vertical GPU RED/GREEN

The first implementation supported identity F32 attention with actual device
packing, score/value calculation, gating and a separate output commit kernel.
The target build succeeded; the focused CTest passed 1/1, reporting
`PASS attention_v2 CUDA identity` (2.59 seconds for that test). The request used
an explicit nonblocking stream and checked both enqueue and completed status.

The next test slice introduced the independent rounded-input oracle, all seven
widths and differing V, MHA/GQA/MQA, both logit orders with/without softcap, all
four independent K/V dtype combinations, host rejection sentinels, fixed-basis
fixtures, device errors, independent streams and graph capture. The focused test
failed with `Spin8: unsupported; CUDA: no error` at mixed storage. Implementing
F16 decoding independently for K and V made the identity geometry matrix pass.
The same test then failed at `BEGIN actual fixed-basis cases`, because fixed
plan creation was still explicitly unsupported.

Before fixed implementation, tests also added dense Sylvester-parity/matrix
oracles for actual device Q/K/V workspace and original-scale/gate-order negative
controls. Adding exported audited coefficients, real Spin8/H128 transforms and
inverse V before gate made the focused suite pass (567 counted mixed cases).
The later boundary supplement added >128 rows, host-memory rejection, null/
unaligned descriptors, invalid fixed configurations and H128 with zero planes.
It passed with 585 counted mixed cases. No tolerance was loosened.

Repeated focused commands were:

```powershell
cmake --build H:/Strata/validation/spin8-cuda135-20261106/b2-opencode-cuda135 --config Release --target spin8_attention_v2_cuda_test --parallel 1
ctest --test-dir H:/Strata/validation/spin8-cuda135-20261106/b2-opencode-cuda135 -C Release -R '^spin8_attention_v2_cuda$' --output-on-failure -V
```

### Broader standalone build interruption and recovery

An all-target standalone build used a process-local `NVCC_APPEND_FLAGS` of
`--ptxas-options=-v` to obtain resource diagnostics. The prior value was restored
in `finally`; no compiler configuration or numerical flags were changed. This
build completed B2 but the tool's 120-second timeout interrupted compilation of
the existing `cuda_test.cu`. A process check then returned no nvcc/cl/MSBuild.
The first resume encountered LNK1136 on that generated `cuda_test.obj` (invalid
or corrupt file). Other standalone targets built. This was not a passing build.

Recovery rebuilt only that generated test project and its dependencies in the
owned B2 build tree, then resumed the full standalone build with a 300-second
tool timeout. No baseline directory or source file was cleaned/overwritten:

```powershell
& 'C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/MSBuild/Current/Bin/MSBuild.exe' 'H:/Strata/validation/spin8-cuda135-20261106/b2-opencode-cuda135/spin8_cuda_test.vcxproj' /t:Rebuild /p:Configuration=Release /p:Platform=x64 /m:1 /verbosity:minimal
cmake --build H:/Strata/validation/spin8-cuda135-20261106/b2-opencode-cuda135 --config Release --parallel 1
```

Both recovery commands succeeded. The full standalone build includes the small
existing native adapter test target; this is not a full native engine build.
No native engine/model was launched. NVCC-generated `.cudafe1.stub.c` files emit
MSVC C4211 (extern redefined static), including for unchanged v1 CUDA sources.
These warnings remain visible; no source warning suppression or v1 flag change
was added. The build is successful, not warning-free.

### Final regression evidence

```powershell
ctest --test-dir H:/Strata/validation/spin8-cuda135-20261106/b2-opencode-cuda135 -C Release -R '^(spin8_cpu|spin8_attention_v2|spin8_attention_v2_c|spin8_query|spin8_query_v3|spin8_query_adapter|spin8_query_sidecar_python|spin8_c_abi|spin8_attention_v2_cuda)$' --output-on-failure -V
```

All 9 selected tests passed, zero skipped, total 13.89 seconds. These are the
eight existing CPU entries and the new B2 GPU entry. B1 again reported 499
mixed cases and max error `2.2204460492503131e-15`; its pure-C caller passed.
The sidecar entry ran 10 Python tests and passed. Existing CUDA v1/query/native
adapter executables were built but not executed in this slice.

Final B2 reported **585 counted numerical/negative cases**, not 585 independent
CTest suites or 585 oracle-only cases. Its final CTest duration was 3.03 seconds.
Observed maximum absolute errors:

| Check | Maximum | Predeclared limit |
|---|---:|---:|
| F32-only attention output | 9.375579210768592e-7 | 2e-5 |
| Attention with K or V F16 | 1.1920753095751024e-7 | 2e-5 |
| Actual transformed device Q/K/V vs dense FP64 oracle | 1.7763568394002505e-15 | 1e-11 |

Negative controls diverged by `0.270735795` for replacing the original scale and
`3.1511733` for gate-before-inverse. Actual transformed staging differed from
identity by `7.941528`. The transform oracle verifies kernel behavior even though
a common orthogonal basis preserves original-space attention mathematically.

Independent plans and one shared immutable plan worked across separate streams.
CUDA Graph capture, two initial replays, a NaN replay with unchanged entire
output, and a recovered replay passed. Late Q/K/V/bias/gate NaN/+Inf/-Inf,
masked nonfinite bias, late all-masked rows, scale overflow and final F32-range
overflow produced observable device status without output publication. A
387-row case verifies the global commit barrier across CTAs. Host validation
sentinels check workspace/status/output remain untouched before submission.

Tracked peak explicit device allocation was **312098 bytes**, including plan
matrix/mapping, all tensor capacities/guards, full workspace and status across
simultaneously live fixtures. The tiny initial identity fixture was separate and
smaller. Host fixture/oracle buffers are bounded small vectors; no large model
or allocation was used. CUDA runtime/context/graph metadata is not part of the
explicit-allocation counter. A later resource snapshot was RAM 7626316 KiB and
GPU free 4502 MiB; tests also continuously enforced their allocation-time floors.

CTest evidence:
`H:/Strata/validation/spin8-cuda135-20261106/b2-opencode-cuda135/Testing/Temporary/LastTest.log`.
Build/RED/diagnostic outputs are retained in the session tool transcript; this
log records their commands and results rather than inventing separate raw files.

### Compiler resource observation

NVCC 13.5.37 ptxas reported the following for sm_120 Release B2. Every kernel had
**0 bytes stack frame, 0 bytes spill stores, 0 bytes spill loads**:

| Kernel | Registers | Barriers |
|---|---:|---:|
| pack | 22 | 0 |
| transform | 48 | 0 |
| attention | 96 | 0 |
| gate | 28 | 0 |
| commit | 24 | 0 |

No width-sized local array is used. The only explicit transform array contains
eight doubles; H128 state lives in the checked caller workspace. These compiler
observations are not throughput or occupancy qualification.

### Formatting, C header and analysis

```powershell
& 'C:/Program Files/LLVM/bin/clang-format.exe' --dry-run --Werror spin8/include/spin8/attention_v2_cuda.h spin8/src/attention_v2_cuda.cu spin8/tests/attention_v2_cuda_test.cu
```

Final formatting check passed with no output. All edits, including formatting,
used apply_patch. The earlier header-format findings were corrected locally.

The new public header was compiled as C using MSVC `/TC /Zs /W4 /WX`. The initial
check failed because CUDA's external headers trigger anonymous-struct C4201 and
the shell's CP932 decoding triggers C4819. A rerun with `/utf-8` and the toolkit
marked as external (`/external:I... /external:W0`) passed. Project header warnings
remained `/W4 /WX`; this was a C syntax check, not a new pure-C GPU caller test:

```powershell
& 'C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/cl.exe' /nologo /TC /Zs /W4 /WX /utf-8 /Ispin8/include /external:I'H:/Strata/builds/cuda135-comparison-20261106/toolkit-13.5-vs-view/include' /external:W0 /I'C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/include' /I'C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/ucrt' spin8/include/spin8/attention_v2_cuda.h
```

Clang-tidy was attempted, but **did not complete analysis**:

```powershell
& 'C:/Program Files/LLVM/bin/clang-tidy.exe' '--checks=-*,clang-analyzer-*,bugprone-*,-bugprone-easily-swappable-parameters' '--warnings-as-errors=clang-analyzer-*,bugprone-*' spin8/src/attention_v2_cuda.cu -- -std=c++17 -x cuda --cuda-host-only --cuda-gpu-arch=sm_120 --cuda-path=H:/Strata/builds/cuda135-comparison-20261106/toolkit-13.5-vs-view -nocudalib -Ispin8/include
```

LLVM 22's CUDA wrapper requires `curand_mtgp32_kernel.h`, absent from the supplied
minimal toolkit view. It stopped at that missing header (138 warnings before the
error, largely external). No fake header, dependency installation or diagnostic
weakening was used. CUDA static analyzer validation remains open. A requested
cuobjdump resource inspection also could not start because the executable is
absent from that view; the actual ptxas report above supplied the resource
evidence instead. Matching 13.5 Compute Sanitizer was not present in the view;
the PATH tool is 13.3. Sanitizer execution was not attempted with mismatched tools.

## Design and lifetime decisions

The B1 public geometry/request descriptors are reused rather than edited. Plan
creation uses B1's validator with its FP64 selector internally, then exports the
actual audited Spin8 matrix. The plan owns one device allocation holding the
selected FP64 matrix and copied mapping; H128 uses the same FP64 normalized
coefficient convention audited by B1. Startup is allowed to allocate and copy.
The hot path performs only host validation and CUDA submissions.

Workspace is exactly `8*(Q*H*D + K*J*D + K*J*V + Q*H*V + Q*H*K)` bytes: packed
Q/K/V, staged output and full scores. Bias/gate/mask are read directly. Separate
status uses four bytes; each plan adds `512 + 4*H` device bytes. Caller tensor
capacities and runtime overhead are additional. The guide accounts for startup
host copies and audits too. No scores/staging are omitted from the formula.

The returned pair distinguishes semantic errors from CUDA runtime errors. OK
means enqueued. The caller must check stream/event completion and device flags
before consuming output. Numerical failure is whole-output transactional via a
separate commit kernel. CUDA execution failures can interrupt publication and
require discarding the invocation. Plan destruction is caller-serialized after
all stream and graph uses; cudaFree may synchronize. Enqueue has no allocation,
host copy or synchronization. Graphs retain addresses and by-value scalars.

Input-only aliasing is allowed; output/workspace/status must be disjoint from
inputs, descriptors and plan. Span arithmetic and required extents are checked.
Actual accessible allocation sizes, stable inputs, truthful source IDs and live
handles remain caller obligations. Pointer attributes reject unsupported host/
managed/foreign-device memory but cannot validate arbitrary pointer lifetime.

## Exact changed files and preservation evidence

Only these six assigned paths were edited/added:

- `spin8/include/spin8/attention_v2_cuda.h`
- `spin8/src/attention_v2_cuda.cu`
- `spin8/tests/attention_v2_cuda_test.cu`
- `spin8/CMakeLists.txt`
- `spin8/docs/attention_v2_cuda.md`
- `_docs/2026-11-06_spin8-attention-v2-cuda_OpenCode.md`

No shared helper or B1/v1 source edit was necessary. CMake adds the new source,
test and test skip/timeout metadata, retaining existing numerical flags.

```powershell
git diff --exit-code e959b84f -- spin8/src/spin8.cpp spin8/src/attention_v2.cpp spin8/src/cuda.cu spin8/src/query_cuda.cu spin8/src/query_v3_cuda.cu spin8/include/spin8/spin8.h spin8/include/spin8/attention_v2.h spin8/include/spin8/cuda.h spin8/tests/cpu_test.cpp spin8/tests/attention_v2_test.cpp spin8/tests/attention_v2_c_test.c spin8/tests/cuda_test.cu spin8/docs/attention_v2.md
git diff --check
git status --short
```

The preservation diff returned no content and passed. Whitespace check passed.
Git's existing LF-to-CRLF notice for CMake is not a compiler diagnostic. Status
shows only the six owned paths plus the original parent untracked log/plans.

## Self-review

Self-review-event: type=ticket_completed scope=spin8/attention_v2_cuda category=correctness evidence=_docs/2026-11-06_spin8-attention-v2-cuda_OpenCode.md

Self-review-event: type=qa_defect scope=spin8/attention_v2_cuda category=qa-coverage evidence=standalone-build-timeout-and-clang-tidy-blocker

Applied the completion self-review skill and its event/governance references.
Review response is review-only for governance. Expected TDD REDs, the interrupted
build, LNK1136 recovery, generated-stub warnings and incomplete analysis are kept
distinct from passing checks. Added direct transformed-workspace evidence and
multi-CTA whole-output sentinels because final orthogonal invariance and a
single-row flag alone would not establish those properties. Corrected the free
contract to acknowledge cudaFree synchronization. No AGENTS/Skill/SOP changes
are justified; broad governance edits were rejected as outside this task.

## Residual limits

Bounded standalone reference only. Complete phase B, independent SPEC/QUALITY
review, runtime integration and qualification remain pending. No speed or model
quality claim follows from these tests. CUDA static analysis and matching-toolkit
Compute Sanitizer remain unverified. No allocation/runtime-failure injection,
long-context test, concurrency stress, alternate OS/compiler qualification or
multi-device execution was done. Raw allocation provenance and caller lifetime
violations are outside the API's protection.

No real model, full native engine build, process stop, release, install, commit,
push, dependency/global driver change or subdelegation occurred. Existing v1
GPU and native adapter tests were built, not executed. The baseline build tree
was not reused. Next action is independent B2 SPEC then QUALITY review, including
the recorded analysis/toolkit gaps, before any runtime integration. Rollback is
removal of only these five additive files and their additive CMake entries.

## P1 QUALITY request-changes follow-up (2026-11-06)

Independent QUALITY review returned **REQUEST_CHANGES**, P1: constructor used
`cudaMemcpy` from a pageable vector and published the plan without proving DMA
completion. An immediate nonblocking-stream caller could read matrix/mapping
before initialization completed. This is an accepted static API-contract
finding; the earlier 585-case pass does not establish safe publication. Existing
tests allocated invocation workspace after creation, which could mask the gap.

Goal: complete and check the initialization upload before assigning `*out`, clean
up failed creation with `*out` unchanged, and keep synchronization out of enqueue.
Same six B2 paths only. The earlier interrupted resume calls delivered no tool
results or edits. The current resume confirmed the same branch/HEAD and status.
Fresh available RAM was 5363812 KiB and GPU free 4077 MiB, above the unchanged
3 GiB/1 GiB floors. No compiler process was returned. The running GUI and Hermes
are outside this task; no process or installed-app action is needed.

Applied the already-read start gate, canonical prompt, C/CPP and baseline SOPs,
plus DeepResearch for the CUDA API ordering decision and the supplied research
skill. NVIDIA primary references independently checked on 2026-11-06:

- [CUDA Runtime API 13.5 synchronization behavior](https://docs.nvidia.com/cuda/cuda-runtime-api/api-sync-behavior.html): pageable H2D copy return need not mean final DMA completion.
- [CUDA Runtime API 13.5 stream management](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__STREAM.html): a nonblocking stream has no implicit stream-0 dependency; stream synchronization waits for its operations. Stream destruction alone need not wait.

The current pages identify version 13.5 (synchronization page updated
2026-11-02). Initial guessed `/archive/13.5.0/` URLs returned 404; they are not
used as evidence. This is narrow primary-source API research, not a package or
security audit.

Added the behavioral regression before changing production: 32 freshly created
plans, identity and all three fixed views/H128, varied noncontiguous mapping and
all independent K/V dtype pairs. Invocation buffers, output, workspace, status,
stream and input uploads are prepared before creation. The first enqueue is
immediately adjacent to successful creation, with no caller allocation/copy/
resource query/synchronization in between. It checks actual output and device Q
staging against independent oracles. Pre-fix and post-fix observations follow.

### Pre-fix regression observation

The focused target compiled successfully before the production change. At the
run gate, RAM was 6764704 KiB and GPU free 4470 MiB. Command:

```powershell
cmake --build H:/Strata/validation/spin8-cuda135-20261106/b2-opencode-cuda135 --config Release --target spin8_attention_v2_cuda_test --parallel 1
& 'H:/Strata/validation/spin8-cuda135-20261106/b2-opencode-cuda135/Release/spin8_attention_v2_cuda_test.exe' --first-use-only
```

The 32-plan pre-fix run **passed**, reporting Q-staging max error
`4.4408920985006262e-16`. It did not reproduce the timing-dependent race and is
not described as RED. The reason for the fix is the independently verified CUDA
contract violation, not a fabricated failing runtime result. Earlier 585-case
and 9-suite results above likewise predate this production fix.

### Production fix and cleanup

Replaced the constructor's pageable `cudaMemcpy` with a private nonblocking
initialization stream, `cudaMemcpyAsync`, checked `cudaStreamSynchronize`, and
checked stream destruction. Completion is checked before the host coefficient
vector can die and before the final `*out = p.release()`. Even a copy-submission
error is followed by stream synchronization/destruction attempts. Any create,
copy, completion or destroy failure takes the checked `cudaFree` path and leaves
`*out` unchanged; host RAII then releases the unpublished plan and temporaries.
An error from device cleanup is returned preferentially, as in the original
cleanup contract. CUDA context failure can still prevent resource recovery;
this path is not advertised as context repair.

There is no device-wide wait or default-stream dependency. No kernel or enqueue
code changed. All added synchronization is initialization-only. Header and CUDA
guide now state the ready-on-success construction contract and startup stream
overhead. CMake is unchanged in this follow-up. Changed follow-up paths are the
CUDA source, test, header, guide and this log, all within the six-file ownership.

### Post-fix resource gate and current verification state

On the next user-directed resume, fresh resources were RAM **3527472 KiB** and
GPU free **182 MiB**. GPU memory is below the unchanged 1 GiB floor. No compiler
process was returned. Per the latest instruction to compile only when floors
meet, the post-fix compile and GPU regression are **BLOCKED / NOT RUN** at this
checkpoint. The binary in the B2 validation directory still represents the
pre-fix constructor until rebuilt. No post-fix CPU suite rerun is claimed.
Source/format checks and the final re-review state are recorded below.

Self-review-event: type=qa_defect scope=spin8/attention_v2_cuda category=qa-coverage evidence=P1-pageable-plan-upload-QUALITY-request-changes

The review gap was relying on a copy API's name and tests with intervening
allocations rather than an explicit publication completion edge. Prevention is
the local first-use regression plus documented checked initialization, not a
governance edit. Runtime failure injection for copy/synchronize/destroy/free
cleanup remains unverified. Parent re-review and post-fix build/GPU execution
remain required; only the parent owns any server maintenance. No GUI/Hermes/
server stop, installation, commit, push or subdelegation occurred.

### Re-review checkpoint

Post-fix `clang-format --dry-run --Werror` passed for the CUDA header/source/test
after correcting continuation whitespace. `git diff --check` passed (the
existing CMake LF/CRLF notice remains). The B1/v1 preservation diff against
e959b84f was empty. HEAD remains
`e959b84fd5de69a6b3090034730ac757e5efc8c6`; status still contains only the six B2
paths plus the parent's original log/plans. No shared file or CMake change was
made during the P1 follow-up.

Exact constructor delta, before the existing checked cleanup and publication:

```diff
-    const auto e = cudaMemcpy(p->storage, coefficients.data(), p->storage_bytes,
-                              cudaMemcpyHostToDevice);
+    cudaStream_t upload = nullptr;
+    auto e = cudaStreamCreateWithFlags(&upload, cudaStreamNonBlocking);
+    if (e == cudaSuccess) {
+      const auto copy =
+          cudaMemcpyAsync(p->storage, coefficients.data(), p->storage_bytes,
+                          cudaMemcpyHostToDevice, upload);
+      // A pageable H2D copy can return before DMA completes. Finish this
+      // private stream before publishing to arbitrary caller streams or
+      // releasing the host vector. Also drain/check it when submission fails.
+      const auto completed = cudaStreamSynchronize(upload);
+      const auto destroyed = cudaStreamDestroy(upload);
+      e = copy != cudaSuccess        ? copy
+          : completed != cudaSuccess ? completed
+                                     : destroyed;
+    }
```

Current package: constructor fix in `spin8/src/attention_v2_cuda.cu`, 32-plan
preallocated first-use regression and `--first-use-only` selector in the CUDA
test, ready-on-success contract in the CUDA header/guide, and this evidence
appendix. **Source fix is ready for parent re-review; post-fix build and GPU
verification remain blocked, not passed.** After the parent makes resources
available, rebuild the existing B2 target and run the bounded first-use/full B2
tests with the same floors. Do not use the currently built pre-fix executable as
evidence for this source revision. Copy/synchronization/cleanup failure injection
and the earlier analyzer/sanitizer gaps also remain open.

## Source checkpoint review — 2026-11-07

Independent QUALITY re-review approved the constructor fix at source level:
initialization completes before publication, errors take checked cleanup before
publishing, and enqueue remains unchanged. The original static P1 is resolved
in source. Post-fix build, first-use/full GPU regression and failure injection
remain NOT_RUN. The parent is committing this as an explicitly unqualified
source checkpoint at the user's request, not as a finished A–H release.
The imported plan's three trailing Markdown spaces and final empty line were
normalized for the repository whitespace check; numerical/design content is
unchanged. Its recorded intake hash still identifies the original attachment.
