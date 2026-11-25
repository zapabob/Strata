"""Section 16 & Section 22 Markdown report generator for PWS benchmarks."""

from __future__ import annotations

from typing import Any


def _fmt(v: Any) -> str:
    if v is None:
        return "null (not measured)"
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def render_pws_markdown_report(payload: dict[str, Any]) -> str:
    """Render a King's English Markdown report from a PWS replay/audit JSON payload."""
    lines = [
        "# NKAT–URT Predictive Weight Streaming (PWS) Report",
        "",
        "> `releaseQualified=false` — Unmeasured quantities are explicitly recorded as `null`.",
        "",
    ]
    if "cache_policies" in payload:
        cp = payload["cache_policies"]
        lines.append("## Cache Policy Comparison")
        lines.append("")
        lines.append(
            f"- Memory budget: `{cp['memory_budget_bytes']:,}` bytes · "
            f"Events: `{cp['num_events']:,}` · Distinct experts: `{cp['distinct_experts']:,}`"
        )
        lines.append("")
        lines.append("| Policy | Online Deployable | Expert Hit Rate | Byte-Weighted Hit Rate | Physical Miss Bytes | Evictions |")
        lines.append("|---|---|---:|---:|---:|---:|")
        for row in cp["policies"]:
            lines.append(
                f"| `{row['policy']}` | `{row['deployable_online']}` "
                f"| {_fmt(row['expert_hit_rate'])} "
                f"| {_fmt(row['byte_weighted_hit_rate'])} "
                f"| {row['physical_miss_bytes']:,} "
                f"| {row['evictions']:,} |"
            )
        lines.append("")

    if "deadline_prefetch" in payload:
        lines.append("## Deadline-Aware Prefetch vs Demand-Only Comparison")
        lines.append("")
        lines.append("| Mode | Exposed I/O Stall (ms/tok) | Logical B/tok | Physical B/tok | Prefetch Precision | Prefetch Recall | Deadline Miss Rate |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        for label, row in payload["deadline_prefetch"].items():
            lines.append(
                f"| `{label}` "
                f"| {_fmt(row['exposed_io_stall_ms_per_token'])} "
                f"| {_fmt(row['ssd_logical_bytes_per_token'])} "
                f"| {_fmt(row['ssd_physical_bytes_per_token'])} "
                f"| {_fmt(row['prefetch_precision'])} "
                f"| {_fmt(row['prefetch_recall'])} "
                f"| {_fmt(row['prefetch_deadline_miss_rate'])} |"
            )
        lines.append("")
    return "\n".join(lines)
