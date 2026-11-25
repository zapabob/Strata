"""Integrated multi-tier Roofline model and DAG critical-path estimator (Sections 6 & 18).

Computes both:
1. Idealised fully-overlapped Roofline upper bound:
       decode_rate <= min(P_gpu/F, B_vram/W_vram, B_ram/W_ram, B_pcie/W_pcie, B_ssd/W_ssd)
2. Realistic DAG critical-path estimate incorporating non-overlapped CPU expert execution,
   serial residual/attention/GDN chains, synchronisation overhead, and exposed I/O stall.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


@dataclass(frozen=True)
class MultiTierRooflineInput:
    """Per-token resource demands and effective sustained tier throughputs."""

    flops_per_token: float
    vram_bytes_per_token: float
    ram_bytes_per_token: float
    pcie_bytes_per_token: float
    ssd_bytes_per_token: float

    gpu_flops_per_s: float
    vram_bw_bytes_per_s: float
    ram_bw_bytes_per_s: float
    pcie_bw_bytes_per_s: float
    ssd_bw_bytes_per_s: float

    # Optional non-overlapped critical-path terms (seconds per token)
    cpu_compute_s_per_token: float = 0.0
    attention_gdn_serial_s_per_token: float = 0.0
    sync_overhead_s_per_token: float = 0.0
    exposed_io_stall_s_per_token: float = 0.0


def evaluate_multitier_roofline(inp: MultiTierRooflineInput) -> dict[str, Any]:
    """Compute ideal parallel Roofline ceiling, binding bottleneck, and DAG critical-path rate."""
    caps: dict[str, float] = {}

    def _rate(cap: float, demand: float, name: str) -> float:
        if cap <= 0.0:
            raise ValueError(f"Capacity for {name} must be positive: {cap}")
        if demand < 0.0:
            raise ValueError(f"Demand for {name} must be non-negative: {demand}")
        return float("inf") if demand == 0.0 else (cap / demand)

    caps["gpu_compute"] = _rate(inp.gpu_flops_per_s, inp.flops_per_token, "gpu_compute")
    caps["vram_bandwidth"] = _rate(inp.vram_bw_bytes_per_s, inp.vram_bytes_per_token, "vram_bandwidth")
    caps["ram_bandwidth"] = _rate(inp.ram_bw_bytes_per_s, inp.ram_bytes_per_token, "ram_bandwidth")
    caps["pcie_bandwidth"] = _rate(inp.pcie_bw_bytes_per_s, inp.pcie_bytes_per_token, "pcie_bandwidth")
    caps["ssd_bandwidth"] = _rate(inp.ssd_bw_bytes_per_s, inp.ssd_bytes_per_token, "ssd_bandwidth")

    bottleneck_name = min(caps, key=lambda k: caps[k])
    ideal_ceiling_tok_s = caps[bottleneck_name]
    ideal_ms_per_tok = (1000.0 / ideal_ceiling_tok_s) if (math.isfinite(ideal_ceiling_tok_s) and ideal_ceiling_tok_s > 0.0) else 0.0

    # Realistic serial/exposed critical-path time
    base_gpu_s = max(
        inp.flops_per_token / inp.gpu_flops_per_s,
        inp.vram_bytes_per_token / inp.vram_bw_bytes_per_s,
    )
    dag_critical_s = (
        base_gpu_s
        + inp.cpu_compute_s_per_token
        + inp.attention_gdn_serial_s_per_token
        + inp.sync_overhead_s_per_token
        + inp.exposed_io_stall_s_per_token
    )
    dag_rate_tok_s = (1.0 / dag_critical_s) if dag_critical_s > 0.0 else float("inf")

    return {
        "tier_ceilings_tok_s": {
            k: (round(v, 4) if math.isfinite(v) else "inf") for k, v in caps.items()
        },
        "binding_roofline_tier": bottleneck_name,
        "ideal_parallel_roofline_tok_s": (
            round(ideal_ceiling_tok_s, 4) if math.isfinite(ideal_ceiling_tok_s) else "inf"
        ),
        "ideal_parallel_ms_per_token": round(ideal_ms_per_tok, 4),
        "dag_critical_path_ms_per_token": round(dag_critical_s * 1000.0, 4),
        "dag_estimated_tok_s": (
            round(dag_rate_tok_s, 4) if math.isfinite(dag_rate_tok_s) else "inf"
        ),
        "exceeds_roofline_impossible": (
            dag_rate_tok_s <= ideal_ceiling_tok_s + 1e-9
            if math.isfinite(ideal_ceiling_tok_s) and math.isfinite(dag_rate_tok_s)
            else True
        ),
        "caveat": (
            "Roofline upper bound assumes complete overlap between compute and all memory tiers; "
            "actual throughput is constrained by the serial DAG critical path and shared bus contention."
        ),
    }
