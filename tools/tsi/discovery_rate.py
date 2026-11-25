"""Quantisation discovery-rate theorem, robust adoption, and Jensen heterogeneity audit.

Implements Sections 4, 6, and 7 of the Phase 2 mathematical specification:
- Asymptotic discovery rate: Lambda_Q = -ln(1 - p_Q) / c_Q
- Critical quantised success rate: p_crit = 1 - (1 - p_R)^(c_Q / c_R)
- Full total-trial cost accounting (never estimated from decode tok/s alone)
- Conservative robust adoption criterion under simultaneous uncertainty bounds
- Jensen inequality audit for pass@k heterogeneity across tasks
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Sequence


@dataclass(frozen=True)
class TrialCostBreakdown:
    """Complete end-to-end cost accounting for a single reasoning trial (Section 4).

    Never estimate total trial cost solely from decode tokens per second.
    """

    prefill_s: float = 0.0
    decode_s: float = 0.0
    model_switch_s: float = 0.0
    context_rebuild_s: float = 0.0
    retry_s: float = 0.0
    verify_s: float = 0.0
    counterexample_s: float = 0.0
    init_s: float = 0.0

    def __post_init__(self) -> None:
        for name in (
            "prefill_s",
            "decode_s",
            "model_switch_s",
            "context_rebuild_s",
            "retry_s",
            "verify_s",
            "counterexample_s",
            "init_s",
        ):
            val = float(getattr(self, name))
            if val < 0.0 or not math.isfinite(val):
                raise ValueError(f"TrialCostBreakdown.{name} must be finite and non-negative: {val}")

    @property
    def total_cost_s(self) -> float:
        return (
            self.prefill_s
            + self.decode_s
            + self.model_switch_s
            + self.context_rebuild_s
            + self.retry_s
            + self.verify_s
            + self.counterexample_s
            + self.init_s
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "prefill_s": round(self.prefill_s, 6),
            "decode_s": round(self.decode_s, 6),
            "model_switch_s": round(self.model_switch_s, 6),
            "context_rebuild_s": round(self.context_rebuild_s, 6),
            "retry_s": round(self.retry_s, 6),
            "verify_s": round(self.verify_s, 6),
            "counterexample_s": round(self.counterexample_s, 6),
            "init_s": round(self.init_s, 6),
            "total_cost_s": round(self.total_cost_s, 6),
        }


def asymptotic_discovery_rate(p_success: float, trial_cost: float) -> float:
    """Compute Lambda = -ln(1 - p) / c under independent constant-cost trials."""
    if not (0.0 <= p_success <= 1.0):
        raise ValueError(f"p_success must lie in [0, 1]: {p_success}")
    if trial_cost <= 0.0 or not math.isfinite(trial_cost):
        raise ValueError(f"trial_cost must be positive and finite: {trial_cost}")
    if p_success == 0.0:
        return 0.0
    if p_success == 1.0:
        return float("inf")
    return -math.log1p(-p_success) / trial_cost


def critical_quantised_success_rate(p_ref: float, cost_ref: float, cost_quant: float) -> float:
    """Compute p_crit = 1 - (1 - p_R)^(c_Q / c_R) for Lambda_Q > Lambda_R."""
    if not (0.0 <= p_ref <= 1.0):
        raise ValueError(f"p_ref must lie in [0, 1]: {p_ref}")
    if cost_ref <= 0.0 or cost_quant <= 0.0:
        raise ValueError("cost_ref and cost_quant must be positive")
    if p_ref == 0.0:
        return 0.0
    if p_ref == 1.0:
        return 1.0
    ratio = cost_quant / cost_ref
    return 1.0 - math.pow(1.0 - p_ref, ratio)


def independent_trial_success_curve(p_success: float, trial_cost: float, budget: float) -> float:
    """Theoretical independent constant-cost model: S(B) = 1 - (1 - p)^floor(B / c)."""
    if not (0.0 <= p_success <= 1.0):
        raise ValueError(f"p_success must lie in [0, 1]: {p_success}")
    if trial_cost <= 0.0 or budget < 0.0:
        raise ValueError("trial_cost must be positive and budget non-negative")
    trials = int(math.floor(budget / trial_cost))
    if trials <= 0:
        return 0.0
    return 1.0 - math.pow(1.0 - p_success, trials)


def compare_quantised_discovery_rate(
    *,
    p_ref: float,
    cost_ref: float,
    p_quant: float,
    cost_quant: float,
    finite_budgets: Sequence[float] = (),
) -> dict[str, Any]:
    """Evaluate Section 4 quantisation discovery-rate theorem and finite-budget comparisons."""
    lambda_r = asymptotic_discovery_rate(p_ref, cost_ref)
    lambda_q = asymptotic_discovery_rate(p_quant, cost_quant)
    p_crit = critical_quantised_success_rate(p_ref, cost_ref, cost_quant)

    finite_rows: list[dict[str, Any]] = []
    for b in finite_budgets:
        sr = independent_trial_success_curve(p_ref, cost_ref, b)
        sq = independent_trial_success_curve(p_quant, cost_quant, b)
        finite_rows.append(
            {
                "budget": float(b),
                "reference_trials": int(math.floor(b / cost_ref)),
                "quantised_trials": int(math.floor(b / cost_quant)),
                "reference_success_model": round(sr, 6),
                "quantised_success_model": round(sq, 6),
                "delta_quant_minus_ref": round(sq - sr, 6),
            }
        )

    return {
        "model_assumption": "independent_constant_cost_trials",
        "p_ref": p_ref,
        "cost_ref": cost_ref,
        "p_quant": p_quant,
        "cost_quant": cost_quant,
        "cost_ratio_q_over_r": round(cost_quant / cost_ref, 6),
        "lambda_ref": round(lambda_r, 6) if math.isfinite(lambda_r) else "inf",
        "lambda_quant": round(lambda_q, 6) if math.isfinite(lambda_q) else "inf",
        "p_crit": round(p_crit, 6),
        "asymptotic_quant_exceeds_ref": lambda_q > lambda_r,
        "p_quant_exceeds_p_crit": p_quant > p_crit,
        "finite_budget_model_comparison": finite_rows,
        "caveat": (
            "Asymptotic discovery rate assumes independent constant-cost trials; "
            "finite-budget dominance and correlated/heterogeneous tasks must be verified empirically."
        ),
    }


def check_robust_adoption(
    *,
    p_ref_upper: float,
    p_quant_lower: float,
    rho_upper: float,
) -> dict[str, Any]:
    """Conservative robust quantisation adoption check (Section 6).

    Verifies p_Q_lower > 1 - (1 - p_R_upper)^rho_upper under simultaneous confidence
    bounds. Failing this criterion does NOT automatically disqualify Q; it simply means
    improvement in discovery rate is not yet certified.
    """
    if not (0.0 <= p_ref_upper <= 1.0 and 0.0 <= p_quant_lower <= 1.0):
        raise ValueError("Success probability bounds must lie in [0, 1]")
    if rho_upper <= 0.0 or not math.isfinite(rho_upper):
        raise ValueError(f"rho_upper must be positive and finite: {rho_upper}")

    threshold = 1.0 - math.pow(1.0 - p_ref_upper, rho_upper)
    certified = p_quant_lower > threshold
    return {
        "p_ref_upper": p_ref_upper,
        "p_quant_lower": p_quant_lower,
        "rho_upper": rho_upper,
        "robust_threshold": round(threshold, 6),
        "margin": round(p_quant_lower - threshold, 6),
        "certified_improvement": certified,
        "status": "certified_improvement" if certified else "not_certified_not_disqualified",
        "caveat": (
            "Validity requires simultaneous coverage of p_ref_upper, p_quant_lower, and rho_upper. "
            "Failure to certify does not prove inferiority."
        ),
    }


def jensen_pass_at_k_audit(per_task_probs: Sequence[float], k: int) -> dict[str, Any]:
    """Compare heterogeneous pass@k S(k) = 1 - E_q[(1 - p_q)^k] against homogeneous bound.

    By Jensen's inequality for convex x -> (1 - x)^k (k >= 1):
        S(k) <= 1 - (1 - E_q[p_q])^k
    Prevents over-estimating pass@k from mean pass@1.
    """
    if not per_task_probs:
        raise ValueError("per_task_probs must be non-empty")
    if k < 1:
        raise ValueError(f"k must be >= 1: {k}")
    probs = [float(p) for p in per_task_probs]
    if any(p < 0.0 or p > 1.0 for p in probs):
        raise ValueError("All task probabilities must lie in [0, 1]")

    mean_p = sum(probs) / len(probs)
    exact_heterogeneous = 1.0 - (sum(math.pow(1.0 - p, k) for p in probs) / len(probs))
    naive_homogeneous = 1.0 - math.pow(1.0 - mean_p, k)
    gap = naive_homogeneous - exact_heterogeneous
    return {
        "k": k,
        "num_tasks": len(probs),
        "mean_pass_at_1": round(mean_p, 6),
        "exact_heterogeneous_pass_at_k": round(exact_heterogeneous, 6),
        "naive_homogeneous_upper_bound": round(naive_homogeneous, 6),
        "jensen_overestimation_gap": round(max(0.0, gap), 6),
        "inequality_holds": exact_heterogeneous <= naive_homogeneous + 1e-12,
    }
