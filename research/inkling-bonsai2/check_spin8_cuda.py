"""Measure transform arithmetic, bit-exact ternary fitting and kernel-only latency on a local GPU."""
import argparse
import json
from pathlib import Path
import numpy as np
import torch

from official_weights import Original, reconstruct
from spin8_cuda import Kernels
from spin8_quantizer import Basis, fit


def main(a):
    orig=Original(a.source)
    key="model.llm.layers.6.mlp.experts.w2_weight"
    w=reconstruct(orig.parts(key,0,0,64,True))
    x=torch.from_numpy(w).cuda()
    h=np.random.default_rng(58).uniform(.1,2,w.shape[-1]).astype(np.float32)
    kernels=Kernels(a.library)
    results=[]
    for kind in ("V","P","M"):
        b=Basis(kind,theta=float(np.float32(.18)))
        ref=b.apply(w.astype(np.float64))
        reference=kernels.rotate(x,b,reference=True)
        fused=kernels.rotate(x,b)
        diffs=[float(np.max(np.abs(out.cpu().numpy()-ref))) for out in (reference,fused)]
        payload,rot=kernels.encode(x,b,h)
        physical=payload.cpu().numpy()
        expected=fit(rot.cpu().numpy(),h)
        if max(diffs)>3e-6 or not np.array_equal(physical,expected):
            raise ArithmeticError(f"CUDA discrepancy {kind}, errors {diffs}, mismatched bytes {np.sum(physical!=expected)}")
        timings={}
        for is_ref in (True,False):
            y=torch.empty_like(x)
            r=kernels.table(b,x.device)
            def launch():
                status=kernels.fn(r.data_ptr(),x.data_ptr(),y.data_ptr(),x.numel()//128,is_ref,
                                  torch.cuda.current_stream().cuda_stream)
                if status: raise RuntimeError(status)
            for _ in range(10): launch()
            start,end=torch.cuda.Event(enable_timing=True),torch.cuda.Event(enable_timing=True)
            samples=[]
            for _ in range(5):
                start.record()
                for _ in range(50): launch()
                end.record()
                end.synchronize()
                samples.append(start.elapsed_time(end)*1000/50)
            timings["reference_us" if is_ref else "fused_us"]=samples
        results.append(dict(representation=kind,shape=list(x.shape),maximum_error_fp64=diffs,
                            byte_mismatches=int(np.sum(physical!=expected)),kernel_timings=timings))
    a.output.write_text(json.dumps(dict(gpu=torch.cuda.get_device_name(),sm=torch.cuda.get_device_capability(),
         input_tensor=key,expert=0,calibration="deterministic diagnostic feature weights",results=results),indent=2))
    print([(v["representation"],v["maximum_error_fp64"],v["byte_mismatches"]) for v in results])


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for s in ["source","output","library"]:p.add_argument("--"+s,type=Path,required=True)
    main(p.parse_args())
