from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("strata.qualification")


class GateStatus(str, Enum):
    PASSED = "PASSED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class GateResult:
    status: GateStatus
    real_model_qualified: bool
    reason: str
    details: dict[str, Any] | None = None


DISALLOWED_BINARY_HASHES = frozenset({
    "native-sha",
    "placeholder",
    "todo",
    "none",
    "unknown",
    "",
})

STATIC_DUMMY_TIMESTAMPS = frozenset({
    "2026-10-25T02:45:00Z",
    "1970-01-01T00:00:00Z",
})


def evaluate_gate(receipt: dict[str, Any]) -> GateResult:
    """Evaluate RunReceipt v2 against strict empirical evidence criteria.
    
    Rejects any mock, synthetic, or dry-run claims from being promoted to real_model_qualified.
    """
    method = str(receipt.get("verification_method", "")).strip()
    if method == "DRYRUN_QUALIFICATION_RECEIPT" or "dryrun" in method.lower():
        return GateResult(
            status=GateStatus.REJECTED,
            real_model_qualified=False,
            reason="DRYRUN qualification receipt cannot qualify real model execution",
        )

    invocations = int(receipt.get("invocations", 0))
    if invocations <= 0:
        return GateResult(
            status=GateStatus.REJECTED,
            real_model_qualified=False,
            reason=f"Model invocations count must be > 0 (found {invocations})",
        )

    tokens = int(receipt.get("tokens_generated", 0))
    if tokens <= 0:
        return GateResult(
            status=GateStatus.REJECTED,
            real_model_qualified=False,
            reason=f"Tokens generated must be > 0 (found {tokens})",
        )

    bin_hash = str(receipt.get("binary_sha256", "")).strip().lower()
    if bin_hash in DISALLOWED_BINARY_HASHES or len(bin_hash) < 32:
        return GateResult(
            status=GateStatus.REJECTED,
            real_model_qualified=False,
            reason=f"Placeholder or invalid binary sha256: {bin_hash!r}",
        )

    ts = str(receipt.get("timestamp", "")).strip()
    duration = float(receipt.get("duration_seconds", 1.0))
    if ts in STATIC_DUMMY_TIMESTAMPS or duration <= 0.0:
        return GateResult(
            status=GateStatus.REJECTED,
            real_model_qualified=False,
            reason=f"Fixed timestamp {ts!r} or zero duration {duration} does not reflect runtime execution",
        )

    log_path = receipt.get("log_path")
    recorded_log_hash = receipt.get("raw_log_sha256")
    if log_path:
        p = Path(log_path)
        if not p.is_file():
            return GateResult(
                status=GateStatus.REJECTED,
                real_model_qualified=False,
                reason=f"Log file not found at path: {log_path}",
            )
        try:
            actual_log_hash = hashlib.sha256(p.read_bytes()).hexdigest()
            if recorded_log_hash and actual_log_hash.lower() != str(recorded_log_hash).lower():
                return GateResult(
                    status=GateStatus.REJECTED,
                    real_model_qualified=False,
                    reason=f"Raw log hash mismatch: recorded {recorded_log_hash} != actual {actual_log_hash}",
                )
        except OSError as e:
            return GateResult(
                status=GateStatus.REJECTED,
                real_model_qualified=False,
                reason=f"Failed to read log file {log_path}: {e}",
            )

    return GateResult(
        status=GateStatus.PASSED,
        real_model_qualified=True,
        reason="Evidence gate passed all verification criteria",
        details={"candidate_id": receipt.get("candidate_id")},
    )
