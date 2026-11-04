# 2026-11-05 Q36 T04 observational warmup pair {Cursor}

## 概要

durable Q36 Hakua goal を継続。`main` @ `7a79384c` へ復帰し、VRAM headroom ありで T04 observational pair（mapped-pack / ctx65536 / MTP2 / warmup vs `--no-warmup`）を **PAIR_RECORDED**。既定変更なし。Goal complete にしない。Hermes 未殺。

## 背景・要求

- Codex handover: `_docs/2026-11-04_qwen36-codex-handover-plan{Cursor}.md`
- Remaining: T04–T08 paired speeds; optional installer honesty; README honesty
- 本 turn: main sync → orphan strata のみ掃除 → free≥12GiB なら T04/T06 測定優先

## 前提・判断

- DESIGN #6: Hermes / 他推論 server を殺さない
- 偽速度禁止・1 pair で製品既定を変えない
- intentional skip: `_docs/intake/` と engine-died ログ
- T06–T08 は候補 arm なしのため NOT_RUN（測定優先の結果 T04 に振った）

## 変更対象ファイル

- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/t04_warmup_cost_pair.py`（新規）
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/run-23-20-t04/**`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/NOTES-23-20-t04.md`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/nvidia-smi-*-23-18.*`
- `_docs/q36-32gb16gb/evidence-summary.json`
- `_docs/q36-32gb16gb/DESIGN.md`
- `_docs/q36-32gb16gb/Strata_Qwen36_Implementation_Plan_2026-11-02.md`
- 本実装ログ

## 実装詳細

1. `pr/q36-docs-qualify-32gb-ram` → `main` / `origin/main`（`7a79384c`）
2. nvidia-smi: free **14962 MiB**（GO）。orphan strata なし。Hermes desktop あり・llama-server なし
3. `t04_warmup_cost_pair.py` で armA warmup / armB `--no-warmup` を同一契約で連続測定
4. 結果を NOTES / evidence-summary / DESIGN / 計画 Status に正直反映（採用判断なし）

## 実行コマンド

```powershell
git fetch origin main; git checkout main; git pull --ff-only origin main
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu --format=csv
py -3 -m py_compile _docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/t04_warmup_cost_pair.py
py -3 _docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/t04_warmup_cost_pair.py
```

## テスト・検証結果

| Item | Result |
|------|--------|
| digest `64226fde…` | verified |
| armA | PASS — READY 1480524 ms; READY→first T 13603.8 ms; 2nd TTFT 787.0 ms; warmup 222.2 s |
| armB | PASS — READY 1705414 ms; READY→first T 34108.1 ms; 2nd TTFT 1638.7 ms; warmup stages absent |
| pair | **PAIR_RECORDED** / adoption **NOT_DECIDED** |
| Hermes killed | false |
| strata orphan after | none (free ~14837 MiB) |
| T06–T08 | NOT_RUN |
| Goal complete | false |

## 残留リスク

- n=1 pair。expert_host_alloc 分散が大きく、`--no-warmup` の READY 短縮は未実証
- harness の `ready_to_first_done_ms` は first-T 待ち後の逐次タイマ（NOTES に明記）
- T06 転送最適化・T07 hotspot・T08 FP16 KV・次インストーラ honesty は未着手

## 次の推奨アクション

1. 追加 T04 pairs（同条件）で中央値を取るか、実 T06 候補 arm を用意して paired する
2. 任意: `64226fde…` を載せる次 preview installer（署名 `b5e4d525…` 非接触）
3. README / upstream PR-2 docs honesty
4. **UpdateGoal complete しない**
