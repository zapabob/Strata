# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

Hakua / Strata is the Windows-focused fork of [Niko1221/Strata](https://github.com/Niko1221/Strata). It runs local models for chat, coding and agent workflows. On compatible models, the native runtime can place mixture-of-experts weights across GPU memory, system RAM and SSD storage.

## Get started

Download the Windows per-user installer from the [Hakua releases](https://github.com/zapabob/Strata/releases). The CUDA engine is distributed separately. In the app, open **Models** and choose the installed variant explicitly. For an Inkling 2 Mini SC117 model, choose its matching SQ-10, SQ-15 or SQ-20 profile. Set a context length that fits the available memory. See the [Windows guide](docs/HAKUA_INSTALL.md) and [model documentation](docs/MODELS.md).

## Reuse agent workflows

Open **Settings → Tools** and enable **Find skills on demand** to omit the full skill catalogue from agent requests. The agent can search and open one skill as needed. In **Skills**, enable learning from completed work and automatic application independently. A saved workflow is an editable `SKILL.md`. Automatic application uses skill names, trigger phrases and workspace scope. The **Skills** and **Helper assistants** switches are separate from file operations and `/goal`. See the [workflow guide](docs/WORKFLOW_SKILLS.md).

## Measurements and limits

On an RTX 5060 Ti 16 GB, SC117 SQ-10 wrote a single-file Pagoda Bench scene from Strata’s `/goal` and repaired its own renderer after diagnostic feedback. Chrome displayed all five roofs after zooming out. The scene reported 7,079 voxels. The initial view cropped the top and no official score was measured. The [0.8.5 engine measurements](_docs/2026-11-27_v085-release-notes.md) use short inputs at the stated context capacity. A configured capacity does not establish full-length retrieval.

Component compatibility, installer signing and tested limits are documented in the [release record](docs/HAKUA_RELEASE.md). Hakua is distributed under the [MIT licence](LICENSE). Models and bundled components have separate terms.
