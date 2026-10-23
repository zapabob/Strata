"""Run a pinned Prism child without inherited LLAMA_ARG_* overrides.

The parent environment is never changed. Receipts expose removed names only.
Explicit command-line cache choices are preserved.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Mapping, Sequence


def library_receipts(output: str) -> list[dict[str, object]]:
    """Hash the concrete module paths emitted by the native provenance probe."""
    libraries = []
    for line in output.splitlines():
        if line.startswith("dependency="):
            path = Path(line.removeprefix("dependency="))
            libraries.append({"path": str(path), "bytes": path.stat().st_size,
                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return libraries


def controlled_environment(
    source: Mapping[str, str] | None = None,
) -> tuple[dict[str, str], list[str]]:
    """Copy the environment, omitting both empty and populated argument keys."""
    original = os.environ if source is None else source
    removed = sorted(key for key in original if key.upper().startswith("LLAMA_ARG_"))
    return {key: value for key, value in original.items() if key not in removed}, removed


def run_child(command: Sequence[str], *, timeout: float = 60) -> dict[str, object]:
    """Capture a bounded child execution with an explicit sanitized environment."""
    environment, removed = controlled_environment()
    try:
        result = subprocess.run(
            command, env=environment, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout, check=False,
        )
        receipt = {"returncode": result.returncode, "removedNames": removed,
                   "stdout": result.stdout, "stderr": result.stderr, "timedOut": False}
    except subprocess.TimeoutExpired as error:
        def text(value: str | bytes | None) -> str:
            return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""
        receipt = {"returncode": 124, "removedNames": removed, "timedOut": True,
                   "stdout": text(error.stdout), "stderr": text(error.stderr)}
    receipt["libraries"] = library_receipts(str(receipt["stdout"]))
    return receipt


def main() -> int:
    """CLI for build version probes and controlled model-test subprocesses."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a child command is required")
    receipt = run_child(command, timeout=args.timeout)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return int(receipt["returncode"])


if __name__ == "__main__":
    raise SystemExit(main())
