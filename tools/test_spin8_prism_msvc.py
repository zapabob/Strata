"""Real Ninja header-change regression, run inside the disposable VS child."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--ninja", required=True)
    args = parser.parse_args()
    args.evidence.mkdir(exist_ok=False)
    launcher = Path(__file__).with_name("spin8_prism_msvc.py").as_posix()
    (args.evidence / "CMakeLists.txt").write_text(
        'cmake_minimum_required(VERSION 3.20)\nproject(dependency_probe CXX)\n'
        'set(CMAKE_CL_SHOWINCLUDES_PREFIX "メモ: インクルード ファイル: ")\n'
        f'set(CMAKE_CXX_COMPILER_LAUNCHER "{Path(sys.executable).as_posix()};{launcher}")\n'
        'add_executable(probe main.cpp)\n', encoding="utf-8")
    (args.evidence / "main.cpp").write_text('#include "config.h"\nint main() { return VALUE; }\n', encoding="utf-8")
    header = args.evidence / "config.h"
    header.write_text("#define VALUE 1\n", encoding="utf-8")
    build = args.evidence / "build"

    def run(label: str, command: list[str], expected: int = 0) -> str:
        result = subprocess.run(command, capture_output=True, timeout=120, check=False)
        (args.evidence / (label + ".stdout.bin")).write_bytes(result.stdout)
        (args.evidence / (label + ".stderr.bin")).write_bytes(result.stderr)
        if result.returncode != expected:
            raise RuntimeError(f"{label}: expected {expected}, got {result.returncode}")
        return result.stdout.decode("utf-8", errors="replace")

    run("configure", ["cmake", "-S", str(args.evidence), "-B", str(build), "-G", "Ninja", f"-DCMAKE_MAKE_PROGRAM={args.ninja}"])
    run("build-first", ["cmake", "--build", str(build), "--parallel", "1"])
    run("value-first", [str(build / "probe.exe")], 1)
    deps = run("dependencies", [args.ninja, "-C", str(build), "-t", "deps"])
    assert "config.h" in deps and "#deps 0" not in deps
    header.write_text("#define VALUE 2\n", encoding="utf-8")
    rebuilt = run("build-header-change", ["cmake", "--build", str(build), "--parallel", "1"])
    assert "main.cpp.obj" in rebuilt
    run("value-second", [str(build / "probe.exe")], 2)
    unchanged = run("build-unchanged", ["cmake", "--build", str(build), "--parallel", "1"])
    assert "no work to do" in unchanged
    (args.evidence / "invalid.cpp").write_text("#error EXPECTED_COMPILER_FAILURE\n", encoding="utf-8")
    result = subprocess.run([sys.executable, launcher, "cl", "/nologo", "/c", str(args.evidence / "invalid.cpp")], capture_output=True, timeout=30, check=False)
    (args.evidence / "expected-failure.bin").write_bytes(result.stdout + result.stderr)
    assert result.returncode != 0 and b"EXPECTED_COMPILER_FAILURE" in result.stdout
    (args.evidence / "result.json").write_text(json.dumps({"passed": True, "headerRebuild": True, "compilerFailureExit": result.returncode}), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
