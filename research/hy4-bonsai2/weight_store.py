"""Read original model tensors from a single PQ2_0 GGUF or the pinned BF16 source."""

from __future__ import annotations

import base64
import ctypes
import json
import math
import os
import sqlite3
import threading
from collections import Counter
from pathlib import Path

import numpy as np
import torch

from experiment import PrismCodec
from full_gguf import ARCH, GROUP
from source_archive import Archive, ITEMSIZE, atomic_bytes
from stream_routed import check_resources

DTYPES = {"BF16": torch.bfloat16, "F32": torch.float32, "I32": torch.int32}
NATIVE = {30: torch.bfloat16, 0: torch.float32, 26: torch.int32}
ASSETS = (
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "generation_config.json",
    "processor_config.json",
    "chat_template.jinja",
)


def as_tensor(data, shape, dtype):
    return torch.frombuffer(bytearray(data), dtype=dtype).reshape(shape)


def invert_basis(x, block, direction):
    shape = x.shape
    for i in range(block.bit_length() - 1):
        a, b = x.reshape(-1, block // (2 << i), 2, 1 << i).unbind(2)
        x = torch.stack((a + b, a - b), dim=2)
    return (x.reshape(shape) / math.sqrt(block)) * direction


class Original:
    def __init__(self, source, sample_cache, offline, cache_gib):
        self.arc = Archive(source)
        self.fields = self.arc.fields
        self.assets = Path(source)
        self.cache = Path(sample_cache)
        self.cache.mkdir(parents=True, exist_ok=True)
        marker = self.cache / "revision.txt"
        if marker.exists() and marker.read_text().strip() != self.arc.revision:
            raise ValueError("BF16 samples belong to a different model")
        atomic_bytes(marker, self.arc.revision.encode())
        self.cap = int(cache_gib * 2**30)
        self.cache_bytes = sum(f.stat().st_size for f in self.cache.glob("*.raw"))
        self.offline = offline
        self.lock = threading.Lock()
        self.stats = Counter()

    def data(self, key, row=0, count=None):
        field = self.fields[key]
        shape = field["shape"]
        count = shape[0] - row if count is None else count
        if row < 0 or count < 1 or row + count > shape[0]:
            raise ValueError(f"Invalid BF16 slice of {key}")
        stride = math.prod(shape[1:]) * ITEMSIZE[field["dtype"]]
        size = count * stride
        native = self.arc.cached_path(key)
        path = self.cache / f"{key}.{row}.{count}.raw"
        if native.is_file():
            with native.open("rb") as f:
                f.seek(row * stride)
                data = f.read(size)
            origin = "local_backbone_bytes"
        elif path.is_file():
            data = path.read_bytes()
            origin = "local_sample_bytes"
        else:
            if self.offline:
                raise FileNotFoundError(
                    f"Offline BF16 sample missing: {key}[{row}:{row + count}]"
                )
            data = self.arc.read(key, row * stride, size)
            origin = "remote_bytes"
            with self.lock:
                if self.cache_bytes + size <= self.cap:
                    check_resources(self.cache, size)
                    atomic_bytes(path, data)
                    self.cache_bytes += size
        if len(data) != size:
            raise OSError(f"Invalid source extent for {key}")
        with self.lock:
            self.stats[origin] += size
        return as_tensor(data, (count, *shape[1:]), DTYPES[field["dtype"]])

    def get(self, key, device, dtype=None):
        return self.data(key).to(device=device, dtype=dtype)

    def expert(self, layer, expert):
        base = f"model.layers.{layer}.mlp.experts."
        return self.data(base + "gate_up_proj", expert, 1)[0], self.data(
            base + "down_proj", expert, 1
        )[0]

    def row(self, key, index):
        return self.data(key, index, 1)[0]

    def decode(self, val, device, dtype):
        return val.to(device=device, dtype=dtype)


class Packed:
    def __init__(
        self,
        path,
        gguf,
        prism_bin,
        assets,
        partial=False,
        cuda_codec=None,
        architecture=ARCH,
        prefix="hy4",
        asset_names=ASSETS,
    ):
        self.path = Path(path)
        if self.path.name.endswith(".partial") and not partial:
            raise ValueError("Full-model inference requires the completed GGUF")
        self.partial = partial
        self.db_path = self.path.parent / "progress.sqlite"
        self.reader = gguf.GGUFReader(self.path)
        fields = self.reader.fields
        if fields["general.architecture"].contents() != architecture:
            raise ValueError("Unexpected GGUF architecture")
        self.assets = Path(assets)
        self.assets.mkdir(parents=True, exist_ok=True)
        for name in asset_names:
            expected = fields[prefix + ".source." + name].contents().encode("utf-8")
            dest = self.assets / name
            if dest.exists() and dest.read_bytes() != expected:
                raise ValueError(f"Cached GGUF asset differs: {name}")
            if not dest.exists():
                atomic_bytes(dest, expected)
        dirs = {f.name: f for f in self.reader.tensors}
        plan = json.loads(fields[prefix + ".source.layout"].contents())
        self.fields, self.physical = {}, {}
        for t in plan:
            v = dirs[t["name"]]
            if (
                list(reversed(v.shape.tolist())) != t["shape"]
                or int(v.tensor_type) != t["type"]
                or v.n_bytes != t["bytes"]
            ):
                raise ValueError(f"Invalid GGUF descriptor: {t['name']}")
            t["offset"] = v.data_offset
            self.fields[t["source"]] = {"shape": t["origin"]}
            self.physical[t["name"] if t["role"] == "routed" else t["source"]] = t
        self.directions = {
            w: torch.from_numpy(
                np.frombuffer(
                    base64.b64decode(fields[f"{prefix}.signs.{w}"].contents()),
                    dtype=np.int8,
                ).copy()
            )
            for w in {t["shape"][-1] for t in plan if t["block"]}
        }
        with os.add_dll_directory(str(prism_bin)):
            self.codec = PrismCodec(ctypes.CDLL(str(prism_bin / "ggml-base.dll")))
        self.stats = Counter()
        self.lock = threading.Lock()
        self.fused = None
        self.gpu_directions = {}
        if cuda_codec:
            from cuda_codec import CudaCodec

            self.fused = CudaCodec(cuda_codec)

    def raw(self, key, row=0, count=None):
        t = self.physical[key]
        rows = math.prod(t["shape"][:-1]) if t["type"] == 142 else t["shape"][0]
        count = rows - row if count is None else count
        if row < 0 or count < 1 or row + count > rows:
            raise ValueError(f"Invalid GGUF slice of {key}")
        stride = t["bytes"] // rows
        if self.partial:
            db = sqlite3.connect(f"{self.db_path.as_uri()}?mode=ro", uri=True)
            try:
                written = db.execute(
                    "SELECT coalesce(sum(size),0) FROM chunks WHERE name=?",
                    (t["name"],),
                ).fetchone()[0]
            finally:
                db.close()
            if (row + count) * stride > written:
                raise ValueError(f"Requested bytes not yet verified for {key}")
        with self.path.open("rb") as file:
            file.seek(t["offset"] + row * stride)
            data = file.read(count * stride)
        if len(data) != count * stride:
            raise OSError(f"Truncated GGUF tensor {key}")
        with self.lock:
            self.stats["local_gguf_bytes"] += len(data)
        return t, data, count

    def decode(self, item, device, dtype):
        t, data, count = item
        if t["type"] != 142:
            return as_tensor(data, (count, *t["origin"][1:]), NATIVE[t["type"]]).to(
                device=device, dtype=dtype
            )
        width = t["shape"][-1]
        if self.fused and str(device).startswith("cuda"):
            key = (str(device), width)
            if key not in self.gpu_directions:
                self.gpu_directions[key] = self.directions[width].to(device)
            return self.fused.decode(
                data, count, t, self.gpu_directions[key], device, dtype
            )
        src = np.frombuffer(data, dtype=np.uint8)
        stride = width // GROUP * 34
        tile = max(1, 2**20 // width)
        direction = self.directions[width].to(device)
        out = torch.empty(
            (count, t["original_width"]), device=device, dtype=dtype or torch.bfloat16
        )
        for start in range(0, count, tile):
            end = min(start + tile, count)
            x = self.codec.decode(
                src[start * stride : end * stride], (end - start, width)
            )
            x = invert_basis(torch.from_numpy(x).to(device), t["block"], direction)
            out[start:end].copy_(x[:, : t["original_width"]])
        return out

    def get(self, key, device, dtype=None):
        raw = self.raw(key)
        return self.decode(raw, device, dtype).reshape(self.physical[key]["origin"])

    def expert(self, layer, expert):
        def read(proj):
            return self.raw(f"blk.{layer}.ffn_{proj}_exps.weight", expert * 1536, 1536)

        return (read("gate"), read("up")), read("down")

    def row(self, key, index):
        return self.raw(key, index, 1)
