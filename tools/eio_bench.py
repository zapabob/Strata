#!/usr/bin/env python3
"""CLI entrypoint for NKAT-URT Evolutionary Inference Optimisation (EIO, Phase 3 Revised).

Subcommands:
    inspect-deps     Inspect installed Sakana AI / CUDA / Lean dependencies honestly
    math-check       Verify EIO invariants, Pareto dominance, URT speedup LCB, and amortisation
    evolve           Run bounded multi-island Pareto evolutionary search with holdout check
    compare-bandits  Compare sliding_window_ucb, thompson_sampling, cost_aware_ucb, and
                     uniform_random at identical search budget
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys
from typing import Any, Sequence

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from evolution import EIO_SCHEMA_VERSION  # noqa: E402
from evolution.certificates import certify_paired_speedup, search_amortisation_breakeven  # noqa: E402
from evolution.genome import InferenceGenome  # noqa: E402
from evolution.hardware_evolve import (  # noqa: E402
    RealEngineGenome,
    run_real_hardware_evolution,
    run_single_native_trial,
)
from evolution.invariant_verifier import verify_genome_invariants, verify_hard_acceptance_gates  # noqa: E402
from evolution.multi_fidelity import FidelityContext  # noqa: E402
from evolution.shinka_adapter import (  # noqa: E402
    EvolutionRunConfig,
    inspect_official_shinka_environment,
    run_evolutionary_search,
)
from pws.trace import generate_structured_moe_trace, load_strata_routing_trace  # noqa: E402

LOGGER = logging.getLogger("strata.eio_bench")


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def run_eio_math_checks() -> dict[str, Any]:
    """Verify EIO hard constraints, paired speedup certification, and search amortisation."""
    valid_g = InferenceGenome(
        gpu_cache_budget_bytes=32 * 1024 * 1024,
        ram_cache_budget_bytes=32 * 1024 * 1024,
        cache_decay=0.95,
        eviction_hysteresis=0.5,
        prefetch_depth=2,
        prefetch_threshold=0.25,
        prefetch_queue_size=4,
        io_chunk_bytes=524288,
        staging_buffers=2,
    )
    bad_g = InferenceGenome(
        gpu_cache_budget_bytes=32 * 1024 * 1024,
        ram_cache_budget_bytes=32 * 1024 * 1024,
        cache_decay=0.95,
        eviction_hysteresis=0.5,
        prefetch_depth=2,
        prefetch_threshold=0.25,
        prefetch_queue_size=4,
        io_chunk_bytes=1000,  # unaligned -> MUST fail Level-0 invariant check!
        staging_buffers=2,
    )
    assert verify_genome_invariants(valid_g).passed
    assert not verify_genome_invariants(bad_g).passed

    gate_fail = verify_hard_acceptance_gates(
        numerical_correctness_pass=False,
        resource_guards_pass=True,
        model_integrity_pass=True,
        required_quality_pass=True,
        verifier_integrity_pass=True,
    )
    assert not gate_fail["accepted_for_archive"]

    cert_holdout = certify_paired_speedup(
        baseline_times_s=[1.00, 1.02, 0.99, 1.01, 1.03, 1.00, 1.01, 0.98],
        candidate_times_s=[0.78, 0.80, 0.79, 0.77, 0.81, 0.79, 0.78, 0.79],
        range_width_R=0.5,
        range_width_R_certified=True,
        is_independent_holdout=True,
    )
    assert cert_holdout["certified_speedup"]

    cert_not_holdout = certify_paired_speedup(
        baseline_times_s=[1.00, 1.02, 0.99, 1.01],
        candidate_times_s=[0.80, 0.81, 0.79, 0.80],
        is_independent_holdout=False,
    )
    assert not cert_not_holdout["certified_speedup"]

    amort = search_amortisation_breakeven(
        search_wall_s=120.0,
        build_and_verify_s=60.0,
        delta_t_saved_per_token_s=0.005,
        expected_deployment_tokens=100_000,
    )
    assert amort["break_even_tokens"] == 36000
    assert amort["cost_recovered_at_expected_usage"]

    return {
        "schema": EIO_SCHEMA_VERSION,
        "pass": True,
        "paired_speedup_holdout_cert": cert_holdout,
        "amortisation_example": amort,
    }


def _default_baseline(cache_mb: float) -> InferenceGenome:
    half = int((cache_mb * 1024 * 1024) // 2)
    return InferenceGenome(
        gpu_cache_budget_bytes=half,
        ram_cache_budget_bytes=half,
        cache_decay=0.95,
        eviction_hysteresis=0.5,
        prefetch_depth=0,
        prefetch_threshold=0.5,
        prefetch_queue_size=2,
        io_chunk_bytes=524288,
        staging_buffers=2,
        cache_policy="lru",
    )


def cmd_inspect_deps(_args: argparse.Namespace) -> int:
    info = inspect_official_shinka_environment()
    LOGGER.info("Sakana AI / CUDA / Lean dependency inventory:\n%s", json.dumps(info, indent=2))
    return 0


def cmd_math_check(args: argparse.Namespace) -> int:
    res = run_eio_math_checks()
    txt = json.dumps(res, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(txt + "\n", encoding="utf-8")
    LOGGER.info("EIO mathematical & invariant self-checks PASSED:\n%s", txt)
    return 0


def cmd_evolve(args: argparse.Namespace) -> int:
    if args.trace is not None:
        all_ev = load_strata_routing_trace(args.trace, max_events=args.max_events)
        split_at = max(1, (len(all_ev) * 2) // 3)
        train_ev, holdout_ev = all_ev[:split_at], all_ev[split_at:]
    else:
        train_ev = generate_structured_moe_trace(num_tokens=40, seed=args.seed)
        holdout_ev = generate_structured_moe_trace(num_tokens=40, seed=args.seed + 999)

    baseline = _default_baseline(args.cache_mb)
    max_half = int(args.cache_mb * 1024 * 1024 * 0.75)
    res = run_evolutionary_search(
        train_trace=train_ev,
        holdout_trace=holdout_ev,
        baseline_genome=baseline,
        run_cfg=EvolutionRunConfig(
            generations=args.generations,
            num_islands=args.islands,
            bandit_name=args.bandit,
            seed=args.seed,
            max_gpu_budget_bytes=max_half,
            max_ram_budget_bytes=max_half,
        ),
        ctx=FidelityContext(ssd_bandwidth_bytes_per_s=args.ssd_gb_s * 1e9),
    )
    txt = json.dumps(res, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(txt + "\n", encoding="utf-8")
    LOGGER.info("EIO search complete:\n%s", txt)
    return 0


def cmd_compare_bandits(args: argparse.Namespace) -> int:
    train_ev = generate_structured_moe_trace(num_tokens=36, seed=args.seed)
    holdout_ev = generate_structured_moe_trace(num_tokens=36, seed=args.seed + 777)
    baseline = _default_baseline(args.cache_mb)
    max_half = int(args.cache_mb * 1024 * 1024 * 0.75)
    ctx = FidelityContext(ssd_bandwidth_bytes_per_s=args.ssd_gb_s * 1e9)

    comparison: dict[str, Any] = {}
    for b_name in ("uniform_random", "ucb1", "sliding_window_ucb", "thompson_sampling", "cost_aware_ucb"):
        out = run_evolutionary_search(
            train_trace=train_ev,
            holdout_trace=holdout_ev,
            baseline_genome=baseline,
            run_cfg=EvolutionRunConfig(
                generations=args.generations,
                num_islands=2,
                bandit_name=b_name,
                seed=args.seed,
                max_gpu_budget_bytes=max_half,
                max_ram_budget_bytes=max_half,
            ),
            ctx=ctx,
        )
        comparison[b_name] = {
            "search_wall_seconds": out["search_wall_seconds"],
            "pareto_frontier_size": out["pareto_frontier_size"],
            "best_holdout_candidate": out["best_holdout_candidate"],
        }
    txt = json.dumps(comparison, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(txt + "\n", encoding="utf-8")
    LOGGER.info("Equal-budget bandit comparison vs uniform_random:\n%s", txt)
    return 0


def cmd_real_evolve(args: argparse.Namespace) -> int:
    baseline = RealEngineGenome(
        vram_reserve_mb=args.vram_reserve_mb,
        cpu_pool_threads=args.base_cpu_threads,
        ssd_prefetch=0,
        rh_3tier=0,
        sata_pf_threads=0,
    )
    # Token-ID sequences for deterministic strata-inkling2 --tokens evaluation (search vs disjoint holdout)
    search_prompt = "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24"
    holdout_prompts = (
        "101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120",
        "250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269",
        "512,513,514,515,516,517,518,519,520,521,522,523,524,525,526,527,528,529,530,531",
    )

    def _eval(genome: RealEngineGenome, prompt: str, ref_sha: str | None) -> Any:
        return run_single_native_trial(
            engine_exe=args.engine_exe,
            model_path=args.model,
            genome=genome,
            prompt=prompt,
            max_tokens=args.max_tokens,
            ctx_size=args.ctx_size,
            reference_sha256=ref_sha,
            timeout_s=args.timeout,
        )

    res = run_real_hardware_evolution(
        evaluator=_eval,
        baseline=baseline,
        search_prompt=search_prompt,
        holdout_prompts=holdout_prompts[: max(1, args.holdout_prompts)],
        budget_candidates=args.candidates,
        bandit_name=args.bandit,
        seed=args.seed,
    )
    txt = json.dumps(res, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(txt + "\n", encoding="utf-8")
    LOGGER.info("Real-hardware EIO run complete (auto_adopted=False):\n%s", txt)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="NKAT-URT Evolutionary Inference Optimisation (EIO) CLI.")
    p.add_argument("--verbose", action="store_true")
    sub = p.add_subparsers(dest="command", required=True)

    pi = sub.add_parser("inspect-deps", help="Inspect Sakana AI / CUDA / Lean dependencies.")
    pi.set_defaults(func=cmd_inspect_deps)

    pm = sub.add_parser("math-check", help="Run EIO invariant, certificate, and amortisation checks.")
    pm.add_argument("--out", type=Path, default=None)
    pm.set_defaults(func=cmd_math_check)

    pe = sub.add_parser("evolve", help="Run multi-island Pareto evolutionary search with holdout verification.")
    pe.add_argument("--trace", type=Path, default=None)
    pe.add_argument("--max-events", type=int, default=4000)
    pe.add_argument("--generations", type=int, default=12)
    pe.add_argument("--islands", type=int, default=2)
    pe.add_argument("--bandit", default="sliding_window_ucb")
    pe.add_argument("--cache-mb", type=float, default=64.0)
    pe.add_argument("--ssd-gb-s", type=float, default=0.5)
    pe.add_argument("--seed", type=int, default=42)
    pe.add_argument("--out", type=Path, default=None)
    pe.set_defaults(func=cmd_evolve)

    pc = sub.add_parser("compare-bandits", help="Compare bandits against uniform random at equal budget.")
    pc.add_argument("--generations", type=int, default=10)
    pc.add_argument("--cache-mb", type=float, default=64.0)
    pc.add_argument("--ssd-gb-s", type=float, default=0.5)
    pc.add_argument("--seed", type=int, default=42)
    pc.add_argument("--out", type=Path, default=None)
    pc.set_defaults(func=cmd_compare_bandits)

    pr = sub.add_parser("real-evolve", help="Run real-hardware ShinkaEvolve-inspired search on a native Strata engine.")
    pr.add_argument("--engine-exe", type=Path, required=True, help="Path to native strata-inkling2.exe binary.")
    pr.add_argument("--model", type=Path, required=True, help="Path to local GGUF model file.")
    pr.add_argument("--ctx-size", type=int, default=16384)
    pr.add_argument("--max-tokens", type=int, default=32)
    pr.add_argument("--candidates", type=int, default=6)
    pr.add_argument("--holdout-prompts", type=int, default=3)
    pr.add_argument("--vram-reserve-mb", type=int, default=1536)
    pr.add_argument("--base-cpu-threads", type=int, default=6)
    pr.add_argument("--bandit", default="sliding_window_ucb")
    pr.add_argument("--timeout", type=float, default=240.0)
    pr.add_argument("--seed", type=int, default=42)
    pr.add_argument("--out", type=Path, default=None)
    pr.set_defaults(func=cmd_real_evolve)
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(args.verbose)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
