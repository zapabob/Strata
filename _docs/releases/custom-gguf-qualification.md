# Strata Upstream Integration & Custom GGUF / DeepSeek Derivative Release Qualification (v2 Corrected)

- **Release Target**: Strata 0.3.0 Upstream Integrated Edition
- **Integration Branch**: `main`
- **Locked Upstream Cut**:
  - `U1`: `7dd5cf18e68c639a8773e096c5c79f971ea2a9f5` (Full upstream merge)
  - `C1`: `c487c875d05075113965bc61d822b27179f70639` (GUI TOCTOU settings fix)
  - `F0`: `ddc8f9e19cafb981ed91caaab0992ca814e6eca9` (Fork baseline)
- **Status**: **VERIFIED WITH AUDITED LIMITATIONS** (Corrective Audit Complete)
- **Audit Tool**: `tools/check_upstream_cut.py`, `tools/verify_run_evidence.py --strict`

---

## 1. Release Architecture Overview

This release merges upstream Strata while retaining all 11 proprietary fork capabilities (F01–F11). It introduces safe content-addressed arbitrary GGUF model bundle loading and deep integration with DeepSeek-V4.1-Flash-1017 uncensored derivatives under strict 32 GB RAM / 16 GB VRAM physical constraints.

```
+---------------------------------------------------------------+
|                      Unified GUI & CLI                        |
|   (Desktop Tauri Host / Web UI / Strata Terminal strata.py)   |
+-------------------------------+-------------------------------+
                                |
             +------------------v-------------------+
             |    ModelBundle Content Resolver      |
             |  (Bounded Header, Shard Ordering,    |
             |   GHSA-vgg9-87g3-85w8 Overflow Guard)|
             +------------------+-------------------+
                                |
             +------------------v-------------------+
             |       Deterministic Router           |
             |   (Strict Local, Zero Cloud Fallback)|
             +-----+------------+------------+------+
                   |            |            |
+------------------v-+   +------v-----+   +--v---------------+
| strata-dsv41       |   | strata-    |   | prism            |
| (DeepSeek V4.1 MLA |   | native     |   | (PQ2_0 Bonsai    |
|  Uncensored & Base)|   | (Qwen2 /   |   |  Low-Bit Quant)  |
|                    |   |  Spin(8))  |   |                  |
+--------------------+   +------------+   +------------------+
```

---

## 2. Preserved Fork Contracts Ledger (F01–F11)

| ID | Contract Name | Upstream Boundary & Protection Mechanism | Test Verification | Status |
| :--- | :--- | :--- | :--- | :--- |
| **F01** | Spin(8) Triality Attention | Versioned sidecar bridge in `adapters/upstream/native_attention_bridge.cpp`. Isolated from MLA. | `tests/regression/test_regression_spin8_triality.py` | **PRESERVED** |
| **F02** | TurboQuant Projection | Low-rank KV compression hooks preserved in native engine. | `tests/regression/test_regression_spin8_triality.py` | **PRESERVED** |
| **F03** | Query-v3 Attention Swizzle | Identity initialization preserved in attention pipeline. | `tests/regression/test_regression_spin8_triality.py` | **PRESERVED** |
| **F04** | Windows Fail-Closed Boundary | Strict sandbox boundary: absolute UNC / symlink / path traversal rejection. | `tests/security/test_native_boundary_e2e.py` | **VERIFIED** |
| **F05** | Hikari 27B PQ2_0 Bonsai | Supported via dedicated `prism` backend adapter. | `tests/backends/test_external_binary_smoke.py` | **PRESERVED** |
| **F06** | Refusal-Direction Steering | Isolated steering vectors; mathematically bound operators; disabled on abliterated variants. | `tests/steering/test_bound_operators.py` | **VERIFIED** |
| **F07** | Localized README Suite | All 7 languages preserved: English, Japanese, Chinese, German, Spanish, French, Portuguese. | Local inspection | **PRESERVED** |
| **F08** | Long-Term Memory & SOUL.md | Hermes SQLite & Hakua Composite memory via MCP stdio tool `tools/strata_memory_mcp.py`. | Architecture contract | **PRESERVED** |
| **F09** | Safe GGUF Preflight Limits | 64 MiB bounded header cap, max tensor dims $2^{30}$, rank $\le 4$ checked arithmetic. | `tests/security/test_native_gguf_bounds.py` | **VERIFIED** |
| **F10** | Content-Addressed Identity | Streaming SHA-256 digest + drift detection aborts execution on tampering. | `tests/models/test_bundle_verified_identity.py` | **VERIFIED** |
| **F11** | 32GB RAM Budget Guard | Planned host RAM $\le 24.0$ GiB, OS reserve $\ge 4.0$ GiB, VRAM $\le 14.0$ GiB. | `tests/resources/test_model_memory_real.py` | **VERIFIED** |

---

## 3. Audited Empirical Status for DeepSeek & Candidate GGUF

In accordance with Tasks R01 and R16 of the corrective plan, previous dry-run receipts have been audited and updated:

1. **DeepSeek-V4.1-Flash Uncensored**:
   - Adapter and preparation pipeline (`strata_control/backends/dsv41.py`) and bounded I/O (`src/dsv41/ds4_bounded_io.hpp`) are fully connected to real inspection.
   - Physical storage audit confirms only shard 1 of 6 (`...-00001-of-00006.gguf`) is present on local disk. Shards 2–6 are missing.
   - **Status**: **BLOCKED** pending download of remaining shards. No synthetic tokens were generated.

2. **Swift-1.5 Abliterated (`H:\Strata\models\SC117`)**:
   - Both weight shards (totaling 63.4 GiB) and vision projector are recognized.
   - Memory budgeting accurately recognizes that 63.4 GiB cannot run locally on a single 32 GB RAM host without multi-GPU/offload.
   - **Status**: **BLOCKED_BY_MEMORY** (Accurately guarded).

3. **Arbitrary GGUF Inspection**:
   - Truly parses binary KV pairs, tensor directories, array strings, and quant dialects (PQ2_0, PTQ1_0, TQ4_1S, TQ3_0S).
   - **Status**: **VERIFIED & OPERATIONAL**.

---

## 4. Verification & Gate Approval

- **Upstream Ancestor Verification**: `7dd5cf18e` is confirmed direct ancestor.
- **GUI TOCTOU Security Hardening**: Snapshot patch `c487c87` verified.
- **Suite Results**:
  - Python tests: **80 passed in 2.27s** across bounded GGUF, security boundaries, and regressions.
  - Strict evidence gate: Verified all dry-runs revoked.
