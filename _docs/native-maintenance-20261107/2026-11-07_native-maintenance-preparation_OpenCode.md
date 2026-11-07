# Native maintenance preparation — OpenCode — 2026-11-07

## Scope and acceptance

Goal: give the parent a concrete private snapshot, read-only idle/admission checks,
and a single-use guarded maintenance/restore path. Preparation only. No process
stop/start, restore, installation, GPU work, production edit, staging, commit,
shared-main-log edit, or delegation was authorized or performed by this task.
Goal API is unavailable; this log and the helper README carry the goal.

All changes are in this dedicated helper directory. Private JSON, raw CIM commands,
selected settings, process environment and future runtime logs belong only in
`H:/Strata/private-backups/native-maintenance-20261107`. Model weights are not copied.
Parent's Telemetry/localization edits were present before work and remain separate.

Acceptance: unknown activity/identity fails closed; owner-only evidence precedes
private writes; exact command and executable/creation identity are retained;
Strata stays under its real Host; candidate ownership/resource/deadline guards are
explicit; both restoration attempts survive candidate/journal failures; parent
alone can execute a frozen candidate once. Preparation success does not qualify E2E.

## Context and decisions

Applied supplied home/project AGENTS and read canonical
`C:/Users/downl/_docs/prompts/CLAUDE-FABLE-5.md`; incompatible identity/tool/date claims
in that document do not supersede this runtime. Applied existing MILSPEC and
deep-research baseline instructions, plan-mode, Common Engineering, Implementation
Start Gate, Skill Selection, Security, DeepResearch, Application Development,
LLMOps, Internet Connectivity and Python SOPs. Completion/failed-gate self-review
uses `agent-self-review-evolution`. No formal standards-conformance claim.

Sources were local first-party code and evidence: current main AGENTS/README/
SECURITY, `docs/AI_REFERENCE.md`, installed-path qualification/handoff helpers,
Host `index.mjs`, `models.mjs`, `engine.mjs`, `supervisor.mjs`, existing
`serve/winjob.py`, `tools/native_model_resource_guard.py`, and local llama server
endpoint documentation. No internet research or new dependency/trust claim was
needed. Current machine facts come from read-only calls, not model memory.

Corrected historical paths read:
`H:/Strata/worktrees/upstream-0211-latest-20261105/_docs/evidence/prepare-maintenance051.py`,
`resume-maintenance051.py`, and
`2026-11-06-startup-fix/run-with-hermes-restore.ps1`.
The old wrapper explicitly allowed interruption of current generation and wrote
raw commands to its receipt. That policy was not reused. The original generator
also had a control-character path defect corrected by its resume helper. New
helpers use direct argument arrays/explicit paths, private receipts, and idle gates.

## Implementation and traceability

| Requirement | Implementation | Verification |
| --- | --- | --- |
| R1: secret containment | Protected owner-only root, recursive ACL validation, exclusive private writes, sanitized exceptions, private-pipe CIM/task helpers | Live ACL check; no private JSON displayed; exclusive-write mock |
| R2: exact identity | CIM creation UTC + kernel creation FILETIME, executable digest, raw command, argv/cwd/env, model size/mtime/resolved target | Read-only snapshot; PID reuse/metadata-drift mocks |
| R3: actual activity | Host active turns and serving counts; backend health/props/slots/processing/deferred, loopback owner before/after HTTP | Live partial checks and strict missing-counter/listener/redirect mocks |
| R4: managed restoration | Existing Host unload/load; exact Hermes CreateProcess command; no shell evaluation or dedup | Mock exact replay and Host-only reload |
| R5: bounded candidate | Frozen inputs, single-use claim, operation lock, existing native Job/PressurePolicy, 3/4/10/5 GiB floors | Containment failure, timeout and each floor mocked |
| R6: failure recovery | Intent before mutation, candidate cleanup, independent restores in finally, explicit recovery subcommand | Failure/interrupt/full-journal mocks; real restoration not run |
| R7: parent boundary | Explicit execute + parent approval + quiesced-producer assertion; built candidate 044 required | Default-mode and missing-approval mocks |

Files: `foundation.py`, `maintenance.py`, `candidate_guard.py`, `private-store.ps1`,
`process-inventory.ps1`, `task-inventory.ps1`, `test_maintenance.py`, `README.md`,
and this log. No production or shared guard file was edited.

## Read-only observations

At 2026-11-06 17:56:37 UTC, known Hermes PID 17336 was healthy on owned loopback
8080, one slot/98,304 context, active count 1; `/metrics` was HTTP 501. Installed
Strata Host/shell was absent. `snapshot.json` SHA-256:
`c27206c6e504b2ea3314f94b2c5b57e2647c617c63d40a3bb93a2bae00d66ead`.
Hermes executable SHA-256:
`95105be565fcb2ad6bd1c343ae851339cbad63b26de4edb76eb878a58ae21039`.
Exact command SHA-256:
`4cf6f965372007b579e35be34d06574986574b887403535cc63503752ea79474`.

At 18:13:29 UTC, both known servers/shell were absent, with no stop/start issued
by this session. `snapshot-current.json` SHA-256:
`b752ed283355beb0f0ea6ea604a2ec4b4278ebea07bccd512fb388c81cc987bf`.
That snapshot preserves selected state and installed/launcher hashes, plus two
read-only related task records. No observed enabled periodic trigger. Available
RAM/commit/H:/C: were 12.837/36.961/318.153/3.746 GiB. C: violates its floor.
Absence is not proof of an idle running restoration target. Fresh complete capture
is mandatory before an executable window.

## Commands and verification

Preparation Python prefix (`$uvpy` below is notation, not a shell command):

```text
C:\Users\downl\.hermes\bin\uv.exe run --offline --no-project --python C:\Users\downl\AppData\Local\Programs\Python\Python312\python.exe python -B
```

Read-only `git status --short` was run in both the initial C: checkout and actual
H: main worktree. The latter was identified from the current local-install evidence.
`Get-CimInstance` console output was limited to PID, parent PID, executable/name
and creation date. Command lines were handled only by the checked private pipe.

Executed `private-store.ps1 -Mode Init`, snapshot/readiness/plan modes, and `--help`.
Existing runtime probe: Python 3.12.10, psutil 7.2.2; pytest 8.3.5, Black 26.3.1,
flake8 7.2.0. Initial `uv` PATH lookup failed after interruption; full verified
`uv.exe` path worked. Existing dangling dist-info warnings were not repaired.

Mock tests use `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `-p no:cacheprovider`,
`--confcutdir _docs/native-maintenance-20261107`, fresh
`--basetemp H:/Strata/private-backups/native-maintenance-20261107/mock-tests-NN`.
Initial suite: **36 passed in 0.37s**. Extended suite: **46 passed in 0.47s**.
Final verification results are appended below after running the completed helpers.

Initial default Black check reported formatting differences. Formatting was
applied using `apply_patch`, retaining the surrounding single-quote style with
`--line-length 120 --skip-string-normalization`. That check passed for all four
Python files. Initial full flake8 found the intentional native-guard import path
ordering and a lambda assignment; the import now has a narrow documented E402
exception and the lambda was replaced with a typed function. Final lint is rerun.

Pytest's synthetic temp trees introduced explicit extra ACL grants, which caused
the strict recursive private-store check to block a concurrent snapshot. No new
private snapshot was written during that failure. The `SealMockTests` mode now
tightens only those synthetic directories/files; operational evidence ACL drift
still fails closed. An initial generic Set-Acl attempt hit PrivilegeNotHeld; using
the existing ACL and changing access rules only succeeded without privilege changes.
Root and operational evidence keep the same owner-only policy.

## Residual limits and next action

Parent must resolve runtime absence, admission visibility, C: reserve and candidate
044 build/freeze before releasing a window. Caller Job membership is a preflight
blocker for exact Hermes lifetime; execution/recovery must use an independent
standalone console. The script does not alter or suspend scheduled tasks.

Read-only activity checks cannot atomically prevent another producer submitting a
request. Parent must quiesce producers for the whole window. Private-memory mode
and native-Control instances have a different exact-restore lifecycle and are
explicitly rejected pending a reviewed adapter. External changes to Host/settings/
model bytes are refused rather than overwritten. A fully terminated supervisor
or OS shutdown needs explicit recovery; no watchdog was installed. An unavailable
Host cannot be replaced with an untracked standalone Strata server.

Skipped by authorization: actual server stop/reload, Windows Job kill smoke,
candidate build/inference/GPU measurements, installer, live E2E and model quality.
Mocks establish control-flow evidence only. Next action is parent review of this
foundation and preparation of a complete frozen recipe, followed by fresh readiness.

Self-review-event: `qa_defect`, `local_fix`, and task-preparation completion.
Evidence: stale runtime identity, unavailable admission metrics, changing C: reserve,
temp ACL gate failure, journal failure path, and formatting/lint findings. Response:
review-only for governance; narrow helper fixes and regression mocks. Rejected:
weakening unknown activity into zero, broad ACL exceptions, restarting an absent
server during preparation, deduplicating/killing unrelated processes, or editing
AGENTS/SOP/skills. Remaining limitations are explicit above.

## Final preparation verification and handoff

The completed helper suite passed **50 tests in 0.50s** with the same offline
prefix and pytest options above, using fresh `mock-tests-04` and
`--junitxml H:/Strata/private-backups/native-maintenance-20261107/mock-tests-04-results.xml`.
The preceding completed run had 49 tests in 0.49s; the additional regression
requires a failed Job cleanup to prevent a success result. Input rehashing after
the original stops now runs inside the outer deadline-owned candidate guard,
so slow candidate file I/O cannot extend the outage before the timer starts.

`$uvpy -m black --check --line-length 120 --skip-string-normalization _docs/native-maintenance-20261107`:
PASS, four Python files unchanged.
`$uvpy -m flake8 _docs/native-maintenance-20261107 --max-line-length 120 --extend-ignore E203,W503`:
PASS, no findings.
PowerShell `Language.Parser.ParseFile` on the three `.ps1` helpers: zero errors.
`foundation.py --help`, `maintenance.py --help`, `candidate_guard.py --help`: PASS.
`private-store.ps1 -Mode SealMockTests` followed by recursive verification: PASS,
owner-only. `git diff --check -- _docs/native-maintenance-20261107`: no errors;
these helpers are untracked, so this is not presented as an untracked-file lint.
Final `git status --short` still shows only this task's new helper directory in
addition to the parent's pre-existing work. Nothing staged or committed.

Final private snapshot `snapshot-final.json` at `2026-11-06T18:26:46.476434Z`:
`f571507668de80879fd28d44d921ca82d48f7fa29048d27e85e9620044494e47`.
Both known original services remain absent in that inventory. Selected settings
are preserved privately, not inferred to be live inference settings.

Sanitized final `readiness-handoff.json` at `2026-11-06T18:30:46.639952Z`:
`e9c1923222441376eb30c2b71df6d514266bfad327f5c1ef46061d9e489022b0`.
RAM 11.292 GiB, commit 35.855 GiB, H: 318.152 GiB, C: 3.273 GiB. Confirmed additional
blocker: this tool caller is inside a Windows Job. Use an independent standalone
console for the eventual restoration supervisor. The receipt contains the exact
six executable-helper hashes, also copied into the dedicated README. The earlier
`readiness-final.json` is retained as historical evidence, not the final code seal.

Result: PREPARATION_DELIVERED / EXECUTION_BLOCKED. Parent must reconcile original
runtime state, obtain real admission visibility and a fresh complete snapshot,
restore disk headroom, freeze built candidate 044, and explicitly invoke once.
No live E2E, restore, or native quality success is claimed.

Final non-execution artifact check: `execution-claim.json`,
`execution-journal.jsonl`, `execution-result.json`, `frozen-candidate.json`,
`candidate-result.json`, and `hermes-restore.log` are all absent. A final
`private-store.ps1 -Mode Verify` again returned `ok=true, ownerOnly=true`.
