# Mapped-live headroom remeasure 2026-11-04 04:09 JST

- Purpose: hours-later recheck after ~01:04 blocker; do not kill Hermes (DESIGN #6).
- GPU: RTX 5060 Ti — 15322 / 16311 MiB used, **729 MiB free**, util ~96%.
- RAM: free **6.82 GiB** / 31.87 GiB (better than earlier <4 GiB, still not a live run with Hermes holding VRAM).
- Hermes `llama-server` PIDs **22836** / **22944** still alive (Hikari PQ2_0 on 127.0.0.1:8080). Not killed.
- Decision: **mapped-live remains BLOCKED**. No Q36_STARTUP / ExpertPinPool capture this turn.
- T03 chat→stop→restart: **NOT_RUN** (no Q36 serve).
- T04 / T06 / T07 / T08: **NOT_RUN** (no paired live).
- Non-GPU honesty: `node --test` on `apps/host/tests/q36-*.test.mjs` → **19/19 PASS** (cache forced to C: because **H: FreeGB=0** caused npm ENOSPC).
- Engine digest still `6fe11065…` (unsigned q36 allowlist). Signed `b5e4d525…` not touched.
- Model + `.q36epk` still present under `H:\Strata\models\models\qwen36-UD-Q4_K_XL\`.
- Evidence files: `preflight-blocker-04-08.json`, `nvidia-smi-*-04-08.*`, `ram-recheck-04-08.json`, `host-q36-node-tests-04-08.txt`.
