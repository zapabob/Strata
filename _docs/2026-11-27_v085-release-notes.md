# Hakua 0.8.5 — release notes (Gen-N: SM120 Fusion and AVX2 Expert Offload)

## Scope
A local, unsigned Windows NSIS build of the Hakua fork carrying app shell 0.8.5, staged Control
0.6.3, and rebuilt CUDA 13.5 / SM120 engine 0.8.5 (`strata.exe` + `strata-inkling2.exe`) bound to
frozen native source `1c2e93e738b848bdff4402dc866504d355bb1c01` by `native-build.json` digest.

## Highlights (v0.8.4 → v0.8.5: Gen-N)
- **Riemann-zero-inspired admission heuristics (`riemann_rh.hpp`, `scripts/shinka_evolve_genn.py`)**:
  - Odlyzko 8-zero RH explicit-formula spectral phase (`rh_explicit_spectral_phase`,
    `rh_spectral_entropy_decay`) + RH-UCB cold-start admission (`rh_ucb_admission_bonus`) on top
    of real-machine-optimal Zeta/LeCaR/von-Koch constants.
- **SM120 GPU Kernel Fusion & Lightweight DMA (`inkling2_kernels.cuh`, `inkling2_engine.cu`)**:
  - 100% bit-exact fused `k_combine_shortconv_t1` & `k_combine_hybrid_shortconv_t1` eliminating
    **48 kernel launches and 48 `moe_raw` HBM round-trips per token** across all 48 layers.
  - Single `dma_pin[2]` double-buffer reuse across layers in `place_experts` (**load time -31% to
    -41%**) + tuned Windows pinned-RAM headroom (`head_b = 4096 MiB`, safely above 3 GiB floor)
    eliminating `SSD_mmap` spilling (`SSD_mmap = 0` across all 4 modes).
- **Lightweight Zero-Contention Pool & 4-Row Unrolled NVFP4 AVX2 (`pool.hpp`, `pool.cpp`, `nvfp4_avx2.cpp`, `kq_avx2.cpp`)**:
  - Per-worker `alignas(64) WorkerPark wparked_[i]` (zero locked-RMW wake/park contention), lazy
    Q2_0 `split_multi_q2_` + lazy `split_` + lazy-grow `split_multi_` (**-13.9 MiB RAM** upfront,
    decode stride 160 KiB → 96 KiB), and hoisted `now_ms()` out of host `drain()`.
  - Zero-spill 4-row unrolled `row_dot4_t1` (`<=13/16` YMM) + 2-line `_MM_HINT_NTA` prefetch in
    `nvfp4_avx2.cpp` and `kq256_down_t1_q5_0` / `kq256_down_t1_q8_0`.

## Sakura benchmark on the Ryzen 5 4500 and RTX 5060 Ti 16 GiB
Command: `--max-context 98304 --kv-q8 --bench --chunk 512 --tokens 1..16 --max-new 32`

| Mode (`VRAM`) | Load (s) | GPU / RAM / SSD | Hits / Misses | pp (t/s) | tg (t/s) | cpu_ms | Parity vs v0.8.3 ref | Delta vs v0.8.4 / v0.8.3 |
|---|---:|---|---:|---:|---:|---:|---|---|
| **Default `11.5 GiB`** | 124.95 | 2329 / 743 / **0** | 7416 / 1704 | 36.75 | 17.09 | 940.1 | **32/32 exact** | vs v0.8.3: **pp +58.3%, tg +8.0%, cpu_ms -21.4%** |
| **Default `8.5 GiB`** | 73.41 | 1735 / 1337 / **0** | 5827 / 3293 | **24.35** | 10.14 | **2045.4** | coherent | vs v0.8.4: **cpu_ms -5.4%**; vs v0.8.3: **tg +67.3%, cpu_ms -47.0%** |
| **`--transcode-q6k-nvfp4` `11.5 GiB`** | **98.58** (-41%) | **2618** / 454 / **0** | **8109** / 1011 | **60.01** | **26.11** | **462.0** | **32/32 exact** | vs v0.8.4: **tg +29.8%, cpu_ms -44.2%**; vs v0.8.3: **tg +65.0%** |
| **`--transcode-down-nvfp4` `11.5 GiB`** | **68.33** (-31%) | **2725** / 347 / **0** | **8414** / 706 | **44.02** | **26.59** | **288.4** | 29/32 exact | vs v0.8.4: **tg +34.8%, cpu_ms -59.8%**; vs v0.8.3: **tg +68.1%, cpu_ms -75.9%** |

The benchmark used 16 prompt tokens and generated 32 at a configured 98,304-token capacity. A full 98,304-token prefill and 131,072-token retrieval were outside this run. The combined changes were benchmarked together. The measurements do not isolate the admission heuristic or establish a result about the Riemann hypothesis.

Strata also lists registered SC117 SQ-10, SQ-15 and SQ-20 profiles under Inkling-2-Mini, with each profile loaded using its saved local runtime settings.


Inkling profiles with explicit SSD Expert caching receive a longer, bounded cold-start wait. The Host respects the ceiling of the installed Control.

## Artifacts and limits

The Windows installer and matching CUDA engine are separate assets. This candidate retains the resource floors and has eleaseQualified=false. The Windows installer is unsigned.
