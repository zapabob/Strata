# 2026-10-27 upstream fork merge execute{Cursor}

実施：2026-10-27 23:12 JST（Tokyo）。作業先 `H:/Strata/worktrees/hakua-chatbot-20261027`。

草、163 コミットの崖を実際に越えた。仮説検証はこう：

1. **H1** dirty Hakua cancel-path を失わずに merge できるか → `--stash-dirty` で `pre-upstream-merge-hakua-20261027T140640Z` に退避 → merge 後 `stash pop` 成功（`stopCancelledLoad` / F03b 復元）→ **採用**
2. **H2** `py -3 tools/merge_upstream_fork.py --execute --upstream-ref upstream/main --stash-dirty --backup --no-commit` → exit 2（想定 CONFLICT）だが mid-merge 到達 → **採用**
3. **H3** proprietary を残しつつ upstream API を取れるか → 下記 conflict 解決 → **採用**
4. **H4** host 臨界テストが緑か → native-load-cancel / chat-turn / packaged-control / session-workspace / native-settled / engine-version 全 pass → **採用**
5. **H5** 署名付き full release まで今すぐか → feed/Tauri 秘密鍵がこの worktree に無い。ローカル tag のみ → **ブロック継続（ACTIVE）**

## Merge result

| item | value |
|------|-------|
| branch | `codex/strata-hakua-chatbot-20261027` |
| merge commit | `7e79763fde955f1499779cac729cec28f97bdb18` |
| upstream tip | `upstream/main` @ `4b9e05a2` (v0.2.6) |
| previous HEAD | `67313f58` |
| backup branches | `backup/pre-upstream-merge-20261027T140453Z`, `backup/pre-upstream-merge-20261027T140640Z` |
| local tag | `v0.3.2-preview.20261027.2` (annotated, **not pushed**) |
| app version in-tree | `0.3.2-preview.20261027.2` |

## Conflict resolutions (summary)

| path | resolution |
|------|------------|
| `apps/host/server/native-control.mjs` | Keep fork `checkedSettingsConfig` + spin8 / NATIVE_FLAG_FIELDS save path; add upstream `assertSettingsFile` shim, `capabilities.dsExperts`, `ds_experts` save gate; restore stash `stopCancelledLoad` |
| `apps/host/server/index.mjs` | Both: `engineFirstRun` (upstream) + `memory.mjs` Hakua routes (fork) |
| `apps/host/src/lib/store.ts` | `turnWorkspace ?? workspaceIdForSession(...)` (Hakua override + upstream session bind) |
| `apps/host/src/screens/ModelRun.tsx` | Upstream settled skeleton (#3740) + fork `llamaPath` / `onAlternative` (F11) |
| `apps/host/package.json` / desktop package / Cargo.toml | Fork preview version `0.3.2-preview.20261027.2` (not upstream 0.2.6) |
| `apps/desktop/src-tauri/Cargo.lock` | Ours + version patch |
| `strata_control/models.py` | Fork arch descriptors (DeepSeek/Qwen/Prism) then upstream `_candidate_by_layout` |
| `README.md` | Rewritten: upstream models/install/hardware + fork notes / measured preview only |
| translated READMEs | Taken from upstream (official 0.2.6 translations) |

## Build / test evidence

**Ran (pass):**

- `node --test` critical Hakua paths: 10/10 (native-load-cancel F03/F03b, chat-turn, stream, no-model)
- packaged-control + session-workspace: 34/34
- native-settled + engine-version: 2/2
- `py -3 tools/check_upstream_cut.py` → `LOCKED`, `all_passed: true`
- **CUDA/CMake engine (2026-10-27 23:32 JST):** `build-cuda-sm120-verify` CONFIG_EXIT=0 BUILD_EXIT=0; `strata.exe --version` → `strata 0.1.51` (CUDA 13.3, arch 120, ggml `H:/Strata/deps/ggml-3cf03257`). Log: `_docs/cmake-cuda-sm120-20261027.log`. Detail: `_docs/2026-10-27_upstream-merge-build-release-evidence{Cursor}.md`

**Ran (fail / incomplete):**

- Full `npm test` in `apps/host`: partial ✔39 / ✖1 / ﹣40 then hung (~28 min CPU0); force-killed. Fail: `without the agent component the chat says so and still uses the model the user chose`. Log: `_docs/npm-test-20261027.log`

**Blocked (release):**

- Signed feed / Tauri updater artifacts — no private keys on this PC (`packaging/UPDATES.md`)
- `git push` / GitHub Release — no auto-push; needs explicit user OK
- Draft notes prepared: `_docs/2026-10-27_v032-preview-release-notes-draft{Cursor}.md`

## README status

`README.md` rewritten to state this is `zapabob/Strata` forked from `Niko1221/Strata`, synced to upstream v0.2.6, with proprietary inventory and **only previously measured** Windows preview numbers. Translated READMEs track upstream wording.

## Goal status

**ACTIVE** — CUDA sm_120 build evidence now green; proprietary greps still hit. Still missing for COMPLETE under packaging definition: **signed release** (feed + Tauri keys) and **explicit push/publish OK**. Full `npm test` also unfinished (1 fail + hang).
