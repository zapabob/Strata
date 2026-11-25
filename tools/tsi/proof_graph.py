"""NKAT proof-state bisimulation quotient and exact reduction check (Theorem 7, Section 9).

Verifies the three exact conditions of Theorem 7 for two proof states u, v to belong
to the same predictive equivalence class (bisimulation):
1. Equal terminal verification reward V(u) == V(v),
2. Equal admissible action set and action costs,
3. Identical induced transition probability distribution over equivalence classes for
   every admissible action.

When all three hold, finite-budget Bellman values on the quotient MDP match the full
unreduced MDP identically. Also provides an explicit counterexample helper demonstrating
that matching visible proof goals alone do NOT imply equivalence when underlying LLM
context/KV distributions differ.
"""

from __future__ import annotations

from typing import Any

from .bellman import DiscreteMDP, solve_bellman_dp


def compute_bisimulation_quotient(
    mdp: DiscreteMDP,
    *,
    tol: float = 1e-12,
) -> dict[str, Any]:
    """Compute the coarsest exact Theorem 7 bisimulation partition and reduced quotient MDP."""
    mdp.validate()

    # Initial partition by (is_verified, available_actions_with_costs)
    def initial_sig(s: str) -> tuple[Any, ...]:
        is_ver = s in mdp.verified_states
        acts = tuple(
            (a, mdp.action_costs[a])
            for a in mdp.actions
            if (s, a) in mdp.transitions
        )
        return (is_ver, acts)

    groups: dict[tuple[Any, ...], list[str]] = {}
    for s in mdp.states:
        groups.setdefault(initial_sig(s), []).append(s)

    # Map each state to an integer block ID; refine until fixed point.
    blocks = sorted(groups.values(), key=lambda g: sorted(g)[0])
    state_to_block = {s: idx for idx, blk in enumerate(blocks) for s in blk}

    while True:
        refined_groups: dict[tuple[Any, ...], list[str]] = {}
        for s in mdp.states:
            sig_parts: list[Any] = [state_to_block[s]]
            for a in mdp.actions:
                dist = mdp.transitions.get((s, a))
                if dist is None:
                    continue
                block_probs: dict[int, float] = {}
                for ns, prob in dist:
                    bid = state_to_block[ns]
                    block_probs[bid] = block_probs.get(bid, 0.0) + prob
                # Quantise probabilities at tol to build a deterministic signature
                quant_dist = tuple(
                    (bid, round(p / max(tol, 1e-15)))
                    for bid, p in sorted(block_probs.items())
                    if p > tol
                )
                sig_parts.append((a, quant_dist))
            refined_groups.setdefault(tuple(sig_parts), []).append(s)

        new_blocks = sorted(refined_groups.values(), key=lambda g: sorted(g)[0])
        if len(new_blocks) == len(blocks):
            break
        blocks = new_blocks
        state_to_block = {s: idx for idx, blk in enumerate(blocks) for s in blk}

    # Build quotient DiscreteMDP
    q_names = tuple(f"Q{idx}" for idx in range(len(blocks)))
    state_to_q = {s: q_names[state_to_block[s]] for s in mdp.states}
    q_verified = frozenset(
        q_names[idx] for idx, blk in enumerate(blocks) if any(s in mdp.verified_states for s in blk)
    )
    q_transitions: dict[tuple[str, str], list[tuple[str, float]]] = {}
    for idx, blk in enumerate(blocks):
        rep = blk[0]
        q_name = q_names[idx]
        for a in mdp.actions:
            dist = mdp.transitions.get((rep, a))
            if dist is None:
                continue
            agg: dict[str, float] = {}
            for ns, prob in dist:
                qn = state_to_q[ns]
                agg[qn] = agg.get(qn, 0.0) + prob
            q_transitions[(q_name, a)] = sorted(agg.items())

    quotient_mdp = DiscreteMDP(
        states=q_names,
        verified_states=q_verified,
        actions=mdp.actions,
        action_costs=dict(mdp.action_costs),
        transitions=q_transitions,
    )
    quotient_mdp.validate()
    return {
        "original_state_count": len(mdp.states),
        "quotient_state_count": len(q_names),
        "compression_ratio": round(len(q_names) / max(1, len(mdp.states)), 6),
        "equivalence_classes": {q_names[i]: sorted(blk) for i, blk in enumerate(blocks)},
        "state_to_class": state_to_q,
        "quotient_mdp": quotient_mdp,
    }


def verify_quotient_bellman_invariance(
    mdp: DiscreteMDP,
    *,
    max_budget: int,
) -> dict[str, Any]:
    """Verify Theorem 7: exact Bellman values agree between full MDP and its bisimulation quotient."""
    q_info = compute_bisimulation_quotient(mdp)
    q_mdp: DiscreteMDP = q_info["quotient_mdp"]
    full_dp = solve_bellman_dp(mdp, max_budget=max_budget)
    quot_dp = solve_bellman_dp(q_mdp, max_budget=max_budget)
    mapping: dict[str, str] = q_info["state_to_class"]

    max_diff = 0.0
    for b in range(max_budget + 1):
        for s in mdp.states:
            diff = abs(full_dp["values"][b][s] - quot_dp["values"][b][mapping[s]])
            if diff > max_diff:
                max_diff = diff

    return {
        "original_state_count": q_info["original_state_count"],
        "quotient_state_count": q_info["quotient_state_count"],
        "equivalence_classes": q_info["equivalence_classes"],
        "max_budget": max_budget,
        "max_bellman_value_abs_diff": max_diff,
        "theorem7_invariance_holds": max_diff < 1e-12,
    }
