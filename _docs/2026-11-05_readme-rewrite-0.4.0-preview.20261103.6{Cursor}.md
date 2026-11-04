# README rewrite for Hakua 0.4.0-preview.20261103.6

- **日時**: 2026-11-05 02:13 JST
- **実装AI**: Cursor (Composer / Auto)

## 概要

公開タグ `v0.4.0-preview.20261103.6` の事実に合わせて、主 README をリライトし、七言語ローカライズの版番号・ハッシュ・バイト数・署名区別・T04/T06–T08 未採用を同期した。

## 背景・要求

- 直前 ship: `0.4.0-preview.20261103.6`
- Setup SHA-256 `784d4f992443a43076e7de8dbcdc624b35d95e97e13b716ea9de0e13a1baeac9`（113,075,186 bytes）
- 未署名 Q36 digest `64226fde…` は live-proven；署名 CUDA `b5e4d525…` は未改変
- 上流 Niko1221 インストーラーと混同しないこと
- T04 adoption / T06–T08 を過大主張しないこと

## 前提・判断

- 一次根拠: `docs/HAKUA_INSTALL.md`, `docs/HAKUA_RELEASE.md`, `AGENTS.md`, `gh release view v0.4.0-preview.20261103.6`
- このタグの公開資産は setup EXE + SHA256SUMS のみ（7z なし）
- 英語を正本とし、他言語は事実同期（全文再翻訳はしない）

## 変更対象ファイル

- `README.md`（全面リライト）
- `README.ja.md`（英語骨格に合わせて再構成）
- `README.zh-CN.md` / `README.de.md` / `README.fr.md` / `README.es.md` / `README.pt-BR.md` / `README.pl.md`（バイト数・step4・署名表・T04/T06–T08）
- 本実装ログ

## 実装詳細

1. 冒頭で zapabob Hakua fork / 上流 Niko1221 経路の非同一を明示。
2. Engines 表で `.6` 未署名アプリ、`.20261101.1` 署名 CUDA（`b5e4d525…`）、未署名 Q36（`64226fde…`）を分離。
3. Q36 節に T04 = NOT_DECIDED、T06/T07/T08 未実施を明記。
4. 欧州語 README に残っていた誤サイズ `114,984,071` を `113,075,186` に修正。
5. 「同リリースの署名エンジン」と読める step4 を訂正。

## 実行コマンド

```powershell
gh release view v0.4.0-preview.20261103.6 --repo zapabob/Strata --json tagName,name,publishedAt,assets
Get-Date -Format 'yyyy-MM-dd HH:mm:ss K'
py -3 _docs/_tmp_readme_sync.py
py -3 _docs/_tmp_readme_sync2.py
```

## テスト・検証結果

| 確認 | 結果 |
| --- | --- |
| Release assets size/digest | EXE 113075186 / SHA-256 `784d4f99…` 一致 |
| 八言語 `NOT_DECIDED` | すべて含む |
| 八言語 `b5e4d525` | すべて含む（zh/EU 含む） |
| 誤バイト `114984071` | 残存なし |
| ネイティブ話者レビュー | 未実施 |

## 残留リスク

- EU/zh の文体は機械同期。ネイティブレビュー未実施。
- `HAKUA_RELEASE.md` 本文の上部は `.6` を述べつつ、下段の詳細計測は `.20261101.1` 記録のまま。README は混同しないよう分離したが、RELEASE 自体の再編は本作業外。
- `docs/HAKUA_INSTALL.md` に制御文字の痕跡があり得る（本作業では未修正）。

## 次の推奨アクション

- 必要なら `HAKUA_INSTALL.md` の null バイト掃除と、RELEASE 先頭の `.6` 要約と `.1` 詳細の見出し分離。
- ネイティブ話者による EU/zh 文体レビュー。
