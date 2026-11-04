# mapped-live gate 2026-11-04 21:05–22:18 JST

- Purpose: user freed VRAM — stop installer ship, remeasure, run durable mapped-live, capture Q36_STARTUP + pin-pool, then T03. DESIGN #6: do not kill Hermes. No invented speeds. Goal complete: **false**.
- Path taken: **live** (not ship).
- GPU at 21:04–21:05: RTX 5060 Ti — used **~1079 MiB** / free **~14972 MiB** (gate min 12000 → GO).
- Hermes `llama-server`: **absent**. Hermes desktop processes still listed; **not killed**.
- Unsigned `0.4.0-q36-…\strata.exe` SHA-256 **`64226fde7905821148c78b7de85ede4d291c4df8184d80866dccba014d7c02b7`** verified. Signed `b5e4d525…` untouched.

## mapped-live (`run-21-05`)

Command:

```text
py -3 _docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/launch_mapped_live_durable.py --out-dir …/run-21-05
```

- Preflight free **14982 MiB**; launched pid **28032**.
- Brief duplicate strata (second babysitter) was stopped; primary **28032** kept. Hermes untouched.
- Default 1200 s READY timeout hit during `expert_host_alloc` (~18.6 min); babysitter **kept** stdin+logs open (no mid-load pipe abort).
- stdout: `READY 65536 stop` at **21:28:28+09:00**. `launch-meta.json` → `mapped_live: READY`.

### Captured markers (stderr)

- `Q36_STARTUP … stage=dense_load … end elapsed_ms=56196`
- `Q36_STARTUP … stage=buffers … end`
- `strata-q36: mapped-pack host pin pool cudaHostAlloc 32 MiB x2 (64.00 MiB committed)`
- `Q36_STARTUP … stage=expert_host_alloc … end elapsed_ms=1116175`
- `strata-q36: hybrid experts: 41 of 256 per layer in VRAM (3.00 GiB), all 18.75 GiB in mapped file-backed host memory + cudaHost pin pool…; 1135.0 s`
- `Q36_STARTUP … stage=expert_repack … end elapsed_ms=1134970`
- warmup_prefill / warmup_decode / warmup_spec end; `warmed up in 143.6 s`
- Snapshots: `*-ready-snapshot.*` under `run-21-05/`

Observed stage timings are load evidence only — **not** a T04/T06 paired speed claim.

## T03 (`run-21-05-t03`)

| Step | Result |
|------|--------|
| launch1 READY | **PASS** (pid 18132, ~21:48:57) |
| GEN chat | **PASS** — `DONE 7 15 3104.9 910.4 stop…`; 7× `T` lines |
| STOP then exit | **PARTIAL** — `STOP` alone does not exit idle serve loop; process exited after parent closed stdin (EOF). Script later fixed to `STOP` + stdin EOF. |
| launch2 restart READY | **FAIL** — pid 31820 crashed during `warmup_prefill` begin; exit **3221226505** (`0xC0000409`). Pin-pool + expert_repack lines were captured before crash. |

T04 / T06 / T07 / T08 paired measurements: **NOT_RUN** (no fake speeds). Installer ship: **deferred** (live evidence secured first).

## Status

| Item | Result |
|------|--------|
| mapped-live pin-pool log | **PASS** |
| mapped-live READY | **PASS** |
| T03 chat | **PASS** |
| T03 stop/restart | **PARTIAL** (restart crash) |
| T04–T08 | **NOT_RUN** |
| invented speeds | **false** |
| Hermes killed | **false** |
| goal complete | **false** |

## Evidence paths

- `run-21-05/` (+ `*-ready-snapshot.*`)
- `run-21-05-t03/` (`t03-report.json`, `launch1-*`, `launch2-*`)
- `nvidia-smi-*-21-05.*`
- this NOTES
