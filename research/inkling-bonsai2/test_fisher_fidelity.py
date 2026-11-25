import numpy as np
import pytest

from fisher_fidelity import fisher_action, gauss_newton_vector, row_metrics


def test_softmax_shift_and_finite_difference():
    z=np.array([-.4,1.3,.2,-.9])
    u=np.array([2.,-.7,.9,.2])*0.0001
    m=row_metrics(z,z+u,1)
    assert m["quadratic_kl_nats"] == pytest.approx(m["kl_nats"], rel=.001)
    assert abs(row_metrics(z,z+13.,1)["kl_nats"])<1e-12
    assert abs(row_metrics(z,z+13.,1)["quadratic_kl_nats"])<1e-28


def test_expanded_vocabulary_support_mass():
    z=np.array([-.4,1.3,.2,-.9])
    m=row_metrics(z,np.append(z,2.),0)
    assert m["support_penalty_nats"] == pytest.approx(m["kl_nats"])
    assert m["quadratic_kl_nats"] == 0


def test_shared_three_visit_gauss_newton():
    import torch
    z=torch.tensor([.12,.23,-.41],dtype=torch.double)
    v=torch.tensor([-.3,.2,.6],dtype=torch.double)
    def recurrent(w):
        h=z
        for _ in range(3):
            h=(h.roll(1)+w*h+.27*w).tanh()
        return h
    result,=gauss_newton_vector(recurrent,(z,),(v,))
    j=torch.autograd.functional.jacobian(recurrent,z).numpy()
    p=recurrent(z).softmax(dim=-1).numpy()
    expected=j.T@fisher_action(p,j@v.numpy())
    np.testing.assert_allclose(result.numpy(),expected,atol=1e-14)
