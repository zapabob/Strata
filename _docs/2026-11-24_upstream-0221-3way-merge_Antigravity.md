# 2026-11-24 Upstream v0.2.21 3-Way Merge (Antigravity)

## Overview

Merged official upstream `Niko1221/Strata` **`v0.2.21`** (`d46f5f268f8ed797e83a5c63a69bffbd7a581cf6`, engine/Control `0.1.67`) into the Hakua fork (`main` at `f72af5423`, product `0.8.0` / engine `0.6.9`) using a dedicated Python 3-way merge script (`tools/merge_upstream_0221.py`).

All 8,369 fork-only / fork-retained files were preserved untouched, 502 upstream-changed files were updated cleanly with zero remaining conflict markers, and fork GUI/Engine/Terminal features were aligned to the official `v0.2.21` APIs.

## Background / Requirements

- Preserve all Hakua proprietary/custom features (Gen-F/G/H/I/J CUDA 13.5 SM120 optimizations, `q8_0_quant_avx2`, LeCaR cache, Q38/DSv41 engines, Sakura 98K `--draft` compatibility, RustXNG web search, `/btw`, `/deepresearch`, skill import/learning, refusal projection, Q36 KV/memory capabilities, Hermes memory stack, desktop shortcut creator).
- Adopt all official `v0.2.21` features, security hardening, and bug fixes across Engine, GUI (`app/host`), Serve, CLI, Control, and Docs.
- Where upstream latest features overlap with custom features, merge custom advantages into the latest upstream structure.
- Perform the 3-way merge and conflict resolution via a reproducible Python script (`logging` + `tqdm`, UTF-8, no `print`).
- Follow official upstream APIs in custom code and GUI.

## Assumptions / Decisions

- **Safety backup**: Created `backup/pre-upstream-0221-20261124` at `f72af54235c178ea6a9db9420d64a65749deaa70` before modifying any files.
- **Pre-existing dirty file preserved**: `_docs/2026-11-23_four-separate-components-disk_OpenCode.md` was left untouched.
- **3-way merge anchor**: Used `BASE = v0.2.20` (`a34979fc94`), `OURS = HEAD` (`f72af5423`), `THEIRS = upstream/main` (`v0.2.21` = `d46f5f268`).
- **Versioning**: Kept Hakua fork product version `0.8.0` in `app/desktop/package.json`, `app/desktop/src-tauri/Cargo.toml`, `Cargo.lock`, `app/host/package.json`, `package-lock.json`, and `docs/data/release.json` (while updating `docs/data/release.json`'s `"upstream"` block and `AGENTS.md` anchor to `v0.2.21` / `0.1.67`).

## Changed Files

Full 502-file manifest recorded in `_docs/upstream-intake/merge-0221-manifest.json`:

- **Added**: `tools/merge_upstream_0221.py` (reproducible Python 3-way merge & conflict-resolution script).
- **Upstream additions (`add_upstream`)**: 216 files (new v0.2.21 tests, kernels, docs, release grid, GUI components).
- **Upstream-only updates (`adopt_upstream`)**: 176 files.
- **Clean 3-way merges (`clean_3way`)**: 54 files.
- **Explicit Python conflict resolutions (56 files)**:
  - **Engine (7)**: `engine/src/kernels/cpu/native_expert.cpp` (upstream `#6552` opt-in `dot_x4_enabled` + fork Gen-I/J `q8_0_quant_avx2`), `engine/src/hy4flash/run/hy4_gpu_model.hip.h` (verified all 7 fork compatibility symbols exist in v0.2.21 + upstream `#6648` UMA pool / `#6693` 48GB / `#6744` score-arena fixes), `engine/src/inkling2/cuda/ink_cuda.cuh`, `engine/src/inkling2/cuda/ink_runner.cuh` (SM120 L2 prefetch, adaptive hot-expert tier, auto prefill chunk, `#6905` K/V growth fix, Windows 16 GiB pinned host arena), `engine/src/program/generate.cpp` (`watchdog_limits.hpp`, `adapt_coverage_rules.hpp`, `#4870`), `engine/metal/CMakeLists.txt`, `engine/tests/platform/host_limits_test.cpp`.
  - **GUI / App Host (14 + 2 API-alignment follow-ups)**: `agent-bridge.mjs` (2h `engineGraceMs` + `boundedRpc` + `agent-question-end` + fork `turn.research`/`localStallMs`/`selectSkillsForTurn`), `llm-shape.mjs` (`hy4`/`nativeAgent` + fork `samplingForPolicy`), `profile.mjs` (`INKLING_LOCAL_EFFORTS`, `xhigh`->`max`, `inst.arch` + fork `privateConversationCache`; removed duplicate legacy `effortOf`), `index.mjs` (`#6661` `drainChatStore`, `withSkills`/`historyWithSkills`, `onlyIn` validation, `hy4Local`/`inklingLocal` effort + fork RustXNG/web search/`/btw`/`strata_cache_session`/durable `beforePublish`/`rollback`/`hub.close()`/`supervisor.stop()`), `native-control.mjs` (`#6772` `mergeEnvChanges` diff-save + Hy4/Inkling hints + `arch` + fork Q36/projection/dense contracts), `native-gateway.mjs`, `run-config-check.mjs` (`inkling_thinking_budget`, `shape_title`), `native-settings.mjs` (`dfly2`/`dspark` drafting choices), `skill-files.mjs` (`#6857`), `NativeSettings.tsx` (`#6772` `base` diff-save), `native.ts` + `native-catalog.ts` (official `NativeSize['inkling']` / `hy4` / `arch`), `store.ts` (`stopSession`, Inkling default `Low` thinking), `Chat.tsx` (`#6668` QuestionCard focus, `awaitingQuestion`, `/pause-for-update` + fork `/btw` and slash commands), `Skills.tsx`, `qa1-storage.test.mjs`.
  - **Serve / Terminal / Tests**: `terminal/serve/frontend.py` (`#6734` reasoning budget), `terminal/serve/inkling_kind.py` (`--draft-beam`/`--draft-adapt` + fork Sakura 98K guard only emitting `--draft off` when `spec_opts=1`), `terminal/serve/server.py` (upstream v0.2.21 routing/crash-loop/api_keys + fork `memory_harness` & `deepseek41` hooks), `terminal/setup.py` (added `hy4_family`/`hy4_fit`/`inkling_family`/`inkling_fit` imports and `HY4_FAMILIES`/`INKLING_FAMILIES`), `terminal/strata_cli/launch/cmd.py`, `terminal/tests/terminal/launch_support.py`, `terminal/tests/terminal/update_fixture.py`, and 6 previously 0-byte test stubs restored from upstream.
- **Metadata / Docs**: `AGENTS.md`, `README.md`, `docs/data/release.json`, `docs/SETTINGS.md`, `docs/bench-results/README.md`, `terminal/data/settings-register.json`.

## Commands Run

- `git fetch upstream --tags`
- `git branch -f backup/pre-upstream-0221-20261124 HEAD`
- `terminal/.venv/Scripts/python.exe tools/merge_upstream_0221.py --mode dry-run`
- `terminal/.venv/Scripts/python.exe tools/merge_upstream_0221.py --mode apply`
- `app/host`: `.\node_modules\.bin\tsc.cmd --noEmit`, `node --check` across all `server/**/*.mjs`, `node scripts/build.mjs`, `node --test tests/run-config-check.test.mjs tests/qa1-storage.test.mjs tests/split-qa2-skills.test.mjs tests/packaged-control.test.mjs`
- Anchor & conflict-marker audit (`0` markers, `16/16` fork anchors, `13/13` upstream anchors)
- `terminal`: `unittest` on `test_arc_feed_models`, `test_inkling_fit_slots`, `test_inkling_drafting_default`

## Test / Verification Results

- **Conflict markers**: `0` across all 502 updated files.
- **Fork anchors**: `16 / 16` intact.
- **Upstream anchors**: `13 / 13` intact.
- **GUI TypeScript typecheck (`tsc --noEmit`)**: PASS (exit 0, 0 errors).
- **GUI Server JS syntax (`node --check` on all `app/host/server/**/*.mjs`)**: PASS (`SYNTAX_BAD=0`).
- **GUI Production Build (`node scripts/build.mjs` / Vite 6.4.6)**: PASS (`✓ built in 6.91s`, 558 modules transformed).
- **GUI Host Unit Tests (`packaged-control`, `qa1-storage`, `run-config-check`, `split-qa2-skills`)**: **63 / 63 PASS (0 failures)**.
- **Desktop Tauri Rust (`app/desktop/src-tauri`)**: No `.rs` source files changed in v0.2.21 (`Cargo.toml` / `Cargo.lock` retained fork `0.8.0`). `cargo check` inside this session hit Windows `build.rs` `os error 2` with `RUSTC_WRAPPER=''` (not a code error).
- **Native CUDA/C++ engine rebuild**: Not compiled in this turn (requires full CUDA 13.5 CMake build with `CMAKE_BUILD_PARALLEL_LEVEL=5` into `H:/Strata`).

## Residual Risks

- `terminal/.venv` does not have the optional `regex` package installed, so `test_updater.py` (which imports `tools.strata_tokenizer` -> `regex`) could not run inside that venv.
- `test_feed_aarch64.py` asserts `Niko1221/Strata` feed URLs, whereas this fork intentionally serves `zapabob/Strata`.
- Native C++/CUDA engines (`strata.exe`, `strata-inkling.exe`, `strata-hy4.exe`, `strata-q38.exe`) have updated source code (`v0.2.21` + fork Gen-F/G/H/I/J) and should be rebuilt with 5-job parallelism (`CMAKE_BUILD_PARALLEL_LEVEL=5`) before packaging a new release.

## Recommended Next Actions

1. Review `git status` and commit the v0.2.21 3-way merge when ready.
2. Rebuild the 4 CUDA 13.5 native engine binaries with `CMAKE_BUILD_PARALLEL_LEVEL=5` and run CTest (`host_limits_test`, `cuda_spill_guard`, etc.).
3. Bump Hakua product/engine version (e.g. `0.8.1` / `0.7.0`) if preparing a new installer release.
