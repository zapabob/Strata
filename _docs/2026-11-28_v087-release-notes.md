# Hakua 0.8.7

This Windows update improves local Inkling-2-Mini SC117 loading reliability and context selection while retaining the 0.8.5 CUDA engine and Control 0.6.3.

## SC117 context and Expert scratch improvements

- **64K–128K context steps**: The Models screen now offers 16K increments across 64K–128K (`81,920`, `98,304`, `114,688`, `131,072`) in addition to the existing SC117 context choices and any custom prepared size.
- **Consistent local-profile context handoff**: Loading a prepared local SC117 profile now applies the selected conversation context from both the main Models view and the Manage dialog, while keeping the prepared profile file untouched on disk.
- **Automatic Expert scratch fallback**: Before starting an Inkling engine with `--expert-cache-dir`, the host checks whether the configured volume has enough free space for the variant's estimated Expert scratch payload (SQ-10: 0.5 GiB, SQ-15: 2.75 GiB, SQ-20: 6.0 GiB) plus the engine's 5 GiB reserve. If the configured volume lacks space or is not writable, Strata automatically redirects `--expert-cache-dir` to a writable fallback volume (checking `STRATA_INK_SCRATCH_DIRS`, model/executable volumes, and mounted fixed or USB drives by largest free space) and logs the redirection. If no volume has enough headroom, Strata fails fast with a clear message instead of failing silently inside the engine.
- **Serve-mode engine error logging**: `engine/src/inkling2/ink_main.cpp` now always writes `open:` and `init:` errors to `stderr` in addition to the `serve` protocol line (takes effect in future engine builds; this release ships the existing 0.8.5 CUDA engine component).

## Packaging and verification

- **Windows installer**: `Strata-0.8.7-windows-x64-setup.exe` (SHA-256: `cd348b568708baf65cacd602be83d9464e60257f47306fdba6940aab86a1565e`)
- **Windows bundle**: `Strata-0.8.7-windows-x64.tar.7z` (SHA-256: `7fb0bb7f6d71ee4f44ed2a9faff2c20d23f64970bc83debd5e8c12d6896e3368`)
- **Separate CUDA engine**: `strata-engine-0.8.5-windows-x86_64-cuda-cuda13.tar.gz` (SHA-256: `72672f6c84a6eba9f89afd3b416c1d07533ee2b97632f5fe7685107c3dae6201`)

Verified with `app/host` TypeScript typecheck (`tsc --noEmit`), 49/49 focused host tests (`inkling-unsloth-4gb-updater.test.mjs`, `packaged-control.test.mjs`), bundled Node 24.22.3 UI build and `verify-release.mjs`, Tauri NSIS packaging, and per-user silent overwrite installation preserving existing local SC117 profiles.

The 0.8.7 desktop installer is unsigned. This validation does not qualify full-window inference or general model quality. The release qualification flag remains false (`releaseQualified=false`).
