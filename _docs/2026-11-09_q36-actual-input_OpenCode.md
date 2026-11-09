# Q36 actual-input QA preparation

Date: 2026-11-09. Owner: OpenCode. Status: CPU preparation complete; runtime NOT_RUN.

Latest checkpoint:49 CPU behavior cases passed after the independent review
requested a genuinely unscoped carrier case and external-engine/Host-activity
refusal plus emergency abort. Those source fixes are present, but the worker's
final review/log update was interrupted by an API connection failure. Historical
26-case results below predate them. Runtime, final formatting and independent
closure review remain open; do not treat a source checkpoint as native execution.
Goal: prepare the first meaningful actual-input intermediate for the parent's 32 GB RAM /
16 GB VRAM long-input, private-cache, cancel and restart qualification. No Goal API is
available here. This log tracks this preparation unit, not completion of the full goal.

## Scope and decisions

Worktree: `H:/Strata/worktrees/main-integration-20261106`. Only new files in
`_docs/native-longinput-20261109/` and this log belong to this unit. Entry status already
contained two parent logs and `_docs/native-diagnostics-20261109/maintenance.py`.
The parent's files, historical qualification scripts and receipts are retained.

Applied Common, Implementation Start Gate, Skill Selection, Security, LLMOps,
Application Development and Python SOPs; the already supplied MILSPEC baseline,
QA Engineer, plan-mode and completion self-review instructions. The canonical
`C:/Users/downl/_docs/prompts/CLAUDE-FABLE-5.md` was read as compatible context;
its alternate identity/date/tool statements do not override the active harness.
Local code and existing receipts provide the sources for this preparation. No web
claim, package-trust assessment, dependency change or formal compliance claim is made.

The CUDA worker owns the serial compiler window. This unit did not invoke a native
engine, GPU query/workload, compiler, model load, app API, process stop/start, download,
installation, commit or push. The parent explicitly paused installed Swift for
diagnostics and must restore the same model/settings after the admitted window.
The QA entrypoint has no user-app/profile maintenance operation.

## Files and requirement trace

| Requirement | New file / check |
| --- | --- |
| R1: actual model tokenizer and shipped postprompt | `fixtures.py`: extracted tokenizer matched to actual GGUF header; `serve.frontend.ChatTemplate`, thinking disabled, preserve empty-think prefix, `parse_special=True` |
| R2: approximately 3072 actual input, no truncation | Full-text search within predeclared 3072 +/-24; exact decode/re-encode; ordered compact-JSON ID SHA-256; count/headroom checks in `contracts.py` |
| R3: bounded retrieval sanity | Three unique synthetic ledger codes, positions checked; exact three-key JSON oracle fixed in source before execution; no contains/regex/hidden reasoning extraction |
| R4: owner/cache/cancel/restart | `qa.py`: first A, actual-output extended A, identical extended input B, cancel A, postcancel extended A, independent new process; strict reuse ranges and PP/DONE accounting |
| R5: containment/resource limits | Existing `tools/perf131k/windows_job.py` atomic suspended Job launch; worker membership before GO; inherited non-breakaway child tree; continuous floors and protocol STOP before owned-handle/Job fallback |
| R6: evidence and failures | Fresh owner-only H: attempt directory, complete bounded stdin/stdout/stderr transcripts, per-request predeclared input and outcome, raw PP/DONE, process RSS/private samples, whole-GPU samples, lifecycle and guard receipts |
| R7: CPU behavior checks | `test_contracts.py`: truncation, headroom/output-budget refusal, empty output, owner and cancel boundaries, PP fresh-input semantics, nonfinite/error/schema rejection, strict oracle, persisted retrieval failure and normal STOP/EOF ordering |

All four Python files are new. No product/backend file is changed. `qa.py` is the
only command entrypoint. Default is plan-only. `--test` is CPU-only. `--prepare`
reads the tokenizer files and GGUF header metadata, never tensor data or the expert
pack. The inspected `tools/gguf_reader.py` reads only metadata/tensor descriptors;
it does not map or read weight tensors. GGUF, `.q36epk` and `.verified` existence,
size and mtime are checked before/after preparation. No pack/receipt priming occurs.

## Actual CPU fixture

Fresh evidence directories, outside Git:

`H:/Strata/validation/q36-longinput-20261109/cpu-prep-01/fixture.json`

`H:/Strata/validation/q36-longinput-20261109/cpu-prep-02/fixture.json`

`H:/Strata/validation/q36-longinput-20261109/cpu-prep-03/fixture.json`

All preparations found **3071 actual tokenizer IDs**, target 3072, delta -1.
The text has 212 deterministic filler lines and three unique lookup codes at
zero-based prefix token offsets **35 / 1528 / 3021**. Actual prompt includes
the shipped system/user/assistant framing and disabled-thinking postprompt.

Ordered IDs SHA-256 (compact ASCII JSON array, no newline):

`081160eef22d06d2ec1bad5c7a91006869893899e0481dff20a95d78a7ad3469`

Predeclared expected answer:

```json
{"begin":"ALPHA7K","middle":"BRAVO9M","end":"CHARLIE4P"}
```

Only outer whitespace, JSON whitespace/key order and one final model EOS literal
are tolerated. Duplicate keys, extra keys, missing/wrong values, code fences,
reasoning or surrounding text fail retrieval. A failed retrieval remains
`RETRIEVAL_FAIL` even if the protocol/count checks passed. Boundary cases can
continue after that quality failure, but the complete result cannot pass.

The CPU oracle-only simulated assistant text encodes to **24 tokens including
EOS** and renders a valid **3120-token follow-up**, delta **49**. These are
tokenized expected text, not observed model-generated IDs. At runtime the follow-up
is built from actual generated text; its exact full rendered IDs must preserve
both the initial and emitted continuation prefixes, with delta 1..256. Otherwise
the continuation boundary fails as inconclusive rather than passing reuse0.

Every request explicitly uses `GEN 128`. Input +128 output budget +3 MTP/verifier
cells must fit capacity4096. For the base fixture this reserves 894 additional
cells. No input ID slicing, output-budget reduction or capacity-as-input claim.
The first measured native input count remains **unknown until execution**.

## Deferred native execution contract

Exact `strata.exe` SHA-256:

`13fc3b96fe71afcb98990d828d2c743f85e8b59b16174a1f7da3eb4ef9b4f8e3`

Prior source checkpoint: `4a171bdeb33675963edcca51f423519863fb7127`.
The worker will verify the built-in trusted component signature, full component
payload hashes, version0.5.2 and native-build/executable identity before creation.
This preparation did not reverify or rebuild the installed payload.

The installed component directory was confirmed by directory metadata at
`C:/Users/downl/AppData/Local/Strata/components/engine/0.5.2-windows-x86_64-cuda-cuda13`.
The actual model/pack paths exist at
`H:/Strata/models/qwen36-UD-Q4_K_XL/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf`
and its `.q36epk` / `.q36epk.verified` siblings. Historical scripts' extra
`models/models` path is deliberately not reused.

Engine arguments: mapped-pack, bounded-experts-v1, F32 K and F32 V, context4096,
prefill512, expert-slots5, MTP2, no-warmup, greedy, prompt-cache0,
conversation-cache-mib0, private-conversation-cache. Pre-READY F32/private-owner
capabilities and the exact bounded expert-working-storage allocation receipt
are required. That receipt explicitly says total_process_bound=0.

Private owner carriers are per-attempt random64hex values. The native GEN carrier
is the same `cache_scope` protocol used by `qualify.py` and by the authenticated
serve bridge; this direct harness does not exercise HTTP authentication itself.
The same-owner follow-up must report positive reuse at least the complete initial
3071 IDs and at most initial+emitted IDs. Other-owner and postcancel requests must
report reuse0. Cancellation sends STOP after the first actual T and requires
finish=cancel, full prompt accounting and nonempty actual generated IDs. A race
that finishes stop/length instead fails; no relaxed retry or relabeling.

The first owned process receives normal STOP/EOF and is reaped before a new
process is created. Restart's independent request requires fresh input and reuse0.
Serial sequence stops on protocol/resource failures. Each case's original raw
transcript and failure receipt are retained even if later cases do not run.

The Q36 PP schema counts **fresh** input, not total submitted input when reused.
The parser checks monotonic PP, PP total/final read=fresh, DONE prompt=submitted,
fresh+reuse=submitted, emitted T count=DONE generated and nonempty IDs/text.
These are **protocol count receipts, not cryptographic consumed-input proofs**.
O1 native consumed-ID hashing is not implemented. Retrieval is bounded synthetic
sanity, not general quality or 98K/131K/full-window qualification.

The existing Job launcher verifies containment while suspended, then resumes the
worker, which verifies Job membership before reading GO. Native children inherit
that non-breakaway Job. The outer controller samples RAM/commit/C:/H: continuously
and whole GPU0 at about1-second intervals; the native worker samples held-handle
RSS/private bytes at about250ms during active protocol reads. Whole-GPU values
include unrelated GUI/desktop occupancy and are not attributed to this process.
No telemetry value is an exact unsampled peak.

Floors are RAM3GiB, commit4GiB, C:5GiB, H:10GiB. Any breach signals abort immediately;
the worker stops protocol work and sends normal STOP/EOF. A15-second cleanup grace
then permits the outer owned Job fallback. The lower-level launcher's thresholds
are zero only to avoid racing the controller's normal-STOP-first enforcement;
the controller enforces all four actual floors without a grace for continuing work.
The worker stops accepting input by1170s; the outer run deadline is1200s, followed
only by bounded Job cleanup. GPU admission requires14GiB free before first load
and restart. No PID/name-wide process termination is present.

Optional legacy comparison is not implemented; the parent can separately choose
a short same-source first-request comparison. It must not consume the serial
compiler/runtime window implicitly.

## Commands

Use this working directory and already installed interpreter. No dependency setup:

```powershell
$env:TMP='H:/Strata/validation'
$env:TEMP=$env:TMP
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$uv='C:/Users/downl/.local/bin/uv.exe'
$py='C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe'
& $uv run --offline --no-project --no-cache --python $py python -B _docs/native-longinput-20261109/qa.py
& $uv run --offline --no-project --no-cache --python $py python -B _docs/native-longinput-20261109/qa.py --test
& $uv run --offline --no-project --no-cache --python $py python -B -m black --check --line-length 120 _docs/native-longinput-20261109
& $uv run --offline --no-project --no-cache --python $py python -B -m flake8 _docs/native-longinput-20261109 --max-line-length 120 --extend-ignore E203,E402,W503
```

The three actual CPU preparation commands used the same wrapper plus
`qa.py --prepare --report H:/Strata/validation/q36-longinput-20261109/cpu-prep-01`
(then fresh `cpu-prep-02`, `cpu-prep-03`). Existing directories are refused.

**Parent only, after compiler release and explicit runtime admission; NOT_RUN here:**

```powershell
& $uv run --offline --no-project --no-cache --python $py python -B _docs/native-longinput-20261109/qa.py --execute --component C:/Users/downl/AppData/Local/Strata/components/engine/0.5.2-windows-x86_64-cuda-cuda13 --report H:/Strata/validation/q36-longinput-20261109/runtime-01
```

All execution scratch/cache paths are set under that fresh H: attempt. It contains
`guard.json`, `result.json`, `fixture.json`, request JSON, full private transcripts,
process/system/GPU JSONL and lifecycle receipts. Success requires both guard and
result passed, confirmed zero active owned Job descendants, normal lifecycle exits
and unchanged model/pack/receipt size+mtime. Preserve failures; use a fresh label
for any later attempt. Parent restores Swift independently even after QA failure.

## Verification and remaining gates

Initial RAM metadata query observed20,210,808KiB free physical RAM; commit limit
68,584,493,056 bytes and committed23,352,324,096 bytes. Every CPU action rechecks
the floors. Selected interpreter reported CPython3.12.10. No package installation
or resolution was requested; uv was offline/no-project/no-cache.

The first23-test run passed but printed an incidental installed torch/pynvml import
warning. Collection was then isolated with `--noconftest`, plugin autoload disabled
and empty project addopts; subsequent24-test runs passed without that warning.
No native engine or CUDA workload was invoked by these tests. Installed uv metadata
also reports two pre-existing dangling site-package directories; they were not changed.

CPU prep01/02/03 passed and preserved model metadata. Prep02/03 additionally checked
the expected-answer follow-up; prep03 checked the emitted-continuation prefix gate.
The initial default Black check failed formatting; patches were applied using the
required file editor. The final formatting profile is explicit120 columns, matching
the scoped flake8 check; E203/W503 are Black compatibility and E402 permits lazy
project imports that keep default plan/test paths free of model/GPU startup.

Final CPU behavioral check: **26 passed in0.24s**, zero failed. Final
`black --check --line-length 120` passed, all four Python files unchanged.
Final full scoped flake8 passed with the stated120-column/Black/lazy-import options.
`git diff --no-index --check -- NUL <file>` checked each of the five new files and
reported no whitespace errors; Git printed its existing LF-to-CRLF notices.
Final git status showed only the two new owned paths in addition to the entry's
three parent-owned paths; tracked diff remained empty. Tests execute actual parser,
oracle, request-recording and cleanup helpers; they do not source-grep the code.
No broad product regression, static type checker, native build or backend test was
run: only these new task-local Python files are in scope and runtime is deferred.

Native READY/load/PP/DONE, actual generated IDs, retrieval result, memory peaks,
same-owner reuse, other-owner isolation, cancel/restart and actual elapsed inference
time are all NOT_RUN. There is no inference timing estimate before observation.
The new Job integration and native lifecycle require parent runtime qualification.

Unconfirmed static-analysis risk: recurrent session matching requires the entire
held prefix; MTP can hold accepted drafts beyond visible EOS/output boundaries.
A same-owner continuation may fail reuse despite preserving emitted text. Such a
failure remains FAIL with raw transcripts; the harness does not invent unseen IDs,
relax the owner assertion or claim cache qualification from a zero-reuse request.
Stop-after-first-T can also race an already completed short answer; that is a failed
cancellation attempt, not evidence of successful cancellation.

## Self-review

Self-review-event: ticket_completed (preparation unit only), review-only.
Evidence: CPU tests, strict parser/oracle fixtures, real tokenizer roundtrip and
source-backed native protocol inspection. The narrow fixes isolated pytest collection,
added actual emitted-prefix eligibility, preserved retrieval failure and normal-STOP
ordering. No AGENTS/Skill/SOP changes are justified or authorised. Rejected alternatives:
arbitrary IDs, ID truncation, substring/think extraction, silent lower output budgets,
old receipt edits, runtime execution during the compiler window and user-app control.
Parent spec/quality review and admitted serial execution remain the next actions.
