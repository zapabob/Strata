# Native build and qualification adapter preparation

## Overview and requirements

Prepared a native-only, opt-in execution handoff under the user-authorized
`H:/Strata/worktrees/main-integration-20261106/_docs/local-053-20261109/native/`.
Actual build and qualification remain pending the parent's explicit clean frozen
source root, reviewed commit and execution approval. No native source or version
metadata was edited. No build, native executable, app, inference model, packager,
signing, installation, commit, push, subagent or Windows Job termination was run.
The only model-related execution was CPU tokenizer construction and reading GGUF
header metadata, without tensor loading or inference.

Plan ID: `PLAN-2026-11-09-local053-native`. Scope risk: future native execution
has high resource impact; preparation changes are isolated and reversible.
Goal API and TodoWrite are unavailable in this tool surface. The goal is recorded
here and in progress updates, and completion is based on validation evidence.

| Requirement | Implementation | Verification/disposition |
| --- | --- | --- |
| N01: Changes only inside native handoff directory | All nine authored files and validation outputs live here | Read-only Git status/diff showed no tracked source modifications |
| N02: Explicit frozen source/root and full reviewed commit | `common.freeze`, `adapter.py` gates and immutable `freeze.json` | Mocked wrong commit, dirty tree, wrong native version and wrong ggml pin all rejected |
| N03: Fresh portable one-job CUDA13.3.73/MSVC/sm120 recipe | `common.configure`, actual source build helper, compiler/cache checks | Recipe tests; actual configure/build NOT RUN |
| N04: Safe async owned execution, floors and receipts | `adapter.py`, `common.owned`, existing atomic `windows_job.run_owned` | Mocked launch reservation, duplicate rejection, Job-drain lock-release cases; actual Job execution NOT RUN |
| N05: Preserve failures and baseline policy | One-shot phases/commands, explicit diagnostic/bind only, unchanged default spill allowances | Retention/negative run tests; actual spill suite NOT RUN |
| N06: Native functional coverage and optional upstream targets | `phases.py` CPU/GPU/sanitizer/spill, exact CTest inventory and regex selection | Skip/absent selection tests; actual native suites NOT RUN |
| N07: Actual bounded/legacy short comparison, explicit restart | `model.py` r3 protocol adaptation, hash/metadata preservation and fresh comparison | Pre-READY receipt negative tests, token mismatch test, real tokenizer/header check; inference NOT RUN |
| N08: Native-only unsigned existing-packager component | `phases.stage`, `binding.mjs`, no composite/signing | Syntax/static review only; actual staging NOT RUN |
| N09: Parent metadata/results handoff with no stale counts/digests | README output map, dynamic source count and EXE hashes, audit with false release qualification | README and scripts reviewed together; real EXE/source/component results pending execution |

## Baselines and decisions

Applied the provided PC/project AGENTS instructions, canonical pre-implementation
context `C:/Users/downl/_docs/prompts/CLAUDE-FABLE-5.md` under higher-priority
identity/tool/safety constraints, and these SOPs: Common MILSPECLLMOps Engineering
Standard, Implementation Start Gate, Skill Selection, Security, Application
Development and Python. Skills: supplied milspec baseline, user-named
`yaraikata-memo`, `plan-mode`, and required completion self-review. Yaraikata's
helper-delegation steps were superseded by the user's explicit no-subagent rule;
concise progress updates and plain-language handoff were retained.

All technical claims here are grounded in local source, scripts and retained
output. No web research, new dependency or package-trust judgment was required.
The Security SOP was used for the narrow process/path/environment boundary;
this was not a repository security audit. No formal MILSPEC conformance is claimed.

Inspected the historical guard/build/qualify/followup/receipt-check scripts,
actual retained r3 model evidence, current CMake test registrations and spill
policy, `tools/build_hakua_engine.mjs`, release-integrity functions, Windows Job
helper, existing engine packager, tokenizer/header readers, project README and
packaging README. Read the adjacent app adapter's fixed output constants to
identify the shared BASE coordination requirement; no app file was edited.

Parent expected versions are product `0.5.3-local.1`, Control `0.5.4`, native
`0.5.3`. The supplied native source root must enforce native 0.5.3 and clean full
Git status; product/Control version qualification remains parent-owned.
Outputs are fixed to the requested new BASE with `native`, `native-build` and
native-only `native-component/0.5.3-windows-x86_64-cuda-cuda13`. Native init must
precede the app lane's creation of the shared BASE. Existing BASE is refused.

The old generic helper version probe is not bypassed. A failure remains in its
receipt. `probe-diagnostic` is informational. Parent may explicitly choose `bind`
to rerun the same current source helper on the retained configured build; no
synthetic record is written. No retry starts automatically. Empty explicit spill
baseline preserves the historical default allowance policy; no allowance edits.

`ef3df253` is unavailable locally. No candidate implementation or tuning flags
were reconstructed, included or qualified. No old native source count, digest,
functional pass count or resource violation count is assumed. r3's memory receipt
byte contracts are deliberately checked and any changed value fails for review.

## Changed files and implementation

`adapter.py` implements safe read-only planning, fresh init, one-shot run/launch,
source/adapter binding, exclusive reservation and token-scoped internal workers.
Workers and model drivers reject execution outside a Windows Job. Controllers
have no user-process lookup or cleanup path; locks release only after confirmed
owned Job drain. An abandoned lock needs parent diagnosis.

`common.py` defines fixed paths/tools, cleans child environments, puts temp/cache
paths on H:, strips inherited Git overrides for identity checks, captures
source/dependency/helper/adapter identity, builds the recipe, enforces admission,
uses atomic receipt checkpoints, and delegates process control to the existing
`windows_job.run_owned`. Continuous floors are RAM3/commit4/C5/H10 GiB, max phase
90 minutes, bounded child output. Process counters and memory handles are owned
only; no machine-wide process inventory is used.

`phases.py` invokes the actual source helper; verifies CUDA13.3.73 and MSVC compiler
data; stages fresh native files; packages an unsigned native-only component with
the existing packager; runs exact serial CPU/GPU targets, B2 first-use/full,
separate sanitizer and spill phases; audits fresh results without promoting them.
`binding.mjs` verifies current native source membership/bytes and both binary
hashes, never creates a build identity. Unavailable optional upstream tests are
recorded as NOT_AVAILABLE; required absence/skip/failure is not PASS.

`model.py` adapts the actual r3 line protocol, private-owner reuse/reset,
cancellation, mapped expert store and pre-READY memory contract. Actual prompt
tokenization is matched with supplied tokenizer files and GGUF metadata. Both
bounded and legacy use seven short requests, 4096 context cells, f32 KV, and at
most eight non-cancel generated tokens. Restart is a separate optional explicit
phase. Full SHA-256/size/mtime snapshots protect weights, pack, verification/done
receipts and tokenizer files around an owned driver Job. A driver failure exits
to Job cleanup before the wrapper checks preservation.

`test_adapters.py` supplies meaningful mocked negative-gate, async-reservation,
cleanup-confirmation, retention, environment, recipe, protocol and comparison
tests. `validate.py` runs only syntax/help/dry-plan/read-only tokenizer checks,
small tests and selected lint through installed offline tools, retaining each
attempt. `README.md` supplies exact parent commands, phase boundaries, failure
handling, pending evidence paths and limits. This file is the implementation log.

## Commands and evidence

Read-only `git status --short` and `git diff --stat` were run in the integration
worktree. The only reported untracked root was the already shared
`_docs/local-053-20261109/`; no tracked source diff was reported. A standalone
private Node `--version` returned `v24.22.2`. Initial Python AST/module-availability
inspection confirmed the selected interpreter had existing pytest, flake8,
black and regex modules; nothing was installed.

Primary final command:

```powershell
& 'C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe' -B 'H:/Strata/worktrees/main-integration-20261106/_docs/local-053-20261109/native/validate.py'
```

The bootstrap's direct pinned interpreter is intentional: it establishes H:
cache/temp paths before uv is started. Every Python validation child and detached
controller uses the specified uv in offline/no-project/no-config/no-managed-python
mode, with the pinned interpreter. All exact child commands and exit codes are
in `validation-20261109-155554/results.json`.

Final checks: Python AST syntax PASS; Node syntax PASS; adapter/model/binding help
PASS; no-write dry-plan PASS; tokenizer/header equality and prompt round trip
PASS; pytest **31 passed in 0.19s**; flake8 `--select=E9,F` PASS. Tool output showed
Python 3.12.10 and Node 24.22.2. Tokenizer prompt IDs were
`[760, 6511, 314, 9338, 369]`. GGUF tensor data/inference was not read/run by that
check. Full formatting/type checking was not run; focused fatal/undefined/unused
code lint, AST and regression tests were selected for this script-only handoff.

Earlier validation folders are retained. `validation-20261109-154620/` had 28
tests before the additional async/cleanup cases. `validation-20261109-154839/`
added the tokenizer check and 31 tests. The wider lint pass in
`validation-20261109-155319/` failed F401 for an unused `json` import in `model.py`;
the import was removed and the final run passed. No failure evidence was deleted
or reclassified. uv reported pre-existing dangling installed-package metadata;
there was no dependency repair or installation. The first pytest invocation saw
an upstream conftest import warning; subsequent validation explicitly uses
`--noconftest --confcutdir <this directory>` to keep these tests isolated.
Final `git diff --check` passed with no output. Final read-only `Test-Path` for
the requested release BASE returned false: no release output was initialized by
this preparation task.

## Self-review

Self-review-event: type=qa_defect scope=local053-native-adapters category=qa-coverage evidence=validation-20261109-155319/flake8.txt

Self-review-event: type=ticket_completed scope=local053-native-adapter-preparation category=docs-traceability evidence=validation-20261109-155554/results.json

Collected the failed lint and final validation evidence, reviewed phase ownership,
source version/pin gates, one-shot retention, skip handling, no-source-change
boundary and parent handoff. Decision: review-only for governance; no AGENTS,
skill or SOP changes are warranted or authorized. The narrow implementation
correction removed the unused import. Existing selected lint catches recurrence.
Rejected alternatives: broad baseline edits, relaxing Job/version/resource gates,
synthetic identity rebinding, stale source/pass-count reuse, and launch-based
verification before authorization. The final checks above verify the changed
scripts at the permitted non-launching level.

## Residual risks and next actions

Actual clean frozen source root and commit have not been supplied. No final
native source commit, executable hash, component hash or functional result is
claimed. Those are future generated data at the exact paths in README. CUDA/MSVC
configure/build, actual nested Job execution, GPU/B2 behavior, sanitizer/spill
results, model hashes across real inference and native-only packaging remain
untested. This preparation cannot establish full-window, general quality,
performance, release, installer or composite qualification.

Parent should review these adapters, freeze the full source/version state,
initialize fresh native output before the app lane creates BASE, and explicitly
launch build using README. On completion, inspect each receipt and run only the
desired next phase. Retain all resource/spill failures and let parent decide
disposition. Parent owns old fixed PrismML/TurboQuant assembly, signing, Host q36
digest update after fresh tests, installation and any future release action.
