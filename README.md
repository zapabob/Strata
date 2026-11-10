# Hakua / Strata

**[Install the Windows app / Windows版をインストール](INSTALL.md)** · [Search and browser tools](docs/BROWSER_SEARCH.md)

Development candidate: `0.5.5-local.1` / native `0.5.5` / Control `0.5.6`.
`Strata-0.5.5-local.1-windows-x64-setup.exe` is pending source-bound build and
installed acceptance. Downloads below remain the measured `0.5.4-local.1` preview.

Run local language models from a Windows desktop app: chat, reuse your GGUFs,
manage workspace files and choose what Hakua memory may read or save.
This is the [zapabob fork](https://github.com/zapabob/Strata) of
[Niko1221/Strata](https://github.com/Niko1221/Strata), integrating official
**0.2.13** while retaining the fork's memory, model and cache controls.

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Download the Windows preview

**[0.5.4-local.1 prerelease](https://github.com/zapabob/Strata/releases/tag/v0.5.4-local.1)**
targets Windows x64 / CUDA `sm_120`. Checks used an RTX 5060 Ti with 16 GB VRAM
and 32 GB RAM. **Twelve CUDA resource-guard violations remain;
`releaseQualified=false`.** Prism passed an unchanged rerun after one restart
warm-up timeout. Read the [measured scope and limits](docs/HAKUA_RELEASE.md).

| Download | Contents |
| --- | --- |
| [Windows installer](https://github.com/zapabob/Strata/releases/download/v0.5.4-local.1/Strata-0.5.4-local.1-windows-x64-setup.exe) · 112 MB | Tauri NSIS app, private Node/Python and Control. GPU engine is separate. |
| [One-download tar.7z bundle](https://github.com/zapabob/Strata/releases/download/v0.5.4-local.1/Strata-0.5.4-local.1-windows-x64.tar.7z) · 1.65 GB | Same installer, signed engine, Control, signed feed, checksums and bilingual instructions. |
| [Signed CUDA engine](https://github.com/zapabob/Strata/releases/download/v0.5.4-local.1/strata-engine-0.5.4-windows-x86_64-cuda-cuda13.tar.gz) · 1.47 GB | Import this compressed file from the app's preparation screen. |
| [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.5.4-local.1/SHA256SUMS.txt) | Verify downloads before running or extracting them. |

The installer follows upstream's Windows layout. It is a fork distribution,
with fork-signed components; the EXE has no Windows code signature or Tauri
updater signature. Updates are manual. The previous stable
[0.5.1 release](https://github.com/zapabob/Strata/releases/tag/v0.5.1) remains
GitHub Latest and the default stable feed.

### Install in four steps

1. Download the bundle and checksums. Extract the **7z, then the tar**; check
   `BUNDLE-SHA256SUMS.txt` inside. Full model weights and personal data are excluded.
2. Finish requests, unload models, back up app data and quit Strata, including
   its tray icon. Run `Strata-0.5.4-local.1-windows-x64-setup.exe` once.
3. On the preparation screen choose **I already have the file** and select this
   release's `strata-engine-0.5.4-windows-x86_64-cuda-cuda13.tar.gz`, still compressed.
   The app verifies the fork signature and payload hashes before activation.
4. Select a model that fits the PC, or **Use a local GGUF**, then press **Load**.
   Startup leaves models unloaded. System Python, Node, pip and compilers are unnecessary.

The normal app location is `%LOCALAPPDATA%\Programs\Strata`; an older install
may remember another folder. Models, chats and memory retain their separate
data locations. See [installation and rollback](docs/HAKUA_INSTALL.md).

## What the fork adds

- **Existing model reuse.** Select one shard of a split GGUF; the complete set
  is checked in place. Catalog setup reuses a unique valid local match and asks
  when several match. Model files, custom names and verified expert packs remain on disk.
- **Workspace files.** An on-demand sidebar editor can read, edit, create and
  rename files/folders in registered workspaces. Delete uses reversible trash;
  stale edits are rejected. [Workspace guide](docs/WORKSPACE_FILES.md).
- **Private conversation caches.** Supported Qwen3.6 engines reuse a prefix only
  within its authenticated conversation. Owner changes, cancellation, errors
  and idle expiry clear private state. Shared caches remain disabled.
- **Hakua memory.** Reading and saving have separate consent controls for each
  turn. Open the sidebar after loading a supported model; enabling memory for
  PrismML/TurboQuant can restart its owned server. [Memory guide](serve/MEMORY_HARNESS.md).
- **Optional model controls.** Spin(8), Triality, TurboQuant cache settings and
  compatible Qwen3.8 refusal-direction controls remain opt-in. The licensed small
  control vector is off by default; positive Qwen3.8 projection is unqualified.

Native models may need a one-time expert-pack conversion. Progress and resume
reuse existing files where supported. Engine and optional draft-layer downloads
are separate from reuse of the model's GGUF.

| Model path | How to load |
| --- | --- |
| Supported native Qwen / Swift sets | Prepare and load with the native Strata engine. |
| Hikari or another supported PQ2_0 GGUF | **Load with Strata**, using PrismML. No native Q2_0 pack conversion. |
| Ordinary supported GGUF with TurboQuant cache | Choose TurboQuant, K=`FP16`, V=`TURBO2`, `TURBO3` or `TURBO4`, then reload. |

File validation checks structure and compatibility metadata; the engine still
checks actual allocation and model support at load time. A failed or stopped
engine clears the loading indicator. See [local backends](docs/LOCAL_LLAMA_BACKENDS.md).

## Versions and source

| Component | Version / distribution |
| --- | --- |
| Desktop GUI / Host | `0.5.4-local.1` |
| Native CUDA engine | `0.5.4` |
| Control / Terminal | `0.5.5` |
| PrismML / TurboQuant | `0.4.1` / `0.4.0` |
| Private runtimes | Node `24.22.2`, CPython `3.12.15` |
| Hakua-memory | `0.3.5` |
| Upstream integration | `v0.2.13` / `f33c8c30` |
| App / Control build source | `85a78234` |
| Separately frozen native source | `7bb24974` |

Product, Control and engine versions are independent. `SOURCE.json` in the
release records their full commit and artifact identities. See the
[0.2.13 integration record](docs/UPSTREAM_0213.md) for API changes and tests.

## What was checked

Five-job incremental builds, CPU/GPU/sanitizer checks and short native requests
passed: 7 bounded, 7 legacy and 2 restart requests, using 4096 capacity. The
installer passed 13 startup self-tests, matched 29,544 payload files and preserved
4,028 backed-up user files during the measured overwrite. Actual installed
WebView2 Qwen3.6, Prism and workspace checks passed, with the retained Prism timeout.

The resource guard remains **FAIL (12 violations)**. Full-window generation,
general/low-precision model quality, other GPUs/backends and positive Qwen3.8
projection remain unqualified. Full server discovery timed out, six language
catalogs have pre-existing missing keys and a supplemental memory-browser fixture
failed to launch. [Results, failed attempts and limits](docs/UPSTREAM_0213.md).

Native image input and a separate native DeepSeek engine are not included in
this Windows package. Mapped expert packs require a recognized executable;
TurboQuant K modes with failed quality checks remain unavailable. Available RAM,
VRAM and disk space still constrain each model. The [historical 96K–128K results](docs/WINDOWS_16GB_CONTEXT.md)
describe their original artifacts and do not qualify this preview.

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
<a href="https://github.com/kod88vn"><img src="https://github.com/kod88vn.png?size=96" width="48" height="48" alt="kod88vn" title="kod88vn"></a>
<a href="https://github.com/seoulworker"><img src="https://github.com/seoulworker.png?size=96" width="48" height="48" alt="seoulworker" title="seoulworker"></a>
<a href="https://github.com/jackyini"><img src="https://github.com/jackyini.png?size=96" width="48" height="48" alt="jackyini" title="jackyini"></a>
<a href="https://github.com/router0mail"><img src="https://github.com/router0mail.png?size=96" width="48" height="48" alt="router0mail" title="router0mail"></a>
<!-- supporters:end -->
