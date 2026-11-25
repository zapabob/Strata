"""Fit on calibration sequences, lock per-expert decisions, then evaluate unseen sequences and rows."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from activation_optimisation import block_covariance, fit_covariance, paired_interval, rotate
from benchmark_spin8_ablation import metrics
from official_weights import Original, reconstruct
from source import atomic_bytes
from spin8_continuous import optimise_continuously
from spin8_quantizer import Basis, basis_matrix, decode


def f32bits(value):
    return (value.astype(np.uint32)<<16).view(np.float32)


class Traces:
    def __init__(self,paths,layer):
        self.layer=layer
        self.files=[(p.stem,np.load(p)) for p in paths]
        self.records=[]
        self.counts=np.zeros((3,128),np.int64)
        for doc,f in self.files:
            for visit in range(3):
                prefix=f"l{layer}.v{visit}"
                if prefix+".ids" not in f:continue
                ids=f[prefix+".ids"];self.counts[visit]+=np.bincount(ids.ravel(),minlength=128)
                self.records.append((doc,visit,f,prefix,ids,f32bits(f[prefix+".gate_input"])))

    def expert(self,e,proj):
        items=[]
        for doc,visit,f,prefix,ids,gate in self.records:
            tokens,_=np.where(ids==e)
            if len(tokens):
                x=gate[tokens] if proj=="w13" else f32bits(f[prefix+f".e{e}.down_input"])
                items.append((doc,visit,x))
        return items

    def close(self):
        for _,f in self.files:f.close()


def aggregate_visits(records):
    return [np.concatenate([x for _,j,x in records if j==v])
            for v in sorted({j for _,j,_ in records})]


def basis_desc(b):
    return dict(kind=b.kind,theta=b.theta,seed=b.seed,parameters=list(b.parameters))


def fit_projection(w,b,cal,sweeps):
    r=basis_matrix(b)
    visits=aggregate_visits(cal)
    c=block_covariance(visits,r)
    payload=fit_covariance(rotate(w.astype(np.float64),r),c,sweeps)
    return rotate(decode(payload,w.shape).astype(np.float64),r.T)


def sequence_loss(w,q,records):
    d=(w-q).astype(np.float64)
    by={}
    for doc,v,x in records:
        value=float(np.mean((x.astype(np.float64)@d.T)**2))
        by.setdefault(doc,[]).append((v,value))
    return {doc:float(np.mean([a for _,a in vals])) for doc,vals in by.items()}


def search_pair(ws,fit_data,budget,sweeps,seed):
    baseline=Basis("hadamard"); study={}
    memo={}
    def loss(j,b):
        key=(j,b)
        if key not in memo:
            q=fit_projection(ws[j],b,fit_data[j],sweeps)
            memo[key]=np.mean(list(sequence_loss(ws[j],q,fit_data[j]).values()))
        return memo[key]
    # Fixed controls have one distinct point; identical repeated scores consume no extra information.
    for label,kind in (("fixed-hadamard","hadamard"),("direct","direct"),("fixed-V","V"),("fixed-P","P"),("fixed-M","M")):
        b=Basis(kind);study[label]=([b,b],[[float(loss(j,b))]*budget for j in range(2)])
    for label,kind in (("signed-hadamard","signed"),("haar-SO128","random"),("haar-octet","random-octet"),("spinor-gauge","gauged-P")):
        selected=[]; histories=[]
        for j in range(2):
            choices=[baseline if kind=="signed" and i==0 else Basis(kind,seed=seed+i) for i in range(budget)]
            h=[float(loss(j,b)) for b in choices];selected.append(choices[int(np.argmin(h))]);histories.append(h)
        study[label]=selected,histories
    for label,rep in (("general-SO8","V"),("optimised-Splus","P"),("optimised-Sminus","M")):
        selected=[];histories=[]
        for j in range(2):
            def score(theta):
                return loss(j,Basis(rep,parameters=tuple(map(float,theta))))
            theta,h=optimise_continuously(score,budget,seed+j)
            selected.append(Basis(rep,parameters=tuple(map(float,theta))));histories.append(h)
        study[label]=selected,histories
    norm=[max(loss(j,baseline),1e-30) for j in range(2)]
    def coupled(theta):
        return sum(loss(j,Basis(rep,parameters=tuple(map(float,theta))))/norm[j] for j,rep in enumerate("PM"))/2
    theta,h=optimise_continuously(coupled,budget,seed)
    study["coupled-triality"]=([Basis(rep,parameters=tuple(map(float,theta))) for rep in "PM"],[h,h])
    return study


def save(path,data):
    atomic_bytes(path,json.dumps(data,indent=2,allow_nan=False).encode())


def run(args):
    original=Original(args.source)
    out=args.output;out.mkdir(parents=True,exist_ok=True)
    cpaths=sorted(args.traces.glob("calibration-*.npz"))
    if len(cpaths)<4:raise ValueError("At least four calibration sequences are required for fitting and selection")
    cut=len(cpaths)//2
    ctrl={"source_revision":original.revision,"selection_split":"calibration","candidate_evaluations_per_projection":args.budget,
          "reserved_metadata_bytes_per_expert_projection":128,"margin":args.margin,"experts":[]}
    for l in args.layers:
        fit=Traces(cpaths[:cut],l);selection=Traces(cpaths[cut:],l)
        counts=fit.counts.sum(axis=0)+selection.counts.sum(axis=0)
        order=np.argsort(counts,kind="stable")
        experts=np.unique(order[np.rint(np.linspace(0,127,args.experts)).astype(int)]).tolist()
        for e in experts:
            keys=[f"model.llm.layers.{l}.mlp.experts.{p}_weight" for p in ("w13","w2")]
            data=[fit.expert(e,p) for p in ("w13","w2")]
            valid=[selection.expert(e,p) for p in ("w13","w2")]
            record=dict(layer=l,expert=e,source_scheme=original.schemes[keys[0]]["weight_transform"],
                        calibration_counts_per_visit=(fit.counts[:,e]+selection.counts[:,e]).tolist(),
                        decision=["fixed-hadamard"]*2,choices={})
            if not all(data) or not all(valid):
                record["reason"]="Insufficient calibration routes";ctrl["experts"].append(record);continue
            train=[reconstruct(original.parts(k,e,0,args.rows)) for k in keys]
            results=search_pair(train,data,args.budget,args.sweeps,803+l*128+e)
            validation={}
            for method,(bs,histories) in results.items():
                validation[method]=[sequence_loss(train[j],fit_projection(train[j],bs[j],data[j],args.sweeps),valid[j]) for j in range(2)]
                record["choices"][method]=dict(bases=list(map(basis_desc,bs)),evaluation_history=histories,
                                                calibration_selection=validation[method])
            permitted=("general-SO8","optimised-Splus","optimised-Sminus","coupled-triality")
            for j in range(2):
                ref=validation["fixed-hadamard"][j]
                if len(ref)<2:continue
                best=min(permitted,key=lambda method:np.mean(list(validation[method][j].values())))
                rel=[(ref[k]-validation[best][j][k])/max(ref[k],1e-30) for k in ref]
                if min(rel)>args.margin:record["decision"][j]=best
            ctrl["experts"].append(record)
            save(out/"calibration-progress.json",ctrl)
            print(f"Calibration L{l} E{e}: {record['decision']}",flush=True)
        fit.close();selection.close()
    # No holdout file has been opened above this line.
    lock=out/"selection-lock.json"
    if lock.exists() and json.loads(lock.read_bytes())!=ctrl:raise ValueError("Refusing to change an existing selection lock")
    if not lock.exists():save(lock,ctrl)
    results={"lock_sha256":hashlib.sha256(lock.read_bytes()).hexdigest(),"rows_per_projection":args.rows,"experts":[]}
    hpaths=sorted(args.traces.glob("holdout-*.npz"))
    if not hpaths:raise ValueError("No held-out sequences are available")
    for l in args.layers:
        cal=Traces(cpaths,l);held=Traces(hpaths,l)
        for rec in [x for x in ctrl["experts"] if x["layer"]==l]:
            e=rec["expert"]
            for j,p in enumerate(("w13","w2")):
                calx,holdx=cal.expert(e,p),held.expert(e,p)
                if not calx or not holdx or not rec["choices"]:continue
                k=f"model.llm.layers.{l}.mlp.experts.{p}_weight"
                w=reconstruct(original.parts(k,e,original.header[k]["shape"][1]-args.rows,args.rows))
                trial={}; cache={}
                for label,entry in rec["choices"].items():
                    d=entry["bases"][j]
                    b=Basis(d["kind"],theta=d["theta"],seed=d["seed"],parameters=tuple(d["parameters"]))
                    if b not in cache:
                        q=fit_projection(w,b,calx,args.sweeps)
                        cache[b]=dict(**metrics(w,q,aggregate_visits(holdx)),sequence_mse=sequence_loss(w,q,holdx),
                                     delta_by_visit=[dict(sequence=s,visit=v,mse=float(np.mean((x.astype(float)@(w-q).T)**2))) for s,v,x in holdx])
                    trial[label]=cache[b]
                results["experts"].append(dict(layer=l,expert=e,projection=p,selected=rec["decision"][j],methods=trial))
        cal.close();held.close()
        save(out/"heldout.json",results)
    # Cluster both projections and all sequences within each physical layer/expert.
    clustered={}
    for item in results["experts"]:
        a=item["methods"]["fixed-hadamard"]["activation_mse"]
        b=item["methods"][item["selected"]]["activation_mse"]
        clustered.setdefault((item["layer"],item["expert"]),[]).append((a-b)/max(a,1e-30))
    if clustered:
        gains=np.array([np.mean(x) for x in clustered.values()])
        results["paired_expert_relative_gain"]=paired_interval(gains,np.zeros_like(gains))
    save(out/"heldout.json",results)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("source","traces","output"):p.add_argument("--"+key,type=Path,required=True)
    p.add_argument("--layers",type=int,nargs="+",default=[0,6,17,20,23])
    p.add_argument("--experts",type=int,default=3);p.add_argument("--rows",type=int,default=8)
    p.add_argument("--budget",type=int,default=5);p.add_argument("--sweeps",type=int,default=1)
    p.add_argument("--margin",type=float,default=.01)
    run(p.parse_args())
