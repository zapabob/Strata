<p align="center"><img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380"></p>

# Strata

Local LLM inference with a desktop app, a command-line controller and a native engine. This fork retains Spin(8) / Triality, Query-v3, TurboQuant and Bonsai alongside the upstream runtime.

[Project website](https://zapabob.github.io/Strata/) · [Stable v0.3.1](https://github.com/zapabob/Strata/releases/tag/v0.3.1) · [Windows inference preview](https://github.com/zapabob/Strata/releases/tag/v0.3.2-preview.20261027.1)

## Windows inference preview

`0.3.2-preview.20261027.1` packages the engine tested on Windows, RTX 5060 Ti 16 GiB and 32 GiB system RAM. It is a CUDA 13 / SM120 preview, not a new desktop installer. Existing models and settings are retained by the local overlay installation.

The tested configuration is Qwen3.8 Q2_0, capacity **131072**, **spec4 + MTP**, **k8v4**, and a 256-token output reservation. Startup profile prefetch now uses joined threads so completed batches release their retained I/O scratch.

| Actual input | First and repeated generation | Recall check | Cleanup |
| --- | --- | --- | --- |
| 4096 tokens | Both completed, 52 output tokens each | Both passed | Zero remaining Job processes |
| 32768 tokens | Both completed, 52 output tokens each | Both passed | Zero remaining Job processes |

These runs had source and controller diagnostics OFF. The 32K first prompt took 494.76 seconds; the repeated prompt took 0.646 seconds with prefix reuse. Decode took 13.759 and 3.255 seconds respectively. These are observations from one synthetic task, not a statistical speed or broad quality claim.

The fixed Windows Job commit cap was 29.8125 GiB; the 32K Job peak was 22.69 GiB. This cap is an explicit safety condition, separate from physical RAM and context capacity. Earlier 10 GiB attempts failed before READY. The larger condition was separately authorized; there was no automatic memory-cap escalation.

A 64K trial was intentionally cancelled after the user changed acceptance to reliable working inference. Full-length 126000-token inference with at least 512 generated steps, exact final-cell device boundaries, PPL/KL, paired statistical performance, 32-turn/2-hour stability, image inference and HIP/SYCL remain unqualified. The preview does not claim full 131k certification. Same-source cloud CI is reported separately from local tests and actual inference.

Read [the measurement record](docs/PERF131K.md), [machine-readable status](docs/perf131k-status.json), and the archive's README and status before using this preview. Previous previews and historical failures remain documented.

## Install and use

For the desktop app, use the appropriate release installer and follow [INSTALL](docs/INSTALL.md). The Windows inference preview archive is an engine/component overlay for an existing installation; it is not a desktop setup executable. Keep the previous component and rollback backup.

For terminal setup and explicit model selection, follow [AI_SETUP](docs/AI_SETUP.md) and [TERMINAL](docs/TERMINAL.md). Check the proposed configuration before starting a model:

```sh
strata launch --plan --family qwen --model q2_0
```

Use the model files already present on the machine where possible. Leave the listener on `127.0.0.1` unless remote access is needed. Model downloads, hardware compatibility and licenses are documented in [MODELS](docs/MODELS.md).

The preview includes its required CUDA/VC runtimes and notices. The legacy vision executable is retained unchanged for compatibility; image inference is not validated by these text tests. No model weights, API keys or user conversations are distributed.

## GUI fixes in this preview

Quiet local inference now has a finite 30-minute allowance instead of the previous four-minute cutoff. Remote-model and running-tool limits remain separate, and cancellation still ends a stalled turn.

The local GGUF importer validates the file and tokenizer without restricting text models to a short architecture list. When the native engine cannot import a model, **Try with llama-server** opens the generic path with the same file selected. The GUI companion package supplies the tested generic backend. Actual architecture support is checked when loading; auxiliary files and unsupported configurations report their reason.

Missing K/V metadata is shown as an unknown fit with a provisional estimate. Models whose head width cannot use the selected quantized cache request explicit FP16 selection. A backend that exits immediately reports its error promptly, and a failed load can be retried after correcting settings without downloading the same file again. Invalid K/V settings are rejected before stopping a running native model.

The runtime now records that no child has been launched before publishing its host state. This closes a recovery gap if the host stops before launching the server. Missing child ownership records still require inspection; the app does not guess which process to stop. On the test PC, the exact legacy orphan state was preserved after verifying that its host and listener were absent.

The GUI/host regression set passed 36 tests; four additional tests passed with the real installed Harness. A small GGUF completed import, load, chat generation and unload through the GUI's actual host API, using an isolated synthetic profile and explicit FP16. The frontend builds successfully. Interactive screen testing was unavailable in this session; it is not claimed.

## Memory integration

The optional memory harness is **disabled by default**. It requires server-side per-user identities, isolated databases, approved persona hashes and explicit per-turn consent. Normal requests keep their existing path. Native multiuser memory behavior and its resource/latency qualification remain open. See [MEMORY_HARNESS](serve/MEMORY_HARNESS.md).

## Development and verification

The tested executable SHA-256 is `20373ca6b9b16b9d220820a902b584d604a64e068d383a26ba11dd4e43f85d93`. The engine source checkpoint is `56c4613be8e5f63868f8dbd52e41ab644a324aba`; later controller and documentation commits are separate.

The integrated CPU gate ran 88 tests with two Windows symlink subcases skipped. The native controller passed 15 tests; package and overlay tests passed 23. These checks complement actual inference; they do not substitute for untested backends or long-run stability. The offline statistical executor passed 16 synthetic tests; measured paired comparisons have not been run.

The code is split between the [engine](src/), [server](serve/), [Terminal](strata_cli/) and [desktop/host](apps/). Build and API details are in [DETAILS](docs/DETAILS.md); model-specific and platform guidance is in [docs](docs/). Other hardware and model families have separate requirements and are outside this Windows preview's tested scope.

Read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md) before changing the project. Preserve existing inference features, keep new features opt-in, and provide actual evidence for performance claims. Local evidence and private model/configuration files are not committed.

## License

[MIT](LICENSE). Based on [Niko1221/Strata](https://github.com/Niko1221/Strata), with work by the upstream and fork contributors, Spin(8)/TurboQuant authors and model authors. Model licenses remain separate. Runtime redistribution notices accompany the archive.
