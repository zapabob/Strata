"""Evaluate four arms in one traversal of the original recurrent graph on one GPU."""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import tempfile
import time
import types

import numpy as np

from benchmark_generation import digest, read, save
from expert_attention import ARMS, protocol
from phase7_controls import immutable


ATTENTION_LINEAR={"wq_du":"q_proj.linear","wk_dv":"k_proj.linear","wv_dv":"v_proj.linear",
                  "wo_ud":"o_proj.linear","wr_du":"relative_position_bias.linear","gate_attn":"o_proj.gate_proj"}
GROUPS={"forward":("A","B","C","D"),"reverse":("R_EA","R_A","R_E","F")}


def install_attention(model,source,decoded,masks,batch):
    import torch
    from torch.nn import functional as F
    installed=set()
    for l,layer in enumerate(model.model.language_model.layers):
        for raw_name,attr in ATTENTION_LINEAR.items():
            key=f"model.llm.layers.{l}.attn.{raw_name}.weight"
            module=layer.self_attn.get_submodule(attr)
            if decoded.logical[key]!={"attention"} or tuple(decoded.entries[key]["shape"])!=tuple(module.weight.shape):
                raise ValueError("Unexpected attention parameter "+key)
            for row in (0,module.weight.shape[0]-1):
                if not torch.equal(module.weight[row:row+1],source.read(key,"cuda",row,1)):
                    raise ValueError("The Transformers conversion changed the attention coordinates at "+key)
            quant=decoded.read(key,"cuda").to(module.weight.dtype)
            def linear(self,x,q=quant):
                parts=x.split(batch,dim=0)
                if len(parts)!=len(masks) or any(p.shape[0]!=batch for p in parts):
                    raise ValueError("Ambiguous attention batch dimension")
                return torch.cat([F.linear(part,q if flag else self.weight,self.bias)
                                  for part,flag in zip(parts,masks,strict=True)])
            module.forward=types.MethodType(linear,module)
            installed.add(key)
    if installed!={key for key,c in decoded.logical.items() if c=={"attention"}}:
        raise ValueError("Omitted a quantised attention matrix")


def install_experts(model,source,decoded,masks,positions,obs):
    import torch
    from torch.nn import functional as F
    from infer import Experts
    pools=[Experts(s,.5,"cuda") for s in (source,decoded)]
    for l,layer in enumerate(model.model.language_model.layers):
        def forward(module,x,ids,mix,l=l):
            ids,mix=obs.begin(l,x,ids,mix)
            if len(x)!=positions*len(masks): raise ValueError("Unequal expert input geometry")
            out=torch.zeros_like(x,dtype=torch.float32)
            # Expert-major traversal reads each physical pair once for all simultaneous arms.
            for e in ids.unique(sorted=True).tolist():
                tokens,slots=torch.where(ids==e)
                arm=torch.div(tokens,positions,rounding_mode="floor")
                pairs={}
                for i,quant in enumerate(masks):
                    selection=arm==i
                    dest,slot=tokens[selection],slots[selection]
                    if not len(dest):continue
                    if quant not in pairs:pairs[quant]=pools[int(quant)].get(l,e)
                    w13,w2=pairs[quant]
                    gu=F.linear(x[dest],w13)
                    mid=module.act_fn(gu[...,::2],gu[...,1::2])
                    y=F.linear(mid,w2)*mix[dest,slot,None]
                    out.index_add_(0,dest,y.float())
            return out.to(x.dtype)
        layer.mlp.experts.forward=types.MethodType(forward,layer.mlp.experts)


def evaluate(a):
    import torch
    from calibrate_inkling2 import Observer,frozen_batch,split_observations
    from decoded_reference import DecodedOfficial,components
    from infer import OfficialSafetensors,load_graph
    loc,rows,path,manifest=protocol(a.root)
    labels=GROUPS[a.group]
    fields=[components(ARMS[k]) for k in labels]
    target=loc/"matched"/("frozen" if a.frozen else "dynamic")
    source=OfficialSafetensors(a.root/"official")
    quant=DecodedOfficial(a.root/"official",path,manifest,a.llama,"full")
    torch.set_float32_matmul_precision("highest")
    model=load_graph(source,"cuda",False)
    width=max(len(r["ids"]) for r in rows)
    n=len(rows)
    if a.group=="reverse":
        # These weights are fixed at their deployed precision in all four reverse arms.
        for mod,key in ((model.model.language_model.embed_tokens,"model.llm.embed.weight"),
                        (model.lm_head,"model.llm.unembed.weight")):
            d=quant.read(key,"cuda",0,len(mod.weight))
            if d.shape!=mod.weight.shape or d.dtype!=mod.weight.dtype:raise ValueError(key)
            mod.weight=torch.nn.Parameter(d,requires_grad=False)
    with torch.inference_mode(),ExitStack() as hooks:
        install_attention(model,source,quant,["attention" in v for v in fields],n)
        frozen=None
        if a.frozen:
            archives=[hooks.enter_context(np.load(loc/"matched/dynamic/A"/f"holdout-{i}.npz")) for i in range(n)]
            if any(not np.array_equal(z["input_ids"][0],r["ids"]) for z,r in zip(archives,rows,strict=True)):
                raise ValueError("Frozen inputs differ")
            frozen={k:np.tile(v,(len(labels),1)) for k,v in frozen_batch(archives,width).items()}
        obs=Observer(frozen,compact=True)
        install_experts(model,source,quant,["gate" in v for v in fields],n*width,obs)
        for i,layer in enumerate(model.model.language_model.layers):
            for mod,hook in ((layer,obs.layer_hook(i)),(layer.mlp.gate,obs.router_hook(i)),
                             (layer.self_attn,obs.output_hook(i,True)),(layer.mlp,obs.output_hook(i,False))):
                hooks.callback(mod.register_forward_hook(hook).remove)
        inputs=torch.as_tensor([r["ids"]+[0]*(width-len(r["ids"])) for r in rows],device="cuda").repeat(len(labels),1)
        print("Running original Transformers graph",labels,"on",n,"documents",flush=True)
        hidden=model.model(input_ids=inputs,attention_mask=torch.ones_like(inputs),use_cache=False).last_hidden_state
        expected={i:3 if 6<=i<18 else 1 for i in range(24)}
        if dict(obs.visits)!=expected:raise ValueError("Physical layer visit counts differ")
        for ix,label in enumerate(labels):
            out=target/label
            out.mkdir(parents=True,exist_ok=True)
            for i,r in enumerate(rows):
                item=ix*n+i
                ids=np.asarray(r["ids"],dtype=np.int64)
                d=split_observations(obs.data,item,width,len(ids))
                z=model.logit_softcap(model.lm_head(hidden[item:item+1]).float())[0,:len(ids)].cpu().numpy()
                if not np.isfinite(z).all():raise FloatingPointError("Non-finite logits")
                dst=out/f"holdout-{i}.npz"
                with dst.with_suffix(".partial").open("wb") as f: np.savez(f,input_ids=ids[None,:],logits=z,**d)
                dst.with_suffix(".partial").replace(dst)
            immutable(out/"splits.json",dict(condition=ARMS[label],protocol=digest(loc/"protocol.json"),
                batch_documents=n,paired_group=list(labels),visits=sum(expected.values()),routing="frozen" if a.frozen else "dynamic",
                expert_coordinates="Exact Walsh integer sums, FP16 scale, source BF16 weight boundary"))
            print("Committed",label,"on",sum(len(r["ids"])-1 for r in rows),"prediction positions",flush=True)


def run(a):
    from filelock import FileLock
    from sm120_native import run as guarded
    loc,_,_,_=protocol(a.root)
    dest=loc/"matched"/("frozen" if a.frozen else "dynamic")
    os.environ["INKLING_SOURCE_CUDA"]=str(a.kernels.resolve(strict=True))
    lock=FileLock(str(Path(tempfile.gettempdir())/"strata-inkling-benchmark-gpu0.lock"))
    for group in a.groups:
        if all((dest/k/"splits.json").exists() for k in GROUPS[group]): continue
        cmd=[sys.executable,"-u","-B",__file__,"measure","--root",str(a.root),"--llama",str(a.llama),"--group",group]
        if a.frozen:cmd.append("--frozen")
        for attempt in range(12):
            folder=dest/(group+"-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
            try:
                with lock.acquire(poll_interval=.004):guarded(folder,cmd,12000,3600,21600)
                break
            except RuntimeError:
                f=folder/"measurement.json"
                if attempt==11 or not f.exists() or read(f)["reason"] not in {
                       "physical_memory_pressure","device_memory_pressure","commit_pressure","disk_space_pressure"}: raise
                time.sleep(15)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=("run","measure"))
    for k in ("root","llama","kernels"):p.add_argument("--"+k,type=Path,required=k!="kernels")
    p.add_argument("--group",choices=GROUPS,default="forward")
    p.add_argument("--groups",nargs="+",choices=GROUPS,default=list(GROUPS))
    p.add_argument("--frozen",action="store_true")
    a=p.parse_args()
    if a.action=="run" and not a.kernels: p.error("Supply the verified source reconstruction library")
    (run if a.action=="run" else evaluate)(a)
