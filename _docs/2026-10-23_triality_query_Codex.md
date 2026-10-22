# Triality query transform implementation record

## Objective and requirements

Add a standalone C ABI for a strict Spin(8) triality query transform, with no model-specific types or runtime activation. Each complete eight-coordinate group of a query row uses one proper orthogonal matrix. A short tail is copied unchanged. The optional rank-eight controller derives one spinor per row from finite query values and owns a copy of its weights.

Acceptance criteria were: construction from the existing chirality-ordered Clifford generators; identity at the reference spinor; independent contraction and octonion checks; determinant and Gram audit; finite tangent behavior including large values; F32/F64 strided transforms with explicit byte capacity and atomic failure; controller zero and nonzero behavior.

## Standards and decisions

Read the canonical pre-implementation prompt at `<PC_CANONICAL_PROMPT>`, PC and project `AGENTS.md`, the common and implementation-start SOPs, skill-selection SOP, application-development SOP, C and C++ SOPs, and the required `milspec-codex-standard` skill. No other task-specific skill was needed. The higher-priority Codex and project instructions govern conflicts with the canonical prompt.

`C(c)[i,a]` contracts the upper-right 8×8 generator block against the negative-chirality spinor `c`; `A(c)=C(c)C(e0)^T`. `c` must have a finite norm within `1e-13` of one. Matrix publication requires the shared numerical audit to report positive determinant, normalized Frobenius and maximum Gram errors at most `1e-12`, and signed log-determinant magnitude at most `1e-12`. The tangent basis is the seven coordinate directions after `e0`; the map bounds its angle below `pi/8` and uses a scaled norm for extreme finite inputs.

The controller copies row-major `Wdown[8,d]` and `Wup[7,8]`, then computes `Wup*tanh(Wdown*RMSNorm(x))` with `epsilon=1e-6`. There are no biases. A zero `Wup` follows an exact copy path. It makes one spinor per row, shared by all complete eight-coordinate groups. This is a standalone query transform, with no engine or model routing change.

## Traceability

| Requirement | Implementation | Verification |
| --- | --- | --- |
| Triality construction and proper rotation | `spin8/src/query.cpp`: contraction and matrix audit | `spin8/tests/query_test.cpp`: octonion reference, identity, random matrix audit |
| Stable tangent map | `spin8_query_spinor_from_tangent` | zero, finite differences, two maximal doubles, nonfinite rejection |
| Safe query rows and tails | `spin8_query_transform` | F32/F64, strides, tail, in-place, capacity, overlap, overflow, NaN |
| Rank-eight controller | `spin8_query_controller_create/apply/free` | zero and nonzero weights, copied weights, F32, tail, capacity and NaN |

## Changed files

`spin8/include/spin8/query.h`, `spin8/src/query.cpp`, `spin8/tests/query_test.cpp`, and this log. CMake integration was assigned to the root agent and was already present when the CMake verification ran.

## Commands and fresh results

- `clang++ -std=c++17 -Wall -Wextra -Wpedantic -Werror -I spin8/include spin8/src/spin8.cpp spin8/src/query.cpp spin8/tests/query_test.cpp -o %TEMP%\spin8_query_test.exe`: passed.
- `%TEMP%\spin8_query_test.exe`: passed.
- `clang-format -i` on the three owned code files: completed.
- `cmake -S spin8 -B %TEMP%\spin8-query-cmake -G "Visual Studio 17 2022" -A x64 -DSPIN8_ENABLE_CUDA=OFF`: passed.
- `cmake --build %TEMP%\spin8-query-cmake --config Release --target spin8_query_test`: passed under MSVC `/W4 /WX /fp:strict`. MSBuild warned only that its build directory was in `%TEMP%`, which can affect incremental builds.
- `ctest --test-dir %TEMP%\spin8-query-cmake -C Release -R ^spin8_query$ --output-on-failure`: one test passed.
- `clang -x c -std=c11 -Wall -Wextra -Wpedantic -Werror -fsyntax-only -I spin8/include -include spin8/query.h -` with empty C input: passed, confirming that the public header parses as C.
- The root agent separately reported a full MSVC CPU CTest run of `spin8_cpu`, `spin8_query`, and `spin8_c_abi`: 3/3 passed. This is root-reported evidence, not a command run by this worker.

## Limits and containment

This work has not tested CUDA, HIP, SYCL, Metal, model integration, throughput, model quality, or concurrency under caller mutations. The immutable controller can be shared only while the caller keeps it alive and does not free it during an apply call. The C ABI assumes the supplied pointer refers to a genuinely accessible allocation of at least the declared capacity; no C library can prove that property from a pointer and byte count alone. F16 and BF16 storage return `SPIN8_UNSUPPORTED`.

Rollback is removal of these three new code files and the separate CMake additions by their owner; the existing Spin(8) API behavior is unchanged. The remaining integration action is an independent review of the API and its callers before any engine use.
