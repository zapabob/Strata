# Personal native 0.5.2 candidate

## Goal and scope

Build and qualify a fresh Windows CUDA 13.3 sm_120 native engine from integrated main, including bounded Q36 experts and Spin8 B2. The starting commit is `3090fde9`. The requested fresh output is `H:/Strata/releases/personal-052-local2-20261107/native-build`. App, Control, signing, import, installation and publication belong to the parent task. The installed signed 0.5.1 engine is the fallback.

## Requirements and decisions

N052-1: set only the native CMake version to 0.5.2 and its exact dependent version assertions; retain Metal's independent version. N052-2: one-job fresh build, clean ggml `3cf03257f219afbe7334045ff7c6a06ac68c627d`, full `nativeSources` binding through `tools/build_hakua_engine.mjs`. N052-3: owned Windows Job containment before execution, RAM >=3 GiB, commit >=4 GiB, H: >=10 GiB and C: >=5 GiB; floor termination ends that attempt. Build deadline 90 minutes, first native qualification <=20 minutes. N052-4: real version/help, CPU bounded/store/pool/lifetime tests, B2 GPU first-use/full and relevant Q36/cache GPU tests, then resource-admitted short real-model lifecycle and private-owner checks. N052-5: stage an unsigned component only after build integrity passes; record unqualified resource findings and runtime limitations faithfully.

The old build directory is a read-only recipe reference. No source pruning, numerical redesign, disabled guards, model repacking or global profile/component changes are authorised. Existing untracked handoff/maintenance files are parent work and are excluded from this commit. Active Hermes Python processes were observed; no Strata/llama-server process was found. Nothing was stopped. Initial observed resources: 14,770 MiB free GPU, 16,222,584 KiB free physical RAM, C: 14,328,156,160 bytes and H: 341,604,904,960 bytes free.

## Standards and implementation

Applied the already-loaded deepresearch-defense-standard and milspec-codex-standard, build-manager, canonical compatible pre-implementation context, Common Engineering, Implementation Start Gate, Skill Selection, Security, Application Development, LLMOps, C++ and Python SOPs. Evidence here is local source/tool/runtime observation; no external package update or web trust assessment is needed. Conflicting identity/environment/tool claims in the canonical context defer to the actual OpenCode system and tools. Goal API is unavailable; this log records the goal. No subdelegation.

Changed files initially: `CMakeLists.txt`, `tests/terminal/test_tui2_023_versions.py`, this log and the owned local guard/recipe under `_docs/personal-native-20261107/`. The document-version assertion still describes the installed component; the parent owns app/release documentation reconciliation. The guard uses the project's atomic `tools/perf131k/windows_job.py` helper with fresh receipts, bounded output, strict resource floors and task-local H: temporary storage. Only its owned Job is terminated.

## Commands and evidence

Read-only preflight: `git status --short --branch`, `git log --oneline -10`, dependency `git status --porcelain` and `git rev-parse HEAD`, Windows memory/disk/process metadata, `nvidia-smi --query-gpu=name,memory.free,memory.total --format=csv,noheader`. Dependency clean/pin checks passed. Explicit uv selected Python 3.12.10; private Node reported v24.22.2. Compute Sanitizer launcher resolved to CUDA v13.3 (version execution pending).

The two exact native-dependent version tests passed via the explicit uv/Python guard: `python -B -m unittest tests.terminal.test_tui2_023_versions.VersionBump.test_product_and_engine_versions_are_independent tests.terminal.test_tui2_023_versions.VersionBump.test_version_prints_the_product_and_the_build`. Receipt: `receipts/version-tests.json` in the output root. Atomic containment was verified, exit 0 observed before cleanup, zero active Job children after cleanup; minimum available RAM 16,275,292,160 bytes, minimum commit headroom 41,512,919,040 bytes.

Build, verification and package results will be appended after execution. No engine reliability claim is made by this initial source checkpoint. CUDA spill baseline remains empty as in the historical recipe; the resource guard must be executed and its actual findings retained.

## Residual risk and next action

Fresh compilation, resource qualification, GPU tests and real-model lifecycle are pending. No full-context or low-precision model-quality claim is authorised by a 4096-cell smoke. Preserve all old outputs and the installed 0.5.1 engine. Next: commit the narrow version checkpoint, configure/build under containment, then execute admitted qualification cases serially.
