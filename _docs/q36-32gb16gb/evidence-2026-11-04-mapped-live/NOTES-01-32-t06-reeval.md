# T06 re-evaluation — 2026-11-05 01:32 JST

- Goal complete: **false** (do not UpdateGoal complete)
- Path taken: **evidence-only** (no fake T06 code, no paired speed claim)

## What T06 is (plan)

`Strata_Qwen36_Implementation_Plan_2026-11-02.md` §T06 / PR-6:

- Transfer + expert residency optimization on measured reuse/cost
- Touch points: `stream_kick`, `moe_hybrid_gpu`/`moe_hybrid_cpu`, `rebalance`, T05 store
- Required tests (absent): `tests/qwen35/q36_stage_scheduler_test.cpp`, `q36_residency_test.cpp`
- Acceptance: same-route process once (no miss/dup), race 0; paired E2E copy-wait or CPU-wait down without hurting token latency; keep full-layer when that shape wins
- Must not change routing top-k / weights; must not drop unselected experts from compute

## Candidate hunt (static, this turn)

| Near-miss | Why rejected (not inventing scope) |
|---|---|
| Paired `STRATA_Q36_STREAM_ALL` vs default | Existing env diagnostic only — evidence already says T06 is **not** a second observational pair |
| CLI wrap of `2 * n_slots < ne` whole-layer heuristic | Plumbing around an existing RTX 3060 comment; no new measured scheduler / gather / residency policy |
| §5.2 selected-expert gather + compact index | Needs measured \(D_{full}-D_{selected}\) vs gather/sync cost; no such profile on 5060 Ti mapped-pack path |
| Cost-aware `rebalance` (CPU save − transfer / byte) | Needs measured CPU/GPU/H2D costs as inputs; inventing weights would fake T06 |
| T07 one CUDA hotspot | Plan input is T02/T06 hotspot profile — **none** for this path |
| T08 `--q36-kv-storage fp16` | Optional quality arm, out of required order, large KV surface — **not similarly clear** as a small opt-in |

**Verdict:** no clear measurable opt-in T06 code candidate without inventing scope. **T06 = NOT_RUN / BLOCKED.** No RED tests added. No engine/default change. No invented speeds.

## Machine / process (facts only)

- GPU: NVIDIA GeForce RTX 5060 Ti, 16311 MiB total
- VRAM free at re-eval: **15044 MiB** (unused for fake T06)
- Hermes: **not killed** (PIDs observed include 8024, 26248, 26680, 26836, 27640 + hermes-watchdog 13284)
- Tip at start: `0f6d15ab` (preview `.6` ship)
- Unsigned engine digest remaining: `64226fde…`; signed `b5e4d525…` untouched

## Remaining for goal

- T04 adoption: **NOT_DECIDED** (n=1 observational)
- T06 / T07 / T08 paired: **NOT_RUN**
- T09 full close: partial (installer honesty advanced; speed/quality gates open)
- Do not change defaults from T04; do not force-push; skip intake + engine-died from commits
