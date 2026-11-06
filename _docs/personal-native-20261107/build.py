"""Fresh one-job source-bound build; invoked only inside the owned resource guard."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from guard import ROOT, OUT, NODE


def main() -> None:
    build = OUT / "native-build"
    assert OUT.is_dir() and not build.exists(), "Never reuse a compiled output directory"
    dependency = Path("H:/Strata/deps/ggml-3cf03257")
    pin = subprocess.check_output(["git", "-C", str(dependency), "rev-parse", "HEAD"], text=True).strip()
    assert pin == "3cf03257f219afbe7334045ff7c6a06ac68c627d"
    assert not subprocess.check_output(["git", "-C", str(dependency), "status", "--porcelain"], text=True).strip()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert not subprocess.check_output(["git", "status", "--porcelain", "--", "CMakeLists.txt", "src", "include", "cmake", "spin8", "tqcodec"], cwd=ROOT, text=True).strip()
    command = ["cmake", "-S", str(ROOT), "-B", str(build), "-G", "Visual Studio 17 2022",
               "-A", "x64", "-T", "cuda=13.3", "-DCMAKE_CUDA_ARCHITECTURES=120",
               "-DSTRATA_GGML_DIR=" + str(dependency),
               "-DSTRATA_PORTABLE=ON", "-DSTRATA_ENABLE_CUDA=ON", "-DSTRATA_NATIVE_EXPERTS=ON",
               "-DSTRATA_ENABLE_SPIN8=ON", "-DSTRATA_ENABLE_NATIVE_CACHE=ON", "-DSTRATA_NATIVE_CACHE_OWNER=ON",
               "-DSTRATA_MMQ_KQUANTS=ON", "-DSTRATA_MMQ_TQ_OVERLAY=ON", "-DSTRATA_BUILD_TESTS=ON",
               "-DSTRATA_BUILD_DSV41=OFF", "-DSTRATA_BUILD_SPLIT=OFF", "-DSTRATA_PREFILL_MMQ=OFF",
               "-DSTRATA_CUDA_SPILL_BASELINE="]
    (OUT / "build-source.json").write_text(json.dumps({"commit": commit, "ggmlCommit": pin, "configure": command}, indent=2) + "\n")
    subprocess.run(command, check=True, cwd=ROOT)
    subprocess.run([str(NODE), str(ROOT / "tools/build_hakua_engine.mjs"), str(build), "1"], check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
