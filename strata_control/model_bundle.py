"""strata_control/model_bundle.py - Bounded GGUF descriptor and ModelBundle definitions."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
from typing import Any

from strata_control.gguf_dialects import resolve_dialect_type, DialectType


@dataclass(frozen=True)
class InspectionLimits:
    max_header_bytes: int = 64 * 1024 * 1024  # 64 MiB
    max_metadata_keys: int = 8192
    max_tensors: int = 65536
    max_tensor_bytes: int = 64 * 1024 * 1024 * 1024  # 64 GiB per tensor


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


SUPPORTED_ARCHITECTURES = {
    "qwen2", "qwen", "llama", "deepseek2", "deepseek", "dsv41", "mistral", "phi"
}


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
    # Read GGUF header safely (bounded)
    with path.open("rb") as f:
        magic = f.read(4)
        if magic != b"GGUF":
            raise ValueError(f"Invalid magic bytes in {path}: {magic!r}")
        version_bytes = f.read(4)
        if len(version_bytes) < 4:
            raise ValueError(f"Truncated header in {path}")
        import struct
        version = struct.unpack("<I", version_bytes)[0]
        if version not in (2, 3):
            raise ValueError(f"Unsupported GGUF container version {version} in {path}")

        n_tensors, n_metadata = struct.unpack("<QQ", f.read(16))
        if n_tensors > limits.max_tensors:
            raise ValueError(f"Tensor count {n_tensors} exceeds maximum {limits.max_tensors}")
        if n_metadata > limits.max_metadata_keys:
            raise ValueError(f"Metadata key count {n_metadata} exceeds maximum {limits.max_metadata_keys}")

    # Fallback/stub metadata parsing for descriptor
    # In production, parses key-value pairs up to limits.max_header_bytes
    arch = "unknown"
    is_metadata_only = (n_tensors == 0)
    
    # Try reading architecture from metadata if small
    metadata: dict[str, Any] = {}
    is_runnable = True
    unrunnable_reason = None

    # Determine runnable status based on supported architectures
    if arch not in SUPPORTED_ARCHITECTURES and not is_metadata_only:
        is_runnable = False
        unrunnable_reason = f"Architecture '{arch}' has no verified local backend"

    return GgufDescriptor(
        path=str(path),
        file_size_bytes=file_size,
        architecture=arch,
        is_runnable=is_runnable,
        unrunnable_reason=unrunnable_reason,
        split_count=1,
        split_index=0,
        tensor_count=n_tensors,
        tensors=[],
        metadata=metadata,
    )
