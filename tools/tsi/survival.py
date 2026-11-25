"""Stopping-time survival theory and finite-budget RMST analysis (Sections 3 & 14).

Models cumulative computational cost until first independent verification:
    tau_q = inf { b >= 0 : V(q, pi_b) = 1 }
    S_pi(B) = Pr(tau_q <= B)
    RMST(B_max) = integral_0^{B_max} (1 - S_pi(b)) db

Never excludes failed, timed-out, or censored trials, never claims infinite-horizon
E[tau_q] or continuous infimum B*_pi(delta) from finite measurements, and explicitly
separates continuous-policy cumulative curves from per-budget distinct configurations.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import statistics
from typing import Any, Literal, Sequence

from .math_foundations import (
    bonferroni_alpha,
    clopper_pearson_interval,
    finite_budget_attainment,
    wilson_interval,
)

CurveType = Literal["continuous_policy", "per_budget_config"]


@dataclass(frozen=True)
class StoppingObservation:
    """Stopping-time outcome for one independent task under a given policy."""

    task_id: str
    verified: bool
    cost_to_first_verified: float | None
    total_cost_spent: float
    censored: bool
    budget_cap: float
    discovery_class: str = "known_benchmark_problem"


def hoeffding_simultaneous_lower_bound(
    empirical_rate: float,
    n_tasks: int,
    num_budgets: int,
    alpha: float = 0.05,
) -> float:
    """One-sided simultaneous Hoeffding lower bound over J pre-specified budgets.

        S(B) >= S_hat(B) - sqrt(ln(J / alpha) / (2 * n))
    """
    if n_tasks <= 0:
        return 0.0
    if num_budgets <= 0:
        raise ValueError(f"num_budgets must be positive: {num_budgets}")
    if not (0.0 < alpha < 1.0):
        raise ValueError(f"alpha must lie in (0, 1): {alpha}")
    if not (0.0 <= empirical_rate <= 1.0):
        raise ValueError(f"empirical_rate must lie in [0, 1]: {empirical_rate}")
    radius = math.sqrt(math.log(num_budgets / alpha) / (2.0 * n_tasks))
    return max(0.0, empirical_rate - radius)


def restricted_mean_time_to_success(
    observations: Sequence[StoppingObservation],
    b_max: float,
) -> float:
    """Exact empirical RMST(B_max) = integral_0^{B_max} (1 - S_hat(b)) db.

    Evaluated directly from the right-continuous empirical step function S_hat(b).
    Unsuccessful, timed-out, and right-censored trials remain in the denominator and
    contribute full survival mass 1 up to `b_max` (equivalent to min(tau_q, b_max)).
    """
    if b_max <= 0.0:
        raise ValueError(f"b_max must be positive: {b_max}")
    n = len(observations)
    if n == 0:
        raise ValueError("observations must be non-empty")

    # Collect finite event times within (0, b_max]
    event_times = sorted(
        float(obs.cost_to_first_verified)
        for obs in observations
        if obs.verified and obs.cost_to_first_verified is not None and 0.0 <= obs.cost_to_first_verified <= b_max
    )
    # Exact piecewise-constant integration of (1 - S_hat(b)) over [0, b_max]
    area = 0.0
    prev_b = 0.0
    solved_so_far = 0
    idx = 0
    m = len(event_times)
    while idx < m:
        t = event_times[idx]
        if t > prev_b:
            survival = 1.0 - (solved_so_far / n)
            area += survival * (t - prev_b)
            prev_b = t
        while idx < m and event_times[idx] == t:
            solved_so_far += 1
            idx += 1
    if b_max > prev_b:
        survival = 1.0 - (solved_so_far / n)
        area += survival * (b_max - prev_b)
    return area


def analyse_stopping_times(
    observations: Sequence[StoppingObservation],
    budget_grid: Sequence[float],
    *,
    axis_name: Literal["tokens", "wall_seconds"],
    curve_type: CurveType,
    delta: float = 0.20,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Compute empirical survival S_pi(B), RMST(B_max), censored counts, and simultaneous bounds."""
    if not observations:
        raise ValueError("observations must be non-empty")
    if not budget_grid:
        raise ValueError("budget_grid must be non-empty")

    ordered_grid = sorted(float(b) for b in budget_grid)
    if ordered_grid[0] <= 0.0:
        raise ValueError("All budgets in budget_grid must be positive")
    n = len(observations)
    num_budgets = len(ordered_grid)
    alpha_bonf = bonferroni_alpha(alpha, num_budgets)

    curve: list[dict[str, Any]] = []
    rates_for_attainment: dict[int, float] = {}
    for b in ordered_grid:
        solved_by_b = sum(
            1
            for obs in observations
            if obs.verified and obs.cost_to_first_verified is not None and obs.cost_to_first_verified <= b
        )
        rate = solved_by_b / n
        w_lo, w_hi = wilson_interval(solved_by_b, n)
        cp_lo, cp_hi = clopper_pearson_interval(solved_by_b, n, alpha=alpha)
        cp_b_lo, cp_b_hi = clopper_pearson_interval(solved_by_b, n, alpha=alpha_bonf)
        hoeff_lo = hoeffding_simultaneous_lower_bound(rate, n, num_budgets, alpha=alpha)
        curve.append(
            {
                "budget": b,
                "verified_count": solved_by_b,
                "total_tasks": n,
                "success_probability": round(rate, 6),
                "hoeffding_simultaneous_lower": round(hoeff_lo, 6),
                "wilson_ci": [round(w_lo, 6), round(w_hi, 6)],
                "clopper_pearson_ci": [round(cp_lo, 6), round(cp_hi, 6)],
                "clopper_pearson_bonferroni_ci": [round(cp_b_lo, 6), round(cp_b_hi, 6)],
            }
        )
        rates_for_attainment[int(round(b))] = rate

    b_max = ordered_grid[-1]
    rmst = restricted_mean_time_to_success(observations, b_max)

    solved_costs = [
        float(obs.cost_to_first_verified)
        for obs in observations
        if obs.verified and obs.cost_to_first_verified is not None
    ]
    censored_count = sum(1 for obs in observations if obs.censored)
    unsuccessful_count = sum(1 for obs in observations if not obs.verified)

    # Separate aggregation by discovery_class (Section 1)
    by_class: dict[str, dict[str, Any]] = {}
    for d_cls in ("known_benchmark_problem", "novel_discovery_candidate"):
        subset = [obs for obs in observations if obs.discovery_class == d_cls]
        if subset:
            solved_sub = sum(1 for obs in subset if obs.verified)
            by_class[d_cls] = {
                "total_tasks": len(subset),
                "verified_tasks": solved_sub,
                "verified_rate": round(solved_sub / len(subset), 6),
                "rmst_at_b_max": round(restricted_mean_time_to_success(subset, b_max), 6),
            }

    return {
        "axis": axis_name,
        "curve_type": curve_type,
        "num_tasks": n,
        "b_max": b_max,
        "rmst_at_b_max": round(rmst, 6),
        "infinite_horizon_expected_cost": None,
        "censored_trials": censored_count,
        "unsuccessful_trials": unsuccessful_count,
        "verified_trials": len(solved_costs),
        "median_cost_among_verified_only": round(statistics.median(solved_costs), 6) if solved_costs else None,
        "mean_cost_among_verified_only": round(statistics.mean(solved_costs), 6) if solved_costs else None,
        "empirical_b_star_grid": finite_budget_attainment(rates_for_attainment, delta=delta),
        "by_discovery_class": by_class,
        "curve": curve,
        "epistemic_caveat": (
            "RMST is restricted to [0, B_max] with all censored and failed trials retained; "
            "infinite-horizon E[tau_q] and continuous B*_pi(delta) are never inferred from finite budgets. "
            "Distinct per-budget configurations are never conflated with a single continuous policy."
        ),
    }
