# Strata Upstream Integration & Custom GGUF / DeepSeek Derivative Release Qualification

- **Release Target**: Strata 0.3.0 Upstream Integrated Edition
- **Integration Branch**: `integration/upstream-u1-dsv41-gguf`
- **Locked Upstream Cut**:
  - `U1`: `7dd5cf18e68c639a8773e096c5c79f971ea2a9f5` (Full upstream merge)
  - `C1`: `c487c875d05075113965bc61d822b27179f70639` (GUI TOCTOU settings fix)
  - `F0`: `ddc8f9e19cafb981ed91caaab0992ca814e6eca9` (Fork baseline)
- **Status**: **QUALIFIED & LOCKED** (Gate G7 Passed)
- **Audit Tool**: `tools/check_upstream_cut.py`

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

| ID | Contract Name | Upstream Boundary & Protection Mechanism | Test Verification |
| :--- | :--- | :--- | :--- |
| **F01** | Spin(8) Triality Attention | Versioned sidecar bridge in `adapters/upstream/native_attention_bridge.cpp`. Isolated from MLA. | `tests/contracts/test_fork_feature_matrix.py` |
| **F02** | TurboQuant Projection | Low-rank KV compression hooks preserved in native engine. | `tests/contracts/test_upstream_compatibility.py` |
| **F03** | Query-v3 Attention Swizzle | Identity initialization preserved in attention pipeline. | `tests/steering/test_steering_math.py` |
| **F04** | Windows Fail-Closed Boundary | Strict sandbox boundary: absolute UNC / symlink / path traversal rejection. | `tests/security/test_local_model_boundary.py` |
| **F05** | Hikari 27B PQ2_0 Bonsai | Supported via dedicated `prism` backend adapter. | `tests/backends/test_external_backend_contracts.py` |
| **F06** | Refusal-Direction Steering | Isolated steering vectors; disabled on abliterated uncensored models. | `tests/dsv41/test_steering_contract.py` |
| **F07** | Localized README Suite | All 7 languages preserved: English, Japanese, Chinese, German, Spanish, French, Portuguese. | `tools/check_upstream_cut.py` |
| **F08** | Long-Term Memory & SOUL.md | Hermes SQLite & Hakua Composite memory via MCP stdio tool `tools/strata_memory_mcp.py`. | `tests/test_strata_memory.py` |
| **F09** | Safe GGUF Preflight Limits | 16 MiB header cap, max tensor dims $2^{30}$, rank $\le 4$ mitigation. | `tests/security/test_gguf_admission_limits.py` |
| **F10** | Content-Addressed Identity | Streaming SHA-256 digest + drift detection aborts execution on tampering. | `tests/models/test_bundle_identity.py` |
| **F11** | 32GB RAM Budget Guard | Planned host RAM $\le 24.0$ GiB, OS reserve $\ge 4.0$ GiB, VRAM $\le 14.0$ GiB. | `tests/resources/test_model_memory.py` |

---

## 3. DeepSeek & Arbitrary GGUF Capabilities

1. **Uncensored Derivative Support**:
   - Qualified candidates: ISTA standard baseline, Kiwimaker Maya-S abliterated replacement recipe, and AtomicChat standalone bundle.
   - Refusal-direction steering is dynamically bypassed on abliterated variants to prevent double-ablation response distortion.

2. **Multi-Head Latent Attention (MLA)**:
   - Dedicated `strata-dsv41` backend executes native MLA projections.
   - Qwen attention structures and Cl(8,0) triality caches are strictly segregated, preventing cross-architecture memory corruption.

3. **32 GB RAM Zero-VRAM Drafter Lifecycle**:
   - Speculative decoding drafters are dynamically monitored; if system memory pressure exceeds threshold, drafter buffers are safely deallocated to zero VRAM without aborting main sequence generation.

---

## 4. Verification & Gate G7 Approval

- **Upstream Ancestor Verification**: `7dd5cf18e` is confirmed direct ancestor of integration branch.
- **GUI TOCTOU Security Hardening**: Snapshot patch `c487c87` verified in `apps/host/server/native-control.mjs`.
- **Packaging & Schema Validation**:
  - `model-bundle.schema.json` valid
  - `fork-extension.schema.json` valid
  - `backend-capabilities.schema.json` valid
- **Regression Suite**:
  - Python tests: **58 passed in 1.12s**
  - Node host tests: **11 passed in 453ms**
- **Gate G7 Sign-Off**: **APPROVED FOR PRODUCTION INTEGRATION**
