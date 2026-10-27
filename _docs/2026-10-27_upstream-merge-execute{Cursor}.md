# Upstream merge plan (execute)

- Generated: `2026-10-27T14:06:40.161855+00:00`
- Branch: `codex/strata-hakua-chatbot-20261027` @ `67313f58287adaf08b9ae053ebd2222b7178944b`
- Upstream: `upstream/main` @ `4b9e05a2a806a3fe24f7b2560d98626c37dade35`
- Merge-base: `7dd5cf18e68c639a8773e096c5c79f971ea2a9f5`
- Ahead / behind: **143** / **163**
- Dirty: `False`
- Backup branch: `backup/pre-upstream-merge-20261027T140640Z`
- Executed: `False` (merge failed (1): Auto-merging CMakeLists.txt
Auto-merging README.de.md
CONFLICT (content): Merge conflict in README.de.md
Auto-merging README.es.md
CONFLICT (content): Merge conflict in README.es.md
Auto-merging README.fr.md
CONFLICT (content): Merge conflict in README.fr.md
Auto-merging README.ja.md
CONFLICT (content): Merge conflict in README.ja.md
Auto-merging README.md
CONFLICT (content): Merge conflict in README.md
Auto-merging README.pt-BR.md
CONFLICT (content): Merge conflict in README.pt-BR.md
Auto-merging README.zh-CN.md
CONFLICT (content): Merge conflict in README.zh-CN.md
Auto-merging apps/desktop/package.json
CONFLICT (content): Merge conflict in apps/desktop/package.json
Auto-merging apps/desktop/src-tauri/Cargo.lock
CONFLICT (content): Merge conflict in apps/desktop/src-tauri/Cargo.lock
Auto-merging apps/desktop/src-tauri/Cargo.toml
CONFLICT (content): Merge conflict in apps/desktop/src-tauri/Cargo.toml
Auto-merging apps/host/package.json
CONFLICT (content): Merge conflict in apps/host/package.json
Auto-merging apps/host/server/index.mjs
CONFLICT (content): Merge conflict in apps/host/server/index.mjs
Auto-merging apps/host/server/native-control.mjs
CONFLICT (content): Merge conflict in apps/host/server/native-control.mjs
Auto-merging apps/host/server/native-settings.mjs
Auto-merging apps/host/src/lib/native.ts
Auto-merging apps/host/src/lib/store.ts
CONFLICT (content): Merge conflict in apps/host/src/lib/store.ts
Auto-merging apps/host/src/lib/types.ts
Auto-merging apps/host/src/screens/ModelRun.tsx
CONFLICT (content): Merge conflict in apps/host/src/screens/ModelRun.tsx
Auto-merging apps/host/tests/packaged-control.test.mjs
Auto-merging serve/server.py
Auto-merging src/program/generate.cpp
Auto-merging strata_cli/cli.py
Auto-merging strata_control/models.py
CONFLICT (content): Merge conflict in strata_control/models.py
Auto-merging strata_control/runtime.py
Auto-merging tests/terminal/test_runtime.py
Automatic merge failed; fix conflicts and then commit the result.)

## Remotes
- `origin` fetch=`https://github.com/zapabob/Strata.git` push=`https://github.com/zapabob/Strata.git`
- `upstream` fetch=`https://github.com/Niko1221/Strata.git` push=`https://github.com/Niko1221/Strata.git`

## Proprietary features (must preserve)
- **F01** Clifford/Spin(8)/Triality KV Cache — `spin8`
- **F02** Query-v3 & Identity Initialization — `tqcodec / adapters`
- **F03** TurboQuant Dialects — `tqcodec`
- **F04** Dynamic Shared Audit Fix & Guard — `src + host guards`
- **F05** Model/Pack/Position/Hash Snapshot Integrity — `native-control / run-config`
- **F06** GUI/CLI Fork-Specific Settings & Clean OFF — `apps/host`
- **F07** Windows Ownership, Job Guard & Fail-Closed — `packaging / control`
- **F08** Hikari 27B PQ2_0 & Nimble Weights — `prism / model bundles`
- **F09** Research PoC, Negative Results & Ledger — `_docs`
- **F10** Refusal-Direction / Control Vector Steering — `research opt-in`
- **F11** Arbitrary GGUF & DeepSeek Derivative Integration — `ModelBundle router`
- **HAKUA** Hakua consented authenticated memory chat — `apps/host + serve/memory_harness.py`
- **KEYS** Fork / Hakua harness API keys + run-config known keys — `run-config-check / native keys`
- **HERMES** Hermes agent + long-term memory integration — `serve / docs`
- **PKG** Hakua-labelled Windows full packaging (-hakua) — `packaging/full_windows.py`

## Proprietary path presence
- `OK` `_docs/upstream-intake/fork-contracts.json`
- `MISSING` `adapters/upstream`
- `OK` `apps/host/server/memory.mjs`
- `OK` `apps/host/server/native-control.mjs`
- `OK` `apps/host/server/run-config-check.mjs`
- `OK` `apps/host/src/lib/store.ts`
- `OK` `packaging/full_windows.py`
- `OK` `serve/memory_harness.py`
- `OK` `spin8`
- `OK` `tests/contracts/test_fork_feature_matrix.py`
- `OK` `tests/contracts/test_upstream_compatibility.py`
- `OK` `tools/check_upstream_cut.py`
- `OK` `tools/generate_t00_intake.py`
- `OK` `tools/merge_upstream_fork.py`
- `OK` `tqcodec`

## merge-tree conflict hints
- changed in both

## Notes
- Fork is ahead=143, behind=163 vs upstream/main.
- merge-tree heuristic flagged 1 conflict hint(s).
- Some proprietary paths are absent from the worktree (sparse-checkout or not yet landed): adapters/upstream
- Stashed dirty work: pre-upstream-merge-hakua-20261027T140640Z
- Merge stopped with conflicts or error; working tree may be mid-merge. Resolve manually.
- To abort: git merge --abort
- Restore stash later with: git stash list  # look for pre-upstream-merge-hakua-20261027T140640Z

## Next steps
1. Review this plan JSON/Markdown; keep proprietary features listed below.
1. Ensure dirty Hakua edits are committed or stashed (script can --stash-dirty).
1. Re-run: py -3 tools/merge_upstream_fork.py --plan --upstream-ref upstream/main
1. When ready (explicit): py -3 tools/merge_upstream_fork.py --execute --upstream-ref upstream/main --stash-dirty --backup
1. Resolve conflicts preferring fork proprietary anchors + upstream security/bugfixes.
1. Run host tests + check_upstream_cut; then build, tag/release (no auto-push), rewrite README.
