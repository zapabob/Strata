# GPT Pro consultation: 131072-capacity startup under a Windows Job limit

Read-only technical consultation. Use the exact Git commit supplied with this request.
Do not execute a model, change files, contact services or treat this as qualification.
The implementation owner remains Codex. Please separate facts, hypotheses and proposed tests.

## Goal and invariant configuration

Windows,32GiB system RAM,RTX5060Ti16GiB,CUDA13.3/SM120. Preserve the current
Q2_0 model/pack/tokenizer,capacity131072,spec4+MTP,k8v4,Attention view count and
256-token output reservation. Do not suggest reducing context/precision, changing
models, disabling MTP silently, cloud inference, firmware/register/driver changes,
pagefile enlargement or an automatic Job-cap increase.

Spin(8),Triality,Query-v3,TurboQuant and Bonsai must remain intact. The normal
path keeps optional tracing/diagnostics OFF. Startup diagnostics may record known
failures, but cannot change I/O order,all-issued OVERLAPPED drain or fallback.

## Evidence from the one-shot diagnostic

The candidate executable was compiled from the reviewed dirty source on base
`4de7d9646dba63a8b03acb0db8dec46b42223c7c`. Actual product expert_source.cpp and
generate.cpp host compiles,engine archive and final link passed. Existing device
objects were reused; their complete source correspondence remains UNRESOLVED.
Candidate SHA256:
`a8ec8e3d4ed948fafcc5c20e829b0d6b49f4f8482d30e279a1d0314e5e1004dd`.
Selected installed baseline SHA256:
`4281dd8b886f4863fd85e71e35c4fe64c084c4cdb9ce1cd1029c5dbbed958610`.

One real root launch used4K input/capacity131072/spec4+MTP/k8v4/reserve256,
traceOFF,CPU-memory and blob diagnostics ON. Job cap was10GiB,timeout900s,
raw-output cap16MiB. Consumer admission met RAM12GiB/commit-headroom16GiB/
evidence-volume8GiB. No service stop,model move or automatic retry occurred.

| Observation | Value |
| --- | --- |
| Controller-observed elapsed,including monitoring and cleanup | 41.609 seconds |
| Controller result | COMMIT_BUDGET_EXCEEDED /125 |
| Native exit | 1, observed before cleanup |
| Job commit limit | 10,737,418,240 bytes |
| Observed Job peak commit | 10,740,895,744 bytes |
| Actual root launches / Job lifetime process count | 1 /2 |
| READY / DONE / completed requests | 0 /0 /0 |
| Termination / active after | confirmed /0 |
| Owned-root CPU memory samples / failed samples | 1443 /0 |
| Sampled maximum root private / working set | 10,735,017,984 /2,382,999,552 bytes |
| Sampled minimum system available RAM / commit headroom | 11,046,375,424 /17,025,765,376 bytes |

These extrema have different scopes and sampling times. Do not add/subtract them
to infer memory ownership,required capacity or the exact failure-time state. The
3,477,504-byte peak overshoot is not proof that a tiny cap increase would fit.

The raw CUDA trace reported cuMemCreate CUresult2 for a536,870,912-byte segment
at segment6. The engine retried cache sizes5283/3962/2971/2228 slots,then reported
a2228-slot/2.87GiB cache after three smaller tries. It subsequently failed profile
fill at pair1,layer46/expert185 with blob acquisition cause=unknown. Thus the VMM
failures recovered before the terminal blob acquisition failure; a shared immediate
cause has not been established.

The bounded BLOB_DIAG snapshot reported131 seen events,32 retained records,
0 pending and99 dropped. All retained records are new_nothrow failures requesting
1,382,400 bytes,with worker context source=unknown and request/layer/expert=null.
The terminal is file-source profile_blob_null,request2,layer46/expert185,
requested_bytes1382400. The retained allocations cannot be directly attributed to
that terminal pair; other dropped branches cannot be ruled out. Failed requested
bytes are not successfully allocated memory or physical I/O. Do not infer bottleneck
fractions from this incomplete startup.

Independent read-only reviews accepted CPU diagnostics,limited host build,launch
preparation and corrected evidence scope. They did not qualify inference or GPU
performance. The reviewers requested Astra Extra High; backend assignment was not
observable. Inference/performance/quality/paired statistics remain NOT_RUN.

## Code to inspect first

- `src/core/expert_source.cpp`: detail memory budgets,claim_stage,staged_blob,
  read_direct,resident/complement allocation and unbuffered startup paths.
- `src/core/expert_cache.cpp`: segmented VMM allocation,cleanup and cache retries.
- `src/program/generate.cpp`: pre-profile allocations,read-ahead/profile fill and
  later resident-tier allocation; preserve the actual ordering in your analysis.
- `include/strata/perf131k/blob_failure.hpp`: fixed32 slots,terminal snapshot,
  unknown worker context and dropped records.
- `tools/perf131k/windows_job.py`: Job limit/peak classification,native exit
  preservation,owned-process lifetime and resource sampling.
- `tools/perf131k/native_pilot.py`: binding,normal-series arguments,first/repeated
  requests,resource gates and the distinction between engine timing and client time.

No full model-file hash has been completed. Do not silently treat path/size checks
or an exact executable hash as proof of model or reused-object source provenance.

## Requested assessment

1. Rank falsifiable explanations for simultaneous near-cap Job accounting,
   recovered cuMemCreate failures and host new(nothrow) failures. Distinguish Job
   commit,system commit,physical RAM and VRAM. Identify what source/data would
   distinguish each explanation and what cannot be inferred from these receipts.
2. Audit VMM retry cleanup and startup staging allocation/lifetime. Identify a
   minimum model-neutral CPU-only investigation or implementation that can be
   tested with a fake budget/allocator/I/O before another expensive trial. Do not
   assume the later4GiB resident tier was already allocated at the earlier failure.
3. Propose bounded memory planning that preserves all model/context/numeric
   semantics and safe asynchronous I/O. Any effective cache-budget/profile change
   must be explicit and measured as a separate configuration,not hidden behind
   identical argv. Do not promise an unmeasured performance improvement.
4. If additional diagnostics are needed,retain bounded output and reserve useful
   terminal-local metadata without growing buffers indefinitely. Worker failures
   must not be presented as causal for an unrelated foreground request.
5. Review the grouped held-out/paired statistical design in
   `docs/perf131k-statistical-protocol.json`. Fixed binaries are not retrained;
   folds/repetitions are not independent samples. No p-value or equivalence claim
   is valid without real valid pairs,frozen task/fold mapping and an appropriate
   same-weights quality reference. Full qualification also needs P02 capacity
   contracts,64K/full boundaries,126K history with512+ actual steps and32turn/2h.

Return source references,ranked hypotheses,minimum change/test plan,resource and
approval requirements,and explicit NOT_RUN/BLOCKED items. No execution is requested.

## Follow-on product request

After this consultation,integrate hakua_memory plus SOUL.md/USER.md loading into
Strata itself as part of its AI-agent harness. Preserve existing conversation,
tool execution,cancellation/auth and inference paths. Treat memory recall/storage
and persona/user context as bounded,permissioned harness operations with explicit
token accounting inside total capacity131072. Do not edit/publish personal files,
copy private memory contents or treat retrieved text as higher-priority authority.
The integration has not been implemented by this checkpoint.
