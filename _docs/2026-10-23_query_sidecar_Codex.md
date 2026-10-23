# Query-v3 portable sidecar implementation record

Date: 2026-10-23 JST. Base: `32a1dc9`. Scope: Task4A from
`.superpowers/sdd/2026-10-23_strata_030_execution_Codex/task-4a-brief.md`.
This record accompanies the implementation commit. It does not report a model
integration, learned adapter, model-quality result or release qualification.

## Required context and control

Read the canonical `C:/Users/downl/_docs/prompts/CLAUDE-FABLE-5.md`, home and
Codex AGENTS, project AGENTS, the scoped brief, spin8 README, query-v3 header and
implementation, current tests and CONTRIBUTING. Apply compatible engineering
instructions; conflicting identity, historical date, product, tool and Linux
environment claims from the imported prompt do not replace the actual runtime.
No narrower spin8/tools instruction file was found.

Applied skills: `milspec-codex-standard` and `code-review-and-quality`. Applied
SOPs: common MILSPECLLMOps engineering, Implementation Start Gate, Skill
Selection, Security, Application Development, Python, CPP and C. The requirements
and evidence below are engineering traceability; no formal MILSPEC certification
is claimed. No external security research or package download was needed.

The controller delegated only this sidecar and its focused tests/docs. Other
agents own subsequent model hooks and the heavy Prism build. No agent was
spawned. Root granted compiler clearance after stopping its own Prism build;
this worker configured/built only a new small CPU tree, one job. Compiler
completion was reported, and root resumed its Prism build. No CUDA/core numerical
source was edited. Models were not read, rewritten or moved. No server,
download, package install, environment change or external publishing occurred.

Before evidence writes H: had 4,035,301,376 bytes free and C: had
18,004,705,280 bytes free. A fresh pre-configure guard required at least
1,500,000 KiB free physical memory and 500 MiB free on H:. Build and raw evidence
are in `H:/Strata/build/query-sidecar-20261023`; no existing evidence was removed
or moved to recover capacity.

## Requirements, implementation and acceptance

| Requirement | Implementation | Evidence |
| --- | --- | --- |
| Fixed portable canonical v3 format | 160-byte LE header; 32-byte records; contiguous F32 arrays; strict 64 MiB bound | Python structural mutations and C++ parser consuming the same fixtures |
| Independent exact identity binding | Ordered 1..256 model hashes; profile/position hashes; fixed convention hash; exact sorted layer geometry | One/two-file golden round trips; changed/zero identities and wrong/missing/reordered expected layer tests |
| Safe bounded immutable C ABI | Versioned sized descriptors, byte capacities, checked spans/alignment, owned F32 storage, null failure result, unchanged failed getters | MSVC C/C++ build; actual C consumer; alias/capacity/alignment/overflow/lifetime tests |
| Numerical representation retained | Per-head Win/bin/Wout/bout; finite bit check; signed zero retained; exact float bits | Distinct parameter pattern checks; independently computed MLP/rational spinor per head; identity and tail tests |
| Complete file integrity and identity | Pinned attributed SHA-256, footer over preceding bytes, full-file content hash | Empty/abc/million-a known vectors against hashlib; Python-derived full-file hash consumed by C++ |
| Independent standard-library writer/reader | Python dataclasses, strict encode/decode, explicit identity initialization and CLI | CLI create/inspect/exclusive refusal/explicit overwrite; 256-shard bound; independent parser adversarial tests |
| Preserve default engine path | Added isolated static-library code and test wiring, no engine hook/default change | Scoped diff and existing CPU/query/v3/C ABI regression suite |

Public API is in `spin8/include/spin8/query_adapter.h`, implementation in
`spin8/src/query_adapter.cpp`. `spin8/docs/query_adapter_format.md` defines every
wire byte, convention, status, lifetime and caller identity obligation. The
Python writer/reader is `tools/spin8_query_sidecar.py`; Python adversarial/CLI/
cross-language tests are `tools/test_spin8_query_sidecar.py`. Focused C/C++ tests
are `spin8/tests/query_adapter_test.cpp` and `query_adapter_c_test.c`.
`spin8/CMakeLists.txt` adds the loader/hash sources, strict-warning test target
and Python cross-language CTest when an interpreter is available.

Geometry tests include Q24/KV4/width256 and Q2/KV1/width11. The latter checks the
partial block. Test model bindings are hashes of explicit synthetic labels,
not claimed real GGUF file hashes. The actual runtime must compute model-file
hashes and derive codec/profile/position/geometry expectations independently.
The mathematical digest hashes an exact documented ASCII contract, not an
executable or proof. The actual existing core basis audit is run separately.

SHA files were copied from local Prism commit
`73bfe6cc485554822f80c473a3c0c4f25e80f41b`. All SHA identifiers were namespaced
`spin8_sidecar_sha256_` to avoid Prism collisions, with no algorithm changes.
The guard was renamed; rotate-bits and licenses were retained.
`spin8/third_party/sha256/PROVENANCE.md` records exact original hashes and
public-domain/MIT attribution. No cryptographic certification is implied.

## Commands and observed results

The explicit scoped instruction required the existing Python312 interpreter,
with no environment installation. This overrides the general UV-first default
for these commands. `C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe`
was used directly with `-B`; black, flake8 and pytest were already present.
There is no project pyproject.toml. This path adds no dependency graph or runtime
environment and leaves the Python module standard-library-only.

First regression execution failed as expected with `ModuleNotFoundError` before
the writer module existed. The independent Python suite then passed, initially
7, then 8 cases. Raw early green output is `python-initial-green.log`; later
cases expanded CLI and explicit independent known-vector coverage to 10.

```powershell
cmake -S spin8 -B H:/Strata/build/query-sidecar-20261023/cpu -G "Visual Studio 17 2022" -A x64 -DSPIN8_ENABLE_CUDA=OFF -DPython3_EXECUTABLE=C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe
cmake --build H:/Strata/build/query-sidecar-20261023/cpu --config Release --parallel 1
ctest --test-dir H:/Strata/build/query-sidecar-20261023/cpu -C Release --output-on-failure
```

Passed: MSVC 19.44.35224.0 CPU build with `/W4 /WX /fp:strict` on the library
and focused new C/C++ test. `build-final.log` has no warning. Full CTest passed
6/6 in 14.82 seconds (`ctest-final.log`), including existing CPU, query, query-v3
and C ABI tests plus the new native and Python cross-language tests. The CTest
environment was inspected to confirm the actual native test executable path
was passed through `SPIN8_SIDECAR_TEST_EXE`, so cross-language cases did run.

After adding only Python CLI/explicit known-vector cases, the final complete
suite passed 10/10 in 5.79 seconds (`pytest-complete-green.log`):

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:SPIN8_SIDECAR_TEST_EXE='H:/Strata/build/query-sidecar-20261023/cpu/Release/spin8_query_adapter_test.exe'
$env:SPIN8_TEST_TMP='H:/Strata/build/query-sidecar-20261023'
& C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe -B -m pytest -q -p no:cacheprovider tools/test_spin8_query_sidecar.py
```

Adversarial fixtures include bad magic/version/header/flags/count/size/
convention tags, truncation, checksum damage, rehashed NaN/Inf, invalid GQA,
oversized geometry/offset/length, duplicate/reordered layers, zero/mismatched
model/profile/position/convention bindings and rehashed unexplained trailing
bytes. Expected descriptors additionally test bad ABI/reserved fields, missing
layers, invalid byte capacities/alignment, overflowing address ranges and
result/input alias rejection. Valid unaligned file bytes load successfully.
Source bytes are overwritten after load while views still reproduce original
bits, demonstrating owned storage.

Passed: black check, flake8 with `--max-line-length=88 --extend-ignore=E203`
(standard black slice spacing compatibility), and clang-format dry-run/Werror.
Logs: `black-complete.log`, `flake8-complete.log`, `clang-format-complete.log`.
Production C++ clang-tidy `-*,clang-analyzer-*,bugprone-*` with warnings as errors
passed for user code (`clang-tidy-green.log`); 120 standard-library warnings
were hidden by clang-tidy's default non-user-code filter.

Observed failed checks were retained and repaired or isolated. Initial
clang-tidy found explicit-comparison/type-conversion clarity diagnostics; those
were fixed. Enabling strict warnings on the new test exposed int-to-byte
`std::fill` warnings; the values now have explicit uint8_t type. The intermediate
failure is `build-green.log`, followed by passing `build-final.log`.

The first unrestricted pytest run auto-loaded unrelated pytest-randomly/thinc/
numpy plugins and failed their seed hooks: 4 passed, 10 setup/teardown errors,
45.79 seconds (`pytest-final.log`). The focused suite needs none of those
plugins; disabling automatic third-party plugin loading left every task test
enabled and passed all 10. No installed plugin or repository config was changed.

The C test's clang analyzer flagged its fixed-size `memcpy(before,&view,
sizeof(view))` solely under DeprecatedOrUnsafeBufferHandling, which requests
optional nonportable memcpy_s. Source/destination arrays have the same compile-
time size; there is no external length. The rerun excludes only that blanket
checker and passes all other C analyzer checks. The failed log is
`clang-tidy-c-green.log`; the bounded-copy rerun command is:

```text
clang-tidy spin8/tests/query_adapter_c_test.c --checks=-*,clang-analyzer-*,-clang-analyzer-security.insecureAPI.DeprecatedOrUnsafeBufferHandling --warnings-as-errors=* -- -x c -Ispin8/include
```

## Self-review, limits and rollback

Reviewed tests first, then the complete public header, parser, Python parser/
writer, CMake diff, provenance and documentation against correctness,
readability, architecture, security and bounded resource use. Identity, length,
offset, finite-bit and alias checks precede allocation/publication. Counts bound
all metadata arithmetic; uint64_t retains layer-size products even on 32-bit
hosts, and those products must fit remaining file bytes before narrowing.
RAII destroys incomplete allocations. Borrowed pointer lifetime/destruction
rules and invalid-result-pointer exceptions are documented. No operational log,
secret, local model path or fixture binary is added to the source tree.

Not run: actual model/backend integration, CUDA/HIP/SYCL/Metal builds, GPU
execution, model inference, learned weights, performance/quality evaluation,
cross-platform or big-endian execution, fuzzing campaign, forced allocation-
failure injection, sanitizers, packaging/release/CI and external independent
review. No GPU/backend source is changed. Windows x64 CPU tests do not establish
cross-platform runtime behavior. Runtime pointer accessibility and concurrent
input mutation/destruction remain caller obligations. Footer integrity does not
authenticate origin. The codec/profile and position digest schemas are owned
by the later runtime integration; this loader cannot infer their semantics.

Rollback is a normal revert of this isolated commit, after coordinating with
any subsequent hook that starts using the new API. There is no model or runtime
state to undo. The new H: build/evidence folder can be retained independently;
do not delete existing evidence to perform rollback. The controller must obtain
independent review and implement/validate the real hook separately before
claiming Task4/model integration complete.

## Independent review correction: overflowing input span aliases

The independent review of `f6a7440` returned Spec issues / Needs fixes for one
Important static finding. The original top-level alias predicates were gated
by `pointer(input, declared_bytes, 1)`. A file or expectation byte count of
SIZE_MAX made that predicate false; the loader then cleared `*out` even when
it aliased the input base. Nested alias checks were similarly gated by the
validated count/capacity predicates. The initial self-review did not combine
aliasing with invalid span sizes, and therefore missed this failure path.

The focused correction is based on controller documentation commit `6985a24`.
It adds a single `disjoint_input` guard before any result write, independent
of count/capacity validity. Every nonnull declared input span must have a
representable endpoint and be disjoint from the output span. An unrepresentable
span makes disjointness unknown and is rejected conservatively without output
writes. A nonnull zero-capacity span protects its base byte. Top-level file and
expectation spans are checked before accessing the expectation descriptor;
only an aligned, exactly sized descriptor may expose nested model/layer spans.
Those nested spans use the same guard before `*out` can be written.

The failure contract is now precise: representable verified-disjoint output is
nulled on subsequent validation failure. Invalid/aliased output, or any nonnull
input span whose endpoint cannot be represented, is rejected with no output
writes. Source/header/spec documentation agree. Normal valid calls, the wire
layout, ABI version, finite F32 bits and numerical core are unchanged. The old
standalone overflow tests now check the conservative untouched-output result;
ordinary verified-disjoint validation failures still require null output.

New `overflow_alias_regressions()` runs even in the no-argument native test. It
combines file output alias with SIZE_MAX and zero lengths; expectation output
alias with SIZE_MAX and zero capacities; nested model/layer output aliases with
invalid zero counts and SIZE_MAX/zero capacities; and a numerically overflowing
expectation descriptor address, rejected without dereference or output write.
Each input is checked byte-for-byte for preservation. Existing golden, signed-
zero, identity, C ABI, capacity, geometry, malformed container and hash tests
remain enabled.

Root explicitly granted the compiler window after its Prism build had reached
321/321 and terminated at a separate version-smoke failure. A fresh capacity
guard passed (at least 1,500,000 KiB physical RAM and 500 MiB H: free). Evidence
is in `H:/Strata/build/query-sidecar-alias-fix-20261023`. Only the focused target
was rebuilt with one job:

```powershell
cmake --build H:/Strata/build/query-sidecar-20261023/cpu --config Release --target spin8_query_adapter_test --parallel 1
& H:/Strata/build/query-sidecar-20261023/cpu/Release/spin8_query_adapter_test.exe
```

RED was observed against the original production loader with only new tests:
build passed, native test exited1 with `overflow/zero file range with result
alias preserves input` (`build-red.log`, `test-red.log`). This is the first
combined failing case, not a claim that every negative case ran past the failure.
After the guard fix, the same target built with `/W4 /WX /fp:strict` and the
native test exited0 (`build-green.log`, `test-green.log`). The complete existing
Python suite, with the actual rebuilt C++/C executable and unrelated plugin
autoload disabled, passed10/10 in5.44s (`pytest-green.log`). The command and env
are the same as above, except `SPIN8_TEST_TMP` points to this fix evidence folder.
Production clang-tidy analyzer/bugprone checks passed for user code
(`clang-tidy-green.log`); the same120 standard-library diagnostics were filtered
by its default non-user-code policy. Clang-format dry-run/Werror and Git
whitespace checks passed (`format-green.log`).

The compiler window was explicitly returned to root after these checks. No
further compiler call, model access, server, numerical-core change, package
installation or external action occurred. Root's concurrent execution log was
preserved and excluded from this worker's commit. Self-review of the correction
checked overflow before overlap arithmetic, zero-length behavior, descriptor
read order, nested invalid-count paths and the documented null/untouched split.
Independent re-review is still required before accepting the corrected stage.
