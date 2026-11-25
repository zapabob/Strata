"""Block covariance, correlated ternary coordinate descent and paired sequence-level uncertainty."""
import numpy as np

from spin8_quantizer import fit, pack, unpack


def rotate(x,r):
    if x.shape[-1]%len(r):raise ValueError("The basis must divide the actual width")
    return (x.reshape(-1,len(r))@r.T).reshape(x.shape)


def block_covariance(visits,r,weights=None,chunk=128):
    if not visits or any(len(x)==0 for x in visits):raise ValueError("Each included visit needs observed inputs")
    weights=np.ones(len(visits)) if weights is None else np.asarray(weights,np.float64)
    if len(weights)!=len(visits) or (weights<0).any() or weights.sum()<=0:raise ValueError("Invalid visit mixture")
    groups=visits[0].shape[1]//128
    gram=np.zeros((groups,128,128),np.float64)
    for mass,x in zip(weights/weights.sum(),visits):
        for off in range(0,len(x),chunk):
            a=rotate(x[off:off+chunk].astype(np.float64),r).reshape(-1,groups,128).transpose(1,0,2)
            gram+=(a.transpose(0,2,1)@a)*(mass/len(x))
    return gram


def covariance_distortion(w,t,scale,c):
    err=w-t*scale[:,None]
    return np.einsum("ri,ij,rj->r",err,c,err,optimize=True)


def calibration_covariance(visits, basis, prior=128):
    """Shrink a low-rank non-centred estimate towards its group-average second moment."""
    gram=block_covariance(visits,basis)
    effective_count=len(visits)**2/sum(1/len(x) for x in visits)
    mass=effective_count/(effective_count+prior)
    target=gram.diagonal(axis1=1,axis2=2).mean(axis=1)
    gram*=mass
    k=np.arange(128)
    gram[:,k,k]+=(1-mass)*target[:,None]
    return gram.astype(np.float32)


def fit_covariance(rotated,gram,sweeps=1):
    """Exactly re-score stored binary16 scales and accept only monotone coordinate updates."""
    w=np.asarray(rotated,np.float64)
    if w.ndim!=2 or w.shape[1]%128 or gram.shape!=(w.shape[1]//128,128,128):
        raise ValueError("The block covariance does not match the weight rows")
    if not np.isfinite(gram).all() or not np.allclose(gram,gram.transpose(0,2,1),atol=1e-10):
        raise ValueError("Non-finite or asymmetric covariance")
    groups=w.reshape(len(w),-1,128)
    initial=fit(w,np.maximum(gram.diagonal(axis1=1,axis2=2).ravel(),0))
    ts,sc=unpack(initial)
    ts=ts.reshape(groups.shape).copy()
    sc=sc.reshape(len(w),-1).copy()
    for g,c in enumerate(gram):
        v=groups[:,g,:]
        t=ts[:,g,:].astype(np.float64)
        a=sc[:,g].astype(np.float64)
        for _ in range(sweeps):
            prior_t,prior_a=t.copy(),a.copy()
            before=covariance_distortion(v,t,a,c)
            residual=(v-t*a[:,None])@c
            for j in range(128):
                if c[j,j]<=0:continue
                # Taking the nearest ternary value gives the exact coordinate minimiser at fixed alpha.
                target=t[:,j]+np.divide(residual[:,j],a*c[j,j],out=np.zeros(len(a)),where=a>0)
                new=np.where(target>.5,1.,np.where(target<-.5,-1.,0.))
                delta=(new-t[:,j])*a
                residual-=delta[:,None]*c[j]
                t[:,j]=new
            tc=t@c
            den=np.sum(tc*t,axis=1)
            alpha=np.divide(np.sum(tc*v,axis=1),den,out=np.zeros(len(a)),where=den>0)
            a=np.clip(alpha,0,np.finfo(np.float16).max).astype(np.float16).astype(np.float64)
            worse=covariance_distortion(v,t,a,c)>before
            t[worse],a[worse]=prior_t[worse],prior_a[worse]
        t[a==0]=0
        ts[:,g,:],sc[:,g]=t, a
    return pack(ts.reshape(-1,128),sc.ravel())


def paired_interval(reference,candidate,seed=37,draws=4000):
    """The independent unit is supplied by the caller, normally a whole sequence or physical expert."""
    delta=np.asarray(reference,np.float64)-np.asarray(candidate,np.float64)
    if delta.ndim!=1 or not len(delta) or not np.isfinite(delta).all():raise ValueError("Invalid paired observations")
    out=dict(n=len(delta),mean=float(delta.mean()),median=float(np.median(delta)),
             improved=int(np.count_nonzero(delta>0)),worsened=int(np.count_nonzero(delta<0)),ties=int(np.count_nonzero(delta==0)))
    out["percentile_95"]=None if len(delta)<2 else np.quantile(np.mean(
        np.random.default_rng(seed).choice(delta,(draws,len(delta)),replace=True),axis=1),[.025,.975]).tolist()
    return out
