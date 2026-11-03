# Mapped-live + H: reclaim 2026-11-04 04:12–04:21 JST

- Purpose: remeasure headroom; if VRAM free run mapped-live; else reclaim H: safely (DESIGN #6: do not kill Hermes).
- GPU: RTX 5060 Ti — **15321 / 16311 MiB used**, **730 MiB free**, util ~97%.
- RAM: free **7.61 GiB** / 31.87 GiB.
- Hermes `llama-server` PIDs **22836** / **22944** still alive. Not killed.
- Decision: **mapped-live remains BLOCKED**. No Q36_STARTUP / ExpertPinPool / T03 restart / T04–T08 this turn.

## H: disk reclaim (secondary ENOSPC blocker)

| | FreeGB |
|---|---:|
| Before reclaim | 1.047 |
| After reclaim | 14.209 (later 14.423 after partial npm retry) |
| Observed reclaim | ~13.16 GB |

Deleted (obsolete / regenerable; no models / no `.q36epk` / no signed components-r3 / no current `.5` setup):

- `H:\pip_cache` (~0.25 GB)
- `H:\Strata\releases\hakua040-nsis-cargo-20261103` (~2.48 GB) — older than `.5`
- `H:\Strata\releases\hakua040-nsis-cargo-20261103-4` (~2.18 GB) — superseded by `-5`
- `H:\Strata\releases\hakua040-q36-engine-20261103` (~1.34 GB) — keep `-5`
- `H:\Strata\releases\hakua040-q36-engine-sync-20261103` (~1.35 GB)
- `H:\Strata\temp\official-first-run-r{2,3,4,5,6,7,8,9,10}` — stale QA sandbox engine extracts
- `H:\Strata\tmp` (~0.67 GB) — stale subprocess temps

Partial / locked:

- `H:\npm-cache` — most cleared; remnant ~0.58 GB locked on `codegraph-kernel.node` / `node.exe` (Access denied). Not forced.

Kept untouched (verified present after):

- `H:\Strata\models\...\*.q36epk`
- `H:\Strata\releases\hakua040-preview.20261103.5\Strata_0.4.0-preview.20261103.5_x64-setup.exe`
- `H:\Strata\releases\hakua040-components-r3`
- `H:\Strata\releases\hakua040-nsis-cargo-20261103-5`
- `H:\Strata\releases\hakua040-q36-engine-20261103-5`
- `H:\Strata\releases\hakua040-native-sync-20261103`

Evidence: `h-disk-reclaim-04-12.json`, `preflight-blocker-04-12.json`, `nvidia-smi-*-04-12.*`, `ram-recheck-04-12.json`.

## Honesty labels (unchanged FAIL-open)

- T03 chat→stop→restart: **NOT_RUN**
- T04 / T06 / T07 / T08: **NOT_RUN**
- invented speeds: **false**
- goal_complete: **false**
