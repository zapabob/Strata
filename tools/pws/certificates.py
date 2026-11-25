"""PWS + TSI joint certification separating lossless cache placement from lossy weight approximation.

Implements Section 15 of the PWS specification:
- Lossless cache/prefetch/layout changes preserve exact model outputs (bit-exact parity),
  so any reduction in total trial cost c_new < c_ref strictly increases Lambda = -ln(1-p)/c.
- Lossy weight factorisation/quantisation changes the model distribution and must satisfy
  the TSI adoption criterion p_new > 1 - (1 - p_ref)^(c_new / c_ref) using end-to-end
  trial costs (including verification, retries, and SSD stalls).
"""

from __future__ import annotations

from typing import Any, Literal

from tsi.discovery_rate import compare_quantised_discovery_rate

OptimisationKind = Literal["lossless_cache_placement", "lossy_weight_approximation"]


def certify_pws_tsi_efficiency(
    *,
    optimisation_kind: OptimisationKind,
    p_ref: float,
    cost_ref_s: float,
    p_new: float,
    cost_new_s: float,
    bit_exact_parity_verified: bool | None = None,
) -> dict[str, Any]:
    """Evaluate Section 15 joint PWS + TSI scientific discovery-rate improvement."""
    if optimisation_kind not in ("lossless_cache_placement", "lossy_weight_approximation"):
        raise ValueError(f"Unsupported optimisation_kind: {optimisation_kind!r}")

    cmp = compare_quantised_discovery_rate(
        p_ref=p_ref,
        cost_ref=cost_ref_s,
        p_quant=p_new,
        cost_quant=cost_new_s,
    )
    if optimisation_kind == "lossless_cache_placement":
        parity_ok = bool(bit_exact_parity_verified)
        improved = parity_ok and (cost_new_s < cost_ref_s) and (p_new + 1e-12 >= p_ref)
        status = (
            "lossless_efficiency_improved"
            if improved
            else ("parity_unverified" if not parity_ok else "no_net_cost_reduction")
        )
    else:
        improved = bool(cmp["asymptotic_quant_exceeds_ref"])
        status = (
            "lossy_discovery_rate_improved_model"
            if improved
            else "lossy_below_critical_threshold"
        )

    return {
        "optimisation_kind": optimisation_kind,
        "bit_exact_parity_verified": bit_exact_parity_verified,
        "status": status,
        "improved": improved,
        "discovery_rate_comparison": cmp,
    }
