"""SSD bandwidth limits, MoE active-weight hit-rate requirements, and physical byte accounting.

Implements Sections 4, 5, and 16 of the PWS specification:
- Dense full-weight streaming upper bound: W = N * b / 8, decode_rate <= B_ssd / W
- MoE active-weight bound: W_ssd = (1 - h) * W_a, h >= max(0, 1 - B_ssd / (v * W_a))
- Physical SSD bytes breakdown: demand_reads + unused_prefetch + alignment_overhead +
  read_amplification + repeated_reads (distinguishing OS page-cache hits from physical I/O).
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Sequence


@dataclass(frozen=True)
class ActualSsdBytesBreakdown:
    """Physical SSD read accounting per window or per token (Section 5 & Section 16)."""

    demand_reads_bytes: int
    unused_prefetch_bytes: int = 0
    alignment_overhead_bytes: int = 0
    read_amplification_bytes: int = 0
    repeated_reads_bytes: int = 0
    os_page_cache_bytes: int | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "demand_reads_bytes",
            "unused_prefetch_bytes",
            "alignment_overhead_bytes",
            "read_amplification_bytes",
            "repeated_reads_bytes",
        ):
            if int(getattr(self, field_name)) < 0:
                raise ValueError(f"{field_name} must be non-negative")

    @property
    def logical_demand_bytes(self) -> int:
        return self.demand_reads_bytes

    @property
    def physical_total_bytes(self) -> int:
        return (
            self.demand_reads_bytes
            + self.unused_prefetch_bytes
            + self.alignment_overhead_bytes
            + self.read_amplification_bytes
            + self.repeated_reads_bytes
        )

    @property
    def read_amplification_factor(self) -> float | None:
        if self.demand_reads_bytes == 0:
            return None if self.physical_total_bytes == 0 else float("inf")
        return self.physical_total_bytes / self.demand_reads_bytes

    def to_dict(self) -> dict[str, Any]:
        raf = self.read_amplification_factor
        return {
            "demand_reads_bytes": self.demand_reads_bytes,
            "unused_prefetch_bytes": self.unused_prefetch_bytes,
            "alignment_overhead_bytes": self.alignment_overhead_bytes,
            "read_amplification_bytes": self.read_amplification_bytes,
            "repeated_reads_bytes": self.repeated_reads_bytes,
            "logical_demand_bytes": self.logical_demand_bytes,
            "physical_total_bytes": self.physical_total_bytes,
            "os_page_cache_bytes": self.os_page_cache_bytes,
            "read_amplification_factor": (
                round(raf, 6) if (raf is not None and math.isfinite(raf)) else None
            ),
        }


def dense_full_weight_streaming_bound(
    *,
    num_params: float,
    effective_bpw: float,
    ssd_bandwidths_gb_s: Sequence[float],
) -> dict[str, Any]:
    """Section 4: Idealised upper bound when streaming all weights of a dense model every token.

    Uses SI GB (10^9 bytes) to match storage bandwidth specs (e.g. 27e9 * 3.69 / 8 = 12.45375 GB).
    """
    if num_params <= 0.0 or effective_bpw <= 0.0:
        raise ValueError("num_params and effective_bpw must be positive")
    weight_bytes = num_params * effective_bpw / 8.0
    weight_gb = weight_bytes / 1e9
    rows: list[dict[str, float]] = []
    for bw in ssd_bandwidths_gb_s:
        if bw <= 0.0:
            raise ValueError(f"Bandwidth must be positive: {bw}")
        rows.append(
            {
                "effective_ssd_bandwidth_gb_s": float(bw),
                "max_decode_tok_s": round(bw / weight_gb, 6),
            }
        )
    return {
        "model_class": "dense_full_weight_streaming_ideal_bound",
        "num_params": num_params,
        "effective_bpw": effective_bpw,
        "weight_bytes": int(round(weight_bytes)),
        "weight_gb_decimal": round(weight_gb, 6),
        "ceilings": rows,
        "caveat": "Theoretical bandwidth ceiling only; not a measured Strata runtime speed.",
    }


def moe_cache_hit_requirement(
    *,
    active_params: float,
    effective_bpw: float,
    ssd_bandwidth_gb_s: float,
    target_decode_tok_s: float,
    probe_hit_rates: Sequence[float] = (0.90,),
) -> dict[str, Any]:
    """Section 5: Active-weight MoE SSD demand and required byte-weighted cache hit rate.

        W_a = active_params * effective_bpw / 8
        h_req = max(0, 1 - B_ssd / (v * W_a))
    """
    if active_params <= 0.0 or effective_bpw <= 0.0:
        raise ValueError("active_params and effective_bpw must be positive")
    if ssd_bandwidth_gb_s <= 0.0 or target_decode_tok_s <= 0.0:
        raise ValueError("ssd_bandwidth_gb_s and target_decode_tok_s must be positive")

    active_bytes = active_params * effective_bpw / 8.0
    active_mb = active_bytes / 1e6
    ssd_bw_mb_s = ssd_bandwidth_gb_s * 1e3
    allowable_ssd_mb_per_tok = ssd_bw_mb_s / target_decode_tok_s
    required_hit_rate = max(0.0, 1.0 - ssd_bw_mb_s / (target_decode_tok_s * active_mb))

    probes: list[dict[str, Any]] = []
    for h in probe_hit_rates:
        if not (0.0 <= h <= 1.0):
            raise ValueError(f"Hit rate must lie in [0, 1]: {h}")
        w_ssd_mb = (1.0 - h) * active_mb
        ceiling = (ssd_bw_mb_s / w_ssd_mb) if w_ssd_mb > 0.0 else float("inf")
        probes.append(
            {
                "byte_hit_rate": float(h),
                "ideal_ssd_demand_mb_per_token": round(w_ssd_mb, 6),
                "ssd_bandwidth_only_ceiling_tok_s": round(ceiling, 6) if math.isfinite(ceiling) else "inf",
            }
        )

    return {
        "model_class": "moe_active_weight_streaming_ideal_bound",
        "active_params": active_params,
        "effective_bpw": effective_bpw,
        "active_weight_mb": round(active_mb, 6),
        "effective_ssd_bandwidth_gb_s": ssd_bandwidth_gb_s,
        "target_decode_tok_s": target_decode_tok_s,
        "allowable_ssd_mb_per_token": round(allowable_ssd_mb_per_tok, 6),
        "required_byte_hit_rate": round(required_hit_rate, 6),
        "probes": probes,
        "caveat": (
            "Idealised demand-only ceiling excluding unused prefetch, alignment padding, "
            "read amplification, CPU compute, and PCIe/VRAM bottlenecks."
        ),
    }
