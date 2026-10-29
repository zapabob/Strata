# Hakua Windows release qualification

Candidate: GUI/Product `0.3.3-preview.20261030.1`, native engine/Control `0.3.3`, Hakua-memory `0.3.5`.

This candidate is not yet qualified or published. Pending README download links are proposed asset names, not proof that a release exists.

## Corrected packaging

The old staged Control did not match current source, and GUI identity could be overridden by Control's number or a fixed fallback. The engine bundle was incomplete. Product identity now prefers the GUI product version, while Control/native components use numeric engine versions. The new native and Control version sorts after the previously installed fork components.

The GUI build records hashes of its source and output assets. Before Tauri packaging, the verifier checks current Host/Control source trees, product and engine numbers, required memory tools, real Hakua imports, Harness revision/budget patch, both local-backend packages, native source/build identity and executable versions. Missing, changed or stale payloads stop packaging.

The Windows runtime is pinned to official Node 24.22.2. Its executable SHA-256 is `1c331340fa6cac5e4294725959070a143fa0507195a78ad77eed7943f719aac9`. Node 24.12.0 reproduced an uncatchable failure while deleting a Cyrillic test path; the unchanged test passes with 24.22.2. Both fetch scripts pin official archive hashes and reject unrecorded version overrides. See [Node's tracked defect](https://github.com/nodejs/node/issues/56049).

Hakua's universal wheel is selected by its exact local file URI and SHA-256. A same-version index build cannot replace it. No package installation or compilation runs at app startup. Windows credential files receive an exact protected owner-only DACL; explicit group grants left by the previous ACL implementation are removed.

## Real inference and memory evidence

| Scenario | Result |
| --- | --- |
| Current native executable | Reports Strata 0.3.3; package and native source hashes reverified. |
| PrismML PQ2_0 | Two actual cold-start/chat/stream/stop/restart rounds passed with Hikari-LoRA-fixed-scale-PQ2_0.gguf. |
| PrismML DLL origin | CUDA, cuBLAS and OpenMP libraries loaded from its own package with System32-only PATH. |
| Native ordinary chat | Actual Qwen3.8-Flash-Next Q2_0 answered 2+2. |
| Native Hakua memory | Saved fictional cerulean preference, completely stopped Python/native engine, started fresh processes and recalled the preference. |
| Read-only memory | Records remained unchanged; both server rounds exited with code 0. |
| TurboQuant | Standard-sm_120 build passed. K=FP16 with V=turbo2/turbo3/turbo4 each passed two strict arithmetic/greeting/stream/stop/restart rounds; K=q8_0,V=turbo3 also passed. Turbo K modes failed and are excluded from the candidate K capabilities. |
| Extracted GUI | Installer r2 extracts successfully. Its packaged self-test passes all 13 checks on System32-only PATH. Normal window responds and its API reports the current product version. Visual interaction and final rebuilt Control qualification remain open. |

The memory probe used a dedicated temporary profile and fixture keys. It used the real locked Hakua writer and real native engine. An earlier QA reader accidentally created SQLite WAL/SHM sidecars; the production harness correctly omitted that database. The probe was fixed to use immutable read-only inspection, and the complete fresh scenario then passed. No production privacy check was relaxed.

These results do not qualify general summary quality, multiple principals, other model families or all hardware. On this 32 GiB PC, the large native model used mmap/file-backed experts and has substantial loading/prefill delay. No general throughput improvement is claimed. The separate PrismML/TurboQuant inference routes currently do not share the native memory sidebar.

## Tests and remaining gates

The complete Host r10 run passed: 1,295 tests, 1,266 passed, zero failed and 29 conditional skips, with the real pinned Harness. This includes chat, approval/denial, stop, restart and permission modes. Six additional current public-asset/build-integrity cases passed after that run. Earlier diagnostic runs with failures or a skipped Harness are not substituted for this result.

Python full r12 recorded 2,862 passed, eight failed, 75 skipped and 704 passing subtests. Its failures led to a long-path Save-screen layout fix, a Python 3.12 HEAD-redirect fix, accurate HTTP test-server transfer counting, blocked default network acquisition in setup fixtures and a corrected missing-Hakua dependency expectation. Targeted r14 passed 294 cases with one remaining server-counting failure; the corrected download file then passed all 29 cases in r15. Full r16 and the current server suite are running; these results are not yet a full-green claim. A coarse-clock regression also verifies that throughput timing uses the high-resolution performance counter.

Native CTest r3 completed 225 registered tests: 216 passed, zero failed and nine conditional skips. Independently generated GGML/F32 PLE captures passed unchanged CUDA parity tolerances (worst relative stage error 1.713e-3). A reviewed source/compiler/ggml-bound per-entry CUDA resource budget passed; new or increased nonzero-stack entries and changed inputs fail the guard. The original general allowance table is unchanged. One skipped Windows ISA gate was subsequently run with isolated test dependencies: an MSVC object-name regression was fixed and strict inspection passed all 121 wide functions. Eight other conditional gates remain untested.

Eight targeted mutations were detected by temporary-copy checks, including removal of source membership, source hash and engine payload verification. Recheck the final fault model after source freeze. An import/syntax failure does not count as detection.

The public UI uses pinned approved Lucide assets, an owned MIT icon and system fonts. The package excludes the supplied proprietary font and unqualified installer artwork. Its build receipt binds asset membership, hashes and Node version. The package also carries Node's official license and 93 inventoried third-party notice files for its bundled GUI, Python, GGML, CUDA and Microsoft components. The build and bundle hooks require these checks.

## Test cleanup incident

A preexisting whole-drive planning test recursively removed the real drive's Strata directory after a read-only plan. Running it on this PC partially removed dependency sources and build outputs before an access error stopped it. The cleanup is removed. Tests now use a dedicated scratch tree and reject recursive cleanup outside it, including parent-junction escapes. Timestamp fixtures also stay in their temporary install directory.

Known pinned sources were fetched again. Both preexisting Strata worktrees report no tracked deletions. Current native/Prism packages were rehashed successfully. The old experimental Prism work and earlier build outputs are not proven fully recovered. The incident and recovery limits remain recorded in the implementation record; they must not be hidden by a release success claim.

## Publication requirements

Finish current suites and resolve their failures. The initial symmetric turbo4 probe only found a numeral inside a degraded response and does not qualify usable inference; its result is superseded by strict arithmetic-response and named-greeting checks for supported asymmetric K/V settings. Build the installer from verified current inputs, then exercise actual installed/extracted startup, memory, restart, shutdown and an isolated upgrade from the previous installer.

Create the 7z from that candidate, extract it into a new directory, and verify every payload hash and the final downloaded release hashes. Exclude model weights, memories, keys, developer caches and absolute build-path metadata. Record the final source commit, binary identities and SHA256SUMS.txt before pushing main, tagging and publishing.

This preview is unsigned and uses manual installer updates. The fork update URL is configured, but an owned signed automatic-update feed/key has not been qualified. Older releases remain available for rollback.

Only Windows x64/CUDA sm_120 on the tested RTX 5060 Ti is in this qualification scope. Other CUDA architectures, HIP, SYCL, Linux and Metal need separate build/runtime evidence. Updating Metal's source version does not establish a tested Metal artifact.
