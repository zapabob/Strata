"""Stage B/C/VRE adaptive reasoning scheduler outside the GPU engine (Sections 7-9 & VRE Section 13).

Implements practical, strictly bounded empirical reasoning policies on top of
`ResearchState`, independent verifiers, and step-level Doob/Gibbs candidate selection:
- `adaptive`: Failure-guided retry, continuation on truncation, counterexample critique,
  lemma decomposition, and formatting repair under strict cumulative token & wall budgets.
- `vre`: Step-level Doob/Gibbs candidate selection over multiple proposed reasoning branches
  when token-level raw logits are unavailable via `/v1/chat/completions`.

Explicitly marks every scheduler as an empirical heuristic (never an optimal Bellman policy)
and gates `ESCALATE_PRECISION` behind four mandatory safety checks.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time
from typing import Any, Literal

from .client import CompletionResponse, LocalOpenAIClient
from .doob import StepCandidate, select_step_candidates_gibbs
from .research_state import ResearchAction, ResearchState, VerifiedLemma
from .tasks import SYSTEM_PROMPT, MathTask, verify_response
from .verifier import VerificationLevel, VerificationResult

LOGGER = logging.getLogger("strata.tsi.scheduler")

SchedulerMode = Literal["adaptive", "vre"]


@dataclass(frozen=True)
class PrecisionEscalationGate:
    """Four-condition safety gate for ESCALATE_PRECISION (Section 9 & Section 19)."""

    allow_escalation: bool = False
    target_model_present: bool = False
    user_approved: bool = False
    free_ram_bytes: int | None = None
    free_vram_bytes: int | None = None
    min_free_ram_bytes: int = 3 * 1024 * 1024 * 1024  # 3 GiB floor
    min_free_vram_bytes: int = 768 * 1024 * 1024      # 768 MiB floor
    switch_cost_s: float = 0.0

    def can_escalate(self, remaining_time_s: float) -> tuple[bool, str]:
        if not self.allow_escalation:
            return False, "precision_escalation_disabled"
        if not self.user_approved:
            return False, "user_approval_missing"
        if not self.target_model_present:
            return False, "target_model_not_present"
        if self.free_ram_bytes is None or self.free_ram_bytes < self.min_free_ram_bytes:
            return False, "insufficient_free_ram_floor"
        if self.free_vram_bytes is None or self.free_vram_bytes < self.min_free_vram_bytes:
            return False, "insufficient_free_vram_floor"
        if self.switch_cost_s >= remaining_time_s:
            return False, "switch_cost_exceeds_remaining_time_budget"
        return True, "escalation_permitted"


@dataclass(frozen=True)
class SchedulerConfig:
    """Configuration for bounded adaptive or step-level VRE reasoning."""

    mode: SchedulerMode = "adaptive"
    total_token_budget: int = 512
    max_wall_seconds: float = 180.0
    max_steps: int = 3
    initial_slice_fraction: float = 0.50
    temperature: float = 0.0
    retry_temperature: float = 0.25
    seed: int = 42
    reasoning_effort: str | None = None
    vre_lambda: float = 3.0
    vre_eta: float = 0.01
    vre_branch_candidates: int = 2
    escalation_gate: PrecisionEscalationGate = PrecisionEscalationGate()


@dataclass(frozen=True)
class AdaptiveTaskResult:
    """Complete execution outcome for one task under the adaptive/VRE scheduler."""

    task_id: str
    policy_label: str
    verified: bool
    verification_level: VerificationLevel
    final_outcome: str
    termination_reason: str
    attempts_log: list[dict[str, Any]]
    cumulative_prompt_tokens: int
    cumulative_completion_tokens: int
    cumulative_total_tokens: int
    cumulative_wall_seconds: float
    tokens_to_first_verified: int | None
    wall_s_to_first_verified: float | None
    prompt_tps_samples: list[float]
    decode_tps_samples: list[float]
    research_state_snapshot: dict[str, Any]


def _build_followup_prompt(
    task: MathTask,
    action: ResearchAction,
    prev_text: str,
    prev_ver: VerificationResult,
) -> str:
    """Construct an independent failure-guided follow-up prompt without leaking ground truth."""
    snippet = prev_text.strip()[-400:] if prev_text.strip() else "(empty output)"
    if action == ResearchAction.CONTINUE_REASONING:
        return (
            f"{task.prompt}\n\n"
            "Your previous attempt was truncated at the token budget before finishing. "
            "Proceed concisely directly to the calculation and output ONLY the final result "
            f"in \\boxed{{...}} ({task.answer_hint})."
        )
    if action == ResearchAction.VERIFY_CANDIDATE:
        return (
            f"{task.prompt}\n\n"
            f"Your previous response failed formatting verification ({prev_ver.outcome}). "
            "Do not use prose for the final answer. Emit the exact final value cleanly inside "
            f"\\boxed{{...}} ({task.answer_hint})."
        )
    if action == ResearchAction.SEARCH_COUNTEREXAMPLE:
        return (
            f"{task.prompt}\n\n"
            "An independent verifier rejected your previous candidate answer "
            f"({prev_ver.extracted_answer!r}). Check for an arithmetic or algebraic counterexample "
            "to your previous reasoning, recompute independently from scratch using a second method, "
            f"and provide the corrected exact answer inside \\boxed{{...}} ({task.answer_hint})."
        )
    if action == ResearchAction.GENERATE_LEMMA:
        return (
            f"{task.prompt}\n\n"
            f"Previous attempt excerpt:\n{snippet}\n\n"
            "Break the problem into one small intermediate lemma, check it explicitly, then "
            f"deduce the exact final answer in \\boxed{{...}} ({task.answer_hint})."
        )
    return (
        f"{task.prompt}\n\n"
        "Restart cleanly from first principles with a concise derivation and place the exact "
        f"answer inside \\boxed{{...}} ({task.answer_hint})."
    )


def _select_next_action(prev_outcome: str, step_idx: int) -> ResearchAction:
    """Deterministic empirical action policy conditioned on independent verifier feedback."""
    if prev_outcome == "truncated_budget":
        return ResearchAction.CONTINUE_REASONING
    if prev_outcome in ("format_error", "unverified_no_answer"):
        return ResearchAction.VERIFY_CANDIDATE
    if prev_outcome == "verified_fail":
        return ResearchAction.SEARCH_COUNTEREXAMPLE if step_idx == 1 else ResearchAction.GENERATE_LEMMA
    if prev_outcome in ("timeout_error", "api_error"):
        return ResearchAction.RESTART_REASONING
    return ResearchAction.RESTART_REASONING


def _empirical_committor_score(ver: VerificationResult, resp: CompletionResponse) -> float:
    """Heuristic committor estimate g_hat in (0, 1) used solely for step-level VRE ranking."""
    if ver.verified:
        return 1.0
    if ver.outcome in ("api_error", "timeout_error", "verifier_error"):
        return 0.02
    if ver.outcome == "truncated_budget":
        return 0.35 if resp.completion_tokens > 0 else 0.10
    if ver.outcome == "format_error":
        return 0.45
    if ver.outcome == "unverified_no_answer":
        return 0.25
    if ver.outcome == "verified_fail":
        return 0.20
    return 0.15


def run_adaptive_task(
    *,
    client: LocalOpenAIClient,
    task: MathTask,
    model: str,
    config: SchedulerConfig,
    quantisation: str = "unspecified",
) -> AdaptiveTaskResult:
    """Execute bounded adaptive or step-level VRE reasoning for a single task."""
    policy_label = (
        "step_level_vre_heuristic" if config.mode == "vre" else "empirical_heuristic_scheduler"
    )
    state = ResearchState(
        unresolved_goals=[task.task_id],
        model_configuration={
            "model": model,
            "quantisation": quantisation,
            "mode": config.mode,
            "policy_label": policy_label,
        },
        remaining_token_budget=max(1, int(config.total_token_budget)),
        remaining_time_budget=max(0.1, float(config.max_wall_seconds)),
        remaining_memory_budget=config.escalation_gate.free_vram_bytes,
    )

    attempts_log: list[dict[str, Any]] = []
    cum_prompt = 0
    cum_comp = 0
    cum_total = 0
    cum_wall = 0.0
    pp_samples: list[float] = []
    tg_samples: list[float] = []

    verified = False
    ver_level = VerificationLevel.UNVERIFIED
    final_outcome = "unverified_no_answer"
    termination_reason = "budget_exhausted"
    tokens_to_first: int | None = None
    wall_to_first: float | None = None

    prev_text = ""
    prev_ver: VerificationResult | None = None
    consecutive_api_errors = 0
    started = time.perf_counter()

    max_steps = max(1, int(config.max_steps))
    for step_idx in range(max_steps):
        elapsed = time.perf_counter() - started
        if state.remaining_token_budget <= 0:
            termination_reason = "token_budget_exhausted"
            break
        if elapsed >= config.max_wall_seconds or state.remaining_time_budget <= 0.0:
            termination_reason = "time_budget_exhausted"
            break

        # Allocate per-step token slice strictly within remaining_token_budget.
        if step_idx == 0 and max_steps > 1:
            slice_tokens = max(
                16,
                min(
                    state.remaining_token_budget,
                    int(round(config.total_token_budget * config.initial_slice_fraction)),
                ),
            )
        else:
            slice_tokens = state.remaining_token_budget

        if step_idx == 0:
            action = ResearchAction.CONTINUE_REASONING
            prompt_text = task.prompt
            temp = config.temperature
        else:
            assert prev_ver is not None
            action = _select_next_action(prev_ver.outcome, step_idx)
            prompt_text = _build_followup_prompt(task, action, prev_text, prev_ver)
            temp = config.retry_temperature if action != ResearchAction.VERIFY_CANDIDATE else 0.0

        # In step-level VRE mode on retry steps, sample up to `vre_branch_candidates` branches if budget allows.
        num_branches = 1
        if (
            config.mode == "vre"
            and step_idx > 0
            and config.vre_branch_candidates > 1
            and state.remaining_token_budget >= 32
        ):
            num_branches = min(config.vre_branch_candidates, max(1, state.remaining_token_budget // 32))
            slice_tokens = max(16, state.remaining_token_budget // num_branches)

        branch_results: list[tuple[StepCandidate, CompletionResponse, VerificationResult, str, int]] = []
        for b_idx in range(num_branches):
            if state.remaining_token_budget <= 0 or state.remaining_time_budget <= 0.0:
                break
            req_max_toks = min(slice_tokens, state.remaining_token_budget)
            attempt_num = len(attempts_log) + 1
            attempt_seed = config.seed + (attempt_num - 1)
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_text},
            ]
            resp = client.chat_completion(
                messages=messages,
                max_tokens=req_max_toks,
                model=model,
                temperature=temp if b_idx == 0 else max(0.25, temp + 0.15 * b_idx),
                seed=attempt_seed,
                reasoning_effort=config.reasoning_effort,
            )
            eval_text = resp.content if resp.content.strip() else resp.reasoning_content
            ver = verify_response(
                task,
                eval_text,
                finish_reason=resp.finish_reason,
                api_error=resp.api_error,
                timed_out=resp.timed_out,
            )

            # Account for every token and millisecond spent, including failures and errors.
            tokens_charged = max(resp.completion_tokens, 1 if resp.api_error is None else 0)
            cum_prompt += resp.prompt_tokens
            cum_comp += resp.completion_tokens
            cum_total += resp.total_tokens
            cum_wall += resp.wall_seconds
            if resp.prompt_per_second is not None:
                pp_samples.append(resp.prompt_per_second)
            if resp.predicted_per_second is not None:
                tg_samples.append(resp.predicted_per_second)

            new_lemma = None
            if ver.verified:
                new_lemma = VerifiedLemma(
                    lemma_id=f"{task.task_id}:step{attempt_num}",
                    statement=f"Verified solution {ver.extracted_answer}",
                    verification_level=ver.verification_level,
                    verifier_name=ver.verifier_name,
                )
            else:
                state.record_failed_attempt(
                    attempt_index=attempt_num,
                    outcome=ver.outcome,
                    extracted_answer=ver.extracted_answer,
                    detail=ver.detail,
                    tokens_used=resp.completion_tokens,
                    wall_s=resp.wall_seconds,
                )
                if action == ResearchAction.SEARCH_COUNTEREXAMPLE and ver.extracted_answer is not None:
                    state.record_counterexample(ver.extracted_answer, ver.detail, verified=False)

            trace_entry = state.apply_action(
                action=action,
                cost_tokens=tokens_charged,
                cost_wall_s=resp.wall_seconds,
                verified=ver.verified,
                verification_level=ver.verification_level,
                new_lemma=new_lemma,
                resolved_goal=task.task_id if ver.verified else None,
                note=ver.outcome,
            )

            attempt_row = {
                "attempt": attempt_num,
                "step": step_idx + 1,
                "branch": b_idx + 1,
                "action": action.value,
                "seed": attempt_seed,
                "requested_max_tokens": req_max_toks,
                "verified": ver.verified,
                "verification_level": ver.verification_level.value,
                "outcome": ver.outcome,
                "verifier": ver.verifier_name,
                "extracted_answer": ver.extracted_answer,
                "extraction_source": ver.extraction_source,
                "verifier_detail": ver.detail,
                "finish_reason": resp.finish_reason,
                "prompt_tokens": resp.prompt_tokens,
                "completion_tokens": resp.completion_tokens,
                "total_tokens": resp.total_tokens,
                "wall_seconds": round(resp.wall_seconds, 4),
                "prompt_per_second": resp.prompt_per_second,
                "predicted_per_second": resp.predicted_per_second,
                "api_error": resp.api_error,
                "state_hash_after": trace_entry.state_hash_after,
            }
            attempts_log.append(attempt_row)

            cand = StepCandidate(
                candidate_id=f"attempt-{attempt_num}",
                prior_weight=1.0 / num_branches,
                estimated_committor=_empirical_committor_score(ver, resp),
                estimated_cost=float(resp.completion_tokens) + resp.wall_seconds,
                verified_immediately=ver.verified,
            )
            branch_results.append((cand, resp, ver, eval_text, attempt_num))

            final_outcome = ver.outcome
            if ver.verified:
                verified = True
                ver_level = ver.verification_level
                termination_reason = "verified_success"
                tokens_to_first = cum_comp
                wall_to_first = cum_wall
                break

            if ver.outcome == "api_error":
                consecutive_api_errors += 1
                if consecutive_api_errors >= 2:
                    termination_reason = "api_disconnected"
                    break
            else:
                consecutive_api_errors = 0

        if verified or termination_reason == "api_disconnected":
            break

        if not branch_results:
            termination_reason = "token_budget_exhausted"
            break

        # Choose the highest Gibbs/Doob weighted candidate to seed the next step.
        if len(branch_results) > 1 and config.mode == "vre":
            sel = select_step_candidates_gibbs(
                [br[0] for br in branch_results],
                lam=config.vre_lambda,
                eta=config.vre_eta,
            )
            chosen_id = sel["selected_candidate_id"]
            chosen = next(br for br in branch_results if br[0].candidate_id == chosen_id)
        else:
            chosen = branch_results[-1]

        _, _, prev_ver, prev_text, _ = chosen

    if not verified and termination_reason not in ("token_budget_exhausted", "time_budget_exhausted", "api_disconnected"):
        if state.remaining_token_budget <= 0:
            termination_reason = "token_budget_exhausted"
        elif state.remaining_time_budget <= 0.0:
            termination_reason = "time_budget_exhausted"
        else:
            termination_reason = "max_steps_reached"

    return AdaptiveTaskResult(
        task_id=task.task_id,
        policy_label=policy_label,
        verified=verified,
        verification_level=ver_level,
        final_outcome=final_outcome,
        termination_reason=termination_reason,
        attempts_log=attempts_log,
        cumulative_prompt_tokens=cum_prompt,
        cumulative_completion_tokens=cum_comp,
        cumulative_total_tokens=cum_total,
        cumulative_wall_seconds=round(cum_wall, 4),
        tokens_to_first_verified=tokens_to_first,
        wall_s_to_first_verified=round(wall_to_first, 4) if wall_to_first is not None else None,
        prompt_tps_samples=pp_samples,
        decode_tps_samples=tg_samples,
        research_state_snapshot=state.to_snapshot(),
    )
