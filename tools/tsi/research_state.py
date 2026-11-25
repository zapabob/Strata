"""Non-commutative ResearchState and proof-search action operators (Section 8).

Tracks the exact nine state fields mandated by Section 8:
- unresolved_goals
- verified_lemmas (strictly separated from unverified reasoning attempts!)
- counterexamples
- failed_attempts
- proof_dependencies
- model_configuration
- remaining_token_budget
- remaining_time_budget
- remaining_memory_budget

Every transition records operator order, state hashes before/after, verification status,
and dependency edges, explicitly capturing non-commutativity A_i A_j != A_j A_i.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any

from .verifier import VerificationLevel


class ResearchAction(str, Enum):
    """Canonical proof-search and reasoning actions (Section 7)."""

    CONTINUE_REASONING = "CONTINUE_REASONING"
    RESTART_REASONING = "RESTART_REASONING"
    SEARCH_COUNTEREXAMPLE = "SEARCH_COUNTEREXAMPLE"
    GENERATE_LEMMA = "GENERATE_LEMMA"
    VERIFY_CANDIDATE = "VERIFY_CANDIDATE"
    RETRIEVE_VERIFIED_KNOWLEDGE = "RETRIEVE_VERIFIED_KNOWLEDGE"
    ESCALATE_PRECISION = "ESCALATE_PRECISION"


@dataclass(frozen=True)
class VerifiedLemma:
    """An independently verified lemma that may enter the verified knowledge store."""

    lemma_id: str
    statement: str
    verification_level: VerificationLevel
    verifier_name: str
    dependencies: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.verification_level == VerificationLevel.UNVERIFIED:
            raise ValueError(
                "Unverified content cannot be stored in VerifiedLemma; "
                "verified_lemmas and unverified attempts must remain strictly separated."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "lemma_id": self.lemma_id,
            "statement": self.statement,
            "verification_level": self.verification_level.value,
            "verifier_name": self.verifier_name,
            "dependencies": list(self.dependencies),
        }


@dataclass(frozen=True)
class OperationTraceEntry:
    """Audit record for a single non-commutative state transition A_a."""

    step: int
    action: ResearchAction
    state_hash_before: str
    state_hash_after: str
    verified: bool
    verification_level: VerificationLevel
    cost_tokens: int
    cost_wall_s: float
    dependency_ids: tuple[str, ...] = ()
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "action": self.action.value,
            "state_hash_before": self.state_hash_before,
            "state_hash_after": self.state_hash_after,
            "verified": self.verified,
            "verification_level": self.verification_level.value,
            "cost_tokens": self.cost_tokens,
            "cost_wall_s": round(self.cost_wall_s, 6),
            "dependency_ids": list(self.dependency_ids),
            "note": self.note,
        }


@dataclass
class ResearchState:
    """Structured state for non-commutative verified proof search (Section 8)."""

    unresolved_goals: list[str]
    model_configuration: dict[str, Any]
    remaining_token_budget: int
    remaining_time_budget: float
    remaining_memory_budget: int | None
    verified_lemmas: list[VerifiedLemma] = field(default_factory=list)
    counterexamples: list[dict[str, Any]] = field(default_factory=list)
    failed_attempts: list[dict[str, Any]] = field(default_factory=list)
    proof_dependencies: dict[str, list[str]] = field(default_factory=dict)
    operator_trace: list[OperationTraceEntry] = field(default_factory=list)

    def state_digest(self) -> str:
        """Deterministic SHA-256 digest of the semantic research state (order-sensitive)."""
        payload = {
            "unresolved_goals": self.unresolved_goals,
            "verified_lemma_ids": [lm.lemma_id for lm in self.verified_lemmas],
            "counterexample_count": len(self.counterexamples),
            "failed_attempt_count": len(self.failed_attempts),
            "proof_dependencies": self.proof_dependencies,
            "model_configuration": self.model_configuration,
            "remaining_token_budget": self.remaining_token_budget,
            "remaining_time_budget_ms": int(round(self.remaining_time_budget * 1000.0)),
            "remaining_memory_budget": self.remaining_memory_budget,
            "action_history": [entry.action.value for entry in self.operator_trace],
        }
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()[:16]

    def add_verified_lemma(self, lemma: VerifiedLemma) -> None:
        """Insert a verified lemma into the verified store (never accepts UNVERIFIED)."""
        if not isinstance(lemma, VerifiedLemma):
            raise TypeError("Only VerifiedLemma instances may enter verified_lemmas")
        if any(existing.lemma_id == lemma.lemma_id for existing in self.verified_lemmas):
            return
        self.verified_lemmas.append(lemma)
        self.proof_dependencies[lemma.lemma_id] = list(lemma.dependencies)

    def record_failed_attempt(
        self,
        *,
        attempt_index: int,
        outcome: str,
        extracted_answer: str | None,
        detail: str,
        tokens_used: int,
        wall_s: float,
    ) -> None:
        """Record an unverified/failed attempt strictly outside `verified_lemmas`."""
        self.failed_attempts.append(
            {
                "attempt": attempt_index,
                "outcome": outcome,
                "extracted_answer": extracted_answer,
                "detail": detail,
                "tokens_used": tokens_used,
                "wall_s": round(wall_s, 6),
            }
        )

    def record_counterexample(self, candidate: str, detail: str, verified: bool) -> None:
        self.counterexamples.append(
            {
                "candidate": candidate,
                "detail": detail,
                "verified": verified,
            }
        )

    def consume_budget(self, *, tokens: int, wall_s: float) -> None:
        self.remaining_token_budget = max(0, self.remaining_token_budget - max(0, int(tokens)))
        self.remaining_time_budget = max(0.0, self.remaining_time_budget - max(0.0, float(wall_s)))

    def apply_action(
        self,
        *,
        action: ResearchAction,
        cost_tokens: int,
        cost_wall_s: float,
        verified: bool = False,
        verification_level: VerificationLevel = VerificationLevel.UNVERIFIED,
        new_lemma: VerifiedLemma | None = None,
        resolved_goal: str | None = None,
        dependency_ids: tuple[str, ...] = (),
        note: str = "",
    ) -> OperationTraceEntry:
        """Apply one non-commutative operator A_a, updating budgets, lemmas, and trace."""
        before = self.state_digest()
        self.consume_budget(tokens=cost_tokens, wall_s=cost_wall_s)
        if new_lemma is not None:
            self.add_verified_lemma(new_lemma)
        if resolved_goal is not None and resolved_goal in self.unresolved_goals:
            self.unresolved_goals.remove(resolved_goal)
            if dependency_ids:
                self.proof_dependencies[resolved_goal] = list(dependency_ids)
        after = self.state_digest()
        entry = OperationTraceEntry(
            step=len(self.operator_trace) + 1,
            action=action,
            state_hash_before=before,
            state_hash_after=after,
            verified=verified,
            verification_level=verification_level,
            cost_tokens=cost_tokens,
            cost_wall_s=cost_wall_s,
            dependency_ids=dependency_ids,
            note=note,
        )
        self.operator_trace.append(entry)
        return entry

    def to_snapshot(self) -> dict[str, Any]:
        return {
            "state_digest": self.state_digest(),
            "unresolved_goals": list(self.unresolved_goals),
            "verified_lemmas": [lm.to_dict() for lm in self.verified_lemmas],
            "counterexamples": list(self.counterexamples),
            "failed_attempts": list(self.failed_attempts),
            "proof_dependencies": dict(self.proof_dependencies),
            "model_configuration": dict(self.model_configuration),
            "remaining_token_budget": self.remaining_token_budget,
            "remaining_time_budget": round(self.remaining_time_budget, 6),
            "remaining_memory_budget": self.remaining_memory_budget,
            "operator_trace": [e.to_dict() for e in self.operator_trace],
        }
