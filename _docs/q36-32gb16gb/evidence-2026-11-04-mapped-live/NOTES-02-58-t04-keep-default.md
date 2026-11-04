# T04 adoption decision — KEEP_DEFAULT — 2026-11-05 02:58 JST

- Goal complete: **false**
- Tip at decision: `c2242cd3` (docs tip before this turn's commit)
- Hermes: **not killed**
- Defaults changed in product code: **false** (decision only)

## Scope of this decision

| Question | Decision |
|----------|----------|
| Change product default away from legacy/on warmup? | **KEEP_DEFAULT** |
| Make `--no-warmup` the product default or a “faster start” claim? | **REJECT** (implicit in KEEP_DEFAULT) |
| Adopt unimplemented `--q36-warmup-mode bounded`? | **N/A — not implemented**; plan still requires n≥5 + RED fixtures before any ADOPT |

## Evidence used (measured only; no invented speeds)

### Pair 1 — `run-23-20-t04` / `NOTES-23-20-t04` — `PAIR_RECORDED`

| Endpoint | armA warmup | armB `--no-warmup` | Δ (B−A) |
|----------|------------:|-------------------:|--------:|
| load→READY ms | 1480524.0 | 1705414.1 | +224890.1 |
| READY→first T ms | 13603.8 | 34108.1 | +20504.3 |
| second TTFT ms | 787.0 | 1638.7 | +851.7 |

### Pair 2 — `run-01-36-t04` composite / `NOTES-02-53-t04-pair2-recovery` — `PAIR_RECORDED_WITH_ARM_B_RETRY`

| Endpoint | armA warmup | armB retry `--no-warmup` | Δ (B−A) |
|----------|------------:|-------------------------:|--------:|
| load→READY ms | 1282936.7 | 1439964.8 | +157028.1 |
| READY→first T ms | 11666.5 | 25541.8 | +13875.3 |
| second TTFT ms | 1060.8 | 2627.3 | +1566.5 |

Honesty: pair2 armB attempt1 was READY_FAIL OOM; comparison uses armB_retry1 only.

## Rationale (plan / DESIGN)

1. Plan T04 受入: 「改善しなければ計測だけ採用し、policyは既定化しない」。両 pair で `--no-warmup` は READY を早めず、初回・2回目 TTFT が悪化（費用移動）。
2. Plan / DESIGN の性能採否は「5組以上」と `load_request→first_useful_token` 改善。n=2 は **新policy ADOPT には不足**だが、**既定を変えない KEEP_DEFAULT** には十分（同じ方向の費用移動が再現）。
3. READY 秒数だけの成功指標は禁止。本決定は READY 改善主張をしない。
4. bounded warmup の RED fixture / capability flag は未実装のまま。偽実装しない。

## Explicit verdict

```
T04_ADOPTION = KEEP_DEFAULT
T04_BOUNDED_POLICY = NOT_IMPLEMENTED
T04_DEFAULTS_CHANGED = false
```

## Not claimed

- 30% load→first_useful_token 短縮（未達・未採否目標）
- n≥5 中央値の安定推定
- `--no-warmup` が常に遅い（host/IO 分散あり；方向一致のみ）
