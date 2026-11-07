# Monitor state consistency and app connection ownership

Date: 2026-11-07. Agent: OpenCode. Status: focused source checks passed; inherited catalog failure and parent WebView E2E remain.

## Objective and scope

Make Monitor, sidebar and focus mode agree about unloaded, unavailable, failed and
actively working models. A ready service is not proof of a loaded model. Preserve
request history, PC sensors, chats, goals, drafts, manual startup and verified
hardware profiles. Make the connection banner describe app/live-update state.
Reproduce and repair stale EventSource and overlapping bootstrap ownership.
Only the assigned frontend files, focused tests, distinct locale entries and this
log are owned here. Parent-owned locale keys `prof01`–`prof05` remain intact.

## Standards and decisions

Applied the supplied PC/project AGENTS, MILSPEC baseline, Common, Implementation
Start Gate, Skill Selection, Security, WebApp Development, Frontend Design and
TypeScript SOPs. Skills: systematic-debugging and test-driven-development. Read
the canonical CLAUDE-FABLE-5 context; its incompatible identity/tool/platform
claims do not override the active harness. Existing UI tokens and classes are
the visual authority. No dependency or network policy changes are needed.
Goal API is unavailable; the objective above is the source-phase completion goal.

## Evidence and hypotheses

The user's authoritative read-only snapshot reports a healthy app Host and an
HTTP 200 SSE stream with native/monitor frames, alongside a ready native service
whose model phase is unloaded. This is user-supplied evidence, not a fresh probe
by this unit. The earlier screenshot does not prove the current frontend's
EventSource is offline. No private conversation payload is read or copied.

Source inspection found unguarded closed-source listeners, no bootstrap call
generation, late optional writes, and HTTP bootstrap declaring live before SSE
open. Controlled boundary tests reproduced each case. Final review also reproduced
older initial chat hydration replacing a newer conversation and an older reconnect
list deleting a conversation kept by the newer bootstrap. These are controlled
reproductions of source defects, not proof of the earlier screenshot's cause.
TaskTree's count uses `board.need`, which intentionally includes unresolved chat
errors and approvals, whereas its list contains scheduled tasks. Both board and
sidebar use `useBoard`. The exact screenshot count is unverified; no concrete
count defect is established, and its behavior is outside this patch.

## Verification plan and resource gate

Run RED then GREEN against production projection and component/handler code,
controlled EventSource and store HTTP boundaries, then relevant existing tests
and TypeScript. No full suite, model/GPU operation, installed-app change or commit.
Tests use fictional data, in-memory bundles and mocked API boundaries. Temporary
paths are under `H:/Strata/validation`, selected by `STRATA_TEST_SCRATCH_ROOT` and
TEMP/TMP; Windows USERPROFILE stays `C:/Users/downl`.
Initial measured free RAM: 18.10 GiB; C: free: 5.79 GiB (floors 3 / 5 GiB).

## Implementation and changed files

`apps/host/src/lib/native-monitor.ts` now owns `projectedModelState`, shared by the
native dashboard, sidebar and focus bar. Explicit unloaded becomes idle / No model
loaded; unknown phases become Status unavailable, not a fabricated engine error.
Actual instance errors remain errors with their detail. Ready and active phases
retain their ready/busy presentation. Historical load-job failures are not promoted
to a current model failure. Throughput provenance now requires numerical live
activity or recorded request/history speeds, not merely a metrics object. Request
history and hardware readings are retained.

`apps/host/src/app/Sidebar.tsx` gives unloaded/error/unavailable/loading states
priority over the workflow's Working line, including the accessible chip label.
It does not cancel, delete or rewrite the ongoing workflow. `apps/host/src/app/App.tsx`
uses the same projection in FocusBar, avoids a fabricated zero speed, and describes
the app/live-update connection and retained readings in ConnectionBar. The retry
handler still invokes bootstrap.

`apps/host/src/screens/Monitor.tsx` changes only the state badge/detail projection:
idle preserves No model loaded, unavailable has an explicit badge, and a retained
queue cannot override the unloaded state.

`apps/host/src/lib/client.ts` invalidates replaced/unsubscribed EventSource owners
before closing them. Every named/default/open/error callback and the watchdog
check ownership. Stale callbacks cannot change data, connection or heartbeat age.
Watchdog and retry durations are unchanged.

`apps/host/src/lib/store.ts` assigns bootstrap generations at invocation, revokes
the preceding subscription, and allows only the current generation to publish
success, failure, optional reads or events. HTTP completion unlocks the screen;
EventSource open establishes live. Optional reads also lose to newer events or
explicit refreshes of the same field, protecting verified hardware. The same
ownership predicate accompanies bootstrap chat hydration/list/body reads so a
superseded read cannot replace or remove conversations. Existing non-bootstrap
chat callers retain their default behavior.

All nine `apps/host/src/locales/{en,zh,ja,de,fr,es,ru,pt,ko}.json` files add only
the five distinct `monconn01`–`monconn05` entries for this unit. Their existing
uncommitted `prof01`–`prof05` parent entries are preserved. Existing translated
model-state keys are reused.

Tests added: `apps/host/tests/event-stream-ownership.test.mjs`,
`apps/host/tests/bootstrap-ownership.test.mjs`, and
`apps/host/tests/monitor-state-components.test.mjs`.
Tests extended: `apps/host/tests/native-monitor-projection.test.mjs` and
`apps/host/tests/bootstrap-hang-0213.test.mjs` (the latter now explicitly emits
the mocked SSE-open event instead of relying on HTTP alone to imply live).
This log is the only documentation change owned by this unit.

## Commands and actual results

Commands ran in `H:/Strata/worktrees/main-integration-20261106/apps/host` unless
noted. Test commands used `STRATA_TEST_SCRATCH_ROOT=H:/Strata/validation` and
`TEMP=TMP=H:/Strata/validation`, with unchanged Windows USERPROFILE. Bundles are
in-memory (`esbuild write:false`); the existing session persistence tests create
and remove their own synthetic scratch directories under that temporary root.

RED: `node --test --test-concurrency=1 --test-reporter=spec
tests/event-stream-ownership.test.mjs tests/bootstrap-ownership.test.mjs
tests/native-monitor-projection.test.mjs tests/monitor-state-components.test.mjs`.
The first attempt had six passing checks, twelve expected production failures,
and six fixture failures due to a missing DOM `removeProperty` stub. After fixing
that stub, a bootstrap-only rerun produced six genuine assertion failures: HTTP
incorrectly live, stale failure, stale success, stale optional data, lost newer
monitor data, and a revoked callback starting another bootstrap. The in-memory
legacy chat fixture was subsequently corrected to use the actual storage key and
now asserts a nonempty fictional chat, active goal and unchanged draft.

Additional RED: `node --test --test-name-pattern="late initial chat|late reconnect chat"
--test-reporter=spec tests/bootstrap-ownership.test.mjs`: both tests failed with
the old conversation replacing the new one and the old empty list removing it.
The ownership predicate was then propagated through those reads. Another test
covers a chat body already in flight when its bootstrap is superseded.

Final GREEN command:

```powershell
node --test --test-concurrency=1 --test-reporter=spec tests/event-stream-ownership.test.mjs tests/bootstrap-ownership.test.mjs tests/native-monitor-projection.test.mjs tests/monitor-state-components.test.mjs tests/bootstrap-hang-0213.test.mjs tests/monitor-host-sensors.test.mjs tests/session-persist.test.mjs tests/chat-turn-ownership.test.mjs
node node_modules/typescript/bin/tsc --noEmit
```

Result: **49/49 passed**; TypeScript passed with exit 0. This includes the real
production projection and React components/catalogs, the production Retry handler,
controlled EventSource callbacks, actual store HTTP/event boundaries, retained
history/sensors, conversation ownership, and existing persistence regressions.
No Host or model service was started for these checks.

Earlier relevant `tests/board.test.mjs` run: **17/17 passed**, supporting the
intentional attention-count behavior. That 50-check command also named a nonexistent
`tests/serving-state.test.mjs`; Node did not run it. No result is claimed for that
path, and it was removed from the final command above.

Additional catalog check: `tests/languages-and-catalog.test.mjs` had four passing
tests and one failure. Its all-key equality check found 56 existing Chinese keys
missing (`uxweb*`, `uxskill*`, `uxtool*`). A read-only `git show HEAD:...` JSON-key
comparison reproduced the same 56 missing keys in HEAD. This unrelated catalog
gap is retained, not hidden or repaired by this unit. All five newly added strings
pass the nine-language component/catalog checks.

Diff inspection and `git diff --check` on the owned tracked files passed. Git
emitted existing LF-to-CRLF notices; no whitespace errors. Last pre-test resource
measurement: 17.58 GiB free RAM, 5.68 GiB free C:, USERPROFILE `C:/Users/downl`.
Final read-only gate: HEAD `be3040e6`, 17.81 GiB free RAM and 5.66 GiB free C:;
USERPROFILE unchanged. Final owned-file `git diff --check` also passed.

## Self-review and residual risks

Self-review-event: `qa_defect`, `ticket_completed` (source unit). Evidence: the
RED fixtures, late chat hydration/deletion reproductions, final GREEN output,
and baseline catalog comparison. Decision: review-only for governance. The
smallest prevention artifact is the focused regression tests already added.
Rejected alternatives: timeout increases, HTTP-health-as-SSE proof, global chat
resets, rewriting task attention history, broad translation repair, and changes
to PC-wide guidance. No AGENTS/Skill/SOP changes were made.

The source-level ownership and rendering assertions pass. Parent must still run
real WebView E2E with synthetic conversation content, including desktop/compact
layout, localized text wrapping, live reconnect and model transitions. This unit
does not establish the current installed frontend connection state, the actual
cause of the old screenshot banner, or the exact source of its count of 113.
Native polling/Control/backend behavior is not qualified by these mock boundaries.
The inherited Chinese catalog gap remains a separate known failure.

No installed-app changes, model/GPU operations, process stops, dependency changes,
subdelegation, commit, or publication occurred. Changes stay uncommitted as
requested because locale files also contain parent work. Reversal must remove only
this unit's hunks and `monconn*` entries, preserving the parent's `prof*` entries.

## Next action

Parent reviews this source diff and runs the real WebView acceptance checks before
the personal installer. The backend Prism registration and memory-child work are
separate owners; this unit does not alter or requalify them.
