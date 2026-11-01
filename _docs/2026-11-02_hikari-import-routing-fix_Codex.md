# Hikari import routing fix — 2026-11-02

## Request and acceptance

The user reported the same approximately 35 GB / 32 GB free error again after the earlier runtime-only recovery. Their selected model remains the existing Hikari-Bonsai 27B, and switching its inference ownership from Hermes to Strata was already authorized. Acceptance: prevent the Hikari GGUF from entering unrelated native Qwen Q2_0 preparation, apply the fix to the installed Control, and confirm an actual Hikari response.

The earlier recovery record is 2026-11-02_hikari-local-model-recovery_Codex.md. Its successful API load did not establish that the UI import route was repaired. This follow-up supersedes that limited closeout.

## Evidence and cause

The installed host is http://127.0.0.1:47831. Fresh native jobs repeatedly selected family qwen / model Q2_0 with the Hikari folder as gguf_dir; the last observed failed setup started at 05:29:35 JST. The errors were repeat operations, not merely stale text.

POST /api/native/local/preview on Hikari-LoRA-fixed-scale-PQ2_0.gguf returned plausible, candidate qwen/Q2_0, basis prism_pq2_0_descriptor, and no issues before the fix. Its metadata was architecture qwen35, 851 tensors, with BF16=96, F32=353, PQ2_0=402. Source and installed strata_control/models.py both assigned this fallback candidate to qwen35 or Prism encodings.

NativeLocalModel.tsx uses that candidate and plausible status to enable Prepare and load. Its existing unsupported-variant path already offers Try with llama-server. No frontend modification was required to expose that existing path.

## Source changes

strata_control/models.py removes the unsupported assumption that dense qwen35/Prism descriptors mean native Qwen Q2_0. PQ2_0 or PTQ1_0 tensor metadata now clears native candidates, including misleading known filenames, and reports local_runtime=PrismML plus a local-backend instruction.

tools/strata_mcp.py rejects native preparation of a selected Prism GGUF folder before hardware checks, downloads or pack preparation. This protects against an old screen resubmitting the previous candidate. Empty acquisition folders retain existing behavior. The normal model-table bootstrap remains first so a standalone MCP process can import Control modules without depending on its caller's working directory.

tests/terminal/test_models.py adds real small GGUF fixtures and regression checks for PQ2_0/PTQ1_0, Hikari and misleading Flash-Q2_0 names, unsupported dense qwen35, unchanged input bytes, and stale native preparation rejection.

No C++, frontend, dependency or release files were changed by this fix. Pre-existing Cargo/GDN experiments and their untracked evidence remain untouched.

## Installed hotfix and rollback

Before replacement, both installed Python files matched repository HEAD after line-ending normalization. Backups were retained:
- C:\Users\downl\AppData\Local\Programs\Strata\control\strata_control\models.py.bak-hikari-20261102-053108
- C:\Users\downl\AppData\Local\Programs\Strata\control\tools\strata_mcp.py.bak-hikari-20261102-053108

Only these two Control modules were copied from the working tree. Final SHA-256:
- models.py: 23178027940215F6686D198E14F45C95DE9E37E2BD94E797D71053657D440F91
- strata_mcp.py: 69A229D9F4E67ACF5D027F42E76183901947793ED1741A5138D496C8F3167302

Before each helper restart, the native API reported no running install, active job or native instance. Exact Python executable, parent host PID 46352 and strata_mcp.py command were checked. Only idle helpers 38136 and then 38656 were stopped so the host could reconnect to the changed code. The app host, Hermes app and inference processes were not stopped by these helper resets.

To roll back the installed code, close Strata, restore the two backup files over their corresponding .py files, then reopen Strata. This restores the defective native-import behavior as well. The earlier state.json backup remains available for the separate runtime settings recovery. This is a local hotfix; no installer was rebuilt, version bumped, commit created or publication performed. A future installer can overwrite these local module changes.

## Verification

Passed: final targeted run, using the bundled Python through uv run --no-project, of tests.terminal.test_models, tests.terminal.test_own_files, tests.terminal.test_discovery, and tools.test_strata_mcp.MacCatalog.test_the_install_plan_on_a_mac_has_no_card_kv_or_ram_options. Ran 68 tests in 10.016 seconds: OK, skipped=5.

A prior broader run of those first three suites plus tools.test_strata_mcp ran 119 tests. It found one empty-folder regression introduced during this fix, which was corrected and passed in the final targeted run. It also found an unrelated Mac DeepSeek catalogue assertion that expects two IST-DAS options but observes additional UD-IQ1 options. Running that single test against the unmodified HEAD version of tools/strata_mcp.py loaded in memory reproduced the same failure. The full broader suite is not claimed green and was not repeated after the targeted correction. Existing ResourceWarning about an unclosed scandir iterator at models.py:620 remains outside this change.

Passed: isolated Python -I / runpy standalone MCP check, starting without the repository on sys.path, using the actual Hikari folder. The final guard returned the PrismML message before the mocked hardware routine was reached.

Passed: installed POST /api/native/local/preview returned candidate_selection=null, local_runtime=PrismML and the unsupported-native-variant issue. Installed POST /api/native/plan with stale qwen/Q2_0 plus the Hikari folder returned the intended PrismML error without starting preparation. The final installed guard was checked again after the standalone-bootstrap correction.

Passed: POST /api/models/local-e7d83e78598be18b75bf0498/load loaded the existing file and POST /v1/chat/completions returned exactly 42 for What is 17 + 25? Reply with only the result. The first follow-up request finished in 4.65 seconds, with 3,395 prompt and 29 completion tokens. This is a smoke check, not a benchmark.

The running configuration changed during observation; those settings were not overwritten. Final observed state: model local-e7d83e78598be18b75bf0498, requested backend Automatic, actual executable C:\Users\downl\AppData\Local\Strata\components\generic-gguf\prism-b10826-c9c34bc\llama-server.exe, PID 37448, actual process -c 65536, running=true, error=null. A new smoke request against this final runtime also returned 42 with finish_reason=stop, 3,395 prompt and 28 completion tokens. An earlier process had -c 131072 while the host advertised 65536; neither observation is a long-context qualification.

The source GGUF remains at C:\Users\downl\Desktop\SO8T\gguf_models\zapabobouj\Hikari-Bonsai-27B-Nimble-LoRA-GGUF\Hikari-LoRA-fixed-scale-PQ2_0.gguf, 7,206,168,928 bytes, LastWriteTimeUtc 2026-10-21T13:02:53.8142805Z. No model download, copy, move or deletion was performed for this fix. Final disk snapshot: C: 30.12 GiB free, H: 157.15 GiB free.

Passed: git diff --check, with line-ending notices only.

## Limits and self-review

Interactive screen verification was attempted using the computer-use skill and cua_repl. Native access failed because codex app-server could not be launched (Windows error 3: path not found). This was not bypassed with another UI driver. UI behavior is supported by source inspection plus installed API results, not a completed visual interaction test.

Historical failed jobs were retained. Full-file GGUF hashing, long-context recall, general response quality, throughput, Hakua memory and other backend builds were not performed. No formal MILSPEC qualification is claimed.

Applied previously read PC/project AGENTS, canonical prompt, debugging-and-error-recovery, milspec-codex-standard, codex-session-style-and-standards, agent-self-review-evolution, computer-use and relevant engineering SOPs. Tool/runtime facts and higher-priority instructions govern contradictory imported prompt claims.

Self-review-event: type=qa_defect scope=local-model-import category=correctness. The earlier recovery verified an API path while leaving the user-facing import classifier incorrect. This fix repairs the classifier and independently guards stale preparation requests. Decision: review-only; no AGENTS, skill, SOP or memory modification.
