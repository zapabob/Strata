# Minimal upstream PR candidates

Agent: OpenCode. Checked2026-11-10. User asks which current repairs could be
submitted upstream with minimal changes. This is candidate assessment, not an
opened PR or a claim that pending validation passed.

## Current official source and submission rules

Official main API returned87dfca0e7c3ee24ad36cc3f69a31b859587245f8
(2026-11-10T05:47:31Z). Its DFlash2 blob69a8f56303d63fc2a88325bbe85bcb222f6ab5ec
and IQ-kernels blobc70ca9e106a9bbf7518e4d74963a9a18744d3a1a match the local
f33c8c30 intake exactly. Thus those two candidate contexts remain current.

- https://github.com/Niko1221/Strata/commit/87dfca0e7c3ee24ad36cc3f69a31b859587245f8
- https://github.com/Niko1221/Strata/blob/87dfca0e7c3ee24ad36cc3f69a31b859587245f8/CONTRIBUTING.md

Rules: one problem per PR, no unrelated formatting/versions/packaging, real
source-bound evidence, unchanged default paths, affected backend builds. Missing
backend validation means draft and an explicit targeted test request. Performance
claims need same-day before/after data. A proposed command is not a passing test.

## Ranked candidates

1. **DFlash2 scoped scale lifetime.** Production change is about10 lines in
   src/kernels/cuda/dflash2.cu, restricted to WARPS8/R1/UNR4or8. Existing parity
   test can add missing columns4/6/7 in one line. The optional raw-output dumping
   helper used locally is not needed in the minimal proposed patch. No new
   feature, mode, default choice or allowance. Full83-entry object guard passed;
   all64 column/shape cases passed per schedule17/18/21 and their raw GPU output
   SHA256 matched2931ac0e797f706652727012c54b9e8b9d309e5ffdc390a701888ce9a36cc9b8.
   Actual instruction-byte comparison of all83 kernels found only the two
   intended schedules changed; the other81, including the default, matched.
   Additional HIP/backend
   checks and measured tradeoffs remain prerequisites for non-draft review.
   Suggested title: `[Engine] avoid Q4 drafter register spills in long-unroll variants`.
2. **EXPDEC R4 pair-local lifetime.** One small conditional in iq_kernels.cu,
   retaining four-row dispatch/launch bounds and the existing R2 arithmetic.
   Object guard passed. A real GPU benchmark executed the repaired R4 down path
   with T1–T4 and reported all comparisons identical; the initial orchestration
   falsely matched DIFFERENT in its comment header and remains a failed wrapper
   attempt, while the raw numerical subprocess genuinely passed. No speedup claim.
   Larger-group regression and HIP coverage remain. Coordinate scope with the
   existing EXPDEC/HIP work rather than submitting a competing broad rewrite.
3. **QSA three shared tail keys.** One kernel; restores original64-bit indexing,
   keeps shared allocation within48KiB. Full35-entry object guard passed. Needs
   boundary/tie/active-bound numerical checks and before/after timing. More
   scheduling/memory impact than DFlash2, so lower priority for a minimal first PR.
4. **W4A8 bounded accumulator lifetime.** The third candidate passes all8 object
   entries but recomputes weights for a second token pass. Numerical and same-day
   old/new timing are essential. Existing PR5498 touches the same file. Hold this
   candidate until tradeoffs and maintainer scope are clear.

## Duplicate and overlap checks

GitHub open/closed issue+PR searches: `spill`, `DFlash2`, exact
`gemm4_rows_kernel` (0results), exact `expdec_down_kernel` (9results).
This search found no same-name DFlash2 repair, not proof that no related work exists.

- https://github.com/Niko1221/Strata/pull/3259 — existing EXPDEC/HIP work.
- https://github.com/Niko1221/Strata/pull/3233 — existing HIP QSA work.
- https://github.com/Niko1221/Strata/pull/5498 — W4A8 sm75 work; API file list
  includes moe_iq4_w4a8.cu, moe_mmq.cu and its parity test.
- https://github.com/Niko1221/Strata/pull/2683 — historical resource guard.

Existing zapabob PRs were listed before recommending new work:5374,5359,5273,
5221,5216,4989,4250,4249,4248 and closed3954. Update an existing relevant thread
if later evidence establishes overlap. In particular, do not duplicate4250's
managed-host child-absence topic or4248's inference-silence policy.

The agent-local supervisor shim and workspace-files CRUD module are absent from
the official f33c8c30 tree: the current fixes there are fork-specific. The broad
sidebar/file-CRUD redesign, Hakua/signing/version changes and unmeasured98K MMA
proposal do not belong in the minimal DFlash2 PR.

## Evidence and next action

Resource/numerical receipts are under the exclusively owned repair output,
identified in2026-11-10_release-055-repair_OpenCode.md. Any upstream report must
sanitize machine paths and include only independently checked results. Keep
passed/failed/NOT_RUN separate. Recommended first submission unit: DFlash2 kernel
scope plus one-line column coverage, after GPU results and backend checks.

The two-file proposed patch is repair-055-20261110/upstream-dflash-minimal.patch.
Its reverse/applicability syntax check passed against the current repair tree,
without applying changes. Full diagnostic libraries passed cuda_spill_guard;
the serial GPU acceptance passed all21 checks on the current hardware. Those
results do not cover a future rebased upstream branch until that exact branch is
built and checked. No PR or issue was created by this candidate assessment.
