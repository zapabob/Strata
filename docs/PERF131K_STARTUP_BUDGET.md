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
| Executable | Current `strata.exe` SHA256 `6f3374e3a6438023aad5b7a8dad9020a9c4383f90b3a31e3402bbfcf271d15b3`, 80,759,296 bytes; `strata_kq.dll` SHA256 `919db9448abedaeac4bdf963160b09c47ad55cca28ca6d1ebec2024c92ae94f2`. Both are in `H:\Strata\build\p01-startup-cuda-20261026\Release`. | Read-only `--help` returned exit 0 after the last link; model launch not run. |
| Model/pack | SHA256 and sizes of both GGUF shards, native pack and MTP dense/expert files are in `H:\Strata\evidence\p01-full-build-20261026\artifact-sha256.json`; tokenizer and profile hashes are in `small-input-sha256.json`. | Content identity recorded; compatibility and runtime provenance not proved. |
| Statistical JSON | `docs/perf131k-statistical-protocol.json` SHA256 `2fc40ea4eda197ddb19627b57c561cb405553684f04dcaeb9a8a067366401884` records design, not measured pairs. | `DESIGN_NOT_RUN`. |

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
untracked host commit is mandatory. Unknown amounts and omitted phases block
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
and an incremental CUDA SM120 link; the full Python server suite passed 354
tests with three skips. None of these results is a native long-context run.
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
