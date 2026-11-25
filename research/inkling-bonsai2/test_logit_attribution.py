import numpy as np
import pytest

from logit_attribution import at_position


def test_offset_invariance_and_unobserved_candidate_vocab():
    a=np.array([3.,2.,2.,-1.])
    b=np.array([.3,.22,.5,-.1,1.2])
    r=at_position(a,b,1)
    s=at_position(a+19,b-400,1)
    for k in ("kl","target_specific_nll","nll_change","target_margin_change","entropy_change"):
        assert s[k]==pytest.approx(r[k],abs=1e-11)
    assert r["reference"]["rank"]==2
    assert r["candidate"]["rank"]==4
    assert r["nll_change"]==pytest.approx(r["kl"]+r["target_specific_nll"])
    assert r["nll_change"]==pytest.approx(r["log_partition_change"]-r["raw_target_logit_change"])


def test_expected_target_residual_is_zero():
    a=np.array([.2,1.,-.3])
    b=np.array([.4,.2,1.])
    p=np.exp(a)/np.exp(a).sum()
    rows=[at_position(a,b,i) for i in range(3)]
    assert p@[r["target_specific_nll"] for r in rows]==pytest.approx(0.,abs=1e-14)
    assert p@[r["nll_change"] for r in rows]==pytest.approx(rows[0]["kl"])
