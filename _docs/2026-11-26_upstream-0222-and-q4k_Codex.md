# 2026-11-26 - upstream 0.2.22 security fixes, Q4_K rebuild, GGUF recognition

## Upstream sync
- upstream/main = c234774038d1c9249cb33637d27b895d47b39786 (v0.2.22). Full merge produced
  7876 unmerged paths because upstream moved tests/ to terminal/tests/; merge aborted in a
  disposable worktree at H:\Strata\worktrees\upstream-0222-merge.
- Cherry-picked 15 upstream security/bugfix commits into branch codex/upstream-0222-merge,
  including d86322048 and 4999a979a (browser /api restriction, SVG/HTML sandbox),
  75f76a8a3 and 89ef8456a (conflicts resolved preserving fork's `proc` variable).
  Conflicting sampling/app-UI commits were skipped where fork APIs differ.
- Fork features are kept; no `-X theirs` whole-tree overwrite was used.

## Q4_K rebuild, name without bonsai2
- Recipe: H:\Strata\evidence\phase13-agentic-hybrid\heretic_modeB_nvfp4_dense_q4k_recipe.json
  (120 PQ2_0 dense attn tensors changed to Q4_K; output/embed stay Q6_K; experts NVFP4).
- Output: H:\Strata\models\inkling2-heretic-q4k\Inkling-2-Mini-Heretic-ModeB-NVFP4-DenseQ4_K.gguf
  15,036,265,248 bytes (14.004 GiB), sha256 prefix 1806c06942efbb47, BUILD_RC=0.
- No "bonsai2" in the new directory or model name.

## GGUF recognition and PrismML
- /api/local-models/inspect recognizes the new file: id local-a0274a9d32cdb9411ef10a7f,
  quant Q4_K_M, architecture inkling2_loop, context 1048576.
- Added auto-selection in app/host/server/index.mjs: local Inkling/Prism-format GGUFs set
  runtime.backend=PrismML when it was Automatic, following the official explicit-adapter rule.
  Verified via API: BEFORE=Automatic, AFTER=PrismML.
- GUI load is still blocked by RAM protection (needs >19 GiB available, 10.8 GiB free).
  RAM/commit/disk floors were not changed. Close applications to load the 14 GiB model.

## Setup fix
- terminal/setup.py and installed Control setup.py now dispatch INKLING_FAMILIES to
  install_inkling2(); previously --family inkling-2-mini raised KeyError and left
  "The last install failed" in the GUI. py_compile passes; an SQ-10 install is running.

## releaseQualified
- Still false. The 0.8.2 installer is a local unsigned build.

## Integration into the main working tree (added)
- 49 upstream files copied from the disposable merge worktree into the main checkout.
- app/host/server/index.mjs and terminal/setup.py were merged by hand so the fork's
  PrismML auto-selection and INKLING_FAMILIES dispatch survive.
- Official API following: added setup.event(), updated fail(msg, hint, **detail) to
  emit the error event, and added frontend._FAMILY updated by use_family().
- Three upstream test files were dropped because their engine/API dependencies are not
  in this fork: test_inkling_image_cap.py, test_conversation_cache_budget.py,
  test_inkling_card_sampling_7092.py. The corresponding source files remain but are
  not claimed as qualified.
- Verification: 42 Python tests passed (ready deadline, tool result names, web key hint,
  conversation cache size, shape engine failure reason #7119) and 12 Node tests passed
  (request guard, SVG/HTML sandbox, branch keeps folder).
- releaseQualified remains false.

## Upstream sync scope and exclusions (2026-11-26)
- Full merge of upstream/main (c23477403, v0.2.22) produced 7,876 unmerged paths because
  upstream moved tests/ into terminal/tests/ and reorganized engine third-party trees.
  It was aborted in a disposable worktree; no whole-tree overwrite was used.
- Integrated by cherry-pick: security (#7130 browser /api restriction, #7130 follow-up
  SVG/HTML sandbox), setup (#7119 engine failure reason, #7090 MTP auto), engine (#7089
  layer split reserves, #7093 peer-card expert budget, libgomp packaging), serve (#7035
  Inkling shared effort, #7060 READY wait, #7044 conversation cache, #7051 tool result
  names, #7092 sampling, #7043 image cap). Conflicts were resolved retaining fork code.
- Skipped or reverted because the fork API differs: #7133 thinking-budget cap (reverted
  after 6 test failures), #7082 macOS Metal, #7132 keep-alive tool call, #7084 reporting,
  #7101 GUI pause button, several app-UI commits. They remain upstream-only.
- Dropped upstream tests whose engine/API dependencies are absent here:
  test_inkling_image_cap.py, test_conversation_cache_budget.py,
  test_inkling_card_sampling_7092.py.
- Compatibility shims added to follow the official API: setup.event(), fail(..., **detail),
  frontend._FAMILY, Service.strict_model, no-key flag handling, and stubs for upstream
  hold/parser/dispatch calls introduced by cherry-picks.

## Harness verification
- Direct Control server started with the Mode B SQ-10 config and --no-api-key reached READY.
- Both MCP harnesses started: hakua-memory (8 tools) and web-search (2 tools).
- POST /v1/chat/completions returned HTTP 200. A tool-enabled request returned
  tool_calls with function "memory_recall" arguments {"query":"preference"}; a second
  returned "search" arguments {"query":"OpenCode release"}.

## Final GUI instance verification (2026-11-26)
- GUI load job finished 'done'; instance 20a78186-1035-42a7-b821-f1baa4dbecb2 status 'ready',
  port 18500, GET /health = 200.
- POST /v1/chat/completions on the GUI instance returned HTTP 200
  (chatcmpl-f6f67b49c4b44034830f3737).
- Tool-enabled request on the GUI instance returned HTTP 200 with
  tool_calls function 'memory_recall' arguments {"query":"preference"}
  (chatcmpl-f267b33a20394f4db6a65d4e).
- Direct server instance also returned HTTP 200 with 'search' tool call.
- Compatibility fixes applied to both repo and installed Control: cache/pool flag gating,
  setup event API, frontend._FAMILY, no-key handling, strict_model, and stubs for
  upstream parser/hold/dispatch references.

## Post-restart stability fix and final E2E
- After a host crash/restart, loading failed with "unsupported key cvec"; projection_key()
  was made a no-op in repo and installed Control (strata-inkling does not accept cvec).
- GUI instance ae836bc5-479e-46c1-9d71-1f9671ccca8b reached 'ready', GET /health = 200.
- GUI E2E: chat request HTTP 200, tool request HTTP 200 with
  tool_calls function 'memory_recall' arguments {"query":"preference"}.

## One-by-one upstream test/API adaptation (added)
- `terminal/serve/server.py` and installed `control/serve/server.py`: added the missing
  `from serve import inkling_dialect` import. `thinking_level_line()` (#7035) and
  `inkling_default_budget()` previously raised NameError. `py_compile` OK.
- `terminal/serve/test_inkling_config_effort.py`: adapted expectations to the official
  frontend mapping (a client's "high" reaches the Inkling template as "xhigh");
  `thinking_level_line()` still prints the config's word verbatim.
- `app/host/tests/agent-lost.test.mjs`: imported `MAX_CUT_RETRIES` (the exported constant)
  instead of the non-existent `MAX_RECOVERY_PROMPTS`; upstream 0.2.22 has the same stale import.
- `app/host/tests/agent-context.test.mjs`: removed a duplicated `const huge`; adapted three
  expectations to current 0.2.22 behavior (calibration survives model/selection; a 32K request
  in a 512K window is under the 25% raise threshold; a late compaction refusal re-shrinks every
  piece and drops the partial summary).
- Restored the official `projectForeignReasoning()` in repo and installed
  `server/agent/plugins/strata-context.mjs` (source: upstream 0a8b39376 / v0.2.20) and wired it
  into `streamWithSnapshot`, retaining the fork's `privateConversationSnapshot` and reply-cap
  behavior. Native reasoning is no longer replayed to a different provider/model.

## Fresh verification after the above
- Python targeted suite (7 files, #7133 + #7035 etc.): **70 passed** in 87.28s
  (`C:\Users\downl\AppData\Local\Temp\opencode\pytest_targeted_v2.out`).
- Node targeted suite (agent-context, agent-lost, request-guard, svg-sandbox, branch-folder):
  **54 tests, 39 pass, 0 fail, 15 skipped** (`...\node_targeted_v4.out`).
- Post-change E2E: `GET /api/health` = 200, engine `/health` = 200, chat 200,
  `memory_recall` tool call 200 (`{"query": "user"}`), `search` tool call 200
  (`{"query": "OpenCode release"}`). The first search attempt consumed its token budget on
  reasoning (`finish_reason: length`); the retry with a 320-token cap emitted the tool call.
- `releaseQualified` remains false; no RAM/commit/disk floor was changed.

## Upstream commits and dropped tests adapted one by one (added)
- **#7132 keepalive** (`e83de74d7`): `events()` of `_responses` now tracks the last byte
  (`quiet`) and yields a keep-alive when a held-back custom tool's input leaves the stream
  silent for `KEEPALIVE_S`. Applied to repo and installed Control (fork's `svc.run` signature
  retained). New `terminal/serve/test_responses_custom_keepalive_7132.py`: **3 passed**.
- **#7084 rewrapped thinking** (`752ac4519`): added `INKLING_REWRAP_BUDGET = 512` and
  `INKLING_ANSWER_OPENER`, kept the budget armed after a wrap-up for a re-opened Inkling
  thinking turn, and opened the text turn on the second wrap-up; other families are unchanged.
  Applied to repo and installed Control. New `test_inkling_rewrap_7084.py`: **7 passed**.
  Three expectations use `finish=length` because the fork's #6612 empty-reply retry leaves
  that reason even when the answer is produced (pre-existing in the fork).
- **#7044 dropped test** (`test_conversation_cache_budget.py`): **8 passed**. While adapting it,
  two real integration bugs were found and fixed in repo and installed Control:
  1. `q36_kv_receipt_matches()` had a stray copy of `engine_args`' body (NameError on `cfg`);
     restored the original receipt check from commit `953a4350c`.
  2. The auto conversation-cache budget call was inside that stray body; moved it into
     `engine_args()` with the official hy4/inkling family guard.
- **#7092 dropped test** (`test_inkling_card_sampling_7092.py`): **8 passed**. The fork's
  `server.py` shadowed `server_parts/http_api.py`'s card table and lacked the Inkling/Hy4
  entries; added them (keeping the fork's DeepSeek card). The expected key list in the test
  includes `deepseek41` for that fork feature.
- **#7043 dropped test** (`test_inkling_image_cap.py`): **17 passed** after adapting the
  exception import to the fork's `serve.server.EngineSilent`.
- After each commit/test: GUI/API E2E regression was rerun (host `/api/health`, engine
  `/health`, chat, `memory_recall`, `search` tool calls) and stayed green.
- **Pause-for-update API (0.2.22 toolbar commit `6df3f1af1`)**: added
  `app/host/src/lib/update-waiting.ts` (`strataUpdateWaiting`) and the
  `useStrataUpdateWaiting()` hook in `update-check.ts`; it reads only kept update state,
  never the network. `app/host/tests/pause-button-visibility-0222.test.mjs`: **4 passed**.
  The toolbar gating and the "Resume agents" state themselves are NOT ported: this fork
  lacks #7099 (`/resume-agents`, `onResumeAfterUpdate`), so hiding the pause button without
  a resume control would remove the only manual pause path. That remains a UI follow-up.
- Final combined Python verification (12 files): **113 passed in 117.91s**
  (`...\pytest_all_final.out`). Final GUI/API E2E: host `/api/health` 200, engine `/health`
  200, chat 200, `memory_recall` and `search` tool calls 200 (`...\e2e_final*.out`).
- `releaseQualified` stays false; RAM/commit/disk floors unchanged.

## #7099 resume-agents + #7101 toolbar gating (added)
- The fork's `agent-bridge.mjs` had lost the whole update-pause subsystem in an earlier merge
  (1841 lines vs 2167 at `0a8b39376`; `prepareForUpdate`, `updatePaused`, `pauseMarker`,
  `checkpointAndStop`, `STRATA_UPDATE_PAUSE_FILE` were absent). Restored a functional equivalent
  adapted to the current bridge: `beforeAbort`, `prepareForUpdate`, `checkpointAndStop` (checkpoint
  + pause marker + per-chat stop receipts via `update-checkpoint.mjs`), `resumeAfterUpdate`,
  `allowWork()` in `runTurn`, `status().paused`, and the two exports.
- Host wiring (repo + installed): `/api/chat/pause-for-update` and `/api/chat/resume-after-update`
  routes, `beforeUpdate`/`afterUpdate` on `createNativeControl` and the `update-strata` job
  lifecycle (resume unless the app installer took over), `CONTROL_UPDATED` message.
- UI: module-level `pauseForUpdate`/`resumeAfterUpdate`, `/resume-agents` slash command,
  `ChatToolbar` paused state from `/api/agent/status` + `strata:agents-paused`, and the #7101
  condition `{(paused || updateWaiting) && <Btn ...>}`. Four strings added to all ten locales.
- Verification: `app/host/tests/update-resume-7099.test.mjs` (10) and
  `update-resume-ui-7099.test.mjs` (3) plus `pause-button-visibility-0222.test.mjs` (4):
  **20 passed** (`...\node_7099_v2.out`; the full pause-button static assertions now hold).
  `npm run typecheck` clean.
- The pause is a functional equivalent, not a byte-for-byte copy of upstream's 326-line
  checkpoint flow: it uses the fork's `stop()` and the existing `update-checkpoint.mjs`.
- The bridge, host routes, native-control lifecycle and messages were applied to both the repo
  and the installed host (`C:\Users\downl\AppData\Local\Programs\Strata\host`), with
  `node --check` clean on every changed .mjs file. GUI/API E2E rerun afterwards stayed green.

## Final verification state (2026-11-26, end of session)
- Final E2E after the installed-host patches: host `/api/health` 200, engine `/health` 200,
  chat 200, `memory_recall` tool call 200 (`{"query": "user preferences and context"}`),
  `search` tool call 200 (`{"query": "OpenCode release"}`). Evidence:
  `...\sh_216f4d2b1001ThiXlGFQ6LlA3c.out` and `...\e2e_quick.ps1` run.
- Python: **112 passed / 1 failed** in the last combined run; the single failure was
  `test_responses_custom_keepalive_7132.py::test_function_tool_is_untouched`, a timing
  assertion (`max_gap < 2 s`) that fails under concurrent CPU load. An earlier idle run of the
  same file passed 3/3, and the later isolated rerun passed the other 2 tests; treat that test
  as load-sensitive, not as a code regression.
- Pre-existing `test_inkling_reasoning_budget.py` failures (2 × `finish` "length" vs "stop")
  were fixed: the fork left `finish = "length"` after a budget wrap / empty-reply retry even
  when the model completed the reply. Repo + installed Control now report "stop" when the reply
  was answered (`answered`) and the engine's own receipt says "stop"
  (`self.engine.last.finish == "stop"`). `test_inkling_reasoning_budget.py`: **7 passed**.
  The three temporary "length" expectations in `test_inkling_rewrap_7084.py` were reverted to
  the official "stop" expectation.
- Final targeted Python suite (13 files, includes the previously failing budget tests and all
  upstream test adaptations): **120 passed in 149.97s** (`...\pytest_final_all.out`).
- The last remaining app-UI commit, `12145b78c` (Hebrew "Resume agents" wording), was applied:
  `updateResumeButton` in `src/locales/he.json` is now "המשך עבודת הסוכנים".
- `releaseQualified` stays false by policy: the 0.8.2 installer is a local unsigned build, the
  full-window inference / general model quality / GPU concurrency remain unqualified. All
  upstream app/serve commits in the 0.2.21→0.2.22 range are now accounted for (security,
  serve, setup and app-UI); the full-tree merge itself was infeasible and remains documented.
  No RAM/commit/disk floor was changed.
- At the end of the session the GUI host and engine were down (HTTP 000, no strata-desktop nor
  strata-inkling process), so the last E2E rerun could not execute. Per the owner's decision the
  already-confirmed green E2E from after the host patches is accepted; the later Python-only
  finish fix was not E2E-verified. Restart the app and rerun `e2e_quick.ps1` when convenient.

## Release workflow v0.8.3 (owner-approved, in progress)
- Owner decisions: new immutable version `v0.8.3` (do not overwrite published v0.8.2), commit all
  132 working-tree changes, scope = app NSIS installer + SHA256SUMS, overwrite-install locally,
  publish to GitHub; no engine rebuild (no signing key); `releaseQualified=false` retained.
- Security: diff scanned for tokens/keys/private-material before staging; none found.
- Version bumped 0.8.2 -> 0.8.3 in `VERSION`, `app/host/package.json` + lock,
  `app/desktop/package.json` + lock, `app/desktop/src-tauri/Cargo.toml` + lock,
  `docs/data/release.json` (tag/assets/product_version).
- Commit `2f4ffe4dc` "[Other] Integrate upstream 0.2.22 fixes and restore agent pause/resume
  (v0.8.3)" pushed to `origin main` (`1d7d29947..2f4ffe4dc main -> main`).
- Next steps: restage Control (`stage-control.py`), UI build with `STRATA_PUBLIC_PACKAGE=1`,
  `cargo tauri build --bundles nsis`, `verify-release.mjs`, overwrite install, publish release
  and readback. Build was starting when the shell tool stalled.
- Restaging Control completed (bundle 0.6.3, 22 models / 6 families). UI rebuilt with Node
  24.22.3 and `STRATA_PUBLIC_PACKAGE=1` (24.04 s, recipe nodeVersion 24.22.3).
- `verify-release.mjs` failed on engine source binding: the staged 0.6.3 component's
  `native-build.json` does not match any available source tree, and the integration commit
  changed engine sources. Owner chose to rebuild the engine component. Fresh portable CUDA
  13.5 / sm_120 configure succeeded from `engine/` (`STRATA_PORTABLE=ON`,
  `STRATA_ENABLE_CUDA=ON`, 5 build jobs) in `H:\Strata\build\engine-083c`.
- Owner then required semantic-version unification: `engine/CMakeLists.txt` project version and
  the rebuilt component version are 0.8.3, matching VERSION / package.json / Cargo.toml.
  `docs/data/release.json` `engine_version` is 0.8.3. Control stays independently at 0.6.3.
  The all-target build linked `strata.exe` but failed on the unrelated pre-existing test target
  `strata_v1_1_inkling2_test.cpp` (missing `ModelFamily::Inkling2Loop`); the production target is
  built with `--target strata` instead.
- Final gate passed with a separate digest-bound native source root:
  `Release payload verified: Hakua 0.8.3, engine 0.8.3, Control 0.6.3`
  (`native-source-083` commit `90bd866c`, manifest `a209d071…` before repackaging).
- Version/docs/CMake changes committed as `b15f12d3e` and pushed. Engine repackaged with clean
  build ID `b15f12d3e77f`, manifest `daa09073…`. NSIS build in progress.

