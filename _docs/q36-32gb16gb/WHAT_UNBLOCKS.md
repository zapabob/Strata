# WHAT_UNBLOCKS — next agent file-level patches

Captured after T07 profile PASS (`NOTES-03-54-t07-hotspot-profile.md`). Goal complete remains **false**.

## Unblocked this turn

- **T07 profile input**: `STRATA_Q36_HOTSPOT_PROFILE=1` emits `Q36_HOTSPOT` lines. Warmup dominant bucket = **gdn**. Digests: unsigned `907341c74d5a9f26…` allowlisted; signed `b5e4d525…` untouched.

## Still blocked / next concrete patches

### 1) T07 one GDN hotspot opt-in (highest fidelity next)

Plan already names candidates; do **not** invent a new family.

| File | Patch |
|------|--------|
| `src/qwen35/q36_kernels.cuh` / `q36_engine.cu` | Opt-in dispatch for `k_gdn_seq_cols` (prefill) or `k_gdn_seq` (decode) behind env/flag; keep old kernel as fallback |
| `tests/qwen35/q36_kernel_parity_test.cu` (new) | RED parity for token counts named in plan §T07 |
| evidence | Same-day paired run with profile ON vs OFF **separately** from timing claim; `STRATA_Q36_VERIFY=1` |

Do not change default path until paired E2E + quality gates pass. Do not claim Flash-Next GDN numbers.

### 2) T06 transfer/residency (still no invented scheduler)

Profile already gives `stream_h2d_bytes`, `stream_copy_wait_ms`, `moe_cpu_ms`, `hy_cpu`/`hy_gpu`.

| File | Patch |
|------|--------|
| `src/qwen35/q36_engine.cu` (`stream_kick`, `rebalance`) | Only after a measured §5.2 gather vs full-layer comparison on **this** machine’s shapes |
| `tests/qwen35/q36_stage_scheduler_test.cpp`, `q36_residency_test.cpp` | RED: each route entry processed once (miss/dup 0) before any cost-aware rebalance weights |

Forbidden: inventing byte-cost weights without measured CPU/H2D inputs; wrapping `STRATA_Q36_STREAM_ALL` as “T06 done”.

### 3) T04 bounded warmup

| File | Patch |
|------|--------|
| `q36_engine.cu::warmup` + capability | `--q36-warmup-mode legacy\|bounded` only after RED fixtures + **n≥5** paired arms |
| `tests/qwen35/q36_warmup_contract_test.cpp` | Plan RED: GDN/conv/pos/MTP/RNG fresh-state fixtures |

Do **not** fake n=5. KEEP_DEFAULT stands until then.

### 4) T08 measured FP16 KV

Refuse-before-serve already PASS. Measured arm still needs `--q36-kv-storage fp16` engine path + quality gates — large surface; keep optional / out of required order.

## Build / install recipe (this PC)

```text
cmake --build H:\Strata\releases\hakua040-native-sync-20261103 --config Release --target strata --target strata-q36 --parallel 2
py -3 packaging/package_engine.py --src …\Release --backend cuda --version 0.4.0 --platform windows-x86_64 --variant cuda13 --arch sm_120 --arch compute_120 --min-driver nvidia=580.65 --out H:\Strata\releases\<tag> --include strata-q36.exe
# rename folder to 0.4.0-q36-windows-x86_64-cuda-cuda13; robocopy to %LOCALAPPDATA%\Strata\components\engine\…
# allowlist new strata.exe digest in apps/host/server/q36-run-contract.mjs
$env:STRATA_Q36_HOTSPOT_PROFILE=1
py -3 …\launch_mapped_live_durable.py --expect-sha256 <digest> …
```

Never kill Hermes. Never force-push. Never UpdateGoal complete from a single gate.
