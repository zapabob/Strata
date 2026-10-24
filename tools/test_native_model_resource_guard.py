"""Resource policy and retained-handle termination for native diagnostics."""

import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

import pytest

from native_model_resource_guard import PressurePolicy, run_owned
import native_model_resource_guard as guard


def test_ram_requires_continuous_thirty_seconds() -> None:
    policy = PressurePolicy()
    low = {
        "available_physical_bytes": 256 * 1024**2 - 1,
        "available_commit_bytes": 2 * 1024**3,
    }
    assert policy.observe(low, 0) is None
    assert policy.observe(low, 29.9) is None
    assert policy.observe(dict(low, available_physical_bytes=256 * 1024**2), 30) is None
    assert policy.observe(low, 31) is None
    assert policy.observe(low, 60.9) is None
    assert policy.observe(low, 61) == "physical_memory_pressure"


def test_commit_pressure_is_immediate() -> None:
    policy = PressurePolicy()
    assert (
        policy.observe(
            {
                "available_physical_bytes": 8 * 1024**3,
                "available_commit_bytes": 2 * 1024**3 - 1,
            },
            0,
        )
        == "commit_memory_pressure"
    )


@pytest.mark.parametrize("kind", ["pressure", "telemetry"])
def test_owned_child_abort_preserves_other_child(tmp_path: Path, kind: str) -> None:
    """Exercise real Windows process handles; no name/PID lookup can target peer."""

    def sample() -> dict:
        if kind == "telemetry":
            raise OSError("injected telemetry failure")
        return {"available_physical_bytes": 8 * 1024**3, "available_commit_bytes": 0}

    command = [sys.executable, "-B", "-c", "import time; time.sleep(60)"]
    with subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW) as peer:
        try:
            result = run_owned(
                command,
                tmp_path / "trace.jsonl",
                tmp_path / "result.json",
                timeout_seconds=10,
                sample=sample,
            )
            assert result["status"] == "aborted"
            assert result["reason"] == (
                "telemetry_failure" if kind == "telemetry" else "commit_memory_pressure"
            )
            assert result["child_exit_code"] is not None
            assert result["owned_child_reaped"] is True
            assert peer.poll() is None
            assert json.loads((tmp_path / "result.json").read_text()) == result
            assert (tmp_path / "trace.jsonl").stat().st_size > 0
        finally:
            peer.terminate()
            peer.wait(timeout=5)


@pytest.mark.parametrize("exit_code", [0, 7])
def test_natural_exit_is_separate_from_generation_success(
    tmp_path: Path, exit_code: int
) -> None:
    result = run_owned(
        [sys.executable, "-B", "-c", f"raise SystemExit({exit_code})"],
        tmp_path / "trace.jsonl",
        tmp_path / "result.json",
        timeout_seconds=10,
        sample=lambda: {
            "available_physical_bytes": 8 * 1024**3,
            "available_commit_bytes": 8 * 1024**3,
        },
    )
    assert result["status"] == "exited" and result["child_exit_code"] == exit_code
    assert result["reason"] is None and result["owned_child_reaped"]


def test_timeout_reaps_real_owned_child(tmp_path: Path) -> None:
    result = run_owned(
        [sys.executable, "-B", "-c", "import time; time.sleep(60)"],
        tmp_path / "trace.jsonl",
        tmp_path / "result.json",
        timeout_seconds=1,
        sample=lambda: {
            "available_physical_bytes": 8 * 1024**3,
            "available_commit_bytes": 8 * 1024**3,
        },
    )
    assert result["status"] == "aborted" and result["reason"] == "wall_timeout"
    assert result["child_exit_code"] is not None and result["owned_child_reaped"]


def test_existing_evidence_prevents_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result_path = tmp_path / "result.json"
    result_path.write_text("retained evidence")
    calls = []

    def forbidden(*args: object, **kwargs: object) -> None:
        calls.append(args)
        raise AssertionError("no process may start when evidence already exists")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    with pytest.raises(FileExistsError):
        run_owned(
            [sys.executable], tmp_path / "trace.jsonl", result_path, timeout_seconds=10
        )
    assert calls == [] and result_path.read_text() == "retained evidence"


@pytest.mark.parametrize("value", [-1, True, None, 1.5])
def test_malformed_telemetry_is_not_healthy(value: object) -> None:
    with pytest.raises(ValueError, match="invalid memory telemetry"):
        PressurePolicy().observe(
            {"available_physical_bytes": value, "available_commit_bytes": 8 * 1024**3},
            0,
        )


@pytest.mark.parametrize("failure", ["plan", "binary"])
def test_cli_binding_failure_never_starts_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "binary": sys.executable,
                "binary_sha256": "0" * 64,
                "command_args": [],
                "timeout_seconds": 10,
            }
        )
    )
    calls = []

    def forbidden(*args: object, **kwargs: object) -> None:
        calls.append(args)
        raise AssertionError("binding failure must not run a model")

    monkeypatch.setattr(guard, "run_owned", forbidden)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "native_model_resource_guard",
            "--plan",
            str(plan),
            "--plan-sha256",
            "0" * 64 if failure == "plan" else guard.digest(plan),
            "--trace",
            str(tmp_path / "trace.jsonl"),
            "--result",
            str(tmp_path / "result.json"),
        ],
    )
    with pytest.raises(ValueError, match="SHA-256"):
        guard.main()
    assert calls == []


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig"])
def test_cli_parses_only_the_bytes_it_hashed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, encoding: str
) -> None:
    """A deterministic second-read substitution must never alter parsed arguments."""
    plan_path = tmp_path / "plan.json"
    original = {
        "binary": sys.executable,
        "binary_sha256": guard.digest(Path(sys.executable)),
        "command_args": ["original-plan"],
        "timeout_seconds": 10,
    }
    original_bytes = json.dumps(original).encode(encoding)
    replacement_bytes = json.dumps(
        dict(original, command_args=["replacement-plan"])
    ).encode(encoding)
    plan_path.write_bytes(original_bytes)
    original_open = Path.open
    reads = []
    calls = []

    def substituted_open(path: Path, *args: object, **kwargs: object) -> object:
        if path != plan_path:
            return original_open(path, *args, **kwargs)
        reads.append(path)
        payload = original_bytes if len(reads) == 1 else replacement_bytes
        mode = args[0] if args else kwargs.get("mode", "r")
        if "b" in mode:
            return io.BytesIO(payload)
        return io.StringIO(payload.decode("utf-8-sig"))

    def capture_owned(command: list[str], *args: object, **kwargs: object) -> dict:
        calls.append(command)
        return {"status": "exited", "reason": None, "child_exit_code": 0}

    monkeypatch.setattr(Path, "open", substituted_open)
    monkeypatch.setattr(guard, "run_owned", capture_owned)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "native_model_resource_guard",
            "--plan",
            str(plan_path),
            "--plan-sha256",
            hashlib.sha256(original_bytes).hexdigest(),
            "--trace",
            str(tmp_path / "trace"),
            "--result",
            str(tmp_path / "result"),
        ],
    )
    with pytest.raises(SystemExit) as stopped:
        guard.main()
    assert stopped.value.code == 0
    assert calls == [[sys.executable, "original-plan"]]
    assert len(reads) == 1
