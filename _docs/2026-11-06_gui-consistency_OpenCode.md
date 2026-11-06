# GUI consistency — E3-B + E4-B — 2026-11-06

Owner: OpenCode. Worktree `H:/Strata/worktrees/gui-consistency-20261106`, branch
`fix/gui-consistency-20261106`, base `ca3ab40a`. Installed app source is
`04fe91d0` / `0.5.2-local.1`. Status: SOURCE_READY_FOR_SPEC_THEN_QUALITY
(adapter/contract invariant follow-up to `e8a9370d`; see the final section).

## Requirements and plan

Goal: make native serving choices and saved-profile hardware provenance consistent
across the editor, validation and execution boundaries. This is source work for
parent review and later real E2E; it does not qualify native inference on 32 GB RAM /
16 GB VRAM. No native binary/model operation or installed-app change is authorised.

1. Reproduce E3-B ignored ordinary KV and incompatible settings admission, plus
   E4-B cold fallback identity/default restoration, against production code.
2. Implement one family/adapter serving policy and apply ordinary Q38 KV to actual
   launch configuration. Preserve Q36 negotiated capability and local manifest adapters.
3. Implement process-local verified CPU topology retention and explicit client
   identity readiness. Guard profile writes and defer defaults without losing drafts.
4. Run focused production/component regressions, strict typecheck and diff review.
5. Record evidence, unresolved contradictions, self-review and exact source commit.

Acceptance: incompatible settings fail before replacement/persistence/job creation
where synchronously knowable; saved incompatible data remains visible until cleared;
no unsupported capability union. Complete CPU topology alone authorises identity;
compatible transient failure retains verified shape with cached status; cold failure
never creates profile provenance. Late replies cannot take ownership of another model.

## Standards, sources and decisions

Applied supplied home AGENTS, this worktree's root AGENTS, compatible canonical
`CLAUDE-FABLE-5.md`, Common / Start Gate / Skill Selection / Security / Application
Development / WebApp / Frontend Design / TypeScript SOPs. Skills: supplied MILSPEC
baseline, systematic-debugging, test-driven-development, plan-mode; completion
self-review follows the PC baseline. No Goal/Todo API is exposed; this log tracks
the goal. Existing controls/styles and `docs/DESIGN.md` were inspected. Host README
links to absent `apps/handoff.md`; actual source/tests and task audits supply context.
No formal compliance claim. Local source is the authority for this bounded fix;
no new external version/package-trust claim or dependency version change.

Read-only inherited findings: `task-E3-audit.md`,
`task-E4-hardware-identity-audit.md`, `task-E3-C-profile-label-triage.md` in the
specified cuda135 worktree. Those files remain research only. U1 `f30b8cf0` and
E3-C outcome ownership already exist here and are preserved.

Trust boundaries: untrusted settings JSON/argv into native launch; hardware probe
output into durable profile identity. Keep existing auth, no-acquire and strict
model/hardware filtering. No disk topology cache or old-profile migration.

## Commands and verification

- Initial `git status --short --branch`: clean intended branch; `git log --oneline -10`
  confirms base and inherited fixes.
- Read-only installed `node/node.exe --version`: `v24.22.2`.
- Locked host dependencies: Node 24.22.2 + system npm CLI, `ci --ignore-scripts
  --no-audit --no-fund --offline`: PASS, 80 packages. npm reports that package.json
  allowScripts overrides .npmrc; install scripts were explicitly disabled.
- Tests use `_docs/hybrid-intake-tests.mjs` (isolated home/fs guard, serial).

## Changed files / implementation / results

Resumed after interruption without discarding this worktree's WIP. All five plan
steps are complete for the source unit; parent review and real E2E remain open.

Production reproductions before fixes: `strata-hybrid-Sm4GqG` ran 16 tests, all
failed at the expected missing contracts. Q38 actual launch config retained old
`k8v4` instead of explicit int8/q4_0/fp16; same-value k8v4 failed saved-config
roundtrip. Incompatible settings saved successfully. Partial CIM was accepted as
verified, and good→empty lost physical topology. Cold empty/malformed lacked an
explicit unavailable source.

Initial test harness attempt `KmmfqS` also failed, but two categories were harness
errors, not accepted product reproductions: an incomplete esbuild OS/catalog
boundary and a POSIX-only server-path matcher. Correcting those produced the
behavioural failures above.

Mounted production ModelRun RED (`NGoGhZ`): 8 passed, 6 failed. Five are E4-B
behavioural failures: unknown provenance save enabled; verified defaults never
restored; selection while waiting never restored the current default; direct
save/update handlers performed validation and persisted the fallback identity.
The sixth was Edge launch timeout, not a product result. The next E4 check
(`jokDIq`) passed all five new cases plus the detector cases, but two older browser
cases failed before assertions (Windows identity discovery / file navigation).
The isolated runner now preserves the original Windows USERPROFILE as an explicit
test-only input for the two browser fixtures. Browser user-data, Local/Roaming,
Strata, workspace and temporary paths remain isolated. No timeout was increased.

Mounted E3-B RED (`J2dAk3`): 11 inherited tests passed, six new cases failed:
missing FP16 option, unknown-KV unchanged shortcut, Q38 selector on Q36/DeepSeek/
unknown, and incompatible stored value hidden without a clear action.

Intermediate failed gates: missing closing brace in the new policy module stopped
three files at import (`Rjmnip`), corrected; first policy run (`JsKQWb`) passed
23/26 but revealed `writeModelConfig` merging the old user KV over the new saved
choice. The explicit choice now replaces that old user flag too. Typecheck then
found three redundant `supported === false` checks after a narrowing return;
removed without changing their enablement.

Intermediate GREEN (`Iy9udq`): 42/42 across native-serving-policy,
native-ui-ownership and run-selection-lifecycle; zero page exceptions. Server
regression (`L4KIzJ`): 45/45 across CPU readiness, native policy, inherited U1,
config persistence, cancellation ownership and Q36 negotiated layout. These are
controlled production-boundary/component tests, not real Host/model E2E.

The next focused regression (`reJlC4`) passed 74/79 and exposed five failures.
DeepSeek `parallel` is supported by `serve/server.py:3914–3958`; an initial policy
assumption that it was Qwen-only was wrong and was removed. Its original tests
are unchanged. Two Qwen vision fixtures deliberately had no catalog or architecture;
they now name `arch:qwen4exp` rather than asking policy to infer from `model_name`.
Two captured-file race tests exposed a second configuration read introduced by
early admission. Load now carries the same captured text from synchronous
admission into the production builder. Valid/invalid captured settings keep their
original contract even if the on-disk future settings change. The corrective run
`KGwnft` passed 44/44; all affected cases also passed in the final run.

## Implemented contracts and changed files

E3-B: `server/native-serving-policy.mjs` chooses the cache contract from saved
architecture/family, then the selected catalog family. No filename, model label,
weight quantization or GPU capability inference. Ordinary Q38 supports exactly
fp16/int8/q4_0/k8v4; per-side KV and every explicit Spin8/capsule option are refused
for ordinary serving. Q36 retains independently negotiated K/V FP32/FP16 and
unknown-engine legacy FP32. DeepSeek retains its packed cache, router5/router6 and
existing concurrent-request support. PrismML/TurboQuant still use their own
unchanged, separately tested manifest/payload/geometry policy.

`server/native-control.mjs` projects this policy into metadata/settings, validates
PATCH via `saveChecked`, checks load/install before job creation where capability
is already knowable, and rechecks before picture/drafter acquisition or replacement.
Q36 negotiation occurs before acquisition/replacement; a request requiring that
asynchronous probe can still create a job before its rejection. `server/index.mjs`
has only the awaited save-service call change. Unknown/incompatible settings remain
readable with named issues and explicit clearing of every field/argv/user-argv
representation. Synchronous internal `save` remains conservative for unknown Q36.
The inherited U1 saved-KV function and its tests remain intact.

The actual load builder applies the explicit ordinary KV to argv and the explicit
user override, retaining GGUF paths. READY persists just that choice into current
settings, respecting later file edits. No redundant prepare/download for KV-only
changes. NativeModels renders only policy-approved ordinary choices (including
FP16), requires an explicit choice for unknown saved ordinary KV, and passes it on
direct load. NativeSettings shows incompatible stored values, clear actions and
issues rather than a false default/newer-engine remedy. Its existing request-owner
guards remain. `src/lib/native.ts` carries the DTO additions.

Two necessary one-line producer changes in `GuidedSetup.tsx` and
`NativeLocalModel.tsx` condition their automatic `kv:int8` on the same server
policy. Without these, tightening admission would break Q36/DeepSeek setup by
rejecting a hidden Q38 default. The manual-start flow and preview ownership logic
are unchanged; the actual mounted local-Q36 preparation payload is tested.

E4-B: `server/cpu-topology.mjs`, `hardware.mjs`, `device-probes.mjs` retain only a
complete parsed CPU shape, bound to platform/architecture/Node CPU models/logical
count. Partial socket sets and mismatched totals are unverified. Socket order is
stable. Good→failure retains the compatible verified shape as `topologySource:
cached`; a cold failure says `unavailable`, a new successful topology says `live`.
Binding changes invalidate the shape; sequence/generation ownership protects
against late failed/successful probes. Whole-hardware response caching also cannot
overwrite a newer response. No disk cache or old-profile rewriting.

`src/lib/types.ts` adds source status. `run-profiles.ts` adds nullable validated
`profileComputerIdentity` while keeping the strict identity bytes unchanged.
`run-selection.ts` accepts unresolved identity without matching a default.
ModelRun keeps manual configuration/load available, blocks profile creation,
update and default writes in UI and handlers, uses the existing explicit bounded
refresh, and explains unavailable/cached hardware. Default restoration waits for
verification, occurs once per model, and preserves later user drafts/manual-load
intent. Exact pre-existing session/default ownership may be recognised only after
verified hardware/model equality; unrelated drafts and late model responses stay
owned by their original selections. Old fallback-bound records remain untouched.

Tests added: `native-serving-policy.test.mjs`, `cpu-profile-readiness.test.mjs`.
Tests extended: `native-ui-ownership.test.mjs`, `run-selection-lifecycle.test.mjs`,
`helpers/native-fixture.mjs` (recorded stop/start/profile effects), and the two
Qwen fixture architecture declarations in `native-ds-args.test.mjs`.
`_docs/hybrid-intake-tests.mjs` adds only the read-only Windows profile input for
isolated browser identity discovery. All edits used apply_patch.

## Final verification

Node executable for every check:
`C:/Users/downl/AppData/Local/Programs/Strata/node/node.exe` (24.22.2, read-only).
Checks were serial with the isolated runner/fs guard. The later handoff's 3 GiB
available-RAM floor was checked with Win32_OperatingSystem before each final
test/typecheck command; the explicit initial reading was 3.36 GiB. This is not a
continuous-memory measurement. Browser fixtures use isolated profiles and
`--disable-gpu`; no real engine or hardware-topology query occurs in tests.

Final CPU/production-boundary command (workspace root):

```text
node _docs/hybrid-intake-tests.mjs native-serving-policy.test.mjs cpu-profile-readiness.test.mjs native-control.test.mjs native-settings.test.mjs native-settings-response.test.mjs native-settings-file.test.mjs native-ds-parallel.test.mjs native-ds-args.test.mjs local-backends.test.mjs model-run.test.mjs annotations-32.test.mjs native-installed-kv.test.mjs native-config-persistence.test.mjs native-load-cancel.test.mjs q36-kv-layout.test.mjs native-run-observation.test.mjs native-job-diagnostics.test.mjs native-onboarding.test.mjs run-selection.test.mjs strata-engine-backend.test.mjs
```

PASS **146/146**, zero failed/skipped/cancelled, 22.447 s. Isolated scratch
`C:/Users/downl/AppData/Local/Temp/opencode/strata-hybrid-YUbY5n`.

Final mounted-component command (workspace root):

```text
node _docs/hybrid-intake-tests.mjs native-ui-ownership.test.mjs run-selection-lifecycle.test.mjs
```

PASS **34/34**, zero failed/skipped/cancelled, 101.452 s; zero uncaught page
exceptions asserted by fixtures. Scratch `.../strata-hybrid-d7C3yX`. These mount
production components with controlled boundaries; they are not real Host E2E.

`node node_modules/typescript/bin/tsc --noEmit` in `apps/host`: PASS after final
source edits. `git diff --check`: PASS (Git only reports existing CRLF conversion
notices). Total final focused tests: **180 passed**. No full-suite claim.

## Self-review and handoff

Self-review-event: `qa_defect`, `local_fix`, `ticket_completed`; review-only.
Evidence is the RED/GREEN sequence, failed harness/typecheck gates, captured-file
regression and corrected DeepSeek parallel assumption above. Accepted prevention:
tests traverse actual production admission/builders and real component handlers,
asserting side-effect counts and asynchronous ownership rather than just request
shapes. Rejected: inference from filenames/GPU, capability unions, loosening
computer identity, old-profile migration, pretending fixtures are real E2E, or
weakening tests to accommodate the captured-file regression. No governance,
AGENTS, SOP or skill update was made. Parent review remains independent.

Rollback: revert this unit's scoped source commit after preserving later work.
No installed application, engine, release guard, B1/B2/kernel, package version or
lockfile change. No app stop, engine pause/restore, model/GPU load, push or release.

## Residuals and next action

Parent independent review and actual Host/UI E2E remain required. Parent owns the
new TelemetryPopover, untranslated chat-error and layout findings in its separate
checkout. This unit did not edit those files, store error handling or locales.
New policy/readiness text currently uses English fallback; locale integration is
explicitly deferred to avoid the parent's overlap.

General chat and loading/status contradictions are not closed by these source
tests. Inherited cancellation/ownership/observation checks passed, but no naturally
occurring real-Host race, live running-model preservation, actual negative HTTP
PATCH, or actual engine KV observation was exercised. Native model startup,
full-window generation, quality and 32 GB / 16 GB reliability remain NOT_RUN.
Full suite, production/native builds, screenshots/responsive/accessibility and
real E2E are NOT_RUN by the current source-only authorisation.

Next: parent reviews this exact source commit, performs its merge, then runs the
isolated real-Host acceptance from the inherited E3/E4 audits. Any live maintenance
window and engine pause/restore belongs to the parent. Preserve the prior failed
fallback-bound profile as evidence; it is not automatically rehabilitated here.

## SPEC review F1/F2 follow-up — 2026-11-07

Scope: the two P2 findings on `14a07fd5a7ec44abe241aa455d91f045decb8096`.
Continued the existing worktree/WIP after interruptions. Same instructions, SOPs,
systematic-debugging/TDD and self-review baseline apply. No delegation or parent
checkout edits. The objective is a narrow source correction for SPEC re-review.

### Reproduction before the fix

Modified the actual production-boundary tests first. Final RED command was
`node _docs/hybrid-intake-tests.mjs native-settings-file.test.mjs
native-serving-policy.test.mjs`, using the same read-only Node 24.22.2 executable.
Scratch `.../strata-hybrid-KP7gpU`: **19 passed, 10 failed**, 3.891 s.

F1 reproduced synchronous journal writes and a new job for malformed JSON,
non-object JSON, invalid known values, incomplete Spin8 pairs and Spin8 off with
a capsule. The non-object case also reached a configuration repair write. Tests
instrument `writeFileSync` and the existing stop/start/profile/before-load spies,
with an already-ready isolated fixture model. They require zero additional jobs,
writes, control effects or process calls. Captured-file race tests additionally
prove that changing the file after the first read cannot change the admission
decision. Existing tests that expected a failed job were updated to the requested
synchronous-refusal contract while preserving valid captured-config coverage.

F2 reproduced both catalog-derived Q36 (no arch, neutral model/executable names)
and `arch:qwen36`: settings negotiated and saved f16, but Load returned a false
unverified-format error without probing. The negative Q38 architecture case with
Q36-looking names was incorrectly routed into the Q36 private-cache contract.
The valid Q36 fixtures explicitly request one concurrent slot, preserving the
existing private-cache limit rather than changing parallel defaults.

The first RED run (`dQLuEC`, also 19/29 passed) produced post-test ENOENT noise
because incorrectly admitted jobs outlived fixture deletion. The fixture cleanup
now drains any such jobs before deleting task-only files. The second RED retained
all ten behavioural failures without that cleanup noise.

### Corrections

`server/native-control.mjs` now calls the throwing captured-config validator
before serving admission and `begin`. Invalid syntax/known values/Spin8 combinations
cannot create or persist a job. A valid load still carries its original captured
text into the builder; it does not reread a different future configuration.

Every Q36 decision in this Host's settings/load/build/tuning/lifecycle paths now
uses the shared actual serving policy. This includes capability probing, argv
preparation, physical admission, startup-log ownership and the no-safer-retry
rule. DeepSeek classification in the same Host paths also uses that policy.
There is no executable/model-name family fallback in `native-control.mjs`.
A selected Q36 run carries canonical `arch:qwen35moe` into the downstream server;
the user's saved architecture/name/executable are not rewritten.

`server/native-settings.mjs` aligns file syntax with the existing PATCH syntax
for f32. The syntax registry recognises f32 without a filename heuristic; actual
per-adapter policy remains the admission authority. Q38 f32/per-side settings
still fail before save/job creation, and Q36 unknown-capability views remain
FP32-only. This additional legacy test initially failed twice after the first
F1/F2 repair (`HEB389`: 29/31 passed), then passed with the syntax alignment.
No engine capability union or new executable capability is introduced.

Changed files in this follow-up: `server/native-control.mjs`,
`server/native-settings.mjs`, `tests/native-settings-file.test.mjs`,
`tests/native-serving-policy.test.mjs`, `tests/q36-run-contract.test.mjs`, and this
log (all Host-relative paths except the log). The Q36 contract test only replaces
its obsolete failed-job expectation with synchronous refusal plus unchanged
journal/config/callback assertions. Engine/native contract implementation is
unchanged.

### Verification and failures

The first expanded focused run (`jXFOuL`) passed **129/130**. Its one failure was
the inherited Q36 test expecting a failed job for an explicit q8_0 cache flag;
the production path already refused synchronously. The updated test strengthens
its boundary assertion rather than weakening admission.

Final command from the workspace root:

```text
node _docs/hybrid-intake-tests.mjs native-settings-file.test.mjs native-serving-policy.test.mjs native-settings.test.mjs run-config-check.test.mjs native-control.test.mjs native-installed-kv.test.mjs native-config-persistence.test.mjs native-load-cancel.test.mjs native-ds-parallel.test.mjs native-ds-args.test.mjs q36-kv-layout.test.mjs q36-load-lifecycle.test.mjs q36-run-contract.test.mjs q36-capabilities.test.mjs q36-private-cache.test.mjs q36-progress.test.mjs native-run-observation.test.mjs
```

PASS **130/130**, zero failed/skipped/cancelled, **24.104 s**. Scratch:
`C:/Users/downl/AppData/Local/Temp/opencode/strata-hybrid-TuVzjc`.
Coverage includes the new positive/negative family cases, explicit legacy FP32,
captured-config ownership, cancellation, private caches, startup observations,
no parallel-drop Q36 retry, DeepSeek and inherited U1 metadata.

`node node_modules/typescript/bin/tsc --noEmit` in `apps/host`: **PASS** after the
final source edits. Both test and typecheck commands enforce the handoff's
3 GiB available-RAM precondition. `git diff --check`: **PASS**, apart from Git's
informational CRLF conversion notices. Test/build commands use the installed
Node binary read-only; all model/process/network boundaries are controlled.

Self-review-event: `rework_returned`, `qa_defect`, `ticket_completed`; review-only.
The prior coverage did not distinguish synchronous rejection from a failed job,
and its Q36 launch fixtures already carried recognisable identity. Added direct
journal/write-effect assertions and neutral-name catalog/alias fixtures. Rejected:
accepting the late error as an early refusal, suppressing a Q36 capability error,
borrowing identity from filenames, changing private-cache parallel limits, or
loosening negative-family tests. No governance update.

Ready for independent SPEC re-review. Real HTTP/Host E2E, engine/model/GPU runs,
installed-app changes, broad suites and releases remain NOT_RUN in this follow-up.
The earlier controlled UI/E4 results are historical evidence, not rerun here;
those source files are unchanged by F1/F2. Parent-owned telemetry/chat/locales
remain outside this lane. No app stop or maintenance operation occurred.

## Downstream F2 Python consumer follow-up — 2026-11-07

Parent SPEC re-review passed F1 and found that F2 still ended at the Host-generated
configuration. Continued from clean `a968e82add5fd6592331795a66b0aa7684dcb8f0` in
the same owned worktree. The additional Python helper/tests are explicitly
authorised. Applied the existing standards and `SOP-Python.md`; no applicable
root/serve pyproject, uv.lock or .python-version exists, and requirements.txt
specifies Python 3.10+. Selected installed Python **3.12.10** through read-only
`C:/Users/downl/.local/bin/uv.exe`, verified with `uv run --no-project --offline
--python C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe python
-B --version`. The first bare `uv` lookup failed because it is not on PATH;
locating the existing executable resolved it without installation. uv reports
two pre-existing dangling dist-info directories; they were not changed.

### Consumer inspection and root cause

Inspected the Q36 selectors and their callers throughout `serve/`, the related
Control paths, and root Python references. The admission chain is:

1. `engine_args` and CLI cache validation call `native_cache_args`.
2. `native_cache_args` selects Q36 negotiation through `server.q36_config`.
3. `child_env` derives the typed-KV requirement through `q36_config`, but formerly
   derived the private-cache requirement through a separate filename-based test.
4. `StrataEngine.__init__` checks those requirements against the actual child's
   capability/binary identity and INFO receipts before setting `known_ctx` and
   making the engine ready. Restarts reuse the captured environment/constructor.

Both former selectors allowed an executable containing `strata-q36` to override
explicit `arch:qwen4exp`. They also disagreed about model-name-only legacy Q36.
Family display/sampling tables already use explicit architecture. Control
autotune/preset family labels use MTP shape for their own tuning metadata; they
do not select these Python cache-admission gates and were not changed.

### Production reproduction and correction

The new `apps/host/tests/helpers/native-family-consumer-fixture.mjs` runs the
actual Host settings/load builder with controlled Control/process boundaries.
It exports only launch-input fields from two generated configs: explicit Q38
with a Q36-looking executable/model label, and catalog-derived Q36 with neutral
names. No model files or native executable are used, and no keys or memory-store
paths are exported.

`serve/test_native_family.py` consumes those real builder outputs with production
`native_cache_args` and `child_env`, then executes the real Python constructor
through the admission gate using the existing AST-based Q36 test harness. Only
process/OS IO and actual-binary probe results are controlled. This is a CPU
cross-language contract test, not a live-engine or browser E2E claim.

RED (`strata-gui-python-KLCNgP`): **4 failed, 2 passed**, 6.49 s. The first test
asserted the incorrect derived requirement. Strengthening it to continue into
the actual READY consumer reproduced **EngineDied at server.py:1356** for the
Host's Q38 config with a bare READY receipt. RED (`strata-gui-python-rEdeY8`):
**4 failed, 2 passed**, 7.10 s. Its environment incorrectly required both Q36 KV
and private-cache acknowledgement. The other failures covered legacy selector
disagreement and the Q36 alias. The canonical Q36 receipt/verification cases
already passed before the fix.

Production changes are minimal: new `serve/native_family.py`, the selector call
in `serve/private_cache.py`, and the `server.q36_config` wrapper/import. Both
consumers now share one rule. Explicit runtime architecture wins; canonical
`qwen35moe` and the existing `qwen36` alias select Q36. An explicit other/unknown
architecture is not reclassified from its path or label. Missing/null/empty
architecture preserves legacy executable/model hints. The helper does not read
or accept any capability claim. This also makes model-name-only legacy Q36
require the same private-cache acknowledgement as the server's Q36 selector.

Actual binary negotiation, digest rechecks, typed layout/allocation receipts,
private-cache capability comparisons and rejection-before-READY code are
unchanged. Tests retain required private-cache versions **1 and 2**, reject
missing/wrong markers, reject missing typed receipts, and prove that declared
Host capability metadata cannot replace an unavailable or different actual
binary. Unknown legacy FP32 still avoids inventing typed support.

Packaging inspection: `packaging/package_terminal.py` includes the whole `serve`
payload and copies directories recursively, so the helper needs no new module
allowlist. This is static source inspection; no package/build/install was run.

### Final checks and evidence

Added `_docs/gui-consistency-python-tests.mjs` as the bounded driver. It uses uv
offline with the existing interpreter, task-local state/home/cache/temp paths,
no downloads, disabled GPU visibility, and disabled pytest plugin autoload.
`--confcutdir=serve` avoids the root conftest's unrelated thinc import; the driver
provides its own profile isolation. Python bytecode and pytest cache writes are
disabled. Node's actual Host fixture receives this same isolated environment.

Final command, using installed Node 24.22.2 read-only:

```text
node _docs/gui-consistency-python-tests.mjs serve/test_native_family.py serve/test_q36_kv_contract.py
```

PASS **16/16**, **14.37 s**, no skips. Scratch:
`C:/Users/downl/AppData/Local/Temp/opencode/strata-gui-python-4Yj3pO`.
This includes six new test methods (with family/receipt subcases) and ten existing
actual-binary/KV receipt tests. The earlier bounded GREEN was 16/16 in 12.42 s;
the final run additionally covers both private-cache protocol requirements.
Available RAM was checked against the 3 GiB floor before test runs.

Fresh checks through the same uv/Python path:

```text
python -B -m black --check serve/native_family.py serve/test_native_family.py
python -B -m flake8 --isolated --max-line-length=88 serve/native_family.py serve/test_native_family.py
python -B -m flake8 --isolated --select=E9,F63,F7,F82 serve/server.py serve/private_cache.py
```

All PASS. Black/flake8 initially found formatting/line-length issues in the new
test; they were corrected with apply_patch and the checks rerun. Existing large
Python files received critical-error lint only, without unrelated reformatting.
`git diff --check`: PASS, with only Git's CRLF conversion notices. The bridge and
driver were both executed successfully by the final test command.

Changed files: the three production Python files above, `serve/test_native_family.py`,
the task-only Python test driver, the Host fixture bridge, and this log. GUI/Host
production policy, telemetry/chat/locales, native kernels and installed files are
unchanged. No dependencies or interpreter were installed or updated.

Self-review-event: `rework_returned`, `qa_defect`, `ticket_completed`; review-only.
The missing gate was cross-language consumption of a correct generated config.
The new test carries that actual builder output through both Python requirements
and the real pre-READY consumer. Rejected: merely asserting generated JSON,
disabling private-cache confirmation, accepting claimed capability without an
actual-binary check, or resolving this by renaming paths. No governance update.

Ready for parent SPEC closure review. Actual native startup/generation, GPU/model
work, full suites, package builds, browser E2E, and live maintenance remain NOT_RUN.
The constructor's real admission code runs with controlled child IO; no native
process, model load, GPU probe or installed-app stop occurred. Prior GUI/E4 and
F1 results are historical/parent-reviewed evidence, not a new all-GUI qualification.

## Adapter / retained-contract invariant — 2026-11-07

Scope: the confirmed P2 contradiction after `e8a9370d8ca3e3864dfd6d066b8c09e045ccd08a`:
explicit Q38 architecture plus a retained Q36 run contract could disable both
requirements while retaining the expected Q36 binary digest. This round changes
only Python family/consumers/tests and this log. The same supplied instructions,
canonical context, SOPs, systematic-debugging/TDD and self-review requirements
apply. No delegation. Python 3.12.10 was freshly rechecked through the existing uv
path; Node 24.22.2 and the isolated CPU driver remain unchanged.

### Boundary review and decision

Re-read all reads of `q36_run`, both environment requirements, the expected binary
digest, native cache argument preparation, child-env construction, and the native
constructor/restart path. The earlier family predicate did not validate the
relationship between architecture and retained execution metadata. It also left
the constructor reading mutable inputs at different stages of admission.

The invariant is now represented by one frozen `NativeAdmission` value:

- Non-Q36 admission cannot retain a Q36 digest, generation or private-cache
  requirement. Contradictory explicit architecture and a Q36 contract are errors.
- A retained contract must have the consumed schema/identity structure: schema 1,
  Q36 backend family, well-formed optional digest/generation, and consistent
  family/digest identity for a declared typed-KV expectation. Metadata is an
  expectation to verify, never an engine capability grant.
- Unknown or malformed explicit architecture with a retained Q36 contract is
  rejected. With no explicit architecture, a structurally valid retained Q36
  contract keeps Q36 verification armed; it cannot become an unverified generic
  start. Contract-free legacy name hints retain their prior behaviour.
- Both config argument layers contribute their requested private-cache requirement.
  At constructor entry the projected requirement cannot be lower than the actual
  argv's requirement. Older private-only environments retain their acknowledgement
  check without manufacturing typed-KV capability.
- One captured argv/environment snapshot supplies binary verification, Popen and
  READY admission. Missing/mismatched actual receipts remain failures.

This validates the consumed identity/requirement fields, not the authenticity of
arbitrary run metadata. Actual help-marker validation, binary digest comparison
and recheck, KV geometry/allocation receipts and private-cache marker comparison
remain the authority for engine support.

### Reproduction evidence

Extended the existing CPU cross-language test. It combines the actual Host
builder's Q38 configuration with its actual Q36 contract, then traverses the real
Python argument/environment/constructor code with controlled child IO.

RED `strata-gui-python-ity0mW`: **7 failed, 7 passed**, 13.91 s. The exact reported
contradiction produced **one Popen and accepted READY**, with no Q36 capability
probe. Further failures proved that config consumers ignored the conflict,
malformed/unknown identities could fall back, malformed retained contracts reached
spawn, corrupted environment projections were not rejected early, contract-only
legacy identity disabled proof, and changing the original environment after
verification could suppress the private-cache receipt check.

The first invariant repair closed those cases. Boundary inspection then found
that `engine_args` merges `user_args`, while the old private requirement looked
only at `args`. Added real-consumer tests before fixing it. RED
`strata-gui-python-lXk6FR`: **2 failed, 14 passed**, 28.78 s: private requirements
were lost from the user layer / actual argv projection. Both now fail closed or
retain the requested acknowledgement as appropriate.

The same snapshot review exposed caller-owned argv mutation after binary proof.
A controlled Popen callback could change F16 to F32 and make an F32 receipt pass.
RED `strata-gui-python-S6hNec`: **1 failed, 17 passed**, 29.75 s. Copying argv at
constructor entry closes that mismatch alongside the environment snapshot.
These are controlled reproductions, not claims about a naturally observed race
or live engine execution.

### Implementation

`serve/native_family.py`: shared immutable requirements and config/environment
validation. `is_q36_config` and `private_cache.required_capability` consume the
same validator. `serve/server.py`: native KV preparation takes its expected digest
from that value; `child_env` validates before device/environment work and projects
all Q36 fields together; the constructor captures argv/env and validates before
binary probing, orphan cleanup or Popen, then uses the same requirement at READY.
`serve/private_cache.py` delegates requirement calculation to the shared value.

`serve/test_native_family.py`: relationship matrix across all config consumers,
actual generated-config-to-Python rejection, malformed/unknown identities and
contracts, direct/inherited environment consistency, legacy private-only env,
contract-only legacy identity with actual binary proof, user-argument propagation,
and argv/env snapshot ownership. Every conflict case asserts no native Popen or
accepted READY; applicable cases also assert no probe or orphan-cleanup callback.
Valid Q38 lookalike paths and genuine Q36 receipts remain covered.

### Final checks

```text
node _docs/gui-consistency-python-tests.mjs serve/test_native_family.py serve/test_q36_kv_contract.py
```

PASS **28/28**, **32.17 s**, no skips. Scratch:
`C:/Users/downl/AppData/Local/Temp/opencode/strata-gui-python-opdZxJ`.
This is 18 consumer tests and 10 existing actual-binary/KV tests, with additional
identity/receipt subcases. Actual model/engine processes are replaced at their IO
boundary; the producer fixture executes the real Host builder with controlled
Control. Test runs checked the 3 GiB available-RAM floor first.

Fresh validation through the fixed uv/Python path:

```text
python -B -m black --check --diff serve/native_family.py serve/test_native_family.py
python -B -m flake8 --isolated --max-line-length=88 serve/native_family.py serve/test_native_family.py
python -B -m flake8 --isolated --select=E9,F63,F7,F82 serve/server.py serve/private_cache.py
```

All PASS. Black initially reported formatting differences; edits were applied
with apply_patch and the check passed before the final test run. The pre-existing
uv dangling-dist-info warnings remain informational. `git diff --check`: PASS,
with only Git's CRLF conversion notices. No dependency, driver or runtime update.

Self-review-event: `rework_returned`, `qa_defect`, `local_fix`, `ticket_completed`;
review-only. Three cross-layer review gaps justify the relational invariant and
producer-to-consumer tests, rather than another independent flag special case.
Rejected: silently deleting retained metadata, converting unknown architecture
into generic mode, trusting claimed capability, skipping the actual binary probe,
or mutating user settings to reconcile a conflict. No governance files changed.

Ready for parent SPEC, then QUALITY. Python native admission is proven before
native Popen/probe/orphan-cleanup for these invalid cases; Host job lifecycle and
GUI production source were not changed in this round. Full suites, live HTTP/UI
E2E, native/model/GPU work, installs, release/push and maintenance operations remain
NOT_RUN. No installed app or live engine was stopped. Earlier F1/E4 results remain
historical/parent-reviewed evidence, not an all-GUI or 32 GB / 16 GB qualification.
