"""Cross-check all recurrent runtime scale values and original NVFP4 bytes on fixed rows."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

import numpy as np

from agentic_external import MODEL
from agentic_quality import lease
from agentic_sensitivity import bank_rows
from benchmark_generation import digest, save
from gguf_stream import directory
from official_weights import Original
from sm120_native import run


def pack_nv(parts):
    """Lossless swap of adjacent source nibbles into the split-half GGML layout."""
    w,scale,amax,denominator=parts
    if amax is None or np.any(scale&128) or np.any(scale==127):
        raise ValueError("Expected finite, unsigned source NVFP4 scales")
    w=w.reshape(len(w),-1,8)
    codes=np.stack((w&15,w>>4),axis=-1).reshape(len(w),-1,16)
    packed=(codes[:,:,:8] | (codes[:,:,8:]<<4)).reshape(len(w),-1,32)
    return np.concatenate((scale.reshape(len(w),-1,4),packed),axis=-1).reshape(len(w),-1)


def check(a):
    sys.path.insert(0,str(a.llama/"gguf-py"))
    import gguf
    dest=a.root/"evaluation/phase13"
    model=dest/"external"/MODEL
    orig=Original(a.root/"official")
    _,ts=directory(model,gguf.GGML_QUANT_SIZES)
    ts={t.name:t for t in ts}
    expected=np.ones((24,2,128),dtype="<f4")
    sampled=[]
    with model.open("rb") as f:
        for layer in range(24):
            for j,part in enumerate(("gate_up","down")):
                base=f"blk.{layer}.ffn_{part}_exps."
                t=ts[base+"weight"]
                if base+"scale" in ts:
                    s=ts[base+"scale"]
                    if s.tensor_type!=0 or s.shape!=(128,):raise ValueError("Scale dimensions differ")
                    f.seek(s.data_offset);expected[layer,j]=np.fromfile(f,dtype="<f4",count=128)
                if t.tensor_type!=40:continue
                src=f"model.llm.layers.{layer}.mlp.experts.{('w13','w2')[j]}_weight"
                # All per-expert scale factors, and both logical projections of a fused bank.
                outer=orig.read(src+"_amax")/orig.read(src+"_outer_scale_denominator")[0]
                if not np.array_equal(outer,expected[layer,j]):raise ValueError("Original NVFP4 outer scale mismatch: "+base)
                positions=sorted({0,t.shape[1]//2-1,t.shape[1]//2,t.shape[1]-1})
                for e in (0,63,127):
                    rows=[2*(k%(t.shape[1]//2))+k//(t.shape[1]//2) for k in positions] if j==0 else positions
                    actual=bank_rows(f,t,e,positions)
                    ref=np.concatenate([pack_nv(orig.parts(src,e,k,1)) for k in rows])
                    if not np.array_equal(actual,ref):raise ValueError(f"Original NVFP4 bits differ: {base}, expert {e}")
                sampled.append(dict(physical=layer,projection=part,experts=[0,63,127],
                                    rows=positions,outer_scales_checked=128,matching_bytes=len(positions)*3*t.n_bytes//(128*t.shape[1])))
    result=dict(source_model=MODEL,nvfp4_banks=len(sampled),source_rows=sampled,runtimes={})
    save(dest/"source-nvfp4-inspection.json",result)
    for name,exe in (("prism-derived",a.prism),("strata-native",a.native)):
        folder=dest/("scales-"+name)
        output=folder/"scale-values.bin"
        if not output.exists():
            work=folder/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
            with lease().acquire(poll_interval=.017):
                run(work,[str(exe),str(model),str(work/"scale-values.bin")],2500,5400,3600)
            (work/"scale-values.bin").rename(output)
        dtype=np.dtype([("visit","<i4"),("layer","<i4"),("projection","<i4"),("scale","<f4",(128,))])
        records=np.fromfile(output,dtype=dtype)
        observed=[];keys=set()
        if records.size!=96:raise ValueError("Wrong number of visited projections")
        schedule=[*range(6),*range(6,18),*range(6,18),*range(6,18),*range(18,24)]
        for rec in records:
            v,l,p=(int(rec[k]) for k in ("visit","layer","projection"))
            if not 0<=v<48 or p not in (0,1) or schedule[v]!=l or (v,p) in keys:
                raise ValueError("Unexpected physical visit")
            keys.add((v,p))
            if not np.array_equal(expected[l,p],rec["scale"]):
                raise ValueError(f"{name}: wrong scale values at visit {v}, layer {l}, projection {p}")
            observed.append(dict(visit=v,physical=l,projection=("gate_up","down")[p],matching_scales=128))
        result["runtimes"][name]=dict(executable=digest(exe),visits=48,exact_scale_comparisons=96*128,results=observed)
        save(dest/"runtime-scale-verification.json",result)
        print(name,48,96*128,flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("root","llama","prism","native"):p.add_argument("--"+k,type=Path,required=True)
    check(p.parse_args())
