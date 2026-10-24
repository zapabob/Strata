# Windows bounded validation guard — Task 2

Date: 24 October 2026. Base: `d8574e858c7db777861783de3059bf43a6846c52`. Working branch: `codex/strata-030-completion`. Scope is the validation runner and its tests; production serving, models and engine sources are unchanged by this task.

## Requirements and implementation

The previous PowerShell runner called `Process.Kill(true)`, which is not available in the installed Windows PowerShell 5.1 framework. It also used a small disk threshold, did not reserve space for objects outside the log directory, and could lose the exact exit status of a fast child. Task 2 requires owned-process termination, exact exit codes, explicit capacity/output budgets, safe arguments and paths, and preservation of old evidence.

`tools/verify_codec_dialects_build.ps1` now loads the dependency-free `tools/verify_bounded_process.cs` with `Add-Type`. The helper creates a private, unnamed, non-inheritable Job Object with kill-on-close and no breakaway permission. A suspended child is assigned to that job atomically by `PROC_THREAD_ATTRIBUTE_JOB_LIST` during `CreateProcessW`. The helper checks membership before resuming its initial thread. This also removes the host-death interval that would exist between a separate create-suspended call and a later assignment. There is no uncontained fallback. Windows 10 or later is required by this attribute. The default job behaviour includes normal descendants created by the child.

Only the three explicit standard-I/O handles are inherited. Stdin is NUL; stdout and stderr use small pipes drained by the supervisor. Process, thread, job, pipe and directory handles are retained through cleanup. A leader exit, resource violation or timeout terminates any remaining members of that exact job and checks its active-process count. The actual 32-bit child exit code is read from the retained process handle only after it is signalled, independently of the guard failure. Values 259 and 4294967295 are covered as legitimate exit codes. No later PID lookup, name-based kill, broad process scan or production process termination is used.

`ReserveBytes` defaults to, and cannot be below, 10 GiB. `ExpectedAdditionalPeakBytes` is separately checked against actual bytes available on H: before launch. It must cover the whole operation, including build objects outside the evidence directory. `MaxOutputBytes` defaults to 96 MiB and applies to the entire evidence root including older files. An explicit larger cap also needs an adequate peak allowance. The runner checks live H: free bytes while the child runs. The timeout defaults to 1800 seconds and is explicit for longer work.

Stdout and stderr have a combined byte cap. Other files are sampled at a 20 ms polling interval; this is a stop threshold, not a filesystem quota, and a write can finish between samples. Initial and final structured receipts add small metadata overhead. The receipt's `output_bytes` is measured before final receipt serialization. Partial output is retained. Guard failures exit 125 and retain `guard_reason`; the child status remains separately visible. Abrupt host termination leaves the initial `state=starting` receipt, which is incomplete evidence rather than a claimed successful result.

Paths remain confined to `H:/Strata/build/task5a-*`. Traversal, reserved labels, invalid Windows path components and existing reparse points are rejected. The evidence directory and ancestors remain open without delete sharing, preventing replacement by rename while in use. Existing labelled outputs or receipts cause refusal. `CreateNew` prevents replacing an existing receipt even across competing starts. Windows CRT argument quoting preserves empty arguments, embedded quotes, Unicode, spaces and trailing backslashes. Absolute executable paths and filesystem paths are resolved literally, including brackets.

## Integration budget distinction

For a native build whose objects remain in `H:/Strata/build/native-spin8`, keep a new `task5a-*` evidence root for its labelled stdout, stderr and receipt. Pass the normal `cmake.exe` build arguments pointing at the existing build directory. Set `ExpectedAdditionalPeakBytes` to the estimated additional peak for objects in `native-spin8`, temporary files and logs together. Set `MaxOutputBytes` to the evidence-root allowance. The existing native build directory is not an allowed evidence root and is not recursively scanned by this guard. Its disk consumption is covered by the initial peak/reserve check and continuous actual-volume reserve check. This task does not authorize or perform that native build.

## Verification and TDD

The focused suite is `tools/test_verify_codec_dialects_build.py`. All fixtures use the installed interpreter through existing uv, with no dependency changes. The real child fixtures use that same interpreter directly because invoking uv inside a child would add another launch layer to the lifetime test. All are finite and test-owned. The tests create no visible console windows. A separate sentinel process must survive every descendant scenario; its retained handle is used only to close that fixture afterwards.

The RED command was:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
& 'C:/Users/downl/.hermes/bin/uv.exe' run --no-project --offline --python 'C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe' python -B -m pytest tools/test_verify_codec_dialects_build.py -q -k fast_exit_exact_status -x -p no:cacheprovider
```

Before the implementation this failed: `NamedParameterNotFound` for `ExpectedAdditionalPeakBytes`; `1 failed, 14 deselected`. No test child was launched by that rejection. Its fresh evidence directory was `H:/Strata/build/task5a-guard-20261024/run-56e1ff6fcabd4d8cb7ee6827f1132079`.

The final full command was:

```powershell
& 'C:/Users/downl/.hermes/bin/uv.exe' run --no-project --offline --python 'C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe' python -B -m pytest tools/test_verify_codec_dialects_build.py -v -p no:cacheprovider --junitxml=H:/Strata/build/task5a-guard-20261024/final-20261024-02.xml
```

Its console output is retained as `H:/Strata/build/task5a-guard-20261024/final-20261024-02.console.txt`. The XML records each test's dedicated evidence directory, containing the structured receipts and partial logs. The installed Windows PowerShell version in those receipts is `5.1.26100.9711`; the controller environment reports Windows version `10.0.26300.0`. Python is 3.12.10, pytest 8.3.5. These are actual Windows PowerShell tests, not pwsh-only tests.

GREEN result: `26 passed in 123.79s (0:02:03)`, with zero failures, errors or skips. The final evidence suite is `H:/Strata/build/task5a-guard-20261024/suite-e4119eac0d364703b0451d93b4503013`. `final-20261024-02.summary.json` records all receipt outcomes and source hashes. Total retained task evidence at the final measurement was 46,479,954 bytes, below the 134,217,728-byte allowance. The final free-space reading was 28,654,886,912 bytes; the lowest final-suite receipt reading was 28,627,755,008 bytes, above the 10,737,418,240-byte safety floor. The deliberately raised disk-test reserve was 28,640,374,784 bytes; its receipt separately reports `disk_reserve`, actual child exit 125, 18 retained output bytes and zero remaining job processes. The stdout flood captured exactly 262,144 bytes and reported `output_limit`; the separate file-output fixture confirms polling can observe a completed 1 MiB write beyond its smaller threshold, which is the documented non-quota limitation.

The coverage includes normal/nonzero/fast exits, full 32-bit status preservation, no arguments and closed stdin, argv round-trip, literal paths, malformed executables, exclusion of an unrelated inheritable event handle, impossible reserve and peak rejection, real nested-job assignment rejection, old-receipt byte preservation, traversal and junction rejection, early leader exit with a live descendant, stdout limit, file-output limit, timeout, host termination, and an actual post-launch disk-reserve crossing. The disk fixture writes only 8 MiB outside its evidence root after a deliberately raised reserve is selected just below current free space; actual free space remains above 10 GiB. Child termination is checked using an OS handle retained before the event, and normal cleanup also requires the job active-process count to be zero.

The first full run is retained as `final-20261024-01.xml` and `.console.txt`: 25 passed, one failed. That failure was in the test snapshot, which attempted to read the new `keep.temp` directory as a file. The snapshot now compares every regular file recursively. The focused regression then passed. Earlier development checks exposed an unavailable `Get-FileHash` command in the inherited PS5.1 module environment; the runner now hashes its small helper using framework SHA-256 instead. The test host explicitly propagates `$LASTEXITCODE` because `-EncodedCommand` otherwise collapses a called script's nonzero result to 1. The first nested-job fixture used the basic limit structure for a flag requiring extended limits; that fixture was corrected and then passed against the real Windows API.

Black and flake8 are installed and were run through the same uv/interpreter path. `python -B -m black --check tools/test_verify_codec_dialects_build.py` passed; `python -B -m flake8 tools/test_verify_codec_dialects_build.py --max-line-length=100` passed. `git diff --check` passed for the owned script. C# is compiled by the actual PS5.1 `Add-Type` during integration tests. C# 5/.NET Framework compatibility prevents using modern nullable-reference syntax; nullable result values are explicit. There is no new .NET project or package to restore. A separate dotnet formatter/analyzer run was not performed.

The existing uv warnings about no project and dangling package directories remain visible in the saved console output. They were not repaired or hidden.

## Source identities

SHA-256 of the verified working files before Git newline normalization:

| File | SHA-256 |
| --- | --- |
| `tools/verify_codec_dialects_build.ps1` | `DE2EE5053B3852A675E06EF25A3A98C98090A19D8769FC828D7CE083C2E9EAC1` |
| `tools/verify_bounded_process.cs` | `C2B697315E61611653410382F64E4EADDD40E079EA137A3CBA5C9212E02DA3E0` |
| `tools/test_verify_codec_dialects_build.py` | `42608A45B2A25EAA21595D34DBAB55610352A88082C544817F6360B7300A70CA` |

## Standards, review and limitations

The canonical pre-implementation prompt, home and repository instructions, task brief and implementer contract were read. Incompatible identity, environment and tool claims in the canonical prompt defer to the actual system/developer instructions. Selected SOPs were Common Engineering, Implementation Start Gate, Skill Selection, DeepResearch, Security, Application Development, CSharp and Python. Skills applied were milspec-codex-standard, deepresearch-defense-standard, code-review-and-quality and agent-self-review-evolution. No governance files, installed packages, global settings or production services were changed. No formal MILSPEC certification is claimed.

Microsoft primary references checked on 24 October: [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects), [process creation flags](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags), and [process/thread attributes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute). These document job lifetime, suspended/hidden creation, selective handle inheritance and the Windows 10 minimum for the job-list attribute. The helper fails closed if the required APIs or containment fail.

Self-review-event: type=qa_defect scope=tools/verify_codec_dialects_build.ps1 category=qa-coverage evidence=H:/Strata/build/task5a-guard-20261024/final-20261024-01.console.txt

Self-review-event: type=local_fix scope=tools/test_verify_codec_dialects_build.py category=windows-paths evidence=H:/Strata/build/task5a-guard-20261024/final-20261024-02.console.txt

Self-review corrected the create/assign crash gap, ensured disposal of one stream cannot skip other cleanup, and allowed ordinary compiler temporary-file disappearance during measurement. Tests now cover those lifetime requirements and the test-snapshot error. The governance decision is review-only: no SOP, skill or AGENTS rewrite is needed; the narrow regression suite is the prevention measure. Independent review remains the controller's responsibility.

Residual limits: this is a trusted-build resource guard, not an adversarial filesystem or security sandbox. Concurrent same-user malicious writes and broker-created processes outside ordinary job inheritance are outside its contract. File/disk polling cannot guarantee a hard byte quota between samples. Abrupt host death prevents finalizing its receipt, while OS job closure still terminates members. Windows versions before 10, 32-bit PowerShell and alternative .NET hosts were not tested. No engine build, GPU work, model test, release or CI claim follows from these tests.

Rollback is a scoped revert of the owned commit after review; retain all new H: evidence and unrelated working-tree changes. The next action is independent Task 2 review, then explicit-budget native work under Task 3.
