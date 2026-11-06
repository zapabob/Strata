# Strata 16GB (RTX 5060 Ti) measurement harness

PR-A diagnostic capture for Windows 11 / RTX 5060 Ti 16GB.

## Rules

- Dedicated VRAM and Windows shared GPU memory are **separate fields**. Never merge them.
- `requested.context` vs `effective.context` must be compared explicitly. A silent shrink is a failed / non-comparable run.
- Do not commit prompt text, API keys, or private absolute paths.
- Attention KV theory (e.g. Hikari 131072 Q8_0 = 4.25 GiB) is **not** a full GPU fit claim.

## Capture baseline

```powershell
# From repo root
powershell -NoProfile -File .\bench\strata-16gb\run-windows.ps1
```

Writes `results/baseline-<timestamp>.json` with git SHAs, nvidia-smi dedicated VRAM, Windows shared usage, CPU/RAM, and a RunObservation shell.

## Related modules

- `apps/host/server/run-observation.mjs`
- `apps/host/server/vram-observation.mjs`
- `apps/host/server/model-memory.mjs`

## Rollback

Remove or ignore `bench/strata-16gb/results/*` local captures. The baseline capture remains a separate, explicit command.

## Opt-in lifecycle and attach-only capture

See [LIFECYCLE.md](LIFECYCLE.md) for startup capture enabled with
`STRATA_RUN_OBSERVATION=1` and the attach-only synthetic runner `run.mjs`.
Those observations use [run-observation.schema.json](run-observation.schema.json).
The baseline command, `measurement-schema.json` and existing results retain
their original contract. Unset the flag and restart the source host to disable
lifecycle capture.
