"""Matrix-free downstream JVPs through the official Inkling graph with one shared expert intervention."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import types
import time

import numpy as np
import torch
from torch.autograd import forward_ad
from torch.nn import functional as F

from infer import Experts, OfficialSafetensors, load_graph
from phase3_study import Traces, aggregate_visits, basis_desc
from activation_optimisation import calibration_covariance
from fisher_fidelity import row_metrics
from source import atomic_bytes
from spin8_cuda import Kernels
from spin8_quantizer import Basis, basis_matrix, decode


def scores(visit_jvps, combined, baseline_logits, actual_logits):
    j=np.asarray(visit_jvps,np.float64)
    if j.ndim!=2 or j.shape[1]!=combined.size:raise ValueError("Each visit must share one output tangent space")
    z=np.asarray(baseline_logits,np.float64);p=np.exp(z-z.max());p/=p.sum()
    net=j.sum(axis=0)
    gram=j@j.T/j.shape[1]
    actual=np.asarray(actual_logits,np.float64)-z
    fisher=lambda v:float(p@(v*v)-(p@v)**2)
    exact=row_metrics(z,actual_logits,200006)
    centred=j-(j@p)[:,None]
    fisher_gram=(centred*p)@centred.T
    eig=np.maximum(0.,np.linalg.eigvalsh(fisher_gram))
    return dict(independent=float(np.trace(gram)),recurrent=float(gram.sum()),
                cross_loop=float(gram.sum()-np.trace(gram)),gram=gram.tolist(),
                fisher=fisher(net),fisher_independent=sum(fisher(v) for v in j),
                fisher_kl_prediction=.5*fisher(combined.astype(float)),actual_kl=exact["kl_nats"],
                termination_kl=exact["termination_bernoulli_kl_nats"],termination_logodds_change=exact["candidate_event_log_odds"]-exact["reference_event_log_odds"],
                fisher_cross_loop=float(.5*(fisher_gram.sum()-np.trace(fisher_gram))),
                singular_values_for_visit_amplitudes=np.sqrt(eig[::-1]).tolist(),
                combined_jvp_mean_square=float(np.mean(combined.astype(float)**2)),
                superposition_relative_l2=float(np.linalg.norm(combined-net)/max(np.linalg.norm(net),1e-30)),
                actual_frozen_logit_mse=float(np.mean(actual**2)),actual_frozen_fisher=fisher(actual),
                first_order_relative_error=float(np.linalg.norm(actual-net)/max(np.linalg.norm(actual),1e-30)),
                first_order_cosine=float(net@actual/max(np.linalg.norm(net)*np.linalg.norm(actual),1e-30)))


def make_pairs(budget,seed):
    pairs={"hadamard":(Basis("V"),Basis("V"))}
    pairs["weight-only-hadamard"]=pairs["hadamard"]
    pairs["diagonal-hadamard"]=pairs["hadamard"]
    rng=np.random.default_rng(seed)
    for i in range(budget):
        theta=rng.normal(size=28);theta*=.25/np.linalg.norm(theta)
        params=tuple(np.asarray(theta,np.float32).tolist())
        pairs[f"signed-{i}"]=(Basis("signed",seed=seed+i),)*2
        for family,kinds in (("SO8","VV"),("triality","PM")):
            pairs[f"{family}-{i}"]=tuple(Basis(k,parameters=params) for k in kinds)
    return pairs


def quantised_pair(weights,bases,features,kernels,mode="block"):
    result=[];error=[]
    for w,b,cal in zip(weights,bases,features):
        c=None if mode=="weight-only" else calibration_covariance(cal,basis_matrix(b))
        h=c.diagonal(axis1=1,axis2=2).ravel().copy() if mode=="diagonal" else None
        payload,rot=kernels.encode(w.float(),b,h,covariance=c if mode=="block" else None)
        # Decode the actual stored bytes before restoring the physical input coordinates.
        decoded=torch.from_numpy(decode(payload.cpu().numpy(),tuple(w.shape))).to(w.device)
        original=(decoded.reshape(-1,128)@kernels.table(b,w.device)).reshape_as(w)
        result.append(original.to(torch.bfloat16))
        error.append(float(torch.mean((rot-decoded)**2)))
    return result,float(np.mean(error))


class Intervention:
    def __init__(self,expert_store,layer,expert):
        self.store=expert_store;self.target=layer;self.expert=expert

    def reset(self,trace,scenarios,eps,quant,dynamic):
        self.trace=trace;self.scenarios=scenarios;self.eps=eps;self.quant=quant;self.dynamic=dynamic
        self.visits=Counter();self.local=[[] for _ in scenarios];self.routes=[]

    def install(self,model):
        for layer,block in enumerate(model.model.language_model.layers):
            def evaluate(module,x,ids,mix,layer=layer):
                visit=self.visits[layer];self.visits[layer]+=1
                prefix=f"l{layer}.v{visit}"
                ref_ids=torch.as_tensor(self.trace[prefix+".ids"].astype(np.int64),device=x.device)
                n=len(ref_ids);batch=len(self.scenarios)
                if len(ids)!=batch*n:raise ValueError("Unexpected batch or router layout")
                frozen=ref_ids.repeat(batch,1)
                if self.dynamic:
                    overlap=(ids[:,:,None]==frozen[:,None,:]).any(-1).reshape(batch,n,-1).float().mean((1,2))
                    self.routes.append(overlap.cpu().tolist())
                else:
                    ids=frozen
                    mix=torch.as_tensor(self.trace[prefix+".weights"],device=x.device,dtype=mix.dtype).repeat(batch,1)
                out=torch.zeros_like(x,dtype=torch.float32)
                for expert in ids.unique(sorted=True).tolist():
                    tokens,slots=torch.where(ids==expert)
                    weights=self.store.get(layer,expert)
                    def expert_output(inp,pair):
                        gu=F.linear(inp,pair[0])
                        return F.linear(module.act_fn(gu[...,::2],gu[...,1::2]),pair[1])
                    selected=x[tokens]
                    current=expert_output(selected,weights).float()
                    if layer==self.target and expert==self.expert:
                        block_ids=tokens//n
                        first=(block_ids==0).nonzero().flatten()
                        if first.numel():
                            changed=expert_output(selected[first],self.quant).float()-current[first]
                            self.local[0].append(float(forward_ad.unpack_dual(changed).primal.square().mean()))
                        for scenario,mask in enumerate(self.scenarios):
                            if visit not in mask: continue
                            where=(block_ids==scenario).nonzero().flatten()
                            if not where.numel(): continue
                            # Differentiate through both physical projections and the original gate.
                            # At epsilon=1 this evaluates the actual decoded quantised expert.
                            pair=[(w.float()+self.eps[scenario]*(q.float()-w.float())).to(w.dtype)
                                  for w,q in zip(weights,self.quant,strict=True)]
                            current=current.index_copy(0,where,expert_output(selected[where],pair).float())
                    out.index_add_(0,tokens,(current.to(x.dtype)*mix[tokens,slots,None]).float())
                return out.to(x.dtype)
            block.mlp.experts.forward=types.MethodType(evaluate,block.mlp.experts)

    def run(self,model,trace,quant,dynamic=False):
        tokens=torch.as_tensor(trace["input_ids"].astype(np.int64),device="cuda")
        visits=[v for v in range(3) if f"l{self.target}.v{v}.ids" in trace]
        if not visits:raise ValueError("No physical layer visit")
        masks=[{v} for v in visits]+[set(visits),set(visits)]
        if dynamic:masks=[set(visits)]
        batch=len(masks)
        with torch.no_grad(),forward_ad.dual_level():
            values=torch.zeros(batch,device="cuda")
            values[-1]=1
            tangent=torch.ones_like(values);tangent[-1]=0
            eps=values if dynamic else forward_ad.make_dual(values,tangent)
            self.reset(trace,masks,eps,quant,dynamic)
            logits=model(input_ids=tokens.repeat(batch,1),attention_mask=torch.ones_like(tokens).repeat(batch,1),
                         use_cache=False,logits_to_keep=1).logits[:,0]
            primal,derivative=forward_ad.unpack_dual(logits)
            z=primal.float().cpu().numpy()
            if dynamic:return dict(logit_mse=float(np.mean((z[0]-trace["logits"][-1])**2)),
                                   router_top8_overlap=float(np.mean(self.routes)),
                                   **row_metrics(trace["logits"][-1],z[0],200006))
            if derivative is None:raise RuntimeError("The official graph did not propagate forward-mode tangents")
            deriv=derivative.float().cpu().numpy()
            if not np.isfinite(z).all() or not np.isfinite(deriv).all():raise ArithmeticError("Non-finite recurrent JVP")
            return dict(**scores(deriv[:len(visits)],deriv[-2],z[0],z[-1]),
                        activation=float(np.mean(self.local[0])) if self.local[0] else 0.,
                        baseline_reference_max_abs=float(np.abs(z[0]-trace["logits"][-1]).max()),
                        observed_visits=visits)


def run(a):
    a.output.mkdir(parents=True,exist_ok=True)
    files=sorted(a.traces.glob("calibration-*.npz"))
    if len(files)<4:raise ValueError("Four disjoint calibration sequences are required")
    traces=Traces(files,a.layer)
    expert=int(np.argmax(np.min(traces.counts,axis=0))) if a.expert is None else a.expert
    fit=Traces(files[:len(files)//2],a.layer)
    features=[aggregate_visits(fit.expert(expert,p)) for p in ("w13","w2")]
    if not all(features):raise ValueError("No calibration features for the selected expert")
    fit.close();traces.close()
    store=OfficialSafetensors(a.source);model=load_graph(store,"cuda",False);model.requires_grad_(False)
    loader=Experts(store,a.cache_gib,"cuda")
    probe=Intervention(loader,a.layer,expert);probe.install(model);kernel=Kernels(a.kernels)
    weights=[kernel.original(store.original.parts(f"model.llm.layers.{a.layer}.mlp.experts.{p}_weight",expert),torch.float32)
             for p in ("w13","w2")]
    pairs=make_pairs(a.budget,9581+a.layer*128+expert)
    conditions=("weight_mse","activation","independent","recurrent","fisher_kl_prediction","joint")
    records={};candidates={}
    for label,bases in pairs.items():
        started=time.monotonic()
        mode={"weight-only-hadamard":"weight-only","diagonal-hadamard":"diagonal"}.get(label,"block")
        candidate,error=quantised_pair(weights,bases,features,kernel,mode)
        candidates[label]=[x.cpu() for x in candidate]
        docs={}
        for path in (files[:1] if a.pilot else files):
            with np.load(path) as z:docs[path.stem]=dict(weight_mse=error,**probe.run(model,z,candidate))
            r=docs[path.stem]
            r["joint"]=sum(w*r[k] for w,k in zip(a.loss_weights,("activation","fisher_kl_prediction","actual_kl","termination_kl"),strict=True))
        torch.cuda.synchronize()
        elapsed=time.monotonic()-started
        for r in docs.values(): r["candidate_calibration_seconds"]=elapsed
        records[label]=docs
        if a.pilot:
            atomic_bytes(a.output/"jvp-pilot.json",json.dumps(dict(layer=a.layer,expert=expert,basis=label,
                         results=docs,scope="single calibration sequence, no deployment selection"),indent=2,allow_nan=False).encode())
            return
        atomic_bytes(a.output/"calibration-results.json",json.dumps(records,allow_nan=False).encode())
        print(f"Scored {label} on {len(files)} calibration sequences",flush=True)
    cut=len(files)//2;select={}
    for metric in conditions:
        select[metric]={}
        for family in ("SO8","triality","signed","codecs"):
            names=(["weight-only-hadamard","diagonal-hadamard","hadamard"] if family=="codecs" else
                   [n for n in pairs if n.startswith(family+"-")])
            best=min(names,key=lambda n:np.mean([records[n][p.stem][metric] for p in files[:cut]]))
            gains=[(records["hadamard"][p.stem][metric]-records[best][p.stem][metric])/
                   max(records["hadamard"][p.stem][metric],1e-30) for p in files[cut:]]
            select[metric][family]=dict(chosen=best if min(gains)>a.margin else "hadamard",validation_gains=gains)
    policy=dict(layer=a.layer,expert=expert,source_revision=store.original.revision,selection=select,margin=a.margin,
                calibration_sequences=[p.name for p in files],budget_per_family=a.budget,
                candidate_bases={n:list(map(basis_desc,b)) for n,b in pairs.items()},selection_split="calibration",
                checkpoint_dtype="raw NVFP4/MXFP8 decoded to FP32 for quantisation, BF16 for reference forward",
                output_positions="last token per sequence",objective_weights=a.loss_weights,
                tangent="shared physical BF16 weights interpolated from source to decoded PQ2_0 through both expert projections and the nonlinear gate",
                finite_time_spectrum="Fisher-weighted logit displacement versus visit amplitudes in this direction only")
    path=a.output/"recurrent-lock.json"
    if path.exists() and json.loads(path.read_bytes())!=policy:raise ValueError("Existing recurrence policy differs")
    atomic_bytes(path,json.dumps(policy,indent=2).encode())
    held={}
    names={"hadamard","weight-only-hadamard","diagonal-hadamard"}|{choice["chosen"] for v in select.values() for choice in v.values()}
    for p in sorted(a.traces.glob("holdout-*.npz")):
        with np.load(p) as z:
            held[p.stem]={}
            for name in sorted(names):
                candidate=[x.cuda() for x in candidates[name]]
                held[p.stem][name]=dict(frozen=probe.run(model,z,candidate),dynamic=probe.run(model,z,candidate,True))
        atomic_bytes(a.output/"recurrent-holdout.json",json.dumps(dict(selection_digest=hashlib.sha256(path.read_bytes()).hexdigest(),
                     results=held),indent=2,allow_nan=False).encode())


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("source","traces","output","kernels"):p.add_argument("--"+key,type=Path,required=True)
    p.add_argument("--layer",type=int,default=6);p.add_argument("--expert",type=int);p.add_argument("--budget",type=int,default=2)
    p.add_argument("--cache-gib",type=float,default=.75);p.add_argument("--margin",type=float,default=.01)
    p.add_argument("--loss-weights",type=float,nargs=4,default=[1.,1.,1.,1.],metavar=("ACT","DYN","KL","TERM"))
    p.add_argument("--pilot",action="store_true",help="Check one real matrix-free JVP without selecting a policy")
    run(p.parse_args())
