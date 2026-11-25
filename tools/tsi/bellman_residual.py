"""Bellman residual certification, error propagation, and unified quantisation-control bounds.

Implements Theorems 4, 5, 6 and Section 12 of the NKAT-URT VRE specification:
- Theorem 4: Per-step log-potential error propagation:
      D_KL(Q_hat || Q*_lambda) <= 0.5 * sum_t eps_t^2
      Q_hat(E_q) >= p*_lambda - 0.5 * sqrt(sum_t eps_t^2)
- Theorem 5: Log-Bellman residual r(u) = log h_hat(u) - log sum_a p(a|u) h_hat(ua),
  path cumulative residual R(w) = sum r(a_{<=t}), telescoping path identity
      Q_hat(w) = P(w) * exp(lambda * V(w) + R(w)) / h_hat(root)
  and non-perturbative logit lower bound:
      logit Q_hat(E_q) >= logit(p0) + lambda - L   where osc(R) <= L.
- Theorem 6: Unified quantisation + control bound:
      D_KL(Q_hat_Q || Q*_R) <= (1/8) * sum_t (r_t + 2 * eps_t)^2
      p_hat_Q >= p*_R - (1/4) * sqrt(sum_t (r_t + 2 * eps_t)^2)
- Section 12: Unified discovery-rate improvement criterion:
      lambda - L > logit(p_crit) - logit(p0)
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from .discovery_rate import critical_quantised_success_rate
from .doob import FiniteSearchTree, doob_step_policy, rollout_policy_path_probs
from .variational import gibbs_variational_binary, logit, sigmoid


# --------------------------------------------------------------------------- Theorem 4
def control_error_propagation_bound(
    *,
    p0: float,
    lam: float,
    step_log_h_errors: Sequence[float],
) -> dict[str, Any]:
    """Theorem 4: KL and success-rate degradation from uniform per-step |log h_hat - log h| <= eps_t."""
    if not step_log_h_errors:
        raise ValueError("step_log_h_errors must be non-empty")
    eps = [float(e) for e in step_log_h_errors]
    if any(e < 0.0 or not math.isfinite(e) for e in eps):
        raise ValueError("All step_log_h_errors must be finite and non-negative")

    sum_sq = sum(e * e for e in eps)
    kl_ub = 0.5 * sum_sq
    p_star = float(gibbs_variational_binary(p0, lam)["p_star"])
    success_lb = max(0.0, p_star - 0.5 * math.sqrt(sum_sq))
    return {
        "p0": p0,
        "lambda": lam,
        "p_star": round(p_star, 8),
        "horizon_steps": len(eps),
        "sum_eps_sq": round(sum_sq, 8),
        "kl_upper_bound_nats": round(kl_ub, 8),
        "success_lower_bound": round(success_lb, 8),
        "conditional_on_uniform_step_error": True,
    }


# --------------------------------------------------------------------------- Theorem 5
def bellman_residual_success_bound(
    *,
    p0: float,
    lam: float,
    residual_oscillation_L: float,
    target_success_rate: float | None = None,
    uniform_bound_certified: bool = False,
) -> dict[str, Any]:
    """Theorem 5: Non-perturbative logit lower bound logit(Q_hat(E_q)) >= logit(p0) + lambda - L."""
    if not (0.0 < p0 < 1.0):
        raise ValueError(f"p0 must lie strictly in (0, 1): {p0}")
    if lam <= 0.0 or not math.isfinite(lam):
        raise ValueError(f"lam must be positive and finite: {lam}")
    if residual_oscillation_L < 0.0 or not math.isfinite(residual_oscillation_L):
        raise ValueError(f"residual_oscillation_L must be finite and non-negative: {residual_oscillation_L}")

    logit_p0 = logit(p0)
    p_star = sigmoid(logit_p0 + lam)
    p_lower = sigmoid(logit_p0 + lam - residual_oscillation_L)

    req_lam: float | None = None
    meets_target: bool | None = None
    if target_success_rate is not None:
        if not (0.0 < target_success_rate < 1.0):
            raise ValueError(f"target_success_rate must lie strictly in (0, 1): {target_success_rate}")
        req_lam = logit(target_success_rate) - logit_p0 + residual_oscillation_L
        meets_target = lam >= req_lam - 1e-12

    return {
        "p0": p0,
        "lambda": lam,
        "residual_oscillation_L": residual_oscillation_L,
        "ideal_p_star": round(p_star, 8),
        "guaranteed_lower_bound": round(p_lower, 8),
        "target_success_rate": target_success_rate,
        "sufficient_lambda_for_target": round(req_lam, 8) if req_lam is not None else None,
        "meets_target_under_bound": meets_target,
        "uniform_bound_certified": uniform_bound_certified,
        "caveat": (
            "Applies rigorously only when sup_w R(w) - inf_w R(w) <= L holds uniformly over "
            "all generation paths; finite calibration samples do not establish a universal bound."
        ),
    }


def audit_tree_bellman_residuals(
    tree: FiniteSearchTree,
    approx_potentials: Mapping[str, float],
    *,
    lam: float,
) -> dict[str, Any]:
    """Audit Theorem 5 on a finite proof-search tree directly from approximate potentials h_hat.

    Requires exact terminal verification potentials h_hat(w) = exp(lambda * V(w)).
    Verifies:
    1. Exact telescoping identity Q_hat(w) == P(w) * exp(lambda*V(w) + R(w)) / h_hat(root)
    2. True Q_hat(E_q) >= sigmoid(logit(p0) + lambda - L) where L = max(R) - min(R).
    """
    tree.validate()
    for term, v in tree.terminals.items():
        expected_h = math.exp(lam * float(v))
        if abs(float(approx_potentials[term]) - expected_h) > 1e-9:
            raise ValueError(
                f"Terminal potential at {term!r} must equal exp(lambda*V)={expected_h:.6f} "
                f"(got {approx_potentials[term]})"
            )

    # Node-level log-Bellman residuals r(u) = log h_hat(u) - log sum_a p(a|u) h_hat(ua)
    node_residuals: dict[str, float] = {}
    for node, elist in tree.edges.items():
        h_u = float(approx_potentials[node])
        if h_u <= 0.0:
            raise ValueError(f"Potential h_hat({node!r}) must be positive")
        expected_next = sum(e.prior_prob * float(approx_potentials[e.child]) for e in elist)
        if expected_next <= 0.0:
            raise ValueError(f"Expected next potential at {node!r} must be positive")
        node_residuals[node] = math.log(h_u) - math.log(expected_next)

    # Compute exact induced policy Q_hat and compare path probabilities against telescoping formula
    policy_hat = doob_step_policy(tree, approx_potentials, eta=0.0)
    q_hat_paths = rollout_policy_path_probs(tree, policy_hat)

    path_R: dict[str, float] = {}
    telescoping_max_err = 0.0
    h_root = float(approx_potentials[tree.root])

    def dfs(node: str, trail: list[str], p_acc: float, r_acc: float) -> None:
        nonlocal telescoping_max_err
        if node in tree.terminals:
            pid = "/".join(trail) if trail else node
            path_R[pid] = r_acc
            v = float(tree.terminals[node])
            q_formula = (p_acc * math.exp(lam * v + r_acc)) / h_root
            err = abs(q_hat_paths[pid] - q_formula)
            if err > telescoping_max_err:
                telescoping_max_err = err
            return
        r_here = node_residuals[node]
        for e in tree.edges[node]:
            dfs(e.child, trail + [e.action], p_acc * e.prior_prob, r_acc + r_here)

    dfs(tree.root, [], 1.0, 0.0)

    paths = tree.enumerate_paths()
    p0 = sum(p.prior_prob * p.verified for p in paths)
    q_hat_success = sum(q_hat_paths[p.path_id] * p.verified for p in paths)
    r_vals = list(path_R.values())
    osc_L = max(r_vals) - min(r_vals)
    bound_info = bellman_residual_success_bound(
        p0=p0,
        lam=lam,
        residual_oscillation_L=osc_L,
        uniform_bound_certified=True,
    )
    lb = float(bound_info["guaranteed_lower_bound"])
    return {
        "p0": round(p0, 8),
        "lambda": lam,
        "oscillation_L": round(osc_L, 8),
        "telescoping_max_abs_err": telescoping_max_err,
        "exact_q_hat_success": round(q_hat_success, 8),
        "theorem5_lower_bound": lb,
        "lower_bound_holds": q_hat_success + 1e-12 >= lb,
        "node_residuals": {k: round(v, 8) for k, v in node_residuals.items()},
        "path_cumulative_residuals": {k: round(v, 8) for k, v in path_R.items()},
    }


# --------------------------------------------------------------------------- Theorem 6
def unified_quantisation_control_bound(
    *,
    p_ref_star: float,
    logit_spans_r: Sequence[float],
    control_log_errors_eps: Sequence[float],
) -> dict[str, Any]:
    """Theorem 6: Unified KL & success-rate bound combining quantisation r_t and control eps_t.

        D_KL(Q_hat_Q || Q*_R) <= (1/8) * sum_t (r_t + 2 * eps_t)^2
        p_hat_Q >= p*_R - (1/4) * sqrt(sum_t (r_t + 2 * eps_t)^2)
    """
    if not (0.0 <= p_ref_star <= 1.0):
        raise ValueError(f"p_ref_star must lie in [0, 1]: {p_ref_star}")
    if len(logit_spans_r) != len(control_log_errors_eps) or not logit_spans_r:
        raise ValueError("logit_spans_r and control_log_errors_eps must have equal non-zero length")
    rs = [float(x) for x in logit_spans_r]
    es = [float(x) for x in control_log_errors_eps]
    if any(x < 0.0 or not math.isfinite(x) for x in rs + es):
        raise ValueError("All error bounds must be finite and non-negative")

    sum_combined_sq = sum((r + 2.0 * e) ** 2 for r, e in zip(rs, es, strict=True))
    sum_quant_only_sq = sum(r * r for r in rs)
    sum_ctrl_only_sq = sum((2.0 * e) ** 2 for e in es)

    kl_ub = sum_combined_sq / 8.0
    p_lower = max(0.0, p_ref_star - 0.25 * math.sqrt(sum_combined_sq))
    return {
        "p_ref_star": p_ref_star,
        "horizon_steps": len(rs),
        "kl_upper_bound_nats": round(kl_ub, 8),
        "quant_only_kl_contribution_nats": round(sum_quant_only_sq / 8.0, 8),
        "control_only_kl_contribution_nats": round(sum_ctrl_only_sq / 8.0, 8),
        "cross_term_kl_contribution_nats": round((sum_combined_sq - sum_quant_only_sq - sum_ctrl_only_sq) / 8.0, 8),
        "p_hat_Q_lower_bound": round(p_lower, 8),
        "conditional_on_uniform_bounds": True,
    }


# --------------------------------------------------------------------------- Section 12
def certify_controlled_discovery_rate(
    *,
    p0: float,
    cost_uncontrolled: float,
    cost_controlled: float,
    lam: float,
    residual_oscillation_L: float,
    assumptions_certified: bool = False,
) -> dict[str, Any]:
    """Section 12 unified discovery-rate improvement criterion for controlled reasoning.

    Under independent constant-cost trials with baseline (p0, c0) and controlled cost c1:
        p_crit = 1 - (1 - p0)^(c1 / c0)
    Sufficient condition for Lambda_controlled > Lambda_uncontrolled:
        lambda - L > logit(p_crit) - logit(p0)
    """
    if not (0.0 < p0 < 1.0):
        raise ValueError(f"p0 must lie strictly in (0, 1): {p0}")
    if cost_uncontrolled <= 0.0 or cost_controlled <= 0.0:
        raise ValueError("Costs must be positive")
    if lam <= 0.0 or residual_oscillation_L < 0.0:
        raise ValueError("lam must be positive and residual_oscillation_L non-negative")

    p_crit = critical_quantised_success_rate(p0, cost_uncontrolled, cost_controlled)
    required_margin = logit(p_crit) - logit(p0)
    achieved_margin = lam - residual_oscillation_L
    inequality_satisfied = achieved_margin > required_margin

    return {
        "p0": p0,
        "cost_uncontrolled": cost_uncontrolled,
        "cost_controlled": cost_controlled,
        "cost_ratio_c1_over_c0": round(cost_controlled / cost_uncontrolled, 6),
        "p_crit": round(p_crit, 8),
        "required_logit_margin": round(required_margin, 8),
        "achieved_margin_lambda_minus_L": round(achieved_margin, 8),
        "inequality_satisfied": inequality_satisfied,
        "certified_improvement": bool(inequality_satisfied and assumptions_certified),
        "assumptions_certified": assumptions_certified,
        "caveat": (
            "Strict certification holds only if p0, full end-to-end costs (c0, c1), and the "
            "uniform path-space residual oscillation L are independently verified."
        ),
    }
