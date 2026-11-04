# Hakua Windows release qualification

## Current product: 0.4.0-preview.20261103.7

Product tag: **0.4.0-preview.20261103.7**. Use the explicit release page, not GitHub `/releases/latest`.

- Release URL: [v0.4.0-preview.20261103.7](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261103.7). Published with `gh release create --latest=false`. GitHub’s latest pointer stays [v0.4.0-preview.20261101.1](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261101.1).
- App assets on this tag: setup EXE and `SHA256SUMS.txt` only (no matching 7z). Setup EXE SHA-256 `5e8b8fff82b6e63dea48bf5c1907950911700c9bf30673444e5d2489a87c0336`, 113064953 bytes. The installer has no Windows code signature.
- Local silent install: a bare empty tree can return NSIS exit 2. Known fix: create the install folder and empty managed dirs (`control`, `host`, `node`, `harness`, `engine-bundle`, `local-backends`, `notices`), then run **one** `/S` (do not wipe/`rmdir` a live tree while setup runs). After repair, DisplayVersion `0.4.0-preview.20261103.7`; ProductVersion on `strata-desktop.exe` matches `.7` (SHA-256 `58426441dcd64fddcbca565d64f59841cbedcb8c972c8dd7b44d294071010b4a`). Recorded InstallLocation on this machine: `H:\Programs\Strata-0.4.0-preview.20261103.7` (restored from the manufacturer install key; do not delete that folder during ship). Concurrent setup/`rmdir` races left a leftover empty `%LOCALAPPDATA%\Programs\Strata` tree; leave it alone rather than wiping.
- Private Node may need a one-shot copy from the NSIS cargo `release\node` staging if a raced `/S` left `node\` empty; that is a copy into the install, not a folder wipe.
- Unsigned Qwen3.6 side-by-side component: `0.4.0-q36-windows-x86_64-cuda-cuda13` (no picture reader; `signature` is null). Hotspot-profile `strata.exe` SHA-256 `907341c74d5a9f26c784e4aaad3460e376d4cabd84635c5d032879c59b08d150`. Bundle `native-build.json` SHA-256 `cd235fdf812d43c45e0a0881073bee97483c5aa50c65bbefb877bd1e8e8dbd8b` (metadata entry, not the engine entrypoint). This is not a signed package.
- Mapped-pack stays off unless the launch asks for it. Allowed resolved `strata.exe` digests: `907341c74d5a9f26c784e4aaad3460e376d4cabd84635c5d032879c59b08d150` (hotspot-profile opt-in rebuild; T07 capture PASS), `64226fde7905821148c78b7de85ede4d291c4df8184d80866dccba014d7c02b7` (help-honesty rebuild; mapped-live READY + T03 PASS + T04 observational pair recorded), `6fe110650940d0c19f09909d769393769650045e6bc6eab29ccc49734dbcab29` (pin-pool wire), `dd53df07789e0fefcb87e33acab54f5bfe1faf312ef6bad515924736b715c5b5`, and the older `512d7f8bba66b57fbe0f8b90807825d3b3172a86dd039452bc29e685ca27d046`. Older digests stay allowed. A digest in model settings does not unlock the flag.
- Signed CUDA component digest `b5e4d5255a48882334b27ab643c22c9c1b54e4580f82b402176a9ca5661bf6f1` on **v0.4.0-preview.20261101.1** was not overwritten. PrismML and TurboQuant stay in that signed component.
- Defaults recorded for this line: legacy host arena; context 65536; FP32 KV; MTP 2; prefill auto.
- T04 adoption is KEEP_DEFAULT (bounded policy NOT_RUN). T06 scheduler still BLOCKED. T07 hotspot **profile** captured (`STRATA_Q36_HOTSPOT_PROFILE`; dominant host bucket gdn); kernel opt-in NOT_RUN. T08 refuse PASS / measured FP16 NOT_RUN. Startup time and token speed claims are not made beyond recorded observational notes. The CUDA spill guard did not pass the reviewed baseline.

Install steps: [HAKUA_INSTALL.md](HAKUA_INSTALL.md). The detailed measured publication below for **0.4.0-preview.20261101.1** is not a measurement of this 20261103.7 app build.

## Historical measured record: 0.4.0-preview.20261101.1

GUI/Product recorded in this section: **0.4.0-preview.20261101.1**, native engine/Control **0.4.0**, Hakua-memory **0.3.5**. Integrated upstream 0.2.9 is frozen at `c62d5e3a15b40ea51c96aae9e8d36928965f53ab`. Local package checks are complete. Public release and anonymous download verification are complete; see the publication record in this section. Keep product `.6` and signed-component `.1` identities apart. An unsigned package is never a signed one.

### Distribution and installation (.20261101.1)

Use the [fork release](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261101.1) for the signed CUDA / feed assets from this publication, and [HAKUA_INSTALL.md](HAKUA_INSTALL.md) for the current app installer on `.6`. Following the official Windows architecture, the app contains GUI/Host, private Node 24.22.2, CPython 3.12.15/Control, Hakua-memory and Harness. GPU runtimes are a separate signed component, downloaded explicitly from the preparation screen or imported from a file. Native CUDA, PrismML/PQ2_0 and TurboQuant are included in that component. Full model weights are separate. System Node/Python, pip and a compiler are unnecessary.

This Windows EXE is code-unsigned and uses manual app updates. Feed/component Ed25519 signatures and file checks do not constitute Windows executable signing. The own-fork default feed preserves explicit alternate feeds, uses flat GitHub asset URLs and a matching ZIP Control/bootstrap manifest. It has engine/Control entries and no automatic app-update entry.

### Final measured checks (.20261101.1)

The complete Terminal/Control and Hakua-memory run covered 2123 passed tests, 73 conditional skips and 367 passed subtests. The first complete run retained two environmental failures when the legacy Windows installer correctly refused C: below its unchanged six-GiB reserve. Its entire installer module then passed 17 tests using the existing H-drive fixture. Test sources and reserves were unchanged. The complete Host/UI suite passed 1320, with 31 conditional skips and zero failures, from the SSD source checkout using the actual installed private Node and Harness, concurrency 1 and original timeouts. Earlier interrupted H-drive runs and their failures remain recorded; they are not counted as passes.

The final EXE's 29292-file managed inventory and the actual installed 29286-file inventory match the intended source/resources, excluding generated CPython bytecode. The extracted production shell passed all 13 self-tests with System32-only PATH and the actual user's conflicting Node CA settings. The direct app update preserved all four complete data SHA256 inventories (3724 files), the selected signed engine and tray=true. The 7z passed integrity, exact three-file membership, re-extraction and installer-hash checks. Normal installed startup passed with the user's NODE_OPTIONS and NODE_USE_SYSTEM_CA retained; global settings were unchanged. The old October 27 cancelling operation recovered to cancelled and no active engine jobs remained.

Two normal-user failures were reproduced and corrected before publication. User-level OpenSSL CA options combined with NODE_USE_SYSTEM_CA=1 made Node exit 9 before Host readiness. The shell now removes only the conflicting system-CA variable from the child environment when OpenSSL was explicitly selected; it preserves certificate verification, other Node options, extra CA certificates and global settings. Desktop Rust tests pass 31, including five CA cases and the exit-9 diagnostic. A persisted cancelling load previously blocked every new operation after restart. Startup recovery now settles it as cancelled; all three cancellation regression tests pass, including the recorded failing pre-fix case. Personal job records were not manually edited.

Native engine SHA256 `b5e4d5255a48882334b27ab643c22c9c1b54e4580f82b402176a9ca5661bf6f1` is unchanged. Complete CTest passed 221 with eight conditional skips, 229 registered. The reviewed 433-entry CUDA13.3/sm120 source/compiler guard and 24 generic/optimized case hashes pass with unchanged resource budgets. This exact engine passed real arithmetic, authenticated independent memory consent, synthetic save, unload/reload, recall and unchanged read-only DB bytes: context4096, 512 expert-cache slots, prefill32, spec2, no MTP, unchanged 300s chat limit. Free dedicated VRAM was14836MiB before loading,9433MiB after first load and9796MiB after reload. Both native ports closed and Host exited0.

PrismML Hikari PQ2_0 (Q8_0 K/V, Quarter GPU) and TurboQuant Qwen3-1.7B-Q8_0 (FP16 K/Turbo3 V) passed actual memory save, full Host/model restart and recall at4096 context. Both checked per-turn independent consent, authentication, unchanged read-only DB and owned-process cleanup. Ordinary TurboQuant GUI chat passed at8192 context, including correct answers, Stop117ms, resend and four viewport sizes. These exact executable hashes match the signed component and installed selection. Earlier browser UI evidence and physical WebView2 rendering/tray/quit confirmation are separate from shell self-tests. The user also confirmed that the final installed shell rendered correctly and the previous engine-operation error was absent; native GUI automation was unavailable.

Earlier supplementary runs passed setup975 with two skips/359 subtests, server1349 registered with30 skips/no failures, desktop39 with five skips/eight subtests and six actual NSIS cleanup/locked/link/uninstall/data-preservation scenarios. These earlier results were not rerun after the final startup fixes; fresh Rust and Host results are identified separately. The approved Hermes GPU loan was restored with health, model/context and synthetic-response evidence. Its later CPU backend automatically replaced itself at port56271; current HTTP200 and the existing model server8080 were checked, and the redundant restore guard was stopped to prevent a duplicate backend.

### Package identities (.20261101.1)

Current public app installer (rebuild uploaded 2026-11-02): workspace `8870f25309ca7142a44b0042b1d16f337e4487af` (Hikari Strata-engine load / agent / 16GB hybrid VRAM tooling). Embedded Control source remains `a684b50d5c149718fdc538d71c97c8389760347d`. Signed engine/Control/feed assets are unchanged from the 2026-11-01 publication. Installed NSIS-patched shell SHA256: `a52b2eff958eed250f43bb7fe5a21b384ff792da59e5010aaa185033e8d60f4c`. Personal memories, keys and full inference model weights are excluded. The licensed small experimental control vector remains off by default.

Earlier first-publication identities (superseded for the three app assets below, retained for audit): app source `be0960a0707ab2e7fc1a90d5a7888ffd149c9858`; native source `4a6a54141ff6adabf64a16117b5ee0f8a80aff93`; shell SHA256 `ee0621a49e38aae3f3b40584a2c2fd77f1636c2f892d3e9f64751dbebff70284`; GUI receipt SHA256 `11433b751da7e7310ef6005c241323e7f7b374d8b9101995195b6fb07270d6be`.

| Asset | Bytes | SHA256 |
| --- | ---: | --- |
| `Hakua-Strata-0.4.0-preview.20261101.1-windows-x64-sm120.7z` | 113749050 | `7d02e384a502600b0e2b2143cbb73ebc8c71893af8a2fd8532b74ad823bb6fbe` |
| `SHA256SUMS.txt` | 720 | `411ab24fd7579daca3a1f73d240de65718399b1de3511b5f416988a32e7c73f6` |
| `Strata_0.4.0-preview.20261101.1_x64-setup.exe` | 113758075 | `9682b59774fa1b552d9ba09c7d0baed0028f0b7b104cfeec4c9b0a3d7eda2a26` |
| `install-manifest.txt` | 135 | `91bb97a42fce7b463dfdf28298ab5f66583b4ecee845c93ed23f29fd41d49b9d` |
| `strata-control-0.4.0-windows-x86_64.zip` | 73041197 | `2f550ea2e0a5b5693b7f42b642538dd545e46e5da94ddd4666fdd4261c4f7c6f` |
| `strata-engine-0.4.0-windows-x86_64-cuda-cuda13.tar.gz` | 1418256311 | `3972253734ce936527d75c6048bad7b7bffbcefad32085cdca6143d367ba0e84` |
| `strata-feed.json` | 1381 | `98d6a3c7b01cc0dc1dc9acb062539bac794348221200ef6e5254289ab1f3331e` |
| `strata-feed.json.sig` | 151 | `d51204e14739662b7ab2791748c3ed761d268248ebc41c3c9f5f01f57d684603` |

### Published download verification (.20261101.1)

First published 2026-11-01T19:36:42Z, release ID430808779, source tag `v0.4.0-preview.20261101.1` at `a35bb92c8fb3f53ff75ebccf1fa457519d6e0b77`. All eight public assets were downloaded without authentication and matched the then-qualified local size, SHA256 and GitHub asset digest. The latest-release pointer, latest/download feed, Ed25519 feed signature, sequence20261101160145 and flat engine/Control package URLs passed at 2026-11-01T19:39:33.566443+00:00. That latest pointer still points here after later `--latest=false` preview tags.

Installer rebuild upload 2026-11-02T09:51Z (JST 18:51): replaced only `Strata_0.4.0-preview.20261101.1_x64-setup.exe`, `Hakua-Strata-0.4.0-preview.20261101.1-windows-x64-sm120.7z` and `SHA256SUMS.txt` on the same tag via `gh release upload --clobber`. Signed engine/Control/feed/install-manifest digests were left unchanged. Anonymous curl downloads of the three replaced assets matched the staged SHA256 and GitHub digests at 2026-11-02T09:58:59Z. Local gates for this rebuild: CUDA engine rebuild + `verify-release` + NSIS `NSIS_BUILD_EXIT=0` + `/S /UPDATE` DisplayVersion `0.4.0-preview.20261101.1` + smoke `strata-desktop` start. Full Host/Python suite and 13 production-shell self-tests were not re-run for this upload; earlier 2026-11-01 suite evidence remains that of the first publication payload.

### Limits and retained failures (.20261101.1)

Windows x64/CUDA sm_120 preview, measured on RTX5060Ti. Native text is included; native image input and the separate native DeepSeek engine are absent. Other GPUs/platforms,131k context and simultaneous large-model coexistence require separate checks. Earlier89MiB VRAM refusals and memory timeouts remain recorded. TurboQuant K modes produced corrupted real answers and remain disabled; use K=FP16 and V=TURBO2/3/4. PQ2_0 and TurboQuant are separate executables. Qwen3-0.6B/Turbo3 did not produce a useful memory summary and is not memory-qualified; the1.7B combination passed.

GitHub CI is NOT_RUN. Real workflow dispatches returned HTTP422, Actions disabled, including the exact a684b50d source dispatch. Repository settings were not changed and no remote pass is inferred. Older all-in-one and split installers, including the f91df6ce candidate that failed normal-user startup, were superseded before publication. Their retained measurements do not identify this release. See the [engineering journal](../_docs/2026-11-01_hakua-official-distribution_Codex.md).

## Historical measured record: 0.3.3-preview.20261030.1

The following sections preserve the earlier package's evidence. Their installer hashes, test counts and GUI observations apply to 0.3.3 only. They are not measurements of 0.4.0-preview.20261103.7, 0.4.0-preview.20261103.7 or 0.4.0-preview.20261101.1.

GUI/Product: **0.3.3-preview.20261030.1**. Native engine/Control: **0.3.3**. Hakua-memory: **0.3.5**.

This Windows preview integrates upstream 0.2.8 at `870aedd9e1ebe1c91f94da93b59af17729f6c5c0`, the release's fixed upstream source cut. Implementation commit: `767b92fdc24aaacda58812aef2fe87869109a308`; native source was merged in `6b1139108b62e08174286357bacb57d7525b564f`. Local package qualification and downloaded-release verification are complete. [Published release](https://github.com/zapabob/Strata/releases/tag/v0.3.3-preview.20261030.1), source tag `336f074b772197ce9ec249b9586c0dab9269c369`, published 2026-10-30 02:12:17 UTC. At that publication it was the fork's latest release; its title and these instructions identify it as an unsigned preview. [Installation instructions](HAKUA_INSTALL.md).

### What changed (0.3.3)

The previous published installer had GUI 0.3.2-preview.20261029.2 and Control 0.3.1. Its engine-bundle contained two placeholder files without an engine executable. Build and bundle hooks now reject stale GUI assets, stale Control source, missing Hakua tools, changed native source/build identity, wrong component versions and changed DLL payloads. They also check the Harness revision, official Node executable and licence, approved public artwork, and third-party notices. The installer carries the newly built CUDA engine and separate PrismML and TurboQuant runtimes.

Managed readiness now selects an accepted operator credential instead of a restricted memory principal. The restricted principal still cannot read shared telemetry. Windows stale-runtime recovery now retries only sharing/lock violations for at most one second; other permission errors still propagate. Qwen4exp Swift discovery accepts supported IQ quantization names when no layout metadata is available, while unsupported variants remain blocked.

### Current source tests (0.3.3)

| Suite | Recorded result |
| --- | --- |
| Host r13, real staged Harness enabled | 1,297 passed; zero failed; 30 conditional skips; 1,327 tests. |
| Python full r20: Terminal, Hakua, models and setup | 2,994 passed; zero failed; 76 conditional skips; 716 passing subtests; 2,483.50 s. |
| Focused stale-state recovery and model discovery | 49 passed; zero failed. |
| Server r3 | 1,265 passed; zero failed; 28 skips; 1,293 registered tests. |
| Rust unit tests, unchanged Rust implementation | 25 passed; zero failed. Final packaged self-test: 13 of 13 passed. |
| Native CTest r5 | 219 passed; zero failed; eight conditional skips; 227 registered tests. |
| Public packaging/data/native integrity cases | 13 passed; zero failed. |
| Fault injection r12 | Eight mutations detected after successful baselines. |
| Public UI r6, TypeScript r3, release guard r8 | Passed. |
| Remote GitHub CI | Not run. Workflow dispatch returned HTTP 422: Actions is disabled for this repository. |

The native skips are qsa_slots_parity, iq_parity_fixtures, iq_parity, prefill_fused_iq_test_ws, expert_multi_test, native_hadamard_test, tq_cpu_parity and tq_cpu_parity_avx2. These require their optional fixtures or dependencies and are not counted as passes. The Windows ISA gate passed in the complete r5 run, checking all 121 wide functions.

Independent CPU GGML/F32 PLE captures passed the unchanged CUDA tolerances, with worst relative stage error 1.713e-3. The source/compiler/ggml-bound resource budget passed: all 432 nonzero stack/local entries matched the earlier measured values, with no added, removed or increased entries. The general allowance table is unchanged.

Python r18 found a Windows sharing-lock failure and a Swift-name discovery failure. Both were corrected before the focused green run and r20. Native r4 was invoked without the required PLE fixture path; the targeted rerun and complete r5 passed with the explicit verified fixture. Failed diagnostics and interrupted runs remain in the implementation record and are not counted as successful qualifications.

### Real inference and memory (0.3.3)

The Windows test machine has an RTX 5060 Ti, driver 621.01, Ryzen 5 4500 and 32 GiB RAM. Native memory tests use Qwen3.8-Flash-Next Q2_0, a 4,096-token context, one request slot, file-backed experts and a fictional temporary profile.

The current native executable reports 0.3.3; SHA-256: `a1bf844ce33ae68990d606fe31c2a9faa9da2dc0f3a24b10627f32eefea44403`. Current Host/Control/native r4 passed two loads, exact arithmetic response 4, memory-page consent controls, restricted telemetry HTTP403, a real SQLite memory write, full unload, a fresh-process recall of Cerulean and unchanged DB bytes for the read-only request. The monitor confirmed the first engine was absent before the second was created, and all 95 recorded owned process identities were absent after cleanup. Both cuBLAS 13 DLLs came from the engine's own package under System32-only PATH.

During concurrent build/test load, readiness took 596,809 ms and 515,688 ms, and the recall request took approximately 230 seconds. These are successful but slow runs, not a claim of interactive-speed startup. The earlier r3 diagnostic's second load exceeded its six-minute driver limit. R4 changed only that diagnostic limit to fifteen minutes and tracked loading instances for cleanup; source, payload and assertions were unchanged. The earlier pre-0.2.8 binary is not used as evidence for this result.

PrismML PQ2_0 passed two fresh-process load, arithmetic, streaming, stop and restart rounds using Hikari-LoRA-fixed-scale-PQ2_0.gguf. TurboQuant K=FP16 with V=turbo2, turbo3 and turbo4 each passed two strict arithmetic, named-greeting, stream, stop and restart rounds using Qwen3-0.6B-Q8_0. K=q8_0 with V=turbo3 also passed. These runtime payloads are unchanged by the upstream integration.

TurboQuant K modes produced corrupted responses and are excluded from the packaged capabilities. The earlier symmetric TURBO4 diagnostic accepted a numeral inside a degraded response and is superseded by strict checks. PrismML PQ2_0 and TurboQuant are separate executables; PQ2_0 with TurboQuant cache quantization in one process is not offered. Their chat paths do not share the native Hakua memory sidebar. [Backend details](LOCAL_LLAMA_BACKENDS.md).

These checks do not establish general model quality, a speed improvement, multiuser isolation, long-context performance or every optional engine feature. Loading and prefill can take minutes on this PC.

### Package integrity (0.3.3)

The package uses official Node 24.22.2, SHA-256 `1c331340fa6cac5e4294725959070a143fa0507195a78ad77eed7943f719aac9`. The reviewed Hakua wheel is selected by exact URI and hash, with hashed dependency installation at build time. App startup does not install Python packages or compile code. Windows credential files use a protected owner-only DACL. The public UI uses approved pinned Lucide assets, an owned MIT icon and system fonts.

There are 94 inventoried third-party notice files. The unchanged upstream 483,520-byte control vector is included, off by default, with its full Qwen Community License 1.0. [Provenance](../data/experimental-speed-projection/PROVENANCE.json) pins its source and licence bytes. Vector SHA-256: `ef0724c5b79297e481017be85769832bc26eb220c984ecba2b0e1b0c8426312b`. The guard permits exactly this declared GGUF and rejects other GGUFs or live profile data in Control. Complete inference model weight packs, personal memories and user keys are not distributed.

### Installer and publication (0.3.3)

R6 completed a fresh full Tauri compilation. Its first bundle guard stopped on a transient Prism execution/source probe failure; the unchanged executable and unchanged probe then passed. R7 repeated the complete bundle guard and produced NSIS from that fresh shell. R8 qualification passed extracted-source/payload comparison of 29,324 application files and all 13 packaged self-tests under System32-only PATH. An independent normal-window extraction had a responsive Strata window; its PE product version and API both reported 0.3.3-preview.20261030.1, and Control reported engine 0.3.3. All 15 recorded owned window/child process identities were absent after cleanup. The build-wait helper's earlier 30-minute orchestration limit and the successful repeat are retained in the implementation record.

The outer 7z passed its integrity test and actual re-extraction. It contains exactly the installer, INSTALL.md and an inner installer checksum. The re-extracted installer bytes match the standalone EXE.

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| Strata_0.3.3-preview.20261030.1_x64-setup.exe | 799,979,767 | `478743a7cbbe633d09101102f2df4be7d4d254bf4119a251ab19c7f1fd4a3533` |
| Hakua-Strata-0.3.3-preview.20261030.1-windows-x64-sm120.7z | 793,967,757 | `0958e9d748a0772cfaaa70b64dfcb9470524dea8c36f18f309827e8c80588373` |

All three uploaded assets were downloaded again into a fresh directory. Their bytes match the local EXE/7z/checksum files and GitHub's SHA-256 digests. Publishing preserved the same asset IDs and digests. Release ID: `428581199`; EXE asset `690609303`; 7z asset `690609304`; checksum asset `690609312`. SHA256SUMS.txt is 239 bytes, SHA-256 `c52aaeba06c54bd811ca8e26077aa54ed4136e3fd250eeadf1c700f3fa204df9`.

The release source tag is fixed at the documentation/qualification commit above. Its production runtime is implementation `767b92fd`; later commits containing only publication receipts do not change that runtime. Remote CI is unrun because the repository rejects dispatch with Actions disabled; the suite results in this document are local results. The repository policy was not changed. Earlier R5 diagnostic installer/7z artifacts are excluded from publication.

The deliverables are `Strata_0.3.3-preview.20261030.1_x64-setup.exe`, `Hakua-Strata-0.3.3-preview.20261030.1-windows-x64-sm120.7z` and `SHA256SUMS.txt`. The 7z contains the same installer and instructions; it is not a portable app.

The current normal window and API passed the observations above. CUA could not start its native app-server, and its in-app browser provider was unavailable. Visual interaction and clicks are not recorded as passed. Upgrade through the user's real uninstall registration has not been run. The existing installed copy has not been replaced during scratch tests.

This is an unsigned manual-update preview. An owned signed automatic-update feed/key is not qualified. Windows x64/CUDA sm_120 on the stated hardware is the runtime qualification scope. HIP, SYCL, Linux, other GPUs and Metal require separate evidence; Metal's source version is not a tested Metal artifact.

### Test cleanup incident (0.3.3)

A preexisting planning test recursively removed part of the real H-drive Strata build/dependency area. That cleanup was removed. Node tests now use a dedicated scratch tree with recursive-cleanup guards, including parent-junction escapes. Known pinned sources and the reviewed experimental Prism patch were reconstructed; both preexisting worktrees had no tracked deletions. Current release inputs were rebuilt or rehashed independently. Complete recovery of every old untracked byte or build output is not established. The correction and limits remain in the [implementation record](../_docs/2026-10-30_hakua-release-integrity_Codex.md).
