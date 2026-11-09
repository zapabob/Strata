# Q36 refusal-direction WebView2 acceptance extension

## Overview / requirements

Resume ownership of the app helpers only. Add truthful refusal-direction GUI
acceptance to candidate and installed Q36 E2E, preserving all existing functional
and installed-EXE gates. Parent reports app source committed/pushed at
26e5889625938459580313ca7ce6b3931606c27b and owns the running native build and frozen
native checkout. This task does not inspect or edit the native adapters/checkout,
execute build/install/app/model operations, stop processes, sign or commit.

Goal: Japanese visibility and accessible status, actual unsupported Q36 capability,
rejected enable before jobs/unload/persistence, no applied badge from a save, and
no retained observation after unload/restart. Ordinary Sampling is request-only;
no compatible Q38 projection runtime is available for positive qualification.

## Context / decisions

Applied the already-read PC/project Common, Start Gate, Skill Selection,
Security, Application Development, Python and TypeScript standards, plus WebApp
and Frontend Design for acceptance/accessibility. Rechecked canonical compatible
pre-implementation context and current project AGENTS. MILSPEC baseline and the
user-named yaraikata-memo workflow remain applicable; no subagents were used.
No visual-design implementation or external research was needed.

Feature inspection was limited to the requested RefusalProjectionStatus.tsx,
server/refusal-projection.mjs, NativeSettings.tsx and GUI implementation log.
Those sources define unsupported Q36 with a reason, distinct saved intent versus
observation, data-refusal-projection/role=status, and request-only Sampling.
Existing app helpers and their tests supplied the lifecycle/integration context.
Initial git status was clean. No application/serve source is changed here.

Use a small inlined acceptance module within the existing Q36 lifecycle. This
keeps each generated recipe hash bound to the complete new assertions and avoids
an additional shell/browser run or any API interception. Both targets receive
the same extension; existing dispatcher isolation and private-user hash checks
still surround the run. Admission negatives happen only against the disposable
profile while the real Q36 child is already ready.

## Changed files

All paths are under `_docs/local-053-20261109/app/`:

- New `q36-projection-acceptance.mjs`: pure fail-closed validators plus real
  WebView2/API lifecycle assertions, with compact negative-only receipt.
- `recipes.py`: inline the module and add checks at existing save/reselection,
  restart/load/chat/unload/reload points. All original checks remain.
- `upgrade.py`: require the new Q36 negative acceptance for either target.
- New `test-projection-acceptance.mjs`: four pure contract tests, no HTTP server,
  mocked API, browser or model.
- `test_adapters.py`: validate generated placement and retained old gates; run
  the Node contract tests along with existing low-impact checks.
- `README.md`: runtime assertions, commands unchanged, explicit limitations.
- This implementation log.

## Requirement → implementation → validation

Q36-P1: actual field supported=false/reason and saved intent OFF. The live GET
must expose both NativeField and refusalProjection unsupported reasons. Missing
fields, positive support, empty reasons or saved ON fail pure contract tests.

Q36-P2: Japanese label/status visibility. Real WebView2 must expose the Japanese
named region, localised Q36 reason, localised role=status, and no enable combobox.
A region-only screenshot is retained in the isolated profile.

Q36-P3: unsupported enable refused before effects. Two real authenticated loopback
requests (settings PATCH and load operation) require 400/422 plus a feature reason.
Config hash, values/MCP/projection, exact job IDs, ready instance, PID and generation
must remain equal. No API route or INFO result is mocked.

Q36-P4: truthful observations. Save-only, reselection, profile restart, failed
enable, chat Sampling, both unloads and real reload may only show unobserved or
real current-child zero-INFO OFF. Unload must show unobserved. Positive cvec,
applied/loaded/request-off/unverified state, stale generation/PID, dead child or
missing zero INFO cannot satisfy OFF. Pure Node cases exercise those rejects.

Q36-P5: ordinary Sampling. Find the real Response settings/Advanced accessible
controls and renamed request-only role=switch. Assert disabled, unchecked,
request-versus-loading help, no old experimental-speed switch, and negative
status. No forced click or positive request is used. Actual selector compatibility
is a parent runtime gate, not a source-level pass claim.

Q36-P6: preserve target and prior gates. Both generated targets pass fresh syntax
checks and contain the inserted calls, existing Q36 invalid-mode and Japanese
recovery checks, installedExeTest identity, and real CDP lifecycle. Existing
success receipts now require the negative projection summary too.

## Commands / observed results

From H:/Strata/worktrees/main-integration-20261106:

```powershell
git status --short
& 'C:/Users/downl/.local/bin/uv.exe' run --no-project --offline --python 'C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe' python -B '_docs/local-053-20261109/app/test_adapters.py'
& 'C:/Users/downl/AppData/Local/Programs/Strata/node/node.exe' --check '_docs/local-053-20261109/app/q36-projection-acceptance.mjs'
git diff --check -- '_docs/local-053-20261109/app'
```

First contract run correctly rejected a non-unique initial-start insertion anchor:
the same start/language/model-screen sequence also occurs during restart. Made
the insertion anchor include the initial sequence's line boundary. Fresh rerun:
**11 Python tests passed in 0.742 s**, including **4 passing Node subtests** and
syntax checks of all five generated JS variants. Runtime-helper node --check
passed. Scoped git diff --check passed, with checkout LF-to-CRLF notices only.
UV again emitted the pre-existing dangling-distribution metadata notices; no
dependency repair or installation was attempted.

Python used the requested existing interpreter through uv with -B. Tests only
render scripts in memory, parse/check syntax, execute pure contract assertions
and the existing harmless Node homedir check. No app or model was launched and
no process was stopped by this task.

## Known limits / next action

Real WebView2 selectors, Japanese translations, API error shape, observation
timing and screenshots remain unexecuted. Parent must run the normal qa-q36
candidate and installed phases with a newly reviewed clean app commit containing
this extension; native provenance remains separately bound. No extra phase was
added and the frozen native source is untouched.

Q36 has no cvec support. No compatible Q38 runtime/model has been qualified.
No vector is loaded, no positive application is claimed, and applied-to-unobserved
behaviour cannot be exercised from a genuine positive state on Q36. Tests reject
such stale/positive records rather than fabricating one in the runtime flow.
Ordinary request ON/OFF propagation is not claimed while its real switch is
disabled; this extension verifies its truthful disabled/OFF presentation only.

## Self-review

Self-review-event: qa_defect — duplicate start anchor was caught before runtime;
the smallest correction is the checked unique line-boundary anchor. Added no
global governance changes. Self-review-event: ticket_completed — review-only.
Rejected API mocks, synthetic projection INFO/history, pretending Q36 support,
loosening installed identity, extra browser launches and positive Q38 claims.
All substantive changes are inside the assigned app directory.
