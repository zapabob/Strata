# Hakua / Strata

Hakua chatbot on Strata. This fork packages a Windows preview with Hakua memory and separate GPU runtimes. [zapabob/Strata](https://github.com/zapabob/Strata) · upstream [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Install (Windows preview)

1. Download the [setup EXE](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Strata_0.4.0-preview.20261101.1_x64-setup.exe) (or the [7z](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/Hakua-Strata-0.4.0-preview.20261101.1-windows-x64-sm120.7z) that contains the same EXE).
2. Compare it with [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261101.1/SHA256SUMS.txt) before you run it. The installer has no Windows code signature. Digests on this tag were refreshed on 2026-11-02; use today’s SUMS file, not an older copy.
3. Quit Strata fully if it is already installed (tray → Quit Strata), then run the EXE.
4. On first start, install the signed engine offered on the preparation screen, or import the matching `.tar.gz` from the same release. Then choose a model folder and load a model.

The click-path is short. Downloads, engine activation and model load take longer and need free disk and VRAM. Full steps: [HAKUA_INSTALL.md](docs/HAKUA_INSTALL.md). Measured limits: [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md).

## What the installer carries

| In the app installer | Separate |
| --- | --- |
| GUI / Host, private Node 24.22.2, Control / CPython 3.12.15, Hakua-memory 0.3.5, Harness | Signed CUDA engine component (~1.4 GB): native Strata + PrismML + TurboQuant |
| Manual app updates via this EXE | Full model weights (tens or hundreds of GB) |

You do not need system Node, Python, pip or a compiler for the released app. An upstream Niko1221 installer does not include this fork’s changes.

## Load a local model

- **Native Strata packs** (qualified Qwen-family text packs): use the app’s native prepare / load path.
- **Hikari / PQ2_0 GGUF**: use **Load with Strata** (PrismML). Do not use native prepare for PQ2_0; that path is for Strata engine packs, not PrismML.
- **Ordinary GGUF + TurboQuant cache**: backend `TurboQuant`, K=`FP16`, V=`TURBO2` / `TURBO3` / `TURBO4`, then reload. TurboQuant K modes stay off after corrupted real-model answers.

Each of PrismML and TurboQuant is its own executable inside the engine component. Details: [LOCAL_LLAMA_BACKENDS.md](docs/LOCAL_LLAMA_BACKENDS.md). Prefer packs that fit the GPU: ISTA-DASLab → Unsloth → Gyro.

When a model is serving on the Strata / supervisor path, Agent can use that local instance for tools the model supports (for example web search). Native-only sessions do not expose that path the same way.

## Hakua memory

After a supported model is loaded, open **Hakua memory** in the sidebar. Read and save consent are separate and reset every turn.

- Native path: copy the profile key from the dialog into About → Settings, then tick memory on the local page.
- PrismML / TurboQuant: the app supplies the local key; finish active requests before opening memory the first time (the owned server restarts with auth and private caches).

Guide: [MEMORY_HARNESS.md](serve/MEMORY_HARNESS.md). Hermes SOUL/MEMORY operator tools are separate from chat and are not required for basic use.

## Versions

| | |
| --- | --- |
| GUI / Product | `0.4.0-preview.20261101.1` |
| Engine / Control | `0.4.0` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Upstream freeze | `c62d5e3a` · 0.2.9 |

Release page: [v0.4.0-preview.20261101.1](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261101.1). The engine component and feed are Ed25519-signed and checked by the app. Automatic signed app updates are not qualified; update the app with this installer.

## Limits (measured preview)

Windows x64, NVIDIA RTX 50-series / CUDA sm_120, checked on an RTX 5060 Ti. Native text is included. Native image input and the separate native DeepSeek engine are not. Other GPUs and OSes need their own packages. Keep models and personal memory outside the app folder. No personal memories, keys or full weight packs ship in the release.

Spin(8) / Triality / Query-v3 / Bonsai stay opt-in experiments. No general speed or quality claim.

## Development

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Models](docs/MODELS.md) · [Build](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/zapabob/Strata/issues)

MIT Strata fork. Hakua-memory and model weights have their own licences. Credit stays with original authors and upstream. The optional ~480 KB control vector stays off by default under [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE).
