# Local053 app adapter implementation log

## Overview and requirements

Prepared reusable candidate-specific app helpers for product 0.5.3-local.1,
Control 0.5.4 and native 0.5.3. User-authorised scope is only this app directory.
Output for later parent execution is H:/Strata/releases/local-053-20261109-opencode/app.
Parent owns native building/signing, metadata, source freeze, commits and execution.
Goal API is not exposed here; the objective is recorded in this log and updates.

## Context, SOPs and decisions

Read the canonical CLAUDE-FABLE-5 pre-implementation context, PC-wide instructions,
project AGENTS, project README, SECURITY and packaging documentation, historical
preparation helpers and the successful execution adapters. Applied compatible
engineering context; system/developer identity, available tools, Windows
environment, and the explicit no-subagent restriction take precedence over
incompatible prompt/skill examples.

Selected SOPs: Common MILSPECLLMOps Engineering Standard, Implementation Start
Gate, Skill Selection, Security, Application Development, Python and TypeScript
(for runtime JS discipline). Applied milspec-codex-standard and the user-named
yaraikata-memo update style. No helper/subagent was spawned. Self-review used the
PC-wide agent-self-review-evolution completion/QA-defect workflow in review-only
mode. No governance files were edited. No web research was needed: implementation
mechanics were checked against the local production code and retained recipes.
No formal MILSPEC compliance claim is made.

The smallest coherent implementation reuses immutable recipe source rather than
maintaining another copied set of long GUI flows. It uses the successful Q36 r14
and Prism r5 execution versions, not the stale wrappers. Checked anchors and
generated-code tests detect recipe drift. All native identities are consumed
from the new parent staging receipt; independent native source binding uses the
production verifier. Fixed backend bytes are compared to the prior composite.

Assets/trust boundaries: parent-supplied signed component and receipt, frozen
app/native sources, Cargo-cache artifacts, installed managed payload, private
profiles/configs, registry/shortcuts, real packaged shell/Host, Control owner,
WebView2 loopback endpoint and actual engine argv/INFO. New files avoid signing
keys, global environment/config edits, private chat screenshots and direct
installed-source patches. Ordinary build logs and synthetic QA diagnostics stay
in fresh output directories; actual user snapshots and activation output stay in
the restricted private backup.

## Changed files

All are new in `_docs/local-053-20261109/app/`:

- `common.py`: new identities, paths, source/staging/resource/environment gates.
- `build.py`: fresh locked Control and standard NSIS with actual cache preservation.
- `verify-native.mjs`: production source/payload/signature verification adapter.
- `recipes.py`: checked qualification/successful-GUI adapters and fresh Q36 fixture.
- `isolate-host-home.mjs`: candidate-specific successful homedir preload.
- `probe.py`: real target shell/Host and native/Prism ownership checks.
- `upgrade.py`: backup, one NSIS claim, prelaunch verification, signed bounded
  test-start, installed acceptance, normal unloaded handoff.
- `adapter.py`: plan-by-default dispatcher and continuous owned-job resource guard.
- `test_adapters.py`: meaningful low-impact adapter and isolation contracts.
- `README.md`: helper-specific parent commands, acceptance and remaining gates.
- This implementation log.

## Implementation and traceability

R1 — candidate/version/source identity: common/build/native verifier consume the
parent receipt and clean reviewed app commit, record app/Control/native identities
separately, and preserve the parent's quality limits without hardcoded old hashes
or source counts. Tests verify plans avoid consuming incomplete staging.

R2 — real installed acceptance: each generated runner has explicit target,
installedExeTest, shell path/hash, actualWebView2 and actualShellAndHost. Dispatcher
checks complete qualified payload before/after, compares user hashes, and writes
separate success-only acceptance. Both targets' recipes pass fresh JS checks.

R3 — real native/Prism behaviour: successful UI selectors/headers and INFO/argv
checks are retained, Control owner binding is corrected, model configs are fresh
and bounded, and Node homedir is genuinely isolated. Preload tests execute Node
without creating files or launching the application/model.

R4 — overwrite/preservation: exact actual Cargo artifact backup, restricted fresh
small-user-data backup, old native inventory, registry/shortcuts, one exclusive
NSIS invocation, installed exact membership and prelaunch user hashes. Import
keeps full signed test-start with an observed qualified bounded config.

R5 — resource/failure/handoff discipline: continuous owned-only guard with floors
RAM3/commit4/C5/H10 GiB, retained failures, unique attempts, and final normal
unloaded launch outside the helper's QA Job Object. Boundary tests exercise all
four floors. Final normal launch checks installed-target passes first.

## Commands and observed verification

From H:/Strata/worktrees/main-integration-20261106:

```powershell
git status --short
& 'C:/Users/downl/.local/bin/uv.exe' run --no-project --offline --python 'C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe' python -B '_docs/local-053-20261109/app/adapter.py' --help
& 'C:/Users/downl/AppData/Local/Programs/Strata/node/node.exe' --check '_docs/local-053-20261109/app/verify-native.mjs'
& 'C:/Users/downl/AppData/Local/Programs/Strata/node/node.exe' --check '_docs/local-053-20261109/app/isolate-host-home.mjs'
& 'C:/Users/downl/.local/bin/uv.exe' run --no-project --offline --python 'C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe' python -B '_docs/local-053-20261109/app/test_adapters.py'
```

Initial status was clean. Help and both checked-in MJS syntax checks passed.
The initial contract run found a whitespace-sensitive Prism recipe anchor; the
next found Python's default Windows cp932 could not encode Prism's middle-dot
version label when piping generated JS to Node. Corrected the anchor and made
the test pipe explicitly UTF-8. The subsequent seven tests passed, including
all five rendered scripts. No app/model process was launched by these checks.
UV printed existing dangling-distribution metadata warnings; no package install
or environment repair was attempted.

Python validation ran through the requested uv/interpreter paths with `-B`;
AST syntax checks avoid writing bytecode. No dependency changes, format tools
with write behaviour, or repository-wide tests were needed for this helper-only
scope. Parent execution is intentionally deferred by user instruction.

Intermediate fresh rerun: all seven tests passed in 0.510 seconds after source/receipt
enhancements. Added three focused rejection tests for target substitution,
prelaunch user membership changes and pre-existing NSIS claims. Final fresh rerun:
all ten tests passed in 0.485 seconds, including all five generated JavaScript
syntax checks and the real Node homedir preload check. Explicit installed-target
`--plan` and `verify-native.mjs`'s default
plan both passed without consuming staging. `git diff --check` produced no
tracked whitespace errors. Final `git status --short --untracked-files=all`
listed only the eleven new files in this assigned app directory; historical and
other source files remained unchanged by this task.

## Self-review and residual risks

Self-review-event: qa_defect — adapter anchor and Windows pipe encoding failures
were caught by the new low-impact contract tests. Prevention is scoped to these
tests and explicit UTF-8. Evidence is the fresh failures and passing rerun above.

Self-review-event: ticket_completed — review-only handoff. Rejected alternatives:
copying historical passes, running stale wrappers, hardcoding prior hashes/counts,
changing application sources, modifying normal profiles, weakening test-start or
running a build/install/model to validate helpers. No higher-scope rule update
is justified or authorised.

New signed staging/version metadata is a parent prerequisite. Hardware execution,
signature/source verification on that input, real GUI selectors, installed NSIS
behaviour, native import/test-start, old selection pinning, private backup paths,
Windows registry/shortcuts and normal launch remain unexecuted. Recipe compatibility
can only be established by the fresh parent runs. Unexpected user-data links,
large non-weight files, active processes or resource-floor failures stop execution.
Native release/general-quality/full-window qualification remains false.

## Recommended next action

Parent supplies staging and freezes the reviewed source, then follows README's
ordered dispatcher commands. Inspect fresh screenshots and receipt targets before
the final normal unloaded handoff. Preserve all failed attempts and review a pinned
component selection explicitly if activation stops there.
