# Resume: GUI consistency, bounded native memory, E2E and release

Date: 2026-11-07 JST. Owner: OpenCode. Status: IN_PROGRESS.

## Objective and acceptance

Continue the full inherited goal: integrate unfinished branches into main, repair
GUI/model/loading/chat contradictions, qualify native operation on this 32 GB
RAM / 16 GB VRAM PC, complete the Spin8 A–H plan, run real-machine E2E and
regressions, rebuild and overwrite-install, align installer README, then push,
tag, publish and independently verify downloads/signatures. The earlier local
0.5.2-local.1 installation is a checkpoint, not completion of this goal.
Goal API is unavailable; the conversation task list and this log retain scope.

## Starting state and maintenance authorization

Main started at 7462de07 with the final Q36 argument-refusal intake uncommitted.
GUI, bounded-native and Spin8 worktrees retained the WIP listed in the handoff.
The installed app remains 0.5.2-local.1 / Control 0.5.2 / signed native 0.5.1.

At 00:49 JST, RTX 5060 Ti VRAM free was 252 MiB (99% utilization), and Windows
reported 5,259,120 KiB available physical RAM. Both Strata and Hermes owned
llama-server processes were present. No compiler process was observed.

The user explicitly approved temporarily stopping Strata/Hermes model servers
after current responses finish, testing a prepared native candidate, and restoring
the original models/settings afterward. The parent owns this maintenance window.
Do not interrupt an active response, stop processes by stale PID, change model
files or expose private command-line credentials. Record original executable,
identity/settings, readiness and restoration privately; public logs use hashes,
counts and statuses. No maintenance stop has happened in this resume yet.

## Standards and decisions

Previously read PC/project baselines, canonical preimplementation context,
Common/Start Gate/Skill Selection/Security/LLMOps/Application/WebApp/Frontend/
CPP/Python/TypeScript/Rust SOPs continue to apply. Skills: goal, MILSPEC and
research baselines, systematic-debugging, qa-engineer, subagent-driven-development
(required by the inherited plan). No formal compliance claim.

Source and real-machine gates are separate. Preserve memory/resource floors,
model/KV precision, context and router settings. Reproduce screenshot issues with
synthetic conversation content. Never publish private background imagery.

## Progress and evidence

- Rechecked status/logs of all four active worktrees and actual running app/GPU.
- Completed the main intake's final native parser commit, 08fa26df. Fresh run:
  `uv run --no-project --offline --python <Python312/python.exe> python -m pytest
  tests/qwen36/test_serve_args_cpu.py -q --basetemp=H:/Strata/validation/q36-parser-resume-20261107
  -p no:cacheprovider`: 24 passed. This compiles/executes the parser fixture only,
  not the CUDA engine. The existing Q36_CPU_COMPILE_RECEIPT selects MSVC.
- GUI worktree committed 14a07fd5: 180 controlled checks and typecheck passed.
  Independent SPEC review found two remaining E3-B gaps: invalid captured config
  can still create/persist a failed job; settings and load use different Q36
  family decisions. Fix/re-review pending. Screenshot translation/layout work is
  separate and remains unqualified.
- Native worktree committed 044722d2: bounded/store/lifetime CPU checks pass and
  three expert-format combinations are byte-identical in synthetic CPU-pool
  parity. Independent SPEC PASS. QUALITY, full source-bound build and real-model
  qualification pending.
- Spin8 constructor P1 fix now applied and source QUALITY approved: private
  upload stream is checked complete before publishing the plan. Post-fix build/
  GPU test is still pending because the GPU is occupied. Earlier passing binary
  contains the old constructor and cannot qualify the fix.

## Residuals and next actions

Finish GUI SPEC fixes, add screenshot regressions with the real translation and
rendering path, independently review source, then perform isolated real Host/UI
E2E. Review native bounded mode and freeze its source before building. Prepare
owned-process maintenance and exact restoration before stopping serving models.
Record GPU/model results with exact binary, model, effective settings and actual
input lengths. Remaining Spin8 stages and final release requirements stay open.

## Source checkpoint requested

The user subsequently requested integration into main, commit/push, a new
handoff, and removal of used worktrees after integration. This is a source
checkpoint request; the full runtime/release goal remains open.

The screenshot's untranslated speed template was reproduced with real React
rendering, the actual catalogs and numeric component. Initial regression: 1 pass,
10 failures (all eight non-English speed displays and two recovery notices).
The animated and accessible speed labels now use the same registered three-slot
template. Both persisted recovery strings have entries in all nine catalogs.
Final focused rendering/locale/error/save-notice run: 52/52 PASS; TypeScript PASS.
These are renderer/production-boundary tests, not a new installed WebView2 pass.

Native bounded source 044722d2 has independent SPEC PASS and QUALITY APPROVED.
The reviewer noted a non-sector-aligned EOF fixture coverage gap; fresh engine
build, actual CUDA transfer lifetime and same-setting real inference remain open.
Spin8's P1 constructor fix has independent source QUALITY approval, but post-fix
compile/GPU execution remains unrun. The new checkpoint must retain that limit.

Maintenance preparation produced read-only snapshots and guarded helpers, with
50 mocked tests. It performed no server stop/start or restoration. Later snapshots
observed both original servers absent, and C: free space below the unchanged 5 GiB
floor. No executable maintenance authorization or frozen candidate was fabricated.
The private snapshots remain outside Git; only reusable helpers and sanitized
documentation are checkpoint inputs.
