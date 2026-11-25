"""Test paired Spin(8) vector and half-spinor bases for PrismML PQ2_0."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path

import numpy as np
from ablation import WIDTH, load_bf16, project
from experiment import SEED, PrismCodec, fit_ternary, gated_inputs, hadamard

DIM = 8
EYE = np.eye(DIM)
FANO = ((1, 2, 3), (1, 4, 5), (1, 7, 6), (2, 4, 6), (2, 5, 7), (3, 4, 7), (3, 6, 5))


def left_basis() -> np.ndarray:
    """Integer matrices for octonion left-multiplication on the standard basis."""
    left = np.zeros((DIM, DIM, DIM), dtype=np.int64)
    left[0] = EYE
    for i in range(1, DIM):
        left[i, i, 0] = 1
        left[i, 0, i] = -1
    for a, b, c in FANO:
        for i, j, k in ((a, b, c), (b, c, a), (c, a, b)):
            left[i, k, j] = 1
            left[j, k, i] = -1
    zero = np.zeros((DIM, DIM), dtype=np.int64)
    gamma = [np.block([[zero, L.T], [L, zero]]) for L in left]
    for i in range(DIM):
        for j in range(DIM):
            expected = 2 * int(i == j) * np.eye(2 * DIM, dtype=np.int64)
            if not np.array_equal(gamma[i] @ gamma[j] + gamma[j] @ gamma[i], expected):
                raise RuntimeError("The octonion Clifford table does not anticommute")
    return left


def build_rotors(
    axis: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    """Align each vector block using two reflections and lift both spinor actions."""
    left = left_basis()
    unit_blocks = axis.reshape(-1, DIM)
    norms = np.linalg.norm(unit_blocks, axis=1, keepdims=True)
    normal = np.divide(
        unit_blocks, norms, out=np.tile(EYE[0], (len(norms), 1)), where=norms > 0
    )
    second = normal - EYE[0]
    second_norm = np.linalg.norm(second, axis=1, keepdims=True)
    first = EYE[1]
    second = np.divide(
        second,
        second_norm,
        out=np.tile(first, (len(norms), 1)),
        where=second_norm > 1e-14,
    )
    reflect_first = EYE - 2 * np.outer(first, first)
    reflect_second = EYE - 2 * second[:, :, None] * second[:, None, :]
    vector = reflect_first @ reflect_second
    left_second = np.einsum("ni,ijk->njk", second, left)
    positive = left[1].T @ left_second
    negative = left[1] @ left_second.swapaxes(-2, -1)
    rotated_left = np.einsum("nki,kab->niab", vector, left)
    defect = float(
        np.max(np.abs(rotated_left @ positive[:, None] - negative[:, None] @ left))
    )
    for representation in (vector, positive, negative):
        orthogonal = representation @ representation.swapaxes(-2, -1)
        if not np.allclose(orthogonal, EYE, atol=1e-12) or not np.allclose(
            np.linalg.det(representation), 1
        ):
            raise RuntimeError("A Spin(8) representation failed its orientation check")
    if defect > 1e-12:
        raise RuntimeError("The octonion multiplication intertwiner failed")
    return vector, positive, negative, second, defect


def left_blocks(rotation: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Apply batched eight-dimensional matrices to consecutive feature rows."""
    return (rotation @ matrix.reshape(-1, DIM, matrix.shape[-1])).reshape(matrix.shape)


def loss(
    matrix: np.ndarray, base: np.ndarray, adapter: np.ndarray, x: np.ndarray
) -> float:
    return float(
        np.linalg.norm(adapter @ ((matrix - base) @ x))
        / np.linalg.norm(adapter @ (base @ x))
    )


def evaluate(weights: Path, metric: Path, output: Path, codec: PrismCodec) -> dict:
    original = load_bf16(weights / "source-expert.bf16", WIDTH).astype(np.float64)
    gates = load_bf16(weights / "gate-up-expert.bf16", 2 * WIDTH)
    adapter = load_bf16(metric / "output-adapter.bf16", 2 * WIDTH).astype(np.float64)
    projected = np.load(
        metric / "metric-projected-expert.npy", allow_pickle=False
    ).astype(np.float64)
    with np.load(metric / "projection.npz", allow_pickle=False) as saved:
        axis = saved["axis"].astype(np.float64)
        removal = saved["removal"].astype(np.float64)
        signs = saved["signs"]
    if (
        axis.shape != (WIDTH,)
        or removal.shape != axis.shape
        or np.isclose(axis @ removal, 0)
    ):
        raise ValueError("Invalid axis or output metric")
    if signs.shape != (WIDTH,) or not np.all(np.abs(signs) == 1):
        raise ValueError("Invalid activation signs")
    removal /= axis @ removal
    vector, positive, negative, second, defect = build_rotors(axis)
    rotated_axis = left_blocks(vector, axis[:, None]).reshape(-1, DIM)
    off_axis = float(np.max(np.abs(rotated_axis[:, 1:])))
    if off_axis > 1e-12:
        raise RuntimeError("The vector action did not localise the specified axis")
    same = np.broadcast_to(EYE, vector.shape)
    undo_vector = vector.swapaxes(-2, -1)

    latent = (
        np.random.default_rng(SEED + 3).normal(size=(WIDTH, 512)).astype(np.float32)
    )
    train, test = np.split(gated_inputs(gates, latent).astype(np.float64), 2, axis=1)
    pq_base = np.fromfile(metric / "metric-projected-expert.pq2_0", dtype=np.uint8)
    native = project(
        hadamard(codec.decode(pq_base, original.shape)) * signs, axis, removal
    )
    base_holdout_loss = loss(native, original, adapter, test)
    cases = []
    winner = None
    best_loss = float("inf")

    for label, in_rotation in (
        ("vector_only", same),
        ("half_spin_plus", positive),
        ("half_spin_minus", negative),
    ):
        undo_input = in_rotation.swapaxes(-2, -1)
        spin_weight = left_blocks(in_rotation, left_blocks(vector, projected).T).T
        exact = left_blocks(undo_vector, left_blocks(undo_input, spin_weight.T).T)
        if np.max(np.abs(exact - projected)) > 1e-12:
            raise RuntimeError(
                "The triality change of basis altered the unquantised map"
            )
        for h512 in (False, True):
            source = spin_weight.astype(np.float32)
            if h512:
                source = hadamard(source * signs)
            packed = codec.encode(fit_ternary(source))
            raw = codec.decode(packed, original.shape)
            if h512:
                raw = hadamard(raw) * signs
            decoded = left_blocks(undo_vector, left_blocks(undo_input, raw.T).T)
            final = project(decoded, axis, removal)
            entry = {
                "basis": label,
                "signed_h512": h512,
                "selection_error": loss(final, original, adapter, train),
                "holdout_error": loss(final, original, adapter, test),
                "unprojected_axis_leakage": float(
                    np.linalg.norm(axis @ decoded) / np.linalg.norm(decoded)
                ),
                "projected_axis_leakage": float(
                    np.linalg.norm(axis @ final) / np.linalg.norm(final)
                ),
            }
            cases.append(entry)
            if label != "vector_only" and entry["selection_error"] < best_loss:
                best_loss = entry["selection_error"]
                winner = (packed, entry)

    if winner is None:
        raise RuntimeError("No triality candidate completed")
    packed, entry = winner
    packed.tofile(output / "triality-expert.pq2_0")
    np.save(
        output / "rotor-second-unit-vector.npy",
        second.astype(np.float32),
        allow_pickle=False,
    )
    bytes_with_side_data = packed.nbytes + second.size * 4 + axis.size * 8
    if entry["signed_h512"]:
        bytes_with_side_data += signs.nbytes
    return {
        "scope": "one real Hy4 expert, real BF16 gate and output adapter, synthetic axis and latent vectors",
        "clifford_anticommutator_exact_integer_check": True,
        "max_triality_intertwiner_defect": defect,
        "max_rotated_off_axis_component": off_axis,
        "axis_nonzeros_before": int(np.count_nonzero(np.abs(axis) > 1e-12)),
        "axis_nonzeros_after": int(np.count_nonzero(np.abs(rotated_axis) > 1e-12)),
        "reference_h512_holdout_error": base_holdout_loss,
        "selection_vectors": train.shape[1],
        "holdout_vectors": test.shape[1],
        "cases": cases,
        "selected": entry,
        "selected_effective_bpw_including_side_data": bytes_with_side_data
        * 8
        / original.size,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prism-bin", type=Path, required=True)
    parser.add_argument("--gated-pilot", type=Path, required=True)
    parser.add_argument("--metric-pilot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    directory = args.prism_bin.resolve(strict=True)
    with os.add_dll_directory(str(directory)):
        codec = PrismCodec(ctypes.CDLL(str(directory / "ggml-base.dll")))
    args.output.mkdir(parents=True, exist_ok=False)
    results = evaluate(args.gated_pilot, args.metric_pilot, args.output, codec)
    (args.output / "results.json").write_text(
        json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
