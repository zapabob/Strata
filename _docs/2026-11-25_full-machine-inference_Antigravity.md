# 2026-11-25 Full-Machine Heterogeneous Inference Implementation Log (Antigravity)

- **Date**: 2026-11-25 (JST)
- **Workspace**: `C:/Users/downl/Documents/ChatGPT/Strata` (`main` base commit `21473cc9b2fb33c27be1ffbd0bdc87c0e12fec02`)
- **Authoring AI**: Antigravity
- **Release Qualification**: `releaseQualified=false` (local unsigned CUDA 13.5 SM120 builds; Windows Authenticode absent)

---

## 1. Overview

Enabled end-to-end full-machine heterogeneous inference across every hardware tier of this physical Windows PC — **GPU (RTX 5060 Ti 16 GB Blackwell SM120) + CPU (Ryzen 5 4500 6 physical cores / 12 logical threads split into 6 primary compute threads + 6 SMT I/O threads) + System RAM (31.87 GiB DDR4 / 63.87 GiB commit) + Dual SSDs (`C:` Crucial P3 1TB NVMe + `H:` S5-1TB SSD)** — across all five Strata native CUDA 13.5 SM120 engines (`strata.exe`, `strata-inkling2.exe`, `strata-inkling.exe`, `strata-hy4.exe`, `strata-q38.exe`), plus a unified hardware-aware planner/benchmarker/server launcher (`tools/full_machine_infer.py`) and ready-to-run server presets (`configs/`).

---

## 2. Target Physical Hardware & Safety Floors

| Tier | Physical Hardware | Role in Full-Machine Pipeline |
|---|---|---|
| **Tier 1 (GPU)** | NVIDIA GeForce RTX 5060 Ti 16 GB (`sm_120`, 36 SMs, 15.93 GiB GDDR7 @ 448 GB/s, 180W, PCIe Gen3 link, CUDA 13.5) | Dense weights, KV cache (Q8/F16), looped-core Tier-1 experts (`128/128/layer`), hot outer Tier-2 experts, CUDA Graphs, WDDM 1536 MiB reserve (zero Shared-GPU-Memory spill). |
| **Tier 0a (CPU Primary)** | AMD Ryzen 5 4500 6 physical cores (`logical CPUs 0, 2, 4, 6, 8, 10`, Zen 2 AVX2+FMA3+F16C) | CPU 0 dedicated to GPU host loop + doorbell; CPUs `2, 4, 6, 8, 10` pinned 1:1 to AVX2 MoE compute workers (host participates in drain = 6 physical cores). |
| **Tier 0b (CPU SMT)** | 6 SMT secondary logical threads (`logical CPUs 1, 3, 5, 7, 9, 11`) | Dedicated via Windows CPU Sets (`io_smt=[1,3,5,7,9,11]`) to `DirectFile` async overlapped SSD I/O (default 6 threads), `TwoPriorityExpertScheduler` (`InkColdStore` / `hy4 ColdStore`), and `MmapPrefetchWorker` (`PrefetchVirtualMemory`). |
| **Tier 2 (System RAM)** | 31.87 GiB DDR4 (63.87 GiB total commit) | Commit-safe pinned host expert slabs (capped below `min(avail_phys, avail_commit) - 7.5 GiB`, up to 10 GiB), mapped zero-copy doorbells, pinned embedding staging, optional `ram_fit.squeeze()`. |
| **Tier 3 (Dual SSD)** | `C:` Crucial P3 1TB NVMe (929.7 GiB, ~10.6 GiB free), `H:` S5-1TB SSD (953.9 GiB, ~220.5 GiB free) | Zero-copy GGUF mmap + async `PrefetchVirtualMemory` lookahead/warmup (`strata-inkling2.exe`, `strata-q38.exe`) and `FILE_FLAG_NO_BUFFERING | FILE_FLAG_OVERLAPPED` Direct I/O (`strata.exe`, `strata-inkling.exe`, `strata-hy4.exe`). |

Mandatory safety floors retained unchanged:
- Available RAM `>= 3.0 GiB`
- Available Commit `>= 4.0 GiB`
- Free `C:\` `>= 5.0 GiB`
- Free `H:\` `>= 10.0 GiB`
- Build parallelism capped at `-j 5` (`CMAKE_BUILD_PARALLEL_LEVEL=5`).

---

## 3. Assumptions, Design Decisions & Empirical A/B Findings

1. **6 Physical Compute Cores + 6 SMT I/O Threads vs 12 Compute Threads**:
   - Measured on Sakura Inkling-2-Mini 131K (`H:/Strata/models/Sakura-Inkling-2-Mini-Uncensored-Q4_K_M.gguf`, 16.28 GiB):
     - **6 physical compute threads (`host=0, workers=2,4,6,8,10`) + 6 SMT I/O (`[1,3,5,7,9,11]`)**: `tg = 37.98–42.33 t/s` (`cpu_ms = 313.5–328.1 ms`).
     - **11 workers (12 compute threads oversubscribing 6 physical cores)**: `tg = 29.68 t/s` (`cpu_ms = 445.4 ms`, **-21.9% slower** due to SMT L1/L2 & DDR4 bandwidth contention).
   - Decision: Keep compute workers at physical cores (`5 workers + host = 6P`) and dedicate all 6 SMT secondary threads (`1,3,5,7,9,11`) exclusively to asynchronous storage/prefetch I/O.
2. **Windows `STRATA_AUX_CPUS` Sweep Default (`off` vs `auto`)**:
   - Measured warm A/B on Sakura 131K (both runs with identical placement `GPU=2232, RAM_pinned=840, SSD_mmap=0`):
     - `STRATA_AUX_CPUS=auto` (swept 14 CUDA/driver threads onto single host SMT sibling `CPU 1`): `cpu_ms = 293.1 ms` (-10.4% faster CPU MoE), **but** total `tg = 35.73 t/s` (`867.6 ms`) because packing 14 CUDA driver threads onto Core 0's single SMT sibling added ~169 ms of GPU/WDDM submission latency.
     - `STRATA_AUX_CPUS=off` (with `io_smt=[1,3,5,7,9,11]` still active for storage/prefetch threads): `cpu_ms = 327.0 ms`, total **`tg = 42.33 t/s`** (`732.4 ms`, **+18.5% faster end-to-end**).
   - Decision (per `AGENTS.md` default-change rule): Keep `STRATA_AUX_CPUS` default `"off"` (opt-in via `STRATA_AUX_CPUS=auto` for machines with spare free physical cores) while keeping `io_smt=[1,3,5,7,9,11]` (`STRATA_AUX_IO_SMT=1`) always active for DirectFile / ColdStore / `MmapPrefetchWorker`.
3. **`q38-cuda135` Target Architecture Fix**:
   - Discovered `H:/Strata/build/q38-cuda135/CMakeCache.txt` had cached `CMAKE_CUDA_ARCHITECTURES=75`. Reconfigured explicitly with `-DCMAKE_CUDA_ARCHITECTURES=120` so `strata-q38.exe` compiles native SM120 Blackwell SASS (`cudart=13050 cublas=130600`).

---

## 4. Changed & Created Files

### Modified Engine Sources (This Session)
- `engine/include/strata/platform/aux_cpus.hpp`: Implemented full Windows backend (`GetLogicalProcessorInformationEx`, `GetSystemCpuSetInformation`, `SetThreadSelectedCpuSets`, `CreateToolhelp32Snapshot`), added `derive_io_smt()`, `pin_io_thread()`, and `io_plan()`, using `GetEnvironmentVariableA` on `_WIN32` for `/W4 /WX` warning-free builds.
- `engine/include/strata/core/ssd_stream_scheduler.hpp`: Pinned `TwoPriorityExpertScheduler` NVMe/SSD worker threads via `strata::aux_cpus::pin_io_thread()`.
- `engine/src/platform/direct_file.cpp`: Raised Windows default overlapped I/O issuing threads from `4` to `6`, switched worker pinning to `pin_io_thread()`, and replaced `std::getenv` with `GetEnvironmentVariableA` on `_WIN32` (0 warnings).
- `engine/tests/platform/aux_cpus_test.cpp`: Added 6C/12T `derive_io_smt` verification and live Windows CPU Sets placement assertions.
- `engine/src/inkling2/inkling2_engine.cu`: Wired `strata::aux_cpus` topology registration (`aux` + `io_smt`), added SMT-pinned `MmapPrefetchWorker` (`PrefetchVirtualMemory` warmup + next-layer zero-copy mmap lookahead, guarded by `STRATA_SSD_PREFETCH`), and added unified `full-machine tiers:` placement telemetry.
- `engine/src/inkling2/cuda/ink_hybrid.cuh`: Added Windows physical-core pinning (`GetLogicalProcessorInformationEx` + `SetThreadGroupAffinity`) for `master_thr` and `workers`, registered `aux_cpus::set_topology()` for `InkColdStore`, replaced bare `std::this_thread::yield()` spins with `strata_cpu_pause()` (fixing MSVC pause absence), and enabled `_mm_prefetch` on MSVC for idle L3 prefetch.
- `engine/src/hy4flash/run/hy4_cpu_experts.cpp`: Fixed Windows `CpuExperts::ram_available_bytes()` to respect Windows commit headroom via `strata::platform::host_ram_budget()`, and registered pinned workers with `strata::aux_cpus::set_topology()` for `ColdStore` SMT I/O placement.
- `engine/q38/src/engine.cu`: Added reusable pinned host embedding staging (`pinned_embrow`, up to `prefill_chunk` slots capped at 16 MiB) for `step()`, `mtp_draft_step()`, and `run_prefill_chunk()`, plus batched Windows `PrefetchVirtualMemory` before prefill embedding upload.

*(Pre-existing uncommitted Gen-L edits in `kq_avx2.*`, `nvfp4_avx2.cpp`, `native_expert.cpp`, `pool.*`, `inkling2_kernels.cuh`, and `_docs/2026-11-23_four-separate-components-disk_OpenCode.md` were preserved intact.)*

### New & Updated Tooling, Configs & Tests
- `tools/full_machine_infer.py`: Full-machine hardware prober (GPU/CPU P+SMT/RAM+Commit/Dual-SSD), GGUF header architecture scanner, 3-tier placement planner, resource-floor guard, live benchmarker, and OpenAI/Anthropic server launcher (`logging` + `tqdm`, strict type annotations, zero `print()`).
- `configs/strata-full-machine-sakura-131k.json`: Sakura Inkling-2-Mini 131K full-machine server preset.
- `configs/strata-full-machine-q38-27b.json`: Qwen3.8-27B SM120 full-machine server preset.
- `configs/strata-hy4-flash-ram32-vram16.json`: Fixed `exe` path (`H:/Strata/build/hy4-cuda135/strata-hy4.exe`) and added `STRATA_AUX_CPUS=off`, `STRATA_AUX_IO_SMT=1`, `STRATA_IO_THREADS=6`.
- `tests/test_full_machine_infer.py`: 5 pytest unit tests covering resource floors, GPU-resident planning, 3-tier SSD overflow planning, GGUF header parsing, and AST verification of zero `print()` calls.

---

## 5. Build, Test & Live Benchmark Results

### 5.1 Unit & Platform Tests
- **`aux_cpus_test.cpp`** (MSVC 14.50 `/std:c++20 /W4 /WX`): **PASS (0 warnings)** — reported live Windows topology `strata aux cpus (Windows): aux=[1] io_smt=[1,3,5,7,9,11] (on; 0 threads placed so far)`.
- **`tests/test_full_machine_infer.py`** (`pytest 9.1.1`): **5/5 PASSED in 1.04s**.
- **Engine binary smoke/selfcheck**:
  - `strata.exe --version` -> `strata 0.1.67` (rc=0)
  - `strata-inkling.exe --selfcheck` -> `[selfcheck] PASS backend=cuda ()` (rc=0)
  - `strata-q38.exe --version` -> `strata-q38 own-native 0.6.3 CUDA13 SM120 cudart=13050 cublas=130600` (rc=0)

### 5.2 Real-Model Full-Machine Benchmarks (RTX 5060 Ti 16 GB + Ryzen 5 4500 6C/12T + 32 GB DDR4)

| Benchmark Run | Model (Size) | Context | Tier Placement (Measured) | Prefill (`pp`) | Decode (`tg`) | CPU MoE (`cpu_ms`) | Parity |
|---|---|---|---|---:|---:|---:|---|
| **End-to-End Launcher (`full_machine_infer.py --bench`)** | Sakura Inkling-2-Mini Q4_K_M (16.28 GiB) | 131,072 (Q8 KV) | GPU 2232 exps (10.85 GiB) + RAM_pinned 840 exps (4.34 GiB) + CPU 6P+6SMT (`io_smt=[1,3,5,7,9,11]`) | **85.08 t/s** (188.1 ms) | **42.22 t/s** (734.3 ms) | 328.1 ms | **32/32 exact** |
| **Warm A/B (`STRATA_AUX_CPUS=off`)** | Sakura Inkling-2-Mini Q4_K_M (16.28 GiB) | 131,072 (Q8 KV) | GPU 2232 + RAM_pinned 840 + CPU 6P+6SMT | 80.49 t/s (198.8 ms) | **42.33 t/s** (732.4 ms) | 327.0 ms | **32/32 exact** |
| **Warm A/B (`STRATA_AUX_CPUS=auto`, 14 threads -> CPU 1)** | Sakura Inkling-2-Mini Q4_K_M (16.28 GiB) | 131,072 (Q8 KV) | GPU 2232 + RAM_pinned 840 + CPU 6P+6SMT | 83.86 t/s (190.8 ms) | 35.73 t/s (867.6 ms) | 293.1 ms | **32/32 exact** |
| **Cold 3-Tier Spill (`RAM tight -> SSD_mmap + Prefetch`)** | Sakura Inkling-2-Mini Q4_K_M (16.28 GiB) | 131,072 (Q8 KV) | GPU 2232 (10.85 GiB) + RAM_pinned 684 (3.60 GiB) + **SSD_mmap 156 (0.74 GiB, prefetch=on)** + CPU 6P+6SMT | 64.80 t/s (246.9 ms) | 14.24 t/s (2177.2 ms) | 1756.6 ms | **32/32 exact** |
| **A/B Oversubscribed (`--cpu-threads 11`)** | Sakura Inkling-2-Mini Q4_K_M (16.28 GiB) | 131,072 (Q8 KV) | GPU 2232 + RAM_pinned 840 + 12 compute threads | 73.90 t/s (216.5 ms) | 29.68 t/s (1044.5 ms) | 445.4 ms | **32/32 exact** |
| **UD Hybrid Default** | Inkling-2-Mini UD Q4_K_M (15.47 GiB) | 16,384 (Q8 KV) | GPU 2339 exps (10.42 GiB) + RAM_pinned 733 exps (3.34 GiB) + CPU 6P+6SMT | **109.64 t/s** (145.9 ms) | **53.28 t/s** (581.8 ms) | 131.6 ms | Greedy clean |
| **Q38 Dense SM120 Rebuilt** | Qwen3.8-27B 3.69bpw MTP (11.73 GiB) | 4,096 (F16 KV) | GPU weights 10.44 GiB + host mmap + pinned emb staging + `PrefetchVirtualMemory` | 6205.99 ms (16 tok cold) | **29.95 t/s** (1035.1 ms / 31 steps) | N/A (GPU) | Greedy clean |

*Comparison vs prior Gen-K baseline recorded in `AGENTS.md`*:
- Sakura: `33.54 t/s` (98K) -> **`42.22–42.33 t/s` (131K)** (**+26.2%** at 33% larger context)
- UD 16K: `35.99 t/s` -> **`53.28 t/s`** (**+48.0%**)

---

## 6. Local Deployment & SHA-256 Verification

All 5 freshly built CUDA 13.5 SM120 executables were deployed via overwrite copy to the local unsigned `0.6.9` component directories under `C:/Users/downl/AppData/Local/Strata/components/engine/` (`0.6.9-windows-x86_64-cuda-cuda13`, `strata-engine-0.6.9-...`, `strata-inkling-0.6.9-...`, `strata-hy4-0.6.9-...`, `strata-q38-0.6.9-...`), with every `engine-component.json` manifest updated (`build_id = "fullmachine-20261125-cuda13.5-sm120-unsigned"`, `releaseQualified = false`) and all 10 copied files verified bit-for-bit via SHA-256 readback:

| Binary | Size (bytes) | SHA-256 |
|---|---:|---|
| `strata.exe` | 67,440,128 | `bbecd9eb18be7df93ae5f63480576593882f457d76421baf19eea00253ebc1fd` |
| `strata-inkling2.exe` | 38,744,576 | `46ae3bf9b7be424ffe74cb25e1c88b419d26e8df9174a8c7983217663b02e0f7` |
| `strata-inkling.exe` | 11,586,560 | `5cc48101f8d01cb2ff50d6ac216b24da385a66bb7c159dffab4983f0f95e7308` |
| `strata-hy4.exe` | 13,686,272 | `b9ecca3a22e40f3b0460d75b45208090eb87fb76388ab6e117a168ce339fee73` |
| `strata-q38.exe` | 2,572,288 | `b2d6d4cf7c30157e80ecf902716ea0e284a4e916d05fb2fdcc798c583a96fcd9` |

---

## 7. Residual Risks & Limits

- **`releaseQualified=false`**: Unsigned local developer builds (no Windows Authenticode signature, no signed public component feed).
- **Not tested on real weights**: `strata-hy4.exe` (`Hy4-Flash-SQ-64.strata` is not present on local `H:/Strata/models`) and `strata-inkling.exe` `.strata` path (only `--selfcheck PASS` verified; GGUF Inkling-2 models ran via `strata-inkling2.exe`).
- **Long-context full-window quality & multi-client GPU concurrency**: Only 16-token prompts + 32-token greedy decode were measured here; full-window 131K generation quality and concurrent GPU workloads remain unqualified.
- **Disk `C:` headroom**: Currently `10.6–10.7 GiB` free (above the 5 GiB floor); keep large model downloads and build caches on `H:` (`220.5 GiB` free).

---

## 8. Quick Usage Commands

```powershell
# 1. List all local models and their computed full-machine GPU+CPU+RAM+SSD plans
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --list-models

# 2. Run Sakura Inkling-2-Mini 131K benchmark with full-machine settings
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --bench --model Sakura --max-new 32

# 3. Start OpenAI/Anthropic API server (127.0.0.1:8092) with RAM squeeze + full-machine settings
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --serve --model Sakura --port 8092 --squeeze

# 4. Or launch Qwen3.8-27B SM120 directly via full-machine preset
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --serve --model qwen3.8-27b --port 8094
```
