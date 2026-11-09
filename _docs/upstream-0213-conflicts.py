"""Read-only, grouped inspection of unmerged Git paths; no source changes."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group", choices=("core", "docs", "tests", "config"))
    args = parser.parse_args()
    paths = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=U", "-z"],
        cwd=ROOT, check=True, capture_output=True,
    ).stdout.decode("utf-8").strip("\0").split("\0")
    for name in paths:
        group = (
            "docs" if name.endswith(".md") else
            "tests" if "test" in name else
            "config" if name.endswith((".json", ".lock", ".toml"))
            or name in (".gitattributes", "CMakeLists.txt", "metal/CMakeLists.txt", "strata_cli/__init__.py") else
            "core"
        )
        if group != args.group:
            continue
        text = (ROOT / name).read_text(encoding="utf-8")
        print(f"\n=== {name} ===")
        matches = list(re.finditer(r"^<<<<<<< .*?^>>>>>>> .*?$", text, re.M | re.S))
        for number, match in enumerate(matches, 1):
            line = text[:match.start()].count("\n") + 1
            print(f"--- conflict {number} at line {line} ---")
            print(text[max(0, text.rfind("\n", 0, max(0, match.start() - 300)) + 1):match.end() + 300])


if __name__ == "__main__":
    main()
