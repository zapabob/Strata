"""Multi-fidelity candidate evaluation pipeline with random proxy-audit promotion (Section 13).

Implements Levels 0-2 directly on CPU without touching the GPU, and defines strict
boundaries for Levels 3-6 (hardware execution):
- Level 0: Immutable static invariant & safety-floor verification (`invariant_verifier`)
- Level 1: Fast CPU-only cache policy replay (`tools/pws/cache_policy.py`)
- Level 2: Deadline-aware EDF prefetch + multi-tier Roofline DAG cost (`tools/pws/`)
- Successive halving promotion PLUS configurable random promotion fraction to audit
  whether proxy evaluators misrank higher-fidelity winners.
"""

from __future__ import annotations

from dataclasses import dataclass
import random
import time
from typing import Any, Sequence

from pws.cache_policy import PolicyName, simulate_cache_policy
from pws.deadline_scheduler import IoTimingModel, PrefetchSchedulerConfig, simulate_deadline_prefetch
from pws.roofline import MultiTierRooflineInput, evaluate_multitier_roofline
from pws.trace import RoutingEvent

from .archive import CandidateRecord, EvaluationCacheKey, ParetoArchive
from .genome import InferenceGenome
from .invariant_verifier import ResourceGuardLimits, verify_genome_invariants


@dataclass(frozen=True)
class FidelityContext:
    """Immutable hardware/workload environment attached to an evolutionary evaluation."""

    ssd_bandwidth_bytes_per_s: float = 500e6
    pcie_bandwidth_bytes_per_s: float = 12e9
    vram_bandwidth_bytes_per_s: float = 448e9
    ram_bandwidth_bytes_per_s: float = 40e9
    gpu_flops_per_s: float = 24e12
    flops_per_token: float = 6e9
    model_hash: str = "synthetic-trace-v1"
    engine_commit: str = "unknown"
    compiler_version: str = "python-cpu-replay"
    driver_version: str = "cpu-only"
    hardware_configuration: str = "cpu-replay"
    verifier_version: str = "eio-verifier-1.0"
    limits: ResourceGuardLimits = ResourceGuardLimits()


def evaluate_candidate_multifidelity(
    *,
    genome: InferenceGenome,
    island_id: int,
    generation: int,
    operator_used: str,
    trace_events: Sequence[RoutingEvent],
    workload_hash: str,
    ctx: FidelityContext,
    archive: ParetoArchive,
    target_fidelity: int = 2,
    promoted_by_random_audit: bool = False,
) -> CandidateRecord:
    """Evaluate a genome through Levels 0..target_fidelity with strict 9-tuple provenance caching."""
    cache_key = EvaluationCacheKey(
        candidate_source_hash=genome.candidate_hash(),
        model_hash=ctx.model_hash,
        engine_commit=ctx.engine_commit,
        compiler_version=ctx.compiler_version,
        driver_version=ctx.driver_version,
        hardware_configuration=ctx.hardware_configuration,
        workload_hash=workload_hash,
        verifier_version=ctx.verifier_version,
        benchmark_configuration=f"fidelity={target_fidelity}",
    ).digest()
    if cache_key in archive.eval_cache:
        return archive.eval_cache[cache_key]

    t0 = time.perf_counter()
    # Level 0: Immutable static invariant & resource-safety gate
    inv = verify_genome_invariants(genome, limits=ctx.limits)
    if not inv.passed:
        rec = CandidateRecord(
            genome=genome,
            island_id=island_id,
            generation=generation,
            fidelity_level=0,
            verified=False,
            byte_hit_rate=0.0,
            exposed_io_stall_ms_per_tok=float("inf"),
            physical_ssd_bytes_per_tok=float("inf"),
            estimated_tok_s=0.0,
            memory_bytes=genome.gpu_cache_budget_bytes + genome.ram_cache_budget_bytes,
            eval_cost_s=time.perf_counter() - t0,
            operator_used=operator_used,
            promoted_by_random_audit=promoted_by_random_audit,
        )
        archive.eval_cache[cache_key] = rec
        return rec

    # Level 1: Fast CPU-only cache policy replay over combined GPU + RAM cache budget
    total_cache_bytes = genome.gpu_cache_budget_bytes + genome.ram_cache_budget_bytes
    pol_name: PolicyName = genome.cache_policy  # type: ignore[assignment]
    l1 = simulate_cache_policy(
        trace_events,
        memory_budget_bytes=total_cache_bytes,
        policy=pol_name,
        lfu_decay=genome.cache_decay,
    )
    hit_rate = float(l1["byte_weighted_hit_rate"])
    num_tokens = max(1, len({e.token_idx for e in trace_events}))
    l1_phys_bytes_per_tok = float(l1["physical_miss_bytes"]) / num_tokens

    if target_fidelity <= 1:
        est_stall_ms = (l1_phys_bytes_per_tok / ctx.ssd_bandwidth_bytes_per_s) * 1000.0
        est_tok_s = 1000.0 / max(1.0, 10.0 + est_stall_ms)
        rec = CandidateRecord(
            genome=genome,
            island_id=island_id,
            generation=generation,
            fidelity_level=1,
            verified=True,
            byte_hit_rate=hit_rate,
            exposed_io_stall_ms_per_tok=est_stall_ms,
            physical_ssd_bytes_per_tok=l1_phys_bytes_per_tok,
            estimated_tok_s=est_tok_s,
            memory_bytes=total_cache_bytes,
            eval_cost_s=time.perf_counter() - t0,
            operator_used=operator_used,
            promoted_by_random_audit=promoted_by_random_audit,
        )
        archive.eval_cache[cache_key] = rec
        return rec

    # Level 2: Deadline-aware EDF prefetch + multi-tier Roofline DAG critical path
    io_model = IoTimingModel(
        ssd_bandwidth_bytes_per_s=ctx.ssd_bandwidth_bytes_per_s,
        pcie_bandwidth_bytes_per_s=ctx.pcie_bandwidth_bytes_per_s,
        alignment_bytes=min(genome.io_chunk_bytes, 65536),
    )
    edf = simulate_deadline_prefetch(
        trace_events,
        cache_budget_bytes=total_cache_bytes,
        io_model=io_model,
        config=PrefetchSchedulerConfig(
            enable_prefetch=genome.prefetch_depth > 0,
            max_prefetch_queue=genome.prefetch_queue_size,
            staging_buffers=genome.staging_buffers,
            layer_lookahead=genome.prefetch_depth,
            min_confidence=genome.prefetch_threshold,
            adaptive_throttle=True,
        ),
    )
    phys_b_tok = float(edf["ssd_physical_bytes_per_token"])
    stall_ms_tok = float(edf["exposed_io_stall_ms_per_token"])

    total_logical_per_tok = sum(e.weight_bytes for e in trace_events) / num_tokens
    vram_share = genome.gpu_cache_budget_bytes / max(1.0, float(total_cache_bytes))
    vram_b_tok = total_logical_per_tok * hit_rate * vram_share
    ram_b_tok = total_logical_per_tok * hit_rate * (1.0 - vram_share) + phys_b_tok
    pcie_b_tok = phys_b_tok

    roof = evaluate_multitier_roofline(
        MultiTierRooflineInput(
            flops_per_token=ctx.flops_per_token,
            vram_bytes_per_token=vram_b_tok,
            ram_bytes_per_token=ram_b_tok,
            pcie_bytes_per_token=pcie_b_tok,
            ssd_bytes_per_token=phys_b_tok,
            gpu_flops_per_s=ctx.gpu_flops_per_s,
            vram_bw_bytes_per_s=ctx.vram_bandwidth_bytes_per_s,
            ram_bw_bytes_per_s=ctx.ram_bandwidth_bytes_per_s,
            pcie_bw_bytes_per_s=ctx.pcie_bandwidth_bytes_per_s,
            ssd_bw_bytes_per_s=ctx.ssd_bandwidth_bytes_per_s,
            cpu_compute_s_per_token=ram_b_tok / ctx.ram_bandwidth_bytes_per_s,
            attention_gdn_serial_s_per_token=0.004,
            sync_overhead_s_per_token=0.0005,
            exposed_io_stall_s_per_token=stall_ms_tok / 1000.0,
        )
    )
    dag_tok_s = float(roof["dag_estimated_tok_s"]) if isinstance(roof["dag_estimated_tok_s"], (int, float)) else 0.0

    rec = CandidateRecord(
        genome=genome,
        island_id=island_id,
        generation=generation,
        fidelity_level=2,
        verified=True,
        byte_hit_rate=hit_rate,
        exposed_io_stall_ms_per_tok=stall_ms_tok,
        physical_ssd_bytes_per_tok=phys_b_tok,
        estimated_tok_s=dag_tok_s,
        memory_bytes=total_cache_bytes,
        eval_cost_s=time.perf_counter() - t0,
        operator_used=operator_used,
        promoted_by_random_audit=promoted_by_random_audit,
    )
    archive.eval_cache[cache_key] = rec
    return rec


def successive_halving_with_random_audit(
    candidates: Sequence[CandidateRecord],
    *,
    keep_top_fraction: float = 0.5,
    random_audit_fraction: float = 0.15,
    rng: random.Random,
) -> list[tuple[CandidateRecord, bool]]:
    """Promote top proxy candidates PLUS a random exploration fraction to detect proxy misranking."""
    verified = [c for c in candidates if c.verified]
    if not verified:
        return []
    ranked = sorted(verified, key=lambda r: (-r.estimated_tok_s, r.exposed_io_stall_ms_per_tok))
    k_top = max(1, int(round(len(ranked) * keep_top_fraction)))
    top_slice = ranked[:k_top]
    rest = ranked[k_top:]
    out: list[tuple[CandidateRecord, bool]] = [(c, False) for c in top_slice]
    if rest and random_audit_fraction > 0.0:
        k_rand = max(1, int(round(len(rest) * random_audit_fraction)))
        for c in rng.sample(rest, k=min(k_rand, len(rest))):
            out.append((c, True))
    return out
