"""URT information geometry, binary KL, DPI, Pinsker bounds, and sequence KL (Section 5).

Explicitly distinguishes four KL quantities and never treats top-k renormalised KL or
single-prefix empirical KL as a certified sequence-level upper bound over all generation
trajectories:
- `empirical_topk_kl`
- `empirical_full_vocab_kl`
- `estimated_sequence_kl`
- `certified_sequence_kl_upper_bound`
"""

from __future__ import annotations

import math
from pathlib import Path
import struct
from typing import Any, Literal, Sequence

from .math_foundations import (
    fisher_kl_quadratic,
    full_vocab_kl,
    range_kl_upper_bound,
    topk_renormalized_kl,
)

KLKind = Literal[
    "empirical_topk_kl",
    "empirical_full_vocab_kl",
    "estimated_sequence_kl",
    "certified_sequence_kl_upper_bound",
]

VALID_KL_KINDS = frozenset(
    {
        "empirical_topk_kl",
        "empirical_full_vocab_kl",
        "estimated_sequence_kl",
        "certified_sequence_kl_upper_bound",
    }
)


def binary_kl(p: float, q: float) -> float:
    """Exact Bernoulli KL divergence d_bin(p || q) in nats."""
    if not (0.0 <= p <= 1.0 and 0.0 <= q <= 1.0):
        raise ValueError(f"Probabilities must lie in [0, 1]: p={p}, q={q}")
    total = 0.0
    if p > 0.0:
        if q <= 0.0:
            return float("inf")
        total += p * math.log(p / q)
    if p < 1.0:
        if q >= 1.0:
            return float("inf")
        total += (1.0 - p) * math.log((1.0 - p) / (1.0 - q))
    return max(0.0, total)


def nats_to_bits(nats: float) -> float:
    """Convert natural-log information units (nats) to base-2 bits."""
    return nats / math.log(2.0)


def pinsker_success_lower_bound(p_ref: float, kl_nats: float) -> float:
    """Pinsker lower bound p_Q >= max(0, p_R - sqrt(KL(P_R || P_Q) / 2))."""
    if not (0.0 <= p_ref <= 1.0):
        raise ValueError(f"p_ref must lie in [0, 1]: {p_ref}")
    if kl_nats < 0.0:
        raise ValueError(f"kl_nats must be non-negative: {kl_nats}")
    if not math.isfinite(kl_nats):
        return 0.0
    return max(0.0, p_ref - math.sqrt(kl_nats / 2.0))


def dpi_consistency_check(p_ref: float, p_quant: float, kl_nats: float) -> dict[str, Any]:
    """Verify Data Processing Inequality: KL(P_R || P_Q) >= binary_KL(p_R || p_Q)."""
    bkl = binary_kl(p_ref, p_quant)
    holds = kl_nats + 1e-12 >= bkl
    return {
        "p_ref": p_ref,
        "p_quant": p_quant,
        "kl_nats": kl_nats,
        "binary_kl_nats": bkl,
        "pinsker_p_quant_lower": pinsker_success_lower_bound(p_ref, kl_nats),
        "dpi_satisfied": holds,
    }


def sequence_kl_chain_rule(
    per_step_ref_logits: Sequence[Sequence[float]],
    per_step_quant_logits: Sequence[Sequence[float]],
    *,
    top_k: int = 64,
) -> dict[str, Any]:
    """Evaluate per-step and summed KL metrics along a shared teacher-forced prefix.

    Records empirical full-vocab KL, Fisher quadratic approximation, range upper bound
    sum(r_t^2 / 8), and top-k renormalised KL as strictly distinct fields. Note that a
    single fixed prefix does NOT certify all diverging autoregressive generation branches.
    """
    if len(per_step_ref_logits) != len(per_step_quant_logits) or not per_step_ref_logits:
        raise ValueError("Reference and quantised logit sequences must have equal non-zero length")

    step_full: list[float] = []
    step_topk: list[float] = []
    step_fisher: list[float] = []
    step_range_ub: list[float] = []
    step_spans: list[float] = []

    for z_ref, z_q in zip(per_step_ref_logits, per_step_quant_logits, strict=True):
        if len(z_ref) != len(z_q) or not z_ref:
            raise ValueError("Every step must have equal non-zero vocabulary size")
        step_full.append(full_vocab_kl(z_ref, z_q))
        step_topk.append(topk_renormalized_kl(z_ref, z_q, top_k=top_k))
        step_fisher.append(fisher_kl_quadratic(z_ref, z_q))
        ub = range_kl_upper_bound(z_ref, z_q)
        step_range_ub.append(ub)
        dz = [q - r for r, q in zip(z_ref, z_q, strict=True)]
        step_spans.append(max(dz) - min(dz))

    sum_full = sum(step_full)
    sum_topk = sum(step_topk)
    sum_fisher = sum(step_fisher)
    sum_range = sum(step_range_ub)
    return {
        "num_steps": len(per_step_ref_logits),
        "vocab_size": len(per_step_ref_logits[0]),
        "top_k": min(top_k, len(per_step_ref_logits[0])),
        "empirical_full_vocab_kl": sum_full,
        "empirical_topk_kl": sum_topk,
        "estimated_sequence_kl_fisher": sum_fisher,
        "shared_prefix_range_upper_bound": sum_range,
        "per_step_spans": step_spans,
        "all_steps_within_range_bound": all(
            f <= u + 1e-12 for f, u in zip(step_full, step_range_ub, strict=True)
        ),
        "scope_warning": (
            "Summed along one shared prefix only; does not constitute a "
            "certified_sequence_kl_upper_bound over all diverging autoregressive paths."
        ),
    }


def read_strata_logits_dump(path: Path) -> list[dict[str, Any]]:
    """Read Strata's native full-vocab float32 `LOGS` binary dump (`STRATA_LOGITS_DUMP`).

    Compatible with `terminal/tools/logits_dump.py` without duplicating C++ paths.
    """
    records: list[dict[str, Any]] = []
    with path.open("rb") as fh:
        while True:
            hdr = fh.read(16)
            if not hdr:
                break
            if len(hdr) < 16:
                raise ValueError(f"Truncated LOGS header in {path}")
            magic, step, token_id, vocab = struct.unpack("<4siii", hdr)
            if magic != b"LOGS":
                raise ValueError(f"Invalid LOGS magic {magic!r} in {path}")
            raw_vals = fh.read(vocab * 4)
            if len(raw_vals) != vocab * 4:
                raise ValueError(f"Truncated LOGS payload at step {step} in {path}")
            logits = list(struct.unpack(f"<{vocab}f", raw_vals))
            records.append({"step": step, "token_id": token_id, "vocab": vocab, "logits": logits})
    return records


def compare_logits_dump_files(ref_path: Path, quant_path: Path, *, top_k: int = 64) -> dict[str, Any]:
    """Compare two native `STRATA_LOGITS_DUMP` full-vocabulary files via chain-rule KL."""
    ref_recs = read_strata_logits_dump(ref_path)
    quant_recs = read_strata_logits_dump(quant_path)
    n = min(len(ref_recs), len(quant_recs))
    if n == 0:
        raise ValueError("One or both LOGS dump files contain zero records")
    return sequence_kl_chain_rule(
        [r["logits"] for r in ref_recs[:n]],
        [q["logits"] for q in quant_recs[:n]],
        top_k=top_k,
    )
