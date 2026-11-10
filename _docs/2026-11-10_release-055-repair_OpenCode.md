# Release repair: CUDA resources, Prism lifecycle, agent chat and sidebar CRUD

Status: INSTALLED_PREVIEW_PUBLISHED_AND_VERIFIED. Agent: OpenCode. User requests resolution of the published
preview's12 resource violations/releaseQualified=false/Prism timeout and a new
distribution installer. The supplied screenshot adds actual interrupted local
agent chat. User subsequently selected all four sidebar improvements: chat/folder
organization, real-file CRUD, discoverable actions, deletion/recovery.

## Requirements and acceptance

R1: Fix the12 measured CUDA findings without increasing ALLOWED, excluding
configurations, injecting a passing baseline or lowering resource floors.
Inspect complete affected objects and final libraries; require numerical parity.
R2: Diagnose Prism pre-readiness noncompletion and fix evidenced lifecycle faults.
Keep strict HTTP/JSON readiness; an unchanged successful rerun is not a repair.
R3: Reproduce and repair the installed local-agent exception and require an
actual agent-path request in subsequent installed acceptance.
R4: Workspace/chat actions must be visible and keyboard accessible; keep scope,
stale revisions, reversible file trash and unsaved drafts. Provide creation,
renaming, moving/organization and persistent recovery through explicit menus.
R5: New native/app source and binaries get new identities and source-bound
checks, including actual installed UI/model tests before publishing an installer.
Older releases/assets, models, user files, failed evidence and frozen sources stay.

Primary source starts at c1ceee69e4d5d9e65f9a62b0a8ff10f8b93b3d4c, clean main.
The previous release v0.5.4-local.1 stays fixed at cff2f050; its app source85a78234
and native source7bb24974 remain historical. Candidate version planned0.5.5-local.1,
Control0.5.6/native0.5.5, to be finalized only with fresh artifacts.
New outputs use H:/Strata/releases/repair-055-20261110-opencode. Compiler jobs5;
RAM3GiB/commit4GiB/C5GiB/H10GiB floors, deadlines and owned/drained Jobs retained.
No currently running user model is implicitly stopped by read-only diagnosis.

## Applicable standards and design

Compatible canonical pre-implementation prompt and PC/project AGENTS; Common,
Start Gate, Skill Selection, Security, Application, LLMOps, WebApp, Frontend,
Python, TypeScript, CPP and Rust SOPs as their surfaces are touched. Existing
milspec/deepresearch baseline; systematic-debugging and test-driven-development.
Systematic-debugging explicitly authorizes delegated investigations; two read-only
investigations were scoped separately to Prism and CUDA. Implementation remains
owned here. No Goal API is exposed; objective and task list track this work.

docs/DESIGN.md concerns landing/documentation; the desktop's existing semantic
--st-* tokens/components/FloatingMenu/Dialog are the UI authority. Sidebar changes
will reuse them, keep compact/mobile support and retain supporter/public docs.
No unrelated redesign or new palette/dependency is needed.

## Observed causes and unknowns

Installed desktop-20261109-225342.log repeatedly records TypeError at
runAgentTurn/index.mjs:663: instance.gpus.map. The Prism supervisor fallback row
from supervisorLocalInstance has modelId but no apiModelId/gpus, unlike native
rows. The exception occurs before the function's try/error-frame boundary. This
directly explains the screenshot's empty interrupted agent stream. Existing
installed acceptance covered plain chat, not this supervisor-backed agent branch.

Prism r1 reached34/34 GPU layers,98304 context/Q8KV, then last logged warm-up;
the Host's120s health deadline terminated it after122.512s launch-to-exit.
The initial warm-up decode, later sequence-removal decode and transport are not
distinguished by available logs. Passing r2 has no persisted success timeline.
Confirmed diagnostic gaps: dropped health-probe details, QA not failing fast on
terminal error, and weak stopped-state teardown checks. Root backend stall is
not yet proven; blanket timeout increases/no-warmup/precision changes are rejected.

CUDA current objects match the12 failures. These are PTXAS register spills, not
addressable PTX arrays: EXPDEC64regs/152stack, DFlash80regs/24or16stack,
QSA64regs/96stack, W4A8 eight entries255regs/32..48stack. Preserved earlier
experiments at H:/Strata/validation/cuda-resource-20261109 show scoped DFlash
scale-lifetime candidate B removes only its two spills; broad candidate A creates
new ones. Fully unrolled EXPDEC row restructuring and QSA radix unrolling regressed.
New EXPDEC pair/immediate-store, QSA bounded counters and W4A8 shortened scale
lifetimes are hypotheses requiring compilation and parity, not claimed fixes.

## Verification and changes

Pending test-first regressions, implementation, diagnostics and new builds.
Read-only investigation used actual installed log, immutable native spill receipt,
source/readiness/agent/workspace contracts and existing compiler experiments.
The guard/helper inputs, source snapshots, commands/results and failed attempts
will be retained under the new H: root; source log records actual outcomes.

Agent regression RED: the new supervisor route/serving contract test reproduced
the exact undefined.map exception (4passed/1failed), under a drained owned Job.
An earlier attempt was refused before launch because available RAM was below3GiB;
that admission failure is retained. User then explicitly approved normal model
unload. By inspection the model/shell were already absent, and the previous Host
port was closed; no absent process was claimed stopped. Fresh admission had
21GB available RAM. The minimal route fix supplies apiModelId and an empty GPU
attribution array rather than falsely assuming GPU0 for every supervisor model.

## Residual risks / next action

The existing public preview's qualification remains false. Screenshot agent
failure is now explained by observed source/log correspondence. Prism backend
noncompletion and native resource candidates remain unresolved. Implement the
reproduced agent boundary regression first, then bounded kernel/compiler and
lifecycle evidence; improve sidebar through real desktop/mobile browser checks.

## Handover intake and independent corrections

Read the complete164-line user-supplied
2026-11-10_cuda13-98k-handover_Antigravity-to-Sol61.md. Preserve that intake;
its recommendations are hypotheses, not a measured optimizer implementation.
The current source/receipts establish several corrections before reuse:

- The failing installed Prism model was DeepSeek-V4-Pro-Qwen3.5-9B heretic,
  SHA8cf793a3..., not the21.28GiB Qwen3.6 model named in intake§4.1. It used
  Q8/Q8. A cold19GiB Qwen3.6 mmap explanation is not evidenced for that failure.
- Production readiness lives in apps/host/server/supervisor.mjs/waitForHealth,
  not the intake's apps/host/src/supervisor/runner.mjs/probeOpenAiReady path.
  Launch-to-forced-exit122.512s is not a measured eventual completion at122.512s.
- 402653184 bytes is384MiB /402.65MB; the intake mixes MB/MiB in its scratch
  and KV estimates. Per-step traffic and output equality require real tracing,
  parity and A/B measurements before any performance claim.
- Native QSA register top-k launches1024 threads, not256 with minblocks4.
  W4A8 uses pipelined MMA, not the intake's DP4A_ROWS design description.
  Shared-memory substitutions can exceed the target's capacity and need review.
- The geometry/model paths and asymmetric-KV dispatch lead are useful separate
  investigation inputs. They do not qualify a new98K model/backend path or prove
  a cause for the retained Q8/Q8 startup timeout. Keep unchanged numerical/default
  behavior until candidate-specific evidence exists.

## Repair verification progress

Agent route regression GREEN passed5/5 after the observed RED. Source-browser
RED1 failed before UI due OS-profile variables being passed to Edge; the fixture
now captures the sanitized browser environment before applying its isolated Host
profile (explicit private browser data directory retained). RED2 then reached
the real UI and failed on the absent workspace action menu, as required.
Trash-history HTTP regression RED reproduced405; implementation GREEN passed
all10 existing workspace tests, including Windows DACL/ADS, stale save, linked
paths, collisions, pagination and registered/origin scope. Fresh typecheck passed.

Native diagnostic run completed360.130s, drained, zero active children. Complete
EXPDEC and DFlash object guards passed; QSA narrowed counters regressed STACK96
to104 (allowance88), and the initial W4A8 negative-magic scale lifetime change
left all8 violations unchanged. Those two hypotheses are rejected, not success.
No runtime numerical parity, library-level gate or release binding has run yet.

QSA second candidate keeps64-bit indexing and moves only three tail keys to
per-thread shared slots beside its histogram (within48KiB; HIP path retains its
original storage). Complete35-entry object guard passed. W4A8 second candidate
on-use shared scale loads left the eight resource results unchanged; preserved
its source/result/prior object under object-attempts/w4a8/r2. That scale change
was rejected. The next bounded-lifetime design retains all CTA configurations
but computes at most64 tokens per complete K traversal, followed by a synchronized
second pass for the remaining tokens. Arithmetic/dispatch coverage is retained;
its extra weight reads may affect opt-in performance and need measurement.

Sidebar source browser GREEN3 passed6 behavioral checks,0 page errors: visible
keyboard workspace menu/new chat, file edit and breakpoint draft retention, move
without byte loss, persistent trash restore after reload, archive/restore after
reload, Japanese mobile menu/Escape/no overflow. Earlier green-attempt failures
were fixture selection of the task-board row and reading disk before async
restore completion; waits now follow visible completion. Failed fixtures remain.
New20 UI keys were translated in all9 catalogs; dedicated scope/move coverage
and screenshot review remain to be completed before installed acceptance.

W4A8 third candidate passed the complete8-entry object guard. All four repaired
objects now pass unchanged allowances, but GPU/library/final binary acceptance
is still separate. Diagnostic numerical targets rearchived/rebuilt with5 jobs
in424.971s (no clean), under retained floors; this is not a release-source bind.

Prism baseline trace used the original120s budget, real0.4.1 runtime, exact9B
GGUF and unchanged98K Q8/Q8 settings. Current measured driver is621.14, so older
621.01 results are not a same-day hardware baseline. Startup reached healthy in
19.673s and independent probes captured503 Loading model ->200/ok. The diagnostic
then failed its arithmetic assertion because its direct request omitted the
original GUI fixture's thinking-Off choice and exhausted its32-token allowance.
That failed attempt remains failed; readiness timeout was not reproduced. The
next diagnostic explicitly uses thinking Off while retaining prompt/KV/context/
token budget and strict readiness. Success and failure traces/stop checks are kept.

## Updated numerical and lifecycle evidence

Serial GPU acceptance r2 passed21 checks: final diagnostic-library spill guard,
EXPDOWN R4/T1–T4 bit equality, grouped experts, all64 DFlash column/shape cases
for variants17/18/21 and equal raw outputs, QSA selftest/135160-cell boundary/
active bounds, all4 W4A8 configurations with old/new same-day runs and2049-token
wide-scale tails. Both IQ4_XS/IQ4_NL kernels executed. This build has no pointer-
table MMQ, so that layout is not claimed. Initial wrapper r1 falsely matched
DIFFERENT in a comment header; its raw numerical subprocess passed. The corrected
parser still rejects every real failure/skip/nonzero exit and requires route coverage.

Actual DFlash SASS instruction-byte comparison:83 kernels; only the intended two
changed,81 including the default matched. Evidence dflash-default-sass.json.
The official-PR candidate assessment and two-file minimal patch are separate
from this fork release; official current source/duplicates were inspected. No PR
was created. See2026-11-10_upstream-minimal-candidates_OpenCode.md.

W4A8 raw old/new timings include slower cases: config0/uniform down kernel2.668
->3.364ms in this single pair. Other rows vary; no statistical/general speedup
or changed default is claimed. The mode remains opt-in. Preserve individual logs.

Prism original-contract trace r2 passed3 actual starts/answers/stops at5979,
5734,5690ms total start call, driver621.14. Historical warm-up timeout remains
unreproduced and its backend cause unconfirmed. A separate deterministic test
reproduced premature stopped status after SIGKILL request but before child exit.
Stop now awaits actual exit, retains ownership on failure, and checks replacement
identity. RED and GREEN receipts remain. Another test reproduced ready/running
publication after the probed child exited; readiness now checks liveness before
acceptance. Timeout diagnostics distinguish safe HTTP503/loading labels from
connection silence, deduplicated without raw body/secret text. Original120s
startup budget and exact HTTP-plus-JSON readiness criterion remain unchanged.
The focused stop/health/startup/diagnostic group passed. Real candidate-source
Prism trace candidate-r1 also passed3 starts/answers/stops; it is not installer QA.

Focused Host group had31 pass plus one cwd-sensitive catalog fixture failure;
with the normal host cwd, catalog behavior5 passed and the known six-language
56-key coverage gap still failed. Independent exact c1ceee69 delta check passed:
all20 new keys translated in all9 catalogs, interpolation preserved, no new
missing keys. The baseline test was not weakened. Existing localization debt
is still recorded as failed. Local QA notes explain fixture/contract corrections.

Expanded sidebar source browser GREEN5 passed10 checks,0 page errors, including
file/folder creation+selection/rename, workspace display rename, durable chat/agent
folder movement and remove/re-register recovery, plus Japanese mobile. GREEN4's
only failure was the fixture assuming201 for workspace registration; the actual
existing contract is200 and the corrected test asserts that exact status.

Candidate source versions are now product0.5.5-local.1, Control0.5.6/native0.5.5.
Metal and dependency versions remain independent. Version sources were patched
explicitly, public0.5.4 download URLs retained, and README development banners
distinguish the pending installer. AGENTS changed only artifact-status/version
metadata; concurrency/floors/preservation policies remain unchanged. Product
consistency check passed. The first owned Python version run failed because it
used the H: output cwd without the checkout import path; a source-cwd driver
will rerun it without changing test expectations or source runtime behavior.
No final055 native/app/installer artifact is built or accepted yet.

User selected distribution build/actual-machine verification as the next priority,
rather than creating an official PR. Candidate patch/research remain saved only.
Corrected source-cwd version run passed6 tests; candidate typecheck and product
consistency passed. Source-browser GREEN5 passed10 checks and0 page errors.
Prototype native cache was copied in full to native-diagnostic-pre055 with
complete before/copy/source-after hash agreement. All failed and passing
intermediate receipts remain. The original user-supplied handover is preserved
byte-for-byte in intake/ with an independent SHA receipt and retained verbatim
as unverified background; the corrections above govern this task's claims.

Source checkpoint will include the reviewed repairs, candidate versions, scripts,
logs and this intake; no model/runtime/private payload. New final build evidence
requires a clean detached055 source freeze and new final-version native identity.

Final source-browser check after candidate version metadata and review cleanup
passed10 checks/0 page errors. Review narrowed visible-chat CSS to workspace
groups so task-tree rows keep their own layout, and removed an unreachable
unused-workspace expression introduced by boolean action results. Script flake8
E9/F found one unused sys import; removed, recheck required. Candidate version6
tests, product consistency and typecheck passed. These remain source checks.

## Final native source-bound acceptance

Checkpoint b995af139cc823537489b886bc1e8602cf10301c was frozen clean at
H:/Strata/worktrees/native-055-source-20261110. Every tracked physical file was
compared with the primary checkout; newline normalization preserved the Git tree.
The diagnostic cache was retained independently before final-version compilation.
The production native helper completed the incremental five-job build in
1233.308 seconds, including source binding. The outer owned Job finished with
zero active children, zero dropped output and unchanged resource floors. Its
minimum sampled available RAM was15625838592 bytes. Copied-cache MSB8028 and
CUDA-header codepage warnings remain in the complete build log; no clean was run.

Final native version0.5.5 binds779 native sources, portable sm_120, Spin8 ON and
ggml3cf03257. No explicit CUDA spill baseline was configured. Artifact identities:

- strata.exe:659607ec2d7c19c65633e4b0e3bad5e0bdf30448f2092ca33cb2d4e1413b6256
- strata-q36.exe:1af1cd06e4158bcf1b6048ea8f4c6dbae29247355f42e30a4330fc6ca638b16c
- native-build.json:80fc22aba3238227505a4253bbfc3ee22222eebd2b5597f2c1c03b26fa49f0b1

Explicit native adapter phases stage/cpu/gpu/sanitizer/spill/model-bounded/
model-legacy7/model-restart/compare/audit all passed and drained. The unchanged
cuda_spill_guard passed on final libraries: the earlier12 findings are absent.
Both memchecks require their actual ERROR SUMMARY:0 errors. Protected real Q36
model/pack/tokenizer snapshots matched before and after all three model phases.
Seven bounded and seven legacy requests matched token/protocol results, including
owner separation, missing owner, cancellation and clearing; two restart requests
also passed. These are short requests with4096-cell capacity, not a full-window
or general-quality benchmark. Phase elapsed times include complete input hashing
and must not be presented as startup or generation timings.

gpu.py gained explicit --final-source-commit admission: successful frozen build
receipt, production binary/source binding, and before/after hashes of tested
libraries and executables are required. Its fresh final-r1 passed all21 numerical
checks, retaining same-day old/new W4A8 timings and DFlash byte equality. This
result is gpu-final-results-final-r1.json; earlier diagnostic reports stay intact.
The final qualification summary still carries releaseQualified=false because
app/installer/installed acceptance and broader quality scope remain separate.

## Delivery preparation and app admission checkpoint

delivery.py prepares version/path-adjusted adapters in fresh revision roots and
records every template/output SHA. Older054 templates, delivery revisions and
artifacts are retained. The new component validator requires a genuinely passing
unchanged resource guard plus all21 source-bound final numerical checks; it still
validates the full protected model/functional/Job contracts. No historical PASS
receipt is copied into a new attempt, and no releaseQualified flag is promoted.

repair-qa.py extends the packaged Prism recipe without removing its two plain
answers: two additional UI messages must emit actual Harness agent start/done
frames, have no fallback/error/demo and return a real answer. Both shell cycles
require normal close and process-absence checks. upgrade acceptance requires this
positive agent/teardown evidence. Workspace selectors follow the visible action
menus and folder auto-entry behavior. Generated recipe syntax, four candidate/
installed QA recipes and eleven read-only phase plans passed. The component
validator independently accepted the completed final native reports in
validate-delivery-r3. Actual packaged/installed GUI execution remains pending.

The exact final strata.exe digest was added to q36-run-contract.mjs only after
the native checks. Expected allowlist test RED reproduced the missing digest;
GREEN passed the13 contract and5 local-agent tests, retaining unknown-digest
rejection and legacy default behavior. The next app/Control build needs a clean
reviewed source checkpoint containing this admission and its QA recipes.

Commands used uv/offline Python3.12 with the owned run.py wrapper, explicit native
adapter run phases, gpu.py --attempt final-r1 --final-source-commit b995af13(full),
delivery.py --execute, validate-delivery.py --native and node --test for the two
focused Host files. All commands and process/resource receipts are under the055
H: root. validate-delivery-r1 failed an incorrect NODE import before any recipe
ran; r2 fixed the helper import and passed. r3 additionally validates final native
evidence. The failing attempt is preserved; expectations were not weakened.

Self-review-event:qa_defect. Evidence: old installer QA bypassed the agent branch,
and the new validation helper had an import error. Response: positive agent-frame
and teardown assertions, generated-plan/syntax checks, explicit final-binary
admission, and narrow QA notes. Rejected alternatives: treating plain chat as
agent evidence, reusing diagnostic PASS, accepting resource failure for055, or
changing global governance. Residual risks: new installer/installed flows not yet
run; old Prism timeout cause remains unconfirmed; W4A8 slower cases and absent
pointer-table/HIP/full-window/general-quality coverage remain as documented.

User explicitly approved creating the local app-source checkpoint and continuing
the installer build. Fresh git diff --check and helper flake8 --select=E9,F
passed. Commit scope is the two admission files, final GPU binding helper, three
delivery/QA preparation scripts, QA notes and this log. Push/publication is not
part of that local-commit approval. The native055 frozen source stays unchanged.
