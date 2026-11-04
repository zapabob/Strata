# 2026-11-05_q36-t07-hotspot-profile-capture{Composer}

## 概要

Durable Qwen3.6 Hakua goal を tip `0a7d0f2a` から継続。T07 の前提である hotspot プロファイル欠落を、DESIGN/plan 既定の CUDA events/host timing 代替で実アンブロックした。偽速度なし。UpdateGoal complete しない。Hermes 未殺。

## 背景・要求

- 残ゲート: T06 / T07 / T08 measured / T04 bounded
- 優先: DESIGN が既に指定する最高忠実度の actionable（新スケジューラ発明禁止）
- 本ターン判定: T07 profile capture path（`STRATA_Q36_HOTSPOT_PROFILE`）が最優先

## 前提・判断（CoT）

1. T06 cost-aware rebalance / gather は計測入力なしでは scope 発明 → 見送り
2. T08 measured FP16 は品質 gate 未定義 → 見送り
3. T04 bounded は n≥5 + RED 未実装 → 偽 n=5 禁止
4. Plan §T07: Nsight 不可時は CUDA events/host timing + `hardware_counters=null` 記録 → **採用**

## 変更対象ファイル

- `include/strata/qwen35/hotspot_trace.hpp`（新規）
- `src/qwen35/q36_engine.cu`（opt-in 計装）
- `tests/qwen36/hotspot_log_analysis.py`, `test_hotspot_log_analysis.py`
- `apps/host/server/q36-run-contract.mjs` + test（digest `907341c7…`）
- `docs/HAKUA_RELEASE.md`
- `_docs/q36-32gb16gb/{DESIGN,計画書,GATE_MATRIX,evidence-summary,WHAT_UNBLOCKS,NOTES-03-54,…}`
- 本実装ログ

## 実装詳細

- env unset 時は既定経路に同期を足さない
- env set 時のみ GDN/attn/MoE/stream/rebalance を計測し `Q36_HOTSPOT schema=1` を stderr へ
- mapped-live 1 回キャプチャ: dominant host bucket = **gdn**

## 実行コマンド

- `py -3 -m unittest discover -s tests/qwen36 -p test_hotspot_log_analysis.py -v` → 4 OK
- `cmake --build H:\Strata\releases\hakua040-native-sync-20261103 --config Release --target strata --target strata-q36 --parallel 2` → exit 0
- package + robocopy → `%LOCALAPPDATA%\Strata\components\engine\0.4.0-q36-…`
- `node --test apps/host/tests/q36-run-contract.test.mjs` → 11 pass
- `launch_mapped_live_durable.py` + `STRATA_Q36_HOTSPOT_PROFILE=1` → READY + hotspot warmup line

## テスト・検証結果

| 項目 | 結果 |
|------|------|
| Hotspot unit | PASS (4) |
| Host contract | PASS (11) |
| T07 profile capture | **PASS** |
| T07 kernel opt-in | NOT_RUN |
| T06 scheduler | BLOCKED（計測入力のみ取得） |
| Signed `b5e4d525…` | untouched |
| Hermes | not killed |
| Goal complete | false |

## 残留リスク

- diagnostic_sync は wall を膨らませる → paired 速度主張に使わない
- `hardware_counters=null`（Nsight Compute 未取得）
- 製品 `.6` installer の allowlist はまだ旧 digest 主導（Host allowlist は新 digest 追加済み）

## 次の推奨アクション

1. `WHAT_UNBLOCKS.md` の T07 GDN opt-in（fallback 付き）を 1 候補だけ
2. T06 は RED route-once テスト後にのみ gather/rebalance
3. UpdateGoal complete しない
