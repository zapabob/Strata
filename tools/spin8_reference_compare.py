"""Independent FP64 Spin8 reference, promoted from the retained G1 probe.

The octonion/Clifford construction and finite differences are independent of
the production C++ audit. Rational spot checks approximate FP64 inputs by
limiting denominators; they are not exact certificates for the original floats.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
from pathlib import Path
import struct
import subprocess
import sys
from fractions import Fraction
from typing import Any

Matrix = list[list[float]]
Record = dict[str, Any]


TRIPLES = [(1, 2, 3), (1, 4, 5), (1, 7, 6), (2, 4, 6), (2, 5, 7), (3, 4, 7), (3, 6, 5)]


def build_octonion_table() -> dict[tuple[int, int], tuple[float, int]]:
    table = {}
    for i in range(8):
        table[(0, i)] = (1.0, i)
        table[(i, 0)] = (1.0, i)
        table[(i, i)] = (-1.0, 0)
    for a, b, c in TRIPLES:
        table[(a, b)] = (1.0, c)
        table[(b, c)] = (1.0, a)
        table[(c, a)] = (1.0, b)
        table[(b, a)] = (-1.0, c)
        table[(c, b)] = (-1.0, a)
        table[(a, c)] = (-1.0, b)
    return table


OCT = build_octonion_table()


def mat_mul(a: Matrix, b: Matrix) -> Matrix:
    n = len(a)
    m = len(b[0])
    k = len(b)
    out = [[0.0] * m for _ in range(n)]
    for i in range(n):
        ai = a[i]
        oi = out[i]
        for t in range(k):
            av = ai[t]
            if av != 0.0:
                bt = b[t]
                for j in range(m):
                    oi[j] += av * bt[j]
    return out


def mat_t(a: Any) -> Matrix:
    return [list(col) for col in zip(*a)]


def identity(n: int) -> Matrix:
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def fro(a: Any) -> float:
    return math.sqrt(sum(x * x for row in a for x in row))


def build_L() -> list[Matrix]:
    Ls = []
    for i in range(1, 8):
        m = [[0.0] * 8 for _ in range(8)]
        for j in range(8):
            s, k = OCT[(i, j)]
            m[j][k] += s
        Ls.append(m)
    return Ls


def build_canonical_gammas() -> list[Matrix]:
    Ls = build_L()
    gm = []
    upper0 = [[0.0] * 8 + [1.0 if i == j else 0.0 for j in range(8)] for i in range(8)]
    lower0 = [[1.0 if i == j else 0.0 for j in range(8)] + [0.0] * 8 for i in range(8)]
    gm.append(upper0 + lower0)
    for i in range(1, 8):
        L = Ls[i - 1]
        upper = [[0.0] * 8 + L[j] for j in range(8)]
        lower = [[-x for x in L[j]] + [0.0] * 8 for j in range(8)]
        gm.append(upper + lower)
    return gm


def unpack_gens_16(flat: list[float]) -> list[Matrix]:
    return [
        [[flat[i * 256 + r * 16 + c] for c in range(16)] for r in range(16)]
        for i in range(8)
    ]


def unpack_gens_8x8(flat: list[float], count: int, n: int) -> list[Matrix]:
    out = []
    for i in range(count):
        m = [[flat[i * n * n + r * n + c] for c in range(n)] for r in range(n)]
        out.append(m)
    return out


def mat_add(a: Matrix, b: Matrix) -> Matrix:
    return [[a[i][j] + b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def mat_sub(a: Matrix, b: Matrix) -> Matrix:
    return [[a[i][j] - b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def structural_checks(gammas: list[Matrix]) -> tuple[float, float, float]:
    anticomm_max = 0.0
    symmetric_max = 0.0
    square_max = 0.0
    for i in range(8):
        gi = gammas[i]
        symmetric_max = max(symmetric_max, fro(mat_sub(gi, mat_t(gi))))
        g2 = mat_mul(gi, gi)
        for r in range(16):
            for c in range(16):
                e = 1.0 if r == c else 0.0
                square_max = max(square_max, abs(g2[r][c] - e))
        for j in range(i, 8):
            gj = gammas[j]
            a = mat_mul(gi, gj)
            b = mat_mul(gj, gi)
            for r in range(16):
                for c in range(16):
                    e = 2.0 if (i == j and r == c) else 0.0
                    anticomm_max = max(anticomm_max, abs(a[r][c] + b[r][c] - e))
    return anticomm_max, symmetric_max, square_max


def finite_L_checks(Ls: list[Matrix]) -> tuple[float, float, float]:
    anticomm_max = 0.0
    skew_max = 0.0
    square_max = 0.0
    for i in range(7):
        Li = Ls[i]
        skew_max = max(skew_max, fro(mat_add(Li, mat_t(Li))))
        L2 = mat_mul(Li, Li)
        for r in range(8):
            for c in range(8):
                e = -1.0 if r == c else 0.0
                square_max = max(square_max, abs(L2[r][c] - e))
        for j in range(i, 7):
            Lj = Ls[j]
            a = mat_mul(Li, Lj)
            b = mat_mul(Lj, Li)
            for r in range(8):
                for c in range(8):
                    e = -2.0 if (i == j and r == c) else 0.0
                    anticomm_max = max(anticomm_max, abs(a[r][c] + b[r][c] - e))
    return anticomm_max, skew_max, square_max


def lu_sign_logdet(m: Matrix) -> tuple[int, float]:
    """Return determinant sign and log magnitude using FP64 pivoted LU."""
    if not m or any(len(row) != len(m) for row in m):
        raise ValueError("determinant requires a nonempty square matrix")
    if any(not math.isfinite(x) for row in m for x in row):
        raise ValueError("determinant requires finite entries")
    n = len(m)
    a = [row[:] for row in m]
    sign = 1
    log_det = 0.0
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(a[r][c]))
        if abs(a[p][c]) < 1e-300:
            return 0, float("-inf")
        if p != c:
            a[c], a[p] = a[p], a[c]
            sign = -sign
        # det(P*A) is the product of U's diagonal, including its pivot signs.
        if a[c][c] < 0:
            sign = -sign
        log_det += math.log(abs(a[c][c]))
        inv = 1.0 / a[c][c]
        for r in range(c + 1, n):
            f = a[r][c] * inv
            for cc2 in range(c, n):
                a[r][cc2] -= f * a[c][cc2]
    return sign, log_det


def det_sign_rationalized(m: Matrix) -> int:
    """Sign after approximate rationalisation with denominator <= 10**12."""
    fr = [[Fraction(x).limit_denominator(10**12) for x in row] for row in m]
    sign = 1
    n = len(fr)
    for k in range(n):
        if fr[k][k] == 0:
            for r2 in range(k + 1, n):
                if fr[r2][k] != 0:
                    fr[k], fr[r2] = fr[r2], fr[k]
                    sign = -sign
                    break
            else:
                return 0
        if fr[k][k] < 0:
            sign = -sign
        inv = fr[k][k]
        for i in range(k + 1, n):
            f = fr[i][k] / inv
            if f:
                for j in range(k, n):
                    fr[i][j] -= f * fr[k][j]
    return sign


def audit_of(m: Matrix) -> Record:
    mt = mat_t(m)
    gram = mat_mul(mt, m)
    n = len(m)
    resid = [
        [gram[i][j] - (1.0 if i == j else 0.0) for j in range(n)] for i in range(n)
    ]
    ef = fro(resid) / math.sqrt(float(n))
    max_err = max(abs(x) for row in resid for x in row)
    sign, log_det = lu_sign_logdet(m)
    return {"ef": ef, "max": max_err, "det_sign": sign, "log_abs_det": log_det}


def jacobi_eig(a: Any, sweeps: int = 200) -> list[float]:
    n = len(a)
    m = [row[:] for row in a]
    v = identity(n)
    for _ in range(sweeps):
        big = 0.0
        p = q = 0
        for i in range(n):
            for j in range(i + 1, n):
                if abs(m[i][j]) > big:
                    big = abs(m[i][j])
                    p, q = i, j
        if big < 1e-15:
            break
        app, aqq, apq = m[p][p], m[q][q], m[p][q]
        if abs(apq) < 1e-300:
            continue
        theta = (aqq - app) / (2.0 * apq)
        t = (1.0 if theta >= 0 else -1.0) / (
            abs(theta) + math.sqrt(theta * theta + 1.0)
        )
        c = 1.0 / math.sqrt(t * t + 1.0)
        s = t * c
        for i in range(n):
            mip, miq = m[i][p], m[i][q]
            m[i][p] = c * mip - s * miq
            m[i][q] = s * mip + c * miq
        for i in range(n):
            mpi, mqi = m[p][i], m[q][i]
            m[p][i] = c * mpi - s * mqi
            m[q][i] = s * mpi + c * mqi
        for i in range(n):
            vip, viq = v[i][p], v[i][q]
            v[i][p] = c * vip - s * viq
            v[i][q] = s * vip + c * viq
    return [m[i][i] for i in range(n)]


def audit16_of(m16: Matrix) -> Record:
    at = mat_t(m16)
    gram = mat_mul(at, m16)
    resid = [
        [gram[i][j] - (1.0 if i == j else 0.0) for j in range(16)] for i in range(16)
    ]
    ef = fro(resid) / 4.0
    max_err = max(abs(x) for row in resid for x in row)
    return {"ef": ef, "max": max_err}


def eigens_compare_max(ma: Matrix, mb: Matrix) -> float:
    ea = sorted(jacobi_eig(mat_mul(mat_t(ma), ma)), key=lambda x: -x)
    eb = sorted(jacobi_eig(mat_mul(mat_t(mb), mb)), key=lambda x: -x)
    return max(abs(x - y) for x, y in zip(ea, eb))


def flat8(m: Matrix) -> list[float]:
    return [x for row in m for x in row]


def square8(flat: list[float]) -> Matrix:
    return [[flat[i * 8 + j] for j in range(8)] for i in range(8)]


def top8(u: Any) -> Matrix:
    return [[u[i][j] for j in range(8)] for i in range(8)]


def bottom8(u: Any) -> Matrix:
    return [[u[i + 8][j + 8] for j in range(8)] for i in range(8)]


def plane_rotation(a: int, b: int, theta: float) -> Matrix:
    r = identity(8)
    ca, sa = math.cos(theta), math.sin(theta)
    r[a][a] = ca
    r[a][b] = sa
    r[b][a] = -sa
    r[b][b] = ca
    return r


def gamma_ab(gammas: list[Matrix], a: int, b: int) -> Matrix:
    return mat_mul(gammas[a], gammas[b])


def compose_planes(
    planes: list[tuple[int, int, float]],
    gammas: list[Matrix],
    cache: dict[tuple[int, int], Matrix],
) -> Matrix:
    m = identity(16)
    for a, b, th in planes:
        key = (a, b)
        if key not in cache:
            cache[key] = gamma_ab(gammas, a, b)
        gab = cache[key]
        ch = math.cos(th / 2.0)
        sh = math.sin(th / 2.0)
        gm = mat_mul(gab, m)
        m = [[ch * m[i][j] - sh * gm[i][j] for j in range(16)] for i in range(16)]
    return m


def compose_rot(planes: list[tuple[int, int, float]]) -> Matrix:
    r = identity(8)
    for a, b, theta in planes:
        r = mat_mul(plane_rotation(a, b, theta), r)
    return r


def vector_rot_from_u(u: Any, gammas: list[Matrix]) -> tuple[Matrix, float]:
    ut = mat_t(u)
    rmat = [[0.0] * 8 for _ in range(8)]
    resid = 0.0
    for j in range(8):
        x = mat_mul(u, mat_mul(gammas[j], ut))
        coords = [0.0] * 8
        for i in range(8):
            s = 0.0
            for rr in range(16):
                for cc in range(16):
                    s += x[rr][cc] * gammas[i][rr][cc]
            coords[i] = s / 16.0
            rmat[i][j] = coords[i]
        for rr in range(16):
            for cc in range(16):
                fitted = sum(coords[i] * gammas[i][rr][cc] for i in range(8))
                resid = max(resid, abs(fitted - x[rr][cc]))
    return rmat, resid


def gamma_vector(gammas: list[Matrix], v: list[float]) -> Matrix:
    out = [[0.0] * 16 for _ in range(16)]
    for k in range(8):
        vk = v[k]
        if vk != 0.0:
            gk = gammas[k]
            for r in range(16):
                vr = gk[r]
                orow = out[r]
                for c in range(16):
                    orow[c] += vk * vr[c]
    return out


def mat_vec(m: Matrix, v: list[float]) -> list[float]:
    return [sum(m[i][j] * v[j] for j in range(len(v))) for i in range(len(m))]


def is_close(a: Matrix, b: Matrix, tol: float) -> tuple[float, bool]:
    worst = 0.0
    for i in range(len(a)):
        for j in range(len(a[0])):
            worst = max(worst, abs(a[i][j] - b[i][j]))
    return worst, worst <= tol


def sylvester_h(block: int) -> Matrix:
    h = [[1.0]]
    while len(h) < block:
        n = len(h)
        nh = [[0.0] * (2 * n) for _ in range(2 * n)]
        for i in range(n):
            for j in range(n):
                nh[i][j] = h[i][j]
                nh[i][n + j] = h[i][j]
                nh[n + i][j] = h[i][j]
                nh[n + i][n + j] = -h[i][j]
        h = nh
    s = 1.0 / math.sqrt(float(block))
    return [[x * s for x in row] for row in h]


def f32(x: float) -> float:
    return struct.unpack("f", struct.pack("f", x))[0]


def softmax(vals: list[float]) -> list[float]:
    mx = max(vals)
    es = [math.exp(v - mx) for v in vals]
    st = sum(es)
    return [e / st for e in es]


def mask_signs(mask: int, n: int) -> list[float]:
    return [-1.0 if (mask >> i) & 1 else 1.0 for i in range(n)]


def write_report(report: Record, path: str | Path) -> None:
    with open(path, "w") as f:
        json.dump(report, f, indent=1, sort_keys=True)


def parse_planes(flat: list[float]) -> list[tuple[int, int, float]]:
    return [(flat[i], flat[i + 1], flat[i + 2]) for i in range(0, len(flat), 3)]


def trial_checks(
    probe: Record, gammas: list[Matrix], chi_plus_first: bool | None, report: Record
) -> None:
    rep = report.setdefault(
        "trial",
        {
            "vector_vs_R": 0.0,
            "orth_lib": 0.0,
            "det_ok": True,
            "logabsdet": 0.0,
            "audit_reprod": 0.0,
            "eigs_match": 0.0,
            "blocks_direct_plus": 0.0,
            "blocks_direct_minus": 0.0,
            "fwd_action_vs_R": 0.0,
            "loopback_f64": 0.0,
            "loopback_f32": 0.0,
            "conjugation": 0.0,
            "triality_lib": 0.0,
            "u_orth": 0.0,
            "u_det_ok": True,
            "vector_fit_residual": 0.0,
            "count": 0,
            "group_inverse": 0.0,
            "rational_spots": 0,
            "rational_sign_ok": True,
            "rational_method": "approximate rationalisation; denominator <= 10**12",
        },
    )
    cache = {}
    for ti, t in enumerate(probe["trials"][: int(probe["python_check"])]):
        planes = [
            (int(p[0]), int(p[1]), float(p[2])) for p in parse_planes(t["planes"])
        ]
        u = compose_planes(planes, gammas, cache)
        inverse = compose_planes(
            [(a, b, -th) for a, b, th in reversed(planes)], gammas, cache
        )
        rep["group_inverse"] = max(
            rep["group_inverse"], is_close(mat_mul(u, inverse), identity(16), 1e-12)[0]
        )
        for constructed in (u, top8(u), bottom8(u)):
            if lu_sign_logdet(constructed)[0] != 1:
                rep["u_det_ok"] = False
        aud16 = audit16_of(u)
        rep["u_orth"] = max(rep["u_orth"], aud16["ef"])
        rot, vfit = vector_rot_from_u(u, gammas)
        if lu_sign_logdet(rot)[0] != 1:
            rep["u_det_ok"] = False
        rep["vector_fit_residual"] = max(rep["vector_fit_residual"], vfit)
        vec_lib = square8(t["vector"])
        d, _ = is_close(rot, vec_lib, 1e-12)
        rep["vector_vs_R"] = max(rep["vector_vs_R"], d)
        plus_lib = square8(t["plus"])
        minus_lib = square8(t["minus"])
        for lib, idx in ((plus_lib, 1), (minus_lib, 2)):
            aud = audit_of(lib)
            rep["orth_lib"] = max(rep["orth_lib"], aud["ef"])
            rep["logabsdet"] = max(rep["logabsdet"], abs(aud["log_abs_det"]))
            lv = t["audit"]["views"][idx]
            rep["audit_reprod"] = max(
                rep["audit_reprod"],
                abs(aud["ef"] - lv["ef_normalized"]),
                abs(aud["max"] - lv["max_error"]),
                abs(aud["log_abs_det"] - lv["log_abs_det"]),
            )
            if aud["det_sign"] != 1 or int(lv["det_sign"]) != aud["det_sign"]:
                rep["det_ok"] = False
            if ti < 100:
                rep["rational_spots"] += 1
                if det_sign_rationalized(lib) != aud["det_sign"]:
                    rep["rational_sign_ok"] = False
        vec_aud = t["audit"]["views"][0]
        aud_v = audit_of(vec_lib)
        rep["audit_reprod"] = max(
            rep["audit_reprod"],
            abs(aud_v["ef"] - vec_aud["ef_normalized"]),
            abs(aud_v["max"] - vec_aud["max_error"]),
            abs(aud_v["log_abs_det"] - vec_aud["log_abs_det"]),
        )
        if chi_plus_first is not None:
            top = top8(u)
            bot = bottom8(u)
            plus_expected, minus_expected = (top, bot) if chi_plus_first else (bot, top)
            rep["blocks_direct_plus"] = max(
                rep["blocks_direct_plus"], is_close(plus_expected, plus_lib, 1e-12)[0]
            )
            rep["blocks_direct_minus"] = max(
                rep["blocks_direct_minus"],
                is_close(minus_expected, minus_lib, 1e-12)[0],
            )
        rep["eigs_match"] = max(
            rep["eigs_match"],
            eigens_compare_max(top8(u), plus_lib),
            eigens_compare_max(bottom8(u), minus_lib),
        )
        src, fwd = t["f64_src"], t["f64_fwd"]
        worst = 0.0
        for r in range(3):
            for g in range(1):
                xg = src[r * 8 + g * 8 : r * 8 + g * 8 + 8]
                yg = fwd[r * 8 + g * 8 : r * 8 + g * 8 + 8]
                y = mat_vec(rot, xg)
                worst = max(worst, max(abs(y[k] - yg[k]) for k in range(8)))
        rep["fwd_action_vs_R"] = max(rep["fwd_action_vs_R"], worst)
        rep["loopback_f64"] = max(rep["loopback_f64"], t["f64_loopback_max"])
        rep["loopback_f32"] = max(rep["loopback_f32"], t["f32_loopback_max"])
        v8 = src[0:8]
        w8 = src[8:16]
        gv = gamma_vector(gammas, v8)
        grv = gamma_vector(gammas, mat_vec(rot, v8))
        x1 = mat_vec(gv, w8)
        y1 = mat_vec(u, x1)
        x2 = mat_vec(u, w8)
        y2 = mat_vec(grv, x2)
        rep["conjugation"] = max(
            rep["conjugation"], max(abs(y1[i] - y2[i]) for i in range(16))
        )
        rep["triality_lib"] = max(rep["triality_lib"], t["audit"]["triality_max_error"])
        rep["count"] += 1


def all_rotation_sign_checks(probe: Record, report: Record) -> None:
    """Check FP64 LU signs for all supplied samples, including non-spot trials."""
    mismatches = []
    count = 0
    for ti, trial in enumerate(probe["trials"]):
        for idx, view in enumerate(("vector", "plus", "minus")):
            sign, _ = lu_sign_logdet(square8(trial[view]))
            library_sign = trial["audit"]["views"][idx]["det_sign"]
            if sign != 1 or library_sign != sign:
                mismatches.append(
                    {
                        "trial": ti,
                        "view": view,
                        "reference_sign": sign,
                        "library_sign": library_sign,
                    }
                )
            count += 1
    report["all_rotation_signs"] = {
        "count": count,
        "mismatches": mismatches,
        "pass": not mismatches,
    }


def integer_determinant(matrix: list[list[int]]) -> int:
    """Exact Leibniz expansion by subsets, independent of pivoted LU."""
    sums = {0: 1}
    for row in matrix:
        next_sums: dict[int, int] = {}
        for used, partial in sums.items():
            for col, value in enumerate(row):
                if used & (1 << col):
                    continue
                parity = (used >> (col + 1)).bit_count() % 2
                target = used | (1 << col)
                term = partial * value * (-1 if parity else 1)
                next_sums[target] = next_sums.get(target, 0) + term
        sums = next_sums
    return sums[(1 << len(matrix)) - 1]


def chi_tests(probe: Record, gens: list[Matrix], report: Record) -> None:
    chi = gens[0]
    for i in range(1, 8):
        chi = mat_mul(chi, gens[i])
    rep = report.setdefault(
        "chi",
        {
            "residual_plus_first": None,
            "residual_minus_first": None,
            "canonical_match": None,
        },
    )
    target_a = [[0.0] * 16 for _ in range(16)]
    target_b = [[0.0] * 16 for _ in range(16)]
    for i in range(16):
        target_a[i][i] = 1.0 if i < 8 else -1.0
        target_b[i][i] = -1.0 if i < 8 else 1.0
    d_a, _ = is_close(chi, target_a, 1e-12)
    d_b, _ = is_close(chi, target_b, 1e-12)
    rep["residual_plus_first"] = d_a
    rep["residual_minus_first"] = d_b
    canon = build_canonical_gammas()
    d_canon, _ = is_close(gens[0], canon[0], 1e-12)
    for i in range(1, 8):
        d_c, _ = is_close(gens[i], canon[i], 1e-12)
        d_canon = max(d_canon, d_c)
    rep["canonical_match"] = d_canon


def pi_checks(probe: Record, gammas: list[Matrix], report: Record) -> None:
    rep = report.setdefault(
        "pi",
        {
            "two_pi": 0.0,
            "four_pi": 0.0,
            "identity_plan": 0.0,
            "det_ok": True,
            "logabsdet": 0.0,
        },
    )
    i8 = identity(8)
    neg8 = [[-1.0 if i == j else 0.0 for j in range(8)] for i in range(8)]
    spec = {
        "two_pi": {"vector": i8, "plus": neg8, "minus": neg8},
        "four_pi": {"vector": i8, "plus": i8, "minus": i8},
        "identity_plan": {"vector": i8, "plus": i8, "minus": i8},
    }
    for key in spec:
        rec = probe[key]
        for view in ("vector", "plus", "minus"):
            m = square8(rec[view])
            d, _ = is_close(spec[key][view], m, 1e-12)
            rep[key] = max(rep[key], d)
            aud = audit_of(m)
            if aud["det_sign"] != 1:
                rep["det_ok"] = False
            rep["logabsdet"] = max(rep["logabsdet"], abs(aud["log_abs_det"]))


def hadamard_checks(probe: Record, report: Record) -> None:
    rep = report.setdefault(
        "hadamard",
        {
            "inv_pair": 0.0,
            "pair_identity": 0.0,
            "orth": 0.0,
            "logabsdet": 0.0,
            "sign_ok": True,
            "reprod": 0.0,
            "reprod_indep": 0.0,
            "count": 0,
        },
    )
    h = sylvester_h(8)
    score_hd = 0.0
    score_dh = 0.0
    for rec in probe["hadamard_masks"]:
        mask = rec["mask"]
        signs = mask_signs(mask, 8)
        dmat = [[signs[i] if i == j else 0.0 for j in range(8)] for i in range(8)]
        m_hd = mat_mul(h, dmat)
        m_dh = mat_mul(dmat, h)
        f = square8(rec["f"])
        iv = square8(rec["i"])
        d_hd, _ = is_close(f, m_hd, 1e-15)
        d_dh, _ = is_close(f, m_dh, 1e-15)
        score_hd += d_hd
        score_dh += d_dh
        if d_hd <= d_dh:
            inv_expected = m_dh
        else:
            inv_expected = m_hd
        d_inv, ok = is_close(iv, inv_expected, 1e-15)
        if not ok:
            rep["inv_pair"] = max(rep["inv_pair"], d_inv)
        prod = mat_mul(f, iv)
        d_prod, ok2 = is_close(prod, identity(8), 1e-12)
        if not ok2:
            rep["pair_identity"] = max(rep["pair_identity"], d_prod)
        aud = audit_of(f)
        aud_ind = audit_of(inv_expected)
        rep["orth"] = max(rep["orth"], aud["ef"], aud_ind["ef"])
        rep["logabsdet"] = max(rep["logabsdet"], abs(aud["log_abs_det"]))
        la = rec["audit"]
        rep["reprod"] = max(
            rep["reprod"],
            abs(aud["ef"] - la["ef_normalized"]),
            abs(aud["max"] - la["max_error"]),
            abs(aud["log_abs_det"] - la["log_abs_det"]),
        )
        expected_sign = 1
        for s in signs:
            expected_sign *= int(s)
        integer = [
            [(-1 if (i & j).bit_count() % 2 else 1) * int(signs[j]) for j in range(8)]
            for i in range(8)
        ]
        exact = integer_determinant(integer)
        exact_sign = (exact > 0) - (exact < 0)
        if not (
            int(la["det_sign"])
            == aud["det_sign"]
            == aud_ind["det_sign"]
            == exact_sign
            == expected_sign
        ):
            rep["sign_ok"] = False
        mv = m_hd if d_hd <= d_dh else m_dh
        aud_mine = audit_of(mv)
        if aud_mine["det_sign"] != expected_sign:
            rep["sign_ok"] = False
        rep["reprod_indep"] = max(
            rep["reprod_indep"],
            abs(aud_mine["ef"] - la["ef_normalized"]),
            abs(aud_mine["max"] - la["max_error"]),
            abs(aud_mine["log_abs_det"] - la["log_abs_det"]),
        )
        rep["count"] += 1
    rep["orientation"] = "HD" if score_hd <= score_dh else "DH"
    rep["orientation_score_hd"] = score_hd
    rep["orientation_score_dh"] = score_dh


def block_checks(probe: Record, report: Record) -> None:
    rep = report.setdefault(
        "block",
        {
            "f64_loopback": 0.0,
            "f32_loopback": 0.0,
            "audit_f64_reprod": 0.0,
            "audit_f32_reprod": 0.0,
            "sign_ok": True,
            "f32_formula": "",
            "mapping": "",
        },
    )
    parity_note = {"sylvester": "positive_for_n_ge_4"}

    for rec in probe["hadamard_blocks"]:
        block = rec["block"]
        h = sylvester_h(block)
        aud64 = audit_of(h)
        if aud64["ef"] > 1e-12:
            rep["sign_ok"] = False
        a = rec["audit_f64"]
        c64 = 1.0 / math.sqrt(float(block))
        gerr = abs(block * c64 * c64 - 1.0)
        logabs = block * math.log(c64 * math.sqrt(float(block)))
        d_log = abs(a["log_abs_det"] - logabs)
        cands64 = {"gerr": gerr, "gerr_norm": gerr / math.sqrt(float(block))}
        d_ef = min(abs(a["ef_normalized"] - v) for v in cands64.values())
        d_max = min(abs(a["max_error"] - v) for v in cands64.values())
        rep["audit_f64_reprod"] = max(rep["audit_f64_reprod"], d_ef, d_max, d_log)
        if a["det_sign"] != 1:
            rep["sign_ok"] = False
        c32 = f32(1.0 / math.sqrt(float(block)))
        c32_alt = f32(1.0 / math.sqrt(f32(math.sqrt(float(block)))))
        b = rec["audit_f32"]
        best_c = None
        best_diff = float("inf")
        for cand, label in ((c32, "f32(1/sqrt(b))"), (c32_alt, "f32(1/sqrtf(b))")):
            gerr32 = abs(block * cand * cand - 1.0)
            logabs32 = block * math.log(abs(cand) * math.sqrt(float(block)))
            cands32 = {"gerr": gerr32, "gerr_norm": gerr32 / math.sqrt(float(block))}
            d_ef32 = min(abs(b["ef_normalized"] - v) for v in cands32.values())
            d_max32 = min(abs(b["max_error"] - v) for v in cands32.values())
            d_log32 = abs(b["log_abs_det"] - logabs32)
            diff = max(d_ef32, d_max32, d_log32)
            if diff < best_diff:
                best_diff = diff
                best_c = label
            if b["det_sign"] != 1:
                rep["sign_ok"] = False
        rep["audit_f32_reprod"] = max(rep["audit_f32_reprod"], best_diff)
        if rep["f32_formula"] and rep["f32_formula"] != best_c:
            rep["f32_formula"] = "mixed"
        else:
            rep["f32_formula"] = best_c
        if rep["mapping"] and rep["mapping"] != parity_note["sylvester"]:
            rep["mapping"] = "mixed"
        else:
            rep["mapping"] = parity_note["sylvester"]
        if rec["dtype"] == "f64":
            rep["f64_loopback"] = max(rep["f64_loopback"], rec["loopback_max"])
        else:
            rep["f32_loopback"] = max(rep["f32_loopback"], rec["loopback_max"])


def reduce_checks(probe: Record, report: Record) -> None:
    rep = report.setdefault("reduce", {"default": 0.0, "custom": 0.0})
    r = probe["reduce"]
    rows, cols = int(r["rows"]), int(r["cols"])
    flat = r["views"]
    views = [flat[k * rows * cols : (k + 1) * rows * cols] for k in range(3)]
    for i in range(rows):
        for j in range(cols):
            idx = i * cols + j
            vals = [views[k][idx] for k in range(3)]
            exp_d = sum(v * (1.0 / 3.0) for v in vals)
            exp_c = sum(v * w for v, w in zip(vals, r["custom"]))
            rep["default"] = max(rep["default"], abs(exp_d - r["out_default"][idx]))
            rep["custom"] = max(rep["custom"], abs(exp_c - r["out_custom"][idx]))


def matmul_checks(probe: Record, report: Record) -> None:
    rep = report.setdefault("matmul", {"default": 0.0, "custom": 0.0, "orth": 0.0})
    rec = probe["matmul"]
    mats = [square8(rec["matrices"][k * 64 : (k + 1) * 64]) for k in range(3)]
    rep["orth"] = max(rep["orth"], max(audit_of(m)["ef"] for m in mats))
    m, n, k = 6, 5, 8
    A = [[rec["A"][i * k + j] for j in range(k)] for i in range(m)]
    B = [[rec["B"][i * k + j] for j in range(k)] for i in range(n)]

    def triple(weights: Any) -> Any:
        out = [[0.0] * n for _ in range(m)]
        for i in range(m):
            for j in range(n):
                acc = 0.0
                for vi, mv in enumerate(mats):
                    av = mat_vec(mv, A[i])
                    bv = mat_vec(mv, B[j])
                    acc += weights[vi] * sum(av[x] * bv[x] for x in range(8))
                out[i][j] = acc
        return out

    for i in range(m):
        for j in range(n):
            rep["default"] = max(
                rep["default"],
                abs(triple([1.0 / 3.0] * 3)[i][j] - rec["out_default"][i * n + j]),
            )
    outc = triple(rec["custom"])
    for i in range(m):
        for j in range(n):
            rep["custom"] = max(
                rep["custom"], abs(outc[i][j] - rec["out_custom"][i * n + j])
            )


def attention_checks(probe: Record, report: Record) -> None:
    rep = report.setdefault("attention", {"value": 0.0, "orth": 0.0, "rows_used": 0})
    rec = probe["attention"]
    nq, nk, d, dv = int(rec["nq"]), int(rec["nk"]), int(rec["d"]), int(rec["dv"])
    q = [[rec["q"][i * d + j] for j in range(d)] for i in range(nq)]
    k = [[rec["k"][i * d + j] for j in range(d)] for i in range(nk)]
    v = [[rec["v"][i * dv + j] for j in range(dv)] for i in range(nk)]
    mats = [
        square8(probe["matmul"]["matrices"][vi * 64 : (vi + 1) * 64]) for vi in range(3)
    ]
    rep["orth"] = max(rep["orth"], max(audit_of(m)["ef"] for m in mats))
    scale = math.sqrt(float(d))
    for i in range(nq):
        allowed = [j for j in range(nk) if int(rec["mask"][i * nk + j]) != 0]
        if not allowed:
            continue
        logits = []
        for j in allowed:
            s = 0.0
            for vi in range(3):
                qv = mat_vec(mats[vi], q[i])
                kv = mat_vec(mats[vi], k[j])
                s += (1.0 / 3.0) * sum(qv[x] * kv[x] for x in range(d))
            logits.append(s / scale)
        sx = softmax(logits)
        for x in range(dv):
            acc = sum(sx[t] * v[allowed[t]][x] for t in range(len(allowed)))
            rep["value"] = max(rep["value"], abs(acc - rec["out"][i * dv + x]))
        rep["rows_used"] += 1


def cc16_from_gammas(gammas: list[Matrix], c: Any) -> Matrix:
    out = [[0.0] * 8 for _ in range(8)]
    for i in range(8):
        gi = gammas[i]
        for a in range(8):
            s = 0.0
            for b in range(8):
                s += gi[a][8 + b] * c[b]
            out[i][a] = s
    return out


def a16_of(gammas: list[Matrix], c: Any) -> Matrix:
    cmat = cc16_from_gammas(gammas, c)
    e0 = cc16_from_gammas(gammas, [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    return mat_mul(cmat, mat_t(e0))


def chart_v1(h: Any) -> list[float]:
    nrm = math.sqrt(sum(x * x for x in h) + 1.0)
    u = [(math.pi / 8.0) * x / nrm for x in h]
    th = math.sqrt(sum(x * x for x in u))
    c = [0.0] * 8
    if th == 0.0:
        c[0] = 1.0
    else:
        c[0] = math.cos(th)
        for i in range(7):
            c[i + 1] = math.sin(th) * u[i] / th
    return c


def query1_checks(probe: Record, gammas: list[Matrix], report: Record) -> None:
    rep = report.setdefault(
        "query1",
        {
            "spinor_chart": 0.0,
            "a_orth": 0.0,
            "a_match": 0.0,
            "a_det_ok": True,
            "a_reprod": 0.0,
            "action": 0.0,
            "tail_ok": True,
            "f32": 0.0,
            "identity_ok": True,
            "cases": 0,
        },
    )
    sec = probe["query1"]
    for case in sec["cases"]:
        h = case["h"]
        c_exp = chart_v1(h)
        rep["spinor_chart"] = max(
            rep["spinor_chart"],
            max(abs(c_exp[i] - case["spinor"][i]) for i in range(8)),
        )
        a_py = a16_of(gammas, c_exp)
        aud = audit_of(a_py)
        rep["a_orth"] = max(rep["a_orth"], aud["ef"])
        if aud["det_sign"] != 1:
            rep["a_det_ok"] = False
        rep["a_reprod"] = max(
            rep["a_reprod"],
            abs(aud["ef"] - case["audit"]["ef_normalized"]),
            abs(aud["max"] - case["audit"]["max_error"]),
            abs(aud["log_abs_det"] - case["audit"]["log_abs_det"]),
        )
        if int(case["audit"]["det_sign"]) != aud["det_sign"]:
            rep["a_det_ok"] = False
        d, _ = is_close(a_py, square8(case["matrix"]), 1e-12)
        rep["a_match"] = max(rep["a_match"], d)
        rows, width = 3, 20
        worst = 0.0
        for r in range(rows):
            for g in range(2):
                xg = case["src"][r * width + g * 8 : r * width + g * 8 + 8]
                yg = case["dst"][r * width + g * 8 : r * width + g * 8 + 8]
                y = mat_vec(a_py, xg)
                worst = max(worst, max(abs(y[k] - yg[k]) for k in range(8)))
            if (
                case["src"][r * width + 16 : r * width + 20]
                != case["dst"][r * width + 16 : r * width + 20]
            ):
                rep["tail_ok"] = False
        rep["action"] = max(rep["action"], worst)
        rep["cases"] += 1
    ident = sec["identity"]
    rep["identity_ok"] = bool(ident["byte_identical"]) and bool(
        ident["matrix_is_identity"]
    )
    rep["identity_spinor_max_e0"] = max(
        abs(ident["spinor"][0] - 1.0), max(abs(x) for x in ident["spinor"][1:])
    )
    fc = sec["f32_case"]
    a_py = a16_of(gammas, chart_v1(fc["h"]))
    rows, width = 3, 20
    worst = 0.0
    for r in range(rows):
        for g in range(2):
            xg = fc["src"][r * width + g * 8 : r * width + g * 8 + 8]
            y = mat_vec(a_py, xg)
            for k in range(8):
                worst = max(worst, abs(f32(y[k]) - fc["dst"][r * width + g * 8 + k]))
    rep["f32"] = worst


def query3_checks(probe: Record, gammas: list[Matrix], report: Record) -> None:
    tau = math.tan(math.pi / 8.0)
    rep = report.setdefault(
        "query3",
        {
            "j_table": 0.0,
            "basis_audit": 0.0,
            "zero_ok": True,
            "apply": 0.0,
            "spinors": 0.0,
            "matrix": 0.0,
            "vjp": 0.0,
            "vjp_zero": 0.0,
        },
    )
    sec = probe["query3"]
    jflat = sec["generators"]
    for a in range(1, 8):
        cj = [1.0 if i == a else 0.0 for i in range(8)]
        j_py = a16_of(gammas, cj)
        j_lib = [[jflat[(a - 1) * 64 + r * 8 + c] for c in range(8)] for r in range(8)]
        d, _ = is_close(j_py, j_lib, 1e-12)
        rep["j_table"] = max(rep["j_table"], d)
    b = sec["basis_audit"]
    rep["basis_audit"] = max(
        b["normed_max_error"],
        b["polarization_max_error"],
        b["skew_max_error"],
        b["clifford_max_error"],
    )
    zero = sec["zero"]
    rep["zero_ok"] = bool(zero["byte_identical"]) and bool(zero["spinors_exact_e0"])
    rep["zero_spinor_max_e0"] = max(
        abs(zero["spinors"][0] - 1.0), max(abs(x) for x in zero["spinors"][1:8])
    )

    def chart_v3(h: Any) -> Any:
        nrm = math.sqrt(tau * tau + sum(x * x for x in h))
        u = [tau * x / nrm for x in h]
        un = math.sqrt(sum(x * x for x in u) + 1.0)
        return [1.0 / un] + [x / un for x in u]

    def controller_output(
        win: Any, binv: Any, wout: Any, bout: Any, qrow: Any, width: Any
    ) -> Any:
        z = [
            sum(win[i * width + k] * qrow[k] for k in range(width)) + binv[i]
            for i in range(8)
        ]
        ah = [math.tanh(v) for v in z]
        h = [sum(wout[j * 8 + i] * ah[i] for i in range(8)) + bout[j] for j in range(7)]
        cvec = chart_v3(h)
        arot = a16_of(gammas, cvec)
        row = []
        g = 0
        while g + 8 <= width:
            row.extend(mat_vec(arot, qrow[g : g + 8]))
            g += 8
        row.extend(qrow[g:width])
        return row, cvec

    width = 20
    nz = sec["nonzero"]
    win = nz["params_win"]
    binv = nz["params_bin"]
    wout = nz["params_wout"]
    bout = nz["params_bout"]
    src = nz["src"]
    rows = len(src) // width
    dst = nz["dst"]
    worst = 0.0
    spins_py = []
    for r in range(rows):
        row, cvec = controller_output(
            win, binv, wout, bout, src[r * width : (r + 1) * width], width
        )
        spins_py.append(cvec)
        for i in range(width):
            worst = max(worst, abs(row[i] - dst[r * width + i]))
    rep["apply"] = worst
    sp = nz["spinors"]
    for r in range(rows):
        for i in range(8):
            rep["spinors"] = max(rep["spinors"], abs(spins_py[r][i] - sp[r * 8 + i]))
    d, _ = is_close(a16_of(gammas, spins_py[0]), square8(nz["case0_matrix"]), 1e-12)
    rep["matrix"] = d
    rep["matrix_from_lib_spinor"] = max(
        abs(a16_of(gammas, sp[0:8])[i][j] - nz["case0_matrix"][i * 8 + j])
        for i in range(8)
        for j in range(8)
    )

    def loss_for(
        win_: Any, bin_: Any, wout_: Any, bout_: Any, qrow: Any, dy: Any
    ) -> Any:
        row, _ = controller_output(win_, bin_, wout_, bout_, qrow, width)
        return sum(dy[i] * row[i] for i in range(len(dy)))

    dy = sec["vjp"]["dy"]
    qrow = sec["vjp_zero"]["q"]

    def fd_grads(params_t: Any, perturb_q: Any) -> Any:
        grads = {
            "dq": [0.0] * width,
            "dwin": [0.0] * 160,
            "dbin": [0.0] * 8,
            "dwout": [0.0] * 56,
            "dbout": [0.0] * 7,
        }
        hv = 1e-6
        wp, bp, wo, bo = params_t
        if perturb_q:
            for gi in range(width):
                qp = qrow[:]
                qp[gi] += hv
                qm = qrow[:]
                qm[gi] -= hv
                grads["dq"][gi] = (
                    loss_for(wp, bp, wo, bo, qp, dy) - loss_for(wp, bp, wo, bo, qm, dy)
                ) / (2 * hv)
        for gi in range(160):
            wp1 = list(wp)
            wp1[gi] += hv
            wm1 = list(wp)
            wm1[gi] -= hv
            grads["dwin"][gi] = (
                loss_for(wp1, bp, wo, bo, qrow, dy)
                - loss_for(wm1, bp, wo, bo, qrow, dy)
            ) / (2 * hv)
        for gi in range(8):
            bp1 = list(bp)
            bp1[gi] += hv
            bm1 = list(bp)
            bm1[gi] -= hv
            grads["dbin"][gi] = (
                loss_for(wp, bp1, wo, bo, qrow, dy)
                - loss_for(wp, bm1, wo, bo, qrow, dy)
            ) / (2 * hv)
        for gi in range(56):
            wo1 = list(wo)
            wo1[gi] += hv
            wm1 = list(wo)
            wm1[gi] -= hv
            grads["dwout"][gi] = (
                loss_for(wp, bp, wo1, bo, qrow, dy)
                - loss_for(wp, bp, wm1, bo, qrow, dy)
            ) / (2 * hv)
        for gi in range(7):
            bo1 = list(bo)
            bo1[gi] += hv
            bm1 = list(bo)
            bm1[gi] -= hv
            grads["dbout"][gi] = (
                loss_for(wp, bp, wo, bo1, qrow, dy)
                - loss_for(wp, bp, wo, bm1, qrow, dy)
            ) / (2 * hv)
        return grads

    def grad_diff(lib_grads: Any, fd_grads_map: Any) -> Any:
        worst = 0.0
        for key in ("dq", "dwin", "dbin", "dwout", "dbout"):
            for i in range(len(lib_grads[key])):
                worst = max(worst, abs(lib_grads[key][i] - fd_grads_map[key][i]))
        return worst

    fdz = fd_grads(([0.0] * 160, [0.0] * 8, [0.0] * 56, [0.0] * 7), True)
    rep["vjp_zero"] = grad_diff(sec["vjp_zero"]["grads"], fdz)
    fdn = fd_grads((win, binv, wout, bout), True)
    rep["vjp"] = grad_diff(sec["vjp"]["grads"], fdn)


def extended_checks(probe: Record, gammas: list[Matrix], report: Record) -> None:
    rep = report.setdefault("extended", {"tail": True, "loopback": 0.0, "action": 0.0})
    rec = probe["extended_loopback"]
    rep["tail"] = bool(rec["tail_byte_equal"])
    rep["loopback"] = rec["loopback_max"]
    planes = [(int(p[0]), int(p[1]), float(p[2])) for p in parse_planes(rec["planes"])]
    cache = {}
    u = compose_planes(planes, gammas, cache)
    rot, _vfit = vector_rot_from_u(u, gammas)
    src = rec["src"]
    fwd = rec["fwd"]
    worst = 0.0
    for r in range(64):
        for g in range(2):
            xg = src[r * 20 + g * 8 : r * 20 + g * 8 + 8]
            yg = fwd[r * 20 + g * 8 : r * 20 + g * 8 + 8]
            y = mat_vec(rot, xg)
            worst = max(worst, max(abs(y[k] - yg[k]) for k in range(8)))
    rep["action"] = worst


def validate_probe(probe: Record) -> None:
    """Reject incomplete samples and non-finite JSON before numerical checks."""
    if probe.get("schema") != "gateA-spin8-probe-v1":
        raise ValueError("unsupported probe schema")
    trials = probe["trials"]
    checked = probe["python_check"]
    if not (1 <= checked <= len(trials) == probe["trials_total"]):
        raise ValueError("inconsistent trial counts")
    if len(probe["generators"]) != 2048:
        raise ValueError("expected eight 16x16 generators")
    if sorted(rec["mask"] for rec in probe["hadamard_masks"]) != list(range(256)):
        raise ValueError("expected every Hadamard mask exactly once")
    for rec in probe["hadamard_masks"]:
        if len(rec["f"]) != 64 or len(rec["i"]) != 64:
            raise ValueError("expected 8x8 Hadamard matrices")
    for trial in trials:
        if any(len(trial[view]) != 64 for view in ("vector", "plus", "minus")):
            raise ValueError("expected 8x8 rotation samples")
    for trial in trials[:checked]:
        if not trial["planes"] or len(trial["planes"]) % 3:
            raise ValueError("invalid rotation planes")

    def finite(value: Any) -> None:
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("non-finite probe value")
        if isinstance(value, dict):
            for child in value.values():
                finite(child)
        elif isinstance(value, list):
            for child in value:
                finite(child)

    finite(probe)


def run_reference(probe: Record) -> Record:
    """Compare a complete probe record; importing this module runs no checks."""
    validate_probe(probe)
    report = {"schema": "gateA-spin8-reference-v2"}
    library_gammas = unpack_gens_16(probe["generators"])
    gammas = build_canonical_gammas()
    La, Ls_, Lsq = finite_L_checks(build_L())
    report["reference_builder"] = {
        "L_anticomm": La,
        "L_skew": Ls_,
        "L_square": Lsq,
        "gamma_canonical_anticomm": structural_checks(build_canonical_gammas())[0],
    }
    chi_tests(probe, library_gammas, report)
    report["chi"]["clifford_max"] = max(structural_checks(library_gammas))
    chi_plus_first = None
    if report["chi"]["residual_plus_first"] <= 1e-12:
        chi_plus_first = True
    elif report["chi"]["residual_minus_first"] <= 1e-12:
        chi_plus_first = False
    trial_checks(probe, gammas, chi_plus_first, report)
    all_rotation_sign_checks(probe, report)
    pi_checks(probe, gammas, report)
    hadamard_checks(probe, report)
    block_checks(probe, report)
    reduce_checks(probe, report)
    matmul_checks(probe, report)
    attention_checks(probe, report)
    query1_checks(probe, gammas, report)
    query3_checks(probe, gammas, report)
    extended_checks(probe, gammas, report)

    rb = report["reference_builder"]
    checks = []
    checks.append(
        (
            "reference_builder",
            max(
                rb["L_anticomm"],
                rb["L_skew"],
                rb["L_square"],
                rb["gamma_canonical_anticomm"],
            )
            <= 1e-12,
        )
    )
    checks.append(
        (
            "generators",
            (
                report["chi"]["residual_plus_first"] <= 1e-12
                or report["chi"]["residual_minus_first"] <= 1e-12
            )
            and report["chi"]["canonical_match"] <= 1e-12
            and report["chi"]["clifford_max"] <= 1e-12,
        )
    )
    t = report["trial"]
    checks.append(
        (
            "trial",
            max(
                t["vector_vs_R"],
                t["vector_fit_residual"],
                t["orth_lib"],
                t["eigs_match"],
                t["audit_reprod"],
                t["fwd_action_vs_R"],
                t["conjugation"],
                t["u_orth"],
                t["group_inverse"],
                t["blocks_direct_plus"],
                t["blocks_direct_minus"],
            )
            <= 1e-12
            and t["det_ok"]
            and t["u_det_ok"]
            and t["triality_lib"] <= 1e-12
            and t["rational_sign_ok"]
            and report["all_rotation_signs"]["pass"]
            and t["loopback_f64"] <= 1e-12
            and t["loopback_f32"] <= 1e-5,
        )
    )
    p = report["pi"]
    checks.append(
        (
            "pi",
            max(p["two_pi"], p["four_pi"], p["identity_plan"], p["logabsdet"]) <= 1e-12
            and p["det_ok"],
        )
    )
    hd = report["hadamard"]
    checks.append(
        (
            "hadamard",
            hd["inv_pair"] <= 1e-15
            and hd["pair_identity"] <= 1e-12
            and hd["orth"] <= 1e-12
            and hd["logabsdet"] <= 1e-12
            and hd["sign_ok"]
            and hd["reprod"] <= 1e-9
            and hd["reprod_indep"] <= 1e-9,
        )
    )
    bl = report["block"]
    checks.append(
        (
            "block",
            bl["f64_loopback"] <= 1e-12
            and bl["f32_loopback"] <= 1e-5
            and bl["audit_f64_reprod"] <= 1e-9
            and bl["audit_f32_reprod"] <= 1e-6
            and bl["sign_ok"],
        )
    )
    rc = report["reduce"]
    checks.append(("reduce", rc["default"] <= 1e-15 and rc["custom"] <= 1e-15))
    mm = report["matmul"]
    checks.append(
        (
            "matmul",
            mm["default"] <= 1e-12 and mm["custom"] <= 1e-12 and mm["orth"] <= 1e-12,
        )
    )
    at = report["attention"]
    checks.append(("attention", at["value"] <= 1e-12 and at["orth"] <= 1e-12))
    q1 = report["query1"]
    checks.append(
        (
            "query1",
            max(
                q1["spinor_chart"],
                q1["a_orth"],
                q1["a_match"],
                q1["a_reprod"],
                q1["action"],
            )
            <= 1e-12
            and q1["spinor_chart"] <= 1e-13
            and q1["a_det_ok"]
            and q1["tail_ok"]
            and q1["f32"] <= 1e-5
            and q1["identity_ok"],
        )
    )
    q3 = report["query3"]
    checks.append(
        (
            "query3",
            max(
                q3["j_table"],
                q3["basis_audit"],
                q3["apply"],
                q3["spinors"],
                q3["matrix"],
            )
            <= 1e-12
            and q3["vjp"] <= 5e-5
            and q3["vjp_zero"] <= 5e-5
            and q3["zero_ok"],
        )
    )
    ex = report["extended"]
    checks.append(
        ("extended", ex["tail"] and ex["loopback"] <= 1e-12 and ex["action"] <= 1e-12)
    )
    report["checks"] = [{"name": nm, "pass": ok} for (nm, ok) in checks]
    report["verdict"] = "PASS" if all(ok for _, ok in checks) else "FAIL"
    return report


def file_hash(path: Path) -> str:
    """Hash file bytes without loading large inputs at once."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main(argv: list[str] | None = None) -> int:
    """Run explicit input/output comparison and write a source-bound receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--input-mode", choices=("fresh", "replay"), required=True)
    parser.add_argument(
        "--source-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument(
        "--artifact",
        type=Path,
        action="append",
        default=[],
        help="Additional build/library/executable receipt to hash",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        if args.report.exists():
            raise ValueError("report already exists; choose a fresh output path")
        root = args.source_root.resolve()
        sources = [root / "spin8" / "CMakeLists.txt"]
        for folder in ("src", "include", "third_party"):
            sources.extend(
                sorted(p for p in (root / "spin8" / folder).rglob("*") if p.is_file())
            )
        sources.extend(
            [
                Path(__file__).resolve(),
                root / "tools" / "test_spin8_reference_compare.py",
            ]
        )
        sources.extend(
            sorted(
                p
                for p in (root / "tools" / "spin8_reference_probe").rglob("*")
                if p.is_file() and p.suffix in (".cpp", ".h", ".py", ".txt", ".md")
            )
        )
        source_hashes = {str(p.relative_to(root)): file_hash(p) for p in sources}
        input_hash = file_hash(args.probe)
        artifact_hashes = {str(p): file_hash(p) for p in args.artifact}
        revision = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        with args.probe.open(encoding="utf-8") as stream:
            probe = json.load(stream)
        report = run_reference(probe)
        if file_hash(args.probe) != input_hash or any(
            file_hash(p) != source_hashes[str(p.relative_to(root))] for p in sources
        ):
            raise ValueError("input or source changed during comparison")
        report["provenance"] = {
            "input_mode": args.input_mode,
            "input_sha256": input_hash,
            "source_sha256": source_hashes,
            "artifact_sha256": artifact_hashes,
            "git_head": revision,
            "python": sys.version,
            "scope": "CPU FP64 reference; no CUDA validation",
        }
        with args.report.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        logging.info("VERDICT %s", report["verdict"])
        for check in report["checks"]:
            logging.info(
                "FAMILY %s %s", check["name"], "PASS" if check["pass"] else "FAIL"
            )
        return 0 if report["verdict"] == "PASS" else 2
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        subprocess.CalledProcessError,
    ) as exc:
        logging.error("FAIL %s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
