"""strata_control/model_bundle.py - Bounded GGUF descriptor and ModelBundle definitions."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import os
from pathlib import Path
import struct
from typing import Any

from strata_control.gguf_dialects import resolve_dialect_type, DialectType
from tools.gguf_reader import BLOCK_GEOMETRY, GGML_TYPES


@dataclass(frozen=True)
class InspectionLimits:
    max_header_bytes: int = 64 * 1024 * 1024  # 64 MiB
    max_metadata_keys: int = 8192
    max_tensors: int = 65536
    max_tensor_bytes: int = 64 * 1024 * 1024 * 1024  # 64 GiB per tensor
    max_string_bytes: int = 1024 * 1024  # 1 MiB


@dataclass(frozen=True)
class TensorDescriptor:
    name: str
    dimensions: list[int]
    type_id: int
    offset: int
    byte_size: int
    dialect_name: str


@dataclass(frozen=True)
class GgufDescriptor:
    path: str
    file_size_bytes: int
    architecture: str
    is_runnable: bool
    unrunnable_reason: str | None
    split_count: int
    split_index: int
    tensor_count: int
    tensors: list[TensorDescriptor]
    metadata: dict[str, Any]
    content_hash: str | None = None
    is_metadata_only: bool = False


SUPPORTED_ARCHITECTURES = frozenset({
    "qwen4exp", "qwen35", "qwen2", "qwen", "llama", "deepseek2", "deepseek", "dsv41", "mistral", "phi"
})


class _BoundedReader:
    def __init__(self, stream, max_bytes: int):
        self.stream = stream
        self.max_bytes = max_bytes
        self.used = 0

    def read_exact(self, count: int) -> bytes:
        if count < 0 or self.used + count > self.max_bytes:
            raise ValueError("GGUF header exceeds bounded inspection limit")
        data = self.stream.read(count)
        if len(data) != count:
            raise ValueError("GGUF header is truncated")
        self.used += count
        return data

    def skip(self, count: int) -> None:
        if count < 0 or self.used + count > self.max_bytes:
            raise ValueError("GGUF header exceeds bounded inspection limit")
        self.stream.seek(count, os.SEEK_CUR)
        self.used += count

    def u32(self) -> int:
        return struct.unpack("<I", self.read_exact(4))[0]

    def i32(self) -> int:
        return struct.unpack("<i", self.read_exact(4))[0]

    def u64(self) -> int:
        return struct.unpack("<Q", self.read_exact(8))[0]

    def i64(self) -> int:
        return struct.unpack("<q", self.read_exact(8))[0]

    def f32(self) -> float:
        return struct.unpack("<f", self.read_exact(4))[0]

    def f64(self) -> float:
        return struct.unpack("<d", self.read_exact(8))[0]

    def string(self) -> str:
        size = self.u64()
        if size > 1024 * 1024:
            raise ValueError("GGUF metadata string exceeds limit")
        raw = self.read_exact(size)
        return raw.decode("utf-8", errors="replace")

    def read_value(self, val_type: int) -> Any:
        if val_type == 0:
            return struct.unpack("<B", self.read_exact(1))[0]
        if val_type == 1:
            return struct.unpack("<b", self.read_exact(1))[0]
        if val_type == 2:
            return struct.unpack("<H", self.read_exact(2))[0]
        if val_type == 3:
            return struct.unpack("<h", self.read_exact(2))[0]
        if val_type == 4:
            return self.u32()
        if val_type == 5:
            return self.i32()
        if val_type == 6:
            return self.f32()
        if val_type == 7:
            return bool(struct.unpack("<B", self.read_exact(1))[0])
        if val_type == 8:
            return self.string()
        if val_type == 9:
            elem_type = self.u32()
            count = self.u64()
            if count > 500_000:
                raise ValueError("Array exceeds maximum count")
            # For large arrays (tokens etc), return count only to stay bounded
            if count > 32 and elem_type in (8, 9):
                for _ in range(count):
                    s_len = self.u64()
                    self.skip(s_len)
                return f"<array of {count} items>"
            if count > 256:
                scalar_sizes = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4, 7: 1, 10: 8, 11: 8, 12: 8}
                if elem_type in scalar_sizes:
                    self.skip(count * scalar_sizes[elem_type])
                    return f"<array of {count} items>"
            items = []
            for _ in range(count):
                items.append(self.read_value(elem_type))
            return items
        if val_type == 10:
            return self.u64()
        if val_type == 11:
            return self.i64()
        if val_type == 12:
            return self.f64()
        raise ValueError(f"Unknown GGUF metadata value type: {val_type}")


def inspect_gguf(
    path: Path,
    limits: InspectionLimits | None = None,
    dialect: str | None = None,
) -> GgufDescriptor:
    """Safely inspect a GGUF file returning a bounded structural descriptor."""
    limits = limits or InspectionLimits()
    if not path.exists():
        raise FileNotFoundError(f"GGUF file does not exist: {path}")

    file_size = path.stat().st_size
    with path.open("rb") as stream:
        reader = _BoundedReader(stream, min(file_size, limits.max_header_bytes))

        # 1. Magic & Version Check
        magic = reader.read_exact(4)
        if magic != b"GGUF":
            raise ValueError(f"Invalid magic bytes in {path}: {magic!r}")
        version = reader.u32()
        if version not in (2, 3):
            raise ValueError(f"Unsupported GGUF container version {version} in {path}")

        # 2. Counts
        n_tensors = reader.u64()
        n_metadata = reader.u64()
        if n_tensors > limits.max_tensors:
            raise ValueError(f"Tensor count {n_tensors} exceeds maximum {limits.max_tensors}")
        if n_metadata > limits.max_metadata_keys:
            raise ValueError(f"Metadata key count {n_metadata} exceeds maximum {limits.max_metadata_keys}")

        # 3. Read Metadata Key-Values
        metadata: dict[str, Any] = {}
        for _ in range(n_metadata):
            k = reader.string()
            val_type = reader.u32()
            val = reader.read_value(val_type)
            metadata[k] = val

        # 4. Read Tensor Directory
        tensors: list[TensorDescriptor] = []
        for _ in range(n_tensors):
            t_name = reader.string()
            n_dims = reader.u32()
            if not 1 <= n_dims <= 8:
                raise ValueError(f"Tensor {t_name} has invalid dimension count: {n_dims}")
            
            dims = []
            elements = 1
            for _ in range(n_dims):
                dim = reader.u64()
                if dim == 0 or dim > 1_000_000_000 or elements > (1 << 63) // dim:
                    raise ValueError(f"Tensor {t_name} dimension integer overflow")
                dims.append(dim)
                elements *= dim

            t_type = reader.u32()
            t_offset = reader.u64()

            # Resolve type and compute byte size
            type_name = GGML_TYPES.get(t_type, f"TYPE_{t_type}")
            geometry = BLOCK_GEOMETRY.get(type_name)
            if geometry is not None and elements % geometry[0] == 0:
                t_bytes = elements // geometry[0] * geometry[1]
            else:
                t_bytes = elements  # fallback approximation if unblocked

            try:
                resolved_dial = resolve_dialect_type(t_type, explicit_dialect=dialect)
                d_name = resolved_dial.name
            except Exception:
                d_name = type_name

            tensors.append(
                TensorDescriptor(
                    name=t_name,
                    dimensions=dims,
                    type_id=t_type,
                    offset=t_offset,
                    byte_size=t_bytes,
                    dialect_name=d_name,
                )
            )

    # Resolve Architecture
    arch = metadata.get("general.architecture", "unknown")
    split_count = int(metadata.get("split.count", 1))
    split_index = int(metadata.get("split.no", 0))
    is_metadata_only = (n_tensors == 0)

    # Determine runnable status based on supported architectures
    is_runnable = True
    unrunnable_reason = None
    if is_metadata_only:
        is_runnable = False
        unrunnable_reason = "GGUF file contains metadata but no tensors (shard or metadata auxiliary)"
    elif arch not in SUPPORTED_ARCHITECTURES:
        is_runnable = False
        unrunnable_reason = f"Architecture '{arch}' has no verified local backend"

    return GgufDescriptor(
        path=str(path),
        file_size_bytes=file_size,
        architecture=arch,
        is_runnable=is_runnable,
        unrunnable_reason=unrunnable_reason,
        split_count=split_count,
        split_index=split_index,
        tensor_count=n_tensors,
        tensors=tensors,
        metadata=metadata,
        is_metadata_only=is_metadata_only,
    )
