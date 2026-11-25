"""Weibull scientific-reasoning scaling hypothesis fitter and residual diagnostics (Section 12).

Fits the empirical hypothesis:
    S(B) = s_inf * [1 - exp(-(B / B0)^beta)]

Explicitly treats this as a testable research hypothesis — NEVER as a universal law —
and reports residuals, jackknife parameter uncertainty, and held-out prediction RMSE.
Finite-budget observations never establish the true asymptotic ceiling s_inf.
"""

from __future__ import annotations

import math
from typing import Any, Sequence


def weibull_success_model(budget: float, s_inf: float, b0: float, beta: float) -> float:
    """Evaluate S(B) = s_inf * [1 - exp(-(B / B0)^beta)]."""
    if budget <= 0.0:
        return 0.0
    if not (0.0 < s_inf <= 1.0):
        raise ValueError(f"s_inf must lie in (0, 1]: {s_inf}")
    if b0 <= 0.0 or beta <= 0.0:
        raise ValueError(f"b0 and beta must be positive: b0={b0}, beta={beta}")
    x = math.pow(budget / b0, beta)
    # Clamp exponent for numerical stability
    if x > 700.0:
        return s_inf
    return s_inf * (1.0 - math.exp(-x))


def _fit_params_core(budgets: Sequence[float], rates: Sequence[float]) -> tuple[float, float, float, float]:
    """Deterministic stdlib coarse-grid + coordinate-refinement least-squares fitter."""
    b_min = min(budgets)
    b_max = max(budgets)
    best_sse = float("inf")
    best = (min(1.0, max(rates) if max(rates) > 0.0 else 0.5), max(1.0, b_min), 1.0)

    # Coarse grid covering s_inf in [0.1, 1.0], log-spaced b0, and beta in [0.25, 3.0]
    s_grid = [0.10 + 0.09 * i for i in range(11)]
    log_lo = math.log(max(1e-3, b_min * 0.25))
    log_hi = math.log(max(b_max * 4.0, b_min * 2.0))
    b0_grid = [math.exp(log_lo + (log_hi - log_lo) * i / 12.0) for i in range(13)]
    beta_grid = [0.25, 0.5, 0.75, 1.0, 1.35, 1.8, 2.5, 3.2]

    for s_inf in s_grid:
        for b0 in b0_grid:
            for beta in beta_grid:
                sse = 0.0
                for b, y in zip(budgets, rates, strict=True):
                    pred = weibull_success_model(b, s_inf, b0, beta)
                    diff = pred - y
                    sse += diff * diff
                if sse < best_sse:
                    best_sse = sse
                    best = (s_inf, b0, beta)

    # Coordinate pattern refinement
    s_cur, b0_cur, beta_cur = best
    steps = [0.05, b0_cur * 0.25, 0.25]
    for _ in range(40):
        improved = False
        candidates = [
            (min(1.0, max(0.01, s_cur + ds)), b0_cur, beta_cur)
            for ds in (-steps[0], steps[0])
        ] + [
            (s_cur, max(1e-4, b0_cur + db), beta_cur)
            for db in (-steps[1], steps[1])
        ] + [
            (s_cur, b0_cur, max(0.05, min(10.0, beta_cur + dbe)))
            for dbe in (-steps[2], steps[2])
        ]
        for cand in candidates:
            sse = sum(
                (weibull_success_model(b, cand[0], cand[1], cand[2]) - y) ** 2
                for b, y in zip(budgets, rates, strict=True)
            )
            if sse + 1e-15 < best_sse:
                best_sse = sse
                s_cur, b0_cur, beta_cur = cand
                improved = True
        if not improved:
            steps = [st * 0.5 for st in steps]
            if max(steps) < 1e-6:
                break

    return s_cur, b0_cur, beta_cur, best_sse


def fit_weibull_scaling(
    budgets: Sequence[float],
    rates: Sequence[float],
    *,
    heldout_budgets: Sequence[float] | None = None,
    heldout_rates: Sequence[float] | None = None,
) -> dict[str, Any]:
    """Fit Section 12 scaling hypothesis with residuals, jackknife ranges, and held-out checks."""
    if len(budgets) != len(rates) or len(budgets) < 3:
        raise ValueError("At least 3 (budget, rate) observations are required to fit 3 parameters")
    b_list = [float(b) for b in budgets]
    r_list = [float(r) for r in rates]
    if any(b <= 0.0 for b in b_list):
        raise ValueError("All budgets must be positive")
    if any(r < 0.0 or r > 1.0 for r in r_list):
        raise ValueError("All rates must lie in [0, 1]")

    s_inf, b0, beta, sse = _fit_params_core(b_list, r_list)
    preds = [weibull_success_model(b, s_inf, b0, beta) for b in b_list]
    residuals = [round(y - p, 6) for y, p in zip(r_list, preds, strict=True)]
    rmse = math.sqrt(sse / len(b_list))

    # Leave-one-out jackknife range when n >= 4
    jackknife: dict[str, list[float]] | None = None
    if len(b_list) >= 4:
        jk_s: list[float] = []
        jk_b0: list[float] = []
        jk_beta: list[float] = []
        for drop in range(len(b_list)):
            sub_b = [b for i, b in enumerate(b_list) if i != drop]
            sub_r = [r for i, r in enumerate(r_list) if i != drop]
            js, jb0, jbe, _ = _fit_params_core(sub_b, sub_r)
            jk_s.append(js)
            jk_b0.append(jb0)
            jk_beta.append(jbe)
        jackknife = {
            "s_inf_range": [round(min(jk_s), 6), round(max(jk_s), 6)],
            "b0_range": [round(min(jk_b0), 6), round(max(jk_b0), 6)],
            "beta_range": [round(min(jk_beta), 6), round(max(jk_beta), 6)],
        }

    heldout_eval: dict[str, Any] | None = None
    if heldout_budgets is not None and heldout_rates is not None:
        if len(heldout_budgets) != len(heldout_rates) or not heldout_budgets:
            raise ValueError("heldout_budgets and heldout_rates must have equal non-zero length")
        h_preds = [weibull_success_model(float(b), s_inf, b0, beta) for b in heldout_budgets]
        h_res = [float(y) - p for y, p in zip(heldout_rates, h_preds, strict=True)]
        h_rmse = math.sqrt(sum(e * e for e in h_res) / len(h_res))
        heldout_eval = {
            "budgets": [float(b) for b in heldout_budgets],
            "observed_rates": [float(r) for r in heldout_rates],
            "predicted_rates": [round(p, 6) for p in h_preds],
            "residuals": [round(e, 6) for e in h_res],
            "rmse": round(h_rmse, 6),
        }

    return {
        "model": "weibull_scaling_hypothesis",
        "parameters": {
            "s_inf": round(s_inf, 6),
            "b0": round(b0, 6),
            "beta": round(beta, 6),
        },
        "train_rmse": round(rmse, 6),
        "train_residuals": residuals,
        "jackknife_parameter_ranges": jackknife,
        "heldout_prediction": heldout_eval,
        "epistemic_caveat": (
            "Empirical scaling hypothesis only (not a universal law). "
            "Finite-budget observations never prove the asymptotic ceiling s_inf."
        ),
    }
