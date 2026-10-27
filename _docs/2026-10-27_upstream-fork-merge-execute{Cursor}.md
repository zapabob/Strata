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

**Not run (recorded blockers, do not invent):**

- Full engine CMake/CUDA GPU build on RTX 5060 Ti
- Full `npm test` suite in `apps/host` (subset only)
- Signed feed / Tauri updater artifacts (`packaging/UPDATES.md` release PC keys)
- `git push` / GitHub Release asset upload (no auto-push)

## README status

`README.md` rewritten to state this is `zapabob/Strata` forked from `Niko1221/Strata`, synced to upstream v0.2.6, with proprietary inventory and **only previously measured** Windows preview numbers. Translated READMEs track upstream wording.

## Goal status

**ACTIVE** — merge + conflict resolve + host critical tests + local tag + README rewrite are done. Missing for COMPLETE: signed release packaging / optional remote publish after explicit network allow, and optional full GPU engine build evidence.
