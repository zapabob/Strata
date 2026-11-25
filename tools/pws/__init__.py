"""NKAT-URT Predictive Weight Streaming (PWS) analysis, replay, and certification package.

Opt-in Python-side research and audit layer extending Strata's existing 4-tier
GPU/RAM/CPU/SSD MoE pipeline (`ExpertCache`, `TwoPriorityExpertScheduler`, `DirectFile`,
`InkExpertPolicy`, `tools/bench_eviction.py`) without altering default inference paths.
"""

from __future__ import annotations

PWS_SCHEMA_VERSION = "strata-pws-v1"

__all__ = ["PWS_SCHEMA_VERSION"]
