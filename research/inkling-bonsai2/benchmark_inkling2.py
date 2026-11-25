"""Score the same token trajectory, compare routing interventions and measure native throughput."""
import argparse
import json
import math
import os
import subprocess
import time
from pathlib import Path
import numpy as np
from scipy.special import logsumexp

from activation_optimisation import paired_interval


def nll_increase(rows):
    """Positive differences mean greater loss after quantisation."""
    pairs = list(rows)
    outcome = paired_interval([math.log(r["candidate_ppl"]) for r in pairs],
                              [math.log(r["reference_ppl"]) for r in pairs])
    outcome["improved"], outcome["worsened"] = outcome["worsened"], outcome["improved"]
    outcome["direction"] = "candidate minus reference NLL, in nats; lower is better"
    return outcome


def aggregate(rows):
    """Use the number of observed next tokens as the cross-entropy denominator."""
    total = sum(r["tokens"] for r in rows.values())
    if not total:
        raise ValueError("No scored next tokens")
    ref = sum(r["sum_reference_nll"] for r in rows.values()) / total
    cand = sum(r["sum_candidate_nll"] for r in rows.values()) / total
    return dict(sequences=rows, total_tokens=total, reference_nll=ref, candidate_nll=cand,
                delta_nll=cand-ref, reference_ppl=math.exp(ref), candidate_ppl=math.exp(cand),
                mean_kl=sum(r["sum_kl"] for r in rows.values())/total,
                top1_agreement=sum(r["argmax_matches"] for r in rows.values())/total,
                sequence_paired_nll_increase=nll_increase(rows.values()))


def score(reference,candidate,ids):
    if (reference.ndim!=2 or candidate.ndim!=2 or reference.shape[0]!=len(ids) or
            candidate.shape[0]!=len(ids) or candidate.shape[1]<reference.shape[1] or len(ids)<2):
        raise ValueError("The reference and candidate must cover the same tokens and vocabulary")
    if not np.isfinite(reference).all() or not np.isfinite(candidate).all():raise ArithmeticError("Non-finite logits")
    kls=[]; nr=[];nc=[];agree=0;extra_mass=0.
    for start in range(0,len(ids)-1,4):
        end=min(start+4,len(ids)-1)
        a=reference[start:end].astype(np.float64);b=candidate[start:end].astype(np.float64)
        a-=logsumexp(a,axis=1)[:,None];b-=logsumexp(b,axis=1)[:,None]
        kls.extend(np.einsum("ij,ij->i",np.exp(a),a-b[:,:a.shape[1]]).tolist())
        extra_mass+=float(np.exp(b[:,a.shape[1]:]).sum())
        gold=np.asarray(ids[start+1:end+1]);rows=np.arange(end-start)
        nr.extend((-a[rows,gold]).tolist());nc.extend((-b[rows,gold]).tolist())
        agree+=int(np.sum(a.argmax(axis=1)==b.argmax(axis=1)))
    return dict(tokens=len(kls),kl_reference_to_quant=float(np.mean(kls)),top1_agreement=agree/len(kls),
                reference_ppl=math.exp(np.mean(nr)),candidate_ppl=math.exp(np.mean(nc)),
                sum_kl=sum(kls),sum_reference_nll=sum(nr),sum_candidate_nll=sum(nc),argmax_matches=agree,
                reference_vocab=reference.shape[1],candidate_vocab=candidate.shape[1],
                mean_extra_vocab_mass=extra_mass/len(kls))


def hidden(a,b):
    a=(a.astype(np.uint32)<<16).view(np.float32).astype(np.float64)
    b=(b.astype(np.uint32)<<16).view(np.float32).astype(np.float64)
    if a.shape!=b.shape:raise ValueError("Unequal hidden-state geometries")
    sa,sb,dot=(float(np.vdot(x,y)) for x,y in ((a,a),(b,b),(a,b)))
    d=a-b
    se=float(np.vdot(d,d))
    return dict(relative_l2=math.sqrt(se/max(sa,1e-60)),cosine=dot/max(math.sqrt(sa*sb),1e-30),
                mse=se/a.size,reference_sum_squares=sa,candidate_sum_squares=sb,
                sum_squared_error=se,dot=dot,values=a.size)


def trace(ref,cand,scored_only=False):
    with np.load(ref) as r,np.load(cand) as c:
        if not np.array_equal(r["input_ids"],c["input_ids"]):raise ValueError("Token trajectories differ")
        s=score(r["logits"],c["logits"],r["input_ids"][0])
        visits=[]
        positions=slice(None,-1) if scored_only else slice(None)
        for k in sorted(r.files):
            if not k.endswith(".hidden"):continue
            name=k.removesuffix(".hidden");a=r[name+".ids"][positions];b=c[name+".dynamic_ids"][positions]
            overlap=(a[:,:,None]==b[:,None,:]).any(axis=-1).mean()
            row=dict(layer=int(name.split(".")[0][1:]),visit=int(name.split(".")[1][1:]),
                     dynamic_router_overlap=float(overlap),**hidden(r[k][:,positions],c[k][:,positions]))
            if scored_only:
                used=c[name+".ids"][positions]
                row["applied_top8_overlap"]=float((a[:,:,None]==used[:,None,:]).any(-1).mean())
                row["per_position_router_overlap"]=(a[:,:,None]==b[:,None,:]).any(-1).mean(-1).tolist()
                for suffix in ("attention_output","expert_mixture"):
                    field=name+"."+suffix
                    if field in r and field in c:
                        row[suffix]=hidden(r[field][:,positions],c[field][:,positions])
                for suffix in ("router_logit_margin","routing_margin"):
                    field=name+"."+suffix
                    if field in r and field in c:
                        mr,mc=r[field][positions],c[field][positions]
                        row[suffix]=dict(reference_mean=float(mr.mean()),candidate_mean=float(mc.mean()),
                                         reference=mr.tolist(),candidate=mc.tolist())
            if name+".router_logits" in r and name+".router_logits" in c:
                def lnrouter(x):
                    logp=-np.logaddexp(0,-x.astype(np.float64))
                    return logp-logsumexp(logp,axis=-1,keepdims=True)
                lr,lc=lnrouter(r[name+".router_logits"][positions]),lnrouter(c[name+".router_logits"][positions])
                row["router_probability_kl"]=float(np.mean(np.sum(np.exp(lr)*(lr-lc),axis=-1)))
            visits.append(row)
        visits.sort(key=lambda v:(v["layer"]//6 if v["layer"]<6 else
                                  (1+2*v["visit"]+(v["layer"]-6)//6 if v["layer"]<18 else 7),
                                  v["layer"]))
        return dict(**s,visits=visits)


def binary(directory,name):
    return str((directory/(name+(".exe" if os.name=="nt" else ""))).resolve(strict=True))


def native_scores(args,files):
    cmd=[binary(args.bin,"inkling-logits"),"--gpu-layers",str(args.gpu_layers),str(args.model)]
    for ref in files:
        inp=args.output.parent/(ref.stem+".i32")
        with np.load(ref) as z:
            z["input_ids"][0].astype("<i4").tofile(inp)
        cmd.extend([str(inp),str(inp.with_suffix(".logits"))])
    if os.name=="nt":
        from sm120_native import run
        run(args.output.parent/"native-run",cmd,args.admit_mib,900,7200)
    else:
        with (args.output.parent/"native.log").open("w",encoding="utf8") as log:
            subprocess.run(cmd,check=True,stderr=log)
    results={}
    for ref in files:
        out=args.output.parent/(ref.stem+".logits")
        with out.open("rb") as f:
            n,v=np.fromfile(f,dtype="<i4",count=2)
        if n<=0 or v<=0 or out.stat().st_size!=8+4*int(n)*int(v):
            raise ValueError("Native output has an incorrect row count, vocabulary size or byte extent")
        output=np.memmap(out,dtype="<f4",mode="r",offset=8,shape=(int(n),int(v)))
        with np.load(ref) as z:
            results[ref.stem]=score(z["logits"],output,z["input_ids"][0])
    return results


def benchmark(args):
    import psutil
    results=[]
    def gpu_sample():
        try:
            values = subprocess.check_output(
                ["nvidia-smi", "--id=0", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                text=True, timeout=5, stderr=subprocess.DEVNULL)
            return int(values.splitlines()[0])
        except (FileNotFoundError, subprocess.SubprocessError, ValueError, IndexError):
            return None
    for depth in args.depth:
        cmd=[binary(args.bin,"llama-bench"),"-m",str(args.model),"-ngl",str(args.gpu_layers),
             "-p",",".join(map(str,args.prefill)),"-n",",".join(map(str,args.decode)),
             "-r",str(args.repetitions),"-d",str(depth),"-o","json","-t","5",
             "-b",str(args.batch),"-ub",str(args.ubatch)]
        output=args.output.parent/f"bench-depth-{depth}.json";log=output.with_suffix(".log")
        baseline_gpu=gpu_sample();peak_rss=peak_gpu=0;start=time.monotonic();samples=0
        with output.open("w",encoding="utf8") as f,log.open("w",encoding="utf8") as e:
            proc=subprocess.Popen(cmd,stdout=f,stderr=e)
            ps=psutil.Process(proc.pid)
            while proc.poll() is None:
                try:peak_rss=max(peak_rss,ps.memory_info().rss)
                except psutil.NoSuchProcess:pass
                sample=gpu_sample()
                if sample is not None:
                    peak_gpu=max(peak_gpu,sample)
                    samples+=1
                time.sleep(.5)
        measurements=json.loads(output.read_bytes()) if proc.returncode==0 else None
        results.append(dict(prefill_depth=depth,returncode=proc.returncode,command=cmd,model=str(args.model),
                            starting_device_used_mib=baseline_gpu,
                            peak_sampled_process_rss_bytes=peak_rss,peak_sampled_device_used_mib=peak_gpu or None,
                            gpu_samples=samples,seconds=time.monotonic()-start,
                            measurements=measurements,log=str(log)))
        args.output.write_text(json.dumps(results,indent=2))
        if proc.returncode or not measurements:
            raise RuntimeError(f"llama-bench produced no successful measurement at depth {depth}. See {log}")


def main(a):
    a.output.parent.mkdir(parents=True,exist_ok=True)
    if a.mode=="throughput":return benchmark(a)
    files=sorted(a.reference.glob("holdout-*.npz"))
    if not files:raise ValueError("No held-out sequences")
    rows=({f.stem:trace(f,a.candidate/f.name) for f in files} if a.mode=="trace" else native_scores(a,files))
    result=aggregate(rows)
    a.output.write_text(json.dumps(result,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=["trace","native","throughput"])
    for k in ("reference","candidate","model","bin","output"):p.add_argument("--"+k,type=Path,required=k=="output")
    p.add_argument("--depth",type=int,nargs="+",default=[0])
    p.add_argument("--prefill",type=int,nargs="+",default=[512,2048,8192])
    p.add_argument("--decode",type=int,nargs="+",default=[128,512])
    p.add_argument("--repetitions",type=int,default=5)
    p.add_argument("--batch",type=int,default=2048)
    p.add_argument("--ubatch",type=int,default=512)
    p.add_argument("--gpu-layers",type=int,default=99)
    p.add_argument("--admit-mib",type=int,default=11300)
    main(p.parse_args())
