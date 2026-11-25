"""Select each physical expert's input basis using calibration only, retaining H128 on weak evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

from official_weights import Original, reconstruct
from activation_optimisation import calibration_covariance, fit_covariance
from phase3_study import Traces, aggregate_visits, basis_desc, sequence_loss
from source import atomic_bytes
from spin8_quantizer import Basis, basis_matrix, decode, fit


def run(args):
    o=Original(args.source); files=sorted(args.traces.glob("calibration-*.npz"))
    if len(files)<4:raise ValueError("Four disjoint calibration sequences are required")
    args.output.mkdir(parents=True,exist_ok=True)
    calibration_identity={}
    for f in files:
        with f.open("rb") as stream:calibration_identity[f.name]=hashlib.file_digest(stream,"sha256").hexdigest()
    kernels=None
    if args.kernels:
        import torch
        from spin8_cuda import Kernels
        kernels=Kernels(args.kernels)
    def codec(weight,basis,visits,mode):
        gram=calibration_covariance(visits,basis_matrix(basis),args.prior) if mode=="block" else None
        if kernels:
            x=torch.from_numpy(weight).to("cuda",dtype=torch.float32)
            payload,_=kernels.encode(x,basis,covariance=gram)
            packed=payload.cpu().numpy()
        else:
            wr=basis.apply(weight)
            packed=fit(wr) if gram is None else fit_covariance(wr,gram)
        return basis.apply(decode(packed,weight.shape),inverse=True)
    fixed=Basis("V")
    candidates=[fixed,Basis("P"),Basis("M")]
    study={}
    if args.lock:
        lock=json.loads(args.lock.read_bytes())
        if lock["source_revision"]!=o.revision or lock["selection_split"]!="calibration":raise ValueError("Wrong study lock")
        for rec in lock["experts"]:
            for j,p in enumerate(("w13","w2")):
                decision=rec["decision"][j]
                if decision!="fixed-hadamard":
                    d=rec["choices"][decision]["bases"][j]
                    study[(rec["layer"],rec["expert"],p)]=Basis(d["kind"],parameters=tuple(d["parameters"]))
    atlas=[fixed]; bank_indices={}; codec_modes={};records=[]
    for layer in range(24):
        train=Traces(files[:len(files)//2],layer)
        valid=Traces(files[len(files)//2:],layer)
        moments={}
        for proj,suffix in [("w13","ffn_gate_up_exps"),("w2","ffn_down_exps")]:
            raw=f"model.llm.layers.{layer}.mlp.experts.{proj}_weight"
            name=f"blk.{layer}.{suffix}.weight"
            bank_indices[name]=[]
            codec_modes[name]=[]
            pooled={}
            for trace in (train,valid):
                for _,v,f,prefix,ids,gate in trace.records:
                    if proj=="w13":
                        pooled.setdefault(v,[]).append(gate)
                    else:
                        # All routed down inputs at this layer/visit provide a measured fallback.
                        from phase3_study import f32bits
                        for e in np.unique(ids):
                            pooled.setdefault(v,[]).append(f32bits(f[prefix+f".e{e}.down_input"]))
            pooled=[np.concatenate(pooled[v]) for v in sorted(pooled)]
            pooled_moments={}
            for expert in range(128):
                training=train.expert(expert,proj); selection=valid.expert(expert,proj)
                b=fixed;mode="weight-only";reason="insufficient calibration routes";scores={}
                choices=candidates+([study[(layer,expert,proj)]] if (layer,expert,proj) in study else [])
                if training and len({s for s,_,_ in selection})>=2:
                    w=reconstruct(o.parts(raw,expert,0,args.rows))
                    visits=aggregate_visits(training)
                    basic=codec(w,fixed,visits,"weight-only")
                    ref=sequence_loss(w,basic,selection)
                    trials={alt:codec(w,alt,visits,"block") for alt in choices}
                    conventional=sequence_loss(w,trials[fixed],selection)
                    def gain(base,alt):
                        return {s:(base[s]-alt[s])/max(base[s],1e-30) for s in base}
                    if min(gain(ref,conventional).values())>args.margin:
                        mode="block";ref=conventional
                    best=min(trials,key=lambda alt:np.mean(list(sequence_loss(w,trials[alt],training).values())))
                    scores=gain(ref,sequence_loss(w,trials[best],selection))
                    reason="conventional Hadamard retained"
                    if best!=fixed and min(scores.values())>args.margin:
                        b,mode=best,"block";reason="calibration margin met on every selection sequence"
                if b not in atlas:atlas.append(b)
                bank_indices[name].append(atlas.index(b))
                codec_modes[name].append(mode)
                observed=aggregate_visits(training+selection)
                if observed:
                    h=np.mean([np.mean(b.apply(x).astype(np.float64)**2,axis=0) for x in observed],axis=0)
                    if mode=="block":
                        moments[f"cov.{proj}.{expert}"]=calibration_covariance(observed,basis_matrix(b),args.prior)
                else:
                    if b not in pooled_moments:
                        pooled_moments[b]=np.mean([np.mean(b.apply(x).astype(np.float64)**2,axis=0) for x in pooled],axis=0)
                    h=pooled_moments[b]
                moments[f"{proj}.{expert}"]=h.astype(np.float32)
                records.append(dict(layer=layer,expert=expert,projection=proj,basis=atlas.index(b),codec=mode,reason=reason,
                                    counts_by_visit=(train.counts[:,expert]+valid.counts[:,expert]).tolist(),
                                    validation_relative_gain=scores,moment_source="expert" if observed else "layer"))
        temp=args.output/f"layer-{layer:02d}.partial"
        with temp.open("wb") as f:np.savez(f,**moments)
        temp.replace(args.output/f"layer-{layer:02d}.npz")
        train.close();valid.close()
        print(f"Selected physical layer {layer+1}/24",flush=True)
    policy=dict(source_revision=o.revision,selection_split="calibration",calibration_sequences=calibration_identity,
                margin=args.margin,rows_per_expert_for_selection=args.rows,bases=list(map(basis_desc,atlas)),bank_indices=bank_indices,
                physical_projection_decisions=len(records),non_hadamard=sum(x["basis"]!=0 for x in records),
                covariance_prior=args.prior,codec_modes=codec_modes)
    dest=args.output/"policy.json"
    if dest.exists() and json.loads(dest.read_bytes())!=policy:raise ValueError("An existing calibration lock differs")
    atomic_bytes(args.output/"expert-decisions.json",json.dumps(records,separators=(",",":")).encode())
    atomic_bytes(dest,json.dumps(policy,indent=2).encode())


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for x in ("source","traces","output"):p.add_argument("--"+x,type=Path,required=True)
    p.add_argument("--rows",type=int,default=8);p.add_argument("--margin",type=float,default=.01);p.add_argument("--lock",type=Path)
    p.add_argument("--prior",type=float,default=128);p.add_argument("--kernels",type=Path)
    run(p.parse_args())
