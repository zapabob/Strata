# Spin8 CUDA implementation and GPU evidence

Date: 2026-10-23, Asia/Tokyo. Branch: `codex/strata-spin8-bonsai`.

## Scope and requirements

Implement the optional standalone Spin8 CUDA primitives and actual masked attention on the installed RTX 5060 Ti (compute capability 12.0). This is one part of the broader Spin8 task. This worker owns `spin8/src/cuda.cu`, `spin8/tests/cuda_test.cu`, `spin8/include/spin8/cuda.h`, and this log. CPU algebra, build files, native engine integration, and live model evaluation belong to other workers. Existing server processes were not stopped or restarted by this worker. No commit, push, release, model conversion, environment variable change, or dependency installation was performed.

Mandatory context read: `C:/Users/downl/_docs/prompts/CLAUDE-FABLE-5.md`, PC and Codex AGENTS, project AGENTS, common engineering SOP, Implementation Start Gate, Skill Selection, CPP, MLOps, and LLMOps. Skills: `milspec-codex-standard` and completion/QA-triggered `agent-self-review-evolution`. This records internal engineering controls; it does not claim formal MILSPEC certification.

Acceptance: real sm_120 build, forward/inverse and fused GPU outputs agree with CPU references, norm and inner product preservation within stated numerical tolerance, safe strided tails, explicit finite/error reporting, one pre-softmax combined score and one common softmax/V reduction, and graph replay with GPU-resident active key counts. No end-to-end acceleration claim is permitted from these tests.

## Implementation and decisions

The C ABI is in `spin8/include/spin8/cuda.h`. Tensor pointers are device pointers and launch matrices/weights are host arrays copied into kernel arguments. The API allocates nothing, changes no global state, retains no host memory, and synchronizes no stream. The caller supplies a CUDA stream, buffers, score scratch, and an integer device error flag. CUDA runtime failures are returned; asynchronous failures require caller stream synchronization. A nonzero device flag invalidates output. Attention `reset_error=0` accumulates errors across heads following a caller-owned flag reset.

Full eight-element blocks use y=Mx; inverse uses M transpose. Host matrices must be finite and orthogonal within 1e-8. A remaining one to seven scalars is copied unchanged. Source/output range overlap is rejected except an exact in-place transform with identical stride. Fused three-view outputs must be disjoint. Weighted reduction applies each view's inverse before mixing in the original vector space. Weights must be finite, nonnegative, and sum to one within 1e-12; null selects one third.

Signed normalized Hadamard uses an actual eight-element FWHT: forward H D, inverse D H. All 256 sign masks are exercised. This CUDA primitive is explicitly block8; the CPU module's later general-width Hadamard API is a separate surface.

Attention accepts F32 Q and F32/F16 K and V, explicit row strides suitable for one head of a gathered GQA KV layout, and an optional byte mask. Mode 0 computes ordinary dot products, mode 1 computes all three matrix-transformed dot products and mixes their logits before a single softmax, and mode 2 computes the signed HD baseline. Original V is reduced once using the common distribution. Head and value dimensions are equal in this CUDA API. Exact orthogonal Q/K transforms preserve dot products mathematically; these tests establish numerical agreement, not a model quality gain.

`nk` is key capacity and score/mask row stride. Optional device `nk_device` provides the active key count for CUDA graph replay. Unused capacity is not read and can contain NaNs. Invalid active counts set bit 4 and write zero output. An all-masked row writes zero and sets bit 2. Any nonfinite active tensor value or arithmetic result sets bit 1. The caller must inspect the flag before accepting output. Allocation capacity and stream/device ownership remain explicit caller contracts.

## Commands and observed results

Toolchain: CMake 4.4, Visual Studio 17 2022 generator, MSVC 19.44.35224.0, CUDA 13.3.73, RTX 5060 Ti, runtime 13030. Configure:

```powershell
cmake -S spin8 -B H:/Strata/build/spin8-cuda -G 'Visual Studio 17 2022' -A x64 -T 'cuda=C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3' -DSPIN8_ENABLE_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=120
cmake --build H:/Strata/build/spin8-cuda --config Release --parallel 2
& H:/Strata/build/spin8-cuda/Release/spin8_cuda_test.exe
```

First CUDA compile failed because `CUDART_INF_F` needs an explicit `math_constants.h` include. That include was added and compilation/linking succeeded. Initial vendor CUDA-header C4819 warnings under the Japanese Windows code page were reported to the CMake owner, who added UTF-8 and W4 options. They are build configuration changes owned by the CPU/core worker.

Fresh GPU executable result: PASS, 1,584,900 checked scalar conditions. Widths 1, 7, 8, 9, 15, 16, 17, 31, 127, 256, 513; row counts 1, 3, 129; six mixed plane rotors. Maximum transform absolute error 4.76837158e-07, maximum relative norm discrepancy 7.36711132e-08, maximum inner-product discrepancy normalized by 1+sqrt(input norm squared) 1.48418922e-07. Tests use independent double matrix multiplication and round trips, padding sentinels, exact in-place execution, fused three-view/reference agreement, and inverse-to-common weighted reduction.

Attention checked both F32 and F16 KV, dimensions 1, 7, 8, 9, 17, 64, 128, key counts 1, 3, 137, two query rows, all three modes, nontrivial row strides, byte masks, exact masked probability zeros, and softmax sums. CPU reference is the core's F64 attention on the exact F32/half-rounded input values. Maximum absolute output error against CPU F64: 1.90135474e-07. CUDA graph capture/replay changed device key counts between one and the available active count, and tested invalid zero/over-capacity counts. Error tests covered undersized strides, arithmetic size overflow, partial overlap, flag/output alias, output/output alias, invalid inverse selector, nonfinite and nonorthogonal matrices, malformed weights, NaN in a full block and tail, infinity in Q, NaN in F16 KV, arithmetic overflow, sticky multi-head error flags, explicit reset, unsupported BF16 KV, and all-masked rows.

```powershell
& 'C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3/compute-sanitizer/compute-sanitizer.exe' --tool memcheck --error-exitcode 99 H:/Strata/build/spin8-cuda/Release/spin8_cuda_test.exe
& 'C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3/compute-sanitizer/compute-sanitizer.exe' --tool racecheck --error-exitcode 99 H:/Strata/build/spin8-cuda/Release/spin8_cuda_test.exe
```

Both full GPU suite runs passed. Memcheck: ERROR SUMMARY: 0 errors. Racecheck: 0 hazards displayed, 0 errors, 0 warnings. These are real GPU executions, including graph replay and shared-memory softmax reductions.

```powershell
& 'C:/Program Files/LLVM/bin/clang-format.exe' --dry-run --Werror spin8/src/cuda.cu spin8/tests/cuda_test.cu spin8/include/spin8/cuda.h
& 'C:/Program Files/LLVM/bin/clang-tidy.exe' spin8/src/cuda.cu --quiet --checks='clang-analyzer-*,bugprone-*,performance-*' -- -std=c++17 --cuda-host-only '--cuda-path=C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3' --no-cuda-version-check -Ispin8/include
```

Formatting passed. clang-tidy 22.1.8 completed with exit 0 and no analyzer correctness finding. It reported maintainability suggestions about adjacent stride/count parameters, bounded view-index multiplication, and enum storage size, plus a warning that CUDA 13.3 is newer than its partially supported 12.9. C enum ABI sizes are intentional. This was host CUDA analysis and is not proof of exhaustive device static analysis.

Initial whole standalone CTest run: CUDA, C ABI, and native adapter passed; CPU failed the reduction oracle. Core owner identified an exact-floating-point comparison of a default one-third weight sum and corrected the CPU oracle tolerance. Final post-fix CTest evidence is recorded below when available.

## Self review, residual risks, and rollback

Self-review-event: `qa_defect` (initial missing constant include and CPU oracle failure) and `ticket_completed` for the independently verified CUDA unit. The compiler issue was fixed at its source. The CPU failure was sent to its owner and was not treated as CUDA failure or hidden. Review mode: review-only; no governance, skill, SOP, automation, or memory changes. These failures do not justify changing global instructions.

No model-level output quality, perplexity, token throughput, end-to-end speed, long-context stress, multi-GPU, HIP, SYCL, BF16 KV, or F64 CUDA tensor execution is established here. This implementation is a straightforward correctness-oriented CUDA path, with repeated per-key view transforms and O(nq*nk) score scratch. Long-running/native graph lifecycle and production performance remain parent-task gates. No live server modification was used to establish this standalone evidence.

Rollback is to leave the optional Spin8 CUDA build disabled and remove only this task's new CUDA files if the task is abandoned. Preserve other workers' changes. Next acceptance step: final standalone CTest and parent-owned native adapter/model evaluation, with numerical and speed claims separated.
