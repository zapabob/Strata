"""Explicit five-job native rebuild with copied incremental objects and retained evidence.

Default plan is read-only. This is a build driver, not model qualification or
installation. Old native source, signed packages and build outputs stay intact.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
OUT = Path("H:/Strata/releases/upstream-0213-20261109-opencode")
OLD = Path("H:/Strata/releases/local-053-20261109-opencode/native-build")
BUILD = OUT / "native-build"


def load_guard():
    spec = importlib.util.spec_from_file_location("native_guard", ROOT / "_docs/local-053-20261109/native/common.py")
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    guard.BASE, guard.BUILD = OUT, BUILD
    return guard


def inventory(folder: Path) -> dict[str, tuple[int, str]]:
    result = {}
    for base, dirs, names in os.walk(folder, followlinks=False):
        for name in dirs + names:
            path = Path(base) / name
            if path.is_symlink() or path.is_junction():
                raise ValueError(f"Linked build input refused: {path}")
        for name in names:
            path = Path(base) / name
            with path.open("rb") as source:
                result[path.relative_to(folder).as_posix()] = (path.stat().st_size, hashlib.file_digest(source, "sha256").hexdigest())
    return result


def worker(action: str, guard) -> None:
    guard.require_current_job(ROOT)
    if action == "prepare":
        guard.no_links(OLD)
        guard.require(OLD.is_dir() and not BUILD.exists(), "Copy only into a fresh incremental-build root")
        before = inventory(OLD)
        guard.require(shutil.disk_usage(OUT).free > sum(size for size, _ in before.values()) + 10 * guard.GIB,
                      "Copied objects must leave the unchanged H: floor")
        shutil.copytree(OLD, BUILD, copy_function=shutil.copy2)
        guard.require(inventory(BUILD) == before and inventory(OLD) == before, "Incremental seed copy changed bytes")
        # CMake caches have absolute source/build paths. Retain the old cache,
        # then regenerate the graph; object files and libraries remain available.
        (BUILD / "CMakeCache.txt").rename(BUILD / "CMakeCache.pre-0213.txt")
        guard.save(OUT / "incremental-seed.json", {"source": str(OLD), "target": str(BUILD),
            "files": len(before), "bytes": sum(size for size, _ in before.values()),
            "allHashesMatched": True, "oldBuildUnchanged": True,
            "inventorySHA256": hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()}, fresh=True)
        print("Incremental objects copied and verified; original source/build evidence retained.")
        return
    guard.require((OUT / "incremental-seed.json").is_file(), "Verified incremental seed required")
    if action == "configure":
        command = guard.configure(ROOT)
    else:
        cache = (BUILD / "CMakeCache.txt").read_text(encoding="utf-8")
        for key, value in {"STRATA_PORTABLE": "ON", "STRATA_ENABLE_CUDA": "ON",
                           "STRATA_ENABLE_SPIN8": "ON", "STRATA_ENABLE_NATIVE_CACHE": "ON",
                           "CMAKE_CUDA_ARCHITECTURES": "120", "STRATA_CUDA_SPILL_BASELINE": ""}.items():
            match = re.search(r"^" + re.escape(key) + r":[^=]+=([^\r\n]*)", cache, re.M)
            guard.require(match is not None and match[1] == value, f"Configured recipe mismatch: {key}")
        command = [str(guard.NODE), str(ROOT / "tools/build_hakua_engine.mjs"), str(BUILD), "5"]
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "prepare", "configure", "build", "launch", "_worker"))
    parser.add_argument("--phase", choices=("prepare", "configure", "build"))
    parser.add_argument("--attempt", default="r1")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.action == "plan":
        print(json.dumps({"source": str(ROOT), "oldBuild": str(OLD), "newBuild": str(BUILD),
            "jobs": 5, "sourceVersion": "0.5.4", "phases": ["prepare", "configure", "build"],
            "oldOutputsPreserved": True, "modelQualification": False, "installation": False}, indent=2))
        return 0
    if not args.execute or not OUT.is_dir():
        parser.error("Explicit --execute and the existing approved output are required")
    guard = load_guard()
    if args.action == "launch":
        command = [str(guard.UV), "run", "--offline", "--no-config", "--no-project",
                   "--python", str(guard.PYTHON), "python", "-B", str(Path(__file__).resolve()),
                   "build", "--attempt", args.attempt, "--execute"]
        env = guard.environment()
        env.update(CMAKE_BUILD_PARALLEL_LEVEL="5", CARGO_BUILD_JOBS="5", PYTHONUTF8="1")
        with (OUT / "receipts" / f"native-build-controller-{args.attempt}.txt").open("x", encoding="utf-8") as output:
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                       stdout=output, stderr=subprocess.STDOUT,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
        report = {"controllerPid": process.pid, "command": command, "jobs": 5,
                  "controllerIsNotOwnedWorker": True,
                  "receipt": str(OUT / "receipts" / f"native-build-{args.attempt}.json")}
        guard.save(OUT / f"native-build-launch-{args.attempt}.json", report, fresh=True)
        print(json.dumps(report, indent=2))
        return 0
    if args.action == "_worker":
        guard.require(args.phase, "Explicit worker phase required")
        worker(args.phase, guard)
        return 0
    env = guard.environment()
    env.update(CMAKE_BUILD_PARALLEL_LEVEL="5", CARGO_BUILD_JOBS="5", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "_worker", "--phase", args.action, "--execute"]
    seconds = 5400 if args.action == "build" else 1800 if args.action == "prepare" else 300
    result = guard.owned(ROOT, f"native-{args.action}-{args.attempt}", command, seconds, env=env,
                         output_bytes=64 * 1024**2)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        print(guard.text(result["name"]))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
