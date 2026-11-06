"""Task-local, bounded native build/qualification; never controls user processes."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
OUT = Path("H:/Strata/releases/personal-052-local2-20261107")
UV = Path("C:/Users/downl/.local/bin/uv.exe")
PYTHON = Path("C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe")
NODE = Path("C:/Users/downl/AppData/Local/Programs/Strata/node/node.exe")
CUDA = Path("C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3")
sys.path.insert(0, str(ROOT / "tools"))
from native_model_resource_guard import available_memory
from perf131k.windows_job import run_owned


def environment() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items()
           if not k.upper().startswith(("STRATA_", "DSH_", "PYTHON", "CUDA_", "CMAKE_"))}
    env.update(TMP=str(OUT / "temp"), TEMP=str(OUT / "temp"),
               PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
               CUDA_PATH=str(CUDA), CUDA_PATH_V13_3=str(CUDA), CMAKE_BUILD_PARALLEL_LEVEL="1",
               CTEST_PARALLEL_LEVEL="1", MSBUILDDISABLENODEREUSE="1")
    env["PATH"] = ";".join([str(CUDA / "bin/x64"), str(CUDA / "bin"),
                            str(PYTHON.parent), "C:/Program Files/CMake/bin", env["PATH"]])
    return env


def sample(_: Path) -> dict[str, int]:
    memory = available_memory()
    return {"available_ram": memory["available_physical_bytes"],
            "commit_headroom": memory["available_commit_bytes"],
            "H_free": shutil.disk_usage("H:/").free}


def main() -> int:
    action, *args = sys.argv[1:]
    if action == "init":
        assert OUT.parent.is_dir() and not OUT.exists(), "Fresh owned output required"
        OUT.mkdir()
        for name in ("temp", "receipts"):
            (OUT / name).mkdir()
        print(str(OUT), flush=True)
        return 0
    name, seconds, *command = args
    assert name.replace("-", "").isalnum() and command
    assert OUT.is_dir() and (OUT / "temp").is_dir()
    seconds = int(seconds)
    assert 0 < seconds <= 5400
    receipt = OUT / "receipts" / (name + ".json")
    assert not receipt.exists(), "Retain prior attempt evidence"
    if action == "launch":
        with (OUT / "receipts" / (name + "-controller.txt")).open("x") as log:
            proc = subprocess.Popen(
                [str(UV), "run", "--offline", "--no-project", "--python", str(PYTHON),
                 "python", "-B", str(Path(__file__).resolve()), "run", name,
                 str(seconds), *command], cwd=ROOT, env=environment(),
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW)
        print(json.dumps({"controllerPid": proc.pid, "receipt": str(receipt)}), flush=True)
        return 0
    assert action == "run"
    budget = SimpleNamespace(job_commit_bytes=None, max_processes=64,
                             min_available_ram=3 * 1024**3, min_commit_headroom=4 * 1024**3,
                             min_H_free=10 * 1024**3, timeout_s=seconds, output_bytes=64 * 1024**2)
    report = {"name": name, "command": command, "started": time.time(), "deadlineSeconds": seconds}
    with receipt.open("x", encoding="utf-8") as record:
        record.write(json.dumps(report) + "\n")
    try:
        pre = sample(ROOT)
        report["preflight"] = pre
        assert pre["available_ram"] >= budget.min_available_ram, "RAM floor"
        assert pre["commit_headroom"] >= budget.min_commit_headroom, "commit floor"
        assert pre["H_free"] >= budget.min_H_free, "H disk floor"
        assert shutil.disk_usage("C:/").free >= 5 * 1024**3, "C disk floor"
        report["run"] = run_owned(
            command, ROOT, environment(), OUT / "receipts" / (name + ".txt"), budget, sample,
            memory_diagnostics=True,
            on_tick=lambda: "C_disk_floor" if shutil.disk_usage("C:/").free < 5 * 1024**3 else None)
        run = report["run"]
        report["passed"] = (run["status"] == "FINISHED" and run["native_exit_code"] == 0
                            and run["termination_confirmed"] and run["contained_before_resume"])
    except BaseException as error:
        report.update(passed=False, error=f"{type(error).__name__}: {error}")
    finally:
        report["finished"] = time.time()
        receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report), flush=True)
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
