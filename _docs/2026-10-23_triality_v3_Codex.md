# Triality v3 CPU math and immutable controller

Date: 2026-10-23. Implementation: Codex. Scope: additive CPU C ABI only.

## Requirements and boundary

The user-supplied `strata_triality_attention_plan_v3.md` and ZIP
`strata_triality_attention_v3_20261023.zip` define a rational bounded chart and
rank-eight controller on already normalized Q. The ZIP reference and tests were
read through .NET ZipArchive; attached scripts were not executed. The existing
`spin8/query.h` and `spin8/src/query.cpp` remain v2: bounded exponential chart,
biasless controller and internal RMS normalization. None of those semantics
were changed by this implementation.

The owned changes are `spin8/include/spin8/query_v3.h`,
`spin8/src/query_v3.cpp`, `spin8/tests/query_v3_test.cpp`, and this log. The root
agent owns CMake integration and broader regression evidence. The dirty shared
branch and unrelated work were preserved. No commit, push, dependency install,
model read, runtime stop or runtime configuration change was performed here.

Applied controls: PC-wide and project AGENTS; canonical pre-implementation
prompt `<PC_CANONICAL_PROMPT>`; common engineering,
implementation-start, skill-selection, security, LLMOps and C++ SOPs;
`milspec-codex-standard`. Identity and environment assertions in the canonical
prompt are subordinate to the actual session's system/developer instructions.
This log records engineering traceability, not certification to a MIL standard.

## Mathematical construction and proof

The runtime reads the existing chirality-ordered positive Clifford generators.
Let `L_i[a,b]=Gamma_i[a,8+b]` and `C(c)[i,a]=sum_b L_i[a,b]c[b]`.
Both full sets of polarized identities are audited over all basis pairs:

`L_i^T L_j + L_j^T L_i = 2 delta_ij I`,

`C(e_a)C(e_b)^T + C(e_b)C(e_a)^T = 2 delta_ab I`.

The first relation proves `||L(v)c||^2=||v||^2||c||^2`. The second, by
bilinearity, gives `C(c)C(c)^T=||c||^2 I`. In particular `C0=C(e0)` is
orthogonal. With `J_a=C(e_{a+1})C0^T`, polarization with `e0` proves
`J_a+J_a^T=0`. Multiplying the remaining polarized identities by the fixed
orthogonal base and using skew symmetry gives
`J_a J_b + J_b J_a = -2 delta_ab I`.

Consequently `A(c)=c[0]I+sum_a c[a+1]J_a=C(c)C0^T` is orthogonal for unit c.
Its determinant is +1: it is continuous on connected S7, nonzero throughout,
and `A(e0)=I`. The proof does not assume that `det(C0)` itself is +1. Every
computed matrix also passes the existing numerical SO(8) audit before export.

This is a seven-parameter isoclinic family. It does not span arbitrary SO(8),
is generally not closed under composition, and does not establish learned
controller equivariance. Tests explicitly demonstrate non-closure.

## Chart and controller

Version `SPIN8_QUERY_V3_VERSION=3` explicitly separates this contract from v2.
The chart is `tau=tan(pi/8)`, `u=tau*a/sqrt(tau^2+||a||^2)`,
`c=(1,u)/sqrt(1+||u||^2)`. The implementation first scales all terms by
`max(tau,max(abs(a)))`. Thus even seven DBL_MAX coordinates remain finite;
chaining unscaled hypot calls, as in the research reference, can overflow for
that input. No change to the mathematical map is intended. The origin is
exact e0, its derivative has the seven unit coordinate tangents, and the angle
is at most pi/8 up to finite-precision rounding.

The immutable controller copies Win[8,width], bin[8], Wout[7,8] and bout[7].
It evaluates `a=Wout*tanh(Win*q+bin)+bout` directly on model-normalized Q.
There is no extra RMS normalization and no implicit weight initialization.
Win is retained exactly as supplied. Wout and bout both zero select an exact
identity path even when nonzero Win times a large finite Q would overflow.
With nonzero output parameters, arithmetic overflow is an explicit NONFINITE
failure. Finite input alone does not promise representable controller dots or
transformed Q output.

One spinor is shared across full groups of eight in each row. An incomplete
tail is copied exactly. F32 accumulates in F64 and is range-checked before its
final cast. Capacities are bytes; strides are scalar elements. Row spans,
alignment, integer/address overflow and partial aliasing are checked. Exact
in-place Q with equal strides is allowed. The optional spinor export rejects
all source/destination overlap. All results are staged before any destination
write, including failures on a later row. Source padding is not inspected and
destination padding is not changed. Zero rows/width and unsupported dtypes are
explicitly rejected. Objects own no model state, device state or caller memory.

## Verification performed

Direct isolated builds use Visual Studio 2022 MSVC 14.44.35207 through
`VC\Auxiliary\Build\vcvars64.bat`, with `/EHsc /std:c++17 /W4 /WX /fp:strict`.
Include path is the workspace's `spin8/include`. Sources are `spin8.cpp`,
`query.cpp`, `query_v3.cpp`, and `query_v3_test.cpp`. Objects and executables are
under `<STRATA_DATA>\build\triality-v3-math-20261023`; no root CMake build was run
by this worker. Final build and test exit codes were zero.

The test reports:

`query v3: independent basis/polarization, 512 matrices, chart Jacobian, controller gradients and buffer contracts passed`

The independent reference uses a separate octonion multiplication table and
the actual chirality sign. It compares all fixed generators and all 512 random
unit-spinor matrices with both that reference and the unchanged v2 matrix API.
It checks all 64 C-basis pair polarizations, exact Cl(0,7), skew symmetry,
proper orthogonality and non-closure. The built-in basis audit reports zero
error on all four metrics for this signed-integer construction.

Chart tests cover the exact origin, unit derivative, all seven matrix tangent
derivatives, a complete analytic Jacobian at a nonzero point, subnormal through
DBL_MAX magnitudes, all seven DBL_MAX inputs, unit norm, angle bound and
nonfinite failure atomicity. The initial two-point c0 Jacobian check at h=1e-6
failed by 2.23e-10 due to cancellation near one (measured derivative
`-0.040965055292385699`, analytic `-0.040965055069110565`). The test now uses a
five-point h=1e-4 stencil for the nonzero-point Jacobian, retaining the same
2e-10 acceptance threshold. Production math was not changed to fix that test.

Controller tests compare direct biased/no-extra-RMS evaluation; complete
blocks, tails, padding, all four weight copies, F64 and F32 in-place results,
F32 against F64 dense output, source/destination/spinor capacities, integer
extent overflow, bad stride, overlap, unsupported dtype, zero rows, late-row
NaN, huge identity input and arithmetic overflow failure atomicity. A central
finite difference confirms the initial Wout spinor and Q-output derivatives
are nonzero and equal their analytic values; the initial Win derivative is
zero as expected, and the bout derivative is one. Version mismatch, all weight
capacities, every nonfinite weight group and creation extent overflow fail.

`clang-format -i` was run on all three owned C/C++ files. `clang-tidy` was run
with `--checks=clang-analyzer-*,bugprone-*,performance-*,-performance-enum-size`
and `--warnings-as-errors=* -- -std=c++17 -Ispin8/include`, and passed. The
initial default invocation enabled no checks. The initial explicit performance
check proposed shrinking the existing C enums in `spin8.h`; that one check
was excluded to preserve the C ABI. The final invocation suppressed 120
non-user/system-header diagnostics and reported no user-source diagnostics.

Final `clang-format --dry-run --Werror` passed. SHA-256 fingerprints of the
tested, formatted source are:

`query_v3.h`: `f08d13c848d3b94087dce25c9c01aa114e62da9922bcc1be535cf8f88c2d4c36`.

`query_v3.cpp`: `4d96732876ffe7b33688ce74668bf2089a8583ce275f30ed0b59091e48852626`.

`query_v3_test.cpp`: `ab5aed38313007112758e4f5e849ccc68c7b39ae4ab4c4661dad76dd57765e8e`.

## Mutation checks

Isolated, deliberately incorrect copies under the build directory check the
committed test oracle. Their production counterpart remains intact. Each was
compiled with the same MSVC strict flags and linked to the final test object
and the existing spin8/query objects. All three compilations succeeded and all
three mutant test executables returned exit code 1, as required:

`chart_half.cpp` replaces the tangent numerator `tau` with `0.5*tau` and is
rejected by `unit derivative at origin`.

`zero_win.cpp` replaces copied Win with all zeros and is rejected by
`biases and NO second RMS`.

`omit_bin.cpp` starts the hidden preactivation at zero instead of bin and is
rejected by `biases and NO second RMS`.

These are targeted mutation checks, not exhaustive mutation coverage. The
unmodified final test executable passed independently before the mutant runs.

## Residual risks and next action

This worker did not implement an analytic backward/VJP, a training/capture
pipeline, sidecar serialization, adapter/cache invalidation, native attention
insertion, device kernel, real-model evaluation, benchmark or runtime recovery.
The CPU spinor export can feed an existing consumer but does not claim a device
stream/lifetime contract. No CPU result here substitutes for those remaining
v3 stages. Broader CMake/C/CUDA regression is owned and recorded by the root
agent separately. No speed or model-quality improvement is claimed.

Rollback is limited to removing the three new v3 files and their separate
CMake entries; it does not require changing v2. Next action: consume this v3
API in an explicitly versioned integration and separately implement/verify the
analytic backward needed for adapter training.

Self-review-event: ticket_completed. `agent-self-review-evolution` was applied
in review-only mode. The numeric stencil failure and static-analysis setup
limitations are recorded above; no governance/skill/SOP changes were needed.
