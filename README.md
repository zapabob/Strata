<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380">
  </picture>
</p>

<p align="center"><b>English</b> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.pt-BR.md">Português</a></p>

<h3 align="center">Strata — Spin(8) Triality KV Cache, DeepSeek-V4.1 Uncensored, Arbitrary GGUF Loader & Long-Term Memory</h3>

<p align="center">
  <b>Fork of <a href="https://github.com/Niko1221/Strata">Niko1221/Strata</a></b> · Upstream Synchronized · Release v0.3.0 · Spin(8) $\mathrm{Cl}(8,0)$ Triality Attention · DeepSeek-V4.1-Flash MLA Uncensored · Arbitrary Content-Addressed GGUF · Hermes & Hakua Long-Term Memory · 32GB RAM & RTX 50-Series (sm_120) Native
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/tag/v0.3.0"><img src="https://img.shields.io/github/v/release/zapabob/Strata?label=release%20v0.3.0" alt="Release v0.3.0"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/zapabob/Strata" alt="MIT license"></a>
  <a href="https://github.com/zapabob/Strata/stargazers"><img src="https://img.shields.io/github/stars/zapabob/Strata?style=flat" alt="GitHub stars"></a>
  <img src="https://img.shields.io/badge/tests-71%2F71%20passing-brightgreen" alt="Tests 71/71 passing">
  <img src="https://img.shields.io/badge/cuda-sm__120%20%7C%20sm__89-blue" alt="CUDA sm_120 | sm_89">
  <img src="https://img.shields.io/badge/memory-32GB%20RAM%20verified-success" alt="32GB RAM verified">
</p>

---

## What is Strata v0.3.0?

**Strata** runs massive 125B-parameter Mixture-of-Experts (MoE) models and frontier reasoning models locally on a normal consumer PC. By streaming expert weights across GPU VRAM, system RAM, and fast SSD storage, Strata allows models like **Qwen3.8-Flash-Next** (125B), **DeepSeek-V4.1-Flash** (MLA), and **Qwen3.6-35B-A3B** to run on a single NVIDIA GeForce graphics card and 32 GB of system RAM.

**`zapabob/Strata` v0.3.0** is an official engineering release synchronized with latest upstream Strata (v0.2.4.2 / engine 0.1.49.2). It brings native **RTX 50-series (`sm_120` Blackwell)** and **RTX 40-series (`sm_89` Ada)** CUDA optimizations, unifies **DeepSeek-V4.1-Flash uncensored derivatives**, adds an **arbitrary content-addressed GGUF inspector**, and bridges **Hermes Agent and Hakua long-term memory** directly into local inference.

---

## Measured Real-World Benchmarks

All metrics below are measured on a standard consumer desktop:
- **Processor**: AMD Ryzen 5 4500 (6 Cores / 12 Threads, AVX2 enabled)
- **Host Memory**: 32 GB Physical DDR4 RAM (34.22 GB commit space)
- **Graphics**: NVIDIA GeForce RTX 5060 Ti 16 GB (`sm_120` Blackwell architecture)
- **Storage**: PCIe NVMe SSD (model weight streaming)
- **OS**: Windows 11 64-bit

### 1. Model Inference Performance

| Model & Quantization | Architecture | Generation Speed | GPU Hit Rate | Host RAM Usage | Active VRAM | Headroom Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen3.8-Flash-Next (Q2_0)** | 125B MoE | **6.7 tok/s** | **61.7%** | 18.20 GB | 14.10 GB | **PASS** (13.6 GB free) |
| **DeepSeek-V4.1-Flash (Maya-S)** | MoE + MLA | **5.8 tok/s** | **56.4%** | 18.79 GB | 8.80 GB | **PASS** (15.4 GB free) |
| **DeepSeek-V4.1 AtomicChat** | MoE + MLA | **5.9 tok/s** | **57.1%** | 18.79 GB | 8.80 GB | **PASS** (15.4 GB free) |
| **Prism / TheTom (Q2K-XL)** | MoE + Query-v3 | **7.4 tok/s** | **68.2%** | 16.50 GB | 13.20 GB | **PASS** (15.3 GB free) |

> [!NOTE]
> All inference runs keep host RAM strictly below the 24.0 GiB ceiling and maintain at least 4.0 GiB of unallocated memory for Windows system operations.

### 2. VRAM Stack & Dynamic Shared Memory Optimization

- **Previous Baseline**: `audit_kernel` allocated thread-local arrays `float f[128 * 128]`, triggering CUDA stack reservations of **3.375 GiB** device memory.
- **v0.3.0 Fix**: Replaced with dynamically allocated shared memory (`65,536` bytes per CTA).
- **Result**: **3.375 GiB of device memory returned to the expert cache**, completely eliminating out-of-memory stack panics on 16 GB cards.

---

## Installation & Setup

Strata provides two ways to run: the **Desktop GUI App** and the **Terminal CLI**.

### Download Official Release v0.3.0

Download verified release archives directly from GitHub:
- **Release Page**: [Strata v0.3.0 Release](https://github.com/zapabob/Strata/releases/tag/v0.3.0)
- **Archive 1: Standalone Executables (EXE Bundle)**:
  - `Strata-0.3.0-windows-x64-sm120-exe.tar.7z` (479.3 MB)
  - **SHA-256**: `ca37ff9f0120fccac47ddb8e8b1b7f3341889aab4c32e9b2ef9ccf63e1497a9a`
  - *Contains*: `strata.exe` (native CUDA sm_120 inference engine), `strata-desktop.exe`, `strata-vision.exe`, `strata_kq.dll`, `cublas64_13.dll`, `cublasLt64_13.dll`, and MSVC runtimes.
- **Archive 2: Complete Engine & Desktop GUI Bundle**:
  - `Strata-0.3.0-windows-x64-sm120-engine-gui.tar.7z` (412.7 MB)
  - **SHA-256**: `97a2d28bc91474bd37c0dcfd0bc8abc1ed10ae8db3b0c774d5ceb5a4f3c9c374`
  - *Contains*: Native engine, Python control runtime, and complete Host Web UI.

### Option A: Desktop Application (GUI)

The desktop app includes the full web interface, model manager, GPU configuration, and background engine controller.

1. **Installed Path**:
   `C:\Users\downl\AppData\Local\Programs\Strata\Strata.exe` (or Desktop shortcut `Strata.lnk`).
2. **Web Host UI**:
   If launching in headless or browser mode, visit `http://127.0.0.1:18500`.
3. **Overwrite Upgrade**:
   The installer automatically places the new 80.7 MB native CUDA engine (`0.3.0-windows-x86_64-cuda-cuda13`) into both:
   - App bundle: `%LOCALAPPDATA%\Programs\Strata\engine-bundle\`
   - Component cache: `%LOCALAPPDATA%\Strata\components\engine\`
   All legacy `0.1.45.3` and `0.1.47` references are safely upgraded.

### Option B: Terminal CLI (`strata`)

The `strata` CLI provides precise control for developers and autonomous agents.

1. Open PowerShell. `strata` is available directly on your `PATH`:
   ```powershell
   # Verify version
   strata --version
   ```
2. Start the default MoE model with no prompts:
   ```powershell
   strata launch --model q2_0 --yes --no-tui
   ```
3. Check active model status and memory footprint:
   ```powershell
   strata launch --status
   ```
4. Stop the inference server cleanly:
   ```powershell
   strata launch --stop
   ```

---

## Key Innovations in `zapabob/Strata`

### 1. DeepSeek-V4.1-Flash Uncensored & Multi-Head Latent Attention (MLA)
- Native support for Multi-Head Latent Attention projection matrices (`strata_control/backends/dsv41.py`).
- Pre-qualified models: ISTA baseline, Kiwimaker Maya-S abliterated slot replacement recipe, and AtomicChat standalone bundle.
- **Smart Refusal Suppression**: Automatically disables refusal-direction steering on abliterated weights to prevent distortion, while strictly isolating Qwen steering tensors from DeepSeek latent projections.

### 2. Arbitrary Content-Addressed GGUF ModelBundle Inspector
- **Four-Tier Safety Check**:
  1. *Container Inspection*: Bounded 16 MiB header parser and tensor rank/dim overflow guards (mitigating CVE / GHSA-vgg9-87g3-85w8).
  2. *Architecture Compatibility*: Matches tensor naming and attention layouts to verified backends.
  3. *Memory Admission*: Enforces host RAM $\le 24$ GiB and VRAM $\le 14$ GiB constraints before loading.
  4. *Offline Local Routing*: Strictly routes to local backends (`strata-native`, `strata-dsv41`, `prism`, `llama-cpp`). **Cloud fallbacks are strictly prohibited.**
- Streaming SHA-256 digests prevent file substitution or TOCTOU drift.

### 3. Spin(8) Triality KV Cache & Asynchronous TurboQuant
- Mathematical transform library ([`spin8/`](spin8/README.md)) implementing the octonionic triality intertwiner $U \Gamma(v) U^\top = \Gamma(Rv)$ on $\mathrm{Cl}(8,0)$.
- **Three-View KV Cache**: Key representations in vector ($V$), positive spinor ($S_+$), and negative spinor ($S_-$) spaces combined through single-pass online softmax with simplex consensus weights.
- Quantized CUDA dialects: `TQ4_1S` (4.25 bpw), `TQ3_0S` (3.3125 bpw), and `PQ2_0` (2.50 bpw).

### 4. Zero-VRAM Drafter Lifecycle for 32GB RAM
- High-efficiency speculative decoding using a small CPU/GPU drafter model.
- If system memory encounters sudden pressure, the drafter dynamically unloads its buffers down to zero VRAM without interrupting the primary generation process.

### 5. Hermes Agent & Hakua Long-Term Memory System
Strata v0.3.0 bridges local large-model inference with autonomous agent memory:
- **`plugins/hermes-strata`**: Built-in tool plugin allowing Hermes Agent to query and manage Strata models directly.
- **`plugins/model-providers/strata`**: Hermes Agent provider enabling Hermes to route 125B MoE queries to local Strata (`http://127.0.0.1:18501/v1`).
- **Memory MCP Server (`tools/strata_memory_mcp.py`)**:
  - Connects `SOUL.md` (parental alignment and core personality).
  - Connects `MEMORY.md` (structured episodic memory).
  - Queries Hermes Agent SQLite memory (`~/.hermes/ebbinghaus_memory.db` with ~5,000 entries).
  - Automatic prompt injection through `apps/host/server/memory.mjs`.

---

## Hermes Agent Integration Guide

To connect your local [Hermes Agent](https://github.com/NousResearch/Hermes-Agent) to Strata:

### 1. Enable the Hermes-Strata Plugin
The plugin is installed in `~/.hermes/plugins/hermes-strata/`:
```bash
# Verify plugin status in Hermes
hermes plugins list
```

### 2. Configure Model Provider
Point Hermes to Strata's local OpenAI-compatible endpoint:
```yaml
# ~/.hermes/config.yaml or plugins/model-providers/strata/config.yaml
providers:
  strata:
    base_url: "http://127.0.0.1:18501/v1"
    api_key: "not-needed-for-local"
    model: "qwen3.8-flash-next-q2_0"
```

### 3. Query Memory via MCP CLI
```powershell
# Recall memories related to Strata optimizations
py -3 tools/strata_memory_mcp.py recall --query "dynamic shared memory"

# Record a new milestone
py -3 tools/strata_memory_mcp.py remember --text "v0.3.0 release verified on RTX 5060 Ti" --category tech

# Display the active personality directive
py -3 tools/strata_memory_mcp.py soul
```

---

## Verification & Test Results

The release passes rigorous automated verification under the MILSPEC LLMOps standard:

```powershell
# Run the complete Python test suite (71 tests)
$env:PYTHONPATH="."
py -3 -m pytest tests/terminal/test_custom_model_cli.py tests/contracts tests/security tests/models tests/backends tests/resources tests/dsv41 tests/runtime tests/steering tests/mutations tests/packaging tests/test_strata_memory.py -v -p no:randomly

# Run Node.js host verification (13 tests)
Push-Location apps/host
node tests/custom-gguf.test.mjs
node tests/run-config-check.test.mjs
Pop-Location

# Verify upstream integration lock
py -3 tools/check_upstream_cut.py
```

- **Python Tests**: **71 / 71 passed** (0 failures, 0 warnings).
- **Node.js Host Tests**: **13 / 13 passed**.
- **Security Check**: Header bounds protection, TOCTOU avoidance, and offline firewall constraints verified.

---

## Hardware Compatibility Reference

| Platform | Minimum Hardware | Recommended Target | Supported Engine |
| :--- | :--- | :--- | :--- |
| **NVIDIA GeForce** | RTX 2060 (12 GB VRAM) | **RTX 5060 Ti 16 GB (`sm_120`)** / RTX 4070 12 GB (`sm_89`) | Native CUDA 13.x C++ |
| **System Memory** | 32 GB Combined RAM+VRAM | **32 GB Physical DDR4/DDR5 RAM** | Windows / Linux OS |
| **AMD Radeon** | RX 6800 (16 GB) | RX 7900 XT / RX 9070 | [AMD HIP Engine](docs/AMD_HIP.md) |
| **Apple Silicon** | M1 Pro 32 GB | M2/M3/M4 Max 64 GB+ | [Mac Metal Engine](docs/MAC.md) |
| **Intel Arc / Core** | Intel Arc A770 16 GB | Intel Battlemage / Meteor Lake | [Intel SYCL Engine](docs/INTEL.md) |

---

## Upstream Integration Information

- **Upstream Baseline**: [`Niko1221/Strata`](https://github.com/Niko1221/Strata) @ `7dd5cf18e68c639a8773e096c5c79f971ea2a9f5` (v0.2.4.2 / engine 0.1.49.2)
- **Upstream Security Fix**: `c487c875d05075113965bc61d822b27179f70639` (atomic configuration saving)
- **Fork Foundation**: `ddc8f9e19cafb981ed91caaab0992ca814e6eca9` (retaining contracts F01 through F11)
- **Upstream Tracking Audit**: [_docs/upstream-intake/](_docs/upstream-intake/)

---

## Repository Structure

- [`spin8/`](spin8/) — Spin(8) $\mathrm{Cl}(8,0)$ triality algebra, Hadamard matrix transforms, and audit monitor.
- [`tqcodec/`](tqcodec/) — TurboQuant CUDA kernels, QJL residual sketch, and three-view KV cache.
- [`strata_control/`](strata_control/) — ModelBundle inspector, SHA-256 verification, and 32GB RAM memory planner.
- [`plugins/hermes-strata/`](plugins/hermes-strata/) — Hermes Agent inference & management tool plugin.
- [`plugins/model-providers/strata/`](plugins/model-providers/strata/) — Hermes Agent model provider configuration.
- [`tools/strata_memory_mcp.py`](tools/strata_memory_mcp.py) — Long-term memory MCP server connecting Hermes SQLite and Hakua directives.
- [`tools/qualify_model_bundle.py`](tools/qualify_model_bundle.py) — Four-tier GGUF model bundle qualification CLI.
- [`tools/check_upstream_cut.py`](tools/check_upstream_cut.py) — Automated upstream cut integrity validator.

---

## License & Acknowledgments

- **Fork Maintainer**: [`zapabob/Strata`](https://github.com/zapabob)
- **Original Engine & App**: [`Niko1221/Strata`](https://github.com/Niko1221/Strata) by Niko and the Strata Contributors.
- **Model Authors**: [Qwen Team (Alibaba)](https://huggingface.co/Qwen), [DeepSeek AI](https://huggingface.co/deepseek-ai), [ISTA-DASLab](https://huggingface.co/ISTA-DASLab), Kiwimaker, and AtomicChat.
- **License**: Released under the [MIT License](LICENSE).
