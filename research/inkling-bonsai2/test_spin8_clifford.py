import numpy as np
from spin8_clifford import chirality, generators


def test_all_anticommutators_and_even_products():
    g = generators()
    omega, p, m = chirality()
    assert p.shape == m.shape == (16, 8)
    np.testing.assert_array_equal(omega @ omega, np.eye(16))
    for i in range(8):
        for j in range(8):
            a = g[i] @ g[j]
            np.testing.assert_array_equal(a + g[j] @ g[i], -2 * (i == j) * np.eye(16))
            np.testing.assert_array_equal(a @ omega, omega @ a)
