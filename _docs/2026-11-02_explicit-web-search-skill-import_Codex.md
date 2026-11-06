# Explicit web search and SKILL.md import implementation

Date: 2026-11-02 JST. Workspace: `C:\Users\downl\.codex\worktrees\strata-16gb-observations\Strata`. Base: `e591c654cb8f2b2516878d4941be5a1da43d0c9a`; branch: `codex/strata-web-skills-20261102`.

## Requirements and boundaries

The parent-approved `task-ux-brief.md` governs this work. Web search must be explicit and usable as reference snippets in plain chat, including external Hikari, without enabling the full Harness. SKILL.md import must preview bounded instructions before creating a skill, preserve scope and enable choice, and explain resource compatibility. API-key save feedback must reflect the actual PUT outcome. Existing full-agent search remains unchanged.

No installed-app files, user profiles, GPU model lifecycle, release, push or merge were changed by this worker. Parent owns live search/Hikari E2E and performance qualification. All integration inference uses a loopback synthetic API clearly identified as a mock.

## Applicable standards and decisions

Read PC and Codex AGENTS, project AGENTS, canonical `C:\Users\downl\_docs\prompts\CLAUDE-FABLE-5.md`, Common Engineering, Implementation Start Gate, Skill Selection, Security, WebApp Development, Frontend Design and TypeScript SOPs. Applied `milspec-codex-standard` and `frontend-ui-engineering`; read the app's `design-system-notes.md` and `interaction-guidelines.md`. No dependency was added. Formal MILSPEC compliance is not claimed.

The existing Host has local Origin checks, not authenticated user principals. New controls require matching local Host/Origin and loopback transport. The resultId is a 192-bit opaque capability bound to the chat routing sessionId. A chat ID is not authentication. Records are never listed and are not persisted. Results live for five minutes, at most 32 records per Host; a search returns at most five public HTTP(S) links. Search is built-in DuckDuckGo/Bing only; an explicitly configured different provider gets a settings action rather than silent substitution.

The provider factory is created once per Host to preserve its existing pacer/cache/cooldown. Its fetch is restricted to fixed HTTPS search endpoints and a maximum of three permitted redirects. HTML is bounded to 1 MiB. Only the separate user-entered query is used, at most 400 characters. No result page fetch was introduced. Provider exceptions are replaced by plain errors without echoed queries or credentials.

Search references are appended as a separate user context message using the server record. Skill matching uses only the original question, before references are attached. The attachment turn bypasses Harness and disables native/worker MCP tools without changing saved preferences. Plain remote-model chat carries the same separate reference context. Snippets are never put in the system role. This limits execution exposure; it is not a claim that prompt injection or model factual errors are solved.

## Changed surfaces

Search: `server/chat-web-search.mjs`, route/inference wiring in `server/index.mjs` and `server/inference.mjs`, `WebSearchDialog.tsx`, Chat actions and slash hint, client cancellation, message options/types, source link display and composer wrapping CSS. English/Japanese strings use the existing catalogs. Search dialogs open with a blank query. Search starts only on explicit Search. Use results in question attaches for the next answer. Close, Stop, navigation and late replies cannot attach a result.

SKILL.md: `server/skill-import.mjs`, read-only preview route and existing create route, `SkillImportDialog.tsx`, Skills screen, scope persistence and Japanese labels. The file/paste input is limited to 64 KiB; parsed instructions are limited to 40000 characters and rejected rather than truncated. `parseSkillFile` now restricts field-prefix whitespace to horizontal space so an empty name cannot consume the next metadata line. Import requires confirmation, defaults disabled, rejects duplicate names and supports editable triggers/scope. It imports instructions only; scripts, references and dependencies are not copied or executed. Existing folder import remains available as From folder.

SettingsTools: API-keyless search and keyed fallback are described. Key save awaits the PUT. Failed save retains the input and displays its error; successful save clears the input and emits the success toast. Other preference saves restore the prior state on failure.

## Verification evidence

TDD RED: the new controller test failed with module-not-found before the implementation. Its first GREEN had four passes. Skill-import tests likewise failed before the module existed; the next run exposed the empty-name parser issue (one failure, one pass), then both passed after the horizontal-whitespace fix.

Initial isolated focused suite: 23 tests, 22 pass, 1 fail. The failure was the new Search label missing from the English catalog; the label was added. This run included successful Host route integration, adverse snippet skill matching, cancellation, reference bounds, existing request-flow and disabled-skill tests. React handler tests exercise the actual component code with isolated hooks/API stubs; they are not GUI tests.

`npm run typecheck` passed after fixing router import and session preference typing. `node --check server/index.mjs` and `node --check server/inference.mjs` passed. `node scripts/audit-ui.mjs` fails with 110 findings. Read-only HEAD source substitution with matching worktree CRLF and new components excluded also yields 110. The same baseline audit with LF blobs reports 68 because its selector parsing is line-ending-sensitive. Neither audit result is called a pass; unrelated baseline CSS/kit/icon findings were not changed.

Focused tests run serially through the existing `isolatedTestEnvironment` and `test-fs-guard` with fresh scratch HOME, USERPROFILE, STRATA_HOME, Local/Roaming/XDG directories and TEMP/TMP. Fixtures reject public networking except synthetic provider responses, and use no GPU model. The full suite and build were deferred during the parent's performance benchmark to avoid contention; final outcomes will be appended before handoff.

## Residual risk and rollback

Native GUI bridge is unavailable; no screenshots, keyboard focus walk, responsive browser run, screen-reader result or real-browser validation is claimed. The existing Dialog/Btn/Select/Field patterns and CSS tokens are retained, but those visual checks remain parent-owned. Real provider accessibility, rate limits and Hikari answer quality require parent E2E. An explicitly configured keyed search provider is unsupported by the new manual path; the existing Harness provider fallback is retained. Third-party skill package resource compatibility is not promised.

Rollback is by reverting the feature commits locally. Result capabilities expire naturally or disappear with Host exit; no durable result cache or new credential file was added. Imported skills use the existing created-skill directory and preferences, so user-created content should not be deleted during code rollback.

## Review round and bounded full-suite outcome

Local feature commits: `a36284dd` explicit search, `079f8588` SKILL.md import/scope, `3f013772` awaited key save. A self-review follow-up `36014f4b` uses the successful skill POST's returned list through existing `setSkills`, avoiding a subsequent GET failure falsely presenting an already completed import as failed.

Parent review found two Important/P2 defects at `3f013772`: source metadata belonged to the user message but the only renderer was in the assistant branch; typed external `/research topic` unconditionally reopened a blank search even after references were selected. Actual ChatScreen submit and MessageView user-return regressions first failed 0/2, then passed 2/2 after `169237a7`. The first search transition strips `/research` into the ordinary question; selected references send once while preserving the current model. The user's sent message now renders links and the snippets-only disclosure. These tests stub surrounding dependencies and hooks; they exercise the actual owning screen/renderer, not a browser or a live model.

One full `npm test` was started with concurrency 1 and requested bundled `STRATA_PYTHON=C:\Users\downl\AppData\Local\Programs\Strata\control\python\python.exe`, with its directory first on PATH. The standard suite runner strips inherited STRATA variables, so this is not evidence that every full-suite child honored that variable. It failed the existing app-ui window-mode Host startup assertion after 19.118 seconds. The helper asserts before its cleanup block and left the file alive; the full suite was therefore bounded and terminated, tool session exit -1, with no aggregate pass result. Its six proven owned processes were `40168 → 33260 → 30760 → 41960 → 37696 → 40356`; creation/parentage were checked, only that test tree was stopped, and all six IDs were subsequently absent. Installed Host/Hikari were not stopped. Evidence: `task-ux-host-tests.log` in the SDD task directory. The full suite was not repeated.

A subsequent isolated serial relevant/mixed run completed with 50 tests: 46 pass, 1 fail, 3 skip, duration 72.739 seconds. The failure is the existing command-server assertion at `tests/agent-tools-settings.test.mjs:273` (`isError` true versus expected false). It is retained as a failed mixed run, without claiming a diagnosed platform cause or a whole-suite pass. New search/import/handler routes passed. Evidence: `task-ux-focused-tests.log`. A final new-UX-only + locale run, final typecheck and build follow the review fix; their outcomes are recorded below when complete.

## Self-review

Self-review-event: type=qa_defect scope=explicit-search/chat-handoff category=qa-coverage evidence=task-ux-review.md

Applied `agent-self-review-evolution` in review-only mode with its event-ledger and update-governance references. The missing checks were the sent user-message branch and the second submission after typed `/research`. The smallest prevention is the focused Chat handoff regression now in the change. No AGENTS, SOP, skill, automation or parent ledger was modified. Rejected a broader instruction rewrite because the concrete screen-level regressions directly cover the failures. GUI verification and live provider/model checks remain separately owned and unclaimed.

## Final worker verification

At code head `169237a7`, the isolated serial final set passed 18/18 tests, zero skips, in 21.130 seconds: `chat-web-search`, `skill-import`, `ux-web-search`, `ux-key-save`, `ux-skill-import`, `ux-chat-handoff`, `explicit-reference-routes`, `skill-import-routes`, and `locale-gaps`. The same final lane is saved as `.superpowers/sdd/2026-11-02_strata-16gb-implementation-plan_Codex/task-ux-run-focused.mjs`; it preserves the exact bundled STRATA_PYTHON in its isolated profile and uses the existing scratch filesystem guard, one test process at a time, and a 90-second file timeout. The saved runner was subsequently invoked from workspace root with `node .superpowers/sdd/2026-11-02_strata-16gb-implementation-plan_Codex/task-ux-run-focused.mjs`, with stdout/stderr directed to `task-ux-new-tests-final.log`.

Final `npm run typecheck` passed (`task-ux-typecheck-final.log`). Final `npm run build` passed (`task-ux-build-final.log`, Vite 8.71 seconds). Vite emits a chunk-size warning above 500 kB; no chunk splitting work was added to this task. `git diff --check` passed. These are source build results; the installed app was not replaced or launched by this worker.

The mixed tests generated one untracked workspace-local `apps/host/Microsoft/Windows/PowerShell/ModuleAnalysisCache` (4892 bytes). It was absent before the runs; only that file was found beneath the directory. A cleanup attempt with exact resolved-directory and contents checks was rejected by automatic approval review as blocked by policy. No retry or alternative deletion was attempted; this generated cache remains preserved. Parent `_docs` baseline/plan files and all SDD evidence were preserved. The previously bounded six-process test tree was rechecked absent.

Parent separately reported real search returning five sources and wrong-chat result rejection, followed by a 90-second Hikari answer timeout; completion ownership/cause remains unresolved. These are parent-owned live checks, not this worker's mocked integration results, and do not establish end-to-end Hikari success or performance qualification. No runtime cancellation or engine stop was attempted by the worker.
