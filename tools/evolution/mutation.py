"""Evolutionary mutation operators including non-commutative operator-order swaps (Sections 10-11)."""

from __future__ import annotations

import random
from typing import Sequence

from .genome import DEFAULT_OPERATOR_SEQUENCE, InferenceGenome, VALID_CACHE_POLICIES

MUTATION_OPERATORS: tuple[str, ...] = (
    "local_gaussian",
    "discrete_knob",
    "global_explore",
    "crossover",
    "noncommutative_order_swap",
)

_ALLOWED_IO_CHUNKS = (65536, 131072, 262144, 524288, 1048576, 2097152)


def _clamp_int(val: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, int(val)))


def _clamp_float(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(val)))


def apply_mutation(
    operator_name: str,
    parent: InferenceGenome,
    *,
    mate: InferenceGenome | None,
    rng: random.Random,
    max_gpu_budget_bytes: int,
    max_ram_budget_bytes: int,
) -> InferenceGenome:
    """Generate one candidate child genome under `operator_name`."""
    min_gpu = min(4 * 1024 * 1024, max_gpu_budget_bytes)
    if operator_name == "local_gaussian":
        return InferenceGenome(
            gpu_cache_budget_bytes=_clamp_int(
                int(round(parent.gpu_cache_budget_bytes * (1.0 + rng.gauss(0.0, 0.08)))),
                min_gpu,
                max_gpu_budget_bytes,
            ),
            ram_cache_budget_bytes=_clamp_int(
                int(round(parent.ram_cache_budget_bytes * (1.0 + rng.gauss(0.0, 0.10)))),
                0,
                max_ram_budget_bytes,
            ),
            cache_decay=_clamp_float(parent.cache_decay + rng.gauss(0.0, 0.015), 0.55, 0.999),
            eviction_hysteresis=_clamp_float(parent.eviction_hysteresis + rng.gauss(0.0, 0.15), 0.0, 3.5),
            prefetch_depth=_clamp_int(parent.prefetch_depth + rng.choice((-1, 0, 1)), 0, 6),
            prefetch_threshold=_clamp_float(parent.prefetch_threshold + rng.gauss(0.0, 0.08), 0.05, 0.95),
            prefetch_queue_size=_clamp_int(parent.prefetch_queue_size + rng.choice((-1, 0, 1)), 1, 12),
            io_chunk_bytes=parent.io_chunk_bytes,
            staging_buffers=parent.staging_buffers,
            cache_policy=parent.cache_policy,
            operator_sequence=parent.operator_sequence,
        )

    if operator_name == "discrete_knob":
        return InferenceGenome(
            gpu_cache_budget_bytes=parent.gpu_cache_budget_bytes,
            ram_cache_budget_bytes=parent.ram_cache_budget_bytes,
            cache_decay=parent.cache_decay,
            eviction_hysteresis=parent.eviction_hysteresis,
            prefetch_depth=rng.randint(0, 5),
            prefetch_threshold=parent.prefetch_threshold,
            prefetch_queue_size=rng.randint(1, 10),
            io_chunk_bytes=rng.choice(_ALLOWED_IO_CHUNKS),
            staging_buffers=rng.choice((2, 3, 4)),
            cache_policy=rng.choice(VALID_CACHE_POLICIES),
            operator_sequence=parent.operator_sequence,
        )

    if operator_name == "global_explore":
        seq = list(DEFAULT_OPERATOR_SEQUENCE)
        rng.shuffle(seq)
        return InferenceGenome(
            gpu_cache_budget_bytes=rng.randint(min_gpu, max_gpu_budget_bytes),
            ram_cache_budget_bytes=rng.randint(0, max(0, max_ram_budget_bytes)),
            cache_decay=round(rng.uniform(0.65, 0.995), 4),
            eviction_hysteresis=round(rng.uniform(0.0, 2.5), 4),
            prefetch_depth=rng.randint(0, 5),
            prefetch_threshold=round(rng.uniform(0.10, 0.85), 4),
            prefetch_queue_size=rng.randint(1, 10),
            io_chunk_bytes=rng.choice(_ALLOWED_IO_CHUNKS),
            staging_buffers=rng.choice((2, 3)),
            cache_policy=rng.choice(VALID_CACHE_POLICIES),
            operator_sequence=tuple(seq),
        )

    if operator_name == "crossover":
        other = mate or parent
        w = rng.uniform(0.25, 0.75)
        return InferenceGenome(
            gpu_cache_budget_bytes=_clamp_int(
                int(round(w * parent.gpu_cache_budget_bytes + (1.0 - w) * other.gpu_cache_budget_bytes)),
                min_gpu,
                max_gpu_budget_bytes,
            ),
            ram_cache_budget_bytes=_clamp_int(
                int(round(w * parent.ram_cache_budget_bytes + (1.0 - w) * other.ram_cache_budget_bytes)),
                0,
                max_ram_budget_bytes,
            ),
            cache_decay=_clamp_float(w * parent.cache_decay + (1.0 - w) * other.cache_decay, 0.55, 0.999),
            eviction_hysteresis=_clamp_float(
                w * parent.eviction_hysteresis + (1.0 - w) * other.eviction_hysteresis, 0.0, 3.5
            ),
            prefetch_depth=rng.choice((parent.prefetch_depth, other.prefetch_depth)),
            prefetch_threshold=_clamp_float(
                w * parent.prefetch_threshold + (1.0 - w) * other.prefetch_threshold, 0.05, 0.95
            ),
            prefetch_queue_size=rng.choice((parent.prefetch_queue_size, other.prefetch_queue_size)),
            io_chunk_bytes=rng.choice((parent.io_chunk_bytes, other.io_chunk_bytes)),
            staging_buffers=rng.choice((parent.staging_buffers, other.staging_buffers)),
            cache_policy=rng.choice((parent.cache_policy, other.cache_policy)),
            operator_sequence=parent.operator_sequence,
        )

    if operator_name == "noncommutative_order_swap":
        seq = list(parent.operator_sequence)
        i, j = rng.sample(range(len(seq)), 2)
        seq[i], seq[j] = seq[j], seq[i]
        return InferenceGenome(
            gpu_cache_budget_bytes=parent.gpu_cache_budget_bytes,
            ram_cache_budget_bytes=parent.ram_cache_budget_bytes,
            cache_decay=parent.cache_decay,
            eviction_hysteresis=parent.eviction_hysteresis,
            prefetch_depth=parent.prefetch_depth,
            prefetch_threshold=parent.prefetch_threshold,
            prefetch_queue_size=parent.prefetch_queue_size,
            io_chunk_bytes=parent.io_chunk_bytes,
            staging_buffers=parent.staging_buffers,
            cache_policy=parent.cache_policy,
            operator_sequence=tuple(seq),
        )

    raise ValueError(f"Unsupported mutation operator: {operator_name!r}")
