# Native maintenance 2026-11-07 — preparation only

Owner: OpenCode. Parent holds execution approval. Candidate 044 has parent-reported
SPEC + QUALITY approval but is not built/frozen by this task. This is a prepared
maintenance foundation, not a completed native E2E test.

Helpers: `H:\Strata\worktrees\main-integration-20261106\_docs\native-maintenance-20261107`.
Private evidence: `H:\Strata\private-backups\native-maintenance-20261107`.
The latter was created with a protected owner-only DACL before writing private data.
Do not copy its raw JSON, environment, commands, or candidate logs into Git or reports.

## Entry points

| File | Purpose |
| --- | --- |
| `foundation.py` | Read-only snapshot and readiness checks; private JSON writer; retained process identity and loopback ownership checks. |
| `private-store.ps1` | Fresh directory creation and recursive owner/DACL verification. `SealMockTests` tightens only synthetic pytest fixture directories. |
| `process-inventory.ps1` | CIM inventory captured by Python into a private pipe. Direct invocation without the pipe handshake fails. |
| `task-inventory.ps1` | Read-only related scheduled-task inventory in the same private-pipe protocol. |
| `maintenance.py` | `plan`, checked `write-recipe`, `freeze`, parent-only `run`, and explicit recovery `restore`. |
| `candidate_guard.py` | Frozen candidate worker; existing `serve/winjob.py` containment and native resource policy. |
| `test_maintenance.py` | Offline mocked acceptance/failure cases. No live stop, start, candidate, or Job operation. |

The verified preparation interpreter is
`C:\Users\downl\AppData\Local\Programs\Python\Python312\python.exe`
(3.12.10, existing psutil 7.2.2). Preparation used existing
`C:\Users\downl\.hermes\bin\uv.exe run --offline --no-project --python <interpreter> python -B ...`.
No dependency installation is required.

## Evidence and current blockers

`snapshot.json` captured Hermes PID 17336, exact creation FILETIME
134384498412224358, port 8080, healthy, context per slot 98,304, one slot,
one active slot, and model size 7,206,168,928 bytes. Its private record includes
the exact executable/command/argv/environment/cwd, model target/mtime, and binary hash.
Its SHA-256 is
`c27206c6e504b2ea3314f94b2c5b57e2647c617c63d40a3bb93a2bae00d66ead`.
It was captured at `2026-11-06T17:56:37.412723Z` (2026-11-07 JST).
The installed Strata shell/Host was absent. Hermes `/metrics` returned HTTP 501,
so admission/queue counts were unknown; one quiet slot would not be sufficient.

`snapshot-current.json` at `2026-11-06T18:13:29.911448Z` records both the installed
Strata shell/Host and the known Hermes executable absent. It preserves current
saved settings, registry identity, installed Host file identities, native 0.5.1
identity, Hermes binary/launcher identity, and the read-only watcher inventory.
Its SHA-256 is
`b752ed283355beb0f0ea6ea604a2ec4b4278ebea07bccd512fb388c81cc987bf`.
Two related scheduled tasks were observed; their enabled triggers did not imply
periodic respawn. No task was changed or started. C: free space was 3.746 GiB,
below the 5 GiB execution floor. RAM was 12.837 GiB available, commit headroom
36.961 GiB, and H: free space 318.153 GiB.

These are observations, not evidence that this helper stopped either service.
This preparation issued no stop/start/install/restore or GPU workload. A missing
server is not treated as an idle, restorable running server. Both snapshots are
deliberately **non-executable**. The parent needs a fresh complete snapshot of the
intended original running state, not a manual edit of these records.

Final snapshot `snapshot-final.json` at `2026-11-06T18:26:46.476434Z` still records
both absent. SHA-256:
`f571507668de80879fd28d44d921ca82d48f7fa29048d27e85e9620044494e47`.
The sanitized `readiness-handoff.json` at `2026-11-06T18:30:46.639952Z` has SHA-256
`e9c1923222441376eb30c2b71df6d514266bfad327f5c1ef46061d9e489022b0`.
Its resource sample is RAM 11.292 / commit 35.855 / H: 318.152 / C: 3.273 GiB.
It also confirms the current tool caller is Job-contained and cannot be the
restoration supervisor. Host activity is unavailable; this is not an active-count
zero or idle certification.

Final helper SHA-256 values (also in the private sanitized handoff receipt):

| Helper | SHA-256 |
| --- | --- |
| `foundation.py` | `51d8bd7b7e5c4036143a00a7f0e4233fb03b82634bda14ac97716b5901050a12` |
| `maintenance.py` | `52f36a1b6694e95bb12fac30480af17c2f2ee1d5a56e90a98950abe27045605d` |
| `candidate_guard.py` | `e00967e8433bbc837743c8f28a2d000f09384879dd69cd61d6dc3bf513634e9f` |
| `private-store.ps1` | `37e955b0af6be200fb933b3f3646e2b5c5f65eee4ff8aaf906f6ca1044819cbe` |
| `process-inventory.ps1` | `dd6152e257066a0a31950016044d98ed6209b950a0c4f3b48d46c55ffe16892c` |
| `task-inventory.ps1` | `19504565a801c78b06556f3720f8dbf2f3e6ed98b2d9e228a2d16f082a2a1798` |

## Read-only commands

Run from a terminal using these exact helper/interpreter paths. Examples below
define variables for readability; no command text or credentials are shell-evaluated.

```powershell
$py = 'C:\Users\downl\AppData\Local\Programs\Python\Python312\python.exe'
$helpers = 'H:\Strata\worktrees\main-integration-20261106\_docs\native-maintenance-20261107'
& $py -B "$helpers\foundation.py" --help
& $py -B "$helpers\foundation.py" snapshot --snapshot-name snapshot-approved.json
& $py -B "$helpers\maintenance.py" plan --snapshot-name snapshot-approved.json --snapshot-sha256 $ApprovedSnapshotSHA256
```

Choose a fresh snapshot name; no snapshot is overwritten. `plan` and `readiness`
only inspect. `run` and `restore` without `--execute` also inspect only.

## Parent execution plan — not run in this task

1. Reconcile the independently changed runtime state and confirm the original
   servers/settings that must be restored. Make backend admission counters
   observable through a reviewed, read-only route. This implementation requires
   `/metrics` processing/deferred gauges as well as `/slots`; HTTP 501 is a hard
   blocker. Restore the C: reserve through separately approved work.
2. Finish candidate 044 build/review and isolate its test profile. Its runner
   must leave the normal installed Host, user settings and original ports alone.
   Freeze all executed binaries, runner modules, configs and runtime dependencies
   needed for the test. Parent review must establish the complete file list.
3. Create a complete fresh snapshot. It dynamically binds installed shell →
   installed Node Host → actual managed backend, rather than assuming PID 9004
   or port 8791. Check its safe summary and all plan blockers.
4. Submit reviewed candidate recipe JSON to `maintenance.py write-recipe` through
   stdin (not command-line arguments); the checked writer validates and creates
   `candidate-recipe.json` privately. Then run `maintenance.py freeze`. Freeze
   only hashes files and writes `frozen-candidate.json`; it executes no candidate.
5. Quiesce request producers and leave the Host open. Read-only sampling is not
   an atomic admission lock. Parent must keep producers quiesced for the whole
   window. The script additionally requires three idle samples, current Host
   active-turn/running/waiting counts, backend slots and processing/deferred
   counters, and an immediate check before stopping each server.
6. From an independent standalone console, parent explicitly runs the single-use
   entrypoint below. The preflight refuses a caller already in a Windows Job so
   the replayed Hermes process cannot accidentally inherit a kill-on-close job.
   This direct-interpreter execution exception is for restoration lifetime;
   ordinary preparation/verification uses uv.

```powershell
# PARENT ONLY, AFTER ALL BLOCKERS ARE RESOLVED AND BOTH DIGESTS ARE SET.
& $py -B "$helpers\maintenance.py" run --execute --parent-approved --clients-quiesced --snapshot-name snapshot-approved.json --snapshot-sha256 $ApprovedSnapshotSHA256 --manifest-sha256 $FrozenCandidateSHA256
```

The entrypoint creates `execution-claim.json` exclusively. It cannot run a second
candidate window in this private directory. It records intent before unloading
Strata through the existing Host `POST /api/models/unload`. It terminates Hermes
only through a retained handle with matching executable, creation FILETIME and
owned loopback listener. There is no blanket kill or duplicate cleanup.

Candidate steps are bounded individually and together (maximum 3,600 seconds).
Both outer and inner handshake workers are assigned to the existing kill-on-close
Job before receiving permission to run candidate code. Every second, RAM >=3 GiB,
commit >=4 GiB, H: >=10 GiB and C: >=5 GiB are required. A floor failure, timeout,
changed input, unexpected original-port listener or nonzero result cancels the
candidate. Only candidate-owned jobs/handles are terminated.

In `finally`, candidate cleanup precedes independent Hermes and Strata restore
attempts. A journal write failure cannot skip either attempt. Hermes reuses the
exact captured raw Windows command with explicit executable, original cwd/env,
`shell=False`, and private output handles. It never evaluates command text in
PowerShell and does not deduplicate servers. Strata reloads only through the
same live Host `POST /api/models/{saved-id}/load`; it never spawns an untracked
Strata executable. Restoration polls for up to 420 seconds per service and
checks exact commands, executable/model metadata, model path, context, slot
count, health and listener ownership. Strata additionally must be owned/tracked
by its original Host and retain the saved settings. Timeout responses are
reconciled before sending a new load; there is no blind repeated load.

## Explicit recovery

Ordinary candidate failures, timeouts and Ctrl+C take the restoration path.
Force-killing the maintenance supervisor or shutting down Windows prevents its
Python `finally` block. Candidate Job containment still closes with the owner;
server restoration then needs the explicit recovery entrypoint. No unattended
watchdog or scheduled task was installed.

```powershell
# PARENT ONLY. Requires the matching claim and a recorded stop intent.
& $py -B "$helpers\maintenance.py" restore --execute --parent-approved --snapshot-name snapshot-approved.json --snapshot-sha256 $ApprovedSnapshotSHA256
```

Recovery takes the same OS operation lock, reconciles already-restored servers,
and refuses duplicates, an unknown listener, changed executable/model bytes or
metadata, changed saved settings, a replaced Host, or an untracked Strata child.
It does not overwrite concurrent user settings to manufacture a successful result.
A partial recovery is reported as failure with a private receipt.

## Candidate recipe shape

This is a schema example, not an executable recipe or a frozen candidate. Paths
must be absolute existing files. A Python/Node runner or PowerShell `-File` must
be pinned alongside its interpreter. Inline shell commands are rejected.

```json
{
  "schema": 1,
  "candidate": "044",
  "candidateRoot": "H:/Strata/worktrees/REVIEWED-ISOLATED-CANDIDATE",
  "originalHostUntouched": true,
  "noInstall": true,
  "windowSeconds": 900,
  "files": ["ABSOLUTE-INTERPRETER.exe", "ABSOLUTE-RUNNER.py", "ABSOLUTE-CANDIDATE.exe"],
  "steps": [{
    "argv": ["ABSOLUTE-INTERPRETER.exe", "-B", "ABSOLUTE-RUNNER.py"],
    "cwd": "H:/Strata/worktrees/REVIEWED-ISOLATED-CANDIDATE",
    "timeoutSeconds": 900,
    "env": {}
  }]
}
```

The trusted candidate runner controls its isolated test; the recipe declarations
are not an operating-system filesystem/network sandbox. Do not use it to install
or modify the original app. Normal Host private-memory mode (rotating key), native
Control instances (different ownership/port/config lifecycle), or a settings/load
preview different from the captured command require a reviewed adapter. Current
helpers fail closed for these cases.

## Validation boundary

Offline mocks cover idle gating, unknown counters, PID reuse, wrong/wildcard
listeners, redirects, command replay, Host-only reload, duplicate refusal, failure
restoration, journal failure, containment handshake failure, timeout and floors.
Actual stop/reload, live Windows Job termination, candidate inference, model quality,
and full restoration remain untested under this preparation-only authorization.
The implementation log records exact verification commands and final results.

Final preparation verification: **50 mocked cases passed in 0.50s**; Black
(`-l 120 -S`) and flake8 passed; all three PowerShell files parsed with zero
errors; recursive owner-only ACL verification passed. Private JUnit evidence:
`mock-tests-04-results.xml`. Earlier snapshots and verification receipts are retained.
