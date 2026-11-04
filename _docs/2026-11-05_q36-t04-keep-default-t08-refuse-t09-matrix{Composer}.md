# 2026-11-05_q36-t04-keep-default-t08-refuse-t09-matrix{Composer}

## 概要

Durable Qwen3.6 Hakua goal を tip `c2242cd3` から継続。偽速度・T06 scheduler・T07 hotspot profile は発明せず、計測根拠だけで T04 **KEEP_DEFAULT**、T08 **refuse-before-serve PASS**（measured FP16 は NOT_RUN）、T09 **§7 gate matrix seal** まで前進。Goal complete は false のまま。

## 背景・要求

- State tip ~`c2242cd3`：`.6` shipped、T04 n=2 same direction / adoption NOT_DECIDED、T06–T07 BLOCKED、T08 NOT_RUN、T09 PARTIAL
- Contract: UD-Q4_K_XL / ctx 65536 / FP32 KV / MTP 2 / mapped-pack opt-in / refuse unsupported / never strip private-cache
- Do NOT UpdateGoal complete / no force / no kill Hermes

## 前提・判断

1. Plan T04 は新policy ADOPT に n≥5 を要求。一方「改善しなければ既定化しない」により、n=2 同方向の費用移動証拠で **KEEP_DEFAULT** は正当。
2. T08 の measured FP16 実装は発明禁止。既存 Host 契約の非 FP32 拒否を明示テストで封印するだけ。
3. T07 instrumentation hook は DESIGN に未指定のため追加しない。
4. Hermes.exe 生存・free VRAM ~15190 MiB を確認。未殺。

## 変更対象ファイル

- `apps/host/tests/q36-run-contract.test.mjs` — T08 refuse 単体テスト追加
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/NOTES-02-58-t04-keep-default.md`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/NOTES-02-58-t08-refuse-gate.md`
- `_docs/q36-32gb16gb/GATE_MATRIX_SECTION7.md`
- `_docs/q36-32gb16gb/DESIGN.md` / `Strata_Qwen36_Implementation_Plan_2026-11-02.md` / `evidence-summary.json`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/run-01-36-t04/t04-pair2-composite-report.json`

## 実装詳細

- T04: pair1/pair2 の READY→first T / second TTFT 悪化を根拠に product default warmup を KEEP_DEFAULT。bounded policy は NOT_IMPLEMENTED。
- T08: `requested.persistentKv` ∈ {fp16,int8,q4_0,k8v4} と user `--kv fp16|int8` の起動前拒否を unit で固定。
- T09: §7 matrix を PASSED/FAILED/BLOCKED/NOT_RUN/PARTIAL で封印。残件を明示。

## 実行コマンド

```powershell
Get-Date -Format "yyyy-MM-dd HH:mm:ss K"
nvidia-smi --query-gpu=... ; nvidia-smi --query-compute-apps=...
node --test tests/q36-run-contract.test.mjs   # cwd apps/host
```

## テスト・検証結果

- `q36-run-contract.test.mjs`: **11 pass / 0 fail**（うち新規 T08 refuse 1）
- Live T04 re-pair: **NOT_RUN**（既存 n=2 で採用判断可能と判断）
- T06/T07: 引き続き BLOCKED（発明なし）
- Hermes killed: **false**

## 残留リスク

- Goal 完了不可：T06/T07 BLOCKED、T08 measured NOT_RUN、T04 bounded 未実装、signed engine 未 pin、remote CI NOT_RUN
- pair2 は armB OOM retry 複合 — クリーン n≥5 ではない

## 次の推奨アクション

1. 実測可能な T06 residency/transfer 候補が出るまで scheduler を触らない
2. T07 は Nsight/host event profile 取得後のみ
3. T08 measured FP16 は品質 gate 定義後の任意 arm
4. UpdateGoal complete は全 gate 監査後のみ
