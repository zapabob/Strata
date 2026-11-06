# Remaining audited branch intake — 2026-11-06

Owner: OpenCode. Initial main HEAD: `ca3ab40a`, clean. Goal: integrate the four
remaining audited contributions into this worktree and verify their CPU/UI
contracts. The parent's all-branches/Spin8 release goal remains separate.

## Scope, standards and plan

Apply the supplied home/project AGENTS, compatible canonical preimplementation
context, MILSPEC baseline, plan-mode and qa-engineer skills; Common, Start Gate,
Skill Selection, Security, Application Development, WebApp, Frontend Design,
Python, TypeScript and C++ SOPs. Local source, tests, design authority and prior
installation evidence are sufficient for this scoped port; no web/package update
is needed. Goal/Todo APIs are unavailable; this log tracks the work.

1. Port disk destinations, filesystem pooling, sparse resume accounting and
   link-before-copy checks. Retain `remaining_pack_gb`, `model_hf` and `fam_pin`.
2. Port small-context Tuning bounds and inspection/reservation tests. Verify the
   rendered slider at 1K/2K/3K and long model windows, including change handlers
   and a recommendation no larger than the model supports.
3. Port the bounded local silence environment override. Keep the 30-minute local
   default and remote/tool policies. Exercise the actual watchdog callback.
4. Refuse unsupported Q36 `--vram-reserve-mib`; retain F32/F16 parsing. Compile
   and execute a CPU parser contract where possible, separately from native build.
5. Run focused regressions and Host typecheck, inspect the final diff, record
   limits, and create scoped commits for parent review.

Risk is bounded to setup preflight, existing UI controls, local watchdog config,
and one native argument refusal. Tests use isolated scratch profiles, mock model
services and no GPU. No install/runtime edits, process stops, dependency changes,
push, tag or release. Rollback is per scoped commit. Settings durability,
observations, hybrid search/skills, manual startup and native capability bindings
remain outside the change surface.

## Original commit mappings

| Audited input | Intake decision |
| --- | --- |
| `fix/gguf-dir-disk-on-data-dir`, merge `c02303b4` relative to parent 2 | Manual port onto newer main setup logic |
| `origin/codex/gui-small-gguf-context`, `c856522f` | Port missing UI/test parts; backend already supports 1K |
| `origin/codex/gui-local-silence-timeout`, `9df2a96a` | Port override using current `localStallMs` fallback/`turnStallLimit` |
| `pr/q36-refuse-unsupported-serve-flags`, `3b7241f4` | Narrow refusal to unsupported reserve flag; KV formats are supported now |

## Initial evidence

`git status --short --branch`: clean main, ahead 28. `git log --oneline -10`:
HEAD `ca3ab40a`, installed candidate source `04fe91d0`, integrated hybrid fixes
`1c521fba`/`7523fdb9`. Reviewed the four original diffs and surrounding code.

Read-only SHA-256 of the existing installer
`H:/Strata/releases/local-052-20261106-opencode/Strata-0.5.2-local.1-windows-x64-setup.exe`
before edits: `b77c1837c0829ff221a8de0fc4df21f898f7f45c4a8ca0f819f1a60dd5f1b87b`.
Installed app `0.5.2-local.1`, Control `0.5.2`, native `0.5.1` are the parent's
qualified installation, not outputs of this unit.

## Implementation

Disk: `setup.py` now pools planned writes using `same_drive` filesystem identity,
probes the nearest existing ancestor, credits only complete sparse-download
pieces, checks combined model/picture writes, and exhausts sibling hard links
before checking copy space. Missing owned shards fail before disk checks. The
newer allocated partial-pack credit and `model_hf`/`fam_pin` selection remain.
Malformed nonfinite chunk indices also receive no credit. Tests are in
`tools/test_setup_disk_destinations.py`; the Unsloth fixture accepts per-path
space and stubs its PCIe query. The DeepSeek Linux PCI fixture now explicitly
selects its simulated OS. Main already had Qwen36's missing-file assertion and
a deterministic DeepSeek engine-install mock, so those old changes were redundant.

UI: `apps/host/src/screens/Tuning.tsx` uses the model maximum down to 1K, with
`min(4K, model maximum)` as its lower bound. Both the recommendation label and
Reset to recommended obey the same model cap. Large models keep the 4K floor and
128K recommendation. `local-small-context.test.mjs` covers GGUF inspection and
reservation plus real React SSR and actual change/reset handlers for 1/2/3/32/
128/256/1024K. `annotations-32.test.mjs` adds the missing 3K launch-argument case.
Surrounding panels/state are fixtures; no CSS or layout tokens changed.

Watchdog: `apps/host/server/agent/agent-bridge.mjs` accepts an integer
`STRATA_LOCAL_STALL_MS` from 1 through 86,400,000, falling back to the existing
`localStallMs` option/default when unset or empty. Invalid values fail before
state writes. Current `turnStallLimit`, engine progress, remote and tool behavior
remain intact. `local-silence-limit.test.mjs` exercises the actual `runTurn`
interval/cancellation path with a controlled clock and fixture Harness transport;
no installed Harness is used. `docs/TROUBLESHOOTING.md` describes the current
30-minute local, 4-minute remote and 20-minute tool defaults and transport limits.

Native: `src/qwen35/q36_engine.cu` refuses `--vram-reserve-mib` and its equals form
with exit 2 before model loading, regardless of argument order. Supported F32/F16
options are unchanged. `tests/qwen36/test_serve_args_cpu.py` compiles the verbatim
parser block as a CPU executable and tests reserve refusals, all four K/V format
pairs before/after `--serve`, invalid formats, the supported expert-VRAM option,
defaults, and the existing unknown-flag compatibility fallback. It omits startup
telemetry, model loading and the engine implementation. This is executable parser
evidence, not a native build or inference qualification.

## Verification commands and results

Commands run from this worktree unless noted. Python uses
`uv run --no-project --offline --python C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe python -B`.
Node uses the installed private `C:/Users/downl/AppData/Local/Programs/Strata/node/node.exe`
read-only, with the unchanged `_docs/hybrid-intake-tests.mjs` runner and its
isolated `STRATA_TEST_SCRATCH`/filesystem guard.

* Setup: `-m unittest tools.test_setup_disk_destinations tools.test_setup_qwen36
  tools.test_setup_unsloth tools.test_setup_dsv41`, with TEMP/TMP at this
  worktree's `_docs` (each fixture creates and removes its own fresh subfolder).
  First fully passing run: 253 run, 252 passed, one expected Linux-sysfs skip.
* CPU native: `-m pytest tests/qwen36/test_serve_args_cpu.py
  tests/qwen36/test_bounded_run.py -q --basetemp
  H:/Strata/evidence/remaining-branch-intake-20261107-r1 -p no:cacheprovider`:
  **51 passed** in 25.74 seconds (24 parser cases and 27 bounded CPU fixtures).
  MSVC toolchain environment was read from the existing
  `H:/Strata/evidence/p01-b0-20261025/build/compile-expert_source.json` via
  `Q36_CPU_COMPILE_RECEIPT`. Fresh parser command/source/compile transcript and
  executable are under the new H: pytest directory, not the installed runtime.
* Host: `node _docs/hybrid-intake-tests.mjs local-small-context.test.mjs
  annotations-32.test.mjs local-silence-limit.test.mjs agent-watchdog.test.mjs`.
  Render/annotations tests passed; after correcting the test event-loop handle,
  standalone `local-silence-limit.test.mjs` passed **7/7**, including five actual
  watchdog branch tests. Three pre-existing real-Harness tests explicitly skip
  because the isolated runner points at `no-harness`.
* Host TypeScript: `node node_modules/typescript/bin/tsc --noEmit` in `apps/host`:
  PASS. Final rerun follows the small shared-recommendation cleanup.
* `git diff --check`: PASS (Git reports expected LF/CRLF normalization warnings).

### Failed attempts and disposition

First setup run had two failures: the added partial-pack test mistakenly selected
Unsloth's budget path (not low-RAM pack copying), and an existing DeepSeek lspci
fixture did not select Linux on Windows. The next pack test selected IQ3_S but
patched a stale package attribute left by `mock.patch.dict(sys.modules)` fixtures;
importing the registered module fixes the fixture without changing pack logic.
Subsequent setup run passed. Initial setup runs also exposed the existing
Unsloth fixture's read-only PCIe hardware query; it is now explicitly stubbed.
No inference/model/GPU allocation was run.

The first SSR bundle lacked the `localeTag` export required by the real estimate
module; the translation fixture now supplies it. Render/handler checks then
passed. The first watchdog run was cancelled because its production interval is
unreferenced and the mock transport has no socket; a bounded test-owned timer now
keeps the event loop alive. The production watchdog was not weakened. All five
interval/cancellation cases subsequently passed.

The uv runner reported existing dangling site-packages directories. Pytest's
ambient plugins emitted pynvml/asyncio warnings; no dependency changes were made.

## Residuals and handoff

Native CUDA/HIP/SYCL compilation, real-engine parsing/loading and GPU/model
generation were not run in this unit. The CPU parser fixture does not qualify the
compiled native engine, mapped-pack capability digest, or Spin8. The parent's
native worktree must compile and qualify its combined changes separately. No
native allowlist/version changes are included here.

The new UI checks are React SSR plus actual handlers, not packaged WebView2 or
browser layout/keyboard qualification. The parent GUI lane owns that integration
gate. Real-Harness watchdog end-to-end cases remain skipped; the portable tests
verify the production watchdog with transport fixtures. Separate filesystem
volumes are emulated; real same-volume identity and hard links are exercised on
the test filesystem. No multi-drive mounted-volume integration run was attempted.

Self-review-event: qa_defect. Evidence and minimal fixture corrections are above.
Review-only governance decision: no AGENTS, skills or SOP changes. Rejected:
lowering assertions, deleting failed cases, native capability claims based on
source matching alone, or changing the installed app to test this intake.

## Final checks (2026-11-07 continuation)

All five implementation/verification steps completed in the existing main WIP
after the interruption. Parent's new GUI/native worktrees were not edited.

| Check | Final result |
| --- | --- |
| Four setup unittest modules above | 253 run: **252 passed**, one expected Linux-sysfs skip, 29.061 s |
| `-m unittest discover -s tests/terminal -p test_pack_space.py` | **1 passed**, allocated partial-pack credit |
| CPU parser + bounded resource pytest | **51 passed**, no skips; retained r1 evidence above |
| Host runner with `local-small-context`, `annotations-32`, `local-silence-limit`, `agent-watchdog`, `local-models` | 39 run: **36 passed**, three explicit real-Harness skips, 20.128 s |
| `tsc --noEmit` after the shared recommendation cleanup | **PASS** |
| Python driver / private Node versions | **3.12.10 / 24.22.2** |
| Private Node SHA-256 | `1c331340fa6cac5e4294725959070a143fa0507195a78ad77eed7943f719aac9`, matches existing pin |
| Existing installer SHA-256 after tests | `b77c1837c0829ff221a8de0fc4df21f898f7f45c4a8ca0f819f1a60dd5f1b87b`, **unchanged** |

Final Host scratch: `C:/Users/downl/AppData/Local/Temp/opencode/strata-hybrid-PiZ0zv`.
Earlier successful standalone watchdog scratch: `strata-hybrid-wOLcr7` in the
same parent. The failed fixture runs and their causes remain recorded above.
The Python driver's version is independent of the packaged private CPython.

Self-review-event: ticket_completed, qa_defect, local_fix. Final evidence: 340
passing test cases across the listed commands, four explicit skips, typecheck,
diff review and installer hash equality. The repeated fixture corrections are
contained to this task's tests. No governance or dependency updates are warranted.
The CPU parser uses the production block verbatim; the watchdog uses the real
interval; the UI uses the actual component and handlers. No regex-only runtime
claim, real engine/Harness claim, or visual browser qualification is made.

Commit boundaries: disk/preflight + affected test fixtures and this log; small
context UI + tests; local override + tests/docs; Q36 reserve refusal + CPU parser
test. Status/diff/recent-log checks and staged whitespace checks precede commits.
Parent independently reviews these scoped ports; the larger GUI/native 32 GB /
16 GB and Spin8 release objectives are still owned by the parent lanes. Next:
reconcile these ports into those lanes, compile the changed native source before
runtime claims, and run the parent GUI browser gate. No installed app/runtime,
manual-startup policy, native mapped-pack allowlist, feed, tag or release changed.

## Intake commits

* `0adfd00a` — `[Other] integrate audited setup disk destination checks`, port of
  `c02303b4` relative to parent 2 with newer main pack/model logic retained.
* `e4b75273` — `[GUI] integrate small model context bounds`, missing contributions
  from `c856522f` plus capped recommendation/reset behavior and render tests.
* `7462de07` — `[GUI] integrate bounded local silence override`, port of
  `9df2a96a` onto the current 30-minute local policy.
* The commit containing this final log entry, `[Engine] refuse unsupported Q36
  reserve arguments`, ports only the still-applicable refusal from `3b7241f4`
  and adds executable CPU parser evidence. Its exact hash is returned in the
  handoff (the commit cannot embed its own hash).

No commit hook failures occurred in the first three commits. The staged files
matched their listed scope and passed whitespace checks. The final native commit
contains only the five-line parser refusal, its CPU test, and this mapping entry.
