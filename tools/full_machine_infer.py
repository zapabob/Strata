#!/usr/bin/env python3
"""Full-machine heterogeneous inference planner, benchmarker, and server launcher for Strata.

Automatically probes every hardware tier on the host PC:
  - Tier 0 (CPU): Physical cores (primary threads) for GPU host loop + AVX2 MoE compute,
    and SMT secondary threads for async NVMe/SSD Direct I/O, PrefetchVirtualMemory, and CUDA driver threads.
  - Tier 1 (GPU): NVIDIA VRAM budget with WDDM safety headroom and CUDA 13.5 SM120 dispatch.
  - Tier 2 (RAM): Commit-safe pinned + zero-copy host RAM pool with optional RAM squeeze.
  - Tier 3 (SSD): Dual-SSD (C: NVMe + H: SSD) Direct I/O / async virtual-memory prefetch streaming.

Enforces mandatory resource floors (RAM >= 3 GiB, Commit >= 4 GiB, C: >= 5 GiB, H: >= 10 GiB)
and records releaseQualified=false for local unsigned builds.
"""

from __future__ import annotations

import argparse
import ctypes
from dataclasses import asdict, dataclass, field
import json
import logging
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time
from typing import Iterable, Sequence

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover - fallback when tqdm is not installed in minimal envs

    def tqdm(iterable: Iterable[object], **_kwargs: object) -> Iterable[object]:
        return iterable


LOGGER = logging.getLogger("strata.full_machine_infer")

GiB = 1024.0 ** 3
MiB = 1024.0 ** 2

MIN_RAM_AVAIL_GIB = 3.0
MIN_COMMIT_AVAIL_GIB = 4.0
MIN_C_FREE_GIB = 5.0
MIN_H_FREE_GIB = 10.0

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_DIRS: tuple[Path, ...] = (
    Path("H:/Strata/models"),
    Path("C:/Strata/models"),
)
DEFAULT_ENGINE_DIRS: tuple[Path, ...] = (
    Path("H:/Strata/build/engine-cuda135"),
    Path("H:/Strata/build/engine-cuda135/src/inkling2"),
    Path("H:/Strata/build/hy4-cuda135"),
    Path("H:/Strata/build/q38-cuda135"),
)


@dataclass(frozen=True)
class DiskStatus:
    """Capacity snapshot for a single local drive."""

    mount: str
    total_gib: float
    free_gib: float


@dataclass(frozen=True)
class HardwareProfile:
    """Live snapshot of GPU, CPU (physical/SMT), RAM/commit, and local SSDs."""

    gpu_name: str
    vram_total_gib: float
    vram_free_gib: float
    compute_cap: str
    pcie_gen: int
    pcie_width: int
    power_limit_w: float
    physical_cores: int
    logical_threads: int
    primary_cpus: tuple[int, ...]
    smt_secondary_cpus: tuple[int, ...]
    ram_total_gib: float
    ram_avail_gib: float
    commit_total_gib: float
    commit_avail_gib: float
    disks: tuple[DiskStatus, ...]


@dataclass(frozen=True)
class ModelSpec:
    """Lightweight metadata extracted from a local .gguf or .strata model file."""

    path: Path
    name: str
    file_format: str
    size_gib: float
    architecture: str
    family: str
    recommended_engine: str


@dataclass(frozen=True)
class ExecutionPlan:
    """Computed 3-tier full-machine placement, environment, and command line."""

    model: str
    family: str
    architecture: str
    tier_mode: str
    engine_exe: str
    context: int
    gpu_budget_gib: float
    ram_pinned_budget_gib: float
    ssd_stream_gib: float
    cpu_compute_threads: int
    cpu_io_smt_threads: int
    primary_cpus: tuple[int, ...]
    smt_secondary_cpus: tuple[int, ...]
    args: tuple[str, ...]
    env: dict[str, str]
    floors_ok: bool
    floor_warnings: tuple[str, ...] = field(default_factory=tuple)
    release_qualified: bool = False


class _MemoryStatusEx(ctypes.Structure):
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


class _GroupAffinity(ctypes.Structure):
    _fields_ = [
        ("Mask", ctypes.c_size_t),
        ("Group", ctypes.c_ushort),
        ("Reserved", ctypes.c_ushort * 3),
    ]


class _ProcessorRelationship(ctypes.Structure):
    _fields_ = [
        ("Flags", ctypes.c_ubyte),
        ("EfficiencyClass", ctypes.c_ubyte),
        ("Reserved", ctypes.c_ubyte * 20),
        ("GroupCount", ctypes.c_ushort),
        ("GroupMask", _GroupAffinity * 1),
    ]


def configure_logging(verbose: bool = False) -> None:
    """Configure UTF-8 structured logging with zero stdout print() usage."""
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def probe_cpu_topology() -> tuple[int, int, tuple[int, ...], tuple[int, ...]]:
    """Return (physical_cores, logical_threads, primary_cpus, smt_secondary_cpus)."""
    logical = os.cpu_count() or 1
    if os.name != "nt":
        half = max(1, logical // 2)
        prim = tuple(range(0, logical, 2)) if logical >= 2 else (0,)
        sec = tuple(range(1, logical, 2)) if logical >= 2 else ()
        return half, logical, prim, sec

    relation_processor_core = 0
    kernel32 = ctypes.windll.kernel32
    buf_len = ctypes.c_ulong(0)
    kernel32.GetLogicalProcessorInformationEx(relation_processor_core, None, ctypes.byref(buf_len))
    if buf_len.value == 0:
        prim = tuple(range(0, logical, 2)) if logical >= 2 else (0,)
        sec = tuple(range(1, logical, 2)) if logical >= 2 else ()
        return max(1, len(prim)), logical, prim, sec

    raw = (ctypes.c_ubyte * buf_len.value)()
    ok = kernel32.GetLogicalProcessorInformationEx(
        relation_processor_core,
        ctypes.byref(raw),
        ctypes.byref(buf_len),
    )
    if not ok:
        prim = tuple(range(0, logical, 2)) if logical >= 2 else (0,)
        sec = tuple(range(1, logical, 2)) if logical >= 2 else ()
        return max(1, len(prim)), logical, prim, sec

    raw_bytes = bytes(raw)
    offset = 0
    primary: list[int] = []
    secondary: list[int] = []
    physical_cores = 0
    while offset + 8 <= len(raw_bytes):
        rel, size = struct.unpack_from("<II", raw_bytes, offset)
        if size == 0 or offset + size > len(raw_bytes):
            break
        if rel == relation_processor_core:
            physical_cores += 1
            # SYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX header is 8 bytes;
            # PROCESSOR_RELATIONSHIP has 22 bytes before GroupCount (uint16) at +22,
            # followed by GROUP_AFFINITY[] at +24 (16 bytes each on x64).
            group_count = struct.unpack_from("<H", raw_bytes, offset + 8 + 22)[0]
            first_seen = False
            for gi in range(max(1, group_count)):
                ga_off = offset + 8 + 24 + gi * 16
                if ga_off + 10 > offset + size:
                    break
                mask, group = struct.unpack_from("<QH", raw_bytes, ga_off)
                for bit in range(64):
                    if mask & (1 << bit):
                        cpu_id = group * 64 + bit
                        if not first_seen:
                            primary.append(cpu_id)
                            first_seen = True
                        else:
                            secondary.append(cpu_id)
        offset += size

    if not primary:
        primary = list(range(0, logical, 2)) if logical >= 2 else [0]
        secondary = list(range(1, logical, 2)) if logical >= 2 else []
        physical_cores = len(primary)

    return physical_cores, len(primary) + len(secondary), tuple(sorted(primary)), tuple(sorted(secondary))


def probe_memory_gib() -> tuple[float, float, float, float]:
    """Return (ram_total_gib, ram_avail_gib, commit_total_gib, commit_avail_gib)."""
    if os.name == "nt":
        ms = _MemoryStatusEx()
        ms.dwLength = ctypes.sizeof(_MemoryStatusEx)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
            return (
                ms.ullTotalPhys / GiB,
                ms.ullAvailPhys / GiB,
                ms.ullTotalPageFile / GiB,
                ms.ullAvailPageFile / GiB,
            )
    return 0.0, 0.0, 0.0, 0.0


def probe_gpu() -> tuple[str, float, float, str, int, int, float]:
    """Probe primary NVIDIA GPU via nvidia-smi."""
    cmd = [
        "nvidia-smi",
        "--query-gpu=name,memory.total,memory.free,compute_cap,pcie.link.gen.max,pcie.link.width.max,power.limit",
        "--format=csv,noheader,nounits",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
        if proc.returncode == 0 and proc.stdout.strip():
            line = proc.stdout.strip().splitlines()[0]
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 7:
                return (
                    parts[0],
                    float(parts[1]) / 1024.0,
                    float(parts[2]) / 1024.0,
                    parts[3],
                    int(float(parts[4])),
                    int(float(parts[5])),
                    float(parts[6]),
                )
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        LOGGER.warning("Failed to probe GPU via nvidia-smi: %s", exc)
    return "Unknown GPU", 0.0, 0.0, "0.0", 0, 0, 0.0


def probe_disks(mounts: Sequence[str] = ("C:/", "H:/")) -> tuple[DiskStatus, ...]:
    """Inspect local SSD capacity for configured mount points."""
    out: list[DiskStatus] = []
    for mount in mounts:
        try:
            usage = shutil.disk_usage(mount)
            out.append(DiskStatus(mount=mount, total_gib=usage.total / GiB, free_gib=usage.free / GiB))
        except OSError as exc:
            LOGGER.debug("Disk %s unavailable: %s", mount, exc)
    return tuple(out)


def probe_hardware() -> HardwareProfile:
    """Gather a full live snapshot of GPU, CPU, RAM/commit, and SSD resources."""
    gpu_name, vram_tot, vram_free, cc, pcie_gen, pcie_w, pwr = probe_gpu()
    phys, logi, prim, sec = probe_cpu_topology()
    ram_tot, ram_av, com_tot, com_av = probe_memory_gib()
    disks = probe_disks()
    return HardwareProfile(
        gpu_name=gpu_name,
        vram_total_gib=round(vram_tot, 2),
        vram_free_gib=round(vram_free, 2),
        compute_cap=cc,
        pcie_gen=pcie_gen,
        pcie_width=pcie_w,
        power_limit_w=pwr,
        physical_cores=phys,
        logical_threads=logi,
        primary_cpus=prim,
        smt_secondary_cpus=sec,
        ram_total_gib=round(ram_tot, 2),
        ram_avail_gib=round(ram_av, 2),
        commit_total_gib=round(com_tot, 2),
        commit_avail_gib=round(com_av, 2),
        disks=disks,
    )


def check_resource_floors(hw: HardwareProfile) -> tuple[bool, tuple[str, ...]]:
    """Verify mandatory safety floors (RAM>=3 GiB, Commit>=4 GiB, C:>=5 GiB, H:>=10 GiB)."""
    warnings: list[str] = []
    if hw.ram_avail_gib < MIN_RAM_AVAIL_GIB:
        warnings.append(f"Available RAM {hw.ram_avail_gib:.2f} GiB < floor {MIN_RAM_AVAIL_GIB:.1f} GiB")
    if hw.commit_avail_gib < MIN_COMMIT_AVAIL_GIB:
        warnings.append(f"Available commit {hw.commit_avail_gib:.2f} GiB < floor {MIN_COMMIT_AVAIL_GIB:.1f} GiB")
    for disk in hw.disks:
        norm = disk.mount.upper()
        if norm.startswith("C:") and disk.free_gib < MIN_C_FREE_GIB:
            warnings.append(f"Disk C: free {disk.free_gib:.2f} GiB < floor {MIN_C_FREE_GIB:.1f} GiB")
        elif norm.startswith("H:") and disk.free_gib < MIN_H_FREE_GIB:
            warnings.append(f"Disk H: free {disk.free_gib:.2f} GiB < floor {MIN_H_FREE_GIB:.1f} GiB")
    return len(warnings) == 0, tuple(warnings)


def _read_gguf_architecture(path: Path) -> str:
    """Fast binary scan of GGUF KV metadata to extract general.architecture without reading weights."""
    try:
        with path.open("rb") as fh:
            header = fh.read(24)
            if len(header) < 24 or header[:4] != b"GGUF":
                return ""
            version, _n_tensors, n_kv = struct.unpack_from("<IQQ", header, 4)
            if version < 2 or version > 4:
                return ""
            # Scan bounded KV entries to find general.architecture cleanly.
            max_kv = min(n_kv, 64)
            for _ in range(max_kv):
                kl_raw = fh.read(8)
                if len(kl_raw) < 8:
                    break
                klen = struct.unpack("<Q", kl_raw)[0]
                if klen > 4096:
                    break
                key = fh.read(klen).decode("utf-8", errors="replace")
                vt_raw = fh.read(4)
                if len(vt_raw) < 4:
                    break
                vtype = struct.unpack("<I", vt_raw)[0]
                if vtype == 8:  # GGUF_TYPE_STRING
                    sl_raw = fh.read(8)
                    if len(sl_raw) < 8:
                        break
                    slen = struct.unpack("<Q", sl_raw)[0]
                    if key == "general.architecture" and slen <= 256:
                        return fh.read(slen).decode("utf-8", errors="replace").strip()
                    fh.seek(slen, os.SEEK_CUR)
                elif vtype in (0, 1, 7):  # u8, i8, bool
                    fh.seek(1, os.SEEK_CUR)
                elif vtype in (2, 3):  # u16, i16
                    fh.seek(2, os.SEEK_CUR)
                elif vtype in (4, 5, 6):  # u32, i32, f32
                    fh.seek(4, os.SEEK_CUR)
                elif vtype in (10, 11, 12):  # u64, i64, f64
                    fh.seek(8, os.SEEK_CUR)
                elif vtype == 9:  # array - stop scanning once past early string keys
                    break
                else:
                    break
    except OSError as exc:
        LOGGER.debug("GGUF header scan skipped for %s: %s", path, exc)
    return ""


def _classify_model(path: Path, arch: str) -> tuple[str, str]:
    """Map architecture/filename to (family, engine_basename)."""
    low_arch = arch.lower()
    low_name = path.name.lower()
    ext = path.suffix.lower()

    if low_arch in ("inkling2", "inkling2_loop") or "inkling" in low_name or "sakura" in low_name:
        if ext == ".strata" or "tq2_0" in low_name:
            return "inkling2_strata", "strata-inkling.exe"
        return "inkling2_gguf", "strata-inkling2.exe"
    if "hy4" in low_name or (ext == ".strata" and "hy4" in str(path).lower()):
        return "hy4flash", "strata-hy4.exe"
    if low_arch in ("qwen35", "qwen3_next") or "qwen3.8-27b" in low_name or "qwen3.5-9b" in low_name or "hikari" in low_name:
        return "qwen38_dense", "strata-q38.exe"
    if (
        low_arch in ("qwen35moe", "qwen3moe")
        or "qwen3.6" in low_name
        or "qsa-" in low_name
        or ext == ".strata"
    ):
        return "qwen36_moe", "strata.exe"
    return "unknown", "strata.exe"


def _is_runnable_gguf(path: Path) -> tuple[bool, str]:
    """Fast check that a GGUF file has non-zero weight payload (not a header-only stub) and is not truncated."""
    try:
        sz = path.stat().st_size
        if sz < 100 * MiB:
            return False, "smaller than 100 MiB"
        with path.open("rb") as fh:
            hdr = fh.read(24)
            if len(hdr) < 24 or hdr[:4] != b"GGUF":
                return False, "bad GGUF magic"
            fh.seek(sz // 2)
            if not any(fh.read(4096)):
                return False, "zero-filled header-only stub"
            fh.seek(max(0, sz - 4096))
            if not any(fh.read(4096)):
                return False, "zero-filled tail stub"
    except OSError as exc:
        return False, f"read error: {exc}"
    return True, ""


def inspect_model(path: Path) -> ModelSpec:
    """Inspect a local model file and determine its family and optimal native engine."""
    size_gib = round(path.stat().st_size / GiB, 2)
    ext = path.suffix.lower().lstrip(".") or "bin"
    arch = _read_gguf_architecture(path) if ext == "gguf" else ext
    family, engine = _classify_model(path, arch)
    return ModelSpec(
        path=path,
        name=path.stem,
        file_format=ext,
        size_gib=size_gib,
        architecture=arch or "unknown",
        family=family,
        recommended_engine=engine,
    )


def discover_models(search_dirs: Sequence[Path] = DEFAULT_MODEL_DIRS) -> list[ModelSpec]:
    """Discover local runnable GGUF and .strata models across configured storage tiers."""
    candidates: list[Path] = []
    for base in search_dirs:
        if not base.exists():
            continue
        for ext in ("*.gguf", "*.strata"):
            for fp in base.rglob(ext):
                low = fp.name.lower()
                if "mmproj" in low or "dspark" in low or "engram" in low or low.startswith("mtp-"):
                    continue
                if fp.stat().st_size < 100 * MiB:
                    continue
                if ext == "*.gguf":
                    ok_gguf, reason = _is_runnable_gguf(fp)
                    if not ok_gguf:
                        LOGGER.debug("Skipping non-runnable GGUF %s (%s)", fp.name, reason)
                        continue
                candidates.append(fp)

    unique = sorted({p.resolve() for p in candidates}, key=lambda p: p.stat().st_size, reverse=True)
    specs: list[ModelSpec] = []
    for fp in tqdm(unique, desc="Scanning local models", unit="model", disable=not sys.stderr.isatty()):
        specs.append(inspect_model(fp))
    return specs


def resolve_engine_exe(engine_basename: str, engine_dirs: Sequence[Path] = DEFAULT_ENGINE_DIRS) -> str:
    """Locate a built CUDA 13.5 SM120 native engine binary on disk."""
    for directory in engine_dirs:
        candidate = directory / engine_basename
        if candidate.is_file():
            return str(candidate).replace("\\", "/")
    return str(DEFAULT_ENGINE_DIRS[0] / engine_basename).replace("\\", "/")


def plan_full_machine(
    hw: HardwareProfile,
    model: ModelSpec,
    context: int | None = None,
    prefer_engine: str | None = None,
    engine_dirs: Sequence[Path] = DEFAULT_ENGINE_DIRS,
) -> ExecutionPlan:
    """Compute a full-machine heterogeneous execution plan across GPU + CPU + RAM + SSD."""
    floors_ok, floor_warnings = check_resource_floors(hw)
    engine_name = prefer_engine or model.recommended_engine
    exe = resolve_engine_exe(engine_name, engine_dirs=engine_dirs)

    # CPU split: all physical primary cores for GPU host + AVX2 compute; all SMT secondary threads for async I/O.
    compute_threads = max(1, hw.physical_cores)
    io_smt_threads = max(1, len(hw.smt_secondary_cpus))
    aux_cpu_str = str(hw.smt_secondary_cpus[0]) if hw.smt_secondary_cpus else "auto"

    # WDDM-safe VRAM reserve on <= 17 GiB Windows cards prevents silent Shared-GPU-Memory spills.
    wddm_reserve_gib = 1.5 if hw.vram_total_gib <= 17.0 else 0.75
    usable_vram_gib = max(0.0, hw.vram_free_gib - wddm_reserve_gib)

    # Commit-safe pinned RAM cap (matches inkling2_engine.cu & hy4 commit budget guardrails).
    safe_ram_headroom = 7.5
    ram_headroom_avail = min(hw.ram_avail_gib, hw.commit_avail_gib)
    pinned_ram_cap_gib = max(0.0, min(10.0, ram_headroom_avail - safe_ram_headroom))

    # Context defaults tuned to RTX 5060 Ti 16 GB + 32 GB DDR4.
    if context is None:
        if model.family in ("inkling2_gguf", "inkling2_strata"):
            context = 131072 if model.size_gib <= 17.0 else 65536
        elif model.family == "qwen38_dense":
            context = 16384
        elif model.family == "hy4flash":
            context = 32768
        else:
            context = 32768

    gpu_budget = min(model.size_gib, usable_vram_gib)
    overflow_gib = max(0.0, model.size_gib - gpu_budget)
    ram_pinned_budget = min(overflow_gib, pinned_ram_cap_gib)
    ssd_stream_gib = max(0.0, overflow_gib - ram_pinned_budget)

    if overflow_gib <= 0.15:
        tier_mode = "GPU-resident (VRAM + CPU Host/Prefetch)"
    elif ssd_stream_gib <= 0.15:
        tier_mode = "GPU+CPU+RAM Hybrid (VRAM + Pinned RAM + 6P/6SMT)"
    else:
        tier_mode = "GPU+CPU+RAM+SSD 3-Tier (VRAM + Pinned RAM + SSD Stream + 6P/6SMT)"

    # Only sweep CUDA/background threads onto aux CPUs automatically when spare physical cores exist;
    # on 6C/12T (where aux is a single SMT sibling [1]), sweeping 14 driver threads onto CPU 1 hurts GPU latency
    # (measured on Ryzen 5 4500 + RTX 5060 Ti: 42.33 t/s off vs 35.73 t/s auto), while keeping io_smt=[1,3,5,7,9,11] ON.
    aux_mode = "auto" if hw.physical_cores > compute_threads else "off"
    env: dict[str, str] = {
        "STRATA_AUX_CPUS": aux_mode,
        "STRATA_AUX_IO_SMT": "1",
        "STRATA_SSD_PREFETCH": "1",
        "STRATA_RH_3TIER": "1",
        "STRATA_SATA_PF_THREADS": "1",
        "STRATA_SATA_COALESCE_GAP_KB": "14336",
        "STRATA_IO_THREADS": str(min(6, io_smt_threads)),
        "STRATA_MAX_PIN_MB": str(int(pinned_ram_cap_gib * 1024)),
        "STRATA_RAM_SQUEEZE": "on" if overflow_gib > 2.0 else "off",
    }

    model_posix = str(model.path).replace("\\", "/")
    args: list[str]
    if engine_name == "strata-inkling2.exe":
        # Reserve space for dense weights + KV cache (~4.5 GiB at 131K Q8) before expert VRAM slabs.
        kv_est_gib = 0.55 if context <= 32768 else (1.1 if context <= 65536 else 2.2)
        dense_est_gib = 3.8
        expert_vram_gib = max(1.0, round(usable_vram_gib - dense_est_gib - kv_est_gib, 2))
        gpu_budget = min(model.size_gib, round(expert_vram_gib + dense_est_gib, 2))
        overflow_gib = max(0.0, round(model.size_gib - gpu_budget, 2))
        ram_pinned_budget = round(min(overflow_gib, pinned_ram_cap_gib), 2)
        ssd_stream_gib = round(max(0.0, overflow_gib - ram_pinned_budget), 2)
        if overflow_gib <= 0.15:
            tier_mode = "GPU-resident (VRAM + CPU Host/Prefetch)"
        elif ssd_stream_gib <= 0.15:
            tier_mode = "GPU+CPU+RAM Hybrid (VRAM + Pinned RAM + 6P/6SMT)"
        else:
            tier_mode = "GPU+CPU+RAM+SSD 3-Tier (VRAM + Pinned RAM + SSD mmap Prefetch + 6P/6SMT)"
        args = [
            "--model",
            model_posix,
            "--max-context",
            str(context),
            "--kv-q8",
        ]
        # Let engine's own Gen-L WDDM 1536 MiB auto-reserve pick optimal VRAM budget; record estimate for telemetry.
        env["STRATA_VRAM_RESERVE_MB"] = str(int(wddm_reserve_gib * 1024))
    elif engine_name == "strata-inkling.exe":
        args = [
            "--native",
            model_posix,
            "--max-context",
            str(context),
        ]
        env["STRATA_INK_THREADS"] = str(compute_threads)
    elif engine_name == "strata-q38.exe":
        args = [
            "--model",
            model_posix,
            "--ctx-size",
            str(context),
            "--kv",
            "auto",
        ]
    elif engine_name == "strata-hy4.exe":
        args = [
            "--native",
            model_posix,
            "--max-context",
            str(context),
            "--chunk",
            "2048",
        ]
        env["HY4_KV_INIT_SLOTS"] = str(min(16384, context))
        env["HY4_VCACHE_FRAC"] = "0.35"
    else:
        resident_gib = max(0.0, round(ram_pinned_budget, 2))
        args = [
            "--model",
            model_posix,
            "--max-context",
            str(context),
            "--aux-cpus",
            aux_cpu_str,
            "--resident-budget-gib",
            f"{resident_gib:.2f}",
        ]

    return ExecutionPlan(
        model=model_posix,
        family=model.family,
        architecture=model.architecture,
        tier_mode=tier_mode,
        engine_exe=exe,
        context=context,
        gpu_budget_gib=round(gpu_budget, 2),
        ram_pinned_budget_gib=round(ram_pinned_budget, 2),
        ssd_stream_gib=round(ssd_stream_gib, 2),
        cpu_compute_threads=compute_threads,
        cpu_io_smt_threads=io_smt_threads,
        primary_cpus=hw.primary_cpus,
        smt_secondary_cpus=hw.smt_secondary_cpus,
        args=tuple(args),
        env=env,
        floors_ok=floors_ok,
        floor_warnings=floor_warnings,
        release_qualified=False,
    )


def resolve_model_argument(model_arg: str, discovered: Sequence[ModelSpec]) -> ModelSpec:
    """Resolve an explicit path or substring query against discovered local models."""
    direct = Path(model_arg)
    if direct.is_file():
        return inspect_model(direct)
    low = model_arg.lower()
    for spec in discovered:
        if low in spec.name.lower() or low in str(spec.path).lower():
            return spec
    raise FileNotFoundError(f"Model not found: {model_arg}")


def log_hardware_summary(hw: HardwareProfile) -> None:
    """Log the full physical hardware topology clearly."""
    disk_str = ", ".join(f"{d.mount} {d.free_gib:.1f}/{d.total_gib:.1f} GiB free" for d in hw.disks)
    LOGGER.info(
        "GPU: %s (%.2f/%.2f GiB VRAM free, SM %s, PCIe Gen%d x%d, %.0fW)",
        hw.gpu_name,
        hw.vram_free_gib,
        hw.vram_total_gib,
        hw.compute_cap,
        hw.pcie_gen,
        hw.pcie_width,
        hw.power_limit_w,
    )
    LOGGER.info(
        "CPU: %d physical cores / %d logical threads | Primary=%s | SMT-IO=%s",
        hw.physical_cores,
        hw.logical_threads,
        list(hw.primary_cpus),
        list(hw.smt_secondary_cpus),
    )
    LOGGER.info(
        "RAM: %.2f/%.2f GiB free | Commit: %.2f/%.2f GiB free | Storage: %s",
        hw.ram_avail_gib,
        hw.ram_total_gib,
        hw.commit_avail_gib,
        hw.commit_total_gib,
        disk_str or "none",
    )


def log_execution_plan(plan: ExecutionPlan) -> None:
    """Log the computed 3-tier heterogeneous placement plan."""
    LOGGER.info("Model: %s (arch=%s, family=%s)", plan.model, plan.architecture, plan.family)
    LOGGER.info("Mode: %s | releaseQualified=%s", plan.tier_mode, plan.release_qualified)
    LOGGER.info(
        "Tiers: GPU=%.2f GiB | RAM_pinned=%.2f GiB | SSD_stream=%.2f GiB | CPU=%dP+%dSMT",
        plan.gpu_budget_gib,
        plan.ram_pinned_budget_gib,
        plan.ssd_stream_gib,
        plan.cpu_compute_threads,
        plan.cpu_io_smt_threads,
    )
    LOGGER.info("Engine: %s %s", plan.engine_exe, " ".join(plan.args))
    LOGGER.info("Env: %s", " ".join(f"{k}={v}" for k, v in sorted(plan.env.items())))
    if not plan.floors_ok:
        for warn in plan.floor_warnings:
            LOGGER.warning("Resource floor violation: %s", warn)


def build_serve_config(plan: ExecutionPlan, host: str = "127.0.0.1", port: int = 8092) -> dict[str, object]:
    """Generate a terminal/serve/server.py-compatible config dict for the planned model."""
    model_stem = Path(plan.model).stem
    arch_field = "inkling2_loop" if plan.family.startswith("inkling2") else plan.family
    cfg: dict[str, object] = {
        "exe": plan.engine_exe,
        "arch": arch_field,
        "model_name": model_stem.lower(),
        "aliases": [model_stem, model_stem.lower()],
        "drafting": "off",
        "args": list(plan.args),
        "env": dict(plan.env),
        "host": host,
        "port": port,
        "open_browser": False,
        "fit_max_tokens": True,
    }
    return cfg


def maybe_squeeze_ram() -> None:
    """Invoke Strata's built-in non-destructive RAM working-set trim if available."""
    terminal_dir = str(REPO_ROOT / "terminal")
    if terminal_dir not in sys.path:
        sys.path.insert(0, terminal_dir)
    try:
        from strata_control import ram_fit  # type: ignore[import-not-found]

        before = ram_fit.mem_gib()
        ram_fit.squeeze()
        after = ram_fit.mem_gib()
        if before and after:
            LOGGER.info(
                "RAM squeeze complete: avail %.2f -> %.2f GiB (commit %.2f -> %.2f GiB)",
                before["avail_gib"],
                after["avail_gib"],
                before.get("commit_free_gib") or 0.0,
                after.get("commit_free_gib") or 0.0,
            )
    except Exception as exc:  # noqa: BLE001 - advisory optimization must never crash launcher
        LOGGER.warning("RAM squeeze skipped: %s", exc)


def run_benchmark(plan: ExecutionPlan, tokens: str, max_new: int, runs: int) -> int:
    """Run live native inference benchmark under the planned full-machine environment."""
    if not Path(plan.engine_exe).is_file():
        LOGGER.error("Engine executable does not exist: %s", plan.engine_exe)
        return 2
    if not plan.floors_ok:
        LOGGER.error("Aborting benchmark due to resource floor violation: %s", "; ".join(plan.floor_warnings))
        return 3

    env = dict(os.environ)
    env.update(plan.env)
    cmd = [plan.engine_exe, *plan.args]
    if plan.family == "inkling2_gguf":
        cmd += ["--bench", "--tokens", tokens, "--max-new", str(max_new)]
    elif plan.family == "inkling2_strata":
        cmd = [
            plan.engine_exe,
            "--bench",
            "--native",
            plan.model,
            "--prompt-len",
            str(max(1, len(tokens.split(",")))),
            "--gen",
            str(max_new),
        ]
    elif plan.family == "qwen38_dense":
        cmd += ["--tokens", tokens, "--n", str(max_new)]
    else:
        cmd += ["--tokens", tokens, "--max-new", str(max_new)]

    for run_idx in tqdm(range(1, runs + 1), desc="Full-machine benchmark", unit="run", disable=not sys.stderr.isatty()):
        t0 = time.perf_counter()
        LOGGER.info("Run %d/%d: %s", run_idx, runs, " ".join(cmd))
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, errors="replace", check=False)
        elapsed = time.perf_counter() - t0
        for line in proc.stderr.splitlines():
            if line.strip():
                LOGGER.info("[engine] %s", line)
        if proc.stdout.strip():
            LOGGER.info("[tokens] %s", proc.stdout.strip().splitlines()[-1])
        LOGGER.info("Run %d/%d exited rc=%d in %.2f s", run_idx, runs, proc.returncode, elapsed)
        if proc.returncode != 0:
            return proc.returncode
    return 0


def launch_server(plan: ExecutionPlan, host: str, port: int, squeeze: bool, config_out: Path | None) -> int:
    """Write a full-machine config and launch terminal/serve/server.py."""
    if not plan.floors_ok:
        LOGGER.error("Aborting server start due to resource floor violation: %s", "; ".join(plan.floor_warnings))
        return 3
    if squeeze or plan.env.get("STRATA_RAM_SQUEEZE") == "on":
        maybe_squeeze_ram()

    cfg = build_serve_config(plan, host=host, port=port)
    cfg_path = config_out or (REPO_ROOT / "configs" / f"strata-full-machine-{Path(plan.model).stem.lower()}.json")
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    LOGGER.info("Wrote full-machine server config to %s", cfg_path)

    env = dict(os.environ)
    env.update(plan.env)
    cmd = [
        sys.executable,
        "-m",
        "serve.server",
        "--engine",
        "strata",
        "--config",
        str(cfg_path),
        "--host",
        host,
        "--port",
        str(port),
    ]
    LOGGER.info("Launching Strata full-machine server at http://%s:%d ...", host, port)
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT / "terminal"), env=env, check=False)
    return proc.returncode


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Full-machine heterogeneous inference planner & runner (GPU + 6P/6SMT CPU + RAM + SSD).",
    )
    parser.add_argument("--list-models", action="store_true", help="Discover local models and show tier plans.")
    parser.add_argument("--plan", action="store_true", help="Compute and display the full-machine execution plan.")
    parser.add_argument("--bench", action="store_true", help="Run a live native benchmark with full-machine settings.")
    parser.add_argument("--serve", action="store_true", help="Launch OpenAI/Anthropic API server with full-machine settings.")
    parser.add_argument("--model", type=str, default="", help="Model file path or substring match in H:/C: models.")
    parser.add_argument("--context", type=int, default=None, help="Explicit context window size.")
    parser.add_argument("--tokens", type=str, default="1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16", help="Benchmark token IDs.")
    parser.add_argument("--max-new", type=int, default=32, help="Tokens to generate in --bench mode.")
    parser.add_argument("--runs", type=int, default=1, help="Number of benchmark iterations.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Bind host for --serve (default 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8092, help="Bind port for --serve.")
    parser.add_argument("--squeeze", action="store_true", help="Run non-destructive RAM squeeze before --serve.")
    parser.add_argument("--write-config", type=Path, default=None, help="Optional path to save generated server JSON config.")
    parser.add_argument("--output", choices=("text", "json"), default="text", help="Output format for --plan / --list-models.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose debug logging.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args(argv)
    configure_logging(verbose=args.verbose)
    hw = probe_hardware()
    log_hardware_summary(hw)

    discovered = discover_models()
    if args.list_models or (not args.plan and not args.bench and not args.serve and not args.model):
        plans = [plan_full_machine(hw, spec, context=args.context) for spec in discovered]
        if args.output == "json":
            payload = {
                "hardware": asdict(hw),
                "models": [
                    {
                        "name": spec.name,
                        "path": str(spec.path).replace("\\", "/"),
                        "size_gib": spec.size_gib,
                        "architecture": spec.architecture,
                        "family": spec.family,
                        "plan": asdict(pl),
                    }
                    for spec, pl in zip(discovered, plans)
                ],
            }
            sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
            return 0
        LOGGER.info("Discovered %d runnable local models:", len(discovered))
        for spec, pl in zip(discovered, plans):
            LOGGER.info(
                "  - %s (%.2f GiB, arch=%s) -> %s | %s | GPU=%.2fG RAM=%.2fG SSD=%.2fG",
                spec.name,
                spec.size_gib,
                spec.architecture,
                Path(pl.engine_exe).name,
                pl.tier_mode,
                pl.gpu_budget_gib,
                pl.ram_pinned_budget_gib,
                pl.ssd_stream_gib,
            )
        return 0

    if not args.model:
        if not discovered:
            LOGGER.error("No models found under H:/Strata/models or C:/Strata/models; pass --model explicitly.")
            return 1
        spec = discovered[0]
    else:
        try:
            spec = resolve_model_argument(args.model, discovered)
        except FileNotFoundError as exc:
            LOGGER.error("%s", exc)
            return 1

    plan = plan_full_machine(hw, spec, context=args.context)
    log_execution_plan(plan)

    if args.write_config and not args.serve:
        cfg = build_serve_config(plan, host=args.host, port=args.port)
        args.write_config.parent.mkdir(parents=True, exist_ok=True)
        args.write_config.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        LOGGER.info("Wrote server config to %s", args.write_config)

    if args.plan and not args.bench and not args.serve:
        if args.output == "json":
            sys.stdout.write(json.dumps({"hardware": asdict(hw), "plan": asdict(plan)}, indent=2, ensure_ascii=False) + "\n")
        return 0 if plan.floors_ok else 3

    if args.bench:
        return run_benchmark(plan, tokens=args.tokens, max_new=args.max_new, runs=max(1, args.runs))

    if args.serve:
        return launch_server(plan, host=args.host, port=args.port, squeeze=args.squeeze, config_out=args.write_config)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
