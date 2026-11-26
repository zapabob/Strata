"""Phase XIV — Mathematical-Scientific & Evolutionary Hardware Optimizer for Inkling-2-Mini Mode B.

Hardware target:
  - CPU: AMD Ryzen 5 4500 (6C/12T, Zen 2, AVX2+FMA)
  - RAM: 32 GiB DDR4
  - GPU: NVIDIA GeForce RTX 5060 Ti 16 GiB (Blackwell SM120, CUDA 13.5)

Mathematical model:
  1. Recurrent visit-frequency optimality:
       v(l) = 3 for l in [6..17] (recurrent core: 36/48 visits = 75% of MoE compute)
       v(l) = 1 for l in [0..5] U [18..23] (single-visit prologue/epilogue)
     All 12 recurrent core layers are strictly pinned on CUDA0. Only k in {4,6,8,10}
     single-visit cold layers are offloaded to 32 GiB RAM / NVMe via `-ot`.
  2. Batched speculative expert-occupancy expectation:
       E[unique experts in batch B] = 128 * (1 - (1 - 8/128)^B)
     Predicts DDR4 bandwidth amortization across draft lengths d in {4, 8, 16, 32}.
  3. Constrained (mu + lambda) Evolutionary Search over runtime genome:
       g = (cold_cpu_layers, threads, ubatch, spec_mode, draft_len)
     Hard feasibility constraints (fitness = -inf if violated):
       - 100% greedy token-sequence parity vs Mode B Strict baseline (temp=0.0)
       - min_vram_free_mib >= 768 MiB
       - peak_shared_gpu_mib < 156.0 MiB (zero silent WDDM shared-memory spill)
       - avail_ram_gib >= 3.0 GiB

Uses logging + tqdm, strict typing, UTF-8, and zero print()/eval()/exec().
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import logging
import math
from pathlib import Path
import random
import sys
import time
from typing import Any

from tqdm import tqdm

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from phase14_modeB_spec_eval import (  # noqa: E402
    SPEC_PROMPTS,
    build_spec_args,
    launch_modeB_server,
    parse_spec_stats_from_log,
)
from phase13_acceptance_eval import (  # noqa: E402
    VramPeakMonitor,
    chat_completion,
    query_gpu_and_ram,
    stop_server,
    wait_health,
)

LOGGER = logging.getLogger("phase14.evo_tuner")

# Cold single-visit layer offload order (lowest activation sensitivity first from Phase XIII sensitivity audit)
COLD_SINGLE_VISIT_ORDER: tuple[int, ...] = (0, 1, 2, 3, 4, 5, 23, 22, 21, 20, 19, 18)

SPEC_MODES: tuple[str, ...] = (
    "none",
    "ngram-cache",
    "ngram-simple",
    "ngram-map-k",
    "ngram-map-k4v",
    "ngram-mod",
)
DRAFT_LENS: tuple[int, ...] = (4, 8, 16, 32)
THREAD_CHOICES: tuple[int, ...] = (5, 6, 8, 10, 12)
UBATCH_CHOICES: tuple[int, ...] = (16, 32)
COLD_LAYER_COUNTS: tuple[int, ...] = (4, 6, 8, 10)


@dataclass(frozen=True)
class Genome:
    cold_cpu_layers: int
    threads: int
    ubatch: int
    spec_mode: str
    draft_len: int

    def key(self) -> tuple[int, int, int, str, int]:
        d = 0 if self.spec_mode == "none" else self.draft_len
        return (self.cold_cpu_layers, self.threads, self.ubatch, self.spec_mode, d)

    def ot_regex(self) -> str:
        layers = sorted(COLD_SINGLE_VISIT_ORDER[: self.cold_cpu_layers])
        joined = "|".join(str(x) for x in layers)
        return rf"blk\.({joined})\.ffn_.*_exps=CPU"


def expected_unique_experts(batch_tokens: int, n_experts: int = 128, top_k: int = 8) -> float:
    """Exact occupancy probability E[unique experts] for top-k routing over B tokens."""
    p_not_chosen = (1.0 - (top_k / float(n_experts))) ** max(1, batch_tokens)
    return float(n_experts) * (1.0 - p_not_chosen)


def theoretical_bandwidth_amortization(draft_len: int) -> float:
    """Ratio of naive (B * 8) expert reads to expected unique expert reads E[unique(B)]."""
    b = max(1, draft_len + 1)
    return round((b * 8.0) / expected_unique_experts(b), 4)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def evaluate_genome(
    args: argparse.Namespace,
    genome: Genome,
    baseline_outputs: dict[str, dict[str, Any]] | None,
    eval_index: int,
) -> dict[str, Any]:
    base_url = f"http://127.0.0.1:{args.port}"
    d_eff = 0 if genome.spec_mode == "none" else genome.draft_len
    log_path = args.out.parent / f"evo_{eval_index:02d}_c{genome.cold_cpu_layers}_t{genome.threads}_u{genome.ubatch}_{genome.spec_mode}_d{d_eff}.log"
    spec_args = build_spec_args(genome.spec_mode, d_eff)
    ot_rules = [genome.ot_regex()]

    # Launch with exact evolved thread count & ubatch
    cmd_proc_log = log_path
    proc, fh = launch_modeB_server(
        args.server,
        args.model,
        ctx=args.ctx,
        ub=genome.ubatch,
        port=args.port,
        log_path=cmd_proc_log,
        ot_rules=ot_rules,
        spec_args=spec_args + ["-t", str(genome.threads)],
    )
    rec: dict[str, Any] = {
        "eval_index": eval_index,
        "genome": asdict(genome),
        "ot_regex": ot_rules[0],
        "theoretical_bw_amortization": theoretical_bandwidth_amortization(d_eff),
        "feasible": False,
        "fitness": -1.0,
    }
    try:
        load_s = wait_health(base_url, proc, timeout_s=240.0)
        monitor = VramPeakMonitor(proc.pid, interval_s=1.0)
        monitor.start()
        cold_runs: dict[str, Any] = {}
        warm_runs: dict[str, Any] = {}
        try:
            for p in SPEC_PROMPTS:
                body, lat = chat_completion(
                    base_url,
                    p["messages"],
                    max_tokens=p["max_tokens"],
                    temperature=0.0,
                    reasoning_effort="none",
                    tools=p.get("tools"),
                    timeout_s=300.0,
                )
                msg = body["choices"][0]["message"]
                cold_runs[p["id"]] = {
                    "content": msg.get("content") or "",
                    "tool_calls": msg.get("tool_calls") or [],
                    "finish_reason": body["choices"][0].get("finish_reason"),
                    "latency_s": lat,
                    "predicted_per_second": body.get("timings", {}).get("predicted_per_second"),
                }
            for p in SPEC_PROMPTS:
                body, lat = chat_completion(
                    base_url,
                    p["messages"],
                    max_tokens=p["max_tokens"],
                    temperature=0.0,
                    reasoning_effort="none",
                    tools=p.get("tools"),
                    timeout_s=300.0,
                )
                msg = body["choices"][0]["message"]
                warm_runs[p["id"]] = {
                    "content": msg.get("content") or "",
                    "tool_calls": msg.get("tool_calls") or [],
                    "finish_reason": body["choices"][0].get("finish_reason"),
                    "latency_s": lat,
                    "predicted_per_second": body.get("timings", {}).get("predicted_per_second"),
                }
        finally:
            peak_hw = monitor.stop()
        post_hw = query_gpu_and_ram()

        parity_ok = True
        if baseline_outputs is not None:
            for pid, run in cold_runs.items():
                ref = baseline_outputs[pid]
                if (
                    run["content"] != ref["content"]
                    or run["tool_calls"] != ref["tool_calls"]
                    or run["finish_reason"] != ref["finish_reason"]
                ):
                    parity_ok = False
                    break

        cold_tps = [r["predicted_per_second"] for r in cold_runs.values() if r.get("predicted_per_second")]
        warm_tps = [r["predicted_per_second"] for r in warm_runs.values() if r.get("predicted_per_second")]
        cold_mean = sum(cold_tps) / len(cold_tps) if cold_tps else 0.0
        warm_mean = sum(warm_tps) / len(warm_tps) if warm_tps else 0.0

        vram_ok = (peak_hw.get("min_vram_free_mib") or 0) >= 768
        shared_ok = (peak_hw.get("peak_shared_gpu_mib") or 0.0) < 156.0
        ram_ok = (post_hw.get("avail_ram_gib") or 0.0) >= 3.0
        feasible = parity_ok and vram_ok and shared_ok and ram_ok
        # Geometric mean of cold & warm decode throughput (strictly penalizes infeasible genomes)
        fitness = round(math.sqrt(max(cold_mean, 0.0) * max(warm_mean, 0.0)), 4) if feasible else -1.0

        rec.update(
            {
                "load_seconds": load_s,
                "cold_mean_decode_tps": round(cold_mean, 2),
                "warm_mean_decode_tps": round(warm_mean, 2),
                "parity_ok": parity_ok,
                "vram_ok": vram_ok,
                "shared_ok": shared_ok,
                "ram_ok": ram_ok,
                "feasible": feasible,
                "fitness": fitness,
                "peak_hw": peak_hw,
                "post_avail_ram_gib": post_hw.get("avail_ram_gib"),
                "cold_runs": cold_runs if baseline_outputs is None else None,
            }
        )
    except Exception as exc:
        rec["error"] = str(exc)
    finally:
        stop_server(proc, fh)
        time.sleep(2.0)

    rec["log_spec_stats"] = parse_spec_stats_from_log(log_path)
    return rec


def mutate(g: Genome, rng: random.Random) -> Genome:
    field = rng.choice(["cold_cpu_layers", "threads", "ubatch", "spec_mode", "draft_len"])
    c = rng.choice(COLD_LAYER_COUNTS) if field == "cold_cpu_layers" else g.cold_cpu_layers
    t = rng.choice(THREAD_CHOICES) if field == "threads" else g.threads
    u = rng.choice(UBATCH_CHOICES) if field == "ubatch" else g.ubatch
    m = rng.choice(SPEC_MODES[1:]) if field == "spec_mode" else g.spec_mode
    d = rng.choice(DRAFT_LENS) if field == "draft_len" else g.draft_len
    return Genome(cold_cpu_layers=c, threads=t, ubatch=u, spec_mode=m, draft_len=d)


def crossover(a: Genome, b: Genome, rng: random.Random) -> Genome:
    return Genome(
        cold_cpu_layers=rng.choice((a.cold_cpu_layers, b.cold_cpu_layers)),
        threads=rng.choice((a.threads, b.threads)),
        ubatch=rng.choice((a.ubatch, b.ubatch)),
        spec_mode=rng.choice((a.spec_mode, b.spec_mode)),
        draft_len=rng.choice((a.draft_len, b.draft_len)),
    )


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", type=Path, required=True)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--ctx", type=int, default=16384)
    p.add_argument("--port", type=int, default=8098)
    p.add_argument("--generations", type=int, default=3)
    p.add_argument("--pop-size", type=int, default=4)
    p.add_argument("--seed", type=int, default=20261125)
    args = p.parse_args(argv)

    rng = random.Random(args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    # Gen 0 anchor: Mode B Strict baseline (8 cold layers, 6 physical cores, ub=32, spec=none)
    baseline_g = Genome(cold_cpu_layers=8, threads=6, ubatch=32, spec_mode="none", draft_len=0)
    LOGGER.info("Evaluating Mode B Strict anchor genome: %s", baseline_g)
    base_rec = evaluate_genome(args, baseline_g, None, 0)
    if not base_rec["feasible"]:
        raise RuntimeError(f"Mode B Strict anchor infeasible: {base_rec}")
    baseline_outputs = base_rec["cold_runs"]
    base_rec["cold_runs"] = None

    evaluated: dict[tuple[int, int, int, str, int], dict[str, Any]] = {baseline_g.key(): base_rec}
    history: list[dict[str, Any]] = [base_rec]
    eval_counter = 1

    # Seed initial diverse population informed by mathematical roofline model
    population: list[Genome] = [
        Genome(cold_cpu_layers=6, threads=6, ubatch=32, spec_mode="ngram-cache", draft_len=8),
        Genome(cold_cpu_layers=6, threads=6, ubatch=32, spec_mode="ngram-simple", draft_len=8),
        Genome(cold_cpu_layers=8, threads=12, ubatch=32, spec_mode="ngram-map-k4v", draft_len=16),
        Genome(cold_cpu_layers=4, threads=6, ubatch=32, spec_mode="ngram-mod", draft_len=8),
    ][: args.pop_size]

    for gen in range(args.generations):
        LOGGER.info("=== Generation %d / %d ===", gen + 1, args.generations)
        for g in tqdm(population, desc=f"evo-gen-{gen + 1}", unit="genome"):
            if g.key() in evaluated:
                continue
            rec = evaluate_genome(args, g, baseline_outputs, eval_counter)
            eval_counter += 1
            evaluated[g.key()] = rec
            history.append(rec)
            LOGGER.info(
                "Gen %d | %s -> fitness=%.2f (cold=%.2f warm=%.2f t/s, feasible=%s, free=%s MiB)",
                gen + 1,
                g.key(),
                rec["fitness"],
                rec.get("cold_mean_decode_tps") or 0.0,
                rec.get("warm_mean_decode_tps") or 0.0,
                rec["feasible"],
                (rec.get("peak_hw") or {}).get("min_vram_free_mib"),
            )
            # Save checkpoint every evaluation
            feasible_sorted = sorted(
                [r for r in history if r["feasible"]],
                key=lambda r: r["fitness"],
                reverse=True,
            )
            args.out.write_text(
                json.dumps(
                    {
                        "schema": "phase14-evolutionary-opt-v1",
                        "model": args.model.name,
                        "hardware": "Ryzen 5 4500 (6C/12T) + 32GiB RAM + RTX 5060 Ti 16GiB (SM120)",
                        "seed": args.seed,
                        "generations_completed": gen + 1,
                        "total_evaluations": len(history),
                        "best_feasible": feasible_sorted[0] if feasible_sorted else None,
                        "pareto_top5": feasible_sorted[:5],
                        "history": history,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

        # Select top-2 feasible elites and breed next generation via crossover + mutation
        elites_rec = sorted([r for r in history if r["feasible"]], key=lambda r: r["fitness"], reverse=True)[:2]
        elites = [Genome(**r["genome"]) for r in elites_rec] or [baseline_g]
        next_pop: list[Genome] = []
        attempts = 0
        while len(next_pop) < args.pop_size and attempts < 40:
            attempts += 1
            if len(elites) >= 2 and rng.random() < 0.5:
                child = mutate(crossover(elites[0], elites[1], rng), rng)
            else:
                child = mutate(rng.choice(elites), rng)
            if child.key() not in evaluated and all(child.key() != x.key() for x in next_pop):
                next_pop.append(child)
        population = next_pop

    LOGGER.info("Evolutionary optimization complete -> %s", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
