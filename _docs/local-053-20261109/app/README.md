# Local 0.5.3 app helpers — parent execution handoff

Prepared for product `0.5.3-local.1`, Control `0.5.4`, native `0.5.3`.
These helpers have only had low-impact validation. They have not built, signed,
installed or launched the candidate. All runtime results must be produced by the
parent's new execution. `releaseQualified=false` is retained throughout.

The only implementation files changed for this task are in this directory.
The implementation log is here too, inside the workspace `_docs` boundary.
No historical helper or execution recipe is modified.

## Entry points and inputs

`adapter.py` is the parent-facing entry point. It defaults to a read-only plan;
`--plan` is also accepted. Each executing phase requires the full clean-source
`--reviewed-commit` and an explicit absolute `--native-source-root`. The app and
fresh Control archive use the reviewed app checkout. Their source commits are
recorded separately from the independently pinned native source commit.

The parent must first supply
`H:/Strata/releases/local-053-20261109-opencode/app-files/staged-native.json`
and the staged component at
`apps/desktop/src-tauri/resources/engine-bundle/0.5.3-windows-x86_64-cuda-cuda13`.
The receipt must contain the agreed `ok`, `signatureVerified`,
`releaseQualified:false`, `nativeSourceCommit`, `engineSHA256`, `q36SHA256`,
`signedManifestSHA256`, `prismVersion`, `prismManifestSHA256`, `prismExeSHA256`,
`archive`, `archiveSHA256`, `archiveBytes`, `payloadInventorySHA256`, and `quality`.
The inventory digest uses the historical preparation convention: SHA-256 of the
UTF-8 JSON object mapping relative forward-slash paths to file SHA-256 values,
sorted keys, separators `(',', ':')`, including `engine-component.json`.

The file-enabled candidate uses fresh `BASE/app-files`; keep the earlier `BASE/app`
installer and all its evidence. The already completed signed native receipt may
be reused only after current payload/archive/production verification; the new
Control, app and GUI receipts must be generated against the newly reviewed app
commit. Q36 real-app acceptance now also requires sidebar file CRUD in its isolated
workspace, and the native fixture starts legacy then explicitly opts in through
the UI. Git output is decoded as UTF-8 so Japanese source filenames are preserved.

No old native hash, source count or commit is asserted. `verify-native.mjs` calls
production `verifyEngine`, `verifyNativeBuild`, `verifyPublicAssets`, and Control's
built-in trusted-key signature verifier. Standard Tauri packaging guards get
the separate source root/commit/manifest binding only in their child environment.
No signing command or private signing-key path is used.

Exact nested Prism `0.4.1` and TurboQuant `0.4.0` inventories are compared with
the immutable previous signed composite under
`H:/Strata/releases/personal-052-local2-20261107/app/signed-component-r4/0.5.2-windows-x86_64-cuda-cuda13`.
Prism's manifest and executable also have the requested fixed hashes.
Keep that reference available. Both unchanged backend trees are verified, not
reconstructed from an old pass receipt.

`build.py` uses the fresh Control packaging recipe with the current lock, CPython
`3.12.15`, and Hakua-memory `0.3.5`. Its cache is on H:. It stages the new Control
in a fresh C: archive directory, preserves the entire previous Control by rename,
then moves the verified new tree into place. Existing repository files are retained.
The app build preserves the actual existing Cargo-cache shell and every existing
NSIS EXE with their current hashes before invoking the standard Tauri NSIS build.
It makes no `local.1` assumption. Build temporary directories, npm/uv caches,
PowerShell analysis cache and Cargo outputs are on H:.

`recipes.py` adapts the actual successful `qa-q36-r14.mjs` and `qa-prism-r5.mjs`
from `execution-20261108`, informed by `make-qa-adapter.py`,
`probe-runtime-owned.py`, and `isolate-host-home.mjs`. It keeps the corrected UI
selectors, `x-strata-client`/Origin headers, explicit Prism display version,
bounded Q36 INFO assertions, runtime ownership and fresh homedir isolation.
Checked replacements fail if their expected historical anchors change.
Generated scripts and their origin/recipe hashes are retained with each attempt.

`probe.py` checks the actual target shell path/hash, packaged Node path/hash and
Host entry point, isolated home/preload, and the runtime's exact arguments and
ownership. Native ownership follows the successful Control owner bound to Host
PID plus a creation token. Prism ownership and loopback listener are checked.
Raw arguments and tokens are never printed.

## Parent commands

Run from `C:/Users/downl/Documents/ChatGPT/Strata` after coordinating the
metadata change and committing the intended clean source. The native source root
must be the frozen checkout that matches the new receipt, which can differ from
the app checkout. The helper does not create or modify that checkout.

Subsequent candidate builds use five jobs for Cargo and CMake. Large outputs and
caches stay on H:. The already completed native build retains its four-job receipt.

```powershell
$uv = 'C:/Users/downl/.local/bin/uv.exe'
$py = 'C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe'
$node = 'C:/Users/downl/AppData/Local/Programs/Strata/node/node.exe'
$helper = '_docs/local-053-20261109/app/adapter.py'
$reviewed = '<full-reviewed-clean-app-commit>'
$nativeRoot = '<absolute-frozen-native-source-root>'

# Safe inspection; these do not consume staging or create output directories.
& $uv run --no-project --offline --python $py python -B $helper build-app --plan
& $uv run --no-project --offline --python $py python -B '_docs/local-053-20261109/app/test_adapters.py'

function Run-Local053Phase([string]$Step, [string]$Target = 'candidate') {
    & $uv run --no-project --offline --python $py python -B $helper $Step --execute --reviewed-commit $reviewed --native-source-root $nativeRoot --target $Target --attempt r1 --seconds 3000
    if ($LASTEXITCODE -ne 0) { throw "Local053 phase failed: $Step / $Target. Retain its evidence and review before continuing." }
}

Run-Local053Phase build-control
Run-Local053Phase build-app
Run-Local053Phase qualify
Run-Local053Phase qa-q36 candidate
Run-Local053Phase qa-prism candidate
Run-Local053Phase backup
Run-Local053Phase install
Run-Local053Phase verify
Run-Local053Phase activate
Run-Local053Phase qa-q36 installed
Run-Local053Phase qa-prism installed

# Run in the parent's standalone handoff console, outside any outer QA Job Object.
# adapter.py deliberately does not contain this phase in its QA kill-on-close job.
Run-Local053Phase normal-start
```

Do not execute `build.py`, `upgrade.py`, generated QA files, or `--worker`
directly. The dispatcher owns review, resource and Job Object gates. Private Node
must report `v24.22.2` at app build time. No dependencies are added by preparation.

## What each acceptance means

The qualification phase extracts the newly built NSIS installer, uses production
source/resource verifiers, checks exact managed membership and the documented
Tauri bundle-marker difference, Windows ProductVersion, fresh Control identity,
native source/signature, and all 13 production self-tests. It writes the new
`qualified-payload.json` and `app-qualification.json`.

Every GUI run gets an exclusive directory under `BASE/app/qa`, such as
`candidate-q36-r1` or `installed-prism-r1`. It starts the actual selected EXE and
connects Playwright to the real loopback WebView2 CDP endpoint. It never launches
a substitute Chromium window. The installed target is fixed to
`C:/Users/downl/AppData/Local/Programs/Strata/strata-desktop.exe`; its entire
managed payload must match the newly qualified package. Fresh isolated copies of
the signed native component are used for model tests. The separately imported
installed component must match too. Normal-user small-file hashes and membership
are compared before/after each isolated run.

The fresh Q36 fixture references the existing GGUF, adjacent expert pack and
verification receipt, and existing tokenizer at the paths in the task. It uses
4096 context, 512 prefill, 5 slots, MTP 2, mapped pack, explicit
`bounded-experts-v1`, F32 native K/V argv, no prompt/conversation cache, private
owner mode and 32 output tokens. It omits the generic F32 aliases that needed a
later historical repair. The real UI saves/reselects settings, saves/restores a
profile across shell restart, loads/chats/unloads/reloads, rejects an invalid
mode without disturbing the live runtime, and checks actual native INFO and
Control owner identity. Japanese screenshots contain only synthetic QA sessions.

Prism hashes the requested real GGUF, uses explicit PrismML `0.4.1`, 98304 context,
Q8 K/V, flash attention, parallel 1 and 32-token output. It checks the actual
binary/version, child argv/listener, `/props`, allocation logs, exact arithmetic
answers `5` and `56`, saved-profile persistence through restart, and GUI unload.
It does not edit the normal user's library, backend choice or Automatic override.

Success-only receipts are `candidate-q36-e2e.json`, `candidate-prism-e2e.json`,
`installed-q36-e2e.json`, and `installed-prism-e2e.json`. They explicitly include
`target`, `installedExeTest`, actual shell path/hash, `actualWebView2`,
`actualShellAndHost`, runtime-check flags, app/Control/native source identities,
fresh recipe hash, unchanged user hashes, `quality`, and `releaseQualified:false`.
An extracted-candidate pass cannot satisfy the installed gate.

### Q36 refusal-direction negative acceptance (candidate and installed)

Both generated Q36 recipes now inline `q36-projection-acceptance.mjs` into the
existing real WebView2 lifecycle. No extra phase or browser launch is needed.
Keep using `qa-q36 --target candidate` and `qa-q36 --target installed`; include
these helper changes in the parent's next reviewed clean app commit. The native
source root/receipt binding remains independent.

The actual settings API must expose `refusal_direction_removal` with
`supported:false` and a nonempty unavailable reason, and `refusalProjection`
must independently report unsupported, a Q36 reason, and saved intent OFF.
Japanese native settings must show the named region `拒否方向ベクトルの除去`,
a Japanese Q36 reason and an accessible Japanese `role=status` observation;
there must be no operable projection-enable combobox for this model.

With the real bounded Q36 child ready, both a settings PATCH and a load operation
requesting `refusal_direction_removal:true` must fail with 400/422 and a relevant
reason. The exact config hash, settings/MCP/projection values, job IDs, ready
instance, process ID and child generation must remain unchanged. These are real
loopback requests with the usual UI/Origin headers, not intercepted API routes.

The status is checked after native settings save, model reselection, profile
restart, rejected enable, both unloads and the real reload. Only `unobserved` or
real INFO-backed `off` is accepted. `off` additionally needs the current live,
admitted child's matching generation/PID and `cvec=0`; an unloaded child must
return to `unobserved`. Q36 may not display `loaded`, `applied`, `request-off` or
an unverified-vector badge. Reload also requires a different actual generation.

In the ordinary chat Sampling drawer, acceptance opens the accessible Response
settings/Advanced controls and requires the renamed request-only switch, disabled
and unchecked without a verified loaded vector, its loading-versus-request help,
and non-applied status. It rejects the old experimental-speed switch name. The
disabled switch is not force-clicked and no positive projection request is sent.
Native Japanese-region and request-switch screenshots use only the isolated QA
profile. Normal-user hashes remain under the existing dispatcher checks.

Success now requires `projectionAcceptance.ok:true`, `supported:false`,
`positiveProjectionRuntimeTested:false` and `q38RuntimeQualified:false` in both
target-specific Q36 receipts. Existing shell/Host/installed-EXE, Q36 functional,
settings, reload, Japanese recovery and resource gates remain in force.

This is negative Q36 coverage. No compatible Q38 runtime is qualified, and no
positive loaded/applied transition or same-child projection execution is claimed.
In particular, a real applied-to-unobserved transition cannot be exercised on
this unsupported Q36 model; no positive observation/history is fabricated to
simulate one. Actual Sampling selectors and screenshots await the parent run.

## Overwrite, backup and failure handling

The fresh private backup is
`H:/Strata/private-backups/local-053-20261109-opencode`. It is restricted to the
current user. It covers all small `.strata`, Roaming/Strata and Local/Strata user
files, model configuration files under the configured install/model roots,
registry export and shortcuts. Weights are excluded. Unexpected large non-weight
inputs or links block the backup. Existing native `0.5.2` bytes and all installed
managed payload hashes are recorded and checked again. Native `0.5.2` stays in
place; it is never deleted or replaced by these helpers.

NSIS is invoked once, with `/S` and `/D=C:\Users\downl\AppData\Local\Programs\Strata`
last. Its exclusive claim prevents another invocation even if it fails or times
out. Prelaunch verification compares the exact new managed payload and all
backed-up user hashes, the retained native component, registration, shortcuts
and Windows version. This gate runs before component activation or GUI launch.

Activation uses installed Control's `components install-file --model-config`
with the new signed archive and an actually observed candidate-Q36 bounded
runtime config. Only nonportable desktop memory/tool/log fields are removed in
a private copy. Engine API authentication, integrity, capabilities and full
test-start stay enabled. There is no skip-test, force retry or signing bypass.
If existing selection remains pinned, activation stops. The parent must review
an explicit `components use <new-folder> --family qwen --model-config <private-config>`
and its full test-start before preparing a separately reviewed activation retry;
this helper never silently rewrites a selection to manufacture success.

All executing phases except the final normal launch have an owned-child Job
Object, bounded deadline, and continuous RAM 3 / commit 4 / C: 5 / H: 10 GiB
floors. Other processes are never stopped. The parent arranges a quiescent window.
The final normal launch strips QA/debug variables, preserves Automatic's existing
override and saved settings/registrations, verifies unloaded status repeatedly,
and leaves the installed app open outside the QA guard. It samples the same
resource floors while waiting for the normal Host and unloaded checks.

Failures keep their guard logs/resource samples, attempt receipts and synthetic
diagnostics. A GUI retry uses a new `--attempt r2` and fresh profile. Success is
not overwritten. Build, qualification, backup, import and NSIS phases are one-shot;
partial output or a failure requires parent review before a new execution layout.
Never delete evidence or copy a prior successful receipt into this run.

## Validation and remaining gates

Preparation validation: ten low-impact unittest cases passed, including syntax
checks of five generated JS variants (qualification and both targets for both
models), side-effect-free plans for every phase, missing-review refusal,
historical-anchor drift refusal, exact resource-floor boundaries, and a real
Node homedir-preload check with rejection of a normal/private home. Additional
tests reject candidate receipts at installed acceptance, new user files before
first launch, and an existing NSIS claim before any installer subprocess.
Both checked-in MJS files pass `node --check`. `adapter.py --help` also passed.

Follow-up projection acceptance validation: all **11 Python contract cases**
passed, including syntax of the same five generated JS variants. The added case
runs **4 Node subtests** against the pure negative-capability/observation checks,
covering missing reasons, saved-enable intent, positive badges, missing INFO,
dead/stopped children and stale generation/PID. The new runtime helper also
passes `node --check`. These tests do not launch a browser or model.

The new signed native staging and current version metadata were not available
when these helpers were prepared. Full build/packaging/signature/source checks,
NSIS overwrite, GPU model runs, real installed WebView2/selector compatibility,
private backup, registry/shortcut verification and final normal launch remain
parent execution gates. No native/resource/general-quality/full-window
qualification is claimed by preparation.
