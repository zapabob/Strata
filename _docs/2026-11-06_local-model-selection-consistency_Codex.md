# E2 local-model selection consistency

Date: 2026-11-06 JST. Owner: Codex E2 implementation worker. Source base: `bcfe9bad9ac8b0ec8e28fd09f32a027bbfb18936`.

## Background and requirements

The real E1 browser report reproduced a Q36 URL with Hikari selected through the picker and a Hikari URL with Q36 still selected after same-document navigation and browser Forward. Restarting on the bare local-model route opened the native import picker although Q36 had been the last visible generic model. This implementation addresses route, visible identity and selected run-profile consistency only. Real E1 rerun and independent source review remain controller-owned gates.

The acceptance criteria are that explicit registered local links, same-route variant changes, picker changes and browser history converge on one identity; unknown or removed explicit IDs expose no other model's controls; the bare local route restores a valid last viewed local model without loading it; and each model keeps its own draft/default profile and backend. An empty or stale last selection retains the native entry behavior. Engine loading, generation, acquisition, native compilation, release and Hermes operations are outside this task.

## Applicable standards and decisions

Read the PC-wide and Codex-local AGENTS, canonical `C:/Users/downl/_docs/prompts/CLAUDE-FABLE-5.md`, worktree AGENTS, the Common, Implementation Start Gate, Skill Selection, Security, WebApp Development, Frontend Design and TypeScript SOPs. Applied `milspec-codex-standard`, `incremental-implementation`, `frontend-ui-engineering` and completion `agent-self-review-evolution`. Reviewed the existing Host README, repository README/SECURITY, design-system notes and interaction guidelines. No design tokens, dependencies, lockfiles or visual styles changed.

The last viewed local identity belongs in the existing browser persistence boundary, beside the already browser-persisted run profiles. It is independent of Host registry current, actual loaded engine and applied engine configuration. No Host selection endpoint or duplicate server selection store was added. Browser persistence remains origin/profile-specific; clearing or blocking that storage prevents durable restoration. The pre-existing session variant is used for migration and draft ownership, with registry validation before a bare-route restore.

## Changed files and implementation

`apps/host/src/lib/run-selection.ts` defines validated local-route precedence and storage helpers, and extracts the actual model settings restoration used by the screen. Explicit ID wins over saved local identity. Until the registry is available the decision is waiting. A missing explicit local ID yields a missing decision; stale saved IDs yield no selection. Settings restoration uses exact variant and hardware profile ownership, clones saved settings, preserves invalid JSON drafts for correction, and retains the existing local context recommendation and backend resolution rules.

`apps/host/src/screens/ModelRun.tsx` subscribes to hash routing rather than consuming an initial variant once. URL changes call the same chooseModel transition used by the picker. Picker/import/family actions update the URL. While an explicit route is unresolved or its profile is being switched, another model's editable controls and validation/placement reads are withheld. Unknown IDs render the existing Choose an installed model error and Back action. Model draft snapshots are keyed by variant ID instead of only by family, so Q36 and Hikari can retain independent unsaved drafts although both are Local models. A draft belonging to a removed prior session identity is retained under that identity rather than attached to the explicit target. Import backend hints are scoped to the imported identity, while quant metadata still resolves PrismML/TurboQuant as before. No quantisation, KV precision or model metadata is inferred from filenames or rewritten.

`apps/host/src/lib/router.ts` adds replaceRoute, using replaceState and a routing notification to canonicalise the restored bare local route without creating a browser Back/Forward loop. Existing query values, including the Settings overlay, are preserved by the caller.

`apps/host/tests/run-selection.test.mjs` executes the actual TypeScript helpers through the existing esbuild dependency. It covers registry readiness, explicit precedence, unknown/empty/removed/nonlocal IDs, durable selection across a new browser session store, native/session separation, route replacement notification without repeated history entries, Q36/Hikari settings and backend identity, same-family unsaved and invalid drafts, and cross-model/cross-hardware default rejection. These are behavioral helper tests; they do not pretend to be React/browser E2E.

## Commands and verification

`npm run typecheck` in apps/host: PASSED, TypeScript `tsc --noEmit`.

`node --test tests/run-selection.test.mjs tests/model-run.test.mjs tests/strata-engine-backend.test.mjs tests/router-view-transition.test.mjs`: PASSED, 19/19, zero failed/skipped/cancelled. The final successful run completed after the initialization/draft-ownership changes. An earlier helper slice passed 5/5 and the first integrated run passed 17/17 before the persistence/history cases were added.

`git diff --check`: PASSED before handoff.

An extra run also included the pre-existing `tests/tune-and-timeskip-routes.test.mjs`. The combined run reported 26 tests, 21 passed and 5 failed in approximately 90.4 seconds. The five failures were all `Error: the host did not become healthy` from fixture startHost at line 65; they were the unavailable-engine, stub-engine plan, missing-plan-input, unknown-job and arbitrary-revision-command cases. The two Time-skip list/refusal cases passed. This result is retained separately; tuning was not modified, and the failure was not attributed to an established baseline without a baseline run. No further tuning investigation or repeat run was performed.

The extra fixture explicitly set unique Temp/strata-tune-routes-* STRATA_HOME and STRATA_TIMESKIP_DIR plus STRATA_REAL_ENGINE=0. It did not isolate LOCALAPPDATA, components or the default Workspace, so fully isolated initialization and zero live-profile side effects are NOT claimed. No STRATA override variables were present in the inherited worker shell for the inspected home/settings/components/runtime/control/workspace/real-engine names. Current read-only findControl inspection returned false. Read-only filesystem metadata inspection after the run found no files modified since the pre-run 12:35 JST boundary beneath LocalAppData/Strata or Documents/Strata/Workspace; the live app-settings timestamp was 12:04 JST, components directory 09:25 JST and Workspace directory 2026-10-21. This is metadata evidence rather than before/after content hashing. The stub-engine plan test failed before reaching its POST, and none of the fixture test bodies call a model-load endpoint. These facts are not a general proof about every startup side effect.

The extra fixture kills each directly spawned Host in its own failure/finally paths. After completion, a Win32_Process audit matched the exact fixture Host script paths and the exact tuning test runner filename and found no remaining process; all other Node/Hermes processes were left untouched. Historical fixture child PIDs were not exposed by that harness and are not invented here. The implementation worker started no GUI browser or engine process.

## Residual risk, rollback and handoff

Real React/Host/Edge E1 rerun: NOT_RUN by this worker; the controller schedules it after source review. Real engine load, native inference, CUDA/GPU work, HMD, packaged candidate, source production build, whole Host suite, localization suite and visual/responsive qualification: NOT_RUN for this source-only task. No native inference or product readiness claim follows from the helper tests. The existing E1 report/trace remains reproduction evidence, not post-fix evidence.

A distinct pre-existing asynchronous profile-save/navigation ownership concern was noticed statically: storeProfile validates an identity asynchronously and later updates activeProfile without a navigation identity guard. It was not reproduced and is not expanded into this task. Broader capability/error-state E3 work remains separate.

Rollback consists of reverting the scoped E2 source/log commit. The new browser key can remain inert after rollback. No registry migrations, models, engine settings or saved profile schema were changed. Preserve the unrelated `_docs/evidence/`, `_scratch/`, QA artifacts and frozen CUDA worktree/build.

Self-review-event: ticket_completed, review-only. Verified scoped ownership and actual behavioral-helper coverage; the adjacent fixture exposed a QA isolation limitation, recorded above without weakening the gate or modifying governance. The existing E2 brief already requires the real no-load E1 browser rerun. No AGENTS, skill, SOP or automation edit is warranted from this single event.
