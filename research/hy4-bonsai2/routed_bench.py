"""Check PrismML's rotated, routed expert graph on a single CPU or CUDA backend."""

from __future__ import annotations

import argparse
import ctypes as ct
import json
import os
from contextlib import contextmanager
from pathlib import Path
from statistics import median
from time import perf_counter_ns

import numpy as np
from experiment import BLOCK, PQ2_0, SEED, PrismCodec, export, hadamard

POINTER = ct.c_void_p
DIM = ct.c_int64
SIZE = ct.c_size_t
I32 = 26
F32 = 0
F16 = 1
BF16 = 30
TOP_K = 16
SHAPE = (1536, 1536)
HADAMARD_HINT = 1


class InitParams(ct.Structure):
    _fields_ = [("mem_size", SIZE), ("mem_buffer", POINTER), ("no_alloc", ct.c_bool)]


def run_graph(
    library,
    backend,
    type_id,
    weight,
    inputs,
    ids,
    signs,
    *,
    spin=None,
    projection=None,
    expert_count=TOP_K,
):
    """Measure resident, synchronous expert dispatch, including rotation if used."""
    tensor_1d = export(library, "ggml_new_tensor_1d", POINTER, POINTER, ct.c_int, DIM)
    tensor_2d = export(
        library, "ggml_new_tensor_2d", POINTER, POINTER, ct.c_int, DIM, DIM
    )
    tensor_3d = export(
        library, "ggml_new_tensor_3d", POINTER, POINTER, ct.c_int, DIM, DIM, DIM
    )
    reshape = export(
        library, "ggml_reshape_4d", POINTER, POINTER, POINTER, DIM, DIM, DIM, DIM
    )
    set_tensor = export(
        library, "ggml_backend_tensor_set", None, POINTER, POINTER, SIZE, SIZE
    )
    get_tensor = export(
        library, "ggml_backend_tensor_get", None, POINTER, POINTER, SIZE, SIZE
    )
    supports = export(library, "ggml_backend_supports_op", ct.c_bool, POINTER, POINTER)
    nbytes = export(library, "ggml_nbytes", SIZE, POINTER)
    run = export(library, "ggml_backend_graph_compute", ct.c_int, POINTER, POINTER)
    free = export(library, "ggml_free", None, POINTER)
    free_buffer = export(library, "ggml_backend_buffer_free", None, POINTER)
    init = export(library, "ggml_init", POINTER, InitParams)
    mm = export(library, "ggml_mul_mat", POINTER, POINTER, POINTER, POINTER)
    mul = export(library, "ggml_mul", POINTER, POINTER, POINTER, POINTER)
    context = init(InitParams(2**20, None, True))
    if not context:
        raise RuntimeError("Cannot allocate GGML graph context")

    tokens, slots, width = inputs.shape
    rows = SHAPE[0]
    buffer = None
    try:
        experts = tensor_3d(context, type_id, width, rows, expert_count)
        vec = tensor_3d(context, F32, width, slots, tokens)
        routes = tensor_2d(context, I32, slots, tokens)
        transfers = [(experts, weight), (vec, inputs), (routes, ids)]
        operations = []

        def rotate_blocks(source, rotation):
            block_count, block, _ = rotation.shape
            permute = export(
                library,
                "ggml_permute",
                POINTER,
                POINTER,
                POINTER,
                ct.c_int,
                ct.c_int,
                ct.c_int,
                ct.c_int,
            )
            cont = export(library, "ggml_cont", POINTER, POINTER, POINTER)
            transform = tensor_3d(context, F32, block, block, block_count)
            transfers.append((transform, rotation))
            blocks = reshape(context, source, block, block_count, slots * tokens, 1)
            transposed = cont(context, permute(context, blocks, 0, 2, 1, 3))
            rotated = mm(context, transform, transposed)
            restored = cont(context, permute(context, rotated, 0, 2, 1, 3))
            operations.extend((transposed, rotated, restored))
            return reshape(context, restored, block_count * block, slots, tokens, 1)

        activation = vec
        if spin is not None:
            activation = rotate_blocks(activation, spin[0])
        if type_id == PQ2_0 and signs is not None:
            signs_tensor = tensor_1d(context, F32, width)
            rotate_tensor = tensor_2d(context, F32, BLOCK, BLOCK)
            hint = export(library, "ggml_mul_mat_set_hint", None, POINTER, ct.c_int)
            signed = mul(context, activation, signs_tensor)
            blocks = reshape(context, signed, BLOCK, width // BLOCK, slots, tokens)
            rotated = mm(context, rotate_tensor, blocks)
            hint(rotated, HADAMARD_HINT)
            activation = reshape(context, rotated, width, slots, tokens, 1)
            operations.extend((signed, rotated))
            rotation = hadamard(np.eye(BLOCK, dtype=np.float32))
            transfers.extend(((signs_tensor, signs), (rotate_tensor, rotation)))

        mul_id = export(
            library, "ggml_mul_mat_id", POINTER, POINTER, POINTER, POINTER, POINTER
        )
        result = mul_id(context, experts, activation, routes)
        operations.append(result)
        if spin is not None:
            result = rotate_blocks(result, spin[1])
        if projection is not None:
            axis_tensor = tensor_2d(context, F32, rows, 1)
            removal_tensor = tensor_1d(context, F32, rows)
            transfers.extend(
                zip((axis_tensor, removal_tensor), projection, strict=True)
            )
            repeat = export(library, "ggml_repeat", POINTER, POINTER, POINTER, POINTER)
            sub = export(library, "ggml_sub", POINTER, POINTER, POINTER, POINTER)
            component = mm(context, axis_tensor, result)
            correction = mul(
                context, repeat(context, removal_tensor, result), component
            )
            result = sub(context, result, correction)
            operations.extend((component, correction, result))
        if not all(supports(backend, node) for node in operations):
            raise RuntimeError(
                "The selected backend does not support the full expert graph"
            )
        new_graph = export(
            library, "ggml_new_graph_custom", POINTER, POINTER, SIZE, ct.c_bool
        )
        expand = export(library, "ggml_build_forward_expand", None, POINTER, POINTER)
        graph = new_graph(context, 64, False)
        expand(graph, result)
        allocate = export(
            library, "ggml_backend_alloc_ctx_tensors", POINTER, POINTER, POINTER
        )
        buffer = allocate(context, backend)
        if not buffer:
            raise RuntimeError("The backend could not allocate the expert graph")
        for tensor, data in transfers:
            if not data.flags.c_contiguous or data.nbytes != nbytes(tensor):
                raise ValueError("Expert graph input does not match its GGML tensor")
            set_tensor(tensor, data.ctypes.data, 0, data.nbytes)
        duration_ms = []
        for _ in range(10):
            start = perf_counter_ns()
            if run(backend, graph) != 0:
                raise RuntimeError("GGML graph computation failed")
            duration_ms.append((perf_counter_ns() - start) / 1e6)
        output = np.empty((tokens, slots, rows), dtype=np.float32)
        get_tensor(result, output.ctypes.data, 0, output.nbytes)
        return output, median(duration_ms[3:])
    finally:
        if buffer:
            free_buffer(buffer)
        free(context)


def read_weights(directory, codec):
    """Load the two recorded specimens used in the repeated expert bank."""
    bits = np.fromfile(directory / "source-expert.bf16", dtype="<u2")
    original = (bits.astype(np.uint32) << 16).view(np.float32).reshape(SHAPE)
    projected = np.load(directory / "directly-projected-expert.npy", allow_pickle=False)
    full = np.tile(
        np.stack((original, projected)).astype(np.float16), (TOP_K // 2, 1, 1)
    )
    payloads = [
        np.fromfile(directory / name, dtype=np.uint8)
        for name in ("expert.pq2_0", "directly-projected-expert.pq2_0")
    ]
    packed = np.tile(np.concatenate(payloads), TOP_K // 2)
    signs = np.load(directory / "activation-signs.npy", allow_pickle=False).astype(
        np.float32
    )
    if signs.shape != (SHAPE[1],) or not np.all(np.abs(signs) == 1):
        raise ValueError("Invalid activation signs")
    reconstructed = [hadamard(codec.decode(data, SHAPE)) * signs for data in payloads]
    return full, packed, signs, reconstructed


def relative_error(actual, expected):
    return float(np.linalg.norm(actual - expected) / np.linalg.norm(expected))


def benchmark(library, backend, directory):
    full, packed, signs, reconstructed = read_weights(directory, PrismCodec(library))
    rng = np.random.default_rng(SEED)
    cases = []
    for tokens in (1, 16):
        inputs = rng.normal(size=(tokens, TOP_K, SHAPE[1])).astype(np.float32)
        ids = np.stack([rng.permutation(TOP_K) for _ in range(tokens)]).astype(np.int32)
        reference = np.empty_like(inputs)
        float_out, float_ms = run_graph(library, backend, F16, full, inputs, ids, signs)
        quant_out, quant_ms = run_graph(
            library, backend, PQ2_0, packed, inputs, ids, signs
        )
        for parity in (0, 1):
            mask = ids % 2 == parity
            reference[mask] = inputs[mask] @ reconstructed[parity].T
        arithmetic_error = relative_error(quant_out, reference)
        if not np.isfinite(arithmetic_error) or arithmetic_error > 0.03:
            raise RuntimeError(
                f"PQ2_0 graph disagrees with the reference: {arithmetic_error:.4g}"
            )
        cases.append(
            {
                "tokens": tokens,
                "routed_slots": TOP_K,
                "f16_median_ms": float_ms,
                "pq2_0_median_ms": quant_ms,
                "pq2_0_arithmetic_relative_l2": arithmetic_error,
                "pq2_0_vs_f16_relative_l2": relative_error(quant_out, float_out),
            }
        )
    return cases


@contextmanager
def open_backend(directory: Path, kind: str):
    directory = directory.resolve(strict=True)
    with os.add_dll_directory(str(directory)):
        library = ct.CDLL(str(directory / "ggml-base.dll"))
        runtime = ct.CDLL(str(directory / f"ggml-{kind}.dll"))
        if kind == "cuda":
            memory = export(
                runtime,
                "ggml_backend_cuda_get_device_memory",
                None,
                ct.c_int,
                POINTER,
                POINTER,
            )
            free_mem, total_mem = SIZE(), SIZE()
            memory(0, ct.byref(free_mem), ct.byref(total_mem))
            if free_mem.value < 2 * 1024**3:
                raise RuntimeError(
                    "Insufficient free CUDA memory for the bounded graph probe"
                )
            backend = export(runtime, "ggml_backend_cuda_init", POINTER, ct.c_int)(0)
        else:
            backend = export(runtime, "ggml_backend_cpu_init", POINTER)()
        if not backend:
            raise RuntimeError("Requested backend failed to initialise")
        try:
            if kind == "cpu":
                export(
                    runtime, "ggml_backend_cpu_set_n_threads", None, POINTER, ct.c_int
                )(backend, 6)
            name = export(library, "ggml_backend_name", ct.c_char_p, POINTER)(
                backend
            ).decode()
            yield library, backend, name
        finally:
            export(library, "ggml_backend_free", None, POINTER)(backend)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prism-bin", type=Path, required=True)
    parser.add_argument("--pilot", type=Path, required=True)
    parser.add_argument("--backend", choices=("cpu", "cuda"), required=True)
    args = parser.parse_args()
    with open_backend(args.prism_bin, args.backend) as (library, backend, name):
        results = benchmark(library, backend, args.pilot)
    report = {
        "backend": name,
        "scope": "two real weight specimens repeated across 16 routed slots",
        "cases": results,
    }
    with (args.pilot / f"routed-{args.backend}.json").open(
        "x", encoding="utf-8"
    ) as file:
        file.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
