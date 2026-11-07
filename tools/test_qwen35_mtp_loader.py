"""Exercise a real pinned llama DLL with small synthetic GGUF model directories.

Uses no model downloads or inference. All tensors are F32 zeros; no_alloc is set
by the C++ probe. The suite intentionally fails against the unpatched loader.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess


def tensor_directory(*, mtp: bool = False) -> dict[str, list[int]]:
    """Small shapes with the real 32-trunk/one-predictor topology."""
    result = {
        "token_embd.weight": [32, 64],
        "output_norm.weight": [32],
        "output.weight": [32, 64],
    }
    for layer in range(33 if mtp else 32):
        shapes = {
            "attn_norm.weight": [32],
            "post_attention_norm.weight": [32],
            "ffn_gate.weight": [32, 64],
            "ffn_up.weight": [32, 64],
            "ffn_down.weight": [64, 32],
        }
        if layer == 32 or (layer + 1) % 4 == 0:
            shapes.update(
                {
                    "attn_q.weight": [32, 64],
                    "attn_k.weight": [32, 16],
                    "attn_v.weight": [32, 16],
                    "attn_output.weight": [32, 32],
                    "attn_q_norm.weight": [16],
                    "attn_k_norm.weight": [16],
                }
            )
        else:
            shapes.update(
                {
                    "attn_qkv.weight": [32, 64],
                    "attn_gate.weight": [32, 32],
                    "ssm_conv1d.weight": [4, 64],
                    "ssm_dt.bias": [4],
                    "ssm_a": [4],
                    "ssm_beta.weight": [32, 4],
                    "ssm_alpha.weight": [32, 4],
                    "ssm_norm.weight": [8],
                    "ssm_out.weight": [32, 32],
                }
            )
        if layer == 32:
            shapes.update(
                {
                    "nextn.eh_proj.weight": [64, 32],
                    "nextn.enorm.weight": [32],
                    "nextn.hnorm.weight": [32],
                }
            )
        result.update({f"blk.{layer}.{name}": shape for name, shape in shapes.items()})
    return result


def fixture(
    path: Path, tensors: dict[str, list[int]], *, declare_mtp: bool = True
) -> None:
    """Write only a fresh synthetic fixture, never a user-supplied GGUF."""
    assert not path.exists() and path.parent.is_dir()

    def integer(item: int) -> bytes:
        return struct.pack("<I", item)

    def length(item: int) -> bytes:
        return struct.pack("<Q", item)

    def text(item: str) -> bytes:
        encoded = item.encode("utf-8")
        return length(len(encoded)) + encoded

    layers = 33 if declare_mtp else 32
    meta = [
        ("general.architecture", 8, "qwen35"),
        ("general.type", 8, "model"),
        ("general.name", 8, "synthetic loader test"),
        ("tokenizer.ggml.model", 8, "none"),
        ("qwen35.vocab_size", 4, 64),
        ("qwen35.context_length", 4, 1024),
        ("qwen35.block_count", 4, layers),
        ("qwen35.nextn_predict_layers", 4, int(declare_mtp)),
        ("qwen35.embedding_length", 4, 32),
        ("qwen35.feed_forward_length", 4, 64),
        ("qwen35.attention.head_count", 4, 2),
        ("qwen35.attention.head_count_kv", 4, 1),
        ("qwen35.attention.key_length", 4, 16),
        ("qwen35.attention.value_length", 4, 16),
        ("qwen35.attention.layer_norm_rms_epsilon", 6, 1e-6),
        ("qwen35.rope.dimension_sections", 9, [4, 4, 0, 0]),
        ("qwen35.full_attention_interval", 4, 4),
        (
            "qwen35.attention.recurrent_layers",
            9,
            [int(i < 32 and (i + 1) % 4 != 0) for i in range(layers)],
        ),
        ("qwen35.ssm.conv_kernel", 4, 4),
        ("qwen35.ssm.inner_size", 4, 32),
        ("qwen35.ssm.state_size", 4, 8),
        ("qwen35.ssm.time_step_rank", 4, 4),
        ("qwen35.ssm.group_count", 4, 2),
    ]

    def value(kind: int, item: object) -> bytes:
        if kind == 8:
            return text(item)
        if kind == 6:
            return struct.pack("<f", item)
        if kind == 9:
            return integer(4) + length(len(item)) + b"".join(integer(i) for i in item)
        return integer(item)

    header = b"GGUF" + integer(3) + length(len(tensors)) + length(len(meta))
    header += b"".join(
        text(key) + integer(kind) + value(kind, item) for key, kind, item in meta
    )
    offset = 0
    for name, shape in tensors.items():
        elements = 1
        for dim in shape:
            elements *= dim
        header += (
            text(name)
            + integer(len(shape))
            + b"".join(length(dim) for dim in shape)
            + integer(0)
            + length(offset)
        )
        offset += (elements * 4 + 31) // 32 * 32
    with path.open("xb") as stream:
        stream.write(header)
        stream.write(bytes((-len(header)) % 32 + offset))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    baseline = None
    if args.baseline:
        baseline = {
            row["name"]: row["fixtureSHA256"]
            for row in json.loads(args.baseline.read_text(encoding="utf-8"))["cases"]
        }
    assert args.out.parent.is_dir() and not args.out.exists()
    args.out.mkdir()
    trunk, full = tensor_directory(), tensor_directory(mtp=True)
    cases = [
        ("trunk-only", trunk, False, True, True),
        ("trunk-explicit-mtp", trunk, True, False, True),
        ("full-no-mtp", full, False, True, True),
        ("full-with-mtp", full, True, True, True),
        ("ordinary-no-predictor-metadata", trunk, False, True, False),
    ]
    for layer in (0, 31):
        cases.append(
            (
                f"missing-block-{layer}",
                {k: v for k, v in trunk.items() if not k.startswith(f"blk.{layer}.")},
                False,
                False,
                True,
            )
        )
    for name in [key for key in trunk if key.startswith(("blk.0.", "blk.31."))]:
        cases.append(
            (
                "missing-" + name,
                {k: v for k, v in trunk.items() if k != name},
                False,
                False,
                True,
            )
        )
    for name in [key for key in full if key.startswith("blk.32.")]:
        cases.append(
            (
                "partial-" + name,
                {k: v for k, v in full.items() if k != name},
                False,
                False,
                True,
            )
        )
    for name in (
        "blk.32.attn_norm.weight",
        "blk.32.nextn.eh_proj.weight",
        "blk.32.unknown.weight",
    ):
        cases.append(("only-" + name, dict(trunk, **{name: [32]}), False, False, True))
    only_mtp = {
        k: v
        for k, v in full.items()
        if not k.startswith("blk.") or k.startswith("blk.32.")
    }
    cases.append(("standalone-mtp", only_mtp, True, True, True))
    cases.append(("standalone-mtp-not-requested", only_mtp, False, False, True))
    cases.append(
        (
            "first-trunk-norm-missing-with-full-mtp",
            {k: v for k, v in full.items() if k != "blk.0.attn_norm.weight"},
            True,
            False,
            True,
        )
    )
    for name in ("token_embd.weight", "output_norm.weight"):
        cases.append(
            (
                "missing-" + name,
                {k: v for k, v in trunk.items() if k != name},
                False,
                False,
                True,
            )
        )
    bad_shape = dict(trunk)
    bad_shape["blk.31.attn_norm.weight"] = [31]
    cases.append(("wrong-trunk-shape", bad_shape, False, False, True))
    fused = {
        k: v
        for k, v in full.items()
        if k
        not in ("blk.32.attn_q.weight", "blk.32.attn_k.weight", "blk.32.attn_v.weight")
    }
    fused["blk.32.attn_qkv.weight"] = [32, 96]
    cases.append(("full-fused-predictor", fused, False, True, True))
    if baseline is not None:
        assert set(baseline) == {case[0] for case in cases}
    rows = []
    for index, (name, tensors, load_mtp, expected, declare_mtp) in enumerate(cases):
        file = args.out / f"{index:02d}.gguf"
        fixture(file, tensors, declare_mtp=declare_mtp)
        digest = hashlib.sha256(file.read_bytes()).hexdigest()
        if baseline is not None:
            assert digest == baseline[name], "Fixture changed from baseline: " + name
        process = subprocess.run(
            [str(args.probe), str(args.runtime), str(file), str(int(load_mtp))],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        (args.out / f"{index:02d}.stderr.txt").write_text(
            process.stderr, encoding="utf-8"
        )
        try:
            result = json.loads(process.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            result = {"loaded": None, "probeError": process.stdout}
        passed = process.returncode == 0 and result["loaded"] is expected
        if expected and result.get("loaded"):
            passed = (
                passed
                and result["trunkLayers"] == 32
                and result["mtpLayers"] == int(declare_mtp)
            )
        assert hashlib.sha256(file.read_bytes()).hexdigest() == digest
        rows.append(
            dict(
                name=name,
                expectedLoaded=expected,
                loadMtp=load_mtp,
                tensorCount=len(tensors),
                result=result,
                passed=passed,
                probeExit=process.returncode,
                fixtureSHA256=digest,
            )
        )
        if process.returncode != 0:
            break  # A broken probe is not an expected loader rejection.
    summary = {
        "passed": sum(row["passed"] for row in rows),
        "failed": sum(not row["passed"] for row in rows),
        "cases": rows,
    }
    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary))
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
