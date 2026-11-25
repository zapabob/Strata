"""Run each arm with the historical GEMM shapes, sharing weight reads between layer visits."""
import argparse
from contextlib import ExitStack
from datetime import datetime,timezone
from pathlib import Path
import sys
import time
import types

import numpy as np

from benchmark_generation import digest,read,save
from expert_attention import ARMS,protocol
from matched_factorial import ATTENTION_LINEAR,GROUPS
from phase7_controls import immutable


# The original 55-token document ran alone. The resumed run grouped lengths 17, 29 and 24.
GROUPS_OF_DOCUMENTS=((0,),(1,2,3),(4,5,6))


def evaluate(a):
    import greenlet
    import torch
    from torch.nn import functional as F
    from calibrate_inkling2 import Observer,split_observations
    from decoded_reference import DecodedOfficial,components
    from infer import Experts,OfficialSafetensors,load_graph
    loc,rows,path,manifest=protocol(a.root)
    target=loc/"serial"/("frozen" if a.frozen else "dynamic")
    labels=[k for k in a.arms if not (target/k/"splits.json").is_file()]
    if not labels:return
    parent=greenlet.getcurrent()
    current=greenlet.getcurrent
    src=OfficialSafetensors(a.root/"official")
    dec=DecodedOfficial(a.root/"official",path,manifest,a.llama,"full")
    model=load_graph(src,"cuda",False)
    pools=[Experts(s,2.05,"cuda") for s in (src,dec)]
    def selected(name):return name in current().selection

    def routed_pair(layer,e):
        gu={k for k in ("gate","up") if selected(k)}
        down=selected("down")
        if len(gu)==2 and down:return pools[1].get(layer,e)
        if not gu and not down:return pools[0].get(layer,e)
        w=pools[0].get(layer,e);q=pools[1].get(layer,e)
        if len(gu)==1:
            first=w[0].clone()
            parity=0 if "gate" in gu else 1
            first[parity::2]=q[0][parity::2]
        else:first=(q if gu else w)[0]
        return first,(q if down else w)[1]

    class Observation:
        def begin(self,*v):return current().observation.begin(*v)
        def down(self,*v):return current().observation.down(*v)
    proxy=Experts(src,0,"cuda")
    proxy.get=routed_pair
    proxy.install(model,Observation())
    if any("attention" in components(ARMS[k]) for k in labels):
        seen=set()
        for l,layer in enumerate(model.model.language_model.layers):
            for raw,attr in ATTENTION_LINEAR.items():
                key=f"model.llm.layers.{l}.attn.{raw}.weight"
                module=layer.self_attn.get_submodule(attr)
                if (dec.logical[key]!={"attention"} or tuple(module.weight.shape)!=tuple(dec.entries[key]["shape"])
                        or not torch.equal(module.weight[0],src.read(key,"cuda",0,1)[0])):
                    raise ValueError("Incorrect attention coordinate mapping at "+key)
                quant=dec.read(key,"cuda").to(module.weight.dtype)
                def linear(self,x,q=quant):
                    return F.linear(x,q if selected("attention") else self.weight,self.bias)
                module.forward=types.MethodType(linear,module)
                seen.add(key)
        if seen!={k for k,c in dec.logical.items() if c=={"attention"}}:raise ValueError("Partial attention replacement")
    embedding=model.model.language_model.embed_tokens
    if any("embedding" in components(ARMS[k]) for k in labels):
        q=dec.read("model.llm.embed.weight","cuda",0,len(embedding.weight)).to(embedding.weight.dtype)
        def embed(self,ids,q=q):
            return self.embed_norm(F.embedding(ids,q if selected("embedding") else self.weight,self.padding_idx,
                                   self.max_norm,self.norm_type,self.scale_grad_by_freq,self.sparse))
        embedding.forward=types.MethodType(embed,embedding)
    if any("head" in components(ARMS[k]) for k in labels):
        q=dec.read("model.llm.unembed.weight","cuda",0,len(model.lm_head.weight)).to(model.lm_head.weight.dtype)
        def readout(self,x,q=q):return F.linear(x,q if selected("head") else self.weight,self.bias)
        model.lm_head.forward=types.MethodType(readout,model.lm_head)

    def run_document_group(label,idx):
        task=current()
        task.selection=components(ARMS[label])
        inputs=[rows[i]["ids"] for i in idx]
        width=max(map(len,inputs))
        frozen=None
        if a.frozen:
            from calibrate_inkling2 import frozen_batch
            with ExitStack() as stack:
                arch=[stack.enter_context(np.load(loc/"serial/dynamic/A"/f"holdout-{i}.npz")) for i in idx]
                if not all(np.array_equal(r,z["input_ids"][0]) for r,z in zip(inputs,arch,strict=True)):raise ValueError("Frozen input differs")
                frozen=frozen_batch(arch,width)
        task.observation=Observer(frozen,compact=True)
        token_tensor=torch.tensor([ids+[0]*(width-len(ids)) for ids in inputs],device="cuda")
        result=model(input_ids=token_tensor,attention_mask=torch.ones_like(token_tensor),use_cache=False)
        if sum(task.observation.visits.values())!=48:raise ValueError("Incomplete recurrent trace")
        out=target/label
        out.mkdir(exist_ok=True,parents=True)
        for j,i in enumerate(idx):
            ids=np.asarray(inputs[j],np.int64)
            data=split_observations(task.observation.data,j,width,len(ids))
            logits=result.logits[j,:len(ids)].float().cpu().numpy()
            if not np.isfinite(logits).all():raise ValueError("Non-finite logits")
            dst=out/f"holdout-{i}.npz"
            with dst.with_suffix(".partial").open("wb") as f:np.savez(f,input_ids=ids[None,:],logits=logits,**data)
            dst.with_suffix(".partial").replace(dst)
        task.observation.data.clear()

    with torch.inference_mode(),ExitStack() as stack:
        for i,l in enumerate(model.model.language_model.layers):
            def stop(module,args,i=i):
                task=current()
                parent.switch((i,task.observation.visits[i]))
            stack.callback(l.register_forward_pre_hook(stop).remove)
            def capture(layer,which):
                def hook(module,args,output):
                    o=current().observation
                    handles={"layer":o.layer_hook,"gate":o.router_hook,
                             "attention":lambda l:o.output_hook(l,True),"moe":lambda l:o.output_hook(l,False)}
                    handles[which](layer)(module,args,output)
                return hook
            for module,which in ((l,"layer"),(l.mlp.gate,"gate"),(l.self_attn,"attention"),(l.mlp,"moe")):
                stack.callback(module.register_forward_hook(capture(i,which)).remove)
        tasks=[greenlet.greenlet(lambda label=label,idx=idx:run_document_group(label,idx))
               for label in labels for idx in GROUPS_OF_DOCUMENTS]
        print("Separate Transformers forwards",labels,"using 1x55, 3x29 and 3x49 batches",flush=True)
        for j in range(49):
            states=[t.switch() for t in tasks]
            if len(set(states))!=1:raise ValueError(f"Unequal physical schedules at call {j}: {states}")
            if j in (0,6,18,30,42,48):print("Completed layer calls per arm",j,flush=True)
        if not all(t.dead for t in tasks):raise ValueError("A source graph did not terminate")
    for label in labels:
        immutable(target/label/"splits.json",dict(condition=ARMS[label],protocol=digest(loc/"protocol.json"),
              batch_indices=[list(x) for x in GROUPS_OF_DOCUMENTS],routing="frozen" if a.frozen else "dynamic",
              greenlet_version=greenlet.__version__,execution="Separate standard model calls, with one physical layer call per coroutine in order"))


def run(a):
    import os
    import tempfile
    from filelock import FileLock
    from sm120_native import run as monitored
    loc,*_=protocol(a.root)
    target=loc/"serial"/("frozen" if a.frozen else "dynamic")
    os.environ["INKLING_SOURCE_CUDA"]=str(a.kernels.resolve(strict=True))
    lock=FileLock(str(Path(tempfile.gettempdir())/"strata-inkling-benchmark-gpu0.lock"))
    cmd=[sys.executable,"-u","-B",__file__,"measure","--root",str(a.root),"--llama",str(a.llama),"--arms",*a.arms]
    if a.frozen:cmd.append("--frozen")
    for trial in range(10):
        out=target/("run-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
        try:
            with lock.acquire(poll_interval=.003):monitored(out,cmd,12000,3600,21600)
            return
        except RuntimeError:
            f=out/"measurement.json"
            if trial==9 or not f.exists() or read(f)["reason"] not in {"physical_memory_pressure","device_memory_pressure","commit_pressure","disk_space_pressure"}:raise
            time.sleep(12)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=("run","measure"))
    for key in ("root","llama","kernels"):p.add_argument("--"+key,type=Path,required=key!="kernels")
    p.add_argument("--arms",nargs="+",choices=ARMS,default=[*GROUPS["forward"],*GROUPS["reverse"]])
    p.add_argument("--frozen",action="store_true")
    a=p.parse_args()
    if a.action=="run" and not a.kernels:p.error("Supply the verified source reconstruction kernel")
    (run if a.action=="run" else evaluate)(a)
