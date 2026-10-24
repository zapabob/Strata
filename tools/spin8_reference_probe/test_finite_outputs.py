"""Inject non-finite SPIN8_OK outputs into the actual probe control flow."""

import argparse
import logging
from pathlib import Path
import subprocess


def main() -> int:
    """Require explicit rejection at every trial/extended/block output stage."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    scopes = [
        f"trial-{dtype}-{direction}"
        for dtype in ("f64", "f32")
        for direction in ("forward", "inverse")
    ]
    scopes += [f"extended-f64-{direction}" for direction in ("forward", "inverse")]
    scopes += [
        f"block-{size}-{dtype}-{direction}"
        for size in (8, 16, 64, 128)
        for dtype in ("f64", "f32")
        for direction in ("forward", "inverse")
    ]
    failed = 0
    for scope in scopes:
        for value in ("nan", "inf"):
            output = args.output_dir / f"{scope}-{value}.json"
            command = [
                str(args.executable),
                scope,
                value,
                "--out",
                str(output),
                "--trials",
                "1",
                "--python-check",
                "1",
                "--seed",
                "20261023",
            ]
            result = subprocess.run(
                command, capture_output=True, text=True, check=False, timeout=30
            )
            (args.output_dir / f"{scope}-{value}.log").write_text(
                result.stdout + result.stderr, encoding="utf-8"
            )
            passed = (
                result.returncode == 2 and f"FAIL nonfinite {scope}" in result.stdout
            )
            logging.info(
                "%s %s %s exit=%s",
                "PASS" if passed else "FAIL",
                scope,
                value,
                result.returncode,
            )
            failed += not passed
    total = len(scopes) * 2
    logging.info(
        "Finite-output regressions: %s passed, %s failed", total - failed, failed
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
