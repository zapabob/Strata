# Hakua 0.8.7

This Windows update improves local Inkling-2-Mini SC117 loading reliability and context selection while retaining the 0.8.5 CUDA engine and Control 0.6.3, and attaches the standalone Q38, Q36, and HY4 CUDA 13 engine packages alongside the desktop installer.

## SC117 context and Expert scratch improvements

- **64K–128K context steps**: The Models screen now offers 16K increments across 64K–128K (`81,920`, `98,304`, `114,688`, `131,072`) in addition to the existing SC117 context choices and any custom prepared size.
- **Consistent local-profile context handoff**: Loading a prepared local SC117 profile now applies the selected conversation context from both the main Models view and the Manage dialog, while keeping the prepared profile file untouched on disk.
- **Automatic Expert scratch fallback**: Before starting an Inkling engine with `--expert-cache-dir`, the host checks whether the configured volume has enough free space for the variant's estimated Expert scratch payload (SQ-10: 0.5 GiB, SQ-15: 2.75 GiB, SQ-20: 6.0 GiB) plus the engine's 5 GiB reserve. If the configured volume lacks space or is not writable, Strata automatically redirects `--expert-cache-dir` to a writable fallback volume (checking `STRATA_INK_SCRATCH_DIRS`, model/executable volumes, and mounted fixed or USB drives by largest free space) and logs the redirection. If no volume has enough headroom, Strata fails fast with a clear message instead of failing silently inside the engine.
- **Serve-mode engine error logging**: `engine/src/inkling2/ink_main.cpp` now always writes `open:` and `init:` errors to `stderr` in addition to the `serve` protocol line (takes effect in future engine builds; this release ships the existing 0.8.5 CUDA engine component).

## Live verification on RTX 5060 Ti 16 GB (Windows)

- **Expert scratch fallback**: Verified against the installed `0.8.7` `inkling.mjs` on mounted Windows drives; requesting `inkling-2-mini-sc117-sq-15` (requires >= 7.8 GB including the 5 GB reserve) with `D:\Strata\scratch\low-space-test` (7.05 GB free) automatically redirected `--expert-cache-dir` to `C:\Strata\scratch\strata-inkling-experts-20261126` (35.1 GB free).
- **SC117 128K context load**: Verified against the installed `0.8.7` host and bundled Control with `inkling-2-mini-sc117-sq-10` at `requestedContext=131072`: engine reported `engineContext=131072`, loaded in `160.0 s`, desktop-inclusive peak VRAM `12,158 MiB` on RTX 5060 Ti, `savedProfileUnchanged=true`, and unloaded cleanly via `native.unload`. (The unauthenticated probe to `/v1/chat/completions` returned HTTP `401` as expected because API-key auth is enabled.)

## Release assets and SHA-256

- `Strata-0.8.7-windows-x64-setup.exe` (`cd348b568708baf65cacd602be83d9464e60257f47306fdba6940aab86a1565e`)
- `Strata-0.8.7-windows-x64.tar.7z` (`7fb0bb7f6d71ee4f44ed2a9faff2c20d23f64970bc83debd5e8c12d6896e3368`)
- `strata-engine-0.8.5-windows-x86_64-cuda-cuda13.tar.gz` (`72672f6c84a6eba9f89afd3b416c1d07533ee2b97632f5fe7685107c3dae6201`) — `strata.exe` + `strata-inkling2.exe`
- `strata-q38-0.6.9-windows-x86_64-cuda-cuda13.tar.gz` (`6505bb523f435560e3ba32b3312b0949f17d7fa4bdf402b819c453506685e43c`) — `strata-q38.exe` (Qwen3.8 CUDA 13)
- `strata-q36-0.6.9-windows-x86_64-cuda-cuda13.tar.gz` (`85190ae7353c0b60a30fae8ac6d7f368f09767ed602748f655454cd5c106b887`) — `strata-q36.exe` + `strata.exe` (Qwen3.6 CUDA 13)
- `strata-hy4-0.1.64-windows-x86_64-cuda-cuda13.tar.gz` (`fad3a1952f6fe6304eeddd57db76cb74f87b34a04b78f5fb83e895898f93ff91`) — `strata-hy4.exe` (HY4 CUDA 13)
- `SHA256SUMS.txt`

Verified with `app/host` TypeScript typecheck (`tsc --noEmit`), 49/49 focused host tests (`inkling-unsloth-4gb-updater.test.mjs`, `packaged-control.test.mjs`), bundled Node 24.22.3 UI build and `verify-release.mjs`, Tauri NSIS packaging, and per-user silent overwrite installation preserving existing local SC117 profiles.

The 0.8.7 desktop installer and companion CUDA engine archives are unsigned. This validation does not qualify full-window inference or general model quality. The release qualification flag remains false (`releaseQualified=false`).
