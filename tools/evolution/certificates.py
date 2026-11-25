"""URT evolutionary speedup certification and search amortisation economics (Sections 14 & 20).

Implements:
- Paired log-speedup d_i = ln(T_{base, i} / T_{cand, i}) over independent measurement blocks
- Bounded-range Hoeffding lower confidence bound:
      LCB(d) = mean(d) - R * sqrt(ln(1 / alpha) / (2 * n))
  STRICTLY gated on `range_width_R_certified=True` (refuses blind Hoeffding when true
  timing range R is unknown!)
- Paired block bootstrap lower confidence bound for unbounded real-world timings
- Section 20 search amortisation break-even calculator:
      break_even_tokens = total_search_and_overhead_s / delta_t_per_token_s
"""

from __future__ import annotations

import math
import random
import statistics
from typing import Any, Sequence


def certify_paired_speedup(
    baseline_times_s: Sequence[float],
    candidate_times_s: Sequence[float],
    *,
    alpha: float = 0.05,
    num_hypotheses: int = 1,
    required_margin_log: float = 0.0,
    range_width_R: float | None = None,
    range_width_R_certified: bool = False,
    bootstrap_samples: int = 2000,
    seed: int = 42,
    is_independent_holdout: bool = False,
) -> dict[str, Any]:
    """Certify speedup of a candidate over baseline from paired independent timing blocks."""
    if len(baseline_times_s) != len(candidate_times_s) or not baseline_times_s:
        raise ValueError("baseline_times_s and candidate_times_s must have equal non-zero length")
    if any(t <= 0.0 for t in baseline_times_s) or any(t <= 0.0 for t in candidate_times_s):
        raise ValueError("All measured durations must be strictly positive")
    if not (0.0 < alpha < 1.0):
        raise ValueError(f"alpha must lie in (0, 1): {alpha}")
    if num_hypotheses < 1:
        raise ValueError(f"num_hypotheses must be >= 1: {num_hypotheses}")

    n = len(baseline_times_s)
    alpha_adj = alpha / float(num_hypotheses)
    ds = [math.log(tb / tc) for tb, tc in zip(baseline_times_s, candidate_times_s, strict=True)]
    mean_d = statistics.mean(ds)
    geom_speedup = math.exp(mean_d)

    # Bounded-range Hoeffding LCB (ONLY valid when true range width R is certified a priori!)
    hoeffding_lcb: float | None = None
    if range_width_R_certified and range_width_R is not None and range_width_R > 0.0:
        radius = range_width_R * math.sqrt(math.log(1.0 / alpha_adj) / (2.0 * n))
        hoeffding_lcb = mean_d - radius

    # Non-parametric paired block bootstrap one-sided LCB at level alpha_adj
    rng = random.Random(seed)
    boot_means: list[float] = []
    for _ in range(max(200, int(bootstrap_samples))):
        sample = [ds[rng.randrange(n)] for _ in range(n)]
        boot_means.append(sum(sample) / n)
    boot_means.sort()
    q_idx = min(len(boot_means) - 1, max(0, int(math.floor(alpha_adj * len(boot_means)))))
    bootstrap_lcb = boot_means[q_idx]

    active_lcb = hoeffding_lcb if hoeffding_lcb is not None else bootstrap_lcb
    certified = bool(is_independent_holdout and active_lcb > required_margin_log)

    return {
        "n_paired_blocks": n,
        "alpha": alpha,
        "bonferroni_alpha": round(alpha_adj, 8),
        "mean_log_speedup_d": round(mean_d, 6),
        "geometric_mean_speedup": round(geom_speedup, 6),
        "hoeffding_lcb_d": round(hoeffding_lcb, 6) if hoeffding_lcb is not None else None,
        "bootstrap_lcb_d": round(bootstrap_lcb, 6),
        "active_lcb_d": round(active_lcb, 6),
        "active_lcb_speedup": round(math.exp(active_lcb), 6),
        "required_margin_log": required_margin_log,
        "is_independent_holdout": is_independent_holdout,
        "range_width_R_certified": range_width_R_certified,
        "certified_speedup": certified,
        "caveat": (
            "Hoeffding LCB is emitted only when a bounded range R is certified a priori; "
            "otherwise paired block bootstrap LCB is reported. Certification requires "
            "evaluation on an independent holdout separated from search data."
        ),
    }


def search_amortisation_breakeven(
    *,
    search_wall_s: float,
    build_and_verify_s: float,
    delta_t_saved_per_token_s: float,
    expected_deployment_tokens: int | None = None,
) -> dict[str, Any]:
    """Section 20 cost-effectiveness check: Break-even tokens = T_total / delta_t."""
    if search_wall_s < 0.0 or build_and_verify_s < 0.0:
        raise ValueError("Search and verification overhead times must be non-negative")
    total_overhead = search_wall_s + build_and_verify_s
    if delta_t_saved_per_token_s <= 0.0:
        return {
            "total_search_and_verify_s": round(total_overhead, 4),
            "delta_t_saved_ms_per_token": round(delta_t_saved_per_token_s * 1000.0, 6),
            "break_even_tokens": None,
            "cost_recovered_at_expected_usage": False,
            "reason": "No positive per-token latency reduction; search cost is never amortised.",
        }
    breakeven = total_overhead / delta_t_saved_per_token_s
    recovered = (
        bool(expected_deployment_tokens >= breakeven)
        if expected_deployment_tokens is not None
        else None
    )
    return {
        "total_search_and_verify_s": round(total_overhead, 4),
        "delta_t_saved_ms_per_token": round(delta_t_saved_per_token_s * 1000.0, 6),
        "break_even_tokens": int(math.ceil(breakeven)),
        "expected_deployment_tokens": expected_deployment_tokens,
        "cost_recovered_at_expected_usage": recovered,
    }
