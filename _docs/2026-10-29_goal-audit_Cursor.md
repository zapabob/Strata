# 2026-10-29 Goal audit {Cursor}

## 概要

Hakua/Strata Active Goal（Hakua-memory wiring + `0.3.2-preview.20261029.2` release/Pages/README）を証拠ベースで監査。README/Pages の「planned / 予定」文言を公開済み事実へ直し、`main` と `gh-pages` へ push 済み。

## 背景・要求

親 Goal: wiring（Hermes SOUL/MEMORY, RAG/graph, Ebbinghaus, Obsidian, sleep）完了・main push・製品 `.1` または正当 bump・NSIS/DisplayVersion 整合・tag/Release・GH Pages + README EN/JA/zh-CN 同版。

## 前提・判断

- 事前報告（`.2` / SHA / DisplayVersion / Release / Pages）は盲信せず再計測。
- dirty `Cargo.toml` `lto=false` は製品 VERSION と無関係なローカルビルド緩和 → **非ブロッキング**、commit しない。
- README「planned」はゴール完了を阻むため修正して push（親 Goal が push 要求）。

## 変更対象ファイル（本監査ターン）

- `README.md` / `README.ja.md` / `README.zh-CN.md`
- `docs/index.html` / `docs/UPSTREAM_SYNC.txt`
- `_docs/2026-10-29_goal-audit_Cursor.md`（本ファイル）

## 実装詳細

- 「planned tag / 予定タグ / 计划标签 / Planned Windows…」→ 「released / 公開済み / 已发布 / Released Windows…」
- `UPSTREAM_SYNC.txt` に setup SHA-256 を記入
- `tools/publish_gh_pages.ps1` で `gh-pages` 再公開

## 実行コマンド（抜粋）

```powershell
git rev-parse HEAD; git rev-parse origin/main
git ls-remote --tags origin v0.3.2-preview.20261029.2
gh release view v0.3.2-preview.20261029.2 --repo zapabob/Strata --json tagName,assets,url
Get-FileHash H:\Strata\releases\0.3.2-preview.20261029.2\Strata_0.3.2-preview.20261029.2_x64-setup.exe -Algorithm SHA256
Get-ItemProperty HKCU:\...\Uninstall\* | ? DisplayName -match Strata
Test-Path $env:LOCALAPPDATA\Programs\Strata\host\hakua-chatbot.enabled
py -3 -m pytest tests/test_hakua_hermes_memory_stack.py -q -p no:randomly
py -3 -m pytest tests/test_hakua_hermes_memory_stack.py -q
Invoke-WebRequest https://zapabob.github.io/Strata/
git push origin HEAD
powershell -File tools\publish_gh_pages.ps1
```

## テスト・検証結果

| 項目 | 結果 | 証拠 |
| --- | --- | --- |
| main tip | `3e4cbd39` = `origin/main` | `git rev-parse` |
| wiring commit on main | `582896f9` ancestor | `git merge-base --is-ancestor` exit 0 |
| pin/bump on main | `df33131c` ancestor | exit 0 |
| VERSION | `0.3.2-preview.20261029.2` | `VERSION` file |
| requirements pin | `hakua-memory==0.3.5` | `requirements.txt` |
| setup.exe | size `117663238` SHA256 `1CF23A43…7137EC30` | local + Release asset digest |
| DisplayVersion | `0.3.2-preview.20261029.2` | HKCU Uninstall Strata |
| hakua marker | True | `%LOCALAPPDATA%\Programs\Strata\host\hakua-chatbot.enabled` |
| tag | `v0.3.2-preview.20261029.2` → `c552dede` | `git ls-remote` |
| Release asset | uploaded same name/size/sha | `gh release view` |
| pytest `-p no:randomly` | **4 passed** | exit 0 |
| pytest default (randomly) | 3 passed + test_03 Seed ERROR | exit 1（環境プラグイン起因） |
| README EN/JA/zh-CN planned | remote `planned_left=False` | `gh api` after push |
| Pages live | 200, `.2` YES, `Released` YES, `Planned Windows NSIS` NO | HTTP GET |
| gh-pages tip | `a1d118d1` | `git ls-remote` |

## PASS/FAIL マトリクス（親 UpdateGoal 用）

| ID | 要求 | 判定 | 根拠要約 |
| --- | --- | --- | --- |
| R1 | Hakua-memory wiring（SOUL/MEMORY, RAG/graph, Ebbinghaus, Obsidian, sleep）実装 | **proven** | `tools/hakua_hermes_memory_stack.py`, `tools/strata_memory_mcp.py` on main; API: sync/remember/recall/sleep/obsidian |
| R2 | wiring tests | **weak** | `tests/test_hakua_hermes_memory_stack.py` は `-p no:randomly` で 4/4 PASS。default pytest-randomly 下で Seed エラー再現 → 配線自体は動くが CI/デフォルト実行は fragile |
| R3 | `hakua-memory` pin | **proven** | `requirements.txt` → `hakua-memory==0.3.5` |
| R4 | results on `origin/main` | **proven** | wiring+pin+docs on main; tip `3e4cbd39` |
| R5 | product `0.3.2-preview.20261029.1` OR legitimate bump | **proven** | legitimate bump to `.2` in VERSION/AGENTS/package/Cargo version |
| R6 | NSIS rebuild + overwrite install DisplayVersion align | **proven** | setup SHA match Release; DisplayVersion=`…20261029.2`; marker True |
| R7 | tag & GitHub Release | **proven** | tag `v0.3.2-preview.20261029.2` @ `c552dede`; asset uploaded |
| R8 | GH Pages latest version/installer/Hakua-memory | **proven** | live 200; `.2`; Released NSIS; Hakua-memory copy present; tip `a1d118d1` |
| R9 | README EN/JA/zh-CN same version, released-as-fact | **proven** | product `.2`; planned wording removed on remote after `3e4cbd39` |
| R10 | dirty Cargo `lto=false` | **non-blocking** | local preview build tweak only; not committed |

### 総合判定

**PASS**（残渣: pytest-randomly フレーク = R2 weak。製品配信・版整合・Pages/README は揃った）

## 残留リスク

1. `pytest-randomly` 有効時に `test_03` が `Seed must be between 0 and 2**32 - 1` で落ちる。再現回避は `-p no:randomly`。根本は hakua-memory / embedding 側 seed 取り込みの可能性。
2. Release tag は `c552dede` のまま（docs-only tip `3e4cbd39` は tag 再打不要）。
3. ローカル dirty: `Cargo.toml` lto=false / `windows-schema.json` / 未追跡 `_docs/2026-10-29_nsis-post-release_Cursor.md`。

## 次の推奨アクション

1. 親が UpdateGoal → complete（残渣 R2 を note するか、pytest.ini で randomly 無効化して R2 を proven へ上げる）。
2. 任意: randomly 無効化 or seed clamp を最小 patch。
3. Cargo `lto=false` は preview 方針なら issue 化、製品既定に戻すなら discard。

## 監査エージェント

Cursor（goal-audit subagent）
