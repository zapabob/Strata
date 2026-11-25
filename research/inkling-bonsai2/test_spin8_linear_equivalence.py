import numpy as np
import pytest
from spin8_quantizer import Basis, mixed_apply


@pytest.mark.parametrize("width", [1152, 2304])
@pytest.mark.parametrize("kind", ["V", "P", "M", "diagonal-M", "hadamard", "signed", "random"])
def test_unquantised_linear_maps(width, kind):
    rng = np.random.default_rng(121)
    w, x = rng.standard_normal((7, width)), rng.standard_normal((5, width))
    for block in (64, 128, 256, 512):
        b = Basis(kind, block, .1)
        if width % block:
            with pytest.raises(ValueError):
                b.apply(w)
        else:
            np.testing.assert_allclose(b.apply(w) @ b.apply(x).T, w @ x.T, atol=2e-12)
    parts = [Basis(kind, 512, .1)] * (width // 512) + [Basis(kind, width % 512, .1)]
    np.testing.assert_allclose(mixed_apply(w, parts) @ mixed_apply(x, parts).T, w @ x.T, atol=2e-12)
