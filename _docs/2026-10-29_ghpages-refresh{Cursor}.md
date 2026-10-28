# GH Pages refresh {Cursor}

記録: 2026-10-29T01:25+09:00

## 問題
https://zapabob.github.io/Strata/ が旧プレビュー（20261027.1 / v0.3.1 tar.7z）のまま。main tip は `0.3.2-preview.20261028.2`、上流同期リリースは `v0.3.2-preview.20261028.1`、資産付き NSIS は `v0.3.2-preview.20261027.2`。

## 対応
- `docs/index.html` / `docs/assets/app.js`（EN/JA/zh）を更新
- CTA → NSIS `v0.3.2-preview.20261027.2`（SHA-256 `83902911…`）
- 同期メモ → `v0.3.2-preview.20261028.1`
- `docs/UPSTREAM_SYNC.txt` 追加
- `origin/main` → `424d8cca`
- `origin/gh-pages` → `2b927157`（Actions 422 のため手動）

## 未達
- workflow_dispatch Deploy GitHub Pages は引き続き HTTP 422（Actions disabled）
