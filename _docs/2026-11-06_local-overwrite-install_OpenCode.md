# Local overwrite installation — 2026-11-06

Status: IN_PROGRESS. Owner: OpenCode. Scope: local installation only.

## Requirements and plan

Build integrated main (initial clean commit `1c521fba`) as app `0.5.2-local.1`,
Control `0.5.2`. Retain signed native `0.5.1` executable SHA-256
`e75716a9d5deb6289e87741d42e7003ba82b7696f6121d5203e615d9fe596a96`.
Do not build/activate a new native engine or claim Spin8 CUDA qualification.
No release, tag or push. Preserve sibling worktrees and original untracked work.

1. Bind the independent native source explicitly and test rejection paths.
2. Freeze the app/Control source, stage verified resources, build with pinned dependencies.
3. Verify exact NSIS payload, 13 production self-tests and isolated actual WebView2 navigation/metadata.
4. Back up small user state privately; run one bounded NSIS `/S /D=C:\Users\downl\AppData\Local\Programs\Strata`.
5. Compare installed payload and prelaunch user hashes; verify normal manual-unloaded startup, versions, settings, shortcuts and registrations; leave the app open safely.

Acceptance requires fresh evidence for each step. Goal API is unavailable; this
log tracks the local-install objective. Completion does not complete the parent
Spin8 A–H/publication goal.

## Standards and decisions

Applied supplied home/project AGENTS, compatible canonical preimplementation
context, MILSPEC/deep-research baseline skills, plan-mode, Common, Start Gate,
Skill Selection, Security, Application Development, WebApp, Frontend Design,
TypeScript, Python and Rust SOPs. Existing source, lock files, design authority,
security docs and prior scripts are the primary local evidence. No new dependency
versions or external package-trust claims. No subdelegation or formal compliance claim.

Default native source verification remains strict. Explicit source root requires
full source commit and exact manifest digest, original native source/baseline and
binary checks, a clean relevant checkout and signature verification with built-in
keys. Frozen reference: `c50ca06a863a98ff121cbff30365a035a90205e2` at
`H:/Strata/worktrees/upstream-0211-latest-20261105`. Native build identity remains
the existing `00ce436f69a9-dirty-hakua-runtimes-v1`, not main.
The historical staging manifest is unsigned; use the retained signed component
instead and compare payload hashes. Its native record has no spill baseline;
test optional-baseline rejection without inventing one for the historical build.

Resource floors: H >=10 GiB, C >=5 GiB, available RAM >=3 GiB and commit >=4 GiB.
Builds use Node 24.22.2, 1024 MiB Node heap, Cargo jobs=1, owned process containment
and timeouts. No unrelated process stops. Personal data and screenshots stay
outside checkout; public evidence contains counts, hashes, versions and booleans.

## Changed files

Product manifests/locks/constants, CONTROL_VERSION, version banner and local
candidate note; packaging README; native source verifier and focused regressions.
Owned build/qualification/install helpers and evidence are recorded below.

## Commands and results

Initial `git status --short --branch`, `git diff --stat`, `git log --oneline -10`:
clean main at `1c521fba`, ahead 26. Frozen worktree HEAD matches c50ca06a; only its
existing untracked evidence is present. Resource preflight: H 323.69 GiB, C 13.67
GiB, available RAM 7.51 GiB, available commit 12.41 GiB; no Strata shell running.

## Residuals / next action

Prebuild gates: release-integrity Node tests 5/5 PASS, including native binding
default drift, partial option, commit/manifest, source, spill-baseline and binary
rejection. `tools/bump_hakua_product_version.py --check`: PASS. Host TypeScript
`tsc --noEmit`: PASS. `git diff --check`: PASS. Desktop locked offline npm install
failed ENOTCACHED for Tauri CLI 2.12.3; normal `npm ci --ignore-scripts --no-audit
--no-fund` installed the same two locked packages, exit 0, with no dependency changes.
Staging guard passed in 176.110 seconds: 23,414 Harness files, 97 notices, 3 Node
files, 38 backend files and 139 signed component files, full source/destination
hash comparisons. Retained signed component also exactly matches the installed
component. Manifest SHA-256:
`7eadce5bd58f5ffe642be86d9ff06c775de3129ebd16fa35520bed31f46882aa`.
Evidence lives in `H:/Strata/releases/local-052-20261106-opencode`.

Self-review-event: qa_defect (offline cache miss). Review-only: no governance
change; retain locked normal installation fallback and log the real failure.
Existing old staging is only a read-only resource donor. The native record has
no baseline; no baseline receipt was manufactured.

Build, qualification and installation pending. Public release remains 0.5.1.
Local candidate is code-unsigned; native GPU/model behavior is outside this unit.
