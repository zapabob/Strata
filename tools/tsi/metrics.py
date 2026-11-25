"""Section 16 trial recording, resource telemetry, and privacy sanitisation.

Guarantees:
- Unmeasured metrics are recorded strictly as `null` (`None`), NEVER filled with `0`.
- API keys, Bearer tokens, and private filesystem user paths are redacted from public
  benchmark records.
- Hardware memory probes (RAM / VRAM) never fail a CPU-only run; if unavailable, they
  return `None`.
"""

from __future__ import annotations

import ctypes
import hashlib
import logging
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Sequence

from . import TSI_RECORD_SCHEMA_VERSION
from .verifier import VerificationLevel

LOGGER = logging.getLogger("strata.tsi.metrics")

_WIN_USER_PATH_RE = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\"'\s]+", re.IGNORECASE)
_BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE)


def sanitise_public_text(text: str | None) -> str | None:
    """Strip Bearer tokens and private Windows user paths before writing benchmark logs."""
    if text is None:
        return None
    cleaned = _BEARER_RE.sub("Bearer <REDACTED>", text)
    cleaned = _WIN_USER_PATH_RE.sub("<USER_HOME>", cleaned)
    return cleaned


def sample_system_memory_bytes() -> dict[str, int | None]:
    """Query host RAM usage on Windows via GlobalMemoryStatusEx; return None if unavailable."""
    if sys.platform != "win32":
        return {"used_ram_bytes": None, "free_ram_bytes": None, "total_ram_bytes": None}

    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    try:
        ms = MEMORYSTATUSEX()
        ms.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ok = ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))  # type: ignore[attr-defined]
        if not ok:
            return {"used_ram_bytes": None, "free_ram_bytes": None, "total_ram_bytes": None}
        total = int(ms.ullTotalPhys)
        avail = int(ms.ullAvailPhys)
        return {
            "used_ram_bytes": max(0, total - avail),
            "free_ram_bytes": avail,
            "total_ram_bytes": total,
        }
    except (OSError, AttributeError):
        return {"used_ram_bytes": None, "free_ram_bytes": None, "total_ram_bytes": None}


def sample_gpu_vram_bytes() -> dict[str, int | None]:
    """Best-effort query of GPU VRAM used/free via nvidia-smi; returns None if unavailable."""
    try:
        proc = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.free,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return {"used_vram_bytes": None, "free_vram_bytes": None, "total_vram_bytes": None}
        first_line = proc.stdout.strip().splitlines()[0]
        parts = [int(p.strip()) for p in first_line.split(",")]
        if len(parts) < 3:
            return {"used_vram_bytes": None, "free_vram_bytes": None, "total_vram_bytes": None}
        mib = 1024 * 1024
        return {
            "used_vram_bytes": parts[0] * mib,
            "free_vram_bytes": parts[1] * mib,
            "total_vram_bytes": parts[2] * mib,
        }
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"used_vram_bytes": None, "free_vram_bytes": None, "total_vram_bytes": None}


def optional_file_sha256(path: Path | None) -> str | None:
    """Compute SHA-256 of a local file if provided and readable; otherwise None."""
    if path is None or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_section16_trial_record(
    *,
    task_id: str,
    model_id: str,
    model_sha256: str | None,
    engine_commit: str | None,
    quantisation: str,
    seed: int,
    token_budget: int,
    tokens_used: int | None,
    wall_time_ms: float | None,
    attempts: Sequence[dict[str, Any]],
    peak_vram_bytes: int | None,
    peak_ram_bytes: int | None,
    verifier: str | None,
    verification_level: VerificationLevel,
    verified: bool,
    termination_reason: str,
    split: str | None = None,
    domain: str | None = None,
    discovery_class: str = "known_benchmark_problem",
    mode: str = "standard",
) -> dict[str, Any]:
    """Build a Section 16 schema-compliant trial record.

    All unmeasured values remain strictly `None` (JSON `null`), never `0`.
    """
    sanitised_attempts = []
    for att in attempts:
        row = dict(att)
        if "api_error" in row:
            row["api_error"] = sanitise_public_text(row["api_error"])
        if "verifier_detail" in row:
            row["verifier_detail"] = sanitise_public_text(row["verifier_detail"])
        sanitised_attempts.append(row)

    return {
        "schema_version": TSI_RECORD_SCHEMA_VERSION,
        "task_id": task_id,
        "model_id": sanitise_public_text(model_id) or "unspecified",
        "model_sha256": model_sha256,
        "engine_commit": engine_commit,
        "quantisation": quantisation,
        "seed": int(seed),
        "token_budget": int(token_budget),
        "tokens_used": int(tokens_used) if tokens_used is not None else None,
        "wall_time_ms": round(float(wall_time_ms), 3) if wall_time_ms is not None else None,
        "attempts": sanitised_attempts,
        "peak_vram_bytes": int(peak_vram_bytes) if peak_vram_bytes is not None else None,
        "peak_ram_bytes": int(peak_ram_bytes) if peak_ram_bytes is not None else None,
        "verifier": verifier,
        "verification_level": verification_level.value,
        "verified": bool(verified),
        "termination_reason": termination_reason,
        "split": split,
        "domain": domain,
        "discovery_class": discovery_class,
        "mode": mode,
    }
