# Local overwrite installation — 2026-11-06

Status: LOCAL_INSTALL_SUCCESS. Owner: OpenCode. Scope: local installation only.

## Requirements and plan

Build integrated main (initial clean commit `1c521fba`) as app `0.5.2-local.1`,
Control `0.5.2`. Retain signed native `0.5.1` executable SHA-256
`e75716a9d5deb6289e87741d42e7003ba82b7696f6121d5203e615d9fe596a96`.
Do not build/activate a new native engine or claim Spin8 CUDA qualification.
No release, tag or push. Preserve sibling worktrees and original untracked work.

1. Bind the independent native source explicitly and test rejection paths.
2. Freeze the app/Control source, stage verified resources, build with pinned dependencies.
3. Verify exact NSIS payload, 13 production self-tests and isolated actual WebView2 navigation/metadata.
4. Back up small user state privately; run one bounded NSIS `/S /D=C:\Users\downl\AppData\Local\Programs\Strata`.
5. Compare installed payload and prelaunch user hashes; verify normal manual-unloaded startup, versions, settings, shortcuts and registrations; leave the app open safely.

Acceptance requires fresh evidence for each step. Goal API is unavailable; this
log tracks the local-install objective. Completion does not complete the parent
Spin8 A–H/publication goal.

## Standards and decisions

Applied supplied home/project AGENTS, compatible canonical preimplementation
context, MILSPEC/deep-research baseline skills, plan-mode, Common, Start Gate,
Skill Selection, Security, Application Development, WebApp, Frontend Design,
TypeScript, Python and Rust SOPs. Existing source, lock files, design authority,
security docs and prior scripts are the primary local evidence. No new dependency
versions or external package-trust claims. Also applied qa-engineer and the
agent-self-review-evolution completion/failed-gate workflow. No subdelegation or
formal compliance claim.

Default native source verification remains strict. Explicit source root requires
full source commit and exact manifest digest, original native source/baseline and
binary checks, a clean relevant checkout and signature verification with built-in
keys. Frozen reference: `c50ca06a863a98ff121cbff30365a035a90205e2` at
`H:/Strata/worktrees/upstream-0211-latest-20261105`. Native build identity remains
the existing `00ce436f69a9-dirty-hakua-runtimes-v1`, not main.
The historical staging manifest is unsigned; use the retained signed component
instead and compare payload hashes. Its native record has no spill baseline;
test optional-baseline rejection without inventing one for the historical build.

Resource floors: H >=10 GiB, C >=5 GiB, available RAM >=3 GiB and commit >=4 GiB.
Builds use Node 24.22.2, 1024 MiB Node heap, Cargo jobs=1, owned process containment
and timeouts. No unrelated process stops. Personal data and screenshots stay
outside checkout; public evidence contains counts, hashes, versions and booleans.

## Changed files

Product manifests/locks/constants, CONTROL_VERSION, version banner and local
candidate note; packaging README; native source verifier and focused regressions.
Owned build/qualification/install helpers and evidence are recorded below.

## Commands and results

Initial `git status --short --branch`, `git diff --stat`, `git log --oneline -10`:
clean main at `1c521fba`, ahead 26. Frozen worktree HEAD matches c50ca06a; only its
existing untracked evidence is present. Resource preflight: H 323.69 GiB, C 13.67
GiB, available RAM 7.51 GiB, available commit 12.41 GiB; no Strata shell running.

## Prebuild results

Prebuild gates: release-integrity Node tests 5/5 PASS, including native binding
default drift, partial option, commit/manifest, source, spill-baseline and binary
rejection. `tools/bump_hakua_product_version.py --check`: PASS. Host TypeScript
`tsc --noEmit`: PASS. `git diff --check`: PASS. Desktop locked offline npm install
failed ENOTCACHED for Tauri CLI 2.12.3; normal `npm ci --ignore-scripts --no-audit
--no-fund` installed the same two locked packages, exit 0, with no dependency changes.
Staging guard passed in 176.110 seconds: 23,414 Harness files, 97 notices, 3 Node
files, 38 backend files and 139 signed component files, full source/destination
hash comparisons. Retained signed component also exactly matches the installed
component. Manifest SHA-256:
`7eadce5bd58f5ffe642be86d9ff06c775de3129ebd16fa35520bed31f46882aa`.
Evidence lives in `H:/Strata/releases/local-052-20261106-opencode`.

Self-review-event: qa_defect (offline cache miss). Review-only: no governance
change; retain locked normal installation fallback and log the real failure.
Existing old staging is only a read-only resource donor. The native record has
no baseline; no baseline receipt was manufactured.

## Built source and artifact identities

App/Control source commit: `04fe91d06f95ca5f7f8622187ccd40735d7c9030`.
The subsequent changes are qualification/install helpers and this evidence log;
they do not change the compiled application or packaged Control source.
Native frozen source: `c50ca06a863a98ff121cbff30365a035a90205e2`.

Installer:
`H:/Strata/releases/local-052-20261106-opencode/Strata-0.5.2-local.1-windows-x64-setup.exe`.
Size: **112,056,754 bytes**. SHA-256:
`b77c1837c0829ff221a8de0fc4df21f898f7f45c4a8ca0f819f1a60dd5f1b87b`.
The qualified/installed NSIS-patched shell SHA-256 is
`a81a67a35683242073cb81b1220a224ce07ecba86bbc26732d06ac589acf9035`.
Its Windows ProductVersion is exactly `0.5.2-local.1`.

Fresh Terminal/Control archive SHA-256:
`d12093d966a06ec15db2bc78da4fa42016c30bb6b1a733e5a68a588864b13dda`;
size 70,581,166 bytes; Control `0.5.2`, product `0.5.2-local.1`.
Runtime lock SHA-256:
`4ffc8ef23b1c5eff02fea403f8e9e0c14421bb85bd8fe202b334f6c5982a28a2`.
Standalone CPython `3.12.15` archive pin:
`194c8f0d9e0de6f1c4576e5dfa67819a48c764be87608b74b8ad43387a57b93b`.
Node `24.22.2` SHA-256:
`1c331340fa6cac5e4294725959070a143fa0507195a78ad77eed7943f719aac9`.
Hakua-memory `0.3.5` and Pillow `13.0.0` verified by the locked recipe/probes.

## Execution and acceptance evidence

All receipt paths in this section are under
`H:/Strata/releases/local-052-20261106-opencode` unless stated otherwise.
Application sources were clean when frozen and built. Tauri rewrote two generated
schema files' working-tree line endings; Git's normalized diffs are empty.
No semantic schema changes were adopted.

| Requirement | Actual result | Evidence |
| --- | --- | --- |
| R1: exact integrated app/Control versions | PASS, app/shell/Host 0.5.2-local.1; Control 0.5.2 | `app-build.json`, `control-build.json`, installed startup |
| R2: independent native binding | PASS; default main-root drift rejected; explicit frozen source accepted; native signed manifest and all bytes checked | `app.txt`, `app-qualification.json`, `resources.json`, five release-integrity tests |
| R3: exact package payload | PASS; source/resource comparisons, documented UNK→NSS shell-marker substitution only, immutable pre-runtime inventory | `app-qualification.json`, `qualified-payload.json` |
| R4: production self-test | PASS, all 13 steps in actual extracted production shell | `selftest-profile-r2/app-selftest.json` |
| R5: actual isolated WebView2 | PASS, 17 checks, zero page/console errors; no inference | `packaged-ui.json`, `ui-result-r6.json` |
| R6: backup + explicit destination | PASS, 781 files / 3,548,154 bytes privately backed up, no model weights copied; one NSIS invocation to C: | `backup.json`, `nsis-install.json` |
| R7: pre-first-launch equality | PASS, all 29,468 installed files equal the qualified archive inventory; all 781 user files unchanged; all 139 native component files unchanged | `installed-payload.json` |
| R8: actual registration/shortcuts | PASS, both registry views name the new C: target/version; Desktop and Start Menu shortcuts target C: | `installed-payload.json`, `shortcuts.json` |
| R9: normal profile startup | PASS for functional startup: 10 idle/unloaded observations, settings/registrations retained, packaged Control and usable engine versions correct | `installed-startup-qualified.json` |
| R10: normal user handoff | PASS, app left open with debugging disabled; 10 idle/unloaded observations; model/context settings and registry retained | `user-handoff.json` |

The isolated WebView2 checks used existing Qwen3.6, Hikari PQ2_0 and split Swift
GGUF metadata. They checked idempotent import, original-file references without
copying weights, split membership, model labels, 96K/128K context editing, CPU
MoE placement, saved-profile persistence, widths 1440/768/375, chat/monitor/skills/
tasks navigation, actual instruction-only skill preview/import and Search web
dialog opening/cancel. No search query or model generation was requested.

The installed normal-profile check observed **four handled HTTP 404/no-turn
responses from `/api/chat/attach`**, with zero page exceptions. The production
contract in `server/index.mjs` returns that exact code when a previous in-memory
turn is absent; `src/lib/store.ts` handles that case by retaining the reply and
clearing streaming. The final check required every response to be precisely
404 + `code: no-turn` on that route and every corresponding browser console
message to be that resource error. Other errors remain failures. This is not a
zero-console-error claim: `consoleClean` is explicitly false in the receipt.

### Backup and installation

Private backup:
`H:/Strata/private-backups/upgrade-052-local1-20261106-opencode-r2`.
Private preflight receipt SHA-256:
`09d687b937e4fcc476dc3bf3cd11512d1c8cedc1c41fe86107e92133e1637c7d`.
It covers `.strata/data`, Roaming/Strata and the selected Local/Strata settings,
tuning, launch and component-selection state. The first incomplete backup is
retained separately; the accepted backup is the fresh `-r2` directory.
Model weights and package-download cache payloads were not copied/deleted.

NSIS started `2026-11-06T14:00:40.817896Z`, ended
`2026-11-06T14:04:54.652747Z`, **exit 0**. Exact arguments were `/S` followed by
`/D=C:\Users\downl\AppData\Local\Programs\Strata`.
The stale registry's H: target did not exist at backup time; no H: application
files were deleted or rewritten. Both actual uninstall registry views and both
shortcuts now resolve to C:. No unrelated application registrations were edited.

Final normal app PID at handoff: 30460. A fresh process check confirmed a visible
window, the expected C: executable and ProductVersion `0.5.2-local.1`. Remote
debugging arguments were absent from its descendants. The user-facing process
is intentionally left open; no build/test background worker remains.

### Commands

Project Python commands used `uv run --no-project --offline --python
C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe python -B ...`.
The build scripts invoke this same interpreter to drive the project packaging
helpers; those helpers deliberately install/probe their pinned standalone Python.
This is the project-native packaging-runtime exception, not a dependency update.
The uv runner warned about pre-existing dangling site-packages directories; it
did not alter them. System interpreter is only a build/QA driver, not shipped.

The owned `guard.py` command was run for stages `stage-resources` (176.110 s),
`control` (199.797 s), `app` (1616.391 s), `qualify-r2` (414.438 s), `webview-r6`
(21.016 s), `backup-r2` (26.031 s), `install` (255.297 s), and `verify-installed`
(401.547 s). Each successful stage exited 0 with no guard abort. The guard used
the project's kill-on-close Job Object and memory policy, plus disk/deadline
checks, and never targeted unrelated processes.

Build calls: `packaging/package_terminal.py --target windows-x86_64 --keep-staging
--cache C:/Users/downl/AppData/Local/Temp/strata-packaging-cache`; fresh archive
passed to `apps/desktop/scripts/stage-control.py`. Tauri CLI 2.12.3 invocation:
`tauri.js build --bundles nsis -- --locked --offline`. Both prebuild and prebundle
release guards passed. Public assets were verified against the existing receipt;
Node heap=1024 MiB, Cargo jobs=1. There was no available old cargo target at the
suggested path, so this candidate owns a fresh `cargo-target` under its output.

Qualification/install commands use the checked-in helpers in
`_docs/local-install-20261106/`: `qualify-app.mjs r2`, `qa-webview.mjs r6`,
`prepare_upgrade.py`, `install-app.py`, `verify-installed.py`,
`check-shortcuts.ps1`, `qa-installed.mjs r3`, and `leave-open.py`.
The real-profile checks used bounded observation and only closed their own idle
shell; the final handoff launches normally, without CDP. All private user-file
inventories remain outside the checkout.

## Failures and their disposition

- Offline desktop npm cache miss: recovered using the same lock, scripts off.
- First qualification: resource guard stopped only the owned tree after 35.078 s
  at physical-memory pressure. It did not install anything. A fresh extraction,
  smaller QA heap and phase-boundary buffer collection passed when memory was
  available again. Resource floors were not lowered.
- WebView r1: no checks completed; its detailed helper receipt collided with the
  outer guard filename. The guard failure remains; the exact inner error was
  lost and is not reconstructed. Subsequent UI/helper and guard names are distinct.
- An installed app was opened through Explorer during the work. Read-only checks
  found one active turn and one running request. It was not stopped. While it was
  present, r2 exited through the single-instance behavior. It later closed without
  this unit stopping it.
- WebView r3/r4: isolated app/Host ran, but CDP was refused. Metadata-only diagnostic
  recorded WebView's debug argument but no listening port. Reusing the prior
  qualified recipe's Windows identity discovery, keeping all app state/WebView
  paths isolated and explicitly binding CDP to loopback, restored access. These
  changes were made together; no single-variable root-cause claim is made.
- WebView r5: 15 checks passed, then the exact Trigger phrases accessible-name
  locator timed out because the label also contains help text. The QA locator
  now matches its label prefix. r6 passed all 17 checks without product edits.
- First backup: the over-broad Local/Strata cache selection encountered model-
  derived GGUFs and a large download-cache object. It stopped before copying
  those files. The fresh r2 backup uses the original small-state recipe plus
  tuning/launch, preserving only `.updates/state.json`, not cache payloads.
- First two normal-profile console gates failed on four 404 attach responses.
  Their reports remain. The final check verified the exact documented no-turn
  contract, while preserving all settings and requiring no unexpected errors.

## Self-review and residuals

Self-review-event: ticket_completed, qa_defect, local_fix. Evidence: the retained
guard/UI/backup/startup receipts above. Decision: apply only local QA recipe
repairs (distinct receipt names, real accessible names, bounded memory, exact
no-turn classification, metadata-only diagnostics); no PC-wide rules, skills,
SOPs or product behavior changes. Rejected: stopping the user's active request,
disabling native checks, rewriting engine provenance, lowering resource floors,
copying model/download caches, or declaring a clean browser console despite the
four handled responses. The final script executions validate these local repairs.
The final real-profile QA helper records only exception type/code on a future
failure, so assertion diffs cannot leak settings into a receipt. This reporting-
only change was syntax-checked without restarting the user's handed-off app.

Public release/tag/feed assets were not changed. No release, tag, push, new native
build or engine activation occurred. The installed native component is exactly
the retained 0.5.1 component, not the integrated main native sources.
This is an unpublished, code-unsigned local app candidate, not a completed release.
Native generation, Spin8 CUDA A–H, full-window/model quality and the parent release
goal remain unqualified/pending. Existing Vite large-chunk/static-vs-dynamic import
warnings remain. Real-profile startup is functionally qualified with the four
explicitly handled no-turn console responses; private conversation contents were
not inspected or logged. Broad tests already supplied by the parent were not
rerun; this unit ran the focused changed-guard tests, type/version checks, actual
packaged shell/WebView2 and installed-payload/startup checks.

Next action: parent may resume the remaining Spin8/source work and publication
plan, preserving this installed local candidate and its independent native binding.
