# Implementation Log: Hakua 0.8.7 SC117 Fix Release

- **Date**: 2026-11-28
- **AI**: Antigravity
- **Target**: Hakua 0.8.7 Windows desktop release (`v087-sc117-fix`)

## Overview

Resumed and completed the in-progress Hakua 0.8.7 (`v087-sc117-fix`) release work after system reboot: synchronized lockfile versions, verified host TypeScript types and unit tests, ran the public-package Node 24.22.3 UI build and `verify-release.mjs`, built the Tauri NSIS installer (`CARGO_BUILD_JOBS=5`), packaged `Strata-0.8.7-windows-x64.tar.7z` and SHA-256 checksums under `H:\Strata\releases\v087-sc117-fix`, and performed a local per-user silent overwrite install.

## Background / Requirements

- Local SC117 profiles (`sq-10`, `sq-15`, `sq-20`) needed finer 64K–128K context selection (`81,920`, `114,688`, `131,072`) and reliable context forwarding from both the main Models view and the Manage dialog.
- When the configured `--expert-cache-dir` volume (e.g., `C:\Users\...\Temp`) lacked the engine's 5 GiB reserve plus variant scratch payload, Inkling engine startup failed without redirecting to another drive with sufficient space.
- `engine/src/inkling2/ink_main.cpp` suppressed `stderr` output for `open:`/`init:` errors in `mode_serve`.
- Local candidate builds must use `CARGO_BUILD_JOBS=5`, reuse the H: drive target cache, verify payload integrity with bundled Node 24.22.3, and preserve user SC117 profiles on overwrite install.

## Assumptions / Decisions

- Retained the existing 0.8.5 CUDA engine component (`H:\Strata\build\native-source-085`, commit `1c2e93e738b848bdff4402dc866504d355bb1c01`, manifest SHA-256 `05b6defc005b8afd28f3e53439212ba406ef52eb5f6c8855b1a77512dbd6a1b2`) as declared in `docs/data/release.json`. The `ink_main.cpp` stderr fix is committed in source for the next engine build.
- Resolved `sccache.exe` from the local WinGet package directory so Cargo's configured `RUSTC_WRAPPER=sccache` ran cleanly with incremental caching.
- Used `7-Zip` (`-mx=1 -mmt=5`) for `Strata-0.8.7-windows-x64.tar.7z` since both contained archives are already compressed.

## Changed Files

- `VERSION` (`0.8.6` -> `0.8.7`)
- `app/desktop/package.json`, `app/desktop/package-lock.json` (`0.8.6` -> `0.8.7`)
- `app/desktop/src-tauri/Cargo.toml`, `app/desktop/src-tauri/Cargo.lock` (`0.8.6` -> `0.8.7`)
- `app/host/package.json`, `app/host/package-lock.json` (`0.8.6` -> `0.8.7`)
- `docs/data/release.json` (`v0.8.6` -> `v0.8.7`, assets updated)
- `app/host/server/inkling.mjs` (added `INKLING_SCRATCH_RESERVE_BYTES`, `inklingScratchPayloadBytes`, `inklingExpertCacheDir`, `discoverInklingScratchCandidates`, `resolveInklingExpertCacheDir`)
- `app/host/server/native-control.mjs` (wired `resolveInklingExpertCacheDir` into `load` and appended redirection note to instance logs)
- `app/host/src/lib/native-catalog.ts` (added `81920`, `114688` to `sc117Contexts`)
- `app/host/src/components/NativeModels.tsx` (forwarded selected context for `localProfile` loads in main view and Manage dialog)
- `app/host/tests/inkling-unsloth-4gb-updater.test.mjs` (updated `sc117Contexts` test; added scratch fallback & insufficient-space tests)
- `app/host/tests/packaged-control.test.mjs` (added packaged 131,072 context + USB/fallback scratch redirect test)
- `engine/src/inkling2/ink_main.cpp` (always print `open:`/`init:` errors to `stderr` even in `mode_serve`)
- `_docs/2026-11-28_v087-release-notes.md` (release notes)
- `_docs/2026-11-28_v087-sc117-fix-release_Antigravity.md` (this log)

## Implementation Details

- `resolveInklingExpertCacheDir` checks free space via `statfsSync` against `inklingScratchPayloadBytes(model) + 5 GiB` and verifies write access; on failure it iterates candidate directories from `STRATA_INK_SCRATCH_DIRS`, model/executable volumes, and mounted Windows volumes sorted by largest free space.
- `NativeModels.tsx` falls back to the current UI `context` when `localContexts[selectedSize.id]` is unset and differs from `installed?.context`, and passes `localContexts[m.model]` from the Manage modal.

## Commands Run

- `node --test app/host/tests/inkling-unsloth-4gb-updater.test.mjs app/host/tests/packaged-control.test.mjs` (both system Node and bundled Node 24.22.3)
- `./node_modules/.bin/tsc --noEmit` in `app/host`
- Bundled Node 24.22.3: `node scripts/build.mjs` (`STRATA_PUBLIC_PACKAGE=1`) and `node scripts/verify-release.mjs`
- `CARGO_BUILD_JOBS=5 CARGO_TARGET_DIR=H:\Strata\build\tauri-083-target` + `tauri build --bundles nsis` (logged to `H:\Strata\releases\v087-sc117-fix\build.log`)
- `tar -cf Strata-0.8.7-windows-x64.tar ...` + `7z a -t7z -mx=1 -mmt=5 Strata-0.8.7-windows-x64.tar.7z Strata-0.8.7-windows-x64.tar`
- `Strata-0.8.7-windows-x64-setup.exe /S` (per-user silent overwrite install)

## Test / Verification Results

- `tsc --noEmit`: PASS (0 errors)
- Focused host tests (`inkling-unsloth-4gb-updater.test.mjs`, `packaged-control.test.mjs`): PASS (49/49)
- `verify-release.mjs`: PASS (`Release payload verified: Hakua 0.8.7, engine 0.8.5, Control 0.6.3`)
- Tauri NSIS build: PASS (`Strata_0.8.7_x64-setup.exe`, 121.50 MiB, exit 0)
- Release bundle & SHA-256:
  - `Strata-0.8.7-windows-x64-setup.exe`: `cd348b568708baf65cacd602be83d9464e60257f47306fdba6940aab86a1565e`
  - `Strata-0.8.7-windows-x64.tar.7z`: `7fb0bb7f6d71ee4f44ed2a9faff2c20d23f64970bc83debd5e8c12d6896e3368`
  - `strata-engine-0.8.5-windows-x86_64-cuda-cuda13.tar.gz`: `72672f6c84a6eba9f89afd3b416c1d07533ee2b97632f5fe7685107c3dae6201`
  - `strata-q38-0.6.9-windows-x86_64-cuda-cuda13.tar.gz`: `6505bb523f435560e3ba32b3312b0949f17d7fa4bdf402b819c453506685e43c`
  - `strata-q36-0.6.9-windows-x86_64-cuda-cuda13.tar.gz`: `85190ae7353c0b60a30fae8ac6d7f368f09767ed602748f655454cd5c106b887`
  - `strata-hy4-0.1.64-windows-x86_64-cuda-cuda13.tar.gz`: `fad3a1952f6fe6304eeddd57db76cb74f87b34a04b78f5fb83e895898f93ff91`
- Local overwrite install: PASS (`INSTALLER_EXIT=0`, `C:\Users\downl\AppData\Local\Programs\Strata\strata-desktop.exe` version `0.8.7`, `host\package.json` version `0.8.7`, all 3 SC117 profiles preserved in `%LOCALAPPDATA%\Strata\install`).
- Normal app startup: PASS (`strata-desktop.exe` PID `34520` alive after 8s).
- Live Expert scratch fallback (`inkling.mjs` on installed 0.8.7): PASS (`D:\Strata\scratch\low-space-test` [7.05 GB free] -> `C:\Strata\scratch\strata-inkling-experts-20261126` [35.1 GB free] for `inkling-2-mini-sc117-sq-15`).
- Live SC117 128K load (`sc117-128k-verification.json`): PASS (`inkling-2-mini-sc117-sq-10`, `requestedContext=131072`, `engineContext=131072`, `loadSeconds=160`, `desktopInclusivePeakMiB=12158`, `savedProfileUnchanged=true`, clean `native.unload`; unauthenticated `/v1/chat/completions` probe returned HTTP 401 as expected).

## Residual Risks

- Desktop installer and separate CUDA engines remain unsigned (`releaseQualified=false`).
- `engine/src/inkling2/ink_main.cpp` change is not compiled into the shipped 0.8.5 engine binary; it will take effect when the CUDA engine is next rebuilt.
- Full-window generation quality and authenticated 128K completion throughput were not measured in this session.
- `tools/release_manifest.py --check` still reports 5 pre-existing historical mismatches (`CMakeLists.txt` 0.8.5 vs upstream 0.1.67, and v0.8.3/v0.8.4 doc references).

## Recommended Next Actions

- Review and push the `v0.8.7` commit/tag and upload `H:\Strata\releases\v087-sc117-fix` artifacts to GitHub Releases if publishing publicly.
- Optionally run a live SC117 128K load in the installed 0.8.7 app to verify end-to-end GPU behavior.
