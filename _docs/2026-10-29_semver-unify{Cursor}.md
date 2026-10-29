# 2026-10-29 semver unify {Cursor}

草、製品版がバラけすぎてて草生えたので一本化した。なんj風に言うと「セマンティクスバージョンをアップが統一されてない」案件、仮説検証の末 `0.3.2-preview.20261029.1` に寄せた。

## 仮説

| ID | 仮説 | 結果 |
|----|------|------|
| H1 | 最新タグ `v0.3.2-preview.20261028.2` よりコード側が遅れている（.1 / .27.1 混在） | **採用** |
| H2 | 今日 (JST 2026-10-29) の次プレビューは `0.3.2-preview.20261029.1`（当日タグ無し → N=1） | **採用** |
| H3 | エンジン CMake `0.1.53` / Metal `0.1.52-metal` は製品版と別系統で残す | **採用** |
| H4 | `VERSION` を Hakua 製品 SemVer の単一正本にし、Cargo / npm / PRODUCT_VERSION / README Fork notes / NSIS / packaging を同期 | **採用** |
| H5 | インストール済み DisplayVersion はソース同期だけでは変わらない（要 rebuild/reinstall） | **採用**（実測: `0.3.2-preview.20261028.2`） |

## Before → After（製品面）

| Source | Before | After |
|--------|--------|-------|
| `VERSION` | `0.3.2-preview.20261028.1` | `0.3.2-preview.20261029.1` |
| `apps/desktop/src-tauri/Cargo.toml` | `0.3.2-preview.20261028.1` | same as VERSION |
| `Cargo.lock` strata-desktop | `0.3.2-preview.20261028.1` | same |
| `apps/desktop/package.json` | `0.3.2-preview.20261028.1` | same |
| `apps/desktop/package-lock.json` | `0.3.2-preview.20261027.2` | same |
| `apps/host/package.json` | `0.3.2-preview.20261028.1` | same |
| `apps/host/package-lock.json` | `0.2.7` | same |
| `strata_cli.PRODUCT_VERSION` | `0.2.7` | same as VERSION |
| README EN/JA/zh-CN Fork notes | `0.3.2-preview.20261028.1` | same |
| `AGENTS.md` banner | `Version 0.2.7, engine 0.1.52.` | `Hakua product version 0.3.2-preview.20261029.1, engine 0.1.53 (Metal 0.1.52-metal)…` |
| `packaging/full_windows.py` | hardcoded `Strata-0.3.2-preview.20261027.1` | reads `VERSION` via `programs_folder()` |
| `packaging/full_installer.nsi` | `…20261027.1` | `…20261029.1` |
| Latest git tag (reference) | `v0.3.2-preview.20261028.2` | （タグ作成は本コミット対象外） |
| Installed DisplayVersion | `0.3.2-preview.20261028.2` | **未変更**（再ビルド/再インストールが必要） |

## エンジン（意図的に非統一）

| Source | Value |
|--------|-------|
| `CMakeLists.txt` project | `0.1.53` |
| `metal/CMakeLists.txt` STRATA_VERSION | `0.1.52-metal` |
| `strata_cli.version()` build | `0.1.53`（preview 文字列の VERSION は無視して CMake へフォールバック） |

## Decisions

1. **正本**: リポジトリ直下 `VERSION`（1 行）。同期は `tools/bump_hakua_product_version.py`。
2. **アプリ SoT との関係**: 既存テストどおり Cargo.toml も製品版と一致。`tauri.conf.json` は version キー無し（従来どおり）。
3. **上流 0.2.7 表記**: README 各言語の公式インストーラ名 `Strata-0.2.7-…` と AGENTS 本文の上流説明は残す。Hakua 製品版は Fork notes / AGENTS バナーで明示。
4. **タグ**: 本作業はソース統一のみ。`v0.3.2-preview.20261029.1` の annotated tag / release / NSIS 再ビルドは別ステップ。

## Commands

```powershell
py -3 tools/bump_hakua_product_version.py --set 0.3.2-preview.20261029.1 --check
py -3 -m pytest tests/terminal/test_tui2_023_versions.py::VersionBump tests/terminal/test_tuiqa_version.py::ProductVersion tests/desktop/test_app_version.py tests/terminal/test_full_windows.py::test_build_verify_zip_and_strict_membership -q --tb=line -p no:randomly
py -3 strata.py --version   # STRATA_NO_HANDOVER=1
```

## Verification

- `bump_hakua_product_version.py --check` → **OK** product sources match
- pytest (上記、`-p no:randomly`) → **12 passed**
- `pytest-randomly` + thinc の seed エラーは環境既知ノイズ（本変更無関係）

## Residual risks

- インストール済みアプリの DisplayVersion は古い。ユーザーに NSIS/Tauri 再ビルド＋上書きインストールが必要。
- 翻訳 README（de/es/fr/pl/pt-BR）に Hakua Fork notes が無い → 上流 0.2.7 ボタンのみ。EN/JA/zh-CN は同期済み。
- `full_windows` ショートカット名 `Strata Preview 0.3.2 (SM120)` はメジャー.マイナー固定のまま（意図的）。
- 本コミット後の git tag / GitHub Release / Pages 更新は未実施。

## Next recommended actions

1. （任意）`git tag -a v0.3.2-preview.20261029.1` + release notes
2. Tauri/NSIS をこの VERSION でビルドし DisplayVersion を揃える
3. `hakua-chatbot.enabled` 同梱は維持したまま（本変更では触っていない）
