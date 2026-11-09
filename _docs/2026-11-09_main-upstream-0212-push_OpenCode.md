# Main delivery of the official 0.2.12 source integration

Date: 2026-11-09. Owner: OpenCode. Status: source integration committed to main,
pushed and remote-readback verified. This follow-up record documents delivery.

## Request and scope

The user explicitly requested: 「メインにコミットプッシュ」.
Deliver the reviewed upstream integration to origin/main. This is source delivery,
not a binary release or a statement that pending type/native/hardware checks pass.
Apply the already-read compatible canonical prompt, project/PC AGENTS, Common,
Start Gate, Skill Selection and Security standards; baseline MILSPEC/research and
event-driven self-review instructions. No formal compliance claim.

Starting fork/main: `dce71248c61992a9ba1e8af99711c2eccc795f4e`.
Incoming upstream parent: `146df3c468739147f520ac3816de806f71232571`.
Integration worktree: `H:/Strata/worktrees/upstream-0212-integration-20261109`.
Main worktree: `H:/Strata/worktrees/main-integration-20261106`.
Origin: `https://github.com/zapabob/Strata.git`.
The freshly queried remote main matched the starting main. No force update is
planned or authorised. Existing user model processes remain active.

## Preserved unfinished README/7z work

Main originally contained12 modified tracked documents and5 untracked preparation
files. Preserve these before its fast-forward, rather than include an unexecuted
packager or pre-integration download text in the source-delivery commit.

Executed on main:
`git stash push --include-untracked --message "preserve README and 7z preparation before upstream 0.2.12 main integration"`.

Retained stash: `b060266a49696898ac59e9f7a0d4bd970f90ec52`.
It contains17 files,907 additions/88 deletions, including the rewritten READMEs,
HAKUA install/release notes, packaging docs, implementation log, distribution
INSTALL/RELEASE_NOTES/artifact pins and `packaging/preview_bundle.py`.
Main became clean. Existing older stashes were retained. Do not drop this stash.
For later reconciliation, its base is the starting main above; its README edits
need to retain the newer upstream supporter/source-status changes when reapplied.

## Verification before the source commit

Inspected both statuses, recent10 commits, remotes, staged critical API/test diffs
and existing hooks (only sample hooks; no hook bypass). Fresh source audit:
158 incoming paths;119 exact upstream/39 adapted blobs;14 unchanged fork anchors;
0 unresolved merge entries. The narrow staged credential/payload checker inspected
160 staged files before adding this delivery record and reported0 findings.
The earlier CPU/local-HTTP tests and all failures/skips are in
`2026-11-09_upstream-0212-integration_OpenCode.md`. No runtime code changed during
this delivery, so those same-source test results are reused without claiming a
new full test run.

Still open: TypeScript heap-limit failure,21 constrained Windows Job reruns under
H: and adequate RAM, native backend compilation and actual-model qualification.
The existing four CUDA resource failures/`releaseQualified=false` remain visible.
The source promotion does not replace the installed personal local.2 payload.

## Executed delivery and verified receipt

The final pre-commit credential/payload scan passed for161 staged files; the
staged whitespace/conflict check passed. `git diff --exit-code` showed no
unstaged integration edits. Normal commit hooks were not bypassed.

Source merge commit: `773013efdf4c75f6f54ee5102ef3aef3cbfc6711`.
Message: `[Other] merge upstream 0.2.12 while preserving Hakua APIs`.
Parents: `dce71248c61992a9ba1e8af99711c2eccc795f4e` and
`146df3c468739147f520ac3816de806f71232571`.

`git merge --ff-only integration/upstream-0212-20261109` advanced main to this
exact commit. Its checkout was clean. `git ls-tree` on the stash's third parent
confirmed all5 previously untracked README/7z preparation files were preserved.

`git push origin main` succeeded: `dce71248..773013ef main -> main`.
Fresh `git ls-remote origin refs/heads/main` returned the complete source merge
SHA above. `git status --short --branch` then showed `## main...origin/main`
with no edits. The following documentation-only commit records this observed
source push; it does not change the tested runtime sources or qualification.

Self-review-event: ticket_completed (Git source-delivery unit only), review-only. Preserve
the source-versus-binary distinction and the named stash. No governance or test
gate was weakened to perform the user-authorised Git delivery.
