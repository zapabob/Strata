# Uniform orthogonal cache transport CPU reference

## Requirements and scope

Add an explicit, external FP64 transport plan for the existing three-K,
shared-V cache, including its optional shared QJL residual. One fixed proper
orthogonal matrix S applies uniformly to every selected logical key. The
storage cache and both cache ledger ABIs must remain unchanged. This is an
opt-in CPU reference; it does not implement CUDA, model position metadata,
per-row different transforms, or full-network rerun equivalence.

Applied sources: the canonical PC prompt at
`<PC_CANONICAL_PROMPT>`, project `AGENTS.md`, the
`milspec-codex-standard` skill, the common engineering SOP and CPP SOP.
This records engineering controls; it makes no formal MILSPEC certification.

## Mathematical decision

For each existing physical reconstruction `khat_r = U_r^T decode(K_r)`,
the logical reconstruction becomes `S khat_r`. Therefore
`q^T S khat_r = (S^T q)^T khat_r`. Compute the canonical query `S^T q`
once, then call the existing attention implementation, preserving its one
softmax and single shared V.

The logical residual becomes `S e`. Its norm is preserved, and its existing
sketch is used as the transported estimator:
`beta sqrt(pi/2) ||e|| sign(G e)^T G S^T q / m`.
Neither G nor the old sign bits are recomputed. This is not a claim that
`sign(G S e)` can be recovered from old signs: in two dimensions, G=(1,0),
e=(1,+/-1)/sqrt(2) have the same stored sign and norm, while a proper
quarter-turn gives opposite new projected signs. No stochastic error guarantee
for a reused deterministic sketch is added.

New logical keys require `S^T key` before the existing append API. Values are
unchanged. Callers own the semantic choice that all allowed rows use the same S.

## Implementation and ownership

`tqcodec/include/tqcodec/transport.h` defines the opaque owning plan, creation,
destruction, audit and external storage ledger APIs, one-vector canonicalization
and transported attention. The plan snapshots row-major S. Its matrix byte cap
covers allocated matrix capacity; the ledger separately includes `sizeof(plan)`.
Allocator metadata, alignment and temporary audit/attention scratch are excluded.

`tqcodec/src/cache.cpp` reuses its private orthogonal validator, with optional
reporting and a determinant +1 requirement only for transport creation. Legacy
cache transforms still admit reflections. Gram Frobenius/max errors, signed
determinant and log absolute determinant are computed once. Transport does not
change the `tq_cache` layout, clone behavior, ledger types or existing attention
arithmetic. All new typed boundaries check alignment, capacities, shapes,
finiteness, range overflow and prohibited aliases. Exact in-place vectors are
staged; partial overlap is rejected. Outputs are committed only on success.
New C entry points translate allocation exceptions and contain other exceptions.

`tqcodec/tests/transport_test.cpp` uses explicit noncommuting proper plane
rotations and a normalized H8 block embedded in dimension nine. An independent
oracle decodes each physical K, forms `S U_r^T decode(K_r)`, computes the residual
projection in logical coordinates and checks score equality before scale or
softmax. It then decodes shared V and checks the final single-softmax result.
It covers active/disabled QJL, masks, identity, copied plan matrix, canonical
append, physical byte/norm preservation, external ledger accounting, determinant
and shape validation, nonfinites, overflow, capacities, aliases, alignment and
failure atomicity.

## Validation and resource constraint

Read-only source inspection and self-review were performed. No compilation or
test execution has been performed by this agent yet: an active model download
requires serialized heavy work, and the parent agent owns the compile window
and CMake target registration. Test success must not be inferred from source
presence. Required next verification: build the CPU target with strict warnings,
run the transport test and existing reference suite, and record exact commands
and results in this log or the parent implementation record.

No CUDA/HIP/SYCL backend files were changed. No model quality, generation,
latency, hardware throughput, or actual position-manager behavior was tested.

Parent verification: CMake target registered, Release build with strict library
MSVC /W4 /WX passed. CTest passed all 7 reference tests, including transport.
Logs: H:/Strata/build/tqcodec-transport-build.log and
tqcodec-transport-ctest.log. The task-owned preparation process was interrupted
with its existing model prefix preserved for this compile window, then resumed.
Independent review found one audit reporting mismatch: raw Frobenius norm
instead of normalized E_F. Fixed sqrt(sum/d), documented the API, and added
the accepted near-orthogonal diagonal regression S=(1+2e-13)I at width9.
The reviewer confirmed the fix and found no other concrete correctness issue.

## Rollback and remaining risk

Remove the new header/test and transport declarations/definitions, restore the
validator's default optional additions, and remove the parent CMake target to
roll back. Preserve unrelated concurrent work. No commits, pushes, release
actions, model downloads or process stops are part of this change.

The plan validates numerical orthogonality with the existing FP64 tolerances;
it is not an exact symbolic certificate. Raw opaque handles require valid live
objects, as with the existing cache API. Callers must synchronize destruction
and cache mutation with readers. Position semantics and multi-transform row
selection remain external caller responsibilities.
