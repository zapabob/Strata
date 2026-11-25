"""Scientific reasoning (lambda, eta) phase diagram evaluator (Section 11).

Sweeps reward control strength `lambda` and cost penalty `eta` across a finite
path ensemble to map:
- Expected verified success E_{Q*}[V_q]
- Expected total computational cost E_{Q*}[C]
- KL information cost D_KL(Q* || P)
- Success-cost covariance Cov_{Q*}(V_q, C)
- Asymptotic discovery rate Lambda(lambda, eta) = -ln(1 - E[V]) / E[C]

Theoretical ensemble outputs are explicitly marked as model calculations, never
physical phase transitions or measured hardware performance.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

from .discovery_rate import asymptotic_discovery_rate
from .variational import PathOutcome, feynman_kac_gibbs_ensemble


def evaluate_phase_diagram(
    paths: Sequence[PathOutcome],
    *,
    lambdas: Sequence[float],
    etas: Sequence[float],
    label: str = "theoretical_finite_path_model",
) -> dict[str, Any]:
    """Compute a (lambda, eta) phase-diagram grid for a finite path ensemble."""
    if not lambdas or not etas:
        raise ValueError("lambdas and etas must be non-empty")

    points: list[dict[str, Any]] = []
    for lam in lambdas:
        for eta in etas:
            res = feynman_kac_gibbs_ensemble(paths, lam=float(lam), eta=float(eta))
            ev_v = float(res["expected_verified_success"])
            ev_c = float(res["expected_cost"])
            disc_rate = (
                asymptotic_discovery_rate(min(1.0, max(0.0, ev_v)), ev_c)
                if ev_c > 0.0
                else 0.0
            )
            points.append(
                {
                    "lambda": float(lam),
                    "eta": float(eta),
                    "expected_verified_success": round(ev_v, 6),
                    "expected_cost": round(ev_c, 6),
                    "var_verified_success": round(float(res["var_verified_success"]), 6),
                    "cov_verified_cost": round(float(res["cov_verified_cost"]), 6),
                    "kl_q_star_p_nats": round(float(res["kl_q_star_p_nats"]), 6),
                    "log_Z": round(float(res["log_Z"]), 6),
                    "discovery_rate_lambda": (
                        round(disc_rate, 6) if math.isfinite(disc_rate) else "inf"
                    ),
                }
            )

    return {
        "label": label,
        "num_paths": len(paths),
        "lambdas": [float(x) for x in lambdas],
        "etas": [float(x) for x in etas],
        "points": points,
        "caveat": (
            "Finite-path variational calculation only; does not represent a physical "
            "phase transition or measured Strata GPU performance."
        ),
    }


def reference_four_path_ensemble() -> list[PathOutcome]:
    """Illustrative 4-path variational ensemble (fast fail, medium fail, deep success, rare short success)."""
    return [
        PathOutcome(path_id="fast_wrong", prior_prob=0.55, verified=0.0, cost=1.0),
        PathOutcome(path_id="medium_wrong", prior_prob=0.35, verified=0.0, cost=3.0),
        PathOutcome(path_id="deep_verified_proof", prior_prob=0.08, verified=1.0, cost=6.0),
        PathOutcome(path_id="concise_verified_proof", prior_prob=0.02, verified=1.0, cost=2.5),
    ]
