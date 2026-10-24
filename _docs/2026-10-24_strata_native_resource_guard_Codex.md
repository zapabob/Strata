# Native diagnostic resource controls, Task 4c0

Task 4c0 supplies the bounded execution prerequisite for native cache
integration. It does not connect the new cache to a model. The controller
explicitly separated this change after the implementer escalated the coupled
native ownership and transaction design. Task 4c1 and Task 4c2 remain open.
Base: `864cf52ca31b5a6db8ff09fc5658e357a8442535`, on
`codex/strata-030-completion`.

## Requirements and scope

Stop a stalled NVIDIA preflight after ten seconds without attempting the
guard or inference launch. During an owned diagnostic, abort on available
physical RAM below 256 MiB continuously for 30 seconds, or available commit
below 2 GiB. Terminate only the retained Popen process handle. Preserve the
trace, the actual exit, and a typed reason. The existing outer Windows Job
guard remains responsible for descendants, output limits and disk reserve.

Owned files are `tools/run_native_validation_step.py`, its existing focused
test, `tools/native_model_resource_guard.py`, its new focused test, and this
record. No engine, model, preset, dependency, service, global environment,
compiler output or original evidence was changed. No model or compiler ran.
Port 8080 was not started. No push, tag, release, deletion or move occurred.
The original baseline executable was not overwritten; the verified-copy
requirement still applies before the future native build.

The canonical prompt and home, Codex and project instructions were consulted;
incompatible identity/tool/OS assertions do not replace actual Windows or
system/developer requirements. Selected SOPs: Common Engineering,
Implementation Start Gate, Skill Selection, Security, LLMOps, Application
Development, Python, CPP and C. Applied skills: milspec-codex-standard,
test-driven-development, code-review-and-quality, evidence-changelog-closeout,
and agent-self-review-evolution. This is internal engineering discipline,
not a claim of certified MILSPEC conformity.

## Implementation and ownership

The NVIDIA subprocess call now has `timeout=10`. A `TimeoutExpired` becomes a
failed runtime GPU preflight; the sequential launch gate records that failure
and never starts its guarded child. Python's bounded `check_output` manages
and reaps its own probe. The timeout is not reported as zero free VRAM.

The new harness reads `GlobalMemoryStatusEx` directly once per approximately
one second. RAM recovery resets the continuous-pressure timer. Thresholds
are strict: exactly 256 MiB physical and 2 GiB commit are admitted. Invalid
or unavailable telemetry fails closed with `telemetry_failure`. A separate
positive wall timeout is mandatory. Each trace row records monotonic elapsed
time, UTC time, physical/commit bytes and an optional abort reason.

The harness reserves new trace and result files before launching. Its result
keeps status, reason, actual child exit and `owned_child_reaped` separate.
Natural process exit, including zero, is not a generation/performance verdict.
It does not look up or terminate a PID or process name. A retained Windows
Popen handle is used for termination and bounded reaping. Cleanup failure is
typed separately; the enclosing reviewed guard still cleans its job members.
This trusted local harness is not a containment replacement or a sandbox.

CLI use requires an explicit plan path and SHA-256. That plan contains the
absolute native executable path, its SHA-256, an argument array and timeout.
Both plan and executable are checked before launch. Invoke the CLI through
`run_native_validation_step.py` and its reviewed fresh PowerShell 5.1 guard;
include the model-source receipt and resource prerequisites in the outer
plan when running a real model. This task's smoke uses a tiny Python sleeper,
not native inference. The nested plan, outer plan and receipts preserve the
executable/plan bindings.

## Verification evidence

Evidence root: `H:/Strata/build/task5a-native-cache-20261024`.
Every executed test, formatter, linter and smoke used a successful terminal
prerequisite and the sequential launcher. Each command allowed an additional
64 MiB peak, 32 MiB aggregate evidence and a 10 GiB reserve, with a 120-second
outer timeout. This is below the dispatched 4 GiB/2 GiB ceilings. No heavy
stages ran concurrently. Fresh guard receipts identify PowerShell
`5.1.26100.9711`, real exit values and zero surviving owned processes.

Python used the existing `uv run --offline --no-project --python
C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe python -B`
runner. No packages were installed. Pytest plugin autoload and bytecode
writing were disabled only in the launched process environment. Test commands
used `-p no:cacheprovider`, explicit evidence-root `--basetemp`, and JUnit XML.

RED preflight: `pytest tools/test_run_native_validation_step.py -q` produced
9 passed and 1 expected failure: the intercepted NVIDIA call had no timeout.
See `preflight-red.stdout.log`, `red.xml`, and `preflight-red.receipt.json`.
RED harness: `pytest tools/test_native_model_resource_guard.py -q` failed
collection because the required harness module did not exist. See
`harness-red.stdout.log`, `harness-red.xml`, and its receipt. These failed
receipts remain retained and were not used as successful prerequisites.

Initial GREEN was 15 passed. The final affected suite was:
`pytest tools/test_run_native_validation_step.py
tools/test_native_model_resource_guard.py -q`, with **24 passed in 4.37 s**.
See `resource-final.stdout.log`, `resource-final.xml`, the exact
`resource-final.plan.json`, and `resource-final.receipt.json`.
Tests cover the thirty-second/reset boundary, immediate commit pressure,
malformed telemetry, actual child termination while a separate child stays
alive, telemetry failure, wall timeout, natural exits zero and seven,
existing-evidence refusal, mismatched plan/executable bindings, and the
existing failed/unfinished prerequisite tests. The NVIDIA timeout test proves
zero attempts to launch the downstream guard. Its probe is simulated, not an
actual ten-second stalled driver experiment.

`flake8 --max-line-length=100 --extend-ignore=E203,W503` passed for all four
owned Python files. Black formatted them; the final `--check` passed with all
four files unchanged under `resource-black-check`. The pytest output has no warnings; uv's existing
no-project/dangling-directory warnings remain visible in launcher logs and
were neither suppressed nor repaired.

Positive CLI smoke used the real Windows memory query and an actual owned
two-second Python sleeper. `resource-smoke.result.json` reports natural exit
zero and reaped true; the outer receipt reports exit zero, null guard/error,
and zero job members after cleanup. The three actual samples report physical
availability from 8,856,793,088 to 8,876,797,952 bytes and commit availability
from 16,010,633,216 to 16,056,532,992 bytes. See the exact nested
`resource-smoke-child.plan.json`, outer plan and trace. Pressure-abort tests
inject telemetry; no experiment deliberately exhausted real system RAM.

## Self-review and remaining work

Self-review checked trace preservation, fail-closed telemetry, timer reset,
retained-handle ownership, natural/error exit separation, CLI binding checks,
and preservation of the existing launcher contract. No governance change was
needed; focused tests are the smallest recurrence control. Existing tests'
hardcoded historical evidence root remains a separately deferred concern.

Self-review-event: type=qa_defect scope=tools/run_native_validation_step.py category=qa-coverage evidence=H:/Strata/build/task5a-native-cache-20261024/preflight-red.stdout.log

Self-review-event: type=ticket_completed scope=native-resource-controls category=correctness evidence=H:/Strata/build/task5a-native-cache-20261024/resource-final.xml

Native cache ownership/configuration, model graph wiring, accepted-boundary
rollback, full dependent-state invalidation, actual model generation,
persistence and runtime transform monitoring remain unimplemented here.
No G1, G2, G3, speed, quality, distribution or release gate closes. The
controller's `task-4c1-blocker.md` contains the inspected source seams and
approved next-scope decisions. Rollback is a scoped revert of the owned
source/test/log commit, retaining all evidence and unrelated dirty files.

## Review fix round 1: bind parsing to verified plan bytes

FIX_BASE is 62c873a07685bcaedb616448cf29a0014b8d3d88. The independent
review's Important1 was initially unconfirmed static analysis: the harness
hashed the plan and then reopened its path for parsing. This round reproduced
the mismatch with a controlled Path.open substitution. The first read returns
the expected plan and a later read returns changed arguments. run_owned is a
capture stub in this regression, so reproduction launches no child and does
not stress a real filesystem race. Both UTF-8 and UTF-8 with BOM were tested.

The harness now reads the plan once, hashes those bytes, and decodes/parses
those same bytes with utf-8-sig. Executable verification is preserved. The
regression asserts the original arguments and exactly one plan read. No
native graph, model, CUDA build or launcher source changed in this fix.

Evidence remains under H:/Strata/build/task5a-native-cache-20261024. Each step
used tools/run_native_validation_step.py with its exact fix1-LABEL.plan.json,
--label fix1-LABEL and a successful --prerequisite receipt. RED and format used
resource-black-check.receipt.json; GREEN used fix1-format.receipt.json; lint,
Black check and smoke then used the preceding successful receipt in order.
All step plans retain the 10 GiB reserve, 64 MiB additional-peak budget,
32 MiB output budget and 120-second timeout. RED was never a successful
prerequisite. Existing receipts and logs were retained.

The exact test invocation prefix was
C:/Users/downl/.hermes/bin/uv.exe run --offline --no-project --python
C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe python -B.
The RED suffix was -m pytest tools/test_native_model_resource_guard.py
-k parses_only_the_bytes -q -p no:cacheprovider --basetemp
H:/Strata/build/task5a-native-cache-20261024/fix1-red-temp
--junitxml=H:/Strata/build/task5a-native-cache-20261024/fix1-red.xml.
Output: 2 failed, 14 deselected in 0.78s. The final GREEN suffix was
-m pytest tools/test_native_model_resource_guard.py -q -p no:cacheprovider
--basetemp H:/Strata/build/task5a-native-cache-20261024/fix1-green-temp
--junitxml=H:/Strata/build/task5a-native-cache-20261024/fix1-green.xml.
Output: 16 passed in 1.95s. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 and
PYTHONDONTWRITEBYTECODE=1 were process-scoped. The module includes CLI
plan/executable mismatch no-launch regressions and the new positive binding
regressions. flake8 on the two changed Python files with
--max-line-length=100 --extend-ignore=E203,W503 passed. Black --check on those
two files passed. Exact command arrays and stdout/stderr/terminal receipts
are preserved in fix1-red, fix1-green, fix1-lint and fix1-black-check files.

One final-source positive CLI smoke used actual Windows memory telemetry and
the existing two-second Python sleeper plan, not a model. Its outer command
reads the harness bytes, asserts their SHA-256, and executes those same bytes.
The exact wrapper and all arguments are in fix1-smoke.plan.json. The inner
plan hash is 3bad5aeeeef3247da7301148102924b3ec1e8557addc8377c3fbbba4e276274e.
fix1-smoke.result.json records status exited, reason null, child exit 0 and
owned_child_reaped true. Its outer receipt records exit 0, null guard/error,
contained_before_resume true and active_processes_after_cleanup 0. Three
actual telemetry samples were retained in fix1-smoke.trace.jsonl; physical
availability stayed at least 12,706,263,040 bytes and commit availability at
least 21,198,651,392 bytes. No memory exhaustion experiment was performed.

Final tested source bindings are in fix1-sources.json, timestamp
2026-10-24T07:56:08.7897322Z, H free 22,761,553,920 bytes:

| File | SHA-256 |
| --- | --- |
| tools/native_model_resource_guard.py | 1b3c930e36e3d904be31c3971d8f76afa65494714585e8eb1e38cb2c8791cddb |
| tools/test_native_model_resource_guard.py | 815e8fc731000c8be48c2d020301e5aa70be15380d83dd89ad4e8e28161bacb8 |
| tools/run_native_validation_step.py | d647a92a8d3da0ad769276c422bac150d61115b05faa14902a467e1c7762511e |
| tools/verify_codec_dialects_build.ps1 | de2ee5053b3852a675e06ef25a3a98c98090a19d8769fc828d7ce083c2e9eac1 |
| tools/verify_bounded_process.cs | c2b697315e61611653410382f64e4eaddd40e079ea137a3cba5c9212e02da3e0 |

Self-review confirmed the new parser consumes the hashed bytes, BOM behavior
is retained, the reproduction checks behavior rather than only call count,
and the smoke binds actual final source before execution. The review finding
is closed locally pending independent re-review; it does not close any native
integration or model-generation gate. Existing uv noise remains deferred.

Self-review-event: type=qa_defect scope=tools/native_model_resource_guard.py category=correctness evidence=H:/Strata/build/task5a-native-cache-20261024/fix1-red.xml
