# v0.7.8 — ship the Sakura/op-offload/distribution fixes

## Background
- v0.7.7 was published by another agent but does NOT contain this session's
  fixes (tag f520eca5; HEAD is 16 commits ahead). Its release assets are also
  mislabeled (v0.7.5 setup/tar.7z names under a v0.7.7 tag).
- Fixes to ship (commits after v0.7.7):
  - `f8cf23502` restore hy4_kind/inkling_kind imports in serve.py (98K startup).
  - `77e5a15ff` deep-research log: op-offload root cause, expert-vram workaround.
  - `83c47b7a2` READMEs point to release Assets, remove dead v0.7.7 links.
  - `93bcc76fe` vramfix config confirmed (391 answer, 38.9 tok/s).
  - `64d376540` launcher GPU/RAM/CPU distribution controls.
  - `dd1d9d972` / `adaf583eb` / `cf5f4e03c` Hermes 98K logs + verification.

## Plan
1. Bump product 0.7.7 -> 0.7.8 (engine family stays 0.6.7; upstream v0.2.19).
   Update VERSION, package.json/lock, Cargo.toml/lock, release.json tag+assets,
   all 8 READMEs (version + download links). `release_manifest --check` ok.
2. Commit + push; create annotated tag v0.7.8.
3. Full Tauri/NSIS build (C: v072-target, Node 24.22.3, 5 jobs, preview comp).
4. NSIS 6-scenario check; tar + tar.7z with SHA-256.
5. GitHub release v0.7.8 with 4 correctly-named assets, --latest; public SHA
   readback.
6. Overwrite-install on the real machine from the published installer payload
   (7-Zip unpack direct copy — the NSIS GUI/silent paths are unreliable here);
   verify exe SHA / reg 0.7.8 / user data / engines / GUI launch.
7. Implementation log + residual risks.

## Upstream v0.2.20 intake (added 2026-11-23)
- `git fetch upstream --tags` found v0.2.20 (upstream/main 923e2df4d,
  2026-11-23). v0.2.19..v0.2.20: 81 commits, 674 files, +76512/-14610.
- Key official changes (release notes read as primary source): unified 4-tier
  GPU+RAM+CPU+SSD MoE down to 4 GiB GPUs (EQUIVALENT to this fork's
  GPU/RAM/CPU distribution -> adopt official, keep fork's Sakura 98K vramfix
  and Hermes provider); multi-GPU --layer-split auto; Unsloth GGUF direct
  GGUF_RAW Inkling-2 quits + speedups; 4-tier HY-4 Flash; critical NVFP4 /
  long-context NaN / WDDM / setup fixes; Control/engines 0.1.66; GUI/TUI
  multi-GPU selection + settings register.
- Plan: one-way intake base v0.2.19, fork 510517c55, upstream v0.2.20 into
  worktree H:/Strata/worktrees/intake-0220; verify fork anchors; sync version
  to 0.7.8 / upstream v0.2.20 / control+engine 0.1.66; README 8 langs;
  then build -> overwrite install -> release -> tag.
- Per user policy: official features adopted; fork-only features retained;
  equivalent features take the official implementation plus fork advantages;
  fork features/GUI follow official API.

## v0.2.20 intake COMPLETE (2026-11-23)
- One-way merge applied into H:/Strata/worktrees/intake-0220 (branch intake-0220):
  8973 paths, 528 adopt_upstream, 164 three-way, 8279 retain_fork, 2 delete,
  errors 0; 8929 file writes.
- `verify_oneway_merge.py`: ok=true, fork anchors 16/16, upstream anchors 13/13,
  digest 8929 checked / 0 failures. Evidence: H:/Strata/evidence/intake-0220-apply/.
- Synced (worktree): release.json upstream section adopted verbatim from official
  v0.2.20 (tag v0.2.20, published 2026-11-22, control/engines 0.1.66, full asset
  list); Cargo.lock strata-desktop 0.7.8 (libloading left 0.7.4); 8 READMEs to
  0.7.8/v0.2.20/0.1.66 with verified Sakura vramfix wording (30.83 t/s @ 11.5,
  replacing the unreproduced 22.44 t/s @ 7.8 claim). `release_manifest --check`
  ok (0.7.8, engine 0.6.7).
- Fork features verified intact in the merged tree: Sakura vramfix config,
  distribution launcher (PpStageMb/VramReserveMb/Tier2Floor), serve hy4_kind
  fix, inkling dialect/template, Hakua UI, kuraneko1 CREDITS, 8 READMEs.
  Official 4-tier MoE / layer-split code adopted.
- Merged intake-0220 into main (merge 1500cd451), updated AGENTS.md upstream
  anchor to v0.2.20 / a34979fc / engine 0.1.66 (commit debe5b932), pushed main.
- Git after push: clean, HEAD debe5b932.

## Build prerequisites resolved (2026-11-23)
- One-way intake changed 79 files under `terminal/`; re-staged Control with
  `stage-control.py --wheelhouse H:/Strata/evidence/upstream-sync-20261116/control-inputs-v2/wheels`
  (exit 0, archive sha a9bc2238..., 22 models/6 families) so verify-release's
  terminal<->Control SHA comparison passes.
- GUI API alignment: upstream `ChatToolbar.tsx` (adopted by the intake) imports
  `dismissAgent`, which the fork's store.ts lacked (Session already had
  dismissedAgentIds). Added the official implementation (commit 14e9ebfd3).
- Host UI rebuilt with bundled Node 24.22.3 and pinned public assets
  (`STRATA_PUBLIC_PACKAGE=1`, recipe nodeVersion 24.22.3, asset commit
  03f11e2d...). `verify-release.mjs` with the digest-only Q38 preview
  (STRATA_Q38_PREVIEW_COMPONENT_DIR=H:/Strata/preview-components/9b-unsigned-local-preview)
  passed: "Release payload verified: Hakua 0.7.8, engine 0.6.3, Control 0.6.3".
- An in-flight `engine/src/inkling2/inkling2_engine.cu` change was included in
  commit 14e9ebfd3: Windows pinned-memory sizing now uses commit-safe headroom
  (7.5 GiB) and no forced 6 GiB pin floor, preventing the "host malloc failed
  for layer 0" seen during the earlier --expert-vram 11.5 benchmark. Reviewed
  and retained as a safety fix.
- Official-API GUI alignment (verified with `tsc --noEmit`, exit 0 after fixes):
  intake-adopted upstream GUI files required APIs the fork lacked; restored
  `dismissAgent` (store), `engine.shapes` (native.ts), `CatalogVersion.inkling`
  (native-catalog.ts), `isHy4Selected` (GuidedSetup), `onPauseForUpdate` prop
  (Chat.tsx, fork stop-and-send semantics), and the 'Context and memory'
  settings-section type; kept the fork's 'interrupt' BusyPlan alongside the
  official 'steer'. Commit d9e6a328c. An in-flight `expert_cache.hpp`
  declaration addition (`slot_capacity`, `scrub_loan_boundary`) was reviewed
  and retained (consistent with the Sakura host-expert investigation).
- First NSIS build (5 jobs, CARGO_TARGET_DIR=H:/Strata/releases/v078-build/cargo-target)
  was SIGTERM'd by a 600 s tool timeout while linking strata-desktop; dependency
  cache is warm. Restarted with a 1200 s timeout, log build-r2.log.
- Second build failed at Rust compile: intake-adopted main.rs calls
  `updater::start(app, token, port)` (official 0.2.20 3-arg API) while the
  fork's updater.rs kept the old 2-arg signature. Added the unused host_port
  parameter to both cfg variants (commit 6f1adcd57); `cargo check --locked`
  then passed (exit 0, only a dead-code warning for the fork's unused
  `open_helper_window`), so no further Rust API drift remains. Final NSIS
  rebuild started 2026-11-23, log build-final.log.
- build-final failed in `beforeBuildCommand` with a Python `MemoryError` while
  hashing the Q38 preview component (the 98K Sakura server held 7.31 GB and
  free RAM was ~8.8 GB at the time). Manual `verify-release.mjs` passed after
  stopping that server (free RAM 14.5 GB). Build restarted as build-r3.log.
  Note: the 98K Sakura/Hermes server on 127.0.0.1:8092 was stopped to free RAM;
  restart it after the release if Hermes 98K chat is needed again.

## Completion evidence (2026-11-23)
- `release_manifest --check`: ok (0.7.8, engine 0.6.7).
- Build: BUILD_EXIT=0 (build-r3.log), installer 127,248,061 B,
  SHA-256 `5801643fbc1e06deb1e759cfc7a832bcc21ba482c6f1271bf18b81b925a0847f`;
  host UI built with pinned Node 24.22.3 + public assets, `tsc --noEmit` exit 0,
  `cargo check --locked` exit 0, verify-release passed before build and bundle.
- NSIS upgrade/cleanup test 6/6 `ok:true` (v078-build/nsis-upgrade.log).
- tar.7z 127,251,106 B, SHA-256 `f373c13054147ed41065bd78ac0712592e94ee6958992f616775545a9135e03f`.
- Tag v0.7.8 pushed; GitHub release v0.7.8 published with 4 assets, all
  `state=uploaded` and public digests matching local exactly:
  setup 5801643f..., tar.7z f373c130..., engine 0.6.7 eb3bf3f0...,
  hy4 0.1.64 fad3a195.... GitHub Latest = v0.7.8.
- Real-machine overwrite install (v078-install.ps1): 29,714 files copied to
  C:/Users/downl/AppData/Local/Programs/Strata; strata-desktop.exe SHA-256
  `d9630231ff296f598803213dd5683b30888b9aff88c7108466178b18a30fbecf`; registry
  DisplayVersion=0.7.8; user settings SHA `6b7d7b11...` preserved; engine
  0.6.7 component present; GUI launched `Strata`, RESPONDING=True.
- Note: the 98K Sakura/Hermes server was stopped before the build to free RAM;
  restart from configs/strata-sakura-inkling2-98k-vramfix.json if needed again.

## Installed-GUI crash diagnosed and fixed (2026-11-23)
- User reported the installed GUI crashed. Crash logs
  (C:/Users/downl/AppData/Local/Strata/logs/desktop-crash-20261123-0057*.log)
  showed "the Strata App Host stopped before it became healthy: exit code 1".
- Run log root cause: `model-providers.mjs` (adopted from upstream) imports
  `REASONING_FORMATS`, `connectionReasoningFormat`, `connectionReasoningEfforts`
  from `agent/profile.mjs`, which the fork's retained profile.mjs did not export
  (Node SyntaxError, not caught by tsc/Vite because these are server-side .mjs).
  A second mismatch: the fork's native-control.mjs imports `writeTuneConfig`,
  replaced upstream by `withTuneConfig`.
- Fix (commit e01a455e4): added the official reasoning exports to profile.mjs
  and restored writeTuneConfig next to withTuneConfig, keeping the fork's Q36
  tune admission. A full host/server import-export scan (188 .mjs files) now
  reports 0 missing exports.
- Verified with patched files copied into the installed app: host started
  ("strata host — http://127.0.0.1:47831", hardware/models loaded), GUI stayed
  alive 15 s with no new crash log. Rebuild r4 + re-release/re-install pending.

## Residual risks
- Windows Authenticode signing absent; ed25519 signature checks removed by user
  decision; SHA-256 digest verification retained. `releaseQualified=false`:
  general model quality, full-window inference and GPU concurrency unqualified.
- Official v0.2.20 4-tier MoE adopted; fork's Sakura vramfix/Hermes provider and
  GUI kept. Some upstream speedups measured only by upstream/other agents and
  were not reproduced here.
- The installed GPU engine component remains the separately built, digest-
  verified 0.6.7 CUDA 13.5 package; concurrent in-flight engine source edits
  (expert-cache declarations, zero-copy mmap expert layouts) are source-only
  and were not rebuilt into a published component in this release.
