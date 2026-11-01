# Hakua / Strata

Hakua chatbot, built on Strata. [zapabob/Strata](https://github.com/zapabob/Strata) · [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## TLDR · installation steps in 30 seconds

Download and run this fork's Windows installer. On first start, install the compatible engine offered by the app, then choose and load a model. Open Hakua memory in the sidebar. The setup actions take about 30 seconds; app, engine and model downloads, installation and loading take longer.

Source candidate 0.4.0: release qualification and publication are still in progress.

[Windows EXE](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Strata_0.4.0-preview.20261101.1_x64-setup.exe) · [7z](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Hakua-Strata-0.4.0-preview.20261101.1-windows-x64-sm120.7z) · [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/SHA256SUMS.txt)

The 7z contains the same installer. Extract it, then run the setup EXE.

## Fork features

Hakua reads remembered context and saves a summary only with your consent for that request. Read and save are independent and reset after each request. When you load a supported native model, the desktop app creates a local memory profile automatically. Open Hakua memory, copy the profile key from its dialog and select a memory checkbox on the local page, then paste the key into About → Settings. See the [memory guide](serve/MEMORY_HARNESS.md), including explicit source-server configuration.

For PrismML/PQ2_0 and TurboQuant, load the model and open Hakua memory in the sidebar. The dialog uses your local profile key automatically, with separate read and save checkboxes for each turn. Opening it first restarts the owned server with private caches and authentication; finish active requests before opening it. Native and additional backends use the same local memory profile. The app checks GUI, Host and desktop versions on startup and shows recovery instructions if files are mixed or cannot load.

Hermes tools support approved SOUL.md / MEMORY.md synchronisation, Ebbinghaus memory, semantic graph, Obsidian export and sleep consolidation. These operator tools are separate from the chat page. Optional RAG and embedding packages are not part of the base installer.

For a local PQ2_0 GGUF, choose `PrismML` under the model’s llama-server backend setting. For standard GGUF models, choose `TurboQuant`, set K cache precision to `FP16` and V to `TURBO2`, `TURBO3` or `TURBO4`. TurboQuant K modes are unavailable in this candidate because real-model tests found corrupted replies. Reload the model after changing the backend. Each backend has its own executable and libraries in the separate engine component; PQ2_0 and TurboQuant are separate paths. See [backend setup and limits](docs/LOCAL_LLAMA_BACKENDS.md).

Spin(8)/Triality, Query-v3 and Bonsai experiments require compatible, explicitly selected settings. No general speed or quality improvement is claimed.

The installer includes private Node and Python and pinned Hakua-memory 0.3.5, following the official app architecture. GPU engines are separate: the app downloads a signed Hakua engine component when you choose to install it, or imports a downloaded component file. This component contains native CUDA, PrismML and TurboQuant runtimes. Model weights are another separate download. No system Node/Python installation, pip or compiler is needed to run the released app.

## Compatibility and updates

This Windows package targets NVIDIA RTX 50-series, CUDA sm_120. Other GPUs, Linux and macOS need their own compatible packages. An upstream installer does not include this fork's changes. Model weights are separate and may need tens or hundreds of GB. Prefer compatible ISTA-DASLab packs, then Unsloth, then Gyro.

The separate native engine supports text chat. Native image input and the separate native DeepSeek engine are not included in this preview.

Keep models and personal memory outside the app folder; no personal memories, profile keys or weights are distributed. Close the app before upgrading. To roll back, retain a data backup and install an earlier fork release.

With tray storage enabled, × hides the window. To exit fully before an update, right-click the Strata tray icon and choose Quit Strata.

[Models](docs/MODELS.md) · [Install](docs/HAKUA_INSTALL.md) · [Hermes tools](tools/hakua_hermes_memory_stack.py)

## Versions and validation

| | |
| --- | --- |
| GUI / Product | `0.4.0-preview.20261101.1` |
| Engine | `0.4.0` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Upstream | `c62d5e3a` · 0.2.9 |

<!-- App version in this preview tree: `0.4.0-preview.20261101.1` -->

The Windows installer has no Windows code signature. Compare SHA256SUMS.txt before installing. The separate engine component and its update feed are signed and verified by the app. App updates use the manual installer; automatic signed app updates are not yet qualified. [Release qualification](docs/HAKUA_RELEASE.md) records actual results and limits, including the real-model memory checks.

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
