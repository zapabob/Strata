# Hakua / Strata

Hakua chatbot on Strata. This repository is the **zapabob Hakua fork**. Its Windows preview path is not the upstream Niko1221 installer path.

[zapabob/Strata](https://github.com/zapabob/Strata) · upstream [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Install (Windows preview)

Current public app tag: **[v0.4.0-preview.20261103.7](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261103.7)**. This tag publishes the setup EXE and `SHA256SUMS.txt` only (no matching 7z).

1. Download [`Strata_0.4.0-preview.20261103.7_x64-setup.exe`](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261103.7/Strata_0.4.0-preview.20261103.7_x64-setup.exe).
2. Compare it with [`SHA256SUMS.txt`](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261103.7/SHA256SUMS.txt) before you run it. The installer has no Windows code signature. Setup EXE SHA-256 `5e8b8fff82b6e63dea48bf5c1907950911700c9bf30673444e5d2489a87c0336` (113,064,953 bytes).
3. Quit Strata fully if it is already installed (tray → Quit Strata), then run the EXE. An installed copy can be updated with `/S /UPDATE`.
4. The installer updates the app. It does not contain a CUDA engine. After install, use the preparation screen (or file import) for GPU runtimes as below.

The click-path is short. Downloads, engine activation and model load take longer and need free disk and VRAM. Full steps: [HAKUA_INSTALL.md](docs/HAKUA_INSTALL.md). Measured limits: [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md). Do not substitute an upstream Niko1221 installer for this fork.

## Engines (signed vs unsigned)

Keep these two identities apart. An unsigned package is never a signed one.

| Component | Where | Signature | Identity |
| --- | --- | --- | --- |
| App installer on `.7` | this tag | no Windows code signature; not an Ed25519-signed app update | setup SHA-256 `5e8b8fff…` above |
| Signed CUDA component (native + PrismML + TurboQuant) | still [v0.4.0-preview.20261101.1](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261101.1) | Ed25519-signed feed/component as published there | native engine digest `b5e4d5255a48882334b27ab643c22c9c1b54e4580f82b402176a9ca5661bf6f1` — **untouched** by the `.7` app tag |
| Qwen3.6 side-by-side package on `.7` | separate unsigned component (`0.4.0-q36-…`) | `signature` is null; no picture reader | hotspot-profile `strata.exe` SHA-256 `907341c74d5a9f26c784e4aaad3460e376d4cabd84635c5d032879c59b08d150` (`native-build.json` `cd235fdf812d43c45e0a0881073bee97483c5aa50c65bbefb877bd1e8e8dbd8b`; older allowed digests listed below) |

PrismML and TurboQuant stay in the signed `.20261101.1` component. The `.7` release does not replace those files.

## What the installer carries

| In the app installer | Separate |
| --- | --- |
| GUI / Host, private Node 24.22.2, Control / CPython 3.12.15, Hakua-memory 0.3.5, Harness | CUDA engines (table above). Full model weights (tens or hundreds of GB) |
| Manual app updates via this EXE | Automatic signed app updates are not qualified |

You do not need system Node, Python, pip or a compiler for the released app.

## Load a local model

- **Native Strata packs** (qualified Qwen-family text packs): use the app’s native prepare / load path.
- **Hikari / PQ2_0 GGUF**: use **Load with Strata** (PrismML). Do not use native prepare for PQ2_0; that path is for Strata engine packs, not PrismML.
- **Ordinary GGUF + TurboQuant cache**: backend `TurboQuant`, K=`FP16`, V=`TURBO2` / `TURBO3` / `TURBO4`, then reload. TurboQuant K modes stay off after corrupted real-model answers.

Each of PrismML and TurboQuant is its own executable inside the signed engine component. Details: [LOCAL_LLAMA_BACKENDS.md](docs/LOCAL_LLAMA_BACKENDS.md). Prefer packs that fit the GPU: ISTA-DASLab → Unsloth → Gyro.

When a model is serving on the Strata / supervisor path, Agent can use that local instance for tools the model supports (for example web search). Native-only sessions do not expose that path the same way.

## Hakua memory

After a supported model is loaded, open **Hakua memory** in the sidebar. Read and save consent are separate and reset every turn.

- Native path: copy the profile key from the dialog into About → Settings, then tick memory on the local page.
- PrismML / TurboQuant: the app supplies the local key; finish active requests before opening memory the first time (the owned server restarts with auth and private caches).

Guide: [MEMORY_HARNESS.md](serve/MEMORY_HARNESS.md). Hermes SOUL/MEMORY operator tools are separate from chat and are not required for basic use.

## Versions

| | |
| --- | --- |
| GUI / Product | `0.4.0-preview.20261103.7` |
| Engine / Control | `0.4.0` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Upstream freeze | `ffa80d73` · 0.2.10 |

Release page: [v0.4.0-preview.20261103.7](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261103.7). This tag’s installer and Qwen3.6 engine package are not signed. The Ed25519 feed and the signed engine on `v0.4.0-preview.20261101.1` were not replaced. Update the app with this installer.

## Qwen3.6 on 32 GB RAM / 16 GB VRAM

The main line stays Qwen3.6-35B-A3B UD-Q4_K_XL, context 65536, FP32 KV, MTP 2, prefill auto. New paths are opt-in. A setting this engine does not apply is refused before the process starts. A private-cache request is refused. It is not removed to force a start.

The mapped expert pack stays off unless the launch asks for it and the SHA-256 of the resolved `strata.exe` is one of:

- `907341c74d5a9f26c784e4aaad3460e376d4cabd84635c5d032879c59b08d150` (unsigned Q36 hotspot-profile opt-in rebuild; T07 profile capture PASS)
- `64226fde7905821148c78b7de85ede4d291c4df8184d80866dccba014d7c02b7` (unsigned Q36 help-honesty rebuild; mapped-live READY recorded)
- `6fe110650940d0c19f09909d769393769650045e6bc6eab29ccc49734dbcab29`
- `dd53df07789e0fefcb87e33acab54f5bfe1faf312ef6bad515924736b715c5b5`
- `512d7f8bba66b57fbe0f8b90807825d3b3172a86dd039452bc29e685ca27d046` (older digest; still allowed)

A digest written in model settings does not unlock the flag. The legacy host arena stays the default. T04 adoption is **KEEP_DEFAULT** (bounded policy NOT_RUN). T06 scheduler remains **BLOCKED**. T07 hotspot **profile** capture PASS; kernel opt-in NOT_RUN. T08 refuse PASS / measured FP16 NOT_RUN. Startup time and token speed for this build were not measured beyond recorded observational notes. The CUDA spill guard did not pass against the reviewed baseline.

On a 32 GB PC the host can refuse UD-Q4_K_XL before launch when free physical RAM cannot hold the legacy 18.75 GiB expert arena plus the reserve. That refusal is not a measurement that the model now fits in 16 GB of VRAM.

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
