"""NKAT-URT Theory of Scientific Intelligence (TSI) verified evaluation and reasoning package.

Implements Stages A-D on the Python side (opt-in, zero changes to Strata's default
inference path or CUDA kernels):
- Stage A: Stopping-time survival metrics, RMST, quantisation discovery-rate theorem,
  URT information-geometric certificates, and statistical bounds.
- Stage B: 5-level independent verification architecture (including optional isolated
  Lean 4 kernel checks), failure-guided retries, counterexample search, and Section 16
  JSONL recording.
- Stage C: Non-commutative ResearchState tracking, optimal restart analysis, discrete
  Bellman DP, URT policy-stability bounds, and empirical adaptive scheduling.
- Stage D: Key-dimension NKAT/GDN observability Gramian diagnostics, time-correlated
  quantisation error, low-rank residual compensation simulation, and Weibull scaling
  hypothesis analysis.
"""

from __future__ import annotations

TSI_RECORD_SCHEMA_VERSION = 1
TSI_SCHEMA_VERSION = "strata-tsi-eval-v1"
DEFAULT_API_BASE_URL = "http://127.0.0.1:8080"

__all__ = [
    "DEFAULT_API_BASE_URL",
    "TSI_RECORD_SCHEMA_VERSION",
    "TSI_SCHEMA_VERSION",
]
