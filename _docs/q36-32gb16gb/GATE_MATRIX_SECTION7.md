# §7 / plan acceptance gate matrix — sealed snapshot

Captured: **2026-11-05 03:54 JST** (T07 profile append)  
Tip before this turn’s commit: `0a7d0f2a`  
Goal complete: **false** (do not UpdateGoal complete)  
Hermes killed: **false**  
Invented speeds: **false**

Statuses are only PASSED / FAILED / SKIPPED / NOT_RUN / BLOCKED / PARTIAL as justified by on-disk evidence. Local PASS is not remote CI PASS.

## Product / accuracy gates

| Gate | Status | Evidence / note |
|------|--------|-----------------|
| Path / model identity (drive bind, fileId) | PASSED | Host tests `q36-run-contract.test.mjs`; mapped-live uses H: UD-Q4_K_XL |
| Capability refuse unsupported + private-cache | PASSED | Host contract + GUI refuse screenshots `evidence-2026-11-04-gui/` |
| Never strip private-cache to force start | PASSED | `q36_private_cache_unsupported`; lifecycle tests |
| Mapped-pack opt-in + digest allowlist | PASSED | allowlist includes `64226fde…`; live READY + pin-pool |
| Legacy physical RAM gate (UD-Q4_K_XL) | PASSED | Host admit + node tests |
| Startup stage telemetry (`Q36_STARTUP`) | PASSED | captured on mapped-live `run-21-05` |
| T03 chat → STOP+EOF → restart | PASSED | `run-21-05-t03` / `NOTES-21-05` |
| Installer `.6` allowlist honesty | PASSED | `NOTES-01-28-preview6-ship`; setup SHA-256 `784d4f99…` |
| Signed engine `b5e4d525…` untouched | PASSED | verified across sessions; not overwritten |
| Remote GitHub Actions CI for this path | NOT_RUN | plan: local ≠ remote |
| Full signed-component re-qualify of unsigned q36 | NOT_RUN | unsigned candidate digest remains `64226fde…` |

## Performance / research gates (T04–T08)

| Gate | Status | Evidence / note |
|------|--------|-----------------|
| T04 observational warmup vs `--no-warmup` | PASSED (obs×2) | pair1 `PAIR_RECORDED`; pair2 `PAIR_RECORDED_WITH_ARM_B_RETRY` |
| T04 product default change | KEEP_DEFAULT | `NOTES-02-58-t04-keep-default.md` — no measured win for skipping warmup |
| T04 bounded warmup policy ADOPT | NOT_RUN | policy not implemented; n≥5 + RED fixtures open |
| T06 transfer/residency scheduler | BLOCKED | scheduler not implemented; H2D/CPU inputs now in `NOTES-03-54-t07-hotspot-profile` |
| T07 hotspot profile capture | PASSED | `STRATA_Q36_HOTSPOT_PROFILE`; `run-hotspot-03-32`; dominant host bucket=gdn; HW counters null |
| T07 CUDA hotspot opt-in | NOT_RUN | profile present; do not invent kernel PR without RED+paired |
| T08 refuse non-FP32 KV before serve | PASSED | `NOTES-02-58-t08-refuse-gate.md` + Host unit test |
| T08 measured FP16 KV quality/speed arm | NOT_RUN | optional; out of required order |
| 30% load→first_useful_token median claim | NOT_RUN | proposal target only; not achieved |

## Memory / store

| Gate | Status | Evidence / note |
|------|--------|-----------------|
| Mapped-pack: no full anonymous expert arena on live path | PASSED (obs) | pin-pool `32 MiB x2`; live READY under contract |
| Byte-exact pack CTest suite as plan names | PARTIAL | store path used live; full named CTest matrix not sealed here |
| Pin/own-cache budget reporting | PARTIAL | pin-pool line captured; full OS page-cache accounting not claimed |

## Report honesty

| Gate | Status | Evidence / note |
|------|--------|-----------------|
| NOT_RUN / BLOCKED kept distinct from PASS | PASSED | this matrix + `evidence-summary.json` |
| DONE tok/s not sold as paired speedup | PASSED | protocol observation only in NOTES |
| README / HAKUA_INSTALL / HAKUA_RELEASE honesty | PASSED | commits `1378afa8`, `df7dd77b` |

## T09 closeout residual

Still open before any goal-complete claim:

1. T06 scheduler still BLOCKED (use hotspot transfer/CPU inputs; do not invent weights)
2. T07 kernel opt-in NOT_RUN (profile PASS; next = GDN behind fallback — see `WHAT_UNBLOCKS.md`)
3. T08 measured FP16 arm optional and NOT_RUN (refuse gate alone ≠ full T08 PR)
4. T04 bounded policy still unimplemented (KEEP_DEFAULT ≠ ADOPT bounded; n≥5 not faked)
5. Signed engine re-pin of unsigned q36 digest if product wants signed path
6. Remote CI NOT_RUN

**T09 overall: PARTIAL** (docs/GUI/installer/refuse/E2E core advanced; speed research gates open).
