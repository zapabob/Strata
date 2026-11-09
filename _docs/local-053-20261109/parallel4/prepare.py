"""Preserve completed failed single-job evidence and admit an explicit four-job resume.

The configured build/intermediate paths stay fixed. No source, allowance, model,
process or installed app is modified here. Default is read-only inspection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "native"))
from common import BASE, BUILD, admit, freeze, git, no_links, read_json, require, save
from phases import validate_cache


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--reviewed-commit", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    root = args.source_root.resolve()
    no_links(BASE)
    require(not (BASE / "active.json").exists(), "Prior owned Job must finish first")
    previous = read_json(BASE / "freeze.json")
    job = read_json(BASE / "receipts/build-phase.json")
    result = job["run"]
    require(job["passed"] is False and result["status"] == "FINISHED"
            and result["native_exit_code"] == 1 and result["termination_confirmed"] is True
            and result["job_active_after"] == 0, "Retained completed failed build required")
    require((BUILD / "Release/strata.exe").is_file()
            and (BUILD / "Release/strata-q36.exe").is_file(), "Expected retained release binaries missing")
    require(Path(previous["sourceRoot"]) == root, "Reuse requires identical source path")
    native_changes = git(root, "diff", "--name-only", previous["sourceCommit"], args.reviewed_commit,
                         "--", "CMakeLists.txt", "src", "include", "spin8", "tqcodec", "tests")
    require(native_changes == "tests/core/flag_order_test.cu", "Only reviewed test portability fix may reuse this build")
    identity = freeze(root, args.reviewed_commit)
    validate_cache(root, record=False)
    archive = BASE / "attempts/single-job-build-r2"
    require(not archive.exists(), "Never replace prior attempt evidence")
    report = {"eligible": True, "previousSource": previous["sourceCommit"],
              "sourceCommit": args.reviewed_commit, "parallelism": 4,
              "retainedBuild": str(BUILD), "archive": str(archive), "executed": args.execute}
    if args.execute:
        admit(root)
        archive.mkdir(parents=True)
        for name in ("receipts", "results", "native", "freeze.json", "build-source.json"):
            (BASE / name).rename(archive / name)
        for name in ("receipts", "results", "native"):
            (BASE / name).mkdir()
        validate_cache(root)
        save(BASE / "freeze.json", identity, fresh=True)
        save(BASE / "four-job-resume.json", report, fresh=True)
        save(BASE / "build-source-parallel4.json", {
            **identity, "parallelism": 4, "reusedObjectsFromSource": previous["sourceCommit"],
            "previousFreezeSHA256": hashlib.sha256((archive / "freeze.json").read_bytes()).hexdigest(),
            "nativeSourceChanges": native_changes.splitlines(),
        }, fresh=True)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
