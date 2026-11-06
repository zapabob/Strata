# B1 CPU attention_v2 implementation evidence

## Scope and start gate

Goal: implement the bounded B1 CPU production slice in the delegated worktree,
starting at c50ca06a. Only the seven assigned paths are owned by this worker.
Initial status contained only the parent's untracked docs/plans and Hermes log.
Those files are preserved. Parent owns spec review, quality review and integration.
This worker does not delegate further.

Applied the supplied PC/project baselines and canonical CLAUDE-FABLE-5 context
only where compatible with higher-priority instructions (its identity, date,
platform and tool substitutions are not applicable). Read Common, Start Gate,
Skill Selection, Security (caller memory boundary), Application Development,
C and CPP SOPs. Skills: supplied milspec-codex-standard, test-driven-development,
and completion self-review. Existing spin8 header, implementation, tests, README,
query adapter ABI and CPU implementation log informed conventions. No web fact,
package trust or model capability claim is needed for this local implementation.

## Requirements and planned evidence

B1-ABI: version/size/reserved validation, immutable opaque plan, copied mapping,
typed C errors and exception containment. B1-SEM: post-position self-attention
with matching nonzero source identity, explicit heads and widths, FP64 only.
B1-MEM: byte strides, capacities, checked arithmetic, disjoint caller output,
staged writes. B1-MATH: explicit scale, bias/softcap order, one masked softmax,
inverse V before gate, real audited Spin8 transforms with optional H128.
B1-QA: independent scalar oracle, bounded MHA/GQA/MQA dimensions, sentinels,
invalid inputs and negative controls, pure C compile and existing CPU suites.

Vertical TDD starts with an identity-attention API test before the API exists.
Later slices add geometry/validation and fixed-basis behavior tests before their
implementation. Acceptance tolerance is absolute output error <=1e-11.

## Environment

Unique build: H:/Strata/validation/spin8-cuda135-20261106/b1-opencode-cpu.
Parent exists; build directory was absent. Initial available physical RAM was
10.748 GiB, above the unchanged 3 GiB floor. Toolchain: requested VS 2022 x64,
Release, CUDA OFF, tests ON, serial build.

## Commands and results

All commands ran in `H:/Strata/worktrees/spin8-cuda135-20261106`. Build commands
were guarded with `Test-Path` for the intended build parent/directory and a
`Win32_OperatingSystem.FreePhysicalMemory * 1KB >= 3GB` check. No resource-floor
setting was changed. Later observed available RAM was 9.830 and 8.740 GiB.
MSVC was 19.44.35224.0, MSBuild 17.14.40, Windows SDK 10.0.26100.0.

### Vertical RED/GREEN sequence

The initial test called the missing API and checked a two-key identity result
against a direct scalar calculation. The only production change at that point
was test-target registration. Configure succeeded and the target build failed
at `attention_v2_test.cpp(1,10)` with MSVC C1083: missing
`spin8/attention_v2.h`. This was an actual compile of the caller, not a source
pattern/regex test. The command was:

```powershell
cmake -S spin8 -B H:/Strata/validation/spin8-cuda135-20261106/b1-opencode-cpu -G "Visual Studio 17 2022" -A x64 -DSPIN8_ENABLE_CUDA=OFF -DSPIN8_BUILD_TESTS=ON
cmake --build H:/Strata/validation/spin8-cuda135-20261106/b1-opencode-cpu --config Release --target spin8_attention_v2_test --parallel 1
```

The first implementation supported the tested identity case. The same target
build then succeeded; this focused CTest command passed 1/1 (one oracle case):

```powershell
ctest --test-dir H:/Strata/validation/spin8-cuda135-20261106/b1-opencode-cpu -C Release -R '^spin8_attention_v2$' --output-on-failure
```

The next test slice added deterministic strided MHA/GQA/MQA oracles and rejection
cases before their implementation. The same build succeeded and the focused
CTest failed 0/1 with `FAIL: create geometry plan`: the first implementation
rejected multiple heads. After implementing geometry, copied mapping, validation,
scale/bias/softcap, gate and staged output, the same commands passed 1/1.
Direct execution printed `204 cases; worst absolute error 0`.

The fixed-basis slice added all three Spin8 views, H128, negative controls,
overflow witnesses and a pure-C caller before implementation. Commands:

```powershell
cmake --build H:/Strata/validation/spin8-cuda135-20261106/b1-opencode-cpu --config Release --target spin8_attention_v2_test spin8_attention_v2_c_test --parallel 1
ctest --test-dir H:/Strata/validation/spin8-cuda135-20261106/b1-opencode-cpu -C Release -R '^spin8_attention_v2' --output-on-failure
```

Both executables compiled, including `attention_v2_c_test.c` as C. Both tests
failed (0/2) because fixed plan creation was unsupported. Implementing real
audited transforms made the same commands pass 2/2. The C++ executable reported
474 cases and worst absolute error `2.2204460492503131e-15`. Supplemental boundary
coverage then added valid-capacity partial aliases, descriptor/plan aliases,
nulls, masked nonfinite bias, late gate overflow and input-only Q/K sharing.

### Final Release and regression evidence

```powershell
cmake --build H:/Strata/validation/spin8-cuda135-20261106/b1-opencode-cpu --config Release --parallel 1
ctest --test-dir H:/Strata/validation/spin8-cuda135-20261106/b1-opencode-cpu -C Release --output-on-failure -V
```

Final build passed without compiler warnings. Production and both new test
targets use `/W4 /WX /fp:strict`. All 8 CTest entries passed in 15.29 seconds:
`spin8_cpu`, `spin8_attention_v2`, `spin8_attention_v2_c`, `spin8_query`,
`spin8_query_v3`, `spin8_query_adapter`, `spin8_query_sidecar_python`,
`spin8_c_abi`. The Python entry ran 10 tests and passed. Native build output
confirmed the separate `.c` compilation and C++ linkage of the library.

The v2 C++ entry passed **499 cases**. These are mixed numerical/negative cases,
not 499 independent CTest executables. Its measured worst absolute oracle error
was **2.2204460492503131e-15**, below the unchanged `1e-11` threshold. Wrong Q/K
bases diverged by `0.954905866`; gate-before-inverse diverged by `3.15127209`.
Finite-input overflow witnesses demonstrated actual Q, K, V and H128 execution
rather than an identity shortcut. No assertion in the v2 suite reads source text.

CTest's retained evidence is
`H:/Strata/validation/spin8-cuda135-20261106/b1-opencode-cpu/Testing/Temporary/LastTest.log`.
The final CMake-only follow-up aligned indentation with surrounding lines;
it did not change commands, targets or test semantics.

### Formatting, analysis and scope checks

```powershell
& 'C:/Program Files/LLVM/bin/clang-format.exe' --dry-run --Werror spin8/include/spin8/attention_v2.h spin8/src/attention_v2.cpp spin8/tests/attention_v2_c_test.c spin8/tests/attention_v2_test.cpp
& 'C:/Program Files/LLVM/bin/clang-tidy.exe' '--checks=-*,clang-analyzer-*,bugprone-*,-bugprone-easily-swappable-parameters' '--warnings-as-errors=clang-analyzer-*,bugprone-*' spin8/src/attention_v2.cpp -- -std=c++17 -Ispin8/include
git diff --exit-code -- spin8/src/spin8.cpp spin8/include/spin8/spin8.h spin8/tests/cpu_test.cpp
git diff --check
git status --short
```

Final formatter check passed with no output; all formatting edits used
`apply_patch`. The initial formatter check found layout violations, corrected
without weakening the style. The initial analyzer run reported four multilevel
pointer-to-void implicit conversions; explicit casts now state the intended
storage-range checks. The final analyzer run passed with no user-source
diagnostics (120 non-user warnings suppressed by clang-tidy). The
easily-swappable-parameters heuristic is excluded for the C ABI scalar arguments;
analyzer checks are enabled. No global configuration or dependency was changed.

The v1 source/header/CPU test diff was empty. Diff whitespace check passed.
Git emitted its existing LF-to-CRLF notice for CMake, not a source diagnostic.
Only the owned additions and CMake change appear alongside the parent's two
original untracked entries.

## API decisions and implementation details

Exact v2 config/request size and version with zero reserved fields avoid silent
interpretation of future descriptors. Semantic selectors are uint32 values to
reject unknown values deterministically across C callers. Only FP64 self-
attention with no codec is accepted. Source IDs and the explicit post-position
stage bind caller assertions; content provenance remains the caller's duty.

The immutable plan retains head/width/source scalars, a copied arbitrary mapping,
and an owned `spin8_plan` for fixed mode. One common basis enforces Q/K agreement
for all sharing heads. No controller, learned weights, multi-view/session state
or global mutable cache is introduced. Actual `spin8_plan_create` audits are
reused; H128 also runs its existing coefficient audit. Forward ordering is
H128 then Spin8. Inverse value ordering is Spin8 inverse then H128 inverse,
followed by optional original-space elementwise gate.

Positive input byte strides and independent K/V layouts use checked spans and
unaligned-safe loads. Output supports padded/permuted layouts with a conservative
sorted-stride proof of nonoverlap. Entire declared capacities are used for alias
checks. All finite validation and computation finish in owned vectors before the
only caller-output commit. Exceptions are translated at the C boundary. Raw
memory provenance, concurrent caller mutation and stale handles remain outside
the contract; no OS-specific invalid-pointer recovery is promised.

## Exact changed files

- `spin8/include/spin8/attention_v2.h`: C ABI, layout and ownership contracts.
- `spin8/src/attention_v2.cpp`: CPU plan/execute implementation.
- `spin8/tests/attention_v2_test.cpp`: independent FP64 oracles and boundaries.
- `spin8/tests/attention_v2_c_test.c`: pure C compilation/call coverage.
- `spin8/docs/attention_v2.md`: caller guide, numerical ordering and limits.
- `spin8/CMakeLists.txt`: additive source and two test targets.
- `_docs/2026-11-06_spin8-attention-v2_OpenCode.md`: this evidence log.

## Self-review

Self-review-event: type=ticket_completed scope=spin8/attention_v2 category=correctness
evidence=_docs/2026-11-06_spin8-attention-v2_OpenCode.md

Self-review-event: type=qa_defect scope=spin8/attention_v2 category=qa-coverage
evidence=initial-format-and-analyzer-checks

Response: review-only for governance. Expected TDD REDs were retained as evidence,
not relabelled as passed checks. Initial formatter/analyzer findings were fixed
locally, then checked again. Review also added meaningful valid-capacity alias
coverage because short-capacity rejection alone does not prove alias checking.
No instruction, Skill or SOP change is justified by this single bounded task.
Broader policy edits were rejected as outside the owned surface. Parent's
independent spec review and then quality review remain necessary before integration.

## Residual risks and next action

No native engine, GPU, models, GUI, installer or release validation is part of
this slice. Caller must supply live memory and truthful source identity; the C
API cannot establish the provenance of pointers or tensor contents. Parent will
independently review specification compliance and quality before integration.

Allocation-failure injection, concurrency stress, MSVC AddressSanitizer and
non-Windows compilers were not run. The numerical evidence is limited to bounded
deterministic FP64 fixtures, not arbitrary magnitudes or full context windows.
The implementation stages multiple FP64 tensors and has no throughput or memory-
saving qualification. Exotic output layouts that fail the documented sorted-
stride proof are rejected. No commits, pushes, release actions, installations,
GPU/model/process stops or further delegation occurred. Rollback is removal of
only these additive files and their CMake entries, preserving parent work.
