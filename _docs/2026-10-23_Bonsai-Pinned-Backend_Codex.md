# Bonsai pinned runtime and supervisor capability boundary

## Objective and requirements

Build the separately pinned Prism Bonsai runtime without replacing Strata's ggml or touching an active server. Preserve default supervisor arguments exactly. Resolve Windows llama-server.exe correctly. Reject unimplemented Spin8 modes and profiling before any start/restart lifecycle action. Record source identity and artifact hashes; do not infer model compatibility or Spin8 integration from a successful build.

## Applicable controls

Read the canonical <PC_CANONICAL_PROMPT>, home and Codex AGENTS, project AGENTS, and common engineering, implementation start gate, skill selection, deep research, security, application, LLMOps, C++, and TypeScript SOPs. Applied milspec-codex-standard, deepresearch-defense-standard and llama-cpp skills. Identity, environment, tool use, authorization, and security conflicts in copied prompt material remain subordinate to actual session instructions. No formal MILSPEC certification is claimed.

## Sources and architecture

Prism source: https://github.com/PrismML-Eng/llama.cpp/tree/73bfe6cc485554822f80c473a3c0c4f25e80f41b . Reference source: https://github.com/zapabob/llama.cpp/tree/2c8e9655cdc6ea31051d4437a71492e717d046a4 . Exact detached checkouts are stored in <STRATA_DATA>\deps\prism-73bfe6cc and <STRATA_DATA>\deps\zapabob-2c8e9655. No fork-wide merge or ggml replacement was made.

The Prism source contains GGML_TYPE_PQ2_0=142, GGML_TYPE_PTQ1_0=143 and GGML_TYPE_Q2_0=42 in ggml/include/ggml.h. Its llama-model.cpp reads prism.hadamard.version, block_size and tied_output metadata, and llama-graph.cpp applies weight-side Hadamard transforms. This is source evidence only. No real model-load inference test has been performed by this backend task. The pinned zapabob source exposes Q2_0, but does not expose the two Prism-private type identifiers; it must not be advertised as interchangeable for them.

Neither pinned source contains the requested Spin8 attention graph hook. The host therefore reports Spin8 unavailable unconditionally, regardless of a manifest's claims. This avoids confusing separately implemented standalone Spin8 operators or a future CLI flag with a working ggml scheduler/attention integration.

## Changes

tools/spin8_backend.ps1 acquires exact source pins, refuses unexpected origins/revisions or dirty base source, builds out of tree, runs --version, and emits bonsai-runtime.json with commands and all adjacent binary/DLL SHA256 digests. It does not install globally, download a model, set persistent environment variables, or start/stop inference. An acquisition-only run writes source-pin.json separately from build evidence. The script targets PowerShell 7 on this Windows machine.

The approved plan requires standard sm_120, so the first unmodified CUDA build was stopped at 30/508 objects when inspection confirmed that upstream CMake unconditionally replaces architecture 120 with 120a. No 120a build is accepted as the planned deliverable. tools/spin8_backend_sm120.patch adds an opt-in GGML_CUDA_STANDARD_SM120 CMake option, preserves CMAKE_CUDA_ARCHITECTURES=120, disables architecture-specific BLACKWELL_MMA_AVAILABLE instructions and their host selection, and retains the regular integer/half paths. It does not change Bonsai dequantization or Hadamard mathematics. The original pinned Prism checkout remains clean; a separate detached worktree <STRATA_DATA>\deps\prism-73bfe6cc-sm120 records the exact patch. Its manifest correctly reports source.dirty=true plus patch identity/digest a291a22cd8915edee441e39b08b1c948e5ecc18b41060529c120701bfcf26ddd. The probe only accepts this explicitly whitelisted patch and checks its artifact digest. This is a source-modified build based on the pinned revision, not an unmodified vendor binary.

apps/host/server/spin8-backend.mjs defines typed configuration errors and a capability probe. Off with no profile produces no additional arguments. Every active mode, and any profile output request, throws SPIN8_BACKEND_UNAVAILABLE. The probe executes only the explicitly selected binary's --version with a timeout, verifies pinned local build provenance and artifact digests, and keeps executable availability, source-level format support and Spin8 support separate. A local manifest is not a vendor signature or model-load proof.

apps/host/server/supervisor.mjs resolves Windows .exe files in engine roots, version directories and CMake bin directories. Its opt-in capability probe uses STRATA_BONSAI_MANIFEST; actual binary selection remains explicit through STRATA_LLAMA_SERVER. Spin8 validation precedes the early-return, stop or spawn paths in start/restart. The existing command argument vector is unchanged when Spin8 is absent or off.

apps/host/tests/spin8-backend.test.mjs checks exact default args, all active modes, invalid configuration, unchanged lifecycle state after rejection, Windows discovery, executable-only probes, and invalid or traversing manifests. A manifest cannot grant Spin8 support.

## Commands and verification

git clone --filter=blob:none --no-checkout followed by git checkout --detach for each exact revision. Initial PrismML/llama.cpp URL returned 404; the official PrismML-Eng URL was then verified and used. No files were obtained from that failed URL.

node --test apps/host/tests/spin8-backend.test.mjs apps/host/tests/monitor-dashboard.test.mjs: 17 passed, 0 failed. Additional regression evidence and final build result will be recorded below.

Build: .\tools\spin8_backend.ps1 -Backend prism -Device cuda -Jobs 4 . Planned output is <STRATA_DATA>\build\prism-73bfe6cc-cuda-sm120. Console evidence is <STRATA_DATA>\build\prism-sm120-build-console.log. The earlier 120a attempt is preserved under prism-73bfe6cc-cuda with prism-build-console.log. A first configure attempt exposed a PowerShell array concatenation error producing a separate ON argument; the owned CMake process was stopped, script corrected to a single -DGGML_CUDA=ON argument, and the attempt preserved as <STRATA_DATA>\build\prism-build-first-attempt.log. No inference process was stopped.

node --test apps/host/tests/platform-paths.test.mjs apps/host/tests/user-args.test.mjs apps/host/tests/parallel-default.test.mjs apps/host/tests/spin8-backend.test.mjs: 32 passed, 0 failed. PowerShell parser reported no syntax errors for tools/spin8_backend.ps1.

Reference acquisition: .\tools\spin8_backend.ps1 -Backend zapabob -AcquireOnly: exact pin cleanly verified and source-pin.json written under <STRATA_DATA>\build\zapabob-2c8e9655-cuda. Reference runtime compilation is not claimed.

## Limits and next integration

The pinned Bonsai runtime needs a real custom ggml attention operation, scheduler/device handling, shape/KV/mask semantics, core ABI integration, profile ownership, and model inference comparison before any active Spin8 mode can be offered through this supervisor. CUDA kernel unit tests or a native Strata hook do not establish Prism graph integration. HIP/SYCL runtime builds, real Bonsai model loads, measured quality/latency and GUI acceptance are outside this backend evidence.

The local manifest records build provenance but is unsigned and trusted only as local build output. Rollback is removal of the opt-in configuration and explicit runtime selection; the original engine and active runtime are preserved. Dependency folders and evidence on H: have not been deleted.

## Self review

Self-review-event: qa_defect. The initial configure array split and the upstream architecture rewrite were detected before completion. Review-only response: require a single -DGGML_CUDA=ON argument and inspect actual generated architecture/cubin evidence, rather than infer it from caller intent. The local script, approved patch digest test, manifest and this log capture the corrective controls. No AGENTS, SOP, skill, automation or global memory was edited. Formal completion remains conditional on the actual CUDA link and runtime probe; a partial build is not a working runtime.

Independent review identified that an unstaged-only git diff could hide additional staged tracked edits in the patched worktree. tools/spin8_backend_verify.ps1 now centralizes the complete git diff HEAD comparison, including both staged and unstaged tracked changes, and both the pre-build and post-build gates call it. apps/host/tests/spin8-backend-source.test.mjs produced 2 passed, 0 failed: an approved offline fixture patch is accepted, an extra staged tracked edit is refused, and the test demonstrates that the old unstaged-only comparison would have missed it. The live compiling source was separately reverified against HEAD with the exact approved digest, saved as source-patch-full-head-now.diff. The currently running script was parsed before this fix, so final manifest acceptance requires a subsequent incremental run of the updated builder and both corrected gates.

The compiled acc.cu.obj was inspected using CUDA 13.3 cuobjdump --list-elf. It reports acc.cu.1.sm_120.cubin. Evidence: <STRATA_DATA>\build\prism-73bfe6cc-cuda-sm120\sm120-object-evidence.txt. This is object-level architecture evidence, not completed server or inference evidence.
