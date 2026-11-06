# Main integration and release continuation

Date: 2026-11-06. Implementer: OpenCode. Status: IN_PROGRESS.

## Objective and acceptance

Continue the unfinished work across feature branches, integrate it into main,
complete GUI E2E and the supplied Spin8 CUDA 13.5 A–H plan, rewrite installer
documentation against official instructions, build and verify the final payload,
perform a data-preserving overwrite installation, then commit/push, tag and
publish a new release with independently checked downloads and signatures.
The runtime exposes no Goal API; the full objective is tracked in this log and
the session task list. Partial source integration is not release completion.

The supplied `strata-readme-20261106.json` is a historical session export, not a
README configuration. Its relevant messages confirm the A–H continuation. Raw
session contents, tool credentials, private reasoning fields and user profiles
are not release inputs. The existing Spin8 execution plan and revision-2 input
are retained in the sibling Spin8 worktree.

## Starting state and decisions

- Original checkout: `codex/windows-latest-0.4.1` at `91f5057b`; pre-existing
  untracked evidence and Control backup are preserved.
- Fresh main worktree: `H:/Strata/worktrees/main-integration-20261106`.
- Local main fast-forwarded from `61a619a5` to public main `c50ca06a`.
- GitHub Latest is v0.5.1, published 2026-11-06T00:32:27Z. Publication metadata
  was checked with `gh`; full asset downloads have not been repeated here.
- `git fetch --all --tags` fetched immutable tags but returned a rejection for
  the existing local `latest` alias. It was not forcibly moved.
- The KV/UI branch has 16 unique commits and 58 changed files relative to its
  merge base. Its merge into main is staged without conflicts and without a
  merge commit, pending verification. FP16 remains opt-in and unqualified for
  full-window/model quality. Published 0.5.1 behavior must remain intact.
- Chat revision recovery and KVA guards are already equivalent on main.
  Snapshot validation and child-absence recovery have newer upstream versions.
  The deployment-only gh-pages branch is not an application source branch.
- Missing intake candidates include saved native KV display, hybrid-memory /
  observation / web-reference / skill-import work, destination disk accounting,
  small-context tuning, and the explicit local-stall override. Reconcile newer
  manual-load, chat-file, engine-selection and model-import behavior.

## Required evidence

| Requirement | Evidence needed | State |
| --- | --- | --- |
| Branch integration | Patch disposition, reviewed merge, focused and full regressions | IN_PROGRESS |
| GUI E2E | Real Host/UI/browser flows, selection/history/save/error ownership, installed WebView2 | NOT_RUN here |
| Spin8 A | CUDA 13.5/SM120 baseline, off/on, resource checks and actual model startup | Pending |
| Spin8 B | Versioned CPU/CUDA contracts, independent numerical and rejection tests | Pending |
| Spin8 C/D | Native and external adapter hook/equivalence evidence | Pending |
| Spin8 E/F | Codec/layout and all state transaction/lifecycle evidence | Pending |
| Spin8 G/H | Model-bound learned evaluation and dedicated compressed-attention qualification | Pending |
| Documentation | Official sources, accurate app/Terminal distinction and actual release assets | Pending |
| Overwrite install | Backup inventories, exact payload, restart and data preservation | Pending |
| Release | New immutable tag, remote SHA, asset hashes/signatures, anonymous readback | Pending |

## Standards and tools

Applied the supplied PC/project AGENTS, compatible canonical preimplementation
context, Common, Implementation Start Gate, Skill Selection, DeepResearch,
Security, Application Development, LLMOps, Internet Connectivity, WebApp,
Frontend Design, CPP, Python, TypeScript and Rust SOPs. Skills: already-loaded
MILSPEC/deep-research baselines, goal, plan-mode, github-repo-management,
qa-engineer and subagent-driven-development (required by the inherited Spin8
execution plan). No formal standards compliance claim is made.

Use existing design tokens and test/build recipes. GPU/runtime operations must
respect the inherited process-ownership and resource boundaries; active unrelated
inference is not a test fixture. Keep published assets immutable and signing keys
outside source and logs. A new source snapshot is required for compiler trials.

## Commands and observed results

- Git status, branch inventory, worktree inventory, remote URLs and recent logs
  inspected. Existing uncommitted work in sibling worktrees was identified.
- `gh auth status`: authenticated; `gh release list --repo zapabob/Strata --limit 12`:
  public v0.5.1 identified as Latest.
- `git worktree add H:/Strata/worktrees/main-integration-20261106 main`: passed.
- `git merge --ff-only origin/main`: passed, main now c50ca06a.
- `git merge --no-ff --no-commit codex/qwen36-low-precision-kv`: automatic merge
  passed; no commit yet. Tests pending.
- The default `python` command resolved to the WindowsApps alias and did not
  parse the supplied export. Node's JSON parser read only selected visible
  conversation fields instead. This is a tool-resolution failure, not a test.
- `npm ci --offline --ignore-scripts --no-audit --no-fund` failed because the
  existing cache lacked locked Vite 6.4.3. Repeating without `--offline` installed
  the same 80 locked packages; no manifest/lock changes or install scripts.
- Integrated Host `npm run typecheck`: PASS. Nine focused Node test files:
  61/61 PASS, including actual Host manual-start behavior and browser component
  lifecycle tests. These component fixtures do not establish full-app E2E.
- Python 3.12.10 selected through `uv run --no-project --offline --python`.
  First focused Python run: 70 passed, 21 failed. Twenty failures came from
  using C-drive pytest temporary output with the inherited H-drive-only resource
  runner. Fresh H-drive `--basetemp` rerun: 90 passed, one failed. The remaining
  failure was an obsolete two-value assertion against a later historical
  progress label; the evidence bytes were not changed. The test now explicitly
  accepts that checkpoint and additionally asserts historical kind/date and
  unknown throughput/wall time. Its verification is pending.
- Spin8 B1 implementation in its sibling worktree: 8/8 CPU CTest suites,
  including 499 v2 cases and a pure-C caller. Independent spec review PASS;
  independent quality review APPROVED with a fresh strict Release build and
  3/3 focused suites. GPU/common adapters remain separate pending requirements.

## Residual risks and next actions

Many inherited results are scoped historical evidence, not measurements of the
integrated tree. CUDA 13.5 compilation previously hit the physical-RAM floor;
the plan includes a pending build-sharding investigation. GUI hardware identity
and family-capability follow-ups remain in the KV worktree ledger. Training
inputs and special-model qualification resources must be established for G/H.
No new installation, release, or tag has been performed by this session.

Next: verify the merged KV/UI changes, integrate the reviewed missing features,
resume bounded Spin8 development with separate spec and quality review, then
collect final GUI/native/package/install/publication evidence.

## Local-install-first steering and integration checkpoint

The user explicitly requested this PC's overwrite installation first, then said
to continue. Prioritize a local GUI/Control candidate and preserve the installed
qualified native engine 0.5.1; unfinished Spin8 CUDA/native changes are not being
represented as installed or released. The current C-drive shell reports 0.5.1
and is stopped. A stale HKCU uninstall entry still names an older H-drive preview,
so the actual C-drive target and shortcuts require explicit verification.

The 11-commit hybrid branch was integrated after independent SPEC and QUALITY
review. Review found and the branch fixed durable settings/import failures,
lost packaged engine exit codes, stale update/restart observations and loss of
the first unsent chat draft when opening search. The final branch is 7523fdb9.
Independent final review ran 47/47 focused CPU checks and approved the change.
After merging with the saved-native-KV display fix, 40/43 selected checks passed;
three failed before exercising code because direct invocation omitted the required
scratch environment. Re-running those three with the retained isolated runner and
the actual private Node 24.22.2 passed 3/3. No assertion or cleanup guard changed.

The earlier historical-log assertion fix passed all 10 tests in its module.
Main contains ff340b92 (KV/UI merge), cbe1d6e1 (reviewed Spin8 CPU merge), f30b8cf0
(saved KV labels), a9354008 (RAM documentation), and c0ae10b9 (historical setup log).
Full browser/installed checks remain pending. No remote push or release yet.

Self-review-event: qa_defect, review-only. Evidence: the incorrect C-drive pytest
temp selection and missing isolated Node runner caused setup failures. Preserve
the required H-drive output and existing scratch-environment runner in subsequent
commands. Rejected alternative: weaken the guards or count pre-execution failures
as application failures. No AGENTS/skill/SOP changes are needed.
