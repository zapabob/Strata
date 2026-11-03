# Qwen3.6 H: reclaim + mapped-live still BLOCKED

- **日時**: 2026-11-04 04:12–04:21 JST
- **実装AI**: Cursor
- **GPU**: RTX 5060 Ti 16GB。速度主張なし。UpdateGoal complete しない。Hermes 未殺（DESIGN #6）。

## 概要

VRAM は Hermes 占有のまま mapped-live 不可。二次ブロッカーの H: FreeGB≈0 を、モデル / `.q36epk` / 署名 component / 現行 `.5` setup を残して安全回収し、FreeGB 1.05→14.2 を得た。正直ラベル（NOT_RUN / BLOCKED）を DESIGN・計画・evidence に同期。

## 背景・要求

durable Q36 32GB/16GB Hakua。force なし。偽速度なし。他アプリ推論を殺さない。

## 前提・判断（CoT）

1. Hermes が消えていれば live → **棄却**: PID 22836/22944 生存、VRAM used 15321 MiB / free 730 MiB。
2. H: 回収すれば将来 live/release の ENOSPC は緩和 → **採択**: 観測 reclaim ~13.16 GB。npm-cache 一部は codegraph lock で残存 (~0.58 GB)。
3. 古い NSIS cargo / 旧 q36 engine / QA first-run extract は現行 `.5` と重複 → **採択して削除**（`-5` / preview `.5` / components-r3 / models は残置確認）。

## 変更対象ファイル

- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/h-disk-reclaim-04-12.json`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/preflight-blocker-04-12.json`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/nvidia-smi-*-04-12.*`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/ram-recheck-04-12.json`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/NOTES-04-12.md`
- `_docs/q36-32gb16gb/evidence-summary.json`
- `_docs/q36-32gb16gb/DESIGN.md` / `Strata_Qwen36_Implementation_Plan_*.md` / `PACKAGE_README.md`
- `_docs/q36-32gb16gb/evidence-2026-11-04-gui/NOTES.md`
- `_docs/2026-11-04_qwen36-h-disk-reclaim-mapped-live-still-blocked{Cursor}.md`（本ログ）

コード変更なし。署名 engine 非接触。

## 実装詳細

削除したもの: `H:\pip_cache`、旧 `nsis-cargo-20261103` / `-4`、旧 `q36-engine-20261103` / `q36-engine-sync`、`H:\Strata\temp\official-first-run-r*`、`H:\Strata\tmp`。`H:\npm-cache` は大部分削除だが locked remnant あり。

## 実行コマンド

```text
nvidia-smi --query-gpu=...
Get-Volume H
Remove-Item (reclaim targets with q36epk / .5 setup guards)
```

## テスト・検証結果

| 項目 | 結果 |
|------|------|
| Headroom | VRAM free 730 MiB; RAM free 7.61 GiB |
| Hermes | 生存・未殺 |
| mapped-live | BLOCKED |
| T03 chat/stop/restart | NOT_RUN |
| T04–T08 | NOT_RUN |
| H: FreeGB | 1.047 → 14.209（後 14.423） |
| keep checks | models / `.5` setup / components-r3 / nsis-5 / engine-5 = True |

## 残留リスク

- mapped-live は Hermes 解放待ち。
- `H:\npm-cache` remnant ~0.58 GB は codegraph-kernel ロック解除後に再回収可。
- native-sync / components-r3 は意図的に残置（容量必要なら別確認）。

## 次の推奨アクション

1. Hermes 終了後に unsigned `0.4.0-q36-…` digest `6fe11065…` で mapped-pack live（ctx 65536 / MTP 2）。
2. Q36_STARTUP + pin-pool 行を捕捉 → T03 restart → 正直な T04/T06。
3. Goal complete は live 証拠後のみ。
