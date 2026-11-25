"""Block bases and scaled ternary fitting with the PrismML type 142 byte layout."""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from spin8_clifford import sylvester
from spin8_triality import spin_lift, vector_rotation


@dataclass(frozen=True)
class Basis:
    kind: str
    block: int = 128
    theta: float = 0.
    seed: int = 8128
    parameters: tuple = ()

    @property
    def identity(self):
        return f"{self.kind}.{self.block}.{self.theta.hex()}.{self.seed}.{self.parameters}"

    def apply(self, rows, inverse=False):
        rows = np.asarray(rows)
        if rows.shape[-1] % self.block:
            raise ValueError(f"Dimension {rows.shape[-1]} is indivisible by {self.block}")
        r = basis_matrix(self).astype(rows.dtype, copy=False)
        return (rows.reshape(-1, self.block) @ (r if inverse else r.T)).reshape(rows.shape)


@lru_cache(maxsize=128)
def octet(kind, theta):
    lift = spin_lift(vector_rotation(theta))
    return {"V": lift.vector, "P": lift.positive, "M": lift.negative}[kind]


@lru_cache(maxsize=128)
def basis_matrix(b):
    if b.block not in (8, 64, 128, 256, 512):
        raise ValueError("Unsupported transform block")
    if b.kind == "direct":
        r = np.eye(b.block)
    elif b.kind == "hadamard":
        r = sylvester(b.block)
    elif b.kind == "signed":
        d = np.random.default_rng(b.seed).choice([-1, 1], b.block)
        r = sylvester(b.block) * d
    elif b.kind == "random":
        m = np.random.default_rng(b.seed).standard_normal((b.block, b.block))
        q, tri = np.linalg.qr(m)
        r = q * np.sign(np.diag(tri))
        r[:, -1] *= np.linalg.slogdet(r)[0]
    elif b.kind in ("random-octet", "gauged-P"):
        q, tri = np.linalg.qr(np.random.default_rng(b.seed).standard_normal((8, 8)))
        q *= np.sign(np.diag(tri))
        q[:, -1] *= np.linalg.slogdet(q)[0]
        u = q if b.kind == "random-octet" else q @ octet("P", b.theta) @ q.T
        r = np.kron(sylvester(b.block // 8), u)
    else:
        kind = b.kind.removeprefix("diagonal-")
        if kind not in ("V", "P", "M"):
            raise ValueError(f"Unsupported basis {b.kind}")
        high = np.eye(b.block // 8) if b.kind.startswith("diagonal-") else sylvester(b.block // 8)
        if b.parameters:
            from spin8_continuous import continuous_octets
            u=continuous_octets(b.parameters)["VPM".index(kind)]
        else:
            u=octet(kind,b.theta)
        r = np.kron(high, u)
    r.setflags(write=False)
    return r


def mixed_apply(rows, blocks, inverse=False):
    if sum(b.block for b in blocks) != rows.shape[-1]:
        raise ValueError("The mixed partition must exactly cover the input")
    return np.concatenate([basis.apply(part, inverse) for basis, part in zip(
        blocks, np.split(rows, np.cumsum([b.block for b in blocks[:-1]]), axis=-1))], axis=-1)


def pack(symbols, scales):
    s = np.asarray(symbols)
    a = np.asarray(scales, dtype="<f2").reshape(-1)
    if (s.ndim != 2 or s.shape != (a.size, 128) or not np.isin(s, [-1, 0, 1]).all()
            or (a < 0).any() or not np.isfinite(a).all()):
        raise ValueError("Invalid ternary groups or scale")
    codes = (s.astype(np.int16) + 1).astype(np.uint8).reshape(-1, 32, 4)
    payload = np.empty((a.size, 34), np.uint8)
    payload[:, :2] = np.ascontiguousarray(a).view(np.uint8).reshape(-1, 2)
    payload[:, 2:] = codes[:, :, 0] | (codes[:, :, 1] << 2) | (codes[:, :, 2] << 4) | (codes[:, :, 3] << 6)
    return payload


def unpack(payload):
    a = np.ascontiguousarray(payload, dtype=np.uint8).reshape(-1, 34)
    scales = a[:, :2].copy().view("<f2").reshape(-1)
    codes = (a[:, 2:, None] >> np.array([0, 2, 4, 6], dtype=np.uint8)) & 3
    if (codes == 3).any() or not np.isfinite(scales).all() or (scales < 0).any():
        raise ValueError("Invalid ternary payload")
    return codes.reshape(-1, 128).astype(np.int8) - 1, scales


def fit(rotated, importance=None, method="least_squares"):
    w = np.asarray(rotated, dtype=np.float32)
    if w.shape[-1] % 128 or not np.isfinite(w).all():
        raise ValueError("Invalid PQ2_0 input")
    groups = w.reshape(-1, 128)
    mag = np.abs(groups)
    if method == "absmax":
        scale = mag.max(axis=1).astype(np.float16)
    elif method == "least_squares":
        order = np.argsort(-mag, axis=1, kind="stable")
        sorted_mag = np.take_along_axis(mag, order, axis=1)
        if importance is None:
            denom = np.arange(1, 129, dtype=np.float64)
            numer = np.cumsum(sorted_mag, axis=1, dtype=np.float64)
        else:
            imp = np.broadcast_to(importance, w.shape).reshape(groups.shape)
            if np.any(imp < 0) or not np.isfinite(imp).all():
                raise ValueError("Activation second moments must be finite and non-negative")
            imp = np.take_along_axis(imp, order, axis=1)
            denom = np.cumsum(imp, axis=1, dtype=np.float64)
            numer = np.cumsum(imp.astype(np.float64) * sorted_mag, axis=1)
        grid = np.divide(numer, denom, out=np.zeros_like(numer), where=denom > 0)
        grid = np.minimum(grid, np.finfo(np.float16).max).astype(np.float16)
        s64 = grid.astype(np.float64)
        score = 2 * s64 * numer - denom * s64**2
        scale = grid[np.arange(len(groups)), np.argmax(score, axis=1)]
    else:
        raise ValueError(f"Unknown scale optimisation {method}")
    symbols = np.sign(groups) * (mag > .5 * scale.astype(np.float32)[:, None])
    symbols[scale == 0] = 0
    return pack(symbols, scale)


def decode(payload, shape):
    t, s = unpack(payload)
    return (t.astype(np.float32) * s.astype(np.float32)[:, None]).reshape(shape)


def fit_for_activations(weight, basis, visits=None, lambdas=None):
    """Use rotated diagonal activation moments; rank candidates with the full sampled outputs."""
    rotated = basis.apply(weight)
    importance = None
    if visits is not None:
        lambdas = np.ones(len(visits)) if lambdas is None else np.asarray(lambdas)
        if (len(visits) == 0 or len(lambdas) != len(visits) or (lambdas < 0).any()
                or lambdas.sum() <= 0 or any(len(x) == 0 for x in visits)):
            raise ValueError("Invalid visit calibration")
        moments = [np.mean(basis.apply(x).astype(np.float64)**2, axis=0) for x in visits]
        importance = np.average(moments, axis=0, weights=lambdas)
    return fit(rotated, importance)
