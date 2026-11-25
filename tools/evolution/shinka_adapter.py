"""Multi-island evolutionary inference optimiser and official ShinkaEvolve boundary adapter.

Strictly distinguishes:
- `engine_kind = "shinka_inspired_builtin"`: self-contained multi-island Pareto +
  non-stationary bandit + multi-fidelity CPU trace/Roofline optimiser with strict
  train-vs-holdout separation and equal-budget uniform-random comparison.
- `inspect_official_shinka_environment()`: checks actual installed SakanaAI/ShinkaEvolve
  and robust-kbench package versions without pretending custom search is an official run.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.metadata
import json
import logging
import random
import shutil
import time
from typing import Any, Sequence

from pws.trace import RoutingEvent

from .archive import CandidateRecord, ParetoArchive, select_parent_fitness_proportionate
from .bandit import make_bandit
from .genome import InferenceGenome
from .multi_fidelity import (
    FidelityContext,
    evaluate_candidate_multifidelity,
    successive_halving_with_random_audit,
)
from .mutation import MUTATION_OPERATORS, apply_mutation

LOGGER = logging.getLogger("strata.evolution.shinka_adapter")


def inspect_official_shinka_environment() -> dict[str, Any]:
    """Report actual installed versions of Sakana AI packages and local verification tools."""
    pkgs: dict[str, str | None] = {}
    for name in ("shinka", "shinka-evolve", "robust-kbench"):
        try:
            pkgs[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pkgs[name] = None
    bins = {
        exe: shutil.which(exe)
        for exe in ("shinka_run", "compute-sanitizer", "nvcc", "lean")
    }
    return {
        "packages": pkgs,
        "binaries": {k: (v is not None) for k, v in bins.items()},
        "official_shinka_cli_available": bins["shinka_run"] is not None,
        "official_robust_kbench_available": pkgs["robust-kbench"] is not None,
    }


def _workload_hash(events: Sequence[RoutingEvent]) -> str:
    h = hashlib.sha256()
    for ev in events[:256]:
        h.update(f"{ev.token_idx}:{ev.layer}:{ev.expert}:{ev.weight_bytes};".encode("ascii"))
    h.update(f"|len={len(events)}".encode("ascii"))
    return h.hexdigest()[:16]


@dataclass(frozen=True)
class EvolutionRunConfig:
    """Configuration for a bounded multi-island evolutionary search run."""

    generations: int = 16
    num_islands: int = 2
    migration_interval: int = 6
    bandit_name: str = "sliding_window_ucb"
    seed: int = 42
    max_gpu_budget_bytes: int = 64 * 1024 * 1024
    max_ram_budget_bytes: int = 64 * 1024 * 1024
    min_novelty_distance: float = 0.025


def run_evolutionary_search(
    *,
    train_trace: Sequence[RoutingEvent],
    holdout_trace: Sequence[RoutingEvent],
    baseline_genome: InferenceGenome,
    run_cfg: EvolutionRunConfig,
    ctx: FidelityContext,
) -> dict[str, Any]:
    """Execute bounded multi-island Pareto evolutionary search on `train_trace` and verify on `holdout_trace`."""
    if not train_trace or not holdout_trace:
        raise ValueError("Both train_trace and holdout_trace must be non-empty")

    t_start = time.perf_counter()
    rng = random.Random(run_cfg.seed)
    train_hash = _workload_hash(train_trace)
    holdout_hash = _workload_hash(holdout_trace)

    archive = ParetoArchive(min_novelty_distance=run_cfg.min_novelty_distance)
    bandit = make_bandit(run_cfg.bandit_name, MUTATION_OPERATORS, seed=run_cfg.seed)

    # Evaluate baseline on both train (Level 2) and independent holdout (Level 2)
    base_train = evaluate_candidate_multifidelity(
        genome=baseline_genome,
        island_id=0,
        generation=0,
        operator_used="baseline",
        trace_events=train_trace,
        workload_hash=train_hash,
        ctx=ctx,
        archive=archive,
        target_fidelity=2,
    )
    archive.add(base_train)

    holdout_archive = ParetoArchive(min_novelty_distance=0.0)
    base_holdout = evaluate_candidate_multifidelity(
        genome=baseline_genome,
        island_id=0,
        generation=0,
        operator_used="baseline",
        trace_events=holdout_trace,
        workload_hash=holdout_hash,
        ctx=ctx,
        archive=holdout_archive,
        target_fidelity=2,
    )

    # Seed secondary islands with perturbed valid genomes
    num_islands = max(1, int(run_cfg.num_islands))
    for isl in range(1, num_islands):
        seed_g = apply_mutation(
            "global_explore",
            baseline_genome,
            mate=None,
            rng=rng,
            max_gpu_budget_bytes=run_cfg.max_gpu_budget_bytes,
            max_ram_budget_bytes=run_cfg.max_ram_budget_bytes,
        )
        seed_rec = evaluate_candidate_multifidelity(
            genome=seed_g,
            island_id=isl,
            generation=0,
            operator_used="island_seed",
            trace_events=train_trace,
            workload_hash=train_hash,
            ctx=ctx,
            archive=archive,
            target_fidelity=2,
        )
        archive.add(seed_rec)

    l1_evals = 0
    l2_evals = len(archive.records)
    random_audit_promotions = 0

    for gen in range(1, max(1, run_cfg.generations) + 1):
        gen_l1_batch: list[tuple[int, CandidateRecord]] = []
        for isl in range(num_islands):
            pool = archive.island_records(isl) or archive.records
            parent = select_parent_fitness_proportionate(pool, rng).genome
            mate = select_parent_fitness_proportionate(archive.records, rng).genome if len(archive.records) > 1 else None
            arm = bandit.select()
            op_name = MUTATION_OPERATORS[arm]
            child = apply_mutation(
                op_name,
                parent,
                mate=mate,
                rng=rng,
                max_gpu_budget_bytes=run_cfg.max_gpu_budget_bytes,
                max_ram_budget_bytes=run_cfg.max_ram_budget_bytes,
            )
            if archive.is_too_similar(child):
                archive.duplicate_skipped_count += 1
                bandit.update(arm, 0.0, eval_cost_s=0.001)
                continue

            # Level 0 + Level 1 fast screen
            rec_l1 = evaluate_candidate_multifidelity(
                genome=child,
                island_id=isl,
                generation=gen,
                operator_used=op_name,
                trace_events=train_trace,
                workload_hash=train_hash,
                ctx=ctx,
                archive=archive,
                target_fidelity=1,
            )
            l1_evals += 1
            if not rec_l1.verified:
                archive.rejected_count += 1
                bandit.update(arm, 0.0, eval_cost_s=rec_l1.eval_cost_s)
                continue
            gen_l1_batch.append((arm, rec_l1))

        # Successive halving + random proxy-audit promotion to Level 2
        if gen_l1_batch:
            arm_by_hash = {r.genome.candidate_hash(): a for a, r in gen_l1_batch}
            promoted = successive_halving_with_random_audit(
                [r for _, r in gen_l1_batch],
                keep_top_fraction=0.6,
                random_audit_fraction=0.2,
                rng=rng,
            )
            best_before = max(r.estimated_tok_s for r in archive.records if r.verified)
            for rec_l1, is_rand_audit in promoted:
                if is_rand_audit:
                    random_audit_promotions += 1
                rec_l2 = evaluate_candidate_multifidelity(
                    genome=rec_l1.genome,
                    island_id=rec_l1.island_id,
                    generation=gen,
                    operator_used=rec_l1.operator_used,
                    trace_events=train_trace,
                    workload_hash=train_hash,
                    ctx=ctx,
                    archive=archive,
                    target_fidelity=2,
                    promoted_by_random_audit=is_rand_audit,
                )
                l2_evals += 1
                archive.add(rec_l2)
                rel_gain = max(0.0, (rec_l2.estimated_tok_s - best_before) / max(1e-6, best_before))
                arm = arm_by_hash[rec_l1.genome.candidate_hash()]
                bandit.update(arm, rel_gain, eval_cost_s=rec_l2.eval_cost_s)

        # Periodic ring migration between islands
        if num_islands > 1 and gen % max(1, run_cfg.migration_interval) == 0:
            for src in range(num_islands):
                src_recs = archive.island_records(src)
                if not src_recs:
                    continue
                best_src = max(src_recs, key=lambda r: r.estimated_tok_s)
                dst = (src + 1) % num_islands
                migrated = CandidateRecord(
                    genome=best_src.genome,
                    island_id=dst,
                    generation=gen,
                    fidelity_level=best_src.fidelity_level,
                    verified=True,
                    byte_hit_rate=best_src.byte_hit_rate,
                    exposed_io_stall_ms_per_tok=best_src.exposed_io_stall_ms_per_tok,
                    physical_ssd_bytes_per_tok=best_src.physical_ssd_bytes_per_tok,
                    estimated_tok_s=best_src.estimated_tok_s,
                    memory_bytes=best_src.memory_bytes,
                    eval_cost_s=0.0,
                    operator_used="island_migration",
                )
                archive.records.append(migrated)

    # Evaluate Pareto frontier on the independent holdout trace (never used during search!)
    frontier = archive.pareto_frontier()
    holdout_results: list[dict[str, Any]] = []
    for cand in frontier:
        h_rec = evaluate_candidate_multifidelity(
            genome=cand.genome,
            island_id=cand.island_id,
            generation=cand.generation,
            operator_used=cand.operator_used,
            trace_events=holdout_trace,
            workload_hash=holdout_hash,
            ctx=ctx,
            archive=holdout_archive,
            target_fidelity=2,
        )
        holdout_results.append(
            {
                "candidate_hash": cand.genome.candidate_hash(),
                "cache_policy": cand.genome.cache_policy,
                "train_estimated_tok_s": round(cand.estimated_tok_s, 4),
                "holdout_estimated_tok_s": round(h_rec.estimated_tok_s, 4),
                "holdout_byte_hit_rate": round(h_rec.byte_hit_rate, 6),
                "holdout_exposed_stall_ms_per_tok": round(h_rec.exposed_io_stall_ms_per_tok, 4),
                "holdout_physical_ssd_bytes_per_tok": round(h_rec.physical_ssd_bytes_per_tok, 2),
                "holdout_gain_vs_baseline_pct": round(
                    100.0 * (h_rec.estimated_tok_s / max(1e-9, base_holdout.estimated_tok_s) - 1.0),
                    4,
                ),
            }
        )

    best_holdout = max(holdout_results, key=lambda x: x["holdout_estimated_tok_s"]) if holdout_results else None
    wall_s = time.perf_counter() - t_start

    return {
        "engine_kind": "shinka_inspired_builtin",
        "note": (
            "Self-contained ShinkaEvolve-inspired multi-island Pareto search on CPU trace/Roofline "
            "replay; explicitly distinct from official SakanaAI/ShinkaEvolve LLM mutation runs and "
            "from real RTX 5060 Ti hardware throughput measurements."
        ),
        "bandit_summary": bandit.summary(),
        "search_wall_seconds": round(wall_s, 4),
        "generations": run_cfg.generations,
        "num_islands": num_islands,
        "l1_evaluations": l1_evals,
        "l2_evaluations": l2_evals,
        "rejected_candidates": archive.rejected_count,
        "duplicate_skipped": archive.duplicate_skipped_count,
        "random_audit_promotions": random_audit_promotions,
        "baseline_train": base_train.to_dict(),
        "baseline_holdout": base_holdout.to_dict(),
        "pareto_frontier_size": len(frontier),
        "pareto_frontier_holdout": holdout_results,
        "best_holdout_candidate": best_holdout,
        "auto_adopted_into_default_inference": False,
    }
