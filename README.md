<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="340">
  </picture>
</p>

<h3 align="center">Run powerful AI on your own computer.</h3>
<p align="center">Chat, code and work with images, locally.</p>

<p align="center">
  <a href="#models">Models</a> · <a href="#install"><b>Install</b></a> ·
  <a href="#hardware">Hardware</a> · <a href="#tools">Tools</a> ·
  <a href="#fork-notes">Fork notes</a> ·
  <a href="#help">Help</a> · <a href="#support-strata">Support</a>
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/latest"><img src="https://img.shields.io/github/v/release/zapabob/Strata?label=fork%20release&color=0ab887" alt="Download this fork"></a>
  <a href="https://github.com/Niko1221/Strata/releases/latest"><img src="https://img.shields.io/github/v/release/Niko1221/Strata?label=upstream&color=555" alt="Upstream Strata"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Niko1221/Strata" alt="MIT license"></a>
</p>

<p align="center"><sub><b>English</b> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.pt-BR.md">Português</a></sub></p>

**Free, open source, and yours to run.** This repository is a fork of [Niko1221/Strata](https://github.com/Niko1221/Strata) that keeps proprietary Spin(8) / Triality, Query-v3, TurboQuant, Bonsai, Hakua memory chat and Windows `-hakua` packaging, while tracking upstream security and bugfixes. Official model, install and hardware guidance below matches upstream **v0.2.6** (`4b9e05a2`) after the 2026-10-27 sync. Fork-only notes and measured preview evidence sit in [Fork notes](#fork-notes).

## Models

We recommend **ISTA-DASLab first**, then **Unsloth** and other providers, where a compatible model fits.

<details>
<summary><img src="docs/media/models/qwen.svg" width="22" alt="" align="middle"> &nbsp;<b>Qwen3.8-Flash-Next</b></summary>

| Provider | Choices |
| --- | --- |
| **ISTA-DASLab · recommended** | Q2\_0, IQ2\_XS, IQ3\_XXS, IQ3\_S. [Coder: IQ1\_M](docs/MODELS.md#coder) for coding. |
| **Unsloth** | UD-IQ4\_XS, UD-Q4\_K\_XL, UD-Q5\_K\_XL, UD-Q6\_K\_XL, Q8\_0 |
| **Gyro · agentionai** | [Gyro-S, Gyro-M](https://huggingface.co/agentionai/Qwen3.8-Flash-Next-Gyro-GGUF). Lower memory use but slower. |
| **Other options** | [Swift 1.5](docs/MODELS.md#swift-15), [NVFP4](docs/NVFP4.md), [OrcaRouter](docs/ORCA.md) |

[Compare sizes, memory needs and compatibility](docs/MODELS.md).

</details>

<details>
<summary><img src="docs/media/models/qwen.svg" width="22" alt="" align="middle"> &nbsp;<b>Qwen3.6-35B-A3B</b></summary>

**Unsloth:** UD-Q4_K_XL, UD-Q6_K_XL, Q8_0. These are the currently documented packs for this model.

[Model guide and compatibility](docs/QWEN36.md).

</details>

<details>
<summary><img src="docs/media/models/deepseek.svg" width="22" alt="" align="middle"> &nbsp;<b>DeepSeekV4.1-Flash-1017</b></summary>

In the **desktop app** and the **Terminal**. What does not fit in memory is read from your SSD, so it needs a lot of free
disk space.

| Set (IST-DAS) | Download | Free disk needed |
| --- | ---: | ---: |
| 1.75 bpw | 239 GB | about 245 GB |
| 2.00 bpw | 257 GB | about 265 GB |
| 2.25 bpw | 274 GB | about 280 GB |

Runs on NVIDIA RTX 30, 40 and 50 series (Windows and Linux) and AMD Radeon AI PRO R9700 (Linux). Setup downloads the
files and the DeepSeek engine, then starts the model.

```sh
strata launch --family deepseek41 --model ist-das-2.00bpw --plan
```

Measured with the 2.00 bpw set on Strata 0.2.5. Output is the speed of the answer, prompt is how fast Strata reads your input.

| Hardware | Output | Prompt |
| --- | ---: | ---: |
| RTX 5070 12 GB, 64 GB RAM | 4 to 6 tokens/s | about 110 tokens/s (4K) |
| RTX 3060 12 GB, 46 GB RAM | 9 to 11 tokens/s | about 155 tokens/s (4K) |
| 1x Radeon AI PRO R9700, 251 GB RAM | 21 to 25 tokens/s | 320 to 360 tokens/s (8K) |
| 4x Radeon AI PRO R9700 | 74 to 77 tokens/s | 400 to 450 tokens/s (8K) |

[Memory, disk and details](docs/DEEPSEEK41.md) · [Upstream release notes](https://github.com/Niko1221/Strata/releases)

</details>

<a id="the-other-sizes"></a>

Not sure what fits? [Choose a model for your computer](docs/MODELS.md#pick-by-memory).

## Install

<a id="option-a-the-strata-app"></a>

### Desktop app

**Upstream installers:** [Niko1221/Strata releases](https://github.com/Niko1221/Strata/releases/latest)  
**This fork's releases:** [zapabob/Strata releases](https://github.com/zapabob/Strata/releases/latest)

Install the app, choose a model, and start chatting. On first start the app downloads the engine for your graphics card. [Help with the installer](docs/INSTALL.md#the-app).

<sub>Upstream 0.2.6 files: `Strata-0.2.6-windows-x64-setup.exe` · `Strata-0.2.6-linux-x86_64.AppImage` · `Strata-0.2.6-macos-arm64.dmg`. Fork packages may use a `-hakua` label; see the release notes for that tag.</sub>

<p align="center">
  <img src="docs/media/app-chat.png" width="900" alt="Strata desktop app with a chat and live code preview side by side">
  <br><sub>Chat, files and a live preview in one window.</sub>
</p>

<a id="option-b-the-terminal-one-line"></a>

### Terminal app

Prefer the terminal? Install Strata, then run **`strata launch`**.

<details open>
<summary><b>Install commands</b></summary>

**Linux / Mac**

```sh
curl -fsSL https://github.com/Niko1221/Strata/releases/latest/download/install.sh -o install.sh && sh install.sh
```

**Windows PowerShell**

```powershell
irm https://github.com/Niko1221/Strata/releases/latest/download/install.ps1 | iex
```

On Windows, open a new terminal afterwards. Then:

```sh
strata launch
```

Follow the prompts to download and start a model. [Terminal guide](docs/TERMINAL_LAUNCH.md).

</details>

<p align="center">
  <img src="docs/media/terminal-monitor.png" width="900" alt="Strata terminal app showing model activity, speed, memory and recent requests">
  <br><sub>Watch your model and hardware while it runs.</sub>
</p>

<a id="build-from-source"></a>

[Build from source](docs/SOURCE_INSTALL.md) · [Docker](docs/DOCKER.md) · [Full install guide](docs/INSTALL.md)

<a id="what-you-need"></a>

## Hardware

| Supported hardware | Guide |
| --- | --- |
| **NVIDIA GeForce RTX 20 / 30 / 40 / 50 series** | [NVIDIA setup](docs/INSTALL.md#what-you-need) |
| **AMD Radeon RX 7700 / 7800 / 7900, RX 9060 / 9070, AI PRO R9700** | [AMD setup](docs/AMD_HIP.md) |
| **AMD Radeon RX 6800 / 6900 · experimental** | [RX 6000 setup](docs/AMD_HIP.md#rdna2-gfx1030) |
| **Intel Arc · Linux** | [Intel setup](docs/INTEL_ARC.md) |
| **Apple Silicon · M1 or newer** | [Mac setup](docs/MAC.md) |
| **AMD Ryzen AI Max · Strix Halo** | [Strix Halo setup](docs/STRIX_HALO.md) |

<a id="using-it"></a>

## Tools

**Claude Code · Codex CLI · OpenCode · oh-my-pi · pi.dev · Hermes Agent · OpenClaw**, and more through the OpenAI- and Anthropic-compatible APIs.

Run **`strata connect`** to see setup instructions for your tool. [Connection guide](docs/TERMINAL_LAUNCH.md#connect-your-apps-strata-connect).

<a id="fork-notes"></a>

## Fork notes

This fork (`zapabob/Strata`) keeps the following surfaces while aligning new host/control APIs with upstream:

| Area | What is kept |
| --- | --- |
| Engine research | Spin(8) / Triality KV, Query-v3, TurboQuant dialects, Bonsai / Prism paths |
| Host | Hakua consented memory chat, run-config known keys, native load cancel ownership |
| Packaging | Windows full packaging with optional `-hakua` label |
| Intake | `_docs/upstream-intake/` contracts and `tools/merge_upstream_fork.py` |

Upstream sync checkpoint: **official v0.2.6 / `upstream/main@4b9e05a2`** (Windows uninstaller fixes and 0.2.6 docs/feed). Fork app version in-tree after merge: **`0.3.2-preview.20261027.2`**.

### Windows inference preview (measured on this fork)

Earlier tag `0.3.2-preview.20261027.1` packages the engine tested on Windows, RTX 5060 Ti 16 GiB and 32 GiB system RAM. It is a CUDA 13 / SM120 preview overlay, not a claim that every upstream installer path was re-measured here.

The tested configuration is Qwen3.8 Q2_0, capacity **131072**, **spec4 + MTP**, **k8v4**, and a 256-token output reservation.

| Actual input | First and repeated generation | Recall check | Cleanup |
| --- | --- | --- | --- |
| 4096 tokens | Both completed, 52 output tokens each | Both passed | Zero remaining Job processes |
| 32768 tokens | Both completed, 52 output tokens each | Both passed | Zero remaining Job processes |

These runs had source and controller diagnostics OFF. The 32K first prompt took 494.76 seconds; the repeated prompt took 0.646 seconds with prefix reuse. Decode took 13.759 and 3.255 seconds respectively. These are observations from one synthetic task, not a statistical speed or broad quality claim.

Read [the measurement record](docs/PERF131K.md) and [machine-readable status](docs/perf131k-status.json) before using that preview. Full-length 126000-token certification, image inference and HIP/SYCL remain unqualified on that record.

The optional memory harness stays **disabled by default**. See [MEMORY_HARNESS](serve/MEMORY_HARNESS.md).

<a id="guides"></a>

## Help

[All guides](docs) · [Troubleshooting](docs/TROUBLESHOOTING.md) · [Report a bug on this fork](https://github.com/zapabob/Strata/issues/new/choose) ·
[Upstream issues](https://github.com/Niko1221/Strata/issues/new/choose) ·
[Benchmarks](docs/COMMUNITY_BENCHMARKS.md) · [How it works](docs/HOW_IT_WORKS.md) · [Contribute](CONTRIBUTING.md)

## Support Strata

**Help keep local AI open to everyone.** Upstream maintains the public project; a coffee helps their development and testing.

<a href="https://buymeacoffee.com/strataengine"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me a Coffee: support Strata" height="48"></a>

[MIT license](LICENSE) · [Credits and model licenses](docs/HOW_IT_WORKS.md#credits) · [Privacy](docs/SAFETY.md)

<sub>For AI tools and automated readers: <a href="AGENTS.md">technical reference</a> · <a href="docs/AI_SETUP.md">setup instructions</a> · <a href="_docs/upstream-intake/fork-contracts.json">fork contracts</a>.</sub>
