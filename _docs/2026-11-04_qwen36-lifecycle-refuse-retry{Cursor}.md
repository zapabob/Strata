# Qwen3.6 T03 lifecycle refuse / no mutated retry

- **日時**: 2026-11-04 00:44–00:50 JST
- **実装AI**: Cursor
- **GPU**: RTX 5060 Ti 16GB。対の速度計測は未実施。T04 / T06 / T07 / T08 は NOT_RUN。

## 概要

T00–T09 を現行ツリーと `v0.4.0-preview.20261103.5` で証跡監査した。本ターンは起動前拒否と同一契約の自動再試行禁止を前進させた。18.75 GiB legacy arena 起動と速度主張はしていない。durable Q36 goal は完了にしない。

## 背景・要求

`_docs/q36-32gb16gb` DESIGN 不変条件: unsupported は起動前拒否、private-cache を削除して成功扱いにしない、同一 configDigest の自動再試行禁止。製品 `.5` / pin-pool は既出荷。

## 前提・判断

- 本機 `apps/host/hakua-chatbot.enabled` があるため、packaged + Qwen3.6 は privacyRequired で拒否される（正しい契約）。
- chatbot オフ時でも、失敗後の `dropParallel` 再試行が Q36 の parallel を変えていた。saferStart は既に null だが、parallel 落としまでは除外されていなかった。
- T04–T08 は対計測なしに既定化しない。legacy 18.75 GiB arena は本機で起動しない。

## 変更対象ファイル

- `apps/host/server/native-control.mjs` — Q36 を safer/dropParallel 再試行から除外; private-memory 二重ガード; `STRATA_HAKUA_CHATBOT=0|false|no|off` で明示オフ
- `apps/host/tests/q36-load-lifecycle.test.mjs` — 新規（private-cache 拒否 / Hakua memory 拒否 / no second try）
- `bench/q36-32gb16gb/bindings/host.json` — 製品 `.5` digest・PCIe gen3 x8・DisplayVersion（baseline は NOT_RUN のまま）
- `_docs/q36-32gb16gb/evidence-summary.json` — `PARTIAL_IMPL_GPU_SPEED_NOT_RUN`
- `tests/qwen36/test_startup_log_analysis.py` — 部分実装ステータスを許容（速度 PASS は禁止）

## 実装詳細

1. `allowed = … && !isQwen36Config(cfg)` で Q36 の第二試行を封じる。
2. `configureDesktopMemory` 直前に Q36 + wantPrivateMemory を再拒否（strip-and-continue 防止）。
3. lifecycle テストで Control `start` 回数 0（拒否）と 1（失敗後に再試行なし）を assert。

## 実行コマンド

```text
node --test apps/host/tests/q36-load-lifecycle.test.mjs apps/host/tests/q36-run-contract.test.mjs apps/host/tests/q36-capabilities.test.mjs apps/host/tests/q36-progress.test.mjs
py -3 -m unittest discover -s tests/qwen36 -p 'test_startup_log_analysis.py' -v
gh release view v0.4.0-preview.20261103.5 --repo zapabob/Strata
```

## テスト・検証結果

| 項目 | 結果 |
|------|------|
| host q36 tests | 19 pass / 0 fail |
| `test_startup_log_analysis.py` | 7 ok |
| T04 / T06 / T07 / T08 | NOT_RUN |
| GUI chat/stop/restart | NOT_RUN |
| 対の速度計測 | NOT_RUN |
| 18.75 GiB legacy arena 起動 | 未実施（計画どおり拒否優先） |

## 監査表（本ターン時点）

| ID | 状態 | 証拠 |
|----|------|------|
| T00 | PARTIAL | `bench/q36-32gb16gb/*`、fixture GREEN、Windows baseline NOT_RUN |
| T01 | DONE | `q36-run-contract` + private-cache refuse tests |
| T02 | DONE | startup events source+packaged（`.4`/`.5`） |
| T03 | PARTIAL | RAM gate / refuse / no mutated retry GREEN。GUI E2E 未 |
| T04 | NOT_RUN | 対計測なし |
| T05-A/B | DONE (opt-in) | mapped-pack + ExpertPinPool H2D、digest `6fe11065…` |
| T06 | NOT_RUN | 対計測なし |
| T07 | NOT_RUN | 対計測なし |
| T08 | NOT_RUN | 任意 arm |
| T09 | PARTIAL | `.5` NSIS/release/README。GUI E2E・paired 速度未 |

## 残留リスク

- Hakua chatbot 有効時、Qwen3.6 は private 隔離未検証のため packaged 起動拒否のまま（意図的）。mapped-pack でも同等隔離は未証明。
- pin-pool H2D の実モデル起動ログ確認は未実施。
- T04–T08 と 5 組 paired は未計測。−30% 目標は未達成・未主張。

## 次の推奨アクション

1. chatbot オフまたは専用 harness で mapped-pack 1 回の起動ログ（pin-pool 行）を取る。速度比較にしない。
2. T04/T06/T07 は対計測計画が揃うまで既定化しない。
3. T09 GUI chat/stop/restart を別記録で実施する。
4. durable Q36 goal は完了にしない。
