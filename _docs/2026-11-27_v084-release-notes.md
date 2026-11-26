# Hakua 0.8.4 — release notes

## Scope
A local, unsigned Windows NSIS build of the Hakua fork. It carries the app shell (0.8.4) and
staged Control 0.6.3. The GPU engine (`strata.exe` + `strata-inkling2.exe`, 0.8.4, CUDA 13.5 /
SM120) is rebuilt from the committed native source for this release and bound by digest via
`native-build.json` (`sourceCommit=ee2645a5cad77ad1233908ce39421fee65d47c23`, no signing key).
Product and engine use the unified semantic version 0.8.4; Control remains independently
versioned at 0.6.3.

## Highlights (v0.8.3 → v0.8.4: Gen-M + CPU AVX2/Pool + Opt-in NVFP4 Transcoding)
- **CPU AVX2+FMA & Thread-Pool Optimizations** (Ryzen 5 4500, 6C/12T, 8 MB L3, 100% bit-exact):
  - `kq256_down_t1_q6k`, `kq256_gu_t1_q4k`, `kq256_down_t1_q4k`: zero YMM register spills on Zen 2
    (`<=15/16` YMM), deferred scale multiply, L1-folded operands, row-ahead `_MM_HINT_NTA` prefetch.
  - `q8k_quant_avx2`: 4x unrolled max-abs + single-pass 256-bit SIMD `bsums` reduction.
  - `ExpertPool::dep_task`: runs `native_quant_h` immediately on the last gate/up finisher while
    `sb.ff` is L1/L2-hot, eliminating `gu_left` spin and `quant` CAS contention.
  - `nvfp4_avx2.cpp` (`row_dot2_t1`) & `native_expert.cpp`: zero-spill 01/23 split and fast AVX2
    dispatch for mixed `Q4_K`/`Q5_K` gate/up + `NVFP4` down.
- **Opt-in Load-Time NVFP4 Down-Proj Transcoding & SM120 CUDA Optimizations**:
  - `--transcode-q6k-nvfp4` (`STRATA_TRANSCODE_Q6K_NVFP4=1`, default OFF): transcodes `Q6_K` and
    `Q8_0` down-proj experts to hardware `NVFP4` (type 40) on load with zero extra host RAM
    (**-1944 MiB**, +289 GPU experts on Sakura 98K).
  - `--transcode-down-nvfp4` (`STRATA_TRANSCODE_DOWN_NVFP4=1`, default OFF): transcodes
    `Q6_K`/`Q8_0`/`Q5_0`/`Q5_K` down-proj experts to `NVFP4` (**-2430 MiB**, +396 GPU experts,
    **32/32 exact v0.8.3 reference tokens**).
  - SM120 CUDA fixes: `k_combine_experts` & `k_f32_to_f16` `n4` grid sizing (cuts 75% idle CTAs),
    warp-ballot + prefix-sum parallelized `k_group_experts_miss_map`, Gen-M 10D ShinkaEvolve
    placement genome + `k_combine_experts_hybrid` shared-memory cache.

## Real-Machine Benchmark (Ryzen 5 4500 6C/12T + RTX 5060 Ti 16 GiB, Sakura 98K)
Command: `--max-context 98304 --kv-q8 --bench --chunk 512 --tokens 1..16 --max-new 32`

| Mode / VRAM | GPU Experts | Hits / Misses | pp (t/s) | tg (t/s) | cpu_ms | vs v0.8.3 Baseline |
|---|---:|---:|---:|---:|---:|---|
| v0.8.3 baseline (`11.5 GiB`) | 2329/3072 | 7316 / 1804 | 23.22 | 15.82 | 1196.2 | baseline |
| **v0.8.4 default (`11.5 GiB`)** | 2329/3072 | 7447 / 1673 | **71.04** | **19.08** | **815.4** | **pp +206% (3.06x), tg +20.6%, cpu_ms -31.8%** |
| v0.8.3 baseline (`8.5 GiB`) | 1735/3072 | 5732 / 3388 | 20.11 | 6.06 | 3862.8 | baseline |
| **v0.8.4 default (`8.5 GiB`)** | 1735/3072 | 5842 / 3278 | **23.65** | **10.21** | **2161.3** | **pp +17.6%, tg +68.5%, cpu_ms -44.0%** |
| **v0.8.4 `--transcode-q6k-nvfp4` (`11.5 GiB`)** | **2618/3072 (+289)** | **8088 / 1032** | **56.82** | **20.11** | **827.4** | **-1944 MiB, tg +27.1%** |
| **v0.8.4 `--transcode-down-nvfp4` (`11.5 GiB`)** | **2725/3072 (+396)** | **8414 / 706** | **43.48** | **19.73** | **718.2** | **-2430 MiB, tg +24.7%, cpu_ms -40.0%, 32/32 ref match** |

## Artifacts & Limits
- Installer: `Strata-0.8.4-windows-x64-setup.exe`, 127,400,344 bytes,
  SHA-256 `82b73955d62b297933fcc3db8a7b4c65bd494257362bb9d6d2610d46837793a0`.
- Rebuilt CUDA 13.5 SM120 engine (`0.8.4-windows-x86_64-cuda-cuda13`, manifest
  `b96de8d6182face0a5b87474c7c4e892179ee1a02f5bacc195b46d003b45044d`):
  - `strata.exe`: `38bb591864f69af8b48a074a2b12286e560993e454c9f4b681de27646d14d4cb`
  - `strata-inkling2.exe`: `3deab1a44a73fe536c110de3bf9cb2e719904c19110ad2254445650ac56861f6`
- `releaseQualified=false` is unchanged. Unsigned local build; no Windows Authenticode signature.
  Full-window inference, general/low-precision model quality, public search quality, and GPU
  concurrency remain unqualified. RAM/commit/disk floors are unchanged.
