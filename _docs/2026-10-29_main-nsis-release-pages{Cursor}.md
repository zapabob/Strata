# 2026-10-29 main NSIS release + Pages {Cursor}

- **When**: 2026-10-29 JST（docs 完了時刻 ~17:50+09:00）
- **Workspace**: `C:\Users\downl\Documents\ChatGPT\Strata`
- **実装AI**: Cursor
- **なんJ風**: README 三言語と Pages ソースを製品版に揃えたで。NSIS 本体は親が焼いてるからこっちはドキュメント専任や。

## Status

| Item | Value |
|------|-------|
| Memory stack commit | `582896f9` |
| Product bump tip (pre-docs) | `df33131c` |
| Docs commit | `68664423` (`68664423528d24d5575edddea15143798f82b32e`) — pushed `origin/main` |
| VERSION / product | `0.3.2-preview.20261029.2` |
| Engine | `0.1.53`（Metal `0.1.52-metal`） |
| Release tag | pending `v0.3.2-preview.20261029.2`（`gh release view` → not found） |
| NSIS | parent-owned（本エージェントは cargo/tauri/makensis 未実行） |
| Pages live | **未公開** — `docs/` は準備済み。Actions 422 の場合は `tools/publish_gh_pages.ps1` |

## Docs section（本ターン）

### 変更ファイル

- `README.md` / `README.ja.md` / `README.zh-CN.md` — Hakua fork 向け全面整理
  - 製品版 vs エンジン版を表で明示
  - 予定 NSIS: `Strata_0.3.2-preview.20261029.2_x64-setup.exe`（404 時の注意）
  - Hakua-memory: Hermes SOUL/MEMORY、RAG/graph、Ebbinghaus、Obsidian、sleep、`hakua-chatbot.enabled`、`hakua-memory==0.3.5`
- `docs/index.html` / `docs/assets/app.js` / `docs/UPSTREAM_SYNC.txt` — Pages ソースを 20261029.2 へ
- `docs/PUBLISH_PAGES.md` + `tools/publish_gh_pages.ps1` — Actions 無効時の手動公開手順

### 検証

- ドキュメント差分のみ（ビルドなし）
- `gh release view v0.3.2-preview.20261029.2` → release not found（プレースホルダリンクは意図通り）
- Cargo.toml など親の NSIS 作業ツリー変更は **コミット対象外**

### Pages publish still needed?

**Yes.** `main` の `docs/` を更新しても、legacy `gh-pages` へ反映するまでは https://zapabob.github.io/Strata/ は旧版のまま。親が NSIS タグ後に:

```powershell
pwsh -File tools/publish_gh_pages.ps1
```

（DryRun: `-DryRun`）。SHA-256 が分かったら `docs/UPSTREAM_SYNC.txt` と download card を埋めて再実行。

## sccache fix（親コンテキストの記録）

- Symptom: `could not execute process sccache ... rustc.exe -vV (never executed)`
- Cause: process/User `RUSTC_WRAPPER=sccache` while binary missing
- Fix: cleared User + process `RUSTC_WRAPPER`; `.cargo/config.toml` already had `rustc-wrapper=""`
- Retry: `CARGO_TARGET_DIR=H:\Strata\cargo-target\desktop`, `CARGO_PROFILE_RELEASE_LTO=false`

## Residual risks

- リリース資産未公開のため README / Pages の setup.exe 直リンクは一時 404
- Actions Pages workflow は引き続き 422 の可能性
- 未測定の速度主張は追加していない
