import numpy as np
from scipy.linalg import expm
from spin8_clifford import chiral_tensor, chirality
from spin8_continuous import continuous_octets, infinitesimal, optimise_continuously
from spin8_triality import spin_lift, vector_rotation
from spin8_quantizer import fit, decode
from activation_optimisation import block_covariance, fit_covariance, rotate


def test_full_lie_algebra_and_exact_triality_in_every_plane():
    c=chiral_tensor()
    theta=np.linspace(-.12,.2,28)
    for t in [theta,*np.eye(28)*.07]:
        v,p,m=continuous_octets(tuple(t))
        np.testing.assert_allclose(np.einsum("ji,jmp->imp",v,c)@p,m@c,atol=2e-13)
        for r in (v,p,m):np.testing.assert_allclose(r.T@r,np.eye(8),atol=4e-13)
    _,generators,_,_=infinitesimal()
    total=spin_lift(vector_rotation()).even@expm(np.tensordot(theta,generators,axes=1))
    _,bp,bm=chirality()
    v,p,m=continuous_octets(tuple(theta))
    np.testing.assert_allclose(p,bp.T@total@bp,atol=2e-13)
    np.testing.assert_allclose(m,bm.T@total@bm,atol=2e-13)
    for l in (infinitesimal()[0],infinitesimal()[2],infinitesimal()[3]):
        assert np.linalg.matrix_rank(l.reshape(28,-1))==28


def test_correlated_objective_monotone_and_budget():
    rng=np.random.default_rng(12)
    x=rng.standard_normal((12,128))
    w=rng.standard_normal((8,128))
    r=np.eye(128)
    c=block_covariance([x[:4],x[4:8],x[8:]],r)
    np.testing.assert_allclose(c[0],x.T@x/len(x),atol=5e-15)
    old=decode(fit(w,c[0].diagonal()),w.shape)
    optim=decode(fit_covariance(w,c),w.shape)
    assert np.mean(((w-optim)@x.T)**2)<=np.mean(((w-old)@x.T)**2)
    theta,hist=optimise_continuously(lambda t:np.sum((t-.2)**2),7)
    assert len(hist)==7 and theta.shape==(28,)
