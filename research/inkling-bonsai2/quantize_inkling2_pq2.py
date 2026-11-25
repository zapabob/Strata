"""Write canonical Inkling GGUF tensors from indexed safetensors, one physical expert at a time."""

import argparse
import ctypes as ct
import hashlib
import json
import math
import os
import sqlite3
import sys
from pathlib import Path

import numpy as np
import torch

from official_weights import Original, reconstruct
from source import REPO, atomic_bytes, await_capacity
from spin8_cuda import Kernels
from spin8_quantizer import Basis, decode, unpack


LABELS = {"quality":"Quality", "balanced":"Balanced", "aggressive":"Aggressive"}
TORCH = {"F32":torch.float32,"BF16":torch.bfloat16,"F16":torch.float16}
NUMPY = {"F32":"<f4","BF16":"<u2","F16":"<f2"}


class Checkpoint:
    def __init__(self, source):
        self.path=source
        meta=json.loads((source/"source.json").read_bytes())
        self.revision, self.repo=meta["revision"],meta["repository"]
        self.original=None if self.repo==REPO else Original(source)
        self.fast_original=None
        head=json.loads((source/"headers.json").read_bytes())
        name,h=next((k,v) for k,v in head.items() if k.startswith("model-"))
        self.file=source/name
        self.base,self.header=h["base"],h["tensors"]

    def size(self,key):
        shape=list(self.header[key]["shape"])
        if self.original and key in self.original.schemes and self.original.schemes[key]["weight_transform"]=="nvfp4_nearest":
            shape[-1]*=2
        return shape

    def raw(self,key,expert=None):
        if expert is not None and self.original:
            parts=self.original.parts(key,expert)
            if self.fast_original is not None:return self.fast_original.original(parts,torch.float32)
            return torch.from_numpy(reconstruct(parts))
        d=self.header[key]
        # Copy-on-write mmap avoids a copy of the complete embedding or routed bank.
        a=np.memmap(self.file, dtype=NUMPY[d["dtype"]], mode="c",offset=self.base+d["data_offsets"][0],shape=tuple(d["shape"]))
        a=a if expert is None else a[expert]
        return torch.from_numpy(a).view(TORCH[d["dtype"]])


def upstream(root):
    sys.path[:0]=[str(root),str(root/"gguf-py")]
    import gguf
    from conversion.inkling2 import Inkling2LoopModel
    class HeaderModel(Inkling2LoopModel):
        model_arch=Inkling2LoopModel.model_arch
        def index_tensors(self,remote_hf_model_id=None):
            return {}
    return gguf,HeaderModel


def mapped(model,cp,meta=True):
    for raw,d in cp.header.items():
        if raw.endswith(("_weight_scale","_weight_amax","_weight_outer_scale_denominator")):
            continue
        filtered=model.filter_tensors((raw,None))
        if filtered is None: continue
        key=filtered[0]
        lid=next((int(i) for i in key.split(".") if i.isdecimal()),None)
        expert=key.endswith((".w13_weight",".w2_weight"))
        if expert:
            shape=cp.size(raw)
            target=key.replace(".w13_weight",".gate_up_proj").replace(".w2_weight",".down_proj")
            yield raw,model.map_tensor_name(target,try_suffixes=())+".weight",shape,None,lid
            continue
        t=torch.empty(d["shape"],device="meta",dtype=TORCH[d["dtype"]]) if meta else cp.raw(raw)
        for name,value in model.modify_tensors(t,key,lid):
            yield raw,name,list(value.shape),value,lid


def precision(g,m,name,key,shape,layer,profile,storage):
    q=g.GGMLQuantizationType
    if key.endswith((".w13_weight",".w2_weight")):return q.PQ2_0
    if len(shape)<=1 or "_norm." in name or name.endswith("norm.weight"):return q.F32
    forced=m.tensor_force_quant(key,name,layer,len(shape))
    if isinstance(forced,q) and forced==q.F32:return q.F32
    if any(s in name for s in ("ffn_gate_inp","loop_","_ctrl_","_conv","_sconv","sink","_bias","_res_query","_clip")):
        return q.F32 if storage=="F32" else q.BF16
    if name=="token_embd.weight":return q.Q4_K if profile=="aggressive" else q.Q6_K
    if name=="output.weight":return q.Q8_0 if profile=="quality" else q.Q6_K
    if profile=="aggressive" and shape[-1]%128==0 and any(name.endswith("."+a+".weight") for a in
                                                            ("attn_q","attn_k","attn_v","attn_output")):return q.PQ2_0
    if len(shape)==2 and shape[-1]%32==0:
        return q.Q8_0 if profile=="quality" or shape[-1]%256 else q.Q4_K
    return q.F32 if storage=="F32" else q.BF16


class NativeMixed:
    def __init__(self, library):
        self.folder=os.add_dll_directory(str(library.parent)) if os.name=="nt" else None
        self.lib=ct.CDLL(str(library))
        self.pack=self.lib.ggml_quantize_chunk
        self.pack.argtypes=[ct.c_int,ct.c_void_p,ct.c_void_p,ct.c_int64,ct.c_int64,ct.c_int64,ct.c_void_p]
        self.pack.restype=ct.c_size_t

    def encode(self, w, typ, length):
        x=np.ascontiguousarray(w.float().numpy())
        if typ.name in ("F32","BF16","F16"):
            rounded=w.to({"F32":torch.float32,"BF16":torch.bfloat16,"F16":torch.float16}[typ.name]).contiguous()
            data=rounded.view(torch.uint8).numpy().tobytes()
            return data,float(np.sum((x-rounded.float().numpy()).astype(np.float64)**2))
        rows=math.prod(w.shape[:-1])
        out=np.empty(length,np.uint8)
        n=self.pack(int(typ),x.ctypes.data,out.ctypes.data,0,rows,w.shape[-1],None)
        if n!=length:raise ArithmeticError("Unexpected native packed extent")
        deq=getattr(self.lib,{"Q4_K":"dequantize_row_q4_K","Q6_K":"dequantize_row_q6_K","Q8_0":"dequantize_row_q8_0"}[typ.name])
        deq.argtypes=[ct.c_void_p,ct.c_void_p,ct.c_int64]
        deq.restype=None
        recon=np.empty_like(x)
        deq(out.ctypes.data,recon.ctypes.data,x.size)
        return out.tobytes(),float(np.sum((x-recon).astype(np.float64)**2))


def prepare(args,cp,g,klass):
    model=klass(cp.path,g.LlamaFileType.MOSTLY_PQ2_0,args.output,model_name="Inkling 2 Mini "+args.profile)
    entries=[]
    for raw,name,shape,_,layer in mapped(model,cp):
        typ=precision(g,model,name,raw,shape,layer,args.profile,cp.header[raw]["dtype"])
        group,nbytes=g.GGML_QUANT_SIZES[typ]
        if shape[-1]%group:raise ValueError(f"Unrepresentable row width {name} {shape} {typ}")
        entries.append(dict(raw=raw,name=name,shape=shape,type=typ.name,bytes=math.prod(shape)//group*nbytes))
    if len({x["name"] for x in entries})!=len(entries):raise ValueError("Duplicate canonical tensor")
    banks=[d for d in entries if d["raw"].endswith((".w13_weight",".w2_weight"))]
    if len(banks)!=48 or any(x["shape"][0]!=128 for x in banks):raise ValueError("Incomplete physical expert coverage")
    return model,entries,banks


def add_contract(w,g,args,cp,entries,banks):
    w.add_string("inkling_quant.source",cp.repo)
    w.add_string("inkling_quant.revision",cp.revision)
    w.add_string("inkling_quant.profile",args.profile)
    names=[d["name"] for d in entries if d["type"]=="PQ2_0"]
    if args.profile not in ("spin8","recurrent"):
        w.add_uint32("prism.hadamard.version",1)
        w.add_uint32("prism.hadamard.block_size",128)
        w.add_string("prism.hadamard.transform","normalized-sylvester-walsh-hadamard")
        w.add_string("prism.hadamard.axis","input-last-dimension")
        w.add_string("prism.hadamard.sign_mode","identity")
        w.add_array("prism.hadamard.weight_names",names)
        return None
    policy=json.loads(args.policy.read_bytes())
    if (policy["source_revision"]!=cp.revision or policy["selection_split"]!="calibration" or
        set(policy["bank_indices"])!={d["name"] for d in banks}):
        raise ValueError("A source-matched, calibration-locked policy is required")
    bases=policy["bases"]
    ids=[i for n in names for i in policy["bank_indices"][n]]
    if len(ids)!=len(names)*128 or min(ids)<0 or max(ids)>=len(bases):raise ValueError("Invalid expert basis ids")
    w.add_string("general.architecture","inkling2-loop-spin8")
    continuous=any(x.get("parameters") for x in bases)
    w.add_uint32("spin8.version",2 if continuous else 1)
    w.add_string("spin8.transform_kind","sylvester-kron-spin8-lie28-v2" if continuous else "sylvester-kron-spin8-hh-v1")
    w.add_uint32("spin8.block_size",128)
    w.add_array("spin8.tensor_names",names)
    w.add_array("spin8.representation",[x["kind"] for x in bases])
    angles=([v for b in bases for v in (b.get("parameters") or [0.]*28)] if continuous else [float(x["theta"]) for x in bases])
    if continuous and any(x.get("theta",0.) for x in bases):raise ValueError("Mixed Lie chart conventions")
    w.add_key_value("spin8.rotation_parameters",angles,g.GGUFValueType.ARRAY,g.GGUFValueType.FLOAT32)
    w.add_key_value("spin8.basis_id",ids,g.GGUFValueType.ARRAY,g.GGUFValueType.UINT32)
    return policy


def make_header(args,model,g,cp,entries,banks):
    w=model.gguf_writer
    for d in entries:
        w.add_tensor_info(d["name"],d["shape"],np.dtype("float32"),d["bytes"],raw_dtype=g.GGMLQuantizationType[d["type"]])
    model.prepare_metadata(vocab_only=False)
    policy=add_contract(w,g,args,cp,entries,banks)
    w.write_header_to_file(args.header)
    w.write_kv_data_to_file()
    w.write_ti_data_to_file()
    w.close()
    align=lambda n:(n+31)//32*32
    pos=align(args.header.stat().st_size)
    for d in entries:
        d["offset"]=pos
        pos+=align(d["bytes"])
    return pos,policy


def quant_part(d,w,basis,importance,g,native,gpu,covariance=None):
    if d["type"]=="PQ2_0":
        x=w.to("cuda",dtype=torch.float32)
        out,rot=gpu.encode(x,basis,importance,covariance)
        if hasattr(gpu.lib,"spin8_pq2_statistics"):
            error,counts=gpu.statistics(rot,out)
            return out.cpu().numpy().tobytes(),error,counts
        cpu=out.cpu().numpy()
        counts=np.bincount(unpack(cpu)[0].ravel().astype(np.int16)+1,minlength=4)
        reconstructed=decode(cpu,w.shape)
        return cpu.tobytes(),float(np.sum((rot.cpu().numpy()-reconstructed).astype(np.float64)**2)),counts.tolist()
    typ=g.GGMLQuantizationType[d["type"]]
    group,nbytes=g.GGML_QUANT_SIZES[typ]
    data,err=native.encode(w,typ,w.numel()//group*nbytes)
    return data,err,[0]*4


class ReusableBaseline:
    """Reuse verified, byte-identical physical groups from a conventional same-source conversion."""
    def __init__(self,path,cp,g):
        from gguf_stream import directory
        manifest=json.loads(path.with_suffix(".manifest.json").read_bytes())
        if (not manifest["integrity"]["digests_verified"] or manifest["activation_weighted"]
                or manifest["repository"]!=cp.repo or manifest["revision"]!=cp.revision):
            raise ValueError("Reused tensors require a verified same-source conventional baseline")
        fields,tensors=directory(path,g.GGML_QUANT_SIZES)
        if fields["general.architecture"]!="inkling2_loop" or "prism.hadamard.version" not in fields:
            raise ValueError("Incompatible baseline transform contract")
        self.tensors={t.name:t for t in tensors}
        self.db=sqlite3.connect(path.with_suffix(".sqlite").resolve().as_uri()+"?mode=ro",uri=True)
        self.stream=path.open("rb")

    def part(self,d,g,part,offset):
        src=self.tensors.get(d["name"])
        if not src or int(src.tensor_type)!=int(g.GGMLQuantizationType[d["type"]]) or tuple(reversed(src.shape))!=tuple(d["shape"]):
            return None
        meta=self.db.execute("select n,err,counts,hash from done where name=? and part=?",(d["name"],part)).fetchone()
        if not meta:return None
        n,err,counts,digest=meta
        self.stream.seek(src.data_offset+offset)
        data=self.stream.read(n)
        if len(data)!=n or hashlib.sha256(data).hexdigest()!=digest:raise IOError("Reused baseline chunk failed validation")
        return data,err,json.loads(counts)


def convert(args):
    cp=Checkpoint(args.source)
    g,klass=upstream(args.llama)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.header=args.output.with_suffix(".gguf.header")
    model,entries,banks=prepare(args,cp,g,klass)
    total,policy=make_header(args,model,g,cp,entries,banks)
    print(f"{len(entries)} canonical text tensors, {len(banks)} physical expert banks, {total:,} bytes",flush=True)
    if args.layout_only:return
    if not cp.file.is_file() or not Path(str(cp.file)+".verified.json").is_file():raise ValueError("The source is not yet verified")
    partial=Path(str(args.output)+".partial")
    if args.output.exists():raise FileExistsError(args.output)
    signature=hashlib.sha256(args.header.read_bytes()).hexdigest()
    ledger=args.output.with_suffix(".sqlite")
    db=sqlite3.connect(ledger)
    db.execute("create table if not exists identity(h text primary key)")
    db.execute("create table if not exists done(name text,part integer,n integer,err real,counts text,hash text,primary key(name,part))")
    identities=db.execute("select h from identity").fetchall()
    recorded=db.execute("select count(*) from done").fetchone()[0]
    if identities and identities!=[(signature,)]:
        raise ValueError("The conversion journal belongs to a different header")
    if recorded or (partial.exists() and partial.stat().st_size):
        if not partial.is_file() or partial.stat().st_size>total or not identities:
            raise ValueError("The partial output does not match its recorded work")
        with partial.open("rb") as f:
            if f.read(args.header.stat().st_size)!=args.header.read_bytes():
                raise ValueError("The partial output header differs from its journal")
        for entry in entries:
            complete=db.execute("select coalesce(sum(n),0) from done where name=?",(entry["name"],)).fetchone()[0]
            if complete and entry["offset"]+complete>partial.stat().st_size:
                raise ValueError("Truncated journalled tensor "+entry["name"])
    else:
        await_capacity(args.output.parent,total)
        db.execute("insert or ignore into identity values(?)",(signature,))
        db.commit()
        with partial.open("r+b" if partial.exists() else "x+b") as f:
            f.write(args.header.read_bytes())
            f.write(bytes((-f.tell())%32))
            f.flush()
            os.fsync(f.fileno())
    native=NativeMixed(args.ggml_base.resolve(strict=True))
    gpu=Kernels(args.kernels)
    if cp.original:
        cp.original.cache_limit=int(float(os.environ.get("INKLING_SOURCE_CACHE_GIB","1.25"))*2**30)
        if hasattr(gpu.lib,"spin8_reconstruct_original"):cp.fast_original=gpu
    reuse=ReusableBaseline(args.reuse,cp,g) if args.reuse else None
    index={x["name"]:x for x in entries}
    model._queries.clear()
    with partial.open("r+b") as f:
        def emit(d,part,load,b,importance,offset,eligible=True,covariance=None):
            if db.execute("select 1 from done where name=? and part=?",(d["name"],part)).fetchone():return
            await_capacity(args.output.parent,0)
            previous=reuse.part(d,g,part,offset) if reuse and eligible else None
            data,err,counts=previous if previous else quant_part(d,load(),b,importance,g,native,gpu,covariance)
            await_capacity(args.output.parent,len(data))
            position=d["offset"]+offset
            end=f.seek(0,os.SEEK_END)
            if position>end:
                if position-end>=32:raise IOError("Unexpected gap before "+d["name"])
                f.write(bytes(position-end))
            else:f.seek(position)
            f.write(data);f.flush();os.fsync(f.fileno())
            db.execute("insert into done values(?,?,?,?,?,?)",(d["name"],part,len(data),err,json.dumps(counts),hashlib.sha256(data).hexdigest()))
            db.commit()
        for raw,name,shape,value,layer in mapped(model,cp,meta=False):
            d=index[name]
            if db.execute("select coalesce(sum(n),0) from done where name=?",(name,)).fetchone()[0]==d["bytes"]:continue
            if value is None:
                for e in range(shape[0]):
                    if db.execute("select 1 from done where name=? and part=?",(name,e)).fetchone():continue
                    b=Basis("hadamard")
                    if policy:
                        choice=policy["bases"][policy["bank_indices"][name][e]]
                        b=Basis(choice["kind"],theta=float(np.float32(choice.get("theta",0.))),
                                parameters=tuple(float(np.float32(t)) for t in choice.get("parameters",[])))
                    h=c=None
                    mode=policy["codec_modes"][name][e] if policy and "codec_modes" in policy else "diagonal" if args.moments else "weight-only"
                    if mode!="weight-only":
                        if not args.moments:raise ValueError("Missing calibration statistics for selected codec")
                        with np.load(args.moments/f"layer-{layer:02d}.npz") as moments:
                            key=f"{'w13' if '.w13_' in raw else 'w2'}.{e}"
                            if mode=="block":c=moments["cov."+key]
                            elif mode=="diagonal":h=moments[key]
                            else:raise ValueError("Unknown calibrated codec "+mode)
                    def load():
                        weight=cp.raw(raw,e)
                        return torch.cat((weight[::2],weight[1::2]),dim=0) if ".w13_" in raw else weight
                    equivalent=(b.kind=="hadamard" or (b.kind=="V" and b.theta==0 and not any(b.parameters)))
                    emit(d,e,load,b,h,e*d["bytes"]//shape[0],equivalent and mode=="weight-only",c)
            else:
                group,nbytes=g.GGML_QUANT_SIZES[g.GGMLQuantizationType[d["type"]]]
                stride=math.prod(shape[1:])
                rows=max(1,8*1024**2//max(1,stride*4)) if len(shape)>1 else shape[0]
                for start in range(0,shape[0],rows):
                    emit(d,start,lambda:value[start:start+rows].contiguous(),Basis("hadamard"),None,start*stride*nbytes//group)
            print(name,flush=True)
        end=f.seek(0,os.SEEK_END)
        if not 0<=total-end<32:raise IOError("Invalid final GGUF extent")
        f.write(bytes(total-end));f.flush();os.fsync(f.fileno())
    for d in entries:
        records=db.execute("select n,err,counts from done where name=?",(d["name"],)).fetchall()
        if sum(v[0] for v in records)!=d["bytes"]:raise IOError("Incomplete "+d["name"])
        d.update(mse=sum(v[1] for v in records)/math.prod(d["shape"]),bpw=d["bytes"]*8/math.prod(d["shape"]),
                 code_counts=np.sum([json.loads(v[2]) for v in records],axis=0).tolist())
    from verify_pq2 import verify
    audit=verify(partial,args.llama,ledger)
    partial.rename(args.output)
    report=dict(repository=cp.repo,revision=cp.revision,profile=args.profile,bytes=total,integrity=audit,tensors=entries,
                activation_weighted=bool(args.moments),basis_selection="locked on calibration" if policy else "fixed Hadamard")
    atomic_bytes(args.output.with_suffix(".manifest.json"),json.dumps(report,indent=2).encode())


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ["source","llama","output","ggml-base","kernels","policy","moments","reuse"]:p.add_argument("--"+flag,type=Path,required=flag in ("source","llama","output"))
    p.add_argument("--profile",required=True,choices=[*LABELS,"spin8","recurrent"])
    p.add_argument("--layout-only",action="store_true")
    with torch.inference_mode():convert(p.parse_args())
