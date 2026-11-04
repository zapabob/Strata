# T07 hotspot profile capture — 2026-11-05 03:32–03:54 JST

- Goal complete: **false** (do not UpdateGoal complete)
- Hermes killed: **false**
- Invented speeds: **false**
- Path: opt-in `STRATA_Q36_HOTSPOT_PROFILE=1` (diagnostic sync arm). Default path unchanged when unset.

## What unblocked

Plan §T07 requires a kernel shape/time profile before any hotspot opt-in. Prior status was `BLOCKED_NO_HOTSPOT_PROFILE`. This turn:

1. Added `include/strata/qwen35/hotspot_trace.hpp` + engine counters behind env flag
2. RED/GREEN: `tests/qwen36/test_hotspot_log_analysis.py` (4 pass)
3. Rebuilt unsigned q36 (`907341c74d5a9f26…`), installed side-by-side only; signed `b5e4d525…` untouched
4. One mapped-live capture with hotspot ON → `run-hotspot-03-32/`

## Capture facts (warmup phase only)

From `run-hotspot-03-32/stderr.log`:

```
Q36_HOTSPOT schema=1 phase=warmup layers_gdn=120 layers_attn=44
gdn_host_ms=5936.797 attn_host_ms=444.887 moe_gpu_host_ms=66.592 moe_cpu_ms=4090.766
stream_copy_wait_ms=10.455 stream_mmq_ms=606.926
stream_h2d_bytes=20127436800 stream_d2d_bytes=0
hy_cpu=3631 hy_gpu=617 hy_swaps=0 rebalance_h2d_bytes=0
hardware_counters=null note=diagnostic_sync
```

Dominant host bucket (parser): **gdn** (not sold as a paired speedup; diagnostic syncs inflate walls).

Also: pin-pool `32 MiB x2`; placement ~1078.3 s; READY true; digest `907341c7…`.

## Gate status after this turn

| Gate | Status |
|------|--------|
| T07 profile capture | **PASS** (CUDA-event/host timing substitute; HW counters null) |
| T07 one kernel opt-in | **NOT_RUN** (do not invent; next = GDN candidate behind fallback) |
| T06 scheduler | still **BLOCKED** for policy code; transfer/CPU bytes now measured as inputs |
| T08 measured FP16 | still **NOT_RUN** |
| T04 bounded n≥5 | still **NOT_RUN** / KEEP_DEFAULT |

## Machine

- RTX 5060 Ti 16GB; free before launch ~14841 MiB; after stop ~14982 MiB
- Hermes PIDs observed alive after stop (not killed)
