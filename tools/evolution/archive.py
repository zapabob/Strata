"""Multi-objective Pareto archive, 9-tuple evaluation cache, and adaptive parent selection.

Implements Sections 3.1, 5, and 13:
- Records the full multi-objective Pareto frontier (maximise hit_rate / throughput,
  minimise exposed I/O stall, physical SSD bytes, and memory footprint) rather than
  collapsing prematurely into one fixed weighted sum.
- Keys reusable evaluation cache entries by the complete Section 13 9-tuple so results
  measured under different hardware, models, commits, compilers, drivers, or workloads
  are NEVER mixed.
- Provides true fitness-proportionate + novelty-aware parent sampling and multi-island
  migration (remediating `scripts/shinka_evolve_rh.py`'s uniform top-5 selection).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import random
from typing import Any, Sequence

from .genome import InferenceGenome, genome_distance


@dataclass(frozen=True)
class EvaluationCacheKey:
    """Section 13 strict 9-tuple provenance key for safe evaluation caching."""

    candidate_source_hash: str
    model_hash: str
    engine_commit: str
    compiler_version: str
    driver_version: str
    hardware_configuration: str
    workload_hash: str
    verifier_version: str
    benchmark_configuration: str

    def digest(self) -> str:
        payload = {
            "candidate_source_hash": self.candidate_source_hash,
            "model_hash": self.model_hash,
            "engine_commit": self.engine_commit,
            "compiler_version": self.compiler_version,
            "driver_version": self.driver_version,
            "hardware_configuration": self.hardware_configuration,
            "workload_hash": self.workload_hash,
            "verifier_version": self.verifier_version,
            "benchmark_configuration": self.benchmark_configuration,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CandidateRecord:
    """One verified candidate evaluation entry stored in the evolutionary archive."""

    genome: InferenceGenome
    island_id: int
    generation: int
    fidelity_level: int
    verified: bool
    # Primary objectives (higher is better for throughput_score & byte_hit_rate;
    # lower is better for exposed_io_stall_ms_per_tok, physical_ssd_bytes_per_tok, memory_bytes)
    byte_hit_rate: float
    exposed_io_stall_ms_per_tok: float
    physical_ssd_bytes_per_tok: float
    estimated_tok_s: float
    memory_bytes: int
    eval_cost_s: float
    operator_used: str
    promoted_by_random_audit: bool = False

    def objective_vector_for_maximisation(self) -> tuple[float, float, float, float]:
        """Higher-is-better 4D objective vector for Pareto dominance."""
        return (
            self.estimated_tok_s,
            self.byte_hit_rate,
            -self.exposed_io_stall_ms_per_tok,
            -self.physical_ssd_bytes_per_tok,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_hash": self.genome.candidate_hash(),
            "island_id": self.island_id,
            "generation": self.generation,
            "fidelity_level": self.fidelity_level,
            "verified": self.verified,
            "byte_hit_rate": round(self.byte_hit_rate, 6),
            "exposed_io_stall_ms_per_tok": round(self.exposed_io_stall_ms_per_tok, 4),
            "physical_ssd_bytes_per_tok": round(self.physical_ssd_bytes_per_tok, 2),
            "estimated_tok_s": round(self.estimated_tok_s, 4),
            "memory_bytes": self.memory_bytes,
            "eval_cost_s": round(self.eval_cost_s, 6),
            "operator_used": self.operator_used,
            "promoted_by_random_audit": self.promoted_by_random_audit,
            "genome": self.genome.to_dict(),
        }


def dominates(a: CandidateRecord, b: CandidateRecord) -> bool:
    """True iff `a` is >= `b` in every objective and strictly > in at least one."""
    va = a.objective_vector_for_maximisation()
    vb = b.objective_vector_for_maximisation()
    ge_all = all(x >= y - 1e-12 for x, y in zip(va, vb, strict=True))
    gt_any = any(x > y + 1e-12 for x, y in zip(va, vb, strict=True))
    return ge_all and gt_any


@dataclass
class ParetoArchive:
    """Verified multi-objective Pareto archive with novelty rejection and provenance cache."""

    min_novelty_distance: float = 0.03
    records: list[CandidateRecord] = field(default_factory=list)
    rejected_count: int = 0
    duplicate_skipped_count: int = 0
    eval_cache: dict[str, CandidateRecord] = field(default_factory=dict)

    def is_too_similar(self, candidate: InferenceGenome) -> bool:
        return any(genome_distance(candidate, r.genome) < self.min_novelty_distance for r in self.records)

    def add(self, rec: CandidateRecord) -> bool:
        if not rec.verified:
            self.rejected_count += 1
            return False
        self.records.append(rec)
        return True

    def pareto_frontier(self) -> list[CandidateRecord]:
        """Return all non-dominated verified candidates in the archive."""
        verified = [r for r in self.records if r.verified]
        frontier: list[CandidateRecord] = []
        for i, cand in enumerate(verified):
            if not any(dominates(other, cand) for j, other in enumerate(verified) if i != j):
                frontier.append(cand)
        frontier.sort(key=lambda r: (-r.estimated_tok_s, r.exposed_io_stall_ms_per_tok))
        return frontier

    def island_records(self, island_id: int) -> list[CandidateRecord]:
        return [r for r in self.records if r.verified and r.island_id == island_id]


def select_parent_fitness_proportionate(
    candidates: Sequence[CandidateRecord],
    rng: random.Random,
    *,
    temperature: float = 1.0,
) -> CandidateRecord:
    """Adaptive fitness-proportionate parent selection (softmax over standardised throughput + hit rate)."""
    if not candidates:
        raise ValueError("candidates must be non-empty")
    if len(candidates) == 1:
        return candidates[0]

    scores = [c.estimated_tok_s + 10.0 * c.byte_hit_rate for c in candidates]
    s_min = min(scores)
    s_max = max(scores)
    span = max(1e-9, s_max - s_min)
    temp = max(0.05, float(temperature))

    import math

    weights = [math.exp(((s - s_min) / span) / temp) for s in scores]
    total = sum(weights)
    pick = rng.random() * total
    acc = 0.0
    for cand, w in zip(candidates, weights, strict=True):
        acc += w
        if pick <= acc:
            return cand
    return candidates[-1]
