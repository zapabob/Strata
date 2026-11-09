"""Single explicitly requested native operation, called only by the owned worker."""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
from typing import Any

from common import (BASE, BUILD, COMPONENT, CTEST, CUDA, HERE, NATIVE, NODE,
                    PYTHON, configure, environment, freeze, owned, read_json, require, save, sha, text)

CPU_REQUIRED = ("q36_bounded_experts_test", "q36_expert_store_test", "q36_transfer_lifetime_test",
                "q36_bounded_cpu_parity_test", "q36_kv_layout_test", "q36_version")
CPU_OPTIONAL = ("adaptive_range_test", "mmq_ids_margin_test", "timer_marks_test",
                "qsa_two_pass_test", "qsa_two_pass_status_test")
GPU_REQUIRED = ("q36_kv_lifecycle_test", "q36_kv_cache_test", "native_cache_bridge", "native_cache_owner")


def command(root: Path, name: str, args: list[str], seconds: int = 120,
            *, env: dict[str, str] | None = None) -> dict[str, Any]:
    return owned(root, name, args, seconds, env=env)


def checked(root: Path, name: str, args: list[str], seconds: int = 120) -> dict[str, Any]:
    result = command(root, name, args, seconds)
    require(result["passed"], f"Command failed; retained receipt: {name}")
    return result


def binding(root: Path, name: str, folder: Path) -> dict[str, Any]:
    checked(root, name, [str(NODE), str(HERE / "binding.mjs"), str(root), str(folder)], 120)
    return json.loads(text(name).strip())


def build(root: Path, commit: str) -> None:
    require(not BUILD.exists() and not any(NATIVE.iterdir()), "Fresh build/native outputs required")
    save(BASE / "build-source.json", {**freeze(root, commit), "configure": configure(root),
         "parallelism": 1, "buildHelper": str(root / "tools/build_hakua_engine.mjs"),
         "historicalRecipe": "personal-native-20261107/build.py; no explicit spill baseline"}, fresh=True)
    checked(root, "tool-node", [str(NODE), "--version"], 15)
    require(text("tool-node").strip() == "v24.22.2", "Private Node version mismatch")
    checked(root, "tool-python", [str(PYTHON), "--version"], 15)
    require(text("tool-python").startswith("Python 3.12."), "Pinned Python is not 3.12")
    checked(root, "tool-nvcc", [str(CUDA / "bin/nvcc.exe"), "--version"], 15)
    require("V13.3.73" in text("tool-nvcc"), "CUDA 13.3.73 required")
    checked(root, "build-configure", configure(root), 300)
    validate_cache(root)
    # The unmodified current source helper builds all targets serially and writes native-build.json.
    result = owned(root, "build-helper", [str(NODE), str(root / "tools/build_hakua_engine.mjs"),
                   str(BUILD), "1"], 5100, output_bytes=64 * 1024**2)
    require(result["passed"], "Build/helper failed. Preserve failure; run probe-diagnostic explicitly, never synthesize identity")
    save(BASE / "results/build.json", binding(root, "build-binding", BUILD / "Release"), fresh=True)


def parse_cmake_cache(contents: str) -> dict[str, str]:
    """Parse one KEY:TYPE=VALUE per line, never consuming comments/newlines as keys."""
    entries: dict[str, str] = {}
    for number, line in enumerate(contents.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith(("#", "//")):
            continue
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_.+-]*):([A-Z][A-Z0-9_]*)=(.*)", line)
        require(match is not None, f"Malformed CMake cache entry at line {number}")
        key, _kind, value = match.groups()
        require(key not in entries, f"Duplicate CMake cache key: {key}")
        entries[key] = value
    return entries


def validate_cache(root: Path) -> None:
    contents = (BUILD / "CMakeCache.txt").read_text(encoding="utf-8")
    entries = parse_cmake_cache(contents)
    expected = {"CMAKE_HOME_DIRECTORY": str(root), "CMAKE_CUDA_ARCHITECTURES": "120",
                "STRATA_GGML_DIR": "H:/Strata/deps/ggml-3cf03257", "STRATA_PORTABLE": "ON",
                "STRATA_ENABLE_CUDA": "ON", "STRATA_NATIVE_EXPERTS": "ON", "STRATA_ENABLE_SPIN8": "ON",
                "STRATA_ENABLE_NATIVE_CACHE": "ON", "STRATA_NATIVE_CACHE_OWNER": "ON",
                "STRATA_MMQ_KQUANTS": "ON", "STRATA_MMQ_TQ_OVERLAY": "ON", "STRATA_BUILD_TESTS": "ON",
                "STRATA_BUILD_DSV41": "OFF", "STRATA_BUILD_SPLIT": "OFF", "STRATA_PREFILL_MMQ": "OFF",
                "STRATA_CUDA_SPILL_BASELINE": "", "FETCHCONTENT_FULLY_DISCONNECTED": "ON",
                "CMAKE_GENERATOR": "Visual Studio 17 2022", "CMAKE_GENERATOR_PLATFORM": "x64",
                "CMAKE_GENERATOR_INSTANCE": "C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools"}
    for key, value in expected.items():
        require(entries.get(key, "<missing>").replace("\\", "/") == value.replace("\\", "/"), f"CMake recipe drift: {key}")
    compilers = list((BUILD / "CMakeFiles").glob("*/CMakeCUDACompiler.cmake"))
    require(len(compilers) == 1 and 'set(CMAKE_CUDA_COMPILER_VERSION "13.3.73")' in compilers[0].read_text(encoding="utf-8"),
            "Configured CUDA compiler differs from requested 13.3.73")
    cxx = list((BUILD / "CMakeFiles").glob("*/CMakeCXXCompiler.cmake"))
    require(len(cxx) == 1 and 'set(CMAKE_CXX_COMPILER_ID "MSVC")' in cxx[0].read_text(encoding="utf-8"), "MSVC required")
    # Keep actual compiler data/hashes rather than inventing an MSVC minor version.
    save(BASE / "results/compiler.json", {"cacheSHA256": sha(BUILD / "CMakeCache.txt"),
         "cache": entries, "cuda": compilers[0].read_text(encoding="utf-8"), "cxx": cxx[0].read_text(encoding="utf-8")}, fresh=True)


def bind(root: Path) -> None:
    require((BUILD / "CMakeCache.txt").is_file(), "Explicit bind requires an existing configured build")
    require(not (BASE / "results/build.json").exists(), "Build already bound")
    # Explicit retry of the same authoritative helper, not a replacement version probe/identity writer.
    checked(root, "bind-helper", [str(NODE), str(root / "tools/build_hakua_engine.mjs"), str(BUILD), "1"], 5100)
    save(BASE / "results/build.json", binding(root, "bind-binding", BUILD / "Release"), fresh=True)


def diagnostic(root: Path) -> None:
    rows = []
    for name in ("strata", "strata-q36"):
        rows.append(command(root, "diagnostic-" + name, [str(BUILD / "Release" / (name + ".exe")), "--version"], 20))
    save(BASE / "results/probe-diagnostic.json", {"diagnosticOnly": True, "cases": rows,
         "note": "Does not repair native-build.json or convert an earlier build failure to PASS"}, fresh=True)


def require_build() -> None:
    require((BASE / "results/build.json").is_file(), "Successful authoritative build binding required")
    receipts = [BASE / "receipts" / (name + "-phase.json") for name in ("build", "bind")]
    require(any(p.is_file() and read_json(p).get("passed") for p in receipts), "Successful build/bind phase receipt required")


def require_package() -> dict[str, Any]:
    package = read_json(BASE / "results/package.json")
    require(sha(COMPONENT / "engine-component.json") == package["manifestSHA256"], "Staged manifest changed")
    for item in package["files"]:
        path = COMPONENT / item["path"]
        require(path.stat().st_size == item["bytes"] and sha(path) == item["sha256"], "Staged payload changed")
    return package


def stage(root: Path, commit: str) -> None:
    require_build()
    info = binding(root, "stage-source-binding", BUILD / "Release")
    require(info == read_json(BASE / "results/build.json"), "Built payload changed")
    require(not any(NATIVE.iterdir()) and not COMPONENT.parent.exists(), "Fresh native/component required")
    for path in sorted((BUILD / "Release").iterdir()):
        if path.name in ("strata.exe", "strata-q36.exe", "native-build.json") or path.suffix.lower() == ".dll":
            require(path.is_file() and not path.is_symlink(), "Regular build artifact required")
            shutil.copy2(path, NATIVE / path.name)
            require(sha(path) == sha(NATIVE / path.name), "Native staging copy mismatch")
    binding(root, "stage-native-binding", NATIVE)
    partial = COMPONENT.parent / ("." + COMPONENT.name + ".partial")
    require(not COMPONENT.exists() and not partial.exists(), "Never replace partial or finished component evidence")
    checked(root, "stage-package", [str(PYTHON), "-B", str(root / "packaging/package_engine.py"),
        "--src", str(NATIVE), "--backend", "cuda", "--version", "0.5.3", "--platform", "windows-x86_64",
        "--variant", "cuda13", "--arch", "sm_120", "--min-driver", "nvidia=580.65", "--build-id", commit,
        "--include", "native-build.json", "--include", "strata-q36.exe",
        "--search", str(CUDA / "bin/x64"), "--search", str(CUDA / "bin"), "--out", str(COMPONENT.parent)], 180)
    checked(root, "stage-verify", [str(PYTHON), "-B", str(root / "packaging/package_engine.py"), "--verify", str(COMPONENT)], 180)
    manifest = read_json(COMPONENT / "engine-component.json")
    require(manifest["signature"] is None and manifest["build_id"] == commit, "Unsigned source-bound package required")
    require(not any(item["path"].startswith("local-backends/") for item in manifest["files"]), "Native-only component required")
    require(sha(COMPONENT / "strata-q36.exe") == info["q36SHA256"], "Q36 staging mismatch")
    save(BASE / "results/package.json", {**info, "nativeSourceCommit": commit, "sourceRoot": str(root),
         "component": str(COMPONENT), "manifestSHA256": sha(COMPONENT / "engine-component.json"),
         "signed": False, "installed": False, "files": manifest["files"]}, fresh=True)


def ctest_args(name: str, seconds: int = 90) -> list[str]:
    return [str(CTEST), "--test-dir", str(BUILD), "-C", "Release", "--parallel", "1",
            "--no-tests=error", "--output-on-failure", "--timeout", str(seconds), "-R", "^" + re.escape(name) + "$"]


def test_pass(row: dict, output: str) -> bool:
    return row["passed"] and not re.search(r"\*\*\*Skipped|Not Run|No tests were found|DISABLED", output, re.I)


def gpu_admit(root: Path, name: str, minimum: int = 1024) -> None:
    checked(root, name, ["C:/Windows/System32/nvidia-smi.exe", "--query-gpu=memory.free", "--format=csv,noheader,nounits"], 15)
    free = int(text(name).splitlines()[0].strip())
    require(free >= minimum, "GPU admission refused; coordinate with parent, never stop user processes")


def suite(root: Path, kind: str) -> None:
    require_build()
    require_package()
    binding(root, kind + "-binding", COMPONENT)
    rows: list[dict] = []
    checked(root, kind + "-inventory", [str(CTEST), "--test-dir", str(BUILD), "-C", "Release", "--show-only=json-v1"], 30)
    inventory = read_json(BASE / "receipts" / (kind + "-inventory.txt"))["tests"]
    names = {entry["name"] for entry in inventory}
    save(BASE / "results" / (kind + "-inventory.json"), inventory, fresh=True)

    def case(label: str, args: list[str], seconds: int = 120, gpu: bool = False) -> dict:
        if gpu:
            gpu_admit(root, kind + "-" + label + "-admission")
        env = environment()
        env["PATH"] = str(COMPONENT) + ";" + env["PATH"]
        row = command(root, kind + "-" + label, args, seconds, env=env)
        row["passed"] = test_pass(row, text(kind + "-" + label))
        rows.append(row)
        save(BASE / "results" / (kind + ".json"), {"cases": rows, "passed": False})
        return row

    save(BASE / "results" / (kind + ".json"), {"cases": [], "passed": False}, fresh=True)
    if kind == "cpu":
        for exe in ("strata", "strata-q36"):
            label = exe + "-version"
            row = case(label, [str(COMPONENT / (exe + ".exe")), "--version"], 20)
            row["passed"] &= bool(re.search(r"\b0\.5\.3\b", text(kind + "-" + label)))
            label = exe + "-help"
            row = case(label, [str(COMPONENT / (exe + ".exe")), "--help"], 20)
            output = text(kind + "-" + label)
            row["passed"] &= all(marker in output for marker in ("Q36_MEMORY_CAPABILITIES", "bounded-experts-v1", "Q36_KV_CAPABILITIES"))
    required = CPU_REQUIRED if kind == "cpu" else GPU_REQUIRED if kind == "gpu" else ("cuda_spill_guard",)
    optional = CPU_OPTIONAL if kind == "cpu" else ()
    for name in (*required, *optional):
        if name not in names:
            rows.append({"name": name, "status": "MISSING_REQUIRED" if name in required else "NOT_AVAILABLE",
                         "passed": False, "optional": name in optional})
            continue
        seconds = 600 if kind == "spill" else 90
        case(name, ctest_args(name, seconds), seconds + 30, gpu=kind == "gpu")
    if kind == "gpu":
        exe = BUILD / "spin8/Release/spin8_attention_v2_cuda_test.exe"
        case("spin8-b2-first-use", [str(exe), "--first-use-only"], 120, gpu=True)
        case("spin8-b2-full", [str(exe)], 180, gpu=True)
    result = {"cases": rows, "passed": all(row["passed"] for row in rows if not row.get("optional")),
              "optionalTestsPassedWhenPresent": all(row["passed"] for row in rows if row.get("status") != "NOT_AVAILABLE"),
              "releaseQualified": False}
    result["passed"] &= result["optionalTestsPassedWhenPresent"]
    save(BASE / "results" / (kind + ".json"), result)
    require(result["passed"], f"{kind} qualification FAIL or incomplete; see retained results")


def sanitizer(root: Path) -> None:
    require_build()
    require_package()
    rows = []
    tool = CUDA / "compute-sanitizer/compute-sanitizer.exe"
    rows.append(command(root, "sanitizer-version", [str(tool), "--version"], 30))
    for name in ("q36_kv_lifecycle_test", "q36_kv_cache_test"):
        gpu_admit(root, "sanitizer-" + name + "-admission")
        label = "sanitizer-" + name
        row = command(root, label, [str(tool), "--tool", "memcheck", "--error-exitcode", "1",
                      str(BUILD / "Release" / (name + ".exe"))], 240)
        row["passed"] &= "ERROR SUMMARY: 0 errors" in text(label)
        rows.append(row)
    result = {"cases": rows, "passed": all(row["passed"] for row in rows), "releaseQualified": False}
    save(BASE / "results/sanitizer.json", result, fresh=True)
    require(result["passed"], "Sanitizer FAIL or incomplete")


def audit(root: Path, commit: str) -> None:
    package = require_package()
    info = binding(root, "audit-binding", COMPONENT)
    require(all(info[key] == package[key] for key in info), "Package identity drift")
    checked(root, "audit-package", [str(PYTHON), "-B", str(root / "packaging/package_engine.py"), "--verify", str(COMPONENT)], 180)
    require(read_json(COMPONENT / "engine-component.json")["signature"] is None, "Component must remain unsigned")
    phases = ("build", "bind", "stage", "cpu", "gpu", "sanitizer", "spill", "model-bounded", "model-legacy7", "model-restart", "compare")
    receipts = {name: read_json(BASE / "receipts" / (name + "-phase.json")) if (BASE / "receipts" / (name + "-phase.json")).is_file()
                else {"passed": False, "status": "NOT_RUN"} for name in phases}
    functional = all(receipts[name].get("passed") for name in ("stage", "cpu", "gpu", "sanitizer", "model-bounded", "model-legacy7", "compare"))
    resource_text = text("spill-cuda_spill_guard")
    violations = [line.strip() for line in resource_text.splitlines() if line.strip().startswith("VIOLATION ")]
    result = {**package, "nativeSourceCommit": commit, "sourceRoot": str(root), "phases": receipts,
              "nativeFunctionalChecksPassed": functional, "resourceGuardPassed": receipts["spill"].get("passed", False),
              "resourceViolations": violations, "resourceLog": str(BASE / "receipts/spill-cuda_spill_guard.txt"),
              "releaseQualified": False, "resultsDirectory": str(BASE / "results"),
              "limits": "Native-only unsigned evidence. Short Q36 requests only. Parent owns composite/signing/Host Q36 digest. No ef3df253 candidate available/included."}
    save(BASE / "results/qualification-summary.json", result, fresh=True)
    require(functional and result["resourceGuardPassed"], "Qualification incomplete/FAIL; summary retained; parent disposition required")


def dispatch(root: Path, commit: str, phase: str) -> None:
    if phase == "build":
        build(root, commit)
    elif phase == "bind":
        bind(root)
    elif phase == "probe-diagnostic":
        diagnostic(root)
    elif phase == "stage":
        stage(root, commit)
    elif phase in ("cpu", "gpu", "spill"):
        suite(root, phase)
    elif phase == "sanitizer":
        sanitizer(root)
    elif phase.startswith("model-") or phase == "compare":
        from model import compare, model
        if phase == "compare":
            compare()
        else:
            require_build()
            require_package()
            binding(root, phase + "-binding", COMPONENT)
            model(root, phase)
    elif phase == "audit":
        audit(root, commit)
    else:
        raise RuntimeError("Unknown phase")
