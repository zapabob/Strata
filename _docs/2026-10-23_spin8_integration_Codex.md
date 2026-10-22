# Spin8 / Bonsai integration implementation ledger

## Objective and frozen inputs

Implement the user-approved architecture-independent C/C++/CUDA Spin(8) library, signed Hadamard auditing, Strata and Bonsai adapters, and two-model performance/quality validation.

Strata base: 011c9e600a93bbc9fd451c563501b5831c32bbca.
Triality reference: zapabob/llama.cpp 2c8e9655cdc6ea31051d4437a71492e717d046a4.
Prism runtime: PrismML-Eng/llama.cpp 73bfe6cc485554822f80c473a3c0c4f25e80f41b.
No universal speedup or fourfold inference-speed claim is authorized by mathematical invariance.

## Standards and decisions

Canonical preimplementation prompt was read. Applied PC AGENTS, project AGENTS, common engineering, implementation-start, skill selection, security, LLMOps, C++, Python and TypeScript SOPs. Skills: milspec-codex-standard, deepresearch-defense-standard, executing-plans/subagent-driven-development and performance-optimization.

Work is on codex/strata-spin8-bonsai; the workspace was an empty initialized repository before fetching the fixed source. Build/model/dependency artifacts belong on H:/Strata. No existing model weights may be changed. Existing live inference must be restored after any authorized benchmark interruption. No publish, PR or push is part of this implementation.

## Tasks and interface review

| Task | Producer/consumer | State |
|---|---|---|
| CPU math and audits | C ABI consumed by CUDA and engine adapters | In progress |
| CUDA transforms/attention | consumes immutable CPU-generated representations | In progress |
| Bonsai runtime | pinned source, capability probe, supervisor integration | In progress |
| Strata native adapter | consumes shared CUDA attention ABI | Pending ABI |
| Two-model benchmarks | requires real connected runtime and verified weights | Pending |

CPU/CUDA share public representation matrices and explicit strides. Runtime flags must never advertise an absent implementation. Signed Hadamard determinant may be -1 according to its signs, whereas Spin(8) representation determinants are +1. The weighted aggregate itself has no orthogonality invariant. Baseline flags and dependencies must remain unchanged with the feature disabled.

## Commands and evidence

Source: git fetch --depth=1 origin <fixed Strata SHA>; git switch -c codex/strata-spin8-bonsai FETCH_HEAD.
Baseline CPU: cmake -S . -B H:/Strata/build/baseline-cpu -DSTRATA_BUILD_TESTS=ON -DSTRATA_NATIVE_EXPERTS=OFF -DSTRATA_ENABLE_CUDA=OFF; build in progress.
Model acquisition: uv run --no-project python tools/spin8_model_fetch.py. Uses literal setup.py pins without importing/executing installer; writes only partial data until both pinned length and SHA-256 pass. Missing or mismatching existing model is preserved and refused.

## Acceptance gates (not yet passed)

Both existing Bonsai 27B and Strata Q2_0 must run through connected strict representations. Compare 4K/32K inputs, 3 warmups and 10 paired measurements, >=5% decode improvement target, TTFT regression <=5%, perplexity increase <=1%, no new fixed-case failures. Monitoring overhead target <=1%. Mathematical correctness, unit tests and standalone kernels cannot substitute for these gates.

## Residual work

Implementation and real-model validation are ongoing. No end-to-end speed or quality result exists yet. See per-component logs for fresh command evidence.
