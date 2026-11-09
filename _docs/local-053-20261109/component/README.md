# Private native 0.5.3 component handoff

Prepared code only. `compose.py` defaults to a read-only plan. It composes a fresh native-only 0.5.3 package with the fixed Prism 0.4.1 and TurboQuant 0.4.0 trees, signs a separate copy, packs a production ZIP, and stages the signed package for the existing app helpers. This preparation does not qualify a new native release.

All paths are fixed to this local candidate. `--reviewed-commit` is the **app** HEAD. `--native-source-root` must explicitly name `H:/Strata/worktrees/native-053-source-20261109`, clean at `26e5889625938459580313ca7ce6b3931606c27b`. App HEAD may advance independently. `verifyNativeBuild` receives the separate source root, commit and actual manifest digest every time.

## Parent prerequisites

Review and freeze the complete app checkout, including these helpers, at the full commit supplied to `--reviewed-commit`. Both checkouts must be clean. Validation caches below this directory are ignored. Do not change the native adapters after their recorded freeze.

Finish the native adapter phases, including the explicit restart, comparison and audit. There must be no `BASE/active.json`. The helper reads the **actual** report names `results/comparison.json` and `results/qualification-summary.json`; there are no `compare.json` or generic audit-summary aliases. The native package must remain unsigned at `BASE/native-component/0.5.3-windows-x86_64-cuda-cuda13`. `BASE` is `H:/Strata/releases/local-053-20261109-opencode`.

Stage, CPU, GPU, sanitizer, bounded model, legacy model, restart and comparison evidence must pass and refer to the frozen build. Required CPU/GPU test names come from the frozen real `native/phases.py` constants. Model reports must contain the real per-request counters, generated IDs, protected-file preservation, memory receipts and drained Job evidence. Missing or unknown required fields block execution. A completed CUDA spill/resource guard failure and the consequent failed audit may be retained only when their actual reports, phase exits, Job cleanup and violation lines agree. A timeout, skipped check or generic command failure cannot stand in for a measured resource FAIL. The implementation deliberately requires CTest's completed resource-failure exit 8, followed by the adapter's exit 1; a different failure contract needs review.

Keep the reference at `H:/Strata/releases/personal-052-local2-20261107/app/signed-component-r4/0.5.2-windows-x86_64-cuda-cuda13`. The execution path verifies its Ed25519 signature with `signing.load_trusted_keys(environ={})` and all payload hashes with production `engine_component.verify(full=True)` before copying retained bytes. It also runs production `verifyEngine`, both local-backend verifiers and the notices inventory check. No extra trust-key override is accepted.

`resources/local-backends/prism` and `resources/local-backends/turboquant` must already equal the corresponding reference trees. The helper leaves those sibling resources in place and checks them with production local-backend guards. `resources/notices/NOTICES.json` must verify. The pinned `H:/Strata/releases/hakua033-public-assets` and its existing `.receipt.json` must pass production `verifyPublicAssets`. These are prerequisites, not inputs the helper repairs.

Use the existing Python 3.12 at `C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe`, private Node **24.22.2**, existing Git and Windows Job support. RAM ≥3 GiB, commit headroom ≥4 GiB, C: free ≥5 GiB and H: free ≥10 GiB are admission and continuous execution floors. Allow additional H: capacity for three composite copies, the archive and the retained former bundle. Operations stop on pressure. No dependency is installed or acquired.

Supply an explicit absolute key path outside source, release and resource trees. Only `packaging/feed_tool.py sign-package` opens that path. The orchestrator never reads, stats, hashes or logs the key, and discards signing stdout/stderr. The resulting signature must verify against the built-in public trust set before staging proceeds.

## Parent commands

These commands are examples for the parent to run after review. The execution command was **not** run during preparation. Keep `$appHead` and `$componentKeyPath` as explicit parent-selected values; do not put key contents in either variable.

```powershell
$component = 'H:/Strata/worktrees/main-integration-20261106/_docs/local-053-20261109/component'
$python = 'C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe'
$uv = 'C:/Users/downl/.local/bin/uv.exe'
$nativeRoot = 'H:/Strata/worktrees/native-053-source-20261109'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:UV_CACHE_DIR = "$component/.validation-cache"
$env:UV_OFFLINE = '1'
$env:UV_PYTHON_DOWNLOADS = 'never'
& $uv run --offline --no-config --no-project --no-managed-python --python $python python -B "$component/compose.py" --plan
```

After setting `$appHead` to the reviewed full current app commit and `$componentKeyPath` to the explicit existing key path:

```powershell
& $uv run --offline --no-config --no-project --no-managed-python --python $python python -B "$component/compose.py" --execute --reviewed-commit $appHead --native-source-root $nativeRoot --key $componentKeyPath
```

Wait for exit 0 and inspect `BASE/app/component-053/owned-job.json` and `BASE/app/staged-native.json`. Parent app phases can then use their existing `common.staged()` and `build_env()` checks with the same explicit native source root. The app's own `verify-native.mjs` remains an independent mandatory build check in `app/build.py`. This helper does not invoke app build, install, activation or model phases.

## Files and state transitions

`core.py` holds exact inventories, exclusive copies, production signature/full-payload adapters, native-first composition, ZIP verification and scoped PE dependency checks. `quality.py` interprets current native evidence. `verify.mjs` calls the reviewed app's production guards without native executable probes. `deps.py` runs production PE parsing in a bounded child. `test_component.py` contains synthetic fixtures only.

Execution reserves `BASE/app/component-053` exclusively. Its `reservation.json` binds the app/native identities and helper hashes. One atomic, suspended-before-resume Windows Job owns the worker and all descendants. The whole operation has a 1,800-second deadline; signing has 60 seconds, ZIP 300, each Node integrity check 180 and dependency check 120. Runtime version probes are Python/Node only. The native executables and retained backend executables are not launched by this helper.

Composition begins with all bytes of the new native-only package. Only `local-backends/prism/**`, `local-backends/turboquant/**` and **all** `notices/**` are added from the authenticated old reference. Native/support collisions must already be byte-identical. Old root executables, `native-build.json`, root DLLs and version-specific `BUILD.json` are never copied from that reference. The new native `native-build.json` and both entrypoints remain byte-identical to the new package. No replacement build record is needed or invented. No model payload is accepted, including the licensed Control vector: that vector belongs to Control.

Unsigned, signed and pending staged copies have distinct fresh destinations. Signing may change only `engine-component.json`. Production `feed_tool.py pack-engine --format zip --url-prefix=` writes a root-payload ZIP with a flat relative entry URL. Every archive member is rehashed; membership, installed bytes, manifest digest, archive bytes and digest must agree. Native, Prism and TurboQuant dependency checks use separate DLL search scopes.

Only after all these checks does the helper carry the reviewed root `.gitignore` and `README.txt` forward into the pending root, rename the **entire** former `resources/engine-bundle` root to `BASE/app/component-053/prior-engine-bundle`, verify its inventory, and rename the pending root into `resources/engine-bundle`. Unknown root-level files block replacement. This preserves tracked scaffolding and keeps app source clean. It never deletes the prior root or mutates installed components. A final integrity/source check runs at the actual staged destination. The worker prepares a pending receipt; the controller publishes `BASE/app/staged-native.json` only after Job completion and confirmed cleanup, followed by another inventory/archive check.

The app receipt contains all requested fields, including `ok`, `signatureVerified:true`, `releaseQualified:false`, the native commit, entrypoint/manifest digests, fixed Prism identity, ZIP path/digest/bytes, and `quality`. `payloadInventorySHA256` is SHA-256 of UTF-8 `json.dumps(path_to_SHA256, sort_keys=True, separators=(',', ':'))`, **including** the signed manifest. Extra fields record native-build identity, dynamic source count, TurboQuant identity, reviewed app commit and retained bundle location.

`quality` preserves the current resource PASS/FAIL and actual violation lines, report paths and SHA-256s. Its short functional/model results do not qualify full-window, low-precision or general model quality. `releaseQualified` and `newNativeQualified` remain false. No historical failure count or passing-test count is copied.

## Failure handling and permitted validation

There is no retry, overwrite mode or automatic rollback. Every failed reservation and partial output remains for parent inspection. If failure occurs between the managed-root renames or after staging, the preserved old root and `prior-engine-bundle.json` identify the exact prior bytes. The parent must inspect those inventories and choose recovery explicitly. Do not delete the reservation or rerun into it to conceal a failure.

Preparation validation is restricted to help, default/explicit plan, syntax and small fixture tests. Use `python -B`, the local UV cache above, and `node --check verify.mjs`. Run fixtures from this directory with:

```powershell
& $uv run --offline --no-config --no-project --no-managed-python --python $python python -B -m unittest discover -s $component -p test_component.py -v
```

The fixture runner creates and removes only `component/fixture-*` directories. It never imports the production signing implementation, generates a key/signature, launches a model/native binary, signs, builds or stages actual resources. See the dated implementation log for the observed results and remaining integration checks.
