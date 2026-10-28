# 2026-10-28 upstream v0.2.7.1 merge + release + Pages {Cursor}

実施：2026-10-28（JST）。作業先 `C:\Users\downl\Documents\ChatGPT\Strata`。

草、前回の v0.2.6 崖のあとにまた 494 コミットの崖が生えてた。仮説検証はこう：

1. **H1** Documents の tip は origin/main と同期待ちか → fetch 後 tip=origin/main=`7466066f`、local main だけ `411d5b63` で遅延 → FF で同期 → **採用**
2. **H2** `tools/merge_upstream_fork.py --execute --no-commit` で mid-merge 到達できるか → 到達（`.gitattributes` 属性警告あり）→ **採用**
3. **H3** proprietary を残しつつ upstream API を取れるか → 21 conflict を公式 API 優先＋Hakua/spin8/gguf/perf131k 合成で解決 → **採用**
4. **H4** host 臨界テスト緑か → F03/F03b pass、packaged-control 30/30（`hakua_harness` 含む）、`check_upstream_cut` LOCKED → **採用**
5. **H5** Actions Pages dispatch が通るか → また HTTP 422 Actions disabled → **棄却（既知ブロッカー）**；代替として `gh-pages` 手動更新 → **採用**

## SHAs / remotes

| item | value |
|------|-------|
| workspace | `C:\Users\downl\Documents\ChatGPT\Strata` |
| branch | `codex/strata-hakua-chatbot-20261027` + `main` |
| pre-merge tip | `7466066f` |
| upstream tip | `upstream/main` @ `46c152a1` (**v0.2.7.1**) |
| merge commit | `e54b90f7` |
| tip after fix | `06387b47` |
| ahead/behind vs upstream after merge | **155 / 0** |
| backup | `backup/pre-upstream-merge-20261028T125117Z` |
| origin | https://github.com/zapabob/Strata.git |
| upstream | https://github.com/Niko1221/Strata.git |
| force-push | **No** |

## Conflict resolution (summary)

- `.gitattributes`: both (spin8 patches + KaTeX vendor)
- versions: fork preview `0.3.2-preview.20261028.1` (not upstream 0.2.7)
- `native-control.mjs`: spin8/NATIVE_FLAG_FIELDS save + `assertSettingsFile` + upstream `speedSwitches` + `stopCancelledLoad`
- `native.ts`: upstream `contextMax` + `hakuaChatbot`
- desktop `main.rs`: fork updater gate + upstream notification plugin
- `serve/server.py`: memory_harness + perf_e2e + upstream `extract_json` / `prefill_only` / `want_lp` / `ds_pics`
- `gguf_reader.py`: union PQ2_0/TQ* + TQP5/6/7
- engine C++: upstream structural API (nibble / layer-major / 2D verify) + fork diagnostics where additive
- `serve/web`: upstream i18n/queue UI + reinjected Hakua memory consent/`memory-chat.js`
- READMEs EN/JA/zh-CN: upstream 0.2.7.1 body + fork badges/notes

## Release

| item | value |
|------|-------|
| tag | `v0.3.2-preview.20261028.1` (annotated, pushed) |
| prerelease | **yes** (unsigned; no feed/Tauri secrets on host) |
| URL | https://github.com/zapabob/Strata/releases/tag/v0.3.2-preview.20261028.1 |

## GitHub Pages

| item | value |
|------|-------|
| live URL | https://zapabob.github.io/Strata/ |
| API status at write | `built` (legacy `gh-pages` source) |
| workflow_dispatch | **BLOCKED** HTTP 422 Actions disabled — settings: https://github.com/zapabob/Strata/settings/actions |
| manual refresh | `origin/gh-pages` @ `252e22d8` (docs synced from tip + `UPSTREAM_SYNC.txt`) |

## README paths

- `README.md`
- `README.ja.md`
- `README.zh-CN.md`
- (other locales track upstream wording; EN/JA/zh-CN carry fork notes)

## Push evidence

```text
7466066f..06387b47  codex/strata-hakua-chatbot-20261027 -> codex/strata-hakua-chatbot-20261027
7466066f..06387b47  main -> main
* [new tag] v0.3.2-preview.20261028.1
17454204..252e22d8  HEAD -> gh-pages
```

## Goal status

**ACTIVE (near-complete)** — merge + README + tag/prerelease + FF push + manual Pages refresh are evidenced. Remaining blocker for full CI/Pages workflow completeness: **GitHub Actions runner switch still 422-disabled** despite `actions/permissions.enabled=true`. Signed installer/feed still out of scope without keys.
