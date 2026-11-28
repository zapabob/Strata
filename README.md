# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

Hakua / Strata is the Windows-focused fork of [Niko1221/Strata](https://github.com/Niko1221/Strata). It runs local models for chat, coding and agent workflows. On compatible models, the native runtime can place mixture-of-experts weights across GPU memory, system RAM and SSD storage.

## Install on Windows

Download the per-user setup program from [Hakua Releases](https://github.com/zapabob/Strata/releases/latest). CUDA engines and model weights are separate downloads. Follow the [Windows guide](docs/HAKUA_INSTALL.md) to install the engine for your model. To use an Inkling 2 Mini SC117 pack, choose the matching SQ-10, SQ-15 or SQ-20 profile under **Models** and set a context length that fits your available memory.

## Inkling 2 Mini CHiPS

Hakua 0.8.9 incorporates the Strata 0.2.23 release changes, including local Inkling SQv2 and the 16 KiB `.strata` layout. Install the [Inkling CUDA companion](docs/HAKUA_INSTALL.md#inkling-2-mini-chips), then import the existing pack with **Models → Use local model files**. The import gives the model its own identity and reads the weights from their existing path. Start with a single 4,096-token slot and drafting and vision off. The complete CHiPS SQv2 pack passed a real chat completion on an RTX 5060 Ti 16 GB. [CHiPS model files](https://huggingface.co/Kujira/Inkling-2-Mini-Strata-CHiPS-Abliterated) · [Verification record](_docs/2026-11-28_upstream-023-hakua_Codex.md)

## Reuse agent workflows

Open **Settings → Tools** and enable **Find skills on demand** to omit the full skill catalogue from agent requests. The agent can search and open one skill as needed. In **Skills**, enable learning from completed work and automatic application independently. A saved workflow is an editable `SKILL.md`. Automatic application uses skill names, trigger phrases and workspace scope. The **Skills** and **Helper assistants** switches are separate from file operations and `/goal`. See the [workflow guide](docs/WORKFLOW_SKILLS.md).

The installed Harness passed 33 tests covering streaming, approvals, Stop and resume with a scripted provider. The DS4 launch and adapter paths remain available. Real-weight DS4 generation, maximum-context retrieval and concurrent GPU use have separate verification requirements. Component compatibility and signing are described in the [release record](docs/HAKUA_RELEASE.md). Hakua uses the [MIT licence](LICENSE). Models and bundled components have separate terms.
