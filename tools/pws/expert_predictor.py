"""Online expert usage predictors for NKAT-URT Predictive Weight Streaming (Section 7).

Implements:
- `MarkovExpertPredictor`: first-order per-layer transition probability P(e_t | e_{t-1})
- `NKATSequencePredictor`: order-sensitive non-commutative sequence predictor P(e_t | e_{t-2}, e_{t-1})
  explicitly distinguishing ordered sequences (A, B) from (B, A)
- `TSITaskAwarePredictor`: task-category conditional frequency estimator (math/code/general)
- `greedy_knapsack_priority`: priority[e] = p[e] * t[e] / w[e] (explicitly documented as
  a greedy approximation to the 0-1 integer knapsack placement problem).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Mapping, Sequence


def greedy_knapsack_priority(
    prob_needed: float,
    marginal_stall_saved_s: float,
    expert_bytes: int,
) -> float:
    """Section 7 greedy knapsack heuristic priority[e] = p[e] * t[e] / w[e].

    Not an exact solver for the general 0-1 integer knapsack problem.
    """
    if expert_bytes <= 0:
        raise ValueError(f"expert_bytes must be positive: {expert_bytes}")
    if prob_needed < 0.0 or marginal_stall_saved_s < 0.0:
        raise ValueError("prob_needed and marginal_stall_saved_s must be non-negative")
    return (prob_needed * marginal_stall_saved_s) / float(expert_bytes)


class MarkovExpertPredictor:
    """First-order per-layer Markov expert predictor P(next_expert | prev_expert, layer)."""

    def __init__(self, smoothing: float = 0.05) -> None:
        self.smoothing = max(1e-6, float(smoothing))
        self._last_by_layer: dict[int, int] = {}
        self._trans: dict[tuple[int, int], dict[int, float]] = defaultdict(lambda: defaultdict(float))
        self._totals: dict[tuple[int, int], float] = defaultdict(float)

    def observe(self, layer: int, expert: int) -> None:
        prev = self._last_by_layer.get(layer)
        if prev is not None:
            self._trans[(layer, prev)][expert] += 1.0
            self._totals[(layer, prev)] += 1.0
        self._last_by_layer[layer] = expert

    def predict_probs(self, layer: int, top_m: int = 4) -> list[tuple[int, float]]:
        prev = self._last_by_layer.get(layer)
        if prev is None:
            return []
        counts = self._trans.get((layer, prev))
        total = self._totals.get((layer, prev), 0.0)
        if not counts or total <= 0.0:
            return []
        denom = total + self.smoothing * len(counts)
        scored = [
            (eid, (cnt + self.smoothing) / denom)
            for eid, cnt in counts.items()
        ]
        scored.sort(key=lambda x: (-x[1], x[0]))
        return scored[: max(1, top_m)]


class NKATSequencePredictor:
    """Non-commutative order-2 sequence predictor P(e_t | (e_{t-2}, e_{t-1}), layer).

    Explicitly preserves operator ordering: transition counts after (A, B) are kept
    strictly separate from counts after (B, A), with backoff to first-order Markov.
    """

    def __init__(self, decay: float = 0.985) -> None:
        self.decay = min(1.0, max(0.5, float(decay)))
        self._hist: dict[int, list[int]] = defaultdict(list)
        self._bigram: dict[tuple[int, int, int], dict[int, float]] = defaultdict(lambda: defaultdict(float))
        self._unigram_tr: dict[tuple[int, int], dict[int, float]] = defaultdict(lambda: defaultdict(float))

    def observe(self, layer: int, expert: int) -> None:
        h = self._hist[layer]
        if len(h) >= 2:
            ctx2 = (layer, h[-2], h[-1])
            d2 = self._bigram[ctx2]
            for k in list(d2.keys()):
                d2[k] *= self.decay
            d2[expert] += 1.0
        if len(h) >= 1:
            ctx1 = (layer, h[-1])
            d1 = self._unigram_tr[ctx1]
            for k in list(d1.keys()):
                d1[k] *= self.decay
            d1[expert] += 1.0
        h.append(expert)
        if len(h) > 4:
            del h[:-4]

    def predict_probs(self, layer: int, top_m: int = 4) -> list[tuple[int, float]]:
        h = self._hist.get(layer)
        if not h:
            return []
        counts: Mapping[int, float] | None = None
        if len(h) >= 2:
            counts = self._bigram.get((layer, h[-2], h[-1]))
        if not counts:
            counts = self._unigram_tr.get((layer, h[-1]))
        if not counts:
            return []
        total = sum(counts.values())
        if total <= 0.0:
            return []
        scored = [(eid, cnt / total) for eid, cnt in counts.items()]
        scored.sort(key=lambda x: (-x[1], x[0]))
        return scored[: max(1, top_m)]

    def predict_prob_of(self, layer: int, expert: int) -> float:
        for eid, prob in self.predict_probs(layer, top_m=64):
            if eid == expert:
                return prob
        return 0.0


class TSITaskAwarePredictor:
    """Task-category conditional frequency predictor separating math/code/general routing."""

    def __init__(self, decay: float = 0.99) -> None:
        self.decay = min(1.0, max(0.5, float(decay)))
        self._counts: dict[tuple[str, int], dict[int, float]] = defaultdict(lambda: defaultdict(float))
        self._totals: dict[tuple[str, int], float] = defaultdict(float)

    def observe(self, task_category: str, layer: int, expert: int) -> None:
        bucket = (task_category, layer)
        self._counts[bucket][expert] += 1.0
        self._totals[bucket] += 1.0

    def predict_prob_of(self, task_category: str, layer: int, expert: int) -> float:
        bucket = (task_category, layer)
        tot = self._totals.get(bucket, 0.0)
        if tot <= 0.0:
            return 0.0
        return self._counts[bucket].get(expert, 0.0) / tot

    def top_experts(self, task_category: str, layer: int, top_m: int = 4) -> list[tuple[int, float]]:
        bucket = (task_category, layer)
        tot = self._totals.get(bucket, 0.0)
        if tot <= 0.0:
            return []
        scored = [(eid, cnt / tot) for eid, cnt in self._counts[bucket].items()]
        scored.sort(key=lambda x: (-x[1], x[0]))
        return scored[: max(1, top_m)]


def evaluate_predictor_accuracy(
    events: Sequence[tuple[int, int, str]],
    *,
    top_k_pred: int = 2,
) -> dict[str, float]:
    """Compare online next-expert hit@k of Markov, NKATSequence, and TSITaskAware predictors."""
    markov = MarkovExpertPredictor()
    nkat = NKATSequencePredictor()
    tsi = TSITaskAwarePredictor()
    hits = {"markov": 0, "nkat_seq": 0, "tsi_task": 0}
    total = len(events)
    if total == 0:
        return {k: 0.0 for k in hits}

    for layer, eid, cat in events:
        if eid in {e for e, _ in markov.predict_probs(layer, top_m=top_k_pred)}:
            hits["markov"] += 1
        if eid in {e for e, _ in nkat.predict_probs(layer, top_m=top_k_pred)}:
            hits["nkat_seq"] += 1
        if eid in {e for e, _ in tsi.top_experts(cat, layer, top_m=top_k_pred)}:
            hits["tsi_task"] += 1
        markov.observe(layer, eid)
        nkat.observe(layer, eid)
        tsi.observe(cat, layer, eid)

    return {k: round(v / total, 6) for k, v in hits.items()}
