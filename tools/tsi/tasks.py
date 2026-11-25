"""Deterministic mathematical reasoning task splits and external loader (Sections 13-14).

Maintains four strictly disjoint built-in splits to enforce benchmark hygiene:
- `dev` (alias `core-v1`): 12 deterministic tasks
- `calibration`: 4 deterministic tasks (for scheduler/threshold calibration)
- `validation`: 4 deterministic tasks (for model/policy selection)
- `frozen-holdout` (alias `holdout-v1`): 8 deterministic tasks (untouched holdout)

Separates `known_benchmark_problem` from `novel_discovery_candidate` so existing
problems are never conflated with independently novelty-checked discoveries.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any, Literal

from .verifier import (
    OutcomeKind,
    VerificationLevel,
    VerificationResult,
    extract_candidate_answer,
    verify_structured_task,
)

DiscoveryClass = Literal["known_benchmark_problem", "novel_discovery_candidate"]
SplitName = Literal["dev", "calibration", "validation", "frozen-holdout"]


@dataclass(frozen=True)
class MathTask:
    """A single deterministic scientific/mathematical reasoning task."""

    task_id: str
    suite: str
    split: str
    domain: str
    prompt: str
    verifier_type: str
    spec: dict[str, Any]
    answer_hint: str
    discovery_class: DiscoveryClass = "known_benchmark_problem"


SYSTEM_PROMPT = (
    "You are a rigorous mathematical assistant. Solve the problem carefully and "
    "present your final answer inside \\boxed{...} (or on a final line prefixed "
    "with FINAL_ANSWER: ). Give an exact integer, reduced fraction a/b, or exact "
    "comma-separated list as requested."
)


def builtin_core_tasks() -> list[MathTask]:
    """Development evaluation split (`dev` / `core-v1`, 12 deterministic tasks)."""
    return [
        MathTask(
            task_id="core-nt-01",
            suite="core-v1",
            split="dev",
            domain="number_theory",
            prompt=(
                "Compute the remainder when 7^100 is divided by 13. "
                "Give the exact integer in \\boxed{...}."
            ),
            verifier_type="exact_int",
            spec={"expected": pow(7, 100, 13)},  # 9
            answer_hint="integer",
        ),
        MathTask(
            task_id="core-nt-02",
            suite="core-v1",
            split="dev",
            domain="number_theory",
            prompt=(
                "Compute Euler's totient function phi(360), the number of integers "
                "k with 1 <= k <= 360 and gcd(k, 360) = 1. Give the exact integer in \\boxed{...}."
            ),
            verifier_type="exact_int",
            spec={"expected": 96},
            answer_hint="integer",
        ),
        MathTask(
            task_id="core-nt-03",
            suite="core-v1",
            split="dev",
            domain="number_theory",
            prompt=(
                "Find the smallest positive integer x satisfying x = 2 (mod 3), "
                "x = 3 (mod 5), and x = 2 (mod 7). Give the exact integer in \\boxed{...}."
            ),
            verifier_type="exact_int",
            spec={"expected": 23},
            answer_hint="integer",
        ),
        MathTask(
            task_id="core-la-01",
            suite="core-v1",
            split="dev",
            domain="linear_algebra",
            prompt=(
                "Let A = [[1, 2], [0, 3]] and B = [[2, -1], [4, 1]]. "
                "Compute Tr(A B) - Tr(B A) + det(A B). Note matrix multiplication is "
                "non-commutative, though trace is cyclic. Give the exact integer in \\boxed{...}."
            ),
            verifier_type="exact_int",
            spec={"expected": 18},
            answer_hint="integer",
        ),
        MathTask(
            task_id="core-la-02",
            suite="core-v1",
            split="dev",
            domain="linear_algebra",
            prompt=(
                "Let A = [[2, 1], [0, 1]] and B = [[1, 0], [3, 2]]. "
                "Compute the top-left entry (row 1, col 1) of the commutator AB - BA. "
                "Give the exact integer in \\boxed{...}."
            ),
            verifier_type="exact_int",
            spec={"expected": 3},
            answer_hint="integer",
        ),
        MathTask(
            task_id="core-comb-01",
            suite="core-v1",
            split="dev",
            domain="combinatorics",
            prompt=(
                "How many ways are there to choose 4 distinct items from 10 distinct items? "
                "Give the exact integer C(10, 4) in \\boxed{...}."
            ),
            verifier_type="exact_int",
            spec={"expected": math.comb(10, 4)},  # 210
            answer_hint="integer",
        ),
        MathTask(
            task_id="core-comb-02",
            suite="core-v1",
            split="dev",
            domain="combinatorics",
            prompt=(
                "A fair 6-sided die is rolled twice independently. What is the exact "
                "probability that the sum of the two faces equals 9? "
                "Write the reduced fraction a/b in \\boxed{...}."
            ),
            verifier_type="exact_rational",
            spec={"expected": "1/9"},
            answer_hint="reduced fraction a/b",
        ),
        MathTask(
            task_id="core-calc-01",
            suite="core-v1",
            split="dev",
            domain="calculus",
            prompt=(
                "Evaluate the definite integral of (3*x^2 + 2*x + 1) dx from x = 0 to x = 2. "
                "Give the exact integer in \\boxed{...}."
            ),
            verifier_type="exact_int",
            spec={"expected": 14},
            answer_hint="integer",
        ),
        MathTask(
            task_id="core-calc-02",
            suite="core-v1",
            split="dev",
            domain="calculus",
            prompt=(
                "Evaluate the definite integral of (x^3 - x) dx from x = 0 to x = 3. "
                "Give the exact reduced fraction a/b in \\boxed{...}."
            ),
            verifier_type="exact_rational",
            spec={"expected": "63/4"},
            answer_hint="reduced fraction a/b",
        ),
        MathTask(
            task_id="core-prob-01",
            suite="core-v1",
            split="dev",
            domain="information_theory",
            prompt=(
                "Consider the range bound KL(p || q) <= r^2 / 8 for logit perturbation span r. "
                "If r = 4/5, what is the exact rational value of r^2 / 8? "
                "Write the reduced fraction a/b in \\boxed{...}."
            ),
            verifier_type="exact_rational",
            spec={"expected": "2/25"},
            answer_hint="reduced fraction a/b",
        ),
        MathTask(
            task_id="core-ce-01",
            suite="core-v1",
            split="dev",
            domain="counterexample",
            prompt=(
                "Consider the false claim: 'For every positive integer n, n^2 + n + 41 is prime.' "
                "Provide any positive integer n >= 1 that is a counterexample (so n^2 + n + 41 is composite). "
                "Give one valid integer in \\boxed{...}."
            ),
            verifier_type="predicate_euler_poly_composite",
            spec={"min_n": 1, "max_n": 100000},
            answer_hint="positive integer n",
        ),
        MathTask(
            task_id="core-ce-02",
            suite="core-v1",
            split="dev",
            domain="counterexample",
            prompt=(
                "Find any integer pair x, y with 1 <= x <= 100 and 1 <= y <= 100 satisfying "
                "7*x - 5*y = 1. Format your answer as two comma-separated integers x,y in \\boxed{x,y}."
            ),
            verifier_type="predicate_linear_diophantine",
            spec={"a": 7, "b": -5, "c": 1, "min_v": 1, "max_v": 100},
            answer_hint="x,y",
        ),
    ]


def builtin_calibration_tasks() -> list[MathTask]:
    """Disjoint calibration split (`calibration`, 4 deterministic tasks)."""
    return [
        MathTask(
            task_id="cal-nt-01",
            suite="calibration-v1",
            split="calibration",
            domain="number_theory",
            prompt=(
                "Compute the remainder when 3^50 is divided by 7. "
                "Give the exact integer in \\boxed{...}."
            ),
            verifier_type="exact_int",
            spec={"expected": pow(3, 50, 7)},  # 3^2 = 2
            answer_hint="integer",
        ),
        MathTask(
            task_id="cal-alg-01",
            suite="calibration-v1",
            split="calibration",
            domain="algebra",
            prompt=(
                "Find all 3 distinct integer roots of the polynomial x^3 - 6*x^2 + 11*x - 6 = 0. "
                "Give them as comma-separated integers in \\boxed{r1,r2,r3}."
            ),
            verifier_type="deterministic_polynomial_roots",
            spec={"coefficients_desc": [1, -6, 11, -6], "expected_root_count": 3},
            answer_hint="r1,r2,r3",
        ),
        MathTask(
            task_id="cal-comb-01",
            suite="calibration-v1",
            split="calibration",
            domain="combinatorics",
            prompt=(
                "Compute the 5th Catalan number C_5 = C(10, 5) / 6. "
                "Give the exact integer in \\boxed{...}."
            ),
            verifier_type="exact_int",
            spec={"expected": 42},
            answer_hint="integer",
        ),
        MathTask(
            task_id="cal-calc-01",
            suite="calibration-v1",
            split="calibration",
            domain="calculus",
            prompt=(
                "Evaluate the definite integral of (2*x + 5) dx from x = 1 to x = 4. "
                "Give the exact integer in \\boxed{...}."
            ),
            verifier_type="exact_int",
            spec={"expected": 30},  # [x^2 + 5x]_1^4 = 36 - 6 = 30
            answer_hint="integer",
        ),
    ]


def builtin_validation_tasks() -> list[MathTask]:
    """Disjoint validation split (`validation`, 4 deterministic tasks)."""
    return [
        MathTask(
            task_id="val-nt-01",
            suite="validation-v1",
            split="validation",
            domain="number_theory",
            prompt=(
                "Compute gcd(252, 198). Give the exact integer in \\boxed{...}."
            ),
            verifier_type="exact_int",
            spec={"expected": math.gcd(252, 198)},  # 18
            answer_hint="integer",
        ),
        MathTask(
            task_id="val-alg-01",
            suite="validation-v1",
            split="validation",
            domain="algebra",
            prompt=(
                "Find both distinct integer roots of x^2 - 5*x - 14 = 0. "
                "Give them as comma-separated integers in \\boxed{r1,r2}."
            ),
            verifier_type="deterministic_polynomial_roots",
            spec={"coefficients_desc": [1, -5, -14], "expected_root_count": 2},
            answer_hint="r1,r2",
        ),
        MathTask(
            task_id="val-la-01",
            suite="validation-v1",
            split="validation",
            domain="linear_algebra",
            prompt=(
                "Let A = [[4, 1], [2, 3]]. Compute det(A) + Tr(A). "
                "Give the exact integer in \\boxed{...}."
            ),
            verifier_type="exact_int",
            spec={"expected": 17},  # det=10, tr=7
            answer_hint="integer",
        ),
        MathTask(
            task_id="val-prob-01",
            suite="validation-v1",
            split="validation",
            domain="information_theory",
            prompt=(
                "For independent trials with single-trial failure probability 1/2, what is the "
                "exact probability of at least one success in 3 independent trials? "
                "Write the reduced fraction a/b in \\boxed{...}."
            ),
            verifier_type="exact_rational",
            spec={"expected": "7/8"},
            answer_hint="reduced fraction a/b",
        ),
    ]


def builtin_holdout_tasks() -> list[MathTask]:
    """Independent frozen holdout split (`frozen-holdout` / `holdout-v1`, 8 tasks)."""
    return [
        MathTask(
            task_id="hold-nt-01",
            suite="holdout-v1",
            split="frozen-holdout",
            domain="number_theory",
            prompt=(
                "Compute the remainder when 5^2026 is divided by 11. "
                "Give the exact integer in \\boxed{...}."
            ),
            verifier_type="exact_int",
            spec={"expected": pow(5, 2026, 11)},  # 5
            answer_hint="integer",
        ),
        MathTask(
            task_id="hold-nt-02",
            suite="holdout-v1",
            split="frozen-holdout",
            domain="number_theory",
            prompt=(
                "Compute the sum of all positive divisors of 72 (including 1 and 72). "
                "Give the exact integer in \\boxed{...}."
            ),
            verifier_type="exact_int",
            spec={"expected": 195},
            answer_hint="integer",
        ),
        MathTask(
            task_id="hold-la-01",
            suite="holdout-v1",
            split="frozen-holdout",
            domain="linear_algebra",
            prompt=(
                "Let A = [[3, 1], [2, 4]] and k = [1, 0]^T. "
                "Compute the Frobenius norm squared of A - 2*I, where I is the 2x2 identity matrix. "
                "Give the exact integer in \\boxed{...}."
            ),
            verifier_type="exact_int",
            spec={"expected": 10},
            answer_hint="integer",
        ),
        MathTask(
            task_id="hold-la-02",
            suite="holdout-v1",
            split="frozen-holdout",
            domain="linear_algebra",
            prompt=(
                "For the 2x2 GDN transition matrix A = (1/2) * (I - (1/2) * k k^T) with unit vector k = [1, 0]^T, "
                "compute the exact determinant det(A). Write the reduced fraction a/b in \\boxed{...}."
            ),
            verifier_type="exact_rational",
            spec={"expected": "1/8"},
            answer_hint="reduced fraction a/b",
        ),
        MathTask(
            task_id="hold-comb-01",
            suite="holdout-v1",
            split="frozen-holdout",
            domain="combinatorics",
            prompt=(
                "How many derangements (permutations with no fixed points) exist for 4 elements? "
                "Give the exact integer in \\boxed{...}."
            ),
            verifier_type="exact_int",
            spec={"expected": 9},
            answer_hint="integer",
        ),
        MathTask(
            task_id="hold-calc-01",
            suite="holdout-v1",
            split="frozen-holdout",
            domain="calculus",
            prompt=(
                "Evaluate the definite integral of (4*x^3 - 3*x^2 + 2) dx from x = 1 to x = 3. "
                "Give the exact integer in \\boxed{...}."
            ),
            verifier_type="exact_int",
            spec={"expected": 58},
            answer_hint="integer",
        ),
        MathTask(
            task_id="hold-info-01",
            suite="holdout-v1",
            split="frozen-holdout",
            domain="information_theory",
            prompt=(
                "Let p = (1/2, 1/2) and perturbation dz = (1, -1). "
                "Compute the exact Fisher quadratic approximation (1/2) * dz^T (diag(p) - p p^T) dz. "
                "Write the exact reduced fraction a/b in \\boxed{...}."
            ),
            verifier_type="exact_rational",
            spec={"expected": "1/2"},
            answer_hint="reduced fraction a/b",
        ),
        MathTask(
            task_id="hold-ce-01",
            suite="holdout-v1",
            split="frozen-holdout",
            domain="counterexample",
            prompt=(
                "Find any integer pair x, y with 1 <= x <= 100 and 1 <= y <= 100 satisfying "
                "11*x - 7*y = 1. Format your answer as two comma-separated integers x,y in \\boxed{x,y}."
            ),
            verifier_type="predicate_linear_diophantine",
            spec={"a": 11, "b": -7, "c": 1, "min_v": 1, "max_v": 100},
            answer_hint="x,y",
        ),
    ]


def get_builtin_suite(name: str) -> list[MathTask]:
    """Return a built-in deterministic evaluation split/suite by name."""
    key = name.strip().lower()
    if key in ("core-v1", "dev"):
        return builtin_core_tasks()
    if key in ("calibration", "calibration-v1"):
        return builtin_calibration_tasks()
    if key in ("validation", "validation-v1"):
        return builtin_validation_tasks()
    if key in ("holdout-v1", "frozen-holdout", "holdout"):
        return builtin_holdout_tasks()
    if key == "all":
        return (
            builtin_core_tasks()
            + builtin_calibration_tasks()
            + builtin_validation_tasks()
            + builtin_holdout_tasks()
        )
    raise ValueError(
        f"Unknown built-in task suite: {name!r} "
        "(expected core-v1/dev, calibration, validation, holdout-v1/frozen-holdout, or all)"
    )


def load_tasks_file(path: Path) -> list[MathTask]:
    """Load external deterministic tasks from a JSON list or JSONL file."""
    raw = path.read_text(encoding="utf-8-sig").strip()
    if not raw:
        raise ValueError(f"Task file is empty: {path}")
    if raw.startswith("["):
        items = json.loads(raw)
    else:
        items = [json.loads(ln) for ln in raw.splitlines() if ln.strip()]
    tasks: list[MathTask] = []
    for idx, obj in enumerate(items):
        if not isinstance(obj, dict):
            raise ValueError(f"Task entry {idx} in {path} is not a JSON object")
        d_cls = str(obj.get("discovery_class", "known_benchmark_problem"))
        if d_cls not in ("known_benchmark_problem", "novel_discovery_candidate"):
            raise ValueError(f"Invalid discovery_class {d_cls!r} in {path}")
        tasks.append(
            MathTask(
                task_id=str(obj["task_id"]),
                suite=str(obj.get("suite", path.stem)),
                split=str(obj.get("split", "custom")),
                domain=str(obj.get("domain", "custom")),
                prompt=str(obj["prompt"]),
                verifier_type=str(obj["verifier_type"]),
                spec=dict(obj["spec"]),
                answer_hint=str(obj.get("answer_hint", "")),
                discovery_class=d_cls,  # type: ignore[arg-type]
            )
        )
    return tasks


def verify_response(
    task: MathTask,
    response_text: str,
    *,
    finish_reason: str | None = None,
    api_error: str | None = None,
    timed_out: bool = False,
) -> VerificationResult:
    """Independently verify a model response against `task`."""
    return verify_structured_task(
        task.verifier_type,
        task.spec,
        response_text,
        finish_reason=finish_reason,
        api_error=api_error,
        timed_out=timed_out,
    )


__all__ = [
    "DiscoveryClass",
    "MathTask",
    "OutcomeKind",
    "SYSTEM_PROMPT",
    "SplitName",
    "VerificationLevel",
    "VerificationResult",
    "builtin_calibration_tasks",
    "builtin_core_tasks",
    "builtin_holdout_tasks",
    "builtin_validation_tasks",
    "extract_candidate_answer",
    "get_builtin_suite",
    "load_tasks_file",
    "verify_response",
]
