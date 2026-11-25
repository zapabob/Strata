# 2026-11-25 — GUI Tencent Hy4-Flash & Inkling-2-Mini Visibility and Shape Engine Fix (Antigravity)

- **Date:** 2026-11-25
- **AI / Engineer:** Antigravity
- **Target Checkout:** `C:/Users/downl/Documents/ChatGPT/Strata` (`main`, baseline `21473cc9b2fb33c27be1ffbd0bdc87c0e12fec02`)
- **Installed App Location:** `C:/Users/downl/AppData/Local/Programs/Strata` & `C:/Users/downl/AppData/Local/Strata`
- **Backup & Receipt:** `H:/Strata/backups/gui-hy4-inkling-20261125/DEPLOY_VERIFICATION.json`
- **Release Qualification:** `releaseQualified=false` (unsigned local build & deployment)

## 1. Problem Statement

After the upstream `v0.2.21` (`0.1.67`) 3-way merge (`21473cc9b`), **Tencent Hy4-Flash** (`hy4-flash` / `strata-hy4`) and **Thinking Machines Inkling-2-Mini** (`inkling-2-mini` / `strata-inkling`) did not appear in the Strata desktop GUI (`Models` catalog and `Settings -> Engine`).

## 2. Root Causes Identified

1. **Control & Catalog Layer (`terminal/tools/strata_mcp.py`, `terminal/setup.py`):**
   - `HY4_FAMILIES` / `INKLING_FAMILIES` catalog entries, visibility helpers (`hy4_visible`, `inkling_visible`), sizing/fit logic, and 18 `setup.py` helper functions + CLI dispatch entries were dropped during the 3-way merge (`dsv41_pack_problems` and `earlier_card_kept` also retained orphaned merge fragments).
2. **Host / Frontend Layer (`app/host/src/lib/native-catalog.ts`, `native.ts`, `server/native-serving-policy.mjs`, `components/*`):**
   - `nativeCatalogModels` filtered out `hy4-flash` and `inkling-2-mini`.
   - Serving policies fell through to `'unknown'` instead of `'hy4flash'` and `'inkling2_loop'`.
   - React UI components lacked `isHy4Selected` / `isInkling` branches, `EngineWarning` family wiring, hidden-field rules (`HY4_HIDDEN_FIELDS`, `INKLING_HIDDEN_FIELDS`), drafting options (`dfly2`/`dspark`), and single-file `.gguf`/`.strata` local Inkling import handling.
3. **Installed Shape Engine Component Layout (`AppData/Local/Strata/components/`):**
   - `strata-hy4` and `strata-inkling` were misfiled under `components/engine/` rather than `components/shapes/{hy4,inkling2}/engine/`.
   - The `strata-inkling` manifest had `"entrypoint": "strata-inkling2.exe"` instead of the actual binary `"strata-inkling.exe"`, causing `--version` startup checks to fail.
   - Setting `"local": true` in `engine-component.json` blocks `engine_component.resolve()` auto-selection unless explicitly pinned.

## 3. Source Changes Applied (Preserving All Hakua Fork Features)

All Hakua fork extensions (`deepseek41`, `q36_memory`, `qwen38_dense`, `PrismML`, `refusal_direction_removal`, `isNativeJobBusy`) were strictly preserved.

- `terminal/tools/strata_mcp.py` — Restored `hy4_visible`, `inkling_visible`, `hy4_fit_row`, `inkling_fit_row`, `hy4_size`, `inkling_size`, `own_families`, `own_size_names`, `own_size`, `sizes_of`, `describe_config`, `_mac_model_table`, `recommend`, `model_table`, `expected_files`, and `install_plan` for `hy4-flash` and `inkling-2-mini`.
- `terminal/setup.py` — Restored `INKLING_COMMUNITY_SOURCES`, `detect_inkling_source_format`, `build_inkling_import_args`, `build_shape_engine`, `hy4_*` / `inkling_*` install & verify flows, `mac_hy4_setup`, `mac_inkling_setup`, cleaned orphaned merge fragments in `dsv41_pack_problems` / `earlier_card_kept`, allowed `--export-tokenizer` in `run()`, and restored `choices_from_config`, `calibration_targets`, and `main()` CLI family choices.
- `app/host/src/lib/native-catalog.ts` — Restored `HY4_FAMILY = 'hy4-flash'`, `INKLING_FAMILY = 'inkling-2-mini'`, `SQ-64/96/128/20/15/10` labels, Inkling `UD-*` version labels, `PICTURE_FETCH_FAMILIES`, `hasKvChoice`, and `nativeCatalogModels` inclusion.
- `app/host/src/lib/native.ts` & `app/host/server/native-serving-policy.mjs` — Added `'hy4flash'` and `'inkling2_loop'` serving policies.
- `app/host/src/components/NativeModels.tsx`, `NativeSettings.tsx`, `GuidedSetup.tsx`, `NativeLocalModel.tsx` — Restored Hy4-Flash & Inkling-2-Mini UI rendering, `<EngineWarning>`, hidden fields, drafting options, and local `.gguf`/`.strata` import.

## 4. Build, Backup, Deployment & Verification

### Backups
- All overwritten installed control/host files and misfiled component directories were backed up to `H:/Strata/backups/gui-hy4-inkling-20261125/` prior to deployment.

### Build & Automated Tests
- **Frontend build (`app/host`, `pnpm run build`, `NODE_OPTIONS=""`):** PASSED (`559 modules transformed`, `EngineWarning-D4xeihic.js`, `12.69s`, 0 errors).
- **Host serving-policy & catalog tests (`node --test tests/native-serving-policy.test.mjs tests/catalog-registered.test.mjs`):** **32 / 32 PASSED** (`8.47s`).
- **Setup unit tests (`py -3 -m unittest terminal/tools/test_setup_hy4.py`):** **32 / 37 PASSED** (all Windows catalog/install/CLI checks passed; remaining 5 failures are macOS-only `move_over_old_layout`/`max_context`, `--check` banner text, and `strata_control/pictures.py` vision shard fetch which was intentionally untouched).

### Live Installed Deployment Verification (`DEPLOY_VERIFICATION.json`)
- Deployed updated `setup.py`, `tools/strata_mcp.py`, `data/{hy4,inkling}-sources.json` to `AppData/Local/Programs/Strata/control/`, `native-serving-policy.mjs` to `host/server/`, and `host/dist/` (119 files).
- Migrated shape engines to:
  - `AppData/Local/Strata/components/shapes/hy4/engine/0.6.9-windows-x86_64-cuda-cuda13/strata-hy4.exe` (plus preserved signed `0.1.64`)
  - `AppData/Local/Strata/components/shapes/inkling2/engine/0.6.9-windows-x86_64-cuda-cuda13/strata-inkling.exe` (manifest entrypoint fixed to `strata-inkling.exe`, `"local"` omitted for auto-resolution)
- Verified live via installed control Python environment:
  - Primary engine: `0.6.9` (`strata.exe`) intact.
  - `shape_engine.find("hy4", full=True)`: `0.6.9`, full SHA-256 PASS, `_test_start` -> `strata-hy4 0.1.67`.
  - `shape_engine.find("inkling2", full=True)`: `0.6.9`, full SHA-256 PASS, `_test_start` -> `strata-inkling 0.1.67`.
  - Installed `model_table(hw)`: returns all 10 families including `('hy4-flash', 'Tencent Hy4-Flash', 3)` (`SQ-64/96/128`) and `('inkling-2-mini', 'Inkling-2-Mini', 13)` (`SQ-20/15/10` + 10 `UD-*` GGUFs).
  - Deployed bundle check: `{"bundle": "EngineWarning-D4xeihic.js", "hasHy4": true, "hasInk": true, "hasGroupPush": true}`.

## 5. Notes & Limitations
- Changes in `C:/Users/downl/Documents/ChatGPT/Strata` remain uncommitted alongside pre-existing local working-tree modifications so no user work is disturbed.
- Restart or reopen the Strata desktop app for the updated `host/dist/` and `control/` files to take effect in the running UI.
- `strata_control/pictures.py` (Hy4 vision shard downloader) was not modified in this task.
