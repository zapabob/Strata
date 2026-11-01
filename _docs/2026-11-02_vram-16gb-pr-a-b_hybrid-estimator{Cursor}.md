# Strata 16GB VRAM最適化 — PR-A / PR-B 実装ログ

- 日時: 2026-11-02 08:24 JST
- 実装AI: Cursor (Composer)
- ブランチ: `feat/vram-16gb-pr-a-b`
- 計画書: `_docs/Strata_RTX5060Ti_16GB_Implementation_Plan_2026-11-02.md`

## SHA固定（実装開始時に再確認）

| 項目 | SHA |
| --- | --- |
| fork HEAD (`zapabob/Strata`) | `b52a198300f11437b1ed2d2cc373aa73f60ea055` |
| upstream HEAD (`Niko1221/Strata`) | `c62d5e3a15b40ea51c96aae9e8d36928965f53ab` |
| 計画書記載値との一致 | 一致 |
| Hikari revision (pin) | `c42fdf9debd1ba8daf4ac171d81b2052f841058f` |
| Prism source (pin) | `73bfe6cc485554822f80c473a3c0c4f25e80f41b` |

実機: Windows 11 Pro 10.0.26300 / RTX 5060 Ti 16311 MiB / Ryzen 5 4500 / RAM ≈32 GiB。  
idle時に `llama-server` / Hermes / strata-desktop が共存（自動killなしで可視化）。

## PR-A: 基準計測・診断基盤

### 追加

- `apps/host/server/run-observation.mjs` — `RunObservation` schema v1（requested / effective 分離）
- `apps/host/server/vram-observation.mjs` — 専用VRAMと Windows shared GPU memory を別フィールド
- `apps/host/tests/run-observation.test.mjs`
- `bench/strata-16gb/` — schema / workload manifest / `run-windows.ps1` / `capture-baseline.mjs`
- 実測: `bench/strata-16gb/results/baseline-20261102-082352.json`

### 受入確認

- requested.context=131072 に対し effective.context が小さい場合は `compareContextCapacity` が非比較失敗
- 欠損値は `null`（0に偽装しない）
- baseline観測例:
  - dedicated: total=16311 / used=9452 / free=6599 / reserved=261 MiB
  - shared: used=177 MiB（専用と非混同）
  - sources: `nvidia-smi`, `windows-gpu-counters`

## PR-B: Hybrid Memory Estimator

### 追加・変更

- **新規** `apps/host/server/model-memory.mjs`
- **新規** `apps/host/tests/model-memory.test.mjs`
- `apps/host/server/gguf.mjs` — `full_attention_interval` / `attention.recurrent_layers` / SSMキーを allowlist に追加。整数配列は `{count,values}` で保持
- `apps/host/server/local-models.mjs` — hybrid層で `kvKbPerToken` を算定、`memoryPlan` を付与
- `apps/host/tests/local-models.test.mjs` — Hikari fixture 追加

### 必須テストベクトル（全合格）

| Fixture | 期待 | 結果 |
| --- | --- | --- |
| Hikari 64 / interval 4 | attention 16 / recurrent 48 | PASS |
| Q8_0 @ 131072 | Attention KV **4.25 GiB** | PASS |
| Q4_0 @ 131072 | **2.25 GiB** | PASS |
| FP16 @ 131072 | **8.00 GiB** | PASS |
| mixed K=q8_0 V=f16 | 6.125 GiB | PASS |
| unknown arch | confidence=low, fits=null | PASS |
| 異常 metadata | NaN/負値なし | PASS |

`fits` は楽観合算では決して `true` にしない。4.25 GiB は Attention KV 理論値であり full GPU fit 宣言ではない。

## テスト

```powershell
cd apps/host
node --test tests/model-memory.test.mjs tests/run-observation.test.mjs tests/local-models.test.mjs tests/kv-settings.test.mjs
# 32 pass / 0 fail
```

## ロールバック手順

1. ブランチ破棄または該当ファイルを revert:
   - `apps/host/server/{run-observation,vram-observation,model-memory}.mjs`
   - `apps/host/server/{gguf,local-models}.mjs` の本PR差分
   - `apps/host/tests/{run-observation,model-memory}.test.mjs` と local-models 追記
   - `bench/strata-16gb/`
2. `gguf.mjs` の allowlist を元に戻すと hybrid metadata は再び読み飛ばされる（旧挙動＝全層KV上界）。
3. main への merge / push / release は未実施（計画書どおり段階ゲート待ち）。

## 未着手（次PR）

- PR-C: RunPlan 統一（GUI/server/argv）
- PR-D: VRAM-aware Automatic GPU placement（1536 MiB display reserve 維持）
- PR-E〜G: Hakua session prefix / native autotune / 研究経路

## 注意

作業ツリーには本PR以外の GDN 実験・Hikari 復旧ドキュメント等の未コミット変更が共存。本PRのコミット時は関連ファイルのみを stage すること。commit / push は未実施（ユーザー指示待ち）。
