"""Evaluate physical expert banks in source coordinates using routed activation samples."""
import argparse
import ctypes as ct
import os
from pathlib import Path
import sys
import time

import numpy as np

from agentic_external import MODEL
from benchmark_generation import digest, read, save
from gguf_stream import directory
from official_weights import Original, reconstruct
from phase3_study import Traces
from spin8_quantizer import decode


class Codec:
    def __init__(self, library, gguf):
        self.dll_dir=os.add_dll_directory(str(library.parent)) if os.name=="nt" else None
        self.lib=ct.CDLL(str(library))
        self.pack=self.lib.ggml_quantize_chunk
        self.pack.argtypes=[ct.c_int,ct.c_void_p,ct.c_void_p,ct.c_int64,ct.c_int64,ct.c_int64,ct.c_void_p]
        self.pack.restype=ct.c_size_t
        self.gguf=gguf

    def encode(self, x, kind, importance):
        typ=self.gguf.GGMLQuantizationType[kind]
        width,nbytes=self.gguf.GGML_QUANT_SIZES[typ]
        x=np.ascontiguousarray(x,dtype=np.float32)
        importance=np.ascontiguousarray(importance,dtype=np.float32)
        if importance.shape!=(x.shape[1],) or not np.all(np.isfinite(importance)) or np.any(importance<0):
            raise ValueError("Invalid importance matrix")
        packed=np.empty((len(x),x.shape[1]//width*nbytes),dtype=np.uint8)
        written=self.pack(int(typ),x.ctypes.data,packed.ctypes.data,0,len(x),x.shape[1],importance.ctypes.data)
        if written!=packed.size:raise ArithmeticError("Unexpected GGML extent")
        return packed

    def unpack(self, raw, kind, width):
        if kind=="PQ2_0":
            from scipy.linalg import hadamard
            x=decode(raw.reshape(-1,34),(len(raw),width)).reshape(-1,128)
            return ((x@hadamard(128,dtype=np.float32))/np.sqrt(np.float32(128))).reshape(len(raw),width)
        fun=getattr(self.lib,"dequantize_row_"+kind.lower())
        fun.argtypes=[ct.c_void_p,ct.c_void_p,ct.c_int64];fun.restype=None
        x=np.empty((len(raw),width),np.float32)
        raw=np.ascontiguousarray(raw)
        fun(raw.ctypes.data,x.ctypes.data,x.size)
        return x


def bank_rows(handle, tensor, expert, rows):
    width,height,experts=tensor.shape
    if not 0<=expert<experts or any(i<0 or i>=height for i in rows):
        raise ValueError("Invalid bank coordinates")
    stride=tensor.n_bytes//(height*experts)
    chunks=[]
    for row in rows:
        handle.seek(tensor.data_offset+(expert*height+int(row))*stride)
        data=handle.read(stride)
        if len(data)!=stride:raise EOFError(tensor.name)
        chunks.append(np.frombuffer(data,np.uint8))
    return np.stack(chunks)


def outer_scale(handle, tensors, name, expert):
    scale=tensors.get(name.removesuffix("weight")+"scale")
    if scale is None:return 1.
    if scale.tensor_type!=0 or scale.shape!=(128,):raise ValueError("Unexpected expert scale type")
    handle.seek(scale.data_offset+4*expert)
    return float(np.frombuffer(handle.read(4),"<f4")[0])


def scores(w, candidate, visits):
    result=[]
    for doc,visit,x in visits:
        ref=x@w.T
        err=x@(candidate-w).T
        result.append(dict(document=doc,visit=visit,rows=len(w),tokens=len(x),
                           squared_error=float(np.square(err,dtype=np.float64).sum()),
                           squared_output=float(np.square(ref,dtype=np.float64).sum())))
    return result


def readout(observations):
    docs={}
    for v in observations:
        a=docs.setdefault(v["document"],[0.,0.])
        a[0]+=v["squared_error"];a[1]+=v["squared_output"]
    return float(np.mean([a/max(b,1e-30) for a,b in docs.values()])) if docs else None


def evaluate(a):
    sys.path.insert(0,str(a.llama/"gguf-py"))
    import gguf
    codec=Codec(a.library,gguf)
    root=a.root;dest=root/"evaluation/phase13";source=Original(root/"official")
    external=dest/"external"/MODEL
    balanced=root/"official-models/Inkling-2-Mini-PQ2_0-Balanced.gguf"
    meta,ext_entries=directory(external,gguf.GGML_QUANT_SIZES)
    _,pq_entries=directory(balanced,gguf.GGML_QUANT_SIZES)
    ext={x.name:x for x in ext_entries};pq={x.name:x for x in pq_entries}
    paths={k:sorted((dest/("source-"+k)).glob("calibration-*.npz")) for k in ("calibration","validation")}
    if any(len(v)!=8 for v in paths.values()):raise ValueError("All independent agentic input traces are required")
    identity=dict(method="Source-coordinate sampled row projection; equal document weights and pooled physical visits",
                  source=source.revision,recipe=digest(dest/"protocol.json"),external=digest(dest/"external/upstream.json"),
                  rows_per_expert=a.rows,experts_per_layer=4,seed=131072)
    result_path=dest/"tensor_sensitivity.json"
    out=read(result_path) if result_path.exists() else dict(identity=identity,banks={})
    if out["identity"]!=identity:raise ValueError("Incompatible sensitivity protocol")
    with external.open("rb") as ef,balanced.open("rb") as pf:
        for layer in range(24):
            if all(f"blk.{layer}.ffn_{p}_exps.weight" in out["banks"] for p in ("gate_up","down")):continue
            cal=Traces(paths["calibration"],layer);val=Traces(paths["validation"],layer)
            try:
                counts=cal.counts.sum(0)
                ranked=sorted(np.flatnonzero(counts),key=lambda e:(-int(counts[e]),int(e)))
                experts=[int(ranked[i]) for i in np.unique(np.linspace(0,len(ranked)-1,4).astype(int))]
                for j,p in enumerate(("gate_up","down")):
                    start=time.monotonic()
                    key=f"blk.{layer}.ffn_{p}_exps.weight"
                    if key in out["banks"]:continue
                    projection=("w13","w2")[j]
                    src=f"model.llm.layers.{layer}.mlp.experts.{projection}_weight"
                    tensor=ext[key];width,height,_=tensor.shape
                    kind=gguf.GGMLQuantizationType(tensor.tensor_type).name
                    nv=source.schemes[src]["weight_transform"]=="nvfp4_nearest"
                    rng=np.random.default_rng(131072+2*layer+j)
                    rows=np.sort(rng.choice(height,size=a.rows,replace=False))
                    src_rows=2*(rows%(height//2))+rows//(height//2) if j==0 else rows
                    records=[]
                    for e in experts:
                        fit,valid=cal.expert(e,projection),val.expert(e,projection)
                        if not fit:continue
                        x=np.concatenate([z for _,_,z in fit])
                        importance=np.mean(np.square(x,dtype=np.float64),axis=0).astype(np.float32)
                        importance=np.maximum(importance,1e-8)
                        w=np.concatenate([reconstruct(source.parts(src,e,int(k),1)) for k in src_rows])
                        external_values=codec.unpack(bank_rows(ef,tensor,e,rows),kind,width)*outer_scale(ef,ext,key,e)
                        candidates={"published_"+kind:external_values,
                                    "PQ2_0_H128":codec.unpack(bank_rows(pf,pq[key],e,rows),"PQ2_0",width),
                                    "source_NVFP4" if nv else "source_MXFP8":w}
                        for alt in ("IQ2_S","IQ3_XXS","IQ4_NL"):
                            candidates[alt]=codec.unpack(codec.encode(w,alt,importance),alt,width)
                        records.append(dict(expert=e,calibration_routes=int(counts[e]),rows=rows.tolist(),
                            errors={k:dict(weight_mse=float(np.mean(np.square(q-w,dtype=np.float64))),
                                      calibration=scores(w,q,fit),validation=scores(w,q,valid)) for k,q in candidates.items()}))
                    # Validation averaging pools observed rows, routes and visits within each domain.
                    rates={}
                    for method in records[0]["errors"]:
                        obs=[v for r in records for v in r["errors"][method]["validation"]]
                        rates[method]=dict(relative_output_mse=readout(obs),documents=len({v["document"] for v in obs}))
                    out["banks"][key]=dict(source_precision="NVFP4" if nv else "MXFP8",published_type=kind,
                        dimensions=list(tensor.shape),validation=rates,experts=records,seconds=time.monotonic()-start)
                    save(result_path,out)
                    print(key,kind,rates["PQ2_0_H128"],flush=True)
            finally:cal.close();val.close()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("root","llama","library"):p.add_argument("--"+k,type=Path,required=True)
    p.add_argument("--rows",type=int,default=32)
    evaluate(p.parse_args())
