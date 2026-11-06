# Multi-model Spin8 CUDA 13.5 Implementation Plan

> For Hermes: use subagent-driven-development for bounded implementation tasks, then independent spec and quality review.

**Goal:** Implement the user's revision-2 A–H plan without publishing unfinished work as a completed product.

**Architecture:** Keep the audited Spin(8) numerical core independent of model semantics. Introduce versioned layer/tensor contracts, then native and external graph adapters and session-owned transactional state. Do not advertise combinations from independent feature booleans or infer model qualification from compilation.

**Tech stack:** Existing C++17 Spin8 C ABI, CUDA, C++20 native engine, GGML/PrismML, Python Control and Node/TypeScript Host. Reuse pinned dependencies and resource guards.

## Authority and frozen inputs

- User-approved scope: stages A–H, followed only after their applicable acceptance gates by overwrite-install, release/tag and official-style installer README.
- Baseline: `c50ca06a863a98ff121cbff30365a035a90205e2`.
- Supplied design: [revision 2](2026-11-06-spin8-cuda135-input-v2.md), original SHA-256 `47214407932409d4f97bd75c2371b3a27ab0f128797c24c1a662cb0cd203c79e`.
- Existing public v0.5.1 and installed application are not experimental test destinations. Do not move `latest`, replace published assets, or change global drivers/PATH.
- Work only in the isolated `feat/spin8-cuda135-20261106` branch. Existing CUDA135/KV and GUI sibling branches are evidence and possible reviewed inputs, not implicitly merged work.

## Acceptance protocol (prospective; results live separately)

Each record uses NOT_RUN, PASS, FAIL or BLOCKED. Compilation, hook connectivity, GPU correctness and model qualification are distinct. Exclude invalid/censored measurements using predeclared reasons; zero valid trials yield N/A, never zero error/success. Never lower resource floors or remove spill checks to pass a build. Retain failed runs; amendments get a new dated revision and are not applied retroactively.

CPU reference thresholds: absolute difference <= 1e-11 against independent FP64 attention on bounded deterministic fixtures; inverse-gated coordinate equality <= 1e-11. These are not FP16/quantized/model thresholds. Exact C ABI rejection/status/sentinel checks are equality assertions. GPU and real-model tolerances must be fixed per dtype and workload before collecting them.

## A: baseline and provenance

1. Use a detached baseline checkout, distinct CPU/CUDA output directories, Release mode, and one compile job. Do not modify source during a build.
2. Run existing standalone Spin8 CPU tests before adding API changes. Save CTest XML/log and toolchain facts outside version control.
3. Discover actual CUDA 13.5/MSVC/Ninja locations; never assume the attachment's example path exists. Validate installed compiler and driver with tools.
4. Build standalone CUDA tests for SM120. Check resources before GPU tests; do not stop unrelated inference servers. Record GPU results separately from full-engine results.
5. Build native off/on from the same source and resource settings, retain spill guards, and qualify explicit real-model startup separately. No published component changes before this gate.

## B: first vertical contract slice

- Create `spin8/include/spin8/attention_v2.h`.
- Create `spin8/src/attention_v2.cpp` and behavioral C/C++ tests under `spin8/tests/`.
- Modify only the necessary `spin8/CMakeLists.txt` registrations.
- First tracer: FP64 CPU MHA/GQA/MQA self-attention, explicit non-contiguous Q-to-KV map, unequal QK/V widths, positive byte strides and checked capacities, original score scale/order, explicit mask, all-masked policy and caller-owned output.
- Test missing API first (RED), implement minimal behavior (GREEN), then add validation and semantics in further RED/GREEN slices. No source-regex tests.
- Versioned C ABI uses `abi_version`, `struct_bytes`, zero reserved fields and explicit support/rejection. Preserve all v1 behavior. Unsupported codecs, layer kinds and operation modes fail before any output mutation.
- Preserve numerical core reuse: actual audited Spin8 plans/transform operations, identity tail, one softmax, inverse V before optional elementwise gate. Generic fallback is correctness, not speed.
- Independent oracle covers widths 64, 80, 96, 128, 130, 192 and 256 plus differing V width, mapping, stride/sentinels, mask/softcap ordering, overflow and NaN/Inf. Capability result claims CPU reference only until CUDA exists and is tested.
- Add CUDA reference only after CPU contract and independent review. Separate K/V dtype/stride; explicit stream and asynchronous device-status semantics. Never silently call CPU and report GPU support.

## C–H: ordered integration gates

C. Connect native QSA then Q36 full attention to the contract; establish hook counts, prefill/decode equivalence and state participation. GDN is not ordinary attention.

D. Integrate fixed external GGML/PrismML sources and ABI; standard attention on two architectures plus window/softcap coverage, separately prove fused/unfused hooks. Do not infer runtime support from flags or patch-file existence.

E. Preserve Turbo-v1 bytes. Add versioned FP16/q8_0/NVFP4/layout paths only with per-combination numerical/byte/lifetime tests, memory accounting and measured timings. No hypothetical capability advertisements.

F. Session transactions include KV, recurrent/conv/compressor/indexer state and graph pointers. Qualify reset, cancel, clone, prefix, serve, batch and MTP independently; unsupported operations fail explicitly.

G. Use model-bound learned sidecars and separately trained S+/S- adapters. Training data, compute and model identity must be available and frozen; held-out evaluation is separate from artifact engineering. Identity tests are not learned-quality evidence.

H. Latent MLA and DSV41 get separate semantics/state adapters and model qualification. Do not expand compressed KV into ordinary triplicated heads and call it equivalent support.

## Packaging and documentation gate

Only after required model/configuration gates pass: build source-bound packages; independently review; preserve user data; test final installer overwrite and payload hashes; rewrite README/install guide using official app-versus-Terminal distinction; explicitly stage/commit/push; verify remote SHA; create a new immutable release tag; read back all release assets/digests/signatures. Do not replace v0.5.1 or present an A/B-only checkpoint as A–H completion.

## Result ledger

Observed results and blockers belong in `_docs/2026-11-06_spin8-cuda135_Hermes.md`, not in this acceptance protocol. Raw local outputs are outside the checkout under a dedicated validation directory.
