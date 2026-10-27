# 2026-10-27 Full Setup Abort（engine already exists）{Cursor}

**完了時刻:** 2026-10-27T08:55:19+09:00  
**実装AI:** Cursor / ボブにゃん  
**証拠:** `H:/Strata/evidence/handoff-20261027/2026-10-27_full-setup-aborted-engine-exists.md`

## 結論（親エージェント向け短文）

Hakua 版 Full Preview Setup（`...-full-setup-hakua.exe`、LastAccess≈08:53）が、共有パス  
`%LOCALAPPDATA%\Strata\components\engine\0.3.2-preview.20261027.1-windows-x86_64-cuda-cuda13`  
が既にあるため **fail-closed で正常中断**。このPCは `Programs\Strata` + Hakua overlay + 同版 engine 済み → **フルセットアップ再実行不要。既存を使え（案A）。**

## 仮説検証（CoT）

| # | 仮説 | 結果 |
|---|------|------|
| H1 | 実行したのは hakua setup | **採用** — hakua EXE LastAccess 08:53:46、Recent に hakua 系 lnk |
| H2 | Programs\Strata 拒否で止まった | **棄却** — 既定 INSTDIR は `Programs\Strata-0.3.2-preview.20261027.1`（未作成）なので Programs 拒否は未発火 |
| H3 | components engine の Require-EmptyTarget | **採用** — スクショ文言と `full_windows.py` 一致 |
| H4 | 削除して入れ直しが必要 | **棄却** — 既に同版 engine（~693MiB、receipt一致）+ Hakua marker |

## 触っていないもの

個人データ / models / Hermes / conversation DB / git tags / 既存 engine・generic フォルダ（削除なし）

## 推奨

1. **A（推奨）** ウィザード Cancel。既存 Strata + Hakua を継続  
2. B QA 用は空の H: INSTDIR でも components は実 LOCALAPPDATA 固定 → 同エラー再発しやすい  
3. C 再インストールは明示意図＋preimage＋ハッシュ証明後のみ（今回はしない）
