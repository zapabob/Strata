# GUI consistency — E3-B + E4-B — 2026-11-06

Owner: OpenCode. Worktree `H:/Strata/worktrees/gui-consistency-20261106`, branch
`fix/gui-consistency-20261106`, base `ca3ab40a`. Installed app source is
`04fe91d0` / `0.5.2-local.1`. Status: SOURCE_READY_FOR_INDEPENDENT_REVIEW.

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
