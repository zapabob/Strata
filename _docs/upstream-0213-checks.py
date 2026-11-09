"""Run one source check with retained output, resource floors and an owned Job."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
OUT = Path("H:/Strata/releases/upstream-0213-20261109-opencode")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--seconds", type=int, default=300)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or command[0] not in ("python", "node"):
        parser.error("An explicit python or node source check is required")
    if not OUT.is_dir():
        raise ValueError("Existing approved output root is required")
    spec = importlib.util.spec_from_file_location("native_check_guard", ROOT / "_docs/local-053-20261109/native/common.py")
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    # Operational output override only; the frozen historical helper is intact.
    guard.BASE = OUT
    (OUT / "receipts").mkdir(exist_ok=True)
    (OUT / "temp").mkdir(exist_ok=True)
    command[0] = sys.executable if command[0] == "python" else str(guard.NODE)
    # The owned Job starts in its output root, not in the checkout.
    for index, value in enumerate(command):
        if value.startswith("_docs/") and (ROOT / value).is_file():
            command[index] = str(ROOT / value)
    env = guard.environment()
    env.update(CARGO_BUILD_JOBS="5", CMAKE_BUILD_PARALLEL_LEVEL="5", PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    result = guard.owned(ROOT, args.name, command, args.seconds, env=env, output_bytes=16 * 1024**2)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        print(guard.text(args.name))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
