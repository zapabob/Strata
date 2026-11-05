# Hakua / Strata

Run local language models in a Windows desktop app, with chat, model controls,
tools and optional Hakua memory. This is the [zapabob fork](https://github.com/zapabob/Strata)
of [Niko1221/Strata](https://github.com/Niko1221/Strata).

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Windows preview

This beta is still being qualified and is not published yet. The filenames and installation steps below describe the planned release; see the [current release status](docs/HAKUA_RELEASE.md).

Product version: **0.4.1-beta.1**. The release contains the setup EXE
and its checksums. It is a manual-update preview without a Windows code signature.

1. Get the [Windows installer](https://github.com/zapabob/Strata/releases/download/v0.4.1-beta.1/Strata_0.4.1-beta.1_x64-setup.exe)
   and compare it with [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.1-beta.1/SHA256SUMS.txt).
2. Quit an existing Strata instance, including the tray app, then run the installer.
   Keep models and personal data outside the application folder.
3. Download `strata-engine-0.4.1-windows-x86_64-cuda-cuda13.tar.gz` from this beta release and import it on the preparation screen. The latest feed still serves the earlier engine. Node and Python are included; no system interpreter, pip or compiler is needed.
4. Choose a model that fits the computer, or select **Use a local GGUF** for
   files already on disk.

See [installation](docs/HAKUA_INSTALL.md), [release checks and limits](docs/HAKUA_RELEASE.md)
and the [release page](https://github.com/zapabob/Strata/releases/tag/v0.4.1-beta.1).
The fork uses its own installer and component feed.

Versions follow [SemVer 2.0.0](https://semver.org/): app `0.4.1-beta.1`, native engine/Control `0.4.1`; unchanged PrismML/TurboQuant runtimes stay `0.4.0`. The default app location is `%LOCALAPPDATA%\Programs\Strata` on C:, independently of the model folder. Existing installs may remember another drive.

## Use the files you already have

For a split GGUF, choose one shard; Strata checks the complete set. Imported
weights stay in their original location. A generic metadata name such as `Hf`
is displayed using the filename. A name you choose is preserved when inspected
again or after a restart.

Settings for a registered local model open while the other model lists are still loading.

Before preparing a catalog model, Strata checks the selected model folder for a
matching local set, including nested repository folders. A single valid match
is reused. Multiple matches require a file choice so a different fine-tune is
not selected silently. An existing canonical download keeps its usual integrity
checks and partial-download recovery.

Native models may need a one-time pack conversion after the GGUF is available.
That stage shows completed layers when the packer supplies them. An interrupted
low-memory pack counts the disk space already allocated to its temporary file
when checking room to resume. Engine and optional draft-layer downloads are
separate from reuse of the model's own GGUF files.

| Model path | How to load |
| --- | --- |
| Supported native Qwen / Swift sets | Prepare and load with the native Strata engine. |
| Hikari or another supported PQ2_0 GGUF | **Load with Strata**, using PrismML. No native Q2_0 pack conversion. |
| Ordinary supported GGUF with TurboQuant cache | Choose TurboQuant, K=`FP16`, V=`TURBO2`, `TURBO3` or `TURBO4`, then reload. |

File validation checks structure and compatibility metadata; the engine still
checks actual allocation and model support at load time. A failed or stopped
engine clears the loading indicator. See [local backends](docs/LOCAL_LLAMA_BACKENDS.md).

## Components and memory

| Component | Version / distribution |
| --- | --- |
| Desktop GUI / Host | `0.4.1-beta.1`, this app release |
| Native engine / Control | `0.4.1` |
| Private runtimes | Node `24.22.2`, CPython `3.12.15` |
| Hakua-memory | `0.3.5` |
| CUDA / PrismML / TurboQuant component candidate | [release status](docs/HAKUA_RELEASE.md) |
| Upstream source reference | `ffa80d73`, upstream `0.2.10` |

The separate CUDA component candidate contains native engine 0.4.1 and the unchanged PrismML/TurboQuant 0.4.0 runtimes. Its new manifest will be signed with the fork’s component key after qualification. Once published, import the file from this beta release; the stable feed keeps its earlier package. Component signing is separate from Windows app code signing. Exact identities are in [the release record](docs/HAKUA_RELEASE.md).

After loading a supported model, open **Hakua memory** in the sidebar. Reading
and saving memory have separate consent controls for each turn. Opening memory
for PrismML / TurboQuant restarts the owned server with authentication and
private caches; finish an active request first. See [the memory guide](serve/MEMORY_HARNESS.md).

## Supported limits

This Windows x64 preview is checked on an RTX 5060 Ti, CUDA sm_120, with 32 GB
system RAM. It does not qualify other GPUs, operating systems, native image
input or a separate native DeepSeek engine. RAM, VRAM, disk speed and available
disk space affect which models can run and how long preparation takes.

The new Qwen3.6 private-cache path retains state within the same authenticated
conversation. Another conversation or user cannot reuse it. Switching owners,
cancellation, errors or five idle minutes clear the private cache. Requests
without a conversation ID do not reuse cached state. The Host’s two pre-start refusal branches have been removed. The server checks
the running engine’s INFO capability before accepting private-cache requests,
including compatible local builds. Initially it serves one request at a time, with
shared prompt and conversation caches disabled. Its mapped expert pack and
experimental kernels remain opt-in, with binary-hash checks. The legacy host
arena can need about 18.7 GiB plus a reserve; 32 GB total RAM does not guarantee
a successful start. Consult the release record for measurements and open checks.
TurboQuant K modes remain unavailable after failed real-model quality checks.

A successful short response with a 131,072 context setting is not full-window
generation or quality qualification. Measured conditions, failures and tests
not run are recorded separately in [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md).
Spin(8), Triality, Query-v3 and Bonsai remain opt-in experiments.

## 96K–128K on a 16 GB GPU

The editor offers 96K (98,304) and 128K (131,072). On the tested RTX 5060 Ti 16 GB / 32 GB RAM PC, Qwen3.6 UD-Q4_K_XL with PrismML, Q8 K/V and 28 CPU MoE layers evaluated 130,792 input tokens without truncation and recovered all three distant lookup codes. This single request took about 29 minutes; it does not establish general quality or speed for other models. See the [settings and full-window results](docs/WINDOWS_16GB_CONTEXT.md).

## Development

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Model reference](docs/AI_REFERENCE.md) · [Build](packaging/README.md) ·
[Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)

Strata is MIT-licensed. Model weights, Hakua-memory and bundled dependencies
retain their own licenses and notices. The optional small control vector is
off by default under the [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE).
