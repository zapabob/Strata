"""Create one checked GGUF from the BF16 Inkling text, image and DSpark safetensors."""

import argparse
import base64
import gc
import hashlib
import json
import math
import os
import sqlite3
import sys
import time
from contextlib import closing
from pathlib import Path

import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"hy4-bonsai2"))

from source import REPO, await_capacity
from full_gguf import (
    Encoder,
    TYPE,
    align,
    closing_index,
    mark_sparse,
    set_sparse_length,
    signs,
)
from source_archive import ITEMSIZE, atomic_bytes

ARCH = "inkling2_bonsai2"
PREFIX = "inkling2"
NAME = "Inkling-2-Mini-Heretic-Full-Bonsai2-PQ2_0.gguf"
ASSETS = (
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "generation_config.json",
    "processor_config.json",
    "special_tokens_map.json",
    "chat_template.jinja",
)
LOOKUP = np.array(
    [
        [sum(((v >> b) & 3) == j for b in (0, 2, 4, 6)) for j in range(4)]
        for v in range(256)
    ],
    dtype=np.int64,
)


def plan_tensors(source):
    header = json.loads((source / "headers.json").read_bytes())
    index = json.loads((source / "model.safetensors.index.json").read_bytes())[
        "weight_map"
    ]
    out = []
    for shard, group in header.items():
        draft = shard == "mtp.safetensors"
        for name, f in sorted(
            group["tensors"].items(), key=lambda item: item[1]["data_offsets"][0]
        ):
            if not draft and index.get(name) != shard:
                raise ValueError(f"Unexpected main tensor {name}")
            key = "mtp." + name if draft else name
            shape = f["shape"]
            byte_start, end = f["data_offsets"]
            if math.prod(shape) * ITEMSIZE[f["dtype"]] != end - byte_start:
                raise ValueError(f"Bad safetensors descriptor for {key}")
            role = (
                "draft"
                if draft
                else "vision"
                if name.startswith("model.visual.")
                else "expert"
                if ".mlp.experts." in name
                else "text"
            )
            width = shape[-1] if shape else 1
            # Preserve the precision of bias, normalisation, router, short-convolution and loop controls.
            control = any(
                s in key
                for s in (
                    ".mlp.gate.",
                    ".controllers.",
                    "_l2_clip.",
                    ".attn_res.",
                    ".rel_logits_proj.",
                    "_sconv.",
                    "cross_pass_",
                )
            )
            quant = (
                f["dtype"] == "BF16"
                and len(shape) >= 2
                and width >= 128
                and not control
            )
            physical = align(width, 128) if quant else width
            dims = [*shape[:-1], physical] if quant else shape
            size = (
                math.prod(shape[:-1]) * (physical // 128) * 34
                if quant
                else end - byte_start
            )
            tensor_name = (
                key if len(key.encode()) < 64 else f"ink.tensor.{len(out):04d}"
            )
            out.append(
                dict(
                    source=key,
                    name=tensor_name,
                    role=role,
                    origin=shape,
                    shape=dims,
                    original_width=width,
                    dtype=f["dtype"],
                    type=142 if quant else TYPE[f["dtype"]],
                    bytes=size,
                    block=(512 if physical % 512 == 0 else 128) if quant else 0,
                    shard=shard,
                    input_offset=group["base"] + byte_start,
                )
            )
    if len(index) != sum(t["role"] != "draft" for t in out) or len(
        {t["name"] for t in out}
    ) != len(out):
        raise ValueError("Incomplete source or duplicate GGUF name")
    return out


def start(root, source, gguf, plan):
    header = root / (NAME + ".header")
    writer = gguf.GGUFWriter(header, ARCH)
    writer.add_type("model")
    writer.add_name("Inkling 2 Mini Heretic Full, fitted ternary PQ2_0")
    writer.add_uint32("general.quantization_version", 2)
    writer.add_string(PREFIX + ".source.repository", REPO)
    writer.add_string(
        PREFIX + ".source.revision",
        json.loads((source / "source.json").read_bytes())["revision"],
    )
    writer.add_string(
        PREFIX + ".source.layout", json.dumps(plan, separators=(",", ":"))
    )
    for name in ASSETS:
        writer.add_string(
            PREFIX + ".source." + name, (source / name).read_text(encoding="utf-8")
        )
    for width in sorted({t["shape"][-1] for t in plan if t["block"]}):
        writer.add_string(
            f"{PREFIX}.signs.{width}", base64.b64encode(signs(width).tobytes()).decode()
        )
    for t in plan:
        writer.add_tensor_info(
            t["name"],
            t["shape"],
            np.dtype("float32"),
            t["bytes"],
            raw_dtype=gguf.GGMLQuantizationType(t["type"]),
        )
    writer.write_header_to_file()
    writer.write_kv_data_to_file()
    writer.write_ti_data_to_file()
    writer.close()
    with header.open("r+b") as f:
        mark_sparse(f)
        pos = align(f.seek(0, 2))
        for t in plan:
            t["offset"] = pos
            pos += align(t["bytes"])
        set_sparse_length(f, pos)
    with closing_index(header, gguf, plan):
        pass
    atomic_bytes(root / "layout.json", json.dumps(plan, separators=(",", ":")).encode())
    os.replace(header, root / (NAME + ".partial"))


def histogram(data):
    blocks = np.frombuffer(data, np.uint8).reshape(-1, 34)
    # Limit the temporary integer array allocated by bincount.
    counts = sum(
        (
            np.bincount(blocks[i : i + 4096, 2:].ravel(), minlength=256)
            for i in range(0, len(blocks), 4096)
        ),
        start=np.zeros(256, dtype=np.int64),
    )
    return counts @ LOOKUP


def location(source, t):
    path = source / t["shard"]
    if path.exists():
        return path
    part = path.with_suffix(".safetensors.partial")
    mark = part.with_suffix(".checkpoint.json")
    need = t["input_offset"] + math.prod(t["origin"]) * ITEMSIZE[t["dtype"]]
    if (
        mark.exists()
        and json.loads(mark.read_bytes())["bytes"] >= need
        and part.exists()
    ):
        return part
    return None


def encode_tensor(f, source_path, t, encoder):
    read_size = ITEMSIZE[t["dtype"]] * t["original_width"]
    rows = math.prod(t["origin"][:-1]) if t["origin"] else 1
    tile = max(1, 8 * 1024**2 // read_size)
    counts = np.zeros(4, dtype=np.int64)
    digest = hashlib.blake2b(digest_size=20)
    f.seek(t["offset"])
    with source_path.open("rb") as src:
        src.seek(t["input_offset"])
        for i in range(0, rows, tile):
            size = min(tile, rows - i) * read_size
            data = src.read(size)
            if len(data) != size:
                raise OSError(f"Truncated source for {t['source']}")
            if t["type"] == 142:
                data = encoder.encode(data, t)
                counts += histogram(data)
            if f.write(data) != len(data):
                raise OSError("Short GGUF write")
            digest.update(data)
    if f.tell() != t["offset"] + t["bytes"] or counts[3]:
        raise ValueError(f"Invalid ternary output for {t['source']}")
    return digest.hexdigest(), counts.tolist()


def verify(root, gguf, plan, db):
    partial = root / (NAME + ".partial")
    totals = np.zeros(4, dtype=np.int64)
    categories = {}
    with closing_index(partial, gguf, plan), partial.open("rb") as f:
        for t in plan:
            f.seek(t["offset"])
            want, codes = db.execute(
                "select digest,codes from tensors where name=?", (t["name"],)
            ).fetchone()
            digest = hashlib.blake2b(digest_size=20)
            remaining = t["bytes"]
            while remaining:
                b = f.read(min(4 * 1024**2, remaining))
                if not b:
                    raise OSError("Truncated final GGUF")
                digest.update(b)
                remaining -= len(b)
            if digest.hexdigest() != want:
                raise ValueError(f"Final GGUF read-back mismatch for {t['name']}")
            counts = json.loads(codes)
            if t["type"] == 142 and sum(counts) != math.prod(t["shape"]):
                raise ValueError("Missing ternary symbols")
            totals += counts
            group = categories.setdefault(
                t["role"],
                dict(
                    tensors=0,
                    packed_tensors=0,
                    model_weights=0,
                    ternary_weights=0,
                    bytes=0,
                ),
            )
            group["tensors"] += 1
            group["model_weights"] += math.prod(t["origin"])
            group["bytes"] += t["bytes"]
            if t["type"] == 142:
                group["packed_tensors"] += 1
                group["ternary_weights"] += math.prod(t["origin"])
    if totals[3] or min(totals[:3]) <= 0:
        raise ValueError("Invalid whole-file ternary alphabet")
    result = dict(
        repository=REPO,
        architecture=ARCH,
        file=NAME,
        gguf_version=3,
        stored_bytes=partial.stat().st_size,
        source_tensors=len(plan),
        roles=categories,
        code_histogram=dict(
            zip(("-1", "0", "+1", "reserved"), map(int, totals), strict=True)
        ),
        every_tensor_read_back=True,
    )
    atomic_bytes(root / "verified.json", json.dumps(result, indent=2).encode())
    gc.collect()
    partial.rename(root / NAME)
    print(json.dumps(result), flush=True)


def convert(args):
    sys.path.insert(0, str(args.gguf_python.resolve(strict=True)))
    import gguf

    source, root = args.source, args.output
    root.mkdir(parents=True, exist_ok=True)
    if (root / NAME).exists():
        raise FileExistsError("Completed GGUF already exists")
    await_capacity(root, 0)
    if not (root / (NAME + ".partial")).exists():
        start(root, source, gguf, plan_tensors(source))
    plan = json.loads((root / "layout.json").read_bytes())
    encoder = Encoder(args.prism_bin, "cuda", args.cuda_codec)
    with closing(sqlite3.connect(root / "progress.sqlite")) as db:
        db.execute("pragma synchronous=FULL")
        db.execute(
            "create table if not exists tensors(name text primary key,digest text,codes text)"
        )
        done = {row[0] for row in db.execute("select name from tensors")}
        with (root / (NAME + ".partial")).open("r+b") as out:
            for t in plan:
                if t["name"] in done:
                    continue
                path = location(source, t)
                while path is None:
                    time.sleep(3)
                    path = location(source, t)
                await_capacity(root, t["bytes"])
                digest, counts = encode_tensor(out, path, t, encoder)
                db.execute(
                    "insert into tensors values(?,?,?)",
                    (t["name"], digest, json.dumps(counts)),
                )
                done.add(t["name"])
                if t["bytes"] > 16 * 1024**2 or len(done) % 32 == 0:
                    out.flush()
                    os.fsync(out.fileno())
                    db.commit()
                    print(f"{len(done)}/{len(plan)} {t['source']}", flush=True)
            out.flush()
            os.fsync(out.fileno())
            db.commit()
        for shard in {t["shard"] for t in plan}:
            while (
                not (source / shard).exists()
                or not (source / (shard + ".verified.json")).exists()
            ):
                time.sleep(3)
        verify(root, gguf, plan, db)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for k in ("source", "output", "gguf-python", "prism-bin", "cuda-codec"):
        p.add_argument("--" + k, type=Path, required=True)
    convert(p.parse_args())
