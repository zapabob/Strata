# Exact CUDA Turbo KV dialects: Task 4a

Baseline: `1b9859cdf4a3eb48e3a69cf7ea62ee49a79ac777`, branch
`codex/strata-030-completion`. This is a codec substep, not full Task 4 closure.

## Requirements and decisions

Implement the pinned TheTom revision
`643956891dfdf51aecdbd05ca508dd21e21e8195` Turbo2/3/4/5/6 KV formats on sm120.
Each block is 128 values, with 34/50/66/82/98 bytes respectively. Preserve
ordered binary32 arithmetic, exact tables, midpoint rules, byte planes, signed
zero, FP16 conversion and checked numerical limits. Decode stays in stored
coordinates. PREPARE normalizes then applies F; PACK never applies F or
renormalizes. Later B insertion is after PREPARE and before PACK.

The scalar device primitives parallelize independent blocks, not reductions.
This intentionally establishes exactness first; no speed claim is made.
The additive C ABI has explicit byte capacities/strides, CUDA ordinal and
nondefault stream. Its sticky device status is separate from host return code.
Host success only means enqueued. Completion and status must both succeed
before outputs can be consumed. A numerical device error invalidates all
outputs even if another block already wrote. Caller owns allocation bounds,
lifetimes, device ownership and inter-stream ordering. CPU failure atomicity
and all existing CPU ABI/implementation files are unchanged.

Only columns 128 and 256 and compute capability 12.0 are qualified. The static
query advertises only those shapes and all six implemented operations. No
Prism or TheTom weight-format device support is advertised.

## Controls and ownership

Read canonical `CLAUDE-FABLE-5.md`, home/Codex/project AGENTS, Common
Engineering, Implementation Start Gate, Skill Selection, Security, LLMOps,
Application Development, C++, C and Python SOPs. Applied skills:
milspec-codex-standard, api-and-interface-design, evidence-changelog-closeout
and agent-self-review-evolution. Actual Windows/tool/identity instructions
override incompatible canonical prose. No formal MILSPEC certification claim.

Owned files: `tqcodec/include/tqcodec/dialects_cuda.h`,
`tqcodec/src/dialects_cuda.cu`, `tqcodec/src/dialect_cuda_device.cuh`,
`tqcodec/tests/dialects_cuda_test.cpp`,
`tqcodec/tests/dialects_cuda_c_test.c`, `tqcodec/CMakeLists.txt`, this record.
Historical dirty documents are not part of this change. No native engine,
fork patch, GUI, dependencies, model, service or governance changes.

All compiler/test transitions use the Task 2 guard in fresh Windows PS5.1.
Only initial configure starts directly. Later stages use
`tools/run_native_validation_step.py` and a terminal successful prerequisite.
Budget: 2 GiB expected additional peak, 1 GiB aggregate evidence output,
10 GiB reserve, one compile job. Initial H: free space: 28,198,641,664 bytes.
Evidence root: `H:/Strata/build/task5a-tqcuda-20261024`. Failed evidence is
retained. No old evidence is deleted or moved. Port 8080 remains stopped.

## Verification record

The original TheTom fixture, input, executable and generated C source hashes
were checked against Task 3 manifests; the checked-in golden hash remains
`326ec8f6e7c17b626a1b7c13845e5b547703f7ec2568a0b4f69b64964ae1d755`.
`oracle-provenance.json` records exact paths and hashes. No new proxy oracle
or regenerated unchanged CPU suites are substituted.

RED: configure and one-job build of the additive C ABI test succeeded with
stubbed unsupported entry points. CTest `^tqcodec_dialects_cuda_c$` then failed
1/1, child exit 8, no guard failure, no remaining owned processes.

Final results and commands follow below.

## Final measured results

CUDA 13.3.73, MSVC 19.44.35224.0, CMake 4.4.0, Visual Studio 17 2022 x64,
Release, sm120. Actual device: NVIDIA GeForce RTX 5060 Ti, compute 12.0.
The final combined CTest run passed 12/12 in 12.03 seconds. CPU-only/default-OFF
configuration and build passed; its six CTests passed in 8.83 seconds. That
configuration also compiles the new public C header without enabling CUDA.

GPU golden: 50 Turbo records, 11,013 checks, zero failures; 25,032
payload/padding bytes and 193,400 F32/padding bytes compared. Full independent
TheTom oracle: 2,762 Turbo records (490/502/526/574/670), 139,805 checks, zero
failures; 413,048 payload/padding bytes and 2,971,512 F32/padding bytes compared.
These totals include supplementary CPU factor/pipeline comparisons and
padding, and are not compressed model storage measurements. All compared
bytes and F32 bit patterns agree exactly, including signed zero. Numerical
absolute error is consequently zero for those compared finite values; no
tolerance was relaxed. Source-produced infinite FP16 scales are deliberately
rejected as RANGE, and nonfinite packed scales as NONFINITE, matching the
previously declared CPU contract.

The 1,605 wrapper, 997 scalar pack and 160 arbitrary decode oracle cases cover
midpoints, FP16 boundaries, random/sign/zero/tiny inputs and independent
128-value blocks at widths 128/256. Every fixture is repeated in two padded
rows. Additional tests compare PREPARE/FORWARD/INVERSE with CPU at three rows,
PREPARE->PACK against full encoding with an actual device-to-device same-stream
pipeline, and PACK of B=-I times prepared coordinates against CPU PACK.
Host version/format/precision/shape/overflow/stride/capacity/alignment/overlap
rejections leave outputs/status untouched. Device scalar/scale NaN/Inf/range,
negative norms, unknown sticky flags and an error followed by valid input
retain the explicit discard contract. Two explicitly created nonblocking
streams are exercised. Actual allocation ownership remains caller-owned.

clang-format dry-run passed for all five new C/C++/CUDA files. C-header
clang-tidy clang-analyzer/bugprone checks passed after changing the test's
implicit strcmp truth test to `!= 0`. Its final executable and CPU-only object
were rebuilt and the C ABI test passed again. CUDA-specific static analysis
and compute-sanitizer were not run; device qualification is the real compiled
GPU suite plus source review. One C4211 warning remains in an nvcc-generated
host registration stub. No project warning is suppressed. The earlier C4819
vendor-header warnings were resolved by the same per-target UTF-8 flags used
by the existing Spin8 build. Existing uv environment warnings are retained.

## Commands and retained failures

The initial guard ran CMake with `-S <repo>/tqcodec -B <evidence>/build -G
"Visual Studio 17 2022" -A x64 -DTQCODEC_DIALECTS=ON
-DTQCODEC_DIALECTS_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=120
-DTQCODEC_ORACLE_FIXTURES=H:/Strata/build/task5a-codec-20261024-01/oracles`.
Every later stage used the exact executable SHA and argument array in the
corresponding retained `*.plan.json` through
`uv run --no-project --offline --python
C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe python -B
tools/run_native_validation_step.py --plan <plan> --label <label>
--prerequisite <completed-success-receipt>`.
The launcher starts a fresh Windows PowerShell 5.1 guard after validating the
terminal prerequisite, binary, plan and capacity. All builds use `--config
Release --parallel 1 -- /p:BuildInParallel=false /p:CL_MPCount=1`.
`test-all` runs `ctest --test-dir <evidence>/build -C Release -V`;
`test-cpu` uses `<evidence>/cpu-off`. Full exact argv/receipts and all source,
toolchain, fixture and binary SHA-256 values are in `final-evidence.json` and
the ignored workflow `task-4a-report.md`.

Retained failures: deliberate `test-red` child 8; initial `build-green` child
1 due to test-only cudaMalloc typed-pointer conversion; initial `test-cuda`
child 8 because a by-value negative-test lambda destroyed its intended
descriptor self-alias; initial `tidy-c` child 1 for the explicit strcmp rule.
The numerical oracle checks already matched in the initial GPU run. The test
helper now takes a const reference and reports expected/actual rejection codes.
No numerical equality, error contract or compiler check was weakened.
Every completed receipt has containment true, no guard/error and zero remaining
owned processes, including retained expected/diagnostic failures.

Self-review-event: ticket_completed and qa_defect. Review covered ownership,
shape bounds, overflow/overlap, numerical rounding and zero behavior, bit
packing, failure propagation, optional build and source provenance. Narrow
test/code fixes above were sufficient; no governance change is warranted.
Frozen CPU dialect source, tables and header match their initial hashes. No
native/Spin8/engine diff exists. A read-only final check found zero listeners
on port 8080. No model/service was launched, no downloads, push, tag or release.

## Remaining scope and rollback

Three physical K caches, shared V, online softmax, QJL, cache provenance,
lifecycle, GPU invariant monitoring, and actual native/Prism/TheTom graph
connections are later Task 4 substeps. These tests cannot close full runtime,
quality, performance, context, packaging or release gates. Rollback is to
disable the default-OFF `TQCODEC_DIALECTS_CUDA` option or revert only this
commit's owned additions. Existing CPU paths and models remain intact.
