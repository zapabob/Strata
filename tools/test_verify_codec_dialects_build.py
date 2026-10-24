"""Small real Windows PowerShell 5.1 process-guard integration fixtures.

Run with pytest. Evidence is intentionally retained, under a unique test run.
"""

import base64
import ctypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

import pytest

ROOT = Path("H:/Strata/build/task5a-guard-20261024")
RUNNER = Path(__file__).with_name("verify_codec_dialects_build.ps1")
PS = Path(os.environ.get("WINDIR", "C:/Windows")) / (
    "System32/WindowsPowerShell/v1.0/powershell.exe"
)
GIB = 1024**3
pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows integration")


def ps_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


@pytest.fixture(scope="module")
def batch() -> Path:
    return ROOT / ("suite-" + uuid.uuid4().hex)


@pytest.fixture
def evidence(batch: Path, request: pytest.FixtureRequest) -> Path:
    assert shutil.disk_usage("H:/").free >= 10 * GIB + 128 * 1024**2
    directory = batch / ("run-" + uuid.uuid4().hex)
    directory.mkdir(parents=True)
    request.node.user_properties.append(("evidence_root", str(directory)))
    return directory


def command(root: Path, label: str, args: list[str], **options: int) -> list[str]:
    code = (
        "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue'; "
        f"& {ps_literal(str(RUNNER))} -OutputRoot {ps_literal(str(root))} "
        f"-Label {ps_literal(label)} -Executable {ps_literal(sys.executable)} "
        "-CommandArgs @(" + ",".join(ps_literal(a) for a in args) + ") "
        "-ExpectedAdditionalPeakBytes 1048576 -MaxOutputBytes 262144 "
        "-TimeoutSeconds 15 "
        + " ".join(f"-{key} {value}" for key, value in options.items())
        + "; exit $LASTEXITCODE"
    )
    return [
        str(PS),
        "-NoProfile",
        "-NonInteractive",
        "-EncodedCommand",
        base64.b64encode(code.encode("utf-16le")).decode("ascii"),
    ]


def invoke(
    root: Path, label: str, args: list[str], **options: int
) -> subprocess.CompletedProcess:
    return subprocess.run(
        command(root, label, args, **options),
        capture_output=True,
        text=True,
        timeout=40,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def receipt(root: Path, label: str) -> dict:
    return json.loads(
        (root / (label + ".receipt.json")).read_text(encoding="utf-8-sig")
    )


def test_actual_windows_powershell_51(evidence: Path) -> None:
    result = subprocess.run(
        [str(PS), "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"],
        capture_output=True,
        text=True,
        check=True,
    )
    (evidence / "powershell-version.txt").write_text(result.stdout)
    assert result.stdout.startswith("5.1.")


@pytest.mark.parametrize("code", [0, 7, 23, 259, -1])
def test_fast_exit_exact_status(evidence: Path, code: int) -> None:
    label = f"exit-{code}"
    result = invoke(
        evidence, label, ["-B", "-c", f"import sys; print('partial'); sys.exit({code})"]
    )
    assert result.returncode == code & 0xFFFFFFFF, result.stderr
    record = receipt(evidence, label)
    assert record["child_exit_code"] == code & 0xFFFFFFFF
    assert record["guard_reason"] is None
    assert record["contained_before_resume"] is True
    assert record["active_processes_after_cleanup"] == 0
    assert "partial" in (evidence / (label + ".stdout.log")).read_text()


def test_argv_roundtrip(evidence: Path) -> None:
    arguments = [
        "",
        "two words",
        "C:\\trailing space\\",
        'a"b',
        "two\\\\",
        "&$;[]日本語",
    ]
    result = invoke(
        evidence,
        "argv",
        ["-B", "-c", "import json,sys; print(json.dumps(sys.argv[1:]))", *arguments],
    )
    assert result.returncode == 0, result.stderr
    assert json.loads((evidence / "argv.stdout.log").read_text()) == arguments


def test_no_arguments_and_closed_stdin(evidence: Path) -> None:
    result = invoke(evidence, "no-args", [])
    assert result.returncode == 0, result.stderr
    assert receipt(evidence, "no-args")["child_exit_code"] == 0


def test_literal_output_path_with_spaces_and_brackets(evidence: Path) -> None:
    target = evidence / "space and [brackets]"
    result = invoke(
        target,
        "literal",
        ["-B", "-c", "import sys; print('stdout'); print('stderr', file=sys.stderr)"],
    )
    assert result.returncode == 0, result.stderr
    assert (target / "literal.stdout.log").read_text().strip() == "stdout"
    assert (target / "literal.stderr.log").read_text().strip() == "stderr"


def test_create_process_failure_is_recorded(evidence: Path) -> None:
    # Existing .exe suffix, invalid executable bytes: real CreateProcess failure.
    invalid = evidence / "invalid.exe"
    invalid.write_bytes(b"not an executable")
    cmd = command(evidence, "invalid-exe", [])
    code = (
        base64.b64decode(cmd[-1])
        .decode("utf-16le")
        .replace(ps_literal(sys.executable), ps_literal(str(invalid)))
    )
    cmd[-1] = base64.b64encode(code.encode("utf-16le")).decode("ascii")
    result = subprocess.run(cmd, capture_output=True, timeout=40)
    assert result.returncode != 0
    record = receipt(evidence, "invalid-exe")
    assert record["guard_reason"] == "runner_error"
    assert record["child_exit_code"] is None
    assert record["contained_before_resume"] is False


def test_unrelated_inheritable_handle_not_forwarded(evidence: Path) -> None:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateEventW.restype = ctypes.c_void_p
    kernel.SetHandleInformation.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
    ]
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    event = kernel.CreateEventW(None, True, False, None)
    assert event and kernel.SetHandleInformation(event, 1, 1)
    try:
        cmd = command(
            evidence,
            "inheritance",
            [
                "-B",
                "-c",
                f"import ctypes; ctypes.windll.kernel32.SetEvent(ctypes.c_void_p({event}))",
            ],
        )
        code = base64.b64decode(cmd[-1]).decode("utf-16le")
        # Verify the test handle truly reached the host, before testing exclusion
        # from the helper's child handle list. The SafeWaitHandle does not own it.
        probe = (
            "$probe = [Threading.EventWaitHandle]::new($false, "
            "[Threading.EventResetMode]::ManualReset); "
            "$probe.SafeWaitHandle = [Microsoft.Win32.SafeHandles.SafeWaitHandle]::new("
            f"[IntPtr]{event}, $false); "
            "if ($probe.WaitOne(0)) { throw 'Unexpected signalled event' }; "
        )
        code = code.replace("& ", probe + "& ", 1)
        cmd[-1] = base64.b64encode(code.encode("utf-16le")).decode("ascii")
        startup = subprocess.STARTUPINFO()
        startup.lpAttributeList = {"handle_list": [event]}
        result = subprocess.run(
            cmd,
            startupinfo=startup,
            capture_output=True,
            timeout=40,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        assert result.returncode == 0, result.stderr
        assert kernel.WaitForSingleObject(event, 0) == 258
    finally:
        kernel.CloseHandle(event)


def test_impossible_reserve_prevents_start(evidence: Path) -> None:
    marker = evidence / "must-not-run"
    result = invoke(
        evidence,
        "reserve",
        ["-B", "-c", f"open({str(marker)!r},'w').close()"],
        ReserveBytes=10**15,
    )
    assert result.returncode != 0
    assert not marker.exists()
    record = receipt(evidence, "reserve")
    assert record["guard_reason"] == "start_capacity"
    assert record["child_exit_code"] is None


def test_expected_peak_checked_separately(evidence: Path) -> None:
    cmd = command(evidence, "peak", ["-B", "-c", "raise SystemExit(0)"])
    code = (
        base64.b64decode(cmd[-1])
        .decode("utf-16le")
        .replace(
            "-ExpectedAdditionalPeakBytes 1048576",
            "-ExpectedAdditionalPeakBytes 1000000000000000",
        )
    )
    cmd[-1] = base64.b64encode(code.encode("utf-16le")).decode("ascii")
    result = subprocess.run(cmd, capture_output=True, timeout=40)
    assert result.returncode != 0
    assert receipt(evidence, "peak")["guard_reason"] == "start_capacity"


def test_job_assignment_failure_never_runs_child(evidence: Path) -> None:
    """A real nested-job active-process limit rejects the suspended creation."""

    class BasicLimits(ctypes.Structure):
        _fields_ = [
            ("process_time", ctypes.c_int64),
            ("job_time", ctypes.c_int64),
            ("flags", ctypes.c_uint32),
            ("minimum", ctypes.c_size_t),
            ("maximum", ctypes.c_size_t),
            ("active_limit", ctypes.c_uint32),
            ("affinity", ctypes.c_size_t),
            ("priority", ctypes.c_uint32),
            ("scheduling", ctypes.c_uint32),
        ]

    class ExtendedLimits(ctypes.Structure):
        _fields_ = [
            ("basic", BasicLimits),
            ("io", ctypes.c_uint64 * 6),
            ("memory", ctypes.c_size_t * 4),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.restype = ctypes.c_void_p
    kernel.SetInformationJobObject.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_uint32,
    ]
    kernel.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    job = kernel.CreateJobObjectW(None, None)
    assert job
    wrapper = None
    try:
        limits = ExtendedLimits()
        limits.basic.flags = (
            0x2008  # Kill-on-close + active-process limit, no breakaway.
        )
        limits.basic.active_limit = 1
        assert kernel.SetInformationJobObject(
            job, 9, ctypes.byref(limits), ctypes.sizeof(limits)
        )
        ready, ack, marker = (
            evidence / name for name in ["host-ready", "host-ack", "uncontained-child"]
        )
        cmd = command(
            evidence, "job-reject", ["-B", "-c", f"open({str(marker)!r},'w').close()"]
        )
        code = base64.b64decode(cmd[-1]).decode("utf-16le")
        preload = (
            f"Add-Type -Path {ps_literal(str(RUNNER.with_name('verify_bounded_process.cs')))}; "
            f"[IO.File]::WriteAllText({ps_literal(str(ready))}, 'ready'); "
            f"while (-not [IO.File]::Exists({ps_literal(str(ack))})) "
            "{ Start-Sleep -Milliseconds 20 }; "
        )
        code = code.replace("& ", preload + "& ", 1)
        cmd[-1] = base64.b64encode(code.encode("utf-16le")).decode("ascii")
        wrapper = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        deadline = time.monotonic() + 15
        while (
            not ready.exists()
            and wrapper.poll() is None
            and time.monotonic() < deadline
        ):
            time.sleep(0.02)
        assert ready.exists()
        assert kernel.AssignProcessToJobObject(job, int(wrapper._handle))
        ack.touch()
        wrapper.communicate(timeout=20)
        assert wrapper.returncode != 0
        record = receipt(evidence, "job-reject")
        assert record["guard_reason"] == "runner_error"
        assert "Create suspended child" in record["error"]
        assert record["contained_before_resume"] is False
        assert record["child_exit_code"] is None
        assert not marker.exists()
    finally:
        if wrapper is not None and wrapper.poll() is None:
            wrapper.kill()
            wrapper.wait(timeout=5)
        kernel.CloseHandle(job)


def test_receipts_cannot_be_overwritten(evidence: Path) -> None:
    assert invoke(evidence, "keep", ["-B", "-c", "print('original')"]).returncode == 0
    before = {
        str(p.relative_to(evidence)): p.read_bytes()
        for p in evidence.rglob("*")
        if p.is_file()
    }
    assert invoke(evidence, "keep", ["-B", "-c", "print('changed')"]).returncode != 0
    assert before == {
        str(p.relative_to(evidence)): p.read_bytes()
        for p in evidence.rglob("*")
        if p.is_file()
    }


@pytest.mark.parametrize(
    "suffix,label",
    [("/../escape", "invalid"), ("", "../escape"), ("", "CON"), ("", "a.b")],
)
def test_rejects_invalid_paths(evidence: Path, suffix: str, label: str) -> None:
    result = invoke(
        Path(str(evidence) + suffix), label, ["-B", "-c", "raise SystemExit(0)"]
    )
    assert result.returncode != 0


def test_reparse_root_rejected(evidence: Path) -> None:
    target = evidence / "junction-target"
    target.mkdir()
    junction = evidence / "junction"
    script = (
        f"New-Item -ItemType Junction -Path {ps_literal(str(junction))} "
        f"-Target {ps_literal(str(target))} | Out-Null"
    )
    subprocess.run(
        [str(PS), "-NoProfile", "-Command", script], check=True, capture_output=True
    )
    result = invoke(junction, "reject", ["-B", "-c", "print('bad')"])
    assert result.returncode != 0
    assert list(target.iterdir()) == []


@pytest.mark.parametrize(
    "mode", ["early", "flood", "files", "timeout", "abort", "disk"]
)
def test_descendant_cleanup_and_unrelated_survival(evidence: Path, mode: str) -> None:
    marker = evidence / (mode + "-child.json")
    sentinel = subprocess.Popen(
        [sys.executable, "-B", "-c", "import time; time.sleep(45)"],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    child_handle = None
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    args = ["-B", str(Path(__file__).resolve()), "--fixture", mode, str(marker)]
    cmd = command(evidence, mode, args)
    if mode == "disk":
        code = base64.b64decode(cmd[-1]).decode("utf-16le")
        code = (
            "$reserve = ([IO.DriveInfo]::new('H:\\')).AvailableFreeSpace - 4MB; "
            + code.replace(
                "; exit $LASTEXITCODE", " -ReserveBytes $reserve; exit $LASTEXITCODE"
            )
        )
        cmd[-1] = base64.b64encode(code.encode("utf-16le")).decode("ascii")
    if mode == "timeout":
        code = (
            base64.b64decode(cmd[-1])
            .decode("utf-16le")
            .replace("-TimeoutSeconds 15", "-TimeoutSeconds 3")
        )
        cmd[-1] = base64.b64encode(code.encode("utf-16le")).decode("ascii")
    wrapper = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    try:
        deadline = time.monotonic() + 20
        while (
            not marker.exists()
            and wrapper.poll() is None
            and time.monotonic() < deadline
        ):
            time.sleep(0.02)
        assert marker.exists(), wrapper.communicate(timeout=5)
        child_pid = int(marker.read_text())
        child_handle = kernel.OpenProcess(0x100001, False, child_pid)
        assert child_handle and kernel.WaitForSingleObject(child_handle, 0) == 258
        (evidence / (mode + "-ack")).touch()
        if mode == "abort":
            wrapper.kill()  # Popen retains the exact process handle, never a later PID lookup.
        stdout, stderr = wrapper.communicate(timeout=25)
        assert kernel.WaitForSingleObject(child_handle, 5000) == 0
        assert sentinel.poll() is None
        if mode != "abort":
            record = receipt(evidence, mode)
            assert record["active_processes_after_cleanup"] == 0
            if mode == "early":
                assert wrapper.returncode == 0, stderr
                assert record["child_exit_code"] == 0
            else:
                assert wrapper.returncode != 0
                assert (
                    record["guard_reason"]
                    == {
                        "flood": "output_limit",
                        "files": "output_limit",
                        "timeout": "timeout",
                        "disk": "disk_reserve",
                    }[mode]
                )
                assert (evidence / (mode + ".stdout.log")).stat().st_size > 0
                assert record["free_bytes"] > 10 * GIB
                if mode == "flood":
                    assert record["captured_bytes"] <= 262144
        else:
            assert receipt(evidence, mode)["state"] == "starting"
    finally:
        if wrapper.poll() is None:
            wrapper.kill()
            wrapper.wait(timeout=5)
        if child_handle:
            if kernel.WaitForSingleObject(child_handle, 0) != 0:
                # Only the retained handle of this exact fixture child; regression cleanup.
                kernel.TerminateProcess(child_handle, 126)
                assert kernel.WaitForSingleObject(child_handle, 5000) == 0
            kernel.CloseHandle(child_handle)
        sentinel.terminate()
        sentinel.wait(timeout=5)


def fixture(mode: str, marker: Path) -> None:
    """Benign finite descendants; no unrelated process discovery or termination."""
    child = subprocess.Popen(
        [sys.executable, "-B", "-c", "import time; time.sleep(30)"],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    marker.write_text(str(child.pid))
    deadline = time.monotonic() + 10
    while not marker.with_name(mode + "-ack").exists() and time.monotonic() < deadline:
        time.sleep(0.02)
    print("partial evidence", flush=True)
    if mode == "early":
        return
    if mode == "flood":
        for _ in range(512):
            os.write(sys.stdout.fileno(), b"x" * 4096)
    if mode == "disk":
        # Deliberately exceed the declared peak outside the evidence root, with
        # only 8 MiB. The real disk remains comfortably above the 10 GiB floor.
        with marker.parent.with_suffix(".capacity-fixture").open("xb") as stream:
            stream.write(b"x" * (8 * 1024**2))
            stream.flush()
            os.fsync(stream.fileno())
    if mode == "files":
        marker.with_suffix(".output-fixture").write_bytes(b"x" * 1048576)
    time.sleep(25)


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "--fixture":
    fixture(sys.argv[2], Path(sys.argv[3]))
