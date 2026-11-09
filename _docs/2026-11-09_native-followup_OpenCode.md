# Native follow-up after personal installation

Date: 2026-11-09 JST. Owner: OpenCode. Status: IN_PROGRESS.

## Goal and scope

Continue the full outstanding CUDA resource, actual-input, Spin8 integration,
regression and public-release goal from installed local.2/main ceffaf85. Goal API
is unavailable; the session task list and this log track the original objective.
Existing signed/installed packages remain immutable during diagnostic work.

## Resource finding and new authorization

At 03:38 JST, the installed app was open with no model process observed, about
14.8 GiB available RAM and 14,207 MiB free VRAM. During the first CUDA investigation
a user model started. Compiler admission correctly refused before child creation.
At 03:55 JST, native process17648 had a sampled working set of24,963,399,680 bytes,
private bytes17,581,568,000, and the OS reported247,440 KiB free physical RAM.
VRAM was14,591 MiB used /1,460 MiB free. This was an actual installed Swift run,
not the new diagnostic or a measured total bound for Q36 expert buffers.

Read-only installed Host checks confirmed healthy HTTP, one active turn, one
running request, Swift IQ2_XS in reading phase, capacity131072 and parallel1.
No native install/load job was active. Capacity is not an input-token count.

The user explicitly chose **Stopして診断を優先**: normal Stop, then unload,
preserving conversation/model/settings and restoring the same model/settings
after diagnosis. This extends the earlier idle-only maintenance approval to the
currently active response. Do not resubmit the interrupted private prompt.

The dedicated helper snapshots the source/runtime config privately with owner-only
permissions before Stop. It uses only the installed Host APIs, checks no new
unrelated job/turn appeared, preserves source-setting hashes, and has a separate
same-setting restore path. No blanket process termination, model-file mutation,
global memory/pagefile change, precision/context reduction or guard relaxation.

## Standards, verification and next actions

Apply the already-read PC/project baseline and compatible canonical prompt,
Common/Start Gate/Skill Selection/Security/LLMOps/CPP/Python/Application SOPs;
goal, systematic-debugging, QA and inherited subagent-driven-development workflow.
No formal compliance claim. Native resource research is frozen-input only until
compiler allocation causes are demonstrated. The four guard failures remain FAIL.

Next: normal Stop/unload and memory-recovery receipt; bounded serial compiler
investigation; prepare real-token input cases while no production-model state is
mutated; restore Swift with the same model/configuration after the diagnostic
window and document all outcomes. Runtime tests require the existing RAM3GiB,
commit4GiB, C:5GiB and H:10GiB floors. No complete-goal or full-window claim.

The initial pause helper stopped before creating private evidence or sending any
API mutation: the public instance DTO omits `configPath`. The helper now resolves
the UUID-bound file in the already inspected installed native-instances layout,
retaining its private configuration outside public output. This was a helper
assumption failure, not a failed model cancellation or altered user configuration.

Normal Stop/unload then passed (one Stop request, source settings unchanged).
Available RAM recovered to25,472,356 KiB. Seven serial compiler experiments
reproduced all602 resource records; a scratch DFlash change removes the two
selected spill frames, but parity is not run and no production kernel changed.
EXPDEC/QSA experiments worsened resource use and were rejected.

A new Swift instance/turn subsequently appeared through the normal app, again at
capacity131072 with one reading request. It was not the diagnostic process and
was not stopped as part of the completed compiler experiment. The actual-input
QA preflight was extended to refuse/abort on external engines or new Host activity;
its runtime remained deferred. The user's next instruction prioritizes main
commit/push and overwrite. A fresh labelled snapshot and normal Stop/unload will
be used for this new update operation; never replay the first instance's ID.

The new update pause sent one normal Stop and then hit
`server_stop_deadline_expired` on unload. Read-only reconciliation confirmed
zero active turns/requests and zero native/llama processes. A second normal
unload, only after that actual absence/identity check, succeeded and removed the
stale error instance. `pause-reconciled.json` is retained in the labelled private
snapshot directory. No process-wide termination or settings-file repair occurred.

The expanded actual-input QA behavior suite passed49 tests in0.27s. The new
unscoped-identity case and external-activity refusal/abort tests are included.
Native execution of that3071-token fixture remains NOT_RUN. Its original49-case
implementation is a checkpoint; final runtime review remains required.

The latest user request is main commit/push followed by overwrite. This checkpoint
contains diagnostic/research/QA files only; no production kernel or compiled
application source has changed from the tested personal local.2 build. The exact
validated local.2 installer can therefore be used for the requested overwrite,
with its compiled source52048324 recorded separately from this newer checkpoint.
