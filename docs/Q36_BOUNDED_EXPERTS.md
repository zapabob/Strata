# Qwen3.6 bounded expert working storage (candidate)

This is an opt-in source candidate for Windows CUDA with the CPU expert pool.
It is not qualified for the installed app or for real-model generation yet.
The default remains `--q36-memory legacy`.

## What it changes

Use `--q36-memory bounded-experts-v1` together with
`--q36-expert-store mapped-pack` and an explicit `--expert-slots N`.
`N` must be a positive decimal integer smaller than the model's expert count.
The model and a valid existing `.q36epk` must already exist. This mode refuses
an invalid/missing pack instead of creating or repairing one.

CPU misses run through the existing CPU pool in waves of at most eight jobs.
Each job keeps its original token group and output addresses. The weights are
read into reusable storage rather than dereferenced in the mapped pack. The
consumer finishes all worker reads before storage is reused.

Both CPU staging and the existing GPU transfer pool read through a serialized,
unbuffered Windows handle to the same pack object. One aligned 1 MiB buffer
handles sector alignment and short end-of-file reads. Unsupported I/O is an
error; there is no mapped-payload or buffered-read fallback. The model and pack
remain read-locked for the bounded pack's lifetime. Full SHA-256, layer CRC,
geometry checks and the existing DPAPI/NTFS receipt rules still apply.

H2D keeps its existing slot completion waits. `STRATA_Q36_PIN_PIPELINE` and
`STRATA_Q36_STREAM_RESIDENT` retain their separate opt-in behavior. This mode
forces file-backed staging regardless of `STRATA_Q36_FILE_STAGING`; it does not
change that environment variable. Expert slot rebalancing still runs normally.
Weights, router/top-k, context, KV precision, MTP depth and arithmetic settings
are not changed by this mode.

## Bounds and admission

CPU expert storage is `8 * align64(max_layer_expert_stride + 4096)` bytes,
capped at 64 MiB; larger layouts are rejected before allocation. The H2D pool
uses at most two 32 MiB buffers. A failed pin allocation can use the existing
smaller pinned or pageable staging, still within that cap. Complete pool failure
is fatal in this mode. The unbuffered I/O buffer adds 1 MiB.

On 2026-11-07, a read of the existing UD-Q4_K_XL pack's 5,376-byte header found
41 layer records, a maximum stride of 2,310,000 bytes and an expert payload of
20,127,604,736 bytes. Those records imply 18,512,896 bytes of CPU stage storage
and at most 86,670,336 bytes (82.6553 MiB) for the three expert-working buffers.
These are header-derived allocation calculations, not measured peak RAM or a
fresh verification of that model/pack.

The bounded path samples available physical RAM and commit headroom before its
new host allocations and while filling CPU/H2D staging. Admission requires the
planned additional bytes to leave at least 3 GiB RAM and 4 GiB commit headroom.
Hybrid expert placement must leave 768 MiB of observed free VRAM after its
planned slots/staging/output buffers. Rejection reports requested and observed
bytes. It does not silently lower a setting.

These checks are not a total-process memory cap. Dense loading, verification,
CPU worker scratch, GPU driver allocations, prompt workspace, recurrent state
and typed KV remain separate. Other programs can consume headroom after a
sample. Real qualification still requires the owned-process external resource
guard, including H-drive 10 GiB and C-drive 5 GiB free-space floors.

## Host integration contract

Probe the exact candidate executable with `--help`, before model/GPU startup.
Both `strata` and `strata-q36` emit a separate line with this prefix and JSON:

```text
Q36_MEMORY_CAPABILITIES {"schema":1,"family":"qwen35moe","modes":["bounded-experts-v1"],"flag":"--q36-memory","requiresExpertStore":"mapped-pack","requiresExplicitSlots":true,"scope":"expert-working-storage","totalProcessBound":false,"qualification":"experimental-unqualified"}
```

Unsupported builds emit the same schema with `modes: []`. Bind the parsed
capability to the executable digest. A missing/unknown marker is not support.
Do not add fields to, or relax parsing of, `Q36_KV_CAPABILITIES`.

After placement, stderr emits `Q36_MEMORY_EFFECTIVE schema=1` with `generation`, `mode`,
`scope`, `cpu_stage_bytes`, `cpu_wave_jobs`, `h2d_stage_bytes`,
`io_scratch_bytes`, `reader=windows-unbuffered`, `existing_pack=1` and
`total_process_bound=0`. The existing `Q36_EFFECTIVE` still reports context,
prefill, slots, KV types, graph mode and CPU workers. Bind observations to the
owned process/startup; the new memory row alone is not readiness or fit evidence.

The parent should expose this only as an explicit candidate selection after
qualification. The installed native 0.5.1 digest is not evidence for this mode.

## Verification boundary and next gate

CPU tests cover bounded waves, original job metadata, reader lifetimes, partial
read/consumer failures, admission boundaries, payload reads with inaccessible
mapped pages, unaligned and concurrent file reads, EOF, same-file identity,
writer exclusion, and refusal to rebuild. A synthetic test using the real CPU
pool also passed byte-for-byte output parity for Q4_K/Q5_K, Q4_K/Q6_K and
Q5_K/Q6_K at 2048 by 512, 19 jobs with 1/4/8 tokens, two repetitions per type
pair. It used the new staging helper and unchanged, prebuilt CPU libraries from
the recorded 13.3 comparison build. This is not CUDA or real-model qualification.

After source review, build a fresh source-bound engine, run the registered
`q36_bounded_cpu_parity_test` against its CPU libraries, and run CUDA
transfer/event lifetime checks and native kernel/cache regressions. Then
use the owned-run harness for startup → generation → cancellation/stop → restart,
with frozen explicit context, prefill, slots, KV types, MTP, router and inputs.
Compare against the same configuration without this mode. Record physical RAM,
commit, process working set/private bytes, VRAM and both drive floors.
Capacity and actual consumed input length must remain separate. Speed, quality
and full-window support require their own measurements.
