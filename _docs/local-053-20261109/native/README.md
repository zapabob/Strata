# Local 0.5.3 native adapters — prepared, execution pending

These are native-only adapters for parent-reviewed execution. The implementation
session has run adapter checks and a read-only tokenizer/header check. It has not
built or started an engine, run inference, staged a component, or qualified a
release. `releaseQualified` stays false in generated reports; parent owns the
final disposition.

## Files and scope

| File | Purpose |
| --- | --- |
| `adapter.py` | Read-only plan, fresh init, explicit synchronous/asynchronous single-phase launcher |
| `common.py` | Fixed paths/recipe, frozen-source gate, private environment, owned Job/resource receipts |
| `phases.py` | Build/bind, diagnostic, native-only stage, CPU/GPU/sanitizer/spill, final audit |
| `binding.mjs` | Verify the actual source helper's build record and fresh EXE hashes; never creates that record |
| `model.py` | r3-derived short mapped-pack bounded/legacy comparison and separately requested restart |
| `test_adapters.py` | Non-launching guard/receipt/protocol/comparison regression tests |
| `validate.py` | Retained syntax/help/dry-plan/tokenizer/small-test validation, entirely in this directory |

Historical scripts and outputs remain at `_docs/personal-native-20261107/` and
`H:/Strata/releases/personal-052-local2-20261107/`. They are read-only references,
not qualification evidence for this build. The implementation follows `build.py`,
`guard.py`, `qualify.py`, `followup.py` and `receipt_check.py`, including the r3
pre-READY memory receipt and seven-request private-cache/cancellation semantics.

There is no composite step, signing, installation, version edit, download,
automatic all-phases command, user-service control or global environment update.
PrismML 0.4.1 and TurboQuant 0.4.0 remain the parent's composite inputs. Parent
adds the new q36 digest to Host only after fresh qualification. Internal GPTPro
candidate `ef3df253` is unavailable here; its optimizations/flags are not recreated,
included or qualified by these adapters.

## Required freeze and fixed outputs

Parent must supply a clean, reviewed **absolute H: checkout root** and its full
40-character lowercase commit. There are deliberately no implicit source-root or
commit defaults. Source/output overlap and linked path components are refused.
The entire supplied checkout must have clean Git status, including untracked
files. Use a separate clean source root if this integration worktree still
contains untracked handoff files. The adapters remain in this directory and do
not need copying into the source checkout.

Parent owns the product `0.5.3-local.1`, Control `0.5.4`, native `0.5.3` freeze.
The adapter enforces native `project(strata VERSION 0.5.3 ...)`, the reviewed Git
commit and clean tree; the other version numbers are recorded as expectations,
not independently qualified product/Control metadata.

`BASE = H:/Strata/releases/local-053-20261109-opencode` must not already exist at
init. Build goes to `BASE/native-build`, native stage to `BASE/native`, unsigned
component to `BASE/native-component/0.5.3-windows-x86_64-cuda-cuda13`. No earlier
compiled output is reused. Existing source dependency
`H:/Strata/deps/ggml-3cf03257` must be clean at
`3cf03257f219afbe7334045ff7c6a06ac68c627d`. There is no fetching fallback.
Initialize native before any app lane creates this shared BASE; the app lane can
subsequently create its own `BASE/app` subtree. An already existing BASE is a
parent coordination blocker, not permission to delete or reuse it.

Init binds the source commit, dependency pin, current helper hashes and these
adapter hashes. Every phase checks that identity before executing, and the worker
checks it again before returning success. A changed frozen root or adapter
requires parent review and a deliberate new-run decision; do not edit receipts
or remove reservations to force continuation.

## Build and containment

The recipe retains the historical portable Release, x64 MSVC BuildTools / VS17,
CUDA 13.3.73, sm_120, one-job build, Spin8, native experts, native cache and cache
owner, K-quant MMQ and TQ overlay. DeepSeek/split builds and HIP prefill MMQ remain
off. The reviewed default spill allowances are retained with an empty explicit
baseline, exactly as in the historical build recipe. No allowance or baseline
file is changed. Fully disconnected FetchContent and an explicit existing ggml
path prevent dependency fetching through this recipe.

The build invokes the **actual supplied source root's**
`tools/build_hakua_engine.mjs <build> 1`. That helper writes the authoritative
`Release/native-build.json`. `binding.mjs` verifies current `nativeSources(root)`
membership and bytes, recipe and EXE hash. Actual source count, compiler metadata,
record and both EXE hashes are emitted later; there is no old source-count,
digest, violation-count or pass-count assumption.

Each phase's worker is created suspended and atomically assigned through
`tools/perf131k/windows_job.run_owned`. Per-command Jobs provide bounded logs,
serial tests and short deadlines. The interactive model is a descendant of its
atomically contained driver Job; it has no breakaway permission. On failure,
the driver exits and `run_owned` drains only that Job before input hashes are
checked. No process discovery, unrelated PID accounting or user-process stop is
used. Request-level `STOP` in the private-cache test is native protocol
cancellation inside that owned model instance.

The launcher uses an exclusive global run lock and immutable per-phase
reservation. A detached controller PID is just a controller, not evidence that a
Job started or completed. Only `receipts/<phase>-phase.json` proves completion;
require its `passed=true`, atomic containment, observed native exit and confirmed
empty Job. Locks are released only after confirmed Job drain. Failed starts,
abandoned controllers or unconfirmed cleanup leave the lock for parent diagnosis.
No automatic stale-PID cleanup is provided.

The guard continuously samples at the existing helper's cadence, keeping free
RAM >=3 GiB, commit headroom >=4 GiB, C: >=5 GiB and H: >=10 GiB. Whole phases
have a hard maximum of 5400 seconds (90 minutes). Normal command output is capped
at 8 MiB; build/whole-phase output at 64 MiB; model stdout/stderr at 8 MiB each
with bounded lines/queue and startup/request deadlines. Model admission also
requires 8 GiB free RAM and 14 GiB free GPU memory. Failed admission means
coordinate with parent for a quiet window; no other processes are stopped.

Only child environments receive private H: temps/uv/pip/CUDA caches. Inherited
tuning, Python hooks, compiler flags and credentials are omitted. Node is pinned
at `C:/Users/downl/AppData/Local/Programs/Strata/node/node.exe` / `24.22.2`;
Python is `C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe`;
detached controllers use `C:/Users/downl/.local/bin/uv.exe` offline, no-project,
no-config, no-managed-python with that exact interpreter. No dependencies install.

## Parent commands — after review and explicit execution approval only

These snippets are a manual handoff, not an automatic run script. Substitute the
real clean source root and full reviewed commit. Run one phase at a time and
inspect its completed receipt before starting another.

```powershell
$py = 'C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe'
$adapter = 'H:/Strata/worktrees/main-integration-20261106/_docs/local-053-20261109/native/adapter.py'
$source = 'H:/PARENT-SUPPLIES-CLEAN-FROZEN-SOURCE'
$commit = 'REPLACE_WITH_FULL_REVIEWED_40_HEX_COMMIT'
$frozen = @('--source-root', $source, '--reviewed-commit', $commit)

# Safe read-only plan: no freeze claim, no writes or native launches.
& $py -B $adapter plan @frozen

# Only after parent approval. Fresh output, source/dependency/adapter binding.
& $py -B $adapter init @frozen --execute

# Detached one-job build; returns a controller PID and eventual receipt path.
& $py -B $adapter launch build @frozen --seconds 5400 --execute
```

After `receipts/build-phase.json` is complete and passed, stage the native-only
unsigned component with the existing packager and source build record:

```powershell
& $py -B $adapter run stage @frozen --seconds 600 --execute
```

Then run the functional suites separately, awaiting each receipt:

```powershell
& $py -B $adapter launch cpu @frozen --seconds 1200 --execute
```

CPU covers actual `strata` and `strata-q36` version/help/capabilities, q36 bounded
experts, store, transfer lifetime, bounded CPU parity, KV layout and
`q36_version` (missing model + GPU hidden). The registered CTest inventory is
retained. When registered, it also runs `adaptive_range_test`,
`mmq_ids_margin_test`, `timer_marks_test`, `qsa_two_pass_test` and
`qsa_two_pass_status_test`. An absent optional test is `NOT_AVAILABLE`, not PASS;
an absent required test, skipped test or present-but-failed optional test fails
the phase. The suite is serial and does not run the entire upstream test catalog.

```powershell
& $py -B $adapter launch gpu @frozen --seconds 1200 --execute
```

GPU covers q36 KV lifecycle/full-cache tests, native-cache bridge/owner and actual
Spin8 B2 first-use/full tests. Run sanitizer as its own phase:

```powershell
& $py -B $adapter launch sanitizer @frozen --seconds 900 --execute
```

Sanitizer runs the toolkit version plus memcheck on lifecycle and full-cache
binaries. Success requires exit zero and an actual `ERROR SUMMARY: 0 errors`.

```powershell
& $py -B $adapter launch spill @frozen --seconds 900 --execute
```

Spill runs the actual configured `cuda_spill_guard` against this build. Skip 77,
missing test and every violation are failures. This independent phase may fail
even if functional tests pass; keep the failure and all `VIOLATION` output.
Audit retains this distinction and never promotes the candidate.

### Optional actual short Q36 comparison (each launch explicit)

Only start with parent-authorized GPU/RAM availability. Each phase uses the
existing `H:/Strata/models/qwen36-UD-Q4_K_XL/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf`,
its adjacent `.q36epk` and `.verified`, plus the supplied tokenizer directory
`H:/Strata/models/packs/qwen36-ud-q4_k_xl/tokenizer`. No conversion, verification
receipt priming or weight writes are requested. Protected inputs include the
GGUF, pack, verified receipt, `.done` and tokenizer files; before/after full
SHA-256, size and modification time must match. This means substantial read I/O
even though inference is short. An updated native verification receipt is
reported as a preservation failure, not silently restored.

```powershell
& $py -B $adapter launch model-bounded @frozen --seconds 3600 --execute
```

After the bounded result is complete:

```powershell
& $py -B $adapter launch model-legacy7 @frozen --seconds 3600 --execute
```

Both use mapped-pack, 4096 context cells, f32 KV, expert slots 5, MTP 2, no warmup,
greedy and private conversation cache. They check seven r3-derived requests:
first owner A, same-owner reuse, different owner B, missing owner, decode
cancellation, post-cancel reset, and short generation. The prompt comes from the
actual supplied tokenizer, cross-checked with GGUF metadata. Non-cancel generation
is at most eight tokens. No full-window, model-quality or speed claim follows.

Restart is separate and never automatic. If wanted, run it before comparison:

```powershell
& $py -B $adapter launch model-restart @frozen --seconds 3600 --execute
```

Restart is a new owned bounded instance with first-use and short-generation
requests. It is never a stop/restart of any user instance. Compare then checks
fresh bounded/legacy token/count/finish equality and any explicitly run restart:

```powershell
& $py -B $adapter run compare @frozen --seconds 120 --execute
& $py -B $adapter run audit @frozen --seconds 300 --execute
```

If model phases were omitted, audit records them as NOT_RUN and exits nonzero
with its summary retained. Run audit once, after the parent's selected phases.

### If the historical generic version-probe transient occurs

Do not patch the source helper, write a synthetic build record, reuse a historical
digest or mark the failed build receipt passed. First inspect
`receipts/build-helper.{json,txt}` and `receipts/build-phase.json`. A separate
diagnostic is available and does not qualify/bind the build:

```powershell
& $py -B $adapter run probe-diagnostic @frozen --seconds 120 --execute
```

Only after parent review, an explicit `bind` phase reruns the **same current build
helper** on that configured build. It does not waive its probe or checks. It may
finish outstanding targets, still within a 90-minute phase limit:

```powershell
& $py -B $adapter launch bind @frozen --seconds 5400 --execute
```

The earlier failed build remains failed and is included in audit. Stage requires
a successful build or explicit bind phase and the helper's actual source-bound
record. Every named phase/command is one-shot. A failed configure/build directory,
partial package or failed qualification is retained; ask parent to choose a
reviewed recovery/new-run path rather than deleting outputs. There is no automatic
retry, output rename or baseline change.

## Evidence handoff generated later

| Output under BASE | What it proves |
| --- | --- |
| `freeze.json`, `build-source.json` | Explicit native source root/commit, helper/adapter hashes, ggml pin and configure recipe |
| `results/compiler.json` | Actual CMake cache and configured CUDA/MSVC identity |
| `native-build/Release/native-build.json` | Authoritative current source helper record |
| `results/build.json` | Verified fresh native source count, recipe, record hash, strata and q36 EXE hashes |
| `native/` | Native-only loose stage |
| `native-component/0.5.3-windows-x86_64-cuda-cuda13/` | Existing-packager unsigned native-only component |
| `results/package.json` | Source commit/root, component manifest hash and per-file hashes |
| `receipts/*-phase.json`, `*-reservation.json`, `*-controller.txt`, `*-launch.json` | Phase result, reservations, async controller evidence |
| `receipts/*.json`, `*.txt` | Per-command admission, owned Job counters, bounds, native exit and raw output |
| `results/{cpu,gpu,spill}-inventory.json` | Actual registered test targets; no assumed catalog count |
| `results/{cpu,gpu,sanitizer,spill}.json` | Functional/resource results, kept separate |
| `results/model-*-inputs-before.json`, `model-*.json`, `model-*-protocol.json`, channel logs | Protected hashes/metadata, actual short requests and pre-READY memory contracts |
| `results/comparison.json` | Fresh bounded/legacy token/count equality, optional explicit restart |
| `results/qualification-summary.json` | Parent handoff with source/executable identities, resource violations, missing phases and limits |

These paths describe future data, not files generated by this preparation task.
Today’s evidence lives in the `validation-*` directories **here**, with exact
commands and exit codes in `results.json`. Re-run only non-launching checks with:

```powershell
& $py -B 'H:/Strata/worktrees/main-integration-20261106/_docs/local-053-20261109/native/validate.py'
```

Final preparation check: `validation-20261109-155554/results.json`, all checks
passed; 31 mocked/non-launching pytest cases passed. Python reported 3.12.10 and
Node 24.22.2. Read-only tokenizer/header equality and prompt round trip passed
with IDs `[760, 6511, 314, 9338, 369]`. A prior wider lint run at
`validation-20261109-155319/` caught one unused import; that failure is retained
and the import was removed before the final passing run. These are adapter
preparation results, not native build/functional qualification results.

The direct pinned interpreter bootstraps these control/validation scripts so uv
cannot select a C: cache before child H: paths exist; Python checks and detached
controllers themselves use the specified offline uv runner. Validation imports
installed test tools only. Native compiler/build, nested Windows Job operation,
actual functional/sanitizer/spill suites, model preservation, performance and
packaging remain unverified until explicit parent execution.
