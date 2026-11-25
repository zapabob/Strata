"""Lift a proper orthogonal matrix and restrict its even Clifford action."""

from dataclasses import dataclass

import numpy as np

from spin8_clifford import chirality, chiral_tensor, clifford, generators, sylvester


@dataclass(frozen=True)
class Lift:
    vector: np.ndarray
    positive: np.ndarray
    negative: np.ndarray
    even: np.ndarray
    reflections: tuple


def spin_lift(rotation, tol=2e-12):
    rotation = np.asarray(rotation, dtype=np.float64)
    eye = np.eye(8)
    if (rotation.shape != (8, 8) or not np.isfinite(rotation).all()
            or np.max(np.abs(rotation.T @ rotation - eye)) > tol
            or abs(np.linalg.det(rotation) - 1) > 8 * tol):
        raise ValueError("The vector rotation must belong to SO(8)")
    reduced = rotation.copy()
    even = np.eye(16)
    normals = []
    for i in range(8):
        u = reduced[:, i] - eye[:, i]
        length = np.linalg.norm(u)
        if length <= tol:
            continue
        u /= length
        reduced -= 2 * np.outer(u, u @ reduced)
        even = even @ clifford(u)
        normals.append(u)
    if len(normals) % 2 or np.max(np.abs(reduced - eye)) > 8 * tol:
        raise ArithmeticError("The reflection decomposition failed its parity or residual check")
    _, p, m = chirality()
    recomputed = np.einsum("jab,iab->ji", generators(), even @ generators() @ even.T) / 16
    if np.max(np.abs(recomputed - rotation)) > 12 * tol:
        raise ArithmeticError("The Clifford conjugation does not recover the requested rotation")
    return Lift(recomputed, p.T @ even @ p, m.T @ even @ m, even, tuple(normals))


def vector_rotation(theta=0., signs=None):
    """Use the signed Sylvester H8 followed on input by a planar rotation."""
    r = sylvester(8)
    if signs is not None:
        d = np.asarray(signs)
        if d.shape != (8,) or not np.isin(d, [-1, 1]).all() or np.prod(d) != 1:
            raise ValueError("An even number of signed coordinates is required")
        r = r * d
    if not np.isfinite(theta):
        raise ValueError("A finite rotation parameter is required")
    c, s = np.cos(theta), np.sin(theta)
    plane = np.eye(8)
    plane[:2, :2] = [[c, -s], [s, c]]
    return r @ plane


def verify_lift(lift):
    c = chiral_tensor()
    transformed = np.einsum("ji,jmp->imp", lift.vector, c)
    transported = lift.negative.T @ transformed @ lift.positive
    omega, _, _ = chirality()
    return {
        "vector_conjugation": float(np.abs(lift.even @ generators() @ lift.even.T -
                                           np.einsum("ji,jab->iab", lift.vector, generators())).max()),
        "orthogonality": float(max(np.abs(a.T @ a - np.eye(8)).max() for a in
                                   (lift.vector, lift.positive, lift.negative))),
        "determinants": [float(np.linalg.det(a)) for a in (lift.vector, lift.positive, lift.negative)],
        "chirality_commutator": float(np.abs(lift.even @ omega - omega @ lift.even).max()),
        "multiplication_intertwiner": float(np.abs(transformed @ lift.positive - lift.negative @ c).max()),
        "invariant_tensor": float(np.abs(transported - c).max()),
        "reflection_count": len(lift.reflections),
    }
