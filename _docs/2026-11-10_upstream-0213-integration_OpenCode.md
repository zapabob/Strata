# Official 0.2.13 integration

Status: COMPLETED for private source/build/overwrite delivery, with the explicit
qualification limits below. Agent: OpenCode. Plan: PLAN-2026-11-10-upstream-0213.

## Requirements and decisions

Integrate official main `f33c8c30588ff00e24b6b63bad0bf6a14da19081`
(release v0.2.13) into the primary C: main checkout. Preserve F01–F11,
Hakua/Hermes memory, authenticated consent, signed fork updates, Windows Job
ownership, model/pack integrity, refusal-direction opt-in and workspace file CRUD.
Adapt overlapping code to the official APIs. Keep models, user files, prior
artifacts and failed evidence. Subsequent builds request five jobs with existing
resource floors and caches. Acceptance requires focused contract, Host, Python,
type and build checks, then separately source-bound installed-app checks.

Applied compatible canonical pre-implementation context, PC/project AGENTS,
Common, Start Gate, Skill Selection, DeepResearch, Security, Application,
WebApp, Frontend, Python, TypeScript, CPP and Rust SOPs. Skills: existing
deepresearch-defense-standard and milspec-codex-standard baseline; plan-mode.
Use existing project design tokens/components and Python merge tooling.
No Goal API is exposed; the objective is recorded here and in the task list.

## Baseline and rollback

Pre-merge source: `1f6661441bf7c09791abd6806a0e551477110b48`, clean main.
Installed personal app: 0.5.3-local.1, Control 0.5.4, native 0.5.3. Its
`app-files/normal-startup.json` and candidate/installed receipts are the baseline;
they do not qualify the new merged source. Native source remains separately
frozen at ded724a4. Existing twelve CUDA resource violations and
releaseQualified=false remain open.

Python created `backup/pre-upstream-merge-20261109T190713Z` at the baseline.
The prior release-preparation stash is untouched. Merge was started with
`--no-commit`, no stash operation, and stopped with expected conflicts. No merge
commit or publication has occurred. Both parent Git objects preserve originals.

## Commands and evidence

`git merge-tree --write-tree --name-only <upstream> HEAD` exposed 42 conflicted
paths; the historical merge helper's heuristic reported only one generic hint.
Actual execution used uv, the existing Python 3.12 interpreter, and:

```text
python -B tools/merge_upstream_fork.py --execute --backup --no-commit --upstream-ref f33c8c30588ff00e24b6b63bad0bf6a14da19081 --output H:\Strata\releases\upstream-0213-20261109-opencode\execute.json --markdown-output H:\Strata\releases\upstream-0213-20261109-opencode\execute.md
```

Exit 2 means the merge stopped with conflicts. Reports are retained under that
H: directory. Conflict resolution, tests and builds are pending.

## Public security evidence checked

The official repository's public advisory endpoint returned no entries during
intake. This is not proof of absence of vulnerabilities. Issue #5284 describes
an older Docker image; its reported package counts are not a scan of this fork.

Checked GitHub primary advisory records on 2026-11-10:

- https://github.com/advisories/GHSA-332p-7hrc-92wf (CVE-2026-112393):
  first fixed Pillow 13.0.0.
- https://github.com/python-pillow/Pillow/security/advisories/GHSA-wqgw-9xfh-qf2g:
  affected <=12.3.0, fixed 13.0.0.
- https://github.com/python-pillow/Pillow/security/advisories/GHSA-xcvg-w56q-r89m:
  affected <=12.3.0, fixed 13.0.0.

Read-only installed interpreter metadata (Python SOP inspection exception)
reported Pillow 13.0.0, urllib3 2.8.0, certifi 2026.10.19 and hakua-memory 0.3.5.
Thus these three Pillow records do not require a further installed-version bump.
This is a narrow version comparison, not a full vulnerability/supply-chain scan.

## Residual risks and next actions

Native/API/UI conflicts need reviewed resolutions. Auto-merged code also needs
contract checks. New source needs new build and hardware evidence; old signed
artifacts cannot be relabelled. Cross-backend compilation, full-window generation,
general model quality and positive Qwen3.8 projection remain unverified.
Finish conflict review, record exact resolutions, run focused regressions, freeze
new source, then build and verify the actual installed candidate.

## Reviewed merge resolution and initial regression

The reviewed `_docs/upstream-0213-resolve.py` first computed all proposals with
no mutation, then resolved42 conflicted paths through the Git index. Three new
official CMake module paths carry the relocated fork GPU/CPU/spill additions.
Both parents are pinned; every conflicted input was also preserved as a Git blob
whose ID was printed in the resolver report. A duplicate setup.py anchor stopped
the initial dry run before mutation; its contextual replacement then passed.
No unmerged paths remain. The upstream-deleted sync-design-kit.mjs was restored
byte-for-byte from the pre-merge parent to honor file preservation; the official
build no longer invokes it. No whole-tree ours/theirs resolution was used.

Official draftingHint/settingsHints, automatic drafter preparation, signed-feed
family availability/fit sizes, deferred screen loading, language catalogs and
highlighter loading are combined with the fork's negotiated KV/memory settings,
checked saves, current-child observations, async tuner, consented memory and
build-identity startup gate. Spin8/cache/Q36 registrations follow the official
modular CMake graph; prefill uses model geometry and retains native cache hooks.

Initial Host group128 pass/2 failures identified synchronous locale fixtures
after the official setTranslationLanguage API became asynchronous. Those tests
now await the real API, and the Hakua UI browser fixture does likewise. The
DeepSeek-dot-ID positive test already passed; its invalid-ID cases now assert
the fork's synchronous pre-job rejection and zero Control/job side effects.
Fresh owned `receipts/new-host-r2.json` and .txt:131 passed,0 failed/skip.
TypeScript1024MiB check passed. Vendored dependency check passed127 files against
the existing external ggml3cf03257 checkout and official manifest.

Python first group143 pass/1 outdated upstream-version assertion; the assertion
now expects official0.2.13 and preserves independent fork versions. Follow-up
drafting/card/private-files/monitor/setup group204 passed/2 skipped.

The broad base-catalog test still finds the pre-existing56 manual web/skill keys
missing in six languages. `_docs/upstream-0213-locales.mjs` compares against exact
pre-merge1f666144: no new missing keys. Chinese now has the missing56 translated
entries; Japanese already covered them. The test was not weakened or skipped.
Its remaining failure is documented, not a full-localization pass.

## Retained QA failures and containment

A broad server test run exceeded the original120s terminal deadline after an
error; no full-suite pass is claimed and a subsequent process inspection found
no matching live test process. The fatal-GPU fixture used a SimpleNamespace
without the fork's cleanup method; it now calls the actual class method and
asserts stale allocation/child evidence is retired. A fresh full run is pending.

Owned source-check wrapper r1 used relative script paths from the H: output cwd
and failed before tests. Absolute checked-in helper paths fixed that issue; both
r1 receipts remain. All subsequent long checks have deadline, output bound,
RAM3GiB/commit4GiB/C5GiB/H10GiB floors and drained owned Windows Jobs.

Python new-feature group r2 timed out300s with21 cases reported. A180s verbose
diagnostic found the exact recent-miss fixture reaching the real stock-drafter
fallback, not a production deadlock. Test now isolates that stock boundary,
still asserts the tuned feed is not called and the supported stock fallback is
called once. Its fixture rejects unexpected transfer.download calls. The failed
Jobs drained with no active descendants; their receipts/output and isolated
scratch remain. A corrected rerun is pending.

Self-review-event: qa_defect. Evidence: asynchronous catalog failures, fixture
side-effect download and wrapper cwd failure. Narrow fixes are in the fixtures
and owned runner. Decision: review-only for governance; no new AGENTS/SOP/Skill
rules or weaker gates. Prevention is observable: await catalogs, prohibit real
transfers in decision-only fixtures, use absolute helper paths under owned cwd.
Reverted/unchecked alternatives (global API fallback, disabled isolation or
relaxed resource/source checks) were rejected. Build/install remains pending.

## Completed source checks and new build identity

Corrected owned new-python-r3:144 passed,5 skipped. Owned server-focused-r1:
187 passed,2 skipped, covering security/request boundaries, memory consent,
private cache, Q36 KV/memory observation, projection, fatal restart, Anthropic
tool ordering and stream ownership. CRUD/workspaces/storage group18 passed.
Full pytest/server and unittest discovery attempts each exceeded600s; their
drained timeout receipts remain failures, not full-suite passes. Further broad
repetition was replaced with the explicit affected-module group above.

New candidate identity: product0.5.4-local.1, Control0.5.5, native0.5.4; Metal
source remains0.5.0-metal. Installed0.5.3-local.1 is unchanged. Version sources
were edited surgically, preserving earlier measurements. The old product checker
assumed the AGENTS banner was line3; it now finds the explicit anchored Hakua
banner. Product --check and six version tests passed. Fresh typecheck-r2 passed.

The new `_docs/upstream-0213-native.py` uses the existing Windows owned-Job
guard, keeps all resource floors, and requests five jobs. Read-only plan passed.
Prepare copied5191 existing build files/2215878552 bytes into a fresh H: build
root; full source/copy inventories matched and the original build matched again.
The absolute-path old CMake cache is retained as CMakeCache.pre-0213.txt.
Configuration passed with CUDA13.3.73, MSVC19.44.35224.0, sm120, portable,
Spin8/native-cache opt-ins and no spill baseline. This uses the official default
flash_next geometry. CMake CMP0194, absent ccache and unused disconnected-fetch
variable warnings remain visible; no dependency acquisition occurred.

Five-job native compilation was launched by an explicit controller; its owned
worker result is pending at receipts/native-build-r1.json. Source is the primary
C: checkout; build outputs are the new H: root. Original frozen source, build,
signed components and model artifacts are retained. MSB8028 warnings from copied
incremental tracking records are retained; no clean/rebuild command was issued.
Actual reuse and elapsed time will be described from the completed build log,
not inferred from copying objects. No new native qualification is claimed yet.

Fresh source browser-r1 passed8 actual workspace file/UI checks with0 page
errors, including editor survival across the sidebar breakpoint, old-file edit,
create/rename, reversible trash/Undo, folder navigation, stale-save rejection
and Japanese mobile keyboard closure. Desktop1600x1000 and mobile430x900
screenshots were read back. This uses real workspace disk routes in a fixture
Host; it is source-browser verification, not installed-shell/model inference.
The browser builds to a new H: output, preserving prior dist and browser evidence.

Pre-checkpoint credential/payload scan:667 staged files,0 findings. Git diff
check with CRLF handling reports only four terminal blank lines in the unchanged
upstream vendored dependency; the127-file provenance check already matched its
manifest and upstream pin. These bytes were preserved. No model/runtime/private
payload was staged. Source checkpoint does not declare build/install completion.

## Source checkpoint, Control and native verification continuation

Merge checkpoint `7bb2497400b8ea40d5d07f5244f010d3aa5eacc0` has parents1f666144
and officialf33c8c30. It was committed locally; publication is not yet complete.
New frozen native source is `H:/Strata/worktrees/native-054-source-20261110` at
that commit. Every tracked file's physical bytes matched the primary checkout.
After copying LF/CRLF-equivalent bytes, Git initially reported stat-only changes
despite identical filtered blob hashes. Refreshing the exclusively owned frozen
index with `git add -u` left the index tree unchanged and made status clean.
Fresh freeze-source-verify-r1 passed; the failed initial freeze receipt remains.
No primary source or prior frozen worktree was reset or rewritten.

Native compilation completed all targets in the five-job r1 attempt, then the
original helper's version probe failed; this remains a failed attempt. Both
executables subsequently reported0.5.4 directly. The unchanged authoritative
five-job build/helper rerun r2 passed in14.024s with the retained objects, and a
separate source-bound bind phase passed. No probe check was relaxed, and that
incremental timing is not a clean-build result. Actual compiled input count779.
strata SHA256 `57d4dc6e06ef50e40d52539dd69ebf87c52f017f87fa2ea0e2621dadbc260c34`;
Q36 SHA256 `d21628d9c24cc73720bbd8ef170e2c06d7500b38ce6c68f063e827274a29c411`.
Fresh stage, CPU, GPU and both sanitizer cases passed under drained Jobs.

Bounded-memory model phase passed seven actual short private-cache requests at
4096 capacity with unchanged model/pack/tokenizer snapshots. Same-owner reuse,
different/missing owner separation, cancellation/clearing and nonempty short
generation passed. This does not qualify full-window or general model quality.
The exact measured native hash is now admitted for mapped-pack launch; no other
unknown binary gains admission and legacy remains the default. Legacy/restart,
comparison, resource guard and final audit are still in progress.

Fresh generated qualification adapters live under the new H: output, with exact
template/transformation hashes. Earlier0.5.3 adapters/evidence remain unchanged.
The first generated set missed an escaped version-regex identity and failed
before init; it is preserved. Corrected native-r2 preserves all original
functional/resource/model gates and uses the actual C: compiler graph plus
byte-identical H: source freeze. Native evidence is in native-evidence/.

Control0.5.5 archive70752510 bytes, SHA256
`71b88908d902cd8feca21888c8bbaa3bf15c7fa567e842893145b4ce47d34904`, was built
from7bb24974 with private Python3.12.15 and the unchanged hash-locked wheels.
Its production stage checks passed. The outer build r1 then rejected the new
untracked backup directory. Fresh accept-control-r1 preserved that complete
backup under the existing ignored archive, rechecked inventories/archive/source
binding and production stage-control --check, and confirmed clean source.
Both the failed build receipt and passing acceptance receipt remain; a source
checkpoint change will require a newly bound Control for the final app build.

User explicitly approved unloading the current Prism model for new tests and
installation. By the subsequent inspection the model and shell had already
exited, leaving15111MiB free VRAM; no absent process was claimed stopped. Test
models are serialized. Old user data and installed0.5.3 bytes remain preserved.

## Final build, overwrite and installed evidence

App/Control checkpoint `85a78234cfcdccd8741cc921677802aba1869e44` adds only the
measured native mapped-pack admission hash, its existing registry test update,
and this evidence log. The mapped-admission lifecycle group passed. Native source
stays frozen at7bb24974; no already frozen adapter/source was edited.

Legacy7 and restart2 phases completed with protected input hashes unchanged.
Bounded-versus-legacy request/token comparison and restart comparison passed.
Fresh spill guard completed with12 actual violations; audit recorded completed
FAIL, nativeFunctionalChecksPassed=true and releaseQualified=false. The resource
guard and audit exit failures were retained. No allowance or guard was relaxed.
The fresh quality validator accepted the private-build disposition: functional
checks pass and genuine resource failures stay failures.

Fresh delivery adapters were generated under the new H: output with template and
transformation hashes. Historical native/component/app helpers remain intact.
The app recipes include the previously observed LF-only scratch fixture, normal
owned-window close, full bounded ownership probes, non-pooled Node QA HTTP,
actual Chat options navigation and actual engine INFO readiness. Four actual-app
recipes plus qualification generated and syntax-checked before runtime execution.
Exact dependency scopes use the new C: staging path. The old UI output54 files
was preserved by same-volume rename with a matching inventory before Vite ran.

Control was rebuilt from85a78234 for the final app, not relabelled from7bb24974.
The final Control archive SHA256 is
`81a8cb78a066b9ca9599d7d95f19d10d1e8e2671c9dc967be49326854c9d21f0`.
Its build/stage phase passed in158.281s. Pinned interpreter cache was copied and
verified, original preserved. Complete earlier Control staging was preserved.

Composition authenticated the complete older signed payload before retaining
Prism0.4.1/TurboQuant0.4.0/notices, verified new native sources and fresh quality,
composed/signed the new0.5.4 component through the production signer, checked its
archive, PE dependencies and builtin trusted-key signature, then preserved the
entire old bundle and staged the new one by same-volume renames. No key contents,
key hash or key-derived private data was inspected or logged. Signed manifest
SHA256 `52e8674bf1dec83df9d972ec4fd5dfa5607bc9b1d30ec3eb99ade499de116ab3`.

Five-job incremental desktop build passed in717.062s with preserved prior Cargo
executable/installer artifacts. Qualification passed in107.531s: thirteen actual
startup self-tests and29544 exact payload files. Installer:

```text
H:/Strata/releases/upstream-0213-20261109-opencode/app-native054/Strata-0.5.4-local.1-windows-x64-setup.exe
112415417 bytes
SHA256 ae05518656ee5afdf92665f5dd71a06a69425ae1957a9ac31468d8a4a1790750
```

Qualified/delivered shell SHA256 is
`e00ebf5c6d5b54f89a1830f694cd5cce184caa868bfc06d4c0d7f38da180e450`.
The separately saved unbundled shell has its own hash in app-build.json; it is
not substituted for the actual extracted/installed shell identity.

Candidate Q36 r1 passed714.375s; candidate Prism r1 passed161.625s. A fresh private
backup retained4028 user/config files without copying model weights. Three exact
previously reviewed large retained component caches were rehashed and included;
the100MiB limit remains for every other non-weight file. Backup, silent NSIS
overwrite, before-first-launch payload/user/registration verification and signed
full-test-start activation all passed. Installed payload29544 files matched;
4028 backed-up files and the previous0.5.3 component were retained; both shortcuts
and registry target/version were correct. Explicit installation target remains
`C:/Users/downl/AppData/Local/Programs/Strata`.

Activation uses the actual candidate's retained production-prepared native-tune
config after normal GUI unload removed ephemeral instance JSON. The exact tested
binary, memory mode, model/privacy args and4096/512/5/2/F32 settings are checked.
Memory-principal credentials are removed only from the private test sandbox;
engine authentication remains enabled. Test-start was not disabled. Older engine
selection/payload preservation and new imported component membership were checked.

Installed Q36 r1 passed844.657s with actual installed EXE, Host, WebView2, native
inference, observed private/cache ownership, settings after restart, unload/new
owned child, Japanese notices/speed, unsupported projection rejection, zero page
errors and seven actual workspace file UI checks. Normal user hashes were
unchanged. Historical recipe labels containing053 remain labels only; the exact
0.5.4 binary, package/source hashes and observed INFO identify this execution.

Installed Prism r1 returned the first correct answer, then its second load stayed
in native warm-up until the existing health deadline. The retained log ends at
"warming up the model with an empty run" before supervised SIGTERM. No model
OOM/format error was reported. The unchanged serial r2 passed in130.406s with
both correct answers, restart/new process, actual Q8 K/V and flash attention,
zero page errors, model metadata preserved and normal user hashes unchanged.
The failed r1 is retained; no production retry/timeout setting or backend binary
was changed. Its root cause remains unresolved, not claimed fixed by a rerun.

A supplemental source-memory consent/recovery browser fixture failed at browser
launch in Chrome, then in Edge, reporting the non-default debugging directory
requirement (Edge also reported a token/path error). Vite close errors followed
the failed launch. No UI assertion in that fixture is claimed passed. Browser
sandbox/security settings were not weakened. Its two receipts remain. This does
not replace the passing actual installed tests or server-side memory tests.

Final normal-startup.json passed: ok=true, leftOpen=true, debuggingEnabled=false,
manualUnloaded=true, settingsRetained=true; product0.5.4-local.1, Control0.5.5,
native0.5.4. Process readback found the installed shell open and no native/Prism
model process. This handoff ran outside QA containment. Source was still clean
at85a78234 before these documentation-only closeout edits.

## Evidence, changed surfaces and remaining limits

Evidence root: `H:/Strata/releases/upstream-0213-20261109-opencode`.
Native evidence: native-evidence/{freeze.json,results,receipts}; actual build and
failed/rebound receipts remain at the root receipts/. App evidence: app-native054/
{control-build.json,staged-native.json,app-build.json,app-qualification.json,
candidate-q36-e2e.json,candidate-prism-e2e.json,installed-q36-e2e.json,
installed-prism-e2e.json,backup.json,installed-payload.json,native-activated.json,
normal-startup.json}. Private backup: H:/Strata/private-backups/local-054-20261110-opencode.
Operational generator/adapter provenance and frozen-source inventories are also
retained under the evidence root. No failed attempt was overwritten.

Changed implementation surfaces are the reviewed upstream merge across engine
geometry/backend CMake, source/native/Metal/SYCL references, Control/Terminal/feed
APIs, Host settings/native starts/lazy UI/catalogs, setup and official tests/docs;
fork adaptations are listed earlier. Follow-up changes are exact native admission,
async/offline fixture repairs, Chinese missing-key translations and independent
product/Control/native version sources. Current closeout updates only AGENTS
artifact metadata, README preambles, HAKUA_RELEASE/UPSTREAM_0213 and this log.

Residual limits: twelve newly measured CUDA resource violations; releaseQualified,
full-window/general/low-precision model quality and positive Qwen3.8 projection
remain false/unqualified. Other backend/device builds were not run on this PC.
Full server discovery exceeded its600s budget; the explicit affected187-test
group passed instead. Six base catalogs retain their pre-existing56 missing
manual web/skill keys; none were newly lost. The supplemental memory browser
fixture is blocked as described. One Prism restart warm-up timeout remains an
observed risk. Security comparisons cover the cited public records, not a claim
of a full vulnerability audit or absence of vulnerabilities.

Recommended next actions are source-bound investigation of the Prism warm-up
failure, resource findings, long-context/quality qualification and remaining
catalog/browser-fixture gaps. Public release/tag/feed publication was not part
of this private overwrite; the published stable download remains0.5.1.

Self-review-event: ticket_completed / qa_defect. Evidence includes each retained
failed gate, corrected fixture and passing fresh owned receipt above. Decision:
review-only for governance. Project AGENTS changed artifact-status metadata only;
no PC-wide AGENTS, SOP, Skill, source/secret/resource guard or release allowance
was weakened. Narrow recipe changes were validated by generation/syntax and the
actual runtime checks. Bypassing browser sandboxing, disabling native test-start,
removing failed evidence or calling short tests general qualification were
rejected. Final source checks and remote readback are recorded below when run.

Final readback passed: the exact installer and installed-shell hashes still
match qualification, and the actual unchanged activation test-config hash
matches native-activated.json. Explicit model path, private conversation cache,
shared-cache-off arguments and source-bound bounded mode were checked without
printing authentication data. Product consistency check passed; all6 current
version tests passed in3.79s under isolated H: scratch; `git diff --check` passed.
These final edits are documentation/status metadata only and do not requalify or
rebuild the installed85a78234 app/Control or7bb24974 native artifact.
