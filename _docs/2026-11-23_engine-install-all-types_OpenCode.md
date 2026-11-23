# Install all latest engine types on the PC (2026-11-23)

## Problem
User reported the engines were not installed on the PC. Investigation found:
- The app's `components/.updates/state.json` still had
  `engine.active`/`engine.pinned` = `strata-engine-0.6.4-...` (from 11-22), so
  the app log said "Strata engine 0.6.3 is installed" and ignored the already
  copied 0.6.8 folder.
- The 3x benchmarks used the newest Gen-I/J binaries from `H:/Strata/build`,
  which were not installed at all (strata.exe 6ac28c84,
  strata-inkling2.exe 17759a44, strata-hy4.exe cd2f36e5; q38 was the same).

## Fix
- Built component 0.6.9 from the 0.6.8 layout with all four fresh binaries:
  `strata.exe`, `strata-inkling2.exe`, `strata-q38.exe`, `strata-hy4.exe`
  (plus the unchanged strata-inkling.exe / strata-q36.exe = all engine types).
- `engine-component.json`: version 0.6.9, build_id
  `genij-021f8cf8b-cuda13.5-sm120-4engines-unsigned`, 155 files;
  `engine_component.verify(full=True)` OK.
- Installed to `C:/Users/downl/AppData/Local/Strata/components/engine/0.6.9-windows-x86_64-cuda-cuda13`
  and set `.updates/state.json` engine.active/pinned to that folder, with a
  `use-engine` history entry (0.6.4 -> 0.6.9).

## Verification
- Installed SHA prefixes match the benchmarked binaries exactly:
  strata 6ac28c84, inkling2 17759a44, q38 ab87e2e6, hy4 cd2f36e5.
- App launch log: `[host] inference — Strata engine 0.6.9 is installed;
  no model is loaded yet`; GUI stays alive (title Strata).
