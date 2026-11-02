# README 八言語リライト

- **日時**: 2026-11-02 19:05 JST
- **実装AI**: Cursor (Composer)

## 概要

公開済み `0.4.0-preview.20261101.1`（2026-11-02 差し替え EXE）と Hikari＝Load with Strata 前提で、八言語 README を全面リライトした。

## 変更対象

- `README.md` / `README.ja.md` / `README.zh-CN.md`
- `README.de.md` / `README.fr.md` / `README.es.md` / `README.pt-BR.md` / `README.pl.md`

## 実装詳細

1. TLDR を番号付き導入に整理（SHA256SUMS・2026-11-02 digest 差し替え注意・トレイ完全終了）。
2. インストーラー同梱 vs 別配布（署名エンジン / 重み）を表で明示。
3. モデル経路を三分: ネイティブ / Hikari PQ2_0（Load with Strata）/ TurboQuant（K=FP16）。
4. Agent は Strata/supervisor 経路でのみローカル実体を使える旨を短く記載（未測定の速度主張なし）。
5. 版表・制限・開発コマンドは HAKUA_RELEASE / INSTALL と整合。

## 残留リスク

- 他言語は英語骨格からの翻訳。ネイティブ話者レビューは未実施。
- Agent / web_search は製品スイート再測定ではなく実装同梱の説明レベル。

## 次の推奨

- 必要なら `[Docs] rewrite eight-language READMEs for 0.4.0 installer rebuild` で main に commit/push
