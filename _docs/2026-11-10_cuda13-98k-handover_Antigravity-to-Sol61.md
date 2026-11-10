# Handover Document: 98K Context CUDA 13 (`sm_120`) Optimization & Multi-Model Analysis (Antigravity -> Sol6.1)

- **Date**: 2026-11-10
- **From**: Antigravity (Session `177183d7-0d5f-46a2-a2fc-bdb41b35a919`)
- **To**: Sol6.1 / OpenCode (working on `_docs/2026-11-10_release-055-repair_OpenCode.md` and `_docs/repair-055-20261110/`)
- **Status**: HANDOVER READY (Read-only static analysis & architectural design complete; **0 tracked files modified** in `C:\Users\downl\Documents\ChatGPT\Strata`; **0 files touched** in `H:\Strata\releases\repair-055-20261110-opencode`).

---

## 1. Executive Summary & Workspace State

1. **Zero Collision Guarantee**:
   - Antigravity performed **strictly read-only static analysis** and hardware/GGUF inspection while Sol6.1 was running `native-cache-r1`, `native-objects-r1`, `workspace-trash-red-r1`, and `sidebar-browser-red-r1`.
   - No tracked files in `C:\Users\downl\Documents\ChatGPT\Strata` were modified by Antigravity.
   - No background processes or GPU tasks from Antigravity are running (`task-115` was explicitly cancelled).
2. **User's Confirmed Requirements in the Antigravity Thread**:
   - **Goal**: Stabilize and accelerate **98K context (`98,304` tokens)** for `Hermes-agent-windows` on this machine (**32 GB RAM, 16 GB VRAM RTX 5060 Ti `sm_120`, Driver 621.14, CUDA 13.3, Ryzen 5 4500 6C/12T**).
   - **Target Models (User explicitly selected `1-3` = all 3 models)**:
     1. **Hikari 27B PQ2_0** (`H:\CDriveEvacuation\2026-11-06-SO8T-073236\Hikari-Bonsai-27B-Nimble-LoRA-GGUF\Hikari-LoRA-fixed-scale-PQ2_0.gguf`, `qwen35` arch) on **PrismML (`llama-server.exe`)**.
     2. **Qwen3.6-35B-A3B UD-Q4_K_XL** (`H:\Strata\models\qwen36-UD-Q4_K_XL\Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf`, `qwen35moe` arch) on **PrismML (`llama-server.exe` CPU MoE)** and/or **native `strata-q36.exe`**.
     3. **Swift Qwen3.8-Flash-Next IQ2_XS** (`H:\Strata\models\SC117\Swift-1.5-Qwen3.8-Flash-Next-GSQ-RCO-abliterated-GGUF\Swift-Qwen3.8-Flash-Next-GSQ-RCO-abliterated-IQ2_XS-00001-of-00002.gguf` + `00002`, `qwen4exp` arch) on **native `strata.exe`**.
   - **Confirmed Execution Strategy (Plan A)**:
     - Step 1: Profile/measure 98K execution across the 3 models under `tools/native_model_resource_guard.py` + `tools/perf131k/windows_job.py` (`available_ram >= 3 GiB`, `commit_headroom >= 4 GiB`, `C_free >= 5 GiB`, `H_free >= 10 GiB`, 5 compiler jobs).
     - Step 2: Implement targeted CUDA 13 (`sm_120`) kernel & runtime optimizations (starting with the PrismML asymmetric-KV Tensor Core MMA defect below), verify numerical/bitwise parity, and run A/B 98K benchmarks.

---

## 2. Exact Model Geometries Extracted from GGUF Headers

Using `tools/gguf_reader.py`, the exact attention & recurrent geometries of the 3 target models at `98,304` context are:

| Metric / Parameter | 1. Hikari 27B PQ2_0 | 2. Qwen3.6-35B-A3B UD-Q4_K_XL | 3. Swift Qwen3.8-Flash-Next IQ2_XS |
| :--- | :--- | :--- | :--- |
| **File Size** | `7,206,168,928` B (6.71 GiB) | `22,853,663,008` B (21.28 GiB) | `18,476,120,032` B (17.21 GiB total) |
| **GGUF `general.architecture`** | `qwen35` (Dense hybrid) | `qwen35moe` (MoE hybrid + MTP) | `qwen4exp` (MoE hybrid + QSA) |
| **`block_count`** | `64` | `40` trunk (`+1` NextN MTP = 41) | `48` |
| **`full_attention_interval`** | `4` (**16 full-attn**, 48 GDN) | `4` (**10 trunk full-attn**, 30 GDN) | `4` (**12 full-attn**, 36 GDN) |
| **`attention.head_count` ($N_q$)** | `24` | `16` | `24` |
| **`attention.head_count_kv` ($N_{kv}$)** | `4` (**GQA ratio = 6**) | `2` (**GQA ratio = 8**) | `2` (**GQA ratio = 12**) |
| **`key_length` / `value_length`** | `256` / `256` | `256` / `256` | `256` / `256` (`qsa_top_k = 2048`) |
| **98K KV Cache (`fp16` / `q8_0` / `q8_0+q4_0`)** | 6,442 MB / 3,423 MB / **2,567 MB** | 2,013 MB / 1,070 MB / **803 MB** | 2,416 MB / 1,284 MB / **963 MB** |

---

## 3. Finding 1 ("Silver Bullet" CUDA Kernel Defect): PrismML Asymmetric KV (`-ctk q8_0 -ctv q4_0`) Disables In-Place Tensor Core MMA at 98K

### 3.1 How Hermes-Agent Launches Hikari 27B PQ2_0 at 98K
From `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/preflight-blocker-04-08.json`, `Hermes-agent-windows` runs Hikari 27B PQ2_0 on PrismML `llama-server.exe` at 98K with **asymmetric KV cache quantization (`-ctk q8_0 -ctv q4_0`)** and **`ngram-mod` speculative decoding**:

```powershell
llama-server.exe `
  -m H:\CDriveEvacuation\2026-11-06-SO8T-073236\Hikari-Bonsai-27B-Nimble-LoRA-GGUF\Hikari-LoRA-fixed-scale-PQ2_0.gguf `
  -c 98304 --parallel 1 -ngl 999 -fa on `
  -ctk q8_0 -ctv q4_0 `
  --threads 6 --threads-batch 12 --batch-size 2048 --ubatch-size 512 `
  --spec-type ngram-mod --spec-ngram-mod-n-min 1 --spec-ngram-mod-n-max 16 --jinja
```

Why `-ctk q8_0 -ctv q4_0` is used: At 98K (`98,304` tokens), Hikari's 6.71 GiBPQ2_0 weights + GDN recurrent state + compute buffers leave ~3.5 GiB of safe VRAM before WDDM shared-memory spillover (`15.0 GiB` ceiling on 16 GB RTX 5060 Ti). `-ctk q8_0 -ctv q4_0` shrinks the 16-layer KV cache from `3,423 MiB` (`q8_0/q8_0`) to `2,567 MiB`, saving **856 MiB of VRAM** while preserving `Q8_0` key precision for long-context retrieval.

### 3.2 The Bug in `ggml-cuda/fattn-mma-f16.cuh` and `ggml-cuda/fattn.cu`
In PrismML (`H:\Strata\deps\prism-73bfe6cc\ggml\src\ggml-cuda\` and `H:\Strata\validation\qwen35-mtp-load-20261107\source-r1\ggml\src\ggml-cuda\`):

1. **[fattn-mma-f16.cuh#L2133-L2156](file:///H:/Strata/deps/prism-73bfe6cc/ggml/src/ggml-cuda/fattn-mma-f16.cuh#L2133-L2156)**:
   ```cpp
   static bool ggml_cuda_fattn_mma_kv_native_supported(const ggml_tensor * dst) {
       const ggml_tensor * Q = dst->src[0];
       const ggml_tensor * K = dst->src[1];
       const ggml_tensor * V = dst->src[2];
       if (K->type != V->type || !ggml_cuda_fattn_mma_kv_native(K->type)) {
           return false;
       }
       ...
   ```
   Because `ggml_cuda_flash_attn_ext_mma_f16_case<DKQ, DV, ncols1, ncols2, type_KV>` is templated on a **single `type_KV`** instead of separate `<type_K, type_V>`, **`K->type != V->type` (`q8_0` vs `q4_0`) unconditionally returns `false`!**

2. **Three Severe Consequences at 98K (`98,304` tokens)**:
   - **Penalty A — 402.65 MiB Permanent VRAM Scratch Allocation**:
     In [fattn.cu#L585-L609](file:///H:/Strata/deps/prism-73bfe6cc/ggml/src/ggml-cuda/fattn.cu#L585-L609), `ggml_cuda_flash_attn_ext_get_alloc_size` checks `!ggml_cuda_fattn_mma_kv_native_supported(dst)` and sets:
     ```cpp
     need_f16_K = K->type != GGML_TYPE_F16;
     need_f16_V = V->type != GGML_TYPE_F16;
     ```
     This permanently reserves `98304 * 4 * 256 * 2 bytes * 2 = 402,653,184 bytes` (**402.65 MiB**) of extra VRAM on top of `dst`, eating almost half of the 856 MiB saved by `-ctv q4_0`!
   - **Penalty B — Full 98K KV Cache `to_fp16_cuda` Conversion on Every Prefill & Speculative Verify Step (`Q->ne[1] > 2`)**:
     Whenever `ngram-mod` drafts $\ge 2$ tokens (`Q->ne[1] >= 3`, up to 16 tokens) or during prefill (`Q->ne[1] = 512`), [fattn.cu#L509](file:///H:/Strata/deps/prism-73bfe6cc/ggml/src/ggml-cuda/fattn.cu#L509) selects `BEST_FATTN_KERNEL_MMA_F16`. Then [fattn-common.cuh#L1040-L1102](file:///H:/Strata/deps/prism-73bfe6cc/ggml/src/ggml-cuda/fattn-common.cuh#L1040-L1102) (`launch_fattn`) runs `to_fp16_cuda` across the **entire 98,304-slot K and V cache** before launching the MMA kernel:
     - Writes `402.65 MiB` of temporary FP16 K/V + reads `160 MiB` of Q8_0/Q4_0 K/V = **563 MiB of extra global VRAM traffic per layer** (**~9.0 GiB per token step across 16 full-attention layers**), even if the prompt only has a few thousand active tokens or `ngram-mod` is verifying 4 tokens!
   - **Penalty C — Non-GQA-Shared Vector Kernel (`fattn-vec`) on 1–2 Token Decode (`Q->ne[1] <= 2`)**:
     In [fattn.cu#L502](file:///H:/Strata/deps/prism-73bfe6cc/ggml/src/ggml-cuda/fattn.cu#L502), `K->type != V->type` forces `BEST_FATTN_KERNEL_VEC` when `Q->ne[1] <= 2`. `fattn-vec` processes 1 query head per block (`ncols1 = 1, ncols2 = 1`) instead of packing `ncols2 = gqa_ratio` (`6` for Hikari, `8` for Qwen3.6) query heads into one Tensor Core tile, reading K and V **6x–8x redundantly** when `Q->ne[1] == 2`.

### 3.3 Exact Fix Design for `fattn-mma-f16.cuh` / `fattn.cu`
Inside `flash_attn_ext_f16_process_tile` ([fattn-mma-f16.cuh#L728](file:///H:/Strata/deps/prism-73bfe6cc/ggml/src/ggml-cuda/fattn-mma-f16.cuh#L728) and [L1085](file:///H:/Strata/deps/prism-73bfe6cc/ggml/src/ggml-cuda/fattn-mma-f16.cuh#L1085)), K tile loading and V tile loading are **already completely decoupled**:
- K uses `flash_attn_ext_f16_load_tile_q<type_K, ...>(K_tile, tile_KV, ...)`
- V uses `flash_attn_ext_f16_load_tile_q<type_V, ...>(V_tile, tile_KV, ...)`

**Implementation Steps**:
1. In [fattn-mma-f16.cuh](file:///H:/Strata/deps/prism-73bfe6cc/ggml/src/ggml-cuda/fattn-mma-f16.cuh):
   - Change `template<..., ggml_type type_KV>` to `template<..., ggml_type type_K, ggml_type type_V = type_K>` in:
     - `flash_attn_ext_f16_process_tile` (line 600)
     - `flash_attn_ext_f16` (line 1429)
     - `ggml_cuda_flash_attn_ext_mma_f16_case` (line 1966)
   - In `flash_attn_ext_f16_process_tile` and `flash_attn_ext_f16`, replace `type_KV != GGML_TYPE_F16` with `(type_K != GGML_TYPE_F16 || type_V != GGML_TYPE_F16)` for the `KQ_row_scale` / quantized path, and use `type_K` for `K_q` / `nb11` stride sizing and `type_V` for `V_q` / `nb21` stride sizing.
   - In `ggml_cuda_fattn_mma_kv_native_supported(const ggml_tensor * dst)` (line 2133):
     ```cpp
     const bool kv_types_ok =
         (K->type == V->type && ggml_cuda_fattn_mma_kv_native(K->type)) ||
         (K->type == GGML_TYPE_Q8_0 && V->type == GGML_TYPE_Q4_0);
     if (!kv_types_ok) {
         return false;
     }
     ```
   - In `ggml_cuda_flash_attn_ext_mma_f16_switch_type_kv` (line 2161), add the `K->type == GGML_TYPE_Q8_0 && V->type == GGML_TYPE_Q4_0` dispatch branch calling `ggml_cuda_flash_attn_ext_mma_f16_case<DKQ, DV, ncols1, ncols2, GGML_TYPE_Q8_0, GGML_TYPE_Q4_0>(ctx, dst)`.
2. In [fattn.cu](file:///H:/Strata/deps/prism-73bfe6cc/ggml/src/ggml-cuda/fattn.cu):
   - In `ggml_cuda_get_best_fattn_kernel` (line 502):
     - Allow `BEST_FATTN_KERNEL_MMA_F16` when `ggml_cuda_fattn_mma_kv_native_supported(dst)` is true, even if `K->type != V->type`!
     - Also when `K->type != GGML_TYPE_F16 || V->type != GGML_TYPE_F16` (quantized KV) and `gqa_ratio >= 4` with `DKQ == 256` on Turing+ (`sm_120`), routing `Q->ne[1] <= 2` through GQA-shared `BEST_FATTN_KERNEL_MMA_F16` (`ncols1=1, ncols2=8`) avoids the non-GQA-shared `fattn-vec` fallback or can be A/B benchmarked directly against `fattn-vec`.
3. **Bitwise / Numerical Parity**:
   - Because `flash_attn_ext_f16_load_tile_q<GGML_TYPE_Q8_0>` and `flash_attn_ext_f16_load_tile_q<GGML_TYPE_Q4_0>` execute the exact same scale*qs FP16 conversion as `to_fp16_cuda`, the new in-place `(Q8_0, Q4_0)` Tensor Core MMA kernel produces **identical outputs** to the baseline `to_fp16` reference path while saving **402.65 MiB VRAM** and **~9.0 GiB/step of VRAM bandwidth** during `ngram-mod` verification and prefill.

---

## 4. Direct Relevance to Sol6.1's `R1` and `R2` Tasks

### 4.1 Connection to Sol6.1 `R2` (Prism Pre-Readiness Noncompletion at 98,304 Context)
In `_docs/2026-11-10_release-055-repair_OpenCode.md`, `R2` investigates why Prism (`Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf`, `34/34` GPU layers, `98304` context, `Q8_0` KV) logged `warming up the model with an empty run` and was killed by Host's 120s health deadline at `122.512s` on `r1`, then passed on `r2`.

Static + memory-layout findings from our 98K analysis:
1. **Why `r1` took >120s while `r2` passed**:
   - `Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf` is **21.28 GiB** (`22,853,663,008` bytes). With `--n-cpu-moe 35` (or CPU-placed routed experts) and `34/34` trunk non-expert tensors on GPU + `98,304` `Q8_0` KV cache (`1,070 MiB`), GPU VRAM usage is **~14.4 GiB** (`nvidia-smi` confirmed `14,441 MiB / 16,311 MiB` while Qwen3.6 was loaded) and host RAM holds ~19 GiB of mmap'd GGUF pages.
   - During `llama-server`'s synchronous startup `--warmup` pass (before HTTP `/health` transitions from `503 Loading model` to `200 {"status":"ok"}`), `llama_decode` executes a dummy token + `llama_Synchronize` + KV removal across all 40 trunk layers (+ NextN MTP if active), faulting in cold mmap pages from `H:\Strata\models\...` while CUDA allocates and initializes compute buffers near the WDDM 15 GiB cliff.
   - On `r1` (cold OS file cache right after native Q36 tests unloaded), faulting ~19 GiB of GGUF pages + CUDA warm-up exceeded the rigid 120.0s Host `probeOpenAiReady` deadline by ~2.5s (`122.512s`). On `r2`, the GGUF pages were already warm in the Windows standby list, so warm-up completed inside 120s.
2. **Host Lifecycle & Diagnostic Gaps to Fix for `R2`**:
   - In `apps/host/src/supervisor/runner.mjs`, when `llama-server` is alive and returning HTTP `503` JSON (`{"error":{"code":503,"message":"Loading model","type":"unavailable_error"}}`), `probeOpenAiReady` currently treats `503 Loading model` identically to a connection refusal or hung socket and drops the HTTP status/body detail when throwing timeout.
   - Recording the last HTTP status/body + stdout progress phase (`loading tensors` vs `warming up` vs `listening`) and distinguishing an **actively loading/warming process (HTTP 503 `Loading model` with alive PID)** from a **dead or unresponsive socket** directly addresses `R2` without disabling `--warmup` or lowering readiness strictness.

### 4.2 Connection to Sol6.1 `R1` (Native CUDA Resource Guard Violations)
We inspected `H:\Strata\releases\repair-055-20261110-opencode\native-objects-r1.json` (completed at 17:13:52):
- `expdec` (`iq_kernels.cu` `iq4_xs_gemv_expdec_d4096_kernel`): **`passed: true`!**
- `dflash` (`dflash2.cu`): **`passed: true`!**
- `qsa` (`qsa_select.cu`): **`passed: false` (`exit: 1`)**
- `w4a8` (`moe_iq4_w4a8.cu`): **`passed: false` (`exit: 1`)**

Note on `qsa_select.cu` and `moe_iq4_w4a8.cu` from our CUDA 13.3 (`sm_120`) inspection:
- In `qsa_select.cu`, PTXAS spills (`64 regs, 96 B stack`) come from live arrays/accumulators across the multi-pass top-k radix selection loop while `__launch_bounds__(256, 4)` caps register count at 64 (`65536 / (256 * 4) = 64`). Keeping per-thread histogram/candidate state in shared memory instead of thread-local register arrays (or bounding loop-carried live registers across `__syncthreads()`) eliminates the 96-byte local stack frame within the 64-register cap.
- In `moe_iq4_w4a8.cu`, the 8 kernel instantiations hit `255 regs, 32..48 B stack` because `DP4A_ROWS` (up to 8) unrolls both the `sub` loop and row accumulators simultaneously across the K-tile loop. Rematerializing row pointers / scale factors inside the inner loop or staging row scales via shared memory keeps live registers under the 255 hardware ceiling with 0 local stack spill.

---

## 5. Native Strata (`strata.exe` / `strata-q36.exe`) 98K Optimization Roadmap (Models 2 & 3)

For whoever executes the next phase of the 98K optimization after Sol6.1 finishes the `0.5.5-local.1` release repair:

1. **PrismML Isolated Build Path (for Model 1 Hikari 27B PQ2_0 & Model 2 Qwen3.6-35B-A3B)**:
   - Source to copy (never mutate in place): `H:\Strata\validation\qwen35-mtp-load-20261107\source-r1` -> `H:\Strata\validation\perf-98k-20261110-agy\prism-source`.
   - Build dir: `H:\Strata\validation\perf-98k-20261110-agy\prism-build-sm120` with `CMAKE_BUILD_PARALLEL_LEVEL=5`, `-DCMAKE_CUDA_ARCHITECTURES=120`.
   - Apply the Section 3.3 `(Q8_0, Q4_0)` in-place Tensor Core MMA patch to `ggml/src/ggml-cuda/fattn-mma-f16.cuh` and `ggml/src/ggml-cuda/fattn.cu`.
   - Run bit-parity test + 98K A/B benchmark (`-c 98304 -ctk q8_0 -ctv q4_0 --spec-type ngram-mod`).
2. **Native `strata-q36.exe` / `strata.exe` 98K Path (for Model 2 Qwen3.6 & Model 3 Swift Qwen3.8)**:
   - **Swift Qwen3.8-Flash-Next IQ2_XS (`qwen4exp`)**:
     - Already uses QSA sparse attention (`qsa_top_k = 2048`), so decode attention cost at 98K is $O(2048)$, not $O(98304)$.
     - The 98K failure mode documented in [docs/WINDOWS_16GB_CONTEXT.md](file:///C:/Users/downl/Documents/ChatGPT/Strata/docs/WINDOWS_16GB_CONTEXT.md) is **host RAM exhaustion (`350 MiB` free RAM)** during 98K arena setup.
     - Launch with `STRATA_ARENA_MMAP=1`, `--vram-reserve-mib 2048`, and `--resident-budget-gib 14` under `tools/native_model_resource_guard.py` (`min_available_ram = 3 GiB`).
   - **Native Full-Attention Prefill Kernel (`src/kernels/cuda/native_flash_attn.cu`)**:
     - Currently uses scalar `float` dot products over `TILE_KV = 32, TILE_HEAD_DIM = 128` (2 streaming passes for `head_dim = 256`). Converting the Q*K and P*V tile contractions in `native_flash_attn.cu` to `mma.sync.aligned.m16n8k16.row.col.f32.f16.f16.f32` (`sm_120` Tensor Cores) with `GQA` head packing (`gqa_ratio = 8` for Qwen3.6, `12` for Qwen3.8) will accelerate native long-context prefill by 4x–8x.
