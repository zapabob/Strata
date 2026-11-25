"""TSI verified evaluation runner (Phase 1 + Phase 2 Stages A-C + VRE step-level mode).

All failed, truncated, timed-out, and unverified attempts are retained in cumulative
token and wall-clock budgets. Emits Section 16 JSONL trial records with strict `null`
for unmeasured metrics, survival RMST curves on both token and wall-clock axes,
Hoeffding simultaneous lower bounds, and separate aggregation for known benchmark
problems versus novel discovery candidates.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import statistics
import subprocess
import sys
from typing import Any, Literal, Sequence

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover

    def tqdm(iterable, **_kwargs):
        return iterable


from . import TSI_RECORD_SCHEMA_VERSION, TSI_SCHEMA_VERSION
from .client import LocalOpenAIClient
from .discovery_rate import compare_quantised_discovery_rate
from .math_foundations import (
    bonferroni_alpha,
    clopper_pearson_interval,
    finite_budget_attainment,
    wilson_interval,
)
from .metrics import (
    build_section16_trial_record,
    sample_gpu_vram_bytes,
    sample_system_memory_bytes,
    sanitise_public_text,
)
from .scheduler import SchedulerConfig, run_adaptive_task
from .survival import (
    StoppingObservation,
    analyse_stopping_times,
    hoeffding_simultaneous_lower_bound,
)
from .tasks import SYSTEM_PROMPT, MathTask, verify_response
from .verifier import VerificationLevel

LOGGER = logging.getLogger("strata.tsi.runner")

EvalMode = Literal["standard", "adaptive", "vre"]


@dataclass(frozen=True)
class RunConfig:
    """Immutable metadata and configuration recorded with every TSI evaluation run."""

    base_url: str
    model: str
    quantization: str
    kv_mode: str
    gdn_mode: str
    compensation_mode: str
    suite: str
    budgets: tuple[int, ...]
    attempts_per_task: int
    temperature: float
    seed: int
    reasoning_effort: str | None
    timeout_s: float
    delta_target: float = 0.20
    release_qualified: bool = False
    mode: EvalMode = "standard"
    model_sha256: str | None = None
    effective_bpw: float | None = None
    sample_hw_metrics: bool = False
    max_wall_seconds_per_task: float = 180.0
    vre_lambda: float = 3.0
    vre_eta: float = 0.01
    vre_branch_candidates: int = 2


def _git_head_sha(repo_root: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except OSError:
        pass
    return None


def _summarise_budget(
    budget: int,
    task_records: Sequence[dict[str, Any]],
    *,
    num_budgets: int,
    delta_target: float,
    mode: EvalMode,
) -> dict[str, Any]:
    """Compute descriptive, survival/RMST, and simultaneous uncertainty metrics for one budget."""
    n_tasks = len(task_records)
    verified_tasks = sum(1 for r in task_records if r["task_verified"])
    unverified_no_answer_tasks = sum(
        1 for r in task_records if r["final_outcome"] in ("unverified_no_answer", "truncated_budget")
    )
    failure_counts = Counter(r["final_outcome"] for r in task_records if not r["task_verified"])
    ver_level_counts = Counter(r["verification_level"] for r in task_records)

    total_attempts = sum(int(r["attempts_used"]) for r in task_records)
    cum_prompt_tokens = sum(int(r["cumulative_prompt_tokens"]) for r in task_records)
    cum_completion_tokens = sum(int(r["cumulative_completion_tokens"]) for r in task_records)
    cum_total_tokens = sum(int(r["cumulative_total_tokens"]) for r in task_records)
    cum_wall_s = sum(float(r["cumulative_wall_seconds"]) for r in task_records)

    pp_vals = [float(v) for r in task_records for v in r["prompt_tps_samples"] if v is not None]
    tg_vals = [float(v) for r in task_records for v in r["decode_tps_samples"] if v is not None]

    rate = verified_tasks / n_tasks if n_tasks > 0 else 0.0
    unverified_rate = unverified_no_answer_tasks / n_tasks if n_tasks > 0 else 0.0
    alpha_adj = bonferroni_alpha(0.05, num_budgets)
    w_lo, w_hi = wilson_interval(verified_tasks, n_tasks)
    cp_lo, cp_hi = clopper_pearson_interval(verified_tasks, n_tasks, alpha=0.05)
    cp_adj_lo, cp_adj_hi = clopper_pearson_interval(verified_tasks, n_tasks, alpha=alpha_adj)
    hoeff_lo = hoeffding_simultaneous_lower_bound(rate, n_tasks, num_budgets, alpha=0.05)

    # Stopping-time survival analysis on both token axis and wall-clock axis
    tok_obs = [
        StoppingObservation(
            task_id=r["task_id"],
            verified=bool(r["task_verified"]),
            cost_to_first_verified=(
                float(r["tokens_to_first_verified"])
                if r.get("tokens_to_first_verified") is not None
                else None
            ),
            total_cost_spent=float(r["cumulative_completion_tokens"]),
            censored=not bool(r["task_verified"]),
            budget_cap=float(budget),
            discovery_class=str(r.get("discovery_class", "known_benchmark_problem")),
        )
        for r in task_records
    ]
    max_wall_cap = max(
        [float(r["cumulative_wall_seconds"]) for r in task_records] + [1e-3]
    )
    wall_obs = [
        StoppingObservation(
            task_id=r["task_id"],
            verified=bool(r["task_verified"]),
            cost_to_first_verified=(
                float(r["wall_s_to_first_verified"])
                if r.get("wall_s_to_first_verified") is not None
                else None
            ),
            total_cost_spent=float(r["cumulative_wall_seconds"]),
            censored=not bool(r["task_verified"]),
            budget_cap=max_wall_cap,
            discovery_class=str(r.get("discovery_class", "known_benchmark_problem")),
        )
        for r in task_records
    ]

    curve_type = "continuous_policy" if mode in ("adaptive", "vre") else "per_budget_config"
    tok_grid = sorted({max(1.0, float(budget) * f) for f in (0.25, 0.5, 0.75, 1.0)})
    wall_grid = sorted({max(1e-3, max_wall_cap * f) for f in (0.25, 0.5, 0.75, 1.0)})

    surv_tokens = analyse_stopping_times(
        tok_obs, tok_grid, axis_name="tokens", curve_type=curve_type, delta=delta_target
    )
    surv_wall = analyse_stopping_times(
        wall_obs, wall_grid, axis_name="wall_seconds", curve_type=curve_type, delta=delta_target
    )

    # Separate aggregation by discovery_class (Section 1)
    by_discovery_class: dict[str, dict[str, Any]] = {}
    for d_cls in ("known_benchmark_problem", "novel_discovery_candidate"):
        sub = [r for r in task_records if r.get("discovery_class", "known_benchmark_problem") == d_cls]
        if sub:
            v_sub = sum(1 for r in sub if r["task_verified"])
            by_discovery_class[d_cls] = {
                "num_tasks": len(sub),
                "verified_tasks": v_sub,
                "verified_success_rate": round(v_sub / len(sub), 6),
            }

    return {
        "token_budget": budget,
        "curve_type": curve_type,
        "num_tasks": n_tasks,
        "verified_tasks": verified_tasks,
        "verified_success_rate": round(rate, 6),
        "hoeffding_simultaneous_lower": round(hoeff_lo, 6),
        "unverified_tasks": unverified_no_answer_tasks,
        "unverified_rate": round(unverified_rate, 6),
        "verified_solutions_per_second": round(verified_tasks / cum_wall_s, 6) if cum_wall_s > 0.0 else 0.0,
        "tokens_per_verified_solution": (
            round(cum_completion_tokens / verified_tasks, 2) if verified_tasks > 0 else None
        ),
        "total_tokens_per_verified_solution": (
            round(cum_total_tokens / verified_tasks, 2) if verified_tasks > 0 else None
        ),
        "total_attempts": total_attempts,
        "cumulative_prompt_tokens": cum_prompt_tokens,
        "cumulative_completion_tokens": cum_completion_tokens,
        "cumulative_total_tokens": cum_total_tokens,
        "cumulative_wall_seconds": round(cum_wall_s, 4),
        "mean_trial_wall_seconds": round(cum_wall_s / n_tasks, 4) if n_tasks > 0 else None,
        "median_prompt_tps": round(statistics.median(pp_vals), 3) if pp_vals else None,
        "median_decode_tps": round(statistics.median(tg_vals), 3) if tg_vals else None,
        "verification_levels": dict(sorted(ver_level_counts.items())),
        "failure_taxonomy": dict(sorted(failure_counts.items())),
        "by_discovery_class": by_discovery_class,
        "survival_tokens": surv_tokens,
        "survival_wall_seconds": surv_wall,
        "uncertainty_if_iid_sample": {
            "wilson_95": [round(w_lo, 6), round(w_hi, 6)],
            "clopper_pearson_95": [round(cp_lo, 6), round(cp_hi, 6)],
            "clopper_pearson_bonferroni_95": [round(cp_adj_lo, 6), round(cp_adj_hi, 6)],
            "hoeffding_simultaneous_lower_95": round(hoeff_lo, 6),
            "bonferroni_alpha": round(alpha_adj, 6),
            "caveat": (
                "Descriptive fixed-suite proportion k/n is exact for this task set; "
                "binomial and Hoeffding bounds apply only when tasks are treated as "
                "independent draws from a wider distribution."
            ),
        },
        "tasks": list(task_records),
    }


def _update_peak(current: int | None, sample: int | None) -> int | None:
    if sample is None:
        return current
    if current is None:
        return sample
    return max(current, sample)


def run_evaluation(
    client: LocalOpenAIClient,
    tasks: Sequence[MathTask],
    config: RunConfig,
    *,
    jsonl_path: Path | None = None,
    summary_path: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Execute deterministic verified evaluation across all configured token budgets."""
    if not tasks:
        raise ValueError("Task list must be non-empty")
    if not config.budgets:
        raise ValueError("At least one token budget must be supplied")

    root = repo_root or Path(__file__).resolve().parents[2]
    engine_commit = _git_head_sha(root)
    detected_models = client.fetch_models()
    resolved_model = config.model or (detected_models[0] if detected_models else "local-strata")

    if jsonl_path is not None:
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        jsonl_path.write_text("", encoding="utf-8")

    peak_ram_bytes: int | None = None
    peak_vram_bytes: int | None = None

    def _sample_hw() -> tuple[int | None, int | None]:
        nonlocal peak_ram_bytes, peak_vram_bytes
        if not config.sample_hw_metrics:
            return None, None
        ram_info = sample_system_memory_bytes()
        vram_info = sample_gpu_vram_bytes()
        r_used = ram_info["used_ram_bytes"]
        v_used = vram_info["used_vram_bytes"]
        peak_ram_bytes = _update_peak(peak_ram_bytes, r_used)
        peak_vram_bytes = _update_peak(peak_vram_bytes, v_used)
        return r_used, v_used

    _sample_hw()

    budget_summaries: list[dict[str, Any]] = []
    rates_by_budget: dict[int, float] = {}
    started_utc = datetime.now(timezone.utc).isoformat()

    for budget in config.budgets:
        task_records: list[dict[str, Any]] = []
        iterator = tqdm(
            tasks,
            desc=f"TSI[{config.mode}] budget={budget}",
            unit="task",
            disable=not sys.stderr.isatty(),
        )
        for task in iterator:
            task_peak_ram: int | None = None
            task_peak_vram: int | None = None

            if config.mode in ("adaptive", "vre"):
                sched_cfg = SchedulerConfig(
                    mode=config.mode,
                    total_token_budget=budget,
                    max_wall_seconds=config.max_wall_seconds_per_task,
                    max_steps=max(2, config.attempts_per_task),
                    temperature=config.temperature,
                    seed=config.seed,
                    reasoning_effort=config.reasoning_effort,
                    vre_lambda=config.vre_lambda,
                    vre_eta=config.vre_eta,
                    vre_branch_candidates=config.vre_branch_candidates,
                )
                r0, v0 = _sample_hw()
                task_peak_ram = _update_peak(task_peak_ram, r0)
                task_peak_vram = _update_peak(task_peak_vram, v0)
                ares = run_adaptive_task(
                    client=client,
                    task=task,
                    model=resolved_model,
                    config=sched_cfg,
                    quantisation=config.quantization,
                )
                r1, v1 = _sample_hw()
                task_peak_ram = _update_peak(task_peak_ram, r1)
                task_peak_vram = _update_peak(task_peak_vram, v1)

                sec16_row = build_section16_trial_record(
                    task_id=task.task_id,
                    model_id=resolved_model,
                    model_sha256=config.model_sha256,
                    engine_commit=engine_commit,
                    quantisation=config.quantization,
                    seed=config.seed,
                    token_budget=budget,
                    tokens_used=ares.cumulative_completion_tokens,
                    wall_time_ms=ares.cumulative_wall_seconds * 1000.0,
                    attempts=ares.attempts_log,
                    peak_vram_bytes=task_peak_vram,
                    peak_ram_bytes=task_peak_ram,
                    verifier=task.verifier_type,
                    verification_level=ares.verification_level,
                    verified=ares.verified,
                    termination_reason=ares.termination_reason,
                    split=task.split,
                    domain=task.domain,
                    discovery_class=task.discovery_class,
                    mode=config.mode,
                )
                if jsonl_path is not None:
                    with jsonl_path.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(sec16_row, ensure_ascii=False) + "\n")

                task_records.append(
                    {
                        "task_id": task.task_id,
                        "suite": task.suite,
                        "split": task.split,
                        "domain": task.domain,
                        "discovery_class": task.discovery_class,
                        "task_verified": ares.verified,
                        "verification_level": ares.verification_level.value,
                        "final_outcome": ares.final_outcome,
                        "termination_reason": ares.termination_reason,
                        "attempts_used": len(ares.attempts_log),
                        "cumulative_prompt_tokens": ares.cumulative_prompt_tokens,
                        "cumulative_completion_tokens": ares.cumulative_completion_tokens,
                        "cumulative_total_tokens": ares.cumulative_total_tokens,
                        "cumulative_wall_seconds": ares.cumulative_wall_seconds,
                        "tokens_to_first_verified": ares.tokens_to_first_verified,
                        "wall_s_to_first_verified": ares.wall_s_to_first_verified,
                        "prompt_tps_samples": ares.prompt_tps_samples,
                        "decode_tps_samples": ares.decode_tps_samples,
                        "peak_vram_bytes": task_peak_vram,
                        "peak_ram_bytes": task_peak_ram,
                        "attempts": ares.attempts_log,
                        "research_state": ares.research_state_snapshot,
                    }
                )
                continue

            # Standard fixed-budget evaluation path
            attempts_log: list[dict[str, Any]] = []
            task_verified = False
            ver_level = VerificationLevel.UNVERIFIED
            final_outcome = "unverified_no_answer"
            termination_reason = "budget_exhausted"
            cum_prompt = 0
            cum_comp = 0
            cum_total = 0
            cum_wall = 0.0
            tokens_to_first: int | None = None
            wall_to_first: float | None = None
            pp_samples: list[float] = []
            tg_samples: list[float] = []

            for attempt_idx in range(1, max(1, config.attempts_per_task) + 1):
                attempt_seed = config.seed + (attempt_idx - 1)
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": task.prompt},
                ]
                resp = client.chat_completion(
                    messages=messages,
                    max_tokens=budget,
                    model=resolved_model,
                    temperature=config.temperature,
                    seed=attempt_seed,
                    reasoning_effort=config.reasoning_effort,
                )
                r_cur, v_cur = _sample_hw()
                task_peak_ram = _update_peak(task_peak_ram, r_cur)
                task_peak_vram = _update_peak(task_peak_vram, v_cur)

                eval_text = resp.content if resp.content.strip() else resp.reasoning_content
                ver = verify_response(
                    task,
                    eval_text,
                    finish_reason=resp.finish_reason,
                    api_error=resp.api_error,
                    timed_out=resp.timed_out,
                )
                cum_prompt += resp.prompt_tokens
                cum_comp += resp.completion_tokens
                cum_total += resp.total_tokens
                cum_wall += resp.wall_seconds
                if resp.prompt_per_second is not None:
                    pp_samples.append(resp.prompt_per_second)
                if resp.predicted_per_second is not None:
                    tg_samples.append(resp.predicted_per_second)

                attempt_row = {
                    "attempt": attempt_idx,
                    "seed": attempt_seed,
                    "verified": ver.verified,
                    "verification_level": ver.verification_level.value,
                    "outcome": ver.outcome,
                    "verifier": ver.verifier_name,
                    "extracted_answer": ver.extracted_answer,
                    "extraction_source": ver.extraction_source,
                    "verifier_detail": sanitise_public_text(ver.detail),
                    "finish_reason": resp.finish_reason,
                    "prompt_tokens": resp.prompt_tokens,
                    "completion_tokens": resp.completion_tokens,
                    "total_tokens": resp.total_tokens,
                    "wall_seconds": round(resp.wall_seconds, 4),
                    "prompt_per_second": resp.prompt_per_second,
                    "predicted_per_second": resp.predicted_per_second,
                    "api_error": sanitise_public_text(resp.api_error),
                }
                attempts_log.append(attempt_row)
                final_outcome = ver.outcome
                ver_level = ver.verification_level
                if ver.verified:
                    task_verified = True
                    termination_reason = "verified_success"
                    tokens_to_first = cum_comp
                    wall_to_first = round(cum_wall, 4)
                    break
                if ver.outcome == "timeout_error":
                    termination_reason = "timeout"
                elif ver.outcome == "api_error":
                    termination_reason = "api_error"
                elif ver.outcome == "truncated_budget":
                    termination_reason = "token_budget_exhausted"
                else:
                    termination_reason = "attempts_exhausted"

            sec16_row = build_section16_trial_record(
                task_id=task.task_id,
                model_id=resolved_model,
                model_sha256=config.model_sha256,
                engine_commit=engine_commit,
                quantisation=config.quantization,
                seed=config.seed,
                token_budget=budget,
                tokens_used=cum_comp,
                wall_time_ms=cum_wall * 1000.0,
                attempts=attempts_log,
                peak_vram_bytes=task_peak_vram,
                peak_ram_bytes=task_peak_ram,
                verifier=task.verifier_type,
                verification_level=ver_level,
                verified=task_verified,
                termination_reason=termination_reason,
                split=task.split,
                domain=task.domain,
                discovery_class=task.discovery_class,
                mode=config.mode,
            )
            if jsonl_path is not None:
                with jsonl_path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(sec16_row, ensure_ascii=False) + "\n")

            task_records.append(
                {
                    "task_id": task.task_id,
                    "suite": task.suite,
                    "split": task.split,
                    "domain": task.domain,
                    "discovery_class": task.discovery_class,
                    "task_verified": task_verified,
                    "verification_level": ver_level.value,
                    "final_outcome": final_outcome,
                    "termination_reason": termination_reason,
                    "attempts_used": len(attempts_log),
                    "cumulative_prompt_tokens": cum_prompt,
                    "cumulative_completion_tokens": cum_comp,
                    "cumulative_total_tokens": cum_total,
                    "cumulative_wall_seconds": round(cum_wall, 4),
                    "tokens_to_first_verified": tokens_to_first,
                    "wall_s_to_first_verified": wall_to_first,
                    "prompt_tps_samples": pp_samples,
                    "decode_tps_samples": tg_samples,
                    "peak_vram_bytes": task_peak_vram,
                    "peak_ram_bytes": task_peak_ram,
                    "attempts": attempts_log,
                }
            )

        b_sum = _summarise_budget(
            budget,
            task_records,
            num_budgets=len(config.budgets),
            delta_target=config.delta_target,
            mode=config.mode,
        )
        budget_summaries.append(b_sum)
        rates_by_budget[budget] = float(b_sum["verified_success_rate"])
        LOGGER.info(
            "mode=%s budget=%d | verified=%d/%d (%.1f%%) | RMST_tok=%.1f | wall=%.2fs | failures=%s",
            config.mode,
            budget,
            b_sum["verified_tasks"],
            b_sum["num_tasks"],
            b_sum["verified_success_rate"] * 100.0,
            b_sum["survival_tokens"]["rmst_at_b_max"],
            b_sum["cumulative_wall_seconds"],
            b_sum["failure_taxonomy"],
        )

    summary: dict[str, Any] = {
        "schema": TSI_SCHEMA_VERSION,
        "record_schema_version": TSI_RECORD_SCHEMA_VERSION,
        "started_utc": started_utc,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": engine_commit,
        "releaseQualified": False,
        "peak_ram_bytes": peak_ram_bytes,
        "peak_vram_bytes": peak_vram_bytes,
        "config": {
            **asdict(config),
            "model": sanitise_public_text(resolved_model),
            "suite": sanitise_public_text(config.suite),
            "detected_server_models": detected_models,
            "budgets": list(config.budgets),
        },
        "attainment": finite_budget_attainment(rates_by_budget, delta=config.delta_target),
        "budgets": budget_summaries,
    }
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        LOGGER.info("Wrote TSI summary JSON to %s", summary_path)
    return summary


def compare_runs(reference: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Paired comparison of a reference TSI run against a candidate run (Section 4 & 14)."""
    ref_by_b = {int(b["token_budget"]): b for b in reference.get("budgets", [])}
    cand_by_b = {int(b["token_budget"]): b for b in candidate.get("budgets", [])}
    common_budgets = sorted(set(ref_by_b).intersection(cand_by_b))
    if not common_budgets:
        raise ValueError("Reference and candidate runs share no common token budgets.")

    rows: list[dict[str, Any]] = []
    for b in common_budgets:
        rb = ref_by_b[b]
        cb = cand_by_b[b]
        ref_tasks = {t["task_id"]: t for t in rb.get("tasks", [])}
        cand_tasks = {t["task_id"]: t for t in cb.get("tasks", [])}
        common_ids = sorted(set(ref_tasks).intersection(cand_tasks))

        both_pass = 0
        both_fail = 0
        ref_only = 0
        cand_only = 0
        regressions: list[str] = []
        improvements: list[str] = []
        for tid in common_ids:
            rp = bool(ref_tasks[tid]["task_verified"])
            cp = bool(cand_tasks[tid]["task_verified"])
            if rp and cp:
                both_pass += 1
            elif rp and not cp:
                ref_only += 1
                regressions.append(tid)
            elif not rp and cp:
                cand_only += 1
                improvements.append(tid)
            else:
                both_fail += 1

        ref_rate = float(rb["verified_success_rate"])
        cand_rate = float(cb["verified_success_rate"])
        ref_cost = rb.get("mean_trial_wall_seconds")
        cand_cost = cb.get("mean_trial_wall_seconds")
        disc_cmp = None
        if ref_cost and cand_cost and ref_cost > 0.0 and cand_cost > 0.0:
            disc_cmp = compare_quantised_discovery_rate(
                p_ref=ref_rate,
                cost_ref=float(ref_cost),
                p_quant=cand_rate,
                cost_quant=float(cand_cost),
            )

        rows.append(
            {
                "token_budget": b,
                "common_tasks": len(common_ids),
                "reference_verified_rate": ref_rate,
                "candidate_verified_rate": cand_rate,
                "verified_rate_delta": round(cand_rate - ref_rate, 6),
                "reference_unverified_rate": float(rb["unverified_rate"]),
                "candidate_unverified_rate": float(cb["unverified_rate"]),
                "paired_contingency": {
                    "both_pass": both_pass,
                    "ref_pass_cand_fail": ref_only,
                    "ref_fail_cand_pass": cand_only,
                    "both_fail": both_fail,
                },
                "regressions": regressions,
                "improvements": improvements,
                "reference_tokens_per_verified": rb.get("tokens_per_verified_solution"),
                "candidate_tokens_per_verified": cb.get("tokens_per_verified_solution"),
                "reference_verified_per_sec": rb.get("verified_solutions_per_second"),
                "candidate_verified_per_sec": cb.get("verified_solutions_per_second"),
                "reference_rmst_tokens": (rb.get("survival_tokens") or {}).get("rmst_at_b_max"),
                "candidate_rmst_tokens": (cb.get("survival_tokens") or {}).get("rmst_at_b_max"),
                "discovery_rate_model_comparison": disc_cmp,
            }
        )

    return {
        "schema": "strata-tsi-compare-v1",
        "releaseQualified": False,
        "reference": {
            "model": reference.get("config", {}).get("model"),
            "quantization": reference.get("config", {}).get("quantization"),
            "mode": reference.get("config", {}).get("mode", "standard"),
            "kv_mode": reference.get("config", {}).get("kv_mode"),
        },
        "candidate": {
            "model": candidate.get("config", {}).get("model"),
            "quantization": candidate.get("config", {}).get("quantization"),
            "mode": candidate.get("config", {}).get("mode", "standard"),
            "kv_mode": candidate.get("config", {}).get("kv_mode"),
        },
        "budgets": rows,
    }
