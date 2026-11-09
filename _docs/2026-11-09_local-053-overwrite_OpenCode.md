# Local 0.5.3 overwrite and installed WebView2 verification

Date2026-11-09. OpenCode. IN_PROGRESS. User requested existing PR updates,
main commit/push, overwrite installation and Playwright real-app verification,
then added GUI refusal-direction removal. Goal is an actual installed, verified
candidate; new speed-plan source is unavailable and is not part of this build.

## PR updates completed

- https://github.com/Niko1221/Strata/pull/4989 normal merge/push head
  `8e1ff872dd3e5203b6212eab9f839148c92733c1`; MERGEABLE. Five-file scope retained.
  Focused44 passed. Broader268 passed/1 skipped/1 failure; the Linux lspci case
  fails identically against unchanged upstream code on this Windows host.
- https://github.com/Niko1221/Strata/pull/4248 normal merge/push head
  `50915d9f22cbf1db976bc58a47661430d41e1ace`; MERGEABLE, draft retained.
  Actual built Harness + synthetic loopback worker:4 passed,0 skipped.
- PR descriptions now state the exact latest base146df3c4, results and limits.
  Narrow five-file credential scans passed; broad merge scans flagged unchanged
  public upstream test-key/header-GGUF fixtures, verified byte-identical to upstream.
  Local PR logs/bodies remain outside their committed diffs. No force push.

## Candidate and constraints

Product0.5.3-local.1, Control0.5.4, native0.5.3; Metal remains independently
0.5.0-metal. Pinned Node24.22.2, packaged Python3.12.15, Hakua-memory0.3.5,
Prism0.4.1 and TurboQuant0.4.0 retain their measured byte identities.
Output is fresh `H:/Strata/releases/local-053-20261109-opencode`.
Explicit C: install target is `%LOCALAPPDATA%/Programs/Strata`.
Old local.2 components, binaries, profiles and weights are retained.
RAM3GiB/commit4GiB/C5GiB/H10GiB floors, serial native work and owned Job gates
remain enabled. Latest observation before work:23GiB free RAM, no matching
shell/native/llama process. No absent server is restored as if it had been running.

The supplied corrected design document explicitly retracts unverified ef3df253
source/test claims. Git object is absent locally and no relevant remote branch
was found. It is a design input, not code, build input or evidence of speed gain.

## GUI implementation and source checks

GUI labels the bundled Qwen3.8 projection as refusal-direction removal, uses
explicit opt-in persisted settings, verifies vector pin and actual selected
binary help, preserves custom vectors/user args, and shows real loaded/observed
current-child status. Q36/Prism/TurboQuant/DeepSeek remain visibly unsupported.
No weight rewriting or general behavioural/speed guarantee is claimed.
Host93 passed/1 Harness prerequisite skip; overlapping affected follow-up53 passed;
Python19 passed; TypeScript1024MiB check passed. Existing language suite's56-key
zh gap reproduces on unmodified HEAD. New18 feature strings have nine catalogs.
See the GUI helper log for exact commands. Native/app helper small tests passed
31/10 respectively; this is not execution of their build/install phases.

## Execution plan and evidence

Freeze reviewed source, build native from a clean detached source root, run the
functional/resource checks, bind the measured executable hash into Host admission,
compose/sign the new component, then build fresh Control and NSIS. Qualify exact
payload and production self-tests, perform one backed-up overwrite, and attach
Playwright over CDP to the **installed EXE's WebView2** in isolated profiles.
Candidate-extracted and installed-E2E results are distinct. Finish with normal,
non-debugging unloaded app startup. Record every failed attempt separately.

Build, signature, qualification, overwrite, installed-model/browser results and
artifact hashes are pending real execution. No formal compliance, new release,
all-model quality or full-window qualification is claimed.

## Main freeze and real build execution

Main GUI/version/helper checkpoint `26e5889625938459580313ca7ce6b3931606c27b`
was committed and pushed; remote main matched. Version consistency and its six
tests passed. Frozen native source is the clean detached worktree
`H:/Strata/worktrees/native-053-source-20261109` at that commit. New app source may
advance for measured digest admission without changing that native checkout.

The first actual configure passed with CUDA13.3.73/MSVC19.44.35224.0, sm120,
then the adapter's cache parser falsely rejected the actual120 value by spanning
comments/blank lines. No engine compilation had started. The owned Job drained
all243 processes with0 active children and no floor stop. It remains a failure.
The complete failed output was preserved at
`H:/Strata/releases/local-053-20261109-opencode-configure-failed-r1` after receipt,
source and absence-of-binary checks. The narrow per-line parser correction passed
54 small tests and all actual550 cache entries; expected settings/floors unchanged.
Fresh init and explicit launch now run the real one-job build under the original
output root, with independent receipts. Its completion is still pending.

The previously constrained Windows Job fixture group was rerun under fresh H:
scratch with adequate resources:27 passed,0 skipped,15.54s. The earlier C:-temp
failures remain in the previous source integration record; no guard was changed.
The TypeScript1024MiB check also now passes after resource recovery.

Installed E2E recipes now include actual Japanese refusal-projection inspection
and unsupported Q36 enable rejection before persistence/job/unload. Source-only
helper checks pass; actual browser receipts are still required. Do not infer a
positive applied projection test from a Q36 unsupported result.

## Packaging preparation while native compilation runs

Fresh component composition helpers are prepared under
`_docs/local-053-20261109/component/`:13 fixture cases and syntax/help/plans passed.
They require current native functional/model evidence, preserve the completed
resource FAIL as FAIL, authenticate the older runtime-only inputs, and create a
new signed native0.5.3 composite/ZIP with fixed Prism/TurboQuant trees. Their
real compose/sign/stage operations have NOT_RUN. No inherited pass is copied.

The production Host build initially failed when the generic test wrapper's
256MiB NODE_OPTIONS propagated to Vite's child; parent CLI heap flags alone did
not change that child budget. With >3GiB available RAM and explicit isolated
child NODE_OPTIONS1024MiB, the actual approved-assets production build passed:
458 modules,8.70s. Existing dynamic-import/large-chunk warnings remain. The
normal package adapter already specifies1024MiB. This is a frontend build, not
an NSIS, overwrite or GPU/runtime result.

Applied compatible canonical prompt, PC/project AGENTS; Common, Start Gate,
Skill Selection, DeepResearch, Security, Application, WebApp, Frontend, Python,
TypeScript, CPP and Rust SOPs; baseline skills plus build-manager/qa-engineer and
yaraikata-memo. Scope-owned helper work is logged in this directory. Source checks
and actual output receipts, not helper intent or reported prior passes, gate installation.
