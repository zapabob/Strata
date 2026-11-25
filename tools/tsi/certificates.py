"""URT certification routines for quantisation discovery rate and policy stability.

Implements:
- Section 5: Information-geometric quantisation discovery-rate certification
  (accepts ONLY `certified_sequence_kl_upper_bound`; explicitly refuses `empirical_topk_kl`,
  single-prefix `empirical_full_vocab_kl`, and `estimated_sequence_kl`).
- Section 10: URT policy stability certification under uniform TV transition error:
  V*_N - V^{pi_hat}_N <= min(1, 2*N*eps) and tighter coupling bound min(1, 2*[1 - (1 - eps)^N]).
"""

from __future__ import annotations

import math
from typing import Any

from .discovery_rate import critical_quantised_success_rate
from .information import (
    KLKind,
    VALID_KL_KINDS,
    binary_kl,
    pinsker_success_lower_bound,
)


def certify_quantisation_discovery_rate(
    *,
    p_ref: float,
    cost_ref: float,
    cost_quant: float,
    kl_value: float,
    kl_kind: KLKind,
) -> dict[str, Any]:
    """Certify Lambda_Q > Lambda_R from a certified sequence KL upper bound (Section 5).

    Certification condition (for c_Q < c_R):
        KL(P_R || P_Q) < binary_KL(p_R || p_crit)
    where p_crit = 1 - (1 - p_R)^(c_Q / c_R).

    Strictly refuses certification when `kl_kind != "certified_sequence_kl_upper_bound"`.
    """
    if kl_kind not in VALID_KL_KINDS:
        raise ValueError(f"Unsupported kl_kind: {kl_kind!r}")
    if not (0.0 <= p_ref <= 1.0):
        raise ValueError(f"p_ref must lie in [0, 1]: {p_ref}")
    if cost_ref <= 0.0 or cost_quant <= 0.0:
        raise ValueError("cost_ref and cost_quant must be positive")
    if kl_value < 0.0:
        raise ValueError(f"kl_value must be non-negative: {kl_value}")

    p_crit = critical_quantised_success_rate(p_ref, cost_ref, cost_quant)
    kl_threshold = binary_kl(p_ref, p_crit) if (0.0 < p_ref < 1.0 and 0.0 < p_crit < 1.0) else 0.0
    pinsker_lb = pinsker_success_lower_bound(p_ref, kl_value)

    if kl_kind != "certified_sequence_kl_upper_bound":
        return {
            "certified": False,
            "reason": (
                f"Certification refused: kl_kind={kl_kind!r} is not a "
                "'certified_sequence_kl_upper_bound' over the full answer distribution."
            ),
            "kl_kind": kl_kind,
            "kl_value": kl_value,
            "p_ref": p_ref,
            "cost_ref": cost_ref,
            "cost_quant": cost_quant,
            "p_crit": round(p_crit, 6),
            "kl_threshold_binary_kl": round(kl_threshold, 6),
            "pinsker_p_quant_lower": round(pinsker_lb, 6),
        }

    if cost_quant >= cost_ref:
        return {
            "certified": False,
            "reason": "Quantised total trial cost c_Q must be strictly lower than reference cost c_R.",
            "kl_kind": kl_kind,
            "kl_value": kl_value,
            "p_ref": p_ref,
            "cost_ref": cost_ref,
            "cost_quant": cost_quant,
            "p_crit": round(p_crit, 6),
            "kl_threshold_binary_kl": round(kl_threshold, 6),
            "pinsker_p_quant_lower": round(pinsker_lb, 6),
        }

    if not (0.0 < p_ref < 1.0):
        return {
            "certified": False,
            "reason": "p_ref must lie strictly in (0, 1) for non-degenerate certification.",
            "kl_kind": kl_kind,
            "kl_value": kl_value,
            "p_ref": p_ref,
            "cost_ref": cost_ref,
            "cost_quant": cost_quant,
            "p_crit": round(p_crit, 6),
            "kl_threshold_binary_kl": round(kl_threshold, 6),
            "pinsker_p_quant_lower": round(pinsker_lb, 6),
        }

    certified = math.isfinite(kl_value) and kl_value < kl_threshold
    return {
        "certified": certified,
        "reason": (
            "Certified: KL(P_R || P_Q) < binary_KL(p_R || p_crit) implies p_Q > p_crit and Lambda_Q > Lambda_R."
            if certified
            else "Not certified: KL upper bound meets or exceeds binary_KL(p_R || p_crit)."
        ),
        "kl_kind": kl_kind,
        "kl_value": kl_value,
        "p_ref": p_ref,
        "cost_ref": cost_ref,
        "cost_quant": cost_quant,
        "p_crit": round(p_crit, 6),
        "kl_threshold_binary_kl": round(kl_threshold, 6),
        "margin_nats": round(kl_threshold - kl_value, 6),
        "pinsker_p_quant_lower": round(pinsker_lb, 6),
        "pinsker_also_exceeds_p_crit": pinsker_lb > p_crit,
    }


def policy_stability_certificate(epsilon_tv: float, horizon_steps: int) -> dict[str, Any]:
    """URT stability bounds for a research policy under uniform TV transition error (Section 10).

    Conditional on TV(P_a(.|s), P_hat_a(.|s)) <= epsilon_tv uniformly across all reachable
    states and actions over at most N steps:
        - Fixed-policy evaluation error: |V_N - V_hat_N| <= 1 - (1 - epsilon)^N
        - Linear optimal-policy gap:     V*_N - V^{pi_hat}_N <= min(1, 2 * N * epsilon)
        - Tighter coupling gap:          V*_N - V^{pi_hat}_N <= min(1, 2 * [1 - (1 - epsilon)^N])
    """
    if not (0.0 <= epsilon_tv <= 1.0):
        raise ValueError(f"epsilon_tv must lie in [0, 1]: {epsilon_tv}")
    if horizon_steps < 0:
        raise ValueError(f"horizon_steps must be non-negative: {horizon_steps}")

    fixed_policy_err = 1.0 - math.pow(1.0 - epsilon_tv, horizon_steps)
    linear_gap = min(1.0, 2.0 * horizon_steps * epsilon_tv)
    coupling_gap = min(1.0, 2.0 * fixed_policy_err)
    return {
        "epsilon_tv": epsilon_tv,
        "horizon_steps": horizon_steps,
        "fixed_policy_value_error_bound": round(fixed_policy_err, 8),
        "linear_optimality_gap_bound": round(linear_gap, 8),
        "coupling_optimality_gap_bound": round(coupling_gap, 8),
        "coupling_tighter_or_equal": coupling_gap <= linear_gap + 1e-12,
        "conditional_on_uniform_tv_bound": True,
        "caveat": (
            "Conditional theorem requiring a proven uniform TV error bound <= epsilon_tv "
            "across all target states and actions. Finite calibration sets do not guarantee "
            "uniform coverage on unseen research states."
        ),
    }
