"""Opt-in pilot contract and CPU fixture consumer. Real engine launch is disabled.

No serve imports, GPU discovery, task/lease operations or external PID controls.
Only the fixed stdlib cpu_child.py can be executed by this revision.
"""
from dataclasses import asdict, dataclass
import ctypes as C
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import shutil

MIB = 1024**2


@dataclass(frozen=True)
class Budget:
    timeout_s: float = 4.0
    job_commit_bytes: int = 192 * MIB
    output_bytes: int = MIB
    max_processes: int = 4
    min_available_ram: int = 512 * MIB
    min_commit_headroom: int = 768 * MIB
    min_H_free: int = 1024 * MIB

    def validate(self):
        if (type(self.timeout_s) not in (int, float) or not math.isfinite(self.timeout_s)
                or not 0 < self.timeout_s <= 60):
            raise ValueError("CPU timeout must be finite and in (0,60]")
        ranges = {"job_commit_bytes": (64*MIB, 256*MIB), "output_bytes": (256, MIB),
                  "max_processes": (1, 4), "min_available_ram": (512*MIB, 64*1024*MIB),
                  "min_commit_headroom": (768*MIB, 128*1024*MIB),
                  "min_H_free": (1024*MIB, 1024*1024*MIB)}
        for name, (low, high) in ranges.items():
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError("invalid CPU resource budget: " + name)


def h_path(value):
    if not isinstance(value, (str, Path)):
        raise ValueError("H absolute path required")
    path = Path(value)
    if not path.is_absolute() or path.drive.upper() != "H:":
        raise ValueError("H absolute path required")
    resolved = path.resolve()
    if resolved.drive.upper() != "H:":
        raise ValueError("resolved path leaves H drive")
    if ":" in str(resolved)[2:]:
        raise ValueError("alternate data streams forbidden")
    return resolved


def contract(cfg, run_root, budget, *, series="normal"):
    """Validate a materialized minimal config, without importing dynamic launch helpers.

    The caller must supply resolved args, not a production config with user_args or
    component references. This is a proposed launch identity, never runtime proof.
    """
    budget.validate()
    if not isinstance(cfg, dict) or set(cfg) != {"args", "env", "exe"}:
        raise ValueError("only explicit args/env/exe are accepted; materialize dynamic settings first")
    exe = h_path(cfg["exe"])
    if not exe.is_file() or exe.suffix.lower() != ".exe":
        raise ValueError("existing absolute verification exe required")
    output = h_path(run_root)
    checkout = h_path(Path.cwd())
    if not (checkout / ".git").exists() or not output.is_relative_to(checkout / "_scratch/perf131k/b2-fixtures"):
        raise ValueError("run directory must be in the H checkout's dedicated B2 fixture area")
    if output.exists():
        raise ValueError("fresh exclusive run directory required")
    if series not in ("normal", "diagnostic"):
        raise ValueError("normal or diagnostic series required")
    args = cfg["args"]
    if (not isinstance(args, list) or len(args) > 128
            or not all(type(v) is str and len(v) <= 4096 and not any(ord(c) < 32 for c in v) for v in args)):
        raise ValueError("explicit string argument array required")
    flags = {"--serve", "--vram-elastic"}
    pairs = {"--pack", "--native", "--ple-gguf", "--expert-profile", "--expert-cache",
             "--prefill", "--spec", "--spec-min-p", "--mtp", "--max-context", "--kv",
             "--resident-budget-gib", "--vram-reserve-mib", "--suffix-draft", "--lookup-chain",
             "--pipeline-windows"}
    values, i = {}, 0
    while i < len(args):
        flag = args[i]
        if flag in values or flag not in flags | pairs:
            raise ValueError("unknown or repeated native option")
        if flag in flags:
            values[flag], i = True, i + 1
        else:
            if i + 1 >= len(args) or args[i + 1].startswith("--"):
                raise ValueError("native option missing value")
            values[flag], i = args[i + 1], i + 2
    required = {"--pack", "--native", "--ple-gguf", "--expert-profile", "--expert-cache",
                "--prefill", "--spec", "--max-context", "--kv", "--resident-budget-gib",
                "--vram-reserve-mib", "--serve", "--vram-elastic"}
    if not required <= values.keys() or values["--max-context"] != "131072" or values["--kv"] != "k8v4":
        raise ValueError("capacity131072 and unchanged explicit baseline required")
    for key in ("--pack", "--native", "--ple-gguf", "--mtp"):
        if key in values:
            h_path(values[key])
    profile = Path(values["--expert-profile"])
    if not profile.is_absolute() or not profile.is_file() or ":" in str(profile)[2:]:
        raise ValueError("existing absolute read-only expert profile required")
    if values["--resident-budget-gib"] != "4" or values["--vram-reserve-mib"] != "2048":
        raise ValueError("resident/reserve baseline change requires another contract")
    if values["--expert-cache"] != "auto" or values["--prefill"] != "auto":
        raise ValueError("preserve baseline automatic policies and record their runtime resolution")
    if values.get("--pipeline-windows", "0") != "0":
        raise ValueError("single CUDA pipeline contract required")
    if values.get("--spec-min-p", "0.5") != "0.5":
        raise ValueError("spec admission baseline mismatch")
    if series == "normal":
        valid = (values["--spec"] == "4" and "--mtp" in values
                 and values.get("--suffix-draft", "3") == "3" and values.get("--lookup-chain", "0") == "0")
    else:
        valid = (values["--spec"] == "2" and "--mtp" not in values
                 and values.get("--suffix-draft") == "0" and values.get("--lookup-chain") == "0")
    if not valid:
        raise ValueError("draft settings do not match selected series")
    expected_env = {"STRATA_RESIDENT_PIN": "0", "STRATA_ADAPT_OVERLAP": "1", "STRATA_PIN_BY_NEED": "1"}
    if cfg["env"] != expected_env:
        raise ValueError("explicit nonsecret baseline env required")
    return {"schema": "perf131k.pilot-contract.v1", "series": series,
            "native_exe": str(exe), "native_args": list(args), "capacity": 131072,
            "output_reserve": 256, "run_root": str(output), "budget": asdict(budget),
            "server_env": {**expected_env, "STRATA_KEEP_LEFTOVERS": "1"},
            "model_launch_enabled": False, "GPU_performance_quality": "NOT_RUN",
            "runtime_resolution": None, "legacy_provenance": "UNRESOLVED",
            "native_binary_hash_verified": False, "attention_view_count_verified": False}


class Memory(C.Structure):
    _fields_ = [("length", C.c_ulong), ("load", C.c_ulong)] + [
        (name, C.c_ulonglong) for name in ("total_phys", "avail_phys", "total_page", "avail_page",
                                         "total_virt", "avail_virt", "avail_ext")]


def system_resources(root):
    """OS memory/commit and H free bytes only; never initialize a GPU runtime."""
    kernel = C.WinDLL("kernel32", use_last_error=True)
    kernel.GlobalMemoryStatusEx.argtypes = [C.POINTER(Memory)]
    kernel.GlobalMemoryStatusEx.restype = C.c_int
    memory = Memory()
    memory.length = C.sizeof(memory)
    if not kernel.GlobalMemoryStatusEx(C.byref(memory)):
        raise OSError("system resource telemetry unavailable")
    return {"available_ram": memory.avail_phys, "commit_headroom": memory.avail_page,
            "H_free": shutil.disk_usage(root).free}


def run_cpu_fixture(cfg, run_root, budget, scenario="ok", *, series="normal"):
    """Actual B2 consumer: validate, preflight, private atomic Job, bounded receipt.

    Engine paths/args are recorded as a proposal only. This function has no route
    to execute those args, import the server or signal an existing process.
    """
    if scenario not in {"ok", "sleep", "flood", "grandchild", "tree_hold", "memory"}:
        raise ValueError("fixed CPU fixture scenario required")
    plan = contract(cfg, run_root, budget, series=series)
    root = h_path(run_root)
    root.mkdir(parents=True, exist_ok=False)
    def write(name, value):
        with (root / name).open("x", encoding="utf-8") as out:
            json.dump(value, out, indent=2, allow_nan=False)
    write("contract.json", plan)
    result = {"status": "PREFLIGHT_BLOCKED", "exit_code": 77, "owned_root_pid": None,
              "contained_before_resume": False, "termination_confirmed": True,
              "job_active_after": 0, "GPU_time_ns": None, "pinned_bytes": None,
              "model_launched": False, "scenario": scenario}
    result["resource_source"] = "GlobalMemoryStatusEx avail_phys/avail_page (process-aware available commit), H disk_usage; not total system commit/RSS/pinned/VRAM"
    try:
        resources = system_resources(root)
        result["preflight"] = resources
        if (resources["available_ram"] < budget.min_available_ram
                or resources["commit_headroom"] < budget.min_commit_headroom
                or resources["H_free"] < budget.min_H_free):
            result["reason"] = "resource admission failed"
        else:
            from tools.perf131k import windows_job
            child = Path(__file__).resolve().with_name("cpu_child.py")
            with child.open("rb") as source:
                result["fixture_sha256"] = hashlib.file_digest(source, "sha256").hexdigest()
            # Do not inherit credentials, CUDA knobs, Python hooks or component state.
            env = {k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ}
            env.update(plan["server_env"], TEMP=str(root), TMP=str(root),
                       PYTHONDONTWRITEBYTECODE="1", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
            command = [sys.executable, "-I", "-B", str(child), scenario]
            result["fixture_command"] = command
            result.update(windows_job.run_owned(command, root, env, root / "raw.bin", budget, system_resources))
            with child.open("rb") as source:
                after = hashlib.file_digest(source, "sha256").hexdigest()
            if after != result["fixture_sha256"]:
                result.update(status="SOURCE_CHANGED", exit_code=78)
    except Exception as error:
        # A failure after a successful child exit is still a failed verification.
        # Keep known Job cleanup/identity counters instead of resetting them.
        result["error_type"] = type(error).__name__  # Never log exception values/credentials.
        if result["status"] == "FINISHED":
            result.update(status="SOURCE_VERIFICATION_FAILED", exit_code=78)
    result["output_complete"] = result["status"] == "FINISHED" and result.get("job_total_processes") == 1
    write("receipt.json", result)
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("run_root", type=Path)
    parser.add_argument("--cpu-fixture", required=True, choices=("ok", "sleep", "flood", "grandchild", "tree_hold", "memory"))
    parser.add_argument("--series", choices=("normal", "diagnostic"), default="normal")
    args = parser.parse_args()
    path = h_path(args.config)
    with path.open("rb") as source:
        blob = source.read(65537)
    if len(blob) > 65536:
        raise ValueError("bounded config required")
    def unique_object(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError("duplicate config field")
            obj[key] = value
        return obj
    cfg = json.loads(blob.decode("utf-8-sig"), object_pairs_hook=unique_object)
    result = run_cpu_fixture(cfg, args.run_root, Budget(), args.cpu_fixture, series=args.series)
    print(json.dumps({key: result.get(key) for key in ("status", "exit_code", "job_active_after")}))
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
