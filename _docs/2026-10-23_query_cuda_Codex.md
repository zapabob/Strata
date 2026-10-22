# GPU triality query transform

Date: 2026-10-23, Asia/Tokyo.

## Overview and scope

This change adds a standalone F32 CUDA query transform with one device spinor per row. It is separate from the CPU controller and does not route live model queries. The task-owned files are `spin8/include/spin8/query_cuda.h`, `spin8/src/query_cuda.cu`, `spin8/tests/query_cuda_test.cu`, and this record. CMake integration is owned by the root agent. No service, model, dependency, release, commit, or existing source file was changed here.

## Requirements and decisions

The CPU definition is `C(c)[i,a] = sum_b Gamma_i[a,8+b] c[b]` and `A(c)=C(c)C(e0)^T`. A caller-created opaque plan reads the actual chirality-ordered Clifford generators once, checks that each upper-right row is a signed permutation, and stores its sign and spinor-coordinate index. It also derives the signed permutation `C(e0)^T`. For each full eight-scalar group, the kernel contracts `C(e0)^T` with the input, then `C(c)` with that result. It generates no per-query matrix on either host or device. The exact `e0` branch copies source bits, including signed zero.

The launch takes an explicit stream, raw device pointers, element strides, byte capacities, row count, and width. Checked arithmetic covers the final accessed element and tile count. Null, misaligned, undersized, stride, and partial-overlap layouts are rejected before launch. Source and destination may be exactly identical with equal strides. The spinor and error flag must not overlap the source or destination. The caller initializes the device error flag; the kernel only ORs flags, including invalid spinor bit 8 and the existing nonfinite bit 1. A finite spinor is accepted when its F32 norm differs from one by at most `1e-5`. On a nonzero flag, destination is invalid; the kernel makes no failure-atomic promise.

The plan is immutable after construction and may be shared while alive. The caller must keep it alive through launch submission and ensure the supplied device allocations and stream belong to the same CUDA device. The API allocates no GPU memory and performs no host-device copy or stream synchronization. Launch errors are returned immediately; asynchronous failures require caller synchronization.

## Traceability and verification

The CPU triality equation maps to the signed permutation plan and two kernel contractions. The independent GPU test compares 100 random row spinors with `spin8_query_matrix`, checks exact identity including signed zero, tests nontrivial exact in-place updates, and exercises all tail lengths 1 through 7. It also checks row padding, capacities, strides, overlap, nonunit/NaN spinor flags, NaN tail detection, and sticky flags.

`clang-format -i` and `clang-format --dry-run --Werror` passed on all three code files. The root agent integrated the two CUDA files in CMake and ran `cmake --build H:/Strata/build/spin8-cuda --config Release --target spin8_query_cuda_test --parallel 1`. I inspected `H:/Strata/build/query-cuda-build.log`: nvcc generated `compute_120,sm_120` code and linked the test executable. MSVC emitted D9025 because the generated `/W1` option overrode `/W4`; this build is not evidence of W4-clean compilation.

The root agent ran the actual GPU test, compute-sanitizer memcheck and racecheck, and the complete standalone CTest suite. I inspected `H:/Strata/build/query-cuda-memcheck.log`, `H:/Strata/build/query-cuda-racecheck.log`, and `H:/Strata/build/spin8-cuda-all-ctest.log`. The new test reported PASS for 100 random row spinors against CPU matrices, exact `e0` in-place identity with signed zero, nontrivial in-place transforms for every tail length 1..7, padding, capacity/stride/overlap rejection, and nonfinite/sticky flags. Memcheck reported zero errors; racecheck reported zero hazards, errors, and warnings. The complete standalone suite passed 6/6 tests, including `spin8_query_cuda`. These build and GPU commands were root-run; the logs provide the shared evidence.

No throughput, model quality, controller fusion, CUDA graph, HIP, SYCL, or production integration claim follows from these tests. The compiler warning-level override remains a build-configuration limit owned by the root agent.

## Applied controls and next action

Read the canonical pre-implementation prompt, PC/Codex/project `AGENTS.md`, common engineering, implementation-start, skill-selection, application-development and C++ SOPs, and the `milspec-codex-standard` skill. This is an internal engineering baseline, not a formal MILSPEC certification. The implementation remains an opt-in standalone API and leaves existing behavior untouched. The next integration step is an explicit caller for GPU-resident controller spinors, with model-level numerical and speed validation before runtime routing. Rollback is removal of these new files and their root-owned CMake entries.

Self-review-event: `ticket_completed`. The new GPU test, memcheck, racecheck, and standalone CTest logs show no task-local failure. Review level: review-only; no AGENTS, SOP, skill, QA, or automation update is supported by this evidence. The `/W4` override is recorded as a configuration warning for its CMake owner, not silently accepted as a clean high-warning build.
