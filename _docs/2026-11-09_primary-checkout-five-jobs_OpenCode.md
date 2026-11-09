# Primary checkout and five-job builds

Date: 2026-11-09. Agent: OpenCode.

## Requirements and decisions

The user explicitly selected `C:/Users/downl/Documents/ChatGPT/Strata` as the
main working location and then requested five-way parallel builds. Acceptance
requires that path to check out main, retain prior user work, and supply five-job
settings for subsequent builds without rewriting earlier measurements.

Applied the compatible canonical pre-implementation context, PC/project AGENTS,
Common Engineering, Implementation Start Gate, Skill Selection and Python SOPs.
Selected skills: the already supplied MILSPEC baseline, worktree-manager,
create-rule and agent-self-review-evolution. No web research was needed for
this local Git/configuration task. No Goal API was available; this log and the
task list record the objective.

## Migration and preservation

Before switching, C: checked out `codex/windows-latest-0.4.1` at
`91f5057bda27b04c908fb22bc054d4fcf1ab7f2e`. H: checked out main at
`da01b4fd7c417d59fb5fee77b623acaf62dc17e2` with no tracked or untracked
changes. The old C: branch is an ancestor of main (0 versus383 unique commits).

Detached `H:/Strata/worktrees/main-integration-20261106` at the same da01b4fd
commit, then ran a normal `git switch main` in C:. No forced checkout, reset,
clean, stash pop/drop or user-file replacement was used. All607 previously
untracked files were checked before and after with Git hash-object. Their paths
and content hashes matched exactly. The old branch and all existing stashes remain.
Ignored runtime folders were retained in place; they were not part of the607-file
fingerprint claim.

The first read-only fingerprint command failed because PowerShell decoded
Japanese filenames incorrectly. It stopped before branch changes. The successful
command used Python's byte-preserving Git subprocess I/O through offline uv.

## Changed files

`AGENTS.md` records the primary location and five-job request. The candidate app's
`common.py` sets `CARGO_BUILD_JOBS=5` and `CMAKE_BUILD_PARALLEL_LEVEL=5`;
its existing environment contract test checks both. Component `compose.py`
retains an exact app-root gate, updated to the requested C: checkout. App and
component READMEs point commands there; the component README's native commit is
corrected to the actual ded724a4 freeze. The ongoing overwrite log records the
transition, fresh bounded-model completion and the retained Control r1 failure.

Large outputs, caches, model files and the frozen native source remain on H:.
Completed native measurements used four jobs. They are not five-job build results.
Frozen native adapters and receipts are not edited to change that fact.

## Commands and verification

Ran `git status --short --branch`, `git worktree list --porcelain`,
`git log -5 --oneline`, `git stash list`, ancestor counts and Git hash-object
checks. After switching, C: main matched origin/main with ahead/behind0/0 and
`git diff HEAD --exit-code` passed. The former C: branch still resolved to91f5057b.

App adapter checks:13 passed, including five-job environment and real Control
packaging-boundary checks. Component fixtures:13 passed. The read-only component
plan identifies the C: app checkout, H: native root and unchanged resource floors.
Final diff checks passed. Native adapter CRLF conversion initially blocked the
frozen-byte gate before starting a phase; restoring exact LF bytes allowed the
legacy phase to launch from C:. Scoped gitattributes now preserves those bytes.
No product runtime change or new native build is claimed by these source checks.

## Residual risks and next steps

The user then requested organization without deleting repository files.
`organize.py` first passed its read-only plan, then moved15 explicitly reviewed
untracked units into `_docs/local-archive/2026-11-09-pre-main/files`, preserving
their original relative paths. It included ignored descendants, for6622 files
total. All before/after SHA256 maps matched; deletedFiles=0. `before.json`,
`moves.jsonl` and `result.json` remain beside the files. The archive is locally
ignored by one scoped rule. No tracked source was moved and no stash was used.

`prepare_resources.py` passed its plan and execution, authenticated the old signed
reference with built-in trust and full payload hashes, staged fixed Prism0.4.1
and TurboQuant0.4.0 plus reviewed notices, and preserved both entire previous
C: resource trees by rename. The production sibling/runtime/notices/public-assets
verifier passed on the actual new C: resources. Nothing was deleted.

The preserved archive was NTFS-compressed with `compact.exe /C /S:<archive> /I /Q`
to retain C: disk headroom without deleting files. Compact completed and reported
1,932,129,559 logical bytes stored in1,400,398,734 bytes. A fresh full SHA256
check of the6622 original archived files passed after compression.

Control attempt r1 failed after the historical recipe import replaced the
independent environment override. That fragile import was replaced with the
explicit equivalent package/stage recipe; fresh same-volume staging preserves
the old Control whole, and the packaging-boundary test reaches the real recipe
without requiring native signing. The prior failure remains. Component staging
also now uses C: for pending/prior trees so its atomic renames remain same-volume.
Native legacy/restart/comparison/resource/audit,
component signing, NSIS, overwrite and installed WebView2 checks remain pending.

Self-review-event: ticket_completed (checkout/concurrency/organization checks). The user's explicit
location/concurrency correction justifies the narrow project AGENTS update;
PC-wide rules and existing resource/clean-source gates are unchanged. The
read-only path-encoding failure and historical-import QA defect are retained.
No broader governance change is justified. Reversal is a normal switch back
to the retained old branch and restoration of these scoped source changes.
