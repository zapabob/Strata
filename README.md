<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380">
  </picture>
</p>

<p align="center"><b>English</b> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.pt-BR.md">Português</a></p>

# Strata

Local LLM inference with a desktop app, a command-line controller and a native engine.
This fork retains Spin(8) / Triality, Query-v3, TurboQuant and Bonsai alongside the
upstream runtime. See [setup](docs/AI_SETUP.md), [engine details](docs/DETAILS.md)
and the [Terminal guide](docs/TERMINAL.md).

## Releases and current verification

[Stable release v0.3.1](https://github.com/zapabob/Strata/releases/tag/v0.3.1) ·
[Published experimental preview](https://github.com/zapabob/Strata/releases/tag/v0.3.2-preview.20261026.1) ·
[Measurement status](docs/PERF131K.md)

The published preview and the development candidate are different artifacts.
The candidate below has not been released or installed. The existing desktop app,
Control settings, models and installed engine have not been replaced by this build.

| Scope, checked 26 October 2026 | Result |
| --- | --- |
| Startup, diagnostics and statistics CPU tests | 43 passed with `pytest-randomly` disabled |
| Opt-in memory harness tests | Python 3.12 ran 27 tests, including temporary-profile real hakua writer; two Windows symlink subcases skipped for missing privilege. Approved persona hashes checked; native multiuser isolation remains unqualified |
| Fresh Windows CUDA SM120 `Release/x64` engine link | Passed with GGML `3cf0325`, CUDA 13.3 and MSVC |
| Windows native preview CPU checks on the pushed branch | Spin8 6/6, tqcodec 10/10, packaging tests 12/12 passed; Linux, HIP and SYCL not checked |
| Opt-in 131072 boundary admission | `130048+1024` and `131071+1` accepted by strict API mock; one-over rejected; native CPU contract and CUDA link passed. Serial serving only; final-cell device execution NOT_RUN |
| Same-source GitHub Actions | NOT_RUN: branch push produced no run; manual dispatch returned HTTP 422 saying Actions is disabled |
| Fresh executable read-only `--help` | Exit 0; no model loaded |
| Earlier 10 GiB Job diagnostic | RAN_FAILED_BEFORE_READY; this was a different executable |
| Fresh candidate GPU startup / completed model inference | NOT_RUN |
| Paired performance statistics / cross-validation evaluation | Offline executor passed 16 synthetic tests; analyzer hash freeze and five fixed grouped evaluation summaries supported. Measured pairs and fitting/tuning NOT_RUN |
| PPL / KL / full-context quality / stability | NOT_RUN |
| Practical 131072-token qualification | NOT_QUALIFIED |
| Fresh build source and artifact hashes | Startup fix `dd0b797a`, benchmark executor `fe7f5159`, boundary contract `00c1b770` plus mode guard `6955c759`; local binary and inputs hashed |

One earlier candidate pilot ended before READY. Controller-observed elapsed
time was 41.61 seconds, including monitoring and cleanup. The controller
reported Job-limit status 125; the preserved native exit was 1. Job peak commit was
10,740,895,744 bytes against 10,737,418,240 configured. No request completed. The
bounded snapshot retained 32 host allocation failures and dropped 99 records; it
does not establish a direct causal link to the terminal blob-null pair. The Job
terminated with no remaining processes. No automatic retry or cap increase occurred.

The current candidate is a fresh Windows `Release/x64` CUDA SM120 build. It
compiled and linked the engine, Spin8, native cache and GGML TQ overlay. The
build does not establish model startup, inference quality or GPU stability.
The latest candidate executable is 80,752,128 bytes:

```text
SHA256 20373ca6b9b16b9d220820a902b584d604a64e068d383a26ba11dd4e43f85d93
```

The selected installed preview executable still has SHA256
`4281dd8b886f4863fd85e71e35c4fe64c084c4cdb9ce1cd1029c5dbbed958610`.
Published archives have their own checksums; the candidate checksum above is not
an archive checksum or a signature. The earlier startup build, `strata_kq.dll`,
both GGUF shards, the pack, MTP files, tokenizer and expert profile are recorded
under `H:\Strata\evidence\p01-full-build-20261026`. Its source and binary link
is in `build-provenance-after-complement.json` there. The later boundary build
and CPU checks are bound to source commit `6955c759` in
`H:\Strata\evidence\p01-boundary-20261026\p02-cpu-receipt-after-review.json`.
Source commits `73cfa347` and `56c4613b` replace task-pool profile prefetch with joined threads
so completed batches release their thread-local I/O scratch. Its CPU lifetime
test, CUDA link and read-only help passed; model execution remains NOT_RUN.
The current artifact binding is `joined-prefetch-receipt.json` in that directory.

## What the candidate changes

Default-OFF blob diagnostics record the failed branch, requested bytes and known
Win32/CUDA error codes. A fixed 32-record buffer reports pending/dropped records;
unknown values remain unknown. Startup profile blob acquisition and transfer
failure are distinguished. Existing I/O order, issued-request drain, scratch/event
lifetime, pageable/mapped fallback and the original class ABI are preserved.

The Windows controller keeps the observed native exit separately from its own
budget or cleanup status. Job commit, process working set, physical available RAM,
VRAM and disk traffic remain different measurements. A Job limit is not a physical
RAM reservation or a guarantee that a model will fit.

Normal execution keeps tracing and blob diagnostics OFF. The disabled diagnostics
add no CUDA calls, events, GPU synchronization, worker or output I/O. This source
property is CPU/static-verified; runtime overhead is not measured yet.

## The 131k evaluation contract

The normal series fixes the same Q2_0 weights/pack/tokenizer, spec4 + MTP, k8v4,
Attention views and capacity 131072. The initial diagnostic uses 4096 input tokens
and an explicit 256-token output reservation. A draftless diagnostic is a separate
series. Trace OFF/ON comparisons use the same series and exact token inputs.

Older executables stopped before READY in Job-limited startup attempts, including
10 GiB. Those failures yielded no completed inference and no throughput or quality
result. The earlier candidate diagnostic also stopped before READY, as recorded
above. The fresh executable has not been used for a model launch. No smaller capacity,
model substitution, silent output-reservation shortening or precision reduction is
accepted as a 131k pass. The internal 8-token slack remains a separate unresolved
capacity-contract item.

The [statistical protocol](docs/perf131k-statistical-protocol.json) is a design,
not a result. It groups all variants/repetitions of an original task into the same
held-out fold and independent statistical unit. Candidate and baseline use paired
inputs and balanced run order. Paired effects, group bootstrap intervals and paired
label-swap tests are planned; fold count and technical repetitions do not inflate
sample count. A nonsignificant difference does not prove equivalence.

Full qualification additionally requires the 64K stage, validated full-length
boundaries after the capacity-contract fix, approximately 126K history with at
least 512 actual generation steps, and 32 turns / two hours of stability. Retrieval,
Japanese, English and code tasks need frozen scoring, plus a same-weights reference
for PPL/KL. A short recall probe, READY line or CPU fixture cannot establish these.
Historical benchmark numbers from other contexts are not current 131k evidence.

## Installation

Use the release notes for the exact artifact you select. The experimental native
archive supplies the engine and required DLLs plus a small overlay for an existing
matching Control installation. It is not a new GUI installer or a complete standalone
HTTP distribution. Models and private configuration are not bundled.
The current development overlay requires `memory_harness.py`, `perf131k_e2e.py`
and `server.py` as three hash-verified Control payload files. Both imported
helpers are placed before the server. Missing payload blocks installation before
backup or publication. On failure, existing Control files are restored; newly
created inactive helpers are retained with the rollback evidence. This change
has passed 11 synthetic file-installation tests and has not been installed live.

For general setup, start with [AI_SETUP.md](docs/AI_SETUP.md). To inspect an existing
Terminal installation without starting a model:

```powershell
strata --version
strata launch --plan --model q2_0
```

An overwrite update must preserve model files, user configuration and rollback
artifacts. The current development candidate has not passed the runtime/release
qualification gates and has not been used for an overwrite update.

## Components and retained functionality

| Area | Source / documentation |
| --- | --- |
| Native engine and CUDA backends | [src](src/) / [include](include/) / [engine details](docs/DETAILS.md) |
| Spin(8), Triality and Query-v3 | [spin8](spin8/) |
| TurboQuant and cache dialects | [tqcodec](tqcodec/) |
| Model inspection and local control | [strata_control](strata_control/) / [Terminal](docs/TERMINAL.md) |
| Server and API | [serve](serve/) |
| Desktop and Host | [apps](apps/) / [packaging](packaging/README.md) |
| Bounded measurement and controller tests | [tools/perf131k](tools/perf131k/) / [tests/perf131k](tests/perf131k/) |

This checkpoint does not change the model, K/V precision or number of Attention
views to make a benchmark pass. Other model families and backends have their own
requirements; see [AMD](docs/AMD_HIP.md), [Mac](docs/MAC.md) and
[Intel](docs/INTEL.md) documentation. They are outside this Windows candidate's
verification scope. Existing Hermes/Hakua integrations remain separate from the
131k performance and quality qualification.

## Evidence and contributing

P00 and P01 remain PARTIAL. Local source/binary manifests, raw receipts and
independent reviews distinguish CPU checks, host compile/link, real inference and
release validation. Machine-local evidence, model files and environment backups
are not published in this repository. Local pilot helpers require explicit bindings
and resource gates; they are not a general-purpose model launcher.

CI must succeed on the exact release source commit. The engine fix, offline
analysis and disabled-by-default memory harness are committed locally as
`dd0b797a`, `fe7f5159` and `fb51a51c`. The branch has been pushed, but no
same-source CI result exists. The historical `e68f8926`
checkpoint has successful workflows; that is not a pass for the current candidate.
Actions permissions currently report enabled, but this alone does not prove the
previous HTTP422 dispatch problem is resolved. Candidate-source CI is pending.

Read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md) before changing
the project. Preserve the original inference features and provide raw, reproducible
measurements for performance claims.

## License and acknowledgments

[MIT License](LICENSE). Based on [Niko1221/Strata](https://github.com/Niko1221/Strata),
with work by the upstream contributors, the fork contributors, Spin(8)/TurboQuant
authors and the model authors. Model licenses remain separate from the software license.
