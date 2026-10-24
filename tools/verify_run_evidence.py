#!/usr/bin/env python3
"""tools/verify_run_evidence.py - Strict verifier for execution evidence and run receipts.
Strictly conforms to MILSPEC-Codex standard: logging only, zero raw print, strict types.
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from strata_control.qualification import evaluate_gate, GateStatus, GateResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [strata.evidence_verifier] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("strata.evidence_verifier")


def verify_evidence_file(file_path: Path, strict: bool = True) -> list[GateResult]:
    """Verify one JSON file containing RunReceipt v2 or list of receipts."""
    if not file_path.is_file():
        raise FileNotFoundError(f"Evidence file not found: {file_path}")

    try:
        content = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error("Failed to parse JSON in %s: %s", file_path, e)
        return [GateResult(status=GateStatus.REJECTED, real_model_qualified=False, reason=f"Invalid JSON: {e}")]

    receipts: list[dict[str, Any]] = []
    if isinstance(content, list):
        receipts = content
    elif isinstance(content, dict):
        if "results" in content and isinstance(content["results"], list):
            receipts = content["results"]
        else:
            receipts = [content]
    else:
        return [GateResult(status=GateStatus.REJECTED, real_model_qualified=False, reason="Root content must be object or list")]

    results: list[GateResult] = []
    for idx, r in enumerate(receipts):
        cid = r.get("candidate_id", f"entry_{idx}")
        res = evaluate_gate(r)
        logger.info("Candidate %s: status=%s, real_model_qualified=%s, reason=%s",
                    cid, res.status.value, res.real_model_qualified, res.reason)
        results.append(res)
    return results


def verify_evidence_root(root_dir: Path, strict: bool = True) -> dict[str, Any]:
    """Verify all evidence receipts under a directory."""
    logger.info("Verifying evidence root: %s (strict=%s)", root_dir, strict)
    all_results: dict[str, list[dict[str, Any]]] = {}
    total_passed = 0
    total_rejected = 0

    json_files = list(root_dir.glob("**/*.json"))
    if not json_files:
        logger.warning("No JSON files found in evidence root: %s", root_dir)

    for p in json_files:
        try:
            res_list = verify_evidence_file(p, strict=strict)
            all_results[str(p)] = [
                {
                    "status": r.status.value,
                    "real_model_qualified": r.real_model_qualified,
                    "reason": r.reason,
                    "details": r.details,
                }
                for r in res_list
            ]
            for r in res_list:
                if r.real_model_qualified:
                    total_passed += 1
                else:
                    total_rejected += 1
        except Exception as e:
            logger.error("Error verifying %s: %s", p, e)
            all_results[str(p)] = [{"status": GateStatus.REJECTED.value, "real_model_qualified": False, "reason": str(e)}]
            total_rejected += 1

    summary = {
        "evidence_root": str(root_dir),
        "total_files": len(json_files),
        "total_passed": total_passed,
        "total_rejected": total_rejected,
        "strict": strict,
        "overall_status": "PASSED" if (total_passed > 0 and total_rejected == 0) else ("REJECTED" if total_rejected > 0 else "EMPTY"),
        "files": all_results,
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Strict Evidence Gate Verifier")
    parser.add_argument("evidence_path", type=str, help="Path to evidence file or directory")
    parser.add_argument("--strict", action="store_true", default=True, help="Enforce strict empirical qualification criteria")
    args = parser.parse_args()

    target = Path(args.evidence_path)
    if not target.exists():
        logger.error("Target path does not exist: %s", target)
        sys.exit(2)

    if target.is_dir():
        summary = verify_evidence_root(target, strict=args.strict)
    else:
        res_list = verify_evidence_file(target, strict=args.strict)
        summary = {
            "evidence_path": str(target),
            "total_passed": sum(1 for r in res_list if r.real_model_qualified),
            "total_rejected": sum(1 for r in res_list if not r.real_model_qualified),
            "results": [
                {
                    "status": r.status.value,
                    "real_model_qualified": r.real_model_qualified,
                    "reason": r.reason,
                }
                for r in res_list
            ]
        }

    sys.stdout.write(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    sys.stdout.flush()

    if summary.get("total_rejected", 0) > 0 and args.strict:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
