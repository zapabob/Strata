# Strata v0.2.23 intake for Hakua

The isolated worktree `H:/Strata/worktrees/hakua-v023-upstream-codex` uses branch `codex/hakua-upstream-0.2.23`. The fork parent is `7ccaa9e793fe81b6b6df57c7703a13c74202b55d`. The official release tag resolves to `4560d03793482ef367294cfbd86a4df8d5679e72`.

The prior Hakua release used a curated v0.2.22 intake. This merge uses v0.2.22 `b28ca95e3e6847f2d5e317994f253b66716deeaa` as the semantic comparison point for the 329 paths in the official release delta. The fork and the v0.2.23 commit are the Git parents. The shared main worktree and index were outside this intake.

The resulting branch includes the 16 KiB SQv2 reader, native Inkling local model import with custom build IDs, the existing GGUF fallback, the DFlash2 path, and the updated server launch settings. The Windows CUDA build keeps the Hakua Expert scratch path. Custom model inventory and chat labels use the app's existing serving state and model IDs.

The DeepSeek engine, adapter, separate package feed, fit logic, and profile names remain available. The v0.2.17 fork intake at `8a3e986614096b6d13e9fe270e7006407666b508` supplied the coherent DS4 setup implementation. The intervening fork setup function contained Inkling logic in its DS4 body. The Harness profile combines the existing blocked-folder settings and model names with the existing provider and browser options in a single gate and a single preset.

The npm, Cargo, and Windows Python locks retain Hakua's versions. The registry comparison in `H:/Strata/evidence/hakua-v023-upstream-codex/dependency-osv.json` records five official host Vite advisories that do not match the pinned Hakua version. Six advisories match the retained Rust lock and twelve match the official lock. Some are maintenance or platform-specific notices. The audit includes the dependency sets of both parent versions.

## Verification

The Windows CUDA 13.5 build produced `strata-inkling.exe`. Its reader layout CTest passed. The built binary inspected the complete CHiPS file. The CLI produced a 4,096-token plan with a separate custom identity, no weight download, and drafting and vision disabled. App host TypeScript typechecking passed. The focused app host suite returned 43 passed and one skipped. The test logs are under `H:/Strata/evidence/hakua-v023-upstream-codex`.

The installed Harness 0.2.1-alpha.3 was exercised with scripted worker replies and temporary session data. Tool execution after approval, denial, Stop with and without an approval pending, resume without tool replay, concurrent session isolation, and live blocked folders all passed. The separate reasoning/text/usage streaming case failed in the same run. See `dsh-real-lifecycle.log` for the observed results.

All 106 targeted Python cases for DS4 launch and adapter behavior, local model import, and custom activation passed. A broader interim run also covered the catalogue, argument layering, and connect clients. It recorded unresolved parallel-default, connect-client expectation, and fixture issues. See `terminal-final-tests.log` for that run and `targeted-final.log` for the final targeted result.

DS4 real-weight generation requires a local DS4 checkpoint. The existing package and model paths remain available for that qualification. The Windows CUDA build emitted compiler warnings, and the release remains locally staged for qualification.

## CHiPS and Harness follow-up

The isolated server and the v0.2.23 CUDA binary from `fcd3f3c1a01c7dc6557ae4ca65d66cdcf58dd620` loaded the complete 19,374,768,128-byte CHiPS pack and returned `4` for the arithmetic smoke test through the OpenAI-compatible chat API. The run used a single 4,096-token slot, 7 GiB each for the Expert VRAM and RAM budgets, and the exact GPU lane for cold Experts. The server took 115.22 seconds from launch through shutdown. The request generated 47 tokens at 8.4 tokens/s. The GPU was checked before launch, and the test owned only its temporary server process. See `H:/Strata/evidence/hakua-v023-upstream-codex/chips-v023-retest.json`.

The previous A01/A02 log ended before the reporter printed the exception. The case passed on a normal rerun and also passed alongside approval, Stop and resume tests. A controlled rerun used the installed Harness 0.2.1-alpha.3 with a 91-second delay before its CLI started. The old fixture's 90-second override failed with `agent-start-failed` after 90.46 seconds. The fixture now uses the same 120-second startup budget as the app. With the same startup delay, A01/A02 passed in 104.27 seconds, including the existing checks for reasoning, visible text, the terminal frame and reported usage. Startup failures record their cause, observed frame types and the number of worker requests. The production startup budget stays at 120 seconds.

The real-Harness regression run passed all 33 cases without skips. Its four suites cover the bridge and streaming, permission modes, blocked folders and model labels. App host TypeScript checking passed. The follow-up used the common engineering and implementation-start SOPs, the application's TypeScript and security SOPs, and the failing-test debugging skill. See `harness-delayed-start-before.log`, `harness-delayed-start-verified.log` and `harness-lifecycle-fixed.log` under `H:/Strata/evidence/hakua-v023-upstream-codex`.
