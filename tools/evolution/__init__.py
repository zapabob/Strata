"""NKAT-URT Evolutionary Inference Optimisation (EIO) package (Phase 3 Revised).

Integrates Sakana AI ShinkaEvolve-inspired evolutionary search, multi-objective Pareto
archiving, non-stationary operator bandits, multi-fidelity evaluation with random
proxy-audit promotion, immutable invariant/resource gates, and URT speedup certification.

Strictly separates:
- Automatic candidate search vs human-approved adoption,
- Custom ShinkaEvolve-inspired search vs official SakanaAI/ShinkaEvolve runs,
- Search/calibration traces vs independent holdout certification traces.
"""

from __future__ import annotations

EIO_SCHEMA_VERSION = "strata-eio-v1"

__all__ = ["EIO_SCHEMA_VERSION"]
