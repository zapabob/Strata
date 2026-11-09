"""Validate the actual local053 native adapter reports, without running native/model code."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from core import BASE, HERE, MANIFEST, NATIVE, NATIVE_COMMIT, NATIVE_ROOT, load, require, sha


def finished(run: dict, exit_code: int = 0) -> bool:
    return (run.get("status") == "FINISHED" and run.get("native_exit_code") == exit_code
            and run.get("contained_before_resume") is True and run.get("termination_confirmed") is True
            and run.get("job_active_after") == 0 and run.get("observed_dropped_bytes") == 0)


def passed(row: dict) -> bool:
    return row.get("passed") is True and finished(row.get("run", {}))


def required_tests(path: Path) -> dict[str, tuple[str, ...]]:
    """Read real helper constants, never import its ambiguous `common` module."""
    wanted = {"CPU_REQUIRED", "GPU_REQUIRED"}
    found = {}
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in wanted:
                    found[target.id] = ast.literal_eval(node.value)
    require(set(found) == wanted and all(isinstance(v, tuple) and v for v in found.values()),
            "Unknown native suite contract")
    return found


def validate(base: Path = BASE, native: Path = NATIVE, source: Path = NATIVE_ROOT,
             adapters: Path = HERE.parent / "native") -> dict[str, Any]:
    """Require fresh functional/model evidence; record genuine resource FAIL without promotion."""
    evidence: dict[str, dict] = {}

    def report(name: str, directory: str = "results") -> dict:
        path = base / directory / name
        value = load(path)
        require(isinstance(value, dict), "Unknown native report type: " + name)
        evidence[directory + "/" + name] = {"path": str(path), "sha256": sha(path)}
        return value

    freeze = report("freeze.json", ".")
    require(freeze["sourceCommit"] == NATIVE_COMMIT and Path(freeze["sourceRoot"]) == source,
            "Native freeze identity differs")
    # Bind report interpretation to the exact adapters that produced the frozen evidence.
    for name, checksum in freeze["adapters"].items():
        require(sha(adapters / name) == checksum, "Native report adapter changed after freeze")
    require({"phases.py", "model.py", "common.py", "binding.mjs"} <= set(freeze["adapters"]),
            "Native report adapter identities absent")
    tests = required_tests(adapters / "phases.py")
    package = report("package.json")
    require(package["nativeSourceCommit"] == NATIVE_COMMIT and Path(package["sourceRoot"]) == source
            and Path(package["component"]) == native and package["signed"] is False
            and package["installed"] is False and package["version"] == "0.5.3",
            "Native package receipt identity differs")
    manifest = load(native / MANIFEST)
    require(package["manifestSHA256"] == sha(native / MANIFEST) and package["files"] == manifest["files"],
            "Native package manifest differs")
    for name, field in (("strata.exe", "strataSHA256"), ("strata-q36.exe", "q36SHA256"),
                        ("native-build.json", "nativeBuildSHA256")):
        require(sha(native / name) == package[field], "New native bytes differ from evidence")
    engine = package["strataSHA256"]
    summary = report("qualification-summary.json")
    require(summary["nativeSourceCommit"] == NATIVE_COMMIT and Path(summary["sourceRoot"]) == source
            and summary["manifestSHA256"] == package["manifestSHA256"]
            and summary["strataSHA256"] == engine and summary["q36SHA256"] == package["q36SHA256"]
            and summary["nativeBuildSHA256"] == package["nativeBuildSHA256"]
            and summary["releaseQualified"] is False, "Unknown/stale audit identity")
    phases = summary["phases"]
    for name in ("stage", "cpu", "gpu", "sanitizer", "spill", "model-bounded", "model-legacy7", "model-restart", "compare"):
        row = report(name + "-phase.json", "receipts")
        require(row == phases[name], "Audit phase snapshot differs")
        require(row["frozenIdentity"] == freeze, "Phase is not bound to native freeze")
        if name != "spill":
            require(passed(row), "Required native phase failed/incomplete: " + name)
    require(any(passed(phases[name]) and phases[name]["frozenIdentity"] == freeze for name in ("build", "bind")),
            "Successful source-bound build/bind required")
    for kind in ("cpu", "gpu", "sanitizer"):
        suite = report(kind + ".json")
        require(suite["passed"] is True and suite["releaseQualified"] is False
                and suite["cases"] and all(passed(row) for row in suite["cases"]
                                          if row.get("status") != "NOT_AVAILABLE"),
                "Required suite evidence failed: " + kind)
        names = {row["name"] for row in suite["cases"]}
        expected = tests["CPU_REQUIRED"] if kind == "cpu" else tests["GPU_REQUIRED"] if kind == "gpu" else (
            "q36_kv_lifecycle_test", "q36_kv_cache_test")
        require({kind + "-" + name for name in expected} <= names, "Required suite cases absent")
        if kind != "sanitizer":
            require(suite["optionalTestsPassedWhenPresent"] is True, "Optional present suite failed")
        if kind == "cpu":
            require({"cpu-" + exe + "-" + option for exe in ("strata", "strata-q36")
                     for option in ("version", "help")} <= names, "Actual native version/help evidence absent")
        if kind == "gpu":
            require({"gpu-spin8-b2-first-use", "gpu-spin8-b2-full"} <= names, "Spin8 GPU evidence absent")
    models = {}
    expected_names = ["first-owner-A", "same-owner-A", "different-owner-B", "missing-owner",
                      "cancel-decode", "after-cancel-clears", "short-generation"]
    for name in ("model-bounded", "model-legacy7", "model-restart"):
        row = report(name + ".json")
        protocol = row["protocol"]
        require(row["passed"] is True and row["ownedJobDrained"] is True
                and row["modelFilesPreserved"] is True and row["modelFilesBefore"]
                and row["modelFilesBefore"] == row["modelFilesAfter"]
                and Path(row["sourceRoot"]) == source and row["releaseQualified"] is False
                and passed(row["driver"]), "Actual protected model evidence incomplete")
        require(protocol == report(name + "-protocol.json") and protocol["passed"] is True
                and protocol["exeSHA256"] == engine and protocol["capacity"] == 4096
                and protocol["ready"] == "READY 4096 stop" and protocol["fullInputQuality"] is False
                and protocol["mode"] == ("legacy" if name == "model-legacy7" else "bounded-experts-v1")
                and protocol["exitCodeBeforeJobCleanup"] == 0 and protocol["memorySamples"] > 0,
                "Unknown actual model protocol identity/contract")
        requests = protocol["requests"]
        require([r["name"] for r in requests] == (expected_names if name != "model-restart" else
                                                  ["first-owner-A", "short-generation"]),
                "Actual model cases missing/unknown")
        memory = protocol["memoryReceipt"]
        require(protocol["inputCount"] == len(protocol["inputIds"]) > 0
                and set(memory) == {"q36_memory_" + key for key in
                                    ("mode", "scope", "total_process_bound", "cpu_stage_bytes", "h2d_stage_bytes", "io_scratch_bytes")}
                and memory["q36_memory_mode"] == protocol["mode"]
                and memory["q36_memory_scope"] == "expert-working-storage"
                and memory["q36_memory_total_process_bound"] == "0"
                and memory["q36_memory_h2d_stage_bytes"] == "67108864"
                and (memory["q36_memory_cpu_stage_bytes"], memory["q36_memory_io_scratch_bytes"])
                == (("0", "0") if name == "model-legacy7" else ("18512896", "1048576")),
                "Unknown actual token/memory receipt contract")
        for request in requests:
            require(request["nativePromptCount"] == request["submittedCount"]
                    == request["nativeFreshReadCount"] + request["nativeReuseCount"]
                    and request["generatedCount"] == len(request["generatedIds"]) > 0
                    and request["generatedText"].strip() and request["generatedCount"] <= request["requestedMaxNew"]
                    and request["finish"] in (("cancel",) if request["name"] == "cancel-decode" else ("length", "stop")),
                    "Actual request failed its native protocol contract")
        models[name] = row
    left, right, restart = (models[k] for k in ("model-bounded", "model-legacy7", "model-restart"))
    require(left["modelFilesAfter"] == right["modelFilesBefore"] == restart["modelFilesBefore"]
            and left["protocol"]["inputIds"] == right["protocol"]["inputIds"] == restart["protocol"]["inputIds"],
            "Model comparison protected input identities differ")
    fields = ("name", "nativePromptCount", "nativeFreshReadCount", "nativeReuseCount", "generatedCount", "generatedIds", "finish")
    require(all(all(a[k] == b[k] for k in fields) for a, b in
                zip(left["protocol"]["requests"], right["protocol"]["requests"], strict=True)),
            "Actual bounded/legacy outputs differ")
    require(restart["protocol"]["requests"][0]["generatedIds"] == left["protocol"]["requests"][0]["generatedIds"],
            "Actual restart differs")
    comparison = report("comparison.json")
    require(comparison["passed"] is True and comparison["restartPassed"] is True
            and comparison["exeSHA256"] == engine and comparison["releaseQualified"] is False
            and [r["case"] for r in comparison["cases"]] == expected_names
            and all(r["sameLegacy"] is True for r in comparison["cases"]), "Current comparison failed/unknown")
    spill = report("spill.json")
    require(type(spill["passed"]) is bool and spill["releaseQualified"] is False
            and len(spill["cases"]) == 1 and spill["cases"][0]["name"] == "spill-cuda_spill_guard",
            "Unknown resource guard report")
    log = base / "receipts/spill-cuda_spill_guard.txt"
    violations = [line.strip() for line in log.read_text(encoding="utf-8").splitlines()
                  if line.strip().startswith("VIOLATION ")]
    evidence["receipts/" + log.name] = {"path": str(log), "sha256": sha(log)}
    resource_pass = spill["passed"]
    require(summary["resourceGuardPassed"] is resource_pass and summary["resourceViolations"] == violations
            and summary["nativeFunctionalChecksPassed"] is True, "Audit quality summary differs")
    guard = spill["cases"][0]
    require(type(guard["passed"]) is bool and guard["passed"] is resource_pass
            and finished(guard["run"], 0 if resource_pass else 8)
            and finished(phases["spill"]["run"], 0 if resource_pass else 1)
            and phases["spill"]["passed"] is resource_pass
            and bool(violations) is not resource_pass, "Resource FAIL must be a completed guard failure, not a timeout/error")
    audit = report("audit-phase.json", "receipts")
    require(audit["frozenIdentity"] == freeze and finished(audit["run"], 0 if resource_pass else 1)
            and audit["passed"] is resource_pass, "Audit did not finish/drain")
    return {"nativeFunctionalChecksPassed": True,
            "nativeResourceGuard": {"status": "PASS" if resource_pass else "FAIL", "passed": resource_pass,
                                    "violations": violations},
            "actualModelChecks": {name: {"passed": True, "requests": len(row["protocol"]["requests"]),
                                        "scope": "short requests, 4096 capacity"} for name, row in models.items()},
            "boundedLegacyComparisonPassed": True, "restartPassed": True,
            "releaseQualified": False, "fullWindowQualified": False, "generalQualityQualified": False,
            "lowPrecisionModelQualityQualified": False, "newNativeQualified": False,
            "retainedBackends": "byte retention and integrity only; no new model qualification",
            "evidence": evidence}
