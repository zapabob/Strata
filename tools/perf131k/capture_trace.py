"""Validate bounded P01 host JSONL. No engine launch, GPU import or performance claims.

Stage and thread unions are overlapping views, never additive components of E2E.
Physical I/O and GPU execution remain unknown until an independent collector exists.
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any

MAX_BYTES = 4 * 1024 * 1024
MAX_RECORDS = 4096
STAGES = {
    "request",
    "prefill_host",
    "verify_host",
    "graph_launch_issue",
    "graph_enqueue_host",
    "host_wait",
    "h2d_issue",
    "expert_copy_host",
    "expert_direct_read_host",
}
SPAN_KEYS = {
    "type",
    "id",
    "parent",
    "generation",
    "thread",
    "stage",
    "start_ns",
    "end_ns",
    "token_start",
    "token_end",
    "layer",
    "stream",
    "graph_handle_id",
    "graph_instance",
    "graph_replay",
    "logical_read_requested_bytes",
    "copy_requested_bytes",
    "gpu_elapsed_ns",
    "physical_read_bytes",
    "event_generation",
    "allocation_id",
}


def integer(value: Any, name: str, minimum: int = 0) -> int:
    if type(value) is not int or not minimum <= value <= 2**63 - 1:
        raise ValueError(f"invalid {name}")
    return value


def union_ns(spans: list[dict]) -> int:
    """Measure the union of host intervals, including parallel and nested intervals once."""
    total, right = 0, 0
    for start, end in sorted((s["start_ns"], s["end_ns"]) for s in spans):
        total += max(0, end - max(start, right))
        right = max(right, end)
    return total


def summarize(document: dict) -> dict:
    """Return host coverage only; never convert unobserved disk/GPU values to zero."""
    spans = document["spans"]
    return {
        "host_covered_ns": union_ns(spans),
        "accounting": "interval_union_not_stage_sum",
        "stage_host_covered_ns": {
            stage: union_ns([s for s in spans if s.get("stage") == stage])
            for stage in sorted({s["stage"] for s in spans if "stage" in s})
        },
        "gpu_elapsed_ns": None,
        "physical_read_bytes": None,
        "e2e_ns": None,
        "page_fault_count": None,
        "os_cache_hit_count": None,
        "cpu_busy_ns": None,
        "gpu_copy_ns": None,
        "unobserved_reason": "P01-A host scopes only; no GPU, ETW or CPU scheduler collector",
        "nvme_bandwidth_bytes_per_second": None,
        "performance_status": "NOT_MEASURED",
    }


def unique_object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def analyze(path: Path) -> dict:
    """Read bounded input, require a terminal footer, and validate interval identities."""
    rows = []
    size = 0
    with path.open("rb") as source:
        while True:
            line = source.readline(2049)
            if not line:
                break
            size += len(line)
            if len(line) > 2048 or size > MAX_BYTES or len(rows) >= MAX_RECORDS + 2:
                raise ValueError("trace input limit exceeded")
            row = json.loads(line, object_pairs_hook=unique_object)
            if not isinstance(row, dict):
                raise ValueError("trace row must be an object")
            rows.append(row)
    if len(rows) < 2:
        raise ValueError("missing trace header/footer")
    header, footer = rows[0], rows[-1]
    if header != {"type": "header", "schema": 1, "source": "host_only", "clock": "steady_ns", "capacity": MAX_RECORDS}:
        raise ValueError("unsupported trace header")
    integer(header["schema"], "schema", 1)
    integer(header["capacity"], "capacity", 1)
    if (
        set(footer)
        != {
            "type",
            "records",
            "dropped",
            "unfinished",
            "identity_overflow",
            "diagnostic_failures",
            "unregistered_graphs",
        }
        or footer["type"] != "footer"
    ):
        raise ValueError("missing or invalid terminal footer")
    for key in ("records", "dropped", "unfinished", "identity_overflow", "diagnostic_failures", "unregistered_graphs"):
        integer(footer[key], key)
    spans = rows[1:-1]
    if footer["records"] != len(spans):
        raise ValueError("record count mismatch")
    incomplete = any(
        footer[k] for k in ("dropped", "unfinished", "identity_overflow", "diagnostic_failures", "unregistered_graphs")
    )
    by_id, replays = {}, set()
    for span in spans:
        if (
            set(span) != SPAN_KEYS
            or span["type"] != "span"
            or type(span["stage"]) is not str
            or span["stage"] not in STAGES
        ):
            raise ValueError("invalid span fields or stage")
        for key in (
            "id",
            "parent",
            "generation",
            "thread",
            "start_ns",
            "end_ns",
            "stream",
            "graph_handle_id",
            "graph_replay",
        ):
            integer(span[key], key)
        for key in ("token_start", "token_end", "layer", "logical_read_requested_bytes", "copy_requested_bytes"):
            integer(span[key], key, -1)
        for key in ("gpu_elapsed_ns", "physical_read_bytes", "event_generation", "allocation_id"):
            if span[key] is not None:
                raise ValueError(f"host-only collector cannot establish {key}")
        if span["thread"] == 0 or span["id"] == 0 or span["id"] in by_id or span["end_ns"] < span["start_ns"]:
            raise ValueError("duplicate identity or reversed interval")
        if span["id"] > MAX_RECORDS or span["parent"] >= span["id"]:
            raise ValueError("invalid span parent or capacity")
        first, last = span["token_start"], span["token_end"]
        if (first == -1) != (last == -1) or (first >= 0 and last < first):
            raise ValueError("invalid token range")
        if bool(span["graph_handle_id"]) != bool(span["graph_replay"]):
            raise ValueError("graph replay lacks handle identity")
        if span["graph_instance"] is not None:
            integer(span["graph_instance"], "graph instance", 1)
            if not span["graph_handle_id"] and not incomplete:
                raise ValueError("graph instance lacks handle identity")
        elif span["graph_handle_id"] and not incomplete:
            raise ValueError("graph instance unregistered without loss marker")
        if span["graph_replay"]:
            replay = (span["graph_handle_id"], span["graph_replay"])
            if (
                span["stage"] not in {"graph_launch_issue", "graph_enqueue_host"}
                or replay in replays
                or span["stream"] == 0
                or span["graph_replay"] != span["id"]
            ):
                raise ValueError("reused or invalid graph replay")
            replays.add(replay)
        by_id[span["id"]] = span
    for span in spans:
        parent = by_id.get(span["parent"])
        if span["parent"] and parent is None and not incomplete:
            raise ValueError("missing parent")
        if parent and (
            parent["thread"] != span["thread"]
            or parent["start_ns"] > span["start_ns"]
            or parent["end_ns"] < span["end_ns"]
        ):
            raise ValueError("parent interval/thread mismatch")
        if parent and span["stage"] != "request" and parent["generation"] != span["generation"]:
            raise ValueError("parent generation mismatch")
        generation = by_id.get(span["generation"])
        if span["stage"] == "request" and span["generation"] != span["id"]:
            raise ValueError("request must own its generation")
        if span["generation"] and (generation is None or generation["stage"] != "request") and not incomplete:
            raise ValueError("missing request generation")
        if generation and (
            generation["thread"] != span["thread"]
            or generation["start_ns"] > span["start_ns"]
            or generation["end_ns"] < span["end_ns"]
        ):
            raise ValueError("request generation interval/thread mismatch")
    result = summarize({"spans": spans})
    result.update(
        schema=1,
        trace_status="INCOMPLETE" if incomplete else "COMPLETE_HOST_TRACE",
        counts=footer,
        source="host_only",
        record_count=len(spans),
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="existing host trace JSONL; never an engine configuration")
    args = parser.parse_args()
    try:
        result = analyze(args.trace)
    except (OSError, ValueError) as error:
        # Do not echo raw trace contents or private file paths into the report.
        sys.stderr.write(f"trace validation failed: {type(error).__name__}\n")
        return 2
    sys.stdout.write(json.dumps(result, sort_keys=True) + "\n")
    return 0 if result["trace_status"] == "COMPLETE_HOST_TRACE" else 3


if __name__ == "__main__":
    raise SystemExit(main())
