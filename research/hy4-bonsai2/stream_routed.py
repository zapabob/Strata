"""Stream a complete Hy4 routed tensor into PrismML PQ2_0 with bounded RAM."""

from __future__ import annotations

import argparse
import ctypes
import importlib
import json
import logging
import os
import re
import shutil
import struct
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from pathlib import Path
from time import monotonic, sleep

import numpy as np
import requests
from experiment import (
    BLOCK,
    GROUP,
    PQ2_0,
    REPO,
    ROOT,
    SEED,
    PrismCodec,
    fit_ternary,
    hadamard,
    read_range,
)
from urllib3.exceptions import HTTPError

sys.path.insert(0, str(ROOT / "tools"))
from native_model_resource_guard import available_memory

LOGGER = logging.getLogger(__name__)
WIDTH = 1536
EXPERTS = 512
ROW_BYTES = WIDTH // GROUP * 34
RANGE_ROWS = 4096
FIT_ROWS = 256
GIB = 1024**3
KINDS = {
    "down_proj": (1536, "ffn_down_exps"),
    "gate_up_proj": (3072, ("ffn_gate_exps", "ffn_up_exps")),
}


def remote_source(
    session: requests.Session, layer: int, kind: str, revision: str | None = None
) -> dict[str, object]:
    if revision is None:
        response = session.get(
            "https://huggingface.co/api/models/tencent/Hy4-flash", timeout=25
        )
        response.raise_for_status()
        revision = response.json()["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Invalid Hugging Face source revision")
    prefix = f"{REPO}/resolve/{revision}"
    source_tensor = f"model.layers.{layer}.mlp.experts.{kind}"
    response = session.get(f"{prefix}/model.safetensors.index.json", timeout=25)
    response.raise_for_status()
    shard = response.json()["weight_map"][source_tensor]
    if not re.fullmatch(r"model-\d{5}-of-\d{5}\.safetensors", shard):
        raise ValueError("Unsafe or unsupported source shard name")
    url = f"{prefix}/{shard}"
    (length,) = struct.unpack("<Q", retry_range(session, url, 0, 8))
    if not 1 <= length <= 8 * 1024**2:
        raise ValueError("Safetensors header length is outside the bound")
    field = json.loads(retry_range(session, url, 8, length))[source_tensor]
    height, target = KINDS[kind]
    if field["dtype"] != "BF16" or field["shape"] != [EXPERTS, height, WIDTH]:
        raise ValueError("Source route does not match the expected BF16 tensor")
    start, end = field["data_offsets"]
    if start < 0 or end - start != EXPERTS * height * WIDTH * 2:
        raise ValueError("Unexpected source tensor extent")
    plan = {
        "repository": "tencent/Hy4-flash",
        "revision": revision,
        "shard": shard,
        "url": url,
        "source_tensor": source_tensor,
        "shape": field["shape"],
        "offset": start + 8 + length,
        "bits_per_weight": 8 * ROW_BYTES / WIDTH,
        "folding_block_size": BLOCK,
        "sign_seed": SEED,
    }
    if kind == "gate_up_proj":
        plan["target_tensors"] = [f"blk.{layer}.{stem}.weight" for stem in target]
    else:
        plan["target_tensor"] = f"blk.{layer}.{target}.weight"
    return plan


def retry_range(session: requests.Session, url: str, offset: int, size: int) -> bytes:
    for attempt in range(3):
        try:
            return read_range(session, url, offset, size)
        except (requests.RequestException, HTTPError, RuntimeError):
            if attempt == 2:
                raise
            LOGGER.warning("Range read retry at byte %d", offset)
            sleep(2**attempt)
    raise RuntimeError("Unreachable range retry state")


def check_resources(output: Path, remaining: int) -> None:
    resources = available_memory()
    if (
        resources["available_physical_bytes"] < 3 * GIB
        or resources["available_commit_bytes"] < 4 * GIB
    ):
        raise RuntimeError("The Windows RAM or commit reserve was reached")
    if (
        shutil.disk_usage("C:/").free < 5 * GIB
        or shutil.disk_usage(output).free < 10 * GIB + remaining
    ):
        raise RuntimeError("The disk reserve would be exceeded")


def encode_chunk(
    session, codec, url: str, offset: int, count: int, signs: np.ndarray, cuda=None
) -> np.ndarray:
    payload = retry_range(session, url, offset, count * WIDTH * 2)
    if cuda is not None:
        packed = cuda.encode(payload, WIDTH, signs, BLOCK)
        if not codec.validate(PQ2_0, packed.ctypes.data, packed.nbytes):
            raise ValueError("PrismML rejected the CUDA PQ2_0 payload")
        return packed
    source = np.frombuffer(payload, dtype="<u2").reshape(count, WIDTH)
    result = np.empty((count, ROW_BYTES), dtype=np.uint8)
    for start in range(0, count, FIT_ROWS):
        end = min(start + FIT_ROWS, count)
        rows = (source[start:end].astype(np.uint32) << 16).view(np.float32)
        result[start:end] = codec.encode(fit_ternary(hadamard(rows * signs))).reshape(
            end - start, ROW_BYTES
        )
    return result


def encode_rows(
    codec, plan, output: Path, signs: np.ndarray, limit: int, workers: int, cuda=None
) -> tuple[int, float, int]:
    offset = plan["offset"]
    height = plan["shape"][1]
    raw = output / "tensor.pq2_0.part"
    existing = raw.stat().st_size if raw.exists() else 0
    if existing % ROW_BYTES or existing > limit * ROW_BYTES:
        raise ValueError("The staged tensor ends at an invalid row boundary")
    initial = current = existing // ROW_BYTES
    started = monotonic()
    with ExitStack() as stack:
        destination = stack.enter_context(raw.open("ab"))
        sessions = [stack.enter_context(requests.Session()) for _ in range(workers)]
        pool = stack.enter_context(ThreadPoolExecutor(max_workers=workers))
        while current < limit:
            check_resources(output, (2 * limit - current) * ROW_BYTES)
            starts = range(
                current, min(current + workers * RANGE_ROWS, limit), RANGE_ROWS
            )
            pending = []
            for slot, start in enumerate(starts):
                count = min(RANGE_ROWS, limit - start)
                job = pool.submit(
                    encode_chunk,
                    sessions[slot],
                    codec,
                    plan["url"],
                    offset + start * WIDTH * 2,
                    count,
                    signs,
                    cuda,
                )
                pending.append((count, job))
            for count, job in pending:
                encoded = job.result()
                if destination.write(encoded) != encoded.nbytes:
                    raise OSError("The staged PQ2_0 write was incomplete")
                destination.flush()
                previous = current
                current += count
                if (
                    current // (height * 16) > previous // (height * 16)
                    or current == limit
                ):
                    LOGGER.info(
                        "Encoded rows %d/%d (%.1f%%)",
                        current,
                        limit,
                        100 * current / limit,
                    )
    return current, monotonic() - started, initial


def write_tensor_gguf(
    gguf, output: Path, plan, limit_experts: int, signs: np.ndarray
) -> Path:
    target = output / "routed-experts.gguf"
    partial = output / "routed-experts.gguf.partial"
    height = plan["shape"][1]
    raw = np.memmap(
        output / "tensor.pq2_0.part",
        dtype=np.uint8,
        mode="r",
        shape=(limit_experts, height, ROW_BYTES),
    )
    if "target_tensors" in plan:
        contents = dict(
            zip(plan["target_tensors"], np.split(raw, 2, axis=1), strict=True)
        )
    else:
        contents = {plan["target_tensor"]: raw}
    writer = gguf.GGUFWriter(partial, "hy_v4_flash")
    try:
        writer.add_type("tensor-fixture")
        writer.add_string("experiment.source_tensor", plan["source_tensor"])
        writer.add_uint32("experiment.source_expert_count", EXPERTS)
        writer.add_uint32("experiment.stored_expert_count", limit_experts)
        writer.add_uint32("prism.hadamard.version", 1)
        writer.add_uint32("prism.hadamard.block_size", BLOCK)
        writer.add_string("prism.hadamard.axis", "input-last-dimension")
        writer.add_string(
            "prism.hadamard.transform", "normalized-sylvester-walsh-hadamard"
        )
        writer.add_string("prism.hadamard.sign_mode", "explicit")
        writer.add_array("prism.hadamard.weight_names", list(contents))
        writer.add_array("prism.hadamard.sign_widths", [WIDTH])
        writer.add_array("prism.hadamard.sign_values", signs.tolist())
        for name, data in contents.items():
            writer.add_tensor(name, data, raw_dtype=gguf.GGMLQuantizationType.PQ2_0)
        writer.write_header_to_file()
        writer.write_kv_data_to_file()
        writer.write_tensors_to_file()
    finally:
        writer.close()
    tensors = gguf.GGUFReader(partial).tensors
    if {tensor.name for tensor in tensors} != contents.keys():
        raise RuntimeError("GGUF read-back failed its tensor inventory check")
    for tensor in tensors:
        data = contents[tensor.name]
        if int(tensor.tensor_type) != PQ2_0 or tuple(tensor.shape) != (
            WIDTH,
            data.shape[1],
            limit_experts,
        ):
            raise RuntimeError(
                "GGUF read-back failed its exact tensor shape/type check"
            )
        for start in range(0, limit_experts, 16):
            finish = start + 16
            if not np.array_equal(tensor.data[start:finish], data[start:finish]):
                raise RuntimeError("GGUF read-back failed its byte comparison")
    del tensor, tensors, raw, writer, data, contents
    partial.rename(target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prism-bin", type=Path, required=True)
    parser.add_argument("--gguf-python", type=Path, required=True)
    parser.add_argument("--cuda-codec", type=Path)
    parser.add_argument("--layer", type=int, choices=range(1, 42), required=True)
    parser.add_argument("--matrix", choices=tuple(KINDS), required=True)
    parser.add_argument(
        "--revision", help="Use the checkpoint revision of the first bank"
    )
    parser.add_argument("--experts", type=int, default=EXPERTS)
    parser.add_argument("--range-workers", type=int, choices=range(1, 5), default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.experts <= EXPERTS:
        parser.error("The expert count must be between 1 and 512")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if (output / "routed-experts.gguf").exists():
        raise FileExistsError("The routed expert fixture is already present")
    sys.path.insert(0, str(args.gguf_python.resolve(strict=True)))
    gguf = importlib.import_module("gguf")
    bin_path = args.prism_bin.resolve(strict=True)
    with os.add_dll_directory(str(bin_path)):
        codec = PrismCodec(ctypes.CDLL(str(bin_path / "ggml-base.dll")))
    cuda = None
    if args.cuda_codec:
        from cuda_codec import CudaCodec

        cuda = CudaCodec(args.cuda_codec)
    signs = np.random.default_rng(SEED).choice(
        np.array([-1, 1], dtype=np.int8), size=WIDTH
    )
    with requests.Session() as session:
        plan = remote_source(session, args.layer, args.matrix, args.revision)
        plan["stored_experts"] = args.experts
        plan_path = output / "source.json"
        if plan_path.exists():
            if json.loads(plan_path.read_text(encoding="utf-8")) != plan:
                raise ValueError(
                    "Existing conversion state describes a different source or output"
                )
        else:
            with plan_path.open("x", encoding="utf-8") as file:
                file.write(json.dumps(plan, indent=2) + "\n")
    rows, elapsed, initial = encode_rows(
        codec,
        plan,
        output,
        signs,
        args.experts * plan["shape"][1],
        args.range_workers,
        cuda,
    )
    final = write_tensor_gguf(gguf, output, plan, args.experts, signs)
    (output / "conversion.json").write_text(
        json.dumps(
            {
                "shape": [args.experts, plan["shape"][1], WIDTH],
                "rows": rows,
                "resumed_rows": initial,
                "stream_and_fit_seconds": elapsed,
                "range_workers": args.range_workers,
                "fit_device": "fused CUDA" if cuda else "NumPy CPU",
                "output_bytes": final.stat().st_size,
                "pq2_tensor_bytes": rows * ROW_BYTES,
                "contains_full_model": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
