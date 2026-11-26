# Phase XIII / XIV — Inkling-2-Mini Heretic Mode B (NVFP4 + Dense PQ2_0 + Strata Native) Progress Report

- **Date**: 2026-11-25 (JST)
- **Implementer**: Antigravity
- **Target Hardware**: AMD Ryzen 5 4500 (6C/12T Zen 2 AVX2) + 32 GiB DDR4 + NVIDIA GeForce RTX 5060 Ti 16 GiB (Blackwell SM120, CUDA 13.5) + NVMe SSD
- **Status**: In Progress (`/goal` active — proceeding through full verification, official-model-card benchmarks, refusal evaluation, Phase XIV evolutionary optimisation, Hugging Face upload, and local overwrite release)
- **Release Qualification**: `releaseQualified=false` (local unsigned build; production Hermes default model remains unchanged until all acceptance gates pass)

---

## 1. Verified Artefacts Completed to Date

| Artefact | Path | Size | SHA-256 (prefix) | Status |
|---|---|---|---|---|
| **Mode B Primary GGUF** (`48/48 NVFP4` + `Q6_K` LM-Head & Embed + `PQ2_0` Dense Attn) | `H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\ablated-models\Inkling-2-Mini-Heretic-ModeB-NVFP4-DensePQ2.gguf` | `13.831 GiB` (`14,851,359,264 B`) | `ed25fe3fc139f67e` | **Built & Verified (752/752 tensors, 96/96 visit scales `max_abs_err=0.0`)** |
| **Mode A Alternative GGUF** (100% VRAM-resident Hybrid) | `H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\ablated-models\Inkling-2-Mini-Heretic-Agentic-128K-Hybrid.gguf` | `11.148 GiB` (`11,969,973,600 B`) | `8216456321154936` | **Built & Verified (726/726 tensors, 96/96 visit scales `max_abs_err=0.0`)** |
| **Strata Native Engine** (`strata-inkling.exe`) | `H:\Strata\builds\strata-inkling-native-pq2-sm120\strata-inkling.exe` | — | — | **Rebuilt & Verified (`build=GGUF-NVFP4`, 2D `PQ2_0` dense support added)** |

---

## 2. Verification Receipts (Mode B Primary)

1. **Rust `strata-gguf-preflight`** (`H:\Strata\evidence\phase13-agentic-hybrid\modeB_rust_preflight.json`):
   - `ok=true`, `architecture="inkling2_loop"`, `tensor_count_reported=752`, `tensor_count_scanned=752`, `payload_extent_valid=true`.
   - Tensor types: `NVFP4: 48` (all 48 MoE expert banks), `F32: 502` (including 48/48 NVFP4 `.scale` tensors + routers/norms), `BF16: 56`, `PQ2_0: 120` (all 24 layers × 5 dense attention projections), `Q6_K: 26` (`output.weight`, `token_embd.weight`, 24 × `attn_rel`).
   - Activation-weighted relative MSE vs all-`PQ2_0` balanced baseline: `21.553927 -> 0.192905` (`-99.11%` / `111.73x`). *(Reconstruction error alone is not used to claim source-equivalent quality; downstream logit KL, tool-calling, coding, and long-context evaluations are required.)*
2. **48 Layer Visits NVFP4 Scale Parity** (`H:\Strata\evidence\phase13-agentic-hybrid\modeB_48visit_scales_verified.json`):
   - Verified via `prism-loop-scales.exe`: all `96` records (`48 visits × 2 projections × 128 experts = 12,288` scale values) match the GGUF `NVFP4` `.scale` tensors with **`max_abs_err = 0.0`**, **`0` mismatches**, **`passed = true`**.
3. **Strata Native Engine Compatibility**:
   - Patched `engine/src/inkling2/ink_gguf_loader.h::validate_pq2_basis` to accept 2D foldable `PQ2_0` dense weights alongside 3D expert banks and handle `strata::GgufFile`'s 64-item metadata array cap.
   - Verified `strata-inkling.exe --info`: `arch=inkling2_loop format=gguf build=GGUF-NVFP4 layers=24 visits=48 hidden=2304 vocab=200058 experts=128 eos=200006`.
4. **Repository Hygiene & Upstream Sync**:
   - All 6 linked worktrees cleaned and unified onto `main` (`engine-067` local diff safely archived to `H:\Strata\backups\engine-067-archive\`).
   - Cherry-picked all 3 Control bugfixes from `upstream/main` `v0.2.21.1` (`2fdbdb56d`, `688999468`, `2ddda80a6`) with zero conflicts; all 29 HIP window/free unit tests pass.

---

## 3. Active & Remaining Gates Before Release / HF Upload

- **Running now (`task-2022`)**: Separate native logit KL / NLL / Top-1 comparison against (a) pre-quantisation Heretic BF16 (`phase7/ablated/core/reference`) and (b) official BF16 (`phase7/official/core/reference`).
- **Queued next**:
  1. Paired `PQ2_0` vs `Q6_K` LM-Head ablation on identical Mode B hidden states (`heretic_lm_head_ablation.py`, `-ub 256` fix applied).
  2. Mode B Strict acceptance suite: `131K / 139K / 147K` VRAM + Windows shared GPU memory + RAM offload profiling, tool calling (unconstrained/constrained + Hermes multi-turn), executable Python + `nvcc --ptx` CUDA coding, actual `131,072`-token input + 3/3 needle retrieval inside `139,264` ctx.
  3. Official model card benchmarks (MMLU zero-shot, Apex 2025, AIME 2025) and Refusal behaviour (Direct `none` vs Thinking-on `high`).
  4. Phase XIV evolutionary optimisation on Ryzen 5 4500 + RTX 5060 Ti (`phase14_evolutionary_tuner.py`) -> `Mode B Strict` & `Mode B Fast` configs.
  5. King's English `README.md` (model card) & Hugging Face upload + readback verification (`zapabobouj/Inkling-2-Mini-Heretic-Agentic-128K-GGUF`).
  6. Push `origin/main` + local overwrite install & release verification.
