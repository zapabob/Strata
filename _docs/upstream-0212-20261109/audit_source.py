"""Check the pinned merge's incoming Git contents and untouched fork anchors.

This is source/intake evidence only, not runtime or security qualification.
Optional JSON output must be fresh; no commit or publication is performed.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import logging
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = "146df3c468739147f520ac3816de806f71232571"
BASE = "9f7d977d220e9fdf2ec53cf2620cdadac1cfb24e"
BEFORE = "dce71248c61992a9ba1e8af99711c2eccc795f4e"
PROTECTED = (
    "spin8",
    "tqcodec",
    "adapters/upstream",
    "serve/memory_harness.py",
    "serve/llama_memory.py",
    "serve/native_family.py",
    "strata_control/update_keys.json",
    "apps/host/server/memory.mjs",
    "apps/host/server/q36-run-contract.mjs",
    "apps/host/server/q36-kv-capabilities.mjs",
    "src/qwen35",
    "include/strata/qwen35",
    "tools/qwen35_absent_mtp.patch",
    "packaging/full_windows.py",
)


def git(*args: str, input_text: str | None = None) -> str:
    """Read this worktree through Git's own path/EOL rules."""
    result = subprocess.run(
        ["git", *args],
        input=input_text,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        timeout=60,
        stdout=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise ValueError("Git check failed: " + " ".join(args) + "\n" + result.stdout)
    return result.stdout


def main() -> None:
    """Refuse unresolved paths, whitespace errors or protected-source drift."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if git("rev-parse", "HEAD").strip() != BEFORE:
        raise ValueError("Fork parent changed")
    if git("rev-parse", "MERGE_HEAD").strip() != UPSTREAM:
        raise ValueError("Upstream parent changed")
    if git("ls-files", "-u").strip():
        raise ValueError("Unresolved merge entries")
    git("-c", "core.whitespace=cr-at-eol", "diff", "HEAD", "--check")
    if git("diff", "HEAD", "--name-only", "--", *PROTECTED).strip():
        raise ValueError("Untouched fork anchor changed")
    for name in PROTECTED:
        if not (ROOT / name).exists():
            raise ValueError("Missing fork anchor: " + name)
    names = git("diff", "--name-only", "-z", BASE, UPSTREAM).strip("\0").split("\0")
    upstream = {}
    for record in (
        git("ls-tree", "-r", "-z", UPSTREAM, "--", *names).strip("\0").split("\0")
    ):
        metadata, name = record.split("\t", 1)
        upstream[name] = metadata.split()[2]
    hashes = git(
        "hash-object", "--stdin-paths", input_text="\n".join(names) + "\n"
    ).splitlines()
    if len(hashes) != len(names):
        raise ValueError("Incomplete incoming inventory")
    rows = [
        {
            "path": name,
            "upstream_blob": upstream[name],
            "merged_blob": digest,
            "classification": (
                "APPLIED_UPSTREAM" if upstream[name] == digest else "ADAPTED_FORK"
            ),
        }
        for name, digest in zip(names, hashes)
    ]
    report = {
        "fork_parent": BEFORE,
        "upstream_parent": UPSTREAM,
        "upstream_base": BASE,
        "merge_conflicts": 0,
        "protected_git_contents_unchanged": list(PROTECTED),
        "counts": dict(Counter(row["classification"] for row in rows)),
        "incoming_files": rows,
        "runtime_qualified": False,
    }
    if args.output:
        if not args.output.parent.is_dir():
            raise ValueError("Output parent missing")
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2)
            stream.write("\n")
    logging.info(
        "Incoming files: %d; %s; unchanged fork anchors: %d; unresolved: 0",
        len(rows),
        report["counts"],
        len(PROTECTED),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
