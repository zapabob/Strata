# Spin(8) standalone CPU library implementation evidence

Date: 2026-10-23 (Asia/Tokyo). Base: `011c9e600a93bbc9fd451c563501b5831c32bbca`.
Branch inspected: `codex/strata-spin8-bonsai`. This worker made no commit or push.

## Scope and requirements

This worker owns `spin8/` except `src/cuda.cu`, `tests/cuda_test.cu` and the CUDA
header owned by the CUDA worker. The parent owns engine integration. Existing
work by other workers was preserved. The library is independently configurable;
CUDA is OFF by default. No GGML dependency is used by the CPU library.

SP8-MATH requires real Cl(8,0) generators from octonion left multiplication with
triples (123),(145),(176),(246),(257),(347),(365), a true 8+8 chirality split,
and vector/half-spin representations of the same plane-rotor product.
SP8-ABI requires explicit C ownership, errors, row strides, finite validation,
overlap/overflow checks, F32/F64 operations and transactional failure.
SP8-REDUCE requires finite nonnegative weights summing to one, default thirds,
three-view matmul and one-softmax attention with arbitrary head widths.
SP8-H requires normalized signed HD forward and DH inverse, actual sign-aware
audit, plus 128-element Bonsai-compatible blocks.
SP8-MON requires an initial audit then 1024-token OR 60-second scheduling with
typed sticky failure. These requirements do not constitute formal MILSPEC
certification or completion of the parent model-integration plan.

## Applicable instructions and design decisions

Read the canonical pre-implementation prompt under the user `_docs/prompts`,
PC-wide and Codex-local AGENTS, project AGENTS, CONTRIBUTING, README and build
configuration. Applied common engineering, implementation-start-gate,
skill-selection, application-development, C and C++ SOPs. Skills applied:
`milspec-codex-standard`, `incremental-implementation`, and review-only
`agent-self-review-evolution` after failed verification attempts.

Plane factors use `U=cos(theta/2)I-sin(theta/2)Gamma_a Gamma_b` and act in array
order. Positive chirality is placed first using an exact fixed block permutation.
Both half-spin matrices are extracted from the SAME U. Vector R is derived from
the same plane convention. Plans audit the intertwiner as well as SO(8) signs.

CPU F32 uses FP64 coefficients/accumulation and a final storage cast. CPU F16/BF16
returns UNSUPPORTED. The tolerance coefficient API (1e-12,1e-5,2e-3,2e-2) is a
policy definition, not proof of support for every storage type. Full blocks8
transform and incomplete tails use identity. General Hadamard blocks are powers
of two from1 through1024. General factor audit reports a rounded-coefficient
model analytically; it is distinguished from numerical LU and runtime errors.

One call of CPU attention handles one head. Callers map arbitrary head counts
and GQA explicitly. Three-view logits reduce BEFORE one stable softmax and the
original V reduction. Orthogonality implies original-space logits in exact
arithmetic; this library makes no speed or model-quality improvement claim.

## Changed files

`spin8/include/spin8/spin8.h` exposes opaque plans, transform/reduction/reference
operations, mathematical diagnostics, matrix/factor audit, precision policy and
explicit monitor state. `spin8/src/spin8.cpp` implements them without extra
dependencies. `spin8/tests/cpu_test.cpp` contains independent arithmetic and
boundary tests. `spin8/tests/c_abi_test.c` verifies C compilation/linkage and an
identity transform. `spin8/README.md` documents conventions, ownership, limits
and commands. `spin8/CMakeLists.txt` builds the standalone project and optional
CUDA/native-adapter tests; CUDA source ownership remains with its worker.

## Commands and observed evidence

`cmake -S spin8 -B <STRATA_DATA>\build\spin8-cpu -G "Visual Studio 17 2022" -A x64 -DSPIN8_ENABLE_CUDA=OFF`
completed with MSVC19.44.35224.0 and Windows SDK10.0.26100.0. The build uses
`/W4 /WX /fp:strict` for the production CPU target.

`cmake --build <STRATA_DATA>\build\spin8-cpu --config Release` completed successfully
after the final source changes, with no emitted compiler warning. An earlier
test-only implicit float conversion warning was removed using explicit casts.

`ctest --test-dir <STRATA_DATA>\build\spin8-cpu -C Release --output-on-failure`
passed2/2 tests after final changes: spin8_cpu and spin8_c_abi. The final observed
CTest elapsed time was1.98seconds. Direct execution of the CPU test printed:

```text
PASS Spin(8) CPU: Clifford, chirality, 80 group trials, double cover, HD/DH, attention, boundaries, monitoring; worst triality 9.9920072216264089e-16
```

The numerical test covers all64 Clifford anticommutators, symmetric real gamma,
chirality +/-I blocks,80 random twelve-plane products, group composition,
independent arbitrary-vector intertwining,2pi/4pi behavior, strided/in-place
inverse and padding, all256 eight-element Hadamard sign masks, dense parity
Hadamard oracle for1,2,8,128,1024blocks, F32 coefficient determinant nonidentity,
weighted/default reduction, matmul and masked attention at widths1,7,8,13,40,64,
96,128, F32 attention and inverse tolerances, nonfinite/stride/overlap/overflow,
invalid weights/signs/blocks, unsupported F16 and all-masked attention, and
monitor scheduling plus sticky invalidation.

`clang-format -i` ran on owned C/C++ sources and header using installed LLVM.
`clang-tidy --checks=clang-analyzer-*,bugprone-*,-bugprone-easily-swappable-parameters spin8/src/spin8.cpp -- -std=c++17 -Ispin8/include`
exited0 with no user-source diagnostic;119 vendor/non-user warnings were
suppressed by the tool. The initial broad pass identified static initialization
noexcept/index widening and easily-swappable C ABI scalars. The first two were
fixed. The scalar ABI observation is inherent in the documented C signature;
that check alone was excluded for the final pass, not analyzer checks.

`git diff --check` exited0 at review time. The core and generic Hadamard code was
reviewed for buffer transactionality, signed determinant logic, representation
ordering, allocation exception boundaries and monitor failure behavior.

## Failed attempts and self-review

Self-review-event: qa_defect; response: review-only, no governance file changed.
The first build command was issued before an asynchronous configure completed,
and reported missing CMakeCache. A CTest invocation similarly occurred before
the asynchronous test executable link finished, producing NotRun. Both were
rerun only after their predecessor completed and final tests passed. Future
commands in this session explicitly wait for process completion before dependent
validation. These orchestration failures are not recorded as code-test passes.

A newly added reduction test asserted exact integer equality after default
binary-floating-point thirds. The CUDA worker's combined CTest exposed the
failure. The production reduction was correct; the oracle was changed to the
specified F64 tolerance1e-12, then freshly passed. This is not a relaxed numerical
requirement. Initial clang-tidy without explicit checks failed because inherited
configuration enabled none; subsequent explicit analyzer/bugprone runs executed.

## Integration review and remaining evidence

Read parent native adapter and decode callsite. Confirmed scheduling is once per
decode iteration rather than per layer. Reported to the parent that native audit
must also cover realized FP32 matrix coefficients used by CUDA rather than only
original FP64 coefficients. The parent owns that correction and validation.

CUDA compilation/execution and compute-sanitizer are owned/reported separately
by the CUDA worker. They are not independently asserted by this CPU log. Root
engine builds, persisted cache compatibility, actual model inference, quality,
throughput and release gates remain parent-owned. Linux/GCC/Clang compilation,
MSVC address sanitizer and formal external review were not executed by this
worker; compiler/analyzer/test evidence above is limited to this Windows CPU
environment. The reference operations deliberately stage full outputs and are
not optimized for production memory/latency.

Rollback is additive: keep engine feature disabled and remove/revert only the
owned Spin(8) files if needed. Preserve other workers' changes and evidence.
