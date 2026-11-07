# Qwen3.5 missing-MTP GGUF load

Date: 2026-11-07. Owner: OpenCode. Status: private Prism 0.4.1 built and staged;
the reported GGUF passed actual 98304-context chat/stop/restart checks. Ready for
parent review/intake. The additional real-file CLI explicit-MTP check is blocked
by external native starts and the C: disk floor; C-API MTP rejection passed.

## Goal, scope and acceptance

Fix the reported local qwen35 GGUF load and preserve the first useful loader error.
Work in `H:/Strata/worktrees/main-integration-20261106`, limited to generic GGUF
compatibility, supervisor, import metadata, associated tests and this log. Other
agents' changes are present. No install, release, model write, registry/config
mutation, native-control/native-settings/serve change or delegation is authorized.

Acceptance: prove the runtime cause, retain model bytes and all trunk layers,
reject missing/wrong trunk tensors and present/partial MTP from any normalization,
honor explicit runtime choice and manifest verification, preserve requested
context/precision, and record an owned bounded actual-model load/response if
resources admit it. A short request does not qualify full-window generation or
general model quality.

## Standards and design constraints

Applied Common, Implementation Start Gate, Skill Selection, DeepResearch,
Security, LLMOps, Application Development, TypeScript and Python SOPs. Skills:
the supplied MILSPEC/research baselines and systematic-debugging. The canonical
`CLAUDE-FABLE-5.md` was read; conflicting identity, environment, tools and date
claims defer to the actual harness and PC/project instructions. Goal API is not
available; the objective is recorded here. No formal compliance claim.

Treat GGUF metadata as untrusted: bounded read-only parsing, explicit architecture,
complete tensor proof, no filename inference, no blind layer subtraction. Runtime
selection and package verification retain their existing contracts. Any per-run
override must be visible in command/status/logs and supported by the selected
runtime. Existing MTP weights must not be disabled.

## Initial evidence and hypothesis

The user supplied an authoritative installed error: Automatic selected
`generic-gguf/prism-b10826-c9c34bc/llama-server.exe` through `STRATA_LLAMA_SERVER`.
The first error names absent `blk.32.attn_norm.weight`; the supervisor currently
retains only the last three generic errors. The supplied inspection reports
5,629,111,584 bytes, qwen35, block_count=33, nextn_predict_layers=1, 427 tensors,
blocks 0..31 only, and no out-of-file tensor extent.

Primary sources checked on 2026-11-07:

- https://huggingface.co/Qwen/Qwen3.5-9B/raw/main/config.json : 32 hidden layers,
  one MTP layer, 4096 hidden width, 12288 FFN width, full attention every fourth layer.
- https://raw.githubusercontent.com/PrismML-Eng/llama.cpp/c9c34bc/src/models/qwen35.cpp
  and local `H:/Strata/deps/prism-73bfe6cc/src/models/qwen35.cpp`: the loader
  subtracts NextN for trunk execution but passes TENSOR_SKIP without
  TENSOR_NOT_REQUIRED for the absent MTP block.
- Local `src/llama-model-loader.cpp`: missing tensor checks are separate from
  skipping present tensors. Static evidence predicts both installed Prism builds
  fail on absent predictor weights, not a lost trunk layer or RAM shortage.

Runtime `--version` reports 0.2.0-dev build 10826 commit c9c34bc9c for Automatic.
The first packaged Prism version probe exceeded 15 seconds; a subsequent process
query found no llama/native processes. Further probes use owned job containment.
No model was launched by these version probes.

## Containment and validation location

Real-model work used fresh
`H:/Strata/validation/qwen35-mtp-load-20261107` profiles, ephemeral loopback ports,
contain-before-GO and 0.5-second sampling against floors of RAM 3 GiB, commit
4 GiB, C: 5 GiB, H: 10 GiB. Cases ran serially with 180-second outer deadlines.
The existing `serve.winjob` containment and `native_model_resource_guard` memory
telemetry were reused read-only. Every guarded case cleaned up its owned tree;
no other process was stopped. The guard would abort only its own tree if another
model appeared. Fresh process counts before/after observed no other model server;
the user's GUI PID 3356 remained running.

## Verified root cause and failed remedies

The actual installed Automatic binary and the manifest-verified packaged Prism
binary both failed on `blk.32.attn_norm.weight`. Each emitted this error before
the generic fit/load failure cascade. This is a runtime/export compatibility
failure at tensor-directory validation, not measured RAM exhaustion. The bounded
reader confirmed all 427 expected trunk tensors, their dimensions, valid row
geometry, nonoverlapping extents, and in-file payloads. No numerical weight
quality claim follows from that inspection.

Both runtimes expose `--override-kv` in actual help output. However, this file
also has `qwen35.attention.recurrent_layers` as an explicit **33-element array**.
A controlled Automatic probe using exactly these proposed overrides:

```text
--override-kv qwen35.block_count=int:32
--override-kv qwen35.nextn_predict_layers=int:0
```

failed with an expected array length of 32 and actual length of 33. No candidate
reached health and no prompt was sent. The inspected CLI supports scalar
overrides, while `get_key_or_arr` validates the original array length before its
scalar lookup. Automating these two flags would replace one load failure with
another; changing the recurrent map to a scalar would also alter model semantics.
No override or runtime substitution was added to production commands.

The read-only TurboQuant pinned source at
`H:/Strata/deps/thetom-64395689/src/models/qwen35.cpp` has the same missing-MTP
flag pattern. This is static evidence only; no TurboQuant inference case was
run, and it is not offered as a verified remedy. The installed ggml source also
has the same distinction between skipping a present tensor and allowing an
absent tensor. No dependency was downloaded, patched or built.

## Owned implementation

Changed files:

- `apps/host/server/gguf.mjs`: optional bounded tensor-directory retention and
  FFN metadata; opt-in directory inspection also checks overlap and quantized
  row geometry. Ordinary imports retain no tensor directory.
- `apps/host/server/qwen35-gguf-compatibility.mjs`: conservative diagnostic for
  the exact source-backed Qwen3.5-9B geometry. Checks every required trunk tensor
  name/shape, explicit recurrent map, single-file identity and no predictor or
  unknown tensor. A tied output head is allowed. It never grants an override
  capability, modifies metadata, infers architecture from a name, or changes a
  model's execution settings.
- `apps/host/server/startup-diagnostics.mjs`: retains the first useful loader
  cause independently of the 400-line ring plus a bounded recent error tail;
  handles pipe chunk boundaries, unterminated lines, UTF-8, ANSI and secret
  redaction. Each launch owns a new collector.
- `apps/host/server/supervisor.mjs`: uses that collector during startup. Only on
  the reported missing-predictor error, and only after complete structural proof,
  appends the runtime-compatibility explanation. Metadata inspection failure
  leaves the original engine diagnostic intact. Runtime selection, strict
  manifest validation and the actual launch arguments retain their behavior.
- `apps/host/tests/gguf-mtp-compatibility.test.mjs` and
  `apps/host/tests/supervisor-diagnostics.test.mjs`: regression/negative controls.
- This implementation log.

Scratch harnesses and raw receipts are under the validation directory, outside
Git. No pre-existing parent/other-agent file was edited or staged. No commit was
requested or created.

## Commands and results

Node was the installed private `24.22.2` at
`C:/Users/downl/AppData/Local/Programs/Strata/node/node.exe`. Python was the
existing `3.12.10` interpreter driven by
`C:/Users/downl/.local/bin/uv.exe run --no-project --offline --python
C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe python -B`.
TEMP/TMP, isolated profile roots, test scratch and the uv cache were directed
to H:. uv reported existing dangling package metadata; no package was changed.

The guarded command form was:

```text
uv run --no-project --offline --python <Python312/python.exe> python -B
  H:/Strata/validation/qwen35-mtp-load-20261107/guard.py
  --name <fresh-case> --seconds 180 -- <private-node> <case-script> <case-args>
```

Each `guard.json` contains the exact command. Each model `case.json` records the
complete argv, exit and health result. Model arguments used the original
configuration: context **98304**, GPU layers **999**, threads **12**, K/V
**q8_0/q8_0**, batch **2048**, microbatch **512**, flash **on**, parallel **1**,
temperature **0.6**, top-p **0.95**, top-k **40**, repetition penalty **1.05**,
and loopback with a fresh ephemeral port. Test profiles did not use production
port 8080 or the user's API key. These are requested settings; none of the
failing runtimes reached a ready allocation.

Validation evidence:

- `inspect-r1`: full model SHA-256; actual runtime help/version; packaged Prism
  source, approved patch and complete payload verification passed.
- `automatic-original-r1`: reproduced missing predictor, exit 1, not READY.
- `prism-original-r1`: same failure, exit 1, not READY. Choosing this Prism build
  does not fix the user's model.
- `automatic-scalar-r1`: reproduced recurrent-array length mismatch, exit 1,
  not READY. The harness exits zero because it asserts this expected failure;
  that is not a successful model load.
- `unit-red`: all 11 new tests initially failed on the missing functionality.
- `unit-green-r1`: 28 focused/new/existing regressions passed.
- `edge-red`: an added test caught an overly broad scalar-capability claim for
  a missing map (8 passed, 1 failed). It was corrected to remain fail-closed.
- `unit-final`: **54 passed, 0 failed** across GGUF compatibility, startup
  diagnostics, supervisor startup, local models, local backends, memory geometry
  and K/V settings. Negative controls remove each of 426 required tensors in
  turn and change each of 427 shapes, and cover partial/present MTP, wrong
  architecture, wrong metadata, overlap, truncation and retention limits.
- `supervisor-real-r2`: production supervisor against the actual Automatic
  executable now exposes the first missing-tensor error and the verified
  32-trunk/absent-predictor/33-entry-map explanation. Explicit environment
  selection and argv equality were asserted. Engine still fails to load.
- `<private-node> node_modules/typescript/lib/tsc.js --noEmit` in `apps/host`:
  passed. `git diff --check`: passed.

Across guarded work, minimum sampled headrooms were RAM 11.738 GiB, commit
41.270 GiB, C: 6.769 GiB, H: 287.613 GiB. All guard abort fields are null.
Final read-only GPU query: RTX 5060 Ti, 14613 MiB free of 16311 MiB. No native or
llama engine remained. Raw summaries are in `summary.json` under the validation
directory; this is a diagnostic run, not a throughput or capacity benchmark.

## Exact identities and externally relocated path

Automatic reports build 10826, commit c9c34bc9c. Measured SHA-256:

```text
llama-server.exe 95105be565fcb2ad6bd1c343ae851339cbad63b26de4edb76eb878a58ae21039
llama.dll        dc6af63ad4ef0a8b04269baa93939d3ee8b0ad1fb7b4f9ca6b2e2f9f046de659
```

Packaged Prism in engine component 0.5.1 reports build 10787, commit 73bfe6cc,
runtime package 0.4.0. Measured SHA-256:

```text
llama-server.exe 90428627933e0c4120fe0bcaa6a3cc7803dd5fe5846102eeacf4cf1298807a8d
llama.dll        d51063b744d462b553c30978189159b02b51d91ead02dd3a084ad654151d81e0
```

The full model SHA-256 before all model cases and again before/after the final
supervisor case was:

```text
8cf793a36e62fb078ac05c2e1bdb2121ff94736dccbede7cf81b76346e868949
```

During the work the original model path became unavailable externally. The
first supervisor smoke (`supervisor-real-r1`) stopped at ENOENT before launch.
Read-only discovery found the same filename at:

```text
H:/Strata/models/models/新しいフォルダー/DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic.i1-Q4_K_M.gguf
```

Its complete hash was checked against the original **before** the subsequent
launch. Size 5,629,111,584, mtimeMs 1794007447373.683 and ctimeMs
1794008108685.2913 matched the initial inspection. Final size/timestamps and
full hash remained unchanged. This agent did not move or write the file. The
installed Host still reported the original path at the read-only check; the
parent/user must explicitly reselect the relocated file if that remains true.

## Earlier handoff residuals (superseded by the continuation below)

The user-facing load is **not fixed yet**. There is no verified successful
load/response or numerical-semantic result. The scoped Host source makes the
cause visible and refuses to manufacture a metadata workaround.

A parent-authorized isolated build of the existing pinned generic runtime is
the next required step. The runtime fix should permit an entirely absent
optional predictor only when MTP loading is not requested, retain strict checks
for every trunk tensor and partial predictors, and leave all 33 metadata/map
entries plus the 32-layer execution count intact. It must not set NextN to zero
while retaining block_count=33, which would incorrectly add a trunk layer.
Check all predictor tensor membership, not just one norm tensor. Present MTP and
explicit MTP requests must retain their existing behavior. This proposed source
fix has not been compiled or run in this scope.

The parent needs to review a new runtime identity/patch and package manifest
rather than weakening the current whitelist or overwriting an installed DLL.
After the candidate succeeds at the same requested 98304 context and cache
settings with a short synthetic response and owned cleanup, include the four
Host source files above in the personal app build and qualify the runtime
component separately. Source inclusion alone cannot repair the installed
runtime. No full-window, general-quality or release qualification is implied.

Self-review-event: type=qa_defect scope=generic-gguf/qwen35 category=correctness evidence=H:/Strata/validation/qwen35-mtp-load-20261107/automatic-scalar-r1/engine.log

Self-review decision: retain the array-length failure, the runtime-load blocker
and the external path relocation explicitly. Reject blind layer subtraction,
silent runtime fallback, reduced context/precision and unapproved dependency
edits. Narrow regression tests and this acceptance record are sufficient; no
AGENTS, skill, SOP or unrelated workflow change is justified.

Rollback is removal of the owned source changes. No installed bytes are changed.

## Parent-authorized private-runtime continuation

The parent subsequently authorized an isolated patch/build of the existing
Prism pin, CPU loader fixtures, a new private generic package and bounded actual
chat/stop/restart checks. Installation, activation, public release, environment
and model mutations remain forbidden. Native 0.5.2 and other agents' files
remain outside this scope. C++ SOP now also applies.

The pinned base `73bfe6cc485554822f80c473a3c0c4f25e80f41b` is present and its
original checkout is clean. Created a detached worktree at
`H:/Strata/validation/qwen35-mtp-load-20261107/source-r1` using existing objects
with `GIT_NO_LAZY_FETCH=1`; no dependency download occurred. The original
dependency worktrees and installed/runtime assets were not changed.

Prepared `tools/qwen35_mtp_loader_probe.cpp` (dynamic calls to the real selected
llama DLL, CPU backend only, no_alloc), `tools/test_qwen35_mtp_loader.py`
(fresh small synthetic GGUF directories), and
`tools/build_qwen35_generic.ps1` (existing MSVC/Ninja/CUDA 13.3, serial build).
The separate reviewable `tools/qwen35_absent_mtp.patch` handles directory-wide
trunk/predictor membership, required recurrent projections, and complete Q/K/V
membership when a present predictor is skipped. It changes no graph loop or
model hyperparameter. It has not yet been applied/built at this checkpoint.

Read-only environment check found `STRATA_LLAMA_SERVER` at both Process and
User scopes pointing to the old c9c34bc runtime; Machine scope is absent.
Desktop Rust and Host source do not synthesize that variable. The installed
generic pointer independently names the same old folder with owner
`cursor-prism-20261027-191448`. Therefore an active-pointer update alone cannot
override the persisted explicit User choice. The parent activation plan must
retain that distinction and obtain an explicit per-launch/user selection; this
agent will not mutate global/User environment values.

Build admission attempts were refused before compiler launch. First sample:
RAM 844767232 bytes (below 3 GiB). Second sample: RAM 2266316800 bytes and C:
4230340608 bytes (both below required floors). Another `iq_pack.py` process,
PID 10764 at observation time, held about 20 GiB resident. It was not stopped.
No guard was weakened. CPU baseline and patched build remain gated pending
resource recovery; failed admission is not a compile or runtime result.

### Published model identity, checked 2026-11-07

Parent supplied the publisher repository and independently matching LFS identity.
This session then fetched the primary tree API directly:

https://huggingface.co/mradermacher/DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic-i1-GGUF

https://huggingface.co/api/models/mradermacher/DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic-i1-GGUF/tree/main?recursive=false&expand=false

The Q4_K_M entry declares size 5629111584 and LFS SHA-256
`8cf793a36e62fb078ac05c2e1bdb2121ff94736dccbede7cf81b76346e868949`, exactly matching
the measured local file. This establishes published-artifact identity, not model
quality or runtime compatibility. No weights were downloaded or rewritten.

### Frozen runtime patch and executable baseline

Private source commit: `1965755ceee6738b9a04ceaf5d30e6305d6ccd00`, tree
`ae33fd73e8811fd0def3f13488c6942848ac5138`. Base remains the existing Prism pin.
Only three source files differ: qwen35 loader, plus the already reviewed two-file
standard-sm120 compatibility patch. Graph construction/execution functions and
model hyperparameter loading are byte-identical to the pinned source.

The standalone Qwen35 patch SHA-256 is
`d40d21c784c411a316dd33ea01665bcbb56511a3641073088c128edba83ddbe9`.
The retained standard-sm120 patch SHA-256 is
`a291a22cd8915edee441e39b08b1c948e5ecc18b41060529c120701bfcf26ddd`.
The complete `git diff --binary --full-index` from base to private source is
`f95abdc644fe6f4de7e3ea20ff5dea8aa2cfe998fb88cd0fac11ff8f95c66bf8`.
All artifacts are in `freeze-r1/` under the validation root.

The actual-DLL C++ probe compiled with MSVC `/W4 /WX`.
The initial probe erroneously treated the statically registered CPU backend as
a loadable plugin (`cpu-baseline-r1`: harness failures, no valid loader verdict).
It was corrected to query the registered CPU device. The corrected
`cpu-baseline-r2` executed all 56 fixture cases through the installed pinned
llama C API with `n_gpu_layers=0`, an empty offload device list and `no_alloc`.
The linked CUDA backend still prints a device-registration message; these are
CPU model-directory checks, not CUDA inference tests.

Baseline result: 50 pass, 6 fail against the desired fixed contract. The six
regressions are trunk-only rejection, acceptance of each missing predictor Q/K/V
projection, acceptance of an MTP-only file without an MTP request, and acceptance
of an incomplete trunk when its first norm is absent and full MTP is present.
Complete ordinary, complete MTP and fused-predictor positive controls loaded.
The patch has now been applied to the isolated source and committed there; no
installed DLL or original dependency checkout was changed.

### Actual source materialization and bounded build

`cuda-build-r1` launched with guard PID 22800 and stopped after 9.25 seconds during
CMake configuration. The owned checkout contained 785 incorrect NUL-filled
files despite a clean cached Git status. Byte hashes differed from the frozen
Git blobs; raw mismatches are retained under `checkout-before-repair/`.
`git restore` and forced checkout-index did not repair those observed bytes.
Only the evidenced mismatches in this owned worktree were re-materialized from
locally available, hash-verified Git blobs, flushed and read back. No source
version was downloaded or changed. The underlying checkout/materialization
failure is not diagnosed as a hardware issue.

`checkout-verified-r2` verifies all 3590 tracked files. Four upstream vendor
files store literal CRLF blobs, so verification accepts either exact Git blob
bytes or Git's normal path-filtered identity. Cached Git status still reported
changes even when content diff returned zero. Therefore the build now uses
`tools/verify_frozen_llama_source.py` before each phase and after linking, rather
than relying on cached status alone. This strengthens the source gate; it does
not alter Git configuration or skip content validation. The CMake version output
may retain a `-dirty` suffix from that cached status and is recorded verbatim.

The owned durable guard records root PID/creation time, child PID/creation time,
contain-before-GO, resource traces and final cleanup. It has a two-hour deadline
for this serial build; model-test deadlines remain at most ten minutes. It is a
single explicitly launched process, not a service, scheduled task or autostart.

`cuda-build-r2` (guard PID 28152, creation epoch 1794016506.145765) configured with
CUDA 13.3.73, MSVC 19.44.35229, Ninja, standard sm_120 and the original format
selection. It reached step 63/508 without a compiler error, then the guard
aborted at 701.328 seconds because another engine appeared. All resource floors
passed; only the owned build tree was terminated. The external engine was not
stopped. Build warnings so far include the toolkit's C4819 code-page warning,
CMake's ASM policy warning and missing optional NCCL/ccache.

After the external engine exited, `cuda-build-r3` resumed the same objects and
configuration under guard PID 20852, creation epoch 1794017304.0542762. Current
live receipt/logs are `cuda-build-r3/guard.json`, `output.txt`, `resources.jsonl`;
build driver receipt is `build-driver-r3.json`. Build verdict is still pending.

The new private package is prepared as Prism runtime **0.4.1**, not an overwrite
of public 0.4.0. `tools/stage_private_llama_runtime.py` requires a successful
build plus completed, passing containment/resource receipt, verifies source and
payload hashes, bundles the DLL closure through the existing packager, probes
the executable and writes an immutable manifest plus a plan-only selection
record. Its six integrity/environment/failed-guard tests pass after observed red
runs. `LOCAL_BACKENDS` has not been changed; the parent must independently
approve this exact new source/patch identity and select PrismML only for the
reported model. The persisted explicit Automatic environment remains untouched.

Two more starts of an external native process stopped `cuda-build-r3` and
`cuda-build-r4` under the unchanged exclusivity guard. The latter recorded
`strata.exe` from installed engine 0.5.1, PID 19616 at that observation, not an
exact `--version`/`--help`-only command. No private command-line arguments were
logged and no external process was stopped. The current attempt is
`cuda-build-r5`, guard PID 2652, creation epoch 1794018139.5830104; it resumes
the same frozen source/configuration and retains the successful object outputs.
All attempts and their reasons remain in separate durable receipt directories.

Black check and Flake8 (`--max-line-length=88`, matching Black) pass for the five
new Python tools/tests. The package tests pass 6/6 after formatting. The frozen
source gate additionally passes 3/3 tests using real temporary Git repositories,
including same-size, same-mtime NUL corruption and untracked-source rejection.
Fixtures and Git identities are synthetic, isolated under H:, and do not change
global Git settings. The fixed-runtime CPU run will also require each of its
56 fixture hashes to match the recorded baseline, preventing a test-data change
from masquerading as a loader repair.

`tools/qualify_qwen35_private_runtime.mjs` is ready to check the immutable
staged package, full original model hash, 427-tensor directory, context 98304,
observed Q8_0 K/V, flash attention and GPU offload, two arithmetic requests
separated by stop/restart, and explicit MTP rejection. The verified `--offline`
flag prevents sidecar acquisition during the explicit-MTP negative test.
These checks have not yet run against a completed patched binary.

## Completed private candidate and actual verdict

The full serial CUDA build completed successfully in `cuda-build-r5`. All
179 CUDA compilation units and the final server target completed. The patched
`src/models/qwen35.cpp` compiled and `llama.dll` linked. The final resumed build
attempt took 4079 seconds; earlier interrupted attempts remain separately
recorded and their completed objects were retained. `cuobjdump --list-elf`
found exclusively standard `sm_120` cubins. Source-byte verification passed
again after linking for all 3590 tracked files. Native Strata 0.5.2 was not
rebuilt or modified by this work.

### Immutable package for parent intake

```text
H:/Strata/validation/qwen35-mtp-load-20261107/runtime-prism-0.4.1-1965755c/
```

The package contains the freshly built executable and DLLs, the complete Windows
DLL closure, license, both reviewable patches, full source diff and `runtime.json`.
Every copied build artifact/patch is checked against its source receipt after
copy, including a regression for same-sized NUL-filled copies. Bundled vendor
DLLs are compared with their explicit search sources as well. Version/help
probes passed with only System32 on PATH. Reported executable version is
`0.2.0-dev (build 2, commit 1965755)`, MSVC 19.44.35229.0. Package version is
independently **0.4.1** and `privateCandidate=true`.

```text
runtime.json     9c729c73eb050dc466203fe149a27acd5be48763a33ea2c5d2b89f78e4ddcbaa
llama-server.exe 5ca5d8bfdfcb6fe46a96a06b71eaf45aedfbd1c6673bda2a10eb6412613be777
llama.dll        40f7bd967ba3b822a872639801c4d0accc2ce40bdebf950350fb2452dc4206db
ggml-cuda.dll    9bc0f979b3619c1826a2f0a2294a27e95fa95457688640d80e96665cdb57c872
```

These are full SHA-256 values. `runtime.json` records all other payload hashes,
private source commit `1965755ceee6738b9a04ceaf5d30e6305d6ccd00`, base pin,
source tree, complete source-diff hash, patch IDs/hashes and build/guard receipt
hashes. Its `dirty=false` means actual bytes match the frozen commit; the
separate `gitStatusReportedDirty=true` retains the misleading cached-status
observation rather than hiding it.

The new payload is separate from every published/installed 0.4.0 runtime.
Neither the generic active pointer nor any registry/profile value was changed.
The plan-only sibling file is:

```text
H:/Strata/validation/qwen35-mtp-load-20261107/runtime-prism-0.4.1-1965755c-selection-plan.json
```

It records the old pointer preimage hash
`873cd3be1a3b0a16df112cc6aefc1cdab461774422d995cf4785fb67a3b28e94`, explicit User
environment selection, rollback folder and proposed generic folder. The primary
parent deployment route is **PrismML for this model**, not an Automatic override.
`LOCAL_BACKENDS` remains unchanged as instructed. Parent review must admit this
exact **version-specific** source/patch identity while preserving the 0.4.0
identity; merely replacing the old global pin would break rollback validation.

### Actual loader fixture results

`cpu-fixed-r1` / `cpu-fixtures-fixed-r1/summary.json`: **56 passed, 0 failed**
through the newly built and staged llama DLL. Every generated fixture SHA-256
was required to match the original unpatched baseline fixture. The same inputs
therefore changed from 50/56 to 56/56 without changing fixture semantics.

The trunk-only 427-tensor case loads with 32 trunk layers and one declared MTP
layer. Explicit MTP with absent predictors fails. Partial predictors, every
tested missing trunk projection/norm/FFN, missing whole first/last blocks and
wrong dimensions fail. Full MTP, ordinary non-MTP, fused-predictor directories
and explicitly requested complete standalone MTP remain valid. These are
CPU/no-allocation loader checks, not numerical MTP generation claims.

### Actual reported GGUF: load, arithmetic, stop and restart

`actual-chat-r1/qualification.json` and its guard both **passed**. Hardware was
RTX 5060 Ti (16311 MiB reported), driver 621.01, on the 32 GB Windows x64 PC.
The complete reported file was hashed before and after the test. Its SHA-256,
5,629,111,584-byte size, mtimeMs and ctimeMs exactly match the recorded original
and the publisher's LFS entry.

Both fresh owned runtime instances used `-c 98304 -ngl 999 -ctk q8_0 -ctv q8_0
-fa on -np 1 -t 12 -b 2048 -ub 512`. Sampling defaults stayed at temperature
0.6, top-p 0.95, top-k 40 and repeat penalty 1.05. Tests added only offline mode,
diagnostic verbosity and explicit ordinary (`--spec-type none`) execution.
Requests used temperature 0, seed 42, maximum 64 output tokens and the model's
non-thinking chat-template option. Authentication keys were random, process-local
and excluded/redacted from evidence.

The first instance reached health in 4.729 seconds and returned HTTP 200 with
exact content `5` for `2 + 3`. It processed 26 prompt tokens and 2 completion
tokens. After its owned stop and port-release check, a second fresh instance
reached health in 6.262 seconds and returned HTTP 200 with exact content `56`
for `7 * 8` (26 prompt tokens, 3 completion tokens). The second instance was
also stopped and its port released. These timings describe this small smoke
check only; the two/three-token output timings are not a throughput benchmark.

Both `/props` responses reported **98304** slot context. Actual logs reported
flash attention enabled and Q8_0 K/V, with 98304 cells across 8 attention layers:
K 816 MiB plus V 816 MiB, total **1632 MiB attention KV**. Logs also reported
34/34 GPU layer slots; that bookkeeping includes the output/declared predictor
slots and does not mean 34 executed trunk layers. The new loader log confirms
32 trunk layers, no predictor tensors and MTP not requested. No metadata
override was passed and the 33-entry recurrent map remained byte-identical.

Successful guard minima (GiB):

| Run | RAM | Commit | C: | H: |
| --- | ---: | ---: | ---: | ---: |
| Final build | 14.621 | 41.559 | 9.138 | 248.516 |
| Staging | 14.067 | 40.441 | 9.111 | 247.381 |
| Fixed loader fixtures | 14.701 | 40.249 | 9.110 | 250.655 |
| Actual chat/restart | 10.829 | 34.331 | 5.541 | 250.656 |

All four completed runs have `abort=null`, successful owned cleanup and zero
remaining engines at their final observation. No external model process was
stopped.

### Remaining check and parent integration gate

Two additional real-file CLI `--spec-type draft-mtp` attempts were interrupted
by newly appearing installed native 0.5.1 processes. They are retained as
`actual-mtp-negative-r1` and `actual-mtp-negative-r2`, both **aborted**, not
passed or failed model verdicts. The second had created its private cycle folder
but did not leave a completed case receipt. Subsequent read-only process checks
found no native/llama process; no owned server was left serving.

C: free space then fell below the unchanged 5 GiB admission floor (latest
recorded check: 2,285,953,024 bytes). No further runtime test is admitted in
that state. This does not invalidate the completed ordinary-model tests or the
explicit-MTP C-API fixture rejection. The **additional real-GGUF CLI MTP
negative remains open** for the next quiet, resource-admitted window. Do not
report it as passed from static reasoning or from the aborted attempts.

The immutable package is ready for parent independent source/build review and
installer intake for the verified ordinary-model path. Parent must approve the
exact new Prism 0.4.1 identity, include this whole self-contained payload in the
personal distribution, explicitly select PrismML for the current GGUF path via
the existing profile API, and perform installed-GUI smoke checks. The original
Automatic User environment and older component payloads remain available for
their existing models and rollback. This agent did not install, activate, push,
tag or change Native 0.5.2.

Read-only re-verification of the complete staged payload succeeded when creating
`H:/Strata/validation/qwen35-mtp-load-20261107/handoff-r1.json` (SHA-256
`ecf5396148802e29a310dda002a4292f76010e90289c1f91d6b49734f55f9954`). This sibling
receipt links the immutable manifest, all completed qualification receipts,
resource minima, model identity and the open CLI-negative check. It does not
alter the package manifest after testing.

Full 98K input, general model quality, numerical MTP generation, other GPUs/OSes
and final installed GUI behavior are not qualified here. `releaseQualified=false`
remains explicit. The selected ordinary path is now measured working at the
user's requested capacity and precision.

Self-review-event: type=qa_defect scope=private-runtime/source-and-copy-integrity category=qa-coverage evidence=H:/Strata/validation/qwen35-mtp-load-20261107/checkout-before-repair/report.json

Self-review: retained the invalid first probe, corrupted checkout, interrupted
build/test attempts and disk-floor block. Added narrow real-source-byte and
same-sized-copy-corruption regression checks instead of weakening Git, package,
job or resource controls. No governance files or other agents' scopes were
changed. Current supporting checks: 54 Host regressions, 56 actual-DLL fixture
checks, 7 packaging checks, 3 real-Git source checks, Black/Flake8 and Node syntax
checks passed; the real-file CLI-MTP attempt and installed integration remain
explicitly outside the completed results.

The private source commit is also preserved in
`freeze-r1/source-1965755.bundle`. `git bundle verify` passed; its sole
prerequisite is the existing base commit `73bfe6cc485554822f80c473a3c0c4f25e80f41b`.
This preserves the exact private commit for parent review after temporary
worktree cleanup, without downloading a dependency or including user weights.

Final owned main-checkout files for the scoped commit:

```text
apps/host/server/gguf.mjs
apps/host/server/qwen35-gguf-compatibility.mjs
apps/host/server/startup-diagnostics.mjs
apps/host/server/supervisor.mjs
apps/host/tests/gguf-mtp-compatibility.test.mjs
apps/host/tests/supervisor-diagnostics.test.mjs
tools/build_qwen35_generic.ps1
tools/qualify_qwen35_private_runtime.mjs
tools/qwen35_absent_mtp.patch
tools/qwen35_mtp_loader_probe.cpp
tools/stage_private_llama_runtime.py
tools/test_frozen_llama_source.py
tools/test_private_llama_package.py
tools/test_qwen35_mtp_loader.py
tools/verify_frozen_llama_source.py
_docs/2026-11-07_qwen35-mtp-load_OpenCode.md
```

Parent version/locales/installer/native-settings/memory-observation changes and
the unrelated untracked `Microsoft/` directory are excluded. Commit validation
uses `git status --short`, scoped diff review, `git diff --check` and recent log
inspection, followed by staging only the listed files. Build output, private
profiles, raw logs and model fixtures remain outside Git under validation.

Staged whitespace review reports four single-space blank-context prefixes in
the stored unified-diff `.patch` file. Those are patch-format data. Strict
whitespace checks pass on the actual private C++ source diff and on all other
owned source/docs; reverse-apply validation passes for the stored patch against
the frozen source. The patch bytes/hash are retained exactly as built and
packaged, rather than silently changing the reviewed artifact for this lint.
