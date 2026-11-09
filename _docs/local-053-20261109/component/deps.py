"""Bounded read-only production PE dependency checks; invoked only by the owned worker."""
from __future__ import annotations

import argparse
from pathlib import Path

from core import NAME, RESOURCES, WORK, check_dependencies, production_modules, require


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    require(args.folder in (WORK / "unsigned" / NAME, WORK / "pending-engine-bundle" / NAME,
                            RESOURCES / "engine-bundle" / NAME), "Explicit managed dependency scope required")
    _, _, deps = production_modules()
    check_dependencies(args.folder, deps)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit("Production dependency verification failed; raw error suppressed") from None
