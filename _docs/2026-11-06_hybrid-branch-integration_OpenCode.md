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
