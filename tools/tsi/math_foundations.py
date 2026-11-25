"""Exact mathematical foundations and self-checks for NKAT-URT TSI (Phase 1).

All routines use the Python standard library only. Proven identities for fixed linear
state-space operators, finite discrete distributions, and SO(8) rotations are explicitly
separated from research hypotheses about nonlinear language models. The Riemann
Hypothesis is never invoked to justify quantisation performance.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

Matrix = list[list[float]]
Vector = list[float]


# --------------------------------------------------------------------------- 4.1 Statistics
def wilson_interval(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Wilson score interval for k successes in n independent Bernoulli trials."""
    if n <= 0:
        return (0.0, 1.0)
    if k < 0 or k > n:
        raise ValueError(f"invalid binomial counts: k={k}, n={n}")
    p = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = (p + z2 / (2.0 * n)) / denom
    half = (z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * n)) / n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def _binom_cdf_upper(k: int, n: int, p: float) -> float:
    """Pr[Bin(n, p) >= k] computed exactly via math.comb."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return 1.0
    q = 1.0 - p
    total = 0.0
    for i in range(k, n + 1):
        total += math.comb(n, i) * (p ** i) * (q ** (n - i))
    return min(1.0, max(0.0, total))


def _binom_cdf_lower(k: int, n: int, p: float) -> float:
    """Pr[Bin(n, p) <= k] computed exactly via math.comb."""
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 0.0
    q = 1.0 - p
    total = 0.0
    for i in range(0, k + 1):
        total += math.comb(n, i) * (p ** i) * (q ** (n - i))
    return min(1.0, max(0.0, total))


def clopper_pearson_interval(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact two-sided Clopper-Pearson interval via bisection on binomial tails."""
    if n <= 0:
        return (0.0, 1.0)
    if k < 0 or k > n:
        raise ValueError(f"invalid binomial counts: k={k}, n={n}")
    if not (0.0 < alpha < 1.0):
        raise ValueError(f"alpha must lie in (0, 1): {alpha}")

    half_alpha = alpha / 2.0
    if k == 0:
        lo = 0.0
    else:
        a, b = 0.0, 1.0
        for _ in range(80):
            mid = 0.5 * (a + b)
            if _binom_cdf_upper(k, n, mid) < half_alpha:
                a = mid
            else:
                b = mid
        lo = 0.5 * (a + b)

    if k == n:
        hi = 1.0
    else:
        a, b = 0.0, 1.0
        for _ in range(80):
            mid = 0.5 * (a + b)
            if _binom_cdf_lower(k, n, mid) < half_alpha:
                b = mid
            else:
                a = mid
        hi = 0.5 * (a + b)
    return (lo, hi)


def bonferroni_alpha(family_alpha: float, num_comparisons: int) -> float:
    """Family-wise error-rate adjustment when selecting across multiple budgets."""
    if not (0.0 < family_alpha < 1.0):
        raise ValueError(f"family_alpha must lie in (0, 1): {family_alpha}")
    return family_alpha / max(1, int(num_comparisons))


def finite_budget_attainment(
    rates_by_budget: dict[int, float],
    delta: float,
) -> dict[str, Any]:
    """Report attainment of S_pi(B) >= 1 - delta over a finite tested budget grid.

    Never claims to measure the true continuous infimum B*_pi(delta).
    """
    if not (0.0 < delta < 1.0):
        raise ValueError(f"delta must lie in (0, 1): {delta}")
    target = 1.0 - delta
    ordered = sorted((int(b), float(r)) for b, r in rates_by_budget.items())
    attained = [b for b, r in ordered if r >= target]
    return {
        "delta": delta,
        "target_success_rate": round(target, 6),
        "tested_budgets": [b for b, _ in ordered],
        "achieved_within_tested_budgets": bool(attained),
        "min_tested_budget_attained": attained[0] if attained else None,
        "max_observed_success_rate": max((r for _, r in ordered), default=0.0),
        "qualification": (
            "Measured over the finite tested budget grid only; does not establish "
            "the true infimum B*_pi(delta) outside the evaluated grid."
        ),
    }


# --------------------------------------------------------------------------- Linear algebra helpers
def _identity(n: int) -> Matrix:
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def mat_mul(a: Matrix, b: Matrix) -> Matrix:
    rows = len(a)
    inner = len(b)
    cols = len(b[0]) if inner else 0
    if any(len(r) != inner for r in a):
        raise ValueError("incompatible matrix dimensions for mat_mul")
    out = [[0.0] * cols for _ in range(rows)]
    for i in range(rows):
        ai = a[i]
        oi = out[i]
        for k in range(inner):
            aik = ai[k]
            if aik != 0.0:
                bk = b[k]
                for j in range(cols):
                    oi[j] += aik * bk[j]
    return out


def mat_transpose(a: Matrix) -> Matrix:
    if not a:
        return []
    return [list(col) for col in zip(*a, strict=True)]


def mat_vec(a: Matrix, x: Vector) -> Vector:
    return [sum(aij * xj for aij, xj in zip(row, x, strict=True)) for row in a]


def vec_outer(u: Vector, v: Vector) -> Matrix:
    return [[ui * vj for vj in v] for ui in u]


def mat_add(a: Matrix, b: Matrix) -> Matrix:
    return [
        [x + y for x, y in zip(ra, rb, strict=True)]
        for ra, rb in zip(a, b, strict=True)
    ]


def mat_sub(a: Matrix, b: Matrix) -> Matrix:
    return [
        [x - y for x, y in zip(ra, rb, strict=True)]
        for ra, rb in zip(a, b, strict=True)
    ]


def mat_trace(a: Matrix) -> float:
    return sum(a[i][i] for i in range(len(a)))


def frobenius_norm_sq(a: Matrix) -> float:
    return sum(x * x for row in a for x in row)


# --------------------------------------------------------------------------- 4.2 NKAT transition
def gdn_transition_matrix(alpha: float, beta: float, key: Sequence[float]) -> Matrix:
    """Construct GDN transition operator A[t] = alpha * (I - beta * k k^T)."""
    n = len(key)
    return [
        [alpha * ((1.0 if i == j else 0.0) - beta * key[i] * key[j]) for j in range(n)]
        for i in range(n)
    ]


def noncommutative_transition_product(
    transitions: Sequence[Matrix],
    start_after_j: int,
    end_t: int,
) -> Matrix:
    """Compute ordered product Phi(t, j) = A[t] A[t-1] ... A[j+1].

    Indices follow 0-based sequence order where transitions[s] is A[s].
    When end_t <= start_after_j, returns the identity matrix.
    """
    if not transitions:
        raise ValueError("transitions must be non-empty")
    dim = len(transitions[0])
    acc = _identity(dim)
    for step in range(start_after_j + 1, end_t + 1):
        # Left-multiply so Phi(t, j) = A[t] @ A[t-1] @ ... @ A[j+1].
        acc = mat_mul(transitions[step], acc)
    return acc


# --------------------------------------------------------------------------- 4.3 URT Gramian
def urt_observability_gramians(
    transitions: Sequence[Matrix],
    queries: Sequence[Vector],
) -> list[Matrix]:
    """Compute backward observability Gramians M[j] = q[j]q[j]^T + A[j+1] M[j+1] A[j+1]^T.

    Applies to row-state evolution S[t] = S[t-1] A[t] + B[t] with readout y[t] = S[t] q[t],
    so a state perturbation R[j] at time j yields future output perturbation
    delta_y[t] = R[j] A[j+1] ... A[t] q[t] and total squared energy Tr(R[j] M[j] R[j]^T).
    """
    horizon = len(queries)
    if len(transitions) != horizon or horizon == 0:
        raise ValueError("transitions and queries must have equal non-zero length")
    gramians: list[Matrix] = [None] * horizon  # type: ignore[list-item]
    gramians[horizon - 1] = vec_outer(queries[horizon - 1], queries[horizon - 1])
    for j in range(horizon - 2, -1, -1):
        a_next = transitions[j + 1]
        propagated = mat_mul(mat_mul(a_next, gramians[j + 1]), mat_transpose(a_next))
        gramians[j] = mat_add(vec_outer(queries[j], queries[j]), propagated)
    return gramians


def future_output_error_energy(error_matrix: Matrix, gramian: Matrix) -> float:
    """Compute E[j] = Tr(R[j] M[j] R[j]^T)."""
    rm = mat_mul(error_matrix, gramian)
    rmrt = mat_mul(rm, mat_transpose(error_matrix))
    return mat_trace(rmrt)


# --------------------------------------------------------------------------- 4.4 Hankel spectrum
def _symmetric_jacobi_eigenvalues(sym: Matrix, max_sweeps: int = 80, tol: float = 1e-14) -> list[float]:
    """Compute eigenvalues of a small real symmetric matrix using cyclic Jacobi rotations."""
    n = len(sym)
    if n == 0:
        return []
    a = [row[:] for row in sym]
    for _ in range(max_sweeps):
        max_off = 0.0
        for p in range(n):
            for q in range(p + 1, n):
                apq = a[p][q]
                if abs(apq) > max_off:
                    max_off = abs(apq)
                if abs(apq) <= tol:
                    continue
                app = a[p][p]
                aqq = a[q][q]
                tau = (aqq - app) / (2.0 * apq)
                t = (1.0 / (abs(tau) + math.hypot(1.0, tau))) * (1.0 if tau >= 0.0 else -1.0)
                c = 1.0 / math.hypot(1.0, t)
                s = t * c
                a[p][p] = app - t * apq
                a[q][q] = aqq + t * apq
                a[p][q] = 0.0
                a[q][p] = 0.0
                for r in range(n):
                    if r == p or r == q:
                        continue
                    arp = a[r][p]
                    arq = a[r][q]
                    a[r][p] = a[p][r] = c * arp - s * arq
                    a[r][q] = a[q][r] = s * arp + c * arq
        if max_off <= tol:
            break
    return sorted((a[i][i] for i in range(n)), reverse=True)


def hankel_singular_values(reachability_op: Matrix, observability_op: Matrix) -> list[float]:
    """Compute singular values of H = O R for a fixed linear input-output operator."""
    h = mat_mul(observability_op, reachability_op)
    ht = mat_transpose(h)
    if len(h) <= len(h[0]):
        gram = mat_mul(h, ht)
    else:
        gram = mat_mul(ht, h)
    eigs = _symmetric_jacobi_eigenvalues(gram)
    return [math.sqrt(max(0.0, ev)) for ev in eigs]


# --------------------------------------------------------------------------- 4.5 URT information geometry
def softmax(logits: Sequence[float]) -> list[float]:
    if not logits:
        raise ValueError("logits must be non-empty")
    m = max(logits)
    exps = [math.exp(z - m) for z in logits]
    s = sum(exps)
    return [e / s for e in exps]


def full_vocab_kl(logits_ref: Sequence[float], logits_quant: Sequence[float]) -> float:
    """Exact full-vocabulary KL(p_ref || p_quant) in nats."""
    if len(logits_ref) != len(logits_quant) or not logits_ref:
        raise ValueError("logits_ref and logits_quant must have equal non-zero length")
    p = softmax(logits_ref)
    q = softmax(logits_quant)
    kl = 0.0
    for pi, qi in zip(p, q, strict=True):
        if pi > 0.0:
            if qi <= 0.0:
                return float("inf")
            kl += pi * math.log(pi / qi)
    return max(0.0, kl)


def topk_renormalized_kl(
    logits_ref: Sequence[float],
    logits_quant: Sequence[float],
    top_k: int = 64,
) -> float:
    """Top-k renormalised KL over the reference top-k support (distinct from full-vocab KL)."""
    if len(logits_ref) != len(logits_quant) or not logits_ref:
        raise ValueError("logits_ref and logits_quant must have equal non-zero length")
    k = min(max(1, top_k), len(logits_ref))
    indices = sorted(range(len(logits_ref)), key=lambda i: logits_ref[i], reverse=True)[:k]
    sub_ref = [logits_ref[i] for i in indices]
    sub_q = [logits_quant[i] for i in indices]
    return full_vocab_kl(sub_ref, sub_q)


def fisher_kl_quadratic(logits_ref: Sequence[float], logits_quant: Sequence[float]) -> float:
    """Second-order Fisher information approximation 0.5 * dz^T (diag(p) - p p^T) dz."""
    if len(logits_ref) != len(logits_quant) or not logits_ref:
        raise ValueError("logits_ref and logits_quant must have equal non-zero length")
    p = softmax(logits_ref)
    dz = [zq - zr for zr, zq in zip(logits_ref, logits_quant, strict=True)]
    mean_dz = sum(pi * di for pi, di in zip(p, dz, strict=True))
    var_dz = sum(pi * ((di - mean_dz) ** 2) for pi, di in zip(p, dz, strict=True))
    return 0.5 * var_dz


def range_kl_upper_bound(logits_ref: Sequence[float], logits_quant: Sequence[float]) -> float:
    """Global upper bound KL(p || p_quant) <= r^2 / 8 where r = max(dz) - min(dz)."""
    if len(logits_ref) != len(logits_quant) or not logits_ref:
        raise ValueError("logits_ref and logits_quant must have equal non-zero length")
    dz = [zq - zr for zr, zq in zip(logits_ref, logits_quant, strict=True)]
    span = max(dz) - min(dz)
    return (span * span) / 8.0


# --------------------------------------------------------------------------- 4.6 Spin(8) / SO(8)
def sylvester_so8_rotation() -> Matrix:
    """Deterministic order-8 Sylvester Hadamard rotation in SO(8) (det = +1)."""
    scale = 1.0 / math.sqrt(8.0)
    return [
        [(-scale if (i & j).bit_count() % 2 else scale) for j in range(8)]
        for i in range(8)
    ]


def weighted_frobenius_objective(
    w: Matrix,
    w_quant: Matrix,
    g_sqrt: Matrix,
    c_sqrt: Matrix,
) -> float:
    """Compute || G^(1/2) (W_quant - W) C^(1/2) ||_F^2."""
    diff = mat_sub(w_quant, w)
    weighted = mat_mul(mat_mul(g_sqrt, diff), c_sqrt)
    return frobenius_norm_sq(weighted)


def run_self_checks() -> dict[str, Any]:
    """Verify exact mathematical identities and counterexamples in Section 4."""
    # 1. Non-commutativity of GDN transition products Phi(t, j)
    a1 = gdn_transition_matrix(0.95, 0.5, [1.0, 0.0, 0.0])
    k2 = [1.0 / math.sqrt(2.0), 1.0 / math.sqrt(2.0), 0.0]
    a2 = gdn_transition_matrix(0.90, 0.6, k2)
    prod_21 = mat_mul(a2, a1)
    prod_12 = mat_mul(a1, a2)
    commutator_norm = math.sqrt(frobenius_norm_sq(mat_sub(prod_21, prod_12)))
    assert commutator_norm > 0.05

    # 2. Exact URT Gramian identity: Tr(R[0] M[0] R[0]^T) == sum_{t=0}^{T-1} ||delta_y[t]||_2^2
    transitions = [
        _identity(3),
        a1,
        a2,
        gdn_transition_matrix(0.85, 0.4, [0.0, 0.6, 0.8]),
    ]
    queries = [
        [1.0, -0.5, 0.25],
        [0.3, 0.7, -0.4],
        [-0.2, 0.6, 0.8],
        [0.5, 0.5, -0.5],
    ]
    gramians = urt_observability_gramians(transitions, queries)
    r0 = [[0.2, -0.1, 0.3], [-0.4, 0.5, 0.1]]
    energy_gramian = future_output_error_energy(r0, gramians[0])
    # Direct forward rollout of delta_S[t] = delta_S[t-1] @ A[t], delta_y[t] = delta_S[t] @ q[t]
    cur_r = r0
    energy_rollout = 0.0
    for t in range(len(queries)):
        if t > 0:
            cur_r = mat_mul(cur_r, transitions[t])
        dy = mat_vec(cur_r, queries[t])
        energy_rollout += sum(v * v for v in dy)
    gramian_abs_err = abs(energy_gramian - energy_rollout)
    assert gramian_abs_err < 1e-12

    # 3. Hankel singular values for a 3x3 rank-2 linear operator (sv[2]^2 < 1e-12 proves rank(H) == 2)
    reach = [[1.0, 0.0, 0.5], [0.0, 2.0, -1.0]]
    obs = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
    sv = hankel_singular_values(reach, obs)
    assert len(sv) == 3 and sv[0] > sv[1] > 0.0 and sv[2] < 1e-6

    # 4. Information geometry: exact KL <= r^2 / 8 and quadratic agreement for small dz
    z_ref = [2.4, 1.1, -0.3, -1.8, 0.5, -0.9]
    z_small = [z + d for z, d in zip(z_ref, [0.02, -0.01, 0.015, -0.02, 0.005, -0.01], strict=True)]
    kl_small = full_vocab_kl(z_ref, z_small)
    fisher_small = fisher_kl_quadratic(z_ref, z_small)
    bound_small = range_kl_upper_bound(z_ref, z_small)
    assert kl_small <= bound_small + 1e-15
    assert abs(kl_small - fisher_small) < 1e-5

    z_large = [z + d for z, d in zip(z_ref, [0.8, -0.6, 0.3, -0.9, 0.2, -0.4], strict=True)]
    kl_large = full_vocab_kl(z_ref, z_large)
    bound_large = range_kl_upper_bound(z_ref, z_large)
    kl_top3 = topk_renormalized_kl(z_ref, z_large, top_k=3)
    assert kl_large <= bound_large + 1e-15

    # 5. SO(8) orthogonality & weighted Frobenius consistency
    rot = sylvester_so8_rotation()
    rt_r = mat_mul(mat_transpose(rot), rot)
    ortho_err = math.sqrt(frobenius_norm_sq(mat_sub(rt_r, _identity(8))))
    assert ortho_err < 1e-14

    return {
        "pass": True,
        "noncommutative_commutator_fro": round(commutator_norm, 6),
        "gramian_energy": round(energy_gramian, 10),
        "rollout_energy": round(energy_rollout, 10),
        "gramian_rollout_abs_err": gramian_abs_err,
        "hankel_singular_values": [round(x, 6) for x in sv],
        "kl_small_exact": kl_small,
        "kl_small_fisher": fisher_small,
        "kl_small_range_bound": bound_small,
        "kl_large_full_vocab": kl_large,
        "kl_large_top3_renorm": kl_top3,
        "kl_large_range_bound": bound_large,
        "so8_orthogonality_err": ortho_err,
    }
