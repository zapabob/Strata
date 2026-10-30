# Hakua Windows release qualification

GUI/Product: **0.3.3-preview.20261030.1**. Native engine/Control: **0.3.3**. Hakua-memory: **0.3.5**.

This Windows preview integrates upstream 0.2.8 at `870aedd9e1ebe1c91f94da93b59af17729f6c5c0`, the release's fixed upstream source cut. Implementation commit: `767b92fdc24aaacda58812aef2fe87869109a308`; native source was merged in `6b1139108b62e08174286357bacb57d7525b564f`. Local package qualification and downloaded-release verification are complete. [Published release](https://github.com/zapabob/Strata/releases/tag/v0.3.3-preview.20261030.1), source tag `336f074b772197ce9ec249b9586c0dab9269c369`, published 2026-10-30 02:12:17 UTC. The release is the fork's latest release; its title and these instructions identify it as an unsigned preview. [Installation instructions](HAKUA_INSTALL.md).

## What changed

The previous published installer had GUI 0.3.2-preview.20261029.2 and Control 0.3.1. Its engine-bundle contained two placeholder files without an engine executable. Build and bundle hooks now reject stale GUI assets, stale Control source, missing Hakua tools, changed native source/build identity, wrong component versions and changed DLL payloads. They also check the Harness revision, official Node executable and licence, approved public artwork, and third-party notices. The installer carries the newly built CUDA engine and separate PrismML and TurboQuant runtimes.

Managed readiness now selects an accepted operator credential instead of a restricted memory principal. The restricted principal still cannot read shared telemetry. Windows stale-runtime recovery now retries only sharing/lock violations for at most one second; other permission errors still propagate. Qwen4exp Swift discovery accepts supported IQ quantization names when no layout metadata is available, while unsupported variants remain blocked.

## Current source tests

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

## Real inference and memory

The Windows test machine has an RTX 5060 Ti, driver 621.01, Ryzen 5 4500 and 32 GiB RAM. Native memory tests use Qwen3.8-Flash-Next Q2_0, a 4,096-token context, one request slot, file-backed experts and a fictional temporary profile.

The current native executable reports 0.3.3; SHA-256: `a1bf844ce33ae68990d606fe31c2a9faa9da2dc0f3a24b10627f32eefea44403`. Current Host/Control/native r4 passed two loads, exact arithmetic response 4, memory-page consent controls, restricted telemetry HTTP403, a real SQLite memory write, full unload, a fresh-process recall of Cerulean and unchanged DB bytes for the read-only request. The monitor confirmed the first engine was absent before the second was created, and all 95 recorded owned process identities were absent after cleanup. Both cuBLAS 13 DLLs came from the engine's own package under System32-only PATH.

During concurrent build/test load, readiness took 596,809 ms and 515,688 ms, and the recall request took approximately 230 seconds. These are successful but slow runs, not a claim of interactive-speed startup. The earlier r3 diagnostic's second load exceeded its six-minute driver limit. R4 changed only that diagnostic limit to fifteen minutes and tracked loading instances for cleanup; source, payload and assertions were unchanged. The earlier pre-0.2.8 binary is not used as evidence for this result.

PrismML PQ2_0 passed two fresh-process load, arithmetic, streaming, stop and restart rounds using Hikari-LoRA-fixed-scale-PQ2_0.gguf. TurboQuant K=FP16 with V=turbo2, turbo3 and turbo4 each passed two strict arithmetic, named-greeting, stream, stop and restart rounds using Qwen3-0.6B-Q8_0. K=q8_0 with V=turbo3 also passed. These runtime payloads are unchanged by the upstream integration.

TurboQuant K modes produced corrupted responses and are excluded from the packaged capabilities. The earlier symmetric TURBO4 diagnostic accepted a numeral inside a degraded response and is superseded by strict checks. PrismML PQ2_0 and TurboQuant are separate executables; PQ2_0 with TurboQuant cache quantization in one process is not offered. Their chat paths do not share the native Hakua memory sidebar. [Backend details](LOCAL_LLAMA_BACKENDS.md).

These checks do not establish general model quality, a speed improvement, multiuser isolation, long-context performance or every optional engine feature. Loading and prefill can take minutes on this PC.

## Package integrity

The package uses official Node 24.22.2, SHA-256 `1c331340fa6cac5e4294725959070a143fa0507195a78ad77eed7943f719aac9`. The reviewed Hakua wheel is selected by exact URI and hash, with hashed dependency installation at build time. App startup does not install Python packages or compile code. Windows credential files use a protected owner-only DACL. The public UI uses approved pinned Lucide assets, an owned MIT icon and system fonts.

There are 94 inventoried third-party notice files. The unchanged upstream 483,520-byte control vector is included, off by default, with its full Qwen Community License 1.0. [Provenance](../data/experimental-speed-projection/PROVENANCE.json) pins its source and licence bytes. Vector SHA-256: `ef0724c5b79297e481017be85769832bc26eb220c984ecba2b0e1b0c8426312b`. The guard permits exactly this declared GGUF and rejects other GGUFs or live profile data in Control. Complete inference model weight packs, personal memories and user keys are not distributed.

## Installer and publication

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

## Test cleanup incident

A preexisting planning test recursively removed part of the real H-drive Strata build/dependency area. That cleanup was removed. Node tests now use a dedicated scratch tree with recursive-cleanup guards, including parent-junction escapes. Known pinned sources and the reviewed experimental Prism patch were reconstructed; both preexisting worktrees had no tracked deletions. Current release inputs were rebuilt or rehashed independently. Complete recovery of every old untracked byte or build output is not established. The correction and limits remain in the [implementation record](../_docs/2026-10-30_hakua-release-integrity_Codex.md).
