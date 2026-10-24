# Strata 0.3.0 completion execution record

Plan identity: PLAN-2026-10-24-STRATA-COMPLETION. Baseline: f8074a670fc0d8b4971a30685f6093b266582e5f. Branch: codex/strata-030-completion. Status: implementation in progress; no release qualification.

## Authority and requirements

The owner's approved message, Strata 0.3.0: latest-plan implementation, verification and distribution, is the specification. The saved [24 October handoff](2026-10-24_strata_030_handoff_implementation_plan_Codex.md) supplies historical state; the [23 October foundation](2026-10-23_strata_prism2_bonsai_spin8_handoff_plan.md) supplies mathematical, compatibility and release requirements. Historical G1 PASS is reopened for determinant reference validation: the saved Python LU omits negative-pivot signs. Reflection and quarter-turn failures are implementation defects, not established floating-point instability. Earlier receipts remain evidence of their original inputs only.

The user explicitly selected this existing checkout and a new branch. Using-git-worktrees guidance is satisfied by honouring that location preference; no second checkout, reset, clean or stash is needed. Existing changes to the two 23 October documents and the untracked 24 October handoff belong to prior work and remain untouched and unstaged.

Before edits the canonical prompt was read: C:/Users/downl/_docs/prompts/CLAUDE-FABLE-5.md, SHA256 54e80937772be0ac111d00681502b27fdf831803a2aa6f6d8df9424bdfc77073. Conflicting identity, tool, environment and product statements in that document defer to system/developer instructions. Home, Codex and project AGENTS, CONTRIBUTING, README and relevant prior records were inspected. Selected SOPs: Common MILSPECLLMOps, Implementation Start Gate, Skill Selection, Security, LLMOps, Application Development, Python, C and CPP. Frontend, TypeScript, Rust, Internet Connectivity and DeepResearch are applied when those surfaces are reached. Skills: executing-plans, subagent-driven-development 7.0.1, using-git-worktrees, git-workflow-and-versioning, evidence-changelog-closeout, milspec-codex-standard. The Det QA defect triggers agent-self-review-evolution in review-only mode; no global governance edits are warranted.

## Global constraints

Existing GGUF weights, prior receipts, model packs and downloads are retained. No existing file is deleted or moved to recover space. Model/dependency/build/distribution data lives under H:/Strata; source and durable records live in this checkout. Large downloads, builds and model runs are sequential, builds use one job. Each operation needs its additional peak storage plus 10 GiB free reserve. Port 8080 remains stopped; model tests bind a dedicated loopback port and terminate only processes owned by the test.

Do not replace Strata's GGML with a fork. Preserve exact dependency commits and model hashes already recorded in the handoff and execution journal. Public C ABI remains GGML-independent and states version, shape, byte stride, capacity, precision, device and stream. Unknown or ambiguous dialects and unsupported device/shape/cache operations fail explicitly. Off is the existing path, byte-identical where applicable. No silent profile changes or invariant repair.

Spin(8) uses the vector and two chiral representations of the same group element. U_r = B_r F, with inverse factors in reverse order and codec Hadamard accounted exactly once. Three physical K caches share V. Weighted scores precede one softmax and one V product. QJL beta is zero by default. Query controllers have rank 8, maximum angle pi/8, zero output initialisation and sit after Q normalisation and before RoPE/MRoPE. Hikari has 16 ordinary Attention layers and 48 recurrent layers; unsupported operators retain their original paths.

Coefficient tolerances FP64/FP32/FP16/BF16 are 1e-12 / 1e-5 / 2e-3 / 2e-2. Log-determinant tolerance is block width times coefficient tolerance. Nonfinite values and wrong determinant sign fail. Audit at load/profile change and every 1024 generated tokens or 60 seconds. Violations report transform_invariant_violation and invalidate cache and dependent recurrent state. Matrix, actual kernel and quantisation errors remain separate metrics.

Mandatory models are zapabobouj/Hikari-Bonsai-27B-Nimble-LoRA-GGUF and the pinned large Strata Q2_0; TheTom's small model is auxiliary. G2 requires real 4K-context HTTP completion with server-reported prompt_tokens > 512 and nonempty output. G4 source-bound native inference precedes G3. Formal G3 input lengths are 4096 and 32768 tokens, with generation space added, 3 warm-ups and 10 alternating pairs, same-day optimised baselines. Both models and conditions must meet generation median improvement >=5%, TTFT worsening <=5%, PPL increase <=1%, zero new fixed functional failures and monitoring overhead <=1%.

Training changes only the additional sidecar; capture aggregate <=1 GiB. Training, calibration, selection and final evaluation are separate. Original 3-seed PoC and additional 10 seeds are separate evidence. Retain the supplied Linux CPU synthetic single-6bit advantage and confidence interval including zero. No inference that three views mean fourfold speed.

Distribution names: Strata-0.3.0-windows-x64-sm120-setup.exe and Strata-0.3.0-windows-x64-sm120-portable.tar.7z. The latter is tar compressed with 7z. Separate runtime directories, fixed Node/Python, required redistributable DLLs and licences, no weights or training environment. Fork identity and manual installation, no upstream update feed. README and Release start with 80-100 words of British English. Publish to zapabob/Strata only; no formal v0.3.0 tag or Release while any acceptance criterion is missing or failed.

## Task 1: Repair and reproduce the independent determinant reference

Own tools/spin8_reference_compare.py (new), tools/test_spin8_reference_compare.py (new), tools/spin8_reference_probe/ (new if needed), a focused _docs log, and the explicitly named external H:/Strata/build/task5a-gateA-spin8-20261023/scripts/compare.py. No production Spin8 or codec changes are required unless a reproduced defect warrants a separate task.

Read the original external compare.py and probe before edits. Preserve the original script byte-for-byte with a hash in a fresh evidence directory. Preserve all existing results. Promote the independently authored reference/probe into reproducible repository tooling with explicit input/output paths, an import-safe entry point, no hard-coded personal paths, and source/input hashes. Correct lu_sign_logdet by including every negative pivot as well as row-swap parity. Do not copy the C++ audit implementation into the independent reference.

Add meaningful RED/GREEN regressions: identity, one reflection, an odd permutation, a proper quarter-turn, two reflections, singularity, negative determinant with log magnitude, and every one of the 256 signed 8x8 Hadamard masks. Compare Hadamard sign to an independent exact integer determinant and construction parity. Reinstate corrected FP64 LU sign checks for every supplied rotation sample; retain rational spot checks separately and identify denominator limiting as approximate rationalisation. Never suppress sign mismatches to make a gate pass.

Run the repaired reference against fresh probe output if the existing small CPU build can be safely reused; otherwise preserve old-input replay as explicitly labelled replay and leave fresh build pending. Exercise Clifford, chirality, group/inverse, Triality, 2pi/4pi, F32/F64 loopback, query identity and gradients. Bind all receipts to actual source/script/input hashes. Explain any old G1 claim that the corrected run supersedes. Keep CPU-only and CUDA claims separate. Evidence root for this task: H:/Strata/build/task5a-g1-reaudit-20261024, maximum additional 256 MiB; refuse to run if fewer than 10 GiB plus this allowance is free. Do not modify other external evidence.

Use the repository's existing Python 3.12 tooling through uv with no dependency update. Record fallback only if required. Run focused tests while iterating, appropriate complete reference suite and format/lint once at completion. Self-review and commit only owned source/test/log files on the completion branch. Do not publish. Return report with commands, RED/GREEN, hashes, remaining CUDA scope and commit.

## Task 2: Make bounded validation reliable on Windows PowerShell

Own tools/verify_codec_dialects_build.ps1 and focused process/capacity tests. Preserve labelled receipts. Replace unsupported Process.Kill(true) behaviour on Windows PowerShell 5.1 with reliable ownership-scoped child-tree termination, avoiding PID-only races. Capture reliable child exit codes, including nonzero and fast-exit processes. Capacity checks use actual free bytes and reserve, stop before launch if insufficient, and retain partial outputs on guard failure. Support explicit bounded output budgets rather than silently lifting limits. Test zero/nonzero exit, child descendants, capacity breach and invalid labels/paths in isolated test-owned directories without touching real services. No unrelated process termination.

## Task 3: Rebind library verification and finish native baseline build

Inventory H:/Strata related model/pack/build/download metadata without deletion. Preserve attribution uncertainty; verify the usable existing Q2 pack instead of re-downloading/repacking. Record bounded peak estimates before each build. Rerun exact dialect byte and FP32 comparisons, capacity/alias/fault tests on the current source. Build CPU and CUDA sm_120 sequentially, test actual kernels and invariant injections. Resume retained native build objects where source identity permits; retain missing/failed old exits. Produce source-bound executable, DLL and compiler manifests, then real native large-Q2 inference. Do not start automatic model downloads.

## Task 4: Complete real compressed CUDA cache execution

Extend the existing portable codec/cache interfaces additively. Implement actual three physical K allocations and shared V, composed transforms, decode, weighted scores, online softmax and V product with GQA/masks/scale/positions/sparse rules. Cover save/restore/clone/move/cancel on all views and provenance mismatch invalidation, including dependent recurrent state. Validate against independent FP64 and exact dialect oracles. Dynamic Q matrix audit freezes its controlling spinor rather than reevaluating the nonlinear controller for each basis input. Runtime monitoring checks actual GPU data without per-token synchronisation. Dispatch in smaller sequential substeps with concrete ownership after inspecting integration seams; this task remains incomplete until real runtime graph tests pass.

## Task 5: Connect independent runtimes to shipped CLI, Control and GUI

Route native Strata, Prism and TheTom as distinct runtimes through the actual packaged Control owner path. Add independent K/V, Spin8 modes, profile and sidecar settings with capability preflight before replacing a running configuration. Preserve authentication, process ownership, actual generation readiness, cancellation and shutdown. Sanitise fork-specific inherited settings only in owned children; manual K/V choices survive all automatic heuristics and retries. Test real Hikari and large-Q2 G2 requests on dedicated loopback ports. Keep 8080 stopped and saved existing user presets untouched.

## Task 6: Train, calibrate and perform mandatory model evaluation

Capture PQ2 layer inputs and non-compressed reference outputs in bounded chunks; train only extra rank-8 Q sidecars and recapture downstream inputs. Add Fisher-centred calibration, error correlation and offline tangent diagnostics. Evaluate all requested variants, single-view 6bit and generic rotations with equal total memory accounting. Reproduce tiny 3 seeds and fixed additional 10 separately. Execute mandatory 4K/32K pairs, functional failures, PPL and monitoring cost, confidence intervals for independent quality claims. Adopt only profiles meeting each formal threshold.

## Task 7: Build and validate Windows distributions

Build one job with pinned dependencies; package GUI and CLI/API with three isolated runtimes, DLLs, fixed Node/Python, licences and manifests. Complete fork app identity/update isolation and uninstall preservation. Verify actual installation, GUI inference, CLI/API, stop/restart/uninstall, portable paths with spaces and no system Node/Python PATH, archive inspection and extracted hashes. No 8080 listener remains after tests.

## Task 8: Review and publish the qualified source and artefacts

Write British English TL;DR and separately labelled reproducible PoC/current-PC figures. Independently review the whole branch, inspect same-SHA CI and all model/distribution gates. Only after acceptance, normal push to fork main, v0.3.0 tag and formal Release; attach checksums, build manifest and test report, then download and verify uploaded assets. No gate is waived to meet a publication request.

## Initial observations and residual risk

At 2026-10-24T03:43:00Z, .NET DriveInfo and Win32_LogicalDisk both report H: free 28,908,257,280 bytes. No port 8080 listener was returned. This supports only a bounded small first task, not the complete distribution pipeline. The historical roughly 183 GiB change remains unattributed. The only initial dirty paths are the two 23 October documents and the 24 October handoff. Source baseline and branch were verified before change.

No current CUDA reaudit, 4K/32K release comparison, distribution acceptance or release publication is claimed. Per-task implementation and verification records follow in separate dated _docs files and this plan's SDD ledger.
