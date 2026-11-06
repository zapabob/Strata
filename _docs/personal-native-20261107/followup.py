"""Native-only r3 follow-up. All operations run inside the existing owned guard."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from guard import ROOT, OUT, NODE, CUDA, environment
import qualify
from receipt_check import check

RUN = OUT / "followup-r3"
BUILD = OUT / "native-build"
COMPONENT = OUT / "component-r3/0.5.2-windows-x86_64-cuda-cuda13"


def init() -> None:
    assert OUT.is_dir() and not RUN.exists()
    RUN.mkdir()
    before = RUN / "r2-before"
    before.mkdir()
    artifacts = {}
    for name in ("strata.exe", "strata-q36.exe", "native-build.json", "strata_qwen35.lib", "q36_kv_cache_test.exe"):
        source = BUILD / "Release" / name
        shutil.copy2(source, before / name)
        assert qualify.sha(source) == qualify.sha(before / name)
        artifacts[name] = qualify.sha(source)
    (RUN / "r2-identities.json").write_text(json.dumps(artifacts, indent=2) + "\n")


def red() -> None:
    env = environment()
    env["CUDA_VISIBLE_DEVICES"] = "-1"
    env["PATH"] = str(qualify.COMPONENT) + ";" + env["PATH"]
    version = subprocess.run([str(qualify.COMPONENT / "strata-q36.exe"), "--model",
                              str(RUN / "nonexistent.gguf"), "--version"],
                             capture_output=True, text=True, env=env, timeout=15)
    results = {"versionBeforeMissingModelAndGpu": version.returncode == 0 and version.stdout.strip() == "strata-q36 0.5.2",
               "versionExit": version.returncode, "receiptBeforeReady": False}
    try:
        check(OUT / "q36-bounded-first-stdout.txt", "bounded-experts-v1")
        results["receiptBeforeReady"] = True
    except AssertionError as error:
        results["receiptFailure"] = str(error)
    (RUN / "red.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results), flush=True)
    assert results["versionBeforeMissingModelAndGpu"] and results["receiptBeforeReady"], "Observed missing native contracts"


def build() -> None:
    assert (RUN / "r2-identities.json").is_file()
    assert not (RUN / "build-source.json").exists()
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert not subprocess.check_output(["git", "status", "--porcelain", "--", "CMakeLists.txt", "src",
                                       "include", "cmake", "spin8", "tqcodec", "tools/qwen35/kv_cache_test.cu"],
                                      cwd=ROOT, text=True).strip()
    configure = ["cmake", "-S", str(ROOT), "-B", str(BUILD)]
    (RUN / "build-source.json").write_text(json.dumps({"sourceCommit": source, "configure": configure,
        "incremental": True, "build": str(BUILD)}, indent=2) + "\n")
    subprocess.run(configure, cwd=ROOT, check=True)
    subprocess.run([str(NODE), str(ROOT / "tools/build_hakua_engine.mjs"), str(BUILD), "1"], cwd=ROOT, check=True)


def stage() -> None:
    assert json.loads((OUT / "receipts/r3-incremental-build.json").read_text())["passed"]
    native = OUT / "native-component-r3/0.5.2-windows-x86_64-cuda-cuda13"
    assert not native.exists() and not COMPONENT.exists()
    source = json.loads((RUN / "build-source.json").read_text())["sourceCommit"]
    subprocess.run([sys.executable, "-B", str(ROOT / "packaging/package_engine.py"), "--src", str(BUILD / "Release"),
                    "--backend", "cuda", "--version", "0.5.2", "--platform", "windows-x86_64", "--variant", "cuda13",
                    "--arch", "sm_120", "--min-driver", "nvidia=580.65", "--build-id", source,
                    "--include", "native-build.json", "--include", "strata-q36.exe", "--search", str(CUDA / "bin/x64"),
                    "--search", str(CUDA / "bin"), "--out", str(native.parent)], cwd=ROOT, check=True, timeout=180)
    subprocess.run([sys.executable, "-B", str(ROOT / "packaging/package_engine.py"), "--verify", str(native)],
                   cwd=ROOT, check=True, timeout=180)
    # Reuse only the exact already-verified r2 payload. No key access in this follow-up.
    old = qualify.COMPONENT
    old_manifest = json.loads((old / "engine-component.json").read_text())
    old_receipt = json.loads((OUT / "package-receipt.json").read_text())
    assert qualify.sha(old / "engine-component.json") == old_receipt["manifestSHA256"]
    for entry in old_manifest["files"]:
        path = old / entry["path"]
        assert path.stat().st_size == entry["bytes"] and qualify.sha(path) == entry["sha256"]
    subprocess.run([str(NODE), str(Path(__file__).with_name("compose.mjs")), str(native), str(old), str(COMPONENT)],
                   cwd=ROOT, check=True, timeout=180)
    result = {"sourceCommit": source, "signed": False, "installed": False, "component": str(COMPONENT),
              "manifestSHA256": qualify.sha(COMPONENT / "engine-component.json"),
              "strataSHA256": qualify.sha(COMPONENT / "strata.exe"),
              "q36SHA256": qualify.sha(COMPONENT / "strata-q36.exe"),
              "nativeBuildSHA256": qualify.sha(COMPONENT / "native-build.json"),
              "reusedR2ManifestSHA256": old_receipt["manifestSHA256"]}
    (RUN / "package.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


def suite() -> None:
    qualify.OUT, qualify.COMPONENT = RUN, COMPONENT
    qualify.suite()
    extra = ["C:/Program Files/CMake/bin/ctest.exe", "--test-dir", str(BUILD), "-C", "Release", "--parallel", "1",
             "--no-tests=error", "--output-on-failure", "-R", "^q36_version$"]
    with (RUN / "q36-version-no-model-no-gpu.txt").open("x") as log:
        subprocess.run(extra, check=True, stdout=log, stderr=subprocess.STDOUT, timeout=30)
    qualify.admit()
    with (RUN / "q36-kv-full-memcheck.txt").open("x") as log:
        subprocess.run([str(CUDA / "compute-sanitizer/compute-sanitizer.exe"), "--tool", "memcheck", "--error-exitcode", "1",
                        str(BUILD / "Release/q36_kv_cache_test.exe")], stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=180)


def model() -> None:
    mode, label, *rest = sys.argv[2:]
    qualify.OUT, qualify.COMPONENT = RUN, COMPONENT
    qualify.model(mode, label, short=rest == ["short"])
    fields = check(RUN / (label + "-stdout.txt"), mode)
    result = json.loads((RUN / (label + ".json")).read_text())
    assert fields["q36_memory_h2d_stage_bytes"] == "67108864"
    expected = {"bounded-experts-v1": ("18512896", "1048576"), "legacy": ("0", "0")}[mode]
    assert (fields["q36_memory_cpu_stage_bytes"], fields["q36_memory_io_scratch_bytes"]) == expected
    (RUN / (label + "-memory-receipt.json")).write_text(json.dumps({"passed": True, "beforeReady": True,
        "binarySHA256": result["exeSHA256"], "fields": fields}, indent=2) + "\n")
    print(json.dumps(fields), flush=True)


if __name__ == "__main__":
    {"init": init, "red": red, "build": build, "stage": stage, "suite": suite, "model": model}[sys.argv[1]]()
