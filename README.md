# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

**Local AI engineered to utilize every resource on your Windows PC — GPU, physical + SMT CPU threads, system RAM, and NVMe/SSD storage.** Hakua is the independent `zapabob/Strata` fork of [Niko1221/Strata](https://github.com/Niko1221/Strata), tracking official upstream **v0.2.21** (`d46f5f268`, engine/Control `0.1.67`) while keeping all fork-only runtimes, memory/agent workflows, and Blackwell CUDA 13.5 optimizations.

## What's new in 0.8.1 (Engine 0.7.0)

- **Full-machine heterogeneous inference across all 4 hardware tiers (GPU + 6P/6SMT CPU + RAM + SSD)**:
  - **Windows native `aux_cpus` CPU Sets + SMT I/O split** (`engine/include/strata/platform/aux_cpus.hpp`, `ssd_stream_scheduler.hpp`, `direct_file.cpp`): pins GPU host + AVX2 MoE compute strictly to physical primary cores while dedicating all SMT secondary threads (`io_smt=[1,3,5,7,9,11]` on a 6C/12T CPU) to 6-thread overlapped Direct I/O and async `PrefetchVirtualMemory` streaming.
  - **5 freshly compiled CUDA 13.5 / SM120 Blackwell native engines** (`strata.exe`, `strata-inkling2.exe`, `strata-inkling.exe`, `strata-hy4.exe`, `strata-q38.exe`) with Gen-K/L zero-copy mapped doorbells, WDDM 1536 MiB VRAM protection, commit-safe Windows RAM budgets (`hy4_cpu_experts.cpp`, `inkling2_engine.cu`), Windows physical-core pinning + `_mm_pause` spin-waits (`ink_hybrid.cuh`), and SM120 Q38 pinned embedding staging + batched `PrefetchVirtualMemory` (`engine/q38/src/engine.cu`).
  - **Unified full-machine launcher & presets**: `tools/full_machine_infer.py` (`--list-models`, `--plan`, `--bench`, `--serve`) automatically probes GPU, physical/SMT CPU topology, RAM/commit headroom, and SSDs to generate 3-tier execution plans and ready server configs under `configs/`.
- **Official upstream v0.2.21 3-way merge**: integrates official unified 4-tier GPU+RAM+CPU+SSD MoE, multi-GPU `--layer-split`, GUI/host updates, and Control/engine `0.1.67` fixes alongside all fork features (`/btw`, `/deepresearch`, RustXNG Full, workflow skills, Q38 dense runner, DeepSeek extension, Hermes `inkling2` provider, and kuraneko1's MIT Inkling-2 profile tables).

## Measured real-hardware benchmarks

Measured on **NVIDIA GeForce RTX 5060 Ti 16 GB (SM120, CUDA 13.5) · AMD Ryzen 5 4500 (6C/12T) · 32 GB DDR4 · Dual SSD (`C:` Crucial P3 NVMe + `H:` S5-1TB SSD)** with 16-token prompts and 32-token greedy decode:

| Model (Size) | Engine & Context | Active Tiers | Prefill (`pp`) | Decode (`tg`) | Parity |
|---|---|---|---:|---:|---|
| **Sakura Inkling-2-Mini Q4_K_M** (16.28 GiB) | `strata-inkling2.exe` · 131K (Q8 KV) | GPU 10.85 GiB (2232 exps) + Pinned RAM 4.34 GiB (840 exps) + 6P/6SMT | **85.08 t/s** | **42.22–42.33 t/s** | **32/32 exact** |
| **Sakura Inkling-2-Mini Q4_K_M** (16.28 GiB) | `strata-inkling2.exe` · 131K (Q8 KV) | 3-Tier spill: GPU 10.85 GiB + RAM 3.60 GiB + **SSD mmap 0.74 GiB (`prefetch=on`)** + 6P/6SMT | 64.80 t/s | 14.24 t/s | **32/32 exact** |
| **Inkling-2-Mini UD Q4_K_M** (15.47 GiB) | `strata-inkling2.exe` · 16K (Q8 KV) | GPU 10.42 GiB (2339 exps) + Pinned RAM 3.34 GiB (733 exps) + 6P/6SMT | **109.64 t/s** | **53.28 t/s** | Greedy clean |
| **Qwen3.8-27B 3.69bpw MTP** (11.73 GiB) | `strata-q38.exe` · 4K (F16 KV) | GPU SM120 weights (10.44 GiB) + pinned host emb staging + `PrefetchVirtualMemory` | 6.21 s cold | **29.95 t/s** | Greedy clean |

*CPU threading note (Ryzen 5 4500 A/B)*: keeping compute workers on 6 physical cores (`host=0`, `workers=2,4,6,8,10`) with SMT threads (`1,3,5,7,9,11`) reserved for I/O achieved **42.22–42.33 t/s**, vs **29.68 t/s** (-21.9%) when oversubscribing 11 compute workers across SMT siblings.

## Version and downloads

Current release: **0.8.1** — GitHub Latest: [v0.8.1 release page](https://github.com/zapabob/Strata/releases/tag/v0.8.1).

- **Desktop Installer**: `Strata-0.8.1-windows-x64-setup.exe` (per-user Tauri/NSIS app with bundled Node 24.22.3, Python, Control 0.6.3, and RustXNG Full).
- **Installer Bundle**: `Strata-0.8.1-windows-x64.tar.7z` (installer + `SHA256SUMS.txt`).
- **CUDA 13.5 SM120 Engine Component (opt-in)**: `strata-engine-0.7.0-windows-x86_64-cuda-cuda13.tar.gz` (all five rebuilt SM120 engines: `strata.exe`, `strata-inkling2.exe`, `strata-inkling.exe`, `strata-hy4.exe`, `strata-q38.exe`).
- **Hy4-Flash Component (opt-in)**: `strata-hy4-0.1.64-windows-x86_64-cuda-cuda13.tar.gz`.

Always download directly from the release **Assets** list and verify SHA-256 digests. Component ed25519 signature verification is removed (no signing key); Windows Authenticode signing is absent; **`releaseQualified=false`**.

![Hakua / Strata real-model Japanese chat on Qwen3.8-27B](docs/media/native-qwen38-japanese-chat.png)
*Hakua / Strata desktop running `qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf` via `strata-q38.exe` (CUDA 13.5 / RTX 5060 Ti 16 GB).*

## Quick start (Full-machine CLI & Desktop)

### Desktop install or overwrite-update

1. Finish active requests, unload models, back up app data, and quit Strata (including its system tray icon).
2. Run `Strata-0.8.1-windows-x64-setup.exe` into your existing installation directory to overwrite-update while preserving models, chats, memory, tools, API keys, and approvals.
3. Import `strata-engine-0.7.0-windows-x86_64-cuda-cuda13.tar.gz` via *I already have the file*, choose a compatible model or local GGUF, and click **Load**. See [installation and rollback](docs/HAKUA_INSTALL.md).

### Full-machine launcher (`tools/full_machine_infer.py`)

```powershell
# Inspect GPU/CPU/RAM/SSD tiers and auto-discover local models
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --list-models

# Run Sakura Inkling-2-Mini 131K benchmark with full-machine settings
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --bench --model Sakura --max-new 32

# Start local OpenAI/Anthropic API server (127.0.0.1:8092) with RAM squeeze
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --serve --model Sakura --port 8092 --squeeze
```

## Recommended GGUF & Fork features

- **Qwen3.8-27B local chat on 16 GB VRAM**: tested with [soyaakinohara's 3.69 bpw mixed-quantized GGUF](https://huggingface.co/soyaakinohara/qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf) (credits to **soyaakinohara** and **AEON-7**). Start with a 4,096-token context; the `12GB` filename label does not guarantee fit on a 12 GB card.
- **Owned Q38 dense runner (`strata-q38.exe`)**: per-tensor mixed-quantization polymorphism across 11 formats (`F32`, `F16`, `BF16`, `Q8_0`, `Q4_K`, `Q5_K`, `Q6_K`, `IQ3_S`, `IQ2_S`, `IQ4_XS`, `PQ2_0`), Tensor Core prefill, Spin(8) / TurboQuant KV modes (`auto`: `f16` → `f16_turbo4` → `spin8_k8v4`), MTP `K=3` draft/verify, and optional Japanese orthography profile. See [QWEN38_DENSE_NATIVE.md](docs/QWEN38_DENSE_NATIVE.md).
- **Agent & workflow tools**: tool-free `/btw` side-question subagent with independent stop control, `/research` and `/deepresearch` with bundled RustXNG Full (queries external providers when enabled), opt-in private workflow skill learning/application, workspace/sidebar file CRUD, and scoped chat memory. See [WORKFLOW_SKILLS.md](docs/WORKFLOW_SKILLS.md) and [BROWSER_SEARCH.md](docs/BROWSER_SEARCH.md).

## Safety floors and limits

Retained unchanged: **3 GiB available RAM**, **4 GiB commit headroom**, **>= 768 MiB GPU reserve** (`1536 MiB` WDDM default for `<= 17 GiB` Inkling-2), **5 GiB free on `C:`**, and **10 GiB free on `H:`**. General model quality, full-window generation, and simultaneous multi-client GPU concurrency remain unqualified (**`releaseQualified=false`**). This Windows fork release does not include native image input or qualified Linux/macOS inference. Historical records retain their original versions in [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md).

## Documentation and development

[Install](docs/HAKUA_INSTALL.md) · [Release evidence](docs/HAKUA_RELEASE.md) · [API & hardware](docs/AI_REFERENCE.md) · [Terminal](docs/TERMINAL.md) · [Source build](docs/SOURCE_INSTALL.md) · [Packaging](tools/packaging/README.md) · [Contributing](.github/CONTRIBUTING.md) · [Security](.github/SECURITY.md) · [License](LICENSE)

```powershell
pytest tests/test_full_machine_infer.py
python -m pytest terminal/tests/terminal
```

```powershell
cd app/host
pnpm test
pnpm run build
```

[Niko1221/Strata](https://github.com/Niko1221/Strata) · [Hermes Agent](https://github.com/NousResearch/hermes-agent) · [Third-party notices](third_party/)

## Acknowledgements

Sincere thanks to **Niko1221/Strata**, **kuraneko1 (`_ryu15_`)**, **ggml & llama.cpp**, **NousResearch (Hermes Agent)**, **Qwen Team (Alibaba Cloud)**, **NVIDIA**, **RustXNG**, **libstrix**, **Node.js / Python / Tauri**, **Microsoft**, **ISTA-DASLab**, **PrismML**, **TurboQuant**, **Spin(8)**, **soyaakinohara**, and **AEON-7** for the open-source foundations, weights, and research that make Hakua / Strata possible.
