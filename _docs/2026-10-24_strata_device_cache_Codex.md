# Task4b physical CUDA cache and online Attention — 2026-10-24

This is the bounded, opt-in library prerequisite for the approved Strata 0.3.0 Task4. It does not integrate native or Prism model graphs. Source baseline: e7f7265072f660316d70ed8fc7de7bf146fde657 on codex/strata-030-completion. Independent controller review remains required. No service, model, download, push, tag, release, default-setting change, or historical evidence cleanup was performed.

The implementation owns tqcodec/include/tqcodec/cache_cuda.h, tqcodec/src/cache_cuda_internal.h, cache_cuda_plan.cpp, cache_cuda.cu, cache_cuda_snapshot.cpp, tqcodec/tests/cache_cuda_test.cpp, cache_cuda_c_test.c, the additive tqcodec/CMakeLists.txt block and this record. Previously dirty documents and the user's untracked implementation plan are unrelated and preserved.

The canonical PC prompt, applicable AGENTS, MILSPEC/SOP instructions, the dispatched brief and bound outline, implementer contract and test-driven-development/writing-good-tests skills were read before implementation. Actual Windows tooling and higher-priority instructions override conflicting identity/Linux/tool assertions. The self-review skill is applied in review-only mode; no governance changes are made. apply_patch returned a generic write error; ordinary authorised PowerShell/.NET literal writes worked. No ACL modification or elevation was used. The failed launcher attempt using a different Python without numpy is retained; no dependencies were installed. Validation uses existing C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe.

## Interface and mathematics

The C ABI is engine independent, version/size checked, with byte capacities, strides, current device ordinal, an explicit nondefault stream and caller-owned aligned arena. Opaque host plans are immutable; each arena is one session. A native VerifyWindow that mixes conversations must partition rows by session in its future adapter. max_append_rows bounds input batches independently of cache capacity and max_queries. It is nonzero and no greater than capacity. Append input buffers need only this bounded batch, not a full-context F32 allocation. The persistent device append count is checked before input reads/publication. Caller buffers, arena and plan must remain alive through their ordered work; graph replay preserves GPU buffers and command metadata, while descriptors are copied by value into launches. Event dependencies are the caller's responsibility when transferring stream ownership. The implementation does not switch devices or use an implicit default stream.

One strict libspin8 plan constructs all three FP64 8x8 matrices from the same Spin element, checks determinant +1, normalized Frobenius/maximum Gram error <=1e-12 and logabsdet <=8e-12, and repeats each block across 128/256 columns. All three FP64 matrix identities participate in cache identity, even for a single selected view. The consumed coefficients are F32, qualified at 1e-5 with logdet bound blockwidth*1e-5. Unsupported F16/BF16 coefficients are capability-false.

K is PREPARE(k), then B_r, then exact PACK with the original norm. Thus U_r=B_r F, and F is applied once. F is the reviewed TheTom D2*(H128/sqrt128)*D1 primitive. Q is B_r F(q). One shared V is PACK(PREPARE(v)) in F coordinates and output applies F inverse once. Exact Task4a private device helpers and CPU dialect references are reused without source modification. Fixed Turbo2/3/4/5/6 block sizes are 34/50/66/82/98 bytes per128 values, including FP16 norm, pinned to TheTom643956891dfdf51aecdbd05ca508dd21e21e8195. No weight/generic-codec substitution is used. Diagnostic F32 is a separate explicit representation without quantisation, not a claim that finite codec error is a rotation defect.

Alpha must be explicitly finite, nonnegative, zero for inactive views and sum to1 within1e-12. The documented uniform default is caller-supplied 1/3 each (or1 for the single selected view). An all-zero vector is rejected, without automatic substitution. Mixed K4/V2 and all five qualified Turbo widths are supported. beta must be0; shared QJL and positional transport capability flags are false and their requests reject. No sketch bytes or work are allocated at beta0. Physical copy does not change positional coordinates.

Attention handles multiple queries/heads, GQA, explicit scale, additive bias, causal positions, byte masks and per-query int64 physical key selections (-1 skips). Duplicate or invalid indices reject on device; future native adapters must expand their original selected block indices into these physical keys without changing semantics. View-weighted scores are summed before one stable online softmax and shared-V accumulation. There is no Q-by-K score matrix. Computation uses bounded per-query/head local arrays and double score/softmax accumulation. This scalar reference-oriented CUDA implementation has no speed/adoption qualification.

## State, lifecycle and integrity

Host structural rejection leaves outputs and arena unchanged. Host OK means enqueued; valid consumption requires successful stream completion, zero device status and valid=1. Numerical, capacity, state, empty, all-masked, index and transform errors invalidate all views and dependent output. On runtime failure, output is invalid even if status cannot be written. Append publishes tentative rows only after every K view/shared V worker succeeds; Attention reads tentative rows for verification. Commit publishes all tentative rows, cancel returns to committed, truncate requires target<=committed, and invalidation is sticky. Explicit quiescent initialise/reset clears all history and audits coefficients. No per-call allocation or host synchronisation occurs in append/attend/control/copy; initialise and snapshots are documented exceptions.

Each arena stores plan identity, checked by hot-operation readiness before consumption. Identity hashes explicit geometry, format, representation, batch/query limits, alpha, convention/pinned codebook source, all three matrices, actual F32 B and F factors, and required caller model/adapter/position SHA256 values; no raw pointers or padding are hashed. Caller identities must honestly describe full model/adapter/position processing. No mutable profile update is allowed: construct a new plan and reset, or restore a matching snapshot.

Clone copies committed rows to an empty distinct identical cache and commits them. Selected physical copy appends committed source rows to a distinct identical destination with one shared stream after caller dependencies. Both arenas must be disjoint. All selected indices are validated before any payload copy; duplicates/ranges fail. Same-cache cycles and all arena intersections reject before mutation. No hidden staging allocation or full-history replica implements relocation.

Snapshot storage is exactly80+arena bytes. Its header binds magic/version, plan identity, complete payload SHA256 and length. The complete capacity arena (including padding/tail) is hashed. Snapshot audits actual factors, copies to bounded host staging, explicitly synchronises the supplied stream, requires committed=tentative and healthy state, and validates identity, exact B and active payload finiteness before copying to caller output. Restore first makes an immutable host staging copy and checks complete lengths, digest, identity, state and payload before any device mutation; it then copies/audits/synchronises. Caller snapshot data must be immutable during the call and privately protected. These are same-machine ABI snapshots, not a portable wire format or authenticated adversarial format. The return/completion/status contract still applies after CUDA errors. Recurrent-state invalidation/replay is outside this standalone cache.

The audit reads actual arena B coefficients and evaluates the actual consumed fwht primitive on128 basis vectors, including its module-constant signs and normalization. The independent expected F factors are recovered from the CPU dialect's FORWARD basis operations; they are not substituted into GPU storage. Full128 Gram/Frobenius error, sign, logabsdet, finite values and baseline drift are recorded for F. B metrics are per repeated8x8 block. The Hadamard determinant sign derives from actual factors; its logdet includes actual normalization. An actual device B fault yields transform_invariant_violation and refusal to attend. Audit is explicit/bounded and not a per-token dense determinant, global synchronisation, correction or fallback. Scheduling every1024 generated tokens OR60seconds and stopping inference/RNN state remain later runtime work.

## Allocation and resource ledger

The cache library owns no GPU malloc. The caller owns one exact 256-aligned arena. Metadata at capacity5 is1048 bytes: state24, command24, identity32, all three B matrices768, audit160, positions40. Payload bytes below include every norm. Other bytes are alignment padding, not omitted storage. Single-view modes still retain all three matrices/identities for provenance, but only the selected compressed K payload. There is no full-precision K/V history in compressed mode.

| columns | K/V bits | active K views | payload | metadata | padding | arena |
|---:|---|---:|---:|---:|---:|---:|
|128|2/2|3|1360|1048|1688|4096|
|256|2/2|3|2720|1048|1352|5120|
|128|3/3|3|2000|1048|1048|4096|
|256|3/3|3|4000|1048|1096|6144|
|128|4/4|3|2640|1048|1432|5120|
|256|4/4|3|5280|1048|1864|8192|
|128|5/5|3|3280|1048|1816|6144|
|256|5/5|3|6560|1048|1608|9216|
|128|6/6|3|3920|1048|1176|6144|
|256|6/6|3|7840|1048|1352|10240|
|128|4/2|3|2320|1048|1496|4864|
|128|4/2|1 (each of v/s/c)|1000|1048|1280|3328|
|128|diagnostic F32|3|20480|1048|1000|22528|
|256|diagnostic F32|3|40960|1048|1000|43008|

These measurements use capacity5, kv_heads2, q_heads4, max_queries2, max_append_rows3. Persistent host plan size is2304 bytes. Construction temporarily allocates a1536-byte strict Spin plan (three64-double matrices), plus fixed automatic local construction arrays; allocator overhead/host stack peak is not measured. Quiescent snapshot/restore host staging is at most80+arena bytes per call, separate from caller's snapshot buffer. Hot calls allocate no staging. External K/V input tensors scale by max_append_rows*kv_heads*stride, Q/output by max_queries*q_heads*stride, positions by their batch/query bounds, and optional masks/bias by max_queries*q_heads*capacity. Caller-selected indices scale by max_queries*selection_width for Attention and capacity for copy. These caller tensors and any integration-owned allocations are excluded from the arena figure, explicitly. Diagnostic input/output/test-reference/snapshot buffers are test allocations, not compressed persistent history.

The consumed constant tables occupy1896 bytes in the linked cache CUDA module (474 floats: centroid/threshold/sign tables), separate from arena. cudaFuncGetAttributes reports1896 constant bytes on each kernel; count module constants once, not six times. Relevant compiler/runtime resources on the tested device are:

| kernel | local bytes/thread | shared bytes/block | registers/thread | max threads/block |
|---|---:|---:|---:|---:|
|audit|66560|0|254|256|
|append|1136|0|128|512|
|finish|0|0|12|1024|
|control|0|0|10|1024|
|attend|6144|0|236|256|
|copy|0|0|36|1024|

Audit local storage includes the fixed128x128 F operator, independent of cache length. Attention/codec local arrays are compiler-managed per thread, not persistent K history. Driver/module/context/local-memory reservations, allocator overhead and external buffers mean arena bytes are not the measured total GPU peak. No GPU peak/speed claim is made.

## Validation and retained failures

Evidence root is H:/Strata/build/task5a-device-cache-20261024. The guard enforces additional peak3GiB, aggregate evidence cap2GiB, reserve10GiB, timeout600 seconds, containment and one compiler job. Independent configure used a fresh WindowsPowerShell5.1 host; every dependent stage used tools/run_native_validation_step.py with a terminal successful prerequisite. Plans contain exact binary hashes/arguments. Failed stages remain alongside successful receipts; a failed test is never a successful prerequisite. Initial H free28154044416 bytes, no8080 listeners; latest pre-closeout free22781280256 bytes with aggregate19422118 bytes and no8080 listeners. No evidence cleanup occurred.

Windows qualification: NVIDIA GeForce RTX5060Ti, compute12.0, driver616.92; CUDA13.3.73, MSVC19.44.35224.0 (toolset14.44.35207), CMake4.4.0, LLVM22.1.8. CUDA uses sm120, --fmad=false --ftz=false --prec-div=true --prec-sqrt=true. Host C++ uses /W4 /WX /fp:strict /utf-8. CUDA generated stubs still emit C4211 extern/static warnings under /W4; these were not hidden or called warning-free.

Failing-first receipts cover C ABI construction (test-red), unimplemented initialise (test-device-red), append (test-append-red), snapshot lifecycle (test-lifecycle-red), arena plan-identity binding (test-binding-red), strict zero-alpha rejection (test-alpha-red), and bounded input acceptance (test-batch-red). The last two reproduce the controller's concrete consumer findings before implementation changes. Build failures for a broad dialect_tables.inc include and old CUDA graph-instantiation signature were retained and corrected using existing CPU FORWARD factor derivation and the installed SDK signature. No unchanged Task4a2762-case bit oracle was rerun because its shared helper was not changed.

Final source-bound build-graph-query and test-graph-query passed. The latter ran4/4 tests: new CUDA and C ABI, affected CPU cache and transport. CUDA reported28068 checks,63816 independently compared physical payload bytes, maximum Attention absolute error6.02325227e-08. Its12.71-second total CTest duration is a correctness test duration, not throughput. The terminal receipt at2026-10-24T07:16:16.2512295Z has child0, no guard/error, contained=true and zero owned processes after cleanup.

The deterministic fixture is source-generated by (int((i*37+seed)%211)-105)*.003f with seeds7/11/19/17 and strict planes(0,1,.37),(2,5,-.61); the test source hash below binds the fixture. CPU PREPARE/B/PACK independently compares actual GPU payload bytes. FP64 ordinary Attention verifies diagnostic rotation equivalence; weighted dequantised-view CPU reference verifies quantised Attention separately. Coverage includes all5 widths at128/256, independent K4/V2, each single view and consensus, nonuniform alpha .2/.3/.5, GQA/multiple queries, padded strides, causal/mask/bias/scale/sparse keys, empty/all-masked, overflow/alias/device/finite boundaries, partial append no publication, zero counts, graph replay with changed device append/query counts and positions (query count2 to1 leaves the unused output rows untouched), clone/copy/truncate/cancel/isolation, compressed and diagnostic snapshot round trips, corrupt/incompatible snapshots, physical fault invalidation and unsupported position/QJL requests. Batch=3/capacity=5 tests use only three-row append buffers and reject count4 before publication.

Actual initial audit values in test-closeout.stdout.log: Bv E_F1.937676551110687e-08, maxGram3.7986350065466468e-08, logdet-3.0313452276109487e-08; Bs/Bc E_F9.9522165832064369e-09, maxGram9.8954073823875888e-09, logdet3.9581629016072206e-08. All three have sign+1, finite1, drift0. F E_F3.4228545331416132e-08, maxGram3.4228545331416171e-08, logdet-2.1906267067933039e-06, sign+1, finite1, drift1.5127021302241417e-09. Quantisation error is separately measured above.

Default-OFF configure-cpu-off/build-cpu-off/test-cpu-off passed with all three cache/dialect options OFF, no CUDA compiler configuration, the new C header object compiled and6/6 existing CPU tests passed in5.24 seconds. This protects the unchanged CPU library source path; it is not a cross-toolchain binary reproducibility claim. No CUDA/HIP/SYCL shared backend source was modified.

Static/format checks passed: tidy-closeout on the two host implementation files with clang-analyzer-* and bugprone-* plus warnings-as-errors; tidy-c on the C ABI sample; format-check used clang-format --dry-run --Werror on all seven owned C/C++ files. Initial tidy-host failed with owned pointer conversion, float-storage memcmp and widening diagnostics plus vendor macro diagnostics. Owned causes were corrected (explicit casts/byte comparisons/widening), and CUDA SDK was correctly classified with -isystem without disabling checks. Final clang-tidy retained its default exclusion of240 host non-user diagnostics and6 C non-user diagnostics; logs disclose these, and no all-dependency warning-free claim is made. CUDA generated-stub C4211 warnings remain as described. Final owned staged whitespace check follows before commit.

At2026-10-24T07:17:04.3597413Z, source hashes matched the final pre-build snapshot, minimum terminal-receipt H free was22766178304 bytes, live H free22766039040 bytes, owned evidence22736474 bytes and8080 listeners0. The difference from initial free space is not attributed to this approximately22.74MB evidence root; unrelated storage/processes were neither modified nor stopped. All guarded stages retained the required reserve.

## Self-review and remaining scope

Self-review-event: local_fix / correctness / tqcodec/device-cache. Device identity was missing from initial arena readiness; a failing cross-adapter test led to persistent identity validation. Self-review-event: rework_returned / interface-contract / tqcodec/device-cache. Controller consumer inspection found full-capacity append input sizing and ambiguous zero-alpha substitution; bounded batch configuration and strict simplex tests now cover both. Self-review-event: qa_defect / observability / tqcodec/device-cache. Arena accounting alone omitted compiler local/module resources; resource queries and consumed-F audit metrics now separate these costs. Response level is review-only: no instruction/skill/governance changes. Future adapter review must explicitly inspect per-conversation ownership, chunk versus history extents, all-masked semantics and original native sparse selections before integrating.

Self-review checked arithmetic/declared span bounds, alias handling, immutable plan identity, sticky errors and publication order, snapshot validation before mutation, same-cache copy rejection, all-three Spin provenance, actual F storage binding, default-OFF wiring and ownership. Caller actual CUDA allocation provenance/ownership remains required; declared byte-span checks cannot prove arbitrary pointer allocation validity. Snapshot integrity is not authentication. Coefficient monitoring does not continuously check every payload byte. No automatic correction or fallback exists.

Not qualified here: Linux/HIP/SYCL/Metal, F16/BF16 coefficients, full position-dependent transforms, beta>0 QJL, native prefill/speculative graph integration, Prism16 normal-Attention layers and48 recurrent-layer state handling, real-model quality/performance, periodic scheduler/inference cessation, G1 runtime/G2/G3/publication/release. No compute-sanitizer/device static-analysis run is claimed. Windows sm120 standalone correctness is the bounded result. Independent controller review follows this local commit.

## Exact source and binary provenance

source-final-before-graph-build.json binds the final implementation/test fixture after formatting and before build-graph-query. The source equality check in closeout-state.json passed. The only change after the earlier source-closeout snapshot was the additional captured-Attention query-count test; no library implementation or CPU-OFF source changed after its qualification. provenance-final.json records shared sources/toolchain and final cache test/library binary hashes. CPU-only binary hashes are in provenance-cpu-off.json. The evidence root retains exact .plan.json command arguments and .receipt.json terminal outcomes for each stage.

Representative dependent invocations (existing installed Python, no dependency installation) are:

```powershell
& 'C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe' -B tools/run_native_validation_step.py --plan H:/Strata/build/task5a-device-cache-20261024/build-final.plan.json --label build-graph-query --prerequisite H:/Strata/build/task5a-device-cache-20261024/format-graph-query.receipt.json
& 'C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe' -B tools/run_native_validation_step.py --plan H:/Strata/build/task5a-device-cache-20261024/test-final.plan.json --label test-graph-query --prerequisite H:/Strata/build/task5a-device-cache-20261024/build-graph-query.receipt.json
```

The build plan uses cmake --build with --parallel1, /p:BuildInParallel=false and /p:CL_MPCount=1. The test plan uses ctest -C Release -V -R '^tqcodec_(cache_cuda.*|cache|transport)$'. The separate default-OFF build was a fresh -S tqcodec -B cpu-off VS2022 x64 configure with no enabling options. Existing evidence labels should not be overwritten by a future reproduction: create fresh labels/root and retain equivalent guards.
```json
[
  {
    "sha256": "87b5d78b9adc1474bbf423bb9548b38d0dd9de2307b831621e637c8ea9395758",
    "path": "tqcodec/CMakeLists.txt"
  },
  {
    "sha256": "7c9611aae850412590b3ab83fe29039cd2ea08ae1d69af469a0a418614e227b1",
    "path": "tqcodec/include/tqcodec/cache_cuda.h"
  },
  {
    "sha256": "5d4c2f86849a9da0b879997e6fe92db3b7710d46891182556a7ba3861d956517",
    "path": "tqcodec/src/cache_cuda_internal.h"
  },
  {
    "sha256": "f919328c18ae05b4694b8ad376cc3f4f544921d6eea57ed289e38f07a1850daf",
    "path": "tqcodec/src/cache_cuda_plan.cpp"
  },
  {
    "sha256": "8f3bbaba98d952ed27fcfac5bf4bb162afaeccbd0e314f65009b1b6880e683a9",
    "path": "tqcodec/src/cache_cuda_snapshot.cpp"
  },
  {
    "sha256": "85f3fef2d6fad23a082374bfc071f749b69a7f99f313ba13514f1392e42a7516",
    "path": "tqcodec/src/cache_cuda.cu"
  },
  {
    "sha256": "06c791975eff26edb4a2adc87740aedd99e1a449c3715b9e27dd8a5f9f981b3c",
    "path": "tqcodec/tests/cache_cuda_test.cpp"
  },
  {
    "sha256": "34214dc98e07cd247b2fab47dede20120fa58d470ebe264302d71af215304f83",
    "path": "tqcodec/tests/cache_cuda_c_test.c"
  }
]

```

```json
[
  {
    "path": "C:/Program Files/CMake/bin/cmake.exe",
    "sha256": "4510f1883dfad3238602bae9a7a4b441fb4a931a643604aa44336710b6be5f6f"
  },
  {
    "path": "C:/Program Files/CMake/bin/ctest.exe",
    "sha256": "b3fcab80b6f4155ea1312380e7f7d4e463b16a975c991d8d599176f410fa3754"
  },
  {
    "path": "C:/Program Files/LLVM/bin/clang-tidy.exe",
    "sha256": "56bd92e0aa76783d1fb2f4c3d57dcaab87c695faf216b8a91129edd79ce51984"
  },
  {
    "path": "C:/Program Files/LLVM/bin/clang-format.exe",
    "sha256": "3c563ca6f676b84bee959e530b2a10c010019168b695f3877f3423e3a4949e1b"
  },
  {
    "path": "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3/bin/nvcc.exe",
    "sha256": "92d993c6e7025e1597d0d895e65e8658f5f1d41576a477656647a7eece2cd35f"
  },
  {
    "path": "C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/cl.exe",
    "sha256": "f4eba2208e132daf500b7d7bbdf051e930c59dbdc1d87c35e146479427ffeb8d"
  },
  {
    "path": "C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/link.exe",
    "sha256": "1a9889872481270ca45febcdaf26e75c53cea505c9eb214daea1098d4cf706bd"
  },
  {
    "path": "H:/Strata/build/task5a-device-cache-20261024/build/Release/tqcodec_cache_cuda_test.exe",
    "sha256": "66fc619773546f618653222aebf557dc34e054ca3141c5c7480f468c482cea58"
  },
  {
    "path": "H:/Strata/build/task5a-device-cache-20261024/build/Release/tqcodec_cache_cuda_c_test.exe",
    "sha256": "9061d559bf35adb7fd20e72c3ac15bc28e4dd6e24d8f3ef70df385bf68d5f2a8"
  },
  {
    "path": "H:/Strata/build/task5a-device-cache-20261024/build/Release/tqcodec_device_cache.lib",
    "sha256": "6b48421f6fed2d69d88fc039537fd1cea4af899c84ecf9e025e1c7ca001c6f36"
  },
  {
    "path": "tqcodec/src/dialect_cuda_device.cuh",
    "sha256": "2e1e9cf921f7c115e05370c6ff61eb8a9299dbb31b85307a3c9a05c845061060"
  },
  {
    "path": "tqcodec/src/dialects.cpp",
    "sha256": "4820e36ccdc083440a52171fd21871bf3fff2ecc2bf593b2815156750300f0d7"
  },
  {
    "path": "tqcodec/src/dialect_tables.inc",
    "sha256": "10cc74988aa448fe3ad6bfae6c52f3d9ce452123b1b014a666fa5b5d3ecb3766"
  },
  {
    "path": "tqcodec/src/dialects_cuda.cu",
    "sha256": "376a9ff0a329008e10e5443ac7ebcf77ed7d784d11db698cad107fa4b2f6c5e7"
  },
  {
    "path": "spin8/src/spin8.cpp",
    "sha256": "18f6ccd47a25d397c22fc13671b15165d285237a204589e2b5b658e7791b2b8f"
  },
  {
    "path": "tools/run_native_validation_step.py",
    "sha256": "17dac228836386d2b16215a3cfd02687f16ca73d07e909631db46b3692cce1ae"
  },
  {
    "path": "tools/verify_codec_dialects_build.ps1",
    "sha256": "de2ee5053b3852a675e06ef25a3a98c98090a19d8769fc828d7ce083c2e9eac1"
  }
]

```

```json
[
  {
    "sha256": "9547581f883fc9e80aa03a84c5483146edb1f1ac4edffea02de689554684fd43",
    "path": "H:\\Strata\\build\\task5a-device-cache-20261024\\cpu-off\\Release\\tqcodec_c_abi_test.exe"
  },
  {
    "sha256": "7ac662446c7ece84a0fb8812bb375659f355f6f619174237253adf7317fb4149",
    "path": "H:\\Strata\\build\\task5a-device-cache-20261024\\cpu-off\\Release\\tqcodec_cache_test.exe"
  },
  {
    "sha256": "a377637323e45145cf72db80ab68d281390fb3da24d07a6d81992a883c4b628c",
    "path": "H:\\Strata\\build\\task5a-device-cache-20261024\\cpu-off\\Release\\tqcodec_calibrate_test.exe"
  },
  {
    "sha256": "18b8147deda6eb8f1cd3421ba7d4407455e430de4e6e0a51643c873b74a146b3",
    "path": "H:\\Strata\\build\\task5a-device-cache-20261024\\cpu-off\\Release\\tqcodec_distill_test.exe"
  },
  {
    "sha256": "754a4f665acff91c46f0d0633b6fe854f12f87a33f8e41c2558e168b02156c8a",
    "path": "H:\\Strata\\build\\task5a-device-cache-20261024\\cpu-off\\Release\\tqcodec_test.exe"
  },
  {
    "sha256": "5a7d5ae4c34b550b329ba6e56d7243847d3b69e52313aa1d4d45bfda21758cd2",
    "path": "H:\\Strata\\build\\task5a-device-cache-20261024\\cpu-off\\Release\\tqcodec_transport_test.exe"
  },
  {
    "sha256": "e141b8f8a3180178533e5be3bbe3d355df87a813a0e583b68aaae5b5617265b4",
    "path": "H:\\Strata\\build\\task5a-device-cache-20261024\\cpu-off\\Release\\tqcodec.lib"
  }
]

```
