# Native cache-parser correction and retry preparation

## Requirement, cause and scope

Fix only the native adapter's CMake cache parsing after the parent-reported
pre-compile failure. Preserve every expected recipe value, resource floor, source
root and output BASE. Prepare an optional explicit parent-only evidence-preserving
retry helper. No real BASE rename, native/app/model launch, source/version edit,
commit, push or historical evidence edit is authorized in this task.

The retained `receipts/build-phase.txt` reports
`CMake recipe drift: CMAKE_CUDA_ARCHITECTURES`. The actual cache line 50 is
`CMAKE_CUDA_ARCHITECTURES:UNINITIALIZED=120`. The original multiline regex used
negated character classes that admitted newlines, so comments/blank lines could
become part of a cache key. This was an adapter parsing bug, not architecture drift.

Applied the existing Common/Implementation Start Gate/Skill Selection/Security/
Application Development/Python SOPs and already-loaded canonical pre-implementation
context. Skills: milspec baseline, yaraikata-memo under the no-subagent constraint,
and self-review. Existing code and retained evidence were inspected first. All
changes remain inside this native handoff directory. Parent's ongoing app-lane
modifications were observed in Git status and left untouched.

## Changed files and implementation

`phases.py`: added strict per-line `parse_cmake_cache`. LF/CRLF, blank lines,
`#`/`//` comments, typed entries and empty/embedded-equals values are handled
without cross-line matching. Keys/types must have valid token syntax. Malformed
or duplicate entries fail. `validate_cache` now uses this parser; its expected
dictionary, exact architecture `120`, compiler checks and output behavior did
not change. `common.py`, BASE/source-root handling and resource floors were not
edited.

`test_adapters.py`: added regressions for LF/CRLF plus comments/blank lines,
UNINITIALIZED architecture type, empty values, embedded equals, split malformed
entries, duplicate keys, and rejection of missing architecture, `121`, `120;121`,
`120 ` and `120-real`. Added retry-helper safety checks and whole-tree preservation
on isolated pytest fixtures only. No test renamed the actual release BASE.

`retry_prepare.py`: default read-only inspection requires the exact first parser
failure, observed failed exit 1, atomic containment, confirmed empty owned Job,
successful configure with exit zero and confirmed cleanup, matching retained
source/helper identities, no active lock and no post-configure/helper/native/app
outputs. The destination must be the absent same-parent sibling ending in
`-configure-failed-r1`. Only explicit `--execute` rechecks eligibility/evidence
hashes and renames the entire BASE. No first-attempt file content is rewritten.
It neither initializes a replacement BASE nor launches any build.

`validate.py`: added the new helper's non-launching help check.
`README.md`: documented the correction, actual inspection result and exact
parent-only retry/new-init commands. This new log preserves the original
implementation log as historical evidence.

## Commands and validation

Ran the pinned Python bootstrap:

```powershell
& 'C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe' -B 'H:/Strata/worktrees/main-integration-20261106/_docs/local-053-20261109/native/validate.py'
```

Evidence: `validation-20261109-164839/results.json`. All checks passed: AST, Node
syntax, existing/new help, dry-plan, read-only tokenizer/header check, flake8
`E9,F`, and **54 pytest cases passed in 0.34s**. Validation children used the
existing pinned offline uv runner. No dependencies were installed.

Read-only actual-cache validation used `phases.validate_cache` against the retained
build and exact supplied source root, replacing only its receipt writer with a
printing callback. It passed all unchanged recipe and compiler checks and printed:

```text
readOnly=True; cacheArchitecture=120; cacheKeys=550
cacheSHA256=e228c2002cd7c00e07dc353bf5190c004e107df6d54576a47aef4b57f188ac7d
```

This check wrote no `compiler.json` or other release output. The direct pinned
interpreter was used intentionally for this stdlib/local read-only inspection,
avoiding changes to retained attempt caches.

Ran the actual helper **without** `--execute`:

```powershell
& 'C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe' -B 'H:/Strata/worktrees/main-integration-20261106/_docs/local-053-20261109/native/retry_prepare.py' --source-root 'H:/Strata/worktrees/native-053-source-20261109' --reviewed-commit '26e5889625938459580313ca7ce6b3931606c27b'
```

Result: `eligible=true`, `renamed=false`. Retained build receipt has
`passed=false`, `FINISHED`, native exit 1, `termination_confirmed=true`,
`job_active_after=0`. Configure has `passed=true`, native exit 0 and confirmed
empty Job. Actual `Release/strata.exe`, active lock and destination were absent.
Source freeze validation passed against the supplied root/commit. No real BASE
rename or replacement init was run.

Inspected `git diff` for the changed parser/runner; the expected-value dictionary
is unchanged. `git diff --check -- _docs/local-053-20261109/native` passed (Git's
existing LF/CRLF conversion notices are informational).

## Traceability, self-review and limits

Parser bug -> strict per-line parser -> comments/blank/CRLF/negative exact-120
tests plus actual retained-cache validation. Retry requirement -> gated helper ->
read-only actual eligibility plus rejection/preservation fixture tests.

Self-review-event: type=qa_defect scope=local053-native-cache-parser category=correctness evidence=H:/Strata/releases/local-053-20261109-opencode/receipts/build-phase.txt

Self-review-event: type=ticket_completed scope=local053-native-cache-parser category=qa-coverage evidence=validation-20261109-164839/results.json

Decision: narrow implementation/test correction only. No governance update is
needed. Rejected bypasses include accepting arbitrary architecture strings,
changing expected values, weakening resource/Job floors, editing the source
freeze, changing BASE, reusing a failed frozen adapter identity, or deleting the
first attempt. No historical failure was converted to PASS.

Actual native compilation/qualification is still pending. The parent's first
failure is intact, and only the parent may run the explicit retry-preparation
rename, then new init with current adapter hashes. The helper assumes exclusive
parent ownership of the output during its short inspection/rename window. The
real rename was not exercised in this session; only isolated fixture renames
were tested. All future native/app/model launches remain separate decisions.
