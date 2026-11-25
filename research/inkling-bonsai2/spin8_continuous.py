"""Continuous proper rotations and their lifted actions on both real chiral modules."""
from functools import lru_cache
from itertools import combinations
import numpy as np
from scipy.linalg import expm

from spin8_clifford import chirality, generators, sylvester
from spin8_triality import spin_lift, vector_rotation


PLANES=tuple(combinations(range(8),2))


@lru_cache(maxsize=1)
def infinitesimal():
    g=generators().astype(np.float64)
    vector=np.zeros((28,8,8))
    for n,(i,j) in enumerate(PLANES):vector[n,j,i],vector[n,i,j]=1,-1
    spin=np.stack([.5*(g[i]@g[j]) for i,j in PLANES])
    _,p,m=chirality()
    return vector,spin,p.T@spin@p,m.T@spin@m


@lru_cache(maxsize=128)
def continuous_octets(parameters):
    t=np.asarray(parameters,np.float64)
    if t.shape!=(28,) or not np.isfinite(t).all():raise ValueError("Expected 28 finite bivector coordinates")
    base=spin_lift(vector_rotation())
    v,_,p,m=infinitesimal()
    return tuple(a@expm(np.tensordot(t,l,axes=1)) for a,l in zip((base.vector,base.positive,base.negative),(v,p,m)))


def octet_basis(kind,theta):
    v,p,m=continuous_octets(tuple(theta))
    return np.kron(sylvester(16),{"V":v,"P":p,"M":m}[kind])


def optimise_continuously(score,budget,seed=8128,radius=.28):
    """A deterministic random-direction trust-region search with an explicit evaluation budget."""
    if budget<1:raise ValueError("Positive evaluation budget required")
    rng=np.random.default_rng(seed)
    centre=np.zeros(28,dtype=np.float32)
    best=float(score(centre)); history=[best]
    while len(history)<budget:
        d=rng.normal(size=28)
        d=(radius*d/np.linalg.norm(d)).astype(np.float32)
        proposals=[centre+d,centre-d][:budget-len(history)]
        values=[float(score(x)) for x in proposals]
        history.extend(values)
        idx=int(np.argmin(values))
        if values[idx]<best:best,centre=values[idx],proposals[idx]
        else:radius*=.72
    return centre,history
