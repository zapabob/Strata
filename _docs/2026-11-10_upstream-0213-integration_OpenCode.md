# Official 0.2.13 integration

Status: IN_PROGRESS. Agent: OpenCode. Plan: PLAN-2026-11-10-upstream-0213.

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
