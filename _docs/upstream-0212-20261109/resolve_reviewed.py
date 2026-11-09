"""Resolve only the reviewed conflicts of the pinned 0.2.12 integration.

Run the repository's merge_upstream_fork.py first with --no-commit and the pinned
upstream SHA. Default is a read-only plan; --execute writes/stages these hunks.
Unconflicted upstream edits and unrelated working-tree text are retained.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BEFORE = "dce71248c61992a9ba1e8af99711c2eccc795f4e"
UPSTREAM = "146df3c468739147f520ac3816de806f71232571"
CHOICES = {
    "AGENTS.md": ("ours",),
    "CMakeLists.txt": ("ours",),
    "apps/desktop/package.json": ("ours",),
    "apps/desktop/src-tauri/Cargo.lock": ("ours",),
    "apps/desktop/src-tauri/Cargo.toml": ("ours",),
    "apps/host/package-lock.json": ("ours", "ours"),
    "apps/host/package.json": ("ours",),
    "apps/host/server/native-gateway.mjs": ("gateway",),
    "apps/host/tests/qa1-storage.test.mjs": ("ours",),
    "metal/CMakeLists.txt": ("ours",),
    "serve/server.py": ("accounting-and-private-debug",),
    "strata_cli/__init__.py": ("ours",),
    "tests/terminal/test_tui2_023_old_launcher.py": ("ours",),
    "tests/terminal/test_tui2_023_versions.py": ("ours", "ours"),
    "tools/check_isa_guard.py": ("ours", "theirs", "ours", "ours", "ours"),
}
CONFLICT = re.compile(
    r"^<<<<<<< HEAD\n(.*?)^=======\n(.*?)^>>>>>>> " + UPSTREAM + r"\n",
    re.MULTILINE | re.DOTALL,
)


def git(*args: str) -> str:
    """Use this worktree's index; never choose the installed application tree."""
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8", timeout=60
    ).strip()


def combine(ours: str, theirs: str, choice: str) -> str:
    """Retain fork boundaries while adopting the official entry points."""
    if choice == "ours":
        return ours
    if choice == "theirs":
        return theirs
    if choice == "gateway":
        # Keep private-consent refusal and timeout-aware inferenceFetch. Use the
        # official /v1/messages single-loaded-model resolver, not a second router.
        if "inferenceFetch" not in ours or "strata_memory" not in ours:
            raise ValueError("Unrecognised fork gateway boundary")
        return (
            ours[: ours.index(" let instance;")]
            + theirs[theirs.index(" let instance;") :]
        )
    if choice == "accounting-and-private-debug":
        if (
            not theirs.startswith("def prefill_leg_stats(")
            or "private=False" not in ours
        ):
            raise ValueError("Unrecognised accounting/debug conflict")
        return theirs[: theirs.index("def _debug_req(")] + ours
    raise ValueError("Unreviewed resolution")


def main() -> None:
    """Validate both parents and the complete conflict set before any write."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if git("rev-parse", "HEAD") != BEFORE or git("rev-parse", "MERGE_HEAD") != UPSTREAM:
        raise ValueError("Pinned merge parents differ")
    unmerged = set(
        git("diff", "--name-only", "--diff-filter=U", "-z").strip("\0").split("\0")
    )
    if unmerged != set(CHOICES):
        raise ValueError("Conflict set differs from reviewed 15 files")
    outputs = {}
    receipt = {
        "before": BEFORE,
        "upstream": UPSTREAM,
        "execute": args.execute,
        "files": {},
    }
    for name, choices in CHOICES.items():
        text = (ROOT / name).read_text(encoding="utf-8")
        matches = list(CONFLICT.finditer(text))
        if len(matches) != len(choices):
            raise ValueError("Conflict count differs: " + name)
        parts = []
        start = 0
        for match, choice in zip(matches, choices):
            parts.extend(
                (text[start : match.start()], combine(*match.groups(), choice))
            )
            start = match.end()
        parts.append(text[start:])
        resolved = "".join(parts)
        if re.search(r"^(?:<<<<<<<|=======|>>>>>>>)", resolved, re.MULTILINE):
            raise ValueError("Conflict marker remains: " + name)
        outputs[name] = resolved
        receipt["files"][name] = {
            "choices": choices,
            "before_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "resolved_sha256": hashlib.sha256(resolved.encode()).hexdigest(),
        }
    if args.execute:
        for name, text in outputs.items():
            (ROOT / name).write_text(text, encoding="utf-8", newline="\n")
        git("add", "--", *outputs)
    logging.info("%s", json.dumps(receipt, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
