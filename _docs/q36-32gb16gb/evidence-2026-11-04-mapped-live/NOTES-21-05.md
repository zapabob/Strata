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
| STOP then exit | **PASS** after script fix — `STOP` alone does not exit idle serve; need stdin EOF. First attempt left resident until owned-child cleanup. |
| launch2 attempt1 | **FAIL** — died in `warmup_prefill` (Cursor shell kill / orphan conflict). Logs: `launch2-*-attempt1.log`. Pin-pool was already printed. |
| orphan cleanup 22:24 | **PASS** — killed leftover mapped-pack `strata.exe` **4024** + babysitter `py` **28188** (`python` **22204** already gone). Hermes untouched. Free **15182 MiB**. Evidence: `cleanup-killed-pids.json`, `preflight-go-cleanup-22-24.json`. |
| launch2 clean retry | **PASS** — pid **37524**, READY **22:52:29+09:00**, pin-pool again, warmup_prefill end **334239 ms**, `pid_reused=false`. STOP+stdin EOF cleared strata (free **~15148 MiB**). `t03-report.json` **result=PASS** at **22:53:50+09:00**. |

T04 / T06 / T07 / T08 paired measurements: **NOT_RUN** (no fake speeds; DONE tok/s is protocol observation only). Installer ship: **deferred**.

## Status

| Item | Result |
|------|--------|
| mapped-live pin-pool log | **PASS** |
| mapped-live READY | **PASS** |
| T03 chat→stop→restart | **PASS** |
| T04–T08 | **NOT_RUN** |
| invented speeds | **false** |
| Hermes killed | **false** |
| goal complete | **false** |

## Evidence paths

- `run-21-05/` (+ `*-ready-snapshot.*`)
- `run-21-05-t03/` (`t03-report.json`, `t03-final-status.json`, `launch1-*`, `launch2-*`, `launch2-*-ready-pass.txt`)
- `cleanup-killed-pids.json`, `preflight-go-cleanup-22-24.json`, `nvidia-smi-*-cleanup-22-24.*`, `nvidia-smi-*-after-launch2-pass-22-55.*`
- `nvidia-smi-*-21-05.*`
- this NOTES
- impl log: `_docs/2026-11-04_q36-mapped-live-orphan-cleanup-launch2-pass{Cursor}.md`
