"""Independent determinant regressions for the CPU Spin8 reference."""

import math

import pytest

import spin8_reference_compare as ref


@pytest.mark.parametrize(
    "matrix, sign, magnitude",
    [
        ([[1.0, 0.0], [0.0, 1.0]], 1, 1.0),
        ([[-1.0, 0.0], [0.0, 1.0]], -1, 1.0),
        ([[0.0, 1.0], [1.0, 0.0]], -1, 1.0),
        ([[0.0, 1.0], [-1.0, 0.0]], 1, 1.0),
        ([[-1.0, 0.0], [0.0, -1.0]], 1, 1.0),
        ([[1.0, 2.0], [2.0, 4.0]], 0, 0.0),
        ([[-2.0, 0.0], [0.0, 3.0]], -1, 6.0),
    ],
    ids=[
        "identity",
        "reflection",
        "odd-permutation",
        "quarter-turn",
        "two-reflections",
        "singular",
        "negative-log-magnitude",
    ],
)
def test_lu_sign_and_log_magnitude(
    matrix: list[list[float]], sign: int, magnitude: float
) -> None:
    original = [row[:] for row in matrix]
    actual_sign, actual_log = ref.lu_sign_logdet(matrix)
    assert actual_sign == sign
    if sign:
        assert actual_log == pytest.approx(math.log(magnitude), abs=1e-14)
    else:
        assert actual_log == -math.inf
    assert matrix == original


def integer_det(matrix: list[list[int]]) -> int:
    """Integer Bareiss oracle, separately written from the subset reference."""
    n = len(matrix)
    a = [row[:] for row in matrix]
    previous = 1
    sign = 1
    for k in range(n - 1):
        if not a[k][k]:
            pivot = next((r for r in range(k + 1, n) if a[r][k]), None)
            if pivot is None:
                return 0
            a[k], a[pivot] = a[pivot], a[k]
            sign = -sign
        pivot_value = a[k][k]
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                a[i][j] = (a[i][j] * pivot_value - a[i][k] * a[k][j]) // previous
            a[i][k] = 0
        previous = pivot_value
    return sign * a[-1][-1]


@pytest.mark.parametrize("mask", range(256))
def test_every_signed_hadamard(mask: int) -> None:
    # Walsh entries are built directly from bit parity, independently of the
    # reference's recursive Sylvester construction and determinant algorithm.
    integer = [
        [
            (-1 if (row & col).bit_count() % 2 else 1)
            * (-1 if mask & (1 << col) else 1)
            for col in range(8)
        ]
        for row in range(8)
    ]
    exact = integer_det(integer)
    assert ref.integer_determinant(integer) == exact
    parity = -1 if mask.bit_count() % 2 else 1
    assert exact == parity * 4096
    matrix = [[x / math.sqrt(8) for x in row] for row in integer]
    sign, log_magnitude = ref.lu_sign_logdet(matrix)
    assert sign == parity == (1 if exact > 0 else -1)
    assert log_magnitude == pytest.approx(0.0, abs=2e-14)


@pytest.mark.parametrize("bad", [[], [[1, 2]], [[math.nan]], [[math.inf]]])
def test_invalid_determinant_input(bad: list[list[float]]) -> None:
    with pytest.raises(ValueError):
        ref.lu_sign_logdet(bad)


def test_all_rotation_signs_include_samples_outside_spot_checks() -> None:
    good = ref.flat8(ref.identity(8))
    reflected = good[:]
    reflected[0] = -1.0
    trial = {
        "vector": good,
        "plus": good,
        "minus": good,
        "audit": {"views": [{"det_sign": 1}] * 3},
    }
    bad = {**trial, "minus": reflected}
    report = {}
    ref.all_rotation_sign_checks({"trials": [trial, bad], "python_check": 1}, report)
    signs = report["all_rotation_signs"]
    assert signs["count"] == 6
    assert signs["pass"] is False
    assert signs["mismatches"] == [
        {"trial": 1, "view": "minus", "reference_sign": -1, "library_sign": 1}
    ]


def minimal_probe() -> dict:
    """Only the validation boundary's required fields, with one rotation."""
    ident = ref.flat8(ref.identity(8))
    return {
        "schema": "gateA-spin8-probe-v1",
        "trials_total": 1,
        "python_check": 1,
        "generators": [0.0] * 2048,
        "trials": [
            {"vector": ident, "plus": ident, "minus": ident, "planes": [0, 1, 0.5]}
        ],
        "hadamard_masks": [{"mask": i, "f": ident, "i": ident} for i in range(256)],
    }


@pytest.mark.parametrize("defect", ["mask", "count", "finite", "shape"])
def test_incomplete_or_invalid_probe_rejected(defect: str) -> None:
    probe = minimal_probe()
    if defect == "mask":
        probe["hadamard_masks"][-1]["mask"] = 0
    elif defect == "count":
        probe["python_check"] = 0
    elif defect == "finite":
        probe["trials"][0]["vector"][0] = math.nan
    else:
        probe["trials"][0]["vector"] = [1.0]
    with pytest.raises(ValueError):
        ref.validate_probe(probe)
