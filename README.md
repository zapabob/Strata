# Hakua / Strata

Hakua chatbot, built on Strata. [zapabob/Strata](https://github.com/zapabob/Strata) · [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## TLDR · installation steps in 30 seconds

Download this fork's Windows installer, run it, then select and load a compatible model. Open Hakua memory in the sidebar. The steps take about 30 seconds; downloading, installing and loading the app and model take longer.

[Windows EXE](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/Strata_0.3.3-preview.20261030.1_x64-setup.exe) · [7z](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/Hakua-Strata-0.3.3-preview.20261030.1-windows-x64-sm120.7z) · [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/SHA256SUMS.txt)

The 7z contains the same installer. Extract it, then run the setup EXE.

## Fork features

Hakua reads remembered context and saves a summary only with your consent for that request. Read and save are independent and reset after each request. Memory chat needs an enabled `hakua_harness` profile and its own profile key; a normal chat key is separate. Follow the [memory setup guide](serve/MEMORY_HARNESS.md).

Hermes tools support approved SOUL.md / MEMORY.md synchronisation, Ebbinghaus memory, semantic graph, Obsidian export and sleep consolidation. These operator tools are separate from the chat page. Optional RAG and embedding packages are not part of the base installer.

For a local PQ2_0 GGUF, choose `PrismML` under the model’s llama-server backend setting. For standard GGUF models, choose `TurboQuant`, set K cache precision to `FP16` and V to `TURBO2`, `TURBO3` or `TURBO4`. TurboQuant K modes are unavailable in this candidate because real-model tests found corrupted replies. Reload the model after changing the backend. Each backend has its own bundled executable and libraries; PQ2_0 and TurboQuant are separate paths. See [backend setup and limits](docs/LOCAL_LLAMA_BACKENDS.md).

Spin(8)/Triality, Query-v3 and Bonsai experiments require compatible, explicitly selected settings. No general speed or quality improvement is claimed.

Private Node and Python, pinned Hakua-memory 0.3.5 and a fork-built CUDA engine are bundled. Starting a model does not install Python packages or compile code.

## Compatibility and updates

This Windows package targets NVIDIA RTX 50-series, CUDA sm_120. Other GPUs, Linux and macOS need their own compatible packages. An upstream installer does not include this fork's changes. Model weights are separate and may need tens or hundreds of GB. Prefer compatible ISTA-DASLab packs, then Unsloth, then Gyro.

Keep models and personal memory outside the app folder; no personal memories, profile keys or weights are distributed. Close the app before upgrading. To roll back, retain a data backup and install an earlier fork release.

[Models](docs/MODELS.md) · [Install](docs/INSTALL.md) · [Hermes tools](tools/hakua_hermes_memory_stack.py)

## Versions and validation

| | |
| --- | --- |
| GUI / Product | `0.3.3-preview.20261030.1` |
| Engine | `0.3.3` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Upstream | `46c152a1` · 2026-10-28 |

<!-- App version in this preview tree: `0.3.3-preview.20261030.1` -->

This preview is unsigned. Compare the download against SHA256SUMS.txt before installing. [Release qualification](docs/HAKUA_RELEASE.md) records actual test results and limitations; a successful build alone does not prove inference works. This unsigned preview uses manual installer updates; automatic signed updates are not yet qualified.

## Development and support

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Build](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/zapabob/Strata/issues)

MIT-licensed Strata fork. Hakua-memory and model weights have separate licences. Original authors and upstream contributions retain their credit.

The optional upstream 480 KB control vector stays off by default and carries [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE). Full inference model weight packs are separate downloads.
