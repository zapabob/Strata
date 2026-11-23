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

## Evidence to collect
Each step's exact output: manifest check, BUILD_EXIT, installer SHA, NSIS 6/6,
tar.7z SHA, GitHub Latest + asset digests, real exe SHA + reg + settings SHA.
