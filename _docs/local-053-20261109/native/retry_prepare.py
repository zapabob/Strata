"""Inspect the specific pre-compile parser failure; rename its entire BASE only with --execute."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import BASE, freeze, no_links, passed_run, read_json, require, sha


def inspect(root: Path, commit: str) -> dict:
    """Read-only eligibility check. Old adapter hashes intentionally remain historical evidence."""
    destination = BASE.with_name(BASE.name + "-configure-failed-r1")
    no_links(BASE)
    no_links(destination)
    require(BASE.is_dir() and not destination.exists(), "Existing BASE and fresh sibling destination required")
    require(not (BASE / "active.json").exists(), "An active/unconfirmed controller lock blocks retry preparation")
    identity = freeze(root, commit)
    paths = {name: BASE / name for name in ("freeze.json", "build-source.json",
             "receipts/build-phase.json", "receipts/build-configure.json", "receipts/build-phase.txt")}
    for path in paths.values():
        no_links(path)
        require(path.is_file(), f"Missing retained evidence: {path.name}")
    phase = read_json(paths["receipts/build-phase.json"])
    configured = read_json(paths["receipts/build-configure.json"])
    run = phase.get("run", {})
    require(phase.get("passed") is False and run.get("status") == "FINISHED"
            and run.get("native_exit_code") == 1 and run.get("exit_code") == 1
            and run.get("native_exit_code_observation") == "OBSERVED_BEFORE_CLEANUP"
            and run.get("contained_before_resume") is True and run.get("termination_confirmed") is True
            and run.get("job_active_after") == 0 and run.get("observed_dropped_bytes") == 0,
            "Retained first build must be failed with observed exit 1 and confirmed empty owned Job")
    require(configured.get("passed") is True and passed_run(configured.get("run", {})),
            "Retained configure must have passed with exit zero and confirmed empty owned Job")
    require(paths["receipts/build-phase.txt"].read_text(encoding="utf-8").strip()
            == "BLOCKED/FAIL: RuntimeError: CMake recipe drift: CMAKE_CUDA_ARCHITECTURES",
            "Only the specific pre-compile cache-parser failure is eligible")
    for record in (read_json(paths["freeze.json"]), read_json(paths["build-source.json"]), phase.get("frozenIdentity", {})):
        for key in ("sourceRoot", "sourceCommit", "ggmlRoot", "ggmlCommit", "helpers"):
            require(record.get(key) == identity[key], f"Retained source identity mismatch: {key}")
    for relative in ("native-build/Release/strata.exe", "native-build/Release/strata-q36.exe",
                     "native-build/Release/native-build.json", "receipts/build-helper.json",
                     "receipts/build-helper.txt", "results/build.json", "native-component", "app"):
        require(not (BASE / relative).exists(), f"Post-configure/shared-lane output blocks retry: {relative}")
    require((BASE / "native").is_dir() and not any((BASE / "native").iterdir()), "Native stage must still be empty")
    return {"eligible": True, "sourceRoot": str(root), "sourceCommit": commit,
            "base": str(BASE), "destination": str(destination),
            "evidenceSHA256": {name: sha(path) for name, path in paths.items()}}


def prepare(root: Path, commit: str, *, execute: bool = False) -> dict:
    report = inspect(root, commit)
    report["renamed"] = False
    if execute:
        # Recheck the receipts and empty-Job/no-output conditions immediately before the Windows rename.
        require(inspect(root, commit) == {key: value for key, value in report.items() if key != "renamed"},
                "Retained evidence changed during retry preparation")
        destination = Path(report["destination"])
        require(not destination.exists(), "Never replace an existing retained attempt")
        BASE.rename(destination)  # Same-parent Windows directory rename; no copying or evidence edits.
        report["renamed"] = True
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--reviewed-commit", required=True)
    parser.add_argument("--execute", action="store_true", help="Parent authorises whole-BASE evidence-preserving rename only")
    args = parser.parse_args()
    no_links(args.source_root)
    print(json.dumps(prepare(args.source_root.resolve(), args.reviewed_commit, execute=args.execute), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
