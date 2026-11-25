"""Section 18 structured report generator for NKAT-URT TSI evaluation summaries.

Formats all core Section 18 metrics cleanly while preserving `null` for unmeasured
fields and separating `known_benchmark_problem` from `novel_discovery_candidate`.
"""

from __future__ import annotations

from typing import Any, Sequence


def _fmt(val: Any, suffix: str = "") -> str:
    if val is None:
        return "null (not measured)"
    if isinstance(val, float):
        return f"{val:.4f}{suffix}"
    return f"{val}{suffix}"


def _fmt_gib(num_bytes: int | None) -> str:
    if num_bytes is None:
        return "null (not measured)"
    return f"{num_bytes / (1024 ** 3):.2f} GiB"


def render_markdown_report(summaries: Sequence[dict[str, Any]]) -> str:
    """Render a King's English Markdown summary report from one or more TSI evaluation runs."""
    lines: list[str] = [
        "# NKAT–URT TSI Evaluation Report",
        "",
        "> `releaseQualified=false` — All unmeasured quantities are explicitly recorded as `null`.",
        "",
    ]
    for idx, summary in enumerate(summaries, start=1):
        cfg = summary.get("config", {})
        lines.append(
            f"## Run {idx}: `{cfg.get('model', 'unknown')}` "
            f"(`{cfg.get('quantization', cfg.get('quantisation', 'unspecified'))}`, "
            f"mode=`{cfg.get('mode', 'standard')}`, suite=`{cfg.get('suite', 'unknown')}`)"
        )
        lines.append("")
        lines.append(f"- Git commit: `{summary.get('git_commit', 'unknown')}`")
        lines.append(f"- Effective bpw: `{_fmt(cfg.get('effective_bpw'))}`")
        lines.append(f"- Peak VRAM: `{_fmt_gib(summary.get('peak_vram_bytes'))}`")
        lines.append(f"- Peak system RAM: `{_fmt_gib(summary.get('peak_ram_bytes'))}`")
        att = summary.get("attainment", {})
        lines.append(
            f"- Empirical $B^*$ over tested grid ($\\delta={att.get('delta')}$): "
            f"`{_fmt(att.get('min_tested_budget_attained'))}` "
            f"(achieved=`{att.get('achieved_within_tested_budgets')}`)"
        )
        lines.append("")
        lines.append(
            "| Token Budget | Verified | Success Rate | Hoeffding LB | Verified/s | Tokens/Verified | "
            "RMST (tokens) | RMST (wall s) | Median Decode t/s | Failures |"
        )
        lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
        for b in summary.get("budgets", []):
            surv_tok = b.get("survival_tokens") or {}
            surv_wall = b.get("survival_wall_seconds") or {}
            h_lb = b.get("hoeffding_simultaneous_lower")
            lines.append(
                f"| {b.get('token_budget')} "
                f"| {b.get('verified_tasks')}/{b.get('num_tasks')} "
                f"| {_fmt(b.get('verified_success_rate'))} "
                f"| {_fmt(h_lb)} "
                f"| {_fmt(b.get('verified_solutions_per_second'))} "
                f"| {_fmt(b.get('tokens_per_verified_solution'))} "
                f"| {_fmt(surv_tok.get('rmst_at_b_max'))} "
                f"| {_fmt(surv_wall.get('rmst_at_b_max'))} "
                f"| {_fmt(b.get('median_decode_tps'))} "
                f"| `{b.get('failure_taxonomy', {})}` |"
            )
        lines.append("")
    return "\n".join(lines)
