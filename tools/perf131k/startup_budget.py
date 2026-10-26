"""CPU-only startup commit ledger. An estimate never authorizes a launch.

These are host committed-byte charges, not requested device bytes. Returning a
buffer to an application pool does not release its commit reservation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DIAGNOSTIC_JOB_LIMIT = 10 * 1024**3
MAX_MANIFEST_BYTES = 1024**2
MAX_EVENTS = 8192
PHASES = ("source_open", "cache_attempt", "profile_fill", "resident_complement", "ready")
CATEGORIES = {"fixed", "stage", "scratch", "metadata", "children", "other_host"}


def known_bytes(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a known nonnegative byte count")
    return value


def stage_payload_bound(blob_bytes: int, lifetime_max_busy: int) -> int:
    """Owned payload only; caller must prove lifetime busy bound and no seq wrap.

    Requires an initially empty pool and serialized claims. Vector/map capacity,
    allocator overhead and events are separate ledger charges.
    """
    blob = known_bytes(blob_bytes, "maximum blob")
    busy = known_bytes(lifetime_max_busy, "lifetime maximum busy slots")
    if not blob:
        raise ValueError("maximum blob must be positive")
    return (256 + busy) * blob


def direct_scratch_bound(blob_bytes: int, fills_per_call: int, role_count: int) -> int:
    """Windows read_direct buffer capacity, excluding its vectors and events.

    Source constants: 4096-byte sectors, <=1 MiB merged gaps, 1 MiB capacity
    rounding. Each fill's role lengths sum to at most blob_bytes. Merging can
    add at most one gap per window after the first; overlap only reduces size.
    Caller must prove the maximum fills per call for every path on the thread.
    """
    blob = known_bytes(blob_bytes, "maximum blob")
    fills = known_bytes(fills_per_call, "fills per call")
    if not blob or not fills or type(role_count) is not int or role_count not in (1, 3):
        raise ValueError("positive blob/fill counts and one or three roles required")
    windows = fills * role_count
    span = fills * blob + windows * (2 * 4096) + (windows - 1) * (1 << 20)
    return (span + (1 << 20) - 1) // (1 << 20) * (1 << 20)


def evaluate(manifest: dict) -> dict:
    """Assess explicit overlap; never mistake the result for measured Job charge."""
    if not isinstance(manifest, dict):
        raise ValueError("a startup inventory object is required")
    limit = manifest.get("job_limit_bytes")
    if limit is not None and (type(limit) is not int or limit <= 0):
        raise ValueError("declared diagnostic Job cap must be a positive byte count")
    reserve = known_bytes(manifest.get("untracked_reserve_bytes"), "untracked reserve")
    reserve_basis = manifest.get("untracked_reserve_basis")
    if not reserve or not isinstance(reserve_basis, str) or not reserve_basis.strip():
        raise ValueError("a positive documented bound for untracked host commit is required")
    events = manifest.get("events")
    if not isinstance(events, list) or len(events) > MAX_EVENTS:
        raise ValueError("a bounded ordered event list is required")

    live: dict[str, tuple[str, int]] = {}
    peaks: dict[str, int] = {}
    phase_index = -1
    phase = None
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("each event must be an object")
        action = event.get("action")
        if action == "enter":
            next_phase = event.get("phase")
            if next_phase not in PHASES or PHASES.index(next_phase) != phase_index + 1:
                raise ValueError("startup phases must be entered once in order")
            phase_index += 1
            phase = next_phase
        elif action == "acquire":
            ident = event.get("id")
            category = event.get("category")
            amount = known_bytes(event.get("bytes"), "allocation")
            if phase is None or not isinstance(ident, str) or not ident or ident in live:
                raise ValueError("an acquisition needs a unique live allocation id")
            basis = event.get("basis")
            if (category not in CATEGORIES or amount == 0
                    or not isinstance(basis, str) or not basis.strip()):
                raise ValueError("acquisition needs category, positive charge and evidence basis")
            live[ident] = category, amount
        elif action == "release":
            ident = event.get("id")
            if phase is None or ident not in live:
                raise ValueError("release needs a live allocation")
            if event.get("kind") != "actual_uncommit":
                raise ValueError("pool reuse or logical release does not reduce commit")
            del live[ident]
        else:
            raise ValueError("unknown startup event")
        if phase is not None:
            charge = reserve + sum(amount for _, amount in live.values())
            peaks[phase] = max(peaks.get(phase, 0), charge)

    if phase_index != len(PHASES) - 1:
        raise ValueError("all startup phases, including ready, are required")
    peak = max(peaks.values())
    comparison = ("CAP_UNSPECIFIED" if limit is None else
                  "ESTIMATE_WITHIN_CAP" if peak <= limit else "ESTIMATE_OVER_CAP")
    return {"status": "ESTIMATE_ONLY", "diagnostic_cap_comparison": comparison,
            "declared_job_limit_bytes": limit, "estimated_peak_host_commit_bytes": peak,
            "estimated_cap_margin_bytes": None if limit is None else limit - peak,
            "phase_peaks_bytes": peaks,
            "live_at_ready_bytes": sum(amount for _, amount in live.values()),
            "actual_required_commit_proven": False, "product_fit_claim": False,
            "runtime_proof": False, "launch_authorized": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        if args.manifest.stat().st_size > MAX_MANIFEST_BYTES:
            raise ValueError("startup manifest exceeds 1 MiB")
        result = evaluate(json.loads(args.manifest.read_text(encoding="utf-8")))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        result = {"status": "BLOCKED_INCOMPLETE", "reason": str(error),
                  "runtime_proof": False, "launch_authorized": False}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "ESTIMATE_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
