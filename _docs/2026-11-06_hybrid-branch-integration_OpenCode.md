# Reviewed hybrid branch integration

## Overview and scope

Implemented the reviewed intake from `codex/strata-hybrid-memory-20261102`
(source tip `cd297d03ee7b4e0923eeab4846a940dabb716d71`) in
`H:/Strata/worktrees/hybrid-integration-20261106`, branch
`integration/hybrid-features-20261106`, based on `ff340b92`.
OpenCode owns this integration worktree. The parent owns the main-line merge,
other intake, Spin8, full real GUI E2E and release qualification.

The objective is to carry all eleven reviewed missing/partial contributions
into a reviewable local commit while retaining newer main-line consumers.
No source branch/worktree was rewritten. No application installation, release,
push, publication, live model launch or real web-provider request was performed.
The dependency install below is confined to this worktree's host package.

## Applied standards and acceptance

Read the canonical `C:/Users/downl/_docs/prompts/CLAUDE-FABLE-5.md`, the supplied
home baseline, this worktree's AGENTS, AI_REFERENCE, host README, design-system
notes, SAFETY, existing implementation log, code, tests and all eleven diffs.
Incompatible legacy identity, environment and tool descriptions in the canonical
prompt defer to the actual harness instructions. The host README's link to
`apps/handoff.md` is missing; the local design-system notes and implementation
were used instead. The named frontend-ui-engineering skill was not installed
under the available shared skills; existing UI components/tokens were used.

Selected SOPs: Common Engineering Standard, Implementation Start Gate,
Skill Selection, Security, WebApp Development, Application Development,
Frontend Design and TypeScript. Applied skills: supplied MILSPEC baseline,
supplied Deep Research baseline, qa-engineer and agent-self-review-evolution
(review-only). No new package-trust claim or outside research was needed for
this source-backed intake. No formal MILSPEC compliance is claimed.

Acceptance: both observation consumers remain usable; capture is opt-in and
does not change launch options; explicit search sends only the entered query;
references cannot activate autonomous tools or match skills; skill import is a
confirmed instruction-only preview with durable scope; key-save success waits
for persistence; estimator APIs preserve main's public fields while handling
bitmap recurrence, MTP, padding and unknown geometry consistently. Tests use
isolated profiles and the existing recursive-cleanup guard.

## Source mapping and implementation decisions

| Source commits | Integrated contribution and reconciliation |
| --- | --- |
| `6745c6fb`, `75ede8f1`, `e591c654` | Capture primitives and native/supervisor lifecycle hooks. New `lifecycle-observation.mjs` holds the branch API. Main's `run-observation.mjs` and its tests remain byte-identical in Git. Native source streams and packaged metrics feed the capture; first terminal failure and numeric exit code survive wrapper errors. Existing Q36 startup/KV, pictures, retry/adoption, settings ownership and restart behavior are retained. |
| `b95e0eec` | Attach-only `bench/strata-16gb/run.mjs`, schema and tests. Source README becomes `LIFECYCLE.md`; the original README keeps the baseline workflow and links to it. Original `measurement-schema.json`, capture-baseline, run-windows and results retain their contracts. |
| `a36284dd`, `169237a7` | Explicit Search web dialog, guarded host result capabilities, plain-chat references, research handoff and sent-user source links. Current chat persistence/reattachment, quotes, parked messages, IME, deliverables, selection ownership and supervisor agent routing are retained. `/research` still takes the agent route when the supervised engine can run it; plain chat opens explicit search. |
| `079f8588`, `36014f4b` | Instruction-only SKILL.md preview/import with trigger, enabled and workspace choices. A successful POST's returned skill list is authoritative; no follow-up GET can relabel a successful import as failed. The newer always-on/skill-name matching hint in the existing editor is retained. |
| `3f013772` | Key save awaits PUT and keeps the typed key plus visible error after failure. Success clears the key and shows the toast only after persistence. |
| `d91c058d` | Historical source verification log retained as `_docs/2026-11-02_explicit-web-search-skill-import_Codex.md`. Those earlier runs are source history, not new verification claims. |
| `cd297d03` | Bounded recurrent bitmap/scalar retention and SSM/MTP metadata, geometry estimator and tests/documentation ported together. Public `model-memory.mjs` adapts both API shapes to `model-memory-geometry.mjs`. Main's `memoryPlan`, `local.nFullAttention`, generic-name fallback and custom-name reinspection remain. Historical Task B log is retained. |

Targeted `git cherry-pick --no-commit` applied the source patches. Conflicts
were resolved with `apply_patch`, by combining actual hunks rather than taking
whole older Chat/store/native files. Temporary baseline/compatibility moves
kept the overlapping added files available during application; temporary paths
are absent from the final tree. One preparation patch named the nonexistent
`run-observation.schema.json` on main and failed atomically; the original schema
is actually `measurement-schema.json`, which was preserved.

Additional integration repairs: the newer native lost-runtime reconciliation
now ends an observation, and an unsuccessful unload records error rather than
stopped. Native actual context accepts only positive numeric safe integers.
Packaged executable identity uses the already resolved engine path. The skill
dialog binds confirmed markdown to its preview and rejects late file/preview
updates from a prior editor generation. These have behavioral regressions.

The main estimator's legacy index-list classification helper remains exported
for explicit callers, but raw GGUF is parsed as the branch bitmap/scalar format.
Main's previous unknown-architecture positive upper-bound assertion was changed
to require null attention bytes/counts: that is the requested unknown-handling
correction, not a weakened test. Other original estimator assertions remain in
`model-memory-compat.test.mjs`. Whole-block alignment and 256-cell per-sequence
padding are shared across APIs. Required backend weights, recurrent allocation,
MTP workspace and total fit remain unqualified. Existing records are read
without migration writes.

## Changed files

Observation: `apps/host/server/lifecycle-observation.mjs`, native-control,
supervisor and index; lifecycle-observation, native-run-observation,
supervisor-startup and strata-16gb-runner tests; native-fixture helper;
`bench/strata-16gb/{README.md,LIFECYCLE.md,run.mjs,run-observation.schema.json}`.

Search/import: `apps/host/server/{chat-web-search,skill-import,skill-files,index,inference}.mjs`;
`src/components/{WebSearchDialog,SkillImportDialog,SettingsTools}.tsx`;
`src/screens/{Chat,Skills}.tsx`; `src/lib/{client,store,types}.ts`;
English/Japanese locales and app.css. Tests: chat-web-search,
explicit-reference-routes, skill-import, skill-import-routes, ux-chat-handoff,
ux-key-save, ux-skill-import and ux-web-search; reference-host, ux-component
helpers and manual-search-network fixture.

Estimator: `apps/host/server/{gguf,local-models,model-memory,model-memory-geometry}.mjs`;
model-memory and model-memory-compat tests, local-gguf helper, and
`apps/host/docs/model-memory-estimator.md`.

Evidence: this log, `_docs/hybrid-intake-tests.mjs`, and the two original
2026-11-02 source logs. The helper is a Windows intake replay tool using the
pre-approved local temp root; it is not a general replacement for `npm test`.

## Commands and results

All commands below ran in the owned worktree. Package commands ran in
`apps/host`; test commands ran at the worktree root. Status, diffs and the
ten most recent commits were reviewed before staging/commit.

```powershell
npm ci --ignore-scripts --no-audit --no-fund
npm run typecheck
npm run build
```

Install: 80 packages, exit 0, with npm's notice that package.json's allowScripts
takes precedence over .npmrc. Manifest/lock unchanged. Typecheck passed on each
invocation, including the final tree. Final UI build passed (456 modules,
9.48 seconds reported by Vite). Build warnings: store.ts is both dynamically
and statically imported, and a minified chunk exceeds 500 kB. These were not
suppressed. Build output stays local/ignored; no distribution was installed.

Initial and final focused command (same list):

```powershell
node _docs/hybrid-intake-tests.mjs lifecycle-observation.test.mjs run-observation.test.mjs native-run-observation.test.mjs strata-16gb-runner.test.mjs supervisor-startup.test.mjs model-memory.test.mjs model-memory-compat.test.mjs local-models.test.mjs kv-settings.test.mjs custom-gguf.test.mjs chat-web-search.test.mjs skill-import.test.mjs ux-web-search.test.mjs ux-key-save.test.mjs ux-skill-import.test.mjs ux-chat-handoff.test.mjs explicit-reference-routes.test.mjs skill-import-routes.test.mjs locale-gaps.test.mjs manual-model-start.test.mjs
```

Initial: 87 tests, 85 passed, 2 failed, 0 skipped, 76.230 seconds.
Both failures were old Chat harness state missing `parked`/`quotes`, before
the handoff assertions. Updated the fixture to the real main store shape and
used the real quote utility; assertions were retained and extended.
Initial output is in the OpenCode tool artifact
`tool_1b04dbc0f001Tot16Nh7owVI45` under the tool-output directory.

Final: **94 tests, 94 passed, 0 failed, 0 skipped**, 51.700 seconds.
Scratch: `C:/Users/downl/AppData/Local/Temp/opencode/strata-hybrid-xeFqe3`.
This includes the real isolated host manual-model-start checks for both new
and previously loaded references. No real GPU engine is used: Node rejects
the fixture's llama-server argument so explicit load admission is observable.

Broader affected regressions:

```powershell
node _docs/hybrid-intake-tests.mjs ux-chat-handoff.test.mjs explicit-reference-routes.test.mjs agent-local.test.mjs native-control.test.mjs native-load-cancel.test.mjs run-selection.test.mjs run-selection-lifecycle.test.mjs image-selection-ownership.test.mjs turn-reattach.test.mjs chat-files.test.mjs request-flow.test.mjs agent-skills.test.mjs skills-used.test.mjs
```

63 tests: 58 passed, 1 failed, 4 skipped, 96.994 seconds. The four skips require
a built real Harness; the scratch profile deliberately supplies no Harness.
Chat file routing, reattachment/background ownership, image selection ordering,
native cancellation, skill selection and supervised agent routing passed.

Follow-up for native/estimator changes and the browser startup failure:

```powershell
node _docs/hybrid-intake-tests.mjs native-run-observation.test.mjs model-memory.test.mjs model-memory-compat.test.mjs q36-load-lifecycle.test.mjs q36-progress.test.mjs q36-private-cache.test.mjs native-control.test.mjs native-load-cancel.test.mjs run-selection-lifecycle.test.mjs
```

55 tests: 54 passed, 1 failed, 0 skipped, 58.541 seconds. Q36 source and packaged
lifecycle contracts passed. The first mounted ModelRun test again failed at
`tests/run-selection-lifecycle.test.mjs:70` during Edge
`launchPersistentContext`, 10-second timeout, before any component assertion.
Both runs reported PathService/local-app-data errors and the non-default-data-dir
DevTools message despite an explicit unique scratch `--user-data-dir`. Creating
all scratch profile directories in the runner did not resolve it. The remaining
eight mounted cases passed on each run. No timeout/assertion was relaxed and no
further retries were made. This failure is retained, not counted as a pass or
proven to be an application regression. No production test fixture was changed
to mask it.

Each runner invocation is serial with a 90-second per-file timeout, scratch
HOME/USERPROFILE/Strata/Local/Roaming/XDG/temp paths, and the project's
`isolatedTestEnvironment` plus `test-fs-guard` inherited by child Node processes.
Fixtures remove only their owned descendants. Remaining scratch evidence is
preserved; no recursive cleanup outside it was attempted.

Static preservation/check commands:

```powershell
git diff --exit-code HEAD -- apps/host/server/run-observation.mjs apps/host/tests/run-observation.test.mjs bench/strata-16gb/capture-baseline.mjs bench/strata-16gb/measurement-schema.json bench/strata-16gb/results apps/host/package.json apps/host/package-lock.json
git diff --check
git diff --cached --check
git status --short
git log --oneline -10
```

The preservation comparison has no diff. Conflict-marker search returned none.
Whitespace checks passed. Final staged review covers 51 intended files. The
temporary baseline/compatibility paths and all build/scratch artifacts are
absent from the staged diff. The source branch still resolves to `cd297d03`.

```powershell
$files = @(git diff --cached --name-only --diff-filter=ACMR -- '*.mjs')
foreach ($file in $files) { node --check $file; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
node --version
npm --version
Get-Process -Id 13556,25140 -ErrorAction SilentlyContinue
```

All 33 changed/new MJS files passed syntax checks. Runtime: Node v26.10.0,
npm 12.0.2. The two timed-out browser launch PIDs were absent at the final
read-only check; this worker did not kill another process tree. Final staged
preservation comparison also included `run-windows.ps1` and passed with no diff.

## Trust boundaries and residual limits

Manual search is same-origin/loopback guarded, explicitly confirmed, provider
redirects are restricted, responses are bounded, and cached result IDs are
opaque, chat-scoped and expiring. Snippets remain untrusted user context and
never participate in trusted skill matching. Reference turns force tools off.
Tests mock providers and reject other external requests. Skill imports store
only instructions with explicit scope/enabled choices; imported content is
never executed during preview. Credential tests use fake values.

No contribution among the eleven is blocked at implementation level. The
unresolved Edge startup case is a verification blocker for that mounted test.
Full application E2E, live provider availability/rate limiting, native/Prism
GPU lifecycle capture, real long-context allocation and quality, installer and
release verification remain parent-owned and unrun here. The attach runner's
exact-token workload needs tokenize/completion endpoints; native Python lacks
that path. Attach mode cannot prove the supplied files belong to the running
process. Observation comparability confirms context only, not codec/identity
qualification. GPU samples are point-in-time, not peaks.

New UI strings are supplied in English/Japanese as on the source branch;
other-language fallback and full keyboard/visual/mobile/accessibility behavior
need parent GUI validation. Hook-level dialog/Chat checks are not full GUI E2E.
The mounted ModelRun tests are controlled component checks only.

## Self-review and next actions

Self-review-event: type=qa_defect scope=hybrid-intake/chat-fixture category=qa-coverage evidence=initial-focused-87

Self-review-event: type=qa_defect scope=hybrid-intake/edge-startup category=windows-paths evidence=broader-63-and-followup-55

Self-review-event: type=ticket_completed scope=hybrid-intake category=correctness evidence=final-focused-94

Reviewed event-ledger and update-governance guidance. The minimal prevention
is concrete compatibility/async regressions and explicit failed-run evidence
in this log. Governance changes were rejected: this task does not justify
changing AGENTS, shared skills, SOPs or another worker's automation. Residual
Edge launch and full GUI limits remain visible. No self-modification occurred.

Recommended next action: independent diff review, then parent intake into the
current main tip, followed by the parent-owned real GUI E2E/release gates. Pay
particular attention to the two estimator API shapes, native terminal-event
ownership, reference/plain versus supervised-agent research routing, import
preview ownership, and the unresolved first Edge-launch case. Rollback is a
local revert of the integration commit; user models, imported skill files and
saved diagnostic results must not be deleted during rollback.

## SPEC review corrections after a2a209c6

Parent SPEC review identified two blockers: High, skill import and Tools key
save accepted the store's best-effort memory-only update as persistence success;
Medium, native display-error wrappers dropped the terminal numeric engine exit
code. Work remains confined to this dedicated integration worktree, with the
same applicable standards and review-only self-review policy. Existing intake
changes and source branches are preserved.

### Persistence contract and import publication

`store.update(patch, {durable:true})` now writes and flushes a unique 0600
same-directory temporary file, atomically replaces `state.json`, and only then
publishes the new in-memory state. Write/rename failures throw and retain the
old in-memory state and committed file. The existing `update(patch)` and
`save()` remain nonthrowing/best-effort for their callers. They also use atomic
file replacement, so a later partial best-effort write cannot truncate saved
skill restrictions or credentials. The model-folder preference's existing
persist-before-publish contract uses the same writer.

The Host Tools persistence callback opts into durable updates. Thus Tools PUT
cannot return success or present a new memory-only key after a state write or
rename failure. The existing custom-tools projection remains separate; this
change does not claim a multi-file transaction across all tool runtime files.

Created/imported instruction files are staged in a unique `.skill-*` sibling
of the discovery root, not inside `<data>/skills`. Before publishing the skill
directory, the Host durably saves the enable, workspace and trigger choices.
Only then is the directory renamed into discovery and the live list updated.
A publication failure rolls preferences back with the durable contract. A
rollback failure is explicitly reported; even if cleanup also fails, only an
undiscovered staging directory and inert preference entry can remain. Neither
the app scan nor the agent's live skill directory activates them after restart.
No rollback deletes an existing user's skill directory.

### Native structured failures

`startFailure` preserves the original cause and forwards only the numeric
`output.engine_exit_code` alongside the existing display message. It is used
by normal, access/shared-GPU, retry, adopted-status and restart wrappers. The
actual packaged-native observation regressions assert error/exitCode **23**
on normal, two-attempt retry, and adopted startup paths; the retry begins with
code 7 and must retain the terminal code 23. Raw Control output/log tails are
not copied into observations.

### Behavioral RED and GREEN

The tests were added before the production fix. They exercise the actual
store and Host routes; persistence callbacks are not replaced with mocks.
One test induces a real OS file-vs-directory write/replace failure. An opt-in
test-process preload injects EACCES/ENOSPC at real filesystem call boundaries
under the guarded scratch HOME. Host processes are stopped and restarted to
test rediscovery and key persistence.

From the worktree root, the RED and first GREEN command was:

```powershell
node _docs/hybrid-intake-tests.mjs store-durability.test.mjs durable-settings-routes.test.mjs native-run-observation.test.mjs
```

RED: **14 tests, 7 passed, 7 failed, 0 skipped**, 42.239 seconds.
Scratch: `strata-hybrid-IREUyq` under the approved temp root. Disabled/scoped
imports returned 201 instead of 400 under EACCES, key PUT returned 200 instead
of 400, the durable store call failed to throw on actual EISDIR, and all three
native paths returned null instead of 23. No test assertion was lowered.

First GREEN: **14 tests, 14 passed, 0 failed, 0 skipped**, 74.317 seconds.
Scratch: `strata-hybrid-QqggpA`. The legacy best-effort negative test intentionally
prints its filesystem error; it is not suppressed or treated as a failed gate.

Additional publication/rollback/partial-write tests and the affected suites:

```powershell
node _docs/hybrid-intake-tests.mjs store-durability.test.mjs durable-settings-routes.test.mjs persistence-publication.test.mjs model-directory.test.mjs model-storage.test.mjs skill-import.test.mjs skill-import-routes.test.mjs ux-skill-import.test.mjs ux-key-save.test.mjs agent-skills.test.mjs skills-used.test.mjs agent-tools-settings.test.mjs agent-tools.test.mjs native-run-observation.test.mjs lifecycle-observation.test.mjs native-control.test.mjs native-load-cancel.test.mjs native-config-persistence.test.mjs native-job-diagnostics.test.mjs q36-load-lifecycle.test.mjs native-fb5.test.mjs manual-model-start.test.mjs supervisor-startup.test.mjs
```

Final affected run: **118 tests, 104 passed, 0 failed, 14 skipped**,
161.070 seconds. Scratch: `strata-hybrid-8LeQYs`. The skips are 12 real-Harness
checks (no built Harness in the scratch profile), one explicitly opt-in real
browser check, and one Windows symlink-privilege check. Manual startup,
model-folder/store callers, skill/tool behavior, native cancellation/settings,
Q36 lifecycle and observation tests passed. From `apps/host`,
`npm run typecheck` passed. These results supersede no earlier failed evidence;
the initial intake's Edge startup limit remains recorded above.

### Review scope, limits and handoff

Production changes are limited to `server/store.mjs`, `skill-files.mjs`,
`index.mjs` and `native-control.mjs`. Tests add `store-durability.test.mjs`,
`durable-settings-routes.test.mjs`, `persistence-publication.test.mjs` and
`fixtures/state-persistence-fault.mjs`; native-run-observation and its existing
fixture are extended. The reference-host helper adds opt-in preloads and an
idempotent stop for restart tests. No dependency/configuration change, push,
publication or installed-app operation was performed.

No real GPU/Control executable, full GUI E2E, installer/release, or sudden
power-loss durability test ran in this correction. Atomic replacement and
file flush do not claim directory-fsync or physical-storage power-loss
qualification. Staging/temporary remnants can remain when filesystem cleanup
is denied; they are outside discovery and are not automatically retried or
activated. Parent re-review should check the durable opt-in contract, staged
publication order and rollback-failure containment, and the three real wrapper
paths carrying exitCode 23. The expanded tests directly cover the missed gates.

Self-review-event: type=qa_defect scope=hybrid-intake/durable-save category=qa-coverage evidence=SPEC-review-and-red-14

Self-review-event: type=qa_defect scope=hybrid-intake/native-exit-code category=correctness evidence=SPEC-review-and-red-14

Self-review-event: type=ticket_completed scope=hybrid-intake/spec-corrections category=correctness evidence=green-14-and-affected-118

Decision: retain the review findings and failures, add real persistence/restart
and packaged-native terminal regressions, and make the smallest scoped
production corrections. No AGENTS, Skill, SOP or automation rewrite is justified.
Final static checks: `git diff --check` and `git diff --cached --check` passed;
`node --check` passed for all **11** changed/new MJS files. Status/diff and
`git log --oneline -10` were reviewed; exactly 12 intended files are staged.
`git diff a2a209c6 --exit-code -- apps/host/src apps/host/server/lifecycle-observation.mjs apps/host/server/model-memory.mjs apps/host/server/model-memory-geometry.mjs apps/host/server/run-observation.mjs bench/strata-16gb apps/host/package.json apps/host/package-lock.json`
returned no diff. The scoped follow-up commit is titled
`[GUI] require durable settings saves and retain native exit codes`.
