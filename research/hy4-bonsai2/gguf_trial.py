"""Write and benchmark a GGUF containing real Hy4 expert weight specimens."""

from __future__ import annotations

import argparse
import ctypes
import importlib
import json
import os
import sys
from pathlib import Path

import numpy as np
from ablation import load_bf16
from experiment import PQ2_0, SEED, PrismCodec, gated_inputs, hadamard
from routed_bench import BF16, TOP_K, open_backend, relative_error, run_graph
from triality import WIDTH, build_rotors, left_blocks

ARCH = "hy_v4_flash"
QUALITY = "experiment.triality"
MAIN = "blk.1.ffn_down_exps.weight"
REFERENCE = "experiment.reference.ffn_down_exps.weight"
CONTROL = "experiment.h512.ffn_down_exps.weight"
AXIS = f"{QUALITY}.axis"
REMOVAL = f"{QUALITY}.removal"
SIGNS = f"{QUALITY}.signs"
SHAPE = (1, WIDTH, WIDTH)
ROW_BYTES = WIDTH // 128 * 34


def write_gguf(gguf, path: Path, gated: Path, metric: Path, triality: Path) -> None:
    if path.exists():
        raise FileExistsError(path)
    metadata = json.loads((triality / "results.json").read_text(encoding="utf-8"))
    selected = metadata["selected"]
    bf16 = np.fromfile(gated / "source-expert.bf16", dtype="<u2").reshape(SHAPE)
    reference = np.fromfile(metric / "metric-projected-expert.pq2_0", dtype=np.uint8)
    reference = reference.reshape(1, WIDTH, ROW_BYTES)
    primary = np.fromfile(triality / "triality-expert.pq2_0", dtype=np.uint8)
    primary = primary.reshape(1, WIDTH, ROW_BYTES)
    with np.load(metric / "projection.npz", allow_pickle=False) as projection:
        axis, removal, signs = (projection[key] for key in ("axis", "removal", "signs"))

    writer = gguf.GGUFWriter(path, ARCH)
    try:
        writer.add_type("tensor-fixture")
        writer.add_name("Hy4-Bonsai2 expert PQ2_0 pilot")
        writer.add_string("experiment.source", "tencent/Hy4-flash")
        writer.add_string("experiment.scope", "layer 1, expert 0, down-projection only")
        writer.add_string(f"{QUALITY}.branch", selected["basis"])
        writer.add_bool(f"{QUALITY}.signed_h512", selected["signed_h512"])
        writer.add_uint32(f"{QUALITY}.block_size", 8)
        writer.add_uint32(f"{QUALITY}.axis_retained_coordinate", 0)
        writer.add_uint32(f"{QUALITY}.first_reflection_coordinate", 1)
        writer.add_tensor(MAIN, primary, raw_dtype=gguf.GGMLQuantizationType.PQ2_0)
        writer.add_tensor(CONTROL, reference, raw_dtype=gguf.GGMLQuantizationType.PQ2_0)
        writer.add_tensor(REFERENCE, bf16, raw_dtype=gguf.GGMLQuantizationType.BF16)
        for name, data in ((AXIS, axis), (REMOVAL, removal), (SIGNS, signs)):
            writer.add_tensor(name, data)
        writer.write_header_to_file()
        writer.write_kv_data_to_file()
        writer.write_tensors_to_file()
    finally:
        writer.close()

    loaded = {tensor.name: tensor for tensor in gguf.GGUFReader(path).tensors}
    for name, data in ((MAIN, primary), (CONTROL, reference), (REFERENCE, bf16)):
        if not np.array_equal(
            loaded[name].data.view(np.uint8).reshape(-1),
            data.view(np.uint8).reshape(-1),
        ):
            raise RuntimeError(f"GGUF sample differs from the source payload: {name}")


def bench(gguf, file: Path, prism_bin: Path, kind: str, destination: Path) -> None:
    reader = gguf.GGUFReader(file)
    if reader.fields["general.type"].contents() != "tensor-fixture":
        raise ValueError("This benchmark expects the detached expert fixture")
    if "experiment.stored_expert_count" in reader.fields:
        bench_streamed_bank(reader, prism_bin, kind, destination)
        return
    tensors = {tensor.name: tensor for tensor in reader.tensors}
    for name, expected in ((MAIN, PQ2_0), (CONTROL, PQ2_0), (REFERENCE, BF16)):
        if (
            int(tensors[name].tensor_type) != expected
            or tuple(tensors[name].shape) != SHAPE[::-1]
        ):
            raise ValueError(f"Unexpected GGUF shape or GGML type for {name}")
    case = reader.fields[f"{QUALITY}.branch"].contents()
    h512 = reader.fields[f"{QUALITY}.signed_h512"].contents()
    axis = np.ascontiguousarray(tensors[AXIS].data, dtype=np.float32)
    removal = np.ascontiguousarray(tensors[REMOVAL].data, dtype=np.float32)
    removal = removal / (axis @ removal)
    signs = np.ascontiguousarray(tensors[SIGNS].data, dtype=np.float32)
    vector, plus, minus, _, _ = build_rotors(axis.astype(np.float64))
    in_rotation = {"half_spin_plus": plus, "half_spin_minus": minus}[case]
    reverse_output = vector.swapaxes(-1, -2)
    rotation = tuple(
        np.ascontiguousarray(matrix, dtype=np.float32)
        for matrix in (in_rotation, reverse_output)
    )
    payloads = {
        name: tensors[name].data.view(np.uint8).reshape(-1)
        for name in (MAIN, CONTROL, REFERENCE)
    }
    banks = {name: np.tile(raw, TOP_K) for name, raw in payloads.items()}
    results = []
    with open_backend(prism_bin, kind) as (library, backend, backend_name):
        codec = PrismCodec(library)
        bf16_bits = payloads[REFERENCE].view("<u2").astype(np.uint32)
        bf16 = (bf16_bits << 16).view(np.float32).reshape(WIDTH, WIDTH)
        decoded_h512 = hadamard(codec.decode(payloads[CONTROL], bf16.shape)) * signs
        main = codec.decode(payloads[MAIN], bf16.shape)
        if h512:
            main = hadamard(main) * signs
        main = left_blocks(
            reverse_output, left_blocks(in_rotation.swapaxes(-1, -2), main.T).T
        )

        rng = np.random.default_rng(SEED + 4)
        for tokens in (1, 16):
            values = rng.normal(size=(tokens, TOP_K, WIDTH)).astype(np.float32)
            ids = np.stack([rng.permutation(TOP_K) for _ in range(tokens)]).astype(
                np.int32
            )
            reference, bf16_ms = run_graph(
                library, backend, BF16, banks[REFERENCE], values, ids, None
            )
            result = {
                "tokens": tokens,
                "routed_slots": TOP_K,
                "bf16_median_ms": bf16_ms,
                "bf16_arithmetic_relative_l2": relative_error(
                    reference, values @ bf16.T
                ),
            }
            for tag, tensor, matrix, transform, input_sign in (
                ("h512", CONTROL, decoded_h512, None, signs),
                ("spin8", MAIN, main, rotation, signs if h512 else None),
            ):
                output, timing = run_graph(
                    library,
                    backend,
                    PQ2_0,
                    banks[tensor],
                    values,
                    ids,
                    input_sign,
                    spin=transform,
                    projection=(axis, removal),
                )
                manual = values @ matrix.T
                manual -= (manual @ axis)[..., None] * removal
                arithmetic = relative_error(output, manual)
                leakage = float(np.linalg.norm(output @ axis) / np.linalg.norm(output))
                if not np.isfinite(arithmetic) or arithmetic > 0.03 or leakage > 1e-6:
                    raise RuntimeError(
                        f"The {tag} graph failed arithmetic or axis validation"
                    )
                result[tag] = {
                    "median_ms": timing,
                    "arithmetic_relative_l2": arithmetic,
                    "relative_l2_against_bf16": relative_error(output, reference),
                    "axis_leakage": leakage,
                }
            results.append(result)

    report = {
        "backend": backend_name,
        "gguf_size_bytes": file.stat().st_size,
        "selected_spinor": case,
        "scope": "phase 1 expert tensor repeated in 16 resident slots, GGUF read-back through the PrismML graph",
        "cases": results,
    }
    with destination.open("x", encoding="utf-8") as output:
        output.write(json.dumps(report, indent=2, allow_nan=False) + "\n")


def bench_streamed_bank(reader, prism_bin: Path, kind: str, destination: Path) -> None:
    expert_count = int(reader.fields["experiment.stored_expert_count"].contents())
    if not TOP_K <= expert_count <= 512:
        raise ValueError("Need at least 16 real experts for the bank benchmark")
    signs = np.asarray(
        reader.fields["prism.hadamard.sign_values"].contents(), dtype=np.float32
    )
    if signs.shape != (WIDTH,) or not np.all(np.abs(signs) == 1):
        raise ValueError("Missing or invalid signed Hadamard metadata")
    rng = np.random.default_rng(SEED + 5)
    trials = []
    with open_backend(prism_bin, kind) as (library, backend, name):
        codec = PrismCodec(library)
        for tensor in reader.tensors:
            if int(tensor.tensor_type) != PQ2_0 or tuple(tensor.shape) != (
                WIDTH,
                WIDTH,
                expert_count,
            ):
                raise ValueError(
                    "The streamed expert bank has an unexpected shape or type"
                )
            for tokens in (1, 16):
                # Vary the experts across slots and keep the same route set for the row oracle.
                selected = rng.choice(expert_count, size=TOP_K, replace=False)
                ids = np.stack(
                    [rng.permutation(selected) for _ in range(tokens)]
                ).astype(np.int32)
                values = rng.normal(size=(tokens, TOP_K, WIDTH)).astype(np.float32)
                graph_result, latency = run_graph(
                    library,
                    backend,
                    PQ2_0,
                    tensor.data,
                    values,
                    ids,
                    signs,
                    expert_count=expert_count,
                )
                expected = np.empty_like(graph_result)
                for expert in selected:
                    payload = tensor.data[expert].reshape(-1)
                    weights = hadamard(codec.decode(payload, (WIDTH, WIDTH))) * signs
                    mask = ids == expert
                    expected[mask] = values[mask] @ weights.T
                error = relative_error(graph_result, expected)
                if not np.isfinite(error) or error > 0.03:
                    raise RuntimeError(
                        "The routed expert bank disagrees with the decoded oracle"
                    )
                trials.append(
                    {
                        "tensor": tensor.name,
                        "tokens": tokens,
                        "median_ms": latency,
                        "relative_arithmetic_l2": error,
                    }
                )
    with destination.open("x", encoding="utf-8") as output:
        output.write(
            json.dumps(
                {
                    "backend": name,
                    "resident_real_experts": expert_count,
                    "selected_per_token": TOP_K,
                    "scope": "native routed multiplication over distinct real expert weights",
                    "cases": trials,
                },
                indent=2,
                allow_nan=False,
            )
            + "\n"
        )


def compare_routed_projection(gguf, args) -> None:
    """Isolate the combined low-bit error of gate, up and down for real expert zero."""
    directory = args.prism_bin.resolve(strict=True)
    with os.add_dll_directory(str(directory)):
        codec = PrismCodec(ctypes.CDLL(str(directory / "ggml-base.dll")))

    def decode(path: Path) -> dict[str, np.ndarray]:
        reader = gguf.GGUFReader(path)
        signs = np.asarray(
            reader.fields["prism.hadamard.sign_values"].contents(), dtype=np.float32
        )
        matrices = {}
        for tensor in reader.tensors:
            if int(tensor.tensor_type) != PQ2_0 or tuple(tensor.shape[:2]) != (
                WIDTH,
                WIDTH,
            ):
                raise ValueError(
                    "The comparison requires square PrismML expert tensors"
                )
            matrices[tensor.name] = (
                hadamard(codec.decode(tensor.data[0].reshape(-1), (WIDTH, WIDTH)))
                * signs
            )
        return matrices

    baseline_down = load_bf16(args.gated_pilot / "source-expert.bf16", WIDTH)
    baseline_gate_up = load_bf16(args.gated_pilot / "gate-up-expert.bf16", 2 * WIDTH)
    adapter = load_bf16(args.metric_pilot / "output-adapter.bf16", 2 * WIDTH)
    packed_down = decode(args.down)["blk.1.ffn_down_exps.weight"]
    gate_up = decode(args.gate_up)
    packed_gate_up = np.concatenate(
        (gate_up["blk.1.ffn_gate_exps.weight"], gate_up["blk.1.ffn_up_exps.weight"])
    )
    latent = (
        np.random.default_rng(SEED + 6).normal(size=(WIDTH, 256)).astype(np.float32)
    )
    reference = gated_inputs(baseline_gate_up, latent)
    fitted = gated_inputs(packed_gate_up, latent)
    expected = adapter @ (baseline_down @ reference)
    with args.output.open("x", encoding="utf-8") as file:
        file.write(
            json.dumps(
                {
                    "scope": "one real expert with the live output adapter and 256 fixed synthetic latent activations",
                    "down_only_relative_output_l2": relative_error(
                        adapter @ (packed_down @ reference), expected
                    ),
                    "gate_up_only_relative_output_l2": relative_error(
                        adapter @ (baseline_down @ fitted), expected
                    ),
                    "all_three_routed_matrices_relative_output_l2": relative_error(
                        adapter @ (packed_down @ fitted), expected
                    ),
                },
                indent=2,
                allow_nan=False,
            )
            + "\n"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gguf-python", type=Path, required=True)
    tasks = parser.add_subparsers(dest="task", required=True)
    export = tasks.add_parser("export")
    export.add_argument("--gated-pilot", type=Path, required=True)
    export.add_argument("--metric-pilot", type=Path, required=True)
    export.add_argument("--triality-pilot", type=Path, required=True)
    export.add_argument("--gguf", type=Path, required=True)
    benchmark = tasks.add_parser("benchmark")
    benchmark.add_argument("--gguf", type=Path, required=True)
    benchmark.add_argument("--prism-bin", type=Path, required=True)
    benchmark.add_argument("--backend", choices=("cpu", "cuda"), required=True)
    benchmark.add_argument("--output", type=Path, required=True)
    compare = tasks.add_parser("compare-layer")
    for parameter in (
        "--down",
        "--gate-up",
        "--gated-pilot",
        "--metric-pilot",
        "--prism-bin",
        "--output",
    ):
        compare.add_argument(parameter, type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.gguf_python.resolve(strict=True)))
    gguf = importlib.import_module("gguf")
    if args.task == "export":
        write_gguf(
            gguf, args.gguf, args.gated_pilot, args.metric_pilot, args.triality_pilot
        )
    elif args.task == "benchmark":
        bench(gguf, args.gguf, args.prism_bin, args.backend, args.output)
    else:
        compare_routed_projection(gguf, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
