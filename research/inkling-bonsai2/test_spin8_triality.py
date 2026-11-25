import numpy as np
import pytest
from spin8_clifford import sylvester, triality_form
from spin8_triality import spin_lift, vector_rotation, verify_lift


@pytest.mark.parametrize("theta", [0., .21, -.37])
def test_entire_triality_tensor(theta):
    h = sylvester(8)
    assert abs(np.linalg.det(h) - 1) < 1e-13
    lift = spin_lift(vector_rotation(theta))
    results = verify_lift(lift)
    for key in ["orthogonality", "chirality_commutator", "multiplication_intertwiner",
                "invariant_tensor", "vector_conjugation"]:
        assert results[key] < 5e-13
    assert np.allclose(results["determinants"], 1, atol=1e-13)
    v, p, m = np.random.default_rng(49).normal(size=(3, 8))
    assert abs(triality_form(lift.vector @ v, lift.positive @ p, lift.negative @ m) -
               triality_form(v, p, m)) < 5e-12


def test_orientation_is_checked():
    with pytest.raises(ValueError):
        spin_lift(np.diag([-1] + [1] * 7))
    with pytest.raises(ValueError):
        vector_rotation(signs=[-1] + [1] * 7)
    verify_lift(spin_lift(vector_rotation(signs=[-1, -1] + [1] * 6)))
