# Qwen3.6 headroom remeasure（still BLOCKED）

- **日時**: 2026-11-04 04:08–04:12 JST
- **実装AI**: Cursor
- **GPU**: RTX 5060 Ti 16GB。速度主張なし。goal complete にしない。

## 概要

約3時間後の headroom 再測定。Hermes `llama-server` PID 22836/22944 が存続し VRAM ほぼ満杯のため mapped-pack live / T03 chat-stop-restart / T04–T08 は実行せず、ブロッカー証拠を新タイムスタンプで追加。非GPUの host Q36 node 試験は 19/19 PASS。

## 背景・要求

durable Q36 32GB/16GB Hakua。DESIGN #6（他アプリ推論を殺さない）。未測定は未測定のまま。`.5` は出荷済み。

## 前提・判断

- Hypotheses → checks:
  1. Hermes が自然終了していれば live 可 → **棄却**: PID 同一で生存、VRAM used 15322 MiB / free 729 MiB。
  2. RAM が改善していれば RAM 単体ブロッカーは緩和 → **部分採択**: free RAM 6.82 GiB（以前しばしば <4）。ただし VRAM が一次ブロッカーのまま。
  3. 非GPU契約試験は H: 満杯でも C: cache で回せる → **採択**: 19/19 PASS。

## 変更対象ファイル

- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/preflight-blocker-04-08.json`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/nvidia-smi-*-04-08.*`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/ram-recheck-04-08.json`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/host-q36-node-tests-04-08.txt`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/NOTES-04-08.md`
- `_docs/q36-32gb16gb/evidence-summary.json`
- `_docs/q36-32gb16gb/evidence-2026-11-04-gui/NOTES.md`（remeasure 追記）
- `_docs/2026-11-04_qwen36-headroom-remeasure-still-blocked{Cursor}.md`（本ログ）

コード変更なし。署名済み engine 非接触。

## 実装詳細

1. `nvidia-smi` + RAM + process 再取得。Hermes 未殺。
2. planned unsigned engine digest 再確認 `6FE11065…`。model/pack 存在確認。
3. mapped-live ABORT。cfg.log は取らない（偽完了禁止）。
4. `node --test apps/host/tests/q36-*.test.mjs`（npm_config_cache を C: に退避）→ 19 pass。

## 実行コマンド

```text
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu --format=csv
Get-CimInstance Win32_OperatingSystem
Get-Process llama-server
Get-FileHash ...\0.4.0-q36-...\strata.exe -Algorithm SHA256
node --test tests/q36-*.test.mjs
```

## テスト・検証結果

| 項目 | 結果 |
|------|------|
| Headroom remeasure | VRAM free 729 MiB; RAM free 6.82 GiB |
| Hermes | 生存・未殺 |
| mapped-live | BLOCKED |
| T03 chat/stop/restart | NOT_RUN |
| T04–T08 | NOT_RUN |
| host q36 node tests | PASS 19/19 |
| 速度数値 | なし（捏造なし） |
| H: disk | FreeGB=0（二次ブロッカー／npm ENOSPC） |

## 残留リスク

- Hermes 占有が続く限り live 証跡は取れない。
- H: 満杯は将来の pack 書き換え・大きなログ書き込みを阻害する。
- T03 の stop/restart と paired T04/T06 は未実施のまま。

## 次の推奨アクション

1. ユーザーが Hermes を明示停止するか、プロセスが自然終了したあと planned mapped-pack serve を1回だけ実行し Q36_STARTUP + ExpertPinPool を保存。
2. H: の空きを確保（npm-cache / 一時物）。intake と engine-died ログはコミットしない方針維持可。
3. durable goal は完了にしない。
