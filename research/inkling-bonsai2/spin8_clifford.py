"""The real sixteen-dimensional Clifford module for negative Euclidean signature."""

from functools import lru_cache

import numpy as np


def sylvester(order):
    if order < 1 or order & (order - 1):
        raise ValueError("The Sylvester order must be a power of two")
    h = np.ones((1, 1))
    while len(h) < order:
        h = np.block([[h, h], [h, -h]])
    return h / np.sqrt(order)


@lru_cache(maxsize=1)
def generators():
    # Coordinates are (1, e1, ..., e7); each oriented triple has e_i e_j = e_k.
    left = np.zeros((8, 8, 8), dtype=np.int8)
    left[0] = np.eye(8, dtype=np.int8)
    for i in range(1, 8):
        left[i, i, 0] = 1
        left[i, 0, i] = -1
    for a, b, c in [(1, 2, 3), (1, 4, 5), (1, 7, 6), (2, 4, 6),
                    (2, 5, 7), (3, 4, 7), (3, 6, 5)]:
        for i, j, k in ((a, b, c), (b, c, a), (c, a, b)):
            left[i, k, j], left[j, k, i] = 1, -1
    z = np.zeros((8, 8), dtype=np.int8)
    gamma = np.stack([np.block([[z, -a.T], [a, z]]) for a in left])
    gamma.setflags(write=False)
    return gamma


@lru_cache(maxsize=1)
def chirality():
    gamma = generators()
    volume = np.eye(16, dtype=np.int8)
    for component in gamma:
        volume = volume @ component
    if not np.array_equal(volume, np.diag(np.diag(volume))):
        raise ArithmeticError("Unexpected chirality basis")
    eye = np.eye(16)
    plus = eye[:, np.diag(volume) == 1]
    minus = eye[:, np.diag(volume) == -1]
    for array in (volume, plus, minus):
        array.setflags(write=False)
    return volume, plus, minus


def clifford(v):
    v = np.asarray(v, dtype=np.float64)
    if v.shape != (8,) or not np.isfinite(v).all():
        raise ValueError("Clifford multiplication requires eight finite coordinates")
    return np.einsum("i,ijk->jk", v, generators())


def chiral_tensor():
    _, plus, minus = chirality()
    return np.einsum("am,iab,bp->imp", minus, generators(), plus)


def triality_form(v, p, m):
    return np.einsum("i,m,p,imp->", v, m, p, chiral_tensor())
