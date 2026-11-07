# Personal local.2 preparation — parent review gate

This directory prepares app **0.5.2-local.2**, Control **0.5.3** and native **0.5.2**,
now composed with the exact private **PrismML 0.4.1** runtime in unsigned r4.
It does not represent a built, installed or published local.2 app. The parent owns
source review/freeze, maintenance pauses/restoration, push, handoff and worktree cleanup.
The scripts default to plans. Do not add `--execute` until the relevant parent gate.

## Verified preparation inputs

The read-only audit is in
`H:/Strata/releases/personal-052-local2-20261107/app/prep-audit-r1.json`.
It verifies 751 native sources against **the current main root**, plus all r3
component file hashes. No `STRATA_NATIVE_SOURCE_*` override is used. Native source
commit is `4a171bdeb33675963edcca51f423519863fb7127`; unsigned manifest SHA-256 is
`1058ccf94a1a78be07a485e968c40b007225a9c7a39b45eae5d78fbe582191e7`;
`strata.exe` SHA-256 is
`13fc3b96fe71afcb98990d828d2c743f85e8b59b16174a1f7da3eb4ef9b4f8e3`.
Node, Harness, notices and local backend trees match the earlier full inventories.

The inherited r3 record reports 17 functional checks passed and actual bounded /
legacy / restart checks, but **releaseQualified=false** and four generic CUDA
resource violations remain. Signing proves integrity, not resource qualification.
The original unsigned r3 tree and its receipts stay immutable. No feed is made.

At preparation, installed versions remain app local.1 / Control 0.5.2 / native
0.5.1. No matching shell/native/llama process was observed. This is not permission
to restore an absent server. Current C: space is below 5 GiB: resolve that reserve
through the parent before staging or executing any later step.

## Entry points

| Helper | Purpose |
| --- | --- |
| `audit-inputs.py` | Read-only exact component/current-source and reusable-resource checks; sanitized version/process/resource receipt. |
| `prepare-prism-r4.py` | Already executed: preserve unsigned r3, verify both exact Prism 0.4.1 and rollback 0.4.0, prepare a fresh unsigned composite, and replace only backed-up managed staging. Never signs or activates. |
| `stage-native.py` | Plan by default. Only after parent-reviewed source: copy/sign unsigned r4 privately with `feed_tool.py`, verify built-in trusted key and every byte, preserve unsigned staging, and make a local ZIP. No activation. |
| `build.py control` | After reviewed clean source: preserve previous staged Control, build fresh locked Terminal and stage Control 0.5.3. |
| `build.py app` | Preserve old unbundled shell and old NSIS bytes/receipt before reusing Cargo cache; run both existing release guards with current-root native binding. Freeze new unbundled shell outside Cargo. |
| `qualify-app.mjs` | Exact archive/source/resource inventory, Windows ProductVersion, documented Tauri marker only, no embedded GPU runtimes, 13 production self-tests. |
| `prepare-e2e.py` | Create a new isolated real-component profile and bounded Q36 run configuration using existing model/pack/tokenizer paths. Starts nothing. |
| `qa-e2e.mjs` | Actual WebView2 NativeSettings/profile/reselection/restart/Japanese rendering and actual Q36 load/chat/unload/reload, with INFO and owned binary/argv assertions. |
| `qa-prism-e2e.mjs` | Additional mandatory actual packaged-GUI test for the hash-bound reported GGUF: explicit PrismML, 98304/Q8/FA, two arithmetic answers, saved-profile restart and GUI unload. Separate isolated profile; no normal-user mutation. |
| `prepare-prism-selection.py` | Already executed read-only: full moved-GGUF hash, metadata/tensor-directory inspection, private prior-library/config snapshots, exact single-target selection/restore plan; no API writes. |
| `probe-owned.py` | Metadata-only runtime ancestry and exact real-engine digest/settings check. Never emits raw arguments or secrets. |
| `upgrade.py` | Separate gated backup, one explicit C: NSIS, prelaunch exact-payload/data verification, offline signed component activation, and normal unloaded startup/handoff. |
| `guard.py` | Owned Job Object, deadline and unchanged RAM 3 / commit 4 / C 5 / H 10 GiB floors. It never pauses/restores another server. |

The prior helpers under `_docs/local-install-20261106` remain immutable reference
recipes. Only `installed_state.py` is imported for the read-only normal-profile
status inspection. Do not execute the old local.1 build/install scripts.

## Parent execution commands — NOT executed during preparation

Use the new uv location. Run from the existing main worktree, not a nested worktree:

```powershell
$uv = 'C:\Users\downl\.local\bin\uv.exe'
$py = 'C:\Users\downl\AppData\Local\Programs\Python\Python312\python.exe'
$node = 'C:\Users\downl\AppData\Local\Programs\Strata\node\node.exe'
$h = '_docs/personal-install-20261107'
# Set only after parent review and coordinated commit of all intended source:
$reviewed = '<full-reviewed-main-commit>'
```

Unsigned r4 staging is complete. Its immutable source is
`H:/Strata/releases/personal-052-local2-20261107/component-copy-r4/0.5.2-windows-x86_64-cuda-cuda13`.
The manifest SHA-256 is `df94ca9c8260e002896b1fe8c26d5e5948358eaf3b83191ad7a0c28cc7f97206`.
The previous managed Prism 0.4.0 and engine 0.5.1 staging are retained in
`app/prism041-r4/backups`; original r3 and published payloads are untouched.
Signing remains blocked by parent source/monitor review. Only the standard
`feed_tool.py sign-package` subprocess reads the private key after that gate.

```powershell
& $uv run --no-project --offline --python $py python -B "$h/guard.py" --name sign-r4 --seconds 900 --execute -- $py -B "$h/stage-native.py" --execute --reviewed-commit $reviewed
& $uv run --no-project --offline --python $py python -B "$h/guard.py" --name control --seconds 1500 --execute -- $py -B "$h/build.py" control --execute --reviewed-commit $reviewed
& $uv run --no-project --offline --python $py python -B "$h/guard.py" --name app --seconds 3000 --execute -- $py -B "$h/build.py" app --execute --reviewed-commit $reviewed
& $uv run --no-project --offline --python $py python -B "$h/guard.py" --name qualify --seconds 900 --execute -- $node --expose-gc "$h/qualify-app.mjs" --execute --reviewed-commit $reviewed
& $uv run --no-project --offline --python $py python -B "$h/guard.py" --name e2e-fixture --seconds 600 --execute -- $py -B "$h/prepare-e2e.py" --execute --reviewed-commit $reviewed
```

Before real inference the parent must recheck all running services. If any are
active, use the parent's reviewed maintenance workflow after responses finish,
with exact restoration. Do not start missing servers as a supposed restoration.
The E2E runner refuses an existing shell/native/llama process and starts only its
isolated app. Keep other clients quiesced for this window.

```powershell
& $uv run --no-project --offline --python $py python -B "$h/guard.py" --name real-e2e --seconds 1200 --execute -- $node "$h/qa-e2e.mjs" --execute --reviewed-commit $reviewed
& $uv run --no-project --offline --python $py python -B "$h/guard.py" --name reported-gguf-e2e --seconds 1200 --execute -- $node "$h/qa-prism-e2e.mjs" --execute --reviewed-commit $reviewed
```

This E2E is **prepared, not runtime-qualified**. Any API/selector/actual-INFO mismatch
must fail and be reviewed; do not replace it with fixtures or mark the missing
check passed. It uses the real r3 component in an isolated component root, no model
download, no weight copies, context 4096, prefill 512, expert slots 5, F32 K/V,
MTP 2 and private-owner cache. It requires a nonempty GUI answer, stops/reloads
through the GUI, checks the actual new child, and bounds output to 32 tokens.
Japanese screenshots use synthetic recovery sessions only. The parent should
visually inspect both captured screenshots as well as the DOM assertions.

Both `functional-e2e.json` (Q36) and `prism-e2e.json` (reported GGUF) must pass.
After both pass, the parent can run the separate overwrite phases:

```powershell
& $uv run --no-project --offline --python $py python -B "$h/guard.py" --name backup --seconds 900 --execute -- $py -B "$h/upgrade.py" backup --execute --reviewed-commit $reviewed
& $uv run --no-project --offline --python $py python -B "$h/guard.py" --name install --seconds 660 --execute -- $py -B "$h/upgrade.py" install --execute --reviewed-commit $reviewed
& $uv run --no-project --offline --python $py python -B "$h/guard.py" --name installed-verify --seconds 900 --execute -- $py -B "$h/upgrade.py" verify --execute --reviewed-commit $reviewed
& $uv run --no-project --offline --python $py python -B "$h/guard.py" --name engine-activate --seconds 900 --execute -- $py -B "$h/upgrade.py" activate --execute --reviewed-commit $reviewed
# User-facing final app must outlive the QA guard. Run from the parent's standalone handoff console:
& $py -B "$h/upgrade.py" normal-start --execute --reviewed-commit $reviewed
```

The install arguments end with `/D=C:\Users\downl\AppData\Local\Programs\Strata`.
Backup covers all small `.strata/data` and Roaming/Strata files, Local settings,
component selection, tuning/launch, and discovered `strata-*.json` model configs.
Weights/download caches are excluded. Payload and user hashes must match before
first launch and before the deliberately recorded new component activation.
An existing 0.5.2 component is a blocker, not silently replaced. If automatic
selection remains pinned to 0.5.1, activation fails and the parent must review
the explicit `components use` choice. The scripts never edit user selections to
manufacture a pass.

All outputs are unique under `H:/Strata/releases/personal-052-local2-20261107/app`;
private backup is outside Git. A failed single-use phase requires a new reviewed
attempt path, not overwriting its receipt. The Cargo cache alone is reusable;
previous installer/evidence directories and their bytes are not modified.
No push, tag, feed publication, worktree removal or public-release qualification
is performed by these helpers.

## Prism 0.4.1 identity and target-profile plan

The exact approved runtime manifest SHA-256 is
`9c729c73eb050dc466203fe149a27acd5be48763a33ea2c5d2b89f78e4ddcbaa`.
Source base `73bfe6cc485554822f80c473a3c0c4f25e80f41b`, commit
`1965755ceee6738b9a04ceaf5d30e6305d6ccd00`, tree
`ae33fd73e8811fd0def3f13488c6942848ac5138`, both individual patches, combined
diff and the raw-byte proof are version-specific. Arbitrary versions and dirty
sources are rejected. Prism 0.4.0 retains its explicit clean/single-patch approval
and component rollback; Automatic still uses the existing environment override.

The real new and legacy payloads passed complete hash/membership verification and
actual `--version` commit probes before and after staging. The new executable is
`5ca5d8bfdfcb6fe46a96a06b71eaf45aedfbd1c6673bda2a10eb6412613be777`.
Inherited primary evidence is `H:/Strata/validation/qwen35-mtp-load-20261107/handoff-r2.json`:
ordinary use on this one file passed; real-file explicit-MTP negative testing was
blocked, and neither general quality nor full-window input is qualified.

The observed file is now one directory above the handoff path:
`H:/Strata/models/新しいフォルダー/DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic.i1-Q4_K_M.gguf`.
Full SHA-256 still equals
`8cf793a36e62fb078ac05c2e1bdb2121ff94736dccbede7cf81b76346e868949`.
The file was not rewritten: declared block count 33, tensor trunk blocks 0–31,
and recurrent map length 33 are retained. Two existing filename-matching library
references were observed; the parent must identify the intended prior target
profile rather than bulk-migrating both.

Safe plan receipt: `app/prism041-r4/selection-plan.json`. The protected private
plan/snapshots are under `H:/Strata/private-backups/prism041-user-selection-20261107`.
It is non-executable. After installation, take a fresh private backup, then use
the normal target-model Saved settings flow. `/api/engine` PATCH edits the current
engine config; there is no invented per-model server-profile endpoint. Persist
only the target's path-derived variant mapping and `runtime.backend=PrismML`;
retain other fields and every unrelated profile/default mapping. The 96K/Q8/FA
settings in this preparation are isolated E2E settings, not authorization to
overwrite the normal user's context settings.

Do not alter User/Machine `STRATA_LLAMA_SERVER` or the generic component pointer.
The normal-start helper preserves the existing Automatic executable override in
its child environment without writing the global environment. Actual r4 payload
is 2,192,713,257 bytes, so activation requires at least 7,561,422,377 free C: bytes
(about 7.05 GiB) to retain the 5 GiB reserve, before other overhead.
