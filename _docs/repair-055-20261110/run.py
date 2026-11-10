"""Fresh repair diagnostics with historical guard/floors; explicit commands only."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path("H:/Strata/releases/repair-055-20261110-opencode")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--seconds", type=int, default=300)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not args.execute:
        print(json.dumps({"execute": False, "out": str(OUT), "name": args.name, "command": command}))
        return 0
    if not command or command[0] not in ("node", "python"):
        parser.error("An explicit Python or Node driver is required")
    if not OUT.parent.is_dir():
        parser.error("Approved H: release parent missing")
    OUT.mkdir(exist_ok=True)
    for name in ("receipts", "temp", "cache"):
        (OUT / name).mkdir(exist_ok=True)
    spec = importlib.util.spec_from_file_location("repair_guard", ROOT / "_docs/local-053-20261109/native/common.py")
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    guard.BASE = OUT
    command[0] = str(guard.NODE) if command[0] == "node" else sys.executable
    for i, part in enumerate(command[1:], 1):
        if part.startswith(("_docs/", "apps/", "tools/")) and (ROOT / part).is_file():
            command[i] = str(ROOT / part)
    env = guard.environment()
    env.update(CARGO_BUILD_JOBS="5", CMAKE_BUILD_PARALLEL_LEVEL="5", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    result = guard.owned(ROOT, args.name, command, args.seconds, env=env, output_bytes=32 * 1024**2)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        print(guard.text(args.name))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
