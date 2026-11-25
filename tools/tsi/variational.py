"""NKAT-URT Variational Reasoning Engine (VRE): Theorems 1 & 2, Gibbs & Feynman-Kac measures.

Implements path-space variational principles for scientific reasoning:
- Theorem 1: Minimum KL information cost inf_{Q: Q(E_q)=p1} D_KL(Q || P) = d_bin(p1 || p0),
  and full-success limit C_* = -log(p0) (undefined/infinite when p0 = 0).
- Theorem 2: Gibbs variational principle maximising
      J_lambda(Q) = E_Q[V_q] - (1/lambda) D_KL(Q || P)
  with Z_lambda = 1 - p0 + p0 * exp(lambda), logit(p*_lambda) = logit(p0) + lambda,
  and exact optimality gap J_lambda(Q*_lambda) - J_lambda(Q_hat) = (1/lambda) D_KL(Q_hat || Q*_lambda).
- Sections 8 & 10: Cost-penalised Feynman-Kac Gibbs measure
      Q*_{lambda, eta}(w) = P(w) exp(lambda * V(w) - eta * C(w)) / Z(lambda, eta)
  effective action S_eff(w) = -log P(w) - lambda * V(w) + eta * C(w), and exact cumulants
  E[V], E[C], Var(V), Cov(V, C) from derivatives of log Z(lambda, eta).

All quantities represent mathematical variational correspondences, never physical
temperature, energy consumption, or VRAM requirements.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Sequence

from .information import binary_kl, nats_to_bits


def logit(p: float) -> float:
    """Exact log-odds log(p / (1 - p)) for p in (0, 1)."""
    if not (0.0 < p < 1.0):
        raise ValueError(f"logit requires p strictly in (0, 1): {p}")
    return math.log(p / (1.0 - p))


def sigmoid(x: float) -> float:
    """Numerically stable logistic sigmoid 1 / (1 + exp(-x))."""
    if x >= 0.0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def discrete_kl(q_probs: Sequence[float], p_probs: Sequence[float]) -> float:
    """Exact discrete KL divergence D_KL(Q || P) in nats."""
    if len(q_probs) != len(p_probs) or not q_probs:
        raise ValueError("q_probs and p_probs must have equal non-zero length")
    total = 0.0
    for q, p in zip(q_probs, p_probs, strict=True):
        if q < -1e-12 or p < -1e-12:
            raise ValueError(f"Negative probability in discrete_kl: q={q}, p={p}")
        if q > 0.0:
            if p <= 0.0:
                return float("inf")
            total += q * math.log(q / p)
    return max(0.0, total)


# --------------------------------------------------------------------------- Theorem 1
def min_kl_information_cost(p0: float, p1: float) -> dict[str, Any]:
    """Theorem 1: Minimum KL cost inf_{Q: Q(E_q)=p1} D_KL(Q || P) = d_bin(p1 || p0)."""
    if not (0.0 <= p0 <= 1.0 and 0.0 <= p1 <= 1.0):
        raise ValueError(f"Probabilities must lie in [0, 1]: p0={p0}, p1={p1}")
    if p0 == 0.0 and p1 > 0.0:
        return {
            "p0": p0,
            "p1": p1,
            "achievable_with_finite_kl": False,
            "min_kl_nats": float("inf"),
            "min_kl_bits": float("inf"),
            "full_success_kl_nats": float("inf"),
            "reason": "When p0 = 0, no verified path has positive prior support; finite-KL reweighting cannot raise success.",
        }
    nats = binary_kl(p1, p0)
    full_nats = -math.log(p0) if p0 > 0.0 else float("inf")
    return {
        "p0": p0,
        "p1": p1,
        "achievable_with_finite_kl": math.isfinite(nats),
        "min_kl_nats": round(nats, 6) if math.isfinite(nats) else float("inf"),
        "min_kl_bits": round(nats_to_bits(nats), 6) if math.isfinite(nats) else float("inf"),
        "full_success_kl_nats": round(full_nats, 6) if math.isfinite(full_nats) else float("inf"),
        "full_success_kl_bits": round(nats_to_bits(full_nats), 6) if math.isfinite(full_nats) else float("inf"),
        "caveat": (
            "Idealised path-space information limit only; does not represent required "
            "VRAM, training compute, or wall-clock inference time."
        ),
    }


# --------------------------------------------------------------------------- Theorem 2
def gibbs_variational_binary(p0: float, lam: float) -> dict[str, Any]:
    """Theorem 2: Closed-form Gibbs variational solution for binary verification reward V in {0, 1}."""
    if not (0.0 <= p0 <= 1.0):
        raise ValueError(f"p0 must lie in [0, 1]: {p0}")
    if lam <= 0.0 or not math.isfinite(lam):
        raise ValueError(f"Control strength lambda must be positive and finite: {lam}")

    # Stable computation of log Z_lambda = log(1 - p0 + p0 * exp(lam))
    if p0 == 0.0:
        log_z = 0.0
        z_lam = 1.0
        p_star = 0.0
    elif p0 == 1.0:
        log_z = lam
        z_lam = math.exp(lam)
        p_star = 1.0
    else:
        a = math.log(1.0 - p0)
        b = math.log(p0) + lam
        m = max(a, b)
        log_z = m + math.log(math.exp(a - m) + math.exp(b - m))
        z_lam = math.exp(log_z) if log_z < 700.0 else float("inf")
        p_star = sigmoid(logit(p0) + lam)

    kl_star = binary_kl(p_star, p0) if (0.0 < p0 < 1.0) else 0.0
    j_star = log_z / lam
    return {
        "p0": p0,
        "lambda": lam,
        "log_Z_lambda": round(log_z, 10),
        "Z_lambda": round(z_lam, 10) if math.isfinite(z_lam) else float("inf"),
        "p_star": round(p_star, 10),
        "kl_q_star_p_nats": round(kl_star, 10),
        "optimal_functional_J_lambda": round(j_star, 10),
        "logit_shift_identity_err": (
            abs((logit(p_star) - logit(p0)) - lam) if (0.0 < p0 < 1.0 and 0.0 < p_star < 1.0) else 0.0
        ),
    }


def gibbs_functional_and_gap(
    *,
    prior_probs: Sequence[float],
    verified_rewards: Sequence[float],
    candidate_probs: Sequence[float],
    lam: float,
) -> dict[str, Any]:
    """Verify Theorem 2 exact optimality gap J_lambda(Q*) - J_lambda(Q_hat) = (1/lambda) D_KL(Q_hat || Q*)."""
    if lam <= 0.0:
        raise ValueError(f"lambda must be positive: {lam}")
    n = len(prior_probs)
    if not (len(verified_rewards) == len(candidate_probs) == n) or n == 0:
        raise ValueError("prior_probs, verified_rewards, and candidate_probs must have equal non-zero length")
    if abs(sum(prior_probs) - 1.0) > 1e-9 or abs(sum(candidate_probs) - 1.0) > 1e-9:
        raise ValueError("Probability vectors must sum to 1")

    # Compute exact Gibbs measure Q*_lambda(w) proportional to P(w) * exp(lam * V(w))
    log_unnorm = [
        (math.log(p) + lam * float(v)) if p > 0.0 else float("-inf")
        for p, v in zip(prior_probs, verified_rewards, strict=True)
    ]
    m = max(log_unnorm)
    weights = [math.exp(lu - m) if math.isfinite(lu) else 0.0 for lu in log_unnorm]
    z_shift = sum(weights)
    log_z = m + math.log(z_shift)
    q_star = [w / z_shift for w in weights]

    e_v_star = sum(q * float(v) for q, v in zip(q_star, verified_rewards, strict=True))
    e_v_hat = sum(q * float(v) for q, v in zip(candidate_probs, verified_rewards, strict=True))
    kl_star_p = discrete_kl(q_star, prior_probs)
    kl_hat_p = discrete_kl(candidate_probs, prior_probs)
    kl_hat_star = discrete_kl(candidate_probs, q_star)

    j_star = e_v_star - kl_star_p / lam
    j_hat = e_v_hat - kl_hat_p / lam
    gap_direct = j_star - j_hat
    gap_identity = kl_hat_star / lam
    return {
        "lambda": lam,
        "log_Z": log_z,
        "J_star": j_star,
        "J_hat": j_hat,
        "optimality_gap_direct": gap_direct,
        "optimality_gap_kl_over_lambda": gap_identity,
        "identity_abs_err": abs(gap_direct - gap_identity) if math.isfinite(gap_identity) else 0.0,
        "q_star": q_star,
    }


# --------------------------------------------------------------------------- Sections 8 & 10
@dataclass(frozen=True)
class PathOutcome:
    """Single path in a finite path-space ensemble with prior P(w), V(w) in {0, 1}, and total cost C(w)."""

    path_id: str
    prior_prob: float
    verified: float
    cost: float


def feynman_kac_gibbs_ensemble(
    paths: Sequence[PathOutcome],
    *,
    lam: float,
    eta: float,
) -> dict[str, Any]:
    """Evaluate Q*_{lambda, eta}(w) = P(w) exp(lambda*V(w) - eta*C(w)) / Z and exact cumulants.

    Returns:
    - Gibbs posterior probabilities Q*(w) and effective actions S_eff(w)
    - log Z(lambda, eta)
    - First cumulants: E_{Q*}[V] = d(log Z)/d(lambda), E_{Q*}[C] = -d(log Z)/d(eta)
    - Second cumulants: Var_{Q*}(V) = d^2(log Z)/d(lambda)^2, Cov_{Q*}(V, C) = -d^2(log Z)/(d(lambda) d(eta))
    - KL divergence D_KL(Q* || P) and variational objective J_{lambda, eta}(Q*)
    """
    if not paths:
        raise ValueError("paths must be non-empty")
    prior_sum = sum(p.prior_prob for p in paths)
    if abs(prior_sum - 1.0) > 1e-9 or any(p.prior_prob < 0.0 for p in paths):
        raise ValueError(f"Path prior probabilities must be non-negative and sum to 1 (got {prior_sum})")

    eff_actions: list[float] = []
    neg_actions: list[float] = []
    for p in paths:
        if p.prior_prob <= 0.0:
            eff_actions.append(float("inf"))
            neg_actions.append(float("-inf"))
        else:
            s_eff = -math.log(p.prior_prob) - lam * p.verified + eta * p.cost
            eff_actions.append(s_eff)
            neg_actions.append(-s_eff)

    m = max(neg_actions)
    weights = [math.exp(na - m) if math.isfinite(na) else 0.0 for na in neg_actions]
    z_shift = sum(weights)
    log_z = m + math.log(z_shift)
    q_star = [w / z_shift for w in weights]

    ev_v = sum(q * p.verified for q, p in zip(q_star, paths, strict=True))
    ev_c = sum(q * p.cost for q, p in zip(q_star, paths, strict=True))
    var_v = sum(q * ((p.verified - ev_v) ** 2) for q, p in zip(q_star, paths, strict=True))
    var_c = sum(q * ((p.cost - ev_c) ** 2) for q, p in zip(q_star, paths, strict=True))
    cov_vc = sum(q * (p.verified - ev_v) * (p.cost - ev_c) for q, p in zip(q_star, paths, strict=True))

    kl_qp = discrete_kl(q_star, [p.prior_prob for p in paths])
    obj = lam * ev_v - eta * ev_c - kl_qp

    return {
        "lambda": lam,
        "eta": eta,
        "log_Z": log_z,
        "expected_verified_success": ev_v,
        "expected_cost": ev_c,
        "var_verified_success": var_v,
        "var_cost": var_c,
        "cov_verified_cost": cov_vc,
        "kl_q_star_p_nats": kl_qp,
        "variational_objective": obj,
        "objective_equals_log_Z_err": abs(obj - log_z),
        "paths": [
            {
                "path_id": p.path_id,
                "prior_prob": p.prior_prob,
                "verified": p.verified,
                "cost": p.cost,
                "effective_action": eff_actions[i],
                "posterior_prob": q_star[i],
            }
            for i, p in enumerate(paths)
        ],
    }
