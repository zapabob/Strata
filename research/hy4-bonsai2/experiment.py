"""Convert a real Hy4-Flash expert with PrismML's PQ2_0 codec."""

from __future__ import annotations

import argparse
import ctypes
import json
import logging
import math
import os
import re
import struct
import sys
from pathlib import Path

import numpy as np
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.squant import codecs as sq

LOGGER = logging.getLogger(__name__)

REPO = "https://huggingface.co/tencent/Hy4-flash"
TENSOR = "model.layers.1.mlp.experts.down_proj"
SHARD = "model-00100-of-00148.safetensors"
GATE_UP_TENSOR = "model.layers.1.mlp.experts.gate_up_proj"
GATE_UP_SHARD = "model-00023-of-00148.safetensors"
BLOCK = 512
GROUP = 128
PQ2_0 = 142
SEED = 20261125


def read_range(session: requests.Session, url: str, offset: int, size: int) -> bytes:
    """Read an exact, bounded safetensors range and verify its response."""
    if offset < 0 or not 0 < size <= 16 * 1024**2:
        raise ValueError("Invalid byte range")
    stop = offset + size - 1
    headers = {"Range": f"bytes={offset}-{stop}", "Accept-Encoding": "identity"}
    with session.get(url, headers=headers, stream=True, timeout=(10, 35)) as reply:
        content_range = reply.headers.get("Content-Range", "")
        if reply.status_code != 206 or not re.fullmatch(
            rf"bytes {offset}-{stop}/\d+", content_range
        ):
            raise RuntimeError(
                f"The source returned an unexpected range ({reply.status_code})"
            )
        payload = reply.raw.read(size + 1)
        if len(payload) != size:
            raise RuntimeError("Truncated tensor range")
        return payload


def fetch_weights(
    tensor_name: str = TENSOR,
    shard: str = SHARD,
    rows: int = 1536,
    *,
    routed: bool = True,
) -> tuple[np.ndarray, bytes, dict[str, object]]:
    """Read one BF16 matrix without downloading the full shard."""
    with requests.Session() as session:
        with session.get(
            "https://huggingface.co/api/models/tencent/Hy4-flash", timeout=(10, 25)
        ) as metadata:
            if metadata.status_code != 200:
                raise RuntimeError("Model metadata is unavailable")
            revision = metadata.json()["sha"]
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError("Invalid model revision")
        url = f"{REPO}/resolve/{revision}/{shard}"
        (length,) = struct.unpack("<Q", read_range(session, url, 0, 8))
        if not 1 <= length <= 8 * 1024**2:
            raise ValueError("Safetensors header is outside the bound")
        header = json.loads(read_range(session, url, 8, length))
        tensor = header[tensor_name]
        expected_shape = [512, rows, 1536] if routed else [rows, 1536]
        if tensor["dtype"] != "BF16" or tensor["shape"] != expected_shape:
            raise ValueError(
                f"Unexpected expert geometry: {tensor['dtype']} {tensor['shape']}"
            )
        start, end = tensor["data_offsets"]
        if end - start != math.prod(tensor["shape"]) * 2:
            raise ValueError("Bad tensor extent")
        size = rows * 1536 * 2
        raw = read_range(session, url, 8 + length + start, size)
    fp32 = (np.frombuffer(raw, dtype="<u2").astype(np.uint32) << 16).view(np.float32)
    return (
        fp32.reshape(rows, 1536),
        raw,
        {
            "repository": "tencent/Hy4-flash",
            "shard": shard,
            "tensor": tensor_name,
            "expert": 0 if routed else None,
            "dtype": "BF16",
            "shape": [rows, 1536],
            "source_bytes": size,
        },
    )


def hadamard(values: np.ndarray) -> np.ndarray:
    """Transform each contiguous 512 features in the input direction."""
    data = values.astype(np.float32, copy=True).reshape(-1, BLOCK)
    width = 1
    while width < BLOCK:
        pair = data.reshape(len(data), -1, 2, width)
        first = pair[:, :, 0].copy()
        second = pair[:, :, 1].copy()
        pair[:, :, 0] = first + second
        pair[:, :, 1] = first - second
        width *= 2
    return (data / math.sqrt(BLOCK)).reshape(values.shape)


def fit_ternary(
    rotated: np.ndarray, importance: np.ndarray | None = None
) -> np.ndarray:
    """Fit ternary levels before handing the groups to PrismML's packer."""
    groups = rotated.reshape(-1, GROUP)
    order = np.argsort(-np.abs(groups), axis=1, kind="stable")
    ordered_magnitudes = np.take_along_axis(np.abs(groups), order, axis=1)
    count = np.arange(1, GROUP + 1)
    if importance is not None:
        weights = np.broadcast_to(importance, rotated.shape).reshape(groups.shape)
        ordered_weights = np.take_along_axis(weights, order, axis=1)
        ordered_magnitudes *= ordered_weights
        count = np.cumsum(ordered_weights, axis=1, dtype=np.float64)
    weight_sum = np.cumsum(ordered_magnitudes, axis=1, dtype=np.float64)
    grid = (weight_sum / count).astype(np.float16).astype(np.float64)
    score = 2 * grid * weight_sum - count * grid.astype(np.float64) ** 2
    best = score.argmax(axis=1)
    scales = grid[np.arange(len(best)), best]
    support = np.empty_like(order, dtype=np.bool_)
    np.put_along_axis(support, order, np.arange(GROUP) <= best[:, None], axis=1)
    return (
        (np.where(support, np.sign(groups), 0) * scales[:, None])
        .astype(np.float32)
        .reshape(rotated.shape)
    )


def export(library: ctypes.CDLL, name: str, returns: type | None, *args: type):
    func = getattr(library, name)
    func.argtypes = list(args)
    func.restype = returns
    return func


class PrismCodec:
    """Bind the published GGML quantisation and read-back API."""

    def __init__(self, library: ctypes.CDLL):
        pointer, integer, size = ctypes.c_void_p, ctypes.c_int64, ctypes.c_size_t
        self.row_size = export(library, "ggml_row_size", size, ctypes.c_int, integer)
        self.quantise = export(
            library,
            "ggml_quantize_chunk",
            size,
            ctypes.c_int,
            pointer,
            pointer,
            integer,
            integer,
            integer,
            pointer,
        )
        self.validate = export(
            library,
            "ggml_validate_row_data",
            ctypes.c_bool,
            ctypes.c_int,
            pointer,
            size,
        )
        self.dequantise = export(
            library, "dequantize_row_pq2_0", None, pointer, pointer, integer
        )
        name = export(library, "ggml_type_name", ctypes.c_char_p, ctypes.c_int)
        block = export(library, "ggml_blck_size", integer, ctypes.c_int)
        if (name(PQ2_0), block(PQ2_0), self.row_size(PQ2_0, GROUP)) != (
            b"pq2_0",
            GROUP,
            34,
        ):
            raise RuntimeError(
                "The DLL does not provide PrismML PQ2_0 (type 142, 34 bytes per block)"
            )

    def encode(self, weight: np.ndarray) -> np.ndarray:
        matrix = np.ascontiguousarray(weight, dtype=np.float32)
        rows, width = matrix.shape
        if width % GROUP or not np.isfinite(matrix).all():
            raise ValueError("Invalid PQ2_0 input matrix")
        payload = np.empty(rows * self.row_size(PQ2_0, width), dtype=np.uint8)
        written = self.quantise(
            PQ2_0, matrix.ctypes.data, payload.ctypes.data, 0, rows, width, None
        )
        if written != payload.nbytes or not self.validate(
            PQ2_0, payload.ctypes.data, written
        ):
            raise RuntimeError("PrismML rejected the encoded payload")
        return payload

    def decode(self, payload: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
        matrix = np.empty(shape, dtype=np.float32)
        rows, width = shape
        if width % GROUP or payload.nbytes != rows * self.row_size(PQ2_0, width):
            raise ValueError("Invalid PQ2_0 payload extent")
        if not self.validate(PQ2_0, payload.ctypes.data, payload.nbytes):
            raise ValueError("Invalid PQ2_0 payload")
        self.dequantise(payload.ctypes.data, matrix.ctypes.data, matrix.size)
        if not np.isfinite(matrix).all():
            raise ValueError("Non-finite expert weights after read-back")
        return matrix


def remove_axis(weights: np.ndarray, unit: np.ndarray) -> np.ndarray:
    """Return an independent matrix with one output axis removed."""
    return weights - np.outer(unit, unit @ weights)


def score(
    original: np.ndarray, candidate: np.ndarray, inputs: np.ndarray
) -> dict[str, float]:
    """Compare a matrix and its outputs on fixed synthetic activations."""
    reference = original @ inputs
    difference = candidate @ inputs - reference
    return {
        "relative_weight_l2": float(
            np.linalg.norm(candidate - original) / np.linalg.norm(original)
        ),
        "relative_output_l2": float(
            np.linalg.norm(difference) / np.linalg.norm(reference)
        ),
    }


def gated_inputs(gate_up: np.ndarray, latent: np.ndarray) -> np.ndarray:
    """Compute the routed expert's clamped SwiGLU in FP32."""
    gate, up = np.split(gate_up @ latent, 2)
    clipped_gate = np.minimum(gate / (1 + np.exp(-np.clip(gate, -50, 50))), 10)
    return (clipped_gate * np.clip(up, -10, 10)).astype(np.float32)


def gated_trial(weight, signs, codec, directory):
    """Use the real gate/up tensor before held-out synthetic-input scoring."""
    gate_up, gate_bytes, gate_source = fetch_weights(
        GATE_UP_TENSOR, GATE_UP_SHARD, 3072
    )
    rng = np.random.default_rng(SEED + 1)
    calibration = gated_inputs(gate_up, rng.normal(size=(1536, 512)).astype(np.float32))
    train, test = np.split(calibration, 2, axis=1)
    train_rotated = hadamard(train.T * signs)
    importance = np.maximum(np.mean(train_rotated**2, axis=0), 1e-9)
    importance /= importance.mean()
    rotated = hadamard(weight * signs)
    result = {
        "gate_up_source": gate_source,
        "fit_vectors": train.shape[1],
        "holdout_vectors": test.shape[1],
    }
    for name, objective in (("weight_only", None), ("diagonal_activation", importance)):
        packed = codec.encode(fit_ternary(rotated, objective))
        restored = hadamard(codec.decode(packed, weight.shape)) * signs
        result[name] = score(weight, restored, test)
        if objective is not None:
            packed.tofile(directory / "gated-fit-expert.pq2_0")
    packed_s2 = sq.encode_sk(sq.fwht64_np(weight), "S2_K")
    s2 = sq.fwht64_np(sq.decode_sk(packed_s2, "S2_K").reshape(weight.shape))
    result["strata_s2_k"] = score(weight, s2, test)
    (directory / "gate-up-expert.bf16").write_bytes(gate_bytes)
    return result


def main() -> int:
    """Run matched controls and save readable evidence and detached weights."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prism-bin", type=Path, required=True)
    parser.add_argument(
        "--source", type=Path, help="Directory containing saved BF16 and source.json"
    )
    parser.add_argument("--gated-activations", action="store_true")
    args = parser.parse_args()
    if args.source:
        raw = (args.source / "source-expert.bf16").read_bytes()
        source = json.loads((args.source / "source.json").read_text(encoding="utf-8"))
        expected = (TENSOR, 0, "BF16", [1536, 1536], 1536 * 1536 * 2)
        if (
            tuple(
                source[key]
                for key in ("tensor", "expert", "dtype", "shape", "source_bytes")
            )
            != expected
            or len(raw) != expected[-1]
        ):
            raise ValueError(
                "Cached expert does not match the expected Hy4 tensor extent"
            )
        weight = (
            (np.frombuffer(raw, dtype="<u2").astype(np.uint32) << 16)
            .view(np.float32)
            .reshape(1536, 1536)
        )
    else:
        weight, raw, source = fetch_weights()
    with os.add_dll_directory(str(args.prism_bin.resolve(strict=True))):
        codec = PrismCodec(ctypes.CDLL(str(args.prism_bin.resolve() / "ggml-base.dll")))
    rng = np.random.default_rng(SEED)
    signs = rng.choice(np.array([-1, 1], dtype=np.int8), size=weight.shape[1])
    inputs = rng.normal(size=(weight.shape[1], 48)).astype(np.float32)
    unit = rng.normal(size=weight.shape[0]).astype(np.float32)
    unit /= np.linalg.norm(unit)
    projected = remove_axis(weight, unit)
    round_trip = hadamard(hadamard(weight * signs)) * signs
    if not np.allclose(weight, round_trip, atol=2e-6):
        raise ValueError("Signed transform round trip failed")

    codecs = {}
    sk_input = sq.fwht64_np(weight)
    for name in ("S1.5", "S2_K", "S3_K", "S4_K"):
        payload = sq.encode_sk(sk_input, name)
        restored = sq.fwht64_np(sq.decode_sk(payload, name).reshape(weight.shape))
        codecs[name] = {
            "bits_per_weight": 8 * len(payload) / weight.size,
            **score(weight, restored, inputs),
        }
    plain = codec.decode(codec.encode(weight), weight.shape)
    rotated = hadamard(weight * signs)
    direct_packed = codec.encode(rotated)
    rotated_native = hadamard(codec.decode(direct_packed, weight.shape)) * signs
    fitted = fit_ternary(rotated)
    baseline = codec.encode(fitted)
    if not np.array_equal(codec.decode(baseline, weight.shape), fitted):
        raise RuntimeError("PrismML did not exactly preserve pre-fitted ternary values")
    restored = hadamard(fitted) * signs
    packed_projection = codec.encode(fit_ternary(hadamard(projected * signs)))
    projected_quant = hadamard(codec.decode(packed_projection, weight.shape)) * signs
    rotated_input = hadamard(inputs.T * signs)
    transformed_output = (rotated_input @ fitted.T).T
    if not np.allclose(transformed_output, restored @ inputs, rtol=1e-4, atol=5e-6):
        raise RuntimeError("Weight rotation did not match activation-side rotation")
    corrected = remove_axis(projected_quant, unit)
    projected_leak = np.linalg.norm(unit @ projected) / np.linalg.norm(projected)
    requant_leak = np.linalg.norm(unit @ projected_quant) / np.linalg.norm(
        projected_quant
    )
    correction_leak = np.linalg.norm(unit @ corrected) / np.linalg.norm(corrected)
    if max(projected_leak, correction_leak) >= 1e-6:
        raise ValueError("Rank-one removal failed")
    if not np.allclose(remove_axis(projected, unit), projected, atol=1e-7):
        raise ValueError("Rank-one removal is not numerically idempotent")

    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "source-expert.bf16").write_bytes(raw)
    (args.output / "source.json").write_text(
        json.dumps(source, indent=2) + "\n", encoding="utf-8"
    )
    baseline.tofile(args.output / "expert.pq2_0")
    packed_projection.tofile(args.output / "directly-projected-expert.pq2_0")
    np.save(args.output / "activation-signs.npy", signs, allow_pickle=False)
    np.save(args.output / "synthetic-axis.npy", unit, allow_pickle=False)
    np.save(
        args.output / "directly-projected-expert.npy", projected, allow_pickle=False
    )
    disk_payload = np.fromfile(
        args.output / "directly-projected-expert.pq2_0", dtype=np.uint8
    )
    if not np.array_equal(disk_payload, packed_projection):
        raise RuntimeError("Saved payload disagrees with the original PQ2_0 bytes")
    report = {
        "source": source,
        "seed": SEED,
        "activation_columns": inputs.shape[1],
        "basis_block": BLOCK,
        "scale_group": GROUP,
        "codec_reference": "S_K codecs with their H64 transform and no activation calibration",
        "native_codec_controls": codecs,
        "prism_type": "PQ2_0",
        "prism_ggml_type_id": PQ2_0,
        "prism_payload_bytes": baseline.nbytes,
        "prism_bits_per_weight": 8 * baseline.nbytes / weight.size,
        "prism_unrotated": score(weight, plain, inputs),
        "prism_signed_h512": score(weight, rotated_native, inputs),
        "prism_signed_h512_with_ternary_fit": score(weight, restored, inputs),
        "direct_projection": score(weight, projected, inputs),
        "pq2_0_after_projection_vs_projected": score(
            projected, projected_quant, inputs
        ),
        "pq2_0_with_post_decode_correction_vs_projected": score(
            projected, corrected, inputs
        ),
        "axis_leakage": {
            "direct_projection": float(projected_leak),
            "after_pq2_0": float(requant_leak),
            "after_post_decode_correction": float(correction_leak),
        },
        "scope": "one real routed expert down matrix, synthetic inputs and output axis",
    }
    if args.gated_activations:
        report["gated_activation_pilot"] = gated_trial(
            weight, signs, codec, args.output
        )
    (args.output / "results.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    LOGGER.info("Hy4-Flash PrismML PQ2_0 pilot completed")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
