# Official 0.2.12 integration, preserving fork contracts

Owner: OpenCode. Date: 2026-11-09. Status: source conflicts resolved; validation
partly BLOCKED. The user subsequently requested main commit/push; see
`2026-11-09_main-upstream-0212-push_OpenCode.md`. No new binary build or release.

## Request, scope and sources

Merge official latest features, vulnerability updates and bug fixes through Python.
Where equivalent features overlap, use the official API/implementation and carry
forward the fork's useful behaviour. Preserve Hakua consent/authenticated memory,
Hermes, Q36 bounded/mapped/cache/admission ownership, Prism/Qwen35 fixes, generic
GGUF reuse, GUI reconnect/state persistence, signing keys, Spin8/TurboQuant opt-ins
and the existing Windows job/resource gates. No formal compliance claim.

Fresh first-party checks:
https://github.com/Niko1221/Strata/releases/tag/v0.2.12
https://github.com/Niko1221/Strata/commit/146df3c468739147f520ac3816de806f71232571
`gh api repos/Niko1221/Strata/security-advisories` returned an empty public list.
This is not proof of no vulnerabilities or of dependency safety. No new CVE ID or
exploitation claim is made. The reviewed incoming fixes include the MMQ row-table
over-read margin, transfer-copy ordering, bounded adaptive copy ranges and tool
protocol handling. Tests/compile/hardware evidence must be recorded separately.

The current official tag and main point to the same commit:
`146df3c468739147f520ac3816de806f71232571`; tag object
`123bad4acd5fd3fe70f02ad4c938e0c360efe5e5`. Previous common upstream cut:
`9f7d977d220e9fdf2ec53cf2620cdadac1cfb24e`. 95 incoming commits;
158 changed paths. The fork has384 divergent commits at the start.

## Isolation and preconditions

Base: `dce71248c61992a9ba1e8af99711c2eccc795f4e`.
Worktree: `H:/Strata/worktrees/upstream-0212-integration-20261109`.
Branch: `integration/upstream-0212-20261109`.
Backup: `backup/pre-upstream-merge-20261109T044752Z`.
The unfinished README/7z edits remain untouched in main-integration-20261106.
They describe older measured payloads, not this new source. Installed model/app
processes are not stopped. Low RAM still prevents native builds/packaging under
the existing3GiB physical /4GiB commit /5GiB system-disk /10GiB output-disk floors.

Applied compatible canonical prompt, PC/project AGENTS, Common, Start Gate,
Skill Selection, DeepResearch, Security, Application, WebApp, Python, TypeScript
and CPP SOPs. Baseline deepresearch/MILSPEC and event-driven self-review skills.

## Python merge and reviewed conflicts

`tools/merge_upstream_fork.py --plan --upstream-ref <full SHA> --json` passed
with a clean tree, no blockers and all15 fork anchor paths present. Its old
merge-tree heuristic reports only a hint, not a complete conflict inventory.
`--execute --no-commit --backup` then performed the actual merge and stopped on
15 conflicts; no commit was created. `_docs/upstream-0212-20261109/resolve_reviewed.py`
pins both parents, the complete actual unmerged path set and hunk counts, previews
all resolutions by default, and writes/stages only with `--execute`.

Decisions: retain fork product/Control/Metal identities; upstream version numbers
are reference metadata, not fork release numbers. Combine upstream Anthropic
single-loaded-model resolution with inferenceFetch and the fork's private-memory
refusal. Combine upstream prefill accounting with private debug redaction. Add
upstream wide-ISA public entry points while keeping the fork's exact MSVC basename
recognition. Preserve VERSION-derived app checks instead of upstream0.2.12 literals.
The incoming drafting/fetch/feed/CLI implementations equal official source.
The native diff against official source retains fork tracing, allocation lifetime
and joined-worker fixes, opt-in native-cache/Spin8 hooks and exact-boundary checks.
Official MMQ margin/transfer/adaptive-range fixes remain intact. Kernel execution
is not established by this static review.

## Verification / residual risk

Fresh interpreter: uv-selected CPython 3.12.10 (not packaged CPython 3.12.15).
Node: installed private 24.22.2. Package/lock/dependency contents and trusted key
file are unchanged from the starting fork. The new worktree's ignored
`apps/host/node_modules` junction reuses the existing matching main worktree
dependencies; no dependency install/update ran.

Both the reviewed Python resolver dry run and `--execute` passed. Actual unmerged
entries are empty. `audit_source.py --output .../intake.json` passed: 158 incoming
paths, 119 exact upstream blobs and 39 adapted blobs (including EOL differences),
14 unchanged fork anchor paths/directories. This is source inventory, not proof
that all fork behaviours or GPU paths work. `git diff HEAD --check` passes with
the per-command `cr-at-eol` setting for preserved incoming CRLF files. Two actual
incoming whitespace-only lines were removed. No Git configuration was changed.

### Passed / rerun results

| Check | Actual result |
| --- | --- |
| Server tool/accounting/Q36 memory/consent group | 124 passed,1 skipped,50.75s |
| Server and parallel group | 429 passed,3 skipped,192.49s |
| Host gateway/config/drafting/inference/storage | 45 passed,0 skipped,9.995s |
| Host Q36/settings group | 78 passed;3 durable-route fixture environment failures |
| Durable-route rerun with required scratch guard | 3 passed,94.985s |
| Terminal drafting/feed/download/installer/split/contracts | 426 passed,3 upstream feed-URL expectation failures,2 skipped,71.49s |
| Tuned-drafter rerun after fork-channel adaptation | 100 passed,7.12s |
| Version/Q36/setup, excluding constrained bounded-run file | 161 passed,1 startup-fixture failure,24 skipped,43.23s |
| Startup-log rerun with actual admission helpers | 10 passed,0.70s |
| New three Python helpers: Black | Passed after formatting |
| New three helpers: flake8, Black-compatible88/E203 rules | Passed |
| Final run_checks sample, python --version | Python3.12.10,exit0 |

Server signal tests skip on Windows. The memory group has a local optional
prerequisite skip. Q36's 24 CPU-compiler cases skip because its C++ compiler is not
configured in this shell. These are distinct from native GPU build/execution.

### Failed, blocked and not run

The first80-case group had79 pass and one missing STRATA_TEST_NODE_EXE; the later
configured124-case group includes the corrected cross-language test. One combined
server batch exceeded the shell180s deadline without final totals; no final pass
is claimed for it. The later split429-case group completed under600s. A selection
named nonexistent `test_feed.py` and ran zero cases; it was corrected to
`test_update_feed.py` before the recorded431-case Terminal group.

The first Host command used repository-root cwd, causing two esbuild path errors;
host cwd corrected them. Its third failure was an outdated source-regex check
for filename-based field hiding. That check now exercises the real architecture
policy: unsupported drafting is blocked, retained invalid settings can be cleared,
and a misleading filename does not change adapter identity. No production
filtering was reverted to satisfy the old regex. Three later durable-route cases
required STRATA_TEST_SCRATCH; configuring that guard, rather than disabling it,
made their rerun pass.

The full Q36 batch initially had22 failures:21 bounded-run cases hit their existing
H:-volume precondition under C: temp, and one isolated startup fixture omitted the
actual admission helper. A corrected H: bounded-run rerun requires3GiB free RAM;
it is deferred. The six other bounded-run cases that passed are not expanded into
an all-pass claim. The production runner/resource rules and tests' assertions were
not weakened. The startup fixture now invokes the real typed admission and legacy
checks, supplies Q36 identity with its generation, and passes all10 cases.

TypeScript `tsc --noEmit` failed with V8 heap exhaustion at the explicitly bounded
256MiB heap (exit134). Type correctness remains UNVERIFIED. Raising the work
budget, native CPU/CUDA/HIP/SYCL/Metal builds and actual-model GUI tests await
resource/toolchain availability. Final measured free RAM was147,616KiB; free
commit25,543,976KiB; C:8,787,333,120 bytes; H:256,625,016,832 bytes. The3GiB physical
floor is unmet. No user model was stopped or unloaded to make checks pass.

Initial default Black/flake8 checks reported formatting and Black's conventional
E203/79-column incompatibility. Only the three new helpers were formatted; the
explicit final lint command uses88 columns/E203 compatibility. Existing large
Python files were not broadly reformatted. No formatter failure is a GPU result.

## Commands and reproducibility

Python prefix throughout:
`C:/Users/downl/.local/bin/uv.exe run --offline --no-project --python C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe python -B`.

Merge commands: `tools/merge_upstream_fork.py --plan --upstream-ref
146df3c468739147f520ac3816de806f71232571 --json`, then
`tools/merge_upstream_fork.py --execute --no-commit --backup --upstream-ref
146df3c468739147f520ac3816de806f71232571 --json`, then
`_docs/upstream-0212-20261109/resolve_reviewed.py` and its `--execute` run.

Subsequent tests use `_docs/upstream-0212-20261109/run_checks.py -- python -B
-m pytest -p no:cacheprovider -q <paths>`. Host checks use its `--cwd host -- node
--test --test-concurrency=1 <paths>`; TypeScript used `--cwd host -- node
node_modules/typescript/bin/tsc --noEmit`. Test paths are the groups listed above:
the incoming serve test files, existing memory tests; eight `test_drafting*`
files plus update_feed/download_integrity/control_install/split_engine/contracts;
the Q36/settings Host files; versions/old_launcher/qwen36/setup_download/unsloth.
Use `--scratch-parent H:/Strata/validation` for the constrained Windows Job suite,
only after its RAM gate can be met. The helper creates a fresh owned child folder.

Final formatting: `python -B -m black --check` for the three helpers;
`python -B -m flake8 --max-line-length=88 --extend-ignore=E203` for those helpers.
The source auditor ran successfully and its full path/blob inventory is
`_docs/upstream-0212-20261109/intake.json`.

## Changed surfaces and remaining actions

The upstream merge supplies the158 incoming paths; local integration edits are
gateway/server conflict composition, the ISA-entry-point union, fork version
metadata, run-config enum validation with a regression case, official-URL fixture
adaptation, real settings-policy/startup-fixture checks, all eight README status
banners, AGENTS factual source status, release/integration records and four intake
helpers/artifacts. No executable artifact or private profile is added to Git.

Finish TypeScript and constrained Windows Job tests when memory permits. Configure
and build every changed backend on its supported host, then run bounded native
parity/actual-model checks before selecting a new source-bound installer version.
Commit/finalise the integration and reconcile the separately preserved README/7z
work only with the actual results visible. No new installer/archive is implied by
the old personal payload or by an uncommitted source merge.

## Self-review

Self-review-event: qa_defect, local_fix (check-runner environment iterations),
review-only. Evidence: missing test Node/cwd/scratch requirements, bounded H:
precondition, old startup-fixture globals and heap-limit failure above. The narrow
runner now isolates temporary HOME/components, filters inherited credentials,
sets explicit Node/Python/serial test identity, and admits an explicit scratch
parent. A formatted sample run passes. Kept existing native floors/guard and
negative assertions; rejected changing the live app, weakening resource gates,
blindly choosing a whole fork/upstream file, or rewriting PC-wide governance.
Residual risk is the uncompleted compiler/hardware/typechecking work, not hidden
behind passing source inventory or fixture counts.

## Pre-delivery staged checkpoint

Fresh final audit:158 incoming paths,119 exact/39 adapted blobs,14 unchanged fork
anchors,0 unresolved entries.160 intended files are staged. The working files
match the index; no untracked integration
artifacts remain. The inherited narrow redacted credential/payload scanner checked
all160 staged files and reported0 findings. The staged whitespace/conflict check
passed with `cr-at-eol`; the formatted source auditor passed again. This narrow
scan is not a security audit. HEAD remains `dce71248`; MERGE_HEAD is `146df3c4`.
At this pre-delivery checkpoint no commit, main promotion, push, binary build or
release had been performed. The separate main worktree then contained all earlier
README/7z preparation. The later explicit delivery request and preservation receipt
are recorded in `2026-11-09_main-upstream-0212-push_OpenCode.md`.
