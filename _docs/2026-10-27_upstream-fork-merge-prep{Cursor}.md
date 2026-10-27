# 2026-10-27 upstream fork merge prep{Cursor}

実施：2026-10-27 23:04 JST（Tokyo）。作業先 `H:/Strata/worktrees/hakua-chatbot-20261027`。

草、上流とフォークの間に 163 コミットの崖が立っとるのを先に測った。破壊的 merge はまだ踏んでない。仮説検証はこう：

1. **H1** official remote があるか → 当初 `origin` のみ。`upstream` = `https://github.com/Niko1221/Strata.git` を追加し `git fetch upstream --tags --prune` 成功 → **採用**
2. **H2** 既存 merge スクリプトがあるか → `tools/check_upstream_cut.py` / `generate_t00_intake.py` / `generate_changes_csv.py` はあるが **destructive merge 用スクリプトは無し** → `tools/merge_upstream_fork.py` を新規作成 → **採用**
3. **H3** 独自機能の定義 → `_docs/upstream-intake/fork-contracts.json` の F01–F11 + Hakua/Hermes/keys/packaging → **採用**
4. **H4** 現カット U1=`7dd5cf18` は upstream/main 祖先か → merge-base がちょうど U1。upstream latest tag **v0.2.6**、main tip `4b9e05a2`。fork ahead **143** / behind **163** → **採用**
5. **H5** sparse-checkout が `_docs` を落としていた → `git sparse-checkout add _docs` で intake 復元。`adapters/upstream` は worktree 未展開（MISSING）→ **注意継続**

## Remotes

| name | URL |
|------|-----|
| origin | https://github.com/zapabob/Strata.git |
| upstream | https://github.com/Niko1221/Strata.git |

## Branch / SHAs

| item | value |
|------|-------|
| branch | `codex/strata-hakua-chatbot-20261027` |
| HEAD | `67313f58287adaf08b9ae053ebd2222b7178944b` |
| upstream/main | `4b9e05a2a806a3fe24f7b2560d98626c37dade35` |
| merge-base (U1) | `7dd5cf18e68c639a8773e096c5c79f971ea2a9f5` |
| upstream latest release | `v0.2.6` |
| backup branch | `backup/pre-upstream-merge-20261027T140453Z` |

## Merge script

- Path: `tools/merge_upstream_fork.py`
- Modes: `--plan` / `--status` (default non-destructive), `--execute` (explicit only)
- Dry-plan artifacts:
  - `_docs/upstream-intake/merge-plan-2026-10-27.json`
  - `_docs/2026-10-27_upstream-merge-plan{Cursor}.md`
- Command evidence:
  - `py -3 tools/merge_upstream_fork.py --plan --backup --upstream-ref upstream/main --json --output _docs/upstream-intake/merge-plan-2026-10-27.json --markdown-output "_docs/2026-10-27_upstream-merge-plan{Cursor}.md"` → exit 0

## Proprietary feature inventory (preserve)

| ID | Name |
|----|------|
| F01 | Clifford/Spin(8)/Triality KV Cache |
| F02 | Query-v3 & Identity Initialization |
| F03 | TurboQuant Dialects |
| F04 | Dynamic Shared Audit Fix & Guard |
| F05 | Model/Pack/Position/Hash Snapshot Integrity |
| F06 | GUI/CLI Fork-Specific Settings & Clean OFF |
| F07 | Windows Ownership, Job Guard & Fail-Closed |
| F08 | Hikari 27B PQ2_0 & Nimble Weights |
| F09 | Research PoC / Ledger |
| F10 | Refusal-Direction steering (opt-in) |
| F11 | Arbitrary GGUF & DeepSeek derivative |
| HAKUA | Consented authenticated Hakua memory chat |
| KEYS | Fork / hakua_harness API keys + run-config |
| HERMES | Hermes agent + LTM |
| PKG | Windows full packaging `-hakua` |

## Dirty work preserved (do not discard)

- `apps/host/server/native-control.mjs` (F03 cancel-path / `stopCancelledLoad`)
- `apps/host/tests/native-load-cancel.test.mjs`
- `apps/host/package.json`
- `packaging/full_windows.py`
- plus local `_docs` Hakua logs and the new merge script

## Blockers (goal still ACTIVE)

1. Working tree dirty → stash/commit before `--execute`
2. Actual merge of 163 upstream commits not run yet
3. Build / tag / release / README rewrite not done
4. No auto-push (per instruction)

## Predicted content conflicts (`git merge-tree HEAD upstream/main`)

README.md / README.ja.md / README.zh-CN.md / README.de.md / README.es.md / README.fr.md / README.pt-BR.md,  
`apps/desktop/package.json`, `Cargo.toml` / `Cargo.lock`,  
`apps/host/package.json`, `apps/host/server/index.mjs`, **`apps/host/server/native-control.mjs`**,  
`apps/host/src/lib/store.ts`, `apps/host/src/screens/ModelRun.tsx`, `strata_control/models.py`

Both sides also touch (overlap, may auto-merge or conflict): `CMakeLists.txt`, `serve/server.py`, `src/program/generate.cpp`, `strata_cli/cli.py`, `strata_control/runtime.py`, host `native.ts` / `types.ts`, etc.

## Next merge step

1. Commit or `stash -u` the Hakua cancel-path + merge script (prefer commit of intentional WIP if user asks; else `--stash-dirty` on execute)
2. `py -3 tools/merge_upstream_fork.py --execute --upstream-ref upstream/main --stash-dirty --backup --no-commit` で conflict 面を先に出す（ユーザー明示後）
3. Conflict 解決方針: proprietary anchors（特に `native-control.mjs` / Hakua / Spin8）優先、upstream security/bugfix・uninstaller は取り込む。README は後段で fork TL;DR に書き直し
4. `py -3 tools/check_upstream_cut.py` + host tests → build → tag/release（push は別途許可）→ README rewrite

## Goal status

**ACTIVE** — merge done / proprietary preserved / build verified / tag-release / README rewrite の全部は未達。
