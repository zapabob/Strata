# Task B: architecture-aware Host memory estimator

Date: 2026-11-02 JST. Worktree: strata-16gb-observations/Strata.
Branch: codex/strata-hybrid-memory-20261102. Base: d91c058db61044dd21df330204aa89f622e9e17e.

## Scope and engineering controls

Task B owns the bounded GGUF metadata reader, additive imported-model metadata,
pure Host estimator, related tiny-fixture tests and estimator documentation.
Startup argv, RunPlan/UI, Task A observation and UX contracts were not changed.
Other agents' parent plans, baseline evidence and cache files were preserved.
Canonical pre-implementation prompt, home/project AGENTS and common/start-gate,
skill-selection, security, WebApp and TypeScript SOPs were inspected. Applied
skills: milspec-codex-standard, incremental-implementation, documentation-and-adrs
and agent-self-review-evolution. Higher-priority tool/identity rules prevail over
incompatible legacy prompt claims. No formal MILSPEC compliance is asserted.

## Requirements and implementation

B1: gguf.mjs selectively retains interval, nextn, SSM dimensions and at most
4,096 integer/boolean recurrent-map entries. Arbitrary/tokenizer arrays retain
counts, never their contents. Header limits and truncation checks remain active.
B2/B3: model-memory.mjs validates qwen35 trunk/recurrent maps, explicit K/V widths,
context and arithmetic. It calculates K and V separately using whole GGML blocks
and exposed 256-token per-sequence capacity padding. Hikari has 16 full-attention
and 48 recurrent trunk layers. q8/q8=4.25 GiB, q4/q4=2.25 GiB, f16/f16=8 GiB,
q8/f16=6.125 GiB at 131,072 tokens and one sequence, attention KV only.
B4: disk, attention, backend weights, recurrent state and workspace remain
separate. Required unmeasured allocations stay null with reasons. totalBytes and
fits stay null. TurboQuant and unknown/unqualified architectures stay unknown.
B5: local-models.mjs attaches modelMemory additively to variant and local records.
Metadata hashes now include retained geometry; they remain separate from full
content identity. Old records read without migration writes. New qwen35 legacy
kvKbPerToken is 32 KiB/token at one-byte elements before scales, not all 64 layers.
Other legacy imports and built-in catalog behavior are unchanged.
B6/B7: tests use tiny GGUF files and isolated HOME with the existing fs guard;
apps/host/docs/model-memory-estimator.md documents arithmetic, units and limits.

Changed files: apps/host/server/gguf.mjs, local-models.mjs, new model-memory.mjs;
apps/host/tests/helpers/local-gguf.mjs, new tests/model-memory.test.mjs;
apps/host/docs/model-memory-estimator.md and this implementation log.

## TDD and verification evidence

The first guarded run of tests/model-memory.test.mjs failed with
ERR_MODULE_NOT_FOUND for the intentionally absent new estimator (RED).
After implementation it passed 6/6 (GREEN).
Added explicit-null fallback and sparse-map/inherited codec-name tests produced
1 and then 2 failing tests respectively. Fixes use absence-only defaults,
materialized map validation and own-property codec lookup. Each subsequent run
passed 6/6. Mixed/asymmetric widths, bf16, real arithmetic overflow, invalid
context/sequences, scalar and array maps, MTP, malformed/truncated arrays,
metadata hash changes and old-record no-write reads are covered.

Final guarded focused command from apps/host:
node --input-type=module -e $taskBRunner tests/model-memory.test.mjs tests/local-models.test.mjs tests/kv-settings.test.mjs tests/custom-gguf.test.mjs
The exact scratch-profile runner is recorded in the adjacent task-b-report.md.
Result: exit 0, 20 tests passed, 0 failed, duration 6983.2981 ms on Node v26.10.0.
All four files ran in a scratch HOME using scripts/test-fs-guard.mjs and
scripts/test-environment.mjs. Existing simulated HTTP/local-model tests passed.

Additional commands: git diff --check; node --check apps/host/server/gguf.mjs;
node --check apps/host/server/local-models.mjs;
node --check apps/host/server/model-memory.mjs. All exited 0.
git -C H:\\Strata\\deps\\prism-73bfe6cc rev-parse HEAD returned
73bfe6cc485554822f80c473a3c0c4f25e80f41b.

## Limits and handoff

Pinned reference source inspection is static analysis, not runtime allocation
validation. The installed binary is a different c9c34bc9c build. No real GGUF
was opened/hashed by these tests; no GPU inference, installed profile changes,
launch/stop, downloads, push, merge or release occurred. No dependency was added.
No full suite was run: the parent coordinates known baseline environment
failures. No TS/UI build was needed for the MJS-only Host addition; functional
integration into C/D/UI remains parent-owned. backendProfile records id only;
unified/backend-specific layouts and TurboQuant are not qualified.

Self-review-event: ticket_completed. Review-only response: the focused tests and
diff evidence support Task B's pure calculation/metadata scope. No governance
rewrite is justified. Rollback is the single local Task B commit. The next
step is parent review and C's explicit runtime-total/per-sequence context mapping.
