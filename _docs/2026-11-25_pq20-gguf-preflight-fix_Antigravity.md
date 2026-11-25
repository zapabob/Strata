# 2026-11-25 — Hikari PQ2_0 (`type 142`) GGUF Preflight & `serve/server.py` Startup Fix (Antigravity)

- **Date:** 2026-11-25
- **AI / Engineer:** Antigravity
- **Target Checkout:** `C:/Users/downl/Documents/ChatGPT/Strata` (`main`)
- **Backup Directory:** `H:/Strata/backups/gguf-pq20-20261125/`
- **Release Qualification:** `releaseQualified=false` (unsigned local build & deployment)

## 1. Root Cause Analysis

1. **Primary Failure (`GGUF tensor has an unsupported encoding or shape`, exit code 2):**
   - `strata-q38.exe` itself already supports `PQ2_0` (`GGML type 142`, block geometry `(128, 34)` in `engine/q38/include/strata/qwen38/quant_tensor.hpp`, `src/ops.cu`, `src/prefill_gemm.cu`). Direct execution of `strata-q38.exe --model H:\Strata\models\hikari-pq20\Hikari-LoRA-fixed-scale-PQ2_0.gguf --ctx-size 4096 --kv spin8_k8v4 --tokens 1,2,3 --n 4` succeeded with exit code 0 (`16,1,198,220`, `prefill=232.184ms`, `decode=143.150ms` for 3 steps, `free_after=9.00 GB VRAM`).
   - The failure occurred in `terminal/strata_control/gguf_preflight.py:L249` because `142: "PQ2_0"` (plus `1001: "PQ2_0"`, `1002: "PTQ1_0"`, `2001: "TQ4_1S"`, `2002: "TQ3_0S"` and their `BLOCK_GEOMETRY` entries `(128, 34)`, `(32, 20)`, `(32, 15)`) existed in root `tools/gguf_reader.py` but were missing from:
     - `terminal/tools/gguf_reader.py`
     - `app/desktop/src-tauri/resources/control/tools/gguf_reader.py`
     - `terminal/crates/strata-gguf-preflight/src/lib.rs` (Rust native preflight helper)
     - Installed `C:/Users/downl/AppData/Local/Programs/Strata/control/tools/gguf_reader.py`
2. **Secondary Merge Regression (`AttributeError: 'Service' object has no attribute 'hy4'`):**
   - After preflight passed and `strata-q38.exe` finished loading `Hikari-LoRA-fixed-scale-PQ2_0.gguf`, `terminal/serve/server.py:L12412` failed because `Service.__init__` was missing `self.hy4` and `self.inkling` (dropped during the `21473cc9b` 3-way merge).

## 2. Changes Applied

- `terminal/tools/gguf_reader.py` & `app/desktop/src-tauri/resources/control/tools/gguf_reader.py` — Added `142: "PQ2_0"`, `1001: "PQ2_0"`, `1002: "PTQ1_0"`, `2001: "TQ4_1S"`, `2002: "TQ3_0S"` to `GGML_TYPES` and `"PQ2_0": (128, 34)`, `"TQ4_1S": (32, 20)`, `"TQ3_0S": (32, 15)` to `BLOCK_GEOMETRY`.
- `terminal/crates/strata-gguf-preflight/src/lib.rs` — Added matching `ggml_type_geometry` arms (`142`, `1001`, `1002`, `2001`, `2002`).
- `terminal/serve/server.py` & `app/desktop/src-tauri/resources/control/serve/server.py` — Restored `self.hy4` and `self.inkling` initialization in `Service.__init__` matching upstream `v0.2.21`.
- Deployed updated `gguf_reader.py` and `server.py` to `C:/Users/downl/AppData/Local/Programs/Strata/control/` with backups saved in `H:/Strata/backups/gguf-pq20-20261125/`.

## 3. Build & Verification Results

- **Rust `strata-gguf-preflight` (`CARGO_BUILD_JOBS=5`):**
  - `cargo test`: **3 / 3 PASSED** (`0.01s`).
  - `cargo build --release`: **PASSED** (`2.32s`, 0 warnings).
  - Live binary check (`strata-gguf-preflight.exe --strata-protocol 1 inspect Hikari-LoRA-fixed-scale-PQ2_0.gguf`): **`"ok": true`**, `tensor_types: {"BF16": 96, "F32": 353, "PQ2_0": 402}`, `payload_extent_valid: true`.
- **Python preflight (repo + installed Control):** **PASSED** (`{'BF16': 96, 'F32': 353, 'PQ2_0': 402}`, `payload_extent_valid: True`).
- **Unit tests (`terminal/tools/test_gguf_tqp.py`):** **3 / 3 PASSED** (`0.011s`).
- **C++/CUDA `strata-q38` incremental build (`cmake --build H:/Strata/build/q38-cuda135 --target strata-q38 -j 5`):** `ninja: no work to do.` (already up to date).
- **Direct RTX 5060 Ti inference (`strata-q38.exe --model Hikari-LoRA-fixed-scale-PQ2_0.gguf --ctx-size 4096 --kv spin8_k8v4 --tokens 1,2,3 --n 4`):** **PASSED (exit 0)**, output tokens `16,1,198,220`, `prefill_forward_ms=232.184`, `decode_forward_ms=143.150` (3 decode steps).
- **End-to-end `serve/server.py` check:** Preflight & server initialization verified past `gguf_preflight` and `Service.__init__`; note that concurrent desktop GPU usage (`9303 MiB` used, `6748 MiB` free) triggers the expected `8552 MB` VRAM admission floor when ComfyUI holds VRAM.
