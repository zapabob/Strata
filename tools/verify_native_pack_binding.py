"""Read-only binding of an unconverted native pack to already hashed GGUF shards.

This deliberately refuses conversion packs and experts.bin: they need different
payload validation. Dense spans use bounded reads; expert payload identity comes
from the supplied completed full-shard hash receipt and unchanged file metadata.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import logging
from pathlib import Path
import re
from types import SimpleNamespace
from typing import BinaryIO

import gguf_reader as G
import iq_pack as P
import strata_tokenizer as ST


def digest(path: Path) -> str:
    """Hash small metadata and source files only."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_index(path: Path) -> dict[str, list[int]]:
    """Parse every field, refusing duplicate names and ambiguous widths."""
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        fields = line.split()
        if len(fields) != 19:
            raise ValueError("index must have 19 fields")
        if fields[0] in rows:
            raise ValueError("duplicate index tensor")
        values = [int(value) for value in fields[1:]]
        if any(value < 0 for value in values):
            raise ValueError("negative index value")
        rows[fields[0]] = values
    return rows


def compare_span(
    source: BinaryIO,
    dense: BinaryIO,
    source_offset: int,
    dense_offset: int,
    size: int,
    chunk: int = 8 * 1024 * 1024,
) -> str:
    """Compare every byte and return the matched payload SHA-256."""
    if min(source_offset, dense_offset, size) < 0 or chunk <= 0:
        raise ValueError("invalid span")
    source.seek(source_offset)
    dense.seek(dense_offset)
    result = hashlib.sha256()
    remaining = size
    while remaining:
        count = min(remaining, chunk)
        original, packed = source.read(count), dense.read(count)
        if len(original) != count or len(packed) != count:
            raise ValueError("truncated tensor span")
        if original != packed:
            raise ValueError(f"dense bytes differ at chunk offset {size - remaining}")
        result.update(packed)
        remaining -= count
    return result.hexdigest()


def verify_tokenizer(root: Path, metadata: dict) -> dict:
    """Bind vocabulary IDs, merge order, types, specials and exact template."""
    vocab = json.loads((root / "vocab.json").read_text(encoding="utf-8"))
    tokens = metadata["tokenizer.ggml.tokens"]
    if vocab != {token: i for i, token in enumerate(tokens)}:
        raise ValueError("tokenizer vocabulary IDs differ")
    merges = (root / "merges.txt").read_text(encoding="utf-8").splitlines()
    if merges != metadata["tokenizer.ggml.merges"]:
        raise ValueError("tokenizer merges differ")
    types = json.loads((root / "token_type.json").read_text(encoding="utf-8"))
    if types != metadata["tokenizer.ggml.token_type"]:
        raise ValueError("tokenizer token types differ")
    config = json.loads((root / "tokenizer.json").read_text(encoding="utf-8"))
    special = {
        key: int(value)
        for key, value in metadata.items()
        if key.startswith("tokenizer.ggml.") and key.endswith("_token_id")
    }
    expected = {
        "model": metadata["tokenizer.ggml.model"],
        "pre": metadata["tokenizer.ggml.pre"],
        "vocab_size": len(tokens),
        "n_merges": len(merges),
        "special_ids": special,
        "add_bos_token": False,
    }
    if any(config.get(key) != value for key, value in expected.items()):
        raise ValueError("tokenizer configuration differs")
    if config.get("pre_pattern") != ST.QWEN35_PATTERN:
        raise ValueError("tokenizer pre-tokenizer pattern differs")
    template = (root / "chat_template.jinja").read_bytes().decode("utf-8")
    if template != metadata["tokenizer.chat_template"]:
        raise ValueError("tokenizer template differs")
    return {"vocabulary": len(tokens), "merges": len(merges), "special_ids": special}


def receipt_mtime_ns(value: str) -> int:
    """Preserve all Windows 100 ns digits, without floating point rounding."""
    seconds, fraction = value.removesuffix("Z").split(".")
    stamp = datetime.fromisoformat(seconds + "+00:00")
    return int(stamp.timestamp()) * 10**9 + int(fraction.ljust(9, "0"))


def verify(pack: Path, receipt_path: Path) -> dict:
    """Validate this intentionally narrow no-copy, no-conversion pack form."""
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    records = receipt["models"]
    before = {}
    files = []
    where = {}
    for record in records:
        path = Path(record["path"])
        info = path.stat()
        if not (
            record["matches"]
            and record["metadata_unchanged"]
            and record["sha256"] == record["expected_sha256"]
            and info.st_size == record["bytes"]
            and info.st_mtime_ns == receipt_mtime_ns(record["last_write_utc"])
        ):
            raise ValueError(f"source receipt no longer binds {path.name}")
        before[path] = (info.st_size, info.st_mtime_ns)
        header = G.GGUFFile(path)
        files.append(header)
        for tensor in header.tensors:
            size = tensor.expected_bytes()
            if (
                size is None
                or header.data_start + tensor.offset + size > info.st_size
                or tensor.name in where
            ):
                raise ValueError("invalid or duplicate source tensor")
            where[tensor.name] = (header, tensor, None, path)
    P.check_split(files)
    model = SimpleNamespace(where=where)
    if (pack / "experts.bin").exists():
        raise ValueError("experts.bin needs its own payload validation")
    layout = P.expert_layout(model, files[0].path)
    if isinstance(layout, str):
        raise ValueError(layout)
    if (pack / "native_experts.txt").read_text(encoding="utf-8") != layout[1]:
        raise ValueError("native expert rows differ from original shard spans")
    conversions = json.loads((pack / "conversions.json").read_text(encoding="utf-8"))
    if conversions["tensors"] or conversions["compat_bf16"]:
        raise ValueError("converted tensors require explicit conversion verification")
    expected_shards = [
        {"name": h.path.name, "size": h.path.stat().st_size} for h in files
    ]
    if conversions["source_shards"] != expected_shards:
        raise ValueError("conversion source shard metadata differs")
    rows = parse_index(pack / "index.txt")
    expected_names = {
        name for name in where if not P.is_expert(name) and name not in P.NOT_IN_PACK
    }
    if rows.keys() != expected_names:
        raise ValueError("index tensor set differs")
    spans, arena, storage, native = [], 0, 0, 0
    with (pack / "dense.bin").open("rb") as dense:
        for name, (header, tensor, _, path) in where.items():
            if name not in expected_names:
                continue
            if len(tensor.shape) > 2:
                raise ValueError("dense tensor has too many dimensions")
            shape = tensor.shape + [0] * (2 - len(tensor.shape))
            values = rows[name]
            if tensor.type_name not in P.FLOAT:
                if P.form_of(name) is not None and not (
                    name == "blk.1.ple_key.weight"
                    and tensor.type_name in P.NATIVE_PLE_KEY
                ):
                    raise ValueError(f"unrecorded quantized conversion for {name}")
                expected = [0, 0, 0, 0, arena, 0, *shape, 8, 0, 32] + [0] * 7
                native += 1
            else:
                if P.form_of(name) not in (None, tensor.type_name):
                    raise ValueError(f"unrecorded conversion for {name}")
                size = tensor.expected_bytes()
                kind = int(P.KIND[tensor.type_name])
                expected = [0, kind, storage, size, arena, size, *shape, 0, 0, 1] + [
                    0
                ] * 7
                with path.open("rb") as source:
                    matched = compare_span(
                        source, dense, header.data_start + tensor.offset, storage, size
                    )
                spans.append({"name": name, "bytes": size, "sha256": matched})
                pad = (-size) % P.ALIGN
                if dense.read(pad) != bytes(pad):
                    raise ValueError("dense padding differs")
                storage += size + pad
                arena += size + pad
            if values != expected:
                raise ValueError(f"index type/shape/offset/bounds differ for {name}")
            if tensor.type_name in P.FLOAT and len(spans) % 100 == 0:
                logging.info(
                    "validated %d dense spans, %d native tensors", len(spans), native
                )
    if (pack / "dense.bin").stat().st_size != storage:
        raise ValueError("dense file size differs from complete index coverage")
    header_text = (pack / "index.txt").read_text(encoding="utf-8")
    if not re.search(
        rf"# align 64 pool {arena} tensors {len(rows)}(?:\n|\r)", header_text
    ):
        raise ValueError("index header totals differ")
    tokenizer = verify_tokenizer(pack / "tokenizer", files[0].metadata)
    for path, original in before.items():
        now = path.stat()
        if (now.st_size, now.st_mtime_ns) != original:
            raise ValueError("source metadata changed during verification")
    return {
        "schema": "strata-native-pack-binding-v1",
        "source_receipt_sha256": digest(receipt_path),
        "source_receipt": str(receipt_path),
        "pack": str(pack),
        "experts": {
            "layers": len(layout[0]),
            "per_layer": layout[2],
            "bytes": layout[3],
        },
        "index_rows": len(rows),
        "native_dense_tensors": native,
        "dense_bytes": storage,
        "dense_spans": spans,
        "tokenizer": tokenizer,
        "metadata_sha256": {
            str(p.relative_to(pack)): digest(p)
            for p in pack.rglob("*")
            if p.is_file() and p.name != "dense.bin"
        },
        "validator_sources_sha256": {
            p.name: digest(p)
            for p in [
                Path(__file__),
                Path(G.__file__),
                Path(P.__file__),
                Path(ST.__file__),
            ]
        },
        "limits": "Receipt reuse requires unchanged source size/mtime; no concurrent writers.",
    }


def main() -> None:
    """Write a new receipt; never overwrite previous validation evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--source-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.output.exists():
        raise FileExistsError("Preserve existing binding receipt")
    result = verify(args.pack, args.source_receipt)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    logging.info("PASS: %d index tensors bound to hashed GGUFs", result["index_rows"])


if __name__ == "__main__":
    main()
