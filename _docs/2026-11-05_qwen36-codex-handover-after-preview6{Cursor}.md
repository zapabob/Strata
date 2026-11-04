# Codex handover after preview `.6` ship

- When: 2026-11-05T01:28+09:00
- Goal complete: **false** (do not UpdateGoal complete)

## Done this turn

- Path: **ship** (T06 blocked — no scheduler/code candidate)
- Product `0.4.0-preview.20261103.6` NSIS + `/S /UPDATE` + `gh release create --latest=false`
- Setup SHA-256 `784d4f992443a43076e7de8dbcdc624b35d95e97e13b716ea9de0e13a1baeac9` (113075186 bytes)
- Allowlist/docs honesty: `64226fde…` primary; signed `b5e4d525…` untouched
- Release: https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261103.6

## Still remaining for goal complete

| Item | Status |
|------|--------|
| T04 adoption | NOT_DECIDED (n=1 observational) |
| T06 paired transfer/residency | NOT_RUN — needs code candidate + RED |
| T07 CUDA hotspot | NOT_RUN |
| T08 FP16 KV | NOT_RUN (optional) |
| T09 full GUI/E2E close | partial — installer honesty advanced; speed/quality gates open |
| Upstream PR #5216 / #5221 | already open — follow reviews |

## Do / Don't

- Do not invent speeds; do not change defaults from T04
- Do not kill Hermes
- Do not overwrite signed engine
- Do not force-push
- Skip `_docs/intake/` and engine-died log from commits
