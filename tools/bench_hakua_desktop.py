#!/usr/bin/env python3
"""Sample host resources for Hakua desktop validation (T7). No keys or prompts are stored.

Usage:
  py -3 tools/bench_hakua_desktop.py
  py -3 tools/bench_hakua_desktop.py --out _docs/bench-sample.jsonl
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def nvidia_query():
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,uuid,memory.total,memory.used,memory.free,driver_version",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": "unknown", "reason": str(exc), "gpus": []}
    gpus = []
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 6:
            continue
        gpus.append(
            {
                "name": parts[0],
                "uuid": parts[1],
                "memory_total_mib": _num(parts[2]),
                "memory_used_mib": _num(parts[3]),
                "memory_free_mib": _num(parts[4]),
                "driver": parts[5],
            }
        )
    return {"status": "ok" if gpus else "unknown", "gpus": gpus}


def _num(value: str):
    try:
        return float(value)
    except ValueError:
        return None


def disk_free(path: Path):
    try:
        usage = shutil.disk_usage(path)
        return {"status": "ok", "total": usage.total, "used": usage.used, "free": usage.free}
    except OSError as exc:
        return {"status": "unknown", "reason": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None, help="Append one JSONL record")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    record = {
        "at": datetime.now(timezone.utc).isoformat(),
        "gpu": nvidia_query(),
        "disk_root": disk_free(args.root),
        "note": "Resource sample only. Pair with turnId/requestId from the host for timing.",
    }
    line = json.dumps(record, ensure_ascii=False)
    print(line)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
