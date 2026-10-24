# 2026-10-25 Strata 0.3.0 Spin(8) 32 GiB VRAM Fix & GUI/Host/Control Integration Log (Antigravity / Codex)

## Summary

1. **CUDA `audit_kernel` Dynamic Shared Memory Fix (`tqcodec/src/cache_cuda.cu`, `tqcodec/include/tqcodec/cache_cuda.h`, `tqcodec/tests/cache_cuda_test.cpp`)**
   - Replaced thread-local `float f[128 * 128]` (64 KiB/thread) inside `tqcodec::cuda_detail::audit_kernel` with opt-in dynamic shared memory (`extern __shared__ float f[];`, `cudaFuncSetAttribute(..., cudaFuncAttributeMaxDynamicSharedMemorySize, 65536)`).
   - Eliminated the **3.375 GiB (`3,623,878,656 B`)** CUDA local-memory stack reservation at `tqc_cache_cuda_initialize`, freeing ~3.3 GiB of device VRAM for the native expert cache on 16 GiB GPUs / 32 GiB RAM hosts.
   - Verified with `tqc_cache_cuda_test.exe` (`28,068` checks, `audit_smem=65536`, `audit_local=0`, `audit_delta=0`) and `strata_spin8_native_owner_test.exe` (`17,361` checks).

2. **Three-View Guarded Q2 Generation (`H:/Strata/build/task5a-audit-memory-20261024`)**
   - Rebuilt `H:/Strata/build/native-spin8/Release/strata.exe` (`SHA256: 564e23b5bcd2b0670d0a2d82e7cd2c20cd5afedf85ddca7c653bea11403727db`).
   - Executed all three guarded Q2 generation arms under identical `--expert-cache auto --vram-reserve-mib 10240` settings:
     - `model-f32-auto10240-r1`: `child_exit_code=0`, `1013` expert slots (`1.30 GiB`), `owner_bytes_total=27,657,216`, `decoded_content="READY"`, `generated_ids=[44061, 248046]`, `termination="eos"`.
     - `model-compressed-auto10240-r1`: `child_exit_code=0`, `1030` expert slots (`1.33 GiB`), `owner_bytes_total=5,342,208`, `decoded_content="READY"`, `generated_ids=[44061, 248046]`, `termination="eos"`.
     - `model-off-auto10240-r1`: `child_exit_code=0`, `1030` expert slots (`1.33 GiB`), `owner_bytes_total=0`, `decoded_content="READY"`, `generated_ids=[44061, 248046]`, `termination="eos"`.

3. **GUI / Host / Control / Server Integration (`serve/`, `strata_control/`, `strata_cli/`, `apps/host/`)**
   - Added `cache_type_k`, `cache_type_v`, `spin8_mode`, `spin8_native_config`, and `spin8_native_sha256` across:
     - `serve/server.py` (`native_cache_args`, CLI flags, preflight validation)
     - `strata_control/profiles.py` (`OVERRIDE_KEYS`, `parse_assignment`, `validate_overrides`)
     - `strata_control/user_args.py` (`USER_KEPT_FLAGS`)
     - `strata_cli/cli.py` (`serve` CLI flags, `_effective`, `_launch_plan`)
     - `apps/host/server/native-settings.mjs` (`NATIVE_FIELDS` under `GPU & memory`, `validateNativeSettings`)
     - `apps/host/server/native-control.mjs` (`settings`, `save` with `user_args`/`args` flag synchronization)
     - `apps/host/server/run-config-check.mjs` & `apps/host/src/lib/run-config-issues.ts` (hand-edited JSON config validation and localized messages)
   - Verified with `tests/terminal/test_profiles.py` (`21 passed, 1 skipped`), `apps/host/tests/*.test.mjs` (`19 passed, 0 failed`), `pnpm --dir apps/host typecheck`, and `pnpm --dir apps/host build`.

4. **Local Overwrite-Installation & Verification (`C:/Users/downl/AppData/Local/Programs/Strata` & `C:/Users/downl/AppData/Local/Strata/components`)**
   - Overwrote `host/dist` (65 files), `host/server` (110 files), `control/serve` (98 files), `control/strata_control` (55 files), `control/strata_cli` (36 files), `control/strata.py`, `control/COMMIT` (`ddc8f9e19cafb981ed91caaab0992ca814e6eca9`), `engine-bundle/0.1.47-windows-x86_64-cuda-cuda13`, and `components/engine/0.1.47-windows-x86_64-cuda-cuda13`.
   - Verified via `engine_component.resolve(..., full=True)` (`ok=True`, `file_count=9`, `bytes=752960332`) and `strata.cmd doctor --json` (`ok=True`).

5. **Multi-Language Fork README Rewrite (`README.md`, `README.ja.md`, `README.zh-CN.md`, `README.de.md`, `README.fr.md`, `README.es.md`, `README.pt-BR.md`)**
   - Rewrote all 7 localized root README files to document the fork's unique Spin(8) $\mathrm{Cl}(8,0)$ Triality KV Cache, `tqcodec` asynchronous CUDA dialects (`TQ4_1S`, `TQ3_0S`, `PQ2_0`), Query-v3 `.prismq3` sidecars, SM120 `audit_kernel` dynamic shared-memory fix (`65,536` bytes smem / `3.375 GiB` stack reservation eliminated), GUI/CLI/Control integration, and `v0.3.0-preview.20261024.2` release artifacts.
   - Verified with `$env:PYTHONUTF8="1"; py -3 -m pytest -p no:randomly tools/test_strata_bench.py` (`17 passed`).
