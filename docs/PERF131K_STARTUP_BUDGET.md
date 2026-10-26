# 131072 startup commit ledger

This ledger is for the failed Windows pilot on `93e9c0ac`. It is a source-order
inventory, not a measured allocation breakdown. The previous one-shot launch
failed before READY. Its 10 GiB Job limit was an artificial containment setting,
not a Strata or 131072-token requirement. No cap change is authorized here.

## Current identity boundary

| Item | Current identification | Launch status |
| --- | --- | --- |
| Source | Base HEAD `93e9c0ac9f8145209a480d704eb8104bd49395db`; startup fix `dd0b797a`, benchmark executor `fe7f5159`, opt-in exact boundary `00c1b770`, and mode guard `6955c759`. Current `expert_source.cpp` Git blob is `d0f331379eb8e00e9e1446543773da6610c8406a`. | Linked to the CUDA build receipts below; no same-source CI or model run. |
| Build objects | Fresh `Release/x64` SM120 CUDA build in `H:\Strata\build\p01-startup-cuda-20261026`, then incremental rebuilds after the complement and boundary changes. The last `strata` link exited 0. Startup source/build hashes are in `H:\Strata\evidence\p01-full-build-20261026\build-provenance-after-complement.json`; current boundary source, executable and build log are bound in `H:\Strata\evidence\p01-boundary-20261026\p02-cpu-receipt-after-review.json`. | Link passed; no GPU model execution. |
| Executable | Current `strata.exe` SHA256 `20373ca6b9b16b9d220820a902b584d604a64e068d383a26ba11dd4e43f85d93`, 80,752,128 bytes, built with joined prefetch and affinity guard at `56c4613b`; `strata_kq.dll` SHA256 `919db9448abedaeac4bdf963160b09c47ad55cca28ca6d1ebec2024c92ae94f2`. Both are in `H:\Strata\build\p01-startup-cuda-20261026\Release`. | CUDA link and read-only `--help` returned exit 0; model launch not run. |
| Model/pack | SHA256 and sizes of both GGUF shards, native pack and MTP dense/expert files are in `H:\Strata\evidence\p01-full-build-20261026\artifact-sha256.json`; tokenizer and profile hashes are in `small-input-sha256.json`. | Content identity recorded; compatibility and runtime provenance not proved. |
| Statistical JSON | `docs/perf131k-statistical-protocol.json` SHA256 `7322c8fba38297cdfecfa278d69c2e5fb92691dcf10733c9991c48b63fb898ff` records design, not measured pairs. | `DESIGN_NOT_RUN`. |

These are separate identities. The previous pilot executable is not the fresh
candidate. The Windows CUDA host translation units for `expert_source.cpp`,
`expert_cache.cpp` and `generate.cpp` also have CPU compilation receipts under
`H:\Strata\evidence\p01-startup-cpu-20261026`. The original sparse-checkout
view omitted `spin8/` and `tqcodec/`. Both directories are tracked in
`93e9c0ac` and have now been expanded in this H: worktree. The fresh full
build passed, but backend runtime qualification remains open.

| Phase | Source order and possible live host allocations | Job charge proved here |
| --- | --- | --- |
| Source open | The file source and model setup precede cache allocation. Stage buffers and direct-I/O scratch can be retained by their owners. | Unknown |
| Cache attempts | `generate.cpp` opens the expert cache and may retry a smaller device cache (`6440–6502`). Device request bytes are not entered as Job commit without measured attribution. | Unknown |
| Profile fill | `generate.cpp` can synchronously prefetch a batch, start the next batch asynchronously, then acquire a blob for a slot (`6530–6582`). A staged buffer returned for reuse and each worker's thread-local scratch may still hold commit. | Unknown |
| Resident complement | `pin_cache_complement` begins later (`8299–8300`). The configured 4 GiB budget cannot be charged to the earlier profile failure. Its actual overlap with retained startup memory remains unmeasured. | Unknown |
| READY | Reached only after successful startup and a completed readiness record. The failed pilot never reached it. | Not observed |

`tools/perf131k/startup_budget.py` accepts an ordered host-commit event ledger.
Every acquire needs a byte count and its evidence basis. Only actual uncommit
releases a charge; pool return does not. A positive documented bound for
untracked host commit is mandatory. A release event also requires
`kind: actual_uncommit`, `outcome: confirmed_success` and a nonempty `basis`
identifying the successful release evidence. Unknown, failed or unsupported
release claims block the calculation instead of reducing the estimate. Heap
object destruction alone does not establish allocator uncommit.
Unknown amounts and omitted phases block
the calculation. The estimated peak is computed independently of any Job cap;
an optional declared cap gives a separate comparison for that experimental
condition. `ESTIMATE_ONLY` always has `launch_authorized=false` and
`product_fit_claim=false`. It cannot prove actual Windows Job accounting,
physical RAM, WDDM usage or model compatibility.

No complete event manifest exists for the failed pilot. Before another launch,
record allocation owners, phase transitions, retained capacity, Job/process
accounting and the evidence behind any untracked reserve. Preserve requested,
attempted and successful device-cache slots as different fields. If a safe
upper bound cannot be established, the launch remains blocked. A cap change
would be a separately approved and recorded diagnostic series, never an
automatic response to an over-cap estimate.

## Offline admission on 26 October 2026

The earlier diagnostic run recorded in
`H:\Strata\evidence\p01-diagnostic-pilot-20261026\authorized-new-exe-attempt\closeout.json`
observed 10,784,382,976 bytes of peak Job commit under a 10 GiB cap and
stopped before READY. Its log reports repeated failure at the sixth 0.5 GiB
VMM segment, then a smaller 2,228-slot cache and a blob failure at profile
pair 18. Those observations give a lower bound for that older executable,
not the current executable's required peak or proof that a particular higher
cap will succeed.

The startup fix passed 43 targeted CPU tests and a full CUDA SM120 link. The
later boundary change passed two focused API tests, its compiled CPU contract
and an incremental CUDA SM120 link; the full Python server suite ran 354
tests, with 351 passed and three skipped. None of these results is a native
long-context run.
At `2026-10-26T10:58:38Z`, `GlobalMemoryStatusEx` reported 11,172,454,400
bytes of available physical RAM and 20,138,393,600 bytes of commit headroom.
The older controller's admission rule for a 10 GiB Job required at least
12 GiB of available physical RAM; this snapshot did not pass that rule.
Available memory changed substantially between nearby samples, so this is
only a timestamped observation. The record is
`H:\Strata\evidence\p01-full-build-20261026\offline-admission-20261026T105838Z.json`.

A second read-only snapshot at `2026-10-26T11:34:31Z` bound the earlier
`0894022c` executable to 8,771,563,520 bytes of available physical RAM and
14,825,586,688 bytes of system commit headroom. It also failed the older
10 GiB controller's 12 GiB available-RAM rule. This observation is in
`H:\Strata\evidence\p01-cpu-native-20261026\offline-admission-20261026T113431Z.json`.
The same evidence directory records Windows Spin8 6/6, tqcodec 10/10 and
targeted startup/statistics CPU 43/43. GitHub Actions returned HTTP 422 on
manual dispatch despite reporting the workflow active and repository Actions
enabled, so no same-source cloud CI result exists.

A read-only snapshot at `2026-10-26T11:56:57Z` bound the boundary candidate
`6f3374e3` to 9,090,052,096 available physical bytes and 14,417,989,632
bytes of system commit headroom. This also failed the older controller's
12 GiB available-RAM condition. Its receipt is
`H:\Strata\evidence\p01-boundary-20261026\offline-admission-final.json`.
There is still no complete source-grounded startup upper bound, and this
candidate has not launched a model.

The stage-buffer pool can retain buffers after logical reuse, the direct-I/O
scratch remains allocated in its thread, and Windows may charge device
allocations to Job commit. The source and CPU fixtures do not give a complete
upper bound for their overlap with model weights, session state, cache
retries, later resident complement and worker allocations. The offline
admission result is `BLOCKED_INCOMPLETE`; no new model launch or cap change
was made.

`claim_stage` retains each allocated stage buffer until an explicit pool clear and
allocates `stage_blob_ = max(layer_blob_bytes)` bytes per buffer. The number of
model expert keys is not a safe pool bound: a failed fill removes its key but
keeps the allocated buffer, and the 256-use age rule can delay reuse. The log
at 512 buffers is a notification, not an allocation cap. A source-grounded
upper bound needs the number of claims that can overlap with busy slots and
failed fills for the selected startup path. The current CPU fixtures do not
establish that count.

The extracted production `claim_stage`, `fill_stage`, `publish_stage` and blob
deleter CPU fixture now checks
1,024 failed fills of the same key: it retains 256 buffers with an unchanged
epoch. A separate case holds 600 valid keys busy, observes 600 buffers, then
checks that reuse retains that capacity and fixture owner destruction frees the
blobs. This does not exercise production source destruction, worker joining,
event cleanup or device synchronization. Successful `end_startup_unbuffered`
handover is another production path that clears the pool before destruction. Both
pageable and fake-pinned cases passed within the seven-test startup lifetime
suite. Buffers were 16 bytes each and allocation/I/O APIs were fakes; these
results establish retention behavior in those schedules, not the model's peak
or a universal pool bound. Generated source, compiler command and case output
are under `H:\Strata\evidence\p01-boundary-20261026\011c0494d87e4e23806d521de6354453`.

For an initially empty pool, serialized claims and a sequence counter that does
not wrap, the selection rule gives a conditional owned-blob count bound of
`256 + B`, where `B` is the maximum busy-slot count over the pool's entire
lifetime. It includes queued/preclaimed slots and cannot be replaced by the
current busy count or worker count. This excludes vector capacity (which can
double), map/event storage, allocator overhead and all other host allocations.
The selected startup path's lifetime `B` still needs a source-grounded bound.

For the primary profile-fill branch only (`!per_layer`, `srcp == &src`, and
unbuffered), the first 64-pair batch finishes before the next asynchronous
batch starts. Every later batch boundary calls `ahead.get()` before starting
another. At most 64 preclaimed slots overlap with one foreground demand, so
this branch has `B <= 65`; this is not yet a bound for every pre-READY caller.
The selected native index has 48 layers with 1,382,400-byte blobs throughout
(SHA256 `015e53d3ae36324f172be4942bcf129539b343e2eb4fcd4f25ca5eff180bfa41`).
The conditional stage payload bound for this branch is 443,750,400 bytes.

`startup_budget.py` provides checked arithmetic helpers for these conditional
payload bounds. For `n` fills with `r` role windows each, the direct-read span
is bounded by `n * blob + n * r * 8192 + (n * r - 1) * 1048576`, rounded up
to 1 MiB. This includes sector padding and merge gaps. The per-thread buffer
capacity bounds are 37/69 MiB for 16 fills with one/three roles, and 74/138 MiB
for 32 fills. The later resident-complement copy uses up to 32 fills per call,
so a 16-fill bound cannot be used for the whole startup. Thread counts, vector
capacity, stacks, events and allocator/driver charges require separate entries.
The model-index identity and arithmetic are recorded in
`H:\Strata\evidence\p01-boundary-20261026\conditional-staging-bounds.json`;
this record does not authorize a launch.

Active reader count is not a retained-scratch count. The local MSVC 14.44
`include/future` implements `std::async` using `Concurrency::create_task` and
waits for task completion. The asynchronous profile batch can therefore run on
a persistent task-pool worker whose `read_direct` thread-local storage outlives
the batch. The active primary profile readers are at most five (main, async
caller and three child workers), but `5 * per-thread capacity` is not a proved
retained-memory bound. This implementation-dependent lifetime must be resolved
before using that multiplication in admission.
For `want > 0`, at most `A = ceil(want / 64) - 1` asynchronous profile tasks
are issued. A conservative retained scratch bound for that profile branch is
`(A + 4) * C16`: main, up to `A` surviving async callers and three currently
active explicit children. For the later complement copy, a conservative bound
is `A * C16 + 6 * C32`, including retained async callers and up to six
complement workers with main participating. `C16`/`C32` denote the per-thread
capacity bounds above. These are source bounds for the stated paths, not
observations of thread-pool growth or a whole-process commit estimate.

## Joined profile prefetch candidate

Commit `73cfa347` replaces the primary profile's `std::async` with an owned
thread that joins at each batch boundary and on early exit. The batch callable
outlives its owner. Allocation/thread-start failure runs the batch synchronously;
task exceptions are saved and rethrown once by `get()`. The CPU test uses real
MSVC threads and checks TLS destruction after each of 128 batches, early exit,
exception propagation and injected launch failures. It passed, as did the CUDA
SM120 incremental link and read-only help. Astra xhigh found no actionable code
defect; its review did not independently execute these tests.

For this candidate, persistent async task-pool callers are removed from the
selected profile schedule. The profile scratch bound becomes `5 * C16`, and
the subsequent complement bound becomes `6 * C32`, with main included. Main
can retain its own high-water scratch through READY. The `B <= 65` stage bound
is unchanged. These payload bounds still exclude metadata, stack, runtime,
weights, sessions, device/driver commit and the complete phase overlap.
The artifact receipt is
`H:\Strata\evidence\p01-boundary-20261026\joined-prefetch-receipt.json`.
HIP/SYCL builds and real model execution remain unperformed.
The joined-thread test is now part of
`python -m unittest tests.perf131k.test_startup_lifetime` under the existing
local CPU receipt gate. All eight tests passed; generated source, compile
commands and case outputs are under
`H:\Strata\evidence\p01-boundary-20261026\79e6f3c53f5d48f19423509e7770244d`.
The source integration check also rejects reintroducing `std::async` into this
profile block or declaring the referenced callable after its thread owner.

## Additional host owners under audit

The local shard header reports `token_embd.weight` as Q3_K, 635,699,200
elements and 273,152,000 payload bytes. `NativeEmbed::load` copies this payload
into mapped/portable `cudaHostAlloc` storage when pinning succeeds; its fallback
uses device storage instead. File-mapping size and this committed copy are
separate quantities. This header inspection did not load the model on a GPU.

The selected MTP pack has a 116,099,072-byte `dense.bin`. With no `--mtp-q4`,
`MtpDrafter::load` reads it into a host vector and uploads it, then later uses
a separate 64 MiB vector for chunked expert uploads. Their C++ scopes do not
overlap, but the allocator may retain commit after vector destruction. Without
uncommit evidence the ledger cannot subtract either charge. Device dense and
expert allocations require separate Windows/driver accounting. The selected
default `kv-resident=0` makes `kv_plan` return mode 0 before considering the
MTP ring window, so neither main nor MTP has a full-context host K/V copy on
this path. Mapped step/position staging, prefill staging and the resident arena
remain separate owners; none is covered by the profile-stage payload bound.

The remaining source audit identified these additional logical requests for
the selected flags. They are not interchangeable with measured Job commit.

| Owner | Known payload request | Lifetime/accounting limit |
| --- | --- | --- |
| WeightTable upload staging | 8 MiB input + 16 MiB output | Temporary pinned storage; release outcome needs evidence. |
| Direct PLE cache and read slab | 100,794,368 bytes | IQ4_NL 90-byte rows: 1,048,576 cache rows, eight ways, plus 256 two-page read slots. Persistent; queue/statistics/container overhead excluded. |
| Initial unshared RoPE construction | 33,554,432 bytes | Temporary host table at capacity 131072 and rotation width 64. |
| Prefill listed host requests | At most 348,070,164 bytes | `R * 1,382,400 + 20,888 * T + 8,468`, defaults `R <= 128`, `T <= 8192`; failed initialization retries and allocator retention need separate accounting. |
| SessionLoopScratch / Doorbell | 102,400 / 10,328 bytes | Mapped host storage; other verifier buffers remain separate. |

Each QSA state also requests 116 pinned host bytes. MTP's ordinary mapped
input/output staging requests 1,328 bytes plus its QSA staging; its default
identity-table temporary requests 524,288 bytes. ExpertCache has residency,
cursor, offset and segmented-cache metadata; retained capacities and retry
overlap must be recorded, rather than charging only container size.

The PE stack reserve is 1,048,576 bytes with 4,096 bytes initially committed.
Reserve is not already committed, and later stack growth and driver/runtime
threads are unknown. The audit therefore does not justify a complete total.
`partial-host-payloads.json` in the local evidence directory binds the partial
inventory to source hashes. `resource-overrides-snapshot.json` records only
allowlisted resource overrides in the tool process; it is not a frozen future
launch environment. The older pilot explicitly set `STRATA_RESIDENT_PIN=0`.

A new read-only resource check reported 8,082,767,872 available physical bytes,
23,051,309,056 bytes of commit headroom and 131,753,775,104 free H: bytes.
Available RAM still fails the older 12 GiB admission condition. No new model
launch, diagnostic authorization, cap change or service action followed.

On Windows, `read_direct` retains its `VirtualAlloc` scratch in thread-local
storage. Its capacity rounds each batch's merged read span up to 1 MiB. The
profile path can overlap a foreground batch with an asynchronous next batch,
and `fill_many` can create up to four workers per batch. A Job estimate must
count the high-water scratch of every such live thread until that thread exits,
including fallback single-blob reads. The Linux-only prefetch worker vector
scratch is a separate path and must not be charged to this Windows candidate.
