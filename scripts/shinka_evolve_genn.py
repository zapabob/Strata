#!/usr/bin/env python3
"""SakanaAI ShinkaEvolve (arXiv:2509.19349) + robust-kbench (arXiv:2509.14279)
Gen-N 3-Island Evolutionary Optimizer for Strata Inkling-2-Mini Hybrid MoE Engine.

Extends Gen-M with Riemann Hypothesis (RH)-conditional primitives assuming Re(rho_k) = 1/2:
  1. RH Explicit-Formula Spectral Phase / Regime-Shift Detector (Odlyzko zeros kZetaZeroImag[0..7]
     + positive Shannon entropy jump delta_H = max(0, H_t - H_{t-1})).
  2. RH-UCB Cold-Start Admission Bound O(sqrt(ln(t+e)) / (sqrt(S+1) * sqrt(t+4))) for early decode.
  3. Continuous-depth Riemann Zeta-Lagrangian VRAM allocation + scale-invariant LeCaR + ST-MoE Markov.

Hardware calibration target:
  - AMD Ryzen 5 4500 (6C/12T AVX2, 8 MB L3) + 32 GiB RAM + NVIDIA RTX 5060 Ti 16 GiB (SM120)
  - 12 outer MoE layers (mixed Q8_0 / Q5_0 / Q6_K / Q4_K), 128 experts/layer, top-8 routing.
"""
from __future__ import annotations

import dataclasses
import json
import logging
import math
import random
from pathlib import Path
from typing import List, Sequence, Tuple

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover
    def tqdm(iterable, **kwargs):  # type: ignore[misc]
        return iterable

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("shinka_evolve_genn")

# First 8 Odlyzko non-trivial Riemann zeta zeros gamma_k on critical line Re(rho_k) = 1/2
ZETA_ZEROS_8: Tuple[float, ...] = (
    14.134725141734694,
    21.022039638771555,
    25.010857580145688,
    30.424876125859513,
    32.935061587739190,
    37.586178158825671,
    40.918719012147495,
    43.327073280914999,
)
ZETA_NORM_8: float = sum(1.0 / math.sqrt(0.25 + g * g) for g in ZETA_ZEROS_8)


@dataclasses.dataclass(frozen=True)
class GenNGenome:
    s_shallow: float
    s_deep: float
    cost_q6k: float
    cost_q80: float
    von_koch_c: float
    impact_alpha: float
    markov_dt1: float
    lecar_w_init: float
    lecar_eta: float
    recency_scale: float
    rh_spec_amp: float     # RH explicit-formula spectral anti-resonance modulation
    rh_dh_gain: float      # Entropy-jump (delta_H > 0) regime-shift flush gain
    rh_ucb_c: float        # RH-UCB cold-start admission bound coefficient

    def as_vec(self) -> Tuple[float, ...]:
        return (
            self.s_shallow,
            self.s_deep,
            self.cost_q6k,
            self.cost_q80,
            self.von_koch_c,
            self.impact_alpha,
            self.markov_dt1,
            self.lecar_w_init,
            self.lecar_eta,
            self.recency_scale,
            self.rh_spec_amp,
            self.rh_dh_gain,
            self.rh_ucb_c,
        )


BOUNDS: Tuple[Tuple[float, float], ...] = (
    (0.95, 2.00),   # s_shallow
    (0.80, 1.65),   # s_deep
    (1.15, 1.70),   # cost_q6k
    (1.10, 1.55),   # cost_q80
    (0.05, 0.50),   # von_koch_c
    (0.15, 1.40),   # impact_alpha
    (0.05, 1.00),   # markov_dt1
    (0.25, 0.88),   # lecar_w_init
    (0.10, 0.85),   # lecar_eta
    (0.30, 2.50),   # recency_scale
    (0.00, 0.08),   # rh_spec_amp (bounded critical-line spectral phase)
    (0.00, 0.65),   # rh_dh_gain (regime-shift entropy-jump decay drop)
    (0.00, 1.50),   # rh_ucb_c (early-decode RH-UCB cold-start bonus)
)


def clamp_genome(vals: Sequence[float]) -> GenNGenome:
    return GenNGenome(*(min(hi, max(lo, v)) for v, (lo, hi) in zip(vals, BOUNDS)))


@dataclasses.dataclass
class EvalResult:
    genome: GenNGenome
    train_score: float
    val_score: float
    hit_rate: float
    verified: bool
    slots: List[int]


def truncated_zeta(n_experts: int, s: float) -> float:
    return sum((k ** (-s)) for k in range(1, n_experts + 1))


def continuous_layer_exponents(n_layers: int, s_shallow: float, s_deep: float) -> List[float]:
    if n_layers <= 1:
        return [s_shallow]
    out: List[float] = []
    for i in range(n_layers):
        t = i / float(n_layers - 1)
        w = 0.5 * (1.0 + math.cos(math.pi * t))
        out.append(s_deep + (s_shallow - s_deep) * w)
    return out


def zeta_lagrangian_allocate(
    costs: List[float],
    strides: List[int],
    exponents: List[float],
    budget: int,
    max_slots: int = 128,
) -> List[int]:
    n_layers = len(costs)
    slots = [0] * n_layers
    inv_z = [1.0 / truncated_zeta(max_slots, s) for s in exponents]
    used = 0
    while True:
        best_i = -1
        best_mu = -1.0
        for i in range(n_layers):
            if slots[i] >= max_slots or used + strides[i] > budget:
                continue
            rank = float(slots[i] + 1)
            mu = (costs[i] * (rank ** (-exponents[i])) * inv_z[i]) / float(strides[i])
            if mu > best_mu:
                best_mu = mu
                best_i = i
        if best_i < 0:
            break
        slots[best_i] += 1
        used += strides[best_i]
    return slots


def rh_explicit_spectral_phase(step: int) -> float:
    """Normalized RH explicit-formula critical-line oscillation in [-1, 1]."""
    ln_x = math.log(float(step) + 2.0)
    acc = 0.0
    for g in ZETA_ZEROS_8:
        acc += math.cos(g * ln_x) / math.sqrt(0.25 + g * g)
    return acc / ZETA_NORM_8


def rh_ucb_admission_bonus(score: float, step: int, c_ucb: float) -> float:
    """RH-conditional O(sqrt(ln(t+e)) / (sqrt(S+1) * sqrt(t+4))) cold-start bonus."""
    if c_ucb <= 0.0 or score <= 0.0:
        return 0.0
    num = math.sqrt(max(1.0, math.log(float(step) + math.e)))
    den = math.sqrt(score + 1.0) * math.sqrt(float(step) + 4.0)
    return c_ucb * (num / den)


def robust_kbench_verify(
    genome: GenNGenome,
    slots: List[int],
    strides: List[int],
    budget: int,
) -> bool:
    for v, (lo, hi) in zip(genome.as_vec(), BOUNDS):
        if not math.isfinite(v) or v < lo - 1e-9 or v > hi + 1e-9:
            return False
    if genome.s_shallow < genome.s_deep - 0.15:
        return False
    used = sum(s * b for s, b in zip(slots, strides))
    if used > budget or any(s < 0 or s > 128 for s in slots):
        return False
    return True


def generate_multi_regime_traces(
    seed: int,
    n_layers: int = 12,
    pp_steps: int = 16,
    tg_steps: int = 64,
    top_k: int = 8,
) -> List[List[List[Tuple[int, float]]]]:
    """Multi-regime routing trace with prefill->decode shift + mid-decode topic shift."""
    rng = random.Random(seed)
    traces: List[List[List[Tuple[int, float]]]] = []
    for li in range(n_layers):
        t_depth = li / float(max(1, n_layers - 1))
        true_s = 1.48 - 0.44 * t_depth
        weights = [(k ** (-true_s)) for k in range(1, 129)]
        perm_pp = list(range(128))
        rng.shuffle(perm_pp)
        perm_a = list(perm_pp)
        # Mild prefill -> decode shift
        sub_a = perm_a[:24]
        rng.shuffle(sub_a)
        perm_a[:24] = sub_a[6:] + sub_a[:6]
        # Stronger mid-decode topic/code regime shift
        perm_b = list(perm_a)
        sub_b = perm_b[:40]
        rng.shuffle(sub_b)
        perm_b[:40] = sub_b[16:] + sub_b[:16]

        layer_tokens: List[List[Tuple[int, float]]] = []
        prev_set: List[int] = []
        total_toks = pp_steps + tg_steps
        for tok in range(total_toks):
            if tok < pp_steps:
                perm = perm_pp
            elif tok < pp_steps + tg_steps // 2:
                perm = perm_a
            else:
                perm = perm_b
            chosen: List[int] = []
            for pe in prev_set:
                if len(chosen) < top_k // 2 and rng.random() < 0.28:
                    chosen.append(pe)
            while len(chosen) < top_k:
                c = rng.choices(perm, weights=weights, k=1)[0]
                if c not in chosen:
                    chosen.append(c)
            rank_map = {e: idx for idx, e in enumerate(perm)}
            tok_entries = [
                (e, 0.08 + 0.32 / (1.0 + 0.25 * rank_map[e])) for e in chosen
            ]
            layer_tokens.append(tok_entries)
            prev_set = chosen
        traces.append(layer_tokens)
    return traces


def simulate_workload(
    genome: GenNGenome,
    traces: List[List[List[Tuple[int, float]]]],
    layer_types: List[str],
    strides: List[int],
    budget: int,
) -> Tuple[float, float, List[int]]:
    n_layers = len(layer_types)
    costs = [
        genome.cost_q6k if t == "q6k" else (genome.cost_q80 if t == "q80" else 1.0)
        for t in layer_types
    ]
    true_costs = [
        1.46 if t == "q6k" else (1.30 if t == "q80" else 1.0)
        for t in layer_types
    ]
    exponents = continuous_layer_exponents(n_layers, genome.s_shallow, genome.s_deep)
    slots = zeta_lagrangian_allocate(costs, strides, exponents, budget)
    if not robust_kbench_verify(genome, slots, strides, budget):
        return 0.0, 0.0, slots

    total_lookups = 0
    total_hits = 0
    weighted_saved = 0.0
    pp_steps = 16

    for li in range(n_layers):
        cap = slots[li]
        resident = set(range(cap))
        scores: List[float] = [0.0] * 128
        last_tok: List[int] = [0] * 128
        w_lfu = genome.lecar_w_init
        ghost: List[Tuple[int, int, int]] = []
        rebal_step = 0
        prev_h = 0.5

        for tok_idx, entries in enumerate(traces[li], start=1):
            for exp_id, ew in entries:
                total_lookups += 1
                if exp_id in resident:
                    total_hits += 1
                    weighted_saved += true_costs[li]
                else:
                    for gi in range(len(ghost) - 1, -1, -1):
                        gid, gstep, greason = ghost[gi]
                        if gid == exp_id:
                            age = max(1, tok_idx - gstep)
                            disc = 0.85 ** min(age, 32)
                            w_lru = 1.0 - w_lfu
                            if greason == 0:
                                w_lru *= math.exp(genome.lecar_eta * disc)
                            else:
                                w_lfu *= math.exp(genome.lecar_eta * disc)
                            norm = w_lfu + w_lru
                            if norm > 0.0:
                                w_lfu = min(0.90, max(0.15, w_lfu / norm))
                            ghost.pop(gi)
                            break

                dt = tok_idx - last_tok[exp_id] if last_tok[exp_id] > 0 else 999
                markov = genome.markov_dt1 if dt == 1 else (0.45 * genome.markov_dt1 if dt == 2 else 0.0)
                last_tok[exp_id] = tok_idx
                scores[exp_id] += 1.0 + genome.impact_alpha * ew + markov

            do_post_pp = (tok_idx == pp_steps)
            do_decode_rebal = (tok_idx > pp_steps and ((tok_idx - pp_steps) % 4 == 0))
            if (do_post_pp or do_decode_rebal) and cap > 0:
                rebal_step += 1
                pos_scores = [s for s in scores if s > 0.0]
                mean_act = (sum(pos_scores) / len(pos_scores)) if pos_scores else 1.0
                rec_amp = genome.recency_scale * mean_act

                def blend(e: int) -> float:
                    age = max(0, tok_idx - last_tok[e]) if last_tok[e] > 0 else 64
                    rec = 1.0 / (1.0 + 0.15 * age)
                    base = w_lfu * scores[e] + (1.0 - w_lfu) * (rec * rec_amp)
                    if e not in resident:
                        base += rh_ucb_admission_bonus(scores[e], rebal_step, genome.rh_ucb_c)
                    return base

                blended = [blend(e) for e in range(128)]
                ranked = sorted(range(128), key=lambda e: blended[e], reverse=True)
                cold_res = sorted(resident, key=lambda e: blended[e])
                max_swaps = min(cap, 24 if do_post_pp else 2)
                swaps = 0
                for hot in ranked[:cap]:
                    if hot in resident or swaps >= max_swaps:
                        continue
                    cold = cold_res[swaps]
                    s_h, s_c = blended[hot], blended[cold]
                    thr = (
                        genome.von_koch_c * math.sqrt(max(0.0, s_h + s_c)) / max(1.0, math.log(rebal_step + math.e))
                        if s_c > 0.0
                        else 0.0
                    )
                    if s_h - s_c > thr:
                        resident.remove(cold)
                        resident.add(hot)
                        ghost.append((cold, tok_idx, 1 if w_lfu < 0.5 else 0))
                        if len(ghost) > 16:
                            ghost.pop(0)
                        swaps += 1

                total_s = sum(s for s in scores if s > 0.0)
                if total_s > 1e-12:
                    h = -sum((s / total_s) * math.log(s / total_s) for s in scores if s > 0.0)
                    h_norm = min(1.0, max(0.0, h / math.log(128.0)))
                else:
                    h_norm = 0.5
                dh_pos = max(0.0, h_norm - prev_h)
                prev_h = h_norm
                base_d = min(0.96, max(0.50, 1.0 - 1.0 / math.sqrt(rebal_step + 4.0)))
                spec_mod = genome.rh_spec_amp * rh_explicit_spectral_phase(rebal_step)
                decay = min(0.96, max(0.50, base_d + 0.08 * (0.5 - h_norm) - genome.rh_dh_gain * dh_pos + spec_mod))
                scores = [s * decay for s in scores]

    hit_rate = total_hits / max(1, total_lookups)
    return weighted_saved, hit_rate, slots


def run_shinka_evolve_genn(generations: int = 36, n_islands: int = 3, seed: int = 20261128) -> EvalResult:
    rng = random.Random(seed)
    # 12 outer layers of Sakura-Inkling-2-Mini (6 Q8_0 shallow + 6 Q5_0/Q8_0 deep)
    layer_types = ["q80", "q80", "q80", "q80", "q80", "q80", "q4k", "q4k", "q80", "q4k", "q4k", "q80"]
    strides = [5750000 if t == "q80" else 4800000 for t in layer_types]
    budget = 720 * 5200000

    train_traces = [generate_multi_regime_traces(seed + i * 101) for i in range(3)]
    val_traces = [generate_multi_regime_traces(seed + 9000 + i * 137) for i in range(2)]

    def eval_candidate(g: GenNGenome) -> EvalResult:
        tr_scores, tr_hits = [], []
        last_slots: List[int] = []
        for tr in train_traces:
            sc, hr, sl = simulate_workload(g, tr, layer_types, strides, budget)
            tr_scores.append(sc)
            tr_hits.append(hr)
            last_slots = sl
        va_scores = [simulate_workload(g, vt, layer_types, strides, budget)[0] for vt in val_traces]
        ok = robust_kbench_verify(g, last_slots, strides, budget)
        return EvalResult(
            genome=g,
            train_score=sum(tr_scores) / len(tr_scores),
            val_score=sum(va_scores) / len(va_scores),
            hit_rate=sum(tr_hits) / len(tr_hits),
            verified=ok,
            slots=last_slots,
        )

    genm_baseline = GenNGenome(
        s_shallow=1.2470, s_deep=0.9116, cost_q6k=1.3065, cost_q80=1.3027,
        von_koch_c=0.2955, impact_alpha=0.5359, markov_dt1=0.1387,
        lecar_w_init=0.6046, lecar_eta=0.6349, recency_scale=1.8393,
        rh_spec_amp=0.0, rh_dh_gain=0.0, rh_ucb_c=0.0,
    )
    base_res = eval_candidate(genm_baseline)
    logger.info(
        "Gen-M baseline (v0.8.4): train=%.1f val=%.1f hit_rate=%.4f slots=%s",
        base_res.train_score, base_res.val_score, base_res.hit_rate, base_res.slots,
    )

    islands: List[List[EvalResult]] = [[base_res] for _ in range(n_islands)]
    op_counts = [1, 1, 1, 1]
    op_rewards = [0.0, 0.0, 0.0, 0.0]

    for gen in tqdm(range(1, generations + 1), desc="ShinkaEvolve Gen-N", disable=True):
        for isl in range(n_islands):
            arch = islands[isl]
            top_k = sorted(arch, key=lambda r: r.train_score, reverse=True)[:5]
            p1 = rng.choice(top_k).genome.as_vec()

            total_pulls = sum(op_counts)
            ucb = [
                (op_rewards[i] / op_counts[i]) + 0.55 * math.sqrt(math.log(total_pulls + 1.0) / op_counts[i])
                for i in range(4)
            ]
            op = max(range(4), key=lambda i: ucb[i])

            if op == 0:
                cand_vec = [v + rng.gauss(0.0, 0.08 * (hi - lo)) for v, (lo, hi) in zip(p1, BOUNDS)]
            elif op == 1:
                cand_vec = [
                    v + 0.14 * (hi - lo) * math.tan(math.pi * (rng.random() - 0.5) * 0.85)
                    for v, (lo, hi) in zip(p1, BOUNDS)
                ]
            elif op == 2:
                p2 = rng.choice(top_k).genome.as_vec()
                w = rng.uniform(0.2, 0.8)
                cand_vec = [w * a + (1.0 - w) * b for a, b in zip(p1, p2)]
            else:
                pw = top_k[-1].genome.as_vec()
                cand_vec = [2.0 * a - b for a, b in zip(p1, pw)]

            cand = clamp_genome(cand_vec)
            cv = cand.as_vec()
            if any(
                math.sqrt(sum((a - b) ** 2 for a, b in zip(cv, r.genome.as_vec()))) < 0.03
                for r in arch
            ):
                continue

            res = eval_candidate(cand)
            op_counts[op] += 1
            if res.verified:
                best_before = max(r.train_score for r in arch)
                reward = max(0.0, res.train_score - best_before) / max(1.0, best_before)
                op_rewards[op] += reward
                arch.append(res)

        if gen % 6 == 0:
            migrants = [max(arch, key=lambda r: r.train_score) for arch in islands]
            for isl in range(n_islands):
                islands[(isl + 1) % n_islands].append(migrants[isl])

    all_cands = [r for arch in islands for r in arch if r.verified]
    best = max(all_cands, key=lambda r: r.val_score)
    gain_train = 100.0 * (best.train_score / max(1e-9, base_res.train_score) - 1.0)
    gain_val = 100.0 * (best.val_score / max(1e-9, base_res.val_score) - 1.0)
    logger.info(
        "ShinkaEvolve Gen-N BEST (val-selected): train=%.1f (%+.2f%%) val=%.1f (%+.2f%%) hit_rate=%.4f",
        best.train_score, gain_train, best.val_score, gain_val, best.hit_rate,
    )
    logger.info("Best Gen-N genome: %s", json.dumps(dataclasses.asdict(best.genome), indent=2))
    logger.info("Best VRAM slots: %s", best.slots)

    out_path = Path("scripts/shinka_evolve_genn_best.json")
    out_path.write_text(
        json.dumps(
            {
                "genome": dataclasses.asdict(best.genome),
                "train_score": best.train_score,
                "val_score": best.val_score,
                "hit_rate": best.hit_rate,
                "gain_train_pct": gain_train,
                "gain_val_pct": gain_val,
                "slots": best.slots,
                "op_counts": op_counts,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info("Saved evolved Gen-N genome to %s", out_path)
    return best


if __name__ == "__main__":
    run_shinka_evolve_genn()
