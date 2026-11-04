# mapped-live attempt 2026-11-04 18:12–18:22 JST

- Purpose: hours later remeasure; if headroom OK run allowlisted unsigned mapped-pack live; capture Q36_STARTUP + pin-pool; then T03 / paired T04–T06. DESIGN #6: do not kill Hermes.
- GPU at 18:13: RTX 5060 Ti — used **865 MiB** / free **~15446 MiB** / util low. Prior heavy Hermes PIDs 22836/22944 **gone**.
- Still present: Hermes `llama-server` PID **14572** on `127.0.0.1:8080` (Hikari-LoRA-fixed-scale-PQ2_0, n_ctx **98304**, model size ~7.2 GiB). Not killed.
- RAM: total 31.87 GiB, free ~10.6 GiB at go / ~7.5 GiB after abort.
- Disk: H FreeGB ~76; C FreeGB ~17.7.
- Unsigned `0.4.0-q36-…\strata.exe` SHA-256 **`64226fde…`** verified. Signed `b5e4d525…` untouched. `.q36epk` present (20127612928 bytes).

## What ran

1. **GO preflight** (`preflight-go-18-13.json`) — free VRAM looked sufficient.
2. **Partial mapped-pack load** (`run-18-14/`, PID 31184) with planned argv:
   `--native …UD-Q4_K_XL.gguf --max-context 65536 --prefill auto --mtp 2 --q36-expert-store mapped-pack --serve`
   - VRAM climbed **865 → ~15912 MiB** in ~2 min; process WS ~10 GB. Proves the allowlisted binary starts the mapped-pack path under load.
   - **Failure:** PowerShell async stdout/stderr handlers never wrote log files; stdin handle not durable → no `Q36_STARTUP` / pin-pool lines captured; T03 impossible on that process.
3. **Abort of our strata only** (Hermes left alive). After abort dedicated VRAM stayed ~7400–10655 MiB used (Hermes Hikari active); free ~5400 MiB.
4. Durable launcher added: `launch_mapped_live_durable.py`. Gate dry-run at 18:22: **exit 4 BLOCKED** (`free VRAM 5399 MiB < min 12000`; 1 llama-server). Evidence: `run-18-22-gate/`.

## Status

| Item | Result |
|------|--------|
| mapped-live pin-pool log | **BLOCKED** (no Q36_STARTUP/pin-pool file capture; headroom lost to Hermes after partial attempt) |
| T03 chat→stop→restart | **NOT_RUN** |
| T04 / T06 / T07 / T08 | **NOT_RUN** |
| invented speeds | **false** |
| Hermes killed | **false** |
| goal complete | **false** |

## Next (when Hermes exits or user frees GPU)

```text
py -3 _docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/launch_mapped_live_durable.py
```

Expect stderr markers (not speed claims): `Q36_STARTUP …` and `strata-q36: mapped-pack host pin pool … MiB x2`.
