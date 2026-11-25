"""Check the actual CUDA encoder against monotone CPU descent on an observed calibration visit."""
import argparse
import json
from pathlib import Path

import numpy as np
import torch

from activation_optimisation import block_covariance, calibration_covariance, fit_covariance
from official_weights import Original, reconstruct
from phase3_study import Traces
from spin8_cuda import Kernels
from spin8_quantizer import Basis, basis_matrix, decode


def compare(source, capture, library, layer, rows):
    ref=Original(source)
    traces=Traces([capture],layer)
    expert=int(np.argmax(traces.counts.sum(axis=0)))
    key=f"model.llm.layers.{layer}.mlp.experts.w2_weight"
    weight=reconstruct(ref.parts(key,expert,0,rows))
    rec=traces.expert(expert,"w2")
    visits=[x for _,_,x in rec]
    basis=Basis("V");r=basis_matrix(basis)
    c=calibration_covariance(visits,r)
    gpu=Kernels(library)
    tensor=torch.from_numpy(weight).cuda()
    initial,rot=gpu.encode(tensor,basis,c.diagonal(axis1=1,axis2=2).flatten().copy())
    candidate,_=gpu.encode(tensor,basis,covariance=c)
    rot=rot.cpu().numpy()
    baseline=initial.cpu().numpy();actual=candidate.cpu().numpy()
    cpu=fit_covariance(rot,c.astype(np.float64))
    def loss(payload):
        err=(rot-decode(payload,weight.shape)).astype(np.float64).reshape(rows,-1,128)
        return np.einsum("rgi,gij,rgj->rg",err,c,err,optimize=True)
    one,two,three=map(loss,(baseline,actual,cpu))
    if np.any(two>one+1e-10) or not np.allclose(two,three,rtol=1e-5,atol=1e-10):
        raise ArithmeticError("Non-monotone CUDA covariance fitting or disagreement with CPU")
    tr={}
    for _,v,x in rec:
        gram=block_covariance([x],r)
        tr[str(v)]=dict(tokens=len(x),mean_second_moment=float(gram.diagonal(axis1=1,axis2=2).mean()))
    traces.close()
    return dict(gpu=torch.cuda.get_device_name(),layer=layer,expert=expert,projection="down",rows=rows,
                capture=capture.name,visits=tr,physical_groups=int(one.size),diagonal_mean=float(one.mean()),
                correlated_mean=float(two.mean()),cpu_mean=float(three.mean()),worsened_groups=int((two>one+1e-10).sum()),
                mismatching_bytes=int((actual!=cpu).sum()),max_abs_cpu_gpu_difference=float(np.max(abs(two-three))))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("source","capture","library","output"):p.add_argument("--"+key,type=Path,required=True)
    p.add_argument("--layer",type=int,default=6);p.add_argument("--rows",type=int,default=32)
    a=p.parse_args();a.output.write_text(json.dumps(compare(a.source,a.capture,a.library,a.layer,a.rows),indent=2))
