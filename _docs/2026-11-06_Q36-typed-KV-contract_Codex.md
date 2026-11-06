# Q36 typed KV contract implementation

Requirement: Task K1, checked typed Q36 layout and actual-binary capability negotiation, preserving independent F32/F16 selection, legacy defaults, digests, private isolation and resource gates.

Base `fdbefe3e7a19443e3b62e3818c2374c5a8ff53bb`; implementation commit `494032aee4c20799cda30bb2c98a479536aa9588` in `H:/Strata/worktrees/cuda135-kv-20261106`. Status: DONE_WITH_CONCERNS, native compile and GPU qualification NOT_RUN.

The detailed requirements, changed files, commands, fresh results, failed attempts, limits and rollback are in [.superpowers K1 report](../.superpowers/sdd/2026-11-06-strata-cuda135-rtx5060ti-implementation-plan/task-K1-report.md). Fresh implementer results are Host 58/58 and Python 15/15; the controller separately recorded TypeScript noEmit exit 0 using existing matching dependencies. The unchanged startup-log suite has one stale historical-summary assertion (9/10 passed).

Design: one native descriptor governs scalar allocation/copy/clear/identity. Quantized layouts are non-executable proposals. A bounded digest-bound existing `--help` query supplies scalar capabilities. Python independently confirms the actual child and checks its observed dtype/allocation before READY for negotiated requests. Selected-model GUI fields hide unrelated codecs. No numerical kernels, model/pack validation, memory floors, release packages or active runtimes were changed.

Applied standards: PC/Codex/project AGENTS and canonical preimplementation prompt; common engineering, implementation start gate, skill selection, security, LLMOps, CPP, Python and TypeScript SOPs. Applied skills: milspec-codex-standard and api-and-interface-design. No formal MILSPEC certification claim. Existing task-specified interpreters were used without dependency installation; the parent owns native build scheduling.

Next gate: independent review and native CPU/CUDA targets after the parent's sequential comparison build; then explicitly authorised real-binary/GPU validation, FP32 output parity and FP16 K2 numerical/lifecycle tests. No speed, quality or long-context fit claim follows from these source/CPU results.
