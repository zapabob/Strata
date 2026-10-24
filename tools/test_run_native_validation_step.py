"""A prerequisite failure must prevent even attempting the guarded child."""

import json
from pathlib import Path
import subprocess
import sys
import uuid
from datetime import datetime, timezone

import pytest

from run_native_validation_step import run_step
import run_native_validation_step as launcher


@pytest.mark.parametrize(
    "change",
    [
        {"state": "starting"},
        {"child_exit_code": 2},
        {"guard_reason": "disk_reserve"},
        {"active_processes_after_cleanup": 1},
        {"contained_before_resume": False},
        {"child_exit_code": False},
        {"error": "failed preflight"},
    ],
)
def test_failed_or_unfinished_prerequisite_never_launches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: dict
) -> None:
    receipt = {
        "schema": 1,
        "state": "finished",
        "child_exit_code": 0,
        "guard_reason": None,
        "error": None,
        "contained_before_resume": True,
        "active_processes_after_cleanup": 0,
    }
    receipt.update(change)
    prior = tmp_path / "prior.receipt.json"
    prior.write_text(json.dumps(receipt))
    calls = []

    def forbidden(*args: object, **kwargs: object) -> None:
        calls.append((args, kwargs))
        raise AssertionError("child must never launch")

    monkeypatch.setattr(subprocess, "run", forbidden)
    with pytest.raises(ValueError, match="prerequisite"):
        run_step(tmp_path / "absent-plan.json", "blocked", [prior])
    assert calls == []


@pytest.mark.parametrize("failure", ["binary", "resources", "gpu_timeout"])
def test_failed_in_process_preflight_never_launches_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    root = Path("H:/Strata/build/task5a-sequential-tests-20261024")
    root.mkdir(exist_ok=True)
    prior = tmp_path / "prior.json"
    prior.write_text(
        json.dumps(
            {
                "schema": 1,
                "state": "finished",
                "child_exit_code": 0,
                "guard_reason": None,
                "error": None,
                "contained_before_resume": True,
                "active_processes_after_cleanup": 0,
            }
        )
    )
    model = tmp_path / "small-source.bin"
    model.write_bytes(b"test source")
    stat = model.stat()
    stamp = datetime.fromtimestamp(stat.st_mtime_ns // 10**9, timezone.utc)
    mtime = stamp.strftime("%Y-%m-%dT%H:%M:%S") + f".{stat.st_mtime_ns % 10**9:09d}Z"
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps(
            {
                "models": [
                    {
                        "path": str(model),
                        "bytes": stat.st_size,
                        "matches": True,
                        "metadata_unchanged": True,
                        "sha256": launcher.digest(model),
                        "expected_sha256": launcher.digest(model),
                        "last_write_utc": mtime,
                    }
                ]
            }
        )
    )
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "output_root": str(root),
                "binary": sys.executable,
                "binary_sha256": (
                    "wrong"
                    if failure == "binary"
                    else launcher.digest(Path(sys.executable))
                ),
                "command_args": ["-B", "-c", "raise SystemExit(0)"],
                "timeout_seconds": 30,
                "expected_additional_peak_bytes": 16 * 1024**2,
                "max_output_bytes": 8 * 1024**2,
                "reserve_bytes": 10 * 1024**3,
                "model_source_receipt": str(source),
            }
        )
    )
    calls = []

    def forbidden(*args: object, **kwargs: object) -> None:
        calls.append((args, kwargs))
        raise AssertionError("guard must never launch")

    def failed_resources() -> dict:
        raise ValueError("injected memory preflight failure")

    monkeypatch.setattr(subprocess, "run", forbidden)
    if failure == "gpu_timeout":

        def stalled_gpu(*args: object, **kwargs: object) -> str:
            assert kwargs.get("timeout") == 10
            raise subprocess.TimeoutExpired("nvidia-smi", 10)

        monkeypatch.setattr(subprocess, "check_output", stalled_gpu)
    else:
        monkeypatch.setattr(launcher, "runtime_resources", failed_resources)
    label = "failed-" + uuid.uuid4().hex
    with pytest.raises(ValueError, match="SHA-256|preflight"):
        run_step(plan, label, [prior])
    receipt = json.loads((root / f"{label}.preflight.json").read_text())
    assert receipt["state"] == "finished" and receipt["exit_code"] == 1
    assert receipt["validated"] is False
    assert calls == []
