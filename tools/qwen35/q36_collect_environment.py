#!/usr/bin/env python3
"""Passive, private build manifest. Never loads CUDA or runs a model/GPU probe."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess


def observation(value=None, reason=None, status=None):
    return {"value": value, "status": status or ("OBSERVED" if value is not None else "UNAVAILABLE"),
            "reason": reason if value is None else None}


def run(argv, cwd=None, hash_output=False):
    """Do not retain stderr, which can contain private paths or credentials."""
    try:
        result = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=30)
        if result.returncode:
            return observation(reason=f"command exited {result.returncode}")
        if hash_output:
            return observation(hashlib.sha256(result.stdout).hexdigest())
        return observation(result.stdout.decode("utf-8", errors="replace").strip())
    except (OSError, subprocess.TimeoutExpired) as exc:
        return observation(reason=type(exc).__name__)


def file_identity(path):
    if path is None:
        return observation(reason="no file specified")
    path = Path(path).resolve()
    try:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return observation({"path": str(path), "bytes": path.stat().st_size,
                            "sha256": digest.hexdigest()})
    except OSError as exc:
        return observation(reason=type(exc).__name__)


def source_identity(root):
    root = Path(root).resolve()
    sha = run(["git", "rev-parse", "HEAD"], root)
    status = run(["git", "status", "--porcelain=v1", "--untracked-files=no"], root)
    # Hash the tracked diff, including staged changes. Never serialize its contents.
    diff_hash = run(["git", "diff", "HEAD", "--binary", "--no-ext-diff", "--no-textconv"],
                    root, hash_output=True)
    return {"root": str(root), "sha": sha,
            "tracked_dirty": observation(bool(status["value"])) if status["value"] is not None else status,
            "tracked_diff_sha256": diff_hash,
            "untracked": observation(reason="not read; private evidence is not source", status="NOT_RUN")}


def cmake_cache(path):
    identity = file_identity(path)
    if identity["value"] is None:
        return {"file": identity, "settings": observation(reason="CMake cache unavailable")}
    settings = {}
    # No environment dump, credentials or unrelated cache variables.
    pattern = re.compile(r"^((?:CMAKE_(?:CUDA|CXX|C)_FLAGS\w*|CMAKE_(?:CUDA_ARCHITECTURES|BUILD_TYPE|GENERATOR\w*|CUDA_RUNTIME_LIBRARY)|STRATA_\w+|GGML_\w+|SPIN8_\w+|TQCODEC_\w+)):[^=]+=(.*)$")
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.match(line)
        if match:
            settings[match[1]] = match[2]
    return {"file": identity, "settings": observation(settings)}


def compiler_metadata(build_dir):
    data = {}
    if build_dir is not None:
        for name in ("CMakeCUDACompiler.cmake", "CMakeCXXCompiler.cmake"):
            files = sorted((Path(build_dir) / "CMakeFiles").glob(f"*/{name}"))
            if files:
                text = files[-1].read_text(encoding="utf-8", errors="replace")
                for key, value in re.findall(r'set\((CMAKE_(?:CUDA|CXX)_(?:COMPILER|COMPILER_VERSION|HOST_COMPILER|HOST_COMPILER_VERSION|RUNTIME_LIBRARY_DEFAULT)) "([^"\n]*)"\)', text):
                    data[key] = value
    return observation(data) if data else observation(reason="compiler metadata unavailable before configure")


def windows_inventory():
    """Read only selected OS/CIM fields. This does not call NVIDIA utilities."""
    if platform.system() != "Windows":
        return observation(reason="Windows CIM inventory unsupported on this OS")
    script = """$ErrorActionPreference='Stop';
$o=Get-CimInstance Win32_OperatingSystem;
$m=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory;
$c=@(Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors);
$g=@(Get-CimInstance Win32_VideoController | Select-Object Name,PNPDeviceID,DriverVersion,DriverDate);
[pscustomobject]@{os=$o.Caption;build=$o.BuildNumber;cpu=$c;ram_total_bytes=([uint64]$o.TotalVisibleMemorySize*1024);ram_available_bytes=([uint64]$o.FreePhysicalMemory*1024);commit_limit_bytes=[uint64]$m.CommitLimit;committed_bytes=[uint64]$m.CommittedBytes;commit_headroom_bytes=([uint64]$m.CommitLimit-[uint64]$m.CommittedBytes);display=$g}|ConvertTo-Json -Depth 5 -Compress"""
    result = run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script])
    if result["value"] is not None:
        try:
            return observation(json.loads(result["value"]))
        except json.JSONDecodeError:
            return observation(reason="CIM output was not JSON")
    return result


def loaded_modules(pid):
    """Optional passive snapshot of an already-running process; never starts it."""
    if pid is None:
        return observation(reason="no running process selected; files are not loaded DLL evidence", status="NOT_RUN")
    if platform.system() != "Windows":
        return observation(reason="process module snapshot only supported on Windows")
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        raise ValueError("pid must be a positive integer")
    script = ("$ErrorActionPreference='Stop'; @((Get-Process -Id " + str(pid)
              + ").Modules | ForEach-Object {$_.FileName}) | ConvertTo-Json -Compress")
    result = run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script])
    if result["value"] is None:
        return result
    try:
        paths = json.loads(result["value"])
        if isinstance(paths, str):
            paths = [paths]
        if not isinstance(paths, list):
            return observation(reason="no module paths returned")
        return observation({"pid": pid, "modules": [file_identity(p) for p in paths]})
    except (json.JSONDecodeError, TypeError):
        return observation(reason="module output was not a path list")


def collect_environment(source_root=None, build_dir=None, nvcc=None, binaries=(),
                        dependencies=(), pid=None) -> dict:
    """Collect schema v1 without GPU access. All unavailable facts have reasons.

    Outputs contain machine paths and belong in private evidence, never in Git.
    CUDA runtime/device facts require a separate, explicitly authorised probe.
    """
    root = Path(source_root or Path(__file__).resolve().parents[2]).resolve()
    build = Path(build_dir).resolve() if build_dir else None
    metadata = compiler_metadata(build)
    known = metadata["value"] or {}
    compiler = nvcc or known.get("CMAKE_CUDA_COMPILER") or shutil.which("nvcc")
    nvcc_path = str(Path(compiler).resolve()) if compiler else None
    unavailable = "NOT_RUN: requires controller clearance and real-GPU ownership; no CUDA library loaded"
    disk = shutil.disk_usage(root)
    return {
        "schema_version": 1,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "passive_no_cuda_initialisation",
        "source": source_identity(root),
        "dependencies": [source_identity(p) for p in dependencies],
        "platform": observation({"system": platform.system(), "release": platform.release(),
                                 "machine": platform.machine()}),
        "host": windows_inventory(),
        "disk": observation({"path": str(root.anchor), "total_bytes": disk.total,
                             "available_bytes": disk.free}),
        "nvcc": {"file": file_identity(nvcc_path), "version": run([nvcc_path, "--version"])
                 if nvcc_path else observation(reason="nvcc not found")},
        "host_compiler": metadata,
        "cmake_cache": cmake_cache(build / "CMakeCache.txt" if build else None),
        "binaries": [file_identity(p) for p in binaries],
        "loaded_dlls": loaded_modules(pid),
        "cuda": {key: observation(reason=unavailable, status="NOT_RUN") for key in (
            "cudaRuntimeGetVersion", "cudaDriverGetVersion", "gpu_uuid", "device_id",
            "pcie_link", "dedicated_vram_total_bytes", "dedicated_vram_available_bytes",
            "asyncEngineCount", "concurrentManagedAccess")},
        "linkage": observation(reason="inspect generated link inputs and PE imports; DLL absence alone cannot prove static cudart", status="NOT_RUN"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--build-dir", type=Path)
    parser.add_argument("--nvcc", type=Path)
    parser.add_argument("--binary", type=Path, action="append", default=[])
    parser.add_argument("--dependency", type=Path, action="append", default=[])
    parser.add_argument("--pid", type=int)
    parser.add_argument("--output", type=Path, required=True, help="new private JSON file; refuses overwrite")
    args = parser.parse_args()
    data = collect_environment(args.source_root, args.build_dir, args.nvcc,
                               args.binary, args.dependency, args.pid)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
