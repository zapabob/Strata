# Independent Spin8 reference repair — 24 October 2026

## Scope and decision

Task 1 repairs the independent determinant reference on branch
`codex/strata-030-completion`, from BASE
`5cf017c8c4a4b615721ce7aca3a28be02d563691`. Production Spin8, codec, dependency,
service, model and release files were not changed. The pre-existing modified
23 October documents and untracked handoff were preserved and excluded from
this commit. The task report records the final commit.

The required canonical prompt, home and Codex-local AGENTS, project AGENTS,
common engineering SOP, implementation-start gate, skill selection, security,
application development, Python and C++ SOPs were read. Actual system identity,
tools and Windows environment take precedence over contradictory canonical
product/environment claims. Applied skills were `milspec-codex-standard`,
`evidence-changelog-closeout`, and `agent-self-review-evolution`. No delegated
review, package update, network research, service start, model download or
publication was performed.

## Defect and implementation

The original external `compare.py` counted row swaps but omitted every negative
LU pivot. It therefore returned the wrong sign for a reflection, a proper
quarter-turn and half the signed Hadamard masks. Its trial checks had also
stopped comparing the FP64 reference determinant sign, relying on library
signs and a limited rational spot check. That could not support the old G1
independent FP64 determinant claim.

The original script, probe and CMake file were copied byte-for-byte before any
edit into `H:/Strata/build/task5a-g1-reaudit-20261024/original`, with SHA-256
receipts. Existing inputs, results, logs and builds were retained. Only the
explicitly authorized old `scripts/compare.py` was repaired in that old tree.
It now counts pivot signs, reinstates every supplied rotation-view LU sign
check, checks the 16x16 lift sign and compares Hadamard reference signs.

Repository tooling is in `tools/spin8_reference_compare.py`,
`tools/test_spin8_reference_compare.py`, and `tools/spin8_reference_probe/`.
The entry point is import-safe, takes explicit input/output paths, labels fresh
versus replay input, refuses an existing report, validates completeness and
finite input, and records source/script/input/artifact hashes. The CMake probe
uses relative source paths and builds CPU-only with one job. Its output path
must be supplied explicitly. No machine-specific path is embedded in the
tooling. The promoted reference builds canonical octonion/Clifford operators
independently and checks library generators against them before comparison.

The repaired LU includes row-swap parity and negative-pivot parity. Tests cover
identity, one reflection, an odd permutation, a proper quarter-turn, two
reflections, singularity, and negative determinant with non-unit magnitude.
All 256 signed Hadamards are checked against bit-parity construction and a
separate exact integer Bareiss oracle. The runtime reference uses exact integer
subset expansion, not a copied C++ determinant implementation. It checks the
FP64 sign of every supplied rotation matrix, including samples outside the
full construction subset, and the determinant signs of constructed lifts and
spinor blocks. Rational spots remain separate and explicitly describe the
10**12 denominator limit as approximate rationalisation of FP64 inputs.

## Commands and evidence

Evidence root is `H:/Strata/build/task5a-g1-reaudit-20261024`. Initial H: free
space was 28,907,380,736 bytes, above the required 10 GiB reserve plus 256 MiB
allowance. A second check preceded probe execution. The final manifest records
the measured footprint and free space. No existing evidence was moved or
deleted. Build/probe/reference output was approximately 27.4 MB, below 256 MiB.

`uv` was `C:/Users/downl/.hermes/bin/uv.exe`. Every Python command used the
existing `C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe`
through `uv run --no-project --offline --python <python312> python ...`.
The interpreter reported Python 3.12.10; existing pytest 8.3.5, black 26.3.1
and flake8 7.2.0 were used without installation. An initial `--no-sync` was
removed after uv warned it has no effect with `--no-project`. uv's warnings
about two unrelated dangling package metadata directories were retained.

Initial pytest auto-loaded unrelated installed plugins and stalled before
test execution; only this task's exact uv/Python processes were stopped.
Subsequent pytest runs used `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`. The original
broken reference produced RED: 131 failed, 132 passed, exit 1, in
`red-isolated.log`. After fixing LU, the original 263 cases passed in
`green-focused.log`. The final expanded suite passed 272 tests in 1.28 s,
exit 0, in `green-complete.log`. `red-replay/` retains the archived broken
module and a self-contained determinant test fixture; its later forensic
replay again produced 131 failed, 132 passed in 3.18 s. This replay is distinct
from the original pre-fix TDD RED.

The fresh CPU commands were:

```powershell
cmake -S tools/spin8_reference_probe -B H:/Strata/build/task5a-g1-reaudit-20261024/cpu -G "Visual Studio 17 2022" -A x64 -DPython3_EXECUTABLE=C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe
cmake --build H:/Strata/build/task5a-g1-reaudit-20261024/cpu --config Release --parallel 1
ctest --test-dir H:/Strata/build/task5a-g1-reaudit-20261024/cpu -C Release --output-on-failure -j 1
H:/Strata/build/task5a-g1-reaudit-20261024/cpu/Release/spin8_reference_probe.exe --out H:/Strata/build/task5a-g1-reaudit-20261024/probe-fresh.json --trials 5000 --python-check 1000 --seed 20261023
```

Configure and both initial/final build commands exited 0. MSVC 19.44.35224,
`/W4 /WX /fp:strict`, was used. The final rebuild followed probe source
formatting. CTest passed 6/6 in 10.82 s, including the Python sidecar test.
Logs are `configure.log`, `build.log`, `build-final.log`, and `ctest.log`.
The probe exited 0; `probe-run.log` records the fresh invocation result.

The final reference command was the uv prefix above followed by:

```powershell
tools/spin8_reference_compare.py --probe H:/Strata/build/task5a-g1-reaudit-20261024/probe-fresh.json --report H:/Strata/build/task5a-g1-reaudit-20261024/reference-fresh.json --input-mode fresh --artifact H:/Strata/build/task5a-g1-reaudit-20261024/cpu/Release/spin8_reference_probe.exe --artifact H:/Strata/build/task5a-g1-reaudit-20261024/cpu/spin8/Release/spin8.lib --artifact H:/Strata/build/task5a-g1-reaudit-20261024/cpu/CMakeCache.txt --artifact H:/Strata/build/task5a-g1-reaudit-20261024/build-final.log --artifact H:/Strata/build/task5a-gateA-spin8-20261023/scripts/compare.py
```

It exited 0: all 12 families passed. It checked 15,000 supplied rotation-view
signs with no mismatches; 1,000 samples received full independent construction,
group/inverse and Triality checks; 200 spinor matrices received separate
rational spots. All 256 masks passed integer determinant and parity comparison,
including 128 negative determinants. The fresh probe bytes match the old probe
bytes exactly; the new result is nevertheless from the fresh executable run,
not labelled as an old-input replay.

Measured trial maxima were 1.11e-15 for group/inverse, 1.11e-15 for vector
agreement, 7.77e-16 for F64 loopback, 5.96e-8 for F32 loopback, 2.00e-15 for
conjugation, and 1.11e-15 for library Triality. Clifford, chirality and canonical
generator agreement were exact. 2pi/4pi errors were 2.45e-16/4.90e-16. Query
identity initialization was exact; query finite-difference gradient maxima
were 1.94e-10 for nonzero parameters and 9.50e-11 for zero parameters. Full
maxima and per-family verdicts are in `reference-fresh.json`.

Final Python checks were `python -m black --check` on the two Python files and
`python -m flake8 --max-line-length=88 --extend-ignore=E203,W503` on the same
files, through uv. Both exited 0. The installed Visual Studio clang-format
checked the promoted C++ probe with `--dry-run --Werror`, exit 0. The CLI help
exited 0; the probe without `--out` exited 2 as intended. A focused import of
the repaired external script passed the seven determinant cases and all
256 masks, exit 0. No standalone clang-tidy run was performed; MSVC warning
checks and the fresh compile/test suite are the C++ analysis evidence here.

## Hashes and superseded claim

Original external script SHA-256:
`7db3b8881760d37f0bbd478bf744600862ca889a0041b72c197613c86fbe3a41`.
Repaired external script SHA-256:
`db83b9063305e90335b1ed9beebb5ee4f2dc6f60cc0c990554db0b04f2e002d0`.
Promoted Python reference SHA-256:
`3866d376bf79b94860e79ed660621391ae30bb070b5bcc6605b1f9028e2d821a`.
Promoted probe source SHA-256:
`24420cb9556658479e667d59b39fe4db1770fa11fecc9e1f002354da35ddeaa4`.
Fresh probe JSON SHA-256:
`b629d8542b482094cb957ba00cfc374ecbaed3ab44255ab331ef3730469342d1`.
Fresh reference report SHA-256:
`53bfd5e79c242847a08dccab4732b80667eb3911ffb1c3ada105ebd8a5c81c62`.
The reference JSON binds its source and binary hashes; `receipt-manifest.json`
additionally binds every retained task receipt and the CPU test sources.

This corrected CPU numerical result supersedes the independent determinant
portion of the G1 PASS claim in
`_docs/2026-10-23_strata_030_execution_Codex.md:168-182`. That document is
pre-existing user work and was not edited or staged by this task. The old
G1 reference had a real sign defect even though its final family verdict was
PASS. This task does not assert a production-library sign defect.

## Self-review and concerns

Self-review-event: type=qa_defect scope=tools/spin8_reference_compare.py category=qa-coverage evidence=H:/Strata/build/task5a-g1-reaudit-20261024/red-isolated.log

Self-review-event: type=ticket_completed scope=tools/spin8_reference_compare.py category=correctness evidence=H:/Strata/build/task5a-g1-reaudit-20261024/reference-fresh.json

The prevention change is the narrow determinant regression suite and the
restored unsuppressed all-sample sign gate. Governance files and SOPs did not
need changes. Review checked failure propagation, original-file preservation,
source/hash provenance, exact versus approximate determinant claims, portable
paths, CPU-only scope and commit ownership. Broader source rewrites and default
changes were rejected as unrelated to this reproduced defect.

One incidental artifact remains outside the new evidence root:
`H:/Strata/build/task5a-gateA-spin8-20261023/scripts/__pycache__/compare.cpython-312.pyc`.
It was created by the external-script import and is excluded from input/source
evidence. Its hash is in the task report and master manifest. Automatic approval
review rejected the exact generated-cache cleanup command as
`rejected: blocked by policy`; no alternative deletion was attempted. The
controller instructed that it remain in place. Later Python commands used
`-B` or `PYTHONDONTWRITEBYTECODE=1`. Old inputs/results/receipts were not changed.

CUDA, native model inference and broader release gates remain untested by this
task. The reference is qualified for these supplied SO(8)/Hadamard samples;
it is not a certificate for arbitrary ill-conditioned matrices. Existing LU
singularity handling uses the retained 1e-300 pivot cutoff. No production
code change is warranted by the corrected result. The next gate is the
controller's separate CUDA/release validation. Reverting this commit restores
the repository tooling state; the archived original script permits exact
manual restoration of the explicitly authorized external script if needed.

## Review fix round 1 — 24 October 2026

FIX_BASE is `7ac9d164f030953257669c4f0dd8745d098c2c87`. Both Important findings
in the Task 1 review were reproduced before correction. The initial commit's
direct spinor comparison covered only the first construction sample and its
errors did not enter the acceptance gate. Whole-matrix negation of a later
plus or minus block preserved its determinant and Gram matrix and passed the
other invariants. Separately, NaN loopback errors could disappear inside max
reductions because un-emitted F32/inverse/block arrays were not finite-checked.
These were reference/probe verification defects, not demonstrated library
transform defects. This addendum supersedes any implication in the initial
entry that those two cases had already been covered.

The Python reference now accumulates direct plus/minus coefficient errors
over every construction sample, maps either chirality order correctly, and
requires both maxima at most 1e-12. Two integration regressions alter the
second sample's entire 8x8 plus/minus block and require the trial family and
overall verdict to fail. Their explicit `SPIN8_REFERENCE_TEST_PROBE` input was
set first to the retained deterministic probe for RED, then to the new fresh
probe for GREEN. Neither integration case was skipped in recorded runs.

The probe now checks every forward and inverse trial, extended F64 and
Hadamard-block F32/F64 output immediately after the transform, before passing
forward output to an inverse and before error reductions. Failure identifies
the stage and element index and exits 2. A separate test-only executable in
`probe_finite_fault.cpp` intercepts the real probe's calls and injects NaN or
infinity at the last output element while retaining SPIN8_OK. The Python driver
requires the actual probe path to exit 2 with the matching non-finite stage.
Its 44 cases cover trial F32/F64, extended F64, both directions and block sizes
8, 16, 64 and 128 in both dtypes/directions. The normal probe and production
library contain no injector. Per-case partial JSON and diagnostic logs remain
retained in the new evidence root.

New evidence root is `H:/Strata/build/task5a-g1-reaudit-20261024-r1`; initial
free bytes were 28,853,153,792. Original round-0 receipts/binaries and all old
evidence were preserved. No cleanup/deletion was attempted. Every Python
execution used uv with the same existing Python 3.12.10, `-B` and/or
`PYTHONDONTWRITEBYTECODE=1`; package metadata warning noise remains qualified.
The Python command prefix was `uv run --no-project --offline --python
C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe python -B`.

RED commands ran `-m pytest -q tools/test_spin8_reference_compare.py -k
later_constructed` with plugin autoload disabled, then configured and built
only `spin8_reference_probe_fault` in `cpu-red` with `--parallel 1`, and ran
`tools/spin8_reference_probe/test_finite_outputs.py --executable
<r1>/cpu-red/Release/spin8_reference_probe_fault.exe --output-dir <r1>/red-faults`.
Results: 2 Python failures in 8.31 s; all 44 fault injections escaped the old
probe and failed the rejection tests (exit 1). The RED executable and source
snapshot remain retained. GREEN configured a separate `cpu-green`, built
`spin8_reference_probe` and `spin8_reference_probe_fault`, also one job and
MSVC `/W4 /WX /fp:strict`, then passed all 44 fault cases (exit 0).

The fresh normal probe ran seed 20261023, 5000 trials and 1000 Python checks,
exit 0. The final 274-test owned Python suite passed in 8.64 s with the fresh
probe fixture. The final fault-driver run passed 44/44. The corrected reference
on that fresh output passed all 12 families, all 15000 supplied rotation-view
signs and all 1000 direct spinor construction comparisons. Both direct plus
and minus error maxima were exactly 0. The deterministic probe bytes again
matched the retained earlier output. Black, flake8 and clang-format checks
passed. No unrelated CTest/model/CUDA suite was rerun; this round changes only
reference/probe gates, and the focused runtime regressions exercise them.

New Python reference SHA-256 is
`f6c0650d56d8ca1c890b8a77a3be8d832ff8702cfa3b3dc7bde1fadfa20bc289`;
probe source is `59739035debf422885197366b039cad86b5c4907a8c4362986602878440c3f5d`;
fresh reference report is
`69e5588dca8f009d5e734a143c8723cceaaef52703f1a98102a4b50ec619e87f`;
ordinary probe executable is
`56ec6ceea0496c079081ec24acdabf9337af459bffabdad428e36787d15516d5`;
fault executable is
`35f87f11690f886e41da64fc96fc1b8d0fefbf3d8edbb6b3542bb419f8135cc8`.
The new master manifest binds receipts, sources, tests and binaries. The same
SDD task report carries complete commands, outputs, final capacity/hash data
and the fix commit. Evidence before that manifest was approximately 111.4 MB,
below 256 MiB, with 28,689,797,120 bytes free at the final pre-log measurement.

Self-review-event: type=qa_defect scope=tools/spin8_reference_compare.py category=qa-coverage evidence=H:/Strata/build/task5a-g1-reaudit-20261024-r1/red-spinor.log

Self-review-event: type=qa_defect scope=tools/spin8_reference_probe/probe_spin8.cpp category=correctness evidence=H:/Strata/build/task5a-g1-reaudit-20261024-r1/red-finite.log

Self-review verified all-sample accumulation, acceptance thresholds, injection
at the final array element, exact failure stages, separation of test-only
injection from normal behavior, and preservation of initial artifacts.
Regression additions are the narrow prevention measure; no governance or
production changes were made. CUDA/model/release qualification remains outside
this CPU task. The initial incidental external Python cache remains in place
under the controller's prior direction; this round did not retry its cleanup.
