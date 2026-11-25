"""Build and verify one GGUF containing the full original Hy4-Flash topology."""

from __future__ import annotations

import argparse
import base64
import ctypes
import hashlib
import json
import math
import msvcrt
import os
import re
import sqlite3
import sys
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing, contextmanager
from pathlib import Path

import numpy as np

from experiment import GROUP, SEED, PrismCodec, fit_ternary
from source_archive import Archive, atomic_bytes
from stream_routed import check_resources

MODEL = "Hy4-Bonsai2-PQ2_0.gguf"
ARCH = "hy4_bonsai2"
TYPE = {"F32": 0, "F16": 1, "I32": 26, "I64": 27, "BF16": 30, "PQ2_0": 142}
ALIGN = 32
MAX_INPUT = 8 * 1024**2
ROUTE = re.compile(r"model\.layers\.(\d+)\.mlp\.experts\.(down_proj|gate_up_proj)$")


def align(n, block=ALIGN):
    return (n + block - 1) // block * block


def signs(width):
    return np.random.default_rng(SEED).choice(
        np.array([-1, 1], dtype=np.int8), size=width
    )


def transform(x, block):
    shape = x.shape
    data = x.astype(np.float32, copy=True).reshape(-1, block)
    for i in range(block.bit_length() - 1):
        stride = 1 << i
        pair = data.reshape(len(data), -1, 2, stride)
        left, right = pair[:, :, 0].copy(), pair[:, :, 1].copy()
        pair[:, :, 0], pair[:, :, 1] = left + right, left - right
    return (data / math.sqrt(block)).reshape(shape)


def tensor_plan(archive):
    result = []
    for ordinal, (source, f) in enumerate(sorted(archive.fields.items())):
        shape = f["shape"]
        match = ROUTE.fullmatch(source)
        if match:
            layer, kind = match.groups()
            for projection in ["gate", "up"] if kind == "gate_up_proj" else ["down"]:
                result.append(
                    dict(
                        name=f"blk.{layer}.ffn_{projection}_exps.weight",
                        source=source,
                        role="routed",
                        shape=[512, 1536, 1536],
                        origin=shape,
                        type=142,
                        block=512,
                        original_width=1536,
                        bytes=512 * 1536 * 408,
                        layer=int(layer),
                        projection=projection,
                    )
                )
            continue
        role = (
            "vision"
            if source.startswith("vit.")
            else "dfly2"
            if source.startswith("model.dfly_layers.")
            else "engram"
            if source.endswith(".multi_head_embedding.embedding.weight")
            else "backbone"
        )
        # Preserve integer maps and native scales, norms and attention-bias vectors.
        quant = f["dtype"] == "BF16" and len(shape) >= 2
        width = math.prod(shape[1:]) if len(shape) >= 2 else shape[0]
        storage = align(width, GROUP) if quant else width
        physical = [shape[0], storage] if quant else shape
        size = shape[0] * (storage // GROUP) * 34 if quant else f["length"]
        name = source if len(source.encode()) < 64 else f"hy4.tensor.{ordinal:04d}"
        result.append(
            dict(
                name=name,
                source=source,
                role=role,
                shape=physical,
                origin=shape,
                original_width=width,
                type=142 if quant else TYPE[f["dtype"]],
                bytes=size,
                block=(512 if storage % 512 == 0 else 128) if quant else 0,
            )
        )
    if len({t["name"] for t in result}) != len(result):
        raise ValueError("The physical GGUF tensor names collide")
    return result


def mark_sparse(handle):
    from ctypes import wintypes

    ctl = ctypes.WinDLL("kernel32", use_last_error=True).DeviceIoControl
    ctl.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.c_void_p,
    ]
    actual = wintypes.DWORD()
    h = msvcrt.get_osfhandle(handle.fileno())
    uncompressed = ctypes.c_uint16(0)
    if not ctl(
        h, 0x9C040, ctypes.byref(uncompressed), 2, None, 0, ctypes.byref(actual), None
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    if not ctl(h, 0x900C4, None, 0, None, 0, ctypes.byref(actual), None):
        raise ctypes.WinError(ctypes.get_last_error())


def set_sparse_length(handle, length):
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    seek = kernel.SetFilePointerEx
    seek.argtypes = [wintypes.HANDLE, ctypes.c_int64, ctypes.c_void_p, wintypes.DWORD]
    eof = kernel.SetEndOfFile
    eof.argtypes = [wintypes.HANDLE]
    h = msvcrt.get_osfhandle(handle.fileno())
    if not seek(h, length, None, 0) or not eof(h):
        raise ctypes.WinError(ctypes.get_last_error())


def init(args, gguf, archive):
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    target = out / (MODEL + ".partial")
    if target.exists() or (out / MODEL).exists():
        raise FileExistsError(
            "The destination already contains a model. Resume with write."
        )
    check_resources(out, 16 * 1024**2)
    plan = tensor_plan(archive)
    temp = out / (MODEL + ".building-header")
    writer = gguf.GGUFWriter(temp, ARCH)
    writer.add_type("model")
    writer.add_name("Hy4 Flash Bonsai2 PQ2_0")
    writer.add_uint32("general.quantization_version", 2)
    writer.add_string("hy4.source.repository", "tencent/Hy4-flash")
    writer.add_string("hy4.source.revision", archive.revision)
    writer.add_string("hy4.source.layout", json.dumps(plan, separators=(",", ":")))
    for name in (
        "config.json",
        "tokenizer.json",
        "processor_config.json",
        "generation_config.json",
        "tokenizer_config.json",
        "chat_template.jinja",
    ):
        writer.add_string(
            "hy4.source." + name, (archive.root / name).read_text(encoding="utf-8")
        )
    # Carry the signed input basis explicitly for each physical width.
    for width in sorted({t["shape"][-1] for t in plan if t["block"]}):
        writer.add_string(
            f"hy4.signs.{width}",
            base64.b64encode(signs(width).tobytes()).decode("ascii"),
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
    with temp.open("r+b") as f:
        mark_sparse(f)
        pos = align(f.seek(0, os.SEEK_END))
        for t in plan:
            t["offset"] = pos
            pos += align(t["bytes"])
        set_sparse_length(f, pos)
    with closing_index(temp, gguf, plan):
        pass
    atomic_bytes(
        out / "layout.json",
        json.dumps(
            {"revision": archive.revision, "length": pos, "tensors": plan},
            separators=(",", ":"),
        ).encode(),
    )
    with closing(database(out)) as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS chunks(name TEXT, pos INTEGER, size INTEGER, digest BLOB, PRIMARY KEY(name,pos))"
        )
        db.commit()
    os.replace(temp, target)
    print(
        f"Indexed {len(plan)} GGUF tensors, {pos / 2**30:.3f} GiB logical size.",
        flush=True,
    )


@contextmanager
def closing_index(path, gguf, plan):
    reader = gguf.GGUFReader(path)
    try:
        if len(reader.tensors) != len(plan):
            raise ValueError("GGUF tensor count differs from the source plan")
        for item, t in zip(reader.tensors, plan, strict=True):
            if (
                item.name,
                list(reversed(item.shape.tolist())),
                item.n_bytes,
                int(item.tensor_type),
                item.data_offset,
            ) != (t["name"], t["shape"], t["bytes"], t["type"], t["offset"]):
                raise ValueError(f"GGUF descriptor mismatch for {t['name']}")
        yield reader
    finally:
        del reader


def database(root):
    db = sqlite3.connect(root / "progress.sqlite", timeout=60)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    return db


class Encoder:
    def __init__(self, bin_path, device, cuda_codec=None):
        with os.add_dll_directory(str(bin_path)):
            self.codec = PrismCodec(ctypes.CDLL(str(bin_path / "ggml-base.dll")))
        self.device = device
        self.fused = None
        if cuda_codec:
            from cuda_codec import CudaCodec

            self.fused = CudaCodec(cuda_codec)
        elif device == "cuda":
            import torch

            self.torch = torch
            free, _ = torch.cuda.mem_get_info()
            if free < 1536 * 1024**2:
                raise RuntimeError(
                    "Insufficient free VRAM for the CUDA calibration tile"
                )

    def levels_gpu(self, matrix, block, direction):
        torch = self.torch
        x = torch.from_numpy(matrix).to("cuda") * torch.from_numpy(direction).to("cuda")
        for i in range(block.bit_length() - 1):
            a, b = x.reshape(-1, block // (2 << i), 2, 1 << i).unbind(2)
            x = torch.stack([a + b, a - b], dim=2)
        x = (x / math.sqrt(block)).reshape(-1, GROUP)
        magnitudes, order = x.abs().sort(dim=-1, descending=True, stable=True)
        prefix = magnitudes.cumsum(-1, dtype=torch.float64)
        count = torch.arange(1, GROUP + 1, device="cuda")
        scale = (prefix / count).half().double()
        best = (2 * scale * prefix - count * scale.square()).argmax(-1, keepdim=True)
        selected = torch.empty_like(order, dtype=torch.bool).scatter_(
            1, order, (count - 1) <= best
        )
        return (
            ((x.sign() * selected) * scale.gather(1, best).float())
            .reshape(matrix.shape)
            .cpu()
            .numpy()
        )

    def encode(self, data, t):
        width, physical = t["original_width"], t["shape"][-1]
        source = np.frombuffer(data, dtype="<u2").reshape(-1, width)
        direction = signs(physical)
        if self.fused:
            packed = self.fused.encode(source, width, direction, t["block"])
            if not self.codec.validate(142, packed.ctypes.data, packed.nbytes):
                raise ValueError("PrismML rejected the fused PQ2_0 payload")
            return packed.tobytes()
        rows = max(1, (1024 * 1024) // physical)
        parts = []
        for start in range(0, len(source), rows):
            x = (source[start : start + rows].astype(np.uint32) << 16).view(np.float32)
            if width != physical:
                x = np.pad(x, ((0, 0), (0, physical - width)))
            if self.device == "cuda":
                levels = self.levels_gpu(x, t["block"], direction)
            else:
                levels = fit_ternary(transform(x * direction, t["block"]))
            parts.append(self.codec.encode(levels).tobytes())
        return b"".join(parts)


def record_chunk(output, db, file, t, pos, data):
    if not data or pos + len(data) > t["bytes"]:
        raise ValueError("Invalid output chunk")
    check_resources(output, len(data))
    file.seek(t["offset"] + pos)
    if file.write(data) != len(data):
        raise OSError("Short GGUF write")
    file.flush()
    os.fsync(file.fileno())
    file.seek(t["offset"] + pos)
    if file.read(len(data)) != data:
        raise OSError("GGUF read-back differs from the encoded bytes")
    digest = hashlib.blake2b(data, digest_size=16).digest()
    db.execute(
        "INSERT INTO chunks VALUES (?,?,?,?)", (t["name"], pos, len(data), digest)
    )
    db.commit()


def write_source(args, archive, db, file, t, encoder, pos):
    quant = t["type"] == 142
    width = t["original_width"]
    row_input = 2 * width if quant else 1
    row_output = t["shape"][-1] // GROUP * 34 if quant else 1
    if pos % row_output:
        raise ValueError("Misaligned resume offset")
    rows_per_read = max(1, MAX_INPUT // row_input)
    total_rows = t["bytes"] // row_output

    def chunks():
        for first in range(pos // row_output, total_rows, rows_per_read):
            yield first, min(total_rows - first, rows_per_read)

    spans = iter(chunks())
    depth = args.readers if t["role"] == "engram" else 1
    ticks = np.zeros(3)
    completed = 0
    batch = bytearray()
    batch_start = pos
    with ThreadPoolExecutor(max_workers=depth) as pool:
        pending = deque()

        def enqueue():
            item = next(spans, None)
            if item is not None:
                first, count = item
                pending.append(
                    (
                        first,
                        count,
                        pool.submit(
                            archive.read,
                            t["source"],
                            first * row_input,
                            count * row_input,
                        ),
                    )
                )

        for _ in range(depth):
            enqueue()
        while pending:
            first, count, future = pending.popleft()
            start = time.monotonic()
            data = future.result()
            ticks[0] += time.monotonic() - start
            enqueue()
            start = time.monotonic()
            if quant:
                data = encoder.encode(data, t)
            ticks[1] += time.monotonic() - start
            if len(data) != count * row_output:
                raise ValueError("Quantiser output size differs from its descriptor")
            start = time.monotonic()
            batch.extend(data)
            if (
                t["role"] != "engram"
                or len(batch) >= 32 * 1024**2
                or first + count == total_rows
            ):
                record_chunk(args.output, db, file, t, batch_start, batch)
                batch_start += len(batch)
                batch.clear()
            ticks[2] += time.monotonic() - start
            completed += 1
            if completed % 32 == 0 and t["role"] == "engram":
                print(
                    f"Rows {first + count}/{total_rows} cumulative wait, fit, write seconds {ticks.round(2).tolist()}",
                    flush=True,
                )


def bank_file(args, t):
    layer = t["layer"]
    root = args.first_layer if layer == 1 else args.routed
    folder = (
        root / f"layer-{layer}-{'down' if t['projection'] == 'down' else 'gate-up'}"
    )
    return folder / "routed-experts.gguf"


def import_bank(args, gguf, archive, db, file, t, pos):
    path = bank_file(args, t)
    from run_routed import verified

    verified(
        path.parent,
        t["layer"],
        "down_proj" if t["projection"] == "down" else "gate_up_proj",
        archive.revision,
    )
    reader = gguf.GGUFReader(path)
    bank = next(item for item in reader.tensors if item.name == t["name"])
    if (
        list(reversed(bank.shape.tolist())) != t["shape"]
        or int(bank.tensor_type) != 142
        or bank.n_bytes != t["bytes"]
    ):
        raise ValueError("Invalid input bank")
    with path.open("rb") as src:
        src.seek(bank.data_offset + pos)
        for start in range(pos, t["bytes"], MAX_INPUT):
            n = min(MAX_INPUT, t["bytes"] - start)
            data = src.read(n)
            if len(data) != n:
                raise OSError("Truncated bank")
            record_chunk(args.output, db, file, t, start, data)


def release_imported(args, gguf, archive, db, plan):
    """Retire only current-run staging whose exact bytes are in the master."""
    state = json.loads((args.routed / "routed-status.json").read_bytes())
    published = set(state["complete_banks"])
    groups = {}
    for t in plan:
        if t["role"] == "routed" and t["layer"] > 1:
            groups.setdefault(bank_file(args, t), []).append(t)
    for path, tensors in groups.items():
        folder = path.parent.resolve()
        if (
            folder.parent != args.routed.resolve()
            or folder.name not in published
            or not path.is_file()
        ):
            continue
        if any(
            db.execute(
                "SELECT coalesce(sum(size),0) FROM chunks WHERE name=?", (t["name"],)
            ).fetchone()[0]
            != t["bytes"]
            for t in tensors
        ):
            continue
        reader = gguf.GGUFReader(path)
        offsets = {v.name: v.data_offset for v in reader.tensors}
        del reader
        if set(offsets) != {t["name"] for t in tensors}:
            raise ValueError("Staging GGUF contains additional tensors")
        with path.open("rb") as src:
            for t in tensors:
                src.seek(offsets[t["name"]])
                pos = 0
                for start, n, digest in db.execute(
                    "SELECT pos,size,digest FROM chunks WHERE name=? ORDER BY pos",
                    (t["name"],),
                ):
                    if (
                        pos != start
                        or hashlib.blake2b(src.read(n), digest_size=16).digest()
                        != digest
                    ):
                        raise ValueError(
                            "Original bank differs from the independently read-back master"
                        )
                    pos += n
        atomic_bytes(
            folder / "assembled.json",
            json.dumps(
                {
                    "revision": archive.revision,
                    "model_directory": str(args.output.resolve()),
                    "tensors": [t["name"] for t in tensors],
                },
                indent=2,
            ).encode(),
        )
        path.unlink()
        print(
            f"Integrated {folder.name} and released its duplicate staging copy.",
            flush=True,
        )


def work(args, gguf, archive, plan):
    target = args.output / (MODEL + ".partial")
    encoder = (
        Encoder(args.prism_bin, args.device, args.cuda_codec)
        if args.role != "routed"
        else None
    )
    todo = [t for t in plan if t["role"] == args.role]
    if args.role == "routed":
        todo.sort(key=lambda t: (t["layer"], t["projection"]))
    with target.open("r+b", buffering=0) as f, closing(database(args.output)) as db:
        for t in todo:
            pos = db.execute(
                "SELECT coalesce(sum(size),0) FROM chunks WHERE name=?", (t["name"],)
            ).fetchone()[0]
            if pos == t["bytes"]:
                continue
            if args.role == "routed":
                if not (bank_file(args, t).parent / "conversion.json").is_file():
                    continue
                import_bank(args, gguf, archive, db, f, t, pos)
            else:
                print(f"{t['role']} {t['source']} ({pos}/{t['bytes']})", flush=True)
                write_source(args, archive, db, f, t, encoder, pos)
        if args.release_staging:
            release_imported(args, gguf, archive, db, plan)
        return all(
            db.execute(
                "SELECT coalesce(sum(size),0) FROM chunks WHERE name=?", (t["name"],)
            ).fetchone()[0]
            == t["bytes"]
            for t in todo
        )


def finish(args, gguf, plan):
    partial = args.output / (MODEL + ".partial")
    with (
        closing_index(partial, gguf, plan),
        partial.open("rb") as f,
        closing(database(args.output)) as db,
    ):
        for t in plan:
            pos = 0
            for start, n, digest in db.execute(
                "SELECT pos,size,digest FROM chunks WHERE name=? ORDER BY pos",
                (t["name"],),
            ):
                if start != pos:
                    raise ValueError(f"Unwritten range in {t['name']}")
                f.seek(t["offset"] + pos)
                if hashlib.blake2b(f.read(n), digest_size=16).digest() != digest:
                    raise OSError(f"GGUF payload changed after read-back: {t['name']}")
                pos += n
            if pos != t["bytes"]:
                raise ValueError(f"Incomplete tensor {t['name']}: {pos}/{t['bytes']}")
    final = args.output / MODEL
    if final.exists():
        raise FileExistsError(final)
    os.rename(partial, final)
    print(f"Verified and published locally: {final}", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("init", "write", "finish"))
    for name in ("source", "output", "gguf-python"):
        p.add_argument("--" + name, required=True, type=Path)
    p.add_argument("--prism-bin", type=Path)
    p.add_argument("--first-layer", type=Path)
    p.add_argument("--routed", type=Path)
    p.add_argument(
        "--role", choices=("routed", "engram", "vision", "dfly2", "backbone")
    )
    p.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    p.add_argument("--cuda-codec", type=Path)
    p.add_argument("--readers", type=int, choices=range(1, 9), default=4)
    p.add_argument("--follow-routed", action="store_true")
    p.add_argument("--release-staging", action="store_true")
    args = p.parse_args()
    if (args.follow_routed or args.release_staging) and (
        args.action != "write" or args.role != "routed"
    ):
        p.error("Only routed import accepts --follow-routed and --release-staging")
    if args.action == "write" and (
        not args.role
        or (args.role == "routed" and not (args.routed and args.first_layer))
        or (args.role != "routed" and not args.prism_bin)
    ):
        p.error("Specify the role and its model or codec paths")
    sys.path.insert(0, str(args.gguf_python.resolve(strict=True)))
    import gguf

    archive = Archive(args.source)
    if args.action == "init":
        init(args, gguf, archive)
        return
    layout = json.loads((args.output / "layout.json").read_bytes())
    if layout["revision"] != archive.revision:
        raise ValueError("Checkpoint changed after GGUF creation")
    with (args.output / (f"{args.role or args.action}.lock")).open("a+b") as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        if args.action == "write":
            while (
                not work(args, gguf, archive, layout["tensors"]) and args.follow_routed
            ):
                time.sleep(30)
        else:
            finish(args, gguf, layout["tensors"])


if __name__ == "__main__":
    main()
