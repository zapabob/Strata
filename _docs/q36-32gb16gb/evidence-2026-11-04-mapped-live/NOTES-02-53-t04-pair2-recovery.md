# T04 pair×2 recovery — 2026-11-05 01:36–02:53 JST

- Goal complete: **false** (do not UpdateGoal complete)
- Path taken: **recover evidence + honest composite** (no fresh 50-min re-run; measurements already existed)
- Tip preserved: README honesty `1378afa8`, docs cleanup `df7dd77b` — **not reverted**

## What failed (prior agent)

1. Harness `t04_warmup_cost_pair.py` → `run-01-36-t04/` → **`PAIR_PARTIAL` exit 5**.
2. Arm A (warmup) **PASS**. Arm B (`--no-warmup`) **READY_FAIL**:
   - `cudaMalloc(&E.stage[b], max_layer + kMmqTail) failed: out of memory`
   - after `expert_host_alloc` **879168 ms** (`q36_engine.cu:3163`)
3. Arm B retry (`armB_retry1/`) **PASS** at 02:41 JST — then agent died before docs/commit (relaunch recovery).

## Recovery facts (02:53 JST)

| Item | Value |
|------|-------|
| free VRAM | **15129 MiB** (≥12 GiB gate) |
| orphan strata PIDs 43040 / 26420 / 42132 | **DEAD** — nothing to reclaim |
| Hermes | **alive, not killed** (DESIGN #6) |
| contract | UD-Q4_K_XL / 65536 / FP32 KV / MTP 2 / mapped-pack |
| unsigned digest | `64226fde…` (matches expect) |

## Pair×2 composite (honest)

| Arm | Result | Key timings |
|-----|--------|-------------|
| armA warmup (pid 43040) | PASS | load→READY **1282936.7 ms**; READY→first T **11666.5 ms**; second TTFT **1060.8 ms**; warmup wall **173.3 s** |
| armB attempt1 (pid 26420) | READY_FAIL OOM | kept as evidence |
| armB retry1 (pid 42132) | PASS | load→READY **1439964.8 ms**; READY→first T **25541.8 ms**; second TTFT **2627.3 ms**; warmup stages **absent** |

### Observational deltas (retry armB − armA)

| Endpoint | armA | armB retry | Δ |
|----------|-----:|----------:|--:|
| load→READY ms | 1282936.7 | 1439964.8 | **+157028.1** |
| READY→first T ms | 11666.5 | 25541.8 | **+13875.3** |
| second TTFT ms | 1060.8 | 2627.3 | **+1566.5** |

### Honest read (not adoption)

1. Result label: **`PAIR_RECORDED_WITH_ARM_B_RETRY`** — not a clean single-harness `PAIR_RECORDED`.
2. Direction matches pair1 (`run-23-20-t04`): `--no-warmup` did **not** buy faster READY here; first-request cost moved later.
3. n=2 still **NOT_DECIDED**. Defaults unchanged. No invented speeds.
4. First armB OOM under same free-VRAM preflight (~14.9 GiB) is a real fragility signal — do not pretend the pair was clean.

## Next clear gates (no invent T06)

| Gate | Status | Why |
|------|--------|-----|
| T06 | **BLOCKED** | prior `NOTES-01-32-t06-reeval` — no measurable scheduler/residency candidate |
| T07 | **BLOCKED_NO_HOTSPOT_PROFILE** | plan input is T02/T06 kernel profile — **none** on mapped-pack 5060 Ti path |
| T08 | **NOT_RUN** (optional) | FP16 KV not similarly clear small opt-in |
| T09 | **PARTIAL** | installer `.6` honesty advanced; speed/quality gates open |

See also: `NOTES-02-53-t07-t08-t09-gate.md`.

## Evidence paths

- `run-01-36-t04/t04-report.json` (PAIR_PARTIAL)
- `run-01-36-t04/armB_retry1/armB-retry1-report.json` (PASS)
- `run-01-36-t04/t04-pair2-composite-report.json`
- `run-01-36-t04/armA_warmup-*` / `armB_no_warmup-*` / `armB_retry1/*-stdout.txt` `*-stderr.txt`
- `nvidia-smi-*-01-35.*` / `nvidia-smi-*-02-53.*`
- this NOTES
