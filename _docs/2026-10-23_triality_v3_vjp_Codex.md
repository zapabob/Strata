# Triality v3 analytic controller VJP

Date: 2026-10-23. Implementation: Codex. Scope: additive CPU F64 backward
interface for one already-normalized query head row. This is engineering
traceability, not a certification claim or a model-quality claim.

## Requirements and decisions

The parent task explicitly assigned only `spin8/include/spin8/query_v3.h`,
`spin8/src/query_v3.cpp`, `spin8/tests/query_v3_test.cpp` and this new log.
The shared branch was verified as `codex/strata-spin8-bonsai`. Existing v2,
other workers' edits, root CMake and runtime configuration were preserved.
No commit, push, process stop, dependency installation or optimizer state was
introduced. The existing v3 controller and its two earlier implementation
logs were read before editing.

The canonical pre-implementation prompt at
`<PC_CANONICAL_PROMPT>`, PC-wide/project instructions,
common engineering, implementation-start, skill-selection, security, LLMOps
and C++ SOPs were applied. Actual session identity, environment and higher
priority instructions take precedence over incompatible prompt assertions.
Skills: `milspec-codex-standard`, `incremental-implementation`, and the
completion/QA review of `agent-self-review-evolution` in review-only mode.
The explicit no-commit instruction takes precedence over a skill's usual
incremental commit recommendation.

Acceptance requirements were analytic derivatives for all four parameter
groups and Q; a nonzero first-step Wout gradient at identity; accumulation
across full blocks; the tail's controller dependence; byte capacities,
alignment, integer/address overflow and alias validation; finite arithmetic;
failure-atomic caller-owned outputs; and no C++ exception escaping the ABI.
These are mapped to the derivative and validation tests described below.

## Public contract and implementation

`spin8_query_v3_controller_vjp_f64` accepts the immutable controller, Q and its
output adjoint dy, each input span with a byte capacity. Its
`spin8_query_v3_gradients_f64` descriptor names dq, dwin, dbin, dwout and dbout,
each with a byte capacity. Required counts are width, 8*width, 8, 56 and 7
doubles. Weight gradients retain create's row-major layout. The five output
spans must be disjoint from each other, Q, dy, the descriptor and the
controller's object and owned parameter storage. Q and dy may overlap each
other. The API checks accessed spans, not unused capacity padding.

All gradients are staged before writing any output. Success overwrites rather
than accumulates; invalid arguments, finite-arithmetic failures and allocation
failures preserve every gradient. Each multiply and sum in unbounded dot
products is checked separately. bad_alloc maps to ALLOCATION_FAILED; other
C++ exceptions map to INVALID_ARGUMENT. The API owns no caller buffers,
optimizer or global training state. Allocation is linear in width for the
staged dq and dwin; remaining storage is fixed-size stack arrays.

Let h=tanh(Win*q+bin), a=Wout*h+bout, u=tau*a/sqrt(tau^2+||a||^2), and
c=(1,u)/sqrt(1+||u||^2), with tau=tan(pi/8). A(c)=c0*I+sum ca*Ja acts on each
complete block of eight. Its c adjoints accumulate from every full block:
gc0=sum dy dot q and gca=sum dy dot (Ja*q). Direct dq is A(c)^T*dy; the copied
tail initially has dq=dy.

The chart pullback uses gu=(gc_tangent-c_tangent*(gc dot c))*c0. With
v=a/sqrt(tau^2+||a||^2) and r=tau/sqrt(tau^2+||a||^2), ga=r*(gu-v*(v dot gu)).
The radius is computed after scaling by max(tau,max(abs(a))); unscaled
tau^2+||a||^2 is never formed. This accepts seven finite DBL_MAX tangent
coordinates without an overflowing radius.

Then dWout=ga outer h, dbout=ga, gx=(Wout^T*ga)*(1-h*h), dWin=gx outer q,
dbin=gx, and dq additionally receives Win^T*gx. Every Q component enters
that last chain, including an unrotated tail. Q is already normalized by the
model; this interface adds no RMS operation. Orthogonality applies to A(c),
not to the full input-dependent Jacobian.

There is deliberately no identity backward shortcut. Even when Wout=bout=0,
the hidden activations determine dWout, while dWin and dbin are zero and dq is
dy. An overflowing Win*q is therefore rejected by VJP even though the existing
forward identity shortcut can avoid that computation. The header documents
this distinction. No existing forward behavior was changed.

## Verification performed

Final isolated direct-MSVC build directory:
`<STRATA_DATA>\build\triality-v3-vjp-20261023`. The saved `build.cmd` enters that
absolute directory before running Visual Studio 2022 Community's
`VC\Auxiliary\Build\vcvars64.bat` and compiling with
`/EHsc /std:c++17 /W4 /WX /fp:strict`. Sources are spin8.cpp, query.cpp,
query_v3.cpp and query_v3_test.cpp with the workspace spin8/include path.
The final build and test exit codes were zero. Evidence: `build.log` and
`test.log` in that directory. This worker did not run or modify shared CMake.

The full query_v3_test executable passes the existing independent basis,
512 matrix, chart and forward tests together with the new analytic VJP tests.
Every scalar of Win[8,9], bin[8], Wout[7,8], bout[7] and Q[9] is compared to
a five-point derivative of dy dot forward(Q), using step 1e-4 and absolute
tolerance 3e-10. Width 17 checks all Q derivatives across two shared-spinor
blocks and a tail. Identity initialization checks exact dq=dy, zero dWin/dbin,
nonzero dWout and its finite difference. Width 3 checks the unrotated-only
case. These provide 170 new scalar finite-difference comparisons.

Validation tests cover zero and one-byte-short capacity for each gradient;
every output's null, misaligned, Q-alias, dy-alias and descriptor-alias cases;
all ten output-pair aliases; partial input/output and output/output overlap;
null/misaligned descriptor; null controller; both input capacities and null or
misaligned pointers; synthetic wrapping input/output addresses; controller
object overlap; NaN and infinity in either input's tail even at identity;
overflowing adjoint products; overflowing hidden preactivation at identity;
late outer-product overflow; and preservation of all five gradient buffers.
Outputs initialized with NaN are fully overwritten on successful derivative
calls. A zero adjoint overwrites all groups with zeros. Seven DBL_MAX bout
coordinates produce finite, nonzero subnormal chart gradients.

`clang-format --dry-run --Werror` passed on all three owned C/C++ files.
Production query_v3.cpp passed clang-tidy with
`--checks=clang-analyzer-*,bugprone-*,performance-*,-performance-enum-size`
and `--warnings-as-errors=* -- -std=c++17 -Ispin8/include`; 120 system/non-user
diagnostics were suppressed. The enum-size check was already excluded in the
existing v3 analysis contract to preserve its public C enum ABI.

The additional same-check clang-tidy run over query_v3_test.cpp failed with
four diagnostics, retained in `tidy-test.log`: the existing deterministic RNG
seed, same-type Q/dy test-helper parameters, an intentional integer-to-pointer
cast for the address-overflow test, and a possible iostream exception escaping
test main. No checks were disabled or source threshold relaxed. This test-file
lint result is separate from the passing production analysis, strict compiler
warnings, format check and runtime tests.

A C translation unit including the header and calling the new function
compiled with MSVC `/TC /c /W4 /WX`; evidence is `header-c.log`. Three isolated
incorrect source copies were compiled and linked to the final test object.
Omitting Win^T*gx from dq is rejected by `every Q analytic VJP`; removing c0
from the chart pullback and forcing ga to zero are each rejected by
`every parameter analytic VJP`. Each incorrect executable exited with code 1;
the mutation script exited zero after observing rejection. Sources and
per-mutation build/test logs are under the same isolated build directory.
Production files were not replaced by mutation sources.

SHA-256 of the final tested source:

query_v3.h: `21a7ef861c87acc7ccd965166d368c963bfbfd32729e1aa6c93a175ce6e9e4ea`.

query_v3.cpp: `aed52bed67d61b0b2d6f46e46359c7b50d6d7bfe34bc4aa04bde77715228d3b0`.

query_v3_test.cpp: `0a597bb3a28aeee82b74a7427f25b463389279b9aeb8e44bd62bf62ae33bb799`.

## Build-location correction and self review

An initial direct cmd invocation failed before compilation because the command
wrapper escaped the quoted vcvars path. A scratch build.cmd fixed that launch.
The next expanded-test rerun invoked that script from the repository instead
of H:, generating seven files at the repository root: spin8.obj, query.obj,
query_v3.obj, query_v3_test.obj, query_v3_test.exe, build.log and test.log.
CreationTime showed all seven were newly created between 07:10:08 and 07:10:18
local time; git status showed the five binary files untracked and two logs
ignored. There was no evidence of a preexisting file being overwritten.

Before relocation, each exact absolute source was verified to be directly
under `<STRATA_REPO>`, and its creation time was
checked. All seven were individually moved with Move-Item -LiteralPath into
the previously nonexistent directory
`<STRATA_DATA>\build\triality-v3-vjp-20261023\repo-cwd-artifacts-071008`.
No wildcard, recursive move, deletion or process kill was used. build.cmd now
contains explicit `cd /d <STRATA_DATA>\build\triality-v3-vjp-20261023`, checks its
status, and the final rebuild ran entirely there. Repository-root artifact
status was empty after relocation. Both the corrected final evidence and the
earlier run's artifacts were retained.

Self-review-event: qa_defect and ticket_completed. The build-location mistake
and optional test-file analysis findings were reviewed. The smallest prevention
was the explicit cwd guard in this scratch build script; no AGENTS, skill,
SOP, automation, memory or other governance file was changed. Suppressing the
test findings merely to obtain a green analysis result was rejected.

## Limits and handoff

This worker's evidence is CPU F64 analytic backward math, validation, C header
compatibility and targeted mutation sensitivity. It does not establish a GPU
backward, model-layer capture, optimizer integration, sidecar lifecycle,
end-to-end model acceptance, throughput improvement or quality improvement.
Allocation failure was not fault-injected. A caller remains responsible for
valid live memory behind non-null pointers and the controller's lifetime.

The parent separately reported five passing cross-library synthetic training
tests: 20 steps reduced training loss from 0.19148204899796717 to
0.16203828674971116, while held-out loss increased from 0.17082027450580836 to
0.19621042465148875. These values were not independently rerun by this worker.
They are negative held-out-quality evidence and do not authorize adopting the
trained parameters. The parent also reported an independent VJP review with
no actionable math/buffer/chain findings; its own artifact is authoritative.

Rollback is the removal of this additive VJP declaration/descriptor,
implementation helpers/function and associated tests; no v2 migration is
needed. Next action is to assess the parent's integration evidence and keep
the still-open full-model gates distinct from this verified CPU derivative.
