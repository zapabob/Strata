# Stable 0.5.9 workflow safety repair

Status: implementation in progress. No new test, CI or release pass is claimed.

## Request and acceptance

Fix the RAM-floor breach, unnecessary deep-research writes and inaccurate CSV
audit from the actual-model verification. Repeat the real-model workflows,
pass exact-source CI, commit/push main, publish the next immutable stable release
with the standard installer in tar.7z, and overwrite-install it. Preserve the
existing profile, RustXNG Full, tool/key/approval choices and older releases.
Keep coordinated product versions and independently identify third-party builds.

RAM-1: admit and continuously monitor the owned local inference runtime, with
early containment before the unchanged 3 GiB physical floor. Do not stop another
application or lower RAM, commit or disk floors. Cover startup, generation,
ownership changes and error reporting with deterministic regression tests.
RES-1: research gathering offers only search and fetch, and final writing offers
no tools; enforce restrictions outside model prose, including stale/direct calls,
without affecting simultaneous ordinary chats. Restore permissions after research.
AUD-1: calculate inventory versions, duplicates, missing IDs and non-passed checks
deterministically from actually read CSV content. A passed check is successful;
never invent a requirement for further execution evidence. Reject malformed or
ambiguous inputs. Preserve the original failed results as historical evidence.
REAL-1: demonstrate /btw, actual RustXNG Full research, correct unclarified audit,
learned skill and automatic reuse with a real local model. Record actual context,
model identity, tool calls, outputs and resource minima; synthetic regressions
remain separately identified. PACK-1: exact-source CI, source-bound builds,
component signatures, backup, standard overwrite, installed checks and anonymous
public asset hash readback before claiming formal delivery.

## Standards and design

Read PC and project AGENTS, Codex-local baseline and the canonical required
prompt. Compatible guidance only; stronger identity/security/tool rules prevail.
Apply Common, Implementation Start Gate, Skill Selection, Security, Application,
LLMOps, TypeScript and Python SOPs; add language SOPs before component changes.
Skills selected: milspec-codex-standard and debug-failing-test, with the existing
project CI/packaging tools preferred. No subagents are requested or spawned.
Resource floors remain RAM 3 GiB, commit 4 GiB, C free 5 GiB and H free 10 GiB.
Builds request five compiler jobs. Large outputs go under
H:/Strata/releases/stable-059-20261113-codex. Do not export secrets, unrelated
chats or profile data. Existing untracked real-model report is this task's
preceding evidence and will be reviewed before including it in a commit.

## Findings, changes and verification

Initial main: a9c84cb82199dfa66978712ffc10feb376231766. Only the preceding
real-model verification report was untracked. Installed 0.5.8 remains the
rollback candidate. The previous mmap run crossed the RAM floor; its no-mmap
rerun passed bounded resource checks. Research prohibition existed in prompt
text but tools remained available. The initial audit added three unsupported
verification issues; the clarified rerun passed. Implementation, regression,
actual-model, CI, installation and publication results will be recorded here.

The initial focused group passed 15 tests. The new actual-Harness safety group
then exposed two real boundary mistakes: scoped delegation registrations survived
the global tool mask, and the LLM waterfall options are immutable. A final
per-request copy at the pinned streamWithRegistration boundary filters every
schema while independent pre-execute and monotonic guards deny stale calls.
The corrected actual-Harness plus pure safety group passed nine tests without
skips. The first attempted Harness command had no inherited component setting
under the filtered guard and skipped its test; it is not actual-Harness evidence.

The full Harness group initially passed 43 and failed its exact inventory test
because audit_inventory was newly added. The inventory expectation now includes
that explicit tool; no tool or assertion was removed. A final group is running.
Typecheck passed. The final focused group passed the safety, supervisor-pressure,
OS-prompt and short-prompt tests. Continuous guard coverage is Windows-specific;
other platforms retain their prior runtime policy and do not claim this repair.

The first host-wide run failed in the temporary verification driver: nested
profile isolation replaced the Windows account profile needed by Edge and its
filtered PATH lacked the installed PowerShell executable. Two prompt-length
regressions were also caught; audit guidance now lives in its tool description,
keeping the existing short general prompt unchanged. The driver now lets the
standard full-suite runner own isolation and adds the actually resolved pwsh
directory. No browser, filesystem, permission or resource assertion was relaxed.
The failed first full output is retained, and the corrected full suite is running.

Self-review-event: qa_defect. Evidence is the retained skipped Harness attempt,
scope-mask leakage, immutable request error and full-suite profile/PATH failures.
Prevention is the new actual-Harness capability test plus using the existing
full-suite environment contract. Review level: review-only for global governance.
No global AGENTS, SOP, Codex skill, automation or security rule was modified.
The project AGENTS change only declares candidate-version provenance.

Main 782e25bd was pushed with the runtime fixes and coordinated versions. Docs
CI caught an invalid historical tar.7z entry in a list reserved for installers;
db640451 corrects that metadata and Docs passed. The other six filtered workflows
were explicitly dispatched at db640451, alongside its Docs/Pages runs. A clean
full source freeze at db640451 is retained on H:. Its first preparation caught
the concurrent two-file metadata commit and stopped at tree equality; the
already copied tree was proven byte-for-byte equal to db640451's Git tree before
the owned detached HEAD was advanced with an expected-old-object update. The
fresh preparation passed without copying historical qualification results.

The complete local Harness group passed 44/44 with zero skips. The second local
host run passed 2070, skipped 123 and failed one PowerShell verifier because the
filtered driver lacked PATHEXT, so bare git was unavailable inside PowerShell.
The driver now forwards the existing extension list. The exact remaining module
passed 2/2; this does not relabel the earlier full run as all green. Hosted full
Windows and Linux suite results remain separately required. Configuration
snapshot generation completed with zero changed files or values. Final focused
checks and typecheck passed. RAM floors and all test assertions remain unchanged.

Review additionally identified late calls after cancellation: restoring ordinary
capabilities on a cancelled or lost research stream could reopen its old session.
Those sessions now retain restrictions and are retired; a later normal turn
receives a fresh session. Only a completed settled research session is restored
in place. The actual-Harness cancellation/reuse test passed, including Bypass
research followed by a Manual turn with a different session identity. This is a
production follow-up requiring a new app build/CI source; native inputs and
Control files are unchanged. Native compilation and Control packaging retain
their actual independently frozen source identities.

On bc355f86, hosted full Windows and Linux host checks passed. Mac host passed
2070 tests with one failure in Time-skip's pre-existing fixed 1400-ms assertion
against a revision delayed 1500 ms. The replacement uses an explicit external
barrier: the real revision process is held until the test observes detached
return and generating state, then is released. Changed-file, apply and rollback
assertions remain intact. The complete Time-skip module passed locally. This
test-only repair does not change distributed Control or native sources.
