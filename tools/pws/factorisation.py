"""NKAT common-basis expert factorisation, URT operator-norm bounds, and Spin(8) comparison.

Implements Sections 9, 10, and 11 of the PWS specification:
- Common-basis decomposition across experts in a layer:
      W[e] = W_shared + U[e] V[e]^T + E[e]
  measured via exact Jacobi SVD on small matrices without assuming arbitrary experts
  are low-rank.
- Inter-expert correlation, singular value spectrum, effective rank, operator-norm
  bound ||W[e] - W_approx[e]||_2 <= eps[e] verifying ||(W[e] - W_approx[e]) x||_2 <= eps[e] ||x||_2.
- Weighted Frobenius sensitivity objective ||G^{1/2} (W_approx - W) C^{1/2}||_F^2.
- Section 10 transfer-bit and net critical-path timing adoption criterion.
- Section 11 comparison of no-rotation, Sylvester SO(8)/Spin(8), and generic SO(8)
  rotations before low-bit quantisation.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

from tsi.math_foundations import (
    Matrix,
    frobenius_norm_sq,
    mat_add,
    mat_mul,
    mat_sub,
    mat_transpose,
    sylvester_so8_rotation,
    weighted_frobenius_objective,
)
from tsi.memory import symmetric_jacobi_eigh


def _svd_truncated(mat: Matrix, rank: int) -> tuple[list[float], Matrix, Matrix, Matrix]:
    """Exact pure-Python SVD via Jacobi eigendecomposition of A^T A (or A A^T)."""
    m = len(mat)
    n = len(mat[0]) if m else 0
    if m == 0 or n == 0:
        raise ValueError("Matrix must be non-empty")

    at = mat_transpose(mat)
    gram = mat_mul(at, mat)  # n x n symmetric PSD
    eigs, v_full = symmetric_jacobi_eigh(gram)
    svals = [math.sqrt(max(0.0, ev)) for ev in eigs]

    r = min(max(0, rank), min(m, n))
    if r == 0:
        approx = [[0.0] * n for _ in range(m)]
        return svals, [], [], approx

    v_r = [[v_full[i][j] for j in range(r)] for i in range(n)]
    # U_r[:, j] = (A V_r[:, j]) / sigma_j
    av = mat_mul(mat, v_r)  # m x r
    u_r = [[0.0] * r for _ in range(m)]
    us_r = [[0.0] * r for _ in range(m)]
    for j in range(r):
        s = svals[j]
        for i in range(m):
            us_r[i][j] = av[i][j]
            u_r[i][j] = (av[i][j] / s) if s > 1e-14 else 0.0

    approx = mat_mul(us_r, mat_transpose(v_r))
    return svals, us_r, v_r, approx


def operator_2_norm(mat: Matrix) -> float:
    """Spectral norm ||A||_2 = sigma_max(A)."""
    svals, _, _, _ = _svd_truncated(mat, rank=0)
    return svals[0] if svals else 0.0


def effective_rank_entropy(singular_values: Sequence[float]) -> float:
    """Roy-Vetterli effective rank exp(H(sigma / sum(sigma)))."""
    pos = [s for s in singular_values if s > 1e-14]
    if not pos:
        return 0.0
    total = sum(pos)
    ent = -sum((s / total) * math.log(s / total) for s in pos)
    return math.exp(ent)


def analyse_common_basis_factorisation(
    experts: Sequence[Matrix],
    *,
    rank: int,
    g_sqrt: Matrix | None = None,
    c_sqrt: Matrix | None = None,
) -> dict[str, Any]:
    """Decompose W[e] = W_shared + U[e] V[e]^T + E[e] and audit URT error bounds (Section 9)."""
    if not experts:
        raise ValueError("experts must be non-empty")
    m = len(experts[0])
    n = len(experts[0][0]) if m else 0
    if m == 0 or n == 0:
        raise ValueError("Expert matrices must be non-empty")
    for w in experts:
        if len(w) != m or any(len(row) != n for row in w):
            raise ValueError("All expert matrices in a layer must share dimensions (m, n)")

    num_e = len(experts)
    # Common component W_shared = element-wise mean across experts in the layer
    w_shared: Matrix = [
        [sum(experts[e][i][j] for e in range(num_e)) / num_e for j in range(n)]
        for i in range(m)
    ]

    # Pairwise mean cosine correlation across flattened expert weights
    flat = [[x for row in w for x in row] for w in experts]
    norms = [math.sqrt(sum(x * x for x in v)) for v in flat]
    corrs: list[float] = []
    for i in range(num_e):
        for j in range(i + 1, num_e):
            denom = norms[i] * norms[j]
            if denom > 0.0:
                corrs.append(sum(a * b for a, b in zip(flat[i], flat[j], strict=True)) / denom)
    mean_corr = (sum(corrs) / len(corrs)) if corrs else 1.0

    per_expert: list[dict[str, Any]] = []
    for idx, w in enumerate(experts):
        delta = mat_sub(w, w_shared)
        svals, _, _, lr_delta = _svd_truncated(delta, rank=rank)
        w_approx = mat_add(w_shared, lr_delta)
        residual = mat_sub(w, w_approx)

        eps_op = operator_2_norm(residual)
        fro_w = math.sqrt(frobenius_norm_sq(w))
        fro_res = math.sqrt(frobenius_norm_sq(residual))
        rel_fro = (fro_res / fro_w) if fro_w > 0.0 else 0.0

        # Direct URT operator-norm verification on a deterministic unit test vector x
        x_raw = [math.sin(0.7 * (j + 1) + 0.3 * idx) for j in range(n)]
        x_norm = math.sqrt(sum(v * v for v in x_raw)) or 1.0
        x_unit = [v / x_norm for v in x_raw]
        wx = [sum(w[i][j] * x_unit[j] for j in range(n)) for i in range(m)]
        wax = [sum(w_approx[i][j] * x_unit[j] for j in range(n)) for i in range(m)]
        out_err = math.sqrt(sum((a - b) ** 2 for a, b in zip(wx, wax, strict=True)))

        weighted_obj = None
        if g_sqrt is not None and c_sqrt is not None:
            weighted_obj = round(weighted_frobenius_objective(w, w_approx, g_sqrt, c_sqrt), 10)

        per_expert.append(
            {
                "expert_idx": idx,
                "delta_singular_values": [round(s, 6) for s in svals],
                "delta_effective_rank": round(effective_rank_entropy(svals), 6),
                "urt_operator_norm_eps": round(eps_op, 8),
                "verified_unit_input_err": round(out_err, 8),
                "urt_bound_holds": out_err <= eps_op + 1e-11,
                "relative_frobenius_error": round(rel_fro, 6),
                "weighted_frobenius_objective": weighted_obj,
            }
        )

    return {
        "num_experts": num_e,
        "shape": [m, n],
        "rank": rank,
        "mean_inter_expert_cosine_correlation": round(mean_corr, 6),
        "max_urt_operator_norm_eps": max(r["urt_operator_norm_eps"] for r in per_expert),
        "mean_relative_frobenius_error": round(
            sum(r["relative_frobenius_error"] for r in per_expert) / num_e, 6
        ),
        "experts": per_expert,
    }


def evaluate_common_basis_adoption(
    *,
    m: int,
    n: int,
    rank: int,
    orig_bits: float,
    corr_bits: float,
    metadata_bytes: int,
    effective_ssd_bw_bytes_per_s: float,
    additional_reconstruction_and_sync_s: float,
) -> dict[str, Any]:
    """Section 10 adoption check: transfer-bit reduction AND net critical-path timing gain.

    Refuses to claim speedup from bit reduction alone unless:
        saved_exposed_io_time > additional_reconstruction_and_sync_time.
    """
    if m <= 0 or n <= 0 or rank < 0 or orig_bits <= 0.0 or corr_bits <= 0.0:
        raise ValueError("Matrix dimensions and bit widths must be positive; rank non-negative")
    if effective_ssd_bw_bytes_per_s <= 0.0 or additional_reconstruction_and_sync_s < 0.0:
        raise ValueError("Bandwidth must be positive and reconstruction time non-negative")

    orig_total_bits = orig_bits * m * n
    corr_total_bits = corr_bits * rank * (m + n) + (metadata_bytes * 8.0)
    bytes_saved = (orig_total_bits - corr_total_bits) / 8.0
    transfer_reduced = corr_total_bits < orig_total_bits

    saved_io_s = max(0.0, bytes_saved) / effective_ssd_bw_bytes_per_s
    net_time_saved_s = saved_io_s - additional_reconstruction_and_sync_s
    net_speedup_justified = transfer_reduced and (saved_io_s > additional_reconstruction_and_sync_s)

    return {
        "original_bits": round(orig_total_bits, 2),
        "correction_plus_metadata_bits": round(corr_total_bits, 2),
        "transfer_reduction_ratio": round(corr_total_bits / orig_total_bits, 6),
        "bytes_saved_per_expert": round(bytes_saved, 2),
        "transfer_reduced": transfer_reduced,
        "saved_exposed_io_ms": round(saved_io_s * 1000.0, 6),
        "additional_reconstruction_and_sync_ms": round(additional_reconstruction_and_sync_s * 1000.0, 6),
        "net_critical_path_gain_ms": round(net_time_saved_s * 1000.0, 6),
        "net_speedup_justified": net_speedup_justified,
        "caveat": (
            "Storage or transfer reduction alone does not prove inference speedup; "
            "net critical-path timing must be verified on real GPU/SSD hardware."
        ),
    }


def _generic_so8_rotation(angle_rad: float = 0.6180339887) -> Matrix:
    """Construct a generic block-Givens orthogonal rotation in SO(8) (det = +1) as a non-Spin(8) baseline."""
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    # Product of two disjoint plane-rotation layers to mix all 8 coordinates cleanly.
    r1 = [[1.0 if i == j else 0.0 for j in range(8)] for i in range(8)]
    for k in range(0, 8, 2):
        r1[k][k], r1[k][k + 1] = c, -s
        r1[k + 1][k], r1[k + 1][k + 1] = s, c
    c2 = math.cos(angle_rad * 1.41421356)
    s2 = math.sin(angle_rad * 1.41421356)
    r2 = [[1.0 if i == j else 0.0 for j in range(8)] for i in range(8)]
    for a, b in ((1, 2), (3, 4), (5, 6), (7, 0)):
        r2[a][a], r2[a][b] = c2, -s2
        r2[b][a], r2[b][b] = s2, c2
    return mat_mul(r2, r1)


def _symmetric_int_quant(mat: Matrix, bits: int) -> Matrix:
    levels = (1 << (bits - 1)) - 1
    max_abs = max((abs(x) for row in mat for x in row), default=0.0)
    if max_abs == 0.0:
        return [row[:] for row in mat]
    scale = max_abs / float(levels)
    return [
        [max(-levels, min(levels, int(round(x / scale)))) * scale for x in row]
        for row in mat
    ]


def compare_spin8_vs_so8_quantisation(
    weight_8col: Matrix,
    *,
    bits: int = 4,
) -> dict[str, Any]:
    """Section 11 empirical comparison: no-rotation vs Sylvester SO(8)/Spin(8) vs generic SO(8).

    Evaluates W_quant = Q(W R^T) R and explicitly records that Spin(8) vector-representation
    symmetry does not automatically guarantee superiority over generic SO(8) rotations.
    """
    if not weight_8col or any(len(r) != 8 for r in weight_8col):
        raise ValueError("weight_8col must be a non-empty matrix with 8 columns")
    if bits < 2 or bits > 8:
        raise ValueError(f"bits must lie in [2, 8]: {bits}")

    ident = [[1.0 if i == j else 0.0 for j in range(8)] for i in range(8)]
    rotations: dict[str, Matrix] = {
        "no_rotation": ident,
        "sylvester_hadamard_so8": sylvester_so8_rotation(),
        "generic_givens_so8": _generic_so8_rotation(),
    }

    w_norm = math.sqrt(frobenius_norm_sq(weight_8col)) or 1.0
    results: dict[str, dict[str, float]] = {}
    for name, rot in rotations.items():
        rotated = mat_mul(weight_8col, mat_transpose(rot))
        q_rot = _symmetric_int_quant(rotated, bits=bits)
        w_q = mat_mul(q_rot, rot)
        err = mat_sub(weight_8col, w_q)
        fro_err = math.sqrt(frobenius_norm_sq(err))
        op_err = operator_2_norm(err)
        results[name] = {
            "frobenius_error": round(fro_err, 8),
            "relative_frobenius_error": round(fro_err / w_norm, 8),
            "operator_2_norm_error": round(op_err, 8),
        }

    return {
        "bits": bits,
        "shape": [len(weight_8col), 8],
        "methods": results,
        "epistemic_note": (
            "The vector representation of Spin(8) acts through SO(8); any claimed advantage "
            "over generic SO(8) or Hadamard rotations must be shown empirically on target weights."
        ),
    }
