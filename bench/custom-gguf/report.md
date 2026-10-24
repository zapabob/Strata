# Strata Custom GGUF & DeepSeek Derivative Qualification Report

> [!WARNING]
> **CORRECTIVE NOTICE (2026-10-25 JST - Task R01)**:
> The initial evaluations recorded under Protocol v1 were preliminary static admission checks (`DRYRUN_QUALIFICATION_RECEIPT`). Per the corrective repair plan (`Strata_Antigravity_修復実装計画_20261025.md`), dry-run receipts cannot grant `real_model_qualified = true`. The status of these candidates is **PROVISIONAL / DRY-RUN ADMISSION PREVIEW ONLY** pending empirical multi-turn token generation under Protocol v2 (Task R16).

- **Protocol**: `STRATA-CUSTOM-GGUF-EVAL-V1` (Superseded by Protocol v2 for empirical qualification)
- **Date**: 2026-10-25 JST
- **Verifier**: Antigravity / MILSPEC-Codex Standard
- **Execution Target**: Windows 11 x64, 32 GB RAM, NVIDIA GeForce RTX 5060 Ti 16 GB (`sm_120`), AVX2

---

## 1. Executive Summary

This qualification report provides the preliminary static evaluation record for Gate G6 of the Strata latest upstream integration plan (`Strata最新上流統合・DeepSeek派生／任意GGUF対応`).

Candidate models—including base DeepSeek-V4.1-Flash reference bundles, uncensored slot replacement recipes, and standalone uncensored derivatives—were evaluated against static four-tier admission rules under 32 GB RAM constraints.

**Notice on Scope**: In accordance with the corrective plan R01, all results in this report represent dry-run admission previews only (`DRYRUN_QUALIFICATION_RECEIPT`). Full empirical qualification requires live weight generation (Task R16).

---

## 2. Hardware Environment Snapshot

Measurements captured on live host via `tools/qualify_model_bundle.py`:

| Parameter | Measured Value | Constraint / Limit | Status |
| :--- | :--- | :--- | :--- |
| **Physical Host RAM** | 34.22 GB (~31.87 GiB) | 32.0 GiB Target Baseline | **NOMINAL** |
| **Available Host RAM** | 10.16 GB | >= 4.0 GiB Headroom Required | **PASS** |
| **System Commit Limit** | 68.58 GB | > 48.0 GiB Required | **PASS** |
| **GPU Model** | NVIDIA GeForce RTX 5060 Ti | Ada/Blackwell Class (`sm_120`) | **CONFIRMED** |
| **Total VRAM** | 16,311 MiB (15.93 GiB) | 16.0 GiB Target Baseline | **NOMINAL** |
| **Active Server** | None Running | Port 8000/18501 Checked | **CLEAR** |

---

## 3. Four-Tier Qualification Results (Provisional Dry-Run Preview)

### Candidate 1: `deepseek-v4.1-flash-ista-standard`
- **Source**: `ISTA-DASLab/DeepSeek-V4.1-Flash-GGUF` (`main@7e4a1b0`)
- **Architecture / Dialect**: `dsv41` / `standard` (4-part shard layout)
- **Uncensored**: No
- **Tier 1 (Container Inspection)**: `PREVIEW_ONLY`
- **Tier 2 (Architecture Compatibility)**: `COMPATIBLE`
- **Tier 3 (Memory Planning)**: `UNVERIFIED_PENDING_WEIGHTS`
- **Tier 4 (Execution Readiness)**: `DRYRUN_PREVIEW`
- **Qualification Verdict**: **PROVISIONAL_DRYRUN_ONLY (real_model_qualified: false)**

### Candidate 2: `deepseek-maya-s-kiwimaker-abliterated`
- **Source**: `Kiwimaker/DeepSeek-Maya-S-Abliterated` (`main@3c8f901`)
- **Kind**: Uncensored Slot Replacement Recipe (`target_slot = 1`)
- **Architecture / Dialect**: `dsv41` / `standard`
- **Uncensored**: Yes
- **Tier 1 (Container Inspection)**: `PREVIEW_ONLY`
- **Tier 2 (Architecture Compatibility)**: `COMPATIBLE`
- **Tier 3 (Memory Planning)**: `UNVERIFIED_PENDING_WEIGHTS`
- **Tier 4 (Execution Readiness)**: `DRYRUN_PREVIEW`
- **Qualification Verdict**: **PROVISIONAL_DRYRUN_ONLY (real_model_qualified: false)**

### Candidate 3: `deepseek-v4.1-atomicchat-uncensored`
- **Source**: `AtomicChat/DeepSeek-V4.1-Uncensored-GGUF` (`main@a5f221e`)
- **Kind**: Standalone Uncensored Model Bundle
- **Architecture / Dialect**: `dsv41` / `standard`
- **Uncensored**: Yes
- **Tier 1 (Container Inspection)**: `PREVIEW_ONLY`
- **Tier 2 (Architecture Compatibility)**: `COMPATIBLE`
- **Tier 3 (Memory Planning)**: `UNVERIFIED_PENDING_WEIGHTS`
- **Tier 4 (Execution Readiness)**: `DRYRUN_PREVIEW`
- **Qualification Verdict**: **PROVISIONAL_DRYRUN_ONLY (real_model_qualified: false)**

---

## 4. Safety & Invariance Audits

1. **Memory Budget & Headroom Compliance**:
   - Live hardware snapshot captured. Real empirical memory measurement deferred to actual model execution under protocol-v2.

2. **Active Server Invariance**:
   - Server state verified via `strata.py launch --status`.
   - No unowned processes terminated.

3. **Steering Invariance**:
   - `adapters/upstream/dsv41_steering_bridge.hpp` separates Qwen vectors from DeepSeek MLA spaces.

---

## 5. Conclusion & Corrective Roadmap

- **Status**: **SUPERSEDED_BY_R01**
- **Evidence Files**:
  - Acceptance Ledger: [_docs/qa/model-acceptance.json](file:///C:/Users/downl/Documents/ChatGPT/Strata/_docs/qa/model-acceptance.json) (v2.0 corrected)
  - Raw Backup: `_docs/qa/model-acceptance.v1.json.bak`
  - Corrections Ledger: `_docs/repair-20261025/claim-corrections.json`
- Next: Real token generation and qualification under Task R16.
