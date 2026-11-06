"""Fresh one-job source-bound build; invoked only inside the owned resource guard."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from guard import ROOT, OUT, NODE


def main() -> None:
    build = OUT / "native-build"
    attempt = sys.argv[1] if len(sys.argv) == 2 else "r1"
    assert attempt in ("r1", "r2")
    if attempt == "r2":
        previous = json.loads((OUT / "receipts/native-build.json").read_text())
        assert not previous["passed"] and previous["run"]["termination_confirmed"]
        assert previous["run"]["status"] == "FINISHED" and previous["run"]["native_exit_code"] == 1
        assert not (build / "Release").exists(), "Only the failed configure may be retained this way"
        retained = OUT / "native-build-configure-failed-r1"
        assert build.is_dir() and not retained.exists()
        build.rename(retained)
    assert OUT.is_dir() and not build.exists(), "Never reuse a compiled output directory"
    dependency = Path("H:/Strata/deps/ggml-3cf03257")
    pin = subprocess.check_output(["git", "-C", str(dependency), "rev-parse", "HEAD"], text=True).strip()
    assert pin == "3cf03257f219afbe7334045ff7c6a06ac68c627d"
    assert not subprocess.check_output(["git", "-C", str(dependency), "status", "--porcelain"], text=True).strip()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert not subprocess.check_output(["git", "status", "--porcelain", "--", "CMakeLists.txt", "src", "include", "cmake", "spin8", "tqcodec"], cwd=ROOT, text=True).strip()
    command = ["cmake", "-S", str(ROOT), "-B", str(build), "-G", "Visual Studio 17 2022",
               "-A", "x64", "-T", "cuda=13.3", "-DCMAKE_CUDA_ARCHITECTURES=120",
               "-DCMAKE_GENERATOR_INSTANCE=C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools",
               "-DSTRATA_GGML_DIR=" + str(dependency),
               "-DSTRATA_PORTABLE=ON", "-DSTRATA_ENABLE_CUDA=ON", "-DSTRATA_NATIVE_EXPERTS=ON",
               "-DSTRATA_ENABLE_SPIN8=ON", "-DSTRATA_ENABLE_NATIVE_CACHE=ON", "-DSTRATA_NATIVE_CACHE_OWNER=ON",
               "-DSTRATA_MMQ_KQUANTS=ON", "-DSTRATA_MMQ_TQ_OVERLAY=ON", "-DSTRATA_BUILD_TESTS=ON",
               "-DSTRATA_BUILD_DSV41=OFF", "-DSTRATA_BUILD_SPLIT=OFF", "-DSTRATA_PREFILL_MMQ=OFF",
               "-DSTRATA_CUDA_SPILL_BASELINE="]
    with (OUT / ("build-source-" + attempt + ".json")).open("x") as record:
        record.write(json.dumps({"commit": commit, "ggmlCommit": pin, "configure": command}, indent=2) + "\n")
    subprocess.run(command, check=True, cwd=ROOT)
    subprocess.run([str(NODE), str(ROOT / "tools/build_hakua_engine.mjs"), str(build), "1"], check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
