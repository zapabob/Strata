"""Sequential launch gate for the reviewed Windows bounded-process guard.

Each prerequisite must be a completed successful guard receipt. Failed checks
raise before launching anything. Each launch uses a fresh PowerShell 5.1 host.
Plans are trusted local validation instructions, never untrusted model output.
"""

from __future__ import annotations

import argparse
import base64
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess

from verify_native_pack_binding import receipt_mtime_ns


def digest(path: Path) -> str:
    """Hash executable/source evidence without loading it all into RAM."""
    result = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def successful_receipt(path: Path) -> dict:
    """Require explicit terminal, containment and cleanup evidence, not truthiness."""
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    fields = {
        "state",
        "child_exit_code",
        "guard_reason",
        "error",
        "contained_before_resume",
        "active_processes_after_cleanup",
    }
    if not (
        fields <= data.keys()
        and type(data.get("schema")) is int
        and data["schema"] == 1
        and data["state"] == "finished"
        and type(data["child_exit_code"]) is int
        and data["child_exit_code"] == 0
        and data["guard_reason"] is None
        and data["error"] is None
        and data["contained_before_resume"] is True
        and type(data["active_processes_after_cleanup"]) is int
        and data["active_processes_after_cleanup"] == 0
    ):
        raise ValueError(f"unsuccessful or unfinished prerequisite: {path}")
    return data


def model_metadata(receipt_path: Path) -> list[dict]:
    """Reuse completed full hashes only with unchanged exact Windows timestamps."""
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    if not receipt.get("models"):
        raise ValueError("empty model source receipt")
    checked = []
    for record in receipt["models"]:
        path = Path(record["path"])
        stat = path.stat()
        if not (
            record["matches"] is True
            and record["metadata_unchanged"] is True
            and re.fullmatch(r"[0-9a-fA-F]{64}", record["sha256"])
            and record["sha256"] == record["expected_sha256"]
            and stat.st_size == record["bytes"]
            and stat.st_mtime_ns == receipt_mtime_ns(record["last_write_utc"])
        ):
            raise ValueError(f"model source binding changed: {path}")
        checked.append(
            {
                "path": str(path),
                "bytes": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "sha256": record["sha256"],
            }
        )
    return checked


def runtime_resources() -> dict:
    """Read real RAM/commit/VRAM before a model process is permitted to start."""

    class Memory(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
            (name, ctypes.c_ulonglong)
            for name in (
                "physical",
                "free_physical",
                "commit",
                "free_commit",
                "virtual",
                "free_virtual",
                "extended",
            )
        ]

    memory = Memory()
    memory.length = ctypes.sizeof(memory)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
        raise OSError("GlobalMemoryStatusEx failed")
    try:
        gpu = subprocess.check_output(
            [
                str(Path(os.environ["SystemRoot"]) / "System32/nvidia-smi.exe"),
                "--query-gpu=memory.free",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10,
        )
    except subprocess.TimeoutExpired as error:
        # check_output owns and reaps this probe; no inference/guard child has
        # been launched. Keep this a typed failed preflight, never zero VRAM.
        raise ValueError("runtime GPU preflight timed out after 10 seconds") from error
    free_gpu_mib = int(gpu.splitlines()[0])
    if memory.free_physical < 4 * 1024**3 or memory.free_commit < 8 * 1024**3:
        raise ValueError("runtime RAM/commit preflight failed")
    if free_gpu_mib < 8192:
        raise ValueError("runtime VRAM preflight failed")
    return {
        "free_physical_bytes": memory.free_physical,
        "free_commit_bytes": memory.free_commit,
        "free_gpu_mib": free_gpu_mib,
    }


def run_step(plan_path: Path, label: str, prerequisites: list[Path]) -> int:
    """Check all prerequisites and preflight synchronously, then invoke one guard."""
    if not prerequisites:
        raise ValueError("at least one successful prerequisite is required")
    # Do not queue a child independently of these checks: an exception must stop
    # control flow here, including malformed or incomplete prerequisite receipts.
    for path in prerequisites:
        successful_receipt(path)
    if not re.fullmatch(r"[a-zA-Z0-9-]{1,100}", label) or re.fullmatch(
        r"CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9]", label, re.IGNORECASE
    ):
        raise ValueError("invalid evidence label")
    plan_bytes = plan_path.read_bytes()
    plan = json.loads(plan_bytes.decode("utf-8-sig"))
    root = Path(plan["output_root"])
    if root.parent.resolve() != Path("H:/Strata/build").resolve() or not re.fullmatch(
        r"task5a-[a-zA-Z0-9-]+", root.name
    ):
        raise ValueError(
            "evidence root must be an immediate H:/Strata/build/task5a-* directory"
        )
    if any(p.is_symlink() or p.is_junction() for p in [root, *root.parents]):
        raise ValueError("reparse evidence path is not allowed")
    preflight_path = root / f"{label}.preflight.json"
    if not root.is_dir():
        raise ValueError("create a fresh task5a evidence root before the step")
    preflight = {
        "schema": "strata-sequential-preflight-v1",
        "state": "starting",
        "exit_code": None,
        "validated": False,
        "started_utc": datetime.now(timezone.utc).isoformat(),
    }
    with preflight_path.open("x", encoding="utf-8") as output:
        json.dump(preflight, output, indent=2)
    try:
        if digest(Path(plan["binary"])) != plan["binary_sha256"]:
            raise ValueError("executable SHA-256 differs from reviewed plan")
        peak, cap, reserve = (
            plan[k]
            for k in (
                "expected_additional_peak_bytes",
                "max_output_bytes",
                "reserve_bytes",
            )
        )
        if any(type(x) is not int for x in (peak, cap, reserve)) or not (
            peak >= cap > 0 and reserve >= 10 * 1024**3
        ):
            raise ValueError("invalid explicit resource plan")
        free = shutil.disk_usage(root).free
        if free < peak + reserve:
            raise ValueError("disk preflight failed")
        if (
            not isinstance(plan["command_args"], list)
            or any(not isinstance(arg, str) for arg in plan["command_args"])
            or type(plan["timeout_seconds"]) is not int
            or plan["timeout_seconds"] <= 0
        ):
            raise ValueError("invalid command/timeout plan")
        preflight.update(
            free_disk_bytes=free,
            plan_sha256=hashlib.sha256(plan_bytes).hexdigest(),
            launcher_sha256=digest(Path(__file__)),
            prerequisite_sha256={str(p): digest(p) for p in prerequisites},
        )
        if plan.get("model_source_receipt"):
            preflight["models"] = model_metadata(Path(plan["model_source_receipt"]))
            preflight["resources"] = runtime_resources()
        preflight.update(state="finished", exit_code=0, validated=True)
    except Exception as error:
        preflight.update(state="finished", exit_code=1, error=str(error))
        raise
    finally:
        preflight["finished_utc"] = datetime.now(timezone.utc).isoformat()
        preflight_path.write_text(
            json.dumps(preflight, indent=2) + "\n", encoding="utf-8"
        )

    quoted_plan = str(plan_path.resolve()).replace("'", "''")
    quoted_check = str(preflight_path.resolve()).replace("'", "''")
    quoted_guard = str(
        Path(__file__).with_name("verify_codec_dialects_build.ps1")
    ).replace("'", "''")
    quoted_label = label.replace("'", "''")
    script = f"""
$ErrorActionPreference='Stop'
$v=Get-Content -LiteralPath '{quoted_check}' -Raw|ConvertFrom-Json
if($v.state -ne 'finished' -or $v.exit_code -ne 0 -or $v.validated -ne $true){{
    throw 'Preflight not successful'
}}
$bytes=[IO.File]::ReadAllBytes('{quoted_plan}')
$sha=[Security.Cryptography.SHA256]::Create()
try{{
    $hashed=$sha.ComputeHash($bytes)
    $actual=[BitConverter]::ToString($hashed).Replace('-','').ToLowerInvariant()
}}finally{{$sha.Dispose()}}
if($actual -ne $v.plan_sha256){{throw 'Validated plan changed before launch'}}
$p=[Text.Encoding]::UTF8.GetString($bytes).TrimStart([char]0xFEFF)|ConvertFrom-Json
$guardArgs=@{{
    OutputRoot=$p.output_root;Label='{quoted_label}';Executable=$p.binary
    CommandArgs=$p.command_args;ExpectedAdditionalPeakBytes=$p.expected_additional_peak_bytes
    MaxOutputBytes=$p.max_output_bytes;ReserveBytes=$p.reserve_bytes
    TimeoutSeconds=$p.timeout_seconds
}}
& '{quoted_guard}' @guardArgs
exit $LASTEXITCODE
"""
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    settings = plan.get("process_environment", {})
    if settings.get("PATH_prepend"):
        environment["PATH"] = (
            settings["PATH_prepend"] + os.pathsep + environment["PATH"]
        )
    if settings.get("CUDA_CACHE_PATH"):
        environment["CUDA_CACHE_PATH"] = settings["CUDA_CACHE_PATH"]
    powershell = (
        Path(os.environ["SystemRoot"])
        / "System32/WindowsPowerShell/v1.0/powershell.exe"
    )
    with (root / f"{label}.launcher.log").open("xb") as launch_log:
        completed = subprocess.run(
            [
                str(powershell),
                "-NoProfile",
                "-NonInteractive",
                "-EncodedCommand",
                base64.b64encode(script.encode("utf-16-le")).decode("ascii"),
            ],
            env=environment,
            stdout=launch_log,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
            check=False,
        )
    if completed.returncode == 0:
        successful_receipt(root / f"{label}.receipt.json")
    logging.info(
        "step %s finished with guard-host exit %d", label, completed.returncode
    )
    return completed.returncode


def main() -> None:
    """Run one trusted local plan after completed successful prerequisites."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--prerequisite", type=Path, action="append", required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(run_step(args.plan, args.label, args.prerequisite))


if __name__ == "__main__":
    main()
