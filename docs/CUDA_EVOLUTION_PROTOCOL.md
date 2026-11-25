# CUDA 13.5 / SM120 Kernel Evolution Protocol

Status: **Safety and verification protocol (`research/tsi-verified-evaluation`)** · **`releaseQualified=false`**

This protocol governs future Stage E native CUDA kernel evolution for NVIDIA RTX 5060 Ti (Blackwell SM120, CUDA 13.5) within `zapabob/Strata`. No default CUDA kernels are modified automatically by the Python EIO layer.

---

## 1. Immutable Verification Boundary (`robust-kbench`-Style)

To prevent reward hacking:

1. **Read-only verifier separation**: any candidate-generating agent or mutation script is strictly forbidden from editing verifiers, FP64 reference implementations, test inputs, tolerances, or resource guards (`tools/evolution/invariant_verifier.py`).
2. **Isolated build and workspace**: candidate CUDA sources compile only inside an isolated worktree/build directory under `H:/Strata` with `CMAKE_BUILD_PARALLEL_LEVEL=5` and unchanged RAM ($\ge 3\text{ GiB}$), commit ($\ge 4\text{ GiB}$), VRAM ($\ge 768\text{ MiB}$), and disk floors.
3. **Mandatory Compute Sanitizer gates** before any candidate enters the verified archive:
   - `compute-sanitizer --tool memcheck <test_binary>`
   - `compute-sanitizer --tool racecheck <test_binary>`
   - `compute-sanitizer --tool synccheck <test_binary>`
4. **Numerical and edge-case battery**:
   - Multiple independent seeds and real-model activation distributions
   - Unaligned and odd tensor shapes (e.g. `(1, 13, 129)`, `(3, 255, 513)`, `(7, 1023, 2049)`)
   - Extreme boundary values, zero/subnormal inputs, and NaN/Inf propagation checks
   - Exact FP64 reference tolerance maintained without relaxation
   - Explicit `cudaDeviceSynchronize()` before start and stop timers (no unsynchronised async timing)
5. **Single-GPU exclusivity**: never execute concurrent GPU benchmarks on the single RTX 5060 Ti when comparing candidate timings, as shared VRAM/PCIe contention invalidates paired measurements.
6. **Hardware feature discipline**: SM120 consumer Blackwell capabilities must be verified explicitly against the installed CUDA 13.5 toolkit and RTX 5060 Ti hardware; datacentre-only Blackwell instructions are never assumed available.
