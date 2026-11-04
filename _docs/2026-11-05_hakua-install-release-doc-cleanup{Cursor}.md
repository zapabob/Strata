# Hakua INSTALL/RELEASE doc cleanup

- **日時**: 2026-11-05 02:37 JST
- **実装AI**: Cursor (Composer / Auto)

## 概要

`docs/HAKUA_INSTALL.md` の null バイトを除去し、`docs/HAKUA_RELEASE.md` 先頭を **0.4.0-preview.20261103.6** 要約と **.20261101.1** / **0.3.3** 歴史計測の見出し分離に再編した。

## 背景・要求

- README リライト後の残余: INSTALL の制御文字、RELEASE の `.6` / `.1` 混同リスク
- 事実のみ（SHA `784d4f99…` / 113075186 bytes、未署名 Q36 `64226fde…`、署名 CUDA `b5e4d525…` 未改変、`--latest=false`）
- AGENTS.md / README と矛盾しないこと（最小同期のみ）
- `[Docs]` commit + push。intake / engine-died は対象外。Goal complete しない。force push しない。

## 前提・判断

- INSTALL の null は `0.4.0-q36-…` の先頭 `0` を潰した 1 バイトのみ（位置 1941）。`\x00` → `0` で意味復元。
- RELEASE の詳細スイート数値は `.1` / `0.3.3` の既存記録のまま。新しい計測は発明しない。
- `gh release view` / API latest で `--latest=false`（latest は `v0.4.0-preview.20261101.1`）を再確認。
- AGENTS.md / README.md は既に `.6` アプリと `.1` 署名コンポーネントを分離済み → 同期変更なし。

## 変更対象ファイル

- `docs/HAKUA_INSTALL.md`
- `docs/HAKUA_RELEASE.md`
- 本実装ログ

## 実装詳細

1. INSTALL: `side-by-side \x00.4.0-q36-…` → `side-by-side 0.4.0-q36-…`。null 残存 0。
2. RELEASE 見出し:
   - `## Current product: 0.4.0-preview.20261103.6`
   - `## Historical measured record: 0.4.0-preview.20261101.1`（配下を `### … (.20261101.1)`）
   - `## Historical measured record: 0.3.3-preview.20261030.1`（配下を `### … (0.3.3)`）
3. `.6` 要約に setup SHA/bytes、未署名 Q36、署名 CUDA 未改変、`--latest=false` / latest 残置、T04/T06–T08 限界を明示。

## 実行コマンド

```powershell
Get-Date -Format 'yyyy-MM-dd HH:mm:ss K'
py -3 -c "...null scan / replace..."
gh release view v0.4.0-preview.20261103.6 --repo zapabob/Strata --json tagName,name,isPrerelease,publishedAt,url,assets
(Invoke-RestMethod -Uri 'https://api.github.com/repos/zapabob/Strata/releases/latest').tag_name
git add docs/HAKUA_INSTALL.md docs/HAKUA_RELEASE.md "_docs/2026-11-05_hakua-install-release-doc-cleanup{Cursor}.md"
git commit -m "[Docs] separate Hakua .6 summary from .1 measured record"
git push origin HEAD
```

## テスト・検証結果

| 確認 | 結果 |
| --- | --- |
| INSTALL null bytes | 0 |
| RELEASE null bytes | 0 |
| `.6` 必須事実（SHA/bytes/`64226fde`/`b5e4d525`/`--latest=false`） | すべて含む |
| GitHub API latest | `v0.4.0-preview.20261101.1` |
| AGENTS.md / README.md 矛盾 | なし（未変更） |
| 新規計測の発明 | なし |

## 残留リスク

- `.1` / `0.3.3` 本文の計測文言自体は再測定していない（見出し分離のみ）。
- INSTALL 日本語節の「7zを選んだ場合」は条件付き表現のまま（`.6` タグに 7z は無い）。
- autocrlf により INSTALL の行末正規化が diff 全体に見える可能性があるが、意味変更は null→`0` のみ。

## 次の推奨アクション

- 必要なら INSTALL 日本語の 7z 言及を `.6` 事実に合わせて短縮。
- Goal complete は別判断。T04 adoption / T06–T08 は未決・未実施のまま。
