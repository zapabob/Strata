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
