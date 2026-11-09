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

## Explicit four-job switch and Windows test portability

The user requested four-core parallel building. On inspection the single-job
attempt had already ended (49-minute whole attempt, owned Jobs drained). The
attempted ownership-checked stop found no such MSBuild process and stopped
nothing. Actual retained error: the new upstream `flag_order_test.cu` used GCC
`__atomic_load_n`/`__ATOMIC_SEQ_CST` unconditionally on MSVC. Production engine
logic is unchanged; the test now uses the same Windows interlocked primitive as
its production header, retaining GCC's path elsewhere and every assertion.

Keep the failed attempt, all compiler output and resource receipts. A separately
reviewed transition archives only its metadata under `attempts/single-job-build-r2`,
retains the configured build path and compiled objects, and freezes the new clean
source. Native build/helper commands and CMAKE_BUILD_PARALLEL_LEVEL now request4.
RAM/commit/disk floors are unchanged. Final build and GPU test results remain
pending; do not relabel the earlier full build as a pass.

The portability/parallel checkpoint `ded724a4029cbfcf48d58821f01f88fe246c7460`
was committed/pushed and the detached native root fast-forwarded to it. Only
`tests/core/flag_order_test.cu` changed among native source/test paths. The guarded
transition archived the completed failed single-job metadata; objects remain at
the identical build path. A fresh source/adapters freeze and `bind` controller
now explicitly invoke the authoritative build helper with parallelism4.
The first helper-test run used C: scratch and the old expected parallelism1:
49 passed/5 failed. Correct H: scratch and the new user-requested expectation:
54 passed. An additional actual-cache read-only check preserved compiler.json.
The component composition pin now follows the reviewed ded724a4 native freeze.

## Fresh native functional evidence and independent Control packaging

The four-job authoritative rebind passed (17.39s with retained objects, not a
full-build performance claim). Native source ded724a4 binds765 source files.
New strata SHA2560932216088cb3a5813175d595a5f1f7f16633f4a7883c438439ded7f5c3bc410;
Q36 SHA2568aca225a2d58a35df910fc1d66e4d979d3f2cb4fb7a131ec10d4eada439bef4b.
Native-only staging, CPU and GPU suites passed; both sanitizer cases passed;
the actual MSVC flag-order GPU test passed without changing assertions.
The seven-case actual bounded protocol/driver passed. Full protected-input
posthash, legacy/restart/comparison/resource/audit results remain pending.
This exact digest is added to Host mapped admission; no arbitrary binary is trusted.

Control packaging is source-independent of native signing. Its dedicated build
may now run while native evidence finishes; every app/QA/install phase still
requires the complete signed-native receipt and production verifiers. Rust's
build concurrency is also4 per the user's request. Floors remain unchanged.

Applied compatible canonical prompt, PC/project AGENTS; Common, Start Gate,
Skill Selection, DeepResearch, Security, Application, WebApp, Frontend, Python,
TypeScript, CPP and Rust SOPs; baseline skills plus build-manager/qa-engineer and
yaraikata-memo. Scope-owned helper work is logged in this directory. Source checks
and actual output receipts, not helper intent or reported prior passes, gate installation.

## Primary checkout and five-job update

The user designated `C:/Users/downl/Documents/ChatGPT/Strata` as the primary
checkout, then requested five-way build parallelism. Main now checks out there
at `da01b4fd7c417d59fb5fee77b623acaf62dc17e2`; the former H: main worktree
is detached at that same commit. The old C: branch remains at91f5057b.
All607 previously untracked C: files retained their paths and Git content hashes.
No stash was applied or removed. The first fingerprint attempt failed before
any branch change because PowerShell decoded Japanese paths incorrectly; a
byte-preserving Git subprocess check then verified the successful switch.

App build environment now requests Cargo5 and CMake5. Component execution's
fixed app-root check and both handoff command paths now name the C: checkout.
Large outputs/caches and the independently frozen native root remain on H:.
The completed native build and its four-job frozen adapters are historical
evidence and retain their actual identities. Future native rebuilds require
an explicit five-job invocation and a separate reviewed freeze.

The actual bounded-model outer phase has now passed, including protected-input
posthash and a drained owned Job. Control attempt r1 failed: importing the
historical recipe replaced the intended independent build_env override, so it
still required the not-yet-created signed-native receipt. That failure and its
logs remain intact; Control, NSIS and the new overwrite are still incomplete.
See `2026-11-09_primary-checkout-five-jobs_OpenCode.md` for migration checks.

The later no-deletion organization request has been applied:15 local input units,
including ignored descendants, are preserved as6622 files in the C: local archive.
All SHA256 inventories matched before/after moving and after NTFS compression.
The complete old sibling-runtime and notices roots were also retained by rename;
production checks passed for the newly staged C: Prism0.4.1/TurboQuant0.4.0/notices.
Control now uses an explicit fresh-stage/preserve-whole-root recipe, replacing
the fragile historical import. Component pending/prior trees stay on C: for
same-volume renames; signed outputs/ZIP/cache remain on H:. App13 and component13
small tests passed. Native helper LF bytes were restored exactly after checkout
conversion, and scoped gitattributes protects their existing freeze hashes.

## Execution continuation and retained failures

C: main checkpoint0298af8b produced the fresh Control0.5.4 archive successfully
in97.109s (r2); r1 remains failed. The explicit five-job incremental native
rebind then passed in15.297s using retained objects. Both executables and
native-build.json remained byte-identical to the measured four-job build.
This is incremental timing, not a clean-build benchmark.

Bounded7, legacy7 and restart2 actual short requests passed. The first restart
controller disappeared before producing model results; its incomplete evidence
is preserved as attempts/model-restart-interrupted-r1. The next restart completed
its actual driver with a drained Job, then was interrupted during posthash.
That failed outer attempt is retained as interrupted-r2. An explicit separate
owned Job finished only the original protected-file posthash, checked the actual
completed driver/protocol/source hashes, and retained its recovery helper hash.
No inference result was invented or replayed as new. Fresh comparison passed.

The new CUDA resource guard actually completed with12 violations (four earlier
kernel findings plus eight IQ4 specializations). Audit retains FAIL and all
qualification flags false; quality.validate() accepted the source-bound short
functional evidence and genuine completed resource failure for this private build.
No CUDA allowances or production kernels were changed for installation.

The user explicitly approved stopping all current Strata conversations/model for
overwrite. The original conservative pause helper refused multiple turns. Before
the separately approved pause could act, the old shell and native process had
already exited; that script also stopped without action. Existing0.5.2 signature
and all141 payload members verified after partial NTFS compression. No absent
runtime is claimed to have been stopped or restored by these attempts.

Composition r1 signed/packed successfully but aborted at the unchanged C:5GiB
floor during pending staging; its drained Job and entire outputs are preserved.
Inactive runtime/Control/native041 backups and the failed C: stage were relocated
to H:/Strata/private-backups/local053-c-space-preserved-20261109 with SHA256 checks:
6041 files,0 lost. A read-only Git pack blocked relocation of old C: build output;
the complete4172-file tree was restored in place and checked against the retained
H: copy. No source reset/clean or user-file disposal occurred.

Composition r2 reached a complete verified C: pending signed payload, then failed
because deps.py still allowed the historical H: pending path. The Node source,
native765-file binding, signatures and backend byte guards passed on that C: tree.
The dependency scope now names the exact C: STAGING constant; a regression check
accepts that path and rejects the obsolete H: path before production imports.
Reuse of signed ZIP/pending bytes requires all production verifiers again under
a fresh owned Job, preserving the failed worker receipt. Source changes require
a newly source-bound Control before the app's five-job incremental build.

Self-review-event: qa_defect. The worktree migration missed one downstream scope
constant. The narrow fix and exact-path acceptance/rejection check address it;
resource, signature, dependency, clean-source and installed-target gates remain.
Do not turn a passed short test, compiler rebind or signature into release/model
quality qualification. Source-bound recovery evidence and remaining app/installed
results must still be recorded before completion.
