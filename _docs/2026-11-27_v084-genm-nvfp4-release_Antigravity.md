# Hakua v0.8.4 Implementation & Release Log (Gen-M + CPU AVX2/Pool + Opt-in NVFP4 Transcoding)

- **Date**: 2026-11-27
- **Implementer**: Antigravity (Swarm: `@nvfp4-opt`, `@cpu-simd-opt`, `@bench-verifier`, `@release-ops`)
- **Target Hardware**: AMD Ryzen 5 4500 (6C/12T AVX2+FMA+F16C, 8 MB L3), 32 GiB RAM, NVIDIA RTX 5060 Ti 16 GiB (Blackwell SM120a, CUDA 13.5.37)
- **Version Unification**: Product `0.8.4`, Engine `0.8.4`, Control `0.6.3` (`releaseQualified=false`, unsigned local build)

## 1. Engineering Changes Summary

### 1.1 CPU AVX2+FMA & Thread-Pool Optimizations (`@cpu-simd-opt`, 100% bit-exact)
- `engine/src/kernels/cpu/kq_avx2.cpp` & `engine/include/strata/kernels/cpu/kq_avx2.hpp`:
  - `kq256_down_t1_q6k`: audited bit-exact against `dot_q6_K_q8_K`; eliminated ~10 YMM register spills on Zen 2 (`<=15/16` YMM) via `sumi = -q8sclsub`, deferred `d0`/`d1` after the `j`-loop, L1-folded `y[i].qs` & shuffle masks, sequenced `b1`/`b2`, and row-ahead `_MM_HINT_NTA` prefetch (`r+2, r+3`).
  - `kq256_gu_t1_q4k` & `kq256_down_t1_q4k`: deferred scale multiplies, folded `get_scale_shuffle_k4` into `vpshufb`, single-instruction `_mm256_permute2x128_si256` scale broadcast, 3-line row-ahead NTA prefetch.
- `engine/src/kernels/cpu/iq_avx2.cpp`:
  - `q8k_quant_avx2`: 4x unrolled max-abs (bit-exact including NaN) + single-pass 256-bit SIMD `bsums` reduction from packed `p8`.
- `engine/src/kernels/cpu/pool.cpp`:
  - `ExpertPool::dep_task`: executes `native_quant_h` immediately on the last gate/up finisher (`gu_left.fetch_sub(1, acq_rel) == 1`) while `sb.ff` is L1/L2-warm, eliminating `gu_left` spin and `quant` CAS contention.
- `engine/src/kernels/cpu/nvfp4_avx2.cpp`:
  - `row_dot2_t1`: sequential 01/23 sub-block split (`<=12/16` YMM, zero spills, bit-exact).
- `engine/src/kernels/cpu/native_expert.cpp`:
  - Dropped `&& f.tail_off == 0` guard on `kq256_gu_t1_q4k`/`q5k` & `kq256_down_t1_*` so mixed `Q4_K`/`Q5_K` gate/up + `NVFP4` down preserves fast AVX2 `T==1` kernels.

### 1.2 Opt-in Load-Time NVFP4 Transcoding & SM120 CUDA Kernels (`@nvfp4-opt`)
- `engine/src/inkling2/inkling2_engine.cu`:
  - Added opt-in `--transcode-q6k-nvfp4` (`STRATA_TRANSCODE_Q6K_NVFP4=1`, default OFF): transcodes `Q6_K` (14) and `Q8_0` (8) down-proj experts on load to hardware `NVFP4` (type 40) with zero extra host RAM (`-31.4%` on `Q6_K`, `-47.1%` on `Q8_0`).
  - Added opt-in `--transcode-down-nvfp4` (`STRATA_TRANSCODE_DOWN_NVFP4=1`, default OFF): transcodes `Q6_K`/`Q8_0`/`Q5_0`/`Q5_K` down-proj experts to `NVFP4` (type 40), packing per-expert `s_down = E_amax / (6 * 448)` into `tail_off + 8`.
  - Fixed `k_combine_experts` and `k_f32_to_f16` launch grids to `n4 = N >> 2` (eliminating 75% idle CTAs, 100% bit-exact).
  - Integrated ShinkaEvolve Gen-M 10D placement genome + post-prefill 192-swap burst + `engine/include/strata/math/riemann_rh.hpp`.
- `engine/src/inkling2/inkling2_kernels.cuh`:
  - Parallelized `k_group_experts_miss_map` with warp-ballot + prefix-sum scan (bit-exact ascending expert ID order).
  - `k_combine_experts_hybrid` shared-memory cache (100% bit-exact `fmaf` order).

## 2. Build, Parity & Real-Machine Benchmark Verification (`@bench-verifier`)

### 2.1 Build Verification (`H:\Strata\build\engine-083c`, Release, `-j 5`, CUDA 13.5.37 SM120)
- `strata.exe` (`strata 0.8.4`) & `strata-inkling2.exe`: **0 errors, 0 new warnings** in all modified files.
- Final `0.8.4` binary digests:
  - `strata.exe`: `38bb591864f69af8b48a074a2b12286e560993e454c9f4b681de27646d14d4cb`
  - `strata-inkling2.exe`: `3deab1a44a73fe536c110de3bf9cb2e719904c19110ad2254445650ac56861f6`

### 2.2 Benchmark Results (`Sakura-Inkling-2-Mini-Uncensored-Q4_K_M.gguf`, 98K)
Command: `--max-context 98304 --kv-q8 --bench --chunk 512 --tokens 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16 --max-new 32`

| Mode / VRAM | GPU Experts | Hits / Misses | pp (t/s) | tg (t/s) | cpu_ms | vs v0.8.3 Baseline |
|---|---:|---:|---:|---:|---:|---|
| v0.8.3 baseline (`11.5 GiB`) | 2329/3072 | 7316 / 1804 | 23.22 (689.2 ms) | 15.82 (1960.0 ms) | 1196.2 | baseline |
| **v0.8.4 default (`11.5 GiB`)** | 2329/3072 | 7447 / 1673 | **71.04** (225.2 ms) | **19.08** (1624.6 ms) | **815.4** | **pp +206% (3.06x), tg +20.6%, cpu_ms -31.8%** |
| v0.8.3 baseline (`8.5 GiB`) | 1735/3072 | 5732 / 3388 | 20.11 (795.5 ms) | 6.06 (5114.8 ms) | 3862.8 | baseline |
| **v0.8.4 default (`8.5 GiB`)** | 1735/3072 | 5842 / 3278 | **23.65** (676.5 ms) | **10.21** (3035.1 ms) | **2161.3** | **pp +17.6%, tg +68.5%, cpu_ms -44.0%** |
| **v0.8.4 `--transcode-q6k-nvfp4` (`11.5 GiB`)** | **2618/3072 (+289)** | **8088 / 1032** | **56.82** (281.6 ms) | **20.11** (1541.4 ms) | **827.4** | **12 Q8_0 layers -> NVFP4 (-1944 MiB), tg +27.1%** |
| **v0.8.4 `--transcode-down-nvfp4` (`11.5 GiB`)** | **2725/3072 (+396)** | **8414 / 706** | **43.48** (368.0 ms) | **19.73** (1571.4 ms) | **718.2** | **24 layers -> NVFP4 (-2430 MiB), tg +24.7%, cpu_ms -40.0%, 32/32 exact ref tokens** |

### 2.3 Parity Verification
- CPU AVX2/pool (`#8`) and CUDA grid/miss-map (`#9`) are **32/32 bit-exact identical** to pre-#8/#9 Gen-M at `11.5 GiB`.
- Default v0.8.4 vs v0.8.3 differs only at a near-tie argmax (token 10) due to Gen-M's improved GPU/CPU placement (`hits 7316 -> 7447` at 11.5 GiB; `5732 -> 5842` at 8.5 GiB). `--transcode-down-nvfp4` (88.7% GPU residency) reproduces all **32/32** v0.8.3 reference tokens identically.

## 3. Packaging, Verification & Release Evidence (`@release-ops`)
- **Version bumps (`0.8.3` -> `0.8.4`)**: `VERSION`, `app/host/package.json`, `app/desktop/package.json`, `app/desktop/src-tauri/Cargo.toml`, `docs/data/release.json`, `engine/CMakeLists.txt` (`CONTROL_VERSION` unchanged at `0.6.3`).
- **Frozen native source snapshot**: `H:\Strata\build\native-source-084`, commit `ee2645a5cad77ad1233908ce39421fee65d47c23`.
- **Engine component package**: `H:\Strata\releases\v084-engine-clean\0.8.4-windows-x86_64-cuda-cuda13` (628.5 MiB, 6 files: `strata.exe`, `strata-inkling2.exe`, `native-build.json`, `cublas64_13.dll`, `cublasLt64_13.dll`, `engine-component.json` SHA-256 `b96de8d6182face0a5b87474c7c4e892179ee1a02f5bacc195b46d003b45044d`).
- **Release integrity gate (`verify-release.mjs`)**: PASSED (`Release payload verified: Hakua 0.8.4, engine 0.8.4, Control 0.6.3`, verified twice: pre-build and `beforeBundleCommand`).
- **UI build**: Node `24.22.3`, `STRATA_PUBLIC_PACKAGE=1`, Vite `6.4.6` (17.98s).
- **NSIS installer**: `H:\Strata\releases\Strata-0.8.4-windows-x64-setup.exe` (`127,400,344` bytes, SHA-256 `82b73955d62b297933fcc3db8a7b4c65bd494257362bb9d6d2610d46837793a0`), `H:\Strata\releases\SHA256SUMS-v084.txt`.
- **Local silent overwrite install (`/S /UPDATE`)**: Pending user execution/approval — the unsandboxed permission prompt timed out after 60s without user response. Run manually:
  ```powershell
  Start-Process -FilePath 'H:\Strata\releases\Strata-0.8.4-windows-x64-setup.exe' -ArgumentList '/S','/UPDATE' -Wait
  Copy-Item -Recurse -Force 'H:\Strata\releases\v084-engine-clean\0.8.4-windows-x86_64-cuda-cuda13' "$env:LOCALAPPDATA\Strata\components\engine\0.8.4-windows-x86_64-cuda-cuda13"
  ```
- **Limits**: `releaseQualified=false`, unsigned local Windows NSIS installer and unsigned digest-bound engine component; RAM/commit/disk floors unchanged.
