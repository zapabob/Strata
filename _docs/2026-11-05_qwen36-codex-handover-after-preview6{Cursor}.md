# Codex handover after preview `.6` ship + T06 re-eval

- When: 2026-11-05T01:32+09:00
- Goal complete: **false** (do not UpdateGoal complete)

## Done since `.6` ship

- Path: **T06 re-eval → BLOCKED** (no clear measurable scheduler/code candidate; evidence-only)
- Notes: `evidence-2026-11-04-mapped-live/NOTES-01-32-t06-reeval.md`
- VRAM free at re-eval: **15044 MiB** (unused for fake T06)
- Hermes: **not killed**
- Prior ship still stands: product `0.4.0-preview.20261103.6` — https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261103.6
- Allowlist/docs honesty: `64226fde…` primary; signed `b5e4d525…` untouched

## Still remaining for goal complete

| Item | Status |
|------|--------|
| T04 adoption | NOT_DECIDED (n=1 observational) |
| T06 paired transfer/residency | **BLOCKED / NOT_RUN** — needs real code candidate + RED (not observational pair) |
| T07 CUDA hotspot | NOT_RUN (no profile input) |
| T08 FP16 KV | NOT_RUN (optional; not similarly clear) |
| T09 full GUI/E2E close | partial — installer honesty advanced; speed/quality gates open |
| Upstream PR #5216 / #5221 | already open — follow reviews |

## Do / Don't

- Do not invent speeds; do not change defaults from T04
- Do not kill Hermes
- Do not overwrite signed engine
- Do not force-push
- Skip `_docs/intake/` and engine-died log from commits
- Do not invent T06 gather/residency without measured costs
