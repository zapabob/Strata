"""Measure a minimum-distortion weight projection in the learnt Hy4 output metric."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path

import numpy as np
from experiment import (
    SEED,
    PrismCodec,
    fetch_weights,
    fit_ternary,
    gated_inputs,
    hadamard,
)

ADAPTER = "model.layers.1.mlp.routed_expert_up_proj.weight"
ADAPTER_SHARD = "model-00144-of-00148.safetensors"
WIDTH = 1536


def load_bf16(path: Path, rows: int) -> np.ndarray:
    bits = np.fromfile(path, dtype="<u2")
    if bits.size != rows * WIDTH:
        raise ValueError(f"Wrong BF16 length for {path.name}")
    return (bits.astype(np.uint32) << 16).view(np.float32).reshape(rows, WIDTH)


def round_bf16(matrix: np.ndarray) -> np.ndarray:
    """Store finite FP32 weights rounded to BF16, ties to even."""
    values = matrix.astype(np.float32, order="C")
    if not np.isfinite(values).all():
        raise ValueError("Non-finite projected weights")
    bits = values.view(np.uint32)
    return ((bits + 0x7FFF + ((bits >> 16) & 1)) >> 16).astype("<u2")


def project(matrix: np.ndarray, axis: np.ndarray, removal: np.ndarray) -> np.ndarray:
    return matrix - np.outer(removal, axis @ matrix)


def score(
    weight: np.ndarray,
    target: np.ndarray,
    adapter: np.ndarray,
    activations: np.ndarray,
    axis: np.ndarray,
) -> dict[str, float]:
    reference = adapter @ (target @ activations)
    change = adapter @ ((weight - target) @ activations)
    return {
        "relative_hidden_output_l2": float(
            np.linalg.norm(change) / np.linalg.norm(reference)
        ),
        "axis_leakage": float(np.linalg.norm(axis @ weight) / np.linalg.norm(weight)),
    }


def evaluate(pilot: Path, codec: PrismCodec, output: Path) -> dict[str, object]:
    base = load_bf16(pilot / "source-expert.bf16", WIDTH).astype(np.float64)
    gate_up = load_bf16(pilot / "gate-up-expert.bf16", 2 * WIDTH)
    axis = np.load(pilot / "synthetic-axis.npy", allow_pickle=False).astype(np.float64)
    signs = np.load(pilot / "activation-signs.npy", allow_pickle=False)
    if (
        axis.shape != (WIDTH,)
        or not np.isfinite(axis).all()
        or not np.linalg.norm(axis)
    ):
        raise ValueError("Invalid experiment axis")
    if signs.shape != (WIDTH,) or not np.all(np.abs(signs) == 1):
        raise ValueError("Invalid activation signs")
    axis /= np.linalg.norm(axis)
    adapter, adapter_bytes, source = fetch_weights(
        ADAPTER, ADAPTER_SHARD, 2 * WIDTH, routed=False
    )
    adapter = adapter.astype(np.float64)
    metric = adapter.T @ adapter
    ridge = 1e-6 * np.trace(metric) / WIDTH
    metric.flat[:: WIDTH + 1] += ridge
    chol = np.linalg.cholesky(metric)
    solution = np.linalg.solve(metric, axis)
    normaliser = float(axis @ solution)
    removal = solution / normaliser
    optimum = project(base, axis, removal)
    orthogonal = project(base, axis, axis)

    latent = (
        np.random.default_rng(SEED + 2).normal(size=(WIDTH, 256)).astype(np.float32)
    )
    activations = gated_inputs(gate_up, latent).astype(np.float64)
    delta = (optimum - base) @ activations
    expected = np.linalg.norm(axis @ (base @ activations)) ** 2 / normaliser
    actual = np.linalg.norm(chol.T @ delta) ** 2
    if not np.isclose(actual, expected, rtol=1e-10):
        raise RuntimeError(
            "The projected weights failed the Cauchy–Schwarz equality check"
        )
    orthogonal_loss = np.linalg.norm(chol.T @ ((orthogonal - base) @ activations)) ** 2
    if actual > orthogonal_loss or np.linalg.norm(axis @ optimum) > 1e-10:
        raise RuntimeError("The projected weights failed the loss or axis check")

    bf16_bits = round_bf16(optimum)
    bf16_weights = (bf16_bits.astype(np.uint32) << 16).view(np.float32)
    payload = codec.encode(fit_ternary(hadamard(optimum.astype(np.float32) * signs)))
    decoded = (hadamard(codec.decode(payload, base.shape)) * signs).astype(np.float64)
    decoded_projected = project(decoded, axis, removal)
    methods = {
        "orthogonal_fp64": orthogonal,
        "metric_optimum_fp64": optimum,
        "metric_fp32_stored": optimum.astype(np.float32),
        "metric_bf16_stored": bf16_weights,
        "metric_pq2_0_stored": decoded,
        "metric_pq2_0_with_exact_runtime_projection": decoded_projected,
    }
    results = {
        name: score(W, base, adapter, activations, axis) for name, W in methods.items()
    }

    left, singular, right = np.linalg.svd(
        chol.T @ (optimum - decoded_projected), full_matrices=False
    )
    corrections = []
    for rank in (16, 32, 64):
        factors = np.linalg.solve(chol.T, left[:, :rank] * singular[:rank]).astype(
            np.float16
        )
        features = right[:rank].astype(np.float16)
        # Correct the finite-precision leakage introduced by storing the factors.
        combined = project(
            decoded + factors.astype(np.float32) @ features.astype(np.float32),
            axis,
            removal,
        )
        common_bytes = payload.nbytes + signs.nbytes + 2 * WIDTH * 4
        bpp = 8 * (common_bytes + factors.nbytes + features.nbytes) / base.size
        corrections.append(
            {
                "rank": rank,
                "effective_bpw_including_side_tensors": bpp,
                **score(combined, base, adapter, activations, axis),
            }
        )
        if rank == 32:
            np.savez(output / "rank32-residual.npz", left=factors, right=features)

    (output / "output-adapter.bf16").write_bytes(adapter_bytes)
    np.save(
        output / "metric-projected-expert.npy",
        optimum.astype(np.float32),
        allow_pickle=False,
    )
    bf16_bits.tofile(output / "metric-projected-expert.bf16")
    payload.tofile(output / "metric-projected-expert.pq2_0")
    np.savez(
        output / "projection.npz",
        axis=axis.astype(np.float32),
        removal=removal.astype(np.float32),
        signs=signs,
    )
    return {
        "scope": "one Hy4 expert and its real output adapter, fixed synthetic axis and latent inputs",
        "adapter_source": source,
        "heldout_vectors": activations.shape[1],
        "ridge": float(ridge),
        "metric_minimum_squared_loss": float(actual),
        "metric_certified_squared_lower_bound": float(expected),
        "metric_orthogonal_squared_loss": float(orthogonal_loss),
        "cases": results,
        "residual_corrections": corrections,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prism-bin", type=Path, required=True)
    parser.add_argument("--gated-pilot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    directory = args.prism_bin.resolve(strict=True)
    with os.add_dll_directory(str(directory)):
        codec = PrismCodec(ctypes.CDLL(str(directory / "ggml-base.dll")))
    args.output.mkdir(parents=True, exist_ok=False)
    report = evaluate(args.gated_pilot, codec, args.output)
    (args.output / "results.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
