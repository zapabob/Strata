# Hakua / Strata

**Source integration candidate:** official `v0.2.12` / latest main at `146df3c4`,
with Hakua and the fork's runtime/state contracts retained. Native builds and
hardware qualification are pending. See [the integration record](docs/UPSTREAM_0212.md).

The installed personal `0.5.2-local.2` build
(`Strata-0.5.2-local.2-windows-x64-setup.exe`, Control `0.5.3`, native `0.5.2`,
PrismML `0.4.1`) was measured **before** this source merge. Its four resource-guard
failures remain open; `releaseQualified=false`. The download links below describe
published `0.5.1`, not a new installer for this integration.

Version 0.5.1 adds manual model loading and fixes native Qwen3.6 startup. Existing models and verified expert packs are retained.

Run local language models in a Windows desktop app, with chat, model controls,
tools and optional Hakua memory. This is the [zapabob fork](https://github.com/zapabob/Strata)
of [Niko1221/Strata](https://github.com/Niko1221/Strata).

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Windows release

Native Qwen3.6 reached READY in 41.250 seconds with a 4096-cell configuration and passed six short private-cache checks. A full 98K/131K input and FP16/NVFP4 model quality are not qualified. Read the [test results and limits](docs/HAKUA_RELEASE.md).

This release targets Windows x64 CUDA sm_120. Local checks used an RTX 5060 Ti with 16 GB VRAM and 32 GB RAM. Read the [release checks and remaining limits](docs/HAKUA_RELEASE.md) before installing.

Product version: **0.5.1**. The release contains the setup EXE
and its checksums. It uses manual updates and has no Windows code signature.

1. Get the [Windows installer](https://github.com/zapabob/Strata/releases/download/v0.5.1/Strata-0.5.1-windows-x64-setup.exe)
   and compare it with [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.5.1/SHA256SUMS.txt).
2. Quit an existing Strata instance, including the tray app, then run the installer.
   Keep models and personal data outside the application folder.
3. Install the signed CUDA component from the preparation screen, using the latest feed or the included `strata-engine-0.5.1-windows-x86_64-cuda-cuda13.tar.gz`. Node and Python are included; no system interpreter, pip or compiler is needed.
4. Choose a model that fits the computer, or select **Use a local GGUF** for
   files already on disk.

See [installation](docs/HAKUA_INSTALL.md), [release checks and limits](docs/HAKUA_RELEASE.md)
and the [release page](https://github.com/zapabob/Strata/releases/tag/v0.5.1).
The fork uses its own installer and component feed.

Versions follow [SemVer 2.0.0](https://semver.org/): app `0.5.1`, native engine `0.5.1`, Control `0.5.1`; unchanged PrismML/TurboQuant runtimes stay `0.4.0`. The default app location is `%LOCALAPPDATA%\Programs\Strata` on C:, independently of the model folder. Existing installs may remember another drive.

The NSIS installer is also included in the [tar.7z bundle](https://github.com/zapabob/Strata/releases/download/v0.5.1/Strata-0.5.1-windows-x64.tar.7z), together with the signed CUDA component, Control, checksums and installation instructions. Model weights and personal data are excluded. The release uses `v0.5.1`, the `latest` tag alias and GitHub Latest.

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
| Desktop GUI / Host | `0.5.1`, this app release |
| Native engine | `0.5.1` |
| Control | `0.5.1` |
| Private runtimes | Node `24.22.2`, CPython `3.12.15` |
| Hakua-memory | `0.3.5` |
| CUDA / PrismML / TurboQuant component candidate | [release status](docs/HAKUA_RELEASE.md) |
| Upstream source reference | `5d37280d`, upstream `0.2.11` |

Version 0.5.1 integrates upstream 0.2.11 and main fixes through `5d37280d`: per-chat files, active-turn reattachment, IME input fixes, renderer recovery, updated model sets, stream ownership fixes and Pillow 13. Hakua memory, local GGUF reuse and Qwen3.6 private caches remain available. The new CUDA build needs its own qualification; historical 0.4.1 results do not qualify its new defaults. Native full-window generation remains unqualified. See [release checks and publication status](docs/HAKUA_RELEASE.md).

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
shared prompt and conversation caches disabled. Its mapped expert pack remains
opt-in and checks an executable-digest allowlist. Experimental kernel switches
are separately opt-in. The legacy host
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

## Supporting upstream Strata

Thank you to everyone who supports Strata.

<!-- supporters:start (one line per public supporter, newest last; copy a line and change the GitHub name in all four places) -->
<a href="https://github.com/ryan4yin"><img src="https://github.com/ryan4yin.png?size=96" width="48" height="48" alt="ryan4yin" title="ryan4yin"></a>
<a href="https://github.com/themactep"><img src="https://github.com/themactep.png?size=96" width="48" height="48" alt="themactep" title="themactep"></a>
<a href="https://github.com/macintog"><img src="https://github.com/macintog.png?size=96" width="48" height="48" alt="macintog" title="macintog"></a>
<a href="https://github.com/bisonbet"><img src="https://github.com/bisonbet.png?size=96" width="48" height="48" alt="bisonbet" title="bisonbet"></a>
<a href="https://github.com/vizv"><img src="https://github.com/vizv.png?size=96" width="48" height="48" alt="vizv" title="vizv"></a>
<!-- supporters:end -->
