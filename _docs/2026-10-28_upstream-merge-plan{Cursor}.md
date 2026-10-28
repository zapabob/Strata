# Upstream merge plan (plan)

- Generated: `2026-10-28T12:51:02.589321+00:00`
- Branch: `codex/strata-hakua-chatbot-20261027` @ `7466066ffc3fd8431c18d72a6d2a6780311f142a`
- Upstream: `upstream/main` @ `46c152a1310f77cd2f0ce2c7cd213962df14fe83`
- Merge-base: `4b9e05a2a806a3fe24f7b2560d98626c37dade35`
- Ahead / behind: **154** / **494**
- Dirty: `False`
- Backup branch: `backup/pre-upstream-merge-20261028T125102Z`
- Executed: `False` (n/a)

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
- `OK` `adapters/upstream`
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
- Fork is ahead=154, behind=494 vs upstream/main.
- merge-tree heuristic flagged 1 conflict hint(s).

## Next steps
1. Review this plan JSON/Markdown; keep proprietary features listed below.
1. Ensure dirty Hakua edits are committed or stashed (script can --stash-dirty).
1. Re-run: py -3 tools/merge_upstream_fork.py --plan --upstream-ref upstream/main
1. When ready (explicit): py -3 tools/merge_upstream_fork.py --execute --upstream-ref upstream/main --stash-dirty --backup
1. Resolve conflicts preferring fork proprietary anchors + upstream security/bugfixes.
1. Run host tests + check_upstream_cut; then build, tag/release (no auto-push), rewrite README.
