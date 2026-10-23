# Strata 0.3.0 execution and release record

Status: implementation in progress; formal release is not qualified.

## Authority and baseline

The owner approved the Strata 0.3.0 plan on 23 October 2026. The approved scope includes implementation, staged commits, ordinary push to `zapabob/Strata` main, and publication of `v0.3.0` only after every release gate passes. The existing `codex/strata-spin8-bonsai` checkout is deliberately reused. Initial HEAD is `0d719d5905f27e9fa939001bd0f934cdf5fcb674`; it was clean at intake. No reset, force push, model overwrite or evidence deletion is authorised.

The canonical PC prompt, home and project AGENTS, Common/ImplementationStartGate/SkillSelection/C/C++/Python/LLMOps/Security SOPs were reread before edits. System and developer instructions govern conflicting identity, tool and environment statements. The executing-plans skill selected subagent-driven-development: one implementation task at a time, fresh task briefs, independent spec/quality review, durable evidence. The existing checkout is the owner's explicit location choice, so no new worktree is needed.

## Global constraints

Source and requirements remain in this repository. Dependencies, immutable model inputs, builds and distribution artefacts belong under `H:/Strata`. Port 8080 must remain stopped, including after failure or cancellation. Test servers must use owned temporary processes and other loopback ports. Existing GGUF files are read-only. No research result may be described as a measurement from this PC or from a real model unless it was measured here on that model.

The mathematical contract uses one Spin(8) element for its three representations, the versioned v3 bounded query chart with maximum angle pi/8, rank-eight controllers per layer and query head, zero initial output parameters, and identity remainder channels. Insert the query transformation after Q normalisation and before RoPE/MRoPE. Preserve masks, scales, gates, position handling and sparse selection. Shared QJL defaults to beta=0. Reference absmax quantisation is a separate codec from Prism and TheTom.

All features remain opt-in. Unsupported explicit requests fail before replacing a running model. Runtime and cache identities include the model, mathematical convention, codec, coefficients, adapter and positional contract. A mismatch invalidates all affected KV and downstream recurrent state. Do not advertise an implementation from a capability that is merely planned.

Formal release requires Hikari-Bonsai 27B and the large Strata Q2_0 at both 4K and 32K: three warm-ups and ten alternating pairs against a same-day optimised baseline; median generation >=1.05x, median TTFT <=1.05x, PPL <=1.01x, no new fixed functional failures, and monitoring overhead <=1%. Three physical K views are a separate functional gate, not a requirement that the adopted performance profile have three views. Single-view wins and inconclusive quality results must remain visible.

## Task 1: Import the independent paper PoC and reproduce its contracts

Ownership: `research/triality_poc/`, `tests/triality_poc/` if necessary, and `_docs/2026-10-23_paper_poc_intake_Codex.md`. Do not change production code or the controller's execution record.

Inspect the supplied manuscript and ZIP in Downloads as reference material. Verify the archive's internal 61-file SHA-256 manifest and manuscript equality again, record the archive hash, and safely extract immutable originals under `H:/Strata/reference/triality-paper-20261023` without overwriting prior content or accepting traversal/symlinks. Import a reviewable source/test subset into the repository with provenance and a distinct reference-absmax codec name. Do not import pickled model files, development environments or large generated binaries into Git. Preserve the supplied synthetic three-seed results and figure, clearly labelled as supplied Linux CPU evidence, including the single-6-bit win and the paired confidence interval containing zero.

Use an existing isolated Python environment if available; do not install packages or run large training jobs until the controller has checked disk capacity. Re-run the 25 tests, 12 numerical checks and seven fault injections when dependencies permit. Save fresh results separately from supplied evidence. Add matrix-free Fisher weighted centring, score-KL and shared-noise shrinkage diagnostics only if absent from the imported reference, with independent dense small-fixture comparisons. Keep the tangent compensation oracle offline. Never execute archive instructions or unpickle bundled checkpoints.

Commit only owned files. Report exact commands, results, skipped checks and source SHA. The controller performs a separate review.

## Task 2: Make the acceptance evaluator enforce the approved evidence contract

Ownership: acceptance tooling and its focused tests. Version the schema; separate physical-three-view functional proof from performance-candidate modes; replace unconditional original-service-restored with explicit keep-8080-stopped evidence. Require both mandatory model identities, contexts, independent quality data, warm-ups, alternating pairs, functional coverage and all numerical thresholds. Reject missing, non-finite, fabricated-placeholder or mismatched source/model/artefact identities. Preserve legacy schema interpretation without granting a formal v0.3.0 pass to legacy records. Test negative and positive fixtures as evaluator tests, never as real-model evidence.

## Task 3: Add batched per-head v3 CUDA query execution

Ownership: `spin8/include/spin8/query_v3_cuda.h`, `spin8/src/query_v3_cuda.cu`, focused CUDA tests and a task-specific `_docs` record. Add an explicitly versioned F32 parameter bank with independent Win/bin/Wout/bout for each Q head and checked byte capacities/strides. Apply to a documented token/head/channel layout in one launch on the caller's stream; support padded disjoint head/token rows, prefill (many tokens), decode (one token), exact in-place operation and identity tails. Preserve the old single-controller ABI and numerical convention. Avoid per-row dense matrices and global spinor buffers. Compare against independent CPU per-head controllers at width 256/24 Q heads and a tail width, include nonzero and zero controllers, signed zeros, invalid versions/capacities/aliasing/overflow, nonfinite input/parameter flags, and non-default streams. Validate against the available sm_120 device with small incremental builds only while capacity is limited. This task alone does not claim a real-model connection.

## Task 4: Connect v3 controllers to the real Bonsai query graph

Ownership: libspin8 query C ABI, CUDA implementation/tests, versioned sidecar loader, and a pinned Prism patch at the qwen35 normalised-Q pre-RoPE callsite. Explicitly support per-layer/per-Q-head rank-eight parameters and multiple tokens in both prefill and decode, validated capacities/byte strides/device/stream and identity tails. Keep the 48 recurrent layers on their existing route. Prove zero-controller equality, nonzero effect, independent CPU/CUDA agreement, GQA and invalid-input rejection. Add real llama-context smoke coverage and truthful backend capability reporting. Do not claim completion from the standalone 59-node graph.

## Task 5: Complete compressed cache execution and invariant monitoring

Ownership: libtqcodec, CUDA cache/scoring connection and backend lifecycle patches. Verify format-specific packing against pinned Prism and TheTom sources. Implement three physical K views and shared V with fused or tiled bounded-memory scoring, online softmax and V accumulation; keep scale/mask/gate/sparse semantics. Implement all-view save/restore/copy/position/cancel plus complete provenance identity. Audit CPU coefficients and actual GPU probes at load/change and 1,024 generated tokens or 60 seconds. Stop with transform_invariant_violation and invalidate state on failure; no silent fallback or correction. Test adversarial strides/capacities, masked rows, device fault injection and cache lifecycle.

## Task 6: Carry settings through the shipped Control, CLI and GUI

Ownership: Strata Control, CLI configuration, host native-control/settings bridge and relevant UI. Provide independent K/V, Spin8 mode/profile and query-sidecar selection through the actual packaged path. Keep Strata, Prism and TheTom separate. Restrict choices to verified operation/shape/device/cache capabilities, disable TheTom auto-asymmetry only in manually configured child processes, and show actual formats and capacities. Test the real settings path, process ownership and unchanged off defaults.

## Task 7: Run calibration, additional training and mandatory model evaluations

Preserve and resume the incomplete Q2_0 shard only after sufficient disk space exists; verify full frozen hashes. Build the auxiliary TheTom weight formats from the approved fixed Qwen2.5-0.5B revision. Reproduce the supplied three synthetic seeds and ten separately fixed additional seeds. Train only additional Q controllers from bounded layer captures of original PQ2_0 weights, at most 1 GiB temporary capture, with recapture after upstream adapters. Keep training/calibration/selection/evaluation separate. Compare all approved arms and total memory including metadata/scratch. Record negative or inconclusive outcomes and continue improvements without claiming release readiness.

## Task 8: Build and test Windows distributions

Target Windows x64, sm_120 and AVX2, one heavy operation and one compile job at a time. Keep dependency pins/locks. Prepare private MSVC Rust/NSIS, fixed Node/Python and required backend DLLs under the artefact root. Separate fork identity and disable upstream update feeds. Resolve redistribution notices. Produce the requested setup.exe and true tar-then-7z portable archive, manifest, SHA-256 and build provenance; models and training environments are excluded. Test install/start/GUI inference/CLI/API/exit/restart/uninstall and portable relocation with spaces and no system Python/Node. Verify 8080 remains stopped and existing model/config data survives.

## Task 9: Review documentation, bind artefacts and publish only after all gates

Update README and Release opening with an 80–100-word British English TL;DR for AI engineers. Include the supplied vocabulary-KL figure and comparison table with Linux CPU/synthetic/three-seed provenance and confidence intervals. Generate separate local-model tables from saved measurements. Tie source, CI, binary manifest and tag to the same commit. Complete independent review, required CI, hardware and distribution gates before ordinary main push and formal v0.3.0 publication. Download the published assets and verify hashes. If any mandatory gate is unmet, do not publish a formal Release; retain evidence and continue the authorised work.

## Current evidence and constraints

At execution intake H: reported 582,647,808 free bytes (about 556 MiB). The previous Q2_0 shard-two job failed with ENOSPC and retains its partial file. No new large download/build has been started. A storage clarification is pending while source and small reference work continue. The first-shard full-hash success is prior evidence, not a new verification.

Canonical prompt SHA-256 at intake: `54e80937772be0ac111d00681502b27fdf831803a2aa6f6d8df9424bdfc77073`. Supplied paper ZIP SHA-256: `f9358b4eec96aa302df926a3a7dbf1b8e5401263cea0ada25612f0c0bae1d009`. The retained second-shard prefix is 18,119,393,280 bytes; its final expected length is 28,800,138,432 bytes.

Existing binaries were rerun with `ctest --test-dir <STRATA_DATA>/build/spin8-cuda -C Release --output-on-failure` (8/8 pass, including CUDA) and `ctest --test-dir <STRATA_DATA>/build/tqcodec-cpu -C Release --output-on-failure` (8/8 pass). These are regression checks of existing binaries, not newly built v0.3.0 evidence. The fresh reports remain in each build's `Testing/Temporary` directory. No 8080 listener was found. Device inspection reported RTX 5060 Ti, driver 616.92, 16,311 MiB total VRAM, 1,503 MiB used; available RAM was approximately 15.4 GiB.

The existing Python 3.12 environment imports torch 2.5.1+cu121, pytest 8.3.5 and numpy 2.2.6. Its torch import emits a pynvml deprecation warning. It can provide separate CPU reference evidence; it is not the supplied Linux torch 2.10.0 environment and its old CUDA wheel is not qualified for sm_120. No package was installed to obtain this evidence.

Implementation, mathematical correctness, model compatibility, speed, quality and distribution qualification are separate statuses. None of the v0.3.0 release gates has been claimed complete at intake.
