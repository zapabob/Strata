"""Optimal restart theory and exact finite-budget Bellman dynamic programming (Sections 7 & 9).

Provides:
- URT optimal restart cutoff solver:
      L(b) = [c0 + integral_0^b (1 - F(t)) dt] / F(b),   b* = argmin_{b: F(b) > 0} L(b)
- Exact backward Bellman DP on small discrete research-state MDPs:
      V_b(s) = max_{a : c_a <= b} E[ V_{b - c_a}(s') ]
      V_b(s_verified) = 1,  V_0(s_unverified) = 0
- Exact policy evaluation under true vs estimated transition kernels to verify Section 10
  URT stability bounds directly on finite MDPs.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence


def optimal_restart_cutoff(
    cdf_points: Sequence[tuple[float, float]],
    restart_overhead_c0: float = 0.0,
) -> dict[str, Any]:
    """Compute expected discovery cost L(b) and optimal cutoff b* = argmin L(b) (Section 7).

    `cdf_points` is a sequence of (time_b, F(b)) pairs representing a monotone non-decreasing
    CDF F(t) on t >= 0 (right-continuous piecewise-constant step CDF or empirical CDF).
    Requires at least one point with F(b) > 0.
    """
    if not cdf_points:
        raise ValueError("cdf_points must be non-empty")
    if restart_overhead_c0 < 0.0 or not math.isfinite(restart_overhead_c0):
        raise ValueError(f"restart_overhead_c0 must be finite and non-negative: {restart_overhead_c0}")

    ordered = sorted((float(t), float(f)) for t, f in cdf_points)
    prev_f = 0.0
    for t, f in ordered:
        if t < 0.0:
            raise ValueError(f"Time coordinate must be non-negative: {t}")
        if not (0.0 <= f <= 1.0):
            raise ValueError(f"CDF value must lie in [0, 1]: {f}")
        if f + 1e-12 < prev_f:
            raise ValueError("CDF values must be monotonically non-decreasing")
        prev_f = f

    # Integrate survival 1 - F(t) left-continuously between step knots (0, 0) -> (t_i, F(t_i)).
    integral = 0.0
    prev_t = 0.0
    prev_cdf = 0.0
    table: list[dict[str, float]] = []
    best_b: float | None = None
    best_l = float("inf")

    for t, f in ordered:
        if t > prev_t:
            integral += (1.0 - prev_cdf) * (t - prev_t)
            prev_t = t
        prev_cdf = f
        if f > 0.0:
            expected_cost = (restart_overhead_c0 + integral) / f
            table.append(
                {
                    "cutoff_b": round(t, 6),
                    "cdf_F_b": round(f, 6),
                    "survival_integral": round(integral, 6),
                    "expected_discovery_cost_L_b": round(expected_cost, 6),
                }
            )
            if expected_cost < best_l:
                best_l = expected_cost
                best_b = t

    if best_b is None:
        raise ValueError("No cutoff point has F(b) > 0; L(b) is undefined")

    return {
        "restart_overhead_c0": restart_overhead_c0,
        "optimal_cutoff_b_star": round(best_b, 6),
        "min_expected_discovery_cost": round(best_l, 6),
        "table": table,
        "assumption_warning": (
            "Assumes independent restarts from a shared time-to-solution distribution F(t). "
            "If restarts repeat correlated reasoning errors, independence fails."
        ),
    }


@dataclass(frozen=True)
class DiscreteMDP:
    """Small finite-state MDP for exact finite-budget Bellman dynamic programming."""

    states: tuple[str, ...]
    verified_states: frozenset[str]
    actions: tuple[str, ...]
    action_costs: Mapping[str, int]
    # transitions[(state, action)] -> list of (next_state, probability)
    transitions: Mapping[tuple[str, str], Sequence[tuple[str, float]]]

    def validate(self) -> None:
        state_set = set(self.states)
        for vs in self.verified_states:
            if vs not in state_set:
                raise ValueError(f"Verified terminal state {vs!r} not in states")
        for act in self.actions:
            c = self.action_costs.get(act)
            if c is None or c <= 0:
                raise ValueError(f"Action {act!r} must have a positive integer cost")
        for (s, a), dist in self.transitions.items():
            if s not in state_set:
                raise ValueError(f"Unknown state {s!r} in transitions")
            total_p = sum(p for _, p in dist)
            if abs(total_p - 1.0) > 1e-9 or any(p < -1e-12 for _, p in dist):
                raise ValueError(f"Transition probabilities for ({s!r}, {a!r}) must sum to 1 (got {total_p})")
            for ns, _ in dist:
                if ns not in state_set:
                    raise ValueError(f"Unknown next state {ns!r} in transitions")


def solve_bellman_dp(mdp: DiscreteMDP, max_budget: int) -> dict[str, Any]:
    """Compute exact optimal Bellman values V_b(s) and actions pi*_b(s) for b = 0..max_budget."""
    mdp.validate()
    if max_budget < 0:
        raise ValueError(f"max_budget must be non-negative: {max_budget}")

    values: dict[int, dict[str, float]] = {}
    policy: dict[int, dict[str, str | None]] = {}

    for b in range(max_budget + 1):
        values[b] = {}
        policy[b] = {}
        for s in mdp.states:
            if s in mdp.verified_states:
                values[b][s] = 1.0
                policy[b][s] = None
                continue
            best_val = 0.0
            best_act: str | None = None
            for act in mdp.actions:
                cost = mdp.action_costs[act]
                if cost > b:
                    continue
                dist = mdp.transitions.get((s, act))
                if not dist:
                    continue
                exp_val = sum(prob * values[b - cost][ns] for ns, prob in dist)
                if best_act is None or exp_val > best_val + 1e-15:
                    best_val = exp_val
                    best_act = act
            values[b][s] = best_val
            policy[b][s] = best_act

    return {
        "max_budget": max_budget,
        "values": values,
        "policy": policy,
    }


def evaluate_policy_dp(
    mdp: DiscreteMDP,
    policy: Mapping[int, Mapping[str, str | None]],
    max_budget: int,
) -> dict[int, dict[str, float]]:
    """Evaluate a fixed budget-dependent policy under `mdp`'s transition kernel."""
    mdp.validate()
    values: dict[int, dict[str, float]] = {}
    for b in range(max_budget + 1):
        values[b] = {}
        for s in mdp.states:
            if s in mdp.verified_states:
                values[b][s] = 1.0
                continue
            act = policy.get(b, {}).get(s)
            if act is None:
                values[b][s] = 0.0
                continue
            cost = mdp.action_costs[act]
            if cost > b:
                values[b][s] = 0.0
                continue
            dist = mdp.transitions.get((s, act), ())
            values[b][s] = sum(prob * values[b - cost][ns] for ns, prob in dist)
    return values


def max_transition_tv_distance(mdp_true: DiscreteMDP, mdp_est: DiscreteMDP) -> float:
    """Compute max_{s, a} TV(P_a(.|s), P_hat_a(.|s)) across shared state-action pairs."""
    max_tv = 0.0
    for key, dist_t in mdp_true.transitions.items():
        dist_e = mdp_est.transitions.get(key)
        if dist_e is None:
            continue
        pt = {ns: p for ns, p in dist_t}
        pe = {ns: p for ns, p in dist_e}
        all_ns = set(pt).union(pe)
        tv = 0.5 * sum(abs(pt.get(ns, 0.0) - pe.get(ns, 0.0)) for ns in all_ns)
        if tv > max_tv:
            max_tv = tv
    return max_tv
