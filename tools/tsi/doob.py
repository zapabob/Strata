"""Doob h-transform, committor recursion, Feynman-Kac tree solver, and step-level controller.

Implements Section 4, Section 8, and Section 13 of the VRE specification:
- Exact backward committor recursion g(u) = P(V_q = 1 | u) on finite proof-search trees/DAGs
- Doob harmonic potential h_lambda(u) = 1 + (exp(lambda) - 1) * g(u)
- Theorem 3 exact next-step law q*_lambda(a | u) = p(a | u) * h_lambda(ua) / h_lambda(u)
  and conditioned success limit q*_inf(a | u) = p(a | u) * g(ua) / g(u)
- Feynman-Kac cost-penalised backward recursion:
      h_t(u) = sum_a p(a | u) * exp(-eta * c_t(u, a)) * h_{t+1}(ua)
      q*_t(a | u) = p(a | u) * exp(-eta * c_t(u, a)) * h_{t+1}(ua) / h_t(u)
- Practical step-level Gibbs/Doob candidate selector for real Strata inference when raw
  token-level logits are unavailable over the Chat Completions endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

from .variational import PathOutcome, feynman_kac_gibbs_ensemble


@dataclass(frozen=True)
class TreeEdge:
    """Directed branch from prefix `u` taking action `action` to child `child`."""

    action: str
    child: str
    prior_prob: float
    step_cost: float = 0.0


@dataclass(frozen=True)
class FiniteSearchTree:
    """Finite acyclic proof-search tree/DAG for exact Doob & Feynman-Kac verification."""

    root: str
    # Non-terminal transitions: node -> sequence of TreeEdge whose prior_probs sum to 1
    edges: Mapping[str, Sequence[TreeEdge]]
    # Terminal nodes: node -> verified reward V in {0.0, 1.0}
    terminals: Mapping[str, float]

    def validate(self) -> None:
        if self.root not in self.edges and self.root not in self.terminals:
            raise ValueError(f"Root {self.root!r} not found in edges or terminals")
        for node, elist in self.edges.items():
            if node in self.terminals:
                raise ValueError(f"Node {node!r} cannot be both non-terminal and terminal")
            if not elist:
                raise ValueError(f"Non-terminal node {node!r} has no outgoing edges")
            s = sum(e.prior_prob for e in elist)
            if abs(s - 1.0) > 1e-9 or any(e.prior_prob < 0.0 for e in elist):
                raise ValueError(f"Edge priors at {node!r} must be non-negative and sum to 1 (got {s})")
            for e in elist:
                if e.child not in self.edges and e.child not in self.terminals:
                    raise ValueError(f"Child node {e.child!r} from {node!r} is undefined")
        for node, v in self.terminals.items():
            if v not in (0.0, 1.0):
                raise ValueError(f"Terminal verification reward at {node!r} must be 0.0 or 1.0 (got {v})")

    def enumerate_paths(self) -> list[PathOutcome]:
        """Enumerate every root-to-terminal path with exact prior probability and cumulative cost."""
        self.validate()
        out: list[PathOutcome] = []

        def dfs(node: str, trail: list[str], prob: float, cost: float) -> None:
            if node in self.terminals:
                out.append(
                    PathOutcome(
                        path_id="/".join(trail) if trail else node,
                        prior_prob=prob,
                        verified=float(self.terminals[node]),
                        cost=cost,
                    )
                )
                return
            for e in self.edges[node]:
                dfs(e.child, trail + [e.action], prob * e.prior_prob, cost + e.step_cost)

        dfs(self.root, [], 1.0, 0.0)
        return out


def compute_committor(tree: FiniteSearchTree) -> dict[str, float]:
    """Compute exact committor g(u) = P(V_q = 1 | u) via backward recursion."""
    tree.validate()
    memo: dict[str, float] = {}

    def solve(node: str) -> float:
        if node in memo:
            return memo[node]
        if node in tree.terminals:
            memo[node] = float(tree.terminals[node])
            return memo[node]
        val = sum(e.prior_prob * solve(e.child) for e in tree.edges[node])
        memo[node] = val
        return val

    solve(tree.root)
    return memo


def compute_doob_potentials(
    tree: FiniteSearchTree,
    *,
    lam: float,
    eta: float = 0.0,
) -> dict[str, float]:
    """Compute exact Feynman-Kac / Doob backward potentials h(u).

    When eta == 0, satisfies h_lambda(u) = 1 + (exp(lambda) - 1) * g(u).
    For general eta >= 0:
        h(u_terminal) = exp(lambda * V(u_terminal))
        h(u) = sum_a p(a | u) * exp(-eta * c(u, a)) * h(child)
    """
    tree.validate()
    memo: dict[str, float] = {}

    def solve(node: str) -> float:
        if node in memo:
            return memo[node]
        if node in tree.terminals:
            memo[node] = math.exp(lam * float(tree.terminals[node]))
            return memo[node]
        val = sum(
            e.prior_prob * math.exp(-eta * e.step_cost) * solve(e.child)
            for e in tree.edges[node]
        )
        memo[node] = val
        return val

    solve(tree.root)
    return memo


def doob_step_policy(
    tree: FiniteSearchTree,
    potentials: Mapping[str, float],
    *,
    eta: float = 0.0,
) -> dict[str, dict[str, float]]:
    """Construct next-step distribution q(a | u) proportional to p(a | u) * exp(-eta*c) * h(ua)."""
    tree.validate()
    policy: dict[str, dict[str, float]] = {}
    for node, elist in tree.edges.items():
        unnorm = [e.prior_prob * math.exp(-eta * e.step_cost) * float(potentials[e.child]) for e in elist]
        z = sum(unnorm)
        if z <= 0.0:
            raise ValueError(f"Zero normalising constant at node {node!r}")
        policy[node] = {e.action: w / z for e, w in zip(elist, unnorm, strict=True)}
    return policy


def doob_conditioned_success_policy(tree: FiniteSearchTree) -> dict[str, dict[str, float]]:
    """Theorem 3 limit lambda -> infinity: q*_inf(a | u) = p(a | u) * g(ua) / g(u) where g(u) > 0."""
    g = compute_committor(tree)
    policy: dict[str, dict[str, float]] = {}
    for node, elist in tree.edges.items():
        if g[node] <= 0.0:
            continue
        policy[node] = {e.action: (e.prior_prob * g[e.child]) / g[node] for e in elist}
    return policy


def rollout_policy_path_probs(
    tree: FiniteSearchTree,
    policy: Mapping[str, Mapping[str, float]],
) -> dict[str, float]:
    """Compute exact terminal path distribution induced by a step-level policy on `tree`."""
    tree.validate()
    probs: dict[str, float] = {}

    def dfs(node: str, trail: list[str], p_acc: float) -> None:
        if node in tree.terminals:
            pid = "/".join(trail) if trail else node
            probs[pid] = p_acc
            return
        step_dist = policy[node]
        for e in tree.edges[node]:
            dfs(e.child, trail + [e.action], p_acc * float(step_dist[e.action]))

    dfs(tree.root, [], 1.0)
    return probs


def verify_doob_gibbs_equivalence(
    tree: FiniteSearchTree,
    *,
    lam: float,
    eta: float = 0.0,
) -> dict[str, Any]:
    """Verify Theorem 3 & Section 8: rolling out Doob/Feynman-Kac q*_t matches exact Gibbs Q*_{lam, eta}."""
    h = compute_doob_potentials(tree, lam=lam, eta=eta)
    pol = doob_step_policy(tree, h, eta=eta)
    rollout = rollout_policy_path_probs(tree, pol)
    paths = tree.enumerate_paths()
    gibbs = feynman_kac_gibbs_ensemble(paths, lam=lam, eta=eta)

    max_err = 0.0
    for row in gibbs["paths"]:
        pid = row["path_id"]
        err = abs(rollout[pid] - float(row["posterior_prob"]))
        if err > max_err:
            max_err = err

    return {
        "lambda": lam,
        "eta": eta,
        "h_root": h[tree.root],
        "exp_log_Z": math.exp(gibbs["log_Z"]),
        "root_partition_abs_err": abs(h[tree.root] - math.exp(gibbs["log_Z"])),
        "max_path_prob_abs_err": max_err,
        "equivalent": max_err < 1e-12 and abs(h[tree.root] - math.exp(gibbs["log_Z"])) < 1e-12,
    }


# --------------------------------------------------------------------------- Practical step-level VRE selector
@dataclass(frozen=True)
class StepCandidate:
    """One candidate proof/reasoning step scored by an empirical committor and step cost."""

    candidate_id: str
    prior_weight: float
    estimated_committor: float
    estimated_cost: float
    verified_immediately: bool = False


def select_step_candidates_gibbs(
    candidates: Sequence[StepCandidate],
    *,
    lam: float,
    eta: float = 0.0,
) -> dict[str, Any]:
    """Compute step-level Doob/Gibbs weights q(c) proportional to p(c) * exp(-eta*cost) * h_hat(c).

    Used when raw token logits are not exposed by the inference server (Section 13).
    Estimated committors are explicitly treated as empirical heuristics unless accompanied
    by certified uniform residual bounds.
    """
    if not candidates:
        raise ValueError("candidates must be non-empty")
    if lam <= 0.0:
        raise ValueError(f"lam must be positive: {lam}")
    if eta < 0.0:
        raise ValueError(f"eta must be non-negative: {eta}")

    log_weights: list[float] = []
    h_vals: list[float] = []
    for cand in candidates:
        if cand.prior_weight <= 0.0:
            raise ValueError(f"prior_weight must be positive for {cand.candidate_id!r}")
        g_hat = 1.0 if cand.verified_immediately else min(1.0, max(0.0, float(cand.estimated_committor)))
        # Exact terminal potential if verified immediately, else h_hat = 1 + (e^lam - 1)*g_hat
        if g_hat >= 1.0:
            log_h = lam
            h_v = math.exp(lam)
        else:
            # Stable log(1 + (e^lam - 1) * g_hat)
            h_v = 1.0 + math.expm1(lam) * g_hat
            log_h = math.log(max(1e-300, h_v))
        h_vals.append(h_v)
        log_weights.append(math.log(cand.prior_weight) - eta * cand.estimated_cost + log_h)

    m = max(log_weights)
    raw = [math.exp(lw - m) for lw in log_weights]
    total = sum(raw)
    probs = [r / total for r in raw]
    ranked_indices = sorted(range(len(candidates)), key=lambda i: probs[i], reverse=True)
    best_idx = ranked_indices[0]

    return {
        "selected_candidate_id": candidates[best_idx].candidate_id,
        "lambda": lam,
        "eta": eta,
        "ranked_candidates": [
            {
                "candidate_id": candidates[i].candidate_id,
                "estimated_committor": candidates[i].estimated_committor,
                "estimated_cost": candidates[i].estimated_cost,
                "verified_immediately": candidates[i].verified_immediately,
                "h_hat": round(h_vals[i], 6),
                "gibbs_weight": round(probs[i], 6),
            }
            for i in ranked_indices
        ],
    }
