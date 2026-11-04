# 2026-11-05_qwen36-t06-reeval-blocked{Cursor}

## 概要

T06（転送・expert residency 最適化）を計画どおり再評価し、測れる opt-in コード候補が無いことを正直に記録した。偽実装・偽速度なし。Goal complete にしない。

## 背景・要求

- Durable Qwen3.6 Hakua goal 継続
- 本ターンは T06: plan/DESIGN を読み、明確な measurable opt-in があれば実装＋RED＋RTX 5060 Ti 16GB paired；無ければ偽作業せず次ゲート or evidence-summary のみ
- UpdateGoal complete 禁止 / force 禁止 / Hermes 殺傷禁止

## 前提・判断

適用: `AGENTS.md`（PC + project）、MILSPEC baseline、CLAUDE-FABLE-5 実装前ゲート、plan T06。

判断:

1. `stream_kick` の全layer/runs 分岐と `STRATA_Q36_STREAM_ALL` は既存診断であり、新スケジューラ候補ではない
2. §5.2 gather / cost-aware rebalance は未計測コストなしでは scope 発明になる
3. T07 は hotspot プロファイル入力なし、T08 は任意品質アームで「同様に明確」ではない
4. VRAM free 15044 MiB は十分だが、候補なしのまま起動しない

## 変更対象ファイル

- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/NOTES-01-32-t06-reeval.md`（新規）
- `_docs/q36-32gb16gb/evidence-summary.json`
- `_docs/q36-32gb16gb/DESIGN.md`
- `_docs/q36-32gb16gb/Strata_Qwen36_Implementation_Plan_2026-11-02.md`
- `_docs/2026-11-05_qwen36-codex-handover-after-preview6{Cursor}.md`（更新）
- 本実装ログ

## 実装詳細

コード変更なし。T06/T07/T08 の RED テスト追加なし。既定経路バイト同一を維持。

## 実行コマンド

- `nvidia-smi --query-gpu=...` / compute-apps（VRAM free 15044 MiB、Hermes 生存確認）
- `Get-Process *hermes*`（殺傷なし）
- git status / commit / push（intake・engine-died 除外）

## テスト・検証結果

- T06 paired: **NOT_RUN**（候補 BLOCKED）
- T07 / T08: **NOT_RUN**
- Engine / unit / GPU: **未実行**（コード差分なし）

## 残留リスク

- T06 を「観測ペアだけ」で進める圧力が残る → 計画どおり拒否を継続
- 将来の gather/residency 実装は計測入力（H2D bytes、copy wait、CPU ms）が先

## 次の推奨アクション

1. T06 に入る前に、同一 slot table で transfer/CPU 計装を別チケットで小さく切る（まだ最適化ではない）
2. または T04 追加 paired（n≥5）で採用判断材料を増やす
3. T07 は Nsight/event プロファイル取得後に hotspot 1つだけ
4. UpdateGoal complete しない

## Goal

- Goal complete: **false**
