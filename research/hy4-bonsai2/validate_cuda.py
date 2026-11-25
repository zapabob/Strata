"""Check the fused CUDA codec against PrismML on original BF16 and adversarial numerical controls."""

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import torch

from cuda_codec import CudaCodec
from experiment import fit_ternary
from full_gguf import Encoder, signs, transform
from weight_store import invert_basis


def samples(source, expert):
    yield "checkpoint_expert", np.fromfile(expert, "<u2").reshape(-1, 1536), 1536
    names = [
        k
        for k in json.loads((source / "catalogue.json").read_bytes())
        if k.startswith("vit.") and k.endswith(".weight")
    ]
    for key in names:
        raw = source / "native" / (key + ".bin")
        if raw.is_file() and 128 * 128 * 2 <= raw.stat().st_size < 12 * 1024**2:
            a = np.fromfile(raw, "<u2")
            if a.size % 128 == 0:
                yield "vision_tile", a[: 128 * 256].reshape(-1, 128), 128
                break
    rng = np.random.default_rng(502)
    for w in (96, 128, 384, 512, 1536):
        x = rng.normal(0.0, 0.08, size=(256, w)).astype(np.float32)
        x[:32] = 0
        x[32:64] = 0.125
        x[64:96] = np.where(np.arange(w) % 3, 0.25, -0.125)
        yield f"tied_and_random_{w}", (x.view(np.uint32) >> 16).astype("<u2"), w


def check(args):
    codec = CudaCodec(args.dll)
    encoder = Encoder(args.prism_bin, "cuda")
    report = []
    for name, raw, width in samples(args.source, args.expert):
        physical = math.ceil(width / 128) * 128
        block = 512 if physical % 512 == 0 else 128
        direction = signs(physical)
        t = dict(shape=[len(raw), physical], block=block, original_width=width)
        result = {}
        for _ in range(2):
            start = time.perf_counter()
            packed = codec.encode(raw, width, direction, block)
            result["cuda_seconds"] = time.perf_counter() - start
        matrix = (raw.astype(np.uint32) << 16).view(np.float32)
        matrix = np.pad(matrix, ((0, 0), (0, physical - width)))
        start = time.perf_counter()
        expected = encoder.codec.encode(
            fit_ternary(transform(matrix * direction, block))
        ).reshape(packed.shape)
        result["numpy_and_PrismML_seconds"] = time.perf_counter() - start
        torch_bytes = np.frombuffer(encoder.encode(raw, t), dtype=np.uint8).reshape(
            packed.shape
        )
        result["different_bytes_against_numpy_PrismML"] = int(
            np.count_nonzero(expected != packed)
        )
        result["different_bytes_against_torch_PrismML"] = int(
            np.count_nonzero(torch_bytes != packed)
        )
        checked = encoder.codec.decode(packed, (len(raw), physical))
        signs_gpu = torch.tensor(direction, device="cuda")
        decoded = codec.decode(
            packed.tobytes(), len(raw), t, signs_gpu, "cuda", torch.bfloat16
        )
        reference = invert_basis(torch.from_numpy(checked).cuda(), block, signs_gpu)[
            :, :width
        ].bfloat16()
        result["different_BF16_values_against_vendor_inverse"] = (
            (reference != decoded).count_nonzero().item()
        )
        result["maximum_BF16_difference"] = (
            (reference.float() - decoded.float()).abs().max().item()
        )
        result.update(fixture=name, shape=list(raw.shape), packed_bytes=packed.nbytes)
        print(result, flush=True)
        report.append(result)
    passed = all(
        not row["different_bytes_against_numpy_PrismML"]
        and not row["different_bytes_against_torch_PrismML"]
        and not row["different_BF16_values_against_vendor_inverse"]
        for row in report
    )
    args.output.write_text(
        json.dumps(
            dict(passed=passed, gpu=torch.cuda.get_device_name(), cases=report),
            indent=2,
        )
        + "\n"
    )
    return passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("expert", "source", "dll", "prism-bin", "output"):
        parser.add_argument("--" + field, type=Path, required=True)
    raise SystemExit(0 if check(parser.parse_args()) else 1)
