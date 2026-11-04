# mapped-live gate 2026-11-04 20:56–20:57 JST

- Purpose: continue durable Q36 Hakua goal after handover `b331b258`. Review/commit durable launcher PIPE→OS-file rewrite; remeasure headroom; launch only if free VRAM ≥ 12000 MiB. DESIGN #6: do not kill Hermes. No invented speeds. Goal complete: **false**.
- GPU at 20:56 CSV: RTX 5060 Ti — used **15887 MiB** / free **164 MiB** / util 4%.
- Launcher preflight at 20:57: used **15720 MiB** / free **331 MiB** (gate min 12000).
- Hermes `llama-server` still present (**2**): PIDs **3108**, **19816** under `C:\Users\downl\.hermes\llama\prism-b10826-c9c34bc\bin\llama-server.exe` (WS ~698 / ~1135 MB). Historical PID 14572 not seen this turn. **Not killed.**
- Hermes desktop process also listed on compute-apps (`Hermes.exe` PID 26836). Untouched.
- RAM: total 31.87 GiB, free **~4.94 GiB** at 20:56.
- Unsigned `0.4.0-q36-…\strata.exe` SHA-256 **`64226fde7905821148c78b7de85ede4d291c4df8184d80866dccba014d7c02b7`** verified. Signed `b5e4d525…` untouched.

## What ran

1. Reviewed uncommitted `launch_mapped_live_durable.py` (OS file redirect + stdin babysitter; 18:14 PIPE abort fix). `py -3 -m py_compile` OK → committed `f4504a3d`.
2. Timestamped headroom evidence: `nvidia-smi-*-20-56.*`, `ram-recheck-20-56.json`.
3. Durable launcher:
   ```text
   py -3 _docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/launch_mapped_live_durable.py --out-dir …/run-20-56-gate
   ```
   **exit 4 BLOCKED** — `free VRAM 331 MiB < min 12000`; 2 llama-server; Hermes not killed.
4. No mapped-pack child started. **Q36_STARTUP / pin-pool not applicable** (gate refused before launch).

## Status

| Item | Result |
|------|--------|
| mapped-live pin-pool log | **BLOCKED** (VRAM headroom) |
| T03 chat→stop→restart | **NOT_RUN** |
| T04 / T06 / T07 / T08 | **NOT_RUN** |
| invented speeds | **false** |
| Hermes killed | **false** |
| goal complete | **false** |
| durable launcher commit | `f4504a3d` |

## Evidence paths

- `run-20-56-gate/launch-meta.json`
- `nvidia-smi-recheck-20-56.txt` / `nvidia-smi-query-20-56.csv` / `nvidia-smi-compute-apps-20-56.csv`
- `ram-recheck-20-56.json`
- this NOTES

## Next (when Hermes exits or user frees GPU)

```text
py -3 _docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/launch_mapped_live_durable.py
```

Expect stderr markers (not speed claims): `Q36_STARTUP …` and `strata-q36: mapped-pack host pin pool … MiB x2`.
