# Shared residual QJL cache reference (2026-10-23)

## Scope and acceptance

This opt-in CPU FP64 reference keeps the existing three independently packed K
arrays and one shared packed V array. One cache represents one KV head. Fixed
transforms, simplex alpha weights, scalar codebooks, beta and projection matrix
are copied at creation and remain unchanged for the cache lifetime. No model
loader, server, GPU backend, deployment, persistence format or legacy GGUF block
is changed. No throughput, memory saving over a particular engine, model quality
gain or formal MILSPEC certification is claimed.

The old `tq_cache_config`, `tq_cache_ledger` and `tq_cache_create` signatures and
struct layouts are unchanged. `tq_cache_create_v2` takes version 2, the base
config, beta, projection row count, a caller-owned matrix and accessible element
count, and a matrix allocation byte cap. Nonzero beta requires beta in [0,1], a
finite row-major m-by-width matrix, sufficient element count and byte budget,
and overflow-safe sizes. The matrix is copied. Matrix provenance, identifier
and independent Gaussian-generation evidence remain the caller's responsibility;
the cache does not generate randomness or certify a distribution.

Beta zero, including legacy creation, allocates no Gaussian, sign or residual
norm arrays. It does not reconstruct K or compute residuals. The opaque cache
object contains empty vector descriptors and configuration fields, which are
included in fixed bytes even when disabled. Sketch fields in a beta-zero v2
config are deliberately ignored. Disabled outputs and physical K bytes are
tested bit-for-bit against legacy creation in the current build.

## Implementation

For an insertion, the existing quantizer stages each rotated physical K payload
and norm and the one V payload and norm. With QJL enabled, it decodes each K
view, applies that transform's transpose, and computes
`e = k - sum_r alpha[r] * U[r]^T * decode(K[r])`. One packed sign vector
`sign(G e)` and one FP64 residual norm are staged per key, shared by all three K
views. No raw key is retained. Every allocation, decode, transform, residual
and projection must succeed before any cache row is written or rows is advanced.

For a query, all transformed query scores are combined as before. Gq is computed
once if an allowed row has a nonzero residual. The row correction is
`beta * sqrt(pi/2) * norm(e) * sum_j sign(G e)[j]*(G q)[j] / m`.
It is added before the existing attention scale and the single online softmax.
The original shared V array supplies that softmax's value reduction. A masked
row is skipped. If all allowed residuals are zero, Gq is not computed. Failed
queries leave the output unchanged.

`tq_cache_copy_residual_row` provides read-only copied diagnostics. Signs are
LSB-first, zero projections map to +1, unused bits are zero. A zero residual has
norm zero and all m active sign bits set to one. Clear zeros all allocated K,
V, sign and norm arrays and resets rows, while preserving copied configuration.
Clone copies all physical arrays and immutable configuration into independent
storage. No mutable borrowed matrix survives creation.

The versioned ledger reports base categories, Gaussian allocation capacity,
packed residual-sign capacity, FP64 residual-norm capacity, and the complete
total. Reserved row slots and packing tails count. The old ledger API rejects
an active-QJL cache with `TQ_INVALID`, preserving its output, so it cannot
silently underreport sketch allocations. Allocator metadata, extra alignment
overhead, temporary query/append scratch and external controllers remain excluded.
The projection byte cap covers the Gaussian vector allocation, including its
actual capacity; it is not an overall cache or scratch budget.

The score-error helper's theoretical independence assumptions are unchanged:
fixed query and residual independent of an ideal iid N(0,1) matrix. Reusing a
fixed sketch during generation, fitting parameters against the same matrix,
softmax error and model quality do not inherit a runtime guarantee.

## Files and verification

The owned changes are `tqcodec/include/tqcodec/cache.h`, `tqcodec/src/cache.cpp`,
`tqcodec/tests/cache_test.cpp` and this record. Other agents own codec, distill,
integration tests and repository CMake changes. They were preserved.

The focused tests independently reconstruct common-coordinate physical K views,
form the residual and signed projection correction, and check a two-row
softmax with attention scale 0.37. They test the enabled correction changes that
fixture, beta-zero bit identity and zero sketch accounting, one shared sign
vector, non-byte-aligned tails, zero and representable residuals, masks, copied
configuration, both clone/clear directions, disabled clone allocations, retained
clear capacities, unchanged physical rows after failure, invalid beta/version,
short matrix count, tight matrix byte cap, size overflow, null/nonfinite matrix,
overlapping outputs, late residual projection overflow, query overflow and
unchanged query outputs. The finite matrix fixture is explicit and deterministic;
it is not presented as a sampled independent Gaussian distribution.

An isolated scratch harness was created only under
`H:/Strata/build/shared-qjl-cache-20261023`. Its CMake source compiles the actual
codec.cpp, cache.cpp and cache_test.cpp directly with C++17 and
`/W4 /WX /fp:strict`. Repository CMake files were not edited by this worker.
Every compiler invocation used this H: directory as the explicit working directory.

Commands from that directory were `cmake -S . -B build -G "Visual Studio 17 2022"
-A x64`, `cmake --build build --config Release --parallel 1`, and
`.\build\Release\cache_test.exe`. Configure and build succeeded with MSVC
19.44.35224.0. The final executable returned success and printed
`tqcodec cache reference failures: 0`. Captured stdout is at
`H:/Strata/build/shared-qjl-cache-20261023/cache-test-release.txt`.
The first attempted direct vcvars/cl command failed in shell quoting before the
compiler ran; the isolated CMake harness replaced that invocation. clang-format
and clang-tidy were not found on PATH, so those tools were not run.

## Standards, self-review and remaining scope

The canonical pre-implementation prompt was read. Applied controls were the PC
and project AGENTS, MILSPEC Codex Standard skill, Common Engineering,
Implementation Start Gate, Skill Selection, Security, LLMOps and CPP SOPs. The
input boundary has no network or secrets: the relevant assets are caller memory,
immutable configuration, append atomicity and complete byte accounting. Explicit
shape, finite-value, capacity, overflow and output-overlap checks address that
boundary. No dependency was added.

Self-review-event: ticket_completed; review-only. Fresh compilation and focused
tests support the CPU claims. No governance update was warranted. The rejected
alternative was changing the legacy config/ledger struct layouts; versioned APIs
retain those interfaces and make sketch accounting explicit instead.

The parent task still owns independent review and the full repository CMake and
integration test runs. No GPU backend, actual model, inference server, performance
benchmark, stochastic quality evaluation, allocator-failure injection or release
was tested here. No commit or push was made. Rollback is limited to these owned
cache/API/test additions; unrelated uncommitted project work must be preserved.
