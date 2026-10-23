"""Portable query-v3 sidecar writer/reader. Only the Python standard library.

Bindings are supplied independently by the caller; reading a sidecar does not
establish which model, codec or position settings a runtime actually selected.
Parameters are explicit little-endian F32 bytes, preserving signed zero.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import struct
from typing import Sequence

MAGIC = b"SP8QV3\r\n"
MAX_BYTES = 64 * 1024 * 1024
MAX_LAYERS = 4096
MAX_MODELS = 256
HEADER_BYTES = 160
RECORD_BYTES = 32
CONTRACT = (
    b"spin8-query-v3;rank=8;chart=rational-tau-tan-pi/8;"
    b"basis=positive-chirality-Gamma-C-J-v1;"
    b"map=C(c)C(e0)^T;placement=post-Qnorm-pre-RoPE;"
    b"mlp=Wout*tanh(Win*q+bin)+bout;no-extra-RMS;tail=identity"
)
CONVENTION_DIGEST = hashlib.sha256(CONTRACT).digest()
_RECORD = struct.Struct("<IIIIQQ")


def _digest(value: bytes) -> None:
    if not isinstance(value, bytes) or len(value) != 32 or not any(value):
        raise ValueError("identity must be a nonzero 32-byte SHA-256 digest")


@dataclass(frozen=True)
class Bindings:
    """Ordered model-file digests and caller-defined codec/position identities."""

    models: tuple[bytes, ...]
    profile: bytes
    position: bytes

    def validate(self) -> None:
        """Reject missing, oversized or placeholder identity bindings."""
        if not 1 <= len(self.models) <= MAX_MODELS:
            raise ValueError("model count must be 1..256")
        for value in (*self.models, self.profile, self.position):
            _digest(value)


@dataclass(frozen=True)
class LayerSpec:
    """Exact selected layer geometry, including GQA grouping."""

    layer_index: int
    q_heads: int
    kv_heads: int
    head_width: int

    def validate(self) -> None:
        """Check bounded integers and positive divisible GQA geometry."""
        values = (self.layer_index, self.q_heads, self.kv_heads, self.head_width)
        if any(type(value) is not int for value in values):
            raise ValueError("geometry must use integers")
        if not (
            0 <= self.layer_index <= 1048575
            and 1 <= self.q_heads <= 4096
            and 1 <= self.kv_heads <= 4096
            and self.q_heads % self.kv_heads == 0
            and 1 <= self.head_width <= 16384
        ):
            raise ValueError("invalid layer geometry")

    def parameter_counts(self) -> tuple[int, int, int, int]:
        """Return flattened Win, bin, Wout, bout scalar counts."""
        return (
            self.q_heads * 8 * self.head_width,
            self.q_heads * 8,
            self.q_heads * 56,
            self.q_heads * 7,
        )


@dataclass(frozen=True)
class Layer:
    """Four row-major, per-Q-head arrays as canonical little-endian F32 bytes."""

    spec: LayerSpec
    win: bytes
    bin: bytes
    wout: bytes
    bout: bytes


@dataclass(frozen=True)
class Adapter:
    """Validated immutable sidecar and its integrity/content identities."""

    bindings: Bindings
    layers: tuple[Layer, ...]
    integrity_digest: bytes
    content_digest: bytes


def _specs(specs: Sequence[LayerSpec]) -> None:
    if not 1 <= len(specs) <= MAX_LAYERS:
        raise ValueError("selected layer count must be 1..4096")
    previous = -1
    for spec in specs:
        spec.validate()
        if spec.layer_index <= previous:
            raise ValueError("layers must be sorted and unique")
        previous = spec.layer_index


def _payload(layer: Layer) -> None:
    for data, count in zip(
        (layer.win, layer.bin, layer.wout, layer.bout), layer.spec.parameter_counts()
    ):
        if not isinstance(data, bytes) or len(data) != 4 * count:
            raise ValueError("parameter byte count disagrees with geometry")
        if any(
            (word[0] & 0x7F800000) == 0x7F800000
            for word in struct.iter_unpack("<I", data)
        ):
            raise ValueError("parameters must contain only finite F32 values")


def encode(bindings: Bindings, layers: Sequence[Layer]) -> bytes:
    """Validate and create canonical bytes without normalizing any F32 bits."""
    bindings.validate()
    _specs([layer.spec for layer in layers])
    prefix = HEADER_BYTES + 32 * len(bindings.models) + RECORD_BYTES * len(layers)
    total = (
        prefix + sum(sum(layer.spec.parameter_counts()) * 4 for layer in layers) + 32
    )
    if total > MAX_BYTES:
        raise ValueError("sidecar exceeds 64 MiB")
    header = bytearray(HEADER_BYTES)
    header[:8] = MAGIC
    struct.pack_into(
        "<IIIIIIQIIIIII",
        header,
        8,
        1,
        HEADER_BYTES,
        0,
        len(bindings.models),
        len(layers),
        RECORD_BYTES,
        total,
        3,
        8,
        1,
        1,
        1,
        0x3EC90FDB,
    )
    header[64:96], header[96:128], header[128:160] = (
        bindings.profile,
        bindings.position,
        CONVENTION_DIGEST,
    )
    directory, payload = bytearray(), bytearray()
    for layer in layers:
        _payload(layer)
        size = sum(layer.spec.parameter_counts()) * 4
        spec = layer.spec
        directory += _RECORD.pack(
            spec.layer_index,
            spec.q_heads,
            spec.kv_heads,
            spec.head_width,
            prefix + len(payload),
            size,
        )
        payload += layer.win + layer.bin + layer.wout + layer.bout
    data = bytes(header) + b"".join(bindings.models) + bytes(directory) + bytes(payload)
    return data + hashlib.sha256(data).digest()


def decode(
    data: bytes, expected: Bindings, expected_layers: Sequence[LayerSpec]
) -> Adapter:
    """Strict independent parser requiring external identities and exact layers."""
    expected.validate()
    _specs(expected_layers)
    if not isinstance(data, bytes) or not HEADER_BYTES + 32 <= len(data) <= MAX_BYTES:
        raise ValueError("invalid file size")
    if data[:8] != MAGIC:
        raise ValueError("invalid magic")
    fields = struct.unpack_from("<IIIIIIQIIIIII", data, 8)
    version, header, flags, models, count, record, total, *conventions = fields
    if (version, header, flags, record, *conventions) != (
        1,
        HEADER_BYTES,
        0,
        RECORD_BYTES,
        3,
        8,
        1,
        1,
        1,
        0x3EC90FDB,
    ):
        raise ValueError("unsupported version, flags or conventions")
    if (
        total != len(data)
        or not 1 <= models <= MAX_MODELS
        or not 1 <= count <= MAX_LAYERS
    ):
        raise ValueError("invalid total length or counts")
    directory = HEADER_BYTES + models * 32
    cursor = directory + count * RECORD_BYTES
    if cursor > len(data) - 32:
        raise ValueError("truncated directory")
    if hashlib.sha256(data[:-32]).digest() != data[-32:]:
        raise ValueError("integrity mismatch")
    actual = Bindings(
        tuple(
            data[HEADER_BYTES + i * 32 : HEADER_BYTES + (i + 1) * 32]
            for i in range(models)
        ),
        data[64:96],
        data[96:128],
    )
    actual.validate()
    if actual != expected or data[128:160] != CONVENTION_DIGEST:
        raise ValueError("identity mismatch")
    if count != len(expected_layers):
        raise ValueError("selected layer count mismatch")
    layers = []
    previous = -1
    for i in range(count):
        index, q, kv, width, offset, size = _RECORD.unpack_from(
            data, directory + i * RECORD_BYTES
        )
        spec = LayerSpec(index, q, kv, width)
        spec.validate()
        if index <= previous or spec != expected_layers[i]:
            raise ValueError("layer order/geometry mismatch")
        previous = index
        sizes = [n * 4 for n in spec.parameter_counts()]
        if offset != cursor or size != sum(sizes) or size > len(data) - 32 - cursor:
            raise ValueError("noncanonical payload range")
        arrays = []
        for length in sizes:
            arrays.append(data[cursor : cursor + length])
            cursor += length
        layer = Layer(spec, *arrays)
        _payload(layer)
        layers.append(layer)
    if cursor != len(data) - 32:
        raise ValueError("unexplained trailing bytes")
    return Adapter(actual, tuple(layers), data[-32:], hashlib.sha256(data).digest())


def identity_layer(spec: LayerSpec, win_scale: float = 0.0) -> Layer:
    """Deterministic test/training initialization; zero outputs mean identity.

    This is not learned data or standard LoRA. Optional nonzero Win alternates
    signs with the explicit scale and is useful for subsequent training.
    """
    spec.validate()
    if not math.isfinite(win_scale):
        raise ValueError("win scale must be finite")
    counts = spec.parameter_counts()
    if sum(counts) * 4 + HEADER_BYTES + 32 + RECORD_BYTES + 32 > MAX_BYTES:
        raise ValueError("layer exceeds sidecar limit")
    try:
        win = struct.pack("<ff", -win_scale, win_scale) * (counts[0] // 2)
    except OverflowError as exc:
        raise ValueError("win scale is outside finite F32") from exc
    layer = Layer(spec, win, *(bytes(n * 4) for n in counts[1:]))
    _payload(layer)
    return layer


def save(path: Path, data: bytes, *, overwrite: bool = False) -> None:
    """Write bytes; exclusive creation by default, explicit overwrite only."""
    with path.open("wb" if overwrite else "xb") as stream:
        stream.write(data)


def _cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("create", "inspect"))
    parser.add_argument("path", type=Path)
    parser.add_argument(
        "--model-sha256",
        action="append",
        required=True,
        help="ordered actual model-file hashes (repeat per shard)",
    )
    parser.add_argument("--profile-sha256", required=True)
    parser.add_argument("--position-sha256", required=True)
    parser.add_argument(
        "--layer",
        action="append",
        required=True,
        help="exact sorted index:q_heads:kv_heads:width",
    )
    parser.add_argument("--win-scale", type=float, default=0.0)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        bindings = Bindings(
            tuple(bytes.fromhex(s) for s in args.model_sha256),
            bytes.fromhex(args.profile_sha256),
            bytes.fromhex(args.position_sha256),
        )
        specs = [LayerSpec(*(int(n) for n in s.split(":"))) for s in args.layer]
        bindings.validate()
        _specs(specs)
        if args.action == "create":
            total = (
                HEADER_BYTES
                + 32 * len(bindings.models)
                + 32 * len(specs)
                + 32
                + sum(sum(s.parameter_counts()) * 4 for s in specs)
            )
            if total > MAX_BYTES:
                raise ValueError("sidecar exceeds 64 MiB")
            data = encode(bindings, [identity_layer(s, args.win_scale) for s in specs])
            save(args.path, data, overwrite=args.overwrite)
        else:
            with args.path.open("rb") as stream:
                data = stream.read(MAX_BYTES + 1)
        adapter = decode(data, bindings, specs)
    except (ValueError, TypeError, OSError) as exc:
        parser.exit(2, f"sidecar: {exc}\n")
    print(
        json.dumps(
            {
                "content_sha256": adapter.content_digest.hex(),
                "integrity_sha256": adapter.integrity_digest.hex(),
                "model_count": len(bindings.models),
                "layers": len(specs),
                "bytes": len(data),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    _cli()
