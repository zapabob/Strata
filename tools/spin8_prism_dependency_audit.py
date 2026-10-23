"""Audit retained NVCC object dependencies against every composed-patch header."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cache = (args.build / "CMakeCache.txt").read_text(encoding="utf-8")
    ninja = re.search(r"^CMAKE_MAKE_PROGRAM:FILEPATH=(.+)$", cache, re.M).group(1)
    raw = subprocess.check_output([ninja, "-C", str(args.build), "-t", "deps"])
    text = raw.decode("utf-8").replace("\r\n", "\n")
    changed = subprocess.check_output(["git", "-C", str(args.source), "diff", "HEAD", "--name-only"], text=True).splitlines()
    headers = {(args.source / name).resolve().as_posix().lower() for name in changed if Path(name).suffix in (".h", ".hpp", ".cuh")}
    records = []
    for block in text.split("\n\n"):
        lines = block.splitlines()
        if not lines or ".cu.obj:" not in lines[0]:
            continue
        name, count = re.match(r"(.+): #deps (\d+),", lines[0]).groups()
        deps = {os.path.abspath(args.build / line.strip()).replace(chr(92), "/").lower() for line in lines[1:] if line.strip()}
        overlap = sorted(headers & deps)
        obj = args.build / name
        stale = [header for header in overlap if Path(header).stat().st_mtime_ns > obj.stat().st_mtime_ns]
        records.append({"object": name, "count": int(count), "changedHeaders": overlap, "staleHeaders": stale})
    rules = (args.build / "build.ninja").read_text(encoding="utf-8")
    expected = {name.replace("\\", "/") for name in re.findall(r"^build (.+\.cu\.obj): CUDA_COMPILER", rules, re.M)}
    missing = sorted(expected - {row["object"] for row in records})
    result = {"headers": sorted(headers), "cudaObjects": records, "missingObjects": missing,
              "passed": bool(records) and not missing and all(row["count"] > 0 and not row["staleHeaders"] for row in records)}
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "cudaObjects": len(records), "affectedCount": sum(bool(row["changedHeaders"]) for row in records)}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
