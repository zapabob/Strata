"""Run one native diagnostic inside the reviewed outer Windows job guard.

This does not contain descendants. The outer verify_codec_dialects_build.ps1
job owns those. Only this harness's retained Popen handle may be terminated.
An exit of zero is process evidence, not a generation or performance verdict.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
import ctypes
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import subprocess
import time

from run_native_validation_step import digest


def available_memory() -> dict[str, int]:
    """Read Windows physical RAM and commit headroom without another process."""

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
    return {
        "available_physical_bytes": memory.free_physical,
        "available_commit_bytes": memory.free_commit,
    }


class PressurePolicy:
    """Require continuous low RAM; inadequate commit stops immediately."""

    def __init__(self) -> None:
        self.low_since: float | None = None

    def observe(self, sample: dict[str, int], now: float) -> str | None:
        """Return a typed abort reason, or None when thresholds admit work."""
        for name in ("available_physical_bytes", "available_commit_bytes"):
            if type(sample.get(name)) is not int or sample[name] < 0:
                raise ValueError(f"invalid memory telemetry: {name}")
        if sample["available_commit_bytes"] < 2 * 1024**3:
            return "commit_memory_pressure"
        if sample["available_physical_bytes"] >= 256 * 1024**2:
            self.low_since = None
        elif self.low_since is None:
            self.low_since = now
        elif now - self.low_since >= 30:
            return "physical_memory_pressure"
        return None


def run_owned(
    command: list[str],
    trace_path: Path,
    result_path: Path,
    *,
    timeout_seconds: int,
    sample: Callable[[], dict[str, int]] = available_memory,
) -> dict:
    """Observe one owned process; preserve trace/result on failure and reap it."""
    if not command or type(timeout_seconds) is not int or timeout_seconds <= 0:
        raise ValueError("explicit command and positive timeout required")
    policy = PressurePolicy()
    result = {
        "schema": "strata-native-resource-run-v1",
        "status": "starting",
        "reason": None,
        "child_exit_code": None,
        "owned_child_reaped": False,
        "command": command,
        "started_utc": datetime.now(timezone.utc).isoformat(),
    }
    process = None
    # Reserve BOTH artifacts before a process can start. Never overwrite evidence.
    with trace_path.open("x", encoding="utf-8") as trace, result_path.open(
        "x", encoding="utf-8"
    ) as receipt:
        receipt.write(json.dumps(result) + "\n")
        receipt.flush()
        start = time.monotonic()
        try:
            process = subprocess.Popen(
                command, creationflags=subprocess.CREATE_NO_WINDOW
            )
            result["owned_pid"] = (
                process.pid
            )  # Diagnostic only, never used to terminate.
            while process.poll() is None:
                now = time.monotonic()
                entry = {
                    "elapsed_seconds": now - start,
                    "utc": datetime.now(timezone.utc).isoformat(),
                }
                try:
                    memory = sample()
                    entry.update(memory)
                    reason = policy.observe(memory, now)
                except Exception as error:
                    reason = "telemetry_failure"
                    entry["error"] = str(error)
                if reason is None and now - start >= timeout_seconds:
                    reason = "wall_timeout"
                entry["abort_reason"] = reason
                trace.write(json.dumps(entry) + "\n")
                trace.flush()
                if reason:
                    result.update(status="aborted", reason=reason)
                    break
                # Bounded wait also promptly reaps natural completion.
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
            if result["status"] == "starting":
                result["status"] = "exited"
        except BaseException as error:
            result.update(status="failed", reason="harness_failure", error=str(error))
            raise
        finally:
            try:
                if process is not None:
                    if process.poll() is None:
                        # Windows Popen retains the kernel handle acquired at creation;
                        # it does not reopen an arbitrary PID that could have been reused.
                        process.terminate()
                    result["child_exit_code"] = process.wait(timeout=5)
                    result["owned_child_reaped"] = True
            except Exception as error:
                result.update(
                    status="failed", reason="owned_cleanup_failed", error=str(error)
                )
            result["finished_utc"] = datetime.now(timezone.utc).isoformat()
            receipt.seek(0)
            receipt.write(json.dumps(result, indent=2) + "\n")
            receipt.truncate()
            receipt.flush()
    return result


def main() -> None:
    """Validate explicit executable/plan bytes before launching the owned model."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if digest(args.plan) != args.plan_sha256:
        raise ValueError("model plan SHA-256 differs from expected value")
    plan = json.loads(args.plan.read_text(encoding="utf-8-sig"))
    binary = Path(plan["binary"])
    if not binary.is_absolute() or digest(binary) != plan["binary_sha256"]:
        raise ValueError("model executable SHA-256 differs from expected value")
    if not isinstance(plan["command_args"], list) or any(
        not isinstance(value, str) for value in plan["command_args"]
    ):
        raise ValueError("model arguments must be explicit strings")
    result = run_owned(
        [str(binary), *plan["command_args"]],
        args.trace,
        args.result,
        timeout_seconds=plan["timeout_seconds"],
    )
    logging.info(
        "native child status=%s reason=%s exit=%s",
        result["status"],
        result["reason"],
        result["child_exit_code"],
    )
    raise SystemExit(result["child_exit_code"] if result["status"] == "exited" else 125)


if __name__ == "__main__":
    main()
