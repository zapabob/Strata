"""Evolvable inference genome and non-commutative operator sequences (Sections 10 & 11).

Only includes parameters that correspond to real configurable knobs in Strata's
4-tier cache, prefetch, I/O, and reasoning layers — never unimplemented dummy knobs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Literal

OptimizationOp = Literal[
    "A1_cache_allocation",
    "A2_prefetch_policy",
    "A3_cpu_gpu_placement",
    "A4_quantisation",
    "A5_cuda_kernel",
    "A6_shared_basis",
    "A7_reasoning_policy",
]

DEFAULT_OPERATOR_SEQUENCE: tuple[OptimizationOp, ...] = (
    "A1_cache_allocation",
    "A2_prefetch_policy",
    "A3_cpu_gpu_placement",
    "A4_quantisation",
    "A5_cuda_kernel",
    "A6_shared_basis",
    "A7_reasoning_policy",
)

VALID_CACHE_POLICIES = ("lru", "lfu", "layer_aware", "markov", "nkat_seq", "tsi_task")


@dataclass(frozen=True)
class InferenceGenome:
    """Candidate inference configuration genome theta (Sections 5 & 10)."""

    gpu_cache_budget_bytes: int
    ram_cache_budget_bytes: int
    cache_decay: float
    eviction_hysteresis: float
    prefetch_depth: int
    prefetch_threshold: float
    prefetch_queue_size: int
    io_chunk_bytes: int
    staging_buffers: int
    cache_policy: str = "nkat_seq"
    operator_sequence: tuple[OptimizationOp, ...] = DEFAULT_OPERATOR_SEQUENCE

    def candidate_hash(self) -> str:
        raw = json.dumps(asdict(self), sort_keys=True, ensure_ascii=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:16]

    def normalised_vector(self) -> tuple[float, ...]:
        """Normalised feature vector for novelty distance filtering."""
        pol_idx = (
            VALID_CACHE_POLICIES.index(self.cache_policy) / max(1, len(VALID_CACHE_POLICIES) - 1)
            if self.cache_policy in VALID_CACHE_POLICIES
            else 0.0
        )
        return (
            self.gpu_cache_budget_bytes / (1024.0 * 1024.0 * 1024.0),
            self.ram_cache_budget_bytes / (1024.0 * 1024.0 * 1024.0),
            self.cache_decay,
            self.eviction_hysteresis,
            self.prefetch_depth / 8.0,
            self.prefetch_threshold,
            self.prefetch_queue_size / 16.0,
            math.log2(max(4096, self.io_chunk_bytes)) / 24.0,
            self.staging_buffers / 4.0,
            pol_idx,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "operator_sequence": list(self.operator_sequence),
            "candidate_hash": self.candidate_hash(),
        }


def genome_distance(a: InferenceGenome, b: InferenceGenome) -> float:
    """Euclidean distance on normalised continuous/discrete features plus order-mismatch term."""
    va = a.normalised_vector()
    vb = b.normalised_vector()
    sq = sum((x - y) ** 2 for x, y in zip(va, vb, strict=True))
    order_diff = sum(1 for x, y in zip(a.operator_sequence, b.operator_sequence, strict=True) if x != y)
    return math.sqrt(sq + 0.05 * order_diff)
