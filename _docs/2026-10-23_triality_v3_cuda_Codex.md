# Fused v3 CUDA controller and Triality Q transform

## Overview and scope

This increment adds an explicit, opt-in standalone CUDA v3 API. It computes the
biased rank-eight controller, bounded rational chart and complete block8 Q
transforms in one kernel. It does not modify the engine's model graph, model
loader, codec, VJP, runtime defaults or server state. No performance or model
quality claim is made. CUDA F32 storage with FP64 accumulation/chart is the
reference implementation policy.

## Requirements and decisions

V3-CUDA-01: the input is already normalized by its caller. There is no additional
RMS. Device arrays are contiguous F32 Win[8,width], bin[8], Wout[7,8], bout[7].
All rows in a call share one parameter set; the caller chooses per-head grouping.
The controller is `a=Wout*tanh(Win*q+bin)+bout`, including all tail components.
The rational chart uses tau=tan(pi/8) and scales before squaring. A single shared
spinor per row supplies `c0*I+sum(c[a+1]*J[a])` to every complete group of eight.
The final incomplete group copies exactly.

V3-CUDA-02: Wout=bout=0 preserves all finite input bit patterns exactly, including
negative zero. The GPU checks every parameter and source value even at identity.
CPU controller creation already rejects nonfinite host weights, and CPU apply
may bypass its hidden arithmetic at identity. GPU validation intentionally does
not bypass Win/bin, because caller-owned device parameters can change between
calls. The parameters must remain immutable during each launch. F32 finite
values are accumulated in FP64, so finite large F32 products do not suffer F32
intermediate overflow.

V3-CUDA-03: source/destination strides AND capacities are bytes. All four device
parameter arrays have explicit byte capacities. Host validation checks counts,
arithmetic overflow, address overflow, alignment, accessed spans and aliases.
All parameter arrays are mutually disjoint and disjoint from source,
destination and error_flag. Exact in-place source/destination is supported only
with equal strides. Padding is untouched. Supplied capacities are not proof of
actual allocation ownership or device/stream association; callers own those
contracts.

V3-CUDA-04: the host plan is immutable and contains only 128 bytes of coefficient
index and sign data. Creation calls the actual v3 basis audit and generator API,
then verifies exactly one +/-1 entry per row and column in each J, no overlapping
J entries and complete coverage together with identity. No hardcoded
alternate octonion convention, GPU allocation or device upload occurs in plan
creation. Each launch copies plan data into kernel parameters. The host
descriptor is borrowed only during enqueue. Destruction is serialized against
concurrent enqueues.

V3-CUDA-05: one CTA owns each row. Eight threads compute complete controller dot
products. All source reads by the controller and finite scan finish at a CTA
barrier before any output write. Each transforming thread loads its full
eight-component block before writing it. A final CTA barrier protects shared
spinor reuse in the capped-grid row loop. There is no per-row dense matrix or
global spinor intermediate, and apply has no allocation/copy/synchronization.

V3-CUDA-06: device errors OR SPIN8_CUDA_NONFINITE into caller-owned error_flag.
Caller clears it and discards all output whenever it is nonzero. F32 output
overflow is checked in FP64 before casting. There is no device failure-atomic
promise. Callers must synchronize the supplied stream, check asynchronous CUDA
status and inspect error_flag before consuming outputs.

## Files

`spin8/include/spin8/query_v3_cuda.h` declares the version-3 C ABI, host plan,
device parameter descriptor and ownership/error contracts.

`spin8/src/query_v3_cuda.cu` implements host layout validation, generator-derived
plan construction and the fused kernel.

`spin8/tests/query_v3_cuda_test.cu` exercises CPU v3 references with weights
rounded to F32 before conversion to double, and an independent dense reference
reconstructed directly from Gamma. Parent integration owns CMake edits.

## Verification plan and current evidence

The test file was written before the kernel implementation. Initial compiler
execution was deferred by the parent because a large model download was active
and heavy operations must be serialized. The parent subsequently stopped the
download and explicitly granted a build/test window. The first Release build
and all eight standalone tests passed, as did initial memcheck and racecheck.
These first results did not include the later cancellation regression.

Reference cases cover widths 1, 7, 8, 23, 256 and 1032, three distinct rows and noncontiguous
source/destination strides, nonzero controller weights and biases, different
spinors across rows, exact identity/signed zero/tails, norm, padding and exact
in-place versus out-of-place agreement. A dedicated width-nine case varies
only the copied tail and requires the complete-block rotation to change.

Boundary cases cover byte capacities for every parameter, short source and
destination spans, zero counts, stride alignment, integer/address overflow,
partial aliasing, unequal-stride in-place calls, parameter aliases, flag aliases,
version and null output. Host rejection must leave output and flag untouched.

Device cases cover NaN/Inf in each parameter array and source tail, sticky flag
OR, NaN Win and Inf bin at zero Wout/bout, maximum finite F32 weights, maximum
finite F32 input under identity and nonfinite F32 output detection. A nondefault
stream capture requires exactly one kernel graph node, then checks replay
against the independent reference.

A 65,536-row width-eight nontrivial in-place case checks the capped-grid loop.
It compares row zero, row 65,534 and row 65,535 against the independent dense
reference, so CTA zero must replace its shared controller state correctly when
it processes its second row. The source/destination buffer is approximately
2 MiB and no larger model allocation is required.

Mixed finite/nonfinite three-row cases at widths 7 and 23 check error detection
even for tail-only transforms. Their diagnostic comparison of the surrounding
valid rows does not change the discard-all-output error contract.

## Independent review finding and regression

The independent reviewer supplied a finite, high-magnitude cancellation case:
Win=0, bin[0]=bin[1]=1, Wout[0,0]=FLT_MAX, Wout[0,1]=-FLT_MAX, all remaining
Wout/bout=0. CPU strict arithmetic separately rounds the two identical products,
then subtracts to exactly zero. CUDA's default multiply/add fusion instead
retained a residual large enough to saturate the bounded chart and rotate Q.
The flag stayed zero because every value was finite.

The new test was compiled against the unchanged kernel first. The actual GPU
execution failed at `large Wout cancellation matches CPU`, exit 1. RED evidence:
`<STRATA_DATA>\build\v3-fused-fma-red-build.log` and
`<STRATA_DATA>\build\v3-fused-fma-red-test.log`. Earlier logs remain preserved.

The correction uses explicit `__dmul_rn`/`__dadd_rn` for the controller's FP64
multiply/add and chart square accumulation. The small plan now maps each matrix
coordinate to one signed spinor coefficient, allowing each block dot to use
the same source-column reduction order and separate product/sum rounding as
the CPU dense reference without constructing a dense matrix. This also avoids
an analogous rounding/order discrepancy with high-magnitude Q. Host/device
tanh implementations can still differ. Tolerance observations cover the tested
cases only. Arbitrary finite weights can amplify transcendental differences;
universal CPU bitwise or tolerance equivalence is not guaranteed. Parameter
profiles need their own calibration and audit before model integration.

## Final worker verification evidence

All checks ran sequentially inside the parent-granted window after the large
download had been stopped. No downloads or servers were started by this worker.

`cmake --build <STRATA_DATA>\build\spin8-cuda --config Release --parallel 1`
succeeded after the fix. The build uses CUDA 13.3 and MSVC 14.44.35207, targeting
compute_120/sm_120. Log: `<STRATA_DATA>\build\v3-fused-fma-green-build.log`.
The pre-existing Visual Studio CUDA flag ordering emitted D9025 because /W1
overrode /W4. The parent owns the separate CMake warning-metadata correction
and its final build; this worker did not change build configuration.

Direct execution of `spin8_query_v3_cuda_test.exe` succeeded, including the
previously failing cancellation case and all newly added width/mixed-row cases.
Log: `<STRATA_DATA>\build\v3-fused-fma-green-test.log`.

`ctest --test-dir <STRATA_DATA>\build\spin8-cuda -C Release --output-on-failure`
passed 8/8: CPU, query, query_v3, C ABI, CUDA, query CUDA, query v3 CUDA and native
adapter. Log: `<STRATA_DATA>\build\v3-fused-fma-green-ctest.log`.

CUDA 13.3 Compute Sanitizer memcheck on the new executable returned exit 0 and
reported 0 errors. Log: `<STRATA_DATA>\build\v3-fused-fma-green-memcheck.log`, with
test stdout in the corresponding `-stdout.log`. Racecheck returned exit 0 and
reported 0 hazards, 0 errors and 0 warnings. Log:
`<STRATA_DATA>\build\v3-fused-fma-green-racecheck.log`, with matching stdout.
Both include the 65,536-row capped-grid and captured graph replay tests.

A C-only header smoke translation unit was created under the explicitly
authorized H: artifact directory:
`<STRATA_DATA>\build\v3-fused-c-header-smoke.c`. MSVC `/TC /std:c17 /Zs /W4 /WX
/utf-8` succeeded, exit 0, proving C syntax/declarations rather than a linked C
runtime test. Log: `<STRATA_DATA>\build\v3-fused-c-header-smoke-utf8.log`.
The first attempt omitted `/utf-8` and failed due solely to CUDA header C4819
code-page warnings; its failure is preserved separately in
`<STRATA_DATA>\build\v3-fused-c-header-smoke.log`.

Clang-format was applied to the three new code files, then
`clang-format --dry-run --Werror` succeeded, exit 0. Log:
`<STRATA_DATA>\build\v3-fused-format.log`. This final formatting and header comment
clarification occurred after the worker's successful runtime checks; no
semantic code change occurred. The parent explicitly owns the following final
build/test and this worker released its compile window. `git diff --no-index
--check NUL <file>` emitted only LF/CRLF repository notices, with no whitespace
error. A separate clang-tidy run was not performed; CUDA/MSVC static-analysis
coverage beyond compiler diagnostics remains open.

## Self-review

Self-review-event: qa_defect. Evidence was the independent FMA counterexample
and actual failing GPU regression despite the initial suite passing. The narrow
prevention change is the source regression test for cancellation plus explicit
arithmetic in this implementation, verified RED then GREEN on hardware.
No AGENTS, skill, SOP or automation was changed. One numerical coverage gap
does not justify a broader governance rewrite. Remaining numerical risk is
profile-specific conditioning and host/device tanh differences.

Read-only preparation commands included Get-Content for canonical prompt,
PC/project AGENTS, common/start/skill-selection/application/CPP SOPs, MILSPEC
and TDD skills, CPU v3 implementation and CUDA patterns; rg files for nested
instructions; git status/branch. No compiler, test runner, GPU workload, endpoint
or server operation was invoked during this source preparation.

## Applied standards and limits

Applied PC MILSPEC skill, common engineering SOP, implementation start gate,
skill-selection SOP, application-development SOP and CPP SOP. The parent uses
subagent-driven-development; this worker owns only the four files named here.
No formal military-standard compliance assertion is made.

Compilation, CUDA execution, sanitizer and formatting evidence is recorded above.
Full static analysis and the parent's final warning-metadata build remain
separate checks. GPU VJP, codec wiring,
GGML/model-graph integration, HIP/SYCL/Metal implementations and end-to-end
inference are outside this increment. The default engine path is untouched by
these new files; application behavior cannot change until separately wired.

## Next action and rollback

Parent has registered the source and test in the optional standalone CUDA target
and reviews the resulting evidence. The parent performs its final serialized
warning-metadata build/test before resuming the download. Revert only these files and their
specific CMake references to roll back; preserve all other concurrent work.

Parent final verification after source formatting/comments: Release build and
CTest8/8 passed (v3-fused-w4-build.log and v3-fused-w4-ctest.log). Final memcheck
reports0errors and racecheck0hazards/errors/warnings in v3-fused-w4-* logs.
Per-source VS Warning=W4 metadata removed D9025; four C4211 warnings remain
inside NVCC-generated temporary stub C files. These were not suppressed and
are not presented as a warning-clean build. No handwritten-source warning
was reported in that final build.
