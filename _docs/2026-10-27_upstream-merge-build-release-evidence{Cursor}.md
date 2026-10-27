# 2026-10-27 upstream merge build+release evidence{Cursor}

実施：2026-10-27 23:14–23:45 JST（Tokyo）。作業先 `H:/Strata/worktrees/hakua-chatbot-20261027`。
GPU: NVIDIA GeForce RTX 5060 Ti 16GB, driver 616.92。CUDA toolkit used: **13.3.73**。

なんJ風に言うと「マージまでは終わってた、今夜はビルド証拠とリリース定義の殴り合い」。仮説検証はこう：

1. **H1** packaging 上の release は git tag で足りるか → `packaging/UPDATES.md` は **signed feed + Tauri minisign + GitHub latest assets** → tag だけは不足 → **棄却（release 未完）**
2. **H2** この PC で CUDA engine が建つか（sm_120 / 5060 Ti）→ Ninja+MSVC+CUDA13.3+pinned ggml → **採用（BUILD_EXIT=0）**
3. **H3** full `npm test` が緑か → 部分実行後にハング、既に 1 fail → **棄却（未完了 / FAIL）**
4. **H4** 署名なしで packaging 定義の release を完了できるか → feed/Tauri 秘密鍵なし + no-auto-push → **棄却（ブロック）**
5. **H5** proprietary が merge 後も残るか → greps ヒット → **採用**

## Packaging definition of “release” (evidence)

From `packaging/UPDATES.md` / `packaging/README.md`:

| Layer | Required for “release” |
|-------|------------------------|
| git tag | helpful, not sufficient |
| App installer build | yes (unsigned bytes OK on build box) |
| Engine/Control packages | yes |
| Ed25519 feed key + `strata-feed.json.sig` | **required** |
| Tauri minisign `.sig` on installers | **required** |
| Upload to GitHub **latest** (not prerelease) | **required** for feed consumers |

Unsigned draft / local tag / release-notes draft ≠ signed release.

Draft notes: `_docs/2026-10-27_v032-preview-release-notes-draft{Cursor}.md`

## BUILD evidence

### CUDA / CMake engine (PASS)

Commands (via `_docs/cmake-cuda-all.cmd`, log `_docs/cmake-cuda-sm120-20261027.log`):

```text
cmake -G Ninja -S <repo> -B build-cuda-sm120-verify ^
  -DCMAKE_BUILD_TYPE=Release -DSTRATA_ENABLE_CUDA=ON -DSTRATA_BUILD_TESTS=OFF -DSTRATA_PORTABLE=ON ^
  -DCMAKE_CUDA_ARCHITECTURES=120 ^
  -DCMAKE_CUDA_COMPILER="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3/bin/nvcc.exe" ^
  -DCUDAToolkit_ROOT="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3" ^
  -DSTRATA_GGML_DIR=H:/Strata/deps/ggml-3cf03257
cmake --build build-cuda-sm120-verify --target strata -j 8
```

Results (honest):

| Check | Result |
|-------|--------|
| CONFIG_EXIT | **0** |
| BUILD_EXIT | **0** |
| `strata.exe --version` | `strata 0.1.51` |
| artifact | `build-cuda-sm120-verify/strata.exe` (~79,448,064 bytes) |
| wall clock | configure+build ~12.7 min (23:19:28 → 23:32:08 JST) |
| notes | MSVC warnings (C4458 / C4211) only; no link failure |

### Full `npm test` in `apps/host` (INCOMPLETE / FAIL)

Command:

```powershell
Set-Location H:\Strata\worktrees\hakua-chatbot-20261027\apps\host
npm test 2>&1 | Tee-Object -FilePath H:\Strata\worktrees\hakua-chatbot-20261027\_docs\npm-test-20261027.log
```

Partial tally before hang kill (Tee/terminal both showed same counts):

| Marker | Count |
|--------|-------|
| ✔ pass | 39 |
| ✖ fail | 1 |
| ﹣ skip/todo | 40 (mostly `# STRATA_HARNESS_DIR is not set to a built Harness`) |

Known failure:

- `✖ without the agent component the chat says so and still uses the model the user chose` (~25.97s)

Hang: after that failure, `node --test` workers showed **CPU delta 0** for ~28 minutes; log mtime stuck at 23:16:16. Suite **force-killed** at 23:44:41 JST (`exit_code` 4294967295). **Full suite did not finish — do not claim green.**

Prior critical subset (from merge execute log) remains the last green host evidence for Hakua cancel/packaged-control paths.

## RELEASE status

| Item | Status | Evidence |
|------|--------|----------|
| Local tag `v0.3.2-preview.20261027.2` | done, **not pushed** | `git show v0.3.2-preview.20261027.2` → `7e79763f` |
| Release notes draft | written | `_docs/2026-10-27_v032-preview-release-notes-draft{Cursor}.md` |
| Signed feed / Tauri `.sig` | **blocked** | no `feed-key.json` / `tauri-updater.key` under worktree, `H:\Strata` depth-3, `D:\strata-keys`, `%USERPROFILE%\strata-keys` |
| `git push` / `gh release create` | **blocked by policy** | user historically no auto-push; not run |

Exact next commands after user OK + keys on release PC: see draft notes file.

Unsigned `gh release create … --draft` would still need push + `gh` auth and **still would not** satisfy packaging signed-feed release.

## Proprietary verify (post-merge)

```text
apps/host/server/native-control.mjs:222  async function stopCancelledLoad(...)
apps/host/server/native-control.mjs:605  function openHakuaChat(...)
apps/host/server/index.mjs               native.openHakuaChat route (present)
apps/host/server/run-config-check.mjs:26 'hakua_harness' in KNOWN_KEYS
apps/host/server/run-config-check.mjs:66 export function checkRunConfig(...)
serve/memory_harness.py / serve/server.py  hakua_harness gates present
```

Counts (rg -c on host server + serve): native-control 18 / run-config-check 3 / index 1 / memory_harness 12 / server.py 3+ hits for `hakua_harness` family.

## Goal status

**ACTIVE — not complete.**

Done with evidence: merge, local tag, README, proprietary greps, **CUDA sm_120 engine build PASS**, release-notes draft + packaging blocker documented.

Still required for COMPLETE under packaging definition:

1. Signed release artifacts (`feed-key` + Tauri updater key on release PC) **or** explicit product decision that preview unsigned packaging is out-of-scope (not claimed here).
2. Explicit user OK for `git push` / tag push / GitHub Release upload.
3. Full `npm test` completion (currently hung/killed with 1 known fail) — optional for packaging “release” but still open for this goal’s BUILD evidence bar if “full npm test” is required.

Do **not** mark UpdateGoal complete until (1)+(2) are satisfied per packaging, or a written product waiver replaces signed release.
