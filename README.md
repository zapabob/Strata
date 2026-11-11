# Hakua / Strata

Local AI on Windows, with separate side questions, research with sources and your
choice of models, memory and tools. This is the [zapabob fork](https://github.com/zapabob/Strata)
of [Niko1221/Strata](https://github.com/Niko1221/Strata), integrating upstream 0.2.13.

[Install on Windows](INSTALL.md) · [日本語](README.ja.md) · [Search and research](docs/BROWSER_SEARCH.md) · [Measured limits](docs/HAKUA_RELEASE.md)

## Download

The **0.5.7-local.1 preview** adds real `/btw` subagents, workflow skill learning
and automatic skill application. It retains `/deepresearch` and bundled
**RustXNG 0.31.1 Full**. It uses upstream's Windows app layout: a per-user Tauri
NSIS installer with private Node/Python and Control. The signed GPU engine is
separate. The complete tar.7z includes the identical installer.

| Package | Download |
| --- | --- |
| Windows x64 installer | [Setup EXE](https://github.com/zapabob/Strata/releases/download/v0.5.7-local.1/Strata-0.5.7-local.1-windows-x64-setup.exe) |
| Installer, engine and instructions together | [tar.7z bundle](https://github.com/zapabob/Strata/releases/download/v0.5.7-local.1/Strata-0.5.7-local.1-windows-x64.tar.7z) |
| Download verification | [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.5.7-local.1/SHA256SUMS.txt) |
| Previous preview / stable | [0.5.6-local.1](https://github.com/zapabob/Strata/releases/tag/v0.5.6-local.1) / [0.5.1](https://github.com/zapabob/Strata/releases/tag/v0.5.1) |

The preview delivery is tracked at [the release](https://github.com/zapabob/Strata/releases/tag/v0.5.7-local.1). The [delivery record](_docs/2026-11-11_workflow-skill-learning_Codex.md)
records installation, archive and public-download verification. Stable GitHub Latest and the
stable feed stay unchanged. This is a fork distribution; it is not endorsed by
upstream. The EXE has no Windows code signature; component signatures are separate.

## Install or update

Finish requests, unload models, back up app data and quit Strata, including its
tray icon. Run the EXE using the existing installation folder. Models, chats and
memories live separately from the installer-managed files.

For the bundle, extract **7z first, then tar**, and check the internal
`BUNDLE-SHA256SUMS.txt`. It contains the same EXE, signed native 0.5.5 engine,
Control 0.5.6 and instructions. Import the compressed engine package using
**I already have the file** in the app. Full model weights and personal data are
excluded. System Python, Node and compilers are unnecessary.

Select a compatible model or **Use a local GGUF**, then **Load**. Startup leaves
models unloaded. [Installation, data paths and rollback](docs/HAKUA_INSTALL.md).

## Ask alongside the main task

```text
/btw What does the last error mean?
```

A real subagent starts under a dedicated side-question parent and answers below
the conversation. It receives a snapshot of completed messages and has no tools. It does not interrupt the main task or add its question
or answer to the main agent's context. Stop and dismiss controls affect only the
side question. Up to five answers are saved with the chat; unfinished answers
are marked interrupted after reload. With one model request slot, inference can
wait behind the main request.

## Research with sources

```text
/deepresearch Compare the current requirements using official documentation
```

With an agent model and web search enabled, the assistant gathers evidence before
writing. The host checks for three distinct successful queries and four distinct
successful page reads. One bounded follow-up asks for missing evidence. If those
checks remain incomplete, the writing step must state the limitation. These
counts do not establish accuracy or exhaustiveness. Existing `/research` remains
the shorter workflow.

Choose **RustXNG Full (no key)** in **Settings → Tools → Web search**. The app
starts the pinned local service on `127.0.0.1` when needed and stops it with
the host. There are no runtime downloads or self-updates. Manual **Search web**
also uses the selected provider and attaches snippets to one tool-free answer.

Full sends queries to enabled external providers, including providers with
restrictive or unreviewed automation terms. Use only providers you have permission
to access. Paid sources need their own setup and are not activated by a Strata
search key. Existing provider choices, saved keys and approval controls remain
available. Search errors are visible; RustXNG is not silently replaced.

## Learn and apply workflow skills

Open **Skills** to enable learning from completed agent work and automatic
application independently. The same task model reviews bounded, redacted tool
metadata and may save a private, editable SKILL.md. Future matching workflows
receive complete enabled instructions, with trigger phrases and workspace scope.
Manual edits and approval choices are preserved; revision history and undo are
available. New profiles keep both options off.
[How it works and its limits](docs/WORKFLOW_SKILLS.md).

We appreciate [Hermes Agent](https://github.com/NousResearch/hermes-agent) for
its work on reusable procedural skills, which inspired this document-based loop.

## Existing capabilities

Reuse compatible GGUF shards and validated expert packs. Supported PQ2_0 models
use PrismML; compatible ordinary GGUFs can use TurboQuant cache modes.
[Model paths](docs/LOCAL_LLAMA_BACKENDS.md).

Read, create, edit and rename workspace files/folders in the sidebar. Delete uses
reversible trash, stale edits are rejected, and folder history cleanup requires
confirmation. [Workspace guide](docs/WORKSPACE_FILES.md).

Hakua memory has separate read/save consent per turn. Private conversation caches
stay scoped to authenticated conversations; shared caches stay off. Spin(8),
Triality and experimental projection remain opt-in.
[Memory guide](serve/MEMORY_HARNESS.md).

## Versions and verification

| Component | Version |
| --- | --- |
| Desktop / Host | 0.5.7-local.1 |
| Native CUDA engine | 0.5.5, frozen source b995af13 |
| Control / Terminal | 0.5.6, retained from the previous preview |
| RustXNG | 0.31.1 Full, official unmodified Windows executable |
| PrismML / TurboQuant | 0.4.1 / 0.4.0 |
| Private Node / Python | 24.22.2 / 3.12.15 |
| Upstream integration | 0.2.13, f33c8c30 |

On 2026-11-11, RustXNG Full returned five results each for two public documentation
queries in 1783 ms and 902 ms on this PC/network. These are functional checks,
not general search or generated-answer quality measurements. New installer and
installed-app evidence is in this preview's [delivery record](_docs/2026-11-11_workflow-skill-learning_Codex.md).

Native qualification remains tied to the existing 0.5.5 artifacts and their
recorded RTX 5060 Ti 16 GB / 32 GB RAM conditions. Full-window generation, broad
model/low-precision quality, other hardware and autonomous research quality
remain unqualified; `releaseQualified=false`. The Windows engine has no native
image input or separate native DeepSeek engine.
[Evidence and retained failures](docs/HAKUA_RELEASE.md).

## Development and licenses

```sh
npm --prefix apps/host test
npm --prefix apps/host run typecheck
node apps/desktop/scripts/stage-rustxng.mjs --execute
```

[Packaging](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)

Strata is MIT-licensed. Bundled components and model weights keep their own
licenses. RustXNG is a separate AGPL-3.0-or-later program. Its LICENSE, NOTICE,
source identity, checksums and corresponding source archive are installed under
`harness/rustxng`. [RustXNG documentation](https://github.com/sahenjp/RustXNG/tree/v0.31.1).

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

## Acknowledgements

We are grateful to the [Strata](https://github.com/Niko1221/Strata) developers for their careful work on local inference and an approachable desktop experience. This fork builds on that substantial foundation.

Our appreciation also goes to [llama.cpp](https://github.com/ggml-org/llama.cpp) and its contributors for making C/C++ model inference accessible to developers and users, and to [RustXNG](https://github.com/sahenjp/RustXNG) for a useful, open search and evidence-retrieval service for local AI. Their engineering and continued maintenance deserve recognition.

The integrations and modifications in this fork are maintained independently; these acknowledgements do not imply endorsement.
