# Bounded Q36 memory opt-in — OpenCode

## Goal / requirements

Integrate `q36_memory: legacy | bounded-experts-v1` through the actual Q36 Host
adapter, settings PATCH, launch contract, Python admission and pre-READY receipt.
Default remains legacy. Bounded mode is experimental and unqualified; its scope is
expert working storage, never a total-process or 32 GB / 16 GB fit guarantee.

BM1: strict separate memory marker from bounded no-model help, bound to executable
SHA-256; preserve the public KV probe and strict KV schema. BM2: reject unsupported
family, conflicting/malformed mode, missing mapped-pack/positive explicit slots
before side effects where known; retain incompatible saved choices for clearing.
BM3: immutable cross-language expectations; actual-child digest/capability and INFO
receipt must prove mode, scope and nonzero bounded storage independently of KV.
BM4: minimal existing settings select, EN/JA help and catalog coverage; display only
actual observed storage. Preserve cache isolation, cancellation and profile identity.

## Scope / standards / plan

Start: main integration `d014e99948130f5bc0a8c754c0e8c618ff93a2aa` in
`H:/Strata/worktrees/main-integration-20261106`. Existing untracked handoff and native
maintenance evidence belong to the parent. Only owned Host/serve/UI/tests and this
log are changed. Native build/source, installation and final qualification are
owned by the parent/native agent. No subdelegation.

Applied supplied PC/project AGENTS, compatible canonical CLAUDE-FABLE-5 context,
Common / Start Gate / Skill Selection / Security / Application / WebApp / Frontend
Design / LLMOps / TypeScript / Python SOPs. MILSPEC baseline already supplied;
test-driven-development loaded for RED/GREEN. Existing components and docs/DESIGN.md
are the visual authority. Local source and supplied native evidence are sufficient;
no external version/package-trust claim or dependency change. No formal compliance
claim. Goal API unavailable; this log records the goal.

Plan: production-boundary RED tests; capability/policy/contract implementation;
Python actual-constructor admission; minimal localized UI and actual observations;
isolated focused regressions, typecheck, diff review, scoped commit and handoff.

## Commands / results

Initial status: only parent-owned untracked evidence. Read existing K1 and GUI
admission logs, production paths, tests and isolated runners. The native agent
independently committed `4a171bde` during this work. This unit does not modify those
native files or their build-source hash.

## Residuals / next action

No GPU/native process will be executed in this lane. Parent owns real native/Host
E2E, independent review, remaining native qualification and personal packaging.
Rollback is the scoped source commit; saved bounded settings remain explicit and
can be cleared or changed to legacy. Test evidence and self-review follow below.

## Implemented interface / files

`apps/host/server/native-settings.mjs` adds the per-model enum `q36_memory`, with
`legacy` default and `bounded-experts-v1` opt-in. `native-serving-policy.mjs` admits
it only for the resolved Q36 adapter, validates actual merged argv prerequisites,
and retains incompatible saved values and explicit clearing across all argument
representations. Native `q36_explicit_slots` is an ASCII decimal positive int;
admission therefore accepts leading zeroes and rejects values above 2147483647.
No context, K/V precision, router, MTP, worker or resource-profile default is added.

`q36-kv-capabilities.mjs` adds `probeQ36Capabilities(exe)` returning
`{kvCapability, memoryCapability}` from one bounded 3-second / 65536-byte no-model
help query with a minimal environment and before/after executable digest binding.
`probeQ36KvCapabilities` keeps its public flat KV result/null shape. The original
strict KV parser/schema is unchanged. The independent memory parser accepts only
the requested exact schema, including `modes: []` for an unsupported build.
Malformed, repeated, oversized, wrong-family and changed-binary responses do not
grant support. Host checks memory capability against the actual executable file.

`native-control.mjs` uses the shared query in settings, checked PATCH service,
load and tuning. Known capability results are keyed to the selected executable
and rechecked against its bytes for synchronous admission. A known unsupported
replacement cannot create a job or stop an existing ready model. Cold asynchronous
negotiation can create a job before rejection, as with existing KV negotiation;
it still precedes picture/drafter acquisition, profile writes and replacement.
Source `qwen36` and catalog Q36 produce runtime `arch:qwen35moe`; saved identity
and hardware-profile rules remain intact.

`q36-run-contract.mjs` adds `--q36-memory` to the source-backed flag table, captures
`requested.q36_memory` and `planned/effective.q36_memory`, and clones the strict
`backend.memoryCapability` expectation with the common binary SHA-256. These are
plan expectations, not observed memory proof. Bounded mode requires actual
`--q36-expert-store mapped-pack` and explicit positive slots. A digest-bound bounded
capability authorises its required mapped store; the legacy mapped-store allowlist
is unchanged. Explicit legacy is stripped from runtime argv and runtime user args
so old binaries never receive an unsupported new flag. The stored user choice is
retained. No native digest is added to the legacy allowlist by this unit.

`serve/native_family.py` extends the existing frozen `NativeAdmission` with mode,
independent expected memory SHA-256 and immutable capability JSON. Retained run
expectations, config/user argv, adapter and digest must agree; metadata cannot
grant engine support or downgrade the requirement. `serve/server.py` projects:

```text
STRATA_Q36_MEMORY_MODE=legacy|bounded-experts-v1
STRATA_Q36_MEMORY_HOST_SHA256=<expected executable digest, bounded Host runs>
STRATA_Q36_MEMORY_CAPABILITY=<strict digest-bound JSON expectation>
```

Ambient/saved copies cannot override these owned values. The constructor captures
argv/env before verification. Bounded mode independently probes the actual child
even with flag-free F32/no KV expectation, reuses that query for KV when needed,
checks its digest before orphan cleanup and again immediately before spawn, and
requires the following actual pre-READY INFO values:

```text
q36_memory_mode=bounded-experts-v1
q36_memory_scope=expert-working-storage
q36_memory_total_process_bound=0
q36_memory_cpu_stage_bytes=<positive uint64>
q36_memory_h2d_stage_bytes=<positive uint64>
q36_memory_io_scratch_bytes=<positive uint64>
```

Missing/wrong/zero receipts stop that child before `known_ctx`/READY admission.
Legacy unnegotiated starts retain their prior receipt requirements. KV and private
cache v1/v2 checks remain independent and mandatory when requested. Existing
metrics expose the child's INFO fields. This unit deliberately does not treat
stderr `Q36_MEMORY_EFFECTIVE` progress as pre-READY proof.

`src/components/NativeSettings.tsx` reuses the existing select and help row, labels
the choice experimental, preserves an incompatible stored choice, and shows actual
storage only from a ready selected-model instance's INFO-backed metrics. Editing a
future choice does not rewrite that observation. Missing/error-instance evidence
shows unreported. `src/lib/native.ts` adds minimal select label/receipt types.
`src/locales/fix-{en,ja,zh,de,es,fr,ru,pt,ko}.json` adds all seven new strings with
matching placeholders; all nine have translations. There is no fit guarantee.

Tests: new `apps/host/tests/q36-memory.test.mjs`,
`serve/test_q36_memory_contract.py`; extended `native-ui-ownership.test.mjs`,
`q36-capabilities.test.mjs`, the existing Host-to-Python fixture bridge, and
`serve/test_q36_kv_contract.py`'s real-constructor AST harness. The latter executes
the additional production verifier while controlling process IO. The source flag
test distinguishes the native parser's explicit refusal of `--vram-reserve-mib`
from implemented flags and still asserts that reserve is unsupported.

## RED / correction evidence

Scratch locations below are under `C:/Users/downl/AppData/Local/Temp/opencode`.
All native/process/network capability boundaries are controlled; executable hash
fixtures are inert bytes. Existing isolated Node/uv runners were reused unchanged.

Initial Host RED `strata-hybrid-yoCVoi`: 4 failed / 7 passed, 11 tests. Missing shared
probe, bounded launch, model-field projection and visible stored mode reproduced.
Initial Python RED `strata-gui-python-ZPAm87`: 6 failed / 12 passed; ten inherited
KV cases were accidentally collected through a class import. The import was changed
to a module before final counts. Actual failures included bare READY accepted,
wrong ambient mode retained, lost expectations, missing child proof and legacy flag
forwarding. UI RED `strata-hybrid-drQUmL`: 1 failed / 18 passed, specifically the
missing experimental label.

Intermediate Host `es8cib`: 44/47 passed. The exact-key parser's sorted key string
had Expert/Explicit in reverse lexical order; corrected. A shallow test capability
copy was replaced by a deep copy before its intentional mutation. `8tinpj`: 10/11
passed; corrected a test that assumed memory was the final argv pair, whereas the
unchanged private-cache policy appends its flags. Assertions now inspect the named
flag and retain the private flags. Python `O8DFsS`: 37/37 passed at that stage.

Cross-language `AEUtdU`: 9/9 passed, including real Host PATCH/build output consumed
by Python and the actual constructor. The source-capability check initially treated
the native reserve-refusal branch as support; the amended test retains that refusal.
Black initially reported formatting differences; all formatting corrections used
apply_patch, then checks passed.

Native parser review found the int overflow mismatch. Host RED `BeiMyq`: 14/15
passed; Python RED `cKxksI`: 10/11 passed. Host had incorrectly created a job for
2147483648 slots. That failed test also produced post-cleanup ENOENT noise; the
task fixture now drains any incorrectly admitted job before deleting its own files.
Both sides now follow the native checked-int range. A final constructor-side-effect
RED `btWjd5`: 10/11 passed; a binary changed after probing reached orphan cleanup
before the existing final digest check. The additional early memory digest check
closes that side-effect gap while retaining the immediate pre-spawn check.

## Final verification

Read-only tools: Node **24.22.2** at
`C:/Users/downl/AppData/Local/Programs/Strata/node/node.exe`; uv at
`C:/Users/downl/.local/bin/uv.exe`, selected installed Python **3.12.10**. No applicable
project pyproject/uv.lock/.python-version exists; requirements specify Python 3.10+.
uv runs offline with no dependency installation. Two pre-existing dangling Python
dist-info warnings remain informational and were not altered.

Host final CPU command (workspace root, `node` denotes the private binary above):

```text
node _docs/hybrid-intake-tests.mjs q36-memory.test.mjs q36-capabilities.test.mjs q36-run-contract.test.mjs q36-kv-layout.test.mjs q36-private-cache.test.mjs q36-load-lifecycle.test.mjs q36-progress.test.mjs native-serving-policy.test.mjs native-settings.test.mjs native-settings-file.test.mjs native-settings-response.test.mjs native-control.test.mjs run-config-check.test.mjs native-config-persistence.test.mjs native-installed-kv.test.mjs native-load-cancel.test.mjs native-ds-parallel.test.mjs native-ds-args.test.mjs native-onboarding.test.mjs
```

PASS **160/160**, zero failed/skipped/cancelled, 15.028 s; scratch
`strata-hybrid-96syRf`. Covers known invalid save/load before side effects, retained
ready model, changed executable, exact canonical runtime identity, private-cache
forwarding, cancel ownership, captured-file races, persistence and legacy flags.

Mounted production UI: **19/19 PASS**, zero page exceptions, in
`strata-hybrid-FZxRAF` using the same isolated runner with
`native-ui-ownership.test.mjs`. Actual experimental option, PATCH payload, future
choice versus actual metric, error-instance invalidation and inherited request
ownership checks pass. These are controlled component tests, not real Host E2E.

Final Python command:

```text
node _docs/gui-consistency-python-tests.mjs serve/test_q36_memory_contract.py serve/test_q36_kv_contract.py serve/test_native_family.py serve/test_control_cancel.py
```

PASS **42/42**, no skips, 61.73 s; scratch `strata-gui-python-z8u24j`. Eleven memory
tests, ten existing KV tests, nineteen family/admission tests and two cancel tests.
The actual constructor executes with captured fake pipes; no native process/GPU.
Focused final total: **221 passing tests** (160 Host + 19 UI + 42 Python).

`node node_modules/typescript/bin/tsc --noEmit` in `apps/host`: PASS. Through the
explicit uv `run --no-project --offline --python <installed Python> python -B`:
`-m black --check --diff serve/native_family.py serve/test_q36_memory_contract.py`,
`-m flake8 --isolated --max-line-length=88` on those two files, and
`-m flake8 --isolated --select=E9,F63,F7,F82 serve/server.py serve/test_q36_kv_contract.py`:
PASS. Large inherited Python files use critical lint, not unrelated reformatting.
`git diff --check`: PASS; Git emits informational CRLF conversion notices.

Broader locale check in `FZxRAF`: **4/5 passed, 1 failed**. Five inherited unregistered
strings remain: NativeModels' FP16 hint; NativeSettings' unavailable-capability text
and Clear; ModelRun's Refresh hardware and cached-topology notice. They were present
before this unit. The new memory catalogs are covered by the passing focused test;
no new missing key is reported. This is an explicit remaining integration issue,
not a green all-GUI/all-locale claim.

## Self-review / handoff limits

Self-review-event: `ticket_completed`, `qa_defect`, `local_fix`; review-only. Evidence
is the RED/GREEN sequence, overflow/parser mismatch, actual pre-READY checks and
orphan-cleanup ordering above. Prevention stays in focused production-boundary and
cross-language tests. Rejected: granting memory capability from version/model names,
relaxing KV schemas/private cache, total-memory claims, weakening tests, changing
native guards, or updating broad governance. No AGENTS/SOP/skill changes.

Remaining: independent parent review; actual rebuilt native INFO integration and
desktop/Host E2E; responsive/accessibility screenshots; parent-owned resource-guard
and other native qualification outcomes; the five inherited locale keys. Full
suites, native build/model/GPU operation, install/overwrite, global/private profile
changes, stop, push/tag/release are NOT_RUN in this lane. No source-only result here
qualifies 32 GB RAM / 16 GB VRAM, full-window generation or model quality. Parent
qualifies the exact binary, then decides personal packaging/overwrite.
