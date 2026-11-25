"""NKAT / GDN memory diagnostics and low-rank residual compensation simulation (Stage D).

Implements Section 11 & Stage D on the key-dimension space (d_k x d_k) without
materialising full LLM Hankel matrices:
- Non-commutative GDN transition contraction rates ||Phi(t, j)||
- Key non-orthogonality diagnostics max_{i != j} |k_i^T k_j|
- Backward observability Gramians M[j] and eigenspectrum
- Time-correlated vs uncorrelated quantisation error energy amplification
- Low-rank residual compensation simulation:
      U[t] = Y[t] - Q(Y[t]),  H[t] = U[t] V V^T,  S_corrected[t] = Q(Y[t]) + H[t]
  including explicit FLOP and DRAM-byte overhead accounting.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

from .math_foundations import (
    Matrix,
    Vector,
    frobenius_norm_sq,
    future_output_error_energy,
    gdn_transition_matrix,
    mat_add,
    mat_mul,
    mat_sub,
    mat_transpose,
    mat_vec,
    noncommutative_transition_product,
    urt_observability_gramians,
)


def symmetric_jacobi_eigh(
    sym: Matrix,
    *,
    max_sweeps: int = 100,
    tol: float = 1e-13,
) -> tuple[list[float], Matrix]:
    """Compute eigenvalues (descending) and orthonormal eigenvectors (columns) of a real symmetric matrix."""
    n = len(sym)
    if n == 0:
        return [], []
    a = [row[:] for row in sym]
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
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
                    if r != p and r != q:
                        arp = a[r][p]
                        arq = a[r][q]
                        a[r][p] = a[p][r] = c * arp - s * arq
                        a[r][q] = a[q][r] = s * arp + c * arq
                    vrp = v[r][p]
                    vrq = v[r][q]
                    v[r][p] = c * vrp - s * vrq
                    v[r][q] = s * vrp + c * vrq
        if max_off <= tol:
            break

    order = sorted(range(n), key=lambda i: a[i][i], reverse=True)
    eigvals = [a[i][i] for i in order]
    eigvecs = [[v[row][col] for col in order] for row in range(n)]
    return eigvals, eigvecs


def _spectral_norm(mat: Matrix) -> float:
    """Operator 2-norm sigma_max(A) via symmetric Jacobi eigenvalues of A^T A."""
    gram = mat_mul(mat_transpose(mat), mat)
    eigs, _ = symmetric_jacobi_eigh(gram)
    return math.sqrt(max(0.0, eigs[0])) if eigs else 0.0


def analyse_gdn_trajectory(
    *,
    alphas: Sequence[float],
    betas: Sequence[float],
    keys: Sequence[Vector],
    queries: Sequence[Vector],
    step_errors: Sequence[Matrix] | None = None,
) -> dict[str, Any]:
    """Run NKAT/URT memory diagnostics along a GDN key/query/gate trajectory."""
    horizon = len(keys)
    if not (len(alphas) == len(betas) == len(queries) == horizon) or horizon == 0:
        raise ValueError("alphas, betas, keys, and queries must have equal non-zero length")

    transitions = [
        gdn_transition_matrix(float(a), float(b), k)
        for a, b, k in zip(alphas, betas, keys, strict=True)
    ]
    gramians = urt_observability_gramians(transitions, queries)

    # Contraction rates of cumulative products Phi(t, 0)
    contraction_norms: list[float] = []
    for t in range(horizon):
        phi = noncommutative_transition_product(transitions, start_after_j=0, end_t=t)
        contraction_norms.append(round(_spectral_norm(phi), 6))

    # Key non-orthogonality (pairwise max cosine magnitude)
    max_non_ortho = 0.0
    norms = [math.sqrt(sum(x * x for x in k)) for k in keys]
    for i in range(horizon):
        for j in range(i + 1, horizon):
            denom = norms[i] * norms[j]
            if denom > 0.0:
                cos_val = abs(sum(a * b for a, b in zip(keys[i], keys[j], strict=True)) / denom)
                if cos_val > max_non_ortho:
                    max_non_ortho = cos_val

    gram0_eigs, _ = symmetric_jacobi_eigh(gramians[0])
    out: dict[str, Any] = {
        "horizon": horizon,
        "key_dim": len(keys[0]),
        "contraction_spectral_norms_from_t0": contraction_norms,
        "max_key_non_orthogonality_abs_cos": round(max_non_ortho, 6),
        "gramian_t0_eigenvalues": [round(max(0.0, ev), 8) for ev in gram0_eigs],
        "gramian_t0_trace": round(sum(max(0.0, ev) for ev in gram0_eigs), 8),
    }

    if step_errors is not None:
        if len(step_errors) != horizon:
            raise ValueError("step_errors must match trajectory horizon")
        # Independent/uncorrelated sum of per-step energies vs exact coherent rollout energy.
        uncorrelated_energy = sum(
            future_output_error_energy(err, gram)
            for err, gram in zip(step_errors, gramians, strict=True)
        )
        rows = len(step_errors[0])
        cols = len(step_errors[0][0])
        cur_delta: Matrix = [[0.0] * cols for _ in range(rows)]
        coherent_energy = 0.0
        for t in range(horizon):
            if t > 0:
                cur_delta = mat_mul(cur_delta, transitions[t])
            cur_delta = mat_add(cur_delta, step_errors[t])
            dy = mat_vec(cur_delta, queries[t])
            coherent_energy += sum(val * val for val in dy)
        ratio = coherent_energy / uncorrelated_energy if uncorrelated_energy > 0.0 else 1.0
        out["uncorrelated_error_energy"] = round(uncorrelated_energy, 10)
        out["time_correlated_error_energy"] = round(coherent_energy, 10)
        out["time_correlation_amplification_ratio"] = round(ratio, 6)

    return out


def _uniform_quantise(mat: Matrix, step: float) -> Matrix:
    if step <= 0.0:
        raise ValueError(f"quant_step must be positive: {step}")
    return [[round(val / step) * step for val in row] for row in mat]


def simulate_low_rank_residual_compensation(
    *,
    state_matrix: Matrix,
    quant_step: float,
    gramian: Matrix,
    rank: int,
    element_bytes: int = 2,
) -> dict[str, Any]:
    """Simulate Gramian-aligned low-rank residual compensation S_corr = Q(Y) + (Y - Q(Y)) V V^T.

    Explicitly accounts for both error reduction (Gramian-weighted future energy and
    unweighted Frobenius error) AND extra FLOP / memory-bandwidth overhead.
    """
    d_v = len(state_matrix)
    d_k = len(state_matrix[0]) if d_v else 0
    if d_v == 0 or d_k == 0:
        raise ValueError("state_matrix must be non-empty")
    if len(gramian) != d_k or any(len(r) != d_k for r in gramian):
        raise ValueError("gramian must be d_k x d_k")
    if not (0 <= rank <= d_k):
        raise ValueError(f"rank must lie in [0, {d_k}]: {rank}")

    q_state = _uniform_quantise(state_matrix, quant_step)
    residual_raw = mat_sub(state_matrix, q_state)
    energy_before = future_output_error_energy(residual_raw, gramian)
    fro_before = frobenius_norm_sq(residual_raw)

    eigvals, eigvecs = symmetric_jacobi_eigh(gramian)
    if rank == 0:
        corrected = q_state
    else:
        # V is d_k x rank (top-r eigenvectors of observability Gramian M)
        v_top: Matrix = [[eigvecs[i][j] for j in range(rank)] for i in range(d_k)]
        proj = mat_mul(v_top, mat_transpose(v_top))  # V V^T
        correction = mat_mul(residual_raw, proj)
        corrected = mat_add(q_state, correction)

    residual_after = mat_sub(state_matrix, corrected)
    energy_after = future_output_error_energy(residual_after, gramian)
    fro_after = frobenius_norm_sq(residual_after)

    # Overhead accounting: computing (U V) takes 2*d_v*d_k*r FLOPs, reconstructing (U V) V^T takes 2*d_v*d_k*r FLOPs.
    extra_flops_per_step = 4 * d_v * d_k * rank
    extra_bytes_per_step = (d_v * rank + d_k * rank) * element_bytes
    reduction_ratio = (energy_before - energy_after) / energy_before if energy_before > 0.0 else 0.0

    return {
        "d_v": d_v,
        "d_k": d_k,
        "rank": rank,
        "quant_step": quant_step,
        "top_gramian_eigenvalues": [round(max(0.0, ev), 8) for ev in eigvals[: max(1, rank)]],
        "gramian_error_energy_before": round(energy_before, 10),
        "gramian_error_energy_after": round(energy_after, 10),
        "gramian_energy_reduction_fraction": round(reduction_ratio, 6),
        "frobenius_error_sq_before": round(fro_before, 10),
        "frobenius_error_sq_after": round(fro_after, 10),
        "extra_flops_per_step": extra_flops_per_step,
        "extra_bytes_per_step": extra_bytes_per_step,
        "note": (
            "Mathematical error reduction on a fixed linear readout Gramian does not "
            "automatically guarantee net end-to-end speedup or LLM accuracy gain without "
            "SM120 kernel benchmarking."
        ),
    }
