# Batched per-head v3 CUDA query execution

Status: implemented; focused CUDA test and all eight spin8 CTests passed. Independent review is still required. This is not model or release qualification.

## Scope and requirements

Task 3 starts from `f992636`. Add a versioned F32 device parameter bank with independent per-head Win[8,width], bin[8], Wout[7,8] and bout[7]. Share each head's parameters across tokens. Execute channel-contiguous [channels,query_heads,tokens] tensors with padded head/token byte strides, prefill, decode, exact in-place operation, and identity tails. Preserve the existing single-controller C ABI and the actual v3 numerical convention.

Acceptance requires independent CPU per-head comparisons at width256/24 heads and tail widths, zero/signed-zero identity, independent parameter/tensor padding, rejection of invalid versions, capacities, strides, aliases and overflow, nonfinite flag propagation, and evidence of one kernel on the caller's non-default stream. No allocation, synchronization, per-row dense matrix or global spinor buffer may be added to apply. Any flagged input/parameter/result invalidates all batch output; output rollback is not promised.

Source ownership is limited to `spin8/include/spin8/query_v3_cuda.h`, `spin8/src/query_v3_cuda.cu`, `spin8/tests/query_v3_cuda_test.cu` and this log. No model, server, engine graph, package, deployment or default changes are included. Parent execution record is not staged.

## Standards and decisions

Read the canonical `C:/Users/downl/_docs/prompts/CLAUDE-FABLE-5.md`, home/Codex/project AGENTS and Common MILSPECLLMOps, Implementation Start Gate, Skill Selection, C++, C, LLMOps and Security SOPs. Apply only instructions compatible with real system/tool/environment rules. Skills used: milspec-codex-standard, incremental-implementation and code-review-and-quality. Independent review is coordinated by the parent; this task spawns no agents. Memory registry had no relevant Strata/query_v3 hits.

The bank descriptor has ABI version 1; the opaque plan remains mathematical convention v3. Independent byte capacities and head strides prevent assuming dense per-head storage. The tensor requires disjoint monotonically nested head/token spans. The final head need not include unused stride padding before the next token. Conservative occupied-span overlap checks include inter-row padding and reject partial overlaps. Device allocation validity and device/stream ownership remain explicit caller contracts.

One existing kernel now selects head=row%heads and token=row/heads before running the unchanged sequential FP64 controller, scaled bounded chart and signed-permutation transform. The legacy wrapper describes one shared head across its rows without changing its signature or validation. Shared state and barriers remain CTA-local. No global error-flag read pretends to provide atomic batch failure: callers discard the complete batch on any nonzero error flag after asynchronous completion.

## Verification plan and evidence

Build directory: `H:/Strata/build/spin8-cuda`, existing Visual Studio 17 2022 generator, CUDA architecture120, Release. Root is separately building Prism and controls serial compiler access. No compiler was started before clearance.

Tests add 24 independent head controllers, width256/263/7, token counts1/4, nontrivial and zero-output heads, signed-zero vectors, independent NaN-filled bank padding, different source/destination tensor padding, exact minimum byte capacities, exact in-place equivalence, graph capture and replay, malformed bank and tensor contracts, non-first-head errors in every parameter array, last-token/head tail errors, identity-controller errors and F32 result overflow. A tail-only controller test checks that copied remainder channels alter each head's block rotation, using a token stride exactly equal to the occupied head span.

Before build: read-only resource check recorded free physical memory3889728 KiB; C free17187426304 bytes and H free4068884480 bytes in a subsequent drive check. Capacity will be rechecked immediately before compilation. No files were moved or deleted.

Formatting used `C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/Llvm/bin/clang-format.exe` with ranges restricted to new/changed sections. `git diff --check` passed (Git reports expected LF-to-CRLF working-copy notices).

Root granted serial compiler clearance after interrupting its own Prism build and preserving its evidence. Immediately before this build: free physical memory7572924 KiB, H free4048154624 bytes, C free17193578496 bytes. The task guard required at least2 GiB free physical memory and1 GiB free disk for this small incremental build. No deletion or cleanup was used.

Evidence directory: `H:/Strata/build/query-v3-batched-20261023`. Each command below has a matching log and separate exit receipt there.

```powershell
& 'C:/Program Files/CMake/bin/cmake.exe' --build 'H:/Strata/build/spin8-cuda' --config Release --target spin8_query_v3_cuda_test -j 1
& 'H:/Strata/build/spin8-cuda/Release/spin8_query_v3_cuda_test.exe'
& 'C:/Program Files/CMake/bin/cmake.exe' --build 'H:/Strata/build/spin8-cuda' --config Release -j 1
& 'C:/Program Files/CMake/bin/ctest.exe' --test-dir 'H:/Strata/build/spin8-cuda' -C Release --output-on-failure -j 1
```

All four commands exited0. The focused executable passed all old and new cases. Six batched reference combinations (width256/263/7, tokens1/4, 24 heads each) measured maximum absolute F32 output error0 against independent CPU per-head controllers. Each combination captured exactly one kernel node on the non-default stream. This is a measurement for these cases only, not a general bitwise accuracy guarantee. Full CTest passed8/8 in7.33 seconds: spin8_cpu, spin8_query, spin8_query_v3, spin8_c_abi, spin8_cuda, spin8_query_cuda, spin8_query_v3_cuda and spin8_native_adapter.

GPU readback: NVIDIA GeForce RTX5060 Ti, compute capability12.0, driver616.92, total memory16311 MiB. CUDA compilation used13.3, compute_120/sm_120, the existing MSVC14.44.35207 toolchain and /W4. The build emitted one C4211 warning in NVCC's generated temporary `query_v3_cuda.cudafe1.stub.c`; there were no handwritten-source compiler diagnostics. No warning was suppressed. The focused executable SHA256 is `190EB5169ECC43CEC6C46FB988C019B0ED9D6C0B6A083EC37AD84C930704B0D0`.

Optional static analysis was attempted with the installed VS LLVM19.1.5 clang-tidy:

```powershell
& 'C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/Llvm/bin/clang-tidy.exe' 'spin8/src/query_v3_cuda.cu' --quiet '--checks=-*,clang-analyzer-*,bugprone-*' -- -std=c++17 --cuda-host-only '--cuda-path=C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3' --no-cuda-version-check -Ispin8/include
```

It exited1 because `__clang_cuda_runtime_wrapper.h` is missing from that installation. Its4865-warning summary and partial warnings are not a valid CUDA static-analysis result. The exact log is retained as `clang-tidy.log`; a complete static-analysis pass is unverified. No dependency was installed or analysis configuration weakened to force success.

Self-review checked byte-to-element conversion only after aligned checked spans, conservative occupied-span aliasing, matching bank dimensions/version, nonzero dimensions, checked head*token count, no in-place write before controller reads finish, immutable head-bank reuse across tokens, per-row shared-state reset/barriers, and whole-batch flag semantics. Existing legacy ABI declarations/validation and numerical operations remain intact. `git diff --check` passed. Final resource readback: H free4047011840 bytes, free physical memory7001428 KiB. Port8080 had no listener. Root was notified when all compiler-dependent work finished, before it resumed Prism.

## Limits, risks and rollback

This task proves only library tensor execution, not real-model integration, quality, speed or release qualification. CPU/GPU tanh differences and arbitrary finite controller calibration limits remain as documented by the legacy API. Device pointer allocation sizes cannot be proven by host range checks; caller ownership/lifetime rules still apply. CUDA sm120 is the available verification target; other devices, precision types and backends are not advertised.

Rollback is a focused Git revert of this task's commit after checking downstream adoption. No user files, existing evidence or running services are changed by rollback of this source-only feature.
