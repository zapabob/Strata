"""Deterministic, CPU-only checks for CIK's finite examples and bounds."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import math
from collections import deque
from collections.abc import Callable
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

LOGGER = logging.getLogger(__name__)
SEED = 20261125
TOL = 1e-10
Matrix = NDArray[np.float64]
ComplexMatrix = NDArray[np.complex128]
Sequence = tuple[int, ...]
Row = tuple[Sequence, Sequence, F]


def require(condition: bool, message: str) -> None:
    """Fail a check even when Python runs with optimisations enabled."""
    if not condition:
        raise RuntimeError(message)


def conditional(
    joint: list[Row], context: Callable[[Row], bool], event: Callable[[Row], bool]
) -> F:
    """Compute one exact conditional probability on a positive-mass history."""
    support = [row for row in joint if context(row)]
    return sum((row[2] for row in support if event(row)), F(0)) / sum(
        (row[2] for row in support), F(0)
    )


def projection(joint: list[Row]) -> dict[str, float]:
    """Evaluate projection KL and the conditional-information sum separately."""
    projection_kl = 0.0
    information = 0.0
    for a, y, mass in joint:
        likelihood = conditional(
            joint, lambda r, a=a: r[0] == a, lambda r, y=y: r[1] == y
        )
        causal_likelihood = F(1)
        for t in range(len(y)):
            a_prefix, y_prefix, current = a[: t + 1], y[:t], y[t]
            q = conditional(
                joint,
                lambda r, t=t, a_prefix=a_prefix, y_prefix=y_prefix: (
                    r[0][: t + 1] == a_prefix and r[1][:t] == y_prefix
                ),
                lambda r, t=t, current=current: r[1][t] == current,
            )
            full = conditional(
                joint,
                lambda r, a=a, t=t, y_prefix=y_prefix: (
                    r[0] == a and r[1][:t] == y_prefix
                ),
                lambda r, t=t, current=current: r[1][t] == current,
            )
            causal_likelihood *= q
            information += float(mass) * math.log(full / q)
        projection_kl += float(mass) * math.log(likelihood / causal_likelihood)
    require(abs(projection_kl - information) < TOL, "Projection identity failed")
    return {
        "projection_kl_nats": projection_kl,
        "conditional_information_nats": information,
    }


def classical_controls() -> dict[str, object]:
    """Check intervention, feedback, selection and a mismatched history measure."""
    bits = (0, 1)
    future_copy = [((0, b), (b, 0), F(1, 2)) for b in bits]
    support_only = [((b, b), (b, 0), F(1, 2)) for b in bits]
    independent = [((0, a), (b, 0), F(1, 4)) for a in bits for b in bits]
    postselected = [(a, y, 2 * p) for a, y, p in independent if a[1] == y[0]]
    results = {
        "future_copy": projection(future_copy),
        "restricted_support": projection(support_only),
        "feedback_interventional": projection(independent),
        "feedback_observational": projection(future_copy),
        "independent_before_selection": projection(independent),
        "conditioned_on_agreement": projection(postselected),
    }
    for label, expected in (
        ("future_copy", math.log(2)),
        ("restricted_support", 0.0),
        ("feedback_interventional", 0.0),
        ("feedback_observational", math.log(2)),
        ("independent_before_selection", 0.0),
        ("conditioned_on_agreement", math.log(2)),
    ):
        require(abs(results[label]["projection_kl_nats"] - expected) < TOL, label)
    q_star_histories = [(a, y, F(1, 4)) for a in bits for y in bits]
    q_star_gap = sum(float(p) * math.log(2) for a, y, p in q_star_histories if a != y)
    p_gap = sum(float(p) * math.log(2) for a, y, p in future_copy if a[1] != y[0])
    require(p_gap == 0 and abs(q_star_gap - math.log(2) / 2) < TOL, "History measure")
    return {
        **results,
        "off_support_uniform_minimax_tv": 0.5,
        "gap_weighted_by_p_nats": p_gap,
        "gap_weighted_by_q_star_nats": q_star_gap,
    }


def partial_first(matrix: ComplexMatrix, traced: int, rest: int) -> ComplexMatrix:
    """Trace the leading subsystem in the matrix tensor order."""
    return np.trace(matrix.reshape(traced, rest, traced, rest), axis1=0, axis2=2)


def real_coordinates(matrix: ComplexMatrix) -> Matrix:
    """Realify a complex matrix without changing its Frobenius norm."""
    return np.concatenate((matrix.real.ravel(), matrix.imag.ravel()))


def comb_residual(w: ComplexMatrix) -> Matrix:
    """Return two linear residuals in the order O2, I2, O1, I1."""
    after_output = partial_first(w, 2, 8)
    one_slot = partial_first(after_output, 2, 4)
    second = after_output - np.kron(np.eye(2) / 2, one_slot)
    first = partial_first(one_slot, 2, 2) - np.trace(one_slot) * np.eye(2) / 2
    return np.concatenate((real_coordinates(second), real_coordinates(first)))


def traceless_basis(d: int) -> list[ComplexMatrix]:
    """Construct a Frobenius-orthonormal basis of traceless Hermitian matrices."""
    basis = []
    for k in range(1, d):
        diagonal = np.zeros(d)
        diagonal[:k] = 1.0
        diagonal[k] = -k
        basis.append(np.diag(diagonal / math.sqrt(k * (k + 1))).astype(complex))
    for i in range(d):
        for j in range(i + 1, d):
            for off_diagonal in (1.0, 1.0j):
                term = np.zeros((d, d), dtype=complex)
                term[i, j] = off_diagonal / math.sqrt(2)
                term[j, i] = term[i, j].conjugate()
                basis.append(term)
    return basis


def quantum_repair() -> dict[str, float | int]:
    """Repair a synthetic two-slot Choi state and check both distance bounds."""
    d = 16
    rng = np.random.default_rng(SEED)
    a = rng.normal(size=(d, 3)) + 1j * rng.normal(size=(d, 3))
    w = a @ a.conj().T
    w /= np.trace(w).real
    tau = np.eye(d) / d
    basis = traceless_basis(d)
    operator = np.column_stack([comb_residual(element) for element in basis])
    residual = comb_residual(w)
    r = float(np.linalg.norm(residual))
    coeffs, _, rank, singular = np.linalg.lstsq(operator, residual, rcond=1e-12)
    delta = r / float(singular[rank - 1])
    correction = np.einsum("i,ijk->jk", coeffs, np.array(basis))
    affine = w - correction
    repaired = (affine + d * delta * tau) / (1 + d * delta)
    repaired_l = float(np.linalg.norm(comb_residual(repaired)))
    min_ev = float(np.linalg.eigvalsh(repaired).min())
    distance = float(np.abs(np.linalg.eigvalsh(w - repaired)).sum())
    lower = r / math.sqrt(10)
    upper = (math.sqrt(d) * delta + 2 * d * delta) / (1 + d * delta)
    require(repaired_l < TOL and min_ev >= -TOL, "Comb repair feasibility failed")
    require(abs(np.trace(repaired) - 1) < TOL, "Repair lost unit trace")
    require(lower <= distance + TOL and distance <= upper + TOL, "Repair bound failed")
    return {
        "residual_before": r,
        "residual_after": repaired_l,
        "constraint_rank": int(rank),
        "pseudoinverse_radius": delta,
        "min_repaired_eigenvalue": min_ev,
        "distance_to_repaired": distance,
        "distance_lower_bound": lower,
        "repair_upper_bound": upper,
    }


def effect(word: Sequence, instrument: list[ComplexMatrix], d: int) -> ComplexMatrix:
    """Propagate the terminal identity backwards through ordered instrument outcomes."""
    result = np.eye(d, dtype=complex)
    for letter in reversed(word):
        k = instrument[letter]
        result = k.conj().T @ result @ k
    return result


def instrument_hankel(instrument: list[ComplexMatrix], state: ComplexMatrix) -> Matrix:
    """Form a finite Hankel section with empty and one-letter prefixes and suffixes."""
    words = [()] + [(i,) for i in range(len(instrument))]
    return np.array(
        [
            [
                np.trace(state @ effect(u + v, instrument, len(state))).real
                for v in words
            ]
            for u in words
        ]
    )


def paired_effect_search(
    left: list[ComplexMatrix],
    right: list[ComplexMatrix],
    rho: ComplexMatrix,
    sigma: ComplexMatrix,
) -> tuple[int, Sequence | None]:
    """Close the paired effect span, or return a distinguishing input/output word."""
    letters = list(zip(left, right, strict=True))
    queue = deque([(np.eye(len(rho)), np.eye(len(sigma)), ())])
    basis: list[Matrix] = []
    while queue:
        e, f, word = queue.popleft()
        difference = np.trace(rho @ e) - np.trace(sigma @ f)
        if abs(difference) > TOL:
            return len(basis), word
        vector = np.concatenate((real_coordinates(e), real_coordinates(f)))
        for direction in basis:
            vector -= (vector @ direction) * direction
        norm = float(np.linalg.norm(vector))
        if norm <= TOL:
            continue
        basis.append(vector / norm)
        for index, (left_op, right_op) in enumerate(letters):
            queue.append(
                (
                    left_op.conj().T @ e @ left_op,
                    right_op.conj().T @ f @ right_op,
                    (index,) + word,
                )
            )
    return len(basis), None


def gram_pivots(minor: list[list[F]], error_squared: F) -> list[F]:
    """Return exact pivots of M-transpose M minus the squared error bound."""
    columns = list(zip(*minor, strict=True))
    a = [
        [
            sum((x * y for x, y in zip(left, right, strict=True)), F(0))
            for right in columns
        ]
        for left in columns
    ]
    pivots = []
    for i in range(len(a)):
        a[i][i] -= error_squared
    for i in range(len(a)):
        pivot = a[i][i]
        pivots.append(pivot)
        if pivot <= 0:
            break
        for j in range(i + 1, len(a)):
            for k in range(i + 1, len(a)):
                a[j][k] -= a[j][i] * a[i][k] / pivot
    return pivots


def observability() -> dict[str, object]:
    """Check finite-word stability, hidden padding and an exact noise certificate."""
    x = np.array([[0, 1], [1, 0]], dtype=complex)
    y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    z = np.diag([1, -1]).astype(complex)
    eye = np.eye(2)
    instrument = [(eye + s * pauli) / 2 for pauli in (x, y, z) for s in (1, -1)]
    state = (eye + 0.3 * x + 0.2 * y + 0.4 * z) / 2
    words: list[Sequence] = [()]
    ranks = []
    for depth in range(3):
        ranks.append(
            int(
                np.linalg.matrix_rank(
                    [real_coordinates(effect(w, instrument, 2)) for w in words]
                )
            )
        )
        if depth < 2:
            words = words + [(i,) + w for i in range(len(instrument)) for w in words]
    h = instrument_hankel(instrument, state)
    padded_instrument = [np.kron(k, eye) for k in instrument]
    padded_state = np.kron(state, eye / 2)
    padded = instrument_hankel(padded_instrument, padded_state)
    pad_error = float(np.max(np.abs(h - padded)))
    require(ranks == [1, 4, 4] and pad_error < TOL, "Effect space or hidden padding")
    require(
        int(np.linalg.matrix_rank(h)) == 4, "Informationally complete Hankel section"
    )
    paired_rank, padded_witness = paired_effect_search(
        instrument, padded_instrument, state, padded_state
    )
    _, different_witness = paired_effect_search(instrument, instrument, state, eye / 2)
    require(paired_rank == 4 and padded_witness is None, "Padded effect closure")
    require(
        different_witness is not None and len(different_witness) == 1,
        "Missing distinguishing word",
    )
    signal = F(1, 10**7)
    imbalance = [eye / 2 + float(s * signal) * z for s in (1, -1)]
    direction = z / math.sqrt(2)
    eta = float(np.linalg.norm([np.trace(e @ direction).real for e in imbalance]))
    require(abs(eta - 2 * float(signal)) < 1e-15, "Ill-conditioned measurement")
    minor = [
        [F(1, 3) + (F(1, 1000) if i == 0 else 0) if i == j else F(0) for j in range(3)]
        for i in range(3)
    ]
    data_error = F(1, 100)
    exact = gram_pivots(minor, data_error**2)
    equality_control = gram_pivots(minor, F(1, 3) ** 2)
    require(len(exact) == 3 and all(p > 0 for p in exact), "Missing exact rank witness")
    require(equality_control[-1] == 0, "Threshold equality incorrectly certified")
    return {
        "effect_space_ranks": ranks,
        "observable_hankel_rank_float": int(np.linalg.matrix_rank(h)),
        "observable_hankel_singular_values": np.linalg.svd(
            h, compute_uv=False
        ).tolist(),
        "max_hankel_difference_after_ancilla_padding": pad_error,
        "padded_pair_effect_span_rank_float": paired_rank,
        "padded_pair_distinguishing_word": padded_witness,
        "different_state_distinguishing_word": different_witness,
        "restricted_measurement_eta": eta,
        "repeated_label_hankel_rank": 3,
        "dimension_lower_bound_from_rank": 2,
        "dimension_from_perfect_discrimination": 3,
        "data_spectral_norm_error_bound": str(data_error),
        "arithmetic_error_in_rational_certificate": "0",
        "exact_gram_pivots": [str(p) for p in exact],
        "threshold_equality_rejected": True,
    }


def project_simplex(row: Matrix) -> Matrix:
    """Project one real row onto the probability simplex."""
    ordered = np.sort(row)[::-1]
    shifts = (np.cumsum(ordered) - 1) / np.arange(1, len(row) + 1)
    shift = shifts[np.flatnonzero(ordered > shifts)[-1]]
    return np.maximum(row - shift, 0)


def labelled_tail_control(matrix: list[list[F]]) -> dict[str, float]:
    """Check the task-labelled singular-tail and regret bounds on a finite fixture."""
    p = np.array(matrix, dtype=float)
    root_weight = 1 / math.sqrt(len(p))
    left, singular, right = np.linalg.svd(root_weight * p, full_matrices=False)
    raw = np.outer(left[:, 0], right[0]) * singular[0] / root_weight
    approx = np.array([project_simplex(row) for row in raw])
    require(np.allclose(approx.sum(axis=1), 1, atol=TOL), "Simplex projection")
    empirical_tv = float(np.abs(p - approx).sum(axis=1).mean() / 2)
    bound = math.sqrt(p.shape[1]) * float(np.linalg.norm(singular[1:])) / 2
    chosen = np.argmax(approx, axis=1)
    best = p.max(axis=1).mean()
    regret = float(best - p[np.arange(len(p)), chosen].mean())
    require(
        empirical_tv <= bound + TOL and regret <= 2 * bound + TOL,
        "Posterior tail bound",
    )
    return {"mean_tv": empirical_tv, "tail_bound": bound, "one_attempt_regret": regret}


def prime_weighted_curve(n: int) -> dict[str, object]:
    """Evaluate the finite von Mangoldt prior without a prime asymptotic estimate."""
    prime = bytearray(b"\x01") * (n + 1)
    prime[:2] = b"\x00\x00"
    for p in range(2, math.isqrt(n) + 1):
        if prime[p]:
            prime[p * p :: p] = bytes((n - p * p) // p + 1)
    weights = np.zeros(n + 1)
    for p in range(2, n + 1):
        if prime[p]:
            power = p
            while power <= n:
                weights[power] = math.log(p)
                power *= p
    psi = np.cumsum(weights)
    curve = psi / psi[-1]
    deviation = float(np.max(np.abs(curve - np.arange(n + 1) / n)))
    require(curve[0] == 0 and curve[-1] == 1, "Prime-weighted curve endpoints")
    return {
        "n": n,
        "psi_n": float(psi[-1]),
        "maximum_deviation_from_uniform": deviation,
    }


def knowledge() -> dict[str, object]:
    """Evaluate the equal-spectrum counterexample and the calibrated spectral law."""
    matrices = [
        [[F(diagonal if i == j else off, 12) for j in range(3)] for i in range(3)]
        for diagonal, off in ((6, 3), (2, 5))
    ]
    grams = [
        [[sum(p[k][i] * p[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
        for p in matrices
    ]
    require(grams[0] == grams[1], "Gram matrices differ")
    curves = [
        [sum(sorted(p[0], reverse=True)[:m], F(0)) for m in range(4)] for p in matrices
    ]
    formula = [F(m, 3) + (1 - F(m, 3)) / 4 for m in (1, 2, 3)]
    require(curves[0][1:] == formula, "Calibrated symmetric law")
    require((curves[0][1], curves[1][1]) == (F(1, 2), F(5, 12)), "Budget contrast")
    return {
        "marginal_repeated_label_predictive_dimension": 3,
        "labelled_posterior_singular_values_exact": ["1", "1/4", "1/4"],
        "positive_spectrum_sign_budget_curve": [str(v) for v in curves[0]],
        "negative_spectrum_sign_budget_curve": [str(v) for v in curves[1]],
        "constant_observation_budget_one_unary_goals_length_one_vs_two": [1, 0],
        "rank_one_task_labelled_tail_control": labelled_tail_control(matrices[0]),
        "finite_prime_weighted_curve": [
            prime_weighted_curve(n) for n in (1_000, 10_000, 100_000)
        ],
    }


def gdn_experiment() -> dict[str, object]:
    """Compare finite GDN impulse responses, Gramian and equal-bit quantisation."""
    rng = np.random.default_rng(SEED + 1)
    steps, d, cut = 18, 8, 8
    keys = rng.normal(size=(steps, d))
    keys /= np.linalg.norm(keys, axis=1, keepdims=True)
    queries = rng.normal(size=(steps, d))
    transitions = [0.88 * (np.eye(d) - 0.6 * np.outer(k, k)) for k in keys]
    impulses = rng.normal(size=(cut + 1, d))
    inputs, features = [], []
    for start in range(cut + 1):
        row = impulses[start].copy()
        for step in range(start + 1, cut + 1):
            row = row @ transitions[step]
        inputs.append(row)
    phi = np.eye(d)
    for step in range(cut, steps):
        if step > cut:
            phi = phi @ transitions[step]
        features.append(phi @ queries[step])
    h = np.array(inputs) @ np.array(features).T
    brute = np.zeros_like(h)
    for start, impulse in enumerate(impulses):
        state = np.zeros(d)
        for step in range(steps):
            state = state @ transitions[step]
            if step == start:
                state += impulse
            if step >= cut:
                brute[start, step - cut] = state @ queries[step]
    state = rng.normal(size=d)
    gram = np.outer(queries[-1], queries[-1])
    for step in range(steps - 2, cut - 1, -1):
        operator = transitions[step + 1]
        gram = np.outer(queries[step], queries[step]) + operator @ gram @ operator.T
    rotation, _ = np.linalg.qr(rng.normal(size=(d, d)))
    rotation[:, 0] *= np.linalg.det(rotation)
    walsh = np.array([[1.0, 1.0], [1.0, -1.0]])
    hadamard = np.kron(np.kron(walsh, walsh), walsh) / math.sqrt(d)
    quantisation = {}
    for label, basis in (
        ("identity", np.eye(d)),
        ("hadamard", hadamard),
        ("random_so8", rotation),
    ):
        rotated = state @ basis
        scale = float(np.max(np.abs(rotated))) / 7
        error = (np.clip(np.rint(rotated / scale), -7, 7) * scale) @ basis.T - state
        direct = float(np.linalg.norm(np.array(features) @ error) ** 2)
        by_gram = float(error @ gram @ error)
        require(abs(direct - by_gram) < TOL, "Gramian energy mismatch")
        quantisation[label] = {
            "state_squared_error": float(error @ error),
            "future_readout_error_energy": direct,
            "gramian_error_energy": by_gram,
        }
    rotated_h = (np.array(inputs) @ rotation) @ (np.array(features) @ rotation).T
    invariance = float(np.max(np.abs(h - rotated_h)))
    hankel_error = float(np.max(np.abs(h - brute)))
    require(max(invariance, hankel_error) < TOL, "Hankel factorisation or rotation")
    u = np.array([1.0, 0.0])
    v = np.array([1.0, 1.0]) / math.sqrt(2)
    a = np.outer(u, u)
    b = np.outer(v, v)
    commutator = float(np.linalg.norm(a @ b - b @ a))
    require(commutator > 0.5, "Noncommuting-key negative control")
    gamma = 0.8
    aligned = 1 + (1 + gamma) ** 2
    alternating = 1 + (1 - gamma) ** 2
    related = alternating < 2 + gamma**2 < aligned
    require(related, "Cross terms disappeared")
    return {
        "hankel_singular_values": np.linalg.svd(h, compute_uv=False).tolist(),
        "hankel_factorisation_max_error": hankel_error,
        "exact_rotation_hankel_max_error": invariance,
        "quantisation": quantisation,
        "synthetic_effective_bits_per_coordinate_with_scale": 4 + 32 / d,
        "correlated_residual_energies": [aligned, alternating],
        "sum_of_separate_residual_energies": 2 + gamma**2,
        "cross_term_control": related,
        "unseen_query_energy": [0.0, 1.0],
        "noncommuting_key_projector_commutator_frobenius": commutator,
    }


def main() -> int:
    """Write exact controls and floating-point checks to JSON and CSV."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {
        "seed": SEED,
        "numpy": np.__version__,
        "floating_point_check_tolerance": TOL,
        "causality": classical_controls(),
        "comb": quantum_repair(),
        "observability": observability(),
        "knowledge": knowledge(),
        "gdn": gdn_experiment(),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "results.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    with (args.output / "knowledge_budget.csv").open(
        "w", newline="", encoding="utf-8"
    ) as out:
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(("unit_budget", "positive_channel", "negative_channel"))
        for budget, (positive, negative) in enumerate(
            zip(
                report["knowledge"]["positive_spectrum_sign_budget_curve"],
                report["knowledge"]["negative_spectrum_sign_budget_curve"],
                strict=True,
            )
        ):
            writer.writerow((budget, positive, negative))
    LOGGER.info("Finite CIK experiments passed. Results in %s", args.output)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
