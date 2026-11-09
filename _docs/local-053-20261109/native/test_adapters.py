"""Small non-launching tests for fail-closed gates and retained qualification semantics."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import adapter
import common
import model
import phases
import retry_prepare


def good_run() -> dict:
    return {"status": "FINISHED", "native_exit_code": 0, "contained_before_resume": True,
            "termination_confirmed": True, "job_active_after": 0, "observed_dropped_bytes": 0}


@pytest.mark.parametrize("key,value", [("status", "TIMEOUT"), ("status", "RESOURCE_PRESSURE"),
    ("native_exit_code", 1), ("native_exit_code", None), ("contained_before_resume", False),
    ("termination_confirmed", False), ("job_active_after", 1), ("observed_dropped_bytes", 1)])
def test_owned_pass_rejects_incomplete_or_failed_run(key: str, value: object) -> None:
    run = good_run()
    assert common.passed_run(run)
    run[key] = value
    assert not common.passed_run(run)


def test_atomic_receipts_refuse_overwrite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(common, "BASE", tmp_path)
    path = tmp_path / "receipt.json"
    common.save(path, {"passed": False}, fresh=True)
    with pytest.raises(RuntimeError, match="Retain prior"):
        common.save(path, {"passed": True}, fresh=True)
    assert json.loads(path.read_text()) == {"passed": False}
    assert not path.with_name("receipt.json.writing").exists()


def test_receipt_outside_base_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(common, "BASE", tmp_path / "owned")
    with pytest.raises(RuntimeError, match="inside"):
        common.save(tmp_path / "outside.json", {})


def test_owned_command_budget_and_retention(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(common, "BASE", tmp_path)
    (tmp_path / "receipts").mkdir()
    observations = []
    resource = {"available_ram": 3 * common.GIB, "commit_headroom": 4 * common.GIB,
                "H_free": 10 * common.GIB, "C_free": 5 * common.GIB}

    def fake_run(command: list, root: Path, env: dict, raw: Path, budget: object, sample: object, **kwargs: object) -> dict:
        observations.append((root, budget, kwargs))
        assert sample(root) == resource
        assert kwargs["on_tick"]() is None
        return good_run()

    monkeypatch.setattr(common, "resources", lambda _: resource)
    monkeypatch.setattr(common, "load_helpers", lambda _: (None, fake_run))
    monkeypatch.setattr(common.shutil, "disk_usage", lambda _: SimpleNamespace(free=5 * common.GIB))
    row = common.owned(tmp_path, "small", ["not-launched.exe"], 90, env={"SAFE": "yes"})
    assert row["passed"]
    root, budget, kwargs = observations[0]
    assert root == tmp_path and budget.timeout_s == 90 and budget.max_processes == 64
    assert (budget.min_available_ram, budget.min_commit_headroom, budget.min_H_free) == (3 * common.GIB, 4 * common.GIB, 10 * common.GIB)
    assert kwargs["memory_diagnostics"] is True and budget.output_bytes == 8 * 1024**2
    with pytest.raises(RuntimeError, match="Retain"):
        common.owned(tmp_path, "small", ["not-launched.exe"], 90)
    with pytest.raises(RuntimeError, match="budget"):
        common.owned(tmp_path, "too-long", ["not-launched.exe"], 5401)


def test_admission_failure_is_retained_without_launch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(common, "BASE", tmp_path)
    (tmp_path / "receipts").mkdir()
    monkeypatch.setattr(common, "resources", lambda _: {"available_ram": 1})
    monkeypatch.setattr(common, "load_helpers", lambda _: pytest.fail("No launch allowed"))
    row = common.owned(tmp_path, "blocked", ["not-launched.exe"], 30)
    assert not row["passed"] and "available_ram" in row["error"]
    assert common.read_json(tmp_path / "receipts/blocked.json") == row


def test_plan_cannot_call_freeze_or_write(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    monkeypatch.setattr(adapter, "freeze", lambda *_: pytest.fail("Plan must not freeze or execute"))
    monkeypatch.setattr(adapter, "save", lambda *_args, **_kwargs: pytest.fail("Plan must not write"))
    monkeypatch.setattr(adapter.sys, "argv", ["adapter.py", "plan", "--source-root", "H:/frozen-source",
                                           "--reviewed-commit", "1" * 40])
    assert adapter.main() == 0
    assert json.loads(capsys.readouterr().out)["execution"] is False


def test_run_requires_execute_before_freeze(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adapter, "freeze", lambda *_: pytest.fail("Must reject before freeze"))
    monkeypatch.setattr(adapter.sys, "argv", ["adapter.py", "run", "build", "--source-root", "H:/frozen-source",
                                           "--reviewed-commit", "1" * 40])
    with pytest.raises(RuntimeError, match="opt-in"):
        adapter.main()


def test_async_launch_reserves_once_and_retains_controller_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "receipts").mkdir()
    monkeypatch.setattr(adapter, "BASE", tmp_path)
    monkeypatch.setattr(common, "BASE", tmp_path)
    monkeypatch.setattr(adapter, "freeze", lambda *_: {"sourceCommit": "1" * 40})
    monkeypatch.setattr(adapter, "check_initialised", lambda _: None)
    monkeypatch.setattr(adapter, "environment", lambda: {"TMP": str(tmp_path)})
    launched = []

    def popen(command: list, **kwargs: object) -> SimpleNamespace:
        launched.append((command, kwargs))
        return SimpleNamespace(pid=12345)

    monkeypatch.setattr(adapter.subprocess, "Popen", popen)
    monkeypatch.setattr(adapter.sys, "argv", ["adapter.py", "launch", "build", "--source-root", str(tmp_path),
                                           "--reviewed-commit", "1" * 40, "--execute"])
    assert adapter.main() == 0
    assert len(launched) == 1 and "--offline" in launched[0][0] and "--no-managed-python" in launched[0][0]
    assert "--token" in launched[0][0]
    assert common.read_json(tmp_path / "active.json")["phase"] == "build"
    assert common.read_json(tmp_path / "receipts/build-launch.json")["controllerIsNotTheOwnedJob"] is True
    assert not (tmp_path / "receipts/build-phase.json").exists()
    with pytest.raises(RuntimeError, match="already attempted"):
        adapter.main()
    assert len(launched) == 1


@pytest.mark.parametrize("drained", [True, False])
def test_controller_releases_lock_only_after_owned_job_drained(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, drained: bool) -> None:
    (tmp_path / "receipts").mkdir()
    (tmp_path / "active.json").write_text(json.dumps({"token": "owned-token"}))
    monkeypatch.setattr(adapter, "BASE", tmp_path)
    monkeypatch.setattr(common, "BASE", tmp_path)
    monkeypatch.setattr(adapter, "owned", lambda *_args, **_kwargs: {"passed": False,
        "run": {"termination_confirmed": drained, "job_active_after": 0 if drained else 1}})
    args = SimpleNamespace(phase="cpu", reviewed_commit="1" * 40, seconds=60)
    assert adapter.controller_run(args, tmp_path, "owned-token", {}) == 1
    assert (tmp_path / "active.json").exists() is not drained
    assert common.read_json(tmp_path / "receipts/cpu-phase.json")["passed"] is False


@pytest.mark.parametrize("failure", ["commit", "dirty", "version", "dependency"])
def test_freeze_rejects_unreviewed_inputs(failure: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Windows tmp_path is deliberately on H:. A separate fake checkout avoids touching real Git state.
    root = tmp_path / "source"
    root.mkdir()
    (root / "CMakeLists.txt").write_text("project(strata VERSION " + ("0.5.2" if failure == "version" else "0.5.3") + " LANGUAGES CXX)")
    commit = "1" * 40

    def fake_git(path: Path, *args: str) -> str:
        if "--show-toplevel" in args:
            return str(root)
        if "status" in args:
            return " M src/native.cpp" if failure == "dirty" else ""
        if path == common.GGML:
            return "2" * 40 if failure == "dependency" else common.GGML_PIN
        return "2" * 40 if failure == "commit" else commit

    monkeypatch.setattr(common, "git", fake_git)
    with pytest.raises(RuntimeError, match={"commit": "commit changed", "dirty": "clean frozen", "version": "freeze native", "dependency": "pin mismatch"}[failure]):
        common.freeze(root, commit)


def test_recipe_keeps_validated_defaults() -> None:
    args = common.configure(Path("H:/frozen-source"))
    for value in ("-DSTRATA_CUDA_SPILL_BASELINE=", "-DSTRATA_MMQ_TQ_OVERLAY=ON", "-DSTRATA_MMQ_KQUANTS=ON",
                  "-DSTRATA_NATIVE_CACHE_OWNER=ON", "-DSTRATA_ENABLE_SPIN8=ON", "-DCMAKE_CUDA_ARCHITECTURES=120",
                  "-DSTRATA_PORTABLE=ON", "-DFETCHCONTENT_FULLY_DISCONNECTED=ON"):
        assert value in args
    assert common.GGML_PIN == "3cf03257f219afbe7334045ff7c6a06ac68c627d"
    assert "ef3df253" not in " ".join(args)


def test_ctest_exact_selection_preserves_skip_detection() -> None:
    args = phases.ctest_args("cuda_spill_guard", 600)
    assert args[-1] == "^cuda_spill_guard$" and "--no-tests=error" in args
    for output in ("***Skipped", "Not Run", "No tests were found", "DISABLED"):
        assert not phases.test_pass({"passed": True}, output)
    assert phases.test_pass({"passed": True}, "100% tests passed")


def receipt_lines(mode: str = "bounded-experts-v1") -> list[str]:
    cpu, scratch = ("18512896", "1048576") if mode == "bounded-experts-v1" else ("0", "0")
    return [f"INFO q36_memory_mode={mode} q36_memory_scope=expert-working-storage q36_memory_total_process_bound=0 "
            f"q36_memory_cpu_stage_bytes={cpu} q36_memory_h2d_stage_bytes=67108864 q36_memory_io_scratch_bytes={scratch}",
            "READY 4096 stop"]


@pytest.mark.parametrize("mode", ["bounded-experts-v1", "legacy"])
def test_actual_pre_ready_memory_receipt(mode: str) -> None:
    assert model.memory_receipt(receipt_lines(mode), mode)["q36_memory_mode"] == mode


@pytest.mark.parametrize("mutation", ["late", "duplicate", "bytes", "bound"])
def test_invalid_memory_receipt_fails(mutation: str) -> None:
    lines = receipt_lines()
    if mutation == "late":
        lines.reverse()
    elif mutation == "duplicate":
        lines.insert(0, lines[0])
    elif mutation == "bytes":
        lines[0] = lines[0].replace("18512896", "18512897")
    else:
        lines[0] = lines[0].replace("total_process_bound=0", "total_process_bound=1")
    with pytest.raises(RuntimeError):
        model.memory_receipt(lines, "bounded-experts-v1")


def test_comparison_records_token_mismatch_and_no_restart(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(model, "BASE", tmp_path)
    monkeypatch.setattr(common, "BASE", tmp_path)
    monkeypatch.setattr(model, "sha", lambda _: "fresh-exe")
    (tmp_path / "results").mkdir()
    row = {"name": "first-owner-A", "nativePromptCount": 5, "nativeFreshReadCount": 5, "nativeReuseCount": 0,
           "generatedCount": 1, "generatedIds": [42], "finish": "length"}
    value = {"passed": True, "modelFilesBefore": {"weight": "unchanged"}, "modelFilesAfter": {"weight": "unchanged"},
             "protocol": {"exeSHA256": "fresh-exe", "inputIds": [1, 2], "requests": [row]}}
    (tmp_path / "results/model-bounded.json").write_text(json.dumps(value))
    value["protocol"]["requests"][0]["generatedIds"] = [43]
    (tmp_path / "results/model-legacy7.json").write_text(json.dumps(value))
    with pytest.raises(RuntimeError, match="comparison failed"):
        model.compare()
    result = common.read_json(tmp_path / "results/comparison.json")
    assert result["passed"] is False and result["cases"][0]["sameLegacy"] is False
    assert result["restart"].startswith("NOT_RUN")


def test_environment_scopes_temps_and_removes_user_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATA_UNKNOWN_SPEED_FLAG", "unsafe")
    monkeypatch.setenv("PYTHONPATH", "C:/user-hooks")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-value-not-a-secret")
    env = common.environment()
    assert "STRATA_UNKNOWN_SPEED_FLAG" not in env and "PYTHONPATH" not in env and "AWS_SECRET_ACCESS_KEY" not in env
    for key in ("TMP", "TEMP", "UV_CACHE_DIR", "CUDA_CACHE_PATH", "PIP_CACHE_DIR"):
        assert Path(env[key]).is_relative_to(common.BASE)
    assert env["CMAKE_BUILD_PARALLEL_LEVEL"] == "1" and env["UV_PYTHON_DOWNLOADS"] == "never"


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_cache_parser_comments_blanks_types_and_exact_values(newline: str) -> None:
    contents = newline.join(["# CMakeCache KEY:TYPE=VALUE", "", "//Default GPU architectures",
        "//continued comment with: punctuation=ignored", "CMAKE_CUDA_ARCHITECTURES:UNINITIALIZED=120", "",
        "# internal entries", "CMAKE_HOME_DIRECTORY:INTERNAL=H:/frozen-source",
        "STRATA_CUDA_SPILL_BASELINE:FILEPATH=", "FLAGS:STRING=-DNAME=a=b", ""])
    assert phases.parse_cmake_cache(contents) == {"CMAKE_CUDA_ARCHITECTURES": "120",
        "CMAKE_HOME_DIRECTORY": "H:/frozen-source", "STRATA_CUDA_SPILL_BASELINE": "", "FLAGS": "-DNAME=a=b"}


@pytest.mark.parametrize("entry", ["KEY\n:STRING=value", "KEY:STRING\n=value", "KEY:STRING=value\nKEY:STRING=other",
                                   " KEY:STRING=value", "KEY:=value"])
def test_cache_parser_rejects_split_malformed_or_duplicate_entries(entry: str) -> None:
    with pytest.raises(RuntimeError, match="Malformed|Duplicate"):
        phases.parse_cmake_cache(entry)


@pytest.mark.parametrize("architecture", [None, "121", "120;121", "120 ", "120-real"])
def test_cache_validation_keeps_exact_120_guard(architecture: str | None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(phases, "BUILD", tmp_path)
    root = Path("H:/frozen-source")
    cache = "# heading\r\n\r\nCMAKE_HOME_DIRECTORY:INTERNAL=H:/frozen-source\r\n\r\n// arch120\r\n"
    if architecture is not None:
        cache += "CMAKE_CUDA_ARCHITECTURES:UNINITIALIZED=" + architecture + "\r\n"
    (tmp_path / "CMakeCache.txt").write_bytes(cache.encode())
    with pytest.raises(RuntimeError, match="CMake recipe drift: CMAKE_CUDA_ARCHITECTURES"):
        phases.validate_cache(root)


def retry_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, str]:
    base = tmp_path / "local-053-20261109-opencode"
    (base / "receipts").mkdir(parents=True)
    (base / "native").mkdir()
    (base / "native-build").mkdir()
    root, commit = Path("H:/frozen-source"), "1" * 40
    identity = {"sourceRoot": str(root), "sourceCommit": commit, "ggmlRoot": str(common.GGML),
                "ggmlCommit": common.GGML_PIN, "helpers": {"helper": "unchanged"}}
    phase_run = {**good_run(), "native_exit_code": 1, "exit_code": 1,
                 "native_exit_code_observation": "OBSERVED_BEFORE_CLEANUP"}
    values = {"freeze.json": identity, "build-source.json": identity,
              "receipts/build-phase.json": {"passed": False, "run": phase_run, "frozenIdentity": identity},
              "receipts/build-configure.json": {"passed": True, "run": good_run()}}
    for name, value in values.items():
        (base / name).write_text(json.dumps(value), encoding="utf-8")
    (base / "receipts/build-phase.txt").write_text("BLOCKED/FAIL: RuntimeError: CMake recipe drift: CMAKE_CUDA_ARCHITECTURES\n")
    monkeypatch.setattr(retry_prepare, "BASE", base)
    monkeypatch.setattr(retry_prepare, "freeze", lambda *_: identity)
    return base, root, commit


def test_retry_preparation_is_readonly_by_default_and_preserves_whole_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base, root, commit = retry_fixture(tmp_path, monkeypatch)
    before = {p.relative_to(base).as_posix(): p.read_bytes() for p in base.rglob("*") if p.is_file()}
    report = retry_prepare.prepare(root, commit)
    assert report["eligible"] and report["renamed"] is False and base.is_dir()
    destination = Path(report["destination"])
    assert not destination.exists()
    # Only the isolated pytest fixture is renamed; the real BASE is never changed by these tests.
    assert retry_prepare.prepare(root, commit, execute=True)["renamed"] is True
    assert not base.exists()
    assert {p.relative_to(destination).as_posix(): p.read_bytes() for p in destination.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("blocker", ["successful-phase", "active-job", "unconfirmed-job", "configure-failed",
                                    "binary", "helper-started", "active-lock", "destination", "other-failure", "app"])
def test_retry_preparation_refuses_unsafe_or_reused_state(blocker: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base, root, commit = retry_fixture(tmp_path, monkeypatch)
    phase = common.read_json(base / "receipts/build-phase.json")
    if blocker == "successful-phase":
        phase["passed"] = True
    elif blocker == "active-job":
        phase["run"]["job_active_after"] = 1
    elif blocker == "unconfirmed-job":
        phase["run"]["termination_confirmed"] = False
    elif blocker == "configure-failed":
        (base / "receipts/build-configure.json").write_text(json.dumps({"passed": False, "run": good_run()}))
    elif blocker == "binary":
        (base / "native-build/Release").mkdir()
        (base / "native-build/Release/strata.exe").write_bytes(b"fixture")
    elif blocker == "helper-started":
        (base / "receipts/build-helper.json").write_text("{}")
    elif blocker == "active-lock":
        (base / "active.json").write_text("{}")
    elif blocker == "destination":
        base.with_name(base.name + "-configure-failed-r1").mkdir()
    elif blocker == "other-failure":
        (base / "receipts/build-phase.txt").write_text("another failure")
    elif blocker == "app":
        (base / "app").mkdir()
    (base / "receipts/build-phase.json").write_text(json.dumps(phase))
    with pytest.raises(RuntimeError):
        retry_prepare.prepare(root, commit, execute=True)
    assert base.is_dir()
