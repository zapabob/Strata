#!/usr/bin/env python3
"""CLI entrypoint for NKAT-URT Theory of Scientific Intelligence (TSI) & VRE evaluation.

Examples:
    python tools/tsi_eval.py math-check
    python tools/tsi_eval.py list-tasks --suite all
    python tools/tsi_eval.py eval --url http://127.0.0.1:8080 --suite dev --mode standard --budgets 128,512 --out out.json --jsonl out.jsonl
    python tools/tsi_eval.py eval --url http://127.0.0.1:8080 --suite dev --mode adaptive --budgets 512 --out adaptive.json --jsonl adaptive.jsonl
    python tools/tsi_eval.py compare ref.json cand.json --out diff.json
    python tools/tsi_eval.py report run1.json run2.json --out report.md
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys
from typing import Any, Sequence

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from tsi import DEFAULT_API_BASE_URL  # noqa: E402
from tsi.bellman_residual import bellman_residual_success_bound  # noqa: E402
from tsi.client import LocalOpenAIClient  # noqa: E402
from tsi.discovery_rate import compare_quantised_discovery_rate  # noqa: E402
from tsi.doob import FiniteSearchTree, TreeEdge, verify_doob_gibbs_equivalence  # noqa: E402
from tsi.math_foundations import run_self_checks  # noqa: E402
from tsi.metrics import optional_file_sha256  # noqa: E402
from tsi.report import render_markdown_report  # noqa: E402
from tsi.runner import RunConfig, compare_runs, run_evaluation  # noqa: E402
from tsi.tasks import get_builtin_suite, load_tasks_file  # noqa: E402
from tsi.variational import min_kl_information_cost  # noqa: E402

LOGGER = logging.getLogger("strata.tsi_eval")


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def _parse_budgets(raw: str) -> tuple[int, ...]:
    vals: list[int] = []
    for part in raw.split(","):
        tok = part.strip()
        if not tok:
            continue
        v = int(tok)
        if v <= 0:
            raise ValueError(f"Token budget must be positive: {v}")
        vals.append(v)
    if not vals:
        raise ValueError("At least one positive token budget is required.")
    return tuple(vals)


def _run_extended_math_checks() -> dict[str, Any]:
    """Run Phase 1, Phase 2, and Phase 3 VRE exact mathematical verification identities."""
    p1 = run_self_checks()
    # Phase 2 Section 4 numerical verification (theoretical example, not hardware measurement)
    disc_check = compare_quantised_discovery_rate(
        p_ref=0.40, cost_ref=1.0, p_quant=0.25, cost_quant=0.5, finite_budgets=(3.0,)
    )
    assert abs(disc_check["p_crit"] - 0.225403) < 1e-5
    assert abs(disc_check["finite_budget_model_comparison"][0]["reference_success_model"] - 0.784) < 1e-6
    assert abs(disc_check["finite_budget_model_comparison"][0]["quantised_success_model"] - 0.822021) < 1e-5

    # Phase 3 Theorem 1 numerical verification (0.01 -> 0.90 = 3.8206 nat / 5.5119 bit)
    t1_check = min_kl_information_cost(0.01, 0.90)
    assert abs(t1_check["min_kl_nats"] - 3.820624) < 1e-4
    assert abs(t1_check["min_kl_bits"] - 5.511995) < 2e-4

    # Phase 3 Theorem 5 numerical verification (p0=0.05, lam=5.0, L=1.0 -> 88.65% / 74.18%)
    t5_check = bellman_residual_success_bound(p0=0.05, lam=5.0, residual_oscillation_L=1.0)
    assert abs(t5_check["ideal_p_star"] - 0.886508) < 1e-4
    assert abs(t5_check["guaranteed_lower_bound"] - 0.741844) < 1e-4

    # Phase 3 Theorem 3 + Section 8 Doob/Feynman-Kac exact equivalence on a synthetic tree
    tree = FiniteSearchTree(
        root="u0",
        edges={
            "u0": [TreeEdge("L", "uL", 0.4, 1.0), TreeEdge("R", "uR", 0.6, 2.0)],
            "uL": [TreeEdge("ok", "t_ok1", 0.25, 1.5), TreeEdge("bad", "t_bad1", 0.75, 0.5)],
            "uR": [TreeEdge("ok", "t_ok2", 0.10, 3.0), TreeEdge("bad", "t_bad2", 0.90, 1.0)],
        },
        terminals={"t_ok1": 1.0, "t_bad1": 0.0, "t_ok2": 1.0, "t_bad2": 0.0},
    )
    doob_eq = verify_doob_gibbs_equivalence(tree, lam=3.5, eta=0.25)
    assert doob_eq["equivalent"]

    return {
        "pass": True,
        "phase1_linear_info_checks": p1,
        "phase2_discovery_rate_theorem_example": disc_check,
        "phase3_theorem1_min_kl_example": t1_check,
        "phase3_theorem5_bellman_residual_example": t5_check,
        "phase3_doob_feynman_kac_equivalence": doob_eq,
    }


def cmd_math_check(args: argparse.Namespace) -> int:
    result = _run_extended_math_checks()
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        LOGGER.info("Wrote math self-check report to %s", args.out)
    LOGGER.info("TSI/VRE mathematical self-checks PASSED:\n%s", text)
    return 0


def cmd_list_tasks(args: argparse.Namespace) -> int:
    tasks = load_tasks_file(args.tasks_file) if args.tasks_file else get_builtin_suite(args.suite)
    LOGGER.info("Loaded %d deterministic TSI tasks:", len(tasks))
    for t in tasks:
        LOGGER.info(
            "  [%s] (split=%s / suite=%s / %s) verifier=%s class=%s",
            t.task_id,
            t.split,
            t.suite,
            t.domain,
            t.verifier_type,
            t.discovery_class,
        )
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    tasks = load_tasks_file(args.tasks_file) if args.tasks_file else get_builtin_suite(args.suite)
    if args.max_tasks > 0:
        tasks = tasks[: args.max_tasks]
    budgets = _parse_budgets(args.budgets)
    client = LocalOpenAIClient(
        base_url=args.url,
        api_key=args.api_key,
        timeout_s=args.timeout,
        allow_non_loopback=args.allow_non_loopback,
    )
    sha256 = args.model_sha256 or optional_file_sha256(args.model_file)
    cfg = RunConfig(
        base_url=client.base_url,
        model=args.model,
        quantization=args.quantization,
        kv_mode=args.kv_mode,
        gdn_mode=args.gdn_mode,
        compensation_mode=args.compensation_mode,
        suite=str(args.tasks_file) if args.tasks_file else args.suite,
        budgets=budgets,
        attempts_per_task=max(1, args.attempts),
        temperature=args.temperature,
        seed=args.seed,
        reasoning_effort=args.reasoning_effort or None,
        timeout_s=args.timeout,
        delta_target=args.delta,
        release_qualified=False,
        mode=args.mode,
        model_sha256=sha256,
        effective_bpw=args.effective_bpw,
        sample_hw_metrics=args.sample_hw_metrics,
        max_wall_seconds_per_task=args.max_wall_per_task,
        vre_lambda=args.vre_lambda,
        vre_eta=args.vre_eta,
        vre_branch_candidates=max(1, args.vre_branches),
    )
    summary = run_evaluation(
        client,
        tasks,
        cfg,
        jsonl_path=args.jsonl,
        summary_path=args.out,
        repo_root=HERE.parent,
    )
    LOGGER.info(
        "Attainment (delta=%.2f): achieved=%s min_tested_budget=%s",
        cfg.delta_target,
        summary["attainment"]["achieved_within_tested_budgets"],
        summary["attainment"]["min_tested_budget_attained"],
    )
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    ref = json.loads(args.reference.read_text(encoding="utf-8-sig"))
    cand = json.loads(args.candidate.read_text(encoding="utf-8-sig"))
    diff = compare_runs(ref, cand)
    text = json.dumps(diff, indent=2, ensure_ascii=False)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        LOGGER.info("Wrote TSI comparison JSON to %s", args.out)
    LOGGER.info("TSI reference-vs-candidate comparison:\n%s", text)
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    summaries = [json.loads(p.read_text(encoding="utf-8-sig")) for p in args.inputs]
    md = render_markdown_report(summaries)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(md + "\n", encoding="utf-8")
        LOGGER.info("Wrote TSI Markdown report to %s", args.out)
    else:
        LOGGER.info("TSI Markdown Report:\n%s", md)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NKAT-URT TSI & VRE verified evaluation CLI.")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_math = sub.add_parser("math-check", help="Run exact Phase 1, 2, and 3 VRE mathematical self-checks.")
    p_math.add_argument("--out", type=Path, default=None, help="Optional output JSON path.")
    p_math.set_defaults(func=cmd_math_check)

    p_list = sub.add_parser("list-tasks", help="List deterministic built-in splits or external tasks.")
    p_list.add_argument(
        "--suite",
        default="all",
        help="core-v1/dev, calibration, validation, holdout-v1/frozen-holdout, or all.",
    )
    p_list.add_argument("--tasks-file", type=Path, default=None, help="External JSON/JSONL tasks file.")
    p_list.set_defaults(func=cmd_list_tasks)

    p_eval = sub.add_parser("eval", help="Evaluate a local OpenAI-compatible Strata endpoint.")
    p_eval.add_argument("--url", default=DEFAULT_API_BASE_URL, help=f"Loopback base URL (default {DEFAULT_API_BASE_URL}).")
    p_eval.add_argument("--allow-non-loopback", action="store_true", help="Explicit opt-in for non-loopback endpoints.")
    p_eval.add_argument("--api-key", default="", help="Optional Bearer API key.")
    p_eval.add_argument("--model", default="", help="Model name sent in requests (empty auto-detects from /v1/models).")
    p_eval.add_argument("--model-sha256", default=None, help="Optional precomputed SHA-256 of the model file.")
    p_eval.add_argument("--model-file", type=Path, default=None, help="Optional path used only to hash model_sha256 (path not logged).")
    p_eval.add_argument("--effective-bpw", type=float, default=None, help="Optional effective bits-per-weight value.")
    p_eval.add_argument("--quantization", default="unspecified", help="Quantisation label recorded in provenance.")
    p_eval.add_argument("--kv-mode", default="unspecified", help="KV cache format label recorded in provenance.")
    p_eval.add_argument("--gdn-mode", default="unspecified", help="GDN state mode label recorded in provenance.")
    p_eval.add_argument("--compensation-mode", default="off", help="Compensation mode label (off/gramian/low-rank).")
    p_eval.add_argument("--mode", choices=["standard", "adaptive", "vre"], default="standard", help="Evaluation policy mode.")
    p_eval.add_argument(
        "--suite",
        default="core-v1",
        help="Built-in split: core-v1/dev, calibration, validation, holdout-v1/frozen-holdout, or all.",
    )
    p_eval.add_argument("--tasks-file", type=Path, default=None, help="External JSON/JSONL tasks file.")
    p_eval.add_argument("--max-tasks", type=int, default=0, help="Optional cap on task count (0 = all).")
    p_eval.add_argument("--budgets", default="128,512", help="Comma-separated max_tokens budgets.")
    p_eval.add_argument("--attempts", type=int, default=1, help="Attempts/steps per task per budget (cumulative budget tracked).")
    p_eval.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature (default 0.0 greedy).")
    p_eval.add_argument("--seed", type=int, default=42, help="Base deterministic seed.")
    p_eval.add_argument("--reasoning-effort", default="", help="Optional Strata reasoning_effort field.")
    p_eval.add_argument("--delta", type=float, default=0.20, help="Target failure rate delta for finite attainment.")
    p_eval.add_argument("--timeout", type=float, default=120.0, help="Per-request HTTP timeout in seconds.")
    p_eval.add_argument("--max-wall-per-task", type=float, default=180.0, help="Cumulative wall-clock cap per task in adaptive/vre modes.")
    p_eval.add_argument("--vre-lambda", type=float, default=3.0, help="Step-level VRE control strength lambda.")
    p_eval.add_argument("--vre-eta", type=float, default=0.01, help="Step-level VRE cost penalty eta.")
    p_eval.add_argument("--vre-branches", type=int, default=2, help="Step-level VRE candidate branches per retry step.")
    p_eval.add_argument("--sample-hw-metrics", action="store_true", help="Sample host RAM and nvidia-smi VRAM (otherwise null).")
    p_eval.add_argument("--out", type=Path, default=None, help="Summary JSON output path.")
    p_eval.add_argument("--jsonl", type=Path, default=None, help="Per-task Section 16 JSONL output path.")
    p_eval.set_defaults(func=cmd_eval)

    p_cmp = sub.add_parser("compare", help="Compare a reference TSI summary JSON against a candidate JSON.")
    p_cmp.add_argument("reference", type=Path, help="Reference run summary JSON.")
    p_cmp.add_argument("candidate", type=Path, help="Candidate (e.g. quantised or adaptive) run summary JSON.")
    p_cmp.add_argument("--out", type=Path, default=None, help="Optional output JSON path.")
    p_cmp.set_defaults(func=cmd_compare)

    p_rep = sub.add_parser("report", help="Render a Markdown Section 18 summary from one or more run JSONs.")
    p_rep.add_argument("inputs", nargs="+", type=Path, help="One or more TSI summary JSON files.")
    p_rep.add_argument("--out", type=Path, default=None, help="Optional Markdown output path.")
    p_rep.set_defaults(func=cmd_report)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.verbose)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
