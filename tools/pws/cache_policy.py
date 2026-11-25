"""Byte-budgeted expert cache policy simulator comparing Section 7 policies.

Compares seven policies on identical routing traces and identical byte memory budgets:
- `lru`
- `lfu` (decayed frequency)
- `layer_aware` (layer-weighted latency-per-byte priority)
- `markov` (first-order transition priority p[e]*t[e]/w[e])
- `nkat_seq` (non-commutative sequence priority p[e]*t[e]/w[e])
- `tsi_task` (task-category aware priority)
- `offline_oracle` (Belady's MIN — strictly marked offline upper bound only!)

Reports BOTH expert-count hit rate AND byte-weighted cache hit rate, physical miss
bytes, and eviction counts.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Literal, Sequence

from .expert_predictor import (
    MarkovExpertPredictor,
    NKATSequencePredictor,
    TSITaskAwarePredictor,
    greedy_knapsack_priority,
)
from .trace import RoutingEvent

PolicyName = Literal[
    "lru",
    "lfu",
    "layer_aware",
    "markov",
    "nkat_seq",
    "tsi_task",
    "offline_oracle",
]

ALL_POLICIES: tuple[PolicyName, ...] = (
    "lru",
    "lfu",
    "layer_aware",
    "markov",
    "nkat_seq",
    "tsi_task",
    "offline_oracle",
)


def _next_use_table(events: Sequence[RoutingEvent]) -> list[int]:
    n = len(events)
    nxt = [n] * n
    last: dict[tuple[int, int], int] = {}
    for i in range(n - 1, -1, -1):
        k = events[i].key
        nxt[i] = last.get(k, n)
        last[k] = i
    return nxt


def simulate_cache_policy(
    events: Sequence[RoutingEvent],
    *,
    memory_budget_bytes: int,
    policy: PolicyName,
    layer_stall_weights: dict[int, float] | None = None,
    lfu_decay: float = 0.995,
) -> dict[str, Any]:
    """Simulate a byte-budgeted expert cache under `policy` over `events`."""
    if memory_budget_bytes <= 0:
        raise ValueError(f"memory_budget_bytes must be positive: {memory_budget_bytes}")
    if not events:
        raise ValueError("events must be non-empty")

    resident: OrderedDict[tuple[int, int], int] = OrderedDict()  # key -> weight_bytes
    used_bytes = 0
    hits = 0
    misses = 0
    hit_bytes = 0
    miss_bytes = 0
    evictions = 0

    freq: dict[tuple[int, int], float] = {}
    last_seen: dict[tuple[int, int], int] = {}
    markov = MarkovExpertPredictor()
    nkat = NKATSequencePredictor()
    tsi = TSITaskAwarePredictor()
    oracle_nxt = _next_use_table(events) if policy == "offline_oracle" else []
    oracle_next_pos: dict[tuple[int, int], int] = {}

    def _stall_weight(layer: int) -> float:
        if layer_stall_weights and layer in layer_stall_weights:
            return float(layer_stall_weights[layer])
        # Deeper layers have shorter lead time when prefetching from layer 0
        return 1.0 + 0.05 * float(layer)

    def _resident_priority(key: tuple[int, int], step_idx: int, cur_cat: str) -> float:
        w = resident[key]
        layer, eid = key
        t_saved = _stall_weight(layer)
        f_val = freq.get(key, 0.0)
        if policy == "lfu":
            return f_val
        if policy == "layer_aware":
            return greedy_knapsack_priority(f_val + 1e-6, t_saved, w)
        if policy == "markov":
            pred_p = 0.0
            for pe, pp in markov.predict_probs(layer, top_m=16):
                if pe == eid:
                    pred_p = pp
                    break
            p_eff = 0.7 * pred_p + 0.3 * min(1.0, f_val / max(1.0, step_idx + 1.0))
            return greedy_knapsack_priority(p_eff + 1e-6, t_saved, w)
        if policy == "nkat_seq":
            pred_p = nkat.predict_prob_of(layer, eid)
            p_eff = 0.75 * pred_p + 0.25 * min(1.0, f_val / max(1.0, step_idx + 1.0))
            return greedy_knapsack_priority(p_eff + 1e-6, t_saved, w)
        if policy == "tsi_task":
            pred_p = tsi.predict_prob_of(cur_cat, layer, eid)
            p_eff = 0.80 * pred_p + 0.20 * min(1.0, f_val / max(1.0, step_idx + 1.0))
            return greedy_knapsack_priority(p_eff + 1e-6, t_saved, w)
        return 0.0

    def _evict_one(step_idx: int, cur_cat: str) -> None:
        nonlocal used_bytes, evictions
        if not resident:
            return
        if policy == "lru":
            victim, v_bytes = resident.popitem(last=False)
            used_bytes -= v_bytes
            evictions += 1
            return
        if policy == "offline_oracle":
            victim = max(resident.keys(), key=lambda k: (oracle_next_pos.get(k, len(events)), -resident[k]))
            used_bytes -= resident.pop(victim)
            oracle_next_pos.pop(victim, None)
            evictions += 1
            return
        # Greedy lowest-priority eviction (oldest on tie)
        victim = min(
            resident.keys(),
            key=lambda k: (_resident_priority(k, step_idx, cur_cat), last_seen.get(k, -1)),
        )
        used_bytes -= resident.pop(victim)
        evictions += 1

    for idx, ev in enumerate(events):
        key = ev.key
        w = ev.weight_bytes
        if idx > 0 and idx % 64 == 0 and freq:
            for fk in list(freq.keys()):
                freq[fk] *= lfu_decay

        if key in resident:
            hits += 1
            hit_bytes += w
            resident.move_to_end(key)
        else:
            misses += 1
            miss_bytes += w
            if w <= memory_budget_bytes:
                while used_bytes + w > memory_budget_bytes and resident:
                    _evict_one(idx, ev.task_category)
                resident[key] = w
                used_bytes += w

        freq[key] = freq.get(key, 0.0) + 1.0
        last_seen[key] = idx
        if policy == "offline_oracle" and key in resident:
            oracle_next_pos[key] = oracle_nxt[idx]
        markov.observe(ev.layer, ev.expert)
        nkat.observe(ev.layer, ev.expert)
        tsi.observe(ev.task_category, ev.layer, ev.expert)

    total_lookups = hits + misses
    total_bytes = hit_bytes + miss_bytes
    return {
        "policy": policy,
        "deployable_online": policy != "offline_oracle",
        "memory_budget_bytes": memory_budget_bytes,
        "total_lookups": total_lookups,
        "hits": hits,
        "misses": misses,
        "evictions": evictions,
        "expert_hit_rate": round(hits / max(1, total_lookups), 6),
        "byte_weighted_hit_rate": round(hit_bytes / max(1, total_bytes), 6),
        "physical_miss_bytes": miss_bytes,
        "total_logical_bytes": total_bytes,
        "final_resident_count": len(resident),
        "final_resident_bytes": used_bytes,
    }


def compare_all_cache_policies(
    events: Sequence[RoutingEvent],
    *,
    memory_budget_bytes: int,
    policies: Sequence[PolicyName] = ALL_POLICIES,
) -> dict[str, Any]:
    """Replay all requested Section 7 policies on the identical trace and byte budget."""
    results = [
        simulate_cache_policy(events, memory_budget_bytes=memory_budget_bytes, policy=p)
        for p in policies
    ]
    return {
        "memory_budget_bytes": memory_budget_bytes,
        "num_events": len(events),
        "distinct_experts": len({e.key for e in events}),
        "policies": results,
        "note": (
            "`offline_oracle` uses future trace knowledge (Belady's MIN) as an upper bound "
            "only and is not deployable online. Greedy priority p*t/w is an approximation "
            "to the integer knapsack placement problem."
        ),
    }
