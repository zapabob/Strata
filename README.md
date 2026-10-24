<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380">
  </picture>
</p>

<p align="center"><b>English</b> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.pt-BR.md">Português</a></p>

<h3 align="center">Strata — Spin(8) Triality KV Cache, TurboQuant CUDA Dialects & Native MoE Inference Engine</h3>

<p align="center">
  <b>Fork of <a href="https://github.com/Niko1221/Strata">Niko1221/Strata</a></b> · Spin(8) $\mathrm{Cl}(8,0)$ Triality Attention · Three-View Quantized KV Cache · Query-v3 `.prismq3` Sidecars · Full GUI & CLI Control
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2"><img src="https://img.shields.io/github/v/release/zapabob/Strata?include_prereleases&label=fork%20release" alt="Fork release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/zapabob/Strata" alt="MIT license"></a>
  <a href="https://github.com/zapabob/Strata/stargazers"><img src="https://img.shields.io/github/stars/zapabob/Strata?style=flat" alt="GitHub stars"></a>
</p>

---

## Overview of This Fork (`zapabob/Strata`)

**`zapabob/Strata`** is an advanced research and engineering fork of [Strata](https://github.com/Niko1221/Strata) (v0.2.2 / engine 0.1.47). In addition to running 125B-parameter Mixture-of-Experts models (**Qwen3.8-Flash-Next**, **Qwen3.6-35B-A3B**, **Gyro**, **Swift 1.5**, **NVFP4**) on a single PC by streaming experts across GPU VRAM, system RAM, and SSD, this fork introduces a complete **Spin(8) Triality & TurboQuant KV Cache stack** across the C++/CUDA engine, Python server, CLI, and Desktop/Web GUI:

1. **Spin(8) Triality & $\mathrm{Cl}(8,0)$ Orthogonal Transform Library ([`spin8/`](spin8/README.md))**
   - Built on the real octonion basis ($1, e_1, \dots, e_7$) and symmetric $\mathrm{Cl}(8,0)$ generators ($\Gamma_0, \dots, \Gamma_7$).
   - Decomposes 16×16 Clifford spinors by chirality into three 8-dimensional representations: **Vector ($V$)**, **Positive Half-Spin ($S_+$)**, and **Negative Half-Spin ($S_-$)**, satisfying the triality intertwiner $U \Gamma(v) U^\top = \Gamma(Rv)$.
   - Every rotation plan is mathematically audited before admission: Frobenius orthogonality error $E_F = \|M^\top M - I\|_F / \sqrt{8} \le 10^{-12}$, max Gram entry error $\le 10^{-12}$, and pivoted-LU signed log-determinant ($\operatorname{sign}=+1$, $|\log|\det|| \le 10^{-12}$).
   - Includes general power-of-two normalized Sylvester Hadamard transforms ($n = 1 \dots 1024$, including 8D Spin(8) sign masks and 128D Bonsai blocks) and a sticky runtime audit scheduler (`spin8_monitor`) that verifies invariants every 1,024 tokens or 60 seconds.

2. **Three-View Triality KV Cache & Asynchronous TurboQuant CUDA Dialects ([`tqcodec/`](tqcodec/README.md))**
   - **Physical CUDA Three-View Cache (`cache_cuda.cu`)**: Maintains three physically independent rotated Key arrays ($V, S_+, S_-$) and one shared quantized Value array per head, scored via single-pass online softmax with simplex consensus weights $(\alpha_0, \alpha_1, \alpha_2)$ and optional packed-sign Gaussian **QJL** residual sketch correction.
   - **Exact Asynchronous CUDA Dialects**:
     - `TQ4_1S` (4.25 bits/weight)
     - `TQ3_0S` (3.3125 bits/weight)
     - `PQ2_0` (2.50 bits/weight)
   - **VRAM Stack-Reservation Fix for SM120 (RTX 50-Series)**: Dynamic shared-memory execution (`65,536` bytes) in `audit_kernel` replaces per-thread `float f[128 * 128]` (64 KiB/thread) local arrays that previously caused CUDA to reserve **3.375 GiB (`3,623,878,656 B`)** of device stack memory at `tqc_cache_cuda_initialize`, freeing ~3.3 GiB of VRAM for the expert cache and enabling all three native views (`off`, `f32`, `compressed`) to run reliably on a 16 GiB GPU / 32 GiB RAM PC.

3. **Versioned Query-v3 Adapter & `.prismq3` Sidecars**
   - Implements a bounded rational tangent chart on the 7 skew generators derived from audited $\mathrm{Cl}(8,0)$ blocks, driven by a rank-8 controller on normalized queries ($Q$) prior to positional encoding (RoPE).
   - Supports zero-allocation fused CUDA execution (`query_v3_cuda.h`) and cryptographically bound `.prismq3` sidecars (`--query-v3-sidecar`) for models such as **Prism / TheTom (`qwen35-9b-thetom-q2kxl`)** and **Hikari / Bonsai (`bonsai-8b-prism-q1_0_g128`)**.

4. **Seamless End-to-End GUI, CLI & Control Integration**
   - **Desktop & Web GUI (`apps/host`)**: Configure **K cache type**, **V cache type** (`f16`, `tq3`, `tq3_spin8_hadamard`, `tq3_spin8_native`), **Spin(8) KV cache mode** (`off`, `f32`, `compressed`), **Spin(8) native config path**, and **Spin(8) native config SHA-256** directly under **Settings → GPU & memory**, backed by live preflight validation (`run-config-check.mjs`).
   - **CLI & Python Server (`strata_cli`, `strata_control`, `serve/server.py`)**: Pass `--cache-type-k`, `--cache-type-v`, `--spin8-mode`, `--spin8-native-config`, and `--spin8-native-sha256` via `strata launch --set ...` or `strata serve`, with pre-launch capsule and SHA-256 verification.

---

## Latest Fork Release: `v0.3.0-preview.20261024.2`

- **Release Page**: [GitHub Release `v0.3.0-preview.20261024.2`](https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2)
- **Combined Engine + GUI + Control Archive**: `Strata-0.3.0-preview.20261024.2-windows-x64-sm120-engine-gui.tar.7z`
  - **Size**: `412,311,508` bytes
  - **SHA-256**: `7639fb8ffb3c8fd13857a59c6b5d9d8b392c8b82a496442f0486a9405fd16e21`
  - **Engine (`strata.exe`) SHA-256**: `564e23b5bcd2b0670d0a2d82e7cd2c20cd5afedf85ddca7c653bea11403727db`
- **Previous CLI-Only Artifact**: [`v0.3.0-preview.20261024.1`](https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.1) · [Technical Release Notes](docs/releases/preview030.md) · [Triality PoC Notes](research/triality_poc/README.md)

### What Is Verified in `v0.3.0-preview.20261024.2`

| Component | Status | Verification Evidence |
| --- | --- | --- |
| **Native Windows CUDA Engine (`sm120`)** | **Verified** | Bounded Q2 (`Qwen3.8-Flash-Next-GSQ-RCO-Q2_0`) generation decoded `READY` and terminated on EOS (`exit 0`) across all three views: `--spin8-mode off`, `--spin8-mode f32`, and `--spin8-mode compressed` (`--vram-reserve-mib 10240`). |
| **`tqcodec` CUDA `audit_kernel` Fix** | **Verified** | Dynamic shared memory (`65,536` bytes) replaces 64 KiB thread-local arrays (`audit_local=0`, `audit_delta=0`), eliminating the 3.375 GiB CUDA stack-frame reservation; `tqc_cache_cuda_test.exe` (`28,068` checks) and `strata_spin8_native_owner_test.exe` (`17,361` checks) pass (`exit 0`). |
| **Host GUI & Preflight Checks** | **Verified** | `pnpm --dir apps/host typecheck` (0 errors), `pnpm --dir apps/host build`, and `node --test` (`19/19` tests passed across `native-settings`, `spin8-backend`, `kv-settings`, `kv-engine`). |
| **Control & Terminal CLI** | **Verified** | `pytest tests/terminal/test_profiles.py` (`21 passed`), `strata doctor --json` (`ok: true`), and full SHA-256 component resolution (`engine_component.resolve(..., full=True)`). |

> **Scope Notice:** `v0.3.0-preview.20261024.2` is an unsigned engineering preview for Windows x64 (`sm120` / CUDA 13.3). Default/off mode preserves upstream behavior (`cache_type_k=f16`, `cache_type_v=f16`, `spin8_mode=off`). Experimental Spin(8) modes (`f32`, `compressed`, `tq3_spin8_native`) are strictly opt-in and require a verified JSON capsule and matching SHA-256 digest.

---

## Quick Start (Fork Features)

### 1. Using the GUI (Desktop / Web Host)

1. Extract `Strata-0.3.0-preview.20261024.2-windows-x64-sm120-engine-gui.tar.7z` (extract the outer `.7z`, then extract the inner `.tar`), or overwrite-install into `%LOCALAPPDATA%\Programs\Strata` and `%LOCALAPPDATA%\Strata\components\engine\0.1.47-windows-x86_64-cuda-cuda13`.
2. Open **Settings → GPU & memory**.
3. Configure the KV Cache & Spin(8) parameters:
   - **K cache type (`cache_type_k`)**: `f16` (default), `tq3`, `tq3_spin8_hadamard`, or `tq3_spin8_native`
   - **V cache type (`cache_type_v`)**: `f16` (default), `tq3`, `tq3_spin8_hadamard`, or `tq3_spin8_native`
   - **Spin(8) KV cache mode (`spin8_mode`)**: `off` (default), `f32`, or `compressed`
   - **Spin(8) native config path (`spin8_native_config`)**: Absolute path to your verified Spin(8) JSON capsule (required when `spin8_mode` is `f32`/`compressed` or cache type is `tq3_spin8_native`)
   - **Spin(8) native config SHA-256 (`spin8_native_sha256`)**: 64-character hex SHA-256 digest of the capsule file

### 2. Using the `strata` CLI & Server

```powershell
# Default launch (upstream-compatible path)
strata launch --model q2_0 --yes --no-tui

# Launch with Hadamard-rotated TurboQuant 3-bit KV cache
strata launch --model q2_0 \
  --set cache_type_k=tq3_spin8_hadamard \
  --set cache_type_v=tq3_spin8_hadamard \
  --yes --no-tui

# Launch with verified Spin(8) native three-view capsule
strata launch --model q2_0 \
  --set cache_type_k=tq3_spin8_native \
  --set cache_type_v=tq3_spin8_native \
  --set spin8_mode=compressed \
  --set spin8_native_config=C:\path\to\capsule.json \
  --set spin8_native_sha256=<64-hex-sha256> \
  --yes --no-tui
```

### 3. Direct Native Engine Execution (`strata.exe`)

For low-level benchmarking and deterministic three-view verification with pre-tokenized inputs and a native pack:

```powershell
# Off-mode baseline
.\strata.exe --pack .\models\q2_0\native-pack `
  --native .\models\q2_0\Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00001-of-00002.gguf `
  --ple-gguf .\models\q2_0\Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00002-of-00002.gguf `
  --tokens-file .\examples\ready-tokens.txt --max-new 32 --max-context 256 `
  --mmap-experts --expert-cache auto --expert-profile .\data\expert-profile.bin `
  --prefill 32 --eos-ids 248044,248046 --spin8-mode off --check-logits --gpu 0 `
  --spec 2 --suffix-draft 0 --lookup-chain 0 --vram-reserve-mib 10240

# Compressed Spin(8) three-view mode with SHA-256 bound capsule
.\strata.exe --pack .\models\q2_0\native-pack `
  --native .\models\q2_0\Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00001-of-00002.gguf `
  --ple-gguf .\models\q2_0\Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00002-of-00002.gguf `
  --tokens-file .\examples\ready-tokens.txt --max-new 32 --max-context 256 `
  --mmap-experts --expert-cache auto --expert-profile .\data\expert-profile.bin `
  --prefill 32 --eos-ids 248044,248046 --spin8-mode compressed `
  --spin8-native-config .\capsules\q2_0-compressed-capsule.json `
  --spin8-native-sha256 <64-hex-sha256> `
  --check-logits --gpu 0 --spec 2 --suffix-draft 0 --lookup-chain 0 --vram-reserve-mib 10240
```

---

## Core Strata Capabilities & Hardware Requirements

Strata runs **[Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next)** (125B MoE) and **[Qwen3.6-35B-A3B](docs/QWEN36.md)** locally on a single PC, exposing OpenAI (`/v1/chat/completions`, `/v1/responses`) and Anthropic (`/v1/messages`) compatible endpoints for Claude Code, Codex CLI, OpenCode, and other coding agents.

### Hardware Requirements

**At least 32 GB of combined system RAM + GPU VRAM is required** (unified memory on Apple Silicon or AMD Ryzen AI Max).

| Hardware | Notes |
| --- | --- |
| **NVIDIA** GeForce RTX 20, 30, 40, 50 series (12 GB+ VRAM) | Primary CUDA target (`sm120` native Spin(8) preview tested on RTX 5060 Ti 16 GB & RTX 5090 32 GB). |
| **AMD** Radeon RX 6800+, RX 7000, RX 9000, Radeon AI PRO R9700 | [AMD HIP Guide](docs/AMD_HIP.md) |
| **Intel** Arc | [Intel Arc](docs/INTEL_ARC.md), [SYCL Engine](docs/INTEL.md) |
| **Apple Silicon Mac** (M1 or newer, macOS 15+) | [Mac Metal Guide](docs/MAC.md) |
| **AMD Ryzen AI Max (Strix Halo)** | [Strix Halo Guide](docs/STRIX_HALO.md) |

### Supported Model Tiers

| Combined Memory (RAM + VRAM) | Recommended Model | Description |
| --- | --- | --- |
| **28–32 GB** | **[Gyro-S](docs/GYRO.md)** (27.6 GB) or **[Coder](docs/MODELS.md#coder)** | Gyro-S fits tight memory budgets; Coder prunes half the experts for coding workloads. |
| **35–40 GB** | **[Swift 1.5](docs/MODELS.md#swift-15)** IQ2_XS (39.2 GB) or **Gyro-M** (35 GB) | Swift 1.5 uses shorter reasoning chains; Gyro-M nears IQ3_XXS quality with ~20% less GPU memory. |
| **48 GB** | **IQ3_XXS** (47.0 GB) | Higher precision than 2-bit quantizations. |
| **64 GB** | **IQ3_S** (54.8 GB) or **Q2_0** | Matches full-model benchmark accuracy; Q2_0 delivers peak decode speed (94 tok/s on RTX 5070). |
| **96 GB+** | **UD-IQ4_XS** (72 GB) to **Q8_0** (136 GB), **[NVFP4](docs/NVFP4.md)** | 4-bit to 8-bit tiers when all experts fit in system RAM. |

---

## Building and Testing This Fork from Source

### 1. Standalone `spin8` & `tqcodec` Libraries (CPU & CUDA)

```powershell
# Spin(8) CPU reference & tests
cmake -S spin8 -B build\spin8-cpu -G "Visual Studio 17 2022" -A x64 -DSPIN8_ENABLE_CUDA=OFF
cmake --build build\spin8-cpu --config Release
ctest --test-dir build\spin8-cpu -C Release --output-on-failure

# tqcodec CPU + CUDA + Spin(8) integration tests
cmake -S tqcodec -B build\tqcodec-cuda -G "Visual Studio 17 2022" -A x64 -DTQCODEC_ENABLE_CUDA=ON -DTQCODEC_SPIN8_TESTS=ON
cmake --build build\tqcodec-cuda --config Release
ctest --test-dir build\tqcodec-cuda -C Release --output-on-failure
```

### 2. Full Native CUDA Engine (`strata.exe`)

```powershell
cmake -S . -B build\engine-cuda -G "Visual Studio 17 2022" -A x64 -DSTRATA_CUDA=ON
cmake --build build\engine-cuda --config Release --target strata spin8_verify
```

### 3. Host Web UI, Node Server & Control Tests

```powershell
# Node host & GUI build + unit tests
pnpm --dir apps/host typecheck
pnpm --dir apps/host build
node --test apps/host/tests/native-settings.test.mjs apps/host/tests/spin8-backend.test.mjs apps/host/tests/kv-settings.test.mjs apps/host/tests/kv-engine.test.mjs

# Python terminal & control profile tests
py -3 -m pytest -p no:randomly tests/terminal/test_profiles.py
```

---

## Repository Structure (Fork Additions)

- [`spin8/`](spin8/README.md) — Standalone Spin(8) $\mathrm{Cl}(8,0)$ triality library, Sylvester Hadamard transforms, `spin8_monitor`, and `query_v3` CPU/CUDA adapters.
- [`tqcodec/`](tqcodec/README.md) — TurboQuant scalar codebooks, asynchronous CUDA dialects (`TQ4_1S`, `TQ3_0S`, `PQ2_0`), QJL residual sketches, calibration, orthogonal transport, and three-view CUDA KV cache (`cache_cuda.cu`).
- [`src/strata_native_cache_bridge.cpp`](src/strata_native_cache_bridge.cpp) & [`src/strata_native_session.cpp`](src/strata_native_session.cpp) — Native engine bridge binding Spin(8) capsules, memory guards, and three-view KV cache into Strata's inference loop.
- [`apps/host/server/native-settings.mjs`](apps/host/server/native-settings.mjs) & [`apps/host/server/run-config-check.mjs`](apps/host/server/run-config-check.mjs) — Host GUI schema and preflight verification for KV cache and Spin(8) settings.
- [`serve/server.py`](serve/server.py), [`strata_control/`](strata_control/profiles.py), [`strata_cli/`](strata_cli/cli.py) — Python API server and CLI integration for Spin(8) and TurboQuant flags.
- [`research/triality_poc/`](research/triality_poc/README.md) — Synthetic Linux CPU PoC and mathematical evaluation records.

---

## Credits & License

- **Fork Engineering (`zapabob/Strata`)**: Spin(8) $\mathrm{Cl}(8,0)$ triality cache, `tqcodec` CUDA dialects, Query-v3 `.prismq3` adapter integration, SM120 `audit_kernel` dynamic shared-memory optimization, and full-stack GUI/CLI controls.
- **Upstream Strata ([`Niko1221/Strata`](https://github.com/Niko1221/Strata))**: Three-tier MoE streaming engine, expert cache, speculative decoding, Desktop/Host app, and Terminal CLI.
- **Models & Compression**: [Qwen Team](https://huggingface.co/Qwen/Qwen3.8-Flash-Next), [ISTA-DASLab](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF), UkisAI (Swift 1.5), agentionai (Gyro), Unsloth, and [llama.cpp / ggml](https://github.com/ggml-org/llama.cpp).
- **License**: Released under the [MIT License](LICENSE). Bundled CUDA/cuBLAS and Microsoft Visual C++ redistributables in release archives retain their respective vendor terms.
