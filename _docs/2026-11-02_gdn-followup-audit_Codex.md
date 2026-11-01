# GDN follow-up: conditional bandwidth, rotations, and native profiling

Date: 2026-11-02 JST. Source checkout: be0960a0707ab2e7fc1a90d5a7888ffd149c9858
plus the earlier opt-in separate-recurrence experiment. The owner's Cargo.toml
work is preserved. This follows the existing canonical prompt, SOP, engineering
skills and implementation gate read in this session. No service, GPU permission,
clock, installed engine, default or release was changed.

## Request and scope

The user supplied a follow-up interpretation of the previous measurements and
proposed coalescing the fused kernel, rotation before quantization, and full
model profiling. Treat supplied numerical claims as hypotheses, not evidence.
The earlier separate-kernel implementation remains opt-in. This follow-up adds
reproducible mathematical checks, repeated measurements and a bounded native
profiling driver. It does not promote an optimization to the normal path.

## Findings from source and mathematics

The existing fused_gdn.cu kernel already loads/stores contiguous columns per
warp. Its base includes threadIdx.x as the column, and every thread advances
the same row_stride. It keeps 32 state values in registers per thread. Adding
the experiment's shared-memory transpose cannot remove a strided global load
that is not present; extra staging/barriers need their own measured benefit.

For 6 MiB of state read/write and a nominal 448 GB/s, the unit-correct quotient
is 14.043428571 us. The vendor lists 448 GB/s for the RTX 5060 Ti:
https://www.nvidia.com/en-us/geforce/graphics-cards/compare/
This is a conditional roofline estimate if those bytes actually cross DRAM
in the interval and that bandwidth applies. Logical state bytes divided by
CUDA-event elapsed time is effective bandwidth, not a measured DRAM throughput.
The earlier 48-buffer experiment supplies cache pressure, not counter evidence
of all DRAM misses; the one-buffer case is not a measured 100% L2 hit rate.
Cache residency, delayed writeback, dynamic clocks, and concurrent activity
prevent the claimed proof of an immutable 14-us floor. Precision reduction is
one possible way to reduce traffic, not a proven unique route to improvement.

The asserted 10-us normalization penalty is not isolated by those experiments.
The earlier one-buffer recurrence versus separate normalization medians differ
by approximately 0.89 and 0.91 us. The fused-vs-separate comparison also changes
block geometry, state staging and reduction order. Independent whole-graph
samples cannot attribute their difference solely to a launch or output traffic.
The 48-head, 128-element output is 24 KiB; a separate output write/read is
48 KiB, additional to the much larger state traffic. No hardware counter was
obtained for either traffic source.

A normalized Sylvester Hadamard R of order 8 has determinant +1. For
x = R^T e_1, ||x||_infinity = 1/sqrt(8), whereas ||R x||_infinity = 1.
Thus even an SO(8) rotation can increase the maximum component by sqrt(8).
The inverse direction helps a single-channel spike, but no fixed rotation can
reduce the maximum component for every input. The analyzer constructs both
the orthogonality check and this counterexample.

With q'=Rq, k'=Rk, and quantization errors e_q,e_k, the inner-product error is
q'^T e_k + e_q^T k' + e_q^T e_k. Orthogonality does not cancel these terms.
The script gives a legal fixed-scale E2M1 rounding counterexample: real dot
0.7, rotated FP64 dot approximately 0.7, rounded dot 0.0. This is a counterexample
to losslessness, not a simulation of adaptive NVFP4 or MXFP4 scaling, and is not
a typical-error estimate. No claim is made that all rotations worsen quality.
QuaRot is relevant primary work, with measured quantization quality outcomes:
https://arxiv.org/abs/2404.00456

For the key-by-value GDN state convention, a consistent key-axis rotation is
S'=R S, k'=R k and q'=R q. Under the update
S_new = g S + beta k (v^T - g k^T S), this gives
S'_new = R S_new and q'^T S'_new = q^T S_new in real arithmetic.
The 32-step FP64 check reaches max state error 4.44e-16 and output error
5.55e-16. This verifies a coordinate identity, not FP32 bitwise equality or
quantized recurrence stability. The recurrent quantization error can carry
forward at subsequent steps and requires a separate long-sequence quality test.

The actual native serve verifier calls gdn_step_norm_multi in verify_kernels.cu,
not the standalone native_gdn_step or the legacy fused_gdn_step_norm used by the
microbenchmark. Its windows, commits and other projections have different work.
Multiplying the synthetic 17 us by 36 gives 0.612 ms of assumed recurrence work;
its reciprocal is not model throughput, and does not identify the real critical
path. Amdahl's law requires the measured fraction of end-to-end runtime.

## Additional microbenchmarks

The unchanged production-linked benchmark ran twice more (r4/r5), with all
four correctness cases passing and 15 samples per configuration. No compiler
or kernel changes separate these runs from the final earlier executable.
Unit: median microseconds per synthetic state buffer.

| State buffers | Mode | r4 | r5 |
| --- | --- | ---: | ---: |
| 1 | original recurrence | 30.22 | 30.31 |
| 1 | coalesced recurrence | 8.53 | 8.55 |
| 1 | coalesced plus separate norm | 9.39 | 9.40 |
| 1 | existing fused norm | 6.74 | 6.59 |
| 48 | original recurrence | 72.43 | 72.35 |
| 48 | coalesced recurrence | 21.45 | 22.28 |
| 48 | coalesced plus separate norm | 23.01 | 22.49 |
| 48 | existing fused norm | 15.74 | 15.92 |

GPU utilization before these runs was 4% and 3%. During the runs utilization
includes this benchmark and is not a measurement of external load. Sampled
memory clocks and SM clocks varied; no clock locking or exclusive-use guarantee
was applied. Raw GPU telemetry is retained. During this task existing external
GPU memory usage dropped from about 11 GiB to about 1.3 GiB without any service
operation by this task. Earlier and later absolute timings are separate series,
not a controlled experiment on that external workload. Fusion remains faster.

## Profiling access and measurement semantics

Nsight Compute 2026.2.1 metric discovery returned ERR_NVGPUCTRPERM: this user
cannot access GPU performance counters. No counters were collected and no
privilege or driver setting was changed. The command also reported a bundled
Python sitecustomize/__future__ error, separately from the explicit counter denial.
Nsight Systems 2026.1.3 status reported no administrator privileges and failed
sampling readiness. A CUDA-only smoke with sample=none and cpuctxsw=none still
timed out after 75 seconds, exit 1, without a trace. The timeout cause has not
been established; do not equate the CPU sampling check with proof that CUDA
tracing always requires administrator access.

NVIDIA documents the effects of cache flushing, serialization and profiling
permissions: https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html
The native diagnostic instead uses the existing STRATA_DECODE_TIMING and
STRATA_VERIFY_PROFILE options, with no kernel implementation changes.
The GPU profile uses timestamp kernels and disables some branches/fusions;
its timing is not the normal engine's uninstrumented latency. Host brackets
are nested inside verify; never sum them again with verify. GPU wait intervals
may include waiting for CPU/I/O; they are not pure compute or physical PCIe time.

## Bounded native experiment

Driver: tools/profile_gdn_native_followup.py. Artifact root:
H:/Strata/evidence/gdn-native-followup-20261102.
The separately built 0.4.0 baseline engine is SHA256
b5e4d5255a48882334b27ab643c22c9c1b54e4580f82b402176a9ca5661bf6f1.
It is not a new build of the modified checkout. It runs the normal fused
native verification path; the separate-recurrence candidate does not participate.

The driver pins the executable hash, reads model files without modifying them,
uses a fixed 51-token synthetic prompt. The initial request limit was 32;
after a resource-floor abort the final bounded diagnostic requests two
independent 8-token continuations. These truncated outputs are not a quality test. Context capacity is 4096, spec=2 without MTP or lookup, k8v4 cache,
512 static expert slots, four CPU workers, and mmap expert source. This is a
short diagnostic with a small expert cache, not the user's 131k qualification,
standard MTP configuration, HTTP latency or a general model-quality benchmark.
Full multi-GB model hashes were not recomputed; file sizes/mtimes and tokenizer/
profile hashes are retained. Model provenance is therefore limited accordingly.

Containment uses the existing atomically assigned Windows Job: 12 GiB commit
cap, one process, 480-second deadline and 8 MiB output cap. Both attempted runs
required 10 GiB at start; after the repeated failure the driver now requires 16 GiB
available RAM and 8 GiB dedicated VRAM; sampled abort floors are 2 GiB RAM,
6 GiB commit headroom and 1 GiB dedicated VRAM. These are sampled floors, not
reservations or proof against WDDM paging. No external process is stopped.
The tokenizer uses regex 2026.9.29 in uv's isolated runtime, without project
manifest or global dependency changes.

The exploratory baseline-r1 used the engine's automatic PCIe choice, short-read
prefill and default route-tail skipping. It is excluded from a controlled
baseline/profile comparison. After inspecting those defaults, subsequent runs
freeze PCIe share at 0.18, adaptive swaps at zero, PLE direct, short-read zero,
and STRATA_ROUTE_TAIL_SKIP=0 so that routed experts are not intentionally omitted.
The exact arguments/environment for each launched process live in its binding.

Exploratory baseline-r1 reached READY and emitted partial output, but the
controller stopped at available RAM 2,142,339,072 bytes (below the 2 GiB floor).
Peak Job commit was 8,504,217,600 bytes, below its 12 GiB cap. This was a physical
RAM admission failure, not a Job-cap failure or CUDA kernel error. No DONE line
was observed. Cleanup confirmed zero active Job processes. No throughput is
reported for this aborted run. Subsequent trials reduce output from 32 to 8
tokens without weakening any resource threshold.

The matched baseline-r2 also stopped at the RAM floor, at 2,142,785,536 available
bytes. It reached READY and completed the first 32 of 51 prompt tokens in 99,219
ms, but no request reached DONE. Peak Job commit was 8,804,040,704 bytes, again
below the cap. Minimum sampled dedicated VRAM was 9,254 MiB. Cleanup confirmed
zero active Job processes. This is not a completed prefill or decode benchmark.
No profiled native arm was launched after two RAM-floor failures. Actual GPU
stage percentages, complete native latency, output parity and a bottleneck
ranking therefore remain NOT_MEASURED. Neither failed run is used as a speed
result or as proof that physical disk I/O is dominant.

The driver's future startup requirement is now 16 GiB available RAM, derived
conservatively from the observed working-set pressure; this threshold has not
been demonstrated sufficient. The 12 GiB Job cap, 2 GiB running RAM floor and
all other limits are unchanged. An explicit GpuMemoryFloor failure remains
distinct from host-RAM pressure. No unrelated application was stopped to create
headroom. A future comparable pair uses a fresh baseline label, then a profile
label, under the same frozen binding. Do not retry the completed run directories.

Reproduction (only when admission passes):
uv run --no-project --python 3.12 --with regex==2026.9.29 python tools/profile_gdn_native_followup.py baseline --label r3
uv run --no-project --python 3.12 --with regex==2026.9.29 python tools/profile_gdn_native_followup.py profile --label r1
uv run --no-project --python 3.12 python tools/analyze_gdn_native_profile.py H:/Strata/evidence/gdn-native-followup-20261102/baseline-r3 H:/Strata/evidence/gdn-native-followup-20261102/profile-r1

## Validation and retained artifacts

The mathematical analyzer passes with the new counterexamples and conditional
roofline calculation. Both additional microbenchmark runs pass all four
correctness geometries. No production CUDA code changed in this follow-up;
the earlier sanitizer evidence is unchanged and was not rerun without a change.
The microbenchmark executable hash matches the previous final receipt.

Five synthetic receipt tests pass for completed-output parsing, failed-run
rejection, argument mismatch, contaminated GPU window counts and differing token
IDs. These fixtures test reporting logic and are not hardware measurements.
Python compilation and git diff --check pass. The native controller exercised
its real resource-floor termination twice, with cleanup confirmed each time.
A successful full native baseline/profile pair remains untested.

Raw r4/r5 JSONL, GPU samples, mathematical output, profiler access observations,
unit-test log and both aborted native runs are retained under
bench/results/2026-11-02-rtx-5060ti-gdn-coalesced/followup. The initial receipt is
unchanged; the follow-up receipt records the extended tooling's current hashes.
No commit, push, install, default change, privilege change or service stop occurred.

Self-review: verified the actual native call route before extrapolating the
microbenchmark; detected profiling-induced fusion changes and default Expert
omission; rejected two partial runs instead of computing misleading throughput.
The intended next performance experiment is a completed, bounded native timing
pair after adequate RAM headroom is available. No FP4/state-layout change is
justified by the current evidence.