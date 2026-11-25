"""Real-hardware ShinkaEvolve-inspired evolutionary optimiser for Strata 4-tier MoE engines.

Searches over real, executable Strata runtime knobs (CPU expert threads, VRAM reserve,
pinned RAM budget, RAM embedding offload, prefill staging/threads, Q8 head pack,
SATA/NVMe prefetch & coalescing) strictly subject to:
- Immutable Level-0 parameter & safety-floor invariants (RAM >= 3 GiB, Commit >= 4 GiB,
  VRAM reserve >= 1536 MiB for Inkling-2, C: >= 5 GiB, H: >= 10 GiB),
- Strict greedy bit-exact numerical parity against baseline output (zero drift allowed),
- Exclusive single-GPU sequential evaluation (never concurrent GPU runs),
- Strict separation between search prompt and independent paired holdout prompts for
  Section 14 URT log-speedup certification,
- Separation of automated search from human-approved adoption (`auto_adopted=False`).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import logging
import os
from pathlib import Path
import random
import re
import shutil
import statistics
import subprocess
import time
from typing import Any, Callable, Sequence

from tsi.metrics import sample_gpu_vram_bytes, sample_system_memory_bytes

from .bandit import make_bandit
from .certificates import certify_paired_speedup, search_amortisation_breakeven

LOGGER = logging.getLogger("strata.evolution.hardware_evolve")

_INK2_STATS_RE = re.compile(
    r"pp\s+\d+\s+tok\s+in\s+[0-9.]+\s+ms\s+\(([0-9.]+)\s+t/s\)\s*\|\s*"
    r"tg\s+\d+\s+tok\s+in\s+[0-9.]+\s+ms\s+\(([0-9.]+)\s+t/s\)"
    r"(?:.*hits=(\d+)\s+misses=(\d+)\s+cpu_ms=([0-9.]+))?",
    re.IGNORECASE,
)
_PP_RE = re.compile(r"pp\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*t/s|prompt[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*t(?:ok)?/s", re.IGNORECASE)
_TG_RE = re.compile(r"tg\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*t/s|decode[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*t(?:ok)?/s|([0-9]+(?:\.[0-9]+)?)\s*tok/s", re.IGNORECASE)


@dataclass(frozen=True)
class RealEngineGenome:
    """Real executable Strata 4-tier MoE runtime knob genome (all knobs verified in inkling2_engine.cu)."""

    vram_reserve_mb: int = 1536
    max_pin_mb: int = 0             # 0 = engine auto
    cpu_pool_threads: int = 6       # Ryzen 5 4500 physical cores = 6 (12 logical)
    pp_stage_mb: int = 128
    pp_stream_threads: int = 2
    q8_head_pack: int = 1
    ram_embd: int = 0
    ssd_prefetch: int = 0
    rh_3tier: int = 0
    sata_pf_threads: int = 0
    sata_coalesce_gap_kb: int = 256
    aux_cpus: str = "off"

    def candidate_hash(self) -> str:
        raw = json.dumps(asdict(self), sort_keys=True, ensure_ascii=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:16]

    def to_env_overrides(self) -> dict[str, str]:
        env: dict[str, str] = {
            "STRATA_VRAM_RESERVE_MB": str(self.vram_reserve_mb),
            "STRATA_INKLING2_CPU_POOL": str(self.cpu_pool_threads),
            "STRATA_PP_STAGE_MB": str(self.pp_stage_mb),
            "STRATA_PP_STREAM_T": str(self.pp_stream_threads),
            "STRATA_Q8_HEAD_PACK": str(self.q8_head_pack),
            "STRATA_RAM_EMBD": str(self.ram_embd),
            "STRATA_SSD_PREFETCH": str(self.ssd_prefetch),
            "STRATA_RH_3TIER": str(self.rh_3tier),
            "STRATA_SATA_PF_THREADS": str(self.sata_pf_threads),
            "STRATA_SATA_COALESCE_GAP_KB": str(self.sata_coalesce_gap_kb),
            "STRATA_AUX_CPUS": self.aux_cpus,
            "STRATA_RAM_SQUEEZE": "on",
        }
        if self.max_pin_mb > 0:
            env["STRATA_MAX_PIN_MB"] = str(self.max_pin_mb)
        return env


def verify_real_engine_genome(genome: RealEngineGenome) -> tuple[bool, list[str]]:
    """Immutable Level-0 invariant & hardware safety verifier for RealEngineGenome."""
    violations: list[str] = []
    if not (1536 <= genome.vram_reserve_mb <= 4096):
        violations.append(f"vram_reserve_mb={genome.vram_reserve_mb} violates [1536, 4096] WDDM safety floor")
    if not (0 <= genome.max_pin_mb <= 8192):
        violations.append(f"max_pin_mb={genome.max_pin_mb} outside [0, 8192]")
    if not (1 <= genome.cpu_pool_threads <= 12):
        violations.append(f"cpu_pool_threads={genome.cpu_pool_threads} outside [1, 12]")
    if genome.pp_stage_mb not in (32, 64, 128, 256, 512):
        violations.append(f"pp_stage_mb={genome.pp_stage_mb} invalid")
    if not (1 <= genome.pp_stream_threads <= 6):
        violations.append(f"pp_stream_threads={genome.pp_stream_threads} outside [1, 6]")
    if genome.q8_head_pack not in (0, 1):
        violations.append("q8_head_pack must be 0 or 1")
    if genome.ram_embd not in (0, 1):
        violations.append("ram_embd must be 0 or 1")
    if genome.ssd_prefetch not in (0, 1):
        violations.append("ssd_prefetch must be 0 or 1")
    if genome.rh_3tier not in (0, 1):
        violations.append("rh_3tier must be 0 or 1")
    if not (0 <= genome.sata_pf_threads <= 2):
        violations.append("sata_pf_threads must be in [0, 2]")
    if genome.sata_coalesce_gap_kb not in (64, 128, 256, 512, 1024):
        violations.append("sata_coalesce_gap_kb invalid")
    if genome.aux_cpus not in ("off", "on"):
        violations.append("aux_cpus must be 'off' or 'on'")
    return (len(violations) == 0), violations


def check_live_resource_floors() -> tuple[bool, dict[str, Any]]:
    """Enforce RAM >= 3 GiB, VRAM free >= 1536 MiB, C: >= 5 GiB, H: >= 10 GiB before every run."""
    ram = sample_system_memory_bytes()
    vram = sample_gpu_vram_bytes()
    gib = 1024.0 ** 3
    mib = 1024.0 ** 2
    free_ram_gib = (ram["free_ram_bytes"] / gib) if ram["free_ram_bytes"] is not None else None
    free_vram_mib = (vram["free_vram_bytes"] / mib) if vram["free_vram_bytes"] is not None else None
    c_free_gib = shutil.disk_usage("C:\\").free / gib if os.name == "nt" else 100.0
    h_free_gib = shutil.disk_usage("H:\\").free / gib if os.name == "nt" and Path("H:\\").exists() else 100.0

    ok = True
    if free_ram_gib is not None and free_ram_gib < 3.0:
        ok = False
    if free_vram_mib is not None and free_vram_mib < 1536.0:
        ok = False
    if c_free_gib < 5.0 or h_free_gib < 10.0:
        ok = False
    return ok, {
        "free_ram_gib": round(free_ram_gib, 2) if free_ram_gib is not None else None,
        "free_vram_mib": round(free_vram_mib, 1) if free_vram_mib is not None else None,
        "c_free_gib": round(c_free_gib, 2),
        "h_free_gib": round(h_free_gib, 2),
        "floors_ok": ok,
    }


@dataclass(frozen=True)
class RealEvalOutcome:
    """Single hardware execution result with bit-exact parity hash and telemetry."""

    genome: RealEngineGenome
    rc: int
    wall_s: float
    decode_tps: float | None
    prefill_tps: float | None
    output_sha256: str
    bit_exact_parity: bool
    peak_vram_bytes: int | None
    peak_ram_bytes: int | None
    verified: bool
    detail: str
    cache_hits: int | None = None
    cache_misses: int | None = None
    cpu_expert_ms: float | None = None


REAL_MUTATION_OPS: tuple[str, ...] = (
    "mutate_cpu_threads_and_aux",
    "mutate_vram_ram_tiers",
    "mutate_prefill_staging",
    "mutate_ssd_prefetch",
    "crossover",
)


def mutate_real_engine_genome(
    op_name: str,
    parent: RealEngineGenome,
    mate: RealEngineGenome | None,
    rng: random.Random,
) -> RealEngineGenome:
    d = asdict(parent)
    if op_name == "mutate_cpu_threads_and_aux":
        d["cpu_pool_threads"] = rng.choice((4, 5, 6, 8, 10, 12))
        d["aux_cpus"] = rng.choice(("off", "on"))
        d["q8_head_pack"] = rng.choice((0, 1))
    elif op_name == "mutate_vram_ram_tiers":
        d["vram_reserve_mb"] = rng.choice((1536, 1792, 2048))
        d["max_pin_mb"] = rng.choice((0, 1024, 2048, 4096, 6144))
        d["ram_embd"] = rng.choice((0, 1))
    elif op_name == "mutate_prefill_staging":
        d["pp_stage_mb"] = rng.choice((64, 128, 256, 512))
        d["pp_stream_threads"] = rng.choice((1, 2, 4, 6))
        d["q8_head_pack"] = rng.choice((0, 1))
    elif op_name == "mutate_ssd_prefetch":
        pf = rng.choice((0, 1))
        d["ssd_prefetch"] = pf
        d["rh_3tier"] = rng.choice((0, 1)) if pf else 0
        d["sata_pf_threads"] = rng.choice((1, 2)) if pf else 0
        d["sata_coalesce_gap_kb"] = rng.choice((64, 256, 512, 1024))
    elif op_name == "crossover" and mate is not None:
        md = asdict(mate)
        for k in d:
            if rng.random() < 0.5:
                d[k] = md[k]
    else:
        d["cpu_pool_threads"] = rng.choice((4, 6, 8, 10))
    return RealEngineGenome(**d)


def parse_engine_telemetry(combined_output: str) -> dict[str, Any]:
    """Parse prefill/decode t/s, GPU expert cache hits/misses, and CPU expert ms from strata-inkling2 stderr."""
    m_ink = _INK2_STATS_RE.search(combined_output)
    if m_ink:
        hits = int(m_ink.group(3)) if m_ink.group(3) is not None else None
        misses = int(m_ink.group(4)) if m_ink.group(4) is not None else None
        cpu_ms = float(m_ink.group(5)) if m_ink.group(5) is not None else None
        return {
            "prefill_tps": float(m_ink.group(1)),
            "decode_tps": float(m_ink.group(2)),
            "cache_hits": hits,
            "cache_misses": misses,
            "cpu_expert_ms": cpu_ms,
        }
    pp, tg = parse_engine_tps(combined_output)
    return {
        "prefill_tps": pp,
        "decode_tps": tg,
        "cache_hits": None,
        "cache_misses": None,
        "cpu_expert_ms": None,
    }


def parse_engine_tps(combined_output: str) -> tuple[float | None, float | None]:
    m_ink = _INK2_STATS_RE.search(combined_output)
    if m_ink:
        return float(m_ink.group(1)), float(m_ink.group(2))
    pp: float | None = None
    tg: float | None = None
    m_pp = _PP_RE.search(combined_output)
    if m_pp:
        val = m_pp.group(1) or m_pp.group(2)
        if val:
            pp = float(val)
    for ln in reversed(combined_output.splitlines()):
        m_tg = _TG_RE.search(ln)
        if m_tg:
            val = m_tg.group(1) or m_tg.group(2) or m_tg.group(3)
            if val:
                tg = float(val)
                break
    return pp, tg


def run_single_native_trial(
    *,
    engine_exe: Path,
    model_path: Path,
    genome: RealEngineGenome,
    prompt: str,
    max_tokens: int,
    ctx_size: int,
    reference_sha256: str | None,
    timeout_s: float = 240.0,
) -> RealEvalOutcome:
    """Execute one exclusive GPU trial of `strata-inkling2.exe` using `--tokens` and check bit-exact parity."""
    ok_inv, violations = verify_real_engine_genome(genome)
    if not ok_inv:
        return RealEvalOutcome(genome, -1, 0.0, None, None, "", False, None, None, False, "; ".join(violations))

    ok_hw, hw_info = check_live_resource_floors()
    if not ok_hw:
        return RealEvalOutcome(genome, -2, 0.0, None, None, "", False, None, None, False, f"safety_floor_violated: {hw_info}")

    env = dict(os.environ)
    env.update(genome.to_env_overrides())
    cmd = [
        str(engine_exe),
        "--model", str(model_path),
        "--max-context", str(ctx_size),
        "--tokens", prompt,
        "--max-new", str(max_tokens),
        "--cpu-threads", str(genome.cpu_pool_threads),
        "--bench",
    ]
    ram0 = sample_system_memory_bytes()["used_ram_bytes"]
    vram0 = sample_gpu_vram_bytes()["used_vram_bytes"]
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=timeout_s, check=False)
    except subprocess.TimeoutExpired:
        return RealEvalOutcome(genome, -3, time.perf_counter() - t0, None, None, "", False, vram0, ram0, False, "timeout")
    wall_s = time.perf_counter() - t0
    ram1 = sample_system_memory_bytes()["used_ram_bytes"]
    vram1 = sample_gpu_vram_bytes()["used_vram_bytes"]
    peak_ram = max([x for x in (ram0, ram1) if x is not None], default=None)
    peak_vram = max([x for x in (vram0, vram1) if x is not None], default=None)

    if proc.returncode != 0:
        err_tail = (proc.stderr or proc.stdout or "").strip()[-300:]
        return RealEvalOutcome(genome, proc.returncode, wall_s, None, None, "", False, peak_vram, peak_ram, False, err_tail)

    # Extract exact greedy `tokens: ...` line for deterministic bit-exact parity check
    tok_lines = [ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip().startswith("tokens:")]
    out_sig = tok_lines[-1] if tok_lines else (proc.stdout or "").strip()
    out_sha = hashlib.sha256(out_sig.encode("utf-8")).hexdigest()
    combined = (proc.stderr or "") + "\n" + (proc.stdout or "")
    tel = parse_engine_telemetry(combined)
    tg = tel["decode_tps"]
    pp = tel["prefill_tps"]
    parity = True if reference_sha256 is None else (out_sha == reference_sha256)
    return RealEvalOutcome(
        genome=genome,
        rc=0,
        wall_s=round(wall_s, 4),
        decode_tps=tg,
        prefill_tps=pp,
        output_sha256=out_sha,
        bit_exact_parity=parity,
        peak_vram_bytes=peak_vram,
        peak_ram_bytes=peak_ram,
        verified=parity and (tg is not None and tg > 0.0),
        detail="ok" if parity else "BIT_EXACT_PARITY_MISMATCH",
        cache_hits=tel["cache_hits"],
        cache_misses=tel["cache_misses"],
        cpu_expert_ms=tel["cpu_expert_ms"],
    )


def run_real_hardware_evolution(
    *,
    evaluator: Callable[[RealEngineGenome, str, str | None], RealEvalOutcome],
    baseline: RealEngineGenome,
    search_prompt: str,
    holdout_prompts: Sequence[str],
    budget_candidates: int = 8,
    bandit_name: str = "sliding_window_ucb",
    seed: int = 42,
) -> dict[str, Any]:
    """Run real-hardware ShinkaEvolve-inspired search + independent paired holdout certification.

    Accepts an injectable `evaluator` so BOTH CPU unit tests (mock evaluator) and real
    RTX 5060 Ti executions share the exact same evolutionary, parity, and certification logic.
    """
    if not holdout_prompts:
        raise ValueError("holdout_prompts must be non-empty")

    t_search0 = time.perf_counter()
    rng = random.Random(seed)
    bandit = make_bandit(bandit_name, REAL_MUTATION_OPS, seed=seed)

    # 1. Measure baseline on search prompt (establishes bit-exact parity reference!)
    base_res = evaluator(baseline, search_prompt, None)
    if not base_res.verified:
        raise RuntimeError(f"Baseline failed verification: {base_res.detail}")
    ref_sha = base_res.output_sha256
    archive: list[RealEvalOutcome] = [base_res]
    seen_hashes: set[str] = {baseline.candidate_hash()}
    rejected: list[dict[str, Any]] = []

    LOGGER.info(
        "Baseline real-hardware eval: hash=%s tg=%s t/s pp=%s t/s wall=%.2fs sha=%s",
        baseline.candidate_hash(),
        base_res.decode_tps,
        base_res.prefill_tps,
        base_res.wall_s,
        ref_sha[:12],
    )

    # 2. Evolutionary search loop (exclusively sequential on single RTX 5060 Ti)
    for step in range(1, max(1, budget_candidates) + 1):
        # Fitness-proportionate parent selection over verified archive
        scores = [(r.decode_tps or 0.0) for r in archive]
        total_s = sum(scores) or 1.0
        pick = rng.random() * total_s
        acc = 0.0
        parent = archive[0].genome
        for r, sc in zip(archive, scores, strict=True):
            acc += sc
            if pick <= acc:
                parent = r.genome
                break
        mate = rng.choice(archive).genome if len(archive) > 1 else None

        arm = bandit.select()
        op_name = REAL_MUTATION_OPS[arm]
        cand: RealEngineGenome | None = None
        for _ in range(12):
            proposal = mutate_real_engine_genome(op_name, parent, mate, rng)
            ok_inv, _ = verify_real_engine_genome(proposal)
            if ok_inv and proposal.candidate_hash() not in seen_hashes:
                cand = proposal
                break
        if cand is None:
            bandit.update(arm, 0.0, eval_cost_s=0.01)
            continue

        seen_hashes.add(cand.candidate_hash())
        res = evaluator(cand, search_prompt, ref_sha)
        best_before = max((r.decode_tps or 0.0) for r in archive)

        if res.verified and res.bit_exact_parity:
            gain = max(0.0, ((res.decode_tps or 0.0) - best_before) / max(1e-6, best_before))
            bandit.update(arm, gain, eval_cost_s=max(0.01, res.wall_s))
            archive.append(res)
            LOGGER.info(
                "EIO cand %d/%d [%s] PASS parity=True tg=%s t/s pp=%s t/s wall=%.2fs (env=%s)",
                step,
                budget_candidates,
                op_name,
                res.decode_tps,
                res.prefill_tps,
                res.wall_s,
                cand.to_env_overrides(),
            )
        else:
            bandit.update(arm, 0.0, eval_cost_s=max(0.01, res.wall_s))
            rejected.append({"candidate_hash": cand.candidate_hash(), "op": op_name, "detail": res.detail})
            LOGGER.warning("EIO cand %d/%d REJECTED: %s", step, budget_candidates, res.detail)

    search_wall_s = time.perf_counter() - t_search0

    # Pick highest verified decode_tps candidate (tie-break by lower wall_s)
    best = max(archive, key=lambda r: ((r.decode_tps or 0.0), -r.wall_s))

    # 3. Independent paired holdout verification (separate prompts from search!)
    t_hold0 = time.perf_counter()
    base_hold_times: list[float] = []
    cand_hold_times: list[float] = []
    base_hold_tps: list[float] = []
    cand_hold_tps: list[float] = []
    holdout_parity_all = True
    holdout_rows: list[dict[str, Any]] = []

    for idx, hp in enumerate(holdout_prompts):
        b_h = evaluator(baseline, hp, None)
        c_h = evaluator(best.genome, hp, b_h.output_sha256)
        if not (b_h.verified and c_h.verified and c_h.bit_exact_parity):
            holdout_parity_all = False
        b_tok_time = 1.0 / max(1e-6, b_h.decode_tps or 1e-6)
        c_tok_time = 1.0 / max(1e-6, c_h.decode_tps or 1e-6)
        base_hold_times.append(b_tok_time)
        cand_hold_times.append(c_tok_time)
        if b_h.decode_tps is not None:
            base_hold_tps.append(b_h.decode_tps)
        if c_h.decode_tps is not None:
            cand_hold_tps.append(c_h.decode_tps)
        holdout_rows.append(
            {
                "holdout_index": idx,
                "baseline_decode_tps": b_h.decode_tps,
                "candidate_decode_tps": c_h.decode_tps,
                "baseline_prefill_tps": b_h.prefill_tps,
                "candidate_prefill_tps": c_h.prefill_tps,
                "baseline_cache_hit_rate": (
                    round(b_h.cache_hits / max(1, b_h.cache_hits + b_h.cache_misses), 6)
                    if (b_h.cache_hits is not None and b_h.cache_misses is not None)
                    else None
                ),
                "candidate_cache_hit_rate": (
                    round(c_h.cache_hits / max(1, c_h.cache_hits + c_h.cache_misses), 6)
                    if (c_h.cache_hits is not None and c_h.cache_misses is not None)
                    else None
                ),
                "baseline_cpu_expert_ms": b_h.cpu_expert_ms,
                "candidate_cpu_expert_ms": c_h.cpu_expert_ms,
                "baseline_wall_s": b_h.wall_s,
                "candidate_wall_s": c_h.wall_s,
                "bit_exact_parity": c_h.bit_exact_parity,
            }
        )
    holdout_wall_s = time.perf_counter() - t_hold0

    cert = certify_paired_speedup(
        base_hold_times,
        cand_hold_times,
        alpha=0.05,
        num_hypotheses=max(1, len(archive) - 1),
        range_width_R=None,
        range_width_R_certified=False,
        is_independent_holdout=True,
    )
    med_b_tps = statistics.median(base_hold_tps) if base_hold_tps else None
    med_c_tps = statistics.median(cand_hold_tps) if cand_hold_tps else None
    delta_t_tok = (
        (1.0 / med_b_tps) - (1.0 / med_c_tps)
        if (med_b_tps and med_c_tps and med_b_tps > 0 and med_c_tps > 0)
        else 0.0
    )
    amort = search_amortisation_breakeven(
        search_wall_s=search_wall_s,
        build_and_verify_s=holdout_wall_s,
        delta_t_saved_per_token_s=delta_t_tok,
        expected_deployment_tokens=100_000,
    )

    return {
        "engine_kind": "shinka_inspired_real_hardware_eio",
        "releaseQualified": False,
        "auto_adopted_into_default_inference": False,
        "search_wall_seconds": round(search_wall_s, 3),
        "holdout_verify_wall_seconds": round(holdout_wall_s, 3),
        "candidates_evaluated": len(archive) + len(rejected),
        "candidates_verified": len(archive),
        "candidates_rejected": len(rejected),
        "bandit_summary": bandit.summary(),
        "baseline_genome": asdict(baseline),
        "best_genome": asdict(best.genome),
        "best_env_overrides": best.genome.to_env_overrides(),
        "search_baseline_decode_tps": base_res.decode_tps,
        "search_best_decode_tps": best.decode_tps,
        "holdout_all_bit_exact_parity": holdout_parity_all,
        "holdout_baseline_median_decode_tps": round(med_b_tps, 3) if med_b_tps is not None else None,
        "holdout_candidate_median_decode_tps": round(med_c_tps, 3) if med_c_tps is not None else None,
        "holdout_trials": holdout_rows,
        "urt_paired_speedup_certificate": cert,
        "amortisation": amort,
        "archive": [
            {
                "candidate_hash": r.genome.candidate_hash(),
                "decode_tps": r.decode_tps,
                "prefill_tps": r.prefill_tps,
                "cache_hits": r.cache_hits,
                "cache_misses": r.cache_misses,
                "cpu_expert_ms": r.cpu_expert_ms,
                "wall_s": r.wall_s,
                "bit_exact_parity": r.bit_exact_parity,
                "peak_vram_bytes": r.peak_vram_bytes,
                "peak_ram_bytes": r.peak_ram_bytes,
                "env": r.genome.to_env_overrides(),
            }
            for r in archive
        ],
        "rejected": rejected,
    }
