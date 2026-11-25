"""Non-stationary mutation operator bandits and random baseline (Section 12).

Implements five operator-selection policies under identical API so they can be compared
fairly at equal search budget:
- `UCB1Bandit`
- `SlidingWindowUCBBandit` (adapts to non-stationary evolutionary reward shifts)
- `ThompsonSamplingBandit` (Beta posterior on bounded [0, 1] rewards)
- `CostAwareBandit` (clamped verified_improvement / evaluation_cost)
- `UniformRandomBandit` (mandatory random baseline)

Does NOT claim stationary bandit regret guarantees during non-stationary evolution.
"""

from __future__ import annotations

from collections import deque
import math
import random
from typing import Any, Sequence


class OperatorBandit:
    """Base interface for mutation-operator selection policies."""

    name: str = "base"

    def __init__(self, operators: Sequence[str], seed: int = 42) -> None:
        if not operators:
            raise ValueError("operators must be non-empty")
        self.operators = tuple(operators)
        self.rng = random.Random(seed)
        self.counts = [0] * len(self.operators)
        self.reward_sums = [0.0] * len(self.operators)
        self.cost_sums = [0.0] * len(self.operators)

    def select(self) -> int:
        raise NotImplementedError

    def update(self, arm: int, improvement: float, eval_cost_s: float = 1.0) -> None:
        bounded = min(1.0, max(0.0, float(improvement)))
        cost = max(1e-6, float(eval_cost_s))
        self.counts[arm] += 1
        self.reward_sums[arm] += bounded
        self.cost_sums[arm] += cost

    def summary(self) -> dict[str, Any]:
        return {
            "bandit": self.name,
            "operators": [
                {
                    "name": op,
                    "pulls": self.counts[i],
                    "mean_reward": round(self.reward_sums[i] / max(1, self.counts[i]), 6),
                    "total_cost_s": round(self.cost_sums[i], 6),
                }
                for i, op in enumerate(self.operators)
            ],
        }


class UniformRandomBandit(OperatorBandit):
    """Mandatory baseline: uniform random operator selection."""

    name = "uniform_random"

    def select(self) -> int:
        return self.rng.randrange(len(self.operators))


class UCB1Bandit(OperatorBandit):
    """Classic UCB1: mean_reward + c * sqrt(ln(N) / n_i)."""

    name = "ucb1"

    def __init__(self, operators: Sequence[str], seed: int = 42, c: float = 0.7) -> None:
        super().__init__(operators, seed=seed)
        self.c = float(c)

    def select(self) -> int:
        for i, cnt in enumerate(self.counts):
            if cnt == 0:
                return i
        total = sum(self.counts)
        scores = [
            (self.reward_sums[i] / self.counts[i]) + self.c * math.sqrt(math.log(total) / self.counts[i])
            for i in range(len(self.operators))
        ]
        return max(range(len(scores)), key=lambda i: scores[i])


class SlidingWindowUCBBandit(OperatorBandit):
    """Sliding-window UCB over the most recent `window` evaluations for non-stationary evolution."""

    name = "sliding_window_ucb"

    def __init__(self, operators: Sequence[str], seed: int = 42, window: int = 24, c: float = 0.7) -> None:
        super().__init__(operators, seed=seed)
        self.window = max(4, int(window))
        self.c = float(c)
        self._history: deque[tuple[int, float]] = deque(maxlen=self.window)

    def update(self, arm: int, improvement: float, eval_cost_s: float = 1.0) -> None:
        super().update(arm, improvement, eval_cost_s)
        bounded = min(1.0, max(0.0, float(improvement)))
        self._history.append((arm, bounded))

    def select(self) -> int:
        win_counts = [0] * len(self.operators)
        win_sums = [0.0] * len(self.operators)
        for arm, rew in self._history:
            win_counts[arm] += 1
            win_sums[arm] += rew
        for i, cnt in enumerate(win_counts):
            if cnt == 0:
                return i
        total = len(self._history)
        scores = [
            (win_sums[i] / win_counts[i]) + self.c * math.sqrt(math.log(max(2, total)) / win_counts[i])
            for i in range(len(self.operators))
        ]
        return max(range(len(scores)), key=lambda i: scores[i])


class ThompsonSamplingBandit(OperatorBandit):
    """Beta-distributed Thompson Sampling over bounded [0, 1] improvements."""

    name = "thompson_sampling"

    def __init__(self, operators: Sequence[str], seed: int = 42) -> None:
        super().__init__(operators, seed=seed)
        self._alpha = [1.0] * len(self.operators)
        self._beta = [1.0] * len(self.operators)

    def update(self, arm: int, improvement: float, eval_cost_s: float = 1.0) -> None:
        super().update(arm, improvement, eval_cost_s)
        r = min(1.0, max(0.0, float(improvement)))
        self._alpha[arm] += r
        self._beta[arm] += 1.0 - r

    def select(self) -> int:
        draws = [self.rng.betavariate(self._alpha[i], self._beta[i]) for i in range(len(self.operators))]
        return max(range(len(draws)), key=lambda i: draws[i])


class CostAwareBandit(OperatorBandit):
    """Cost-aware UCB maximising clamped (verified_improvement / evaluation_cost)."""

    name = "cost_aware_ucb"

    def __init__(self, operators: Sequence[str], seed: int = 42, c: float = 0.5, reward_cap: float = 5.0) -> None:
        super().__init__(operators, seed=seed)
        self.c = float(c)
        self.reward_cap = max(0.1, float(reward_cap))
        self._eff_sums = [0.0] * len(self.operators)

    def update(self, arm: int, improvement: float, eval_cost_s: float = 1.0) -> None:
        super().update(arm, improvement, eval_cost_s)
        ratio = min(self.reward_cap, max(0.0, float(improvement)) / max(1e-3, float(eval_cost_s)))
        self._eff_sums[arm] += ratio / self.reward_cap

    def select(self) -> int:
        for i, cnt in enumerate(self.counts):
            if cnt == 0:
                return i
        total = sum(self.counts)
        scores = [
            (self._eff_sums[i] / self.counts[i]) + self.c * math.sqrt(math.log(total) / self.counts[i])
            for i in range(len(self.operators))
        ]
        return max(range(len(scores)), key=lambda i: scores[i])


def make_bandit(name: str, operators: Sequence[str], seed: int = 42) -> OperatorBandit:
    key = name.strip().lower()
    if key == "uniform_random":
        return UniformRandomBandit(operators, seed=seed)
    if key == "ucb1":
        return UCB1Bandit(operators, seed=seed)
    if key == "sliding_window_ucb":
        return SlidingWindowUCBBandit(operators, seed=seed)
    if key == "thompson_sampling":
        return ThompsonSamplingBandit(operators, seed=seed)
    if key == "cost_aware_ucb":
        return CostAwareBandit(operators, seed=seed)
    raise ValueError(f"Unknown bandit type: {name!r}")
