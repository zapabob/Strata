"""Audit the mathematical claims and summarize retained GPU measurements.

Uses only the Python standard library. Run with uv run --no-project --python 3.12.
Bootstrap intervals describe within-run samples, not exclusive-GPU performance.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from pathlib import Path
from typing import Any


def mathematical_checks() -> dict[str, Any]:
    """Construct counterexamples, rather than relying on terminology."""
    beta = 0.5
    # k=e_0, H=I-beta*k*k^T. Nonidentity H is orthogonal only at beta=2.
    orthogonality_error = abs((1.0 - beta) ** 2 - 1.0)
    assert orthogonality_error == 0.75
    assert (1.0 - 2.0) ** 2 == 1.0
    # Orthogonal block rotation preserves each block's norm independently.
    angle = 0.37
    c, s = math.cos(angle), math.sin(angle)
    norms = [math.hypot(c, s), math.hypot(2 * c, 2 * s)]
    assert math.isclose(norms[0], 1.0) and math.isclose(norms[1], 2.0)
    # q=k=e_0: applying R only to k changes the inner product.
    different_rotation_dot = c
    assert not math.isclose(different_rotation_dot, 1.0)
    # k=(e_0+e_8)/sqrt(2): the update couples different 8-wide blocks.
    off_block_entry = -beta / 2
    assert off_block_entry != 0.0
    levels = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0]
    error = abs(0.7 - min(levels, key=lambda x: abs(x - 0.7)))
    assert error > 0.19
    state_per_layer = 128 * 128 * 48 * 4
    return {
        "pass": True,
        "gdn_orthogonality_error_beta_half": orthogonality_error,
        "reflection_requires_beta_times_norm_squared": 2,
        "rotation_preserved_distinct_block_norms": norms,
        "different_rotation_dot_original": 1.0,
        "different_rotation_dot_after": different_rotation_dot,
        "gdn_cross_8_block_entry": off_block_entry,
        "fp4_fixed_scale_counterexample_abs_error": error,
        "fp32_32_elements_bits": 32 * 32,
        "mxfp4_32_elements_plus_scale_bits": 32 * 4 + 8,
        "arbitrary_64_fp32_bits": 64 * 32,
        "28_fp32_coordinates_bits": 28 * 32,
        "state_bytes_per_layer_hv48": state_per_layer,
        "state_bytes_36_layers": state_per_layer * 36,
        "state_bytes_48_layers": state_per_layer * 48,
    }


def followup_checks() -> dict[str, Any]:
    """Conditional roofline arithmetic and constructive rotation counterexamples.

    Real-arithmetic identities are checked with FP64 tolerance here, not claimed
    to be bitwise identities. The FP4 example uses legal E2M1 levels at a fixed
    scale of one; it is not an implementation of adaptive NVFP4/MXFP4 scaling.
    """
    n = 8
    rotation = [
        [(-1.0 if (i & j).bit_count() % 2 else 1.0) / math.sqrt(n)
         for j in range(n)]
        for i in range(n)
    ]

    def dot(a: list[float], b: list[float]) -> float:
        return sum(x * y for x, y in zip(a, b, strict=True))

    def apply(vector: list[float]) -> list[float]:
        return [dot(row, vector) for row in rotation]

    def rotate_state(state: list[list[float]]) -> list[list[float]]:
        columns = list(zip(*state, strict=True))
        return [[dot(row, col) for col in columns] for row in rotation]

    gram_error = max(
        abs(dot(rotation[i], rotation[j]) - (i == j))
        for i in range(n) for j in range(n)
    )
    assert gram_error < 1e-14
    # This order-8 Sylvester Hadamard also has determinant +1: it is in SO(8).
    triangular = [row.copy() for row in rotation]
    determinant = 1.0
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(triangular[row][col]))
        if pivot != col:
            triangular[col], triangular[pivot] = triangular[pivot], triangular[col]
            determinant = -determinant
        diagonal = triangular[col][col]
        assert abs(diagonal) > 1e-14
        determinant *= diagonal
        for row in range(col + 1, n):
            factor = triangular[row][col] / diagonal
            for j in range(col, n):
                triangular[row][j] -= factor * triangular[col][j]
    assert math.isclose(determinant, 1.0, abs_tol=1e-14)

    uniform = [1.0 / math.sqrt(n)] * n
    concentrated = apply(uniform)
    amplification = max(map(abs, concentrated)) / max(map(abs, uniform))
    assert math.isclose(amplification, math.sqrt(n), abs_tol=1e-14)

    q, k = [1.0] + [0.0] * 7, [0.7] + [0.0] * 7
    rq, rk = apply(q), apply(k)
    levels = sorted({sign * value for sign in (-1, 1)
                     for value in (0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0)})

    def quantize(values: list[float]) -> list[float]:
        return [min(levels, key=lambda level: abs(value - level)) for value in values]

    qq, qk = quantize(rq), quantize(rk)
    eq = [a - b for a, b in zip(qq, rq, strict=True)]
    ek = [a - b for a, b in zip(qk, rk, strict=True)]
    exact_dot = dot(q, k)
    rotated_dot = dot(rq, rk)
    quantized_dot = dot(qq, qk)
    expanded_error = dot(rq, ek) + dot(eq, rk) + dot(eq, ek)
    assert math.isclose(exact_dot, rotated_dot, abs_tol=1e-14)
    assert math.isclose(quantized_dot - rotated_dot, expanded_error, abs_tol=1e-14)
    assert abs(quantized_dot - exact_dot) > 0.69

    rng = random.Random(1102)
    state = [[rng.uniform(-1, 1) for _ in range(n)] for _ in range(n)]
    transformed = rotate_state(state)
    max_state_error = max_output_error = 0.0

    def update(matrix: list[list[float]], key: list[float], value: list[float],
               decay: float, beta: float) -> list[list[float]]:
        prediction = [sum(key[i] * matrix[i][j] for i in range(n)) for j in range(n)]
        return [[decay * matrix[i][j] + key[i] * beta * (value[j] - decay * prediction[j])
                 for j in range(n)] for i in range(n)]

    for _ in range(32):
        query = [rng.uniform(-1, 1) for _ in range(n)]
        key = [rng.uniform(-1, 1) for _ in range(n)]
        norm = math.sqrt(dot(key, key))
        key = [value / norm for value in key]
        value = [rng.uniform(-1, 1) for _ in range(n)]
        state = update(state, key, value, 0.97, 0.4)
        transformed = update(transformed, apply(key), value, 0.97, 0.4)
        expected = rotate_state(state)
        max_state_error = max(max_state_error, max(
            abs(transformed[i][j] - expected[i][j]) for i in range(n) for j in range(n)
        ))
        output = [sum(query[i] * state[i][j] for i in range(n)) for j in range(n)]
        rq = apply(query)
        rotated_output = [sum(rq[i] * transformed[i][j] for i in range(n)) for j in range(n)]
        max_output_error = max(max_output_error, max(
            abs(a - b) for a, b in zip(output, rotated_output, strict=True)
        ))
    assert max_state_error < 1e-12 and max_output_error < 1e-12
    logical_bytes = 6 * 1024**2
    peak_bytes_per_second = 448 * 10**9
    conditional_floor_us = logical_bytes / peak_bytes_per_second * 10**6
    return {
        "pass": True,
        "rotation_gram_max_abs_error": gram_error,
        "rotation_determinant": determinant,
        "linf_before": max(map(abs, uniform)),
        "linf_after": max(map(abs, concentrated)),
        "linf_amplification": amplification,
        "exact_dot": exact_dot,
        "rotated_dot": rotated_dot,
        "fixed_scale_fp4_dot": quantized_dot,
        "dot_error_expansion": expanded_error,
        "rotated_gdn_key_axis_32_steps_max_state_error": max_state_error,
        "rotated_gdn_key_axis_32_steps_max_output_error": max_output_error,
        "logical_state_read_write_bytes": logical_bytes,
        "assumed_peak_bytes_per_second": peak_bytes_per_second,
        "conditional_all_dram_floor_us": conditional_floor_us,
        "qualification": "Not measured DRAM traffic, not a proven runtime lower bound. "
                         "Rotation invariance precedes quantization and assumes coordinated state changes.",
    }

def interval(values: list[float], seed: int = 1102) -> list[float]:
    """Deterministic paired bootstrap of the median speed ratio."""
    rng = random.Random(seed)
    draws = sorted(
        statistics.median(rng.choices(values, k=len(values)))
        for _ in range(10000)
    )
    return [draws[249], draws[9749]]


def summarize(path: Path) -> dict[str, Any]:
    records = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    if not records or records[-1] != {"test": "result", "pass": True}:
        raise ValueError(f"Incomplete or failed benchmark: {path}")
    correctness = [r for r in records if r["test"] == "correctness"]
    if len(correctness) != 4 or not all(
        r["bitwise"] and r["graph"] and r["invalid_inputs"] for r in correctness
    ):
        raise ValueError("Missing correctness gates")
    timings = [r for r in records if r["test"] == "timing"]
    groups: dict[tuple[int, str], dict[int, float]] = {}
    for row in timings:
        value = float(row["us_per_layer"])
        if not math.isfinite(value) or value <= 0:
            raise ValueError("Invalid timing")
        key = (int(row["layers"]), row["mode"])
        rounds = groups.setdefault(key, {})
        if row["round"] in rounds:
            raise ValueError("Duplicate timing")
        rounds[row["round"]] = value
    distributions = []
    for (layers, mode), rounds in sorted(groups.items()):
        values = sorted(rounds.values())
        distributions.append({
            "layers": layers, "mode": mode, "n": len(values),
            "median_us": statistics.median(values),
            "min_us": min(values), "max_us": max(values),
            "p10_us": values[int((len(values) - 1) * 0.1)],
            "p90_us": values[int((len(values) - 1) * 0.9)],
        })
    comparisons = []
    for layers in sorted({k[0] for k in groups}):
        for baseline, candidate in [
            ("original_recurrence", "coalesced_recurrence"),
            ("original_separate_norm", "coalesced_separate_norm"),
            ("existing_fused_norm", "coalesced_separate_norm"),
        ]:
            before, after = groups[layers, baseline], groups[layers, candidate]
            if before.keys() != after.keys():
                raise ValueError("Unpaired timing rounds")
            ratios = [before[r] / after[r] for r in sorted(before)]
            comparisons.append({
                "layers": layers, "baseline": baseline, "candidate": candidate,
                "median_paired_speed_ratio": statistics.median(ratios),
                "median_speed_ratio_bootstrap_95pct": interval(ratios),
                "candidate_faster_rounds": sum(x > 1 for x in ratios),
                "rounds": len(ratios),
            })
    return {
        "source": str(path), "device": records[0], "correctness": correctness,
        "distributions": distributions, "comparisons": comparisons,
        "caveat": "Concurrent GPU workload; these are kernel timings, not model throughput.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", nargs="*", type=Path)
    args = parser.parse_args()
    result = {"math": mathematical_checks(), "followup": followup_checks(),
              "runs": [summarize(p) for p in args.results]}
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
