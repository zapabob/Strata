<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380">
  </picture>
</p>

<p align="center"><b>English</b> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.pt-BR.md">Português</a></p>

<h3 align="center">Strata — Spin(8) Triality KV Cache, DeepSeek-V4.1 Uncensored, Arbitrary GGUF Loader & Long-Term Memory</h3>

<p align="center">
  <b>Fork of <a href="https://github.com/Niko1221/Strata">Niko1221/Strata</a></b> · Upstream Integrated · Spin(8) $\mathrm{Cl}(8,0)$ Triality Attention · DeepSeek-V4.1-Flash MLA Uncensored · Arbitrary Content-Addressed GGUF · Hermes & Hakua Long-Term Memory · 32GB RAM Optimized
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2"><img src="https://img.shields.io/github/v/release/zapabob/Strata?include_prereleases&label=fork%20release" alt="Fork release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/zapabob/Strata" alt="MIT license"></a>
  <a href="https://github.com/zapabob/Strata/stargazers"><img src="https://img.shields.io/github/stars/zapabob/Strata?style=flat" alt="GitHub stars"></a>
</p>

---

## Overview of This Fork (`zapabob/Strata`)

**`zapabob/Strata`** is an advanced engineering fork of [Strata](https://github.com/Niko1221/Strata) synchronized with latest upstream v0.2.4.2 / engine 0.1.49.2. In addition to running 125B-parameter Mixture-of-Experts models (**Qwen3.8-Flash-Next**, **Qwen3.6-35B-A3B**, **Gyro**, **Swift 1.5**, **NVFP4**) on a single PC by streaming experts across GPU VRAM, system RAM, and SSD, this fork introduces **Spin(8) Triality KV Cache**, **DeepSeek-V4.1-Flash uncensored derivatives**, **arbitrary content-addressed GGUF loading**, and **long-term agent memory**:

1. **Spin(8) Triality & $\mathrm{Cl}(8,0)$ Orthogonal Transform Library ([`spin8/`](spin8/README.md))**
   - Built on the real octonion basis ($1, e_1, \dots, e_7$) and symmetric $\mathrm{Cl}(8,0)$ generators ($\Gamma_0, \dots, \Gamma_7$).
   - Decomposes 16×16 Clifford spinors by chirality into three 8-dimensional representations: **Vector ($V$)**, **Positive Half-Spin ($S_+$)**, and **Negative Half-Spin ($S_-$)**, satisfying the triality intertwiner $U \Gamma(v) U^\top = \Gamma(Rv)$.
   - Every rotation plan is mathematically audited before admission: Frobenius orthogonality error $E_F = \|M^\top M - I\|_F / \sqrt{8} \le 10^{-12}$, max Gram entry error $\le 10^{-12}$, and pivoted-LU signed log-determinant ($\operatorname{sign}=+1$, $|\log|\det|| \le 10^{-12}$).
   - Normalized Sylvester Hadamard transforms ($n = 1 \dots 1024$) and a sticky runtime audit scheduler (`spin8_monitor`) that verifies invariants every 1,024 tokens or 60 seconds.

2. **Three-View Triality KV Cache & Asynchronous TurboQuant CUDA Dialects ([`tqcodec/`](tqcodec/README.md))**
   - **Physical CUDA Three-View Cache (`cache_cuda.cu`)**: Maintains three physically independent rotated Key arrays ($V, S_+, S_-$) and one shared quantized Value array per head, scored via single-pass online softmax with simplex consensus weights $(\alpha_0, \alpha_1, \alpha_2)$ and optional packed-sign Gaussian **QJL** residual sketch correction.
   - **Exact Asynchronous CUDA Dialects**: `TQ4_1S` (4.25 bpw), `TQ3_0S` (3.3125 bpw), and `PQ2_0` (2.50 bpw).
   - **VRAM Stack-Reservation Fix for SM120 (RTX 50-Series)**: Dynamic shared-memory execution (`65,536` bytes) in `audit_kernel` replaces per-thread `float f[128 * 128]` local arrays that previously reserved 3.375 GiB of device stack memory, freeing ~3.3 GiB of VRAM for the expert cache.

3. **DeepSeek-V4.1-Flash-1017 Uncensored Derivatives & Dedicated MLA Backend ([`strata_control/backends/dsv41.py`](strata_control/backends/dsv41.py))**
   - Native support for Multi-Head Latent Attention (MLA) projection matrices via dedicated `strata-dsv41` backend.
   - Pre-qualified candidate models: ISTA baseline, Kiwimaker Maya-S abliterated slot replacement recipe, and AtomicChat standalone uncensored bundle.
   - Automatic refusal-direction steering suppression for pre-abliterated models to prevent double-ablation distortion, while strictly isolating Qwen steering vectors and $\mathrm{Cl}(8,0)$ triality cache from DeepSeek latent projections.

4. **Arbitrary Content-Addressed ModelBundle & Deterministic Router ([`strata_control/model_bundle.py`](strata_control/model_bundle.py))**
   - Bounded header parser ($\le 16$ MiB) with tensor dimension overflow protections ($\operatorname{rank} \le 4, \operatorname{dim} \le 2^{30}$, mitigating GHSA-vgg9-87g3-85w8).
   - Streaming SHA-256 identity digest and drift detection to prevent runtime tampering or accidental file substitution.
   - Deterministic local routing (`strata-dsv41`, `strata-native`, `prism`, `llama-cpp`) with **strictly forbidden cloud fallback** (100% offline local privacy).

5. **Hermes Agent & Hakua Composite Long-Term Memory ([`tools/strata_memory_mcp.py`](tools/strata_memory_mcp.py))**
   - Standard MCP stdio server + CLI integrating:
     - `SOUL.md`: Hakua parental alignment and core personality directive with automatic timestamped backup.
     - `MEMORY.md`: Structured episodic working memory using `§ [category] YYYY-MM-DD: Title` format.
     - Hermes Agent SQLite memory store (`~/.hermes/ebbinghaus_memory.db` with ~5,000 indexed memories).
     - Hakua Composite Memory (`~/.hakua-memory`).
   - Automatic injection into chat sessions via `apps/host/server/memory.mjs` and `getEffectiveSystemPrompt()`.

6. **32GB RAM / 16GB VRAM Zero-VRAM Drafter Lifecycle**
   - Tested and verified on Windows 11 with 32 GB RAM + NVIDIA GeForce RTX 5060 Ti 16 GB (`sm_120`).
   - Planned host RAM $\le 24.0$ GiB, OS reserve headroom $\ge 4.0$ GiB, and VRAM budget $\le 14.0$ GiB.
   - Dynamic speculative drafter auto-unload on host memory pressure, deallocating drafter buffers to zero VRAM without terminating the main inference process.

7. **Versioned Query-v3 Adapter & `.prismq3` Sidecars**
   - Implements a bounded rational tangent chart on the 7 skew generators derived from audited $\mathrm{Cl}(8,0)$ blocks, driven by a rank-8 controller on normalized queries ($Q$) prior to positional encoding (RoPE).
   - Supports zero-allocation fused CUDA execution (`query_v3_cuda.h`) and cryptographically bound `.prismq3` sidecars (`--query-v3-sidecar`) for models such as **Prism / TheTom (`qwen35-9b-thetom-q2kxl`)** and **Hikari / Bonsai (`bonsai-8b-prism-q1_0_g128`)**.

---

## Release & Upstream Integration: `v0.3.0` Upstream Integrated Edition

- **Upstream Baseline Merged**: `7dd5cf18e68c639a8773e096c5c79f971ea2a9f5` (v0.2.4.2 / engine 0.1.49.2)
- **GUI Security Hardening**: `c487c875d05075113965bc61d822b27179f70639` (TOCTOU settings fix)
- **Fork Baseline**: `ddc8f9e19cafb981ed91caaab0992ca814e6eca9` (Retaining all F01–F11 contracts)
- **Qualification Documents**:
  - Model Acceptance: [_docs/qa/model-acceptance.json](_docs/qa/model-acceptance.json)
  - Benchmark Report: [bench/custom-gguf/report.md](bench/custom-gguf/report.md)
  - Release Qualification: [_docs/releases/custom-gguf-qualification.md](_docs/releases/custom-gguf-qualification.md)

### Verification Summary

| Component | Status | Verification Evidence |
| --- | --- | --- |
| **Native Windows CUDA Engine (`sm120`)** | **Verified** | Q2_0 baseline (6.7 tok/s, 61.7% GPU hit rate) running stably on port 18501 without interference during tests. |
| **`tqcodec` Dynamic Shared Memory** | **Verified** | Replaced 64 KiB/thread stack arrays, saving 3.375 GiB VRAM on RTX 5060 Ti 16 GB. |
| **Arbitrary GGUF & DeepSeek Router** | **Verified** | Four-tier qualification passed across ISTA baseline, Maya-S replacement, and AtomicChat standalone models. |
| **Long-Term Memory MCP & GUI** | **Verified** | `tests/test_strata_memory.py` passed (5/5); automatic `SOUL.md` injection into prompt generation verified. |
| **Regression Suite** | **Verified** | **71/71 Python tests passed** (`pytest -p no:randomly`), **13/13 Node host tests passed** (`apps/host`). |

---

## Quick Start (Fork Features)

### 1. Using the GUI (Desktop / Web Host)

1. Open **Settings → GPU & memory**.
2. Configure the KV Cache & Spin(8) parameters:
   - **K cache type (`cache_type_k`)**: `f16` (default), `tq3`, `tq3_spin8_hadamard`, or `tq3_spin8_native`
   - **V cache type (`cache_type_v`)**: `f16` (default), `tq3`, `tq3_spin8_hadamard`, or `tq3_spin8_native`
   - **Spin(8) KV cache mode (`spin8_mode`)**: `off` (default), `f32`, or `compressed`
   - **Spin(8) native config path (`spin8_native_config`)**: Absolute path to your verified Spin(8) JSON capsule
   - **Spin(8) native config SHA-256 (`spin8_native_sha256`)**: 64-character hex SHA-256 digest of the capsule file
3. Navigate to **Models** to preview and load custom GGUF bundles or DeepSeek derivatives with content verification.

### 2. Using the `strata` CLI & Model Qualification

```powershell
# Default launch (upstream-compatible path)
py -3 strata.py launch --model q2_0 --yes --no-tui

# Launch with Hadamard-rotated TurboQuant 3-bit KV cache
py -3 strata.py launch --model q2_0 `
  --set cache_type_k=tq3_spin8_hadamard `
  --set cache_type_v=tq3_spin8_hadamard `
  --yes --no-tui

# Qualify an arbitrary GGUF bundle under 32GB RAM constraint
py -3 tools/qualify_model_bundle.py --manifest path\to\model.gguf --architecture dsv41 --dialect standard

# Check and lock upstream integration status
py -3 tools/check_upstream_cut.py
```

### 3. Using Long-Term Memory (Hermes / Hakua / SOUL.md / Memory.md)

```powershell
# Check memory system status
py -3 tools/strata_memory_mcp.py status

# Recall relevant memories by semantic query
py -3 tools/strata_memory_mcp.py recall --query "Strata optimization"

# Store an episodic memory
py -3 tools/strata_memory_mcp.py remember --text "Optimized audit_kernel with dynamic shared memory" --category tech

# Display active SOUL.md directive
py -3 tools/strata_memory_mcp.py soul
```

---

## Core Strata Capabilities & Hardware Requirements

Strata runs **[Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next)** (125B MoE), **[DeepSeek-V4.1-Flash](docs/DEEPSEEK41.md)**, and **[Qwen3.6-35B-A3B](docs/QWEN36.md)** locally on a single PC, exposing OpenAI (`/v1/chat/completions`, `/v1/responses`) and Anthropic (`/v1/messages`) compatible endpoints.

### Hardware Requirements

**At least 32 GB of combined system RAM + GPU VRAM is required.**

| Hardware | Notes |
| --- | --- |
| **NVIDIA** GeForce RTX 20, 30, 40, 50 series (12 GB+ VRAM) | Primary CUDA target (`sm120` verified on RTX 5060 Ti 16 GB & RTX 5090 32 GB). |
| **AMD** Radeon RX 6800+, RX 7000, RX 9000, Radeon AI PRO R9700 | [AMD HIP Guide](docs/AMD_HIP.md) |
| **Intel** Arc | [Intel Arc](docs/INTEL_ARC.md), [SYCL Engine](docs/INTEL.md) |
| **Apple Silicon Mac** (M1 or newer, macOS 15+) | [Mac Metal Guide](docs/MAC.md) |
| **AMD Ryzen AI Max (Strix Halo)** | [Strix Halo Guide](docs/STRIX_HALO.md) |

---

## Building and Testing from Source

```powershell
# 1. Run all regression test suites (Python)
$env:PYTHONPATH="."
py -3 -m pytest tests/terminal/test_custom_model_cli.py tests/contracts tests/security tests/models tests/backends tests/resources tests/dsv41 tests/runtime tests/steering tests/mutations tests/packaging tests/test_strata_memory.py -v -p no:randomly

# 2. Run Node.js Host Tests
$env:NODE_OPTIONS=""
Push-Location apps/host
node tests/custom-gguf.test.mjs
node tests/run-config-check.test.mjs
Pop-Location

# 3. Check Upstream Cut & Integration Lock
py -3 tools/check_upstream_cut.py
```

---

## Repository Structure (Fork Additions)

- [`spin8/`](spin8/README.md) — Standalone Spin(8) $\mathrm{Cl}(8,0)$ triality library, Sylvester Hadamard transforms, and runtime audit scheduler.
- [`tqcodec/`](tqcodec/README.md) — TurboQuant CUDA dialects (`TQ4_1S`, `TQ3_0S`, `PQ2_0`), QJL residual sketch, and three-view CUDA KV cache.
- [`strata_control/`](strata_control/) — ModelBundle resolver, streaming SHA-256 identity, 32GB RAM memory planner, and deterministic backend router.
- [`adapters/upstream/`](adapters/upstream/README.md) — Bridges for native attention and isolated DeepSeek steering.
- [`tools/strata_memory_mcp.py`](tools/strata_memory_mcp.py) — Hermes Agent & Hakua Composite long-term memory MCP server.
- [`tools/qualify_model_bundle.py`](tools/qualify_model_bundle.py) — Four-tier model bundle qualification CLI.
- [`tools/check_upstream_cut.py`](tools/check_upstream_cut.py) — Upstream cut verification and integration integrity lock.

---

## Credits & License

- **Fork Engineering (`zapabob/Strata`)**: Spin(8) $\mathrm{Cl}(8,0)$ triality cache, `tqcodec` CUDA dialects, DeepSeek-V4.1 uncensored integration, arbitrary content-addressed GGUF loader, Hermes/Hakua long-term memory, and full-stack GUI/CLI controls.
- **Upstream Strata ([`Niko1221/Strata`](https://github.com/Niko1221/Strata))**: Three-tier MoE streaming engine, expert cache, speculative decoding, Desktop/Host app, and Terminal CLI.
- **Models & Compression**: [Qwen Team](https://huggingface.co/Qwen/Qwen3.8-Flash-Next), [DeepSeek AI](https://huggingface.co/deepseek-ai), [ISTA-DASLab](https://huggingface.co/ISTA-DASLab), Kiwimaker, AtomicChat, and [llama.cpp / ggml](https://github.com/ggml-org/llama.cpp).
- **License**: Released under the [MIT License](LICENSE).
