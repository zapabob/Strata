# Current boundary candidate — 26 October 2026

Source commit `00c1b770` adds opt-in `--exact-context-boundary` to the native
engine. The Python server uses zero slack only when its configured native args
include that flag. For a strict capacity check, also set `fit_max_tokens` to
`false`; otherwise the usual API behavior may shorten an oversized reservation.
The default still keeps eight spare context cells. This opt-in mode requires
single-request serial serving: `--batch` and `--pipeline-windows` must be off.

Commit `6955c759` rejects pipeline and batch modes for this option after
independent static review found that their final-cell paths were not covered.
The CPU contract accepts 130048 input tokens with a separate 1024-token output
reservation and 131071 input tokens with one output token, and rejects each
one-over request. The API mock passed two focused tests; the native boundary
helper compiled and exited 0; the Windows CUDA SM120 executable linked and
its read-only `--help` exited 0. That historical boundary executable is 80,759,296 bytes,
SHA256 `6f3374e3a6438023aad5b7a8dad9020a9c4383f90b3a31e3402bbfcf271d15b3`.
The receipt is `H:\Strata\evidence\p01-boundary-20261026\p02-cpu-receipt-after-review.json`.
No full-context native request or model startup ran on this build. P02 device
behavior and 131072-token qualification remain unverified.

The current executable includes joined profile prefetch and the foreground
affinity guard at engine source `56c4613b`. It is 80,752,128 bytes, SHA256
`20373ca6b9b16b9d220820a902b584d604a64e068d383a26ba11dd4e43f85d93`.
The CUDA link and read-only help passed; the later one-shot model startup
failed before READY under the 10 GiB Job condition. Native boundary execution
and completed inference remain NOT_RUN. Its build receipt is
`H:\Strata\evidence\p01-boundary-20261026\joined-prefetch-receipt.json`.
The combined CPU gate ran 88 tests with two Windows symlink subcases skipped;
the later overlay dependency gate passed 11 tests. These do not establish
hardware correctness or qualification.

## Earlier diagnostic candidate and pilot

The earlier diagnostic candidate had SHA256
`a8ec8e3d4ed948fafcc5c20e829b0d6b49f4f8482d30e279a1d0314e5e1004dd`
and was80,742,400 bytes. It is separate from the published .1 preview and is not
installed. Blob diagnostics passed8 CPU tests plus18 selected regression tests;
4 mutations were detected. Actual expert_source/generate host compilation, engine
archive and final link passed with independent read-only acceptance. No new device
compile or GPU execution is implied. Reused-object/source provenance is UNRESOLVED.

The authorized single diagnostic ran with4K input,capacity131072,spec4+MTP,
k8v4,reserve256,traceOFF,CPU memory and blob diagnostics ON. Consumer admission
met the RAM12GiB/commit16GiB/H8GiB gates. Controller-observed elapsed was41.61s,
including monitoring and cleanup; startup ended before READY. The controller reported COMMIT_BUDGET_EXCEEDED/125 and native exit1 was observed before
cleanup. Job peak10,740,895,744B exceeded the10,737,418,240B limit. All Job processes
terminated. The one-shot approval is consumed; no retry or cap increase occurred.

The snapshot retained32 new(nothrow) allocation failures requesting1,382,400B each;
99 additional records were dropped. These failed requests are not allocated bytes
or disk traffic. Worker context is unknown; terminal file-source blob-null at
layer46/expert185 remains cause=unknown. Retained heap failures are not proven to
belong to that terminal pair. cuMemCreate error2 attempts recovered via smaller
cache before this terminal failure. Independent review accepted the corrected
evidence scope, not inference or131k qualification.
The wrapper pins the full launch binding,controller sources/import origins and
binary; default startup does not invoke this operator-specific helper.

The [reviewed statistical protocol](perf131k-statistical-protocol.json) has a
schema 2 offline executor checked by 16 synthetic tests. It binds the analyzer
source hash, reports five fixed grouped evaluation summaries and keeps paired
task families together, avoiding treatment of
folds or technical repetitions as independent observations, and separates initial
4K/32K measurements from full qualification. Full boundaries wait for P02;64K,
126k-history/512 actual steps,reference PPL/KL and32turn/2h stability remain separate
gates. No measured p-value, confidence interval or performance improvement is
reported. Fitting/tuning and final held-out execution remain NOT_RUN.

Actions permissions currently report enabled. Latest-candidate CI is still pending;
permission status does not prove the earlier HTTP422 dispatch failure is fixed.
P00/P01 remain PARTIAL. Earlier-candidate GPU startup RAN_FAILED_BEFORE_READY;
current-candidate startup also failed before READY. Completed inference,
performance and quality remain NOT_RUN; full131k is NOT_QUALIFIED.

## Current executable: authorized 10 GiB diagnostic

After the user manually stopped Hikari, admission observed 20,132,864,000
available RAM bytes and 47,326,261,248 bytes of commit headroom. The current
`20373ca6` executable launched once. Controller elapsed was 13.14 seconds,
status COMMIT_BUDGET_EXCEEDED/125, native exit 1. Peak Job commit was
10,788,929,536 bytes against 10,737,418,240 configured. Cleanup confirmed
termination and active 0; no retry or cap increase followed.

Cache attempts requested 5283, 3962 and 2971 slots before successfully opening
2228 slots (2.87 GiB reported). Profile pair 15 then failed blob acquisition at
layer 3, expert 474, cause unknown. Controller memory diagnostics were enabled;
`STRATA_PERF131K_BLOB_DIAG` was omitted, so no source failure-ring evidence binds
an allocation failure to that terminal pair. The diagnostic is not a performance
sample. Hikari remained in the user's stopped baseline; the wrapper made no
service or maintenance-state changes. Evidence:
`H:\Strata\evidence\p01-boundary-20261026\authorized-direct-attempt\closeout.json`.

---

## Historical published-preview records

The following records describe earlier checkpoints and binaries. Their present-tense
wording is historical and does not override the current-candidate status above.

# Experimental 131k measurement tooling

This checkpoint adds measurement infrastructure. It does not establish that a
131072-token context meets performance, quality or stability targets.

The native host trace is disabled unless `STRATA_PERF131K_HOST_TRACE` names an
output file. The disabled path does not create CUDA events, initialize CUDA, add
synchronization, create a worker or periodically write output. Enabled tracing
retains at most4096 spans and reports losses and unfinished spans. The analyzer
rejects malformed identities and distinguishes incomplete captures. Host interval
unions are not GPU critical paths; unsupported GPU, physical disk and event
counters remain unknown.

The Python server's optional `--perf131k-e2e-config` observer connects actual
prepare, native protocol, Service completion and HTTP write paths. Its bounded
request aggregates distinguish native tokens, synthetic tokens, termination
reasons and write completion. Server write completion does not establish client
arrival. External binding hashes are recorded without claiming independent
verification. The normal server path remains disabled by default.

## Local pilot tools

`tools/perf131k/pilot.py` validates an explicit local launch proposal and can run
only fixed CPU fixtures. It does not launch a real model. Its Windows Job helper
uses atomic Job assignment and suspended creation, verifies membership before
resume, bounds commit, process count, time and captured output, and drains only
the Job it created. Missing telemetry and unconfirmed cleanup are failures.
Observed commit peaks above the configured budget remain failures rather than
being rounded away. These controls do not guarantee a strict physical RAM peak.

`native_pilot.py` is an operator-specific experimental native-protocol pilot.
It requires its frozen verification binary, tokenizer, launch binding and explicit
execution flag. It preserves capacity131072, spec4 with MTP, k8v4 and256 output
reservation, separating first and repeated requests and trace OFF/ON cells.
Native counters, HTTP delivery and full-context quality acceptance are separate.
Missing or incomplete ON traces invalidate the comparison. Model content hashes
and legacy build provenance remain unresolved where not independently proved.

`service_pilot.py` is an experimental, separately authorized local service
transition tool. It is not invoked by normal engine/server startup. Its lifecycle
work is a checkpoint: the actual service pause/restore and subsequent native
pilot have not been executed. A lazy TTS restart may restore configuration and
health without restoring loaded/warm state; synthesis verification is separate.
Do not use this checkpoint as evidence that service restoration is qualified.

The local pilot has been blocked before native process creation by its reviewed
start condition: at least10GiB available RAM,14GiB available commit headroom and
8GiB free on the evidence volume. These are conservative start gates, not
physical reservations or a measured model footprint. No smaller capacity,
precision change, alternative model or reduced output reservation substitutes
for a failed131072-capacity cell. C-drive cache placement remains a separate
blocked decision.

## Verification scope

The host trace/consumer changes passed bounded CPU tests and limited Windows
host compilation/archive/final-link checks. CUDA compilation, device execution,
normal graph compatibility, trace overhead, model inference, performance and
quality have not been established by this checkpoint. The linked verification
binary contains reused artifacts whose full source provenance is unresolved.

The latest native-controller CPU regression recorded25 passing tests. Deliberate
faults in stdin forwarding, receipt preservation, external input checks and ON
trace validation were detected. These tests use scripted runtime results and are
not model performance evidence. Independent read-only reviews accepted the
bounded CPU/controller scopes; the newest service-transition work is separately
identified above as unexecuted.

Machine inventories, raw receipts, temporary fixtures, executable test products,
runtime environment backups and model data remain outside Git. Portable
trace-accounting tests can collect normally. The machine-bound tests require
local frozen artifacts and explicit opt-in:

```powershell
$env:STRATA_LOCAL_PERF131K_TESTS = '1'
```

Use the resource-gated unittest runners for actual local test execution. Do not
run broad model/build suites merely because CPU fixtures pass, and do not report
mock counters or a READY line as131k acceptance.


## 26 October 2026 native pilot and preview

The measured source/controller checkpoint is `e68f8926b27ad9d9f12475b6c6897a3e48d823de`.
Its Pages, Native preview CPU and Minimal serving runtime workflows all succeeded.
The10 GiB controller change passed38 targeted CPU tests and two valid limited
mutants were detected. An earlier invalid test selector was excluded from mutation
evidence and rerun correctly. Independent review was read-only; Astra Extra High
was requested and the actual backend assignment was not observable.

The native Q2_0 series fixed capacity131072, spec4 + MTP, k8v4, reserve256 and
the prepared4096/32768 token inputs. No smaller capacity was substituted. The
10 GiB attempt started after the approved idle service pause, with available RAM
13,361,651,712 B, commit headroom22,703,177,728 B and H free69,404,393,472 B.
These met the12/16/8 GiB gates. Job peak commit was10,802,049,024 B against
10,737,418,240 B configured. The first4096/OFF cell stopped before READY or DONE;
the remaining three cells were NOT_RUN. Cleanup confirmed Job active0.

The system-wide gate is not a physical reservation and the observed peak is not
the amount required for successful startup or inference. Generic cache errors
collapse CUDA VMM API stages; a profile-fill error can retain a prior error string.
Individual allocation failure attribution remains unknown. Do not infer whole-run
bottleneck fractions or performance from this incomplete startup.

The temporarily paused service was restored with its original argv, environment,
images and model configuration, with health normal. Its previously loaded model
was not warmed again; minimum synthesis verification was NOT_RUN. Health alone
is not proof of functional/warm restoration.

P00/P01 remain PARTIAL. Inference, throughput, GPU elapsed time, physical Disk I/O,
P17/PPL, full-length quality and131k acceptance remain NOT_RUN / NOT_QUALIFIED.
The old binary/reused-object provenance remains UNRESOLVED. The preview native
exe is the previously limited host compile/link artifact, not a fresh complete
CUDA rebuild. The GUI and global Control VERSION/COMMIT are not part of this
partial overlay.

[Machine-readable status](perf131k-status.json) ·
[Preview release](https://github.com/zapabob/Strata/releases/tag/v0.3.2-preview.20261026.1)

The package retains the unchanged legacy image-reader executable to preserve GUI
discovery. Its source provenance remains UNRESOLVED and image inference is NOT_RUN.

The measured controller checkpoint e68f8926 has all three workflows/four checks
successful. Subsequent docs/installer source CI is BLOCKED: GitHub rejected
workflow dispatch with HTTP422 while repository Actions permissions were enabled
and workflow states were active. No check-run was created. Local installer CPU
tests and independent review are separate evidence; no cloud CI pass is claimed
for that newer source. Repository/billing safeguards were not bypassed.
