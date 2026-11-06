"""Verify final owned artifacts and summarise measured qualification without promotion."""
from __future__ import annotations

import json
import re
import subprocess

from guard import ROOT, OUT, NODE, CUDA
from qualify import BUILD, COMPONENT, sha


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def effective(run: dict) -> dict:
    line = next(line for line in reversed(run["effective"])
                if line.startswith("Q36_EFFECTIVE ") and "expert_store=" in line)
    return {key: value for key, value in re.findall(r"(\w+)=([^\s]+)", line) if key != "generation"}


def main() -> None:
    destination = OUT / "qualification-summary.json"
    assert not destination.exists()
    manifest = load("component/0.5.2-windows-x86_64-cuda-cuda13/engine-component.json")
    package = load("package-receipt.json")
    assert sha(COMPONENT / "engine-component.json") == package["manifestSHA256"]
    assert manifest["signature"] is None
    names = sorted(p.relative_to(COMPONENT).as_posix() for p in COMPONENT.rglob("*") if p.is_file())
    assert names == sorted([row["path"] for row in manifest["files"]] + ["engine-component.json"])
    for row in manifest["files"]:
        path = COMPONENT / row["path"]
        assert path.stat().st_size == row["bytes"] and sha(path) == row["sha256"]
    subprocess.run([str(NODE), "--input-type=module", "-e",
        "import {verifyEngine,verifyNativeBuild} from './apps/host/scripts/release-integrity.mjs';"
        "const folder=process.argv[1];const m=verifyEngine(folder,'0.5.2');"
        "verifyNativeBuild(folder,process.cwd(),m);console.log('final native source/artifact binding passed');",
        str(COMPONENT)], check=True, cwd=ROOT, timeout=60)
    a, restart, b = [load(name + ".json") for name in
                     ("q36-bounded-first", "q36-bounded-restart", "q36-mapped-legacy")]
    assert all(run["passed"] and run["modelFilesPreserved"] and run["exitCode"] == 0
               for run in (a, restart, b))
    assert a["modelFilesBefore"] == b["modelFilesAfter"] == restart["modelFilesAfter"]
    args_a, args_b = a["args"][:], b["args"][:]
    args_a[args_a.index("--q36-memory") + 1] = args_b[args_b.index("--q36-memory") + 1] = "MODE"
    assert args_a == args_b and a["inputIds"] == b["inputIds"]
    assert a["exeSHA256"] == b["exeSHA256"] == restart["exeSHA256"]
    comparison = []
    fields = ("submittedCount", "nativePromptCount", "nativeFreshReadCount", "nativeReuseCount",
              "generatedCount", "generatedIds", "finish")
    assert [r["name"] for r in a["requests"]] == [r["name"] for r in b["requests"]]
    for left, right in zip(a["requests"], b["requests"]):
        comparison.append({"name": left["name"], "countsTokensFinishEqual": all(left[k] == right[k] for k in fields)})
    suite = load("suite.json")
    passed, failed = [], []
    for row in suite["cases"]:
        ok = row["passed"] and row.get("reports052", True) and row.get("memoryMarker", True) and row.get("kvMarker", True)
        (passed if ok else failed).append(row["name"])
    cache = (BUILD / "CMakeCache.txt").read_text()
    options = dict(re.findall(r"^([A-Za-z0-9_]+):[^=]+=(.*)$", cache, re.MULTILINE))
    expected = {"CMAKE_PROJECT_VERSION": "0.5.2", "CMAKE_CUDA_ARCHITECTURES": "120",
                "STRATA_GGML_DIR": "H:/Strata/deps/ggml-3cf03257", "STRATA_CUDA_SPILL_BASELINE": ""}
    expected.update({name: "ON" for name in ("STRATA_PORTABLE", "STRATA_ENABLE_CUDA", "STRATA_NATIVE_EXPERTS",
        "STRATA_ENABLE_SPIN8", "STRATA_ENABLE_NATIVE_CACHE", "STRATA_NATIVE_CACHE_OWNER", "STRATA_MMQ_KQUANTS",
        "STRATA_MMQ_TQ_OVERLAY", "STRATA_BUILD_TESTS")})
    expected.update({name: "OFF" for name in ("STRATA_BUILD_DSV41", "STRATA_BUILD_SPLIT", "STRATA_PREFILL_MMQ")})
    assert all(options[key].strip().replace("\\", "/") == value for key, value in expected.items())
    source = load("build-source-r2.json")
    dependency = "H:/Strata/deps/ggml-3cf03257"
    assert subprocess.check_output(["git", "-C", dependency, "rev-parse", "HEAD"], text=True).strip() == source["ggmlCommit"]
    assert not subprocess.check_output(["git", "-C", dependency, "status", "--porcelain"], text=True).strip()
    receipts = {p.stem: json.loads(p.read_text()) for p in (OUT / "receipts").glob("*.json")
                if p.stem != "final-artifact-audit"}
    assert all("run" in r for r in receipts.values())
    result = {"buildIntegrityPassed": True, "releaseQualified": False, "signed": False, "installed": False,
              "sourceCommit": source["commit"], "ggmlCommit": source["ggmlCommit"],
              "nativeSourcesCount": len(load("native-build/Release/native-build.json")["sources"]),
              "build": str(BUILD), "component": str(COMPONENT), "manifestSHA256": package["manifestSHA256"],
              "nativeOnlyManifestSHA256": sha(OUT / "native-component/0.5.2-windows-x86_64-cuda-cuda13/engine-component.json"),
              "binaries": {r["path"]: r for r in manifest["files"] if r["path"] in ("strata.exe", "strata-q36.exe", "native-build.json")},
              "cudaRuntimeIdentitiesMatchToolkit": all(sha(COMPONENT / name) == sha(CUDA / "bin/x64" / name)
                  for name in ("cublas64_13.dll", "cublasLt64_13.dll")),
              "suitePassed": passed, "suiteFailed": failed, "suiteSkipped": [],
              "models": {name: {k: run[k] for k in ("passed", "readySeconds", "maxWorkingSetBytes", "maxPrivateBytes",
                  "minAvailableRamBytes", "minCommitHeadroomBytes", "exitCode", "modelFilesPreserved")}
                  for name, run in (("boundedFirst", a), ("boundedRestart", restart), ("mappedLegacy", b))},
              "sameEffectiveSettings": effective(a) == effective(b), "comparison": comparison,
              "comparisonLimit": "One short synthetic prompt, 5/6 actual input tokens; cold/warm startup differs. No throughput or full-window quality qualification.",
              "guardCleanupConfirmed": all(r["run"]["termination_confirmed"] for r in receipts.values()),
              "resourceFloorStops": [name for name, r in receipts.items() if r["run"]["status"] == "RESOURCE_PRESSURE" or r["run"].get("observer_reason") == "C_disk_floor"],
              "cudaResourceGuard": receipts["cuda-resource-guard"], "recipe": expected}
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
