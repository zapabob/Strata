# T08 gate split — refuse-before-serve vs measured FP16 — 2026-11-05 02:58 JST

- Goal complete: **false**
- No FP16 KV engine implementation invented
- No measured FP16 quality arm run
- Hermes: **not killed**

## Split (honest)

| Sub-gate | Result | Evidence |
|----------|--------|----------|
| Refuse non-FP32 / explicit `--kv` before spawn | **PASS** | `prepareQ36Launch` already refuses `requested.persistentKv !== 'fp32'`; user `--kv fp16|int8` → `unsupported_setting`. New unit coverage: `apps/host/tests/q36-run-contract.test.mjs` → `T08 refuse-before-serve…` |
| Opt-in `--q36-kv-storage fp16` engine path + quality gates | **NOT_RUN** | Plan §T08 optional / out of required order; large KV surface; quality gates undefined. Same verdict as `NOTES-01-32-t06-reeval` / `NOTES-02-53-t07-t08-t09-gate` |

## What was not done

- No FP16 persistent KV write/read path in `q36_engine.cu`
- No paired FP16 vs FP32 latency/quality numbers (would be invented if claimed)
- No default change away from FP32 KV (contract remains FP32)

## Why refuse-only still advances T08

DESIGN #4 / plan T01: unsupported explicit settings must fail before start, not strip-and-continue. T08’s measured capacity arm remains optional; sealing the refuse gate prevents a false “FP16 applied” success without inventing storage.
