# Qwen3.6 計画ギャップ監査 + T05-B pin pool 寿命

- **日時**: 2026-11-03 23:40 JST
- **実装AI**: Cursor
- **製品**: インストール済み `0.4.0-preview.20261103.4`（commit `ad42648f` 系）。未署名。spill 不合格。速度未計測。

## 概要

T00–T09 を証拠で突き合わせた。T05-B の host pin pool（提案 2×32 MiB）の **寿命機械だけ** を CPU テストとして追加した。エンジンには未接続。既定経路は変えていない。T04 / T06 / T07 / T08 と対の速度計測は NOT_RUN のまま。

## 要求別ステータス

| ID | 状態 | 証拠 |
|----|------|------|
| T00 fixture / binding | PARTIAL | `_docs/q36-32gb16gb/*`、各種 `_docs/2026-11-03_*`。Windows baseline 速度は NOT_RUN |
| T01 contract / fail-closed | DONE | `q36-run-contract.mjs` + host tests（55 pass 系） |
| T02 startup stages | DONE（source + packaged） | `q36-startup-events.mjs`、engine stderr、`.4` packaged tail |
| T03 RAM gate / stop ownership | PARTIAL | legacy physical gate 実測あり。GUI chat/stop/restart クリックは未実施 |
| T04 bounded warmup | NOT_RUN | 契約で拒否。対計測なし。既定化しない |
| T05-A mapped-pack | DONE（opt-in） | `expert_store.*`、cold/reuse/serve ログ。検証費用は隠さない |
| T05-B pin pool 2×32 MiB | PARTIAL | 本変更で寿命機械 + `q36_transfer_lifetime_test`。**engine wire-up なし** |
| T06 transfer schedule | NOT_RUN | 対計測なし。既定化しない |
| T07 CUDA hotspot | NOT_RUN | 対計測なし。既定化しない |
| T08 FP16 KV | NOT_RUN | 任意。本線外 |
| T09 build/install/release/README | PARTIAL | `.3`/`.4` 出荷済み。`--latest=false`。署名なし。paired 速度・GUI E2E 未完 |
| 不変条件（65536 / FP32 / MTP2 / prefill auto / opt-in / fail-closed / no force） | DONE | 契約・README・リリースノート |

## 今回の実装

- `ExpertPinPool` / `PinSlotState`（Reusable → HostFilling → H2dInFlight → Reusable）
- 既定 2 slot × 32 MiB = 64 MiB committed
- `tests/qwen35/q36_transfer_lifetime_test.cpp` + CMake test
- **未実施**: `cudaHostAlloc`、`q36_engine.cu` 接続、速度主張、新インストーラ

## 検証

| 項目 | 結果 |
|------|------|
| `q36_transfer_lifetime_test` | exit 0（`cl` 直ビルド） |
| `q36_expert_store_test` | 再実行予定／同バッチ |

## 残留リスク

- pin pool はエンジン未接続のため、mapped-pack の転送経路は従来どおり。
- T04/T06/T07 と 5 組 paired は未計測。目標の −30% は未達成・未主張。
- legacy UD-Q4_K_XL は本機の物理 RAM gate で拒否され得る。

## 次の推奨アクション

1. pin pool を mapped-pack の opt-in 転送へ接続する前に、同条件の対計測計画を書く。
2. T04/T06/T07 は計測なしに既定化しない。
3. T09 の GUI chat/stop/restart を別記録で実施する（速度主張なし）。
