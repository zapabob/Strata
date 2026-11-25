"""Inventory a pinned safetensors checkpoint and read exact native byte ranges."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import struct
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import sleep

import requests

from experiment import REPO
from stream_routed import check_resources, retry_range

ITEMSIZE = {"F32": 4, "BF16": 2, "F16": 2, "I64": 8, "I32": 4, "I8": 1, "U8": 1}
CHUNK = 12 * 1024**2
LOCAL = threading.local()


def session():
    if not hasattr(LOCAL, "session"):
        LOCAL.session = requests.Session()
    return LOCAL.session


def atomic_bytes(path, data):
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def download(url):
    for attempt in range(5):
        try:
            with session().get(url, timeout=(10, 60)) as response:
                response.raise_for_status()
                return response.content
        except requests.RequestException:
            if attempt == 4:
                raise
            sleep(2**attempt)


def inventory(root: Path, revision: str):
    if not re.fullmatch("[0-9a-f]{40}", revision):
        raise ValueError("Expected an immutable checkpoint revision")
    root.mkdir(parents=True, exist_ok=True)
    prefix = f"{REPO}/resolve/{revision}"
    marker = root / "revision.txt"
    if marker.exists() and marker.read_text().strip() != revision:
        raise ValueError("The directory belongs to another checkpoint")
    atomic_bytes(marker, (revision + "\n").encode())
    for name in (
        "config.json",
        "model.safetensors.index.json",
        "generation_config.json",
        "tokenizer_config.json",
        "processor_config.json",
        "chat_template.jinja",
        "tokenizer.json",
    ):
        target = root / name
        if not target.exists():
            atomic_bytes(target, download(f"{prefix}/{name}"))
    index = json.loads((root / "model.safetensors.index.json").read_bytes())
    mapping = index["weight_map"]
    groups = {}
    for key, shard in mapping.items():
        groups.setdefault(shard, set()).add(key)

    def inspect(shard):
        if not re.fullmatch(r"model-\d{5}-of-\d{5}\.safetensors", shard):
            raise ValueError(f"Invalid shard {shard}")
        url = f"{prefix}/{shard}"
        header_size = struct.unpack("<Q", retry_range(session(), url, 0, 8))[0]
        if not 0 < header_size < 8 * 1024**2:
            raise ValueError("Invalid safetensors header length")
        obj = json.loads(retry_range(session(), url, 8, header_size))
        obj.pop("__metadata__", None)
        if set(obj) != groups[shard]:
            raise ValueError(f"The index and shard disagree for {shard}")
        end = 0
        for value in sorted(obj.values(), key=lambda item: item["data_offsets"]):
            start, stop = value.pop("data_offsets")
            if (
                start != end
                or stop - start != math.prod(value["shape"]) * ITEMSIZE[value["dtype"]]
            ):
                raise ValueError(f"Unexpected tensor extent in {shard}")
            end = stop
            value.update(
                shard=shard, offset=8 + header_size + start, length=stop - start
            )
        return obj

    with ThreadPoolExecutor(max_workers=8) as pool:
        catalogue = {
            k: v
            for shard in pool.map(inspect, sorted(groups))
            for k, v in shard.items()
        }
    total = sum(x["length"] for x in catalogue.values())
    if total != index["metadata"]["total_size"] or catalogue.keys() != mapping.keys():
        raise ValueError("Incomplete source catalogue")
    atomic_bytes(
        root / "catalogue.json", json.dumps(catalogue, sort_keys=True).encode()
    )
    print(
        f"Verified {len(catalogue)} tensors in {len(groups)} shards ({total:,} bytes).",
        flush=True,
    )


class Archive:
    def __init__(self, root):
        self.root = Path(root)
        self.revision = (self.root / "revision.txt").read_text().strip()
        self.fields = json.loads((self.root / "catalogue.json").read_bytes())
        self.prefix = f"{REPO}/resolve/{self.revision}"

    def cached_path(self, name):
        if name not in self.fields or not re.fullmatch(r"[A-Za-z0-9_.]+", name):
            raise ValueError("Invalid source tensor name")
        return self.root / "native" / (name + ".bin")

    def read(self, name, offset=0, size=None):
        field = self.fields[name]
        size = field["length"] - offset if size is None else size
        if offset < 0 or size < 0 or offset + size > field["length"]:
            raise ValueError(f"Read would cross {name} boundaries")
        path = self.cached_path(name)
        if path.is_file():
            if path.stat().st_size != field["length"]:
                raise ValueError(f"Invalid cached tensor {name}")
            with path.open("rb") as file:
                file.seek(offset)
                data = file.read(size)
            if len(data) != size:
                raise OSError(f"Short read for {name}")
            return data
        url = f"{self.prefix}/{field['shard']}"
        parts = []
        for pos in range(0, size, CHUNK):
            parts.append(
                retry_range(
                    session(),
                    url,
                    field["offset"] + offset + pos,
                    min(CHUNK, size - pos),
                )
            )
        return b"".join(parts)


def bulk_source(name):
    return ".mlp.experts." in name or name.endswith(
        ".multi_head_embedding.embedding.weight"
    )


def cache_backbone(root):
    archive = Archive(root)
    (root / "native").mkdir(exist_ok=True)
    groups = []
    for name, f in sorted(
        archive.fields.items(), key=lambda item: (item[1]["shard"], item[1]["offset"])
    ):
        if bulk_source(name):
            continue
        path = archive.cached_path(name)
        if path.exists():
            if path.stat().st_size != f["length"]:
                raise ValueError(f"Truncated published tensor {name}")
            continue
        if groups:
            last = archive.fields[groups[-1][-1]]
            first = archive.fields[groups[-1][0]]
            if (
                last["shard"] == f["shard"]
                and last["offset"] + last["length"] == f["offset"]
                and f["offset"] + f["length"] - first["offset"] <= CHUNK
            ):
                groups[-1].append(name)
                continue
        groups.append([name])

    def fetch(names):
        first, last = archive.fields[names[0]], archive.fields[names[-1]]
        nbytes = last["offset"] + last["length"] - first["offset"]
        url = f"{archive.prefix}/{first['shard']}"
        check_resources(root, min(nbytes, CHUNK))
        if nbytes <= CHUNK:
            data = retry_range(session(), url, first["offset"], nbytes)
            for name in names:
                f = archive.fields[name]
                start = f["offset"] - first["offset"]
                atomic_bytes(
                    archive.cached_path(name), data[start : start + f["length"]]
                )
        else:
            dest = archive.cached_path(names[0])
            temp = dest.with_suffix(".partial")
            pos = temp.stat().st_size if temp.exists() else 0
            if pos > nbytes:
                raise ValueError("Oversized cache staging file")
            with temp.open("ab") as out:
                for start in range(pos, nbytes, CHUNK):
                    count = min(CHUNK, nbytes - start)
                    check_resources(root, count)
                    if (
                        out.write(
                            retry_range(session(), url, first["offset"] + start, count)
                        )
                        != count
                    ):
                        raise OSError("Short source cache write")
            os.replace(temp, dest)
        return len(names)

    # Vision and draft fixtures can run before the language backbone finishes.
    groups.sort(
        key=lambda names: 0 if names[0].startswith(("vit.", "model.dfly")) else 1
    )
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, result in enumerate(pool.map(fetch, groups)):
            if i % 40 == 0:
                print(f"Read {i + 1}/{len(groups)} source ranges", flush=True)
    names = [name for name in archive.fields if not bulk_source(name)]
    if any(
        archive.cached_path(n).stat().st_size != archive.fields[n]["length"]
        for n in names
    ):
        raise OSError("Incomplete backbone cache")
    atomic_bytes(
        root / "native-complete.json",
        json.dumps(
            {
                "tensors": len(names),
                "source_bytes": sum(archive.fields[n]["length"] for n in names),
                "revision": archive.revision,
            },
            indent=2,
        ).encode(),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--first-source", type=Path)
    mode.add_argument("--cache-backbone", action="store_true")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.cache_backbone:
        cache_backbone(args.output)
    else:
        inventory(args.output, json.loads(args.first_source.read_bytes())["revision"])
