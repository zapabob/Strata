# GUI refusal-direction removal — implementation and parent handoff

## Overview / goal

Implement 「拒否ベクトルの除去をGUIでも表示して実装して」 in the integration worktree, based on source HEAD `50b8ef53` (upstream main `146df3c4`). This helper owns the GUI feature only. The parent owns the product `0.5.3-local.1` version/native build/install pipeline.

The GUI now calls the feature **拒否方向ベクトルの除去 / Refusal-direction removal**. Native model settings persist the opt-in. Loads use the existing setup/control-vector mechanism. Requested settings, observed loading, and recorded request application are distinct.

## Baseline, scope and decisions

Applied PC/project AGENTS context, canonical-compatible `CLAUDE-FABLE-5.md`, Common, Implementation Start Gate, Skill Selection, Security, WebApp Development, Frontend Design, Application Development, LLMOps, TypeScript and Python SOPs. Applied the already-loaded MILSPEC baseline, user-named yaraikata-memo workflow as this authorised helper, and completion self-review. No delegation. Canonical material's conflicting identity/environment/tool assertions do not override the active harness.

Local sources inspected: project AGENTS, host README, app design-system notes and CSS/components, `docs/DESIGN.md`, the vector README/PROVENANCE, setup.py's existing `--experimental-speed-projection` path, generate.cpp's help/load/INFO implementation, existing native control/settings/serving/user-argument contracts, serve engine INFO/metrics/request records, ordinary and agent request shaping, related tests, and the parent's isolated check runner. The host README's `apps/handoff.md` and `apps/docs/RUNBOOK.md` links were not present at those paths. No new web-dependent claim or package-trust assessment was needed.

Only relevant `apps/host/server`, `apps/host/src`, `apps/host/tests`, two minimal `serve` observability/test changes, and this implementation log were edited. No native source, adapters outside the Host, root version metadata, CMake, packaging guards, signing, installation, app/model launch, commit, push, or global/profile configuration changes were performed. Tests use fake engine/control boundaries and isolated scratch profiles. In-memory TS compilation is part of the existing test technique; no distributable build was produced. Parent logs were not edited.

## Requirements → implementation → verification

| ID | Requirement / decision | Evidence |
| --- | --- | --- |
| GUI-R1 | Japanese/English truthful name and experimental scope; native opt-in saved per model | NativeSettings, NATIVE_FIELDS, nine fix catalogs; settings round-trip and Japanese translation/SSR tests |
| GUI-R2 | Actual native flags, default/OFF argv unchanged, no weight modification/download | applyProjection and Host builder tests; baseline/OFF exact args comparison; no extra launch probe on default/OFF |
| GUI-R3 | Family, adapter, actual executable and actual pinned vector validated before known-invalid jobs/replacement | 13 invalid-input scenarios in refusal-projection tests; explicit executable override and backend cases; independent split-binary checks |
| GUI-R4 | INFO-backed loaded/off status; no success invented from saved settings or healthy HTTP | actualProjectionState tests: absent INFO, cvec=0, project/add, custom vector, stopped child, stale child history; Python history tests |
| GUI-R5 | Explicit request ON/OFF reaches ordinary and agent routes | loopback HTTP tests through proxyCompletion and createLlmProxy; existing agent shape tests |
| GUI-R6 | Preserve custom vectors/user_args, environment, unknown fields, existing auth | custom-vector/default/OFF and exact-owned-bundle tests; user-args and existing native settings regressions |

## Implementation details

`refusal_direction_removal` is an app-owned boolean in the existing native settings API. Absent/Default is unloaded. `true` persists intent and constructs the existing arguments at load time:

```text
--control-vector-scaled <Control>/data/experimental-speed-projection/Qwen3.8-Flash-Next-experimental-speed-projection.gguf:1.0
--control-vector-layer-range 4 44 --cvec-mode project --cvec-dir per-layer
```

The same code admits known requests before job creation and rechecks before acquisition/replacement. The selected native executable's bounded, no-model `--help` must advertise all four flags, `add|project`, and `cvec=0|1`. Capability is bound to actual executable SHA-256, rather than filename/version. An explicit model-config executable takes precedence over the primary component path. Automatic all-cards split transforms are independently checked; an unverified transformed binary falls back to the already-verified ordinary engine through the existing split fallback. Default/OFF launches do not add a probe or vector args.

Compatibility is conservative: existing serving policy must identify Q38, and the saved/catalog source family must be `qwen` or `coder` (setup.py's shipped-vector families). Q36, PrismML, TurboQuant, DeepSeek, Swift, unknown families/backends, and engines without verified help are unavailable with a reason. Model/display filenames do not grant support. Gyro/Unsloth are not newly qualified by this feature.

The fixed bundled sidecar path is under packaged `control.control.dir` (source mode uses the repository). Actual vector bytes must be 483,520 bytes, SHA-256 `ef0724c5b79297e481017be85769832bc26eb220c984ecba2b0e1b0c8426312b`, and its provenance must still declare that same trusted pin, kind and OFF default. No arbitrary vector path/hash supplied via GUI is treated as a compatible vector. Existing Qwen licence/data stay in place.

Only the exact setup-owned bundle can be removed from `args`, `args_written`, and `user_args`. A different path (including the same basename elsewhere), scale, mode, range, extra vector, or other custom vector configuration remains user-owned. Enabling the shipped feature alongside custom vector flags is refused rather than overriding them. Legacy setup-owned ON is projected as ON in the settings editor, so unrelated GUI saves do not silently clear it.

The Sampling drawer remains a request switch, not a vector loader. Its existing internal key and ordinary default payload remain compatible. It is actionable only when the current default native instance has an actual loaded-vector observation. Explicit agent ON, like OFF, is now forwarded, so a native sampling default of false does not swallow an explicit GUI ON. An unconfigured agent still has no sampling override and keeps its prior route/payload.

Actual UI state requires a ready instance, a live native child and engine INFO `cvec`. Only a Host-verified pinned launch plus exact `project:4-44` is labelled the bundled vector. Different/custom values are labelled unverified. `cvec=0` is unloaded/OFF. Missing/old-server evidence stays unobserved. Applied/request-OFF state additionally requires a successful completed server record from the current child's generation. The minimal serve change adds `projection_child_generation` beside the existing `projection` record, preventing stale history from looking applied after respawn. This is a server execution record plus actual loaded INFO, not a quality/behaviour guarantee or a kernel-output measurement.

UI uses the existing native-setting rows, Select, toggle, small/muted status and design tokens; no new CSS values or dependencies. English/Japanese are authored; the other seven catalogs explicitly carry the English fallback strings in the existing fix-catalog convention.

## Changed files

- `apps/host/server/refusal-projection.mjs` (new)
- `apps/host/server/native-control.mjs`
- `apps/host/server/native-settings.mjs`
- `apps/host/server/catalog.mjs`
- `apps/host/server/agent/llm-shape.mjs`
- `apps/host/src/app/SamplingDrawer.tsx`
- `apps/host/src/components/NativeSettings.tsx`
- `apps/host/src/components/RefusalProjectionStatus.tsx` (new)
- `apps/host/src/lib/native.ts`
- `apps/host/src/lib/refusal-projection.ts` (new)
- `apps/host/src/locales/fix-en.json`
- `apps/host/src/locales/fix-ja.json`
- `apps/host/src/locales/fix-zh.json`
- `apps/host/src/locales/fix-de.json`
- `apps/host/src/locales/fix-es.json`
- `apps/host/src/locales/fix-fr.json`
- `apps/host/src/locales/fix-ru.json`
- `apps/host/src/locales/fix-pt.json`
- `apps/host/src/locales/fix-ko.json`
- `apps/host/tests/refusal-projection.test.mjs` (new)
- `apps/host/tests/agent-shape.test.mjs`
- `apps/host/tests/helpers/native-fixture.mjs`
- `apps/host/tests/user-args.test.mjs`
- `serve/server.py` (two observability lines)
- `serve/test_refusal_projection_observation.py` (new)
- This log.

The old user-args fixture had no catalog identity and no saved architecture, so existing serving policy rejected its `--kv` before reaching its assertions. It now explicitly declares `arch: qwen4exp`; production identity policy was not weakened. The new fixture callbacks mock capability/drafting/split boundaries only.

## Exact verification commands and results

All commands below ran at `H:/Strata/worktrees/main-integration-20261106`. The parent's `run_checks.py` supplies scratch HOME/USERPROFILE/APPDATA/TEMP, a minimal environment, no live agent/model credentials, a 256 MiB Node budget, and no Python bytecode writes. Typecheck explicitly used 1024 MiB. `uv --version`: 0.11.29. Python metadata inspected: no project pyproject/lock/python-version; requirements.txt specifies Python 3.10+ and Jinja2 3.1.6.

### Passed

```powershell
uv run --offline --no-project --no-cache python "_docs/upstream-0212-20261109/run_checks.py" --cwd host -- node --test --test-concurrency=1 tests/refusal-projection.test.mjs tests/agent-shape.test.mjs tests/user-args.test.mjs tests/native-serving-policy.test.mjs tests/native-settings.test.mjs tests/native-settings-file.test.mjs tests/native-settings-response.test.mjs tests/run-config-check.test.mjs
```

Exit 0. **94 tests: 93 passed, 0 failed, 1 skipped**, duration 8031.783 ms. The skip is the existing built-Harness-dependent end-to-end agent turn: the isolated check intentionally does not set STRATA_HARNESS_DIR. Existing loopback agent forwarding tests did run.

After strengthening the ordinary/agent HTTP propagation assertion and adding split-binary tests, the final affected follow-up was:

```powershell
uv run --offline --no-project --no-cache python "_docs/upstream-0212-20261109/run_checks.py" --cwd host -- node --test --test-concurrency=1 tests/refusal-projection.test.mjs tests/native-serving-policy.test.mjs
```

Exit 0. **53 tests: 53 passed, 0 failed, 0 skipped**, duration 4138.1289 ms. These overlap the previous group; do not add their counts. The feature file now has 23 passing tests, including both transformed-engine outcomes.

```powershell
uv run --offline --no-project --no-cache python "_docs/upstream-0212-20261109/run_checks.py" --cwd host -- node --max-old-space-size=1024 node_modules/typescript/bin/tsc --noEmit
```

Exit 0, no TypeScript diagnostics. Ran again after the production UI/type changes.

```powershell
uv run --offline --no-project --no-cache --python "C:/Users/downl/AppData/Local/Programs/Strata/control/python/python.exe" python "_docs/upstream-0212-20261109/run_checks.py" -- python -m unittest serve.test_refusal_projection_observation serve.test_monitor serve.test_server.SharedSettings -v
```

Exit 0. **19 tests passed**, 5.982 s. No native engine/model process. Existing installed app Python supplies runtime dependencies; no installation was performed.

`git rev-parse --short HEAD` returned `50b8ef53`. Normal repository-configured `git diff --check` exited 0 (only the existing LF→CRLF checkout notices).

### Failed / resolved or existing

Initial combined Node check: 67 tests, 59 pass, 7 fail, 1 skip. One new assertion incorrectly assumed cvec flags were the last arguments; the existing privacy layer appends flags later. The assertion now checks the cvec segment at its actual index. Five failures were the old user-args fixture's missing architecture; fixed as above and all eight user-args tests now pass. The remaining failure was the existing full base-language parity gate.

`tests/languages-and-catalog.test.mjs`: **5 tests: 4 passed, 1 failed**. The base zh catalog lacks 56 existing `uxweb*`, `uxskill*`, and `uxtool*` keys present in base en. A read-only `git show HEAD:apps/host/src/locales/{en,zh}.json` comparison independently reproduced the same 56 missing keys at unmodified HEAD. This feature changes fix catalogs only and tests all 18 new keys across all nine languages. The base-catalog gap remains for the parent; no unrelated translation rewrite was made.

The first Python check used uv's already-installed CPython 3.13 and failed before collection because `jinja2` was absent. Selecting the existing app's private Python through uv resolved it. No packages were installed.

A diagnostic `git -c core.autocrlf=false diff --check` treated raw Windows CRLF checkout bytes as whitespace and a whole-file diff. This command was inappropriate for the repository's configured conversion. Normal `git diff --check` passed; no bulk newline rewrite or git-config change was made.

### Not run

Native/app build, signing, installer overwrite, real app launch, real model generation, browser/Playwright runs, real GPU/speed/quality measurement, and built-Harness E2E. These belong to the parent pipeline or were prohibited for this helper. In-memory status-component SSR/Japanese assertions, TypeScript checks and loopback HTTP tests are source-level evidence only.

## Candidate runtime requirements

1. Parent must ship the updated Host UI/server and the updated Control-side `serve/server.py` together. Existing vector data/PROVENANCE/licence must remain in the packaged Control data directory.
2. A real original Qwen3.8 `qwen`/`coder` model and the actual native executable implementing the advertised cvec flags are required. The specialised Q36 engine does not become compatible by accepting a sampling field or by having a Qwen-looking filename. Q36/PrismML/TurboQuant/DeepSeek must remain visibly unsupported.
3. Engine metrics must carry real `cvec=0` or `cvec=project:4-44` INFO plus a live `native_child.generation`. Completed-request applied/OFF status also requires the new same-child `projection_child_generation` record. Older metrics remain unobserved/loaded-only, not applied.
4. User explicitly saves ON and reloads the model. Selecting ON alone must leave actual state unchanged until a real load receipt. No additional vector/model download or model-weight rewrite is required by this feature.

## Practical Playwright assertions for parent after overwrite

Use a disposable test profile and the parent's existing launch workflow. These are proposed assertions, not executed browser evidence.

- Japanese Models → Native engine settings: locate the region `拒否方向ベクトルの除去`. On a verified Q38 binary its `getByRole('combobox', {name: '拒否方向ベクトルの除去'})` is operable. Select the existing On option, save, reopen, and assert the PATCH body and subsequent GET settings both contain `values.refusal_direction_removal === true`. The native settings response must have `refusalProjection.supported === true` and the pinned SHA.
- Before reload, assert no `[data-refusal-projection="applied"]` is created merely by saving. Compare actual cvec state to the existing live metrics, not to the new saved field. After real reload, require `[data-refusal-projection="loaded"]` and exact real `metrics.engine.cvec === 'project:4-44'`, a live child and the real profile's nine cvec arguments (do not screenshot auth material).
- Chat → Response settings → Advanced: `getByRole('switch', {name: 'リクエストで拒否方向ベクトルの除去を使う'})` is disabled/unchecked without a verified loaded vector and enabled only after the real loaded receipt. Verify help says the request switch does not load the vector. Saving request OFF must put `experimental_speed_projection: false` into the actual ordinary and agent model requests; saving ON must put true into both. With successful completed requests, check `request-off`/`applied` status and matching child generations.
- Save native OFF and reload: real engine cvec is 0, `[data-refusal-projection="off"]` appears, and feature-owned launch args are absent. Restart/respawn or unload the child and verify old history does not preserve an applied badge. Missing metrics must become unobserved.
- With the candidate Q36 model, assert the native feature is unavailable and the Japanese unsupported reason is visible; an explicit API enable returns an error before adding a job or unloading the ready model. Repeat a tampered/missing vector in a disposable package copy; never edit the parent's live payload for this check. Preserve existing custom vector/user_args and assert they are not removed by native OFF.
- At desktop and narrow viewports in both themes, assert the long Japanese help wraps without horizontal overflow, keyboard focus and Select/toggle behaviour remain usable, and there are no new console errors. These visual/accessibility checks remain outstanding for the parent.

## Residual risk / recommended next actions

Real candidate help, hardware loading, projection arithmetic, quality and performance are not qualified by this helper. Capability probing is intentionally conservative (3 s, 64 KiB; stdout/stderr accepted); a binary that cannot prove its contract remains unsupported. Pinned path identity is strict and non-canonical/symlinked sidecar paths are rejected. The full base-language parity gate remains red for the independent 56-key gap. Non-Japanese/non-English new copy is currently the English fallback.

Parent next actions: incorporate these scoped source files into its overwrite/build pipeline, verify Q36 stays unsupported, run the browser assertions above against a disposable profile, and only qualify a compatible Q38 path when real INFO, actual flags and request records agree. No unsupported speed plan (`ef3df253`, unavailable source) was implemented.

## Self-review

Self-review-event: `ticket_completed`, `qa_defect`, `local_fix` (2026-11-09). Evidence: bounded checks and the failures/resolutions above; more than five focused iterations in this feature. Decision: review-only; no AGENTS/Skill/SOP/automation mutation is justified or authorised. Smallest prevention artifacts are the feature tests and this parent's pending browser checklist. Review specifically caught explicit-executable selection, OFF launch probes, stale-child history, split transforms dropping intent, and privacy args following cvec; the implementation/assertions now cover those cases. Rejected alternatives: trusting model/executable names, treating request API acceptance as loaded, clearing all cvec flags, downloading/retraining a vector, weakening adapter policy or language gates, or changing native/build/version files. Remaining runtime/browser risks are explicitly handed to the parent above.
