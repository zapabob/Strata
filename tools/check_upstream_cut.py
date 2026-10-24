#!/usr/bin/env python3
"""tools/check_upstream_cut.py - Verify upstream cut SHAs and repository integration state.
Strictly conforms to MILSPEC-Codex standard: logging only, zero print, strict types, error resilience.
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [strata.upstream_cut] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("strata.upstream_cut")

EXPECTED_U1_SHA = "7dd5cf18e68c639a8773e096c5c79f971ea2a9f5"
EXPECTED_C1_SHA = "c487c875d05075113965bc61d822b27179f70639"
EXPECTED_F0_SHA = "ddc8f9e19cafb981ed91caaab0992ca814e6eca9"


def run_git(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    """Execute git command and return result."""
    return subprocess.run(
        ["git"] + cmd,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        timeout=15
    )


def verify_upstream_cut() -> Dict[str, Any]:
    """Verify integration branch HEAD incorporates U1, C1, and preserves F01-F11."""
    # 1. Get current HEAD SHA
    proc_head = run_git(["rev-parse", "HEAD"])
    head_sha = proc_head.stdout.strip() if proc_head.returncode == 0 else "UNKNOWN"
    logger.info("Current repository HEAD SHA: %s", head_sha)

    # 2. Check if U1 is an ancestor
    proc_merge_base = run_git(["merge-base", "--is-ancestor", EXPECTED_U1_SHA, "HEAD"])
    u1_incorporated = (proc_merge_base.returncode == 0)
    logger.info("U1 (%s) is ancestor of HEAD: %s", EXPECTED_U1_SHA[:8], u1_incorporated)

    # 3. Check C1 integration
    # C1 is a GUI commit in host; verify the TOCTOU check in native-control.mjs
    native_control = REPO_ROOT / "apps" / "host" / "server" / "native-control.mjs"
    c1_present = False
    if native_control.exists():
        content = native_control.read_text(encoding="utf-8")
        if "checkedSettingsConfig" in content:
            c1_present = True
    logger.info("C1 GUI security hardening present: %s", c1_present)

    # 4. Check Fork Contracts & localized READMEs preservation
    fork_contracts_file = REPO_ROOT / "_docs" / "upstream-intake" / "fork-contracts.json"
    contracts_count = 0
    if fork_contracts_file.exists():
        try:
            fc_data = json.loads(fork_contracts_file.read_text(encoding="utf-8"))
            contracts_count = len(fc_data.get("contracts", []))
        except Exception as e:
            logger.warning("Error reading fork-contracts.json: %s", e)

    localized_readmes = [
        "README.md",
        "README.ja.md",
        "README.zh-CN.md",
        "README.de.md",
        "README.es.md",
        "README.fr.md",
        "README.pt-BR.md",
    ]
    readmes_ok = all((REPO_ROOT / r).exists() for r in localized_readmes)
    logger.info("Fork contracts registered: %d, Localized READMEs present: %s", contracts_count, readmes_ok)

    # 5. Lock final U_cut
    all_passed = u1_incorporated and c1_present and (contracts_count >= 11) and readmes_ok

    report = {
        "status": "LOCKED" if all_passed else "MISMATCH",
        "head_sha": head_sha,
        "u_cut_sha": EXPECTED_U1_SHA,
        "c1_sha": EXPECTED_C1_SHA,
        "f0_baseline_sha": EXPECTED_F0_SHA,
        "checks": {
            "u1_ancestor_verified": u1_incorporated,
            "c1_gui_patch_verified": c1_present,
            "fork_contracts_count": contracts_count,
            "localized_readmes_verified": readmes_ok
        },
        "all_passed": all_passed
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Check and lock upstream cut SHA and integration status")
    parser.add_argument("--output", type=str, default="", help="Optional path to output JSON status")

    args = parser.parse_args()
    report = verify_upstream_cut()

    out_json = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(out_json, encoding="utf-8")
        logger.info("Upstream cut lock written to %s", p)

    sys.stdout.write(out_json + "\n")
    sys.stdout.flush()

    if not report["all_passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
