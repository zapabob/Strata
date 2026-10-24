#!/usr/bin/env python3
"""tools/generate_changes_csv.py - Classify upstream changes between U0 and U1."""
import csv
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_INTAKE = REPO_ROOT / "_docs" / "upstream-intake"

U0 = "011c9e600a93bbc9fd451c563501b5831c32bbca"
U1 = "7dd5cf18e68c639a8773e096c5c79f971ea2a9f5"

def run_git(args):
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout

def main():
    raw_diff = run_git(["diff", "--name-status", U0, U1]).splitlines()
    rows = []
    for line in raw_diff:
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        status, file_path = parts
        
        # Classification category:
        # APPLIED_UPSTREAM: cleanly merges into upstream/new feature
        # ADAPTED_EQUIVALENT: modified to preserve fork invariants F01-F11
        # NOT_APPLICABLE: platform-specific (e.g. non-Windows) or superseded
        # BLOCKED: requires deep review
        if file_path.startswith("README"):
            cat = "ADAPTED_EQUIVALENT"
            notes = "Fork-specific multi-language README preserved"
        elif file_path == "src/program/generate.cpp":
            cat = "ADAPTED_EQUIVALENT"
            notes = "Preserve spin8/triality/tq generation hooks while adopting upstream fixes"
        elif file_path.startswith("src/dsv41/") or file_path.startswith("tools/dsv41/"):
            cat = "APPLIED_UPSTREAM"
            notes = "DeepSeek-V4.1-Flash official backend and packing tools"
        elif file_path.startswith("apps/host/"):
            cat = "APPLIED_UPSTREAM"
            notes = "Upstream UI/host enhancements"
        elif "security" in file_path.lower() or file_path == "SECURITY.md":
            cat = "APPLIED_UPSTREAM"
            notes = "Upstream security hardening"
        else:
            cat = "APPLIED_UPSTREAM"
            notes = "Upstream baseline update"

        rows.append({
            "status": status,
            "path": file_path,
            "classification": cat,
            "notes": notes
        })

    out_csv = DOCS_INTAKE / "changes.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["status", "path", "classification", "notes"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} entries in {out_csv}")

if __name__ == "__main__":
    main()
