"""Read genuine, revision-pinned Inkling expert weights and their published quantisation scales."""

import json
import math
from collections import OrderedDict
from pathlib import Path

import numpy as np

from source import atomic_bytes, retry_range, session


REPO = "thinkingmachines/Inkling-2-Mini"
E2M1 = np.array([0, .5, 1, 1.5, 2, 3, 4, 6, -0., -.5, -1, -1.5, -2, -3, -4, -6], np.float32)
_CODES = np.arange(256, dtype=int)
_E = (_CODES & 127) >> 3
E4M3 = np.where(_E == 0, np.ldexp((_CODES % 8) / 8., -6),
                np.ldexp(1 + (_CODES % 8) / 8., _E - 7)).astype(np.float32)
E4M3[_CODES >= 128] *= -1
E4M3[(_CODES & 127) == 127] = np.nan
DTYPE = {"F8_E4M3": "u1", "U8": "u1", "BF16": "<u2", "F32": "<f4", "F16": "<f2"}


class Original:
    def __init__(self, directory):
        self.directory = Path(directory)
        s = json.loads((self.directory / "source.json").read_bytes())
        if s["repository"] != REPO:
            raise ValueError("Phase II requires the original Thinking Machines Lab checkpoint")
        self.revision = s["revision"]
        headers = json.loads((self.directory / "headers.json").read_bytes())
        self.filename, descriptor = next((k, v) for k, v in headers.items() if k.startswith("model-"))
        self.header = descriptor["tensors"]
        self.base = descriptor["base"]
        self.url = f"https://huggingface.co/{REPO}/resolve/{self.revision}/{self.filename}"
        self.published = self.directory / self.filename
        self.cache_limit=0
        self.cache_bytes=0
        self.banks=OrderedDict()
        groups = json.loads((self.directory / "hf_quant_config.json").read_bytes())["model"]["parameter_groups"]
        self.schemes = {name: group for group in groups for name in group.get("tensors", [])
                        if name.endswith((".w13_weight", ".w2_weight"))}
        if len(self.schemes) != 48:
            raise ValueError("Expected 48 physical expert banks")

    def read(self, key, begin=0, count=None, cache_ranges=False):
        d = self.header[key]
        dtype = np.dtype(DTYPE[d["dtype"]])
        n = math.prod(d["shape"])
        count = n - begin if count is None else count
        if begin < 0 or count <= 0 or begin + count > n:
            raise ValueError(f"Out-of-bounds range for {key}")
        size = count * dtype.itemsize
        at = self.base + d["data_offsets"][0] + begin * dtype.itemsize
        local = self.published
        if local.is_file() and (self.directory / (self.filename + ".verified.json")).is_file():
            if self.cache_limit and (key in self.schemes or any(key.startswith(k+"_") for k in self.schemes)):
                bank_size=n*dtype.itemsize
                if key not in self.banks and bank_size<=self.cache_limit:
                    import psutil
                    while self.banks and (self.cache_bytes+bank_size>self.cache_limit or
                                          psutil.virtual_memory().available<bank_size+4*2**30):
                        _,old=self.banks.popitem(last=False)
                        self.cache_bytes-=old.nbytes
                    if psutil.virtual_memory().available>=bank_size+4*2**30:
                        with local.open("rb") as f:
                            f.seek(self.base+d["data_offsets"][0]);bank=np.fromfile(f,dtype=dtype,count=n)
                        if len(bank)!=n:raise EOFError(key)
                        self.banks[key]=bank;self.cache_bytes+=bank.nbytes
                if key in self.banks:
                    self.banks.move_to_end(key)
                    return self.banks[key][begin:begin+count]
            with local.open("rb") as f:
                f.seek(at)
                data = f.read(size)
        else:
            cached = self.directory / "ranges" / self.revision / f"{at}-{size}.bin"
            if cache_ranges and cached.is_file():
                data = cached.read_bytes()
            else:
                data = retry_range(session(), self.url, at, size)
                if cache_ranges:
                    cached.parent.mkdir(parents=True, exist_ok=True)
                    atomic_bytes(cached, data)
        if len(data) != size:
            raise IOError(f"Truncated range for {key}")
        return np.frombuffer(data, dtype)

    def parts(self, key, expert, row=0, rows=None, cache_ranges=False):
        group = self.schemes[key]
        scheme = group["weight_transform"]
        nv = scheme == "nvfp4_nearest"
        if not nv and scheme != "mxfp8_nearest":
            raise ValueError("Unsupported original block quantiser")
        e, height, packed = self.header[key]["shape"]
        rows = height - row if rows is None else rows
        if not 0 <= expert < e or row < 0 or rows <= 0 or row + rows > height:
            raise ValueError("Invalid physical expert or row interval")
        width = packed * (2 if nv else 1)
        block = 16 if nv else 32
        scale_key = key + "_scale"
        if self.header[scale_key]["shape"] != [e, height, width // block]:
            raise ValueError("Published scale dimensions do not match expert weights")
        def part(name, cols):
            return self.read(name, (expert * height + row) * cols, rows * cols, cache_ranges).reshape(rows, cols)
        weights = part(key, packed)
        scale = part(scale_key, width // block)
        if nv:
            if group.get("weight_scale_format") != "amax_denominator":
                raise ValueError("Missing NVFP4 outer scale scheme")
            a = self.read(key + "_amax", expert, 1, cache_ranges)
            d = self.read(key + "_outer_scale_denominator", 0, 1, cache_ranges)
            if not np.isfinite(a[0]) or a[0] < 0 or not np.isfinite(d[0]) or d[0] <= 0:
                raise ValueError("Invalid NVFP4 outer scale")
            return weights, scale, a, d
        return weights, scale, None, None


def reconstruct(parts):
    weight, scale, a, d = parts
    if a is not None:
        w = np.stack((E2M1[weight & 15], E2M1[weight >> 4]), axis=-1)
        w = w.reshape(*scale.shape, 16) * E4M3[scale][..., None]
        w *= a[0] / d[0]
    else:
        if np.any(scale == 255):
            raise ValueError("Invalid MXFP8 exponent code")
        w = np.ldexp(E4M3[weight].reshape(*scale.shape, 32), scale.astype(np.int32)[..., None] - 127)
    w = w.reshape(weight.shape[0], -1)
    if not np.isfinite(w).all():
        raise ValueError("Non-finite reconstructed weights")
    return w


def reference_bf16(parts):
    import torch
    from transformers.core_model_loading import Inkling2LoopDequantizeExperts
    w, sc, a, d = parts
    p = [torch.from_numpy(x.copy()) if x is not None else None for x in (w, sc, a, d)]
    p[0] = (p[0] if a is not None else p[0].view(torch.float8_e4m3fn)).unsqueeze(0)
    p[1] = (p[1].view(torch.float8_e4m3fn) if a is not None else p[1]).unsqueeze(0)
    names = ["weight", "scale", "amax", "denominator"]
    state = {name: val for name, val in zip(names, p) if val is not None}
    return Inkling2LoopDequantizeExperts().convert(state, names, ["out"])["out"][0]
