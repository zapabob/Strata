"""Negative controls for read-only native-pack source binding."""

import io
import json
from pathlib import Path
import struct
from datetime import datetime, timezone
import hashlib

import pytest
import strata_tokenizer as ST

from verify_native_pack_binding import (
    compare_span,
    parse_index,
    receipt_mtime_ns,
    verify,
    verify_tokenizer,
)


def test_index_rejects_duplicate_and_bad_width(tmp_path: Path) -> None:
    path = tmp_path / "index.txt"
    row = "weight " + " ".join(["0"] * 18) + "\n"
    path.write_text(row + row, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        parse_index(path)
    path.write_text("weight 0 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="19 fields"):
        parse_index(path)


def test_span_compares_all_chunks_and_rejects_truncation() -> None:
    good = b"a" * 19 + b"b"
    assert compare_span(io.BytesIO(good), io.BytesIO(good), 0, 0, 20, 7)
    with pytest.raises(ValueError, match="differ"):
        compare_span(io.BytesIO(good), io.BytesIO(b"a" * 20), 0, 0, 20, 7)
    with pytest.raises(ValueError, match="truncated"):
        compare_span(io.BytesIO(good), io.BytesIO(good[:-1]), 0, 0, 20, 7)


def test_windows_mtime_preserves_seventh_fraction_digit() -> None:
    assert receipt_mtime_ns("1970-01-01T00:00:01.2361846Z") == 1236184600


@pytest.mark.parametrize("changed", ["vocab", "types", "special", "template", "merges"])
def test_tokenizer_binds_order_types_specials_and_template(
    tmp_path: Path, changed: str
) -> None:
    metadata = {
        "tokenizer.ggml.tokens": ["a", "b", "ab"],
        "tokenizer.ggml.merges": ["a b"],
        "tokenizer.ggml.token_type": [1, 1, 3],
        "tokenizer.ggml.model": "gpt2",
        "tokenizer.ggml.pre": "qwen35",
        "tokenizer.ggml.eos_token_id": 2,
        "tokenizer.chat_template": "{{ messages }}",
    }
    config = {
        "model": "gpt2",
        "pre": "qwen35",
        "vocab_size": 3,
        "n_merges": 1,
        "special_ids": {"tokenizer.ggml.eos_token_id": 2},
        "add_bos_token": False,
        "pre_pattern": ST.QWEN35_PATTERN,
    }
    for name, value in {
        "vocab.json": {"a": 0, "b": 1, "ab": 2},
        "token_type.json": [1, 1, 3],
        "tokenizer.json": config,
    }.items():
        (tmp_path / name).write_text(json.dumps(value), encoding="utf-8")
    (tmp_path / "merges.txt").write_text("a b", encoding="utf-8")
    template = tmp_path / "chat_template.jinja"
    template.write_text(metadata["tokenizer.chat_template"], encoding="utf-8")
    assert verify_tokenizer(tmp_path, metadata)["vocabulary"] == 3
    if changed == "vocab":
        (tmp_path / "vocab.json").write_text('{"a": 1, "b": 0, "ab": 2}')
    elif changed == "types":
        (tmp_path / "token_type.json").write_text("[1, 1, 1]")
    elif changed == "special":
        config["special_ids"]["tokenizer.ggml.eos_token_id"] = 0
        (tmp_path / "tokenizer.json").write_text(json.dumps(config))
    elif changed == "template":
        template.write_text("changed", encoding="utf-8")
    else:
        (tmp_path / "merges.txt").write_text("b a", encoding="utf-8")
    with pytest.raises(ValueError, match="tokenizer"):
        verify_tokenizer(tmp_path, metadata)


@pytest.mark.parametrize("damage", [None, "dense", "offset", "expert", "receipt"])
def test_complete_pack_binding_with_real_gguf_header(
    tmp_path: Path, damage: str | None
) -> None:
    """Exercise the complete validator on a small actual GGUF, not mocked readers."""

    def string(value: str) -> bytes:
        data = value.encode("utf-8")
        return struct.pack("<Q", len(data)) + data

    metadata = {
        "general.architecture": "fixture",
        "tokenizer.ggml.model": "gpt2",
        "tokenizer.ggml.pre": "qwen35",
        "tokenizer.ggml.tokens": ["a", "b", "ab"],
        "tokenizer.ggml.merges": ["a b"],
        "tokenizer.ggml.token_type": [1, 1, 3],
        "tokenizer.ggml.eos_token_id": 2,
        "tokenizer.chat_template": "{{ messages }}",
    }
    rows = [
        ("blk.0.ffn_gate_inp.weight", [2, 2], 30, 0),
        ("blk.0.attn_q_norm.weight", [2], 0, 8),
        ("blk.0.ffn_gate_exps.weight", [64, 2, 2], 42, 16),
        ("blk.0.ffn_up_exps.weight", [64, 2, 2], 42, 88),
        ("blk.0.ffn_down_exps.weight", [64, 2, 2], 42, 160),
    ]
    header = struct.pack("<IIQQ", 0x46554747, 3, len(rows), len(metadata))
    for key, value in metadata.items():
        header += string(key)
        if isinstance(value, str):
            header += struct.pack("<I", 8) + string(value)
        elif isinstance(value, int):
            header += struct.pack("<II", 4, value)
        else:
            kind = 8 if isinstance(value[0], str) else 4
            header += struct.pack("<IIQ", 9, kind, len(value))
            header += b"".join(
                string(v) if kind == 8 else struct.pack("<I", v) for v in value
            )
    for name, shape, kind, offset in rows:
        header += string(name) + struct.pack("<I", len(shape))
        header += struct.pack(f"<{len(shape)}Q", *shape)
        header += struct.pack("<IQ", kind, offset)
    header += bytes((-len(header)) % 32)
    data_start = len(header)
    model = tmp_path / "model.gguf"
    model.write_bytes(header + bytes(range(232)))
    stat = model.stat()
    stamp = datetime.fromtimestamp(stat.st_mtime_ns // 10**9, timezone.utc)
    mtime = stamp.strftime("%Y-%m-%dT%H:%M:%S") + f".{stat.st_mtime_ns % 10**9:09d}Z"
    sha = hashlib.sha256(model.read_bytes()).hexdigest()
    receipt = tmp_path / "source.json"
    receipt.write_text(
        json.dumps(
            {
                "models": [
                    {
                        "path": str(model),
                        "bytes": stat.st_size,
                        "sha256": sha,
                        "expected_sha256": sha,
                        "matches": True,
                        "metadata_unchanged": True,
                        "last_write_utc": mtime,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    pack = tmp_path / "pack"
    token_dir = pack / "tokenizer"
    token_dir.mkdir(parents=True)
    (pack / "dense.bin").write_bytes(
        bytes(range(8)) + bytes(56) + bytes(range(8, 16)) + bytes(56)
    )
    index = pack / "index.txt"
    index.write_text(
        "# align 64 pool 128 tensors 2\n"
        "blk.0.ffn_gate_inp.weight 0 4 0 8 0 8 2 2 0 0 1 0 0 0 0 0 0 0\n"
        "blk.0.attn_q_norm.weight 0 2 64 8 64 8 2 0 0 0 1 0 0 0 0 0 0 0\n"
    )
    experts = pack / "native_experts.txt"
    experts.write_text(
        "# strata native experts v3: layer gu_type d_type offset blob_bytes "
        "gate_off up_off down_off [shard] "
        "(n_expert 2, total 216; absolute offsets in model.gguf, or in the named shard beside it)\n"
        f"0 42 42 0 108 {data_start + 16} {data_start + 88} {data_start + 160}\n"
    )
    for name, value in {
        "conversions.json": {
            "tensors": [],
            "compat_bf16": False,
            "source_shards": [{"name": model.name, "size": stat.st_size}],
        },
        "tokenizer/vocab.json": {"a": 0, "b": 1, "ab": 2},
        "tokenizer/token_type.json": [1, 1, 3],
        "tokenizer/tokenizer.json": {
            "model": "gpt2",
            "pre": "qwen35",
            "vocab_size": 3,
            "n_merges": 1,
            "special_ids": {"tokenizer.ggml.eos_token_id": 2},
            "add_bos_token": False,
            "pre_pattern": ST.QWEN35_PATTERN,
        },
    }.items():
        (pack / name).write_text(json.dumps(value), encoding="utf-8")
    (token_dir / "merges.txt").write_text("a b")
    (token_dir / "chat_template.jinja").write_text(metadata["tokenizer.chat_template"])
    if damage == "dense":
        (pack / "dense.bin").write_bytes(bytes(128))
    elif damage == "offset":
        index.write_text(index.read_text().replace("0 2 64 8", "0 2 63 8"))
    elif damage == "expert":
        experts.write_text(
            experts.read_text().replace("0 42 42 0 108", "0 42 42 0 109")
        )
    elif damage == "receipt":
        record = json.loads(receipt.read_text())
        record["models"][0]["bytes"] += 1
        receipt.write_text(json.dumps(record))
    if damage:
        with pytest.raises(ValueError):
            verify(pack, receipt)
    else:
        result = verify(pack, receipt)
        assert result["index_rows"] == 2
        assert result["dense_bytes"] == 128
        assert result["experts"]["per_layer"] == 2
        # The byte-input seam must run the real parser and complete tiny GGUF
        # verifier without reopening a pathname that has since been replaced.
        pinned = receipt.read_bytes()
        receipt.write_bytes(b'{"models":[],"models":[]}')
        rebound = verify(pack, receipt, receipt_bytes=pinned)
        assert rebound == result
        assert rebound["source_receipt_sha256"] == hashlib.sha256(pinned).hexdigest()
        with pytest.raises(ValueError, match="duplicate receipt field"):
            verify(pack, receipt, receipt_bytes=receipt.read_bytes())
    assert hashlib.sha256(model.read_bytes()).hexdigest() == sha
