# Personal overwrite 2 — preparation only

Date: 2026-11-07. Owner: OpenCode. Status: EXECUTING authorized personal overwrite.

## Requirements and ownership

Prepare app `0.5.2-local.2`, Control `0.5.3`, unchanged r3 native `0.5.2` for the
user's personal candidate. This call must not build the final app/Control,
install, activate an engine, pause/restore servers, push, tag or delete worktrees.
The parent owns integration/review/source freeze, maintenance, handoff and cleanup.
Only product version files, the local-version note/banner, this log and
`_docs/personal-install-20261107` belong to this unit.

Initial HEAD: `c780cc84278855615b8553e3866521090452831a`. Existing parent changes
in server policy/contracts, locales, tests and the resume log were observed and
left to the parent. Existing parent untracked maintenance/handoff work is retained.
No commit/staging coordination has been granted; this unit leaves its changes
unstaged for the parent's coordinated review/commit.

## Standards / decisions

Applied the canonical preimplementation context already read in this conversation,
current project AGENTS, PC-wide MILSPEC and research baselines, Common/Start Gate/
Skill Selection/Security/Application/WebApp/Frontend/LLMOps/Python/TypeScript/Rust
SOPs, plan-mode, qa-engineer and self-review workflow. No subdelegation. No formal
compliance claim. Prior local-install helpers were read in full earlier in this
conversation; `git diff ca3ab40a HEAD -- _docs/local-install-20261106` confirmed no
subsequent changes. Build/staging helpers and relevant current contracts were
rechecked explicitly.

Default current-root native verification is required. The old c50ca06a environment
override is removed from future build environments, not used to bypass drift.
No native guard, budget, source receipt or provenance is modified. Signature and
resource qualification are separate: every future private receipt preserves
`releaseQualified=false` and the four generic CUDA resource failures.

## Preparation evidence

The read-only audit passed against the actual unsigned r3 tree:

- Native source commit: `4a171bdeb33675963edcca51f423519863fb7127`.
- Exact current-root source count: 751; source-map SHA-256
  `8d045918aa2089872e7f7698f2b9dfbb475d169333bd2927387d14cac7042588`.
- Unsigned manifest SHA-256:
  `1058ccf94a1a78be07a485e968c40b007225a9c7a39b45eae5d78fbe582191e7`.
- `strata.exe` SHA-256:
  `13fc3b96fe71afcb98990d828d2c743f85e8b59b16174a1f7da3eb4ef9b4f8e3`.
- `strata-q36.exe` SHA-256:
  `0789a8583c4409bd517357675b96f9507b7d88ae725474a70e05997cc2be5ede`.
- r3 quality receipt SHA-256:
  `f24086470706bc20a6fba521f2c74a5851990baf9e06997e1a8c22fcd9356c26`.
- Resource-origin receipt SHA-256:
  `ab8f65ae0ed12389bad3b428bc64477c968fe3698603100dd6e50c5a12d2f566`.

The 17 native functional checks, actual short bounded/legacy/restart parity and
zero-error sanitizer result are inherited r3 evidence, not reruns by this unit.
The quality record still says `resourceGuard: FAIL`, four violations, and
`releaseQualified: false`. The original unsigned component remains unchanged.

Reusable resource trees fully match the prior local.1 inventories: Node 3 files,
Harness 23,414, notices 97, local backends 38. New full inventories and the safe
audit receipt are under
`H:/Strata/releases/personal-052-local2-20261107/app`.
The private Node remains 24.22.2, SHA-256
`1c331340fa6cac5e4294725959070a143fa0507195a78ad77eed7943f719aac9`.
Installed Host remains `0.5.2-local.1`, Control `0.5.2`, native `0.5.1`, with old
engine digest `e75716a9d5deb6289e87741d42e7003ba82b7696f6121d5203e615d9fe596a96`.
No matching Strata shell, native engine or llama server was observed. Nothing was
started to restore a previously absent service.

Only signing-key path existence was checked; contents were never read or printed.
Actual signing is prepared through `feed_tool.py` on a new private copy. No new
signature, staging replacement, engine archive, component activation or final
Control/app build has been performed.

## Blocking conditions

Initial C: free space was 4.39 GiB. The full audit later recorded 3,826,802,688 bytes
(about 3.56 GiB), below the unchanged 5 GiB floor. RAM/commit/H: reserves passed.
No cleanup or reserve reduction was attempted. Parent review and a coordinated
clean source commit are independently required for build/qualification/install.
The key and Cargo cache exist; the source/model/tokenizer and resource inputs
needed for the prepared paths are present.

## Changes and future execution gates

Surgical version updates: VERSION, CONTROL_VERSION, desktop/Host package manifests
and root lock versions, Cargo manifest/desktop lock entry, CLI PRODUCT_VERSION,
legacy full-installer product strings, AGENTS banner and README local-candidate
note. Published 0.5.1 URLs/status are retained. Native CMake/Metal versions and all
parent server/locale/test changes are outside this unit.

Prepared helpers provide read-only audit; explicit private copy/sign/stage;
bounded owned Job execution; fresh locked Control; Cargo reuse only after old
unbundled shell and NSIS hashes/copies are recorded; exact payload/self-tests;
isolated real r3 E2E; and separately gated backup, one C: NSIS invocation, prelaunch
data/payload verification, offline signed activation and manual-unloaded startup.
Private engine signatures never imply public quality qualification.

The next E2E explicitly requires real NativeSettings capability from r3, saved
settings after reselection and process restart, rejection before unloading a live
model or creating a job, GUI Q36 load/nonempty chat/unload/reload, and real owned
child INFO/argv checks (4096 context, 512 prefill, 5 expert slots, F32, MTP 2,
private-owner cache). Japanese number placeholders and both recovery notices use
actual packaged WebView2 with synthetic sessions/screenshots. No API/engine/mock
replacement is permitted. The runner is prepared but not runtime-qualified.

## Commands / verification

Ran read-only Git status/log/native diff, process/resource/path checks, and
`audit-inputs.py` via the explicit new uv path. Audit PASS, preparation-only.
`tools/bump_hakua_product_version.py --check`: PASS for 0.5.2-local.2, with native
0.5.2 unchanged. Default plans for `stage-native.py` and `build.py app` report the
C: reserve and parent review/source-freeze blockers, with no execution.

`test_preparation.py -v`: **5/5 PASS** in 0.012 seconds. These are isolated gate
tests, not runtime E2E. They cover independent exact resource floors, missing/stale/
dirty review rejection, c50 override removal and refusal to relabel the failed
native resource receipt as release-qualified.

Node `--check`: PASS for verify-native, qualify-app and qa-e2e. Default plans for
qualification, real E2E, fixture preparation, installer and guard all returned
`wouldExecute`/`wouldBuild` false. No `--execute` entry point was run. `upgrade.py`
also refuses offline activation unless C: can hold the new component while keeping
the full 5 GiB reserve. Full validation then passed for **10 Python AST parses**
and **3 Node syntax checks**. The prepared version/helper source inventory digest is
`c25e5c3034c9d36a5db9f8e754f3ea4af1429419fa0cbd7bb679de6b1c281d5d`.
The full per-file hashes are in `app/preparation-validation.json`; it explicitly
records buildExecuted=false, signed=false, installed=false and sourceFrozen=false.
Its fresh process counts again found no shell/native/llama processes.

Fresh metadata check confirmed installed shell ProductVersion `0.5.2-local.1`.
At the final resource check C: had **0.88 GiB**, H: 288.52 GiB, available RAM
16.21 GiB and commit 40.12 GiB. This unit ran no build/download/cache cleanup that
would account for the falling free space. Parent must resolve the C: reserve;
the scripts retain all original floors. `git diff --check`: PASS.

Self-review-event: ticket_completed (preparation unit), qa_defect (unexecuted
runtime acceptance and unmet disk floor). Review-only governance decision: keep
the narrow explicit gates and mark E2E/installation pending; no baseline/skill/SOP
changes. Rejected alternatives: signing in place, promoting the failed resource
guard, using c50's source override, running a final build before review, clearing
unrelated disk space, stopping unknown processes or restoring absent servers.

## Residuals / next action

No final build, GUI/native E2E, backup, installation or activation in this call.
The parent must review the prepared code/selectors and final integrated source,
resolve C: reserve, freeze source, then use the commands in the helper README.
The prepared whole-source inventory permits only semantic-identical rewrites of
Tauri's generated schema JSON (known newline-only behavior); all other tracked
source bytes must remain identical through the build. Raw generated output hashes
are retained separately. Worktree reuse does not overwrite earlier final artifacts.

The unit is preparation for a personal candidate, not release completion; public
release, Spin8 remaining goals and generic CUDA resource qualification stay open.
One combined patch initially failed because an unnecessary README context did not
match; the tool applied nothing. The corrected scoped patch succeeded. No test
failure or product source change was hidden by that tooling retry.

## PrismML 0.4.1 / unsigned composite r4 continuation

New scope starts at main `be3040e6` (also includes live-child memory fix
`8232d672`). Parent retains monitor/client/store/locales, review, combined commit,
push and cleanup ownership. This unit owns the local-backend descriptor/verifier,
focused backend/distribution tests, component stager and the existing personal
helpers/log/version note. It does not sign, activate, install or build the final
app while parent monitor/source review is open. A normal Strata shell was present;
it was not stopped or modified.

### Exact identity and compatibility

PrismML's default package version is now 0.4.1 with a closed version approval map.
0.4.0 remains explicitly approved with its original base commit and original
clean-source or single-standard-sm120-patch rules. Discovery ignores unapproved
versions; verification independently rejects them, including prototype-property
names. Automatic environment-based discovery remains unchanged.

0.4.1 requires the exact base/commit/tree, both patch identities/paths/digests,
combined diff digest, clean raw-byte proof (3590 tracked files, 4 exact raw
overrides, verified=true), the original reported-dirty annotation, and private /
releaseQualified=false markers. It additionally pins the entire raw runtime.json
to `9c729c73eb050dc466203fe149a27acd5be48763a33ea2c5d2b89f78e4ddcbaa` before checking
every payload hash and exact inventory. The dirty-status exception is not generic.

Source base: `73bfe6cc485554822f80c473a3c0c4f25e80f41b`.
Source commit: `1965755ceee6738b9a04ceaf5d30e6305d6ccd00`.
Source tree: `ae33fd73e8811fd0def3f13488c6942848ac5138`.
Qwen35 patch: `d40d21c784c411a316dd33ea01665bcbb56511a3641073088c128edba83ddbe9`.
SM120 patch: `a291a22cd8915edee441e39b08b1c948e5ecc18b41060529c120701bfcf26ddd`.
Combined diff: `f95abdc644fe6f4de7e3ea20ff5dea8aa2cfe998fb88cd0fac11ff8f95c66bf8`.
Executable: `5ca5d8bfdfcb6fe46a96a06b71eaf45aedfbd1c6673bda2a10eb6412613be777`.

Primary local handoff: `H:/Strata/validation/qwen35-mtp-load-20261107/handoff-r2.json`,
SHA-256 `f683169433b78c28cc017e079a6c210b58f91fc5c0096d9af778616a7efe1b02`.
Its two real short arithmetic checks at 98,304 capacity, Q8 KV and flash attention,
56 C-API fixtures and ordinary-model-use qualification are inherited evidence.
Its real-file explicit-MTP negative test remains blocked by external processes /
disk reserve; general model quality and full-window input remain unqualified.
This unit did no new inference or MTP/model qualification.

### Executed staging and read-only checks

`prepare-prism-r4.py --execute` ran under the owned resource guard, exit 0 in
211.016 seconds. The recipe verifies r3/current-root native source binding, the
new runtime, legacy rollback runtime and approved notices. The component stager's
new explicit native-component input still uses the current-root native guard.
When reusing a composite, runtime/notice members are rebuilt from verified inputs
so obsolete members cannot silently survive. No verification guard was removed.

New unsigned composite:
`H:/Strata/releases/personal-052-local2-20261107/component-copy-r4/0.5.2-windows-x86_64-cuda-cuda13`.
Manifest SHA-256: `df94ca9c8260e002896b1fe8c26d5e5948358eaf3b83191ad7a0c28cc7f97206`.
141 files including manifest; payload 2,192,713,257 bytes.
Full component inventory digest:
`bc45b257d7c20cfdfd0a09f1525a763c870cc85b4ca902b44b008315859ee958`.
Native executable remains `13fc3b96...`; native-build.json, Q36 executable and
native kernel library were also compared exactly against r3. Original unsigned
r3 and original Prism 0.4.1 artifact inventories remain unchanged.

`resources/local-backends/prism` now matches exact Prism 0.4.1 and the staged
`resources/engine-bundle/0.5.2-...` matches unsigned r4. Previous managed Prism
0.4.0 and engine 0.5.1 staging were moved into verified backups under
`app/prism041-r4/backups`. Installed C: files and older published payloads were
not replaced. New and legacy full payload checks plus actual `--version` probes
passed both before and after staging. New output identifies commit 1965755;
legacy identifies 73bfe6cc. No model was loaded by these probes.

Receipts: `app/prism041-r4/{staging.json,runtime-readonly.json,staged-runtime-readonly.json,original-inputs.json,staged-inventories.json}`
and `app/receipts/job-prism041-r4-stage.json`. r4's signed=false, activated=false,
installed=false, releaseQualified=false flags are explicit. All four inherited
native CUDA resource failures remain in its quality receipt. Signing now requires
`--reviewed-commit` and a clean coordinated source before reading any private key.

### Single-target normal-profile plan

The supplied handoff path under `models/models/新しいフォルダー` no longer existed.
A filename-scoped search found the file at
`H:/Strata/models/新しいフォルダー/DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic.i1-Q4_K_M.gguf`.
Full SHA-256 matches `8cf793a36e62fb078ac05c2e1bdb2121ff94736dccbede7cf81b76346e868949`,
size 5,629,111,584 bytes. Read-only inspection confirms declared blocks=33,
actual tensor blocks=32 (0–31), recurrent map length=33. No GGUF metadata/tensor
directory or weights were changed, copied or deleted.

The non-executable private selection plan and two exact prior state/library
snapshots are under `H:/Strata/private-backups/prism041-user-selection-20261107`.
Private plan SHA-256: `98ed124f7c334388ba385c8aa0b8a42f8b4ce6a8735f5b952c758f0c94a4ebda`.
Two filename-matching library references exist; this is explicitly ambiguous and
requires the parent's target-profile choice, not bulk migration. No normal-profile
fields changed. Actual User Automatic override was present and unchanged.

The plan requires a fresh post-install backup of the actual WebView's
`strata.run-profiles.v1`, a restore mapping for the target old path/backend/default,
and only that target's path/variant and PrismML selection change. Existing APIs
are used: local inspection/import and current engine validation/PATCH, plus the
normal target Saved settings UI. No nonexistent server profile API is invented.
Context/Q8/FA values are only for isolated E2E; other normal settings and all
unrelated profiles/defaults must remain unchanged. User/Machine environment and
the generic active pointer must not be rewritten.

### Tests, failures and remaining gates

Focused backend/distribution run initially had 31 pass / 2 fail: the checked-in
metadata fixture did not reproduce the immutable artifact's CRLF with no final
newline. The JSON was semantically identical. Diagnostic hashes proved the exact
serialization; only the fixture constructor was corrected. Production still
hashes raw bytes and rejects reformatted manifests. Rerun: **33/33 PASS**.

First selection-plan run failed on the externally moved path before any private
snapshot/API change. The second verified the full file hash, then failed an overly
simple expected declared-block count of 32. The final check distinguishes declared
33 from actual trunk 32 and requires the untouched 33-entry map. Third guarded
run passed in 6.016 seconds. Both failures remain in guard receipts.

Prepared `qa-prism-e2e.mjs` is an additional required real packaged-GUI gate for
this exact moved file and runtime, including saved target profile, explicit
PrismML despite the old Automatic override, capacity/Q8/FA, owned actual child,
two GUI arithmetic answers, GUI unload and restart. Q36's real bounded E2E remains
separate and mandatory. Both receipts now gate `upgrade.py`; neither was executed
in this preparation. The normal-start helper preserves the old Automatic override
in its child environment without global writes.

Install/activation needs at least 7,561,422,377 free C: bytes (about 7.05 GiB)
for this component plus the unchanged 5 GiB reserve, before extra overhead.
Parent monitor review, independent source review and source freeze remain pending.
All owned changes remain unstaged for the parent's combined commit. No signing,
activation, final build/install, push, tag, worktree deletion or subdelegation.

Final continuation verification: backend/distribution **33/33 PASS**, preparation
gates **6/6 PASS** (including unchanged Automatic override), Python AST and all
owned Node syntax checks PASS, and `git diff --check` PASS. The actual default
signing plan reports parentReviewRequired=true and unsignedR4Prepared=true; the
new GUI runner's default plan executes nothing. Future build and qualification
also compare the staged composite against the exact signed-copy receipt, and
qualification rechecks its signature with packaged Control's built-in keys.

Final source/helper inventory digest:
`d89811cce9109ebe6e63fbecadc334e5643454a667b02489d3f72f8f4fe87fa9`.
Receipt: `app/prism041-r4/preparation-validation-r2.json`. Earlier validation
receipts are retained. Final observed HEAD remains `be3040e69c64def183244da469b552bb708f32f7`;
index is empty. The final resource sample has C: 6,091,227,136 bytes (about 5.67
GiB), below the future component activation requirement; RAM/commit/H floors pass.
The app shell remains present; native/llama counts are zero. No unrelated process
or parent-owned monitor/UI source was changed by this unit.

New/changed production surfaces for parent review: `apps/host/server/local-backends.mjs`,
`apps/host/tests/local-backends.test.mjs`, `apps/host/tests/hakua-distribution.test.mjs`,
`apps/host/tests/fixtures/prism-0.4.1-runtime.json`, and
`apps/desktop/scripts/stage-engine-components.mjs`. Preparation helpers, the local
README note and this log are the remaining owned changes. The parent's App,
Sidebar, Monitor, client, store, locale and associated test edits are separate.

Self-review-event: ticket_completed (Prism preparation), qa_defect (fixture
serialization / moved path / declared-versus-trunk count), local_fix. Evidence:
the failed and passing CPU/guard receipts and exact read-only model/package
checks above. Decision: narrow fixture/plan corrections and exact source/artifact
pinning; no global SOP/skill changes or guard relaxation. Rejected: accepting
arbitrary runtime versions, generic dirty-source exceptions, signing before
parent review, rewriting model metadata, mutating all matching profiles, or
replacing the Automatic environment. The remaining actual GUI/sign/install
gates are explicit and have not been reported as passed.

## Execution authorization at 3425966c — measured system blockers

The user/parent authorized actual personal signing/build/GUI qualification and
overwrite from reviewed and pushed source
`3425966c18295c394729c8bf1206b8355827f652`. Main HEAD and the local origin/main
tracking state match it; tracked source was clean on entry. All parent-reported
source review/test gates are accepted as supplied. This attempt is not waiting
for another source review. No push/tag/public release was performed here.

Fresh system preflight observed one installed Strata shell, no strata/strata-q36
engine and no llama-server process. The owned shell → private Node Host endpoint
was resolved from current process ancestry and its loopback listener, not a stale
PID or fixed port. Host HTTP was healthy, chat active turns=0, serving running=0,
queued=0, task activity=0 and native live instances=0. The Host nevertheless had
one native **install** job still running. Its engine status was `error`, not a
trusted indication that every tool was idle.

Bounded read-only waiting collected **25 observations over 120 seconds**. The
same native install job still reported running, with start timestamp
`2026-11-07T04:54:56.709Z`, and no job error. No active user tool was cancelled or
process stopped. No previously absent Hermes server was started. The current app
was left open. Raw chat, task, goal and settings contents were not logged.

The explicitly authorized legacy source-build output at
`C:/Users/downl/Documents/ChatGPT/Strata/build` was inventoried read-only:
**4,172 files, 815,508,912 bytes, zero links and zero referencing processes seen**.
It includes the existing build inputs, `_deps`, CMake files and experiment reports;
none were excluded from the size inventory. This is only 0.76 GiB and cannot by
itself establish the required activation reserve.

The later disk sample was C: **6,027,776,000 bytes**. Adding the entire legacy
tree's logical bytes yields **6,843,284,912 bytes**, against the r4 payload plus
5 GiB lower-bound requirement of **7,561,422,377 bytes**. The remaining shortfall
is at least **718,137,465 bytes** (about 0.67 GiB), before the signed manifest,
filesystem/update receipt overhead and independent background writes. These are
logical-size projections, not a claimed measured reclamation. C: free space
fluctuated during the observations. RAM, commit and H: reserve passed.

The source build tree remains on C:, and
`H:/Strata/private-backups/legacy-C-build-20261107` does not exist. No real C: build
files were retired. A proposed exclusive-handle archive helper was exercised only
against disposable H: fixtures; that fixture command timed out at 120 seconds
before any successful test receipt. It is **not validated for real relocation**.
A subsequent process inventory confirmed no remaining process referencing that
test command or its unique fixture directory. The real C: archive operation was
not executed, and no failure was relabelled as a successful archive.

The inherited untracked `Microsoft/Windows` tree contains one 8,246-byte
PowerShell `ModuleAnalysisCache`, with its expected PSMODULECACHE signature and
SHA-256 `5946ffe8d7f05530932424afca5eb75a5964b5d09e6f2193bf8c6a17fcd2adb4`.
It was not proved to be this unit's WebView cache, so it was not staged, deleted,
moved or hidden through Git exclusions. The prepared source helper's untracked-
file gate therefore also remains unresolved; no source guard was bypassed.

Evidence and execution-only scripts are retained outside the frozen checkout at:
`H:/Strata/releases/personal-052-local2-20261107/app/execution-20261107`.
Important receipts: `preflight.json`, `legacy-build-metadata.json` and
`activity-wait.json`. Commands used the explicit uv path and existing Python
driver, plus read-only Git/CIM/disk checks. `wait-idle.py` stopped no process.

Actual phase status for this execution attempt: signing NOT_RUN; fresh Control
NOT_RUN; final NSIS build NOT_RUN; 13 package self-tests NOT_RUN; both new actual
GUI suites NOT_RUN; fresh personal-data backup NOT_RUN; NSIS NOT_RUN (no exit code);
native activation NOT_RUN. Existing app/Control/native installation was not
changed. The earlier local.1 success and inherited native/Prism measurements must
not be presented as results for this local.2 attempt.

Next required conditions: let the active native install/tool complete or obtain
explicit authorization for its separate cancellation; provide additional C:
headroom beyond the authorized legacy tree (at least the measured 718 MB deficit
plus overhead, preferably 1 GiB or more); resolve the nonpayload untracked cache
without deleting unknown work. Preserve the 5/10/3/4 GiB disk/RAM/commit floors.
Then resume the reviewed source with new single-use execution receipts. No
application source changes, global environment/pagefile changes, model moves,
weight edits or unrelated worktree changes were made.

Self-review-event: qa_defect / blocked execution. Kept actual measured blockers,
the archive-fixture timeout and all NOT_RUN gates. Rejected lowering disk floors,
interrupting the running native install, treating zero model processes as proof
that tools were idle, deleting unknown cache/source data, or claiming a local.2
installer/installation that does not exist. The unit remains BLOCKED, not complete.

## Resumed execution after explicit cancel/update and preservation authorization

The latest user instruction explicitly authorizes normal cancellation of the
current native preparation, preserving downloads, followed by the actual update.
It also authorizes scoped helper/evidence commits and main pushes, preservation
of specified inactive old C: staging/test trees if needed, and private preservation
of the exact PowerShell module cache. No tags or public release are authorized.

Fresh HEAD/origin tracking remains reviewed `3425966c`. Current resources recovered
externally to C: 9,256,488,960 bytes (about 8.62 GiB), RAM 16.73 GiB available,
commit headroom 42.44 GiB. No legacy C: build/control/test tree relocation is needed
at this point; all those trees remain intact. The previously timed-out exclusive-
handle archive prototype is not used.

`cancel-install.py --execute` re-resolved the actual installed shell/Host and
checked answers, requests, tasks and native operations three times. No active
native job remained by this observation, so it sent **zero cancellation requests**
rather than replaying the old job ID. All 13 observed GGUF/completed/partial weight
references remained present without shrinkage; completed file size/mtime records
matched. It stopped no unrelated process and started no absent Hermes server.
Receipt: `app/cancel-install-r1.json`.

The exact authorized `Microsoft/Windows/PowerShell/ModuleAnalysisCache` tree was
preserved privately at `H:/Strata/private-backups/main-powershell-cache-20261107`.
The synthetic H: test first proved refusal of an open writer and the standard
copy/hash/unchanged-source/remove pattern. Actual result: one file, 8,246 bytes,
SHA-256 `5946ffe8d7f05530932424afca5eb75a5964b5d09e6f2193bf8c6a17fcd2adb4`,
exact source tree removed only after verification. Unknown entries would refuse
the operation. Receipt: `app/main-cache-preserved.json`. Child build and normal
app environments now set `PSModuleAnalysisCachePath` under owned H: temp to avoid
recreating the cache inside the checkout. No global environment was written.

Signing and build gates already depend only on reviewed source/resources, not
on runtime job idleness. Quiescence remains required for actual GUI/model E2E,
backup, overwrite and activation. Runtime-source/native guards and resource
floors remain unchanged. The next scoped commit will contain only this execution
log and the owned cancellation/cache environment helpers; application code stays
identical to reviewed 3425966c. Its actual commit is the new build provenance.
